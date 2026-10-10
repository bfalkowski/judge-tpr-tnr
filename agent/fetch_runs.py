"""Copy this repo's agent runs from the `data` branch into data/agent_runs/.

  git fetch origin data
  python agent/fetch_runs.py gh38078712356

Takes every runs/<prefix>-agent-*/ folder on the local `data` ref whose name
starts with the given prefix, checks the manifest (API backend, pinned
paper 2 commit, no errored tickets), and writes one file per dataset:
data/agent_runs/<prefix>_<dataset>.jsonl.
"""

import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P2_COMMIT = "12a0eef7c90b3b77b84953c81946398f2d1f84d7"


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, check=True).stdout


def main(prefix, ref="data"):
    names = [n for n in git("ls-tree", "--name-only", ref, "runs/").split()
             if n.startswith(f"runs/{prefix}-agent-")]
    if not names:
        sys.exit(f"no agent runs starting with {prefix} on {ref}")
    by_dataset = {}
    for n in sorted(names):
        m = json.loads(git("show", f"{ref}:{n}/manifest.json"))
        if m["backend"] != "api" or m["p2_commit"] != P2_COMMIT or m.get("errored"):
            sys.exit(f"{n}: not a clean API run of the pinned agent: {m}")
        rows = [json.loads(l) for l in git("show", f"{ref}:{n}/decisions.jsonl").splitlines() if l.strip()]
        if len(rows) != m["n_tickets"]:
            sys.exit(f"{n}: {len(rows)} decisions for {m['n_tickets']} tickets (spend cap?)")
        by_dataset.setdefault(m["dataset"], []).extend(rows)
        print(f"{n}: {len(rows)} decisions, config {m['config']}, spend ${m['spend_usd']}")
    for v, rows in by_dataset.items():
        out = os.path.join(ROOT, "data", "agent_runs", f"{prefix}_{v}.jsonl")
        with open(out, "w") as f:
            for r in rows:
                f.write(json.dumps(r, sort_keys=True) + "\n")
        print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main(sys.argv[1])
