# Hill-Climb Study Overview

What the study tested, how it connects to the TPR and TNR primer, and what it found

Bryan Falkowski · October 2026 · Code and data: [github.com/bfalkowski/judge-tpr-tnr](https://github.com/bfalkowski/judge-tpr-tnr) (`hillclimb/`)

**Summary.** My primer, [Can You Trust Your Judge's Score?](https://bfalkowski.github.io/writing/judge-score.html),
shows how to measure an LLM judge with TPR and TNR. It also shows how to use these two rates to correct the pass rate
that the judge reports. In the primer, you measure the judge one time. Then you use it on new outputs that are similar
to the outputs that you measured.

A hill climb uses a judge in a different way. In each round, the loop makes one change to the app. Then it compares two
pass rates from the judge, and it keeps the change only if the pass rate increases. Thus the outputs change in each
round, and the judge decides which changes stay.

This study asks one question: **do the rules in the primer still apply when a judge controls a hill climb?** The study
tested six rules from the primer. Two rules apply as written. Two rules apply, but they need an addition. Two rules do
not always apply in a hill climb.

## 1. Where the study started

Two documents started this study.

- **The primer.** It teaches four things. A judge makes two types of mistakes. TPR and TNR measure each type. You can
  correct the judge's pass rate with these rates. The correction works only while the judge acts as it did when you
  measured it.
- **Anthropic's article on hill climbing with Claude** (Martin 2026) and the `claude-api` skill that it describes. In
  this loop, an analyzer reads failures and proposes one change. The loop keeps the change only if the pass rates on
  two sets of cases both increase.

The connection is this. When an LLM judge gives the pass rates in this loop, the judge's mistakes are part of each keep
or revert choice. The primer gives the tools to measure these mistakes. This study applies those tools to the loop.

## 2. Goals

1. Test the rules of the primer in a hill climb, and find which rules still apply.
2. Find what a team must measure before, during and after a climb, to trust the result.
3. Find changes that can improve Anthropic's hillclimb skill. A second article will cover this goal.

The study does not try to show that hill climbing does not work. With a perfect grader, the same loop increased the
pass rate on the holdout tickets from 79% to 100%.

## 3. The six rules and the results

| Rule from the primer | What the rule means in a hill climb | Result |
|---|---|---|
| **1.** Measure TPR and TNR separately. One agreement number hides which mistakes the judge makes. (Section 3) | Before the climb, measure the judge with TPR and TNR | <span class="chip ok">Applies</span> |
| **2.** If J = TPR + TNR − 1 is near zero, the correction cannot help. Improve the judge first. (Section 6) | A judge with J near zero cannot control the loop | <span class="chip ok">Applies</span> |
| **3.** TPR and TNR do not depend on the mix of good and bad outputs. Thus you can use them on new data. (Section 5) | The rates from the baseline apply to each new version of the app | <span class="chip mod">Applies, with an addition</span> |
| **4.** When the outputs change, label a new sample and measure the judge again. (Section 8) | A hill climb changes the outputs in each round | <span class="chip mod">Applies, with an addition</span> |
| **5.** Compare two versions with the same judge, on the same kind of data. The judge's errors then affect both versions in almost the same way. (Section 7) | Each keep or revert choice compares two versions with the same judge | <span class="chip no">Does not always apply</span> |
| **6.** Correct the judge's pass rate with TPR and TNR. (Section 5) | Correct the pass rate of the final version with the rates from the baseline | <span class="chip no">Does not apply after a climb</span> |

The section numbers refer to the primer.

## 4. The experiment

**The app.** A support agent from my earlier work reads a ticket and selects one of four actions: refund, reship,
escalate or reply. A written policy with five rules decides the correct action. An answer key, written as code, gives
the correct action for each ticket. The loop could change only the agent's instructions.

**The tickets.** There were 400 new tickets in three sets. The analyzer read the train set. The loop used the train and
validation sets for each keep or revert choice. The loop did not use the holdout set. I scored the holdout set only
after the climbs.

<!-- figure:loop -->

**The graders.** I ran the same loop with four graders. Each grader stayed the same for all rounds of its climb. I
measured each judge with TPR and TNR before the climbs, as the primer teaches.

| Grader | What it is | TPR | TNR | J |
|---|---|---|---|---|
| answer key | the policy as code | 1.00 | 1.00 | 1.00 |
| calibrated | a judge (Claude Haiku 4.5) that I refined with labelled tickets | 0.95 | 0.93 | 0.88 |
| lenient | an earlier version of that judge (Jev), with a low threshold | 0.95 | 0.65 | 0.61 |
| weak | the judge from my run-validity paper (Jev) | 0.76 | 0.24 | 0.00 |

**The climbs.** There were eight climbs and 18 rounds. The calibrated and lenient climbs ran three times each, because
the analyzer can propose different changes in each run. The answer-key and weak climbs ran one time.

**What makes this study possible.** After the climbs, the answer key graded every decision of every version. Thus the
study can see each mistake of each judge, in each round. A normal climb does not have an answer key, and it cannot do
this.

**Two new values.** In each round, a change fixes some decisions and breaks some other decisions. The study measures
two values for each round:

- **J on fixes** is the part of the fixes that the judge detects. A value of 1 means that the judge detects all of the
  fixes. A value of 0 means that the judge detects none of them.
- **J on breaks** is the same value for the breaks.

The primer's J is one value for all outputs together. If rule 5 applies, J on fixes and J on breaks are equal to the
primer's J. The paper calls this case the uniform-error model.

## 5. What we found

### Rule 1 applies: measure TPR and TNR, not one agreement number

Two usual checks did not show the difference between the lenient judge and the calibrated judge. The first check reads
the 10 cases with the lowest judge scores. It found approximately 2 grader errors for each judge. The second check
measures agreement on 40 random decisions. Most of these decisions are correct, so the check measures mostly TPR. The
lenient judge reached 90% agreement in 60% of random samples. The calibrated judge reached it in 95%.

TNR showed the difference clearly: 0.65 for the lenient judge and 0.93 for the calibrated judge. This result agrees
with the primer.

### Rule 2 applies: a judge with J near zero cannot control the loop

The weak judge had J = 0.00. Its verdicts gave almost no information about correct decisions. The analyzer could not
know this. It found patterns in the verdicts and wrote them into the agent. In round 1, it told the agent to escalate
when a customer asks for a supervisor, which the policy does not allow. The loop reverted both rounds, because the
weak judge's own pass rate decreased. The loop could not detect an improvement. This result agrees with the primer.

### Rule 3 needs an addition: the rates depend on the kind of output

The primer says that TPR and TNR do not depend on the mix of good and bad outputs. That is correct. But the rates do
depend on the kind of output. A change in a hill climb affects only a small number of kinds of output. Thus the
judge's accuracy on the outputs that a change affects can be very different from its average.

<!-- figure:jscatter -->

Two examples show this. Each example occurred in all three runs.

- **The lenient judge did not detect a true improvement.** Its J on the baseline was 0.61. Each round tried the same
  fix: the $500 refund limit applies to out-of-stock refunds. On the decisions that this fix corrected, the judge's J
  was 0 or less. The judge fails the correct escalation on 17 of 18 tickets of this kind. Thus the loop reverted the
  fix in all six rounds, although each round fixed more decisions than it broke. Then the analyzer concluded that the
  fix did not work.
- **The calibrated judge did not detect some breaks.** Its J on the baseline was 0.88. One kind of ticket has damage
  reported on an order that did not arrive. The policy text does not decide the correct action for this kind. The
  judge passes the action of rule 3, and the answer key says reply. The climbs broke 43 decisions on these tickets, and
  the judge counted all 43 as fixes.

**Addition to the primer:** measure the judge for each kind of output. Include correct outputs that the app does not
produce yet. On the baseline, the agent never gave the correct escalation, so the lenient judge's problem was not
visible there.

### Rule 4 needs an addition: in a hill climb, measure again in each round

The primer says: when the outputs change, label a new sample and measure the judge again. A hill climb changes the
outputs in each round. Each round changed 44 to 97 of its 480 train and validation decisions. Each keep or revert
choice depends only on these changed decisions.

I tested a small sample after the climbs. I calculated the probability that 20 changed decisions, labelled by a person,
give the correct direction of the true change. This probability was at least 81% in 17 of the 18 rounds. The one
exception had a net change near zero.

<!-- figure:labels -->

**Addition to the primer:** in a hill climb, label a small sample of the changed outputs in each round. I tested this
step only on the completed climbs. It is not yet tested in a running loop.

### Rule 5 does not always apply: errors do not cancel when a change affects one kind of output

The primer says that a comparison of two versions with the same judge, on the same kind of data, is more reliable
than one pass rate. The reason is that the judge's errors affect both versions in almost the same way. Each keep or
revert choice is such a comparison.

But a change in a hill climb usually changes the kind of data. It changes which kinds of output the app gives, on the
same tickets. Thus the condition of the rule is not true, and the judge's errors do not affect both versions in the same
way:

- For the lenient judge, the fix moved decisions from incorrect to correct. For most of these decisions, the judge
  failed both the old incorrect decision and the new correct decision. Thus the fix gave no increase. The breaks of
  the same change did give a decrease. The judge showed a validation decrease of 2.5 to 4.6 points in all six rounds,
  but each change truly fixed more decisions than it broke.
- For the calibrated judge, the judge counted breaks on one kind of ticket as fixes. In all three runs, the judge's
  holdout pass rate showed a larger gain than the true gain. The judge showed +6.6, +11.6 and +9.4 points. The true
  gains were +5.0, +6.9 and +7.8 points.

<!-- figure:outcomes -->

This is the main finding of the study. **A judge can be accurate on the baseline and still make incorrect keep or
revert choices.** The cause is the judge's accuracy on the outputs that each change affects, not its average accuracy.

### Rule 6 does not apply after a climb: the climb changes the judge's error rates

The climb changes which mistakes the agent makes. Thus the judge's rates on the final version can be different from
its rates on the baseline. The calibrated climbs moved the agent's mistakes to the kind of ticket that the judge
passes. Before the climbs, the judge passed 6% of the agent's incorrect decisions. After them, it passed 16%, 26% and
16%.

<!-- figure:drift -->

When I corrected the final pass rates with the baseline rates, the result was too high in all three runs. The
corrected values were 86.7%, 92.4% and 89.9%. The true values were 84.4%, 86.2% and 87.2%. The raw pass rates were
nearer to the true values.

The primer already warns that the correction needs rates that are correct for the new outputs. A hill climb is a case
where the rates change because of the optimization itself. This is a form of Goodhart's law: when the judge's pass rate
becomes the target, the loop moves the app toward the judge's errors.

**Addition to the primer:** after an optimization, measure TPR and TNR again on the final version before you correct
or report its pass rate.

## 6. What a team must measure

| When | What to measure | Why |
|---|---|---|
| Before the climb | TPR and TNR on labelled outputs, with at least 30 incorrect outputs | The usual agreement checks do not show TNR |
| Before the climb | TPR and TNR for each kind of output, with a correct output for each kind | A judge can have J near zero on one kind of output |
| During the climb | A small labelled sample of the outputs that each change affects | Each keep or revert choice depends only on these outputs |
| During the climb | Changes that break the specification, or that decide a case the specification leaves open | The loop can move the app toward the judge's errors |
| After the climb | TPR and TNR again, on the final version | The climb can change the judge's error rates |

## 7. What the study does not show

- The study used one task, one agent and one policy. It does not show how frequently these problems occur in other
  tasks.
- Each judge ran in three climbs at most. Three runs show that the results repeat. They do not show how frequently they
  repeat.
- I tested the labelling step in Section 5 only on the completed climbs.
- For the ambiguous kind of ticket, the answer key gives one possible reading of the policy. The size of the TNR
  decrease depends on that reading. The argument does not.

## 8. The next study

The next study will test the additions from Section 5 in a running loop. This study tested some of them only on the
completed climbs.

**Step 1: change the hillclimb skill.** Six changes are already written, in `hillclimb/skill_patch/`:

- Before round 1, measure TPR and TNR for each main kind of output. If the app does not give a correct output for a
  kind, grade a correct reference output.
- Sort the failures by cause on the baseline, not only after two rounds without an increase.
- In the audit of the judge, measure TPR and TNR, not one agreement number. Also read a sample of the outputs that
  the judge passed.
- Tell the analyzer that the specification has priority over the grader.
- After a revert, show the analyzer the changed cases, with their old and new grades.
- After the climb, measure the judge again on the final version. Report its rates with the gain.

One more change is not in the patch yet: label a small sample of the changed outputs in each round.

**Step 2: run the same climbs again with the changed skill.** Use the same agent, tickets and judges. Then compare the
results with this study.

**Questions for the next study:**

- Does the measurement before round 1 find the lenient judge's problem with the correct escalation?
- With a labelled sample in each round, does the loop keep the $500 fix when the lenient judge grades it?
- Does the priority of the specification stop the calibrated climbs from deciding the open tickets?
- Is the cost of the labels small, at approximately 20 decisions for each round?

## Sources

- Falkowski. [Can You Trust Your Judge's Score? A Primer on TPR and TNR for LLM Judges](https://bfalkowski.github.io/writing/judge-score.html). 2026.
- Martin. [Automating eval design and hillclimbing with Claude](https://claude.dev/blog/automating-eval-design-and-hillclimbing/). claude.dev, September 2026.
- The full results: [`hillclimb/RESULTS.md`](https://github.com/bfalkowski/judge-tpr-tnr/blob/main/hillclimb/RESULTS.md), generated by `hillclimb/analyze.py`.
- The draft paper: [`hillclimb/paper/draft.md`](https://github.com/bfalkowski/judge-tpr-tnr/blob/main/hillclimb/paper/draft.md).
- Wikipedia. [Goodhart's law](https://en.wikipedia.org/wiki/Goodhart%27s_law).
