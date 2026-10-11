"""Every number the paper reports for the frozen judge: test rates, the
pre-declared sensitivity check, and the pass-rate correction on v4.

  git fetch origin data
  python analysis/final.py

Inputs (all on the `data` branch, run IDs below):
  test run  the frozen judge on the test split (TPR and TNR come from here only)
  v4 run    the frozen judge on the v4 correction batch, scored without labels
Writes paper/results.json and paper/results.md.

The correction (Rogan and Gladen 1978):
  theta = (p_obs + TNR - 1) / (TPR + TNR - 1), clipped to [0, 1]
p_obs is the share of an agent run's decisions the judge passes. Each of the
four v4 agent runs (one per config) is corrected separately and compared with
its true pass rate from the answer key.

Two 95% intervals per run:
  item-level    as in judgy 0.1.0: resample test items; p_obs held fixed
  ticket-level  resample test tickets and v4 tickets (Field and Welsh 2007),
                so the uncertainty in p_obs is included and items that share
                a ticket move together
"""

import json
import os
import random
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from judge.estimate import corrected, estimate, rates  # noqa: E402

TEST_RUN = "gh38115612251-c3-labeled-test"
V4_RUN = "gh38116159452-c3-v4-prod"
V4_DECISIONS = "data/correction/gh38116062449_v4.jsonl"
DEV_RUN = "gh38104945965-c3-labeled-dev"
CONFIGS = ["clean", "template_edit", "context_strip", "prompt_edit"]
ITERATIONS = 10000


def git_show(path):
    return subprocess.run(["git", "-C", ROOT, "show", f"data:{path}"], capture_output=True, text=True,
                          check=True).stdout


def verdicts(run, threshold):
    rows = [json.loads(l) for l in git_show(f"runs/{run}/judgments.jsonl").splitlines() if l.strip()]
    return {r["item_id"]: r for r in rows if r["call"] == 1 and r["noul"] is not None}, \
        json.loads(git_show(f"runs/{run}/manifest.json"))


def item_level_ci(labels, preds, p_obs, iterations=ITERATIONS, seed=0):
    """judgy 0.1.0's procedure, reimplemented so the dropped resamples can be counted."""
    rng = random.Random(seed)
    n, boot, dropped = len(labels), [], 0
    for _ in range(iterations):
        idx = [rng.randrange(n) for _ in range(n)]
        r = rates([labels[i] for i in idx], [preds[i] for i in idx])
        est = None if r["tpr"] is None or r["tnr"] is None else corrected(p_obs, r["tpr"], r["tnr"])
        if est is None:
            dropped += 1
        else:
            boot.append(est)
    boot.sort()
    return [boot[int(0.025 * (len(boot) - 1))], boot[int(0.975 * (len(boot) - 1))]], dropped / iterations


def ambiguous(it):
    """Pre-declared in paper/decisions.md: damage or wrong item reported on an order still Shipped."""
    return it["issue"] in ("damaged", "wrong_item") and it["order"]["status"] == "Shipped"


def main():
    freeze = json.load(open(os.path.join(ROOT, "freeze.json")))
    t = freeze["threshold"]
    labeled = {json.loads(l)["item_id"]: json.loads(l) for l in open(os.path.join(ROOT, "data", "items_labeled.jsonl"))}

    test_v, test_m = verdicts(TEST_RUN, t)
    assert test_m["fingerprint"] == freeze["fingerprint"] and test_m["split"] == "test"
    test = [{"ticket_id": labeled[i]["ticket_id"], "label": labeled[i]["label"], "pred": int(v["noul"] >= t),
             "ambiguous": ambiguous(labeled[i])} for i, v in sorted(test_v.items())]
    r_all = rates([x["label"] for x in test], [x["pred"] for x in test])
    clear = [x for x in test if not x["ambiguous"]]
    r_clear = rates([x["label"] for x in clear], [x["pred"] for x in clear])
    dev_v, _ = verdicts(DEV_RUN, t)
    dev = [(labeled[i]["label"], int(v["noul"] >= t)) for i, v in dev_v.items()]
    r_dev = rates([a for a, _ in dev], [b for _, b in dev])
    calls = [json.loads(l) for l in git_show(f"runs/{TEST_RUN}/judgments.jsonl").splitlines() if l.strip()]
    by_item = {}
    for c in calls:
        by_item.setdefault(c["item_id"], []).append(int(c["noul"] >= t))
    repeat_disagree = sum(len(set(v)) > 1 for v in by_item.values())

    v4_v, v4_m = verdicts(V4_RUN, t)
    assert v4_m["fingerprint"] == freeze["fingerprint"] and v4_m["dataset"] == "v4"
    decisions = [json.loads(l) for l in open(os.path.join(ROOT, V4_DECISIONS))]
    test_labels, test_preds = [x["label"] for x in test], [x["pred"] for x in test]
    runs = []
    for cfg in CONFIGS:
        ds = [d for d in decisions if d["config"] == cfg]
        run = [{"ticket_id": d["ticket_id"], "label": d["label"],
                "pred": int(v4_v[f"v4:{d['ticket_id']}:{d['action']}"]["noul"] >= t)} for d in ds]
        e = estimate(test, run, iterations=ITERATIONS, seed=1)
        ci_item, dropped = item_level_ci(test_labels, test_preds, e["p_obs"])
        runs.append({"config": cfg, "m": len(run), "k": sum(x["pred"] for x in run), "p_obs": e["p_obs"],
                     "true": e["true_rate"], "corrected": e["corrected"],
                     "ci_ticket": e["ci"], "ci_ticket_undefined": e["undefined_share"],
                     "ci_item": ci_item, "ci_item_dropped": dropped,
                     "covered_ticket": e["ci"][0] <= e["true_rate"] <= e["ci"][1],
                     "covered_item": ci_item[0] <= e["true_rate"] <= ci_item[1]})

    res = {"freeze": freeze, "runs_used": {"dev": DEV_RUN, "test": TEST_RUN, "v4": V4_RUN,
                                           "v4_decisions": V4_DECISIONS},
           "dev": r_dev, "test": r_all, "test_repeat_disagree": repeat_disagree, "test_items": len(by_item),
           "test_without_ambiguous": {**r_clear, "set_aside": len(test) - len(clear)},
           "v4_items": len(v4_v), "v4_spend_usd": v4_m.get("spend_usd"), "test_spend_usd": test_m.get("spend_usd"),
           "correction": runs}
    json.dump(res, open(os.path.join(ROOT, "paper", "results.json"), "w"), indent=1)
    open(os.path.join(ROOT, "paper", "results.md"), "w").write(report(res))
    print(report(res))


def pct(x):
    return f"{100 * x:.1f}%"


def report(r):
    T, C, D = r["test"], r["test_without_ambiguous"], r["dev"]
    L = ["# Results for the frozen judge (generated by analysis/final.py)", "",
         f"Frozen judge: {r['freeze']['variant']}, fingerprint `{r['freeze']['fingerprint']}`, "
         f"threshold {r['freeze']['threshold']}. Runs: dev `{r['runs_used']['dev']}`, test `{r['runs_used']['test']}`, "
         f"v4 `{r['runs_used']['v4']}`.", "",
         "## Dev and test", "",
         "| Split | Items | TP | FN | FP | TN | TPR | TNR | TPR + TNR - 1 |", "|---|---|---|---|---|---|---|---|---|"]
    for name, x in (("dev", D), ("test", T), ("test without the pre-declared ambiguous items", C)):
        L.append(f"| {name} | {x['n']} | {x['tp']} | {x['fn']} | {x['fp']} | {x['tn']} | {x['tpr']:.3f} | "
                 f"{x['tnr']:.3f} | {x['youden']:.3f} |")
    L += ["", f"Set aside in the last row: {C['set_aside']} test items (damage or wrong item reported on an order "
          "still Shipped; see paper/decisions.md). The two calls per test item disagreed on "
          f"{r['test_repeat_disagree']} of {r['test_items']}.", "",
          "## Correcting the judge's pass rate on v4", "",
          "TPR and TNR from the test run. Each v4 agent run has 200 decisions; the judge scored them without labels.", "",
          "| Agent config | Judge passes (k of m) | p_obs | Corrected | True | Ticket-level 95% CI | Contains true | "
          "Item-level 95% CI (judgy) | Contains true |", "|---|---|---|---|---|---|---|---|---|"]
    for x in r["correction"]:
        L.append(f"| {x['config']} | {x['k']} of {x['m']} | {pct(x['p_obs'])} | {pct(x['corrected'])} | {pct(x['true'])} | "
                 f"[{pct(x['ci_ticket'][0])}, {pct(x['ci_ticket'][1])}] | {'yes' if x['covered_ticket'] else 'no'} | "
                 f"[{pct(x['ci_item'][0])}, {pct(x['ci_item'][1])}] | {'yes' if x['covered_item'] else 'no'} |")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    main()
