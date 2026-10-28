# Can You Trust Your Hill Climb? Applying TPR and TNR to a Keep-or-Revert Loop

Bryan Falkowski · October 2026 · Code and data: [github.com/bfalkowski/judge-tpr-tnr](https://github.com/bfalkowski/judge-tpr-tnr) (`hillclimb/`)

*Fourth draft: the third draft, rewritten in ASD-STE100 Simplified Technical English. Every number comes from
`hillclimb/analyze.py` and is in `hillclimb/RESULTS.md`.*

**Abstract.** Hill climbing improves an app with one change at a time. If the pass rate on the eval increases, you
keep the change. If not, you revert it. When an LLM judge grades the eval, the mistakes of the judge can cause
incorrect keep or revert choices. This paper examines how.

I ran the same loop on one support agent with four graders. One grader was the answer key. The other three were
judges with a measured TPR and TNR. TPR is the rate at which a judge passes correct outputs. TNR is the rate at which it
fails incorrect outputs. After the climbs, the answer key graded every decision.

- **Answer key:** The pass rate on the holdout tickets increased from 79% to 100%. The loop did not use these tickets.
- **Calibrated judge, three runs:** Each climb increased the true pass rate on holdout by 5 to 8 points. Each climb
  also gave the agent the judge's answer for one type of ticket that the policy does not decide. Before the climbs,
  the judge passed 6% of the agent's incorrect decisions. After them, it passed 16% to 26%.
- **Lenient judge, three runs:** Each change fixed more decisions than it broke. But the judge gave no net increase
  in passes for the fixed decisions. It also changed most of the broken decisions from pass to fail. Thus the loop
  reverted every change.
- **Weak judge:** Its verdicts gave almost no information. Thus the loop could not detect an improvement, and it kept
  no change.

A simple model says that, on average, a judge shows each change at J = TPR + TNR − 1 times its true size. This model
is correct when TPR and TNR are the same for all outputs. In these climbs, they were not the same. Thus the quality of
a judge on the baseline does not tell you how it grades the changes that a loop tries. Section 7 shows how to measure
this before, during and after a climb.

<!-- figure:glance -->

## 1. The question

Hill climbing is a common way to improve a prompt or an agent. In each round, you make one change and run the eval.
You keep the change only if the pass rate increases. Anthropic's guide for hill climbing with Claude divides the cases
into two sets (Martin 2026). The analyzer that proposes changes reads only one set. The loop keeps a change only when
the pass rates on both sets increase. This rule decreases the risk of overfitting to the cases that the analyzer
reads.

The rule does not prevent errors that come from the grader. When the grader is an LLM judge, "the pass rate increased"
means "the judge passed more outputs." The primer shows what a judge's pass rate contains (Falkowski 2026a):

pass rate = TPR × θ + (1 − TNR) × (1 − θ)

In this equation, θ is the true fraction of correct outputs. Each keep or revert choice compares two of these pass
rates.

What does a change do to the judge's pass rate? Assume that a change fixes F incorrect outputs and breaks B correct
outputs, out of n outputs. Before the change, the judge passed each of the F incorrect outputs with probability
1 − TNR. After the change, the judge passes each fixed output with probability TPR. Thus, on average, each fix adds
this amount to the judge's count of passes:

TPR − (1 − TNR) = TPR + TNR − 1

The same calculation shows that each break removes the same amount. TPR + TNR − 1 is Youden's J (Youden 1950). The
primer uses J to show why it is not possible to correct a weak judge. Assume that the judge's TPR and TNR are the same
for all outputs. I call this assumption the uniform-error model. Then:

**expected observed change = J × true change, where true change = (F − B) / n.**

In this model, the judge makes each true improvement smaller by the factor J. A judge with J = 0.88 shows a 10-point
gain as approximately 8.8 points. A judge with J = 0.6 shows it as 6 points. A judge with J = 0 shows no gain. A judge
with a negative J gives higher pass rates to worse outputs. The model also gives an approximate rule. When J is
clearly more than zero, the smallest true gain that the loop can detect is approximately the noise divided by J.

<!-- figure:shrink -->

The uniform-error model is only the start. A change in a hill climb usually affects a small number of types of output.
The judge's rates are different for each type. Thus each fixed output adds its own J. This J is the judge's TPR on the
new answer minus its false-pass rate on the old answer. Each broken output removes its own J:

**expected observed change = (sum of J over the fixed outputs − sum of J over the broken outputs) / n.**

Thus the net count F − B does not decide what the judge shows. The mix of fixes and breaks decides it. A change can be
a true improvement and still decrease the judge's pass rate. This can occur when the judge grades the fixed outputs
badly. I call the average J over the fixes of a change its "J on fixes." I call the average J over its breaks its
"J on breaks."

This changes the question. The question is not only "Is the judge accurate?" It is also "Can the judge control an
optimization correctly?" These are two different questions. The loop changes the outputs of the agent. This changes
where the judge makes its mistakes, and that has an effect on the next round. The remainder of this paper shows this
effect in the climbs of this study. It also shows how to measure it.

## 2. Setup

**The agent.** I used the support agent from my run-validity paper without changes (Falkowski 2026b). For each
ticket, the agent gets the order record and the stock level. Then it asks Jev which of four actions the support policy
requires: refund, reship, escalate or reply. Jev is a small decision model from TypeSafe. The policy has five rules.
The climb could change only two things: the decision instructions that go with each question, and the descriptions of
the four actions. The climb could not change the policy text, the fields that the agent sees, the model or the code.

**The answer key.** The answer key is the policy written as code, as in my run-validity paper. It gives the correct
action for each decision.

**Tickets.** I made 400 new tickets with the same generator that made the labelled tickets that I used to refine
the judges below. I divided them at random into three sets, within each customer framing. Thus each set has
approximately the same mix of framings.

| Set | Tickets | Use in the loop |
|---|---|---|
| Train | 120 | The analyzer reads these transcripts to propose changes |
| Validation | 120 | The loop scores this set in each round, and keeps a change only if the pass rate here increases. The guide calls this set "test" |
| Holdout | 160 | The loop does not use this set. I scored it only after the climbs |

The validation set decides which changes stay. Thus it is part of the optimization. The holdout set gives independent
evidence about the true gain. Each version of the agent ran each ticket two times. Thus the pass rate of a set is the
mean over two decisions for each ticket. The validation set has 240 decisions.

**The loop.** I followed Anthropic's hill-climbing guide as written. The guide is the `eval-hillclimb.md` file of the
`claude-api` skill (Anthropic 2026). The repo has a copy of it at a fixed commit. In each round, a new analyzer
(Claude Opus 5.5) read the train transcripts and grades of the current version. It proposed one change. The Claude session that ran
the study applied the change exactly, without edits. The loop kept a change when the train and validation pass rates both increased. When the
validation pass rate increased and the train pass rate did not, the loop ran the change one more time. It kept the
change only if the validation pass rate increased again. After two rounds without an increase larger than the noise
level, the loop ran one round that sorted the remaining failures by cause. The loop stopped after three consecutive
rounds without such an increase, or when the analyzer had no change to propose.

The repo records the design, and each change to the design during the study, before the results that they could
affect. The
branch `hillclimb-history` keeps each commit, with the time of each round. After the first four climbs, I ran the
climbs with the calibrated judge and the lenient judge two more times. These repeat runs used the same baseline, judge
verdicts and rules. Only the analyzer's proposals, and thus the changes that the loop kept, could be different.

<!-- figure:loop -->

**The graders.** Each climb used one grader for all its rounds. I measured each judge on the 240 train decisions of
the baseline. Of these decisions, 46 were incorrect.

| Grader | What it is | TPR | TNR | J |
|---|---|---|---|---|
| answer key | the policy as code | 1.00 | 1.00 | 1.00 |
| calibrated | a judge (Claude Haiku 4.5). I refined its prompt with labelled tickets from earlier batches. Its code is in the repo | 0.95 | 0.93 | 0.88 |
| lenient | an earlier judge from that refinement (Jev), with a low threshold | 0.95 | 0.65 | 0.61 |
| weak | the judge from my run-validity paper (Jev, with a one-sentence prompt) | 0.76 | 0.24 | 0.00 |

The input to a judge is only the ticket, the order, the stock and the action. Thus I ran each judge one time on all
four actions of each ticket before the climbs started. The loop then found the verdict for the action that the agent
selected. The total API cost was $3.89. Of this, $2.93 was for the calibrated judge's verdicts and $0.26 was for the
repeat runs. In the repo, the three judges are `c3`, `j2` at threshold 0.3, and `p2`.

**Noise.** The guide gives an approximate noise level for a pass rate: 1/√(cases × runs). Here, that is approximately
6.5 points. This value assumes that all 240 validation decisions are independent. Also, it applies to one pass rate,
not to a comparison of two. I measured two types of noise directly. First, a rerun of the same version changed very
little. Between the two repetitions of the baseline, 0 to 2 of the 120 validation tickets got a different grade. The
number depended on the grader. This is approximately 1 to 2 points of noise when you compare two versions. Second, the selection
of tickets in the set causes more noise. I calculated paired 95% intervals on the change in each round by resampling
tickets. The half-widths of these intervals were approximately 3 to 8 points. The sections below use the paired
intervals.

## 3. Results of the climbs

The final version of a climb is the version that the climb ends with. If the loop kept no change, the final version
is the baseline. The table shows the first run of each climb.

| Grader | Rounds | Change that the loop reported (validation) | True change, validation | True change, holdout |
|---|---|---|---|---|
| answer key | 3 | +18.3 points, 79.2% to 97.5% | +18.3 | +20.6, 79.4% to 100% |
| calibrated | 3 | +4.6, 77.1% to 81.7% | +4.2 | +5.0, 79.4% to 84.4% |
| lenient | 2, both reverted | no change, 89.2% | 0 | 0 |
| weak | 2, both reverted | no change, 83.8% | 0 | 0 |

The calibrated judge's climb was the only climb with an imperfect grader that kept a change. In that run, the gain
that the loop reported was close to the true gain. The repeat runs show that this result was partly chance:

| Grader | Run | Rounds kept | Reported (validation) | True change, validation | True change, holdout [95% interval] |
|---|---|---|---|---|---|
| calibrated | 1 | 2 of 3 | +4.6 | +4.2 | +5.0 [−0.9, +10.9] |
| calibrated | 2 | 2 of 2 | +9.6 | +4.2 | +6.9 [+0.0, +13.8] |
| calibrated | 3 | 2 of 2 | +5.8 | +7.1 | +7.8 [+1.3, +14.7] |
| lenient | 1 | none of 2 | 0 | 0 | 0 |
| lenient | 2 | none of 2 | 0 | 0 | 0 |
| lenient | 3 | none of 2 | 0 | 0 | 0 |

All three calibrated climbs increased the true pass rate on holdout. But only the interval for run 3 clearly excludes
zero. The gain that the loop reported on validation was different from the true gain by +0.4, +5.4 and −1.3 points.
On holdout, the judge's own pass rates showed a larger gain than the true gain in all three runs, by 1.6, 4.7 and 1.6
points. All three lenient climbs reverted every round. The results for each round below show why a judge that is
good on the baseline can make an incorrect keep or revert choice. This can occur when a change affects outputs that
the judge grades differently.

<!-- figure:outcomes -->

In the uniform-error model, the paired noise of 3 to 8 points sets the smallest true change that each judge can
detect.
For the calibrated judge, it is approximately 3.5 to 9 points. For the lenient judge, it is approximately 5 to 13
points. The weak judge, with J near 0, can detect no change. The climbs are consistent with this model. The answer key kept three
large changes, and the calibrated judge kept small changes. The lenient and weak judges kept no change. But the
uniform-error model does not show what occurred in each round.

The next table divides each change into the decisions that it truly fixed and the decisions that it truly broke. It
also shows how much of each the grader detected. Here, a decision is one run of one ticket. Thus the train and validation
sets have 480 decisions. "Fixed" and "broken" are counts of decisions. The last two columns are net counts, and each
decision is 0.21 points of the 480.

| Grader | Round | Kept? | Fixed | J on fixes | Broken | J on breaks | True change | Grader's change |
|---|---|---|---|---|---|---|---|---|
| answer key | 1 to 3 | all kept | 38, 62, 42 | 1.00 | 15, 35, 2 | 1.00 | +23, +27, +40 | same |
| calibrated | 1 | kept | 32 | 0.97 | 12 | 0.50 | +20 | +25 |
| calibrated | 2 | reverted | 20 | 0.75 | 46 | 0.41 | −26 | −1 |
| calibrated | 3 | kept | 30 | 0.57 | 20 | 0.10 | +10 | +15 |
| lenient | 1 | reverted | 36 | 0.00 | 23 | 0.65 | +13 | −15 |
| lenient | 2 | reverted | 36 | 0.00 | 10 | 0.70 | +26 | −7 |
| weak | 1 | reverted | 10 | −0.20 | 68 | 0.26 | −58 | −26 |
| weak | 2 | reverted | 5 | 0.20 | 37 | 0.16 | −32 | −8 |

The table compares each round with the version that the loop tested it against. It shows the first run of each climb.
The repeat runs show the same pattern. In all seven calibrated rounds of the three runs, J on fixes was higher than J
on breaks. In the last kept round of each run, J on breaks was between 0.10 and 0.19. In all six lenient rounds, J on
fixes was between −0.08 and 0.00, and J on breaks was between 0.53 and 0.86. `RESULTS.md` has each round of each run.

<!-- figure:jscatter -->

No judge had one J. Each judge had a J on fixes and a different J on breaks. This difference decided the round. Two
rounds show this most clearly on the validation set:

- The lenient judge's round 2 increased the true validation pass rate by 2.5 points (95% interval −2.1 to +7.1). It
  increased the true holdout pass rate by 5.0 points. But the judge showed a decrease of 2.9 points, and the interval
  excludes zero (−6.2 to −0.4).
- The calibrated judge's round 2 decreased the true validation pass rate by 6.2 points (−11.7 to −0.8). The judge
  showed a decrease of only 2.5 points (−7.9 to +2.9), which is not larger than the noise. The loop reverted the change
  because the judge's validation pass rate decreased. But on train and validation together, the judge showed a net loss of only one
  decision.

The next three sections examine each case.

## 4. A judge that passes incorrect outputs cannot detect fixes

The lenient judge's J on the baseline was 0.61. On the decisions that the two rounds of its first run fixed, its J was
0.00.

Round 2 applied the $500 refund limit to every refund, as the policy requires. The change fixed 36 decisions and broke
10. For 7 of the 10 broken decisions, the judge's verdict changed from pass to fail. But for the 36 fixed
decisions, the number of passes did not increase:

- 4 changed from fail to pass.
- 4 changed from pass to fail.
- 5 passed before and after, because the judge already passed the old incorrect decision.
- 23 failed before and after.

The last group is the main cause. Some tickets have an out-of-stock order over $500, and the policy requires the
agent to escalate them. On these tickets, this judge passes the correct escalation on only 1 of 18. Its TPR on this
type of decision is almost zero. After the change, the judge failed 27 of the fixed decisions. Of these 27, 26 are
those escalations.

Thus the change was a true improvement, but the judge showed it as a loss. The loop reverted it, which is correct by
the loop's rule. Round 1 tried the same fix. In round 1 also, the number of passes did not increase for the 36 fixed
decisions.

<!-- figure:waffle -->

The repeat runs gave the same result. In all six lenient rounds of the three runs, the change applied the $500 limit
to the out-of-stock refund. Each time, the over-$500 out-of-stock tickets alone increased the holdout pass rate by 2.5
points. The calibrated judge kept the same fix in round 1 of all three of its runs. In all six lenient rounds, J on
fixes was between −0.08 and 0.00. The judge showed a validation decrease of 2.5 to 4.6 points, and each interval
excluded zero. The loop reverted each change. All six changes truly fixed more decisions than they broke. If you
apply the same keep rule to answer-key grades, it keeps five of them. Each run had one best reverted round. The trial versions of these
rounds had a true holdout pass rate higher than the baseline by 5.0, 3.8 and 9.1 points.

Each run then stopped in the same way. The analyzer read the history. It saw two rounds that tried to apply the $500
limit, and the judge showed both rounds as losses. Thus the analyzer proposed no change. Run 1's analyzer described
the over-limit refunds as a behavior "that two artifact rounds already failed to move." Run 3's analyzer said that the
same behavior "has already resisted both in-scope levers." But on the over-$500 out-of-stock tickets, the fix worked
each time. The judge's error became the analyzer's conclusion about the agent.

Two different problems hid the fixes, and each problem needs a different repair. First, a low TNR on the old
incorrect decisions means that the judge already passed them. Thus a fix gives no increase. Second, a low TPR on the
new correct decisions means that the judge fails them. Thus a fix can even decrease the pass rate. The judge's average
does not show these problems. You cannot measure the second problem on the baseline, because the baseline agent never
gave the correct escalation. To detect it, grade a correct answer for each type of ticket.

## 5. The climb moves mistakes to where the judge does not detect them

The calibrated judge is a good judge, with J = 0.88 on the baseline. Its first climb reported a gain of +4.6 points on
validation. The true gain was +4.2 points on validation and +5.0 points on holdout.

In that run, its J on breaks was much lower than its overall J: 0.50, 0.41 and 0.10 in the three rounds. Most of the
breaks that it did not detect were on one type of ticket. On this type, a customer reports damage. The order is Lost,
or it shipped more than 14 days ago and did not arrive. The policy text does not say which rule applies. The answer
key says reply. The calibrated judge passes the rule 3 action on all 13 tickets of this type. This action is reship,
or refund or escalate when the item is out of stock. The judge passes reply on only 1 of them. I call these tickets
the open tickets.

In round 3, the analyzer read the judge's verdicts. Then it wrote the judge's reading into the agent's
instructions. The new instructions said: "Rule 3 applies to every ticket on it, including damaged or wrong-item
reports and tickets that only ask for a status update: reship if stock is above 0, otherwise refund." The change broke
20 decisions. For the 11 ordinary breaks, the judge's verdict changed from pass to fail. For the 9 breaks on the open
tickets, it changed from fail to pass, as for a fix. Round 2 did the same with more tickets. Of its 46 breaks, 10 were
on the open tickets, and the judge's verdict on them changed from fail to pass.

The repeat runs gave the same result. Each run kept the $500 fix in round 1. Then each run kept a change that applied
rule 3 to the open tickets. Run 2's instructions had a new rule for shipped orders more than 14 days old.
The rule said: "rule 3, whatever the ticket reports, including damage, a wrong item or only a request for an update."
Run 3's instructions said: "reship if stock is above 0, otherwise refund, even when the ticket reports a damaged or
wrong item." In the seven calibrated rounds of the three runs, changes broke 43 decisions on the open tickets. For all
43, the judge's verdict changed from fail to pass, as for a fix. For 105 of the other 127 breaks, it changed from pass
to fail.

<!-- figure:breaks -->

Two related effects occur here.

The first effect is selection. The loop keeps the changes that the judge gives a higher pass rate. Thus the loop can move
the agent toward the judge's reading where the judge and the answer key disagree. This is
Goodhart's law (Wikipedia): when the judge's pass rate becomes the target, the loop optimizes the judge's opinion
together with the agent's quality.

The second effect is a change in where the judge makes its mistakes. This effect is the empirical result. The
climb changed which mistakes the agent makes. Thus the judge's error rates on the baseline no longer describe the
judge. On validation and holdout, the answer key graded 2 decisions on the open tickets as incorrect at the baseline.
At the final versions of runs 1, 2 and 3, it graded 14, 16 and 12 as incorrect. The judge passed each of them. At each
final version, most of the judge's false passes were on this type of ticket. The counts were 14 of 14, 16 of 22 and
12 of 12. Its TNR on the
agent's decisions decreased from 0.94 at baseline to 0.84, 0.74 and 0.84. At baseline, it failed 109 of 116 incorrect
decisions. At the final versions, it failed 76 of 90, 62 of 84 and 62 of 74.

The two repetitions of a ticket are not independent. Thus I also counted only one repetition for each ticket. The
judge failed 53 of 57 incorrect decisions at baseline. At the three final versions, it failed 38 of 45, 32 of 43 and
33 of 39. When you examine each run separately, only the decrease in run 2 is unlikely to be chance. The p-values are
0.02 for run 2, and 0.2 and 0.3 for runs 1 and 3. Three runs with the same baseline do not prove the result.
But the decrease has the same direction and the same cause in each run.

<!-- figure:drift -->

This argument does not depend on which reading is correct. The loop decided an unclear part of the policy. It used
the judge's reading, and it did not show this decision to a person. No number from the loop shows that it decided a
policy question.

## 6. A judge with J near zero gives the agent incorrect rules

The weak judge's J on the baseline was 0.00. Thus its verdicts gave almost no information about whether a decision was
correct. The analyzer could not know this. It read the verdicts, found patterns, and wrote the patterns into the
agent.

In round 1, the analyzer made the agent escalate in two cases. One case is a customer request for a
supervisor. The other case is a ticket that does not agree with the order record. The policy escalates in only two cases, and a customer's request is not one of them. In
round 2, the analyzer made the agent refund each ticket that does not agree with the record. The instruction said
"whatever the order total." This skips the $500 limit. Both changes also decided two types of ticket that the policy does not decide, and
both decided them differently from the answer key. One type is the damage reports from Section 5. The other type is
"never came" on an order that the record shows as Delivered.

Both changes decreased the weak judge's own pass rate. Thus the loop reverted both changes, and no harmful change
stayed. The answer key shows that the round 1 version had a holdout pass rate 8.1 points lower than the
baseline. Of this, 5.9 points were on these two types of ticket. The other 2.2 points were on tickets that the
numbered rules decide. The round 2 version was 4.4 points lower, all on these two types of ticket. Thus that loss
depends on the answer key's reading.

After two rounds with no kept change, the loop's stall step asked the correct question. It sorted the remaining train
failures by cause. It put 34 of the weak judge's 57 failures in a "grader disagreement" group. By the answer key, all 34
were judge errors. The step recommended a measurement of the judge's TPR and TNR before more tuning. The climb needed that step
first, but it came last.

## 7. How to use TPR and TNR in a hill climb

The climbs suggest a procedure. This study shows some of the steps. For other steps, the study gives support but not
proof. I identify each type of step.

<!-- figure:procedure -->

**Before the climb: measure TPR, TNR and J.** *Shown in this study.* Label decisions from the baseline. Include at
least approximately 30 incorrect decisions. Measure TPR and TNR with intervals. If J is not clearly more than zero,
improve the judge or replace it. More cases or runs do not help, because the judge's pass rate changes very little when
the true quality changes. If J is clearly more than zero, divide the noise of a paired comparison by J. The result is
approximately the smallest true gain that the loop can detect. Compare it with the improvement that you expect.
*This value is an approximate rule* from the uniform-error model. It is not a guarantee, because the J that is
important is the J on the outputs that a change affects.

Two usual checks did not show the difference between these judges. The first check reads the cases with the lowest
judge scores. This check detects false fails, where the judge fails correct outputs. The calibrated and lenient judges
make false fails at approximately the same rate. They are different in what they pass. The second check measures
agreement on a random sample of 40 decisions. Such a sample from production traffic has approximately 8
incorrect decisions. Thus agreement on it measures mostly TPR:

| Check on the baseline's train decisions | calibrated | lenient | weak |
|---|---|---|---|
| Grader errors in the 10 cases with the lowest judge scores, with ties broken at random (average of 10,000 draws) | 2.0 | 2.2 | 8.2 |
| How often 40 random decisions have 90% agreement (10,000 draws) | 95% | 60% | under 0.1% |
| TPR | 0.95 | 0.95 | 0.76 |
| TNR | 0.93 | 0.65 | 0.24 |

Most of the cases with the lowest judge scores have the same score, 0. Thus the selection of the ten cases is
arbitrary. If you read them in the order of the lenient judge's own score, its ten lowest cases have no grader errors.

**Before the climb: measure the judge for each type of output.** *Shown in this study.* A judge can be good on
average and have J near zero on one type of output. Often you cannot measure this on the baseline, because the app never
gives the correct output there. Grade a correct output for each main branch of the specification. The lenient judge
fails the correct escalation on 17 of 18 tickets. This check needs only a small number of labels, and it detects that
problem. In this study, the loop used two rounds in each of three runs on a fix that the judge almost never passed.

**During the climb: label a sample of the changed outputs.** *Supported by a check after the climbs, not tested in a
loop.* A round changes a small number of outputs. Here, each round changed 44 to 97 of its 480 train and validation
decisions. Each keep or revert choice depends only on these decisions. If you label a small random sample of them,
you get an estimate of the true change without the judge.

To learn how small the sample can be, I calculated an exact probability for each round. The probability is for a
sample of k changed decisions, selected at random without replacement and labelled with the answer key. It is the
probability that fixes minus breaks in the sample has the same sign as fixes minus breaks in all the changed decisions. The 18 rounds of all the runs gave these results with k = 20. The
probability was at least 81% in 17 rounds, and 98% or more in 9 rounds. The exception was round 2 of the calibrated judge's run 2. It fixed 45 decisions and broke
37. For a net change of +8 in 86 changed decisions, it is difficult to get the correct sign from a sample. With 20 labels, the sign is correct
64% of the time. With 30 labels, it is correct 70% of the time. With k = 30, each other round was 91% or more.

These rounds come from one task. Thus they show that the method can work, not that 20 labels are sufficient in
general. For this task, a review of 20 decisions takes a few minutes. The same labels show where J on fixes and J on
breaks are different. With these labels, you can detect the incorrect reverts of the lenient judge. You can also detect that
the calibrated judge showed only a small decrease in round 2 of run 1.

<!-- figure:labels -->

**During the climb: if a change breaks the specification, examine the judge.** *A hypothesis from a small number of
examples.* The analyzer can propose a change that the specification does not allow. It can also decide a case that the
specification leaves open. If the analyzer proposes such a change because of the grader's verdicts, examine the
grader. This occurred at
the start of both rounds of the weak judge. It also occurred in the rounds of each calibrated run that applied rule 3
to the open tickets.

**After the climb: measure the judge again on the final version.** *The same result in three runs. Significant in
only one.* The judge's rates on the outputs of the final version can be different from its rates on the baseline. The cause is that
the climb changed which mistakes the agent makes. The calibrated judge's TNR decreased in all three runs (Section 5). Measure TPR and TNR again
on a labelled sample of the outputs of the final version. Include outputs that the judge passed. Report these rates
with the gain.

Do not correct the pass rate of the final version with the rates from the baseline. With those rates, the three
calibrated final versions correct to 86.7%, 92.4% and 89.9% on holdout. The true values were 84.4%, 86.2% and 87.2%.
The raw pass rates, 83.1%, 88.1% and 85.9%, were nearer to the true values each time. A correction needs rates that
are correct for the data that it corrects.

## 8. Limitations

- I used one task, one agent and a policy written as code. This task is easy for a good grader. The answer-key climb
  finished in three rounds.
- The calibrated and lenient climbs ran three times each. The answer-key and weak climbs ran one time. The repeat runs
  have the same baseline, sets and judge verdicts. Thus only the analyzer's proposals, and the changes that the loop
  kept, can be different. Three runs show which results repeat, not how frequently they repeat.
- I calculated the judge verdicts one time for each ticket and action. Thus the judges had no run-to-run noise in the
  loop. Climbs in production have this noise in addition to the effects here.
- The lenient judge is an earlier judge from the refinement of the calibrated judge. I selected its threshold to make
  it lenient.
- The analyzer was a Claude Opus 5.5 subagent that followed the text of the guide. It was not the guide in Claude Code.
  In each round, it saw the transcripts of the current version. After a reverted round, the text of the guide gives
  the analyzer the transcripts of the reverted version. My analyzer did not get them. These transcripts possibly help
  the analyzer detect that the lenient judge fails the correct escalations. Without them, all three lenient runs ended with the analyzer's conclusion that
  the fix did not work.
- The analyzer for the answer-key climb saw the expected action for each case. No judge gives this information. Thus
  this climb shows an upper limit, and it is not directly comparable with the other climbs.
- The answer key gives one reading of the unclear part of the policy. The argument in Section 5 does not depend on which
  reading is correct. The size of the TNR decrease in Section 5 does depend on it, because most of the new false passes
  are on the open tickets. The loss in round 2 of the weak judge also depends on it.
- I measured J on fixes and J on breaks with the answer key. A climb in production does not have an answer key. The labelling
  step in Section 7 estimates these values without it. I tested that step only after the climbs.

## 9. In practice

- Before a climb, measure the judge's TPR and TNR on labelled incorrect outputs. Do not use only a few dozen cases from
  production traffic. Grade a correct output for each type of case. If J = TPR + TNR − 1 is not clearly more than zero,
  repair the judge first.
- A judge's quality on the baseline does not tell you how it grades the changes that a loop tries. In each round,
  label a sample of the outputs that the change affected. The judge's errors on these outputs decide the round.
- Measure the judge again on the final version before you report its gain.
- Measure the evaluator on the decisions that the optimization makes, not only on a fixed dataset.

## How this was made

I selected the question and the four graders. Claude (Opus 5.5) built the harness, ran the loop, wrote the analysis
scripts and wrote the draft of this paper from their output. A separate Claude agent then checked each number in the
findings against the raw data, and the paper includes its corrections. An external reviewer read the first draft, and
the second draft follows that review. The reviewer recommended repeat runs as the most useful addition. I added them
after the review, and a separate Claude agent checked their numbers in the same way. The fourth draft rewrites the
text in ASD-STE100 Simplified Technical English. The judges, agent runs and analysis are in the repo. The `data`
branch has the data for each run.

## References

- Anthropic. `claude-api` skill, [`shared/evals/eval-hillclimb.md`](https://github.com/anthropics/skills/tree/main/skills/claude-api), commit `dbd4588`. 2026.
- Falkowski. [Can You Trust Your Judge's Score? A Primer on TPR and TNR for LLM Judges](https://bfalkowski.github.io/writing/judge-score.html). 2026a.
- Falkowski. [Is This Run Valid? Attributing Pipeline Failures Before Scoring LLM Evaluations](https://bfalkowski.github.io/writing/run-valid.html). 2026b.
- Martin. [Automating eval design and hillclimbing with Claude](https://claude.dev/blog/automating-eval-design-and-hillclimbing/). claude.dev, September 2026.
- Wikipedia. [Goodhart's law](https://en.wikipedia.org/wiki/Goodhart%27s_law).
- Youden. Index for rating diagnostic tests. Cancer, 1950.
