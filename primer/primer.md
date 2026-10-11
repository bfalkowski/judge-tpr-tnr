# TPR and TNR for LLM Judges: A Primer

Bryan Falkowski · October 2026

*Draft.*

An LLM judge reads an output and says PASS or FAIL. Before you trust the pass rate it reports, you need to know two things about it: how often it passes things that should pass, and how often it fails things that should fail. Those are its true positive rate (TPR) and true negative rate (TNR). This primer explains both, shows how they bend the pass rate a judge reports, and shows how to undo that. Each section is short and has a worked example you can check by hand. My other papers link back to the sections here.

## 1. Why accuracy is not enough

Say 95 of 100 outputs are good and 5 are bad. A judge that says PASS to everything is right 95 times, so its accuracy is 95%. It also catches none of the 5 bad outputs. If the point of the judge is to find failures, it is useless, and accuracy hides that completely.

Accuracy mixes two different questions into one number:

- When an output is good, does the judge pass it?
- When an output is bad, does the judge fail it?

TPR answers the first question and TNR the second. Kept separate, they show what accuracy hides: the always-PASS judge has TPR 1.0 and TNR 0.0.

## 2. The confusion matrix

Start with labeled items: outputs where you already know the right answer, because a person (or, in my case, code) labeled them. Run the judge on them. Every item lands in one of four cells.

| | Judge says PASS | Judge says FAIL |
|---|---|---|
| **Should PASS** | true positive (TP) | false negative (FN) |
| **Should FAIL** | false positive (FP) | true negative (TN) |

In this convention PASS is the "positive" class, so a false positive is a false pass: the judge passed something that should fail. A false negative is a false fail.

**Example.** 20 labeled items. 14 should pass and 6 should fail.

| | Judge says PASS | Judge says FAIL | Total |
|---|---|---|---|
| **Should PASS** | 13 | 1 | 14 |
| **Should FAIL** | 4 | 2 | 6 |
| **Total** | 17 | 3 | 20 |

The judge passed 17 of the 20. It was right on 13 + 2 = 15, so its accuracy is 75%.

## 3. TPR and TNR

- **TPR = TP / (TP + FN).** Of the items that should pass, the share the judge passed.
- **TNR = TN / (TN + FP).** Of the items that should fail, the share the judge failed.

In the example, TPR = 13 / 14 = 0.93 and TNR = 2 / 6 = 0.33. The judge is good at recognizing good outputs and bad at catching bad ones: it passed 4 of the 6 failures.

Each rate is computed only within its own row. TPR uses only the items that should pass, and TNR only the items that should fail. That is why they do not depend on how many good or bad items happen to be in the set, and it is the property everything below relies on.

**Other names.** In medical testing these are sensitivity (TPR) and specificity (TNR) (Altman and Bland 1994). In machine learning, TPR is the recall of the PASS class and TNR is the recall of the FAIL class. They are the same numbers.

**Why not precision?** Precision asks a different question: of the items the judge passed, how many should have passed? The answer depends on how many good and bad items are in the batch, not only on the judge. Here is the same judge, with TPR 0.9 and TNR 0.8, on two batches of 100 outputs:

| | Batch A | Batch B |
|---|---|---|
| Good outputs / bad outputs | 70 / 30 | 30 / 70 |
| Good outputs it passes (90% of good) | 63 | 27 |
| Bad outputs it passes (20% of bad) | 6 | 14 |
| Total it passes | 69 | 41 |
| Precision: good among those it passed | 63 / 69 = 0.91 | 27 / 41 = 0.66 |
| TPR | 63 / 70 = 0.9 | 27 / 30 = 0.9 |
| TNR | 24 / 30 = 0.8 | 56 / 70 = 0.8 |

The judge treated every output the same way, but its precision fell from 0.91 to 0.66. Batch B has more bad outputs, so the same 20% slip rate on bad outputs produces more false passes, and they make up a bigger share of what it passed. TPR looks only at the good outputs and TNR only at the bad ones, so neither moves. That is why they are used to describe a judge: you measure them on one labeled set and carry them to new batches whose mix you do not know. Precision describes the judge on one particular batch.

## 4. How the judge's errors bend the pass rate

What you usually want from a judge is a pass rate: what share of your system's outputs are good. Call the true pass rate θ (theta). The judge does not report θ. It reports the share of outputs it passed, p_obs (observed pass rate), and that share is built from two parts:

- the good outputs it correctly passes: TPR × θ
- the bad outputs it wrongly passes: (1 − TNR) × (1 − θ)

So:

**p_obs = TPR × θ + (1 − TNR) × (1 − θ)**

**Example.** True pass rate θ = 0.70. The judge has TPR 0.9 and TNR 0.8.

- Good outputs it passes: 0.9 × 0.70 = 0.63
- Bad outputs it passes: 0.2 × 0.30 = 0.06
- Reported pass rate: 0.63 + 0.06 = 0.69

The judge reports 69% when the truth is 70%. The two kinds of error push in opposite directions. Missing good outputs (TPR below 1) pulls the reported rate down. Passing bad outputs (TNR below 1) pushes it up. Here they nearly cancel. They will not always: a judge with the same TPR but TNR 0.5 would report 0.63 + 0.15 = 78%.

This one formula explains most of what follows. Moving the sliders on the interactive version of this page is the quickest way to get a feel for it.

## 5. Undoing the mix

If you know TPR and TNR, you can solve the formula in Section 4 for θ:

p_obs = TPR × θ + (1 − TNR) − (1 − TNR) × θ

p_obs − (1 − TNR) = (TPR + TNR − 1) × θ

**θ = (p_obs + TNR − 1) / (TPR + TNR − 1)**

This is the Rogan-Gladen estimator, from epidemiology, where it corrects disease rates measured with an imperfect test (Rogan and Gladen 1978). If the result falls below 0 or above 1, it is clipped to that range.

**Example.** From Section 4: p_obs = 0.69, TPR = 0.9, TNR = 0.8.

θ = (0.69 + 0.8 − 1) / (0.9 + 0.8 − 1) = 0.49 / 0.70 = 0.70

The correction recovers the true 70%.

In practice the steps are:

1. Label a set of items and measure the judge's TPR and TNR on them.
2. Run the judge on new, unlabeled outputs and count the share it passes, p_obs.
3. Plug both into the formula.

The labeled set and the new outputs must be different items. On the labeled set itself the formula gives back the exact true rate every time. For the 20 items in Section 2, p_obs = 17/20 = 0.85, and (0.85 + 0.333 − 1) / (0.929 + 0.333 − 1) = 0.70, exactly the true 14/20. That is algebra, not evidence that the judge works.

## 6. Why a weak judge breaks the correction

The bottom of the formula, TPR + TNR − 1, is called Youden's J (Youden 1950). It measures how much better than a coin flip the judge is. It is 1 for a perfect judge and 0 for a judge that ignores the output. A judge that passes everything has TPR 1 and TNR 0, so J = 0.

Every error in the inputs gets divided by J. If p_obs is off by 1 point:

| Judge | J | Corrected estimate is off by |
|---|---|---|
| TPR 0.95, TNR 0.95 | 0.90 | about 1.1 points |
| TPR 0.9, TNR 0.8 | 0.70 | about 1.4 points |
| TPR 0.6, TNR 0.5 | 0.10 | about 10 points |

The same holds for errors in TPR and TNR themselves, which are only estimates. With a weak judge, a 2-point wobble in p_obs can move the corrected estimate by 20 points. When J is 0 or below, the formula has no answer at all.

So the correction is not a way to rescue a bad judge. You improve the judge first, until TPR and TNR are both high (a common target is above 0.9), and then correct. My worked example of that improvement loop is in the companion paper.

## 7. How many labels you need

TPR and TNR are measured on a sample, so each has an uncertainty. A rough 95% range for a rate measured on n items is ±1.96 × √(rate × (1 − rate) / n). For a rate near 0.9:

| Items in that row | Rough 95% range |
|---|---|
| 30 | ±0.11 |
| 50 | ±0.08 |
| 100 | ±0.06 |
| 200 | ±0.04 |

What matters is the count in each row: TNR is measured only on items that should fail. If failures are rare, a random sample will have very few of them and TNR will be poorly measured. That is why the usual advice is to collect enough of both, 30 to 50 of each even if that over-represents failures. Because each rate stays within its own row, over-representing failures does not bias them.

Two more practical points:

- **Count distinct cases.** If the same input appears many times, those repeats are not independent evidence. Ten copies of one hard case count closer to one.
- **Report an interval, not just a number.** Recompute the corrected estimate on many resamples of your data (a bootstrap; Efron and Tibshirani 1993) and report the range that holds the middle 95%. A corrected 80% that could be anywhere from 72% to 89% should be reported that way.

## 8. Using the numbers

Here is the whole procedure on one run, the way you would report it to someone who only wants to know how good the outputs are.

**Step 1: measure the judge once, on labeled items.** Say you labeled 100 good and 100 bad outputs. The judge passed 88 of the good ones and failed 91 of the bad ones, so TPR = 0.88 and TNR = 0.91.

**Step 2: run the judge on new outputs.** A new run has 200 outputs. The judge passes 122 of them, so its raw score is p_obs = 122 / 200 = 61%. This is not the run's real pass rate. It still contains the judge's mistakes: the good outputs it missed and the bad ones it let through.

**Step 3: correct the raw score.**

θ = (0.61 + 0.91 − 1) / (0.88 + 0.91 − 1) = 0.52 / 0.79 = 0.66

The best estimate of the run's real pass rate is 66%. Here the correction moved the number up, because this judge's bigger problem is missing good outputs (12% of them) rather than passing bad ones (9%). For a judge whose bigger problem is passing bad outputs, the correction moves the number down.

**Step 4: put a range on it.** Resample the labeled items and the run many times, recompute the corrected estimate each time, and keep the middle 95%. For these counts the range is about 56% to 76%.

**Step 5: report the result with what it rests on.**

> Pass rate: 66% (95% range 56% to 76%). The judge passed 61% of the 200 outputs in this run; that was corrected for its measured error rates. It passes 88% of good outputs and fails 91% of bad ones, measured on 200 labeled examples (100 good, 100 bad), last checked on [date].

The person reading this gets the number they care about, how sure it is, and why it can be trusted.

**Making the range narrower.** (All numbers in this section are recomputed by `primer/numbers.py`.) The range comes from three sources of uncertainty: the judge's raw score on the run, its TPR, and its TNR. For the same judge (TPR 0.88, TNR 0.91, raw score 61%):

| Labeled items (good / bad) | Outputs in the run | 95% range | Width |
|---|---|---|---|
| 100 / 100 | 200 | 56% to 76% | 21 points |
| 300 / 300 | 200 | 57% to 75% | 18 points |
| 100 / 100 | 1,000 | 59% to 73% | 14 points |
| 300 / 300 | 1,000 | 61% to 71% | 10 points |
| 1,000 / 1,000 | 5,000 | 63% to 68% | 5 points |

With only 200 outputs, more labels barely help; the run itself is the main source of uncertainty. A better judge also narrows the range, because the correction divides everything by TPR + TNR − 1 (Section 6). With TPR and TNR both 0.97 and the first row's counts, the range is 15 points wide instead of 21.

**Keeping the numbers current.** TPR and TNR describe the judge on the kinds of outputs it was checked on. Re-check them on a fresh labeled sample when the system changes, its inputs change, or the judge's model or prompt changes. Section 9 explains why.

**When the correction barely moves the number.** If the judge is strong and its two kinds of mistakes are about equal, the raw score and the corrected estimate will be close. In my companion paper the raw score was within 1.5 points of the truth for a strong judge. The correction is still worth running, because it is what gives you the range.

## 9. The assumption underneath

The correction assumes the judge makes mistakes on the new outputs at the same rates it made them on the labeled set. That is the price of using two numbers to describe a judge.

It can fail. If a judge is good at catching some kinds of failure and bad at others, its TNR on a new batch depends on which kinds of failure that batch contains. In my companion paper, one judge measured TNR 0.53 on its labeled set. On four new batches its actual TNR was 0.19, 0.22, 0.42 and 0.67, depending on what kinds of mistakes the system made in each batch, and the corrected estimates were badly wrong. A strong judge's rates held steady across the same batches.

Practical consequences:

- Build the labeled set from failures your system actually produces, not from wrong answers you made up. Made-up wrong answers tend to be easier to catch.
- Re-measure TPR and TNR on fresh labels when the system or its inputs change.
- Prefer a strong judge. Its errors are fewer, so there is less for the assumption to get wrong.

## 10. Glossary

| Term | Meaning |
|---|---|
| Labeled item | An output whose correct verdict is known in advance |
| True positive (TP) | Should pass; judge passed it |
| False negative (FN) | Should pass; judge failed it (a false fail) |
| False positive (FP) | Should fail; judge passed it (a false pass) |
| True negative (TN) | Should fail; judge failed it |
| TPR | TP / (TP + FN). Sensitivity. Recall of PASS |
| TNR | TN / (TN + FP). Specificity. Recall of FAIL |
| Accuracy | (TP + TN) / all items. Hides which kind of error the judge makes |
| Precision (PASS) | TP / (TP + FP). Changes with the share of good outputs, so it is not a property of the judge alone |
| θ (theta) | The true pass rate of a set of outputs |
| p_obs | The share of outputs the judge passed |
| Youden's J | TPR + TNR − 1. How much better than a coin flip the judge is |
| Rogan-Gladen correction | θ = (p_obs + TNR − 1) / (TPR + TNR − 1), clipped to [0, 1] |
| Bootstrap interval | The range of an estimate across many resamples of the data |

## References

- Altman and Bland. [Diagnostic tests 1: sensitivity and specificity](https://www.bmj.com/content/308/6943/1552). BMJ, 1994.
- Efron and Tibshirani. An Introduction to the Bootstrap. Chapman and Hall, 1993.
- Husain. [Using LLM-as-a-Judge For Evaluation: A Complete Guide](https://hamel.dev/blog/posts/llm-judge/). 2024.
- Husain and Shankar. [evals-skills](https://github.com/ai-evals-course/evals-skills), `validate-evaluator`.
- Rogan and Gladen. Estimating prevalence from the results of a screening test. American Journal of Epidemiology, 1978.
- Youden. Index for rating diagnostic tests. Cancer, 1950.
