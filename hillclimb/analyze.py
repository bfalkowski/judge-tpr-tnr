"""Every number the hill-climbing write-up reports (hillclimb/DESIGN.md, Measures).

  git fetch origin data
  python hillclimb/analyze.py

Reads each arm's flow directory and hillclimb/_sealed/, which hold the answer
key's verdict and every grader's verdict for every (ticket, rep) of every
version the loop ran, including holdout tickets. Run only after every arm has
stopped. Writes hillclimb/results.json and hillclimb/RESULTS.md.
"""

import json
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import hc  # noqa: E402
from judge.estimate import corrected, rates  # noqa: E402

ARMS = list(hc.ARMS)
ORIGINAL = [a for a in ARMS if "replicate_of" not in hc.ARMS[a]]
RUNS = {base: [base] + sorted(a for a in ARMS if hc.ARMS[a].get("replicate_of") == base) for base in ORIGINAL}
ITER = 5000


def sealed(arm, name):
    return hc.jsonl(os.path.join(hc.SEALED, arm, f"{name}.jsonl"))


def mean(v):
    return sum(v) / len(v) if v else None


def by_split(rows, field, splits):
    return mean([r[field] for r in rows if r["split"] in splits])


def boot_diff(a_rows, b_rows, field, splits, seed=0):
    """95% interval of mean(b) - mean(a), resampling tickets (paired: same tickets in both)."""
    ga, gb = defaultdict(list), defaultdict(list)
    for r in a_rows:
        if r["split"] in splits:
            ga[r["ticket_id"]].append(r[field])
    for r in b_rows:
        if r["split"] in splits:
            gb[r["ticket_id"]].append(r[field])
    keys = sorted(set(ga) & set(gb))
    rng, out = random.Random(seed), []
    for _ in range(ITER):
        s = [rng.choice(keys) for _ in keys]
        a = [x for k in s for x in ga[k]]
        b = [x for k in s for x in gb[k]]
        out.append(mean(b) - mean(a))
    out.sort()
    return [out[int(0.025 * (ITER - 1))], out[int(0.975 * (ITER - 1))]]


def judge_rates(rows, splits=("climb_test", "holdout")):
    r = [x for x in rows if x["split"] in splits]
    rr = rates([x["true"] for x in r], [x["grader"] for x in r])
    mistakes = [x for x in r if not x["true"]]
    rr["mistakes"] = len(mistakes)
    rr["mistakes_passed"] = sum(x["grader"] for x in mistakes)
    return rr


def pre_loop_checks(arm):
    """The grader checks a careful user could run on the baseline's train decisions (DESIGN.md, Measure 5)."""
    rows = [r for r in sealed(arm, "baseline") if r["split"] == "climb_train"]
    by_case = defaultdict(list)
    for r in rows:
        by_case[r["ticket_id"]].append(r)
    # eval-hillclimb.md Step 0.5: read the lowest-scoring baseline cases; is the grade fair?
    # Many cases tie at a score of 0, so the ten read depend on the tie-break: ticket order, the judge's
    # own raw score (noul, averaged over reps), or random (10,000 draws).
    score = lambda t: mean([x["grader"] for x in by_case[t]])
    is_err = lambda t: any(x["grader"] == 0 and x["true"] == 1 for x in by_case[t])
    order = sorted(by_case, key=lambda t: (score(t), t))[:10]
    errors = sum(map(is_err, order))
    raw = None
    if hc.ARMS[arm]["grader"] == "judge":
        J = {(r["ticket_id"], r["action"]): r["noul"] for r in hc.jsonl(hc.run_file(hc.ARMS[arm]["judge_run"], "judgments.jsonl"))
             if r["call"] == 1}
        raw = lambda t: mean([J[(x["ticket_id"], x["action"])] for x in by_case[t]])
    errors_by_raw = sum(map(is_err, sorted(by_case, key=lambda t: (score(t), raw(t), t))[:10])) if raw else errors
    rng, dist = random.Random(0), []
    for _ in range(ITER * 2):
        k = {t: rng.random() for t in by_case}
        dist.append(sum(map(is_err, sorted(by_case, key=lambda t: (score(t), k[t]))[:10])))
    tied = sum(1 for t in by_case if score(t) == 0)
    # eval-audit.md section 4: agreement on a few dozen human-labelled cases
    rng = random.Random(20261027)
    sample = rng.sample(rows, 40)
    agree = mean([int(x["grader"] == x["true"]) for x in sample])
    # the primer's check: TPR and TNR, with ticket-level intervals
    rr = rates([x["true"] for x in rows], [x["grader"] for x in rows])
    keys = sorted(by_case)
    tprs, tnrs = [], []
    rng = random.Random(0)
    for _ in range(ITER):
        s = [x for _ in keys for x in by_case[rng.choice(keys)]]
        q = rates([x["true"] for x in s], [x["grader"] for x in s])
        if q["tpr"] is not None:
            tprs.append(q["tpr"])
        if q["tnr"] is not None:
            tnrs.append(q["tnr"])
    tprs.sort(), tnrs.sort()
    ci = lambda v: [v[int(0.025 * (len(v) - 1))], v[int(0.975 * (len(v) - 1))]]
    passes = [x for x in rows if x["grader"] == 1]
    rng = random.Random(1)
    pass_sample = rng.sample(passes, min(10, len(passes)))
    return {"spotcheck_lowest10_grader_errors": errors, "spotcheck_by_judge_score": errors_by_raw,
            "spotcheck_random_ties_mean": mean(dist), "spotcheck_random_ties_flag_rate": mean([int(d > 1) for d in dist]),
            "spotcheck_cases_tied_at_zero": tied,
            "spotcheck_flags": errors > 1,
            "agreement_40": agree, "agreement_flags": agree < 0.9,
            "tpr": rr["tpr"], "tnr": rr["tnr"], "tpr_ci": ci(tprs), "tnr_ci": ci(tnrs),
            "n_true_pass": rr["tp"] + rr["fn"], "n_true_fail": rr["tn"] + rr["fp"],
            "tpr_tnr_flags": rr["tpr"] < 0.9 or rr["tnr"] < 0.9,
            "spotcheck_of_10_passes_wrong": sum(1 for x in pass_sample if x["true"] == 0)}


def rounds_of(arm):
    st = hc.state(arm)
    return st, ["baseline"] + [h["round"] for h in st["history"] if h["decision"] != "none"]


def arm_summary(arm):
    st, names = rounds_of(arm)
    S = {n: sealed(arm, n) for n in names}
    base, best = S["baseline"], S[st["best"]["name"]]
    out = {"arm": arm, "grader": hc.ARMS[arm]["description"], "winner_name": st["best"]["name"],
           "stopped": st["stopped"], "rounds": len(names) - 1,
           "categorization": st.get("categorization")}
    for label, rows in (("baseline", base), ("winner", best)):
        out[label] = {f"{f}_{sp}": by_split(rows, f, [s]) for f in ("grader", "true")
                      for sp, s in (("train", "climb_train"), ("test", "climb_test"), ("holdout", "holdout"))}
    out["reported_test_delta"] = out["winner"]["grader_test"] - out["baseline"]["grader_test"]
    out["reported_test_delta_ci"] = boot_diff(base, best, "grader", ["climb_test"])
    out["true_test_delta"] = out["winner"]["true_test"] - out["baseline"]["true_test"]
    out["true_test_delta_ci"] = boot_diff(base, best, "true", ["climb_test"])
    out["true_holdout_delta"] = out["winner"]["true_holdout"] - out["baseline"]["true_holdout"]
    out["true_holdout_delta_ci"] = boot_diff(base, best, "true", ["holdout"])
    out["grader_holdout_delta"] = out["winner"]["grader_holdout"] - out["baseline"]["grader_holdout"]
    # judge error rates on each version, and the correction with baseline-measured rates
    out["versions"] = []
    b_rates = judge_rates(base, ("climb_train",))
    for n in names:
        rows = S[n]
        jr = judge_rates(rows)
        hold = [r for r in rows if r["split"] == "holdout"]
        p_obs = mean([r["grader"] for r in hold])
        corr = corrected(p_obs, b_rates["tpr"], b_rates["tnr"]) if b_rates["tpr"] is not None else None
        h = next((x for x in st["history"] if x["round"] == n), None)
        out["versions"].append({"name": n, "decision": h and h["decision"], "change": h and h["change"],
                                "tpr": jr["tpr"], "tnr": jr["tnr"], "mistakes": jr["mistakes"],
                                "mistakes_passed": jr["mistakes_passed"],
                                "grader_test": by_split(rows, "grader", ["climb_test"]),
                                "true_test": by_split(rows, "true", ["climb_test"]),
                                "grader_holdout": p_obs, "true_holdout": mean([r["true"] for r in hold]),
                                "corrected_holdout": corr})
    # would the same rule on answer-key scores have made the same call?
    agree, calls = 0, []
    cur = "baseline"
    for h in [h for h in st["history"] if h["decision"] != "none"]:
        n = h["round"]
        t = lambda name, sp: by_split(S[name], "true", [sp])
        c = {"train": t(cur, "climb_train"), "test": t(cur, "climb_test")}
        k = {"train": t(n, "climb_train"), "test": t(n, "climb_test")}
        rr = None
        if os.path.exists(os.path.join(hc.SEALED, arm, f"{n}-rerun.jsonl")):
            rr = {"test": by_split(sealed(arm, f"{n}-rerun"), "true", ["climb_test"])}
        key_call, _ = hc.decide(c, k, rr)
        key_call = {"rerun": "revert"}.get(key_call, key_call)
        calls.append({"round": n, "loop": h["decision"], "key_rule": key_call,
                      "true_holdout_change_vs_current": by_split(S[n], "true", ["holdout"]) - by_split(S[cur], "true", ["holdout"])})
        agree += key_call == h["decision"]
        if h["decision"] == "keep":
            cur = n
    out["decisions"] = calls
    out["decisions_agree"] = f"{agree} of {len(calls)}"
    return out


def categorization_check(arm):
    st = hc.state(arm)
    c = st.get("categorization")
    if not c:
        return None
    cat = json.load(open(hc.flow(arm, f"categorize_after_{c['after']}", "categorize.json")))
    cur_name = None  # the current version when the categorization ran: the last kept round up to and including c["after"]
    for h in st["history"]:
        if h["decision"] == "keep":
            cur_name = h["round"]
        if h["round"] == c["after"]:
            break
    rows = {(r["ticket_id"], r["rep"]): r for r in sealed(arm, cur_name or "baseline")}
    gd = [f for f in cat["failures"] if f["bucket"] == "grader_disagreement"]
    real = sum(1 for f in gd if rows.get((f["case"], f["rep"]), {}).get("true") == 1)
    fails = [r for r in rows.values() if r["split"] == "climb_train" and r["grader"] == 0]
    false_fails = sum(1 for r in fails if r["true"] == 1)
    return {"version": cur_name or "baseline", "grader_disagreement_calls": len(gd), "of_which_real_judge_errors": real,
            "train_failures": len(fails), "real_false_fails_among_them": false_fails, "counts": cat["counts"]}


def agreement_check_power(arm, n=40, draws=10000):
    """How often the eval-audit agreement check (n random decisions, >= 90% agreement) passes this grader."""
    rows = [r for r in sealed(arm, "baseline") if r["split"] == "climb_train"]
    rng, ok, fails = random.Random(0), 0, []
    for _ in range(draws):
        s = rng.sample(rows, n)
        ok += mean([int(r["grader"] == r["true"]) for r in s]) >= 0.9
        fails.append(sum(1 for r in s if not r["true"]))
    return {"p_pass": ok / draws, "mean_true_failures_in_sample": mean(fails)}


CATEGORIES = {
    "over_limit_out_of_stock": "never arrived, out of stock, total over $500: the policy says escalate",
    "damage_open": "damage or wrong item reported on an order that is Lost or shipped more than 14 days ago and not "
                   "delivered: the answer key says reply; rule 3 could also be read to apply; the policy text does not settle it",
    "damage_early": "damage or wrong item reported on an order shipped 14 days ago or less and not delivered: rule 1 says reply",
}


def category(t):
    from judge.policy import days_ago
    o, i = t["order"], t["issue"]
    if i in ("not_arrived", "where_is_it") and t["key"] == "escalate":
        return "over_limit_out_of_stock"
    if i in ("damaged", "wrong_item") and o["status"] in ("Shipped", "Lost"):
        return "damage_open" if o["status"] == "Lost" or days_ago(o["shipped_on"]) > 14 else "damage_early"
    return None


def category_verdicts():
    """For each hard category and judge: how many tickets' correct and wrong actions the judge passes (all v5 tickets)."""
    T = hc.tickets()
    out = {}
    for c in CATEGORIES:
        ts = [t for t in T.values() if category(t) == c]
        out[c] = {"tickets": len(ts)}
        for arm in ORIGINAL:
            g = hc.grader(arm)
            out[c][arm] = {"correct_passed": sum(g[(t["ticket_id"], t["key"])][0] for t in ts),
                           "wrong_passed": sum(g[(t["ticket_id"], a)][0] for t in ts
                                               for a in ("refund", "reship", "escalate", "reply") if a != t["key"]),
                           "wrong_total": 3 * len(ts)}
    return out


def drift_by_category(arm):
    """True mistakes on climb_test and holdout by category, and how many the grader passes, for each version."""
    T = hc.tickets()
    _, names = rounds_of(arm)
    out = {}
    for n in names:
        rows = [r for r in sealed(arm, n) if r["split"] in ("climb_test", "holdout") and not r["true"]]
        d = defaultdict(lambda: {"mistakes": 0, "passed": 0})
        for r in rows:
            c = category(T[r["ticket_id"]]) or "other"
            d[c]["mistakes"] += 1
            d[c]["passed"] += r["grader"]
        out[n] = dict(d)
    return out


def change_visibility(arm, a_name, b_name, splits=("climb_test", "holdout")):
    """Rows whose action changed from version a to b, by true change and grader change."""
    a = {(r["ticket_id"], r["rep"]): r for r in sealed(arm, a_name)}
    out = defaultdict(int)
    for r in sealed(arm, b_name):
        o = a[(r["ticket_id"], r["rep"])]
        if r["split"] in splits and o["action"] != r["action"]:
            out[f"true {o['true']}->{r['true']}, grader {o['grader']}->{r['grader']}"] += 1
    return dict(sorted(out.items()))


def rates_without_open(arm, name="baseline", splits=("climb_train",)):
    T = hc.tickets()
    rows = [r for r in sealed(arm, name) if r["split"] in splits and category(T[r["ticket_id"]]) != "damage_open"]
    return rates([r["true"] for r in rows], [r["grader"] for r in rows])


def open_case_verdicts():
    """On the open tickets: how many tickets each judge passes reply (the key) and rule 3's action for."""
    from judge.policy import resolve
    T = hc.tickets()
    ts = [t for t in T.values() if category(t) == "damage_open"]
    out = {"tickets": len(ts)}
    for arm in ORIGINAL:
        g = hc.grader(arm)
        r3 = lambda t: resolve("not_arrived", t["order"], t["stock"])
        out[arm] = {"reply_passed": sum(g[(t["ticket_id"], "reply")][0] for t in ts),
                    "rule3_action_passed": sum(g[(t["ticket_id"], r3(t))][0] for t in ts)}
    return out


def visibility_by_round(arm, splits=("climb_train", "climb_test")):
    """For each round, against the version it was compared with: the rows the change truly fixed and broke, and how
    much of each the grader saw. J_fix = net grader credit per fixed row; J_break = net grader charge per broken row.
    With one TPR and TNR for every row both would equal TPR + TNR - 1 (Youden's J)."""
    st = hc.state(arm)
    cur, out = "baseline", []
    for h in [h for h in st["history"] if h["decision"] != "none"]:
        a = {(x["ticket_id"], x["rep"]): x for x in sealed(arm, cur)}
        fx, bk, oth = [], [], []
        for x in sealed(arm, h["round"]):
            if x["split"] not in splits:
                continue
            o = a[(x["ticket_id"], x["rep"])]
            d = x["grader"] - o["grader"]
            (fx if (o["true"], x["true"]) == (0, 1) else bk if (o["true"], x["true"]) == (1, 0) else oth).append(d)
        out.append({"round": h["round"], "against": cur, "decision": h["decision"], "fixed": len(fx), "fix_credit": sum(fx),
                    "broken": len(bk), "break_charge": -sum(bk), "other": sum(oth),
                    "j_fix": sum(fx) / len(fx) if fx else None, "j_break": -sum(bk) / len(bk) if bk else None,
                    "true_change_rows": len(fx) - len(bk), "grader_change_rows": sum(fx) + sum(bk) + sum(oth)})
        if h["decision"] == "keep":
            cur = h["round"]
    return out


def label_the_diff(arm, ks=(10, 20, 30), splits=("climb_train", "climb_test")):
    """Retrospective: if a person had labelled k random rows whose action changed in a round, how often would the
    labelled net change (fixes minus breaks) have the same sign as the true net change over every changed row?"""
    st = hc.state(arm)
    cur, out = "baseline", []
    for h in [h for h in st["history"] if h["decision"] != "none"]:
        a = {(x["ticket_id"], x["rep"]): x for x in sealed(arm, cur)}
        P = [(a[(x["ticket_id"], x["rep"])], x) for x in sealed(arm, h["round"])
             if x["split"] in splits and a[(x["ticket_id"], x["rep"])]["action"] != x["action"]]
        true = sum(n["true"] - o["true"] for o, n in P)
        # Exact: drawing k rows without replacement from F fixes, B breaks and O other changed rows is multivariate
        # hypergeometric; sum the probability of every (fixes, breaks) count whose sign matches the true net.
        from math import comb
        F = sum(1 for o, n in P if (o["true"], n["true"]) == (0, 1))
        B = sum(1 for o, n in P if (o["true"], n["true"]) == (1, 0))
        O, agree = len(P) - F - B, {}
        for k in ks:
            k = min(k, len(P))
            agree[k] = sum(comb(F, f) * comb(B, b) * comb(O, k - f - b)
                           for f in range(0, min(F, k) + 1) for b in range(0, min(B, k - f) + 1)
                           if k - f - b <= O and f != b and (f > b) == (true > 0)) / comb(len(P), k)
        out.append({"round": h["round"], "changed_rows": len(P), "rows_total": sum(1 for x in sealed(arm, h["round"]) if x["split"] in splits),
                    "true_net": true, "agree": agree})
        if h["decision"] == "keep":
            cur = h["round"]
    return out


def kind(t):
    """category(), plus the second case the policy text leaves open: "never came" on an order the record shows Delivered."""
    c = category(t)
    if c is None and t["issue"] in ("not_arrived", "where_is_it") and t["order"]["status"] == "Delivered":
        return "never_came_delivered"
    return c or "other"


def breaks_by_kind(arm, splits=("climb_train", "climb_test")):
    """Each round's truly broken rows, against the version it was compared with, split into damage_open tickets and the
    rest, with what the grader did: charged (pass -> fail), credited (fail -> pass) or unchanged."""
    T = hc.tickets()
    st = hc.state(arm)
    cur, out = "baseline", []
    for h in [h for h in st["history"] if h["decision"] != "none"]:
        a = {(x["ticket_id"], x["rep"]): x for x in sealed(arm, cur)}
        row = {"round": h["round"], "decision": h["decision"]}
        for k in ("damage_open", "rest"):
            row[k] = {"broken": 0, "charged": 0, "credited": 0}
        for x in sealed(arm, h["round"]):
            if x["split"] not in splits:
                continue
            o = a[(x["ticket_id"], x["rep"])]
            if (o["true"], x["true"]) != (1, 0):
                continue
            k = "damage_open" if category(T[x["ticket_id"]]) == "damage_open" else "rest"
            row[k]["broken"] += 1
            d = x["grader"] - o["grader"]
            row[k]["charged"] += d < 0
            row[k]["credited"] += d > 0
        out.append(row)
        if h["decision"] == "keep":
            cur = h["round"]
    return out


def holdout_change_by_kind(arm):
    """Each round's true change on holdout against the version it was compared with, in points, split by kind."""
    T = hc.tickets()
    st = hc.state(arm)
    cur, out = "baseline", {}
    for h in [h for h in st["history"] if h["decision"] != "none"]:
        a = {(x["ticket_id"], x["rep"]): x for x in sealed(arm, cur)}
        rows = [x for x in sealed(arm, h["round"]) if x["split"] == "holdout"]
        d = defaultdict(float)
        for x in rows:
            d[kind(T[x["ticket_id"]])] += (x["true"] - a[(x["ticket_id"], x["rep"])]["true"]) / len(rows)
        out[h["round"]] = {k: round(100 * v, 1) for k, v in sorted(d.items())}
        if h["decision"] == "keep":
            cur = h["round"]
    return out


def replicate_summary(base):
    """One row per run of an arm: what the loop reported and kept, what was true, and how the judge's errors moved."""
    T = hc.tickets()
    rows = []
    for arm in RUNS[base]:
        st = hc.state(arm)
        rounds = [h for h in st["history"] if h["decision"] != "none"]
        b, w = sealed(arm, "baseline"), sealed(arm, st["best"]["name"])
        tnr = lambda rows_: judge_rates(rows_)["tnr"]
        open_m = [r for r in w if r["split"] in ("climb_test", "holdout") and not r["true"] and category(T[r["ticket_id"]]) == "damage_open"]
        all_m = [r for r in w if r["split"] in ("climb_test", "holdout") and not r["true"]]
        vis = visibility_by_round(arm)
        rows.append({"arm": arm, "rounds": len(rounds), "kept": [h["round"] for h in rounds if h["decision"] == "keep"],
                     "winner": st["best"]["name"], "stopped": st["stopped"],
                     "reported_val": by_split(w, "grader", ["climb_test"]) - by_split(b, "grader", ["climb_test"]),
                     "true_val": by_split(w, "true", ["climb_test"]) - by_split(b, "true", ["climb_test"]),
                     "true_holdout": by_split(w, "true", ["holdout"]) - by_split(b, "true", ["holdout"]),
                     "true_holdout_ci": boot_diff(b, w, "true", ["holdout"]),
                     "winner_true_holdout": by_split(w, "true", ["holdout"]),
                     "tnr_baseline": tnr(b), "tnr_winner": tnr(w),
                     "open_mistakes_winner": len(open_m), "open_passed_winner": sum(r["grader"] for r in open_m),
                     "false_passes_winner": sum(r["grader"] for r in all_m),
                     "j_fix": [v["j_fix"] for v in vis], "j_break": [v["j_break"] for v in vis],
                     "round_true": [v["true_change_rows"] for v in vis], "round_grader": [v["grader_change_rows"] for v in vis],
                     "categorization": st.get("categorization")})
    return rows


def tnr_drop_c3(arm="c3"):
    """c3's TNR on test and holdout mistakes, baseline against winner, counted per row and with one rep per ticket."""
    def fisher(a, b, c, d):
        import math
        n, r1, c1 = a + b + c + d, a + b, a + c
        pr = lambda x: math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
        p0 = pr(a)
        return sum(pr(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if pr(x) <= p0 + 1e-12)
    st = hc.state(arm)
    out = {}
    for label, reps in (("rows", (0, 1)), ("rep0", (0,))):
        b = [r for r in sealed(arm, "baseline") if r["split"] in ("climb_test", "holdout") and not r["true"] and r["rep"] in reps]
        w = [r for r in sealed(arm, st["best"]["name"]) if r["split"] in ("climb_test", "holdout") and not r["true"] and r["rep"] in reps]
        bt, wt = sum(1 - r["grader"] for r in b), sum(1 - r["grader"] for r in w)
        out[label] = {"baseline": [bt, len(b)], "winner": [wt, len(w)], "p": fisher(bt, len(b) - bt, wt, len(w) - wt)}
    return out


def rerun_noise(arm, name="baseline", split="climb_test"):
    """Noise from re-running the same version: tickets whose grade differs between the two runs, and the 95%
    half-width this implies for comparing two versions that each average two runs (Var(D_t) = Var(rep1 - rep0) / 2)."""
    by = defaultdict(dict)
    for r in sealed(arm, name):
        if r["split"] == split:
            by[r["ticket_id"]][r["rep"]] = r["grader"]
    d = [v[1] - v[0] for v in by.values()]
    return {"tickets_differing": sum(1 for x in d if x), "tickets": len(d),
            "half_width": 1.96 * (sum(x * x for x in d) / 2) ** 0.5 / len(d)}


def round_intervals(arm, split="climb_test"):
    """Each round's change on the validation split against the version it was compared with, for the grader and the
    answer key, with 95% paired intervals that resample tickets."""
    st = hc.state(arm)
    cur, out = "baseline", []
    for h in [h for h in st["history"] if h["decision"] != "none"]:
        a, b = sealed(arm, cur), sealed(arm, h["round"])
        row = {"round": h["round"], "against": cur, "decision": h["decision"]}
        for f in ("grader", "true"):
            row[f] = by_split(b, f, [split]) - by_split(a, f, [split])
            row[f + "_ci"] = boot_diff(a, b, f, [split])
        out.append(row)
        if h["decision"] == "keep":
            cur = h["round"]
    return out


def main():
    res = {"arms": {}, "pre_loop": {}, "categorization": {}}
    res["rerun_noise"] = {arm: rerun_noise(arm) for arm in ARMS}
    res["round_intervals"] = {arm: round_intervals(arm) for arm in ARMS}
    res["holdout_change_by_kind"] = {arm: holdout_change_by_kind(arm) for arm in ARMS}
    res["tnr_drop_c3"] = tnr_drop_c3()
    res["replicates"] = {base: replicate_summary(base) for base in RUNS if len(RUNS[base]) > 1}
    res["tnr_drop_c3_runs"] = {arm: tnr_drop_c3(arm) for arm in RUNS["c3"]}
    res["visibility"] = {arm: visibility_by_round(arm) for arm in ARMS}
    res["breaks_by_kind"] = {arm: breaks_by_kind(arm) for arm in ARMS if hc.ARMS[arm]["grader"] == "judge"}
    res["label_the_diff"] = {arm: label_the_diff(arm) for arm in ARMS}
    res["rates_without_open_case"] = {arm: rates_without_open(arm) for arm in ORIGINAL}
    res["open_case_verdicts"] = open_case_verdicts()
    res["agreement_check_power"] = {arm: agreement_check_power(arm) for arm in ORIGINAL}
    res["category_verdicts"] = category_verdicts()
    res["drift_by_category"] = {arm: drift_by_category(arm) for arm in ARMS}
    res["lenient_v2_visibility"] = change_visibility("lenient", "baseline", "v2")
    for arm in ARMS:
        res["arms"][arm] = arm_summary(arm)
        if arm in ORIGINAL:
            res["pre_loop"][arm] = pre_loop_checks(arm)
        res["categorization"][arm] = categorization_check(arm)
    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    open(os.path.join(HERE, "RESULTS.md"), "w").write(report(res))
    print(report(res))


def p(x):
    return "n/a" if x is None else f"{100 * x:.1f}"


def pci(c):
    return f"[{100 * c[0]:+.1f}, {100 * c[1]:+.1f}]"


def report(res):
    L = ["# Hill-climbing results (generated by hillclimb/analyze.py)", "",
         "Scores are pass rates in percent over (ticket, rep) rows. Grader = the arm's grader; true = the answer key.", "",
         "## Reported versus true gain", "",
         "| Arm | Winner | Rounds | Grader test: baseline -> winner | Reported delta [95% CI] | True test delta [95% CI] | True holdout delta [95% CI] | Grader holdout delta |",
         "|---|---|---|---|---|---|---|---|"]
    for arm, a in res["arms"].items():
        L.append(f"| {arm} | {a['winner_name']} | {a['rounds']} | {p(a['baseline']['grader_test'])} -> {p(a['winner']['grader_test'])} | "
                 f"{100 * a['reported_test_delta']:+.1f} {pci(a['reported_test_delta_ci'])} | "
                 f"{100 * a['true_test_delta']:+.1f} {pci(a['true_test_delta_ci'])} | "
                 f"{100 * a['true_holdout_delta']:+.1f} {pci(a['true_holdout_delta_ci'])} | {100 * a['grader_holdout_delta']:+.1f} |")
    L += ["", "## Levels", "",
          "| Arm | Version | Grader test | True test | Grader holdout | True holdout |", "|---|---|---|---|---|---|"]
    for arm, a in res["arms"].items():
        for lab in ("baseline", "winner"):
            v = a[lab]
            L.append(f"| {arm} | {lab} | {p(v['grader_test'])} | {p(v['true_test'])} | {p(v['grader_holdout'])} | {p(v['true_holdout'])} |")
    L += ["", "## Each version: the grader's error rates and the correction", "",
          "TPR and TNR on climb_test and holdout rows of that version. Corrected holdout uses the TPR and TNR measured on the baseline's train rows.", "",
          "| Arm | Version | Decision | TPR | TNR | True mistakes passed | Grader test | True test | Grader holdout | Corrected holdout | True holdout |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm, a in res["arms"].items():
        for v in a["versions"]:
            L.append(f"| {arm} | {v['name']} | {v['decision'] or ''} | {v['tpr']:.3f} | {v['tnr']:.3f} | "
                     f"{v['mistakes_passed']} of {v['mistakes']} | {p(v['grader_test'])} | {p(v['true_test'])} | "
                     f"{p(v['grader_holdout'])} | {p(v['corrected_holdout'])} | {p(v['true_holdout'])} |")
    L += ["", "## Keep and revert calls against the same rule on answer-key scores", "",
          "| Arm | Round | Loop's call | Key rule's call | True holdout change vs current |", "|---|---|---|---|---|"]
    for arm, a in res["arms"].items():
        for d in a["decisions"]:
            L.append(f"| {arm} | {d['round']} | {d['loop']} | {d['key_rule']} | {100 * d['true_holdout_change_vs_current']:+.1f} |")
        L.append(f"| {arm} | | agree: {a['decisions_agree']} | | |")
    L += ["", "## Grader checks on the baseline's train decisions", "",
          "Grader errors among the 10 lowest-scoring train cases: cases tied at a score of 0 are taken in ticket order, by the judge's raw score, or at random (mean over 10,000 draws, and how often more than 1 of 10 is a grader error, the audit's threshold).", "",
          "| Arm | Cases tied at 0 | Spot-check: ticket order | by judge score | random: mean | random: flagged | Agreement on 40 random decisions | TPR [95% CI] | TNR [95% CI] | Wrong among 10 random passes |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for arm, c in res["pre_loop"].items():
        L.append(f"| {arm} | {c['spotcheck_cases_tied_at_zero']} | {c['spotcheck_lowest10_grader_errors']} | {c['spotcheck_by_judge_score']} | "
                 f"{c['spotcheck_random_ties_mean']:.2f} | {100 * c['spotcheck_random_ties_flag_rate']:.0f}% | {p(c['agreement_40'])} | "
                 f"{c['tpr']:.3f} [{c['tpr_ci'][0]:.2f}, {c['tpr_ci'][1]:.2f}] | {c['tnr']:.3f} [{c['tnr_ci'][0]:.2f}, {c['tnr_ci'][1]:.2f}] | "
                 f"{c['spotcheck_of_10_passes_wrong']} |")
    L += ["", "How often the 40-decision agreement check passes each grader (10,000 random draws of 40 baseline train decisions; pass = 90% or more):", ""]
    for arm, c in res["agreement_check_power"].items():
        L.append(f"- {arm}: passes {100 * c['p_pass']:.1f}% of the time; a draw holds {c['mean_true_failures_in_sample']:.1f} true failures on average")
    L += ["", "## Two hard categories: what each grader passes (all 400 v5 tickets)", ""]
    for c, d in res["category_verdicts"].items():
        L.append(f"- **{c}** ({d['tickets']} tickets; {CATEGORIES[c]}): " + "; ".join(
            f"{arm} passes the correct action on {d[arm]['correct_passed']} and a wrong one on {d[arm]['wrong_passed']} of {d[arm]['wrong_total']}"
            for arm in ORIGINAL))
    o = res["open_case_verdicts"]
    L += ["", f"On the {o['tickets']} damage_open tickets: " + "; ".join(
        f"{arm} passes reply on {o[arm]['reply_passed']} and rule 3's action on {o[arm]['rule3_action_passed']}" for arm in ORIGINAL), "",
        "TPR and TNR on the baseline's train decisions without the damage_open tickets: " + "; ".join(
        f"{arm} {r['tpr']:.3f} / {r['tnr']:.3f}" for arm, r in res["rates_without_open_case"].items())]
    L += ["", "## True mistakes by category on climb_test and holdout, and how many the grader passes", "",
          "| Arm | Version | over_limit_out_of_stock | damage_open | damage_early | other |", "|---|---|---|---|---|---|"]
    for arm, vs in res["drift_by_category"].items():
        for n, d in vs.items():
            cell = lambda k: f"{d[k]['passed']} of {d[k]['mistakes']}" if k in d else "0 of 0"
            L.append(f"| {arm} | {n} | {cell('over_limit_out_of_stock')} | {cell('damage_open')} | {cell('damage_early')} | {cell('other')} |")
    L += ["", "## lenient v2 against baseline: rows whose action changed (climb_test and holdout)", ""]
    for k, v in res["lenient_v2_visibility"].items():
        L.append(f"- {k}: {v}")
    L += ["", "## How much of each change the grader saw (climb_train and climb_test rows, against the version it was compared with)", "",
          "J_fix is the grader's net credit per truly fixed row; J_break its net charge per truly broken row. A grader with one TPR and TNR for every row would have both equal to TPR + TNR - 1.", "",
          "| Arm | Round | Against | Decision | Fixed | Credited | J_fix | Broken | Charged | J_break | True change (rows) | Grader change (rows) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    f2 = lambda v: "n/a" if v is None else f"{v:.2f}"
    for arm, vs in res["visibility"].items():
        for v in vs:
            L.append(f"| {arm} | {v['round']} | {v['against']} | {v['decision']} | {v['fixed']} | {v['fix_credit']} | {f2(v['j_fix'])} | "
                     f"{v['broken']} | {v['break_charge']} | {f2(v['j_break'])} | {v['true_change_rows']:+d} | {v['grader_change_rows']:+d} |")
    L += ["", "Truly broken rows on damage_open tickets and on the rest, and what the grader did with them (charged = pass to fail, credited = fail to pass):", "",
          "| Arm | Round | Decision | damage_open: broken / charged / credited | rest: broken / charged / credited |", "|---|---|---|---|---|"]
    for arm, vs in res["breaks_by_kind"].items():
        for v in vs:
            d, r = v["damage_open"], v["rest"]
            L.append(f"| {arm} | {v['round']} | {v['decision']} | {d['broken']} / {d['charged']} / {d['credited']} | {r['broken']} / {r['charged']} / {r['credited']} |")
    L += ["", "## Labelling only the changed rows (retrospective)", "",
          "If a person had labelled k random rows whose action changed (climb_train and climb_test), the probability that the labelled net change has the same sign as the true net change (exact, from the hypergeometric distribution; a labelled net of 0 counts as a miss).", "",
          "| Arm | Round | Changed rows (of all) | True net change | k = 10 | k = 20 | k = 30 |", "|---|---|---|---|---|---|---|"]
    for arm, vs in res["label_the_diff"].items():
        for v in vs:
            L.append(f"| {arm} | {v['round']} | {v['changed_rows']} of {v['rows_total']} | {v['true_net']:+d} | "
                     + " | ".join(f"{100 * v['agree'][k]:.0f}%" for k in (10, 20, 30)) + " |")
    L += ["", "## True change on holdout by kind of ticket, each round against the version it was compared with (points)", ""]
    for arm, vs in res["holdout_change_by_kind"].items():
        for rd, d in vs.items():
            L.append(f"- {arm} {rd}: " + ", ".join(f"{k} {v:+.1f}" for k, v in d.items()) + f"; total {sum(d.values()):+.1f}")
    t = res["tnr_drop_c3"]
    L += ["", "c3's TNR on test and holdout mistakes, baseline against winner: per row "
          f"{t['rows']['baseline'][0]} of {t['rows']['baseline'][1]} against {t['rows']['winner'][0]} of {t['rows']['winner'][1]} "
          f"(Fisher p = {t['rows']['p']:.3f}, but the two reps of a ticket are not independent); one rep per ticket "
          f"{t['rep0']['baseline'][0]} of {t['rep0']['baseline'][1]} against {t['rep0']['winner'][0]} of {t['rep0']['winner'][1]} (p = {t['rep0']['p']:.3f})."]
    L += ["", "## Noise", "", "Re-running the same version (the baseline's two runs, validation split):", ""]
    for arm, n in res["rerun_noise"].items():
        L.append(f"- {arm}: {n['tickets_differing']} of {n['tickets']} tickets graded differently between runs; "
                 f"95% half-width for comparing two 2-run versions {100 * n['half_width']:.1f} points")
    L += ["", "Each round's change on the validation split (climb_test), with 95% paired intervals over tickets:", "",
          "| Arm | Round | Against | Decision | Grader change [95% CI] | True change [95% CI] |", "|---|---|---|---|---|---|"]
    for arm, vs in res["round_intervals"].items():
        for v in vs:
            L.append(f"| {arm} | {v['round']} | {v['against']} | {v['decision']} | {100 * v['grader']:+.1f} {pci(v['grader_ci'])} | "
                     f"{100 * v['true']:+.1f} {pci(v['true_ci'])} |")
    L += ["", "## Replicate runs", "",
          "Run 1 is the original arm. Validation is climb_test; true changes are against the baseline, in points.", "",
          "| Arm | Rounds | Kept | Winner | Reported (validation) | True (validation) | True (holdout) [95% CI] | Winner holdout | TNR baseline -> winner | Open-case mistakes at winner (passed) | J on fixes by round | J on breaks by round |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    f2 = lambda v: "n/a" if v is None else f"{v:.2f}"
    for base, rows in res["replicates"].items():
        for r in rows:
            L.append(f"| {r['arm']} | {r['rounds']} | {', '.join(r['kept']) or 'none'} | {r['winner']} | {100 * r['reported_val']:+.1f} | "
                     f"{100 * r['true_val']:+.1f} | {100 * r['true_holdout']:+.1f} {pci(r['true_holdout_ci'])} | {p(r['winner_true_holdout'])} | "
                     f"{r['tnr_baseline']:.3f} -> {r['tnr_winner']:.3f} | {r['open_mistakes_winner']} ({r['open_passed_winner']}) | "
                     f"{', '.join(f2(x) for x in r['j_fix'])} | {', '.join(f2(x) for x in r['j_break'])} |")
    L += ["", "c3's TNR on test and holdout mistakes, baseline against winner, in each run:", ""]
    for arm, t in res["tnr_drop_c3_runs"].items():
        r, q = t["rows"], t["rep0"]
        L.append(f"- {arm}: per row {r['baseline'][0]} of {r['baseline'][1]} against {r['winner'][0]} of {r['winner'][1]} (Fisher p = {r['p']:.3f}); "
                 f"one rep per ticket {q['baseline'][0]} of {q['baseline'][1]} against {q['winner'][0]} of {q['winner'][1]} (p = {q['p']:.3f})")
    L += ["", "## Stall categorization", ""]
    for arm, c in res["categorization"].items():
        if c:
            L.append(f"- {arm} (after {c['version']}): {c['counts']}. Grader-disagreement calls: {c['grader_disagreement_calls']}, "
                     f"of which real judge errors: {c['of_which_real_judge_errors']}. Real false fails among the "
                     f"{c['train_failures']} train failures: {c['real_false_fails_among_them']}.")
        else:
            L.append(f"- {arm}: no categorization round")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
