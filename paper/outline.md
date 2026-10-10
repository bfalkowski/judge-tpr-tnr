# Paper outline (working)

Working title: **Hill Climbing an LLM Judge on TPR and TNR: A Worked Example With an Answer Key**

## What the paper is

A step-by-step walkthrough of the standard way to build and validate an LLM judge: labeled traces split into
train, dev and test; refine the judge on dev until its true positive rate (TPR) and true negative rate (TNR)
pass a target; run it once on test; then use TPR and TNR to correct the pass rate it reports on new traces.

Most write-ups of this loop cannot show whether a step really helped, because the labels are one person's
judgment. Here the labels come from code: the support policy from my previous paper is written as a function,
so every trace has a known correct answer. The reader can see the true effect of each step, and the corrected
pass rate can be checked against the true one. In practice the labels come from a domain expert; the procedure
is the same.

This is a worked example, not a recommendation to judge this task with an LLM. A rule that can be written as
code should be checked by code. The policy stands in for a criterion that would normally need judgment.

## Sources (public only)

The course this is based on (AI Evaluation for Engineers and PMs, Husain and Shankar) is cited by name; its
reader is not quoted. Each technical piece has a public source:

| Piece | Source |
|---|---|
| The loop: expert labels, separate TPR and TNR, 10-20 / 40-45 / 40-45 split, 30-50 per label, iterate to over 90% | Husain, "Using LLM-as-a-Judge For Evaluation: A Complete Guide", hamel.dev, 2024 |
| The exact procedure: splits, TPR/TNR above 0.9 (0.8 minimum), what to try when it stalls, one run on test, correction with a bootstrap interval | `validate-evaluator` skill, github.com/ai-evals-course/evals-skills (Shankar and Husain) |
| Why the criteria change while you grade | Shankar et al., "Who Validates the Validators?", UIST 2024 |
| Synthetic inputs from dimensions, then text | `generate-synthetic-data` skill, same repo |
| LLM-as-judge | Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", NeurIPS 2023 |
| TPR and TNR are sensitivity and specificity | Altman and Bland, "Diagnostic tests 1: sensitivity and specificity", BMJ 1994 |
| TPR + TNR - 1 | Youden, "Index for rating diagnostic tests", Cancer 1950 |
| The correction | Rogan and Gladen, "Estimating prevalence from the results of a screening test", Am J Epidemiol 1978 |
| Bootstrap intervals | Efron and Tibshirani, An Introduction to the Bootstrap, 1993 |
| Resampling clustered data | Field and Welsh, "Bootstrapping clustered data", JRSS B 2007 |
| How many few-shot examples help | Min et al., "Rethinking the Role of Demonstrations", EMNLP 2022 |
| Automating the loop | Khattab et al., DSPy, 2024 |
| Reference code for the correction | judgy, github.com/ai-evals-course/judgy |

## Structure

1. **The problem.** Paper 2's judge was consistent and wrong on a quarter of items. Agreement between two calls is not a check; a reference is.
2. **The loop, in my words**, one short paragraph per step, with the sources above.
3. **Setup.**
   - The agent: paper 2's support agent (Jev), unchanged, under four of its configs.
   - The answer key: the reference policy function.
   - Tickets: v2 (60 hand-written, from paper 2) and v3 (240 generated from the policy's dimensions).
   - Labeled data: every distinct decision the agent made, 402 items, PASS when it matches the policy.
   - Splits by ticket: train = v2 (86 items, few-shot pool), dev = half of v3 (158 items: 87 pass, 71 fail), test = the other half (158: 96 pass, 62 fail).
4. **Error analysis of the baseline.** Two failure groups: day counting at the 14- and 30-day cutoffs, and the $500 limit when out of stock. In most, the customer asks for the wrong action or misstates the dates.
5. **The climb on dev.** One change per step, each chosen from the previous step's errors, every step reported. Table in `paper/climb_table.md`, chart of TPR and TNR by step.
6. **Freeze and test.** One run of the frozen judge on test. Dev against test.
7. **Using the judge.** Correct its pass rate on agent runs and compare with the true pass rate, with intervals.
8. **What the answer key showed about the method.**
   - Constructed failures overstate TNR (paper 2's judge: 0.98 on constructed wrong actions, 0.17 on the agent's own).
   - A judge on the same model as the agent passes the mistakes the agent makes.
   - The correction is unusable until TPR + TNR is well above 1 (paper 2's judge: 0.05; undefined in a third of splits).
   - Items repeat per ticket, so an interval that resamples items is too narrow (44% coverage for a nominal 95%); resample tickets.
9. **Limitations.** One domain; generated tickets are formulaic; the reference policy is my reading of the policy text; the agent and the first judge are both Jev.

## Status

| Step | Status |
|---|---|
| Labeled data and splits | Done: 402 items, dev 87/71, test 96/62 |
| Climb steps 0 to 2 (Jev) | Done: TPR 0.84 to 0.91, TNR 0.52 to 0.82 |
| Climb step 3 (Claude) | Built; waiting for `ANTHROPIC_API_KEY` |
| Freeze and test | Not run |
| Correction on agent runs | Estimator built; not run |
| Phase 0 and constructed-items results | Done (`phase0/RESULTS.md`, `paper/preliminary.md`) |
