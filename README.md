# judge-tpr-tnr

Code and data for a worked example of improving an LLM judge by hill climbing on its true positive rate (TPR) and true negative rate (TNR), with an answer key for every trace.

The judge decides whether a support agent's resolution follows a support policy. The agent and the policy come from my previous paper, [Is This Run Valid?](https://bfalkowski.github.io/writing/run-valid.html) ([code](https://github.com/bfalkowski/eval-run-validity)). The policy is written as code, so every label is known, and each step of the judge's refinement can be checked against the truth instead of against one person's judgment.

The method follows the judge-validation loop taught in AI Evaluation for Engineers and PMs (Husain and Shankar), as published in Hamel Husain's [LLM-as-a-judge guide](https://hamel.dev/blog/posts/llm-judge/) and the [`validate-evaluator`](https://github.com/ai-evals-course/evals-skills) skill. Paper plan and sources: [`paper/outline.md`](paper/outline.md).

## The climb so far (dev)

| Step | Change | Model | TPR | TNR |
|---|---|---|---|---|
| 0 | Paper 2's judge: one sentence, no definitions or examples | Jev | 0.84 | 0.52 |
| 1 | Precise Pass/Fail definitions from step 0's errors | Jev | 0.94 | 0.73 |
| 2 | Four train examples with critiques at the day cutoffs | Jev | 0.91 | 0.82 |
| 3 | Same definitions and examples on Claude, reasoning then answer | Claude Haiku 4.5 | 0.95 | 0.97 |

158 dev items (87 pass, 71 fail), every one a real agent decision. Intervals and error counts: [`paper/climb_table.md`](paper/climb_table.md). Target: both above 0.9.

## Data

| | Tickets | Labeled items | Pass | Fail | Use |
|---|---|---|---|---|---|
| train | 60 (v2) | 86 | 58 | 28 | few-shot examples only |
| dev | 120 (v3) | 158 | 87 | 71 | refining the judge |
| test | 120 (v3) | 158 | 96 | 62 | one run of the frozen judge |

- **Tickets.** v2 is paper 2's 60 hand-written tickets. v3 is 240 tickets generated from the policy's dimensions (issue, status, days around the 14- and 30-day cutoffs, totals around $500, stock) and a customer framing (plain, demand, wrong claim, angry, indirect): `data/make_data_v3.py`.
- **Agent outputs.** Paper 2's agent, imported unchanged at commit `12a0eef`, under four of its configs: clean, "keep the customer happy" instructions, stock removed, and the old policy without the $500 limit. v2 decisions come from paper 2's runs (`agent/harvest_paper2.py`); v3 decisions from this repo's runs (`agent/run_agent.py`, `agent` workflow).
- **Labels.** One item per distinct (ticket, action) the agent produced; PASS when the action is the one the reference policy (`judge/policy.py`) gives. `data/build_labeled.py`.
- **Splits** are by ticket. Test is not looked at until a judge is frozen; `run_judge.py` refuses the test split for any judge not recorded in `freeze.json`.

## What is here

| Path | What it does |
|---|---|
| `judge/judges.py` | Every judge version, one per climb step, each with a fingerprint |
| `judge/jev.py`, `judge/claude.py` | Judge backends; the raw score or the reasoning is kept |
| `judge/estimate.py` | TPR, TNR, corrected pass rate, ticket-level bootstrap |
| `run_judge.py` | Runs one judge on one split; `judge` workflow runs it in CI and commits to the `data` branch |
| `analysis/rates.py`, `analysis/errors.py` | TPR/TNR with intervals and a threshold sweep; errors grouped by the rule that decides them |
| `analysis/climb.py` | Rebuilds the climb table from the runs listed in `paper/climb.json` |
| `freeze.py` | Freezes a judge and threshold before the test split |
| `phase0/`, `paper/preliminary.md` | Earlier results: paper 2's judge on its own runs, and on constructed wrong actions |
| `.github/workflows/` | `ci`, `secrets`, `agent`, `judge`, `collect` |

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pre-commit -r requirements.lock && pre-commit install
python -m pytest -q tests                      # no keys needed

# a judge step on dev, locally (keys in .env: TYPESAFE_API_KEY, ANTHROPIC_API_KEY)
python run_judge.py --variant j2 --dataset labeled --split dev --run-id j2-dev
python analysis/rates.py runs/j2-dev
python analysis/errors.py runs/j2-dev

# or through CI, which commits the run to the data branch
gh workflow run judge.yml -f variant=j2 -f dataset=labeled -f split=dev -f backend=api
git fetch origin data && python analysis/climb.py
```

A Jev step on dev costs about a cent; the Claude Haiku step cost $0.57.

## Sources

- `judge/policy.py`, `data/v2/`: [eval-run-validity](https://github.com/bfalkowski/eval-run-validity) `main` at `12a0eef`
- Paper 2 agent decisions and phase 0 items: eval-run-validity `data` branch at `da1d6ae`
- Estimator cross-check: [judgy](https://pypi.org/project/judgy/) 0.1.0

Not affiliated with TypeSafe, Anthropic or Parlance Labs.
