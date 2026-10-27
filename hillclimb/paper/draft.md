# Can You Trust Your Hill Climb? Applying TPR and TNR to a Keep-or-Revert Loop

Bryan Falkowski · October 2026 · Code and data: [github.com/bfalkowski/judge-tpr-tnr](https://github.com/bfalkowski/judge-tpr-tnr) (`hillclimb/`)

*First draft. Every number comes from `hillclimb/analyze.py` and is listed in `hillclimb/RESULTS.md`.*

**Abstract.** Hill climbing improves an app one change at a time: run the eval, keep the change if the score rises,
revert it if not. When an LLM judge grades the eval, every keep or revert compares two judge pass rates. The primer on
TPR and TNR showed that a judge's pass rate mixes in two kinds of mistake. This paper asks what those mistakes do to a
hill climb. I ran the same loop four times on a support agent from my earlier work, each time against a different
fixed grader: the answer key, and three judges whose TPR and TNR I had measured. The answer key graded every decision
afterwards. With the answer key, the climb raised the agent's pass rate on held-out tickets from 79% to 100%. With a
calibrated judge, the reported gain matched the true one, about 5 points, but the climb settled an open policy question
the judge's way. With a lenient judge, the loop reverted a change that truly fixed 36 decisions, because on balance
the judge credited none of them. With a weak judge, nothing the loop tried could register. One number explains all four: a judge
credits a fixed decision, and charges a broken one, by TPR + TNR − 1, measured on the decisions the change touches.
The last sections show how to use that before, during and after a climb.

## 1. The question

Hill climbing is a common way to improve a prompt or an agent. Each round you make one change, run the eval, and keep
the change only if the score goes up. Anthropic's guide for doing this with Claude adds a train/test split: the analyzer
that proposes changes reads only the train cases, and a change is kept only when both the train and test scores rise
(Martin 2026). That guards against overfitting to the cases you read.

It does not guard against the grader. When the grader is an LLM judge, "the score went up" means "the judge passed more
outputs." The primer showed what a judge's pass rate is made of (Falkowski 2026a):

pass rate = TPR × θ + (1 − TNR) × (1 − θ)

where θ is the true share of good outputs. Every keep or revert in a hill climb compares two of these numbers.

So what does a change do to the judge's pass rate? Suppose a change fixes F outputs that were wrong and breaks B outputs
that were right, out of n. Before the change, the judge passed each of the F wrong outputs with probability 1 − TNR. After
it, the judge passes each fixed output with probability TPR. On average the judge credits each fix with

TPR − (1 − TNR) = TPR + TNR − 1

and by the same argument it charges each break the same amount. TPR + TNR − 1 is Youden's J (Youden 1950), the number
the primer used to show why a weak judge can't be corrected. Here it has a second job:

**observed change ≈ J × true change, where true change = (F − B) / n.**

A judge shrinks every real improvement by J. A judge with J = 0.88 shows a 10-point gain as about 8.8 points. A judge
with J = 0.6 shows it as 6. A judge with J near 0 shows nothing, whatever the change did.

Because the loop compares observed changes against its noise floor, J also sets the smallest real gain the loop can see:

**smallest visible true gain ≈ noise floor / J.**

That is the simple version. It assumes the judge's TPR and TNR are the same for every output. They are not. A change in
a hill climb usually touches one kind of output, and a judge's rates differ by kind. What matters is J on the outputs the
change touches, and it can be different for the outputs a change fixes and the outputs it breaks. The rest of this paper
shows what that does to a real climb, and how to measure it.

## 2. Setup

**The agent.** The support agent from my run-validity paper (Falkowski 2026b), imported unchanged. For each ticket it looks up the
order and stock and asks Jev, a small decision model from TypeSafe, which of four actions the five-rule support policy
calls for: refund, reship, escalate, or reply. The climb could change only two things: the decision instructions sent
with every question, and the descriptions of the four actions. The policy text, the fields the agent sees, the model and
the code were off-limits.

**The answer key.** The policy written as code, as in my previous two papers. Every decision has a known correct action.

**Tickets.** 400 new tickets from the same generator as my judge-calibration study (Falkowski 2026c), split at random within each customer framing:
120 train, 120 test, and 160 holdout. The loop read train transcripts, scored train and test every round, and never
used holdout. Each version of the agent ran every ticket twice.

**The loop.** I followed Anthropic's published hill-climbing guide as written: the `eval-hillclimb.md` file of the
`claude-api` skill (Anthropic 2026), vendored in the repo at a fixed commit. Each round, a fresh analyzer (Claude Opus
5.5) read the current version's train transcripts and grades and proposed one change, which was applied word for word.
A change was kept when train and test both rose. After two rounds without a real rise, the loop ran one round that
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

## 3. Four climbs

| Grader | Rounds | What the loop reported (test) | True change, test | True change, holdout |
|---|---|---|---|---|
| answer key | 3 | +18.3 points, 79.2% to 97.5% | +18.3 | +20.6, 79.4% to 100% |
| calibrated | 3 | +4.6, 77.1% to 81.7% | +4.2 | +5.0, 79.4% to 84.4% |
| lenient | 2, both reverted | no change, 89.2% | 0 | 0 |
| weak | 2, both reverted | no change, 83.8% | 0 | 0 |

Brackets for these changes are in `RESULTS.md`. The calibrated judge's gains are within noise: the 95% intervals on the true changes
run from about −2 to +11 points.

The noise floor for this loop was 6.5 points (about 1/√(120 × 2) for a pass rate on 120 test tickets at 2 reps). By the
rule in Section 1, the smallest true gain each judge could show was about 7.3 points for the calibrated judge and 10.6 for the lenient judge. The weak judge, with J near 0, could
not show any gain at all. The table matches that. The answer key's climb made three
large changes. The calibrated judge's climb made small ones that scraped past. The lenient and weak judges' climbs kept nothing.

The averages hide what happened inside each round. The next table splits every change into the decisions it truly fixed
and the ones it truly broke, and shows how much of each the grader saw. "J on fixes" is the grader's net credit per fixed decision, and "J on breaks" its net charge per broken one. If the judge's rates were the same everywhere, both would equal
its J.

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

Counts are decisions on the train and test tickets, 480 in all, compared with the version the change was tested
against.

No judge had one J. Each had a J for what a change fixed and a different J for what it broke, and the difference decided
the round. The next three sections take the cases in turn.

## 4. A judge that passes mistakes can't see fixes

The lenient judge's average J was 0.61. On the decisions its two rounds fixed, its J was 0.00.

Round 2 made the $500 refund limit apply to every refund, which the policy requires. It fixed 36 decisions and broke 10.
The judge charged 7 of the 10 breaks, and it credited the 36 fixes with nothing. Four went from fail to pass and four
from pass to fail. Five it had passed before and after, because it had already passed the old mistake. Twenty-three it
failed before and after. That last group explains most of it: on tickets where an out-of-stock order over $500 has to be
escalated, this judge passes the correct escalation on 1 of 18. Its TPR on that kind of decision is close to zero.
Twenty-six of the 27 fixed decisions it failed after the change are those escalations.

So the change was a real improvement, +26 decisions on train and test and 5 points on holdout, and the judge scored it
as a loss of 7. The loop reverted it, correctly by its own rule. Round 1 tried the same fix, and the judge credited none
of its 36 fixes either.

Two different gaps hid the fixes, and they need different repairs. Low TNR on the old mistakes means the judge already
passed them, so fixing them earns nothing. Low TPR on the new correct answers means the judge fails them, so fixing them
can even cost. Neither shows in the judge's average, and the second can't be measured on the baseline at all, because at
baseline the agent never produced the correct escalation. Grading a correct answer for each kind of ticket finds it.

## 5. The climb moves mistakes to where the judge can't see them

The calibrated judge is a good one, with J = 0.88 on the baseline. Its climb reported +4.6 points and the true gain was +4.2 on test and
+5.0 on holdout. On the headline number, it did its job.

Its J on breaks was much lower than its overall J: 0.50, 0.41 and 0.10 in the three rounds. Most of the breaks it missed were on one
kind of ticket. When a customer reports damage on an order that is Lost, or that shipped more than 14 days ago and was
never delivered, the policy text doesn't say which rule applies. The answer key says reply. The calibrated judge passes the action rule 3
would give (reship, or refund or escalate when out of stock) on all 13 such tickets, and it passes reply on 1.

In round 3 the analyzer, reading the judge's verdicts, wrote the judge's reading into the agent's instructions: "Rule 3 applies to
every ticket on it, including damaged or wrong-item reports and tickets that only ask for a status update: reship if
stock is above 0, otherwise refund." The change broke 20 decisions. The judge charged the 11 that were ordinary mistakes and
credited the 9 on those open tickets as fixes. On test and holdout, answer-key mistakes on the open tickets went from 2
at baseline to 14 at the winner, and the judge passed every one of them. At the winner, all of its false passes were on that
one kind of ticket, and its TNR on the agent's decisions had gone from 0.94 to 0.84 (109 of 116 mistaken decisions
failed, against 76 of 90). The two runs of a ticket are not independent. Counting one run per ticket, it is 53 of 57
against 38 of 45, which could be chance (p = 0.2), so the drop is suggestive, not proven.

Round 2 shows the same effect from the other side. It broke 46 decisions. Ten were on the open tickets, which the judge counted as fixes, and the rest it mostly charged. The judge saw a change that truly cost 26 decisions as a loss of 1, and the
loop reverted it by that one decision.

I don't think the answer key's reading of these tickets is clearly right. [TK: your view on which reading the policy
intends, if you have one.] The point holds either way. The climb settled a question the policy leaves open, it settled
it the judge's way, and nothing in the loop's numbers shows that it did. The judge's error rate on the final agent was
not the rate I had measured on the baseline. A hill climb is a search for outputs the judge passes, and a judge's
remaining mistakes are outputs it passes, so a climb can concentrate them. This is Goodhart's law (Goodhart 1975) at the
size of one category.

## 6. A judge with J near zero teaches the wrong rules

The weak judge's J on the baseline was 0.00: its verdicts carried almost no information about whether a decision was right. The
analyzer had no way to know that. It read the verdicts, found patterns, and wrote them into the agent.

In round 1 it made the agent escalate whenever a customer asks for a supervisor or a ticket contradicts the order record.
The policy only escalates in two situations, and a customer's request is not one of them. In round 2 it made the agent
refund any ticket that contradicts the record "whatever the order total", which skips the $500 limit. Both changes also
decided two kinds of ticket the policy leaves open differently from the answer key: the damage reports from Section 5,
and "never came" on an order the record shows Delivered. Both lowered the weak judge's own score, so both were reverted, and nothing
harmful shipped. Under the answer key, round 1 would have cost 8.1 points on holdout: 5.9 on those open tickets and 2.2
on tickets the numbered rules decide. Round 2 would have cost 4.4, all of it from the open tickets, so that loss depends
on the answer key's reading.

After two wasted rounds, the loop's stall step asked the right question. It sorted the remaining train failures by cause
and put 34 of the weak judge's 57 in a "grader disagreement" bucket. All 34 were real judge errors. It recommended measuring the
judge's TPR and TNR before tuning further. That was the first step the climb needed, and it came last.

## 7. Applying TPR and TNR to a hill climb

The four climbs suggest a procedure. Each step uses a number the primer already defined.

**Before the climb: measure J and turn it into a smallest visible gain.** Label decisions from the baseline, with at
least about 30 wrong ones, and measure TPR and TNR with intervals. Compute J and divide the loop's noise floor by it. If
the result is bigger than the improvement you hope to find, the climb can't show it. Fix the judge first, or add cases
and reps until it can. Here that rule predicted every arm: the calibrated judge could see changes of about 7 points, the lenient judge
about 11, and the weak judge none.

Two common checks did not separate these judges. Reading the lowest-scoring cases finds false fails, the judge failing
correct outputs. The calibrated and lenient judges make those at about the same rate, and they differ in what they pass. A random
sample of 40 decisions from real traffic holds about 8 wrong ones, so agreement on it mostly measures TPR:

| Check on the baseline's train decisions | calibrated | lenient | weak |
|---|---|---|---|
| Grader errors among the 10 lowest-scoring cases, ties broken at random (average over 10,000 draws) | 2.0 | 2.2 | 8.2 |
| How often 40 random decisions reach 90% agreement (10,000 draws) | 95% | 60% | under 0.1% |
| TPR | 0.95 | 0.95 | 0.76 |
| TNR | 0.93 | 0.65 | 0.24 |

Most of the lowest-scoring cases tie at a score of 0, so which ten get read is arbitrary. Read in order of the lenient
judge's own score, its ten lowest hold no grader errors at all.

**Before the climb: measure J by kind of output.** A judge can be fine on average and have J near zero on one kind of
output. On the baseline you often can't see that, because the app never produces the correct output there. Grade a
correct output for each main branch of the spec. The lenient judge fails the correct escalation on 17 of 18 tickets. That
check would have found it in minutes, before the loop spent two rounds on a fix it could never credit.

**During the climb: label the changed outputs, not the eval.** A round changes few outputs. Here each round changed 44
to 97 of its 480 train and test decisions, and every keep or revert depends only on those. Labelling a small random
sample of them estimates the true change directly, without trusting the judge. Looking back at all ten rounds, 20
labelled changed decisions would have pointed the same way as the answer key at least 82% of the time in every round,
and 98% or more in seven of them. At 30, every round was 91% or higher. For this task that is a few minutes of review per round. It
also shows where J on fixes and J on breaks differ, which is how the lenient judge's reverts and the calibrated
judge's round 2 would have been caught.

**During the climb: treat a change that breaks the spec as a judge problem.** When the analyzer proposes something the
spec rules out, or settles a case the spec leaves open, because the grader rewards it, the grader is the thing to look
at. The weak judge's two rounds and the calibrated judge's round 3 each started that way.

**After the climb: measure the judge again on the winner.** The judge's rates on the final outputs can differ from its
rates on the baseline, because the climb changed which mistakes the app makes. Re-measure TPR and TNR on a labelled
sample of the winner's outputs, including outputs the judge passed, and report them next to the gain. Don't correct the
winner's pass rate with the baseline's rates. With them, the winner of the calibrated judge's climb corrects to 86.7% on holdout. The truth was 84.4%,
and the raw pass rate, 83.1%, was closer. The correction needs rates that hold on the data it corrects, as my judge-calibration study found (Falkowski 2026c).

## 8. Limitations

- One task, one agent, and a policy written as code. The task is easy for a good grader: the answer-key arm was done in
  three rounds.
- Each climb ran once. The analyzer's proposals vary from run to run, and a second run of any arm could take a different
  path. Repeating each judge arm is the next step.
- Judge verdicts were computed once per ticket and action, so the judges had no run-to-run noise in the loop. Real climbs
  have that noise on top of the effects here.
- The lenient judge is an earlier judge from my judge-calibration study, at a threshold I chose to make it lenient.
- The analyzer was a Claude Opus 5.5 subagent following the guide's text, not the guide running inside Claude Code. It
  saw the current version's transcripts each round. After a reverted round, the guide's text would have given it the
  reverted version's, which might have helped it notice the lenient judge failing the correct escalations.
- The answer-key arm's analyzer saw each case's expected action, which no judge gives. That arm is a ceiling, not a peer.
- The answer key's reading of the open tickets is one reading of an ambiguous policy. Section 5's point doesn't depend on
  which reading is right. The weak judge's round 2 loss does.
- J on fixes and J on breaks are measured with the answer key, which a real climb doesn't have. Section 7's labelling step is how
  to estimate them without one, and I tested it only retrospectively.

## 9. In practice

- A judge shows a real change at about J times its size, where J = TPR + TNR − 1. Divide your noise floor by J to get the
  smallest gain your climb can see.
- Measure TPR and TNR on labelled wrong outputs, not on a few dozen cases of real traffic, and grade a correct output for
  each kind of case.
- Each round, label a sample of the outputs the change touched. That is where the judge's errors decide the round.
- Measure the judge again on the winner before you report its gain.

[TK: optional. A sentence or two on where you've seen this in your own work, if you can say it publicly.]

## How this was made

I chose the question and the four graders. Claude (Opus 5.5) built the harness, ran the loop, wrote the analysis
scripts, and drafted this paper from their output. A separate Claude agent then checked every number in the findings
against the raw data, and its corrections are included. The judges, agent runs and analysis are in the repo, with each
run's data on its `data` branch.

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
