"""Build the correction batch: v4 items for the frozen judge to score as if unlabeled.

  python data/build_correction.py

Input: the agent's decisions on v4 in data/correction/*.jsonl (copied from the
`data` branch by agent/fetch_runs.py, then moved here so build_labeled.py never
reads them). v4 is in no train, dev or test split and no judge version was
built or tuned on it.

One item per distinct (ticket, action), as in the labeled set, so the judge
scores each distinct decision once. Labels are stored for the final comparison
only; the judge never sees them. Every ticket is in the "prod" split.

Writes data/items_v4.jsonl and data/splits/v4.json.
"""

import glob
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from judge import data  # noqa: E402


def main():
    decisions = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "correction", "*_v4.jsonl"))):
        decisions += [json.loads(l) for l in open(path)]
    decisions = [d for d in decisions if d.get("action")]
    tickets, fixture = data.load("v4")
    by_id = {t["ticket_id"]: t for t in tickets}
    groups = defaultdict(list)
    for d in decisions:
        groups[(d["ticket_id"], d["action"])].append(d)
    items = []
    for (tid, action), ds in sorted(groups.items()):
        t = by_id[tid]
        order = fixture["orders"][str(t["order_id"])]
        items.append({"item_id": f"v4:{tid}:{action}", "dataset": "v4", "ticket_id": tid, "tag": t["tag"],
                      "issue": t["issue"], "action": action, "label": int(action == t["expected"]),
                      "expected": t["expected"], "ticket": t["text"], "order": order,
                      "stock": fixture["stock"].get(order["sku"], 0),
                      "sources": dict(sorted(Counter(d["config"] for d in ds).items()))})
    with open(data.items_path("v4"), "w") as f:
        for it in items:
            f.write(json.dumps(it, sort_keys=True) + "\n")
    json.dump({"dataset": "v4", "counts": {"prod": len(tickets)},
               "tickets": {t["ticket_id"]: "prod" for t in tickets}}, open(data.split_path("v4"), "w"), indent=1)
    p = sum(it["label"] for it in items)
    print(f"{len(decisions)} decisions -> {len(items)} items ({p} pass, {len(items) - p} fail) from {len(tickets)} tickets")


if __name__ == "__main__":
    main()
