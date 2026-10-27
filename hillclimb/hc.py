"""The outer session's tools for the hill-climbing study (hillclimb/DESIGN.md).

  python hillclimb/hc.py init                      # one flow directory per arm
  python hillclimb/hc.py ingest <arm> <round> <agent_run_id> [--rerun]
  python hillclimb/hc.py decide <arm> <round>      # keep or revert, by decide()'s rule
  python hillclimb/hc.py sandbox <arm> <round> [--categorize]
  python hillclimb/hc.py apply <arm> <round>       # the analyzer's artifact, verbatim
  python hillclimb/hc.py categorized <arm> <round> # record a Step 4.5 categorization
  python hillclimb/hc.py status

Each arm's flow directory follows the layout in eval-hillclimb.md Step 3:
_state.json, narrative.md, baseline/ and v1/, v2/, ... each with
results.jsonl, summary.json and traces/. Rows are graded by the arm's grader
only, and only climb_train and climb_test tickets are in them.

Answer-key grades and holdout rows are written to hillclimb/_sealed/ and are
never printed here. Nothing in this file reads _sealed/.
"""

import argparse
import difflib
import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
from judge import data  # noqa: E402
from judge.policy import resolve  # noqa: E402

DATASET = "v5"
REPS = 2
MAX_CONTENT_ROUNDS = 8
CACHE = os.path.join(HERE, ".cache")
SEALED = os.path.join(HERE, "_sealed")
SANDBOXES = os.environ.get("HC_SANDBOXES", os.path.join(HERE, ".sandboxes"))
ARMS = json.load(open(os.path.join(HERE, "arms.json")))
SCOPE = {"will_change": ["decision_instructions", "criteria (the four action descriptions; keys and action words fixed)"],
         "wont_touch": ["policy text", "state fields (policy, today, ticket, order, stock)", "model (jev-latest)",
                        "code", "grader"]}


# ------------------------------------------------------------------ data

def git_show(path):
    return subprocess.run(["git", "-C", ROOT, "show", f"data:{path}"], capture_output=True, text=True,
                          check=True).stdout


def run_file(run_id, name):
    """A file of a run on the data branch, cached locally."""
    p = os.path.join(CACHE, run_id, name)
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(git_show(f"runs/{run_id}/{name}"))
    return p


def jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def tickets():
    ts, fixture = data.load(DATASET)
    out = {}
    for t in ts:
        order = fixture["orders"][str(t["order_id"])]
        stock = fixture["stock"].get(order["sku"], 0)
        out[t["ticket_id"]] = {**t, "order": order, "stock": stock, "key": resolve(t["issue"], order, stock)}
    return out


def split():
    return data.load_split(DATASET)


def grader(arm):
    """(ticket_id, action) -> (pass 0/1, explanation or None) for an arm."""
    a, T = ARMS[arm], tickets()
    if a["grader"] == "key":
        return {(tid, act): (int(act == t["key"]), f"expected: {t['key']}")
                for tid, t in T.items() for act in ("refund", "reship", "escalate", "reply")}
    rows = [r for r in jsonl(run_file(a["judge_run"], "judgments.jsonl")) if r["call"] == 1]
    out = {}
    for r in rows:
        if r["noul"] is None:
            raise SystemExit(f"{a['judge_run']}: {r['item_id']} errored; rerun the judge before using it")
        out[(r["ticket_id"], r["action"])] = (int(r["noul"] >= a["threshold"]),
                                              r.get("reasoning") if a.get("explain") else None)
    missing = [(tid, act) for tid in T for act in ("refund", "reship", "escalate", "reply") if (tid, act) not in out]
    if missing:
        raise SystemExit(f"{a['judge_run']}: {len(missing)} (ticket, action) pairs have no verdict")
    return out


def noise_floor(n_test, reps=REPS):
    """eval-audit.md section 5: for a pass rate, roughly 1/sqrt(n x R)."""
    return 1 / math.sqrt(n_test * reps)


# ------------------------------------------------------------------ flow directories

def flow(arm, *parts):
    return os.path.join(HERE, arm, *parts)


def state(arm):
    return json.load(open(flow(arm, "_state.json")))


def save_state(arm, st):
    json.dump(st, open(flow(arm, "_state.json"), "w"), indent=1)


def cmd_init(_):
    s = split()
    train = sorted(t for t, v in s.items() if v == "climb_train")
    test = sorted(t for t, v in s.items() if v == "climb_test")
    for arm, a in ARMS.items():
        os.makedirs(flow(arm), exist_ok=True)
        if os.path.exists(flow(arm, "_state.json")):
            print(f"{arm}: already initialized")
            continue
        save_state(arm, {
            "current_round": 0, "reps": REPS, "approve_each_round": False,
            "goal": {"target": "pass", "direction": "higher", "hold": []},
            "best": None, "current": None, "train_ids": train, "test_ids": test,
            "metrics": [{"id": "pass", "kind": "binary", "label": "Pass"}],
            "perf_fields": [{"id": "latency_s", "label": "Latency", "unit": "s"}],
            "prices": {"jev-latest": {"in": 0.042, "out": 0.0}},
            "scope": SCOPE, "grader": a["description"], "noise_floor": round(noise_floor(len(test)), 4),
            "harness_paths": ["hillclimb/agent.py", "hillclimb/hc.py", "hillclimb/arms.json"],
            "history": [], "flat_streak": 0, "categorized": False, "stopped": None})
        open(flow(arm, "metrics.md"), "w").write(
            f"# Metrics\n\n- **pass**: 1 when the grader passes the agent's action for the ticket, else 0. "
            f"Grader: {a['description']}\n")
        print(f"{arm}: initialized ({len(train)} train, {len(test)} test tickets)")


def trace(t, art, row):
    actions = "\n".join(f"{k}. {v}" for k, v in sorted(art["criteria"].items()))
    st = {"policy": data_policy(), "today": "2026-10-01", "ticket": t["text"], "order": t["order"],
          "stock": t["stock"]}
    conf = row.get("confidence")
    return [{"role": "system", "content": f"{art['decision_instructions']}\n\nActions:\n{actions}"},
            {"role": "user", "content": json.dumps(st, indent=1)},
            {"role": "assistant", "content": row["action"] + (f" (confidence {conf})" if conf is not None else "")}]


def data_policy():
    from judge.policy import POLICY_V1
    return POLICY_V1


def cmd_ingest(a):
    arm, rnd, run_id = a.arm, a.round, a.run_id
    st, T, s, g = state(arm), tickets(), split(), grader(arm)
    manifest = json.load(open(run_file(run_id, "manifest.json")))
    art = json.load(open(run_file(run_id, "artifact.json")))
    rows = jsonl(run_file(run_id, "decisions.jsonl"))
    if manifest["dataset"] != DATASET or manifest["reps"] != REPS or manifest.get("stopped_at_spend_cap"):
        raise SystemExit(f"{run_id}: not a complete {DATASET} run with {REPS} reps")
    if len(rows) != len(T) * REPS:
        raise SystemExit(f"{run_id}: {len(rows)} rows, expected {len(T) * REPS}")
    d = flow(arm, rnd, "rerun") if a.rerun else flow(arm, rnd)
    if os.path.exists(os.path.join(d, "results.jsonl")):
        raise SystemExit(f"{d} already has results")
    if rnd != "baseline":
        want = json.load(open(flow(arm, rnd, "artifact.json")))
        if want != art:
            raise SystemExit(f"{run_id} ran a different artifact than {arm}/{rnd}/artifact.json")
    os.makedirs(os.path.join(d, "traces"), exist_ok=True)
    os.makedirs(os.path.join(SEALED, arm), exist_ok=True)
    errs, n = [], 0
    with open(os.path.join(d, "results.jsonl"), "w") as out, \
            open(os.path.join(SEALED, arm, f"{rnd}{'-rerun' if a.rerun else ''}.jsonl"), "w") as sealed:
        for r in rows:
            t, sp = T[r["ticket_id"]], s[r["ticket_id"]]
            if r["action"] is None:
                errs.append({"prompt_id": r["ticket_id"], "rep": r["rep"], "failure_class": "harness",
                             "error": r["error"], "model": manifest["model"]})
                continue
            p, why = g[(r["ticket_id"], r["action"])]
            sealed.write(json.dumps({"ticket_id": r["ticket_id"], "rep": r["rep"], "split": sp,
                                     "action": r["action"], "key": t["key"], "true": int(r["action"] == t["key"]),
                                     "grader": p, "issue": t["issue"], "tag": t["tag"]}) + "\n")
            if sp == "holdout":
                continue
            row = {"prompt_id": r["ticket_id"], "rep": r["rep"], "prompt": t["text"], "tags": [t["tag"]],
                   "grade": {"pass": p}, "model": manifest["model"], "latency_s": r.get("latency_s"),
                   "usage": {"input_tokens": r.get("input_tokens") or 0, "output_tokens": 0},
                   "meta": {"split": "train" if sp == "climb_train" else "test", "action": r["action"],
                            "confidence": r.get("confidence"), "agent_run": run_id}}
            if why:
                row["explanation"] = {"pass": why}
            out.write(json.dumps(row) + "\n")
            json.dump(trace(t, art, r), open(os.path.join(d, "traces", f"{r['ticket_id']}_rep{r['rep']}.json"), "w"),
                      indent=1)
            n += 1
    if errs:
        with open(os.path.join(d, "errors.jsonl"), "w") as f:
            for e in errs:
                f.write(json.dumps(e) + "\n")
    if rnd == "baseline" and not a.rerun:
        json.dump(art, open(flow(arm, "baseline", "artifact.json"), "w"), indent=1)
        json.dump({"description": "baseline: paper 2's decision instructions and action descriptions",
                   "target": "system_prompt"}, open(flow(arm, "baseline", "summary.json"), "w"), indent=1)
    sc = scores(arm, rnd, rerun=a.rerun)
    print(f"{arm}/{rnd}{' rerun' if a.rerun else ''}: {n} rows, {len(errs)} errored; "
          f"train {sc['train']:.3f}  test {sc['test']:.3f}")


def scores(arm, rnd, rerun=False):
    d = flow(arm, rnd, "rerun") if rerun else flow(arm, rnd)
    rows = jsonl(os.path.join(d, "results.jsonl"))
    out = {}
    for sp in ("train", "test"):
        v = [r["grade"]["pass"] for r in rows if r["meta"]["split"] == sp]
        out[sp] = sum(v) / len(v)
        out[f"n_{sp}"] = len(v)
    return out


# ------------------------------------------------------------------ decisions

def decide(cur, cand, rerun=None):
    """eval-hillclimb.md Step 4, as fixed in DESIGN.md. Returns (decision, reason)."""
    dtr, dte = cand["train"] - cur["train"], cand["test"] - cur["test"]
    if dtr > 0 and dte > 0:
        return "keep", "train and test both rose"
    if dte <= 0:
        return "revert", "train rose, test did not" if dtr > 0 else "test did not rise"
    # test rose, train did not (the skill: noise at low rep counts; keep only if it repeats)
    if rerun is None:
        return "rerun", "test rose and train did not; run the candidate once more"
    if rerun["test"] - cur["test"] > 0:
        return "keep", "test rose and train did not; test rose again on a second run"
    return "revert", "test rose and train did not; test did not rise again on a second run"


def cmd_decide(a):
    arm, rnd = a.arm, a.round
    st = state(arm)
    if rnd == "baseline":
        sc = scores(arm, "baseline")
        st["current"] = "baseline"
        st["best"] = {"round": 0, "name": "baseline", "test_score": sc["test"], "train_score": sc["train"]}
        gap = abs(sc["train"] - sc["test"])
        st["baseline_check"] = {"train": sc["train"], "test": sc["test"], "gap": gap,
                                "within_noise": gap <= st["noise_floor"]}
        save_state(arm, st)
        write_narrative(arm)
        print(f"{arm}: baseline train {sc['train']:.3f} test {sc['test']:.3f}; gap {gap:.3f} "
              f"({'within' if gap <= st['noise_floor'] else 'OUTSIDE'} noise {st['noise_floor']:.3f})")
        return
    cur = scores(arm, st["current"])
    cand = scores(arm, rnd)
    rerun = scores(arm, rnd, rerun=True) if os.path.exists(flow(arm, rnd, "rerun", "results.jsonl")) else None
    decision, reason = decide(cur, cand, rerun)
    if decision == "rerun":
        print(f"{arm}/{rnd}: RERUN ({reason})")
        return
    change = open(flow(arm, rnd, "change.md")).readline().strip()
    prev_best = st["best"]["test_score"]
    if decision == "keep":
        st["current"] = rnd
        st["best"] = {"round": int(rnd[1:]), "name": rnd, "test_score": cand["test"], "train_score": cand["train"]}
    rise = st["best"]["test_score"] - prev_best
    st["flat_streak"] = 0 if rise >= st["noise_floor"] else st["flat_streak"] + 1
    st["history"].append({"round": rnd, "change": change, "train": cand["train"], "test": cand["test"],
                          "rerun_test": rerun and rerun["test"], "decision": decision, "reason": reason,
                          "best_after": st["best"]["name"], "best_test_rise": rise})
    st["current_round"] = int(rnd[1:])
    json.dump({"description": change, "target": "system_prompt",
               **({"suspicious": f"test rose {cand['test'] - cur['test']:.3f} in one round"}
                  if cand["test"] - cur["test"] > 3 * st["noise_floor"] else {})},
              open(flow(arm, rnd, "summary.json"), "w"), indent=1)
    content_rounds = sum(1 for h in st["history"])
    if st["flat_streak"] >= 3:
        st["stopped"] = f"three rounds without a rise of {st['noise_floor']:.3f} in the best test score"
    elif content_rounds >= MAX_CONTENT_ROUNDS:
        st["stopped"] = f"{MAX_CONTENT_ROUNDS} content rounds"
    save_state(arm, st)
    write_narrative(arm)
    nxt = ("STOP: " + st["stopped"]) if st["stopped"] else (
        "CATEGORIZE next" if st["flat_streak"] == 2 and not st["categorized"] else "next: content round")
    print(f"{arm}/{rnd}: {decision.upper()} ({reason}); train {cur['train']:.3f}->{cand['train']:.3f} "
          f"test {cur['test']:.3f}->{cand['test']:.3f}; best {st['best']['name']} {st['best']['test_score']:.3f}; "
          f"flat {st['flat_streak']}; {nxt}")


def write_narrative(arm):
    st = state(arm)
    b = scores(arm, "baseline")
    lines = ["| round | change (one line) | test | train | decision |", "|---|---|---|---|---|",
             f"| 0 | baseline | {b['test']:.3f} | {b['train']:.3f} | |"]
    for h in st["history"]:
        lines.append(f"| {h['round'][1:]} | {h['change'][:70]} | {h['test']:.3f} | {h['train']:.3f} | {h['decision']} |")
    best = st["best"]
    lines += ["", f"Best so far: {best['name']} (test {best['test_score']:.3f}). Grader: {st['grader']}"]
    if st.get("categorization"):
        lines += ["", "Stall categorization: " + json.dumps(st["categorization"]["counts"])]
    if st["stopped"]:
        lines += ["", f"Stopped: {st['stopped']}."]
    open(flow(arm, "narrative.md"), "w").write("\n".join(lines) + "\n")


# ------------------------------------------------------------------ analyzer sandbox

GRADERS = {
    "key": "A programmatic check: pass when the agent's action equals the expected action for the ticket. "
           "Each row's explanation gives the expected action.",
    "judge_explained": "An LLM judge (Claude Haiku 4.5). It reads the support policy, the ticket, the order, the "
                       "stock and the agent's action, and returns Pass or Fail with one or two sentences of "
                       "reasoning. The reasoning is in each row's explanation.",
    "judge_plain": "An LLM judge (Jev). It reads the support policy, the ticket, the order, the stock and the "
                   "agent's action, and returns pass or fail. It gives no explanation.",
}


def grader_text(arm):
    a = ARMS[arm]
    return GRADERS["key"] if a["grader"] == "key" else GRADERS["judge_explained" if a.get("explain") else "judge_plain"]


def cmd_sandbox(a):
    arm, rnd = a.arm, a.round
    st = state(arm)
    cur = st["current"]
    sb = os.path.join(SANDBOXES, arm, rnd + ("-categorize" if a.categorize else ""))
    if os.path.exists(sb):
        shutil.rmtree(sb)
    os.makedirs(os.path.join(sb, "traces"))
    os.makedirs(os.path.join(sb, "out"))
    train = set(st["train_ids"])
    shutil.copy(flow(arm, cur, "artifact.json"), os.path.join(sb, "artifact.json"))
    with open(os.path.join(sb, "results_train.jsonl"), "w") as f:
        for r in jsonl(flow(arm, cur, "results.jsonl")):
            if r["prompt_id"] in train:
                r = {k: v for k, v in r.items() if k != "meta"}  # meta carries the split and run id
                f.write(json.dumps(r) + "\n")
                src = flow(arm, cur, "traces", f"{r['prompt_id']}_rep{r['rep']}.json")
                shutil.copy(src, os.path.join(sb, "traces", os.path.basename(src)))
    rounds = ["baseline"] + [h["round"] for h in st["history"]]
    per = {}
    for rd in rounds:
        for r in jsonl(flow(arm, rd, "results.jsonl")):
            if r["prompt_id"] in train:
                per.setdefault(r["prompt_id"], {}).setdefault(rd, []).append(r["grade"]["pass"])
    with open(os.path.join(sb, "scores_train.tsv"), "w") as f:
        f.write("case\t" + "\t".join(rounds) + "\n")
        for cid in sorted(per):
            f.write(cid + "\t" + "\t".join(
                f"{sum(per[cid][rd]) / len(per[cid][rd]):.2f}" if rd in per[cid] else "" for rd in rounds) + "\n")
    hist = ["# Earlier proposals", ""] + [f"- {h['round']}: {h['change']} ({'kept' if h['decision'] == 'keep' else 'reverted'})"
                                          for h in st["history"]]
    if len(hist) == 2:
        hist.append("- none yet")
    hist += ["", f"The current version is {cur}. The traces and results here are the current version's."]
    open(os.path.join(sb, "history.md"), "w").write("\n".join(hist) + "\n")
    nf = st["noise_floor"]
    n_test = len(st["test_ids"]) * REPS
    prompt = open(os.path.join(HERE, "prompts", "categorize.md" if a.categorize else "analyzer.md")).read()
    prompt = (prompt.replace("{grader_description}", grader_text(arm)).replace("{sandbox}", sb)
              .replace("{floor_pts}", f"{100 * nf:.1f}").replace("{floor_rows}", str(round(nf * n_test)))
              .replace("{test_rows}", str(n_test)))
    open(os.path.join(sb, "BRIEF.md"), "w").write(prompt)
    print(sb)


def cmd_apply(a):
    arm, rnd = a.arm, a.round
    st = state(arm)
    sb = os.path.join(SANDBOXES, arm, rnd)
    change = os.path.join(sb, "out", "change.md")
    art_new = os.path.join(sb, "out", "artifact.json")
    if not os.path.exists(change):
        raise SystemExit(f"{change} missing")
    os.makedirs(flow(arm, rnd), exist_ok=True)
    shutil.copy(change, flow(arm, rnd, "change.md"))
    if not os.path.exists(art_new):
        print(f"{arm}/{rnd}: the analyzer proposed no change: {open(change).readline().strip()}")
        return
    shutil.copy(art_new, flow(arm, rnd, "artifact.json"))
    old = json.load(open(flow(arm, st["current"], "artifact.json")))
    new = json.load(open(flow(arm, rnd, "artifact.json")))
    if set(new) != {"decision_instructions", "criteria"} or set(new["criteria"]) != set(old["criteria"]):
        raise SystemExit(f"{arm}/{rnd}: artifact has the wrong shape")
    for k, v in new["criteria"].items():
        if v.split(":")[0] != old["criteria"][k].split(":")[0]:
            raise SystemExit(f"{arm}/{rnd}: criteria[{k}] changed its action word")
    diff = difflib.unified_diff(json.dumps(old, indent=1).splitlines(True), json.dumps(new, indent=1).splitlines(True),
                                f"a/hillclimb/{arm}/{st['current']}/artifact.json", f"b/hillclimb/{arm}/{rnd}/artifact.json")
    open(flow(arm, rnd, "change.patch"), "w").write("".join(diff))
    print(f"{arm}/{rnd}: applied: {open(change).readline().strip()}")


def cmd_categorized(a):
    """Record a Step 4.5 categorization made after round <round>; no change is applied."""
    arm, rnd = a.arm, a.round
    st = state(arm)
    sb = os.path.join(SANDBOXES, arm, rnd + "-categorize")
    cat = json.load(open(os.path.join(sb, "out", "categorize.json")))
    d = flow(arm, f"categorize_after_{rnd}")
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(sb, "out", "categorize.json"), os.path.join(d, "categorize.json"))
    shutil.copy(os.path.join(sb, "out", "change.md"), os.path.join(d, "change.md"))
    st["categorized"] = True
    st["categorization"] = {"after": rnd, "counts": cat["counts"]}
    save_state(arm, st)
    write_narrative(arm)
    print(f"{arm}: categorization after {rnd}: {cat['counts']}")


def cmd_status(_):
    for arm in ARMS:
        if not os.path.exists(flow(arm, "_state.json")):
            print(f"{arm}: not initialized")
            continue
        st = state(arm)
        b = st.get("best") or {}
        print(f"{arm}: round {st['current_round']}, current {st['current']}, best {b.get('name')} "
              f"{b.get('test_score', float('nan')):.3f}, flat {st['flat_streak']}, "
              f"categorized {st['categorized']}, stopped {st['stopped']}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("ingest")
    p.add_argument("arm"), p.add_argument("round"), p.add_argument("run_id"), p.add_argument("--rerun", action="store_true")
    p = sub.add_parser("decide")
    p.add_argument("arm"), p.add_argument("round")
    p = sub.add_parser("sandbox")
    p.add_argument("arm"), p.add_argument("round"), p.add_argument("--categorize", action="store_true")
    p = sub.add_parser("apply")
    p.add_argument("arm"), p.add_argument("round")
    p = sub.add_parser("categorized")
    p.add_argument("arm"), p.add_argument("round")
    sub.add_parser("status")
    a = ap.parse_args()
    {"init": cmd_init, "ingest": cmd_ingest, "decide": cmd_decide, "sandbox": cmd_sandbox,
     "apply": cmd_apply, "categorized": cmd_categorized, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    main()
