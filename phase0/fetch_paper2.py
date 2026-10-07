"""Copy the paper 2 judge's votes on the 10 clean runs into this repo.

  python phase0/fetch_paper2.py                     # clones eval-run-validity
  python phase0/fetch_paper2.py /path/to/eval-run-validity

Reads items.jsonl from the 10 clean runs listed in paper 2's Appendix A, from
the `data` branch at a pinned commit, and writes phase0/paper2_clean_items.jsonl
(600 rows). These are the items behind paper 2's "judge wrong on 24.5%" figure.
Each row has the deterministic outcome (`correct`) and both judge votes
(`judge_votes`, thresholded at 0.5; paper 2 did not keep the raw score).
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile

REPO = "https://github.com/bfalkowski/eval-run-validity"
DATA_COMMIT = "da1d6ae7a77f64d4c7cdc6a43d47b1eb08e02038"  # `data` branch, 2026-10-07
CLEAN_RUNS = [  # paper 2, Appendix A: the ten clean runs used in its analysis
    "gh37012503737-v2-clean-loud-none",
    "gh37014038090-v2-clean-loud-none-r1",
    "gh37014038090-v2-clean-loud-none-r2",
    "gh37014038090-v2-clean-loud-none-r3",
    "gh37014038090-v2-clean-loud-none-r4",
    "gh37014038090-v2-clean-loud-none-r5",
    "gh37014574123-v2-clean-loud-none-r1",
    "gh37014574123-v2-clean-loud-none-r2",
    "gh37019134878-v2-clean-loud-none-r3",
    "gh37019134878-v2-clean-loud-none-r4",
]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "paper2_clean_items.jsonl")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def main(repo=None):
    tmp = None
    if repo is None:
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "eval-run-validity")
        subprocess.run(["git", "clone", "--quiet", "--no-checkout", "--filter=blob:none", REPO, repo], check=True)
    git(repo, "fetch", "--quiet", "origin", DATA_COMMIT)
    rows = []
    for run in CLEAN_RUNS:
        for line in git(repo, "show", f"{DATA_COMMIT}:runs/{run}/items.jsonl").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    if len(rows) != 600:
        sys.exit(f"expected 600 items, got {len(rows)}")
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    digest = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    json.dump({"repo": REPO, "data_commit": DATA_COMMIT, "runs": CLEAN_RUNS, "rows": len(rows),
               "sha256": digest}, open(os.path.join(HERE, "SOURCE.json"), "w"), indent=1)
    print(f"wrote {len(rows)} rows to {OUT} (sha256 {digest[:12]})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
