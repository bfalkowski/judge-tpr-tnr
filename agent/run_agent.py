"""Run paper 2's support agent on a dataset from this repo and record its decisions.

  P2_DIR=p2 python agent/run_agent.py --dataset v3 --config clean --run-id agent-v3-clean

The agent is eval-run-validity's, imported unchanged from a checkout at the
pinned commit (P2_COMMIT below). Its decisions are the real outputs the judge
is validated on. Each decision is labeled by the reference policy: PASS when
the agent's action is the one the policy gives, FAIL otherwise.

Configs (all from paper 2):
  clean          policy v1, default decision instructions, full context
  template_edit  "Pick the action that best keeps this customer happy."
  context_strip  stock levels removed from the agent's context
  prompt_edit    policy v0, which predates the $500 refund limit

The judge always sees the true policy, order and stock, whatever the agent saw.

Writes runs/<run_id>/manifest.json and runs/<run_id>/decisions.jsonl.
"""

import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P2_COMMIT = "12a0eef7c90b3b77b84953c81946398f2d1f84d7"
CONFIGS = ["clean", "template_edit", "context_strip", "prompt_edit"]


def load_p2(p2_dir):
    head = subprocess.run(["git", "-C", p2_dir, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != P2_COMMIT:
        sys.exit(f"{p2_dir} is at {head or 'no commit'}, expected eval-run-validity {P2_COMMIT}")
    sys.path.insert(0, os.path.abspath(p2_dir))
    from agents import jev, support  # noqa: F401
    from agents.orders import OrdersService
    from agents.policy import POLICIES
    return jev, support, OrdersService, POLICIES


def make_cfg(config, support, POLICIES):
    cfg = {"policy_version": "v1", "policy_text": POLICIES["v1"],
           "decision_instructions": support.DECISION_INSTRUCTIONS,
           "context_fields": ["order", "policy", "stock", "ticket", "today"],
           "error_policy": "loud", "dataset": None}
    if config == "template_edit":
        cfg["decision_instructions"] = support.EDITED_DECISION_INSTRUCTIONS
    elif config == "context_strip":
        cfg["context_fields"].remove("stock")
    elif config == "prompt_edit":
        cfg["policy_version"], cfg["policy_text"] = "v0", POLICIES["v0"]
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--config", required=True, choices=CONFIGS)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "runs"))
    a = ap.parse_args()
    if os.environ.get("JEV_BACKEND") != "stub" and not os.environ.get("TYPESAFE_API_KEY"):
        sys.exit("TYPESAFE_API_KEY is not set (or use JEV_BACKEND=stub)")
    jev, support, OrdersService, POLICIES = load_p2(os.environ.get("P2_DIR", os.path.join(ROOT, "p2")))

    sys.path.insert(0, ROOT)
    from judge import data
    tickets, fixture = data.load(a.dataset)
    if a.limit:
        tickets = tickets[: a.limit]
    cfg = make_cfg(a.config, support, POLICIES)
    run_dir = os.path.join(a.out, a.run_id)
    if os.path.exists(os.path.join(run_dir, "decisions.jsonl")):
        sys.exit(f"{run_dir} already has results")
    os.makedirs(run_dir, exist_ok=True)
    manifest = {"run_id": a.run_id, "dataset": a.dataset, "config": a.config, "p2_commit": P2_COMMIT,
                "model": jev.model(), "backend": os.environ.get("JEV_BACKEND") or "api",
                "n_tickets": len(tickets), "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    max_spend = float(os.environ.get("MAX_SPEND_USD", "1"))
    errors = 0
    with open(os.path.join(run_dir, "decisions.jsonl"), "w") as out:
        for i, t in enumerate(tickets):
            if jev.SPENT_USD > max_spend:
                print(f"spend cap ${max_spend} reached; stopping")
                break
            svc = OrdersService(fixture)
            row = {"run_id": a.run_id, "dataset": a.dataset, "config": a.config,
                   "ticket_id": t["ticket_id"], "expected": t["expected"]}
            try:
                action, _, _ = support.handle(t, i, svc, cfg)
                row.update(action=action, label=int(action == t["expected"]), error=None)
            except support.ItemError as e:
                errors += 1
                row.update(action=None, label=None, error=f"{e.stage}:{e.error_type}")
            out.write(json.dumps(row) + "\n")
    manifest.update(finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    errored=errors, spend_usd=round(jev.SPENT_USD, 6))
    json.dump(manifest, open(os.path.join(run_dir, "manifest.json"), "w"), indent=1)
    print(f"{a.run_id}: {len(tickets)} tickets, {errors} errored, spend ${jev.SPENT_USD:.4f}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
