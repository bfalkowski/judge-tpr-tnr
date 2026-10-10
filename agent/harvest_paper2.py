"""Copy paper 2's agent decisions on v2 into data/agent_runs/paper2_v2.jsonl.

  python agent/harvest_paper2.py [/path/to/eval-run-validity]

Reads every run on eval-run-validity's `data` branch (pinned commit) whose
agent decisions were not touched by a fault: clean runs, the declared
control, the config changes (context_strip, prompt_edit, template_edit,
missing_env), environment drift (dep_drift, python_drift, wrong_commit) and
judge faults, which leave the agent alone. Infrastructure, data and harness
faults are excluded, as are errored items and the run made before the final
policy wording (gh37011788500).
"""

import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REPO = "https://github.com/bfalkowski/eval-run-validity"
DATA_COMMIT = "da1d6ae7a77f64d4c7cdc6a43d47b1eb08e02038"
KEEP = re.compile(r"^runs/(gh\d+)-v2-(clean|control|context_strip|prompt_edit|template_edit|judge_\w+)"
                  r"-(loud|silent)-(none|dep_drift|python_drift|wrong_commit|missing_env)(-r\d+)?$")
EXCLUDE = {"gh37011788500"}
OUT = os.path.join(ROOT, "data", "agent_runs", "paper2_v2.jsonl")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def main(repo=None):
    if repo is None:
        repo = os.path.join(tempfile.mkdtemp(), "p2")
        subprocess.run(["git", "clone", "--quiet", "--no-checkout", "--filter=blob:none", REPO, repo], check=True)
    git(repo, "fetch", "--quiet", "origin", DATA_COMMIT)
    names = git(repo, "ls-tree", "--name-only", DATA_COMMIT, "runs/").split()
    expected = {json.loads(l)["ticket_id"]: json.loads(l)["expected"]
                for l in open(os.path.join(ROOT, "data", "v2", "tickets.jsonl"))}
    rows, runs = [], 0
    for n in sorted(names):
        m = KEEP.match(n)
        if not m or m.group(1) in EXCLUDE:
            continue
        try:
            txt = git(repo, "show", f"{DATA_COMMIT}:{n}/items.jsonl")
        except subprocess.CalledProcessError:
            continue
        runs += 1
        config = f"{m.group(2)}-{m.group(3)}-{m.group(4)}"
        for line in txt.splitlines():
            r = json.loads(line)
            if r.get("errored") or not r.get("action"):
                continue
            rows.append({"run_id": r["run_id"], "dataset": "v2", "config": config, "ticket_id": r["ticket_id"],
                         "expected": expected[r["ticket_id"]], "action": r["action"],
                         "label": int(r["action"] == expected[r["ticket_id"]]), "error": None})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"{len(rows)} decisions from {runs} paper 2 runs -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
