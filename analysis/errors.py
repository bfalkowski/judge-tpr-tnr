"""Group a judge run's disagreements with the labels by the rule that decides the item.

  python analysis/errors.py runs/<run_id> [--threshold 0.5] [--call 1] [--examples 2]

This is the "inspect false passes and false fails" step of the loop. Each
item is described by the facts that decide it under the policy (status,
which side of the 14- or 30-day cutoff, the $500 limit, stock), the agent's
action and the required one. Writes runs/<run_id>/errors.json.
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from judge.policy import REFUND_LIMIT, days_ago  # noqa: E402


def deciding_facts(it):
    o, issue, stock = it["order"], it["issue"], it["stock"]
    s = o["status"]
    over = o["total"] > REFUND_LIMIT
    if s == "Processing":
        return "not shipped yet"
    if issue in ("damaged", "wrong_item"):
        if s != "Delivered":
            return f"{issue}, not delivered yet"
        d = days_ago(o["delivered_on"])
        return f"{issue}, delivered {'31+' if d > 30 else '<=30'} days ago" + (", over $500" if d <= 30 and over else "")
    if issue in ("not_arrived", "where_is_it"):
        if s == "Delivered":
            return "says not arrived, record says delivered"
        if s == "Shipped" and days_ago(o["shipped_on"]) <= 14:
            return "shipped <=14 days ago"
        where = "lost" if s == "Lost" else "shipped 15+ days ago"
        return f"{where}, {'in stock' if stock > 0 else 'out of stock'}" + (", over $500" if stock <= 0 and over else "")
    return issue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--threshold", type=float, default=None)
    ap.add_argument("--call", type=int, default=1)
    ap.add_argument("--examples", type=int, default=2)
    a = ap.parse_args()
    m = json.load(open(os.path.join(a.run_dir, "manifest.json")))
    t = a.threshold if a.threshold is not None else (m.get("frozen") or {}).get("threshold", 0.5)
    items = {json.loads(l)["item_id"]: json.loads(l) for l in open(data_path(m["dataset"]))}
    rows = [json.loads(l) for l in open(os.path.join(a.run_dir, "judgments.jsonl"))]
    rows = [r for r in rows if r["call"] == a.call and r["noul"] is not None]
    out = {}
    for kind, want_label, want_pred in (("false_pass", 0, 1), ("false_fail", 1, 0)):
        groups, examples = Counter(), defaultdict(list)
        for r in rows:
            it = items[r["item_id"]]
            if it["label"] == want_label and int(r["noul"] >= t) == want_pred:
                k = f"{deciding_facts(it)}: agent {it['action']}, policy {it['expected']}"
                groups[k] += 1
                examples[k].append({"item_id": it["item_id"], "framing": it["tag"], "noul": r["noul"],
                                    "ticket": it["ticket"]})
        out[kind] = [{"group": k, "n": n, "examples": examples[k][: a.examples]} for k, n in groups.most_common()]
    json.dump(out, open(os.path.join(a.run_dir, "errors.json"), "w"), indent=1)
    print(f"{m['run_id']} ({m['variant']}, {m['split']}, threshold {t})")
    for kind in ("false_pass", "false_fail"):
        print(f"{kind.replace('_', ' ')}: {sum(g['n'] for g in out[kind])}")
        for g in out[kind]:
            print(f"  {g['n']:3d}  {g['group']}")
            for e in g["examples"]:
                print(f"         [{e['framing']}, {e['noul']:.2f}] {e['ticket'][:100]}")


def data_path(dataset):
    return os.path.join(ROOT, "data", f"items_{dataset}.jsonl")


if __name__ == "__main__":
    main()
