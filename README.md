# judge-tpr-tnr

Code and data for a planned paper on measuring an LLM judge's true positive rate (TPR) and true negative rate (TNR) against labeled data it has not seen, and using them to correct the pass rate the judge reports.

It follows the method taught in [AI Evaluation for Engineers and PMs](https://maven.com/parlance-labs/evals) (Hamel Husain and Shreya Shankar) and applies it to the judge from my previous paper, [Is This Run Valid?](https://bfalkowski.github.io/writing/run-valid.html) ([code](https://github.com/bfalkowski/eval-run-validity)). That eval has something most evals lack: a deterministic reference for every item. So the corrected pass rate can be checked against the true pass rate, not just reported.

## Phase 0: what the paper 2 judge already shows

`analysis/phase0.py` reads the paper 2 judge's votes on the 600 items of its 10 clean runs (60 tickets x 10 runs) and compares the first vote with the deterministic score. Full output: [`phase0/RESULTS.md`](phase0/RESULTS.md).

| | Judge PASS | Judge FAIL |
|---|---|---|
| Correct (498) | 435 | 63 |
| Wrong (102) | 84 | 18 |

TPR is 0.873 and TNR is 0.176. The judge passed 84 of the 102 wrong resolutions. TPR + TNR - 1 is 0.050, and the correction divides by that number.

Measured on half the tickets and applied to the other half, over 2,000 random splits:

- the correction was undefined (TPR + TNR <= 1) in 33.5% of splits;
- where it was defined, the corrected rate was off by a median of 19.3 points, against 4.7 points for the judge's raw pass rate, and was further from the truth than the raw rate in 92.8% of splits.

For a single 30-ticket run, I checked 95% intervals on 200 splits; the correction was defined on 128 of them. An interval that resamples tickets contained the true rate in 96% of those but had a median width of 100 points, which is the honest answer for this judge. judgy 0.1.0's interval, which resamples items and holds the run's pass rate fixed, contained the true rate in 44%.

Two things follow. The 600 items are 66 distinct ticket/action pairs, so every split and every interval has to be by ticket. And this judge is far from the course's bar of TPR and TNR above 90% on dev, so the paper starts by trying to get it there.

## Study design

**Judge items.** Each v2 ticket is paired with each of the four actions (refund, reship, escalate, reply). An item is PASS when the action is the one the reference policy gives, FAIL otherwise. That gives 240 items, 60 PASS and 180 FAIL, without needing the agent to make mistakes. Built by `data/build.py`.

**Labels.** The reference policy (`judge/policy.py`, copied unchanged from paper 2) is my reading of the support policy written as code. Before any number is treated as final, the tickets where the judge and the reference disagree get a hand audit, because two policy rules were already arguable in paper 2.

**Why the test split is new tickets.** Every v2 ticket has already been seen, in paper 2 and in phase 0, including which ones the judge gets wrong. A variant tuned with that knowledge cannot be tested on the same tickets. So v2 is split by ticket into train (15%, few-shot examples) and dev (85%, iteration), stratified by difficulty tag, and the test split is a new set, v3, written and frozen before any judge sees it. v3 needs roughly 50 tickets so the test split has about 50 PASS items.

**Freeze.** A variant is tuned on dev only, including the choice of threshold on Jev's raw `noul` score. `freeze.py` records the variant's fingerprint and threshold in `freeze.json`; `run_judge.py` refuses to run the test split for anything else.

**Correction.** `judge/estimate.py` computes the corrected pass rate with an interval that resamples tickets on both the labeled side and the run being estimated, and reports how often the correction was undefined. Its point estimate matches judgy's (tested).

Research questions and the paper plan are in [`paper/outline.md`](paper/outline.md).

## What is here

| Path | What it does |
|---|---|
| `judge/policy.py` | The support policy text and reference function, unchanged from paper 2 (checksum in `data/CHECKSUMS.json`) |
| `judge/judges.py` | Judge variants. `p2` is paper 2's judge, verbatim. |
| `judge/jev.py`, `judge/jev_stub.py` | Jev client that keeps the raw `noul` score; a local stand-in for tests |
| `judge/estimate.py` | TPR, TNR, corrected pass rate, ticket-level bootstrap |
| `data/v2/` | Paper 2's tickets and orders, unchanged |
| `data/build.py` | Builds `data/items_v2.jsonl` and the ticket-level split `data/splits/v2.json` |
| `phase0/` | Paper 2's clean-run judge votes (`fetch_paper2.py`, pinned to a commit) and the phase 0 results |
| `run_judge.py` | Runs one variant over one split; writes `runs/<id>/manifest.json` and `judgments.jsonl` |
| `analysis/rates.py` | TPR and TNR for a run, with ticket-level intervals and a threshold sweep |
| `freeze.py` | Freezes a variant and threshold before the test split |
| `.github/workflows/` | `ci` (tests, phase 0 reproduces), `secrets` (gitleaks), `judge` (judge runs), `collect` (runs to the `data` branch) |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pre-commit -r requirements.lock
pre-commit install
```

Put the Jev key in `.env` (gitignored) as `TYPESAFE_API_KEY=...`, and add it as a repository secret for the `judge` workflow.

## Running it

```bash
# no key needed
python -m pytest -q tests
python analysis/phase0.py
JEV_BACKEND=stub python run_judge.py --variant p2 --dataset v2 --split dev --run-id stub-dev
python analysis/rates.py runs/stub-dev

# real Jev; paper runs go through the `judge` workflow instead
python run_judge.py --variant p2 --dataset v2 --split dev --run-id p2-dev-01
```

A p2 dev run is 204 items x 2 calls, about 410 calls and about a cent.

## Sources

- `judge/policy.py`, `data/v2/`: [eval-run-validity](https://github.com/bfalkowski/eval-run-validity) `main` at `12a0eef`
- `phase0/paper2_clean_items.jsonl`: eval-run-validity `data` branch at `da1d6ae` (see `phase0/SOURCE.json`)
- Estimator cross-check: [judgy](https://pypi.org/project/judgy/) 0.1.0

Not affiliated with TypeSafe or Parlance Labs.
