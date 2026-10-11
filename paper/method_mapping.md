# How the study follows the vendored skills

Skills: `vendor/evals-skills/` (ai-evals-course/evals-skills at commit `80d5f7b`, unmodified).

## validate-evaluator

| Skill step | What the skill says | What this study did | Same? |
|---|---|---|---|
| Prerequisite: labels | ~100 binary labels per failure mode, ~50/50, from one domain expert | Labels from the reference policy function (code). 402 items for one criterion ("does the resolution follow the policy"); dev 87/71, test 96/62. Not deliberately balanced; that is how the agent's decisions fell | Departs: labels from code, not a person; one criterion, not one per failure mode |
| 1. Splits | Train 10-20%, dev 40-45%, test 40-45%; random split stratified by label; 30-50 per class across dev and test | Train 86 items (21%), dev 158 (39%), test 158 (39%). Split by ticket, not by item, because items share tickets. Train is all of v2; dev and test split v3 50/50 within framing and has-a-failure groups | Proportions and counts match; splitting unit differs |
| 1. Train examples | "Only clear-cut Pass and Fail cases" | The four few-shot examples sit exactly at the 14- and 30-day cutoffs, because that is where the judge failed | Departs: boundary cases, not clear-cut |
| 2-3. TPR and TNR on dev | Pass is positive; TPR and TNR, not precision, recall or accuracy | Same definitions (`judge/estimate.py`) | Same |
| 4. Inspect disagreements | Read every false pass and false fail; fix wording, examples, rules, or split the criterion | `analysis/errors.py` groups every disagreement by the rule that decides it; each step's change came from that | Same |
| 5. Iterate, stopping rule | Target TPR and TNR > 90%; minimum > 80% | Steps 1 and 2 changed the prompt; step 3 changed the model. Stopped after step 3 at 0.954 / 0.972 | Same |
| 5. If alignment stalls | Both low: more capable LLM. One low: inspect it. Both plateau: decompose. Wrong on input types: targeted examples. Labels inconsistent: re-examine | Targeted examples (step 2), then a more capable LLM (step 3) when TNR stayed low. Never decomposed. Found one label ambiguity; kept the labels and reported results with and without those items | Mostly same; no decomposition step |
| 6. Test once | Run exactly once; do not iterate after | One run of the frozen judge (`gh38115612251`); code refuses test for any judge not in `freeze.json` | Same |
| 6. (extra) | | After the freeze, the step 0 and step 2 judges were also run on test, recorded as post-hoc, for the Section 8 comparison. Nothing changed the frozen judge | Addition |
| 7. Correction | Rogan-Gladen with TPR and TNR from test; clip to [0, 1]; invalid near TPR + TNR - 1 = 0 | Same formula and inputs, applied to four agent runs on v4, a batch in no split | Same |
| 8. Interval | Bootstrap: resample test items, p_obs fixed; or `judgy` | Resample tickets on both the test set and the new run. judgy's item-level interval also reported | Departs: ticket-level, includes p_obs uncertainty |
| Practical: pin models | Dated snapshot id, not an alias | Claude pinned to `claude-haiku-4-5-20251001`. Jev called through the alias `jev-latest` (no dated id used) | Partly |
| Anti-pattern: raw scores without correction | "If you report an aggregate pass rate, apply the Rogan-Gladen formula" | Applied it, and found the corrected point estimate further from the truth than the raw rate for the frozen judge, because its test TPR was below its TPR on the new runs. Reported both, with the interval | Followed; result complicates the advice |

Two details of the skill's own code, for the record:

- The Step 8 snippet skips a bootstrap sample only when |TPR + TNR - 1| < 1e-6, so it keeps samples with a negative denominator. judgy 0.1.0 skips any sample with a denominator ≤ 0. They can give different intervals for a weak judge.
- Both hold p_obs fixed, so neither interval includes sampling error in the run being estimated.

## generate-synthetic-data

| Skill step | What the skill says | What this study did | Same? |
|---|---|---|---|
| 1. Dimensions | Axes that target anticipated failures | Issue, status, days near the 14- and 30-day cutoffs, totals near $500, stock, and customer framing; chosen from paper 2's failure analysis | Same |
| 2. Draft 20 tuples with the user | User confirms tuples are realistic | Not done; tuples were sampled by code | Departs |
| 3. More tuples with an LLM | LLM generates combinations | Code samples combinations with weights (`data/make_data_v3.py`) | Departs |
| 4. Tuple to text with a separate LLM prompt | Two-step generation for varied phrasing | Text from fixed phrase banks, not an LLM | Departs: more repetitive phrasing |
| 5. Filter for quality | Review and discard unrealistic queries | Not done | Departs |
| 6. Run through the pipeline | Capture full traces; ~100 | Ran paper 2's agent under four configs on 240 (v3) and 200 (v4) tickets | Same |

The ticket text departs most from the skill. The labels do not depend on the text, because they come from the
order facts and the policy function, but the phrasing is narrower than real tickets or LLM-written ones.
