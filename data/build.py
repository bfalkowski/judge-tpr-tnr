"""Build the judge items and the ticket-level split for a dataset.

  python data/build.py v2

Writes data/items_<v>.jsonl and data/splits/<v>.json. Checks the dataset
files against data/CHECKSUMS.json first, so a changed ticket or fixture
fails loudly instead of quietly changing the labels.

Split plan (see README, "Why the test split is new tickets"):
  v2   train 15% / dev 85%. Every v2 ticket was already seen in phase 0 and in
       paper 2, so none of them can serve as unseen test data.
  v3   test 100%. New tickets, written and frozen before any judge sees them.
  v5   climb_train 30% / climb_test 30% / holdout 40%, for hillclimb/: the
       hill climber reads climb_train, scores climb_train and climb_test every
       round, and never sees holdout.
Within a dataset the split is stratified by the ticket's difficulty tag and
uses largest-remainder rounding, with a fixed seed.
"""

import hashlib
import json
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from judge import data  # noqa: E402

PLAN = {"v2": {"train": 0.15, "dev": 0.85}, "v3": {"test": 1.0},
        # the hill-climbing study (hillclimb/DESIGN.md): the agent is climbed, not the judge
        "v5": {"climb_train": 0.30, "climb_test": 0.30, "holdout": 0.40}}
SEED = 20261007


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def check_checksums(version):
    want = json.load(open(os.path.join(data.DATA, "CHECKSUMS.json")))
    for name in ("tickets.jsonl", "orders.json"):
        key = f"{version}/{name}"
        got = sha256(os.path.join(data.DATA, version, name))
        if want.get(key) != got:
            raise SystemExit(f"checksum mismatch for data/{key}: {got}")


def allocate(n, fracs):
    """Largest-remainder rounding of n into the given fractions."""
    raw = {k: n * f for k, f in fracs.items()}
    out = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - out[k], reverse=True)[: n - sum(out.values())]:
        out[k] += 1
    return out


def make_split(version, fracs, seed=SEED):
    tickets, _ = data.load(version)
    by_tag = defaultdict(list)
    for t in tickets:
        by_tag[t["tag"]].append(t["ticket_id"])
    totals = allocate(len(tickets), fracs)
    # allocate within tags, then fix up so split totals match the overall target
    rng = random.Random(seed)
    assignment, counts = {}, defaultdict(int)
    for tag in sorted(by_tag):
        ids = sorted(by_tag[tag])
        rng.shuffle(ids)
        n = allocate(len(ids), fracs)
        i = 0
        for split in fracs:
            for tid in ids[i:i + n[split]]:
                assignment[tid] = split
                counts[split] += 1
            i += n[split]
    for split in fracs:  # move tickets between splits if per-tag rounding drifted
        while counts[split] > totals[split]:
            short = next(s for s in fracs if counts[s] < totals[s])
            tid = sorted(t for t, s in assignment.items() if s == split)[0]
            assignment[tid], counts[split], counts[short] = short, counts[split] - 1, counts[short] + 1
    return {"dataset": version, "seed": seed, "fractions": fracs,
            "counts": dict(sorted(counts.items())), "tickets": dict(sorted(assignment.items()))}


def main(version):
    check_checksums(version)
    items = data.build_items(version)
    with open(data.items_path(version), "w") as f:
        for it in items:
            f.write(json.dumps(it, sort_keys=True) + "\n")
    os.makedirs(os.path.dirname(data.split_path(version)), exist_ok=True)
    split = make_split(version, PLAN[version])
    json.dump(split, open(data.split_path(version), "w"), indent=1)
    pos = sum(it["label"] for it in items)
    print(f"{version}: {len(items)} items ({pos} pass, {len(items) - pos} fail) "
          f"from {len(items) // 4} tickets; split {split['counts']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v2")
