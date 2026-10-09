# Paper outline (working)

Working title: **Is This Judge Valid? Following the Course Method for an LLM Judge, With Ground Truth to Check It**

The paper follows the judge workflow taught in AI Evaluation for Engineers and PMs (Husain and Shankar), Module 2:
error analysis, a judge prompt per failure mode, train/dev/test splits of labeled traces, iterative refinement
on dev until TPR and TNR pass a target, a single run on test, then the Rogan-Gladen correction (Rogan and
Gladen 1978) on unlabeled traces with a bootstrap interval. What this study adds is a ground truth that is not
subjective: the support policy is code, so every label is known, every step of the refinement can be checked
against it, and the corrected pass rate can be compared with the true one.

The course reader is marked not for sharing. The paper cites the course and its public material (the judgy
library, the evals-skills repo) and does not quote the reader.

## The method, step by step, and where this study stands

| Course step | In this study | Status |
|---|---|---|
| 1. Error analysis on real traces: open coding, axial coding into failure modes | Read the paper 2 agent's misses (13 tickets in phase 0) and code them. Candidate modes from paper 2's own reading: the customer's account overrides the order record; refunds at 31 to 35 days instead of escalating; the $500 limit missed | Not started |
| 2. Labeled traces, about 100 per failure mode, labeled by one domain expert | Agent traces from paper 2's eval, labeled by the reference policy. Real failures are scarce (102 of 600 items, 13 tickets), so more agent runs are needed, including paper 2's configs that make the agent err more (edited decision instructions, stock removed) | Have 600 items from phase 0; need more failures |
| 3. Split by ticket: train 10 to 20%, dev and test 40 to 45% each, 30 to 50 Pass and 30 to 50 Fail in each of dev and test | v2 tickets for train and dev; v3, new tickets written before any judge sees them, for test | v2 split built; v3 not written |
| 4. Judge prompt with the four parts: one failure mode, Pass/Fail definitions, few-shot examples from train, structured output with reasoning | p2 (paper 2's judge) is the baseline and has none of the four. Each later version adds one | p2 measured on dev |
| 5. Refine on dev, inspect false passes and false fails, stop at TPR and TNR above 0.9 | The hill climb: one logged dev run per version, every step reported including ones that made it worse | Not started |
| 6. If it stalls: a more capable model, decompose the criterion, better labels or examples | Planned in that order. The course also says the judge should be a different LLM from the application's; p2 uses Jev for both | Not started |
| 7. Freeze, run once on test, get TPR and TNR | `freeze.py` and the test gate exist | Not run |
| 8. Correct the judge's pass rate on unlabeled traces (Rogan-Gladen), bootstrap over the test set for a 95% interval | Agent runs at several true pass rates; compare the corrected rate and its interval with the truth | Estimator built |
| 9. Production: re-measure TPR and TNR on fresh labels periodically; pin a dated model ID rather than an alias | Paper 2 used the alias `jev-latest`. Record the dated ID if TypeSafe exposes one | Open |

## Research questions

1. **RQ1.** Starting from paper 2's judge, does refinement on dev, following the course loop, reach TPR and TNR above 0.9? What does each step contribute?
2. **RQ2.** Do the dev numbers hold on the held-out test set?
3. **RQ3.** Does the corrected pass rate, and its interval, contain the true pass rate on agent runs whose true pass rates differ?
4. **RQ4.** Where does the method need care that a subjective ground truth would hide? Candidates already seen:
   - constructed failures overstate TNR (dev: 0.98 on constructed, 0.17 on the agent's own mistakes);
   - a judge on the same model as the agent shares its blind spots;
   - items that come in clusters (one ticket, many runs) make an item-level bootstrap too narrow (phase 0: 44% coverage).

## Sections

1. Problem: paper 2's judge was consistent and wrong on a quarter of items; the course's answer is to measure it against labels and correct.
2. The course method (summary with citations, not quoted).
3. Error analysis of the agent's failures.
4. Labeled data and splits.
5. Refinement on dev: the hill climb.
6. Test.
7. Correcting agent runs.
8. What a known ground truth showed about the method.
9. Limitations: one domain, a reference policy that is my reading of the policy text, Jev as the application model.

## Results in hand

Phase 0 (paper 2 data, no new calls): TPR 0.873, TNR 0.176 on 600 items; correction undefined in 33.5% of
held-out splits and further from the truth than the raw rate in 92.8% of the rest. See `phase0/RESULTS.md`.

p2 on dev (`paper/preliminary.md`): TPR 0.725, TNR 0.915 on all-actions items; TNR 0.167 on the 12 wrong
actions the agent actually made. Not held out.

## Open decisions

- **Judge model.** The course says to use a model distinct from the application's. Which second model, and whether Jev can return a reasoning field with its verdict.
- **More real failures.** How many extra agent runs, and with which configs, to reach 30 to 50 Fail traces in each of dev and test.
- **Constructed items.** Keep the all-actions items only as a secondary set, to show the TNR gap, not as the labeled data the judge is tuned on.
