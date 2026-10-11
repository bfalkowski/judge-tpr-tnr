# Can You Trust Your Judge's Score? A Primer on TPR and TNR for LLM Judges

Bryan Falkowski · October 2026

*Draft.*

An LLM judge reads an output and says PASS or FAIL. Teams use judges to answer questions like "what share of our replies are polite?" without reading every reply themselves. Before you trust the number a judge reports, you need to know how often it gets each kind of output right. That is what TPR and TNR measure.

This primer works through one small example from start to finish: label some outputs, measure a judge, improve it, use it, and report the result with a range. The counts are invented for teaching; every calculation is checked by `primer/numbers.py`.

## 1. The question

**Is this customer service reply polite?**

- "Thanks for reaching out! I've reset your password." PASS
- "Read the FAQ next time." FAIL
- "So sorry your toaster set off the smoke alarm. A replacement is on the way." PASS
- "We received your complaint and laughed." FAIL

Anyone can answer this, which makes it a good first example. Real judge questions are usually fuzzier. That is the point of using a judge: if a simple rule could answer the question, you would write the rule instead.

## 2. Label a set and split it

Pick 100 real replies and decide each one yourself: 50 you would call polite and 50 you would not. The 50/50 balance is deliberate, so that both kinds are well represented, even if real replies are mostly polite. Then split them:

| Set | Replies | Used for |
|---|---|---|
| Train | 10 (5 polite, 5 rude) | Examples to put in the judge's prompt |
| Dev | 40 (20 polite, 20 rude) | Measuring the judge while you improve it |
| Test | 50 (25 polite, 25 rude) | One final measurement at the end |

Keep the three sets separate. A reply used as an example in the prompt must never be used to measure the judge.

## 3. Measure the judge

The first version of the judge:

```
Is this customer service reply polite? Answer Pass or Fail.
Reply: {{REPLY}}
```

Run it on the 40 dev replies and sort the results into a **confusion matrix**. It is a table with what you said down the side and what the judge said across the top, so every reply lands in one of four cells:

| | Judge says PASS | Judge says FAIL |
|---|---|---|
| **You said polite (20)** | 19 | 1 |
| **You said rude (20)** | 8 | 12 |

- **True positive:** polite, and the judge passed it (19)
- **False fail:** polite, but the judge failed it (1). Also called a false negative
- **False pass:** rude, but the judge passed it (8). Also called a false positive
- **True negative:** rude, and the judge failed it (12)

The two true cells are where the judge agrees with you. The two false cells are its mistakes, and the matrix shows which kind it makes.

Two numbers come out of the matrix, one per row:

- **TPR (true positive rate)** = polite replies it passed / all polite replies = 19 / 20 = **0.95**
- **TNR (true negative rate)** = rude replies it failed / all rude replies = 12 / 20 = **0.60**

TPR says how well the judge recognizes good outputs. TNR says how well it catches bad ones. This judge is good at the first and poor at the second: it let 8 of 20 rude replies through.

Why two numbers and not one? This judge's accuracy is (19 + 12) / 40 = 78%, which sounds acceptable and hides the problem. Keeping the rows separate shows exactly which kind of mistake the judge makes. Each rate also only looks at its own row, so it does not change when the mix of polite and rude replies changes. That matters in Section 5.

In other fields TPR and TNR are called sensitivity and specificity (Altman and Bland 1994).

## 4. Improve the judge

TNR is far below the usual target of 0.9, so you stop and read the 8 rude replies it passed. They have something in common: rudeness dressed in polite words.

- "Thanks for your patience. As stated twice already, the FAQ covers this."
- "Great, another password reset. Done."

So the second version says what PASS and FAIL mean and shows one example of each, taken from the train set:

```
Is this customer service reply polite? Answer Pass or Fail.

FAIL if the reply blames the customer, is sarcastic, or brushes them off,
even if it uses words like "thanks" or "please".
PASS if it is courteous and addresses the request, even if it is short.

Example: "Great, another password reset. Done."  -> Fail (sarcastic)
Example: "Done! Your password has been reset."   -> Pass (short but courteous)

Reply: {{REPLY}}
```

On dev again it passes 19 of 20 polite replies and fails 18 of 20 rude ones: **TPR 0.95, TNR 0.90.** Both are at target, so you stop.

Now run it **once** on the test set: it passes 23 of 25 polite replies and fails 22 of 25 rude ones, so **TPR 0.92, TNR 0.88.** Slightly lower than dev is normal, since you tuned on dev. These are the numbers you report. Do not change the judge because of what test shows; if test is bad, go back to dev and use fresh test labels afterwards.

If the judge had stayed poor after a few rounds, the usual next steps are a stronger model for the judge, or splitting the question into smaller ones.

## 5. Use it on new replies

Last month's 400 support replies go through the judge. Nobody labels these. It passes 284, so the judge says **71%** are polite.

That raw number still contains the judge's mistakes. Here is how they mix in. If the true share of polite replies is θ (theta), the judge passes:

- the polite replies it recognizes: TPR × θ
- the rude replies it lets through: (1 − TNR) × (1 − θ)

So its raw score is **p_obs = TPR × θ + (1 − TNR) × (1 − θ)**. Solving that for θ gives the correction (Rogan and Gladen 1978):

**θ = (p_obs + TNR − 1) / (TPR + TNR − 1)**

With the test numbers:

θ = (0.71 + 0.88 − 1) / (0.92 + 0.88 − 1) = 0.59 / 0.80 = **74%**

The judge's number was a little low. Missing 8% of the polite replies pulled it down by about 6 points (0.08 × 0.74), and letting 12% of the rude replies through pushed it up by about 3 (0.12 × 0.26). Undoing both gives 74%.

Notice that 74% is very different from the 50% in your labeled set. That is expected. You balanced the labeled set on purpose; real replies have their own mix. TPR and TNR do not depend on the mix, which is why they can be carried from the labeled set to new data. A different pass rate on new data is not a reason to change the judge. Reading the judge's verdicts on some new replies, and finding mistakes your labeled set did not cover, is.

The interactive version of this page lets you move θ, TPR and TNR and watch the matrix and the raw score change.

## 6. The range, and how to tighten it

The 74% is an estimate. TPR and TNR were measured on only 25 replies each, and the raw score came from one month of 400 replies. Recomputing the correction on many resamples of those counts (a bootstrap; Efron and Tibshirani 1993) gives a 95% range of **63% to 88%** (Appendix A shows the calculation step by step). That is wide, and it is honest: the raw "71%" had the same uncertainty, just hidden.

Three things narrow it. Each row below has the same 74% estimate:

| Test labels (polite / rude) | Replies judged | Judge TPR / TNR | 95% range | Width |
|---|---|---|---|---|
| 25 / 25 | 400 | 0.92 / 0.88 | 63% to 88% | 25 points |
| 100 / 100 | 400 | 0.92 / 0.88 | 66% to 82% | 16 |
| 25 / 25 | 2,000 | 0.92 / 0.88 | 64% to 87% | 23 |
| 25 / 25 | 400 | 0.97 / 0.97 | 67% to 82% | 15 |
| 100 / 100 | 2,000 | 0.92 / 0.88 | 68% to 80% | 12 |
| 100 / 100 | 2,000 | 0.97 / 0.97 | 70% to 78% | 7 |

- **Fix the biggest source of uncertainty first.** Here it is the 25 test labels per row. Judging more replies barely helps until there are more labels. You can add test labels after the judge is frozen, as long as you do not change the judge because of them.
- **A better judge helps a lot.** The correction divides everything by TPR + TNR − 1 (Youden's J; Youden 1950). At 0.80, a 1-point error becomes about 1.2 points. For a weak judge with TPR 0.6 and TNR 0.5, J is 0.10 and a 1-point error becomes 10 points. The correction cannot rescue a weak judge; improve the judge first.

## 7. Report it

> **About 74% of last month's replies were polite (95% range 63% to 88%).** Scored by an LLM judge that agrees with a human reviewer on 92% of polite replies and 88% of rude ones, measured on 50 hand-labeled replies on Oct 11.

This gives the reader the number they care about, how sure it is, and why it can be trusted.

How much weight to give it depends on the use:

- **Big changes** show up clearly. A drop from 74% to 50% after a template change is larger than the whole range.
- **Comparing two versions** scored by the same judge on the same kind of data is more reliable than either number alone, because the judge's errors largely affect both the same way.
- **Small changes in the absolute level**, like 74% to 72%, sit inside the range and should not be read as real.

For comparison, checking 100 random replies by hand would give about 74% ± 9 points. The uncertainty comes from how much checked evidence sits under the number, whether a person or a judge does the scoring.

## 8. When models change

**Changing the judge's model** changes TPR and TNR, because they describe that particular judge. A stronger model often raises both and narrows the range, but you have to measure it: run the new judge on dev, then once on fresh test labels. Call the judge with a dated model ID rather than an alias like "latest", so the provider cannot swap the model underneath you.

**Changing the model that writes the replies** changes the real pass rate, which is what you want to measure. It can also change the judge's TPR and TNR, because the new model may be rude in ways the judge was never checked on. After a change like that, label about 50 new replies and check that the judge still lands near its old TPR and TNR before trusting the corrected numbers. The correction uses the TPR and TNR you measured; if the judge's real rates on new replies have drifted, the corrected number is off and nothing in the math tells you. The interactive version of this page has a box for exactly this: the judge's real TNR has dropped from 0.88 to 0.80 since you measured it, you still correct with 0.88, and the estimate comes out 2.6 points high. In real life you can't see the true share of polite replies or the judge's real rates, so nothing you can see looks wrong. The only way to catch it is to hand-label a fresh sample of today's replies and measure the judge again.

**Using the same model for both** is a risk of its own. A judge tends to miss the same mistakes its own model makes. Use a different, and preferably stronger, model for the judge.

The same applies whenever the replies change in other ways, such as new templates or new kinds of requests: re-check the judge on a fresh labeled sample. In practice that is the ongoing cost of using a judge.

## 9. Putting it together

Go back to Section 5. The judge checked 400 new replies and said 284 were polite (71%). Suppose you hand-labeled all 400 and found 296 were really polite (74%). Everything in this primer comes down to three ideas that explain that gap.

**1. The judge makes two kinds of mistakes.** It fails some polite replies: it passes 92% of them (TPR 0.92), so it fails 24 of the 296. And it passes some rude replies: it fails 88% of them (TNR 0.88), so about 12 of the 104 rude replies get through.

**2. The mistakes push the score in opposite directions.** The 24 polite replies it failed pull the score down. The 12 rude replies it passed push it up. They don't cancel, so the judge reports 284 instead of 296.

**3. If you know the two rates, you can undo the mistakes.** You measure TPR and TNR once by hand-labeling a sample. The correction then works back from the judge's 71% to an estimate of 74%. That only holds while the judge behaves the way it did when you measured it. When the replies change (a new model, new templates), label a fresh sample and check the rates again.

The interactive version of this page shows the 400 replies as one bar, with sliders for TPR and TNR.

## 10. Glossary

| Term | Meaning |
|---|---|
| Confusion matrix | A table of what you said against what the judge said. Its four cells are true positives, false fails, false passes and true negatives |
| TPR | Of the outputs that should pass, the share the judge passes. Sensitivity |
| TNR | Of the outputs that should fail, the share the judge fails. Specificity |
| Train / dev / test | Labeled sets for prompt examples, for improving the judge, and for the one final measurement |
| p_obs | The share of new outputs the judge passes (its raw score) |
| θ (theta) | The true share of outputs that should pass |
| Correction | θ = (p_obs + TNR − 1) / (TPR + TNR − 1), clipped to [0, 1] |
| Youden's J | TPR + TNR − 1. How much better than a coin flip the judge is |
| Range | The middle 95% of the corrected estimate across many resamples |

## Appendix A. How the 95% range is calculated

The range comes from a bootstrap (Efron and Tibshirani 1993). The idea is to ask: if I had happened to label a different 25 polite replies, a different 25 rude ones, and judged a different month of 400 replies, how much would my 74% move?

**Step 1. List what each number was counted from.** Every number in the correction is a count out of a limited sample:

| Number | Counted from | Value |
|---|---|---|
| TPR | 25 polite test replies | 23 passed, 0.92 |
| TNR | 25 rude test replies | 22 failed, 0.88 |
| Raw score | 400 new replies | 284 passed, 0.71 |

**Step 2. Redraw each count.** Pretend to label 25 polite replies again, where each one passes with chance 0.92, and count how many pass. You might get 23 again, or 21, or 25. Do the same for TNR (25 replies, chance 0.88) and for the raw score (400 replies, chance 0.71).

**Step 3. Apply the correction to the redrawn numbers.** Three example redraws:

| Draw | TPR | TNR | Raw score | Corrected |
|---|---|---|---|---|
| 1 | 22/25 = 0.88 | 22/25 = 0.88 | 277/400 = 0.693 | (0.693 + 0.88 − 1) / (0.88 + 0.88 − 1) = 0.753 |
| 2 | 24/25 = 0.96 | 22/25 = 0.88 | 284/400 = 0.710 | (0.710 + 0.88 − 1) / (0.96 + 0.88 − 1) = 0.702 |
| 3 | 24/25 = 0.96 | 20/25 = 0.80 | 296/400 = 0.740 | (0.740 + 0.80 − 1) / (0.96 + 0.80 − 1) = 0.711 |

**Step 4. Repeat 10,000 times and keep the middle 95%.** Sort the 10,000 corrected estimates. The value 2.5% of the way up the list is the bottom of the range and the value 97.5% of the way up is the top. Here that gives about 63% to 88%. Because the draws are random, a rerun can differ by about a point.

**Step 5. Skip draws with no answer.** If a draw happens to give TPR + TNR − 1 of 0 or less, the correction has no answer for it. With a strong judge this almost never happens. If it happens often, the judge is too weak to correct (Section 6).

The repo has a short script that does exactly this (`primer/range.py`).

Two notes:

- **Redraw from what you actually counted.** If the same reply appears in your labeled set many times, count it once. Repeats make the range look narrower than it is.
- **Some tools leave out the raw score's uncertainty.** The `judgy` library and the `validate-evaluator` skill redraw TPR and TNR but keep the raw score fixed. That gives a narrower range. Redrawing all three, as above, includes the fact that this month's 400 replies are also a sample.

## References

- Altman and Bland. [Diagnostic tests 1: sensitivity and specificity](https://www.bmj.com/content/308/6943/1552). BMJ, 1994.
- Efron and Tibshirani. An Introduction to the Bootstrap. Chapman and Hall, 1993.
- Husain. [Using LLM-as-a-Judge For Evaluation: A Complete Guide](https://hamel.dev/blog/posts/llm-judge/). 2024.
- Husain and Shankar. [evals-skills](https://github.com/ai-evals-course/evals-skills), `validate-evaluator`.
- Rogan and Gladen. Estimating prevalence from the results of a screening test. American Journal of Epidemiology, 1978.
- Youden. Index for rating diagnostic tests. Cancer, 1950.
