"""Freeze a judge variant and threshold after tuning on dev.

  python freeze.py --variant p2 --threshold 0.5 --dev-run runs/<dev_run_id>

Writes freeze.json. run_judge.py only runs the test split for the variant
recorded here, with the same fingerprint. Commit freeze.json and tag the
commit (git tag freeze-<variant>) before running the test split, so the order
of events is on record.
"""

import argparse
import json
import os
import subprocess
import time

from judge import judges

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=sorted(judges.VARIANTS))
    ap.add_argument("--threshold", type=float, required=True)
    ap.add_argument("--dev-run", required=True, help="the dev run the threshold was chosen on")
    a = ap.parse_args()
    path = os.path.join(ROOT, "freeze.json")
    if os.path.exists(path):
        raise SystemExit("freeze.json already exists; a frozen judge is not re-frozen. "
                         "Delete it deliberately (and say so in the paper) to start over.")
    m = json.load(open(os.path.join(a.dev_run, "manifest.json")))
    if m["variant"] != a.variant or m["split"] != "dev":
        raise SystemExit(f"{a.dev_run} is a {m['split']} run of {m['variant']}, not a dev run of {a.variant}")
    if m["fingerprint"] != judges.fingerprint(a.variant):
        raise SystemExit("the variant changed since that dev run; rerun dev first")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    json.dump({"variant": a.variant, "fingerprint": judges.fingerprint(a.variant), "threshold": a.threshold,
               "dev_run": m["run_id"], "git_commit": commit,
               "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, open(path, "w"), indent=1)
    print(f"froze {a.variant} at threshold {a.threshold}; commit freeze.json and tag freeze-{a.variant}")


if __name__ == "__main__":
    main()
