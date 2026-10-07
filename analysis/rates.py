"""TPR and TNR for a judge run, with ticket-level intervals and a threshold sweep.

  python analysis/rates.py runs/<run_id> [--threshold 0.5] [--call 1]

A verdict is PASS when the raw `noul` value is >= the threshold. The sweep
shows how TPR and TNR trade off as the threshold moves; pick the threshold on
a dev run, never on a test run. Writes runs/<run_id>/rates.json.
"""

import argparse
import json
import os
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from judge.estimate import rates  # noqa: E402

SWEEP = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def load(run_dir, call):
    rows = [json.loads(line) for line in open(os.path.join(run_dir, "judgments.jsonl"))]
    errored = [r for r in rows if r["noul"] is None]
    return [r for r in rows if r["call"] == call and r["noul"] is not None], rows, errored


def rate_ci(rows, threshold, iterations=5000, seed=0, level=0.95):
    g = defaultdict(list)
    for r in rows:
        g[r["ticket_id"]].append(r)
    keys, rng, tprs, tnrs = list(g), random.Random(seed), [], []
    for _ in range(iterations):
        s = [r for _ in keys for r in g[rng.choice(keys)]]
        rr = rates([r["label"] for r in s], [int(r["noul"] >= threshold) for r in s])
        if rr["tpr"] is not None:
            tprs.append(rr["tpr"])
        if rr["tnr"] is not None:
            tnrs.append(rr["tnr"])
    a = (1 - level) / 2

    def ci(v):
        v.sort()
        return [v[int(a * (len(v) - 1))], v[int((1 - a) * (len(v) - 1))]] if v else None
    return ci(tprs), ci(tnrs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--threshold", type=float, default=None,
                    help="default: the frozen threshold for a test run, else 0.5")
    ap.add_argument("--call", type=int, default=1, help="which call's verdict to score")
    a = ap.parse_args()
    manifest = json.load(open(os.path.join(a.run_dir, "manifest.json")))
    if a.threshold is None:
        a.threshold = (manifest.get("frozen") or {}).get("threshold", 0.5)
    rows, all_rows, errored = load(a.run_dir, a.call)
    labels = [r["label"] for r in rows]
    r = rates(labels, [int(x["noul"] >= a.threshold) for x in rows])
    tpr_ci, tnr_ci = rate_ci(rows, a.threshold)
    sweep = []
    for t in SWEEP:
        s = rates(labels, [int(x["noul"] >= t) for x in rows])
        sweep.append({"threshold": t, "tpr": s["tpr"], "tnr": s["tnr"], "youden": s["youden"]})
    by_item = defaultdict(list)
    for x in all_rows:
        if x["noul"] is not None:
            by_item[x["item_id"]].append(int(x["noul"] >= a.threshold))
    multi = [v for v in by_item.values() if len(v) > 1]
    by_tag = defaultdict(Counter)
    items = {json.loads(l)["item_id"]: json.loads(l) for l in open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", f"items_{manifest['dataset']}.jsonl"))}
    for x in rows:
        p = int(x["noul"] >= a.threshold)
        k = "tp" if x["label"] and p else "fn" if x["label"] else "fp" if p else "tn"
        by_tag[items[x["item_id"]]["tag"]][k] += 1
    out = {"run_id": manifest["run_id"], "variant": manifest["variant"], "split": manifest["split"],
           "threshold": a.threshold, "call": a.call, **r, "tpr_ci": tpr_ci, "tnr_ci": tnr_ci,
           "tickets": len({x["ticket_id"] for x in rows}), "errored_calls": len(errored),
           "repeat_disagreement": (sum(len(set(v)) > 1 for v in multi) / len(multi)) if multi else None,
           "sweep": sweep, "by_tag": {k: dict(v) for k, v in sorted(by_tag.items())}}
    json.dump(out, open(os.path.join(a.run_dir, "rates.json"), "w"), indent=1)
    f = lambda v: "n/a" if v is None else f"{v:.3f}"
    fci = lambda c: "n/a" if not c else f"[{c[0]:.3f}, {c[1]:.3f}]"
    print(f"{out['run_id']} ({out['variant']}, {out['split']}, threshold {a.threshold}): "
          f"{r['n']} items from {out['tickets']} tickets, {len(errored)} errored calls")
    print(f"  TPR {f(r['tpr'])} {fci(tpr_ci)}   TNR {f(r['tnr'])} {fci(tnr_ci)}   "
          f"TPR + TNR - 1 = {f(r['youden'])}")
    print(f"  TP {r['tp']}  FN {r['fn']}  FP {r['fp']}  TN {r['tn']}")
    if out["repeat_disagreement"] is not None:
        print(f"  calls disagree on {100 * out['repeat_disagreement']:.1f}% of items")
    print("  threshold sweep: " + "  ".join(f"{s['threshold']}: {f(s['tpr'])}/{f(s['tnr'])}" for s in sweep))


if __name__ == "__main__":
    main()
