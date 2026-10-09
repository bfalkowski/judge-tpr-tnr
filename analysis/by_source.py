"""Split a judge run's TNR by where the wrong resolution comes from.

  python analysis/by_source.py runs/<run_id> [--threshold 0.5]

A FAIL item is either a mistake the paper 2 agent actually made (the
(ticket, action) pair appears as wrong in phase0/paper2_clean_items.jsonl) or
one of the other wrong actions that the all-actions build adds. TNR on the two
groups answers whether the all-actions items are a fair stand-in for real
failures. Items are weighted by how often the agent made that mistake in the
10 clean runs, as well as counted once per distinct pair.
"""

import argparse
import json
import os
from collections import Counter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--call", type=int, default=1)
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(os.path.join(a.run_dir, "judgments.jsonl"))]
    rows = [r for r in rows if r["call"] == a.call and r["noul"] is not None]
    pred = {(r["ticket_id"], r["action"]): int(r["noul"] >= a.threshold) for r in rows}
    noul = {(r["ticket_id"], r["action"]): r["noul"] for r in rows}
    label = {(r["ticket_id"], r["action"]): r["label"] for r in rows}
    p0 = [json.loads(l) for l in open(os.path.join(ROOT, "phase0", "paper2_clean_items.jsonl"))]
    agent_wrong = Counter((r["ticket_id"], r["action"]) for r in p0 if not r["correct"])

    real = [k for k in pred if k in agent_wrong]
    other = [k for k in pred if label[k] == 0 and k not in agent_wrong]
    weighted_n = sum(agent_wrong[k] for k in real)
    weighted_fail = sum(agent_wrong[k] * (1 - pred[k]) for k in real)
    out = {
        "run_dir": a.run_dir, "threshold": a.threshold, "call": a.call,
        "agent_mistakes": {"pairs": len(real), "tnr_pairs": sum(1 - pred[k] for k in real) / len(real) if real else None,
                           "weighted_items": weighted_n,
                           "tnr_weighted": weighted_fail / weighted_n if weighted_n else None,
                           "detail": [{"ticket_id": k[0], "action": k[1], "runs_wrong": agent_wrong[k],
                                       "noul": noul[k]} for k in sorted(real)]},
        "other_wrong_actions": {"pairs": len(other),
                                "tnr": sum(1 - pred[k] for k in other) / len(other) if other else None},
    }
    json.dump(out, open(os.path.join(a.run_dir, "by_source.json"), "w"), indent=1)
    m, o = out["agent_mistakes"], out["other_wrong_actions"]
    print(f"threshold {a.threshold}, call {a.call}")
    if real:
        print(f"  agent's own mistakes: {m['pairs']} pairs, TNR {m['tnr_pairs']:.3f} "
              f"({m['weighted_items']} items weighted by runs: TNR {m['tnr_weighted']:.3f})")
    print(f"  other wrong actions:  {o['pairs']} pairs, TNR {o['tnr']:.3f}")
    for d in m["detail"]:
        print(f"    {d['ticket_id']} {d['action']:<8} wrong in {d['runs_wrong']:>2} of 10 runs, noul {d['noul']:.2f}")


if __name__ == "__main__":
    main()
