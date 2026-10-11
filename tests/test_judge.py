"""Tests. No key, no network: Jev is the local stub."""

import hashlib
import json
import os
import random
import subprocess
import sys

import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "data"))

from judge import data, estimate, judges  # noqa: E402
import build  # noqa: E402  (data/build.py)


def sha(path):
    return hashlib.sha256(open(os.path.join(ROOT, path), "rb").read()).hexdigest()


# ------------------------------------------------------------------ pinned inputs

def test_pinned_files_match_checksums():
    want = json.load(open(os.path.join(ROOT, "data", "CHECKSUMS.json")))
    for key, digest in want.items():
        path = key if key.startswith("judge/") else os.path.join("data", key)
        assert sha(path) == digest, key


def test_phase0_source_matches_its_record():
    src = json.load(open(os.path.join(ROOT, "phase0", "SOURCE.json")))
    assert sha("phase0/paper2_clean_items.jsonl") == src["sha256"]
    assert src["rows"] == 600


# ------------------------------------------------------------------ items and split

def test_every_ticket_has_one_pass_item_equal_to_its_expected_action():
    items = data.build_items("v2")
    assert len(items) == 240
    by_ticket = {}
    for it in items:
        by_ticket.setdefault(it["ticket_id"], []).append(it)
    for tid, its in by_ticket.items():
        passes = [it for it in its if it["label"] == 1]
        assert len(passes) == 1 and passes[0]["action"] == passes[0]["expected"], tid


def test_committed_items_match_a_fresh_build():
    fresh = [json.dumps(it, sort_keys=True) for it in data.build_items("v2")]
    committed = [line.rstrip("\n") for line in open(data.items_path("v2"))]
    assert fresh == committed


def test_committed_split_is_reproducible_and_by_ticket():
    committed = json.load(open(data.split_path("v2")))
    assert committed == json.loads(json.dumps(build.make_split("v2", build.PLAN["v2"])))
    s = committed["tickets"]
    assert len(s) == 60 and set(s.values()) == {"train", "dev"}
    assert committed["counts"] == {"dev": 51, "train": 9}
    for it in data.load_items("v2"):  # every item of a ticket lands in that ticket's split
        assert it["ticket_id"] in s


def test_largest_remainder_allocation_sums():
    for n in range(1, 80):
        assert sum(build.allocate(n, {"a": 0.15, "b": 0.425, "c": 0.425}).values()) == n


# ------------------------------------------------------------------ judge

def test_p2_state_matches_paper2_judge():
    it = data.load_items("v2")[0]
    st = judges.p2_state(it)
    assert list(st) == ["policy", "today", "ticket", "order", "stock", "agent_resolution"]
    assert judges.VARIANTS["p2"]["instructions"] == (
        "Does the agent's resolution follow the support policy for this ticket and order?")
    assert judges.VARIANTS["p2"]["question"] == "follows_policy"


def test_fingerprint_changes_when_instructions_change(monkeypatch):
    before = judges.fingerprint("p2")
    monkeypatch.setitem(judges.VARIANTS["p2"], "instructions", "something else")
    assert judges.fingerprint("p2") != before


# ------------------------------------------------------------------ estimator

def test_rates_and_correction_by_hand():
    labels = [1, 1, 1, 1, 0, 0, 0, 0]
    preds = [1, 1, 1, 0, 1, 0, 0, 0]
    r = estimate.rates(labels, preds)
    assert (r["tp"], r["fn"], r["fp"], r["tn"]) == (3, 1, 1, 3)
    assert r["tpr"] == 0.75 and r["tnr"] == 0.75
    assert estimate.corrected(0.5, 0.75, 0.75) == pytest.approx(0.5)
    assert estimate.corrected(0.875, 0.75, 0.75) == 1.0      # clipped
    assert estimate.corrected(0.5, 0.5, 0.5) is None          # TPR + TNR = 1
    assert estimate.corrected(0.5, 0.3, 0.4) is None          # worse than chance


def test_point_estimate_matches_judgy():
    judgy = pytest.importorskip("judgy")
    rng = random.Random(3)
    for _ in range(20):
        labels = [int(rng.random() < 0.6) for _ in range(80)]
        preds = [y if rng.random() < 0.85 else 1 - y for y in labels]
        run = [int(rng.random() < 0.7) for _ in range(60)]
        r = estimate.rates(labels, preds)
        ours = estimate.corrected(sum(run) / len(run), r["tpr"], r["tnr"])
        if ours is None:
            continue
        theirs, _, _ = judgy.estimate_success_rate(labels, preds, run, bootstrap_iterations=50)
        assert ours == pytest.approx(theirs)


def test_ticket_bootstrap_is_seeded_and_reports_undefined():
    lab = [{"ticket_id": f"T{i // 4}", "label": int(i % 4 == 0), "pred": int(i % 4 == 0 or i % 7 == 0)}
           for i in range(80)]
    run = [{"ticket_id": f"U{i}", "pred": int(i % 3 != 0), "label": int(i % 3 != 0)} for i in range(30)]
    a = estimate.estimate(lab, run, iterations=500, seed=4)
    b = estimate.estimate(lab, run, iterations=500, seed=4)
    assert a == b
    assert 0 <= a["undefined_share"] <= 1 and a["n_labeled_tickets"] == 20
    assert a["true_rate"] == pytest.approx(20 / 30)


def test_phase0_headline_numbers():
    rows = [json.loads(line) for line in open(os.path.join(ROOT, "phase0", "paper2_clean_items.jsonl"))]
    r = estimate.rates([int(x["correct"]) for x in rows], [int(x["judge_votes"][0]) for x in rows])
    assert (r["tp"], r["fn"], r["fp"], r["tn"]) == (435, 63, 84, 18)


# ------------------------------------------------------------------ runner

def run(args, tmp_path, extra_env=None):
    env = {**os.environ, "JEV_BACKEND": "stub", "JEV_BACKOFF_S": "0", **(extra_env or {})}
    return subprocess.run([sys.executable, "run_judge.py", "--out", str(tmp_path), *args],
                          cwd=ROOT, env=env, capture_output=True, text=True)


def test_stub_run_on_dev_writes_raw_scores(tmp_path):
    p = run(["--variant", "p2", "--dataset", "v2", "--split", "dev", "--run-id", "t1", "--limit", "8"], tmp_path)
    assert p.returncode == 0, p.stderr
    rows = [json.loads(line) for line in open(tmp_path / "t1" / "judgments.jsonl")]
    assert len(rows) == 16 and all(0 <= r["noul"] <= 1 for r in rows)
    m = json.load(open(tmp_path / "t1" / "manifest.json"))
    assert m["split"] == "dev" and m["fingerprint"] == judges.fingerprint("p2") and m["errored_calls"] == 0
    train = {it["ticket_id"] for it in data.items_for("v2", "train")}
    assert not train & {r["ticket_id"] for r in rows}


def test_test_split_refused_without_a_matching_freeze(tmp_path):
    p = run(["--split", "test", "--run-id", "t2"], tmp_path)
    assert p.returncode != 0 and ("freeze.json" in p.stderr or "not the frozen judge" in p.stderr)
    assert not (tmp_path / "t2").exists()


def test_api_backend_without_a_key_stops_before_writing(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("TYPESAFE_API_KEY", "JEV_BACKEND")}
    p = subprocess.run([sys.executable, "run_judge.py", "--out", str(tmp_path), "--split", "dev",
                        "--run-id", "t3"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert p.returncode != 0 and "TYPESAFE_API_KEY" in p.stderr
    assert not (tmp_path / "t3").exists()


# ------------------------------------------------------------------ labeled set

def test_labeled_items_are_real_decisions_labeled_by_the_policy():
    items = data.load_items("labeled")
    assert len({it["item_id"] for it in items}) == len(items)
    for it in items:
        assert it["label"] == int(it["action"] == it["expected"])
        assert sum(it["sources"].values()) >= 1


def test_labeled_split_is_by_ticket_and_train_is_v2_only():
    s = data.load_split("labeled")
    for it in data.load_items("labeled"):
        assert (s[it["ticket_id"]] == "train") == (it["dataset"] == "v2")
    counts = {sp: [0, 0] for sp in ("dev", "test")}
    for it in data.load_items("labeled"):
        if s[it["ticket_id"]] in counts:
            counts[s[it["ticket_id"]]][it["label"]] += 1
    for sp, (fail, ok) in counts.items():
        assert fail >= 30 and ok >= 30, (sp, fail, ok)
