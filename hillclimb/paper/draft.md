# Can You Trust Your Hill Climb? Applying TPR and TNR to a Keep-or-Revert Loop

Bryan Falkowski · October 2026 · Code and data: [github.com/bfalkowski/judge-tpr-tnr](https://github.com/bfalkowski/judge-tpr-tnr) (`hillclimb/`)

*Second draft, revised after an external review. Every number comes from `hillclimb/analyze.py` and is listed in
`hillclimb/RESULTS.md`.*

**Abstract.** Hill climbing improves an app one change at a time: run the eval, keep the change if the score rises,
revert it if not. When an LLM judge grades the eval, every keep or revert compares two judge pass rates. The primer on
TPR and TNR showed that a judge's pass rate mixes in two kinds of mistake. This paper asks what those mistakes do to a
hill climb. I ran the same loop four times on a support agent from my earlier work, each time against a different
fixed grader: the answer key, and three judges whose TPR and TNR I had measured. The answer key graded every decision
afterwards. With the answer key, the climb raised the agent's pass rate on untouched holdout tickets from 79% to 100%.
With a calibrated judge, the reported gain matched the true one in this run, about 5 points, but the climb settled an
open policy question the judge's way. With a lenient judge, the loop reverted a change that truly fixed 36 decisions,
because on balance the judge credited none of them. With a weak judge, nothing the loop tried could register. If a
judge's TPR and TNR were the same for every output, it would show any change at J = TPR + TNR − 1 times its true size.
They are not, and the climbs show why that matters: a judge's quality on the baseline does not tell you how it grades
the particular changes a loop explores. The last sections show how to measure that before, during and after a climb.

## 1. The question

Hill climbing is a common way to improve a prompt or an agent. Each round you make one change, run the eval, and keep
the change only if the score goes up. Anthropic's guide for doing this with Claude splits the cases in two: the analyzer
that proposes changes reads only one part, and a change is kept only when the scores on both parts rise (Martin 2026).
That guards against overfitting to the cases you read.

It does not guard against the grader. When the grader is an LLM judge, "the score went up" means "the judge passed more
outputs." The primer showed what a judge's pass rate is made of (Falkowski 2026a):

pass rate = TPR × θ + (1 − TNR) × (1 − θ)

where θ is the true share of good outputs. Every keep or revert in a hill climb compares two of these numbers.

So what does a change do to the judge's pass rate? Suppose a change fixes F outputs that were wrong and breaks B outputs
that were right, out of n. Before the change, the judge passed each of the F wrong outputs with probability 1 − TNR. After
it, the judge passes each fixed output with probability TPR. On average the judge credits each fix with

TPR − (1 − TNR) = TPR + TNR − 1

and by the same argument it charges each break the same amount. TPR + TNR − 1 is Youden's J (Youden 1950), the number
the primer used to show why a weak judge can't be corrected. If the judge's TPR and TNR are the same for every output,
which I'll call the uniform-error model, then

**expected observed change = J × true change, where true change = (F − B) / n.**

Under this model a judge shrinks every real improvement by J. A judge with J = 0.88 shows a 10-point gain as about 8.8
points, a judge with J = 0.6 shows it as 6, and a judge with J = 0 shows nothing. A judge with negative J favors worse
outputs. It also gives a rule of thumb: when J is clearly above zero, the smallest true gain the loop can tell from its
noise is about the noise divided by J.

The uniform-error model is the starting point, not the result. A change in a hill climb usually touches a few kinds of
output, and a judge's rates differ by kind. Each fixed output adds its own J, the judge's TPR on its new answer minus its
false-pass rate on the old one, and each broken output subtracts its own:

**expected observed change = (sum of J over the fixed outputs − sum of J over the broken outputs) / n.**

So the net count F − B no longer decides what the judge sees. The mix of fixes and breaks does. A change can be a real
improvement and still lower the judge's score, if the outputs it fixes are ones the judge grades poorly. I'll call the
average J over a change's fixes its "J on fixes," and the average over its breaks its "J on breaks."

That reframes the question. It is not only whether a judge is accurate, but whether it is reliable enough to steer an
optimization. Those are different. The loop changes what the agent produces, that changes where the judge's errors fall,
and that shapes the next round. The rest of this paper shows what that does to a real climb, and how to measure it.

## 2. Setup

**The agent.** The support agent from my run-validity paper (Falkowski 2026b), imported unchanged. For each ticket it
looks up the order and stock and asks Jev, a small decision model from TypeSafe, which of four actions the five-rule
support policy calls for: refund, reship, escalate, or reply. The climb could change only two things: the decision
instructions sent with every question, and the descriptions of the four actions. The policy text, the fields the agent
sees, the model and the code were off-limits.

**The answer key.** The policy written as code, as in my previous two papers. Every decision has a known correct action.

**Tickets.** 400 new tickets from the same generator as my judge-calibration study (Falkowski 2026c), split at random
within each customer framing into three sets:

| Set | Tickets | Role in the loop |
|---|---|---|
| Train | 120 | The analyzer reads these transcripts to propose changes |
| Validation | 120 | Scored every round; a change is kept only if its score here rises. The guide calls this set "test" |
| Holdout | 160 | Never used by the loop; scored only afterwards |

Because the validation set decides which changes survive, it is part of the optimization. The holdout set is the
independent evidence of whether a gain is real. Each version of the agent ran every ticket twice, so a set's pass rate is
a mean over two decisions per ticket, 240 on validation.

**The loop.** I followed Anthropic's published hill-climbing guide as written: the `eval-hillclimb.md` file of the
`claude-api` skill (Anthropic 2026), vendored in the repo at a fixed commit. Each round, a fresh analyzer (Claude Opus
5.5) read the current version's train transcripts and grades and proposed one change, which was applied word for word.
A change was kept when its train and validation scores both rose. When validation rose and train did not, the change was
run once more and kept only if validation rose again. After two rounds without a real rise, the loop ran one round that
sorted the remaining failures by cause, and it stopped after three such rounds or when the analyzer had nothing to
propose. The study's design and every decision made during it are recorded in the repo before the results they could
affect.

**The graders.** Each climb used one fixed grader for every round. I measured each judge on the baseline's 240 train
decisions, 46 of which were wrong:

| Grader | What it is | TPR | TNR | J |
|---|---|---|---|---|
| answer key | the policy as code | 1.00 | 1.00 | 1.00 |
| calibrated | the final judge from my judge-calibration study (Claude Haiku 4.5) | 0.95 | 0.93 | 0.88 |
| lenient | an earlier judge from that study (Jev), at a low threshold | 0.95 | 0.65 | 0.61 |
| weak | the judge from my run-validity paper (Jev, one sentence) | 0.76 | 0.24 | 0.00 |

A judge's input is fully set by the ticket, order, stock and action, so I ran each judge once on all four actions of
every ticket before the climbs started. The loop looked up the verdict for whatever action the agent chose. Total API
spend was $3.64, $2.93 of it the calibrated judge. In the repo the three judges are `c3`, `j2` at threshold 0.3, and
`p2`.

**Noise.** The guide's rule of thumb for a pass rate is 1/√(cases × runs), about 6.5 points here. That treats all 240
validation decisions as independent, and it is for one pass rate, not a comparison. I measured two kinds of noise
directly. Re-running the same version changed very little: between the baseline's two runs, 0 to 2 of the 120
validation tickets got a different grade, depending on the grader, which is about 1 to 2 points of noise for comparing
two versions. The larger term is which tickets happen to be in the set. Paired 95% intervals on each round's change,
resampling tickets, had half-widths of about 3 to 8 points. I use the paired intervals below.

## 3. Four climbs

| Grader | Rounds | What the loop reported (validation) | True change, validation | True change, holdout |
|---|---|---|---|---|
| answer key | 3 | +18.3 points, 79.2% to 97.5% | +18.3 | +20.6, 79.4% to 100% |
| calibrated | 3 | +4.6, 77.1% to 81.7% | +4.2 | +5.0, 79.4% to 84.4% |
| lenient | 2, both reverted | no change, 89.2% | 0 | 0 |
| weak | 2, both reverted | no change, 83.8% | 0 | 0 |

The calibrated judge's climb was the only imperfect one that kept any change, and in this run the reported gain matched
the realized one. That shows a calibrated judge can report a gain accurately. It does not show that it reliably does:
the 95% intervals on the true change run from about −2 to +11 points, and this is one run. The round-level results below
show why even a good baseline judge can make the wrong call when a change touches outputs it grades differently.

Under the uniform-error model, with the paired noise of 3 to 8 points, the calibrated judge could register true changes
of roughly 3.5 to 9 points, the lenient judge roughly 5 to 13, and the weak judge, with J near 0, none. The climbs are
consistent with that: the answer key kept three large changes, the calibrated judge kept small ones, and the lenient and
weak judges kept nothing. But the uniform model misses what happened inside each round.

The next table splits every change into the decisions it truly fixed and the ones it truly broke, and shows how much of
each the grader saw. A decision here is one run of one ticket, so the train and validation sets hold 480. "Fixed" and
"broken" count decisions, and the last two columns are net counts: each decision is 0.21 points of the 480.

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

Each round is compared with the version it was tested against.

No judge had one J. Each had a J on fixes and a different J on breaks, and the difference decided the round. Two rounds
show it most clearly on the validation set alone:

- The lenient judge's round 2 truly raised validation by 2.5 points (95% interval −2.1 to +7.1) and holdout by 5.0. The
  judge saw a drop of 2.9 points, with an interval that excludes zero (−6.2 to −0.4).
- The calibrated judge's round 2 truly cut validation by 6.2 points (−11.7 to −0.8). The judge saw a drop of 2.5 points
  (−7.9 to +2.9), which was not distinguishable from noise. The loop reverted it because its validation score fell,
  but across train and validation together the judge saw a net loss of only one decision.

The next three sections take the cases in turn.

## 4. A judge that passes mistakes can't see fixes

The lenient judge's J on the baseline was 0.61. On the decisions its two rounds fixed, its J was 0.00.

Round 2 made the $500 refund limit apply to every refund, which the policy requires. It fixed 36 decisions and broke 10.
The judge charged 7 of the 10 breaks, and it credited the 36 fixes with nothing. Four went from fail to pass and four
from pass to fail. Five it had passed before and after, because it had already passed the old mistake. Twenty-three it
failed before and after. That last group explains most of it: on tickets where an out-of-stock order over $500 has to be
escalated, this judge passes the correct escalation on 1 of 18. Its TPR on that kind of decision is close to zero.
Twenty-six of the 27 fixed decisions it failed after the change are those escalations.

So the change was a real improvement, and the judge scored it as a loss. The loop reverted it, correctly by its own
rule. Round 1 tried the same fix, and the judge credited none of its 36 fixes either.

Two different gaps hid the fixes, and they need different repairs. Low TNR on the old mistakes means the judge already
passed them, so fixing them earns nothing. Low TPR on the new correct answers means the judge fails them, so fixing them
can even cost. Neither shows in the judge's average, and the second can't be measured on the baseline at all, because at
baseline the agent never produced the correct escalation. Grading a correct answer for each kind of ticket finds it.

## 5. The climb moves mistakes to where the judge can't see them

The calibrated judge is a good one, with J = 0.88 on the baseline. Its climb reported +4.6 points on validation, and the
true gain was +4.2 on validation and +5.0 on holdout.

Its J on breaks was much lower than its overall J: 0.50, 0.41 and 0.10 in the three rounds. Most of the breaks it missed
were on one kind of ticket. When a customer reports damage on an order that is Lost, or that shipped more than 14 days
ago and was never delivered, the policy text doesn't say which rule applies. The answer key says reply. The calibrated
judge passes the action rule 3 would give (reship, or refund or escalate when out of stock) on all 13 such tickets, and
it passes reply on 1.

In round 3 the analyzer, reading the judge's verdicts, wrote the judge's reading into the agent's instructions: "Rule 3
applies to every ticket on it, including damaged or wrong-item reports and tickets that only ask for a status update:
reship if stock is above 0, otherwise refund." The change broke 20 decisions. The judge charged the 11 that were ordinary
mistakes and credited the 9 on those open tickets as fixes. Round 2 had done the same on a larger scale: 10 of its 46
breaks were on the open tickets, which the judge counted as fixes.

Two related things are happening here.

The first is selection. The loop keeps changes the judge rewards, so it pulls the agent toward the judge's reading of
anything the judge reads differently from the answer key. That is Goodhart's law (Goodhart 1975): once the judge's score
is the target, the loop optimizes the judge's opinion along with the agent's quality.

The second is a shift in where the judge's errors fall, and this one is the empirical finding. The climb changed which
mistakes the agent makes, so the judge's error rates on the baseline stopped describing it. On validation and holdout,
answer-key mistakes on the open tickets went from 2 at baseline to 14 at the winner, and the judge passed every one of
them. At the winner, all of its false passes were on that one kind of ticket, and its TNR on the agent's decisions had
gone from 0.94 to 0.84 (109 of 116 mistaken decisions failed, against 76 of 90). The two runs of a ticket are not
independent. Counting one run per ticket, it is 53 of 57 against 38 of 45, which could be chance (p = 0.2), so the drop
is suggestive, not proven.

I don't think the answer key's reading of these tickets is clearly right. [TK: your view on which reading the policy
intends, if you have one.] The argument doesn't need it to be. The point is that the loop resolved an ambiguity in the
policy, resolved it the judge's way, and never showed that decision to anyone. Nothing in the loop's numbers says a
policy question was settled.

## 6. A judge with J near zero teaches the wrong rules

The weak judge's J on the baseline was 0.00: its verdicts carried almost no information about whether a decision was
right. The analyzer had no way to know that. It read the verdicts, found patterns, and wrote them into the agent.

In round 1 it made the agent escalate whenever a customer asks for a supervisor or a ticket contradicts the order record.
The policy only escalates in two situations, and a customer's request is not one of them. In round 2 it made the agent
refund any ticket that contradicts the record "whatever the order total", which skips the $500 limit. Both changes also
decided two kinds of ticket the policy leaves open differently from the answer key: the damage reports from Section 5,
and "never came" on an order the record shows Delivered. Both lowered the weak judge's own score, so both were reverted,
and nothing harmful shipped. Under the answer key, round 1 would have cost 8.1 points on holdout: 5.9 on those open
tickets and 2.2 on tickets the numbered rules decide. Round 2 would have cost 4.4, all of it from the open tickets, so
that loss depends on the answer key's reading.

After two wasted rounds, the loop's stall step asked the right question. It sorted the remaining train failures by cause
and put 34 of the weak judge's 57 in a "grader disagreement" bucket. All 34 were real judge errors. It recommended
measuring the judge's TPR and TNR before tuning further. That was the first step the climb needed, and it came last.

## 7. Applying TPR and TNR to a hill climb

The four climbs suggest a procedure. Some steps are demonstrated here. Others are hypotheses this study supports but
does not establish, and I mark them.

**Before the climb: measure TPR, TNR and J.** *Demonstrated here.* Label decisions from the baseline, with at least
about 30 wrong ones, and measure TPR and TNR with intervals. If J is not clearly above zero, the right move is to
improve or replace the judge. More cases or runs won't help, because the judge's score barely moves with true quality.
If J is clearly positive, divide the noise of a paired comparison by J for a rough sense of the smallest true gain the
loop can register, and compare it with the improvement you hope to find. *That threshold is a rule of thumb* under the
uniform-error model, not a guarantee, because the J that matters is the one on the outputs a change touches.

Two common checks did not separate these judges. Reading the lowest-scoring cases finds false fails, the judge failing
correct outputs. The calibrated and lenient judges make those at about the same rate, and they differ in what they pass.
A random sample of 40 decisions from real traffic holds about 8 wrong ones, so agreement on it mostly measures TPR:

| Check on the baseline's train decisions | calibrated | lenient | weak |
|---|---|---|---|
| Grader errors among the 10 lowest-scoring cases, ties broken at random (average over 10,000 draws) | 2.0 | 2.2 | 8.2 |
| How often 40 random decisions reach 90% agreement (10,000 draws) | 95% | 60% | under 0.1% |
| TPR | 0.95 | 0.95 | 0.76 |
| TNR | 0.93 | 0.65 | 0.24 |

Most of the lowest-scoring cases tie at a score of 0, so which ten get read is arbitrary. Read in order of the lenient
judge's own score, its ten lowest hold no grader errors at all.

**Before the climb: measure the judge by kind of output.** *Demonstrated here.* A judge can be fine on average and have
J near zero on one kind of output. On the baseline you often can't see that, because the app never produces the correct
output there. Grade a correct output for each main branch of the spec. The lenient judge fails the correct escalation on
17 of 18 tickets. That check would have found it in minutes, before the loop spent two rounds on a fix it could never
credit.

**During the climb: label a sample of the changed outputs.** *Supported retrospectively, not yet tested in a loop.* A
round changes few outputs. Here each round changed 44 to 97 of its 480 train and validation decisions, and every keep or
revert depends only on those. Labelling a small random sample of them estimates the true change without trusting the
judge. To check how small, I took each round's changed decisions, drew k of them at random without replacement, counted
fixes minus breaks with the answer key, and asked whether the sign matched the count over all of them, repeating 5,000
times per round. At k = 20 the sign matched in at least 82% of draws in every round, and in 98% or more in seven of the
ten. At k = 30 every round was 91% or higher. These are ten rounds of one task, so they show the idea can work, not that
20 is enough in general. For this task, 20 decisions is a few minutes of review. The same labels show where J on fixes
and J on breaks differ, which is how the lenient judge's reverts and the calibrated judge's round 2 would have been
caught.

**During the climb: treat a change that breaks the spec as a judge problem.** *A hypothesis from three examples.* When
the analyzer proposes something the spec rules out, or settles a case the spec leaves open, because the grader rewards
it, the grader is the thing to look at. The weak judge's two rounds and the calibrated judge's round 3 each started that
way.

**After the climb: measure the judge again on the winner.** *Supported, not proven.* The judge's rates on the final
outputs can differ from its rates on the baseline, because the climb changed which mistakes the agent makes. The
calibrated judge's TNR drop in Section 5 is the example, and it is suggestive rather than significant. Re-measure TPR and
TNR on a labelled sample of the winner's outputs, including outputs the judge passed, and report them next to the gain.
Don't correct the winner's pass rate with the baseline's rates. With them, the winner of the calibrated judge's climb
corrects to 86.7% on holdout. The truth was 84.4%, and the raw pass rate, 83.1%, was closer. The correction needs rates
that hold on the data it corrects, as my judge-calibration study found (Falkowski 2026c).

## 8. Limitations

- One task, one agent, and a policy written as code. The task is easy for a good grader: the answer-key arm was done in
  three rounds.
- Each climb ran once. The analyzer's proposals vary from run to run, and each keep or revert changes the rest of the
  search. Repeating the calibrated and lenient arms is the next step, since they give the clearest contrast.
- Judge verdicts were computed once per ticket and action, so the judges had no run-to-run noise in the loop. Real climbs
  have that noise on top of the effects here.
- The lenient judge is an earlier judge from my judge-calibration study, at a threshold I chose to make it lenient.
- The analyzer was a Claude Opus 5.5 subagent following the guide's text, not the guide running inside Claude Code. It
  saw the current version's transcripts each round. After a reverted round, the guide's text would have given it the
  reverted version's, which might have helped it notice the lenient judge failing the correct escalations.
- The answer-key arm's analyzer saw each case's expected action, which no judge gives. That arm is a ceiling, not a peer.
- The answer key's reading of the open tickets is one reading of an ambiguous policy. Section 5's point doesn't depend on
  which reading is right. The weak judge's round 2 loss does.
- J on fixes and J on breaks are measured with the answer key, which a real climb doesn't have. Section 7's labelling
  step is how to estimate them without one, and I tested it only retrospectively.

## 9. In practice

- Before a climb, measure the judge's TPR and TNR on labelled wrong outputs, not on a few dozen cases of real traffic,
  and grade a correct output for each kind of case. If J = TPR + TNR − 1 is not clearly above zero, fix the judge first.
- A judge's quality on the baseline does not tell you how it grades the changes a loop explores. Each round, label a
  sample of the outputs the change touched. That is where the judge's errors decide the round.
- Measure the judge again on the winner before you report its gain.
- Evaluate the evaluator on the decisions the optimization actually makes, not only on a fixed dataset.

[TK: optional. A sentence or two on where you've seen this in your own work, if you can say it publicly.]

## How this was made

I chose the question and the four graders. Claude (Opus 5.5) built the harness, ran the loop, wrote the analysis
scripts, and drafted this paper from their output. A separate Claude agent then checked every number in the findings
against the raw data, and its corrections are included. An external reviewer read the first draft, and this draft
follows that review. The judges, agent runs and analysis are in the repo, with each run's data on its `data` branch.

## References

- Altman and Bland. [Diagnostic tests 1: sensitivity and specificity](https://www.bmj.com/content/308/6943/1552). BMJ, 1994.
- Anthropic. `claude-api` skill, [`shared/evals/eval-hillclimb.md`](https://github.com/anthropics/skills/tree/main/skills/claude-api), commit `dbd4588`. 2026.
- Falkowski. [Can You Trust Your Judge's Score? A Primer on TPR and TNR for LLM Judges](https://bfalkowski.github.io/writing/judge-score.html). 2026a.
- Falkowski. [Is This Run Valid? Attributing Pipeline Failures Before Scoring LLM Evaluations](https://bfalkowski.github.io/writing/run-valid.html). 2026b.
- Falkowski. Hill Climbing an LLM Judge on TPR and TNR: A Worked Example With an Answer Key. Draft, [judge-tpr-tnr](https://github.com/bfalkowski/judge-tpr-tnr) `paper/draft.md`. 2026c.
- Goodhart. Problems of monetary management: the U.K. experience. Papers in Monetary Economics, Reserve Bank of Australia, 1975.
- Husain and Shankar. [evals-skills](https://github.com/ai-evals-course/evals-skills), `validate-evaluator`.
- Martin. [Automating eval design and hillclimbing with Claude](https://claude.dev/blog/automating-eval-design-and-hillclimbing/). claude.dev, September 2026.
- Rogan and Gladen. Estimating prevalence from the results of a screening test. American Journal of Epidemiology, 1978.
- Shankar, Zamfirescu-Pereira, Hartmann, Parameswaran and Arawjo. [Who Validates the Validators?](https://arxiv.org/abs/2404.12272) UIST 2024.
- Youden. Index for rating diagnostic tests. Cancer, 1950.
