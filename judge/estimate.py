"""TPR, TNR and the corrected pass rate, with ticket-level bootstrap intervals.

Convention (as in the course and in judgy): PASS is the positive class.
  TPR = P(judge PASS | truly PASS)
  TNR = P(judge FAIL | truly FAIL)
  corrected = (p_obs + TNR - 1) / (TPR + TNR - 1), clipped to [0, 1]
p_obs is the judge's pass rate on the run being estimated.

The correction is undefined when TPR + TNR <= 1, and it amplifies every error
in p_obs, TPR and TNR by 1 / (TPR + TNR - 1). That denominator is reported
with every estimate.

Why not judgy's interval as is (judgy 0.1.0, estimate_success_rate):
  1. it resamples items, but items here come in clusters (four per ticket,
     and the same ticket in every agent run), so it understates uncertainty;
  2. it holds p_obs fixed, so sampling error in the run being estimated is
     left out;
  3. it drops resamples where TPR + TNR <= 1 without saying how many, which
     narrows the interval most exactly when the judge is weakest.
This module resamples tickets in both the labeled set and the run, and reports
the share of resamples where the correction was undefined. judgy's point
estimate is used as a cross-check (tests/test_estimate.py).
"""

import random
from collections import defaultdict


def confusion(labels, preds):
    tp = fn = fp = tn = 0
    for y, p in zip(labels, preds):
        if y and p:
            tp += 1
        elif y:
            fn += 1
        elif p:
            fp += 1
        else:
            tn += 1
    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn}


def rates(labels, preds):
    c = confusion(labels, preds)
    pos, neg = c["tp"] + c["fn"], c["tn"] + c["fp"]
    tpr = c["tp"] / pos if pos else None
    tnr = c["tn"] / neg if neg else None
    return {**c, "n": pos + neg, "tpr": tpr, "tnr": tnr,
            "youden": None if tpr is None or tnr is None else tpr + tnr - 1}


def corrected(p_obs, tpr, tnr):
    """Clipped corrected pass rate, or None when TPR + TNR <= 1."""
    d = tpr + tnr - 1
    if d <= 0:
        return None
    return min(max((p_obs + tnr - 1) / d, 0.0), 1.0)


def _by_ticket(rows):
    g = defaultdict(list)
    for r in rows:
        g[r["ticket_id"]].append(r)
    return g


def _resample(groups, rng):
    keys = list(groups)
    out = []
    for _ in keys:
        out.extend(groups[rng.choice(keys)])
    return out


def estimate(labeled, run, iterations=10000, seed=0, level=0.95):
    """labeled: rows with ticket_id, label (0/1), pred (0/1).
    run: rows with ticket_id, pred (0/1), and optionally label (true outcome,
    for checking the estimate where truth is known).
    Returns point estimates and a ticket-level percentile interval."""
    r = rates([x["label"] for x in labeled], [x["pred"] for x in labeled])
    p_obs = sum(x["pred"] for x in run) / len(run)
    out = {"tpr": r["tpr"], "tnr": r["tnr"], "denominator": r["youden"], "p_obs": p_obs,
           "corrected": corrected(p_obs, r["tpr"], r["tnr"]) if r["youden"] is not None else None,
           "n_labeled": len(labeled), "n_labeled_tickets": len({x["ticket_id"] for x in labeled}),
           "n_run": len(run), "n_run_tickets": len({x["ticket_id"] for x in run})}
    if all("label" in x for x in run):
        out["true_rate"] = sum(x["label"] for x in run) / len(run)
    lab_g, run_g = _by_ticket(labeled), _by_ticket(run)
    rng = random.Random(seed)
    boot, undefined = [], 0
    for _ in range(iterations):
        L, U = _resample(lab_g, rng), _resample(run_g, rng)
        rr = rates([x["label"] for x in L], [x["pred"] for x in L])
        if rr["tpr"] is None or rr["tnr"] is None:
            undefined += 1
            continue
        est = corrected(sum(x["pred"] for x in U) / len(U), rr["tpr"], rr["tnr"])
        if est is None:
            undefined += 1
        else:
            boot.append(est)
    out["undefined_share"] = undefined / iterations
    if boot:
        boot.sort()
        a = (1 - level) / 2
        out["ci"] = [boot[int(a * (len(boot) - 1))], boot[int((1 - a) * (len(boot) - 1))]]
    else:
        out["ci"] = None
    return out
