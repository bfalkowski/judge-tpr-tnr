# Hill climbing an agent against an LLM judge: study design

Recorded 2026-10-27, before any agent or judge was run on the tickets used here (v5).

## Question

`/claude-api hillclimb` improves an app against a fixed eval, one change per round, with a train/test split to catch
overfitting. When the eval's grader is an LLM judge, the score it climbs is the judge's pass rate, not the true pass
rate. This study asks:

1. How much of the gain the loop reports is real, for judges of different quality?
2. Does climbing against a judge move the agent's mistakes into the judge's blind spots?
3. Which of the skill's own checks catch a bad judge, and which would TPR/TNR checks catch?

The answer key from the judge study (`judge/policy.py`) makes all three measurable: every agent decision has a known
correct action, and the loop never sees it.

## What is climbed

Paper 2's support agent, the `clean` config (policy v1, full context), imported unchanged at eval-run-validity
`12a0eef`. For each ticket it asks Jev (`jev-latest`) to pick one of four actions.

**The artifact the loop may change:** the agent's decision instructions (one string sent with every decision) and the
descriptions of the four actions. The actions themselves and their order stay fixed.

**Off-limits:** the policy text, the fields the agent sees (policy, today, ticket, order, stock), the model, the code,
and the grader. These are recorded as the scope in each arm's `_state.json`.

Baseline artifact: paper 2's defaults, "Which action does the support policy call for on this ticket?" and its four
action descriptions (`hillclimb/baseline_agent.json`).

## Tickets and splits

v5: 400 new tickets from the v3 generator (`data/make_data_v3.py --version v5 --n 400 --seed 20261027`), split by
ticket at random within each customer framing (`data/build.py`, seed 20261007):

| Split | Tickets | Used by the loop |
|---|---|---|
| climb_train | 120 | the analyzer reads these traces; scored every round |
| climb_test | 120 | scored every round, never read; picks the winner and is the headline, as the skill says |
| holdout | 160 | never used by the loop; scored only in the analysis |

Each version of the agent runs every v5 ticket twice (2 reps). The skill's noise floor for a pass rate on climb_test
is about 1/sqrt(120 x 2) = 0.065.

## Arms

Four arms climb the same baseline on the same split. Each uses one fixed grader for every round:

| Arm | Grader | TPR / TNR on the judge study's test split |
|---|---|---|
| `key` | the answer key, as a programmatic check; the explanation shows the expected action | 1 / 1 |
| `c3` | the frozen judge from the judge study (Claude Haiku 4.5, step 3), threshold 0.5 | 0.927 / 0.919 |
| `p2` | paper 2's judge (Jev, one sentence), threshold 0.5 | 0.792 / 0.532 |
| `lenient` | the step 2 judge (Jev, definitions and examples), threshold 0.3 | 1.000 / 0.645 |

`lenient` is included because it never failed a correct decision on the judge study's dev or test split. A
spot-check of the judge's failures, which is the check the skill asks for before round 1, finds no grader errors,
while the judge passes about a third of real mistakes.

**Judge verdicts are computed once.** A judge's input is fully determined by the ticket, order, stock and action, so
every judge is run on all four actions of every v5 ticket before the loop starts (`judge` workflow, dataset v5,
split all: 1,600 items; c3 one call per item, the Jev judges two calls with call 1 used). The loop then looks up the
verdict for whatever action the agent picks. This makes each judge deterministic within the study. A real climb
would also see the judge's run-to-run noise.

## The loop

Each arm follows `vendor/claude-api-evals/.../eval-hillclimb.md` Steps 3 to 5 as written. Where the skill leaves a
choice to the user or to judgment, this study fixes it in advance:

- **Goal:** raise the pass rate on the arm's grader. No guardrail metrics (cost is fixed by the model).
- **Analyzer:** one fresh subagent per round, given a sandbox folder with only: the current artifact, the train rows of
  the current version's results (judge grade, and the judge's explanation where the grader gives one), the train traces
  of the current version, the train rows of the per-round score history, the scope and off-limits list, the target
  metric, the noise floor, and a one-line history of earlier proposals marked kept or reverted (no test numbers). It is
  told to read nothing outside the sandbox and to list the files it read. The prompt is `hillclimb/prompts/analyzer.md`.
- **De-fluff:** the analyzer does the de-fluff pass itself. The outer session applies the proposed artifact verbatim,
  so nothing it knows about the answer key can enter a change.
- **Keep or revert** (`hillclimb/decide.py`), on the arm's grader, comparing the candidate with the current version:
  keep when train and test both rise; revert when train rises and test does not, or when train falls; when test rises
  and train does not, run the candidate once more and keep it only if test rises again. The current version is always
  the best kept version so far.
- **Stall:** after two consecutive rounds in which the best test score does not rise by at least the noise floor, one
  categorization round (`hillclimb/prompts/categorize.md`) buckets every remaining train failure by the skill's Step 4.5
  table. The grader is off-limits here, so a "grader disagreement" bucket is recorded, not acted on.
- **Stop:** after three consecutive rounds without a rise of at least the noise floor in the best test score, or
  after 8 content rounds.
- **Step 0.5 and the eval audit:** the checks that concern the grader are computed for every arm from the baseline and
  reported (Section "Measures"), but the loop proceeds in every arm whatever they show. This is what lets the study see
  what each check would have caught.

The outer session (Claude, running this study) makes keep, revert and stop decisions only from `decide.py`'s output,
which reads the arm's grader scores on climb_train and climb_test. Answer-key scores and everything on holdout are
written by `hillclimb/score.py` to `hillclimb/_sealed/` and are not opened until every arm has stopped.

## Measures

1. **Reported versus true gain.** The skill's headline, the grader's test-score change from baseline to winner, against
   the answer key's change on climb_test and on holdout.
2. **Selection.** The winner's true score on climb_test, which picked it, against its true score on holdout.
3. **Decisions.** For each round, whether the keep or revert call matches the call the same rule makes on answer-key
   scores.
4. **Blind spots.** For each version, the judge's TPR and TNR on that version's decisions (climb_test and holdout), and
   the share of the version's true mistakes that the judge passes.
5. **Pre-loop checks.** For each judge, from the baseline: the share of grader errors among the ten lowest-scoring
   train cases (the skill's spot-check; the audit's threshold is about one in ten); agreement with the answer key on 40
   random train decisions (the audit's threshold is about 90%); and TPR and TNR with intervals on the train decisions
   (the primer's check: both at 0.9 or more).
6. **Categorization.** Of the train failures the analyzer puts in the grader-disagreement bucket, the share that are
   real judge errors.

## Expectations, recorded before the runs

- `key` and `c3`: the reported test gain is within noise of the true gain.
- `lenient`: the reported level is inflated, the reported gain is larger than the true gain, and the judge's TNR on the
  winner's decisions is no higher than on the baseline's.
- `p2`: some rounds chase the judge's false fails, so the true gain is smaller than in `key` and may be negative.
- The skill's failure spot-check flags `p2` but not `lenient`. TPR/TNR checks flag both.
- In every arm, the winner's true climb_test score is at or above its true holdout score.

## Budget

c3 on 1,600 items costs about $3 at the judge study's per-call cost. Jev judging and every agent run together cost under
$1. Each workflow run has a spend cap. The analyzer subagents run in this session and do not use the repository's
API keys.
