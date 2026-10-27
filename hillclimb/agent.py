"""Run one version of the support agent on every v5 ticket, for the hill-climbing study.

  P2_DIR=p2 python hillclimb/agent.py --artifact hillclimb/baseline_agent.json --reps 2 --run-id climb-baseline

The agent is paper 2's (eval-run-validity at the pinned commit), imported
unchanged and run in its `clean` config. The only things a version changes
are the two parts of the artifact the hill climber may edit: the decision
instructions and the four action descriptions (hillclimb/DESIGN.md).

Each (ticket, rep) is one decision. Jev's answer, including its confidence,
is recorded through a thin wrapper around paper 2's `jev.ask`; the agent code
itself is not modified. Labels are not written here: the run records only what
the agent did, and hillclimb/score.py grades it.

Writes runs/<run_id>/manifest.json, decisions.jsonl and artifact.json.
"""

import argparse
import hashlib
import json
import os
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "agent"))
from run_agent import load_p2, make_cfg  # noqa: E402  (agent/run_agent.py: pinned paper 2 import)

DATASET = "v5"


def load_artifact(path, support):
    art = json.load(open(path))
    if set(art) != {"decision_instructions", "criteria"}:
        sys.exit(f"{path}: expected keys decision_instructions and criteria, got {sorted(art)}")
    if not isinstance(art["decision_instructions"], str) or not art["decision_instructions"].strip():
        sys.exit(f"{path}: decision_instructions must be a non-empty string")
    crit = art["criteria"]
    if set(crit) != set(support.CRITERIA):
        sys.exit(f"{path}: criteria keys must be {sorted(support.CRITERIA)}")
    for k, v in crit.items():
        want = support.KEY_TO_ACTION[k] + ":"
        if not isinstance(v, str) or not v.startswith(want):
            sys.exit(f"{path}: criteria[{k}] must start with {want!r}")
    return art


def fingerprint(art):
    return hashlib.sha256(json.dumps(art, sort_keys=True).encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "runs"))
    a = ap.parse_args()
    if os.environ.get("JEV_BACKEND") != "stub" and not os.environ.get("TYPESAFE_API_KEY"):
        sys.exit("TYPESAFE_API_KEY is not set (or use JEV_BACKEND=stub)")
    jev, support, OrdersService, POLICIES = load_p2(os.environ.get("P2_DIR", os.path.join(ROOT, "p2")))
    art = load_artifact(a.artifact, support)

    from judge import data
    tickets, fixture = data.load(DATASET)
    if a.limit:
        tickets = tickets[: a.limit]
    cfg = make_cfg("clean", support, POLICIES)
    cfg["decision_instructions"] = art["decision_instructions"]
    support.CRITERIA = dict(art["criteria"])  # handle() reads the module global when it builds the question

    last = {}
    real_ask = jev.ask

    def recording_ask(state, question_name, question, **kw):
        ans, meta = real_ask(state, question_name, question, **kw)
        last.update(answer=ans, meta=meta)
        return ans, meta
    jev.ask = recording_ask

    run_dir = os.path.join(a.out, a.run_id)
    if os.path.exists(os.path.join(run_dir, "decisions.jsonl")):
        sys.exit(f"{run_dir} already has results")
    os.makedirs(run_dir, exist_ok=True)
    json.dump(art, open(os.path.join(run_dir, "artifact.json"), "w"), indent=1)
    manifest = {"run_id": a.run_id, "dataset": DATASET, "config": "clean", "reps": a.reps,
                "artifact_fingerprint": fingerprint(art), "artifact_path": a.artifact,
                "model": jev.model(), "backend": os.environ.get("JEV_BACKEND") or "api",
                "n_tickets": len(tickets), "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    max_spend = float(os.environ.get("MAX_SPEND_USD", "0.3"))
    errors, stopped = 0, False
    with open(os.path.join(run_dir, "decisions.jsonl"), "w") as out:
        for rep in range(a.reps):
            for i, t in enumerate(tickets):
                if jev.SPENT_USD > max_spend:
                    print(f"spend cap ${max_spend} reached; stopping")
                    stopped = True
                    break
                last.clear()
                row = {"run_id": a.run_id, "ticket_id": t["ticket_id"], "rep": rep}
                try:
                    action, _, _ = support.handle(t, rep * len(tickets) + i, OrdersService(fixture), cfg)
                    ans, meta = last.get("answer") or {}, last.get("meta") or {}
                    row.update(action=action, confidence=ans.get("confidence"),
                               input_tokens=meta.get("input_tokens"), cost_usd=meta.get("cost_usd"),
                               latency_s=meta.get("latency_s"), error=None)
                except support.ItemError as e:
                    errors += 1
                    row.update(action=None, error=f"{e.stage}:{e.error_type}")
                out.write(json.dumps(row) + "\n")
            if stopped:
                break
    manifest.update(finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), errored=errors,
                    stopped_at_spend_cap=stopped, spend_usd=round(jev.SPENT_USD, 6))
    json.dump(manifest, open(os.path.join(run_dir, "manifest.json"), "w"), indent=1)
    print(f"{a.run_id}: {len(tickets)} tickets x {a.reps} reps, {errors} errored, spend ${jev.SPENT_USD:.4f}")
    sys.exit(1 if errors or stopped else 0)


if __name__ == "__main__":
    main()
