# Hill-Climb Study Overview

The hill-climbing loop from Anthropic's claude.dev article, run with LLM judges and measured with the TPR and TNR primer

Bryan Falkowski · October 2026 · Code and data: [github.com/bfalkowski/judge-tpr-tnr](https://github.com/bfalkowski/judge-tpr-tnr) (`hillclimb/`)

**Summary.** A measurement of an LLM judge on a fixed set of outputs does not show that the judge can control an
optimization loop. In the loop, each change alters the outputs that the judge grades. The loop also keeps the changes
that the judge scores well. Thus the judge's errors affect more than the reported pass rate. They also decide which
version of the app stays.

Anthropic's article [Automating eval design and hillclimbing with
Claude](https://claude.dev/blog/automating-eval-design-and-hillclimbing/) describes such a loop. In each round, an
analyzer proposes one change. The loop keeps the change only if the pass rates on a train set and a test set both
increase. My primer, [Can You Trust Your Judge's Score?](https://bfalkowski.github.io/writing/judge-score.html), shows
how to measure a judge with TPR and TNR. It also shows how to correct the pass rate that the judge reports.

This study implements the loop from the article, adapted to isolate grader errors. It uses three LLM judges of
measured quality and an answer key, and it tests six rules from the primer in this loop. **All six rules stay correct.** But a hill climb breaks the conditions of some
rules, and it needs more measurement than the primer describes. The main finding is this: **a judge can be accurate on
the baseline and still make incorrect keep or revert choices**, because each choice depends on how the judge grades
the small number of outputs that the change affects. The practical result is a check of the judge at three times:
before the climb, on the decisions that each change affects, and after the climb.

## 1. Where the study started

Two documents started this study.

- **Anthropic's article on hill climbing with Claude** (Lance Martin, September 28, 2026) and the `claude-api` skill
  that it describes. In
  this loop, an analyzer reads the failures on the train set and proposes one change. The loop keeps the change only if
  the pass rates on the train set and the test set both increase. The two sets protect the loop from overfitting to
  the cases that the analyzer reads.
- **The primer** (Falkowski 2026). It teaches four things. A judge makes two types of mistakes. TPR and TNR measure
  each type. You can correct the judge's pass rate with these rates. The correction works only while the judge acts as
  it did when you measured it.

The article already warns that grading errors are a common cause of a bad eval. It says that it is important to read a
sample of graded transcripts before you trust the grader. Its account of the work also includes a phase of "fixing graders."

This study examines a related question: what occurs when a grader does more than measure performance? In a hill
climb, the grader's verdicts decide which changes stay. I use the measurements from my primer and an answer key to
examine how grader errors affect these choices. The answer key also shows which changes the grader incorrectly rejects
or accepts, and why.

**Terms.** On this page, a *grader* is anything that grades the agent's decisions. A *judge* is a grader that is an
LLM. The *answer key* is a grader that is code. The article also uses the word *grader*, and in one place *evaluator*.

## 2. Goals

1. Run the loop from the article with LLM judges of known quality, and see how the judge's mistakes affect each keep
   or revert choice.
2. Test the rules of the primer in this loop, and find where their conditions fail.
3. Find what a team must measure before, during and after a climb, to trust the result.

The study does not try to show that hill climbing does not work. With the answer key as the grader, the same loop
increased the pass rate on the holdout tickets from 79% to 100%.

## 3. The six rules and the results

Each rule below stays correct. The results show the conditions under which each rule holds in a hill climb, and what a
climb needs in addition.

| Rule from the primer | What the rule means in a hill climb | Result |
|---|---|---|
| **1.** Measure TPR and TNR separately. One agreement number hides which mistakes the judge makes. (Section 3) | Before the climb, measure the judge with TPR and TNR | <span class="chip ok">Holds</span> |
| **2.** If J = TPR + TNR − 1 is near zero, the correction cannot help. Improve the judge first. (Section 6) | A judge with J near zero cannot control the loop | <span class="chip ok">Holds</span> |
| **3.** TPR and TNR do not depend on the mix of good and bad outputs. Thus you can use them on new data. (Section 5) | The rates from the baseline apply to each new version of the app | <span class="chip cond">Holds, if the rates are the same for each kind of output</span> |
| **4.** When the outputs change, label a new sample and measure the judge again. (Section 8) | A hill climb changes the outputs in each round | <span class="chip mod">Holds; a climb needs it in each round</span> |
| **5.** Compare two versions with the same judge, on the same kind of data. The judge's errors then affect both versions in almost the same way. (Section 7) | Each keep or revert choice compares two versions with the same judge | <span class="chip cond">Holds, if the change does not alter the kind of output</span> |
| **6.** Correct the judge's pass rate with TPR and TNR. (Section 5) | Correct the pass rate of the final version with the rates from the baseline | <span class="chip cond">Holds, if the rates are measured on the final version</span> |

The section numbers refer to the primer.

## 4. The experiment

**The app.** A support agent from my earlier work reads a ticket and selects one of four actions: refund, reship,
escalate or reply. A written policy with five rules decides the correct action. An answer key, written as code, gives
the correct action for each ticket. The loop could change only the agent's decision instructions and the descriptions of the four
actions.

**The tickets.** There were 400 new tickets in three sets. Fig 1 shows the sets and one round of the loop. The analyzer
read the train set. The loop used the train and validation sets for each keep or revert choice. The loop did not use
the holdout set. I scored the holdout set only after the climbs.

<!-- figure:loop -->

**What follows the article, and what I changed.** The study follows the method of the article, with changes that
isolate the grader's errors:

| Part of the method | In the article | In this study |
|---|---|---|
| What the loop can change | The system prompt, skills or instruction files, tool descriptions, model choice and API parameters, and harness code | Only the agent's decision instructions and its descriptions of the four actions |
| Grader | Programmatic checks, or an LLM judge with a rubric. If there is a baseline, the judge compares two outputs in random order | One fixed grader for each climb: the answer key or one of three LLM judges. A judge grades each decision alone, with pass or fail |
| Keep or revert rule | Keep a change if the train and test scores both increase | The same rule, as the skill writes it. The skill adds a second run when only the test score increases. That case did not occur. This page calls the test set "validation" |
| Validation of the grader | Check the grader before the first round, fix it if necessary, and check it again when the score stalls | The same checks were calculated, but the loop did not fix the grader. This was the design: the study measures what the grader's errors do |
| Judge noise | Run the grader two times on the same output, and check that the verdict does not change | Each verdict was calculated one time before the climbs, for each ticket and action. Thus each judge had no run-to-run noise |
| What the analyzer reads | The previous round's train transcripts | The train transcripts of the last kept version. After a revert, the analyzer did not see the transcripts of the reverted round |
| Final assessment | The version with the best test result, compared with the baseline, with confidence intervals | The same comparison on the validation set. In addition, a separate holdout set that the loop did not use |
| Analysis of the grader | Validate the grader and examine grading failures | TPR and TNR on the baseline and on the final version, J on fixes and J on breaks in each round, and an answer key for every decision |

Thus the study is an implementation of the article's method, adapted to isolate grader errors. It is not an exact copy.
The findings apply most directly to a judge that grades each output alone.

**Validation and holdout answer different questions.** The loop used the validation set in every round. Thus the
selection of changes depends on it, and a gain on validation is partly a result of that selection. The holdout set
was not used during the climb, so it gives an independent measure of the final version. This page uses validation to
explain the loop's choices, and holdout for the true gains.

**The graders.** I ran the same loop with four graders. Each grader stayed the same for all rounds of its climb. I
measured each judge with TPR and TNR on the train decisions of the baseline, as the primer teaches. A team can make this
measurement before a climb. In this study, I calculated it from the answer key after the climbs, so that the loop
could not use it. Before the climbs, I had only the values from my earlier judge study, on different tickets. Those
values were similar for the calibrated and lenient judges. For the weak judge, J was 0.32 there.

| Grader | What it is | TPR | TNR | J |
|---|---|---|---|---|
| answer key | the policy as code | 1.00 | 1.00 | 1.00 |
| calibrated | a judge (Claude Haiku 4.5). I refined its prompt with labelled tickets from earlier batches | 0.95 | 0.93 | 0.88 |
| lenient | an earlier step of the same judge design, run on Jev, with a low threshold | 0.95 | 0.65 | 0.61 |
| weak | the judge from my run-validity paper (Jev) | 0.76 | 0.24 | 0.00 |

The name "calibrated" describes how I made the judge. It does not mean that the judge is reliable in a loop. The
results show that a refinement on baseline outputs is not sufficient for that.

**The climbs.** There were eight climbs and 18 rounds. The calibrated and lenient climbs ran three times each, because
the analyzer can propose different changes in each run. The answer-key and weak climbs ran one time.

**What makes this study possible.** After the climbs, the answer key graded every decision of every version. Thus the
study can see each mistake of each judge, in each round. A normal climb does not have an answer key, and it cannot do
this.

**Two new values: J on fixes and J on breaks.** A change corrects some decisions and breaks some other decisions. The
important question is not only how often the judge is correct in general. It is also how well the judge detects the
corrections and the breaks of this specific change. Two values measure this for each round:

- **J on fixes** is TPR + TNR − 1, measured only on the decisions that the change fixed. Here, TPR is the judge's pass
  rate on their new correct outputs, and TNR is its fail rate on their old incorrect outputs. A value of 1 means that
  the judge detects all of the fixes. A value of 0 means that it detects none of them.
- **J on breaks** is TPR + TNR − 1, measured only on the decisions that the change broke. Here, TPR is measured on their
  old correct outputs, and TNR on their new incorrect outputs.

The change in the judge's count of passes is then approximately (J on fixes × fixes) − (J on breaks × breaks). A small
term comes from decisions that changed but stayed correct or stayed incorrect. If TPR and TNR are the same for all
outputs, J on fixes and J on breaks are both equal to the primer's J. The paper calls this case the uniform-error
model.

## 5. What we found

### Rule 1 holds: measure TPR and TNR, not one agreement number

Two usual checks did not show the difference between the lenient judge and the calibrated judge. The first check reads
the 10 cases with the lowest judge scores. It found approximately 2 grader errors for each judge. The skill's rule
says to fix the grader if more than 1 case in 10 is a grader error. Thus this check flagged both judges in most
samples: the lenient judge in 79% and the calibrated judge in 69%. It did not show which judge was worse. The second check
measures agreement on 40 random decisions. Most of these decisions are correct, so the check measures mostly TPR. The
lenient judge reached 90% agreement in 60% of random samples. The calibrated judge reached it in 95%.

TNR showed the difference clearly: 0.65 for the lenient judge and 0.93 for the calibrated judge. This result agrees
with the primer.

### Rule 2 holds: a judge with J near zero cannot control the loop

The weak judge had J = 0.00. Its verdicts gave almost no information about correct decisions. The analyzer could not
know this. It found patterns in the verdicts and wrote them into the agent. In round 1, it told the agent to escalate
when a customer asks for a supervisor, which the policy does not allow. The loop reverted both rounds, because the
weak judge's own pass rate decreased. The loop could not detect an improvement. This result agrees with the primer.

### Rule 3 holds only if the rates are the same for each kind of output

The primer says that TPR and TNR do not depend on the mix of good and bad outputs. That is correct. But the rates do
depend on the kind of output. A change in a hill climb affects only a small number of kinds of output. Thus the
judge's accuracy on the outputs that a change affects can be very different from its average. Fig 2 shows J on fixes
and J on breaks for each round. Under the primer's assumption, each round would be on the diagonal.

<!-- figure:jscatter -->

Two examples show this. Each example occurred in all three runs.

- **The lenient judge did not detect a true improvement.** Its J on the baseline was 0.61. Each round tried the same
  fix: the $500 refund limit applies to out-of-stock refunds. On the decisions that this fix corrected, the judge's J
  was 0 or less. The judge fails the correct escalation on 17 of 18 tickets of this kind. Thus the loop reverted the
  fix in all six rounds, although each round fixed more decisions than it broke. Then the analyzer concluded that the
  fix did not work. In this study, the analyzer did not see the transcripts of the reverted rounds. This possibly
  contributed to its conclusion.
- **The calibrated judge disagreed with the answer key on one kind of ticket.** Its J on the baseline was 0.88. On
  this kind of ticket, a customer reports damage on an order that did not arrive. The policy text does not decide the
  correct action. The judge passes the action of rule 3, and the answer key says reply. Thus this is a disagreement on
  an unclear case, not a clear judge error. The climbs broke 43 decisions on these tickets by the answer key's reading,
  and the judge counted all 43 as fixes.

**Extension to the primer:** measure the judge for each kind of output. Include correct outputs that the app does not
produce yet. On the baseline, the agent never gave the correct escalation, so the lenient judge's problem was not
visible there.

### Rule 4 holds, and a climb needs it in each round

The primer says: when the outputs change, label a new sample and measure the judge again. A hill climb changes the
outputs in each round. Each round changed 44 to 97 of its 480 train and validation decisions. Each keep or revert
choice depends only on these changed decisions.

I tested a small sample after the climbs. For each round, I calculated the probability that 20 changed decisions give
the correct direction of the true change. The calculation assumes that a person selects the 20 decisions at random
without replacement, and that the person labels each one correctly. The answer key gave these labels. The probability
was at least 81% in 17 of the 18 rounds. The one exception had a net change near zero. Fig 3 shows the result for
samples of 10, 20 and 30.

<!-- figure:labels -->

**Extension to the primer:** in a hill climb, label a small sample of the changed outputs in each round. This is
retrospective evidence from the completed climbs. It is not yet a tested procedure for a running loop.

### Rule 5 holds only if the change does not alter the kind of output

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
  gains were +5.0, +6.9 and +7.8 points. Fig 4 shows the difference for each climb.

<!-- figure:outcomes -->

This is the main finding of the study. **A judge can be accurate on the baseline and still make incorrect keep or
revert choices.** The cause is the judge's accuracy on the outputs that each change affects, not its average accuracy.

### Rule 6 holds only with rates measured on the final version

The climb changes which mistakes the agent makes. Thus the judge's rates on the final version can be different from
its rates on the baseline. The calibrated climbs changed the types of the agent's mistakes, not only their number. On
validation and holdout, the total number of incorrect decisions decreased, from 116 to 90, 84 and 74. But the number
on the open kind of ticket increased, from 2 to 14, 16 and 12. The judge passes the decisions of that kind. Before the
climbs, the judge passed 6% of the agent's incorrect decisions. After them, it passed 16%, 26% and 16%. Fig 5 shows
this change.

<!-- figure:drift -->

When I corrected the final pass rates with the baseline rates, the result was too high in all three runs. The
corrected values were 86.7%, 92.4% and 89.9%. The true values were 84.4%, 86.2% and 87.2%. The raw pass rates were
nearer to the true values.

The primer already warns that the correction needs rates that are correct for the new outputs. A hill climb is a case
where the rates change because of the optimization itself. This is a form of Goodhart's law: when the judge's pass rate
becomes the target, the loop can move the app toward the judge's blind spots.

**Extension to the primer:** after an optimization, measure TPR and TNR again on the final version before you correct
or report its pass rate.

### Where the effects come from

The results show three sources of the effects. Each source has a different size.

- **The judge's error rates on the baseline.** The order of the graders by J predicted the order of the outcomes. The
  answer key improved the agent the most, the calibrated judge improved it less, and the lenient and weak judges kept
  no change.
- **The decisions that each change affects.** J on fixes and J on breaks were very different from the baseline J
  (Fig 2). This source explains the specific incorrect choices: the lenient judge's reverts, and the calibrated
  judge's larger reported gains.
- **The analyzer's proposals.** The three runs of each judge had different proposals in different words. But each run
  made the same kind of change. Each lenient round tried the $500 fix. Each calibrated run kept the $500 fix, and then
  a change that applied rule 3 to the open kind of ticket. Thus the analyzer changed the size of the results, but not
  their direction.

## 6. What a team must measure

| When | What to measure | Why |
|---|---|---|
| Before the climb | TPR and TNR on labelled outputs, with at least 30 incorrect outputs | The usual agreement checks do not show TNR |
| Before the climb | TPR and TNR for each kind of output, with a correct output for each kind | A judge can have J near zero on one kind of output |
| During the climb | A small labelled sample of the outputs that each change affects | Each keep or revert choice depends only on these outputs |
| During the climb | Changes that break the specification, or that decide a case the specification leaves open | The loop can move the app toward the judge's blind spots |
| After the climb | TPR and TNR again, on the final version | The climb can change the judge's error rates |

## 7. What the study does not show

- **A mechanism, not its prevalence.** The study used one task, one agent and one policy. It shows how these problems
  occur. It does not show how frequently they occur in other tasks.
- **A small number of runs.** Each judge ran in three climbs at most. Three runs show that the results repeat. They do
  not show how frequently they repeat.
- **Unclear cases in the policy.** For the open kind of ticket, the answer key gives one possible reading of the
  policy. On these tickets, the calibrated judge's "errors" are disagreements with that reading. The size of the TNR
  decrease depends on that reading. The argument does not: the loop decided an unclear case without a person.
- **Retrospective labelling.** The labelling result in Section 5 comes from the completed climbs. It assumes random
  samples and correct labels. It is not yet tested in a running loop.
- **Repeated use of the validation set.** The loop used the same validation set in each round. Thus a gain on
  validation is not an independent measure after many rounds. The holdout set is, because the loop did not use it.
- **One type of judge.** The judges graded each output alone, with pass or fail. The article recommends that, for a
  comparison with the baseline, a judge sees both outputs in random order. This study did not test that setup.

## 8. The next study

The next study will test the extensions from Section 5 in a running loop. This study tested some of them only on the
completed climbs. The next study will add the steps from Section 6 to the loop. Then it will run the same climbs
again, with the same agent, tickets and judges. It will examine these questions:

- Does a measurement before the climb find the lenient judge's problem?
- With a labelled sample in each round, does the loop keep a true improvement that the judge does not detect?
- Can the loop stop a change that decides a case that the specification leaves open?
- How many labels does each round need?

## 9. The practical result: check the judge three times

The article checks the grader before the first round and again when the score stalls. The results add a check on the
decisions that each change affects, and a new measurement after the climb. Together, they give three principles.

1. **Measure the judge before the optimization.** One agreement number is not sufficient. Measure both types of error,
   and measure them for each important kind of output. *This study shows this.*
2. **Measure the changes, not only the versions.** A change affects a small set of decisions, and these decisions
   decide whether the change stays. *This study supports this with retrospective evidence. It is not yet tested in a
   running loop.*
3. **Measure the judge again after the optimization.** The final version can have a different mix of errors. Thus the
   rates from the baseline do not automatically apply to it. *This study shows this in three runs, and the decrease is
   significant in one of them.*

A judge that controls an optimization does more than measure quality. Its errors decide which changes stay. That
selection can make the judge's own blind spots more important with each round.

## Sources

- Falkowski. [Can You Trust Your Judge's Score? A Primer on TPR and TNR for LLM Judges](https://bfalkowski.github.io/writing/judge-score.html). bfalkowski.github.io, October 2026.
- Martin, Lance. [Automating eval design and hillclimbing with Claude](https://claude.dev/blog/automating-eval-design-and-hillclimbing/). claude.dev, September 28, 2026.
- The full results: [`hillclimb/RESULTS.md`](https://github.com/bfalkowski/judge-tpr-tnr/blob/main/hillclimb/RESULTS.md), generated by `hillclimb/analyze.py`.
- Wikipedia. [Goodhart's law](https://en.wikipedia.org/wiki/Goodhart%27s_law).
