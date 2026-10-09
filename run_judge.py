"""Run one judge variant over one split of the judge items.

  JEV_BACKEND=stub python run_judge.py --variant p2 --dataset v2 --split dev --run-id stub-dev
  python run_judge.py --variant p2 --dataset v2 --split dev --run-id p2-dev-01

Writes runs/<run_id>/manifest.json and runs/<run_id>/judgments.jsonl, one row
per item per call with the raw `noul` value. The verdict threshold is not
applied here; analysis applies it, so a threshold can be chosen on dev without
calling Jev again.

The test split only runs for a variant frozen in freeze.json, with the same
fingerprint. That keeps test labels out of the loop while the judge is tuned.

Environment:
  TYPESAFE_API_KEY  Jev key (not needed with JEV_BACKEND=stub)
  JEV_BACKEND       "stub" for the local stand-in
  MAX_SPEND_USD     stop (partial run) once Jev spend passes this; default 1
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

from judge import data, jev, judges

ROOT = os.path.dirname(os.path.abspath(__file__))


def load_dotenv(path=os.path.join(ROOT, ".env")):
    if os.path.exists(path):
        for line in open(path):
            k, sep, v = line.strip().partition("=")
            if sep and not k.startswith("#"):
                os.environ.setdefault(k.strip(), v.strip())


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def check_frozen(variant):
    path = os.path.join(ROOT, "freeze.json")
    if not os.path.exists(path):
        sys.exit("refusing to run on the test split: no freeze.json (freeze a variant on dev first)")
    frozen = json.load(open(path))
    fp = judges.fingerprint(variant)
    if frozen.get("variant") != variant or frozen.get("fingerprint") != fp:
        sys.exit(f"refusing to run on the test split: {variant} ({fp}) is not the frozen judge "
                 f"({frozen.get('variant')}, {frozen.get('fingerprint')})")
    return frozen


def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="p2", choices=sorted(judges.VARIANTS))
    ap.add_argument("--dataset", default="v2")
    ap.add_argument("--split", required=True, choices=["train", "dev", "test", "all"])
    ap.add_argument("--repeats", type=int, default=2, help="calls per item (paper 2 used 2)")
    ap.add_argument("--run-id", default=time.strftime("run-%Y%m%d-%H%M%S"))
    ap.add_argument("--limit", type=int, default=None, help="first N items only (smoke tests)")
    ap.add_argument("--out", default=os.path.join(ROOT, "runs"))
    a = ap.parse_args()

    if os.environ.get("JEV_BACKEND") != "stub" and not os.environ.get("TYPESAFE_API_KEY"):
        sys.exit("TYPESAFE_API_KEY is not set: add it to .env, or as a repository secret for the "
                 "judge workflow, or use JEV_BACKEND=stub")
    frozen = check_frozen(a.variant) if a.split == "test" else None
    if a.split == "all" and "test" in set(data.load_split(a.dataset).values()):
        sys.exit("--split all would include test tickets; run the splits separately")
    items = data.load_items(a.dataset) if a.split == "all" else data.items_for(a.dataset, a.split)
    if a.limit:
        items = items[: a.limit]
    if not items:
        sys.exit(f"no items in {a.dataset}/{a.split}")

    run_dir = os.path.join(a.out, a.run_id)
    if os.path.exists(os.path.join(run_dir, "judgments.jsonl")):
        sys.exit(f"{run_dir} already has results; pick a new --run-id")
    os.makedirs(run_dir, exist_ok=True)
    manifest = {
        "run_id": a.run_id, "variant": a.variant, "fingerprint": judges.fingerprint(a.variant),
        "model": jev.model(), "backend": os.environ.get("JEV_BACKEND") or "api",
        "dataset": a.dataset, "split": a.split, "repeats": a.repeats, "n_items": len(items),
        "items_sha256": hashlib.sha256(open(data.items_path(a.dataset), "rb").read()).hexdigest(),
        "split_sha256": hashlib.sha256(open(data.split_path(a.dataset), "rb").read()).hexdigest(),
        "git_commit": git_commit(), "frozen": frozen,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    json.dump(manifest, open(os.path.join(run_dir, "manifest.json"), "w"), indent=1)

    max_spend = float(os.environ.get("MAX_SPEND_USD", "1"))
    errors = 0
    with open(os.path.join(run_dir, "judgments.jsonl"), "w") as out:
        for it in items:
            if jev.SPENT_USD > max_spend:
                print(f"spend cap ${max_spend} reached; stopping")
                break
            for call in range(1, a.repeats + 1):
                row = {"run_id": a.run_id, "item_id": it["item_id"], "ticket_id": it["ticket_id"],
                       "action": it["action"], "label": it["label"], "call": call}
                try:
                    noul, meta = judges.ask(a.variant, it)
                    row.update(noul=noul, error=None, **meta)
                except jev.JevCallError as e:
                    errors += 1
                    row.update(noul=None, error=e.error_type)
                out.write(json.dumps(row) + "\n")
                out.flush()
    manifest.update(finished_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    errored_calls=errors, spend_usd=round(jev.SPENT_USD, 6))
    json.dump(manifest, open(os.path.join(run_dir, "manifest.json"), "w"), indent=1)
    print(f"{a.run_id}: {len(items)} items x {a.repeats} calls, {errors} errored, "
          f"spend ${jev.SPENT_USD:.4f}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
