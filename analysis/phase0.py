"""Phase 0: TPR and TNR of the paper 2 judge, from data paper 2 already has.

  python analysis/phase0.py

Reads phase0/paper2_clean_items.jsonl (600 items: 60 tickets x 10 clean
runs). The reference is the deterministic score, which comes from the
reference policy. The judge's verdict is its first vote, as in paper 2.

Writes phase0/results.json and phase0/RESULTS.md. No API calls.
"""

import json
import os
import random
import statistics
import sys
from collections import Counter, defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from judge.estimate import corrected, estimate, rates  # noqa: E402

SRC = os.path.join(ROOT, "phase0", "paper2_clean_items.jsonl")
SPLITS = 2000


def load():
    rows = [json.loads(line) for line in open(SRC)]
    tags = {json.loads(l)["ticket_id"]: json.loads(l)["tag"] for l in open(os.path.join(ROOT, "data/v2/tickets.jsonl"))}
    for r in rows:
        r["label"], r["pred"], r["tag"] = int(r["correct"]), int(r["judge_votes"][0]), tags[r["ticket_id"]]
    return rows


def split_experiment(rows, n=SPLITS):
    """Label half the tickets, correct the judge's pass rate on the other half."""
    tickets = sorted({r["ticket_id"] for r in rows})
    raw_err, cor_err, denoms, undefined = [], [], [], 0
    for seed in range(n):
        rng = random.Random(seed)
        t = tickets[:]
        rng.shuffle(t)
        lab = set(t[: len(t) // 2])
        L = [r for r in rows if r["ticket_id"] in lab]
        U = [r for r in rows if r["ticket_id"] not in lab]
        rr = rates([r["label"] for r in L], [r["pred"] for r in L])
        p_obs = sum(r["pred"] for r in U) / len(U)
        truth = sum(r["label"] for r in U) / len(U)
        est = corrected(p_obs, rr["tpr"], rr["tnr"]) if rr["tnr"] is not None else None
        denoms.append(rr["youden"])
        raw_err.append(abs(p_obs - truth))
        if est is None:
            undefined += 1
        else:
            cor_err.append(abs(est - truth))
    q = lambda v: [round(x, 3) for x in statistics.quantiles(v, n=10)]
    return {"splits": n, "undefined": undefined, "undefined_share": undefined / n,
            "median_abs_error_raw": statistics.median(raw_err),
            "median_abs_error_corrected": statistics.median(cor_err),
            "corrected_worse_than_raw_share": sum(c > r for c, r in zip(cor_err, raw_err)) / len(cor_err),
            "corrected_error_deciles": q(cor_err), "denominator_deciles": q(denoms)}


def interval_coverage(rows, splits=200, iterations=2000):
    """How often a 95% interval for one run's pass rate contains the true rate.
    Each split labels half the tickets (all runs) and estimates the first clean
    run on the other half. Two intervals:
      ticket-level  resamples tickets on both sides; undefined resamples counted
      judgy 0.1.0   resamples items, holds p_obs fixed, drops undefined resamples"""
    try:
        import numpy as np
        from judgy import estimate_success_rate
    except ImportError:
        np = None
    tickets = sorted({r["ticket_id"] for r in rows})
    first_run = rows[0]["run_id"]
    acc = {"ticket": {"estimates": 0, "covered": 0, "widths": [], "undefined": []},
           "judgy": {"estimates": 0, "covered": 0, "widths": [], "dropped": []}}
    for seed in range(splits):
        rng = random.Random(10_000 + seed)
        t = tickets[:]
        rng.shuffle(t)
        lab = set(t[: len(t) // 2])
        L = [r for r in rows if r["ticket_id"] in lab]
        U = [r for r in rows if r["ticket_id"] not in lab and r["run_id"] == first_run]
        truth = sum(r["label"] for r in U) / len(U)
        e = estimate(L, U, iterations=iterations, seed=seed)
        a = acc["ticket"]
        a["undefined"].append(e["undefined_share"])
        if e["corrected"] is not None and e["ci"]:
            a["estimates"] += 1
            a["covered"] += e["ci"][0] <= truth <= e["ci"][1]
            a["widths"].append(e["ci"][1] - e["ci"][0])
        if np is None:
            continue
        yl = np.asarray([r["label"] for r in L])
        yp = np.asarray([r["pred"] for r in L])
        a = acc["judgy"]
        np.random.seed(seed)
        try:
            _, lo, hi = estimate_success_rate(yl, yp, [r["pred"] for r in U], bootstrap_iterations=iterations)
        except (ValueError, RuntimeError):
            continue
        a["estimates"] += 1
        a["covered"] += lo <= truth <= hi
        a["widths"].append(hi - lo)
        np.random.seed(seed)  # replay judgy's resamples to count the ones it dropped
        dropped = 0
        for _ in range(iterations):
            i = np.random.choice(len(yl), size=len(yl), replace=True)
            b, p = yl[i], yp[i]
            pos, neg = b.sum(), len(b) - b.sum()
            if pos == 0 or neg == 0 or ((b & p).sum() / pos + ((1 - b) & (1 - p)).sum() / neg - 1) <= 0:
                dropped += 1
        a["dropped"].append(dropped / iterations)
    out = {"splits": splits, "iterations": iterations, "labeled_tickets": len(tickets) // 2,
           "run_items": len(tickets) - len(tickets) // 2}
    for k, a in acc.items():
        if k == "judgy" and np is None:
            out[k] = "not installed"
            continue
        out[k] = {"estimates": a["estimates"], "no_estimate": splits - a["estimates"],
                  "coverage": a["covered"] / a["estimates"] if a["estimates"] else None,
                  "median_width": statistics.median(a["widths"]) if a["widths"] else None}
        key = "undefined" if k == "ticket" else "dropped"
        out[k][f"median_{key}_share"] = statistics.median(a[key]) if a[key] else None
    return out


def main():
    rows = load()
    first = rates([r["label"] for r in rows], [r["pred"] for r in rows])
    p_obs = sum(r["pred"] for r in rows) / len(rows)
    truth = sum(r["label"] for r in rows) / len(rows)

    votes_differ = sum(r["judge_votes"][0] != r["judge_votes"][1] for r in rows)
    any_wrong = [r for r in rows if any(int(v) != r["label"] for v in r["judge_votes"])]
    tickets = {r["ticket_id"] for r in rows}
    err_by_ticket = Counter(r["ticket_id"] for r in rows if r["pred"] != r["label"])
    runs = len({r["run_id"] for r in rows})
    by_tag = defaultdict(lambda: Counter())
    for r in rows:
        k = "tp" if r["label"] and r["pred"] else "fn" if r["label"] else "fp" if r["pred"] else "tn"
        by_tag[r["tag"]][k] += 1

    res = {
        "source": json.load(open(os.path.join(ROOT, "phase0", "SOURCE.json"))),
        "items": len(rows), "runs": runs, "tickets": len(tickets),
        "distinct_ticket_action_pairs": len({(r["ticket_id"], r["action"]) for r in rows}),
        "tickets_ever_wrong": len({r["ticket_id"] for r in rows if not r["label"]}),
        "first_vote": first, "true_pass_rate": truth, "judge_pass_rate": p_obs,
        "in_sample_corrected": corrected(p_obs, first["tpr"], first["tnr"]),
        "repeat": {"votes_differ": votes_differ, "votes_differ_share": votes_differ / len(rows),
                   "items_with_a_wrong_vote": len(any_wrong),
                   "of_those_votes_differ": sum(r["judge_votes"][0] != r["judge_votes"][1] for r in any_wrong)},
        "judge_errors_by_ticket": {"tickets_with_any_error": len(err_by_ticket),
                                   "tickets_wrong_every_run": sum(c == runs for c in err_by_ticket.values()),
                                   "counts": dict(err_by_ticket.most_common())},
        "by_tag": {t: dict(c) for t, c in sorted(by_tag.items())},
        "split_experiment": split_experiment(rows),
        "interval_coverage": interval_coverage(rows),
    }
    out = os.path.join(ROOT, "phase0")
    json.dump(res, open(os.path.join(out, "results.json"), "w"), indent=1)
    open(os.path.join(out, "RESULTS.md"), "w").write(report(res))
    print(report(res))


def pct(x):
    return f"{100 * x:.1f}%"


def report(r):
    f, s, ic = r["first_vote"], r["split_experiment"], r["interval_coverage"]
    lines = [
        "# Phase 0 results (generated by analysis/phase0.py)",
        "",
        f"Source: {r['items']} items from {r['runs']} clean paper 2 runs ({r['tickets']} tickets), "
        f"`data` branch at `{r['source']['data_commit'][:7]}`. Reference: deterministic score. "
        "Judge verdict: first vote.",
        "",
        "## Confusion matrix",
        "",
        "| | Judge PASS | Judge FAIL |",
        "|---|---|---|",
        f"| Correct ({f['tp'] + f['fn']}) | {f['tp']} | {f['fn']} |",
        f"| Wrong ({f['fp'] + f['tn']}) | {f['fp']} | {f['tn']} |",
        "",
        f"TPR {f['tpr']:.3f}, TNR {f['tnr']:.3f}, TPR + TNR - 1 = {f['youden']:.3f}. "
        f"True pass rate {pct(r['true_pass_rate'])}, judge pass rate {pct(r['judge_pass_rate'])}.",
        "",
        f"Applying the correction to the same items it was measured on gives "
        f"{pct(r['in_sample_corrected'])}, which equals the true rate by algebra. It is not a result.",
        "",
        "## The 600 items are not independent",
        "",
        f"{r['distinct_ticket_action_pairs']} distinct (ticket, action) pairs. "
        f"{r['tickets_ever_wrong']} tickets are ever wrong. Judge errors fall on "
        f"{r['judge_errors_by_ticket']['tickets_with_any_error']} tickets, "
        f"{r['judge_errors_by_ticket']['tickets_wrong_every_run']} of them in every run.",
        "",
        "## Repeat agreement",
        "",
        f"The two votes differ on {r['repeat']['votes_differ']} items ({pct(r['repeat']['votes_differ_share'])}). "
        f"Of the {r['repeat']['items_with_a_wrong_vote']} items with at least one wrong vote, they differ on "
        f"{r['repeat']['of_those_votes_differ']}.",
        "",
        "## Correcting on held-out tickets",
        "",
        f"{s['splits']} random splits: TPR and TNR measured on half the tickets (all 10 runs), "
        "the judge's pass rate corrected on the other half.",
        "",
        f"- Correction undefined (TPR + TNR <= 1): {s['undefined']} splits ({pct(s['undefined_share'])}).",
        f"- Median error of the raw judge pass rate: {s['median_abs_error_raw'] * 100:.1f} points.",
        f"- Median error of the corrected rate, where defined: {s['median_abs_error_corrected'] * 100:.1f} points.",
        f"- Corrected rate further from the truth than the raw rate: {pct(s['corrected_worse_than_raw_share'])} of defined splits.",
        f"- TPR + TNR - 1 deciles: {s['denominator_deciles']}.",
        "",
        "## Does a 95% interval for one run contain the true rate?",
        "",
        f"{ic['splits']} splits. Each labels {ic['labeled_tickets']} tickets (all runs) and estimates one clean "
        f"run on the other {ic['run_items']} tickets. Intervals use {ic['iterations']} resamples.",
        "",
        "| Interval | Splits with an estimate | Coverage of the true rate | Median width | Median share of resamples undefined or dropped |",
        "|---|---|---|---|---|",
    ]
    for name, key, label in (("ticket", "median_undefined_share", "Ticket-level (this repo)"),
                             ("judgy", "median_dropped_share", "judgy 0.1.0 (item-level, dropped silently)")):
        a = ic[name]
        if not isinstance(a, dict):
            lines.append(f"| {label} | {a} | | | |")
            continue
        cov = pct(a["coverage"]) if a["coverage"] is not None else "n/a"
        wid = f"{a['median_width'] * 100:.0f} points" if a["median_width"] is not None else "n/a"
        lines.append(f"| {label} | {a['estimates']} of {ic['splits']} | {cov} | {wid} | {pct(a[key])} |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
