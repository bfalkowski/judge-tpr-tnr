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
    order = sorted(by_case, key=lambda t: (mean([x["grader"] for x in by_case[t]]), t))[:10]
    errors = sum(any(x["grader"] == 0 and x["true"] == 1 for x in by_case[t]) for t in order)
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
    return {"spotcheck_lowest10_grader_errors": errors,
            "spotcheck_flags": errors > 1,
            "agreement_40": agree, "agreement_flags": agree < 0.9,
            "tpr": rr["tpr"], "tnr": rr["tnr"], "tpr_ci": ci(tprs), "tnr_ci": ci(tnrs),
            "n_true_pass": rr["tp"] + rr["fn"], "n_true_fail": rr["tn"] + rr["fp"],
            "tpr_tnr_flags": rr["tpr"] < 0.9 or rr["tnr"] < 0.9,
            "spotcheck_of_10_passes_wrong": sum(1 for x in pass_sample if x["true"] == 0)}


def rounds_of(arm):
    st = hc.state(arm)
    return st, ["baseline"] + [h["round"] for h in st["history"]]


def arm_summary(arm):
    st, names = rounds_of(arm)
    S = {n: sealed(arm, n) for n in names}
    base, best = S["baseline"], S[st["best"]["name"]]
    out = {"arm": arm, "grader": hc.ARMS[arm]["description"], "winner": st["best"]["name"],
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
    for h in st["history"]:
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


def main():
    res = {"arms": {}, "pre_loop": {}, "categorization": {}}
    for arm in ARMS:
        res["arms"][arm] = arm_summary(arm)
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
        L.append(f"| {arm} | {a['winner']} | {a['rounds']} | {p(a['baseline']['grader_test'])} -> {p(a['winner']['grader_test'])} | "
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
          "| Arm | Grader errors in the 10 lowest-scoring cases | Agreement on 40 random decisions | TPR [95% CI] | TNR [95% CI] | Wrong among 10 random passes |",
          "|---|---|---|---|---|---|"]
    for arm, c in res["pre_loop"].items():
        L.append(f"| {arm} | {c['spotcheck_lowest10_grader_errors']} | {p(c['agreement_40'])} | "
                 f"{c['tpr']:.3f} [{c['tpr_ci'][0]:.2f}, {c['tpr_ci'][1]:.2f}] | {c['tnr']:.3f} [{c['tnr_ci'][0]:.2f}, {c['tnr_ci'][1]:.2f}] | "
                 f"{c['spotcheck_of_10_passes_wrong']} |")
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
