"""Build the labeled set the judge is developed and tested on.

  python data/build_labeled.py

Input: the agent's real decisions in data/agent_runs/*.jsonl (paper 2's runs
on v2, harvested by agent/harvest_paper2.py, and this repo's runs on v3,
copied from the `data` branch by agent/fetch_runs.py).

One labeled item per distinct (ticket, action) the agent produced. The judge's
input for an item is fully determined by the ticket, its order and stock, and
the action, so repeated decisions add no new information; the number of times
the agent made each decision, and under which configs, is kept in `sources`.
Label: PASS when the action is the one the reference policy gives.

Split by ticket, never by item:
  train  every v2 ticket. v2 has been looked at closely (paper 2, phase 0, the
         first dev run), so it is only used as a pool of few-shot examples.
  dev    half of the v3 tickets
  test   the other half, held out until a judge is frozen
v3 tickets are split 50/50 within each (framing, has-a-failure) group, with a
fixed seed, so dev and test get similar mixes of framings and failures.

Writes data/items_labeled.jsonl and data/splits/labeled.json.
"""

import glob
import json
import os
import random
import sys
from collections import Counter, defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from judge import data  # noqa: E402

SEED = 20261010


def main():
    decisions = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "agent_runs", "*.jsonl"))):
        decisions += [json.loads(l) for l in open(path)]
    decisions = [d for d in decisions if d.get("action")]
    fixtures, tickets = {}, {}
    for v in sorted({d["dataset"] for d in decisions}):
        ts, fx = data.load(v)
        fixtures[v] = fx
        for t in ts:
            tickets[(v, t["ticket_id"])] = t

    groups = defaultdict(list)
    for d in decisions:
        groups[(d["dataset"], d["ticket_id"], d["action"])].append(d)
    items = []
    for (v, tid, action), ds in sorted(groups.items()):
        t = tickets[(v, tid)]
        order = fixtures[v]["orders"][str(t["order_id"])]
        stock = fixtures[v]["stock"].get(order["sku"], 0)
        label = int(action == t["expected"])
        assert all(d["label"] == label for d in ds), (v, tid, action)
        items.append({"item_id": f"{v}:{tid}:{action}", "dataset": v, "ticket_id": tid, "tag": t["tag"],
                      "issue": t["issue"], "action": action, "label": label, "expected": t["expected"],
                      "ticket": t["text"], "order": order, "stock": stock,
                      "sources": dict(sorted(Counter(d["config"] for d in ds).items()))})

    split = {}
    for (v, tid) in tickets:
        if v == "v2":
            split[tid] = "train"
    has_fail = {it["ticket_id"] for it in items if it["label"] == 0}
    strata = defaultdict(list)
    for (v, tid), t in sorted(tickets.items()):
        if v == "v3":
            strata[(t["tag"], tid in has_fail)].append(tid)
    rng = random.Random(SEED)
    for key in sorted(strata):
        ids = sorted(strata[key])
        rng.shuffle(ids)
        half = len(ids) // 2 + (rng.random() < 0.5 if len(ids) % 2 else 0)
        for tid in ids[:half]:
            split[tid] = "dev"
        for tid in ids[half:]:
            split[tid] = "test"

    with open(data.items_path("labeled"), "w") as f:
        for it in items:
            f.write(json.dumps(it, sort_keys=True) + "\n")
    os.makedirs(os.path.dirname(data.split_path("labeled")), exist_ok=True)
    counts = Counter(split.values())
    json.dump({"dataset": "labeled", "seed": SEED, "counts": dict(sorted(counts.items())),
               "tickets": dict(sorted(split.items()))}, open(data.split_path("labeled"), "w"), indent=1)

    print(f"{len(decisions)} decisions -> {len(items)} labeled items")
    print(f"{'split':<6} {'tickets':>7} {'items':>6} {'pass':>5} {'fail':>5}")
    for s in ("train", "dev", "test"):
        its = [it for it in items if split.get(it["ticket_id"]) == s]
        p = sum(it["label"] for it in its)
        print(f"{s:<6} {counts[s]:>7} {len(its):>6} {p:>5} {len(its) - p:>5}")


if __name__ == "__main__":
    main()
