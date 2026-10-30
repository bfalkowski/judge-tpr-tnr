# Can You Trust Your Hill Climb? Applying TPR and TNR to a Keep-or-Revert Loop

Bryan Falkowski · October 2026 · Code and data: [github.com/bfalkowski/judge-tpr-tnr](https://github.com/bfalkowski/judge-tpr-tnr) (`hillclimb/`)

*Sixth draft: the fifth draft, in plainer words and in the primer's terms. Every number comes from
`hillclimb/analyze.py` and is in `hillclimb/RESULTS.md`.*

**Abstract.** My primer on TPR and TNR shows how to calibrate an LLM judge on a fixed set of outputs (Falkowski
2026a). This paper asks whether a judge with good TPR and TNR can also control a hill climb. I ran the hill-climbing
loop from Anthropic's article on hill climbing with Claude (Martin 2026). In each round, the loop tries one change. It
keeps the change only if the pass rate increases on a train set and on a validation set. I used one support agent,
three judges of known TPR and TNR, and an answer key that gives the correct output for every ticket.

The six rules in the primer stay correct. But a judge with good TPR and TNR on the baseline can still make wrong keep
or revert choices. Each change affects only a small number of outputs. The judge's accuracy on those outputs can be
far from its overall accuracy. I measure this with two numbers for each round. One is the judge's J on the outputs that
the change fixed. The other is its J on the outputs that the change broke.

Two results show this. Each result occurred in all three climbs with that judge.

- **The lenient judge reverted a real fix six times.** Its overall J was 0.61. The fix applied the $500 refund
  limit. On the outputs that the fix corrected, the judge's J was 0 or less. Each round fixed more outputs than it broke, but the judge showed a loss. Then the
  analyzer concluded that the fix did not work.
- **The climbs with the strong judge moved the agent's mistakes to where the judge does not see them.** Its overall
  J was 0.88, and its climbs
  increased the real holdout pass rate by 5 to 8 points. But each climb also changed the agent to agree with the judge
  on one kind of ticket that the policy leaves unclear. The judge scored all 43 breaks on these tickets as fixes.
  Before the climbs, it passed 6% of the agent's wrong outputs. After them, it passed 16% to 26%.

The usual checks of a judge did not separate the lenient judge from the strong judge. Section 6 gives checks at three points.
Calibrate the judge before the climb. Label a few of the outputs that each change affected. Calibrate the judge again
on the final version. I tested the middle check only on completed climbs. When the answer key took the place of a judge, the
same loop increased the holdout pass rate from 79% to 100%.

<!-- figure:glance -->

## 1. The question

Hill climbing is a common way to improve a prompt or an agent. In each round, you make one change and run the eval.
You keep the change only if the pass rate increases. Anthropic's article on hill climbing with Claude describes such a
loop (Martin 2026), and this study uses its method. An analyzer reads the results on a train set and proposes a
change. The loop keeps the change only if the pass rates on the train set and on a second set both increase. The second
set protects against changes that fit only the cases that the analyzer read.

This rule does not protect against a wrong judge. The article gives a warning about this. It says that grading errors
are a common cause of a bad eval, and that you must read graded transcripts before you trust the grader. In its own
example, the third phase of the work was "fixing graders."

When the judge is an LLM, "the pass rate increased" means "the judge passed more outputs." The primer shows what that
pass rate contains:

pass rate = TPR × θ + (1 − TNR) × (1 − θ)

Here, θ is the real fraction of correct outputs. Each keep or revert choice compares two of these pass rates.

What does one change do to the judge's pass rate? Assume that a change fixes F wrong outputs and breaks B correct
outputs, out of n. Before the change, the judge passed each of the F wrong outputs with probability 1 − TNR. After the
change, it passes each fixed output with probability TPR. Thus, on average, each fix adds this amount to the judge's
count of passes:

TPR − (1 − TNR) = TPR + TNR − 1

Each break removes the same amount. TPR + TNR − 1 is Youden's J (Youden 1950). The primer uses it to show why you
cannot correct a weak judge. If TPR and TNR are the same for every kind of output, then:

**expected change that the judge shows = J × real change, where real change = (F − B) / n.**

Thus the judge makes each real change smaller by the factor J. A judge with J = 0.88 shows a 10-point gain as about 8.8
points. A judge with J = 0.6 shows it as 6 points. A judge with J = 0 shows no gain. Also, the smallest real gain that
the loop can detect is about the noise divided by J.

<!-- figure:shrink -->
![Fig 1: the change a judge shows against the real change, one line for each judge's J](figures/shrink.png)

But TPR and TNR are usually not the same for every kind of output, and a change usually affects only a few kinds. Then
each fixed output adds its own J: the judge's TPR on the new output minus its false-pass rate on the old output. Each
broken output removes its own J:

**expected change that the judge shows = (sum of J over the fixed outputs − sum of J over the broken outputs) / n.**

Thus the net count F − B does not decide what the judge shows. The mix of fixes and breaks decides it. A real
improvement can decrease the judge's pass rate if the judge gives bad verdicts on the fixed outputs. I call the average J over
the fixes of a change its **J on fixes**. I call the average J over its breaks its **J on breaks**. In the primer's
terms, each one is the judge's J, calibrated only on the outputs that the change fixed or broke. Outputs that changed
but stayed correct, or stayed wrong, add a small extra term.

This changes the question. "Is the judge accurate?" is not sufficient. The question is also "Can the judge select the
correct changes?" The loop changes the agent's outputs, and this changes where the judge makes its mistakes.

The primer gives six rules for using a judge on a fixed set of outputs. This paper tests each rule in the loop.
Section 2 lists the rules and the result for each one. Section 5 gives the evidence.

## 2. The six rules

Section 9 of the primer lists six rules for using an LLM judge. Each rule comes from a point in the primer's earlier
sections. The table gives each point as the primer stated it before this study, and the result of this study for it.
After the study, I added what it found to rules 3, 4 and 5 of the primer. The section numbers in the table refer to
the primer. The support policy of the agent also has numbered rules. I call them "policy rule 1" to "policy rule 5."
Plain "rule 1" to "rule 6" are the primer's rules.

| Rule, as the primer stated it before this study | In a hill climb | Result |
|---|---|---|
| **1.** Measure TPR and TNR separately. One accuracy number hides which kind of mistake the judge makes. (Section 3) | Calibrate the judge before the climb | <span class="chip ok">Holds</span> |
| **2.** If J = TPR + TNR − 1 is near zero, the correction cannot help. Improve the judge first. (Section 6) | A judge with J near zero cannot control the loop | <span class="chip ok">Holds</span> |
| **3.** TPR and TNR do not depend on the mix of good and bad outputs. Thus you can use them on new data. (Section 5) | The baseline TPR and TNR apply to each new version | <span class="chip cond">Holds, if TPR and TNR are the same for each kind of output</span> |
| **4.** When the outputs change, label a new sample and check the judge again. (Section 8) | The outputs change in each round | <span class="chip mod">Holds; a climb needs it in each round</span> |
| **5.** Compare two versions with the same judge, on the same kind of data. The judge's mistakes then affect both versions in almost the same way. (Section 7) | Each keep or revert choice compares two versions | <span class="chip cond">Holds, if the change keeps the same kinds of output</span> |
| **6.** Correct the pass rate with TPR and TNR. If the judge's rates on new outputs drift, the corrected number is off. (Sections 5 and 8) | Correct the final pass rate with the baseline rates | <span class="chip cond">Holds; the climb itself moved the rates</span> |

The main finding comes from rule 5. Each keep or revert choice compares two versions with the same judge. But a change
alters which kinds of output the agent gives. Thus the judge's mistakes do not affect the two versions in the same
way.

## 3. Setup

**Terms.** I use the primer's terms where I can. A *judge* is an LLM that gives each output a *verdict*: pass or
fail. The judge gives a score, and its threshold changes the score into the verdict. The *answer key* is code that
gives the correct output. In the tables, the answer key is listed with the judges, as a perfect judge. To *calibrate* a
judge is to label outputs, run the judge on them, and measure TPR and TNR. An *output* is the action that the agent
selects for one ticket, one time. The *baseline* is the agent before any change. A *climb* is one complete use of the
loop, from the baseline to the final version. The article uses the word *grader* for a judge and for code that
scores.

**The agent.** I used the support agent from my run-validity paper without changes (Falkowski 2026b). For each ticket,
the agent gets the order record and the stock level. Then it asks Jev, a small decision model from TypeSafe, which of
four actions the policy requires: refund, reship, escalate or reply. The loop could change only two things: the
decision instructions for each question, and the descriptions of the four actions. It could not change the policy, the
fields that the agent sees, the model or the code.

**The answer key.** The answer key is the policy written as code, as in my run-validity paper.

**The tickets.** I made 400 new tickets with the same generator that made the labeled tickets that I used to refine
the judges. I divided them at random into three sets, within each customer framing. The framing is the way the customer writes the
ticket, for example plain, angry or demanding. Thus each set has about the same mix of framings.

| Set | Tickets | Use |
|---|---|---|
| Train | 120 | The analyzer reads these results to propose a change |
| Validation | 120 | The loop scores this set in each round, and keeps a change only if its pass rate increases. The article calls it the test set. It has the role of the primer's dev set |
| Holdout | 160 | The loop does not use this set. I scored it one time, after the climbs. It has the role of the primer's test set |

The loop uses the validation set to select changes. Thus a gain on validation is partly a result of that selection.
The holdout set gives an independent measure. The agent ran each ticket two times, so each set has two outputs for
each ticket. The validation set has 240 outputs.

**The loop.** The `claude-api` skill gives the article's method in the file `eval-hillclimb.md` (Anthropic 2026). I
call that file the guide. The repo has a copy of it at a fixed commit. Each round has four steps:

1. A new analyzer (a Claude Opus 5.5 subagent) reads the train transcripts and verdicts of the current version.
2. It proposes one change. The Claude session that ran the study applied the change exactly.
3. The agent runs every ticket again, and the judge gives each output a verdict.
4. If the train and validation pass rates both increase, the loop keeps the change. If not, it reverts the change.

The guide has two more steps. If only the validation pass rate increases, run the change again. That did not occur
here. After two rounds without a gain larger than the noise, use one round to sort the remaining failures by cause.
The loop stopped after three rounds in a row without such a gain, or when the analyzer had no change to propose.

<!-- figure:loop -->
![Fig 2: the 400 tickets in three sets, and the four steps of one round of the loop](figures/loop.png)

**Where I am different from the article.** I kept the article's loop and its keep rule. I changed some details, so
that the judge's mistakes are the only thing that changes between climbs:

- The loop could change only the agent's instructions and its descriptions of the four actions. The article also lets the loop change the model, the tools, the
  API settings and the code.
- Each judge scored one output at a time, as pass or fail. When there is a baseline, the article recommends a judge
  that compares two outputs in random order.
- I calculated the article's checks of the grader, but the loop did not fix the judge. The purpose was to see what the
  judge's mistakes do.
- I scored each ticket and action one time, before the climbs. Thus a judge always gave the same verdict to the same output.
- After a reverted round, the analyzer did not see the transcripts of that round. The guide gives them to the
  analyzer.
- I added the holdout set, and the answer key scored every output of every version.

Thus the study is an implementation of the article's method, adapted to isolate the judge's mistakes. It is not an
exact copy. The results apply most directly to a judge that gives a verdict on one output at a time.

The repo records the design, and each change to the design, before the results that it could affect. The branch
`hillclimb-history` keeps each commit, with the time of each round. After the first four climbs, I ran the climbs with
the strong and lenient judges two more times. These repeat climbs used the same baseline, judge verdicts and rules. Only
the analyzer's proposals could be different.

**The judges.** Each climb used one judge, or the answer key, for all its rounds. I calibrated each judge on the 240
baseline outputs of the train set, as in the primer. This is the agent's train set. The judges did not learn from it.
Of these outputs, 46 were wrong.

| Judge | What it is | TPR | TNR | J |
|---|---|---|---|---|
| answer key | the policy as code | 1.00 | 1.00 | 1.00 |
| strong | Claude Haiku 4.5. I refined its prompt on labeled tickets from earlier batches. Its code is in the repo | 0.95 | 0.93 | 0.88 |
| lenient | an earlier version of the same judge, on Jev, with a low threshold | 0.95 | 0.65 | 0.61 |
| weak | the judge from my run-validity paper (Jev, with a one-sentence prompt) | 0.76 | 0.24 | 0.00 |

A team can calibrate a judge before a climb. I calculated these numbers after the climbs, from the answer key, so the
loop could not use them. Before the climbs, I had numbers only from my earlier judge study, on different tickets. For
the strong and lenient judges, those numbers were similar to the numbers above. For the weak judge, J was 0.32 there. I call the J in the table the judge's *overall J*.

The judge sees only the ticket, the order, the stock and the action. Thus I ran each judge one time on all four actions
of each ticket, before the climbs. The loop then found the verdict for the action that the agent selected. The total API
cost was $3.89. Of this, $2.93 was for the strong judge's verdicts and $0.26 was for the repeat climbs. In the repo, the
judges are `c3` (strong), `j2` at threshold 0.3 (lenient) and `p2` (weak).

**Noise.** The guide gives an approximate noise level for a pass rate: 1/√(cases × repetitions). Here, that is about 6.5
points. This value assumes that all 240 validation outputs are independent. Also, it applies to one pass rate, not to
the difference between two. I measured two types of noise directly. First, a repetition of the same version changed very
little. Between the two repetitions of the baseline, 0 to 2 of the 120 validation tickets got a different verdict.
The number depended on the judge. That is about 1 to 2 points when you compare two versions. Second, the selection of tickets
in the set causes more noise. I resampled tickets to get paired 95% intervals on the change in each round. The
half-widths of these intervals were about 3 to 8 points. The sections below use these paired intervals.

## 4. Results of the climbs

The final version of a climb is the version that the climb ends with. If the loop kept no change, the final version is
the baseline. This table shows the first climb with each judge.

| Judge | Rounds | Change that the loop reported (validation) | Real change, validation | Real change, holdout |
|---|---|---|---|---|
| answer key | 3 | +18.3 points, 79.2% to 97.5% | +18.3 | +20.6, 79.4% to 100% |
| strong | 3 | +4.6, 77.1% to 81.7% | +4.2 | +5.0, 79.4% to 84.4% |
| lenient | 2, both reverted | no change, 89.2% | 0 | 0 |
| weak | 2, both reverted | no change, 83.8% | 0 | 0 |

Of the three judges, only the strong judge kept a change. In that climb, the gain that the loop reported was close to
the real gain. The repeat climbs show that this was partly chance:

| Judge | Climb | Rounds kept | Reported (validation) | Real change, validation | Real change, holdout [95% interval] |
|---|---|---|---|---|---|
| strong | 1 | 2 of 3 | +4.6 | +4.2 | +5.0 [−0.9, +10.9] |
| strong | 2 | 2 of 2 | +9.6 | +4.2 | +6.9 [+0.0, +13.8] |
| strong | 3 | 2 of 2 | +5.8 | +7.1 | +7.8 [+1.3, +14.7] |
| lenient | 1 | none of 2 | 0 | 0 | 0 |
| lenient | 2 | none of 2 | 0 | 0 | 0 |
| lenient | 3 | none of 2 | 0 | 0 | 0 |

All three strong climbs increased the real holdout pass rate. But only the interval for climb 3 clearly excludes zero.
On validation, the reported gain was different from the real gain by +0.4, +5.4 and −1.3 points. On holdout, the
judge's own pass rate showed a larger gain than the real gain in all three climbs, by 1.6, 4.7 and 1.6 points. All
three lenient climbs reverted every round.

<!-- figure:outcomes -->
![Fig 3: holdout gain of each climb, from its own judge and from the answer key](figures/outcomes.png)

Assume that TPR and TNR are the same for every kind of output. Then the paired noise of 3 to 8 points sets the
smallest real change that each judge can detect. For the strong judge, it is about 3.5 to 9 points. For the lenient judge, it is
about 5 to 13 points. The weak judge, with J near 0, can detect no change. The climbs agree with this. The answer key
kept three large changes, the strong judge kept small changes, and the lenient and weak judges kept no change. But this
does not explain what occurred in each round.

The next table divides each change into the outputs that it really fixed and the outputs that it really broke. It also
shows how the judge did on each group. An output here is one ticket, one time. Thus the train and validation sets
have 480 outputs together. "Fixed" and "Broken" are counts of outputs. The last two columns are net counts, and one
output is 0.21 points of the 480.

| Judge | Round | Kept? | Fixed | J on fixes | Broken | J on breaks | Real change | Judge's change |
|---|---|---|---|---|---|---|---|---|
| answer key | 1 to 3 | all kept | 38, 62, 42 | 1.00 | 15, 35, 2 | 1.00 | +23, +27, +40 | same |
| strong | 1 | kept | 32 | 0.97 | 12 | 0.50 | +20 | +25 |
| strong | 2 | reverted | 20 | 0.75 | 46 | 0.41 | −26 | −1 |
| strong | 3 | kept | 30 | 0.57 | 20 | 0.10 | +10 | +15 |
| lenient | 1 | reverted | 36 | 0.00 | 23 | 0.65 | +13 | −15 |
| lenient | 2 | reverted | 36 | 0.00 | 10 | 0.70 | +26 | −7 |
| weak | 1 | reverted | 10 | −0.20 | 68 | 0.26 | −58 | −26 |
| weak | 2 | reverted | 5 | 0.20 | 37 | 0.16 | −32 | −8 |

The table compares each round with the version that the loop tested it against. It shows the first climb with each
judge. The repeat climbs show the same pattern. In all seven strong rounds of the three climbs, J on fixes was higher
than J on breaks. In the last kept round of each climb, J on breaks was between 0.10 and 0.19. In all six lenient
rounds, J on fixes was between −0.08 and 0.00, and J on breaks was between 0.53 and 0.86. `RESULTS.md` has each round
of each climb.

<!-- figure:jscatter -->
![Fig 4: J on fixes against J on breaks for each round of each climb](figures/jscatter.png)

No judge had one J. Each judge had a J on fixes and a different J on breaks, and this difference decided the round.
Two rounds show this most clearly on the validation set:

- The lenient judge's round 2 increased the real validation pass rate by 2.5 points (95% interval −2.1 to +7.1). It
  increased the real holdout pass rate by 5.0 points. But the judge showed a decrease of 2.9 points, and that interval
  excludes zero (−6.2 to −0.4).
- The strong judge's round 2 decreased the real validation pass rate by 6.2 points (−11.7 to −0.8). The judge showed a
  decrease of only 2.5 points (−7.9 to +2.9), which is not larger than the noise. The loop reverted the change because
  the judge's validation pass rate decreased. But on train and validation together, the judge showed a net loss of only
  one output.

Section 5 gives the results for each rule.

## 5. Results for each rule

### Rule 1 holds: measure TPR and TNR separately

Two usual checks did not separate the lenient judge from the strong judge.

The first check reads the 10 cases with the lowest judge scores. This check finds false fails, where the judge fails a
correct output. The strong and lenient judges make false fails at about the same rate. They are different in what they
pass. The skill's `eval-audit.md` file says to fix the grader if more than about 1 case in 10 is a grader error. This check
flagged the lenient judge in 79% of samples and the strong judge in 69%. It did not show which judge was worse.

The second check measures agreement on 40 random outputs. A random sample from production has about 8 wrong outputs
in 40. Thus agreement on it mostly measures TPR:

| Check on the baseline's train outputs | strong | lenient | weak |
|---|---|---|---|
| Judge errors in the 10 cases with the lowest judge scores, with ties broken at random (average of 10,000 draws) | 2.0 | 2.2 | 8.2 |
| How often 40 random outputs reach 90% agreement (10,000 draws) | 95% | 60% | under 0.1% |
| TPR | 0.95 | 0.95 | 0.76 |
| TNR | 0.93 | 0.65 | 0.24 |

Most of the lowest-scoring cases have the same score, 0. Thus the selection of the ten cases is arbitrary. If you take
them in the order of the lenient judge's own score, its ten lowest cases have no judge errors.

TNR showed the difference clearly: 0.93 for the strong judge and 0.65 for the lenient judge. This agrees with the
primer.

### Rule 2 holds: a judge with J near zero cannot control the loop

The weak judge's overall J was 0.00. Thus its verdicts gave almost no information about which outputs were
correct. The analyzer could not know this. It read the verdicts, found patterns, and wrote the patterns into the agent.

In round 1, the analyzer told the agent to escalate in two cases. One case is a customer request for a supervisor.
The other case is a ticket that does not agree with the order record. The policy escalates in only two cases, and a customer's request is not
one of them. In round 2, it told the agent to refund each ticket that does not agree with the record, "whatever the
order total." This skips the $500 limit. Both changes also decided two kinds of ticket that the policy leaves unclear,
and both decided them differently from the answer key. One kind is a damage report on an order that is Lost, or that
shipped more than 14 days ago and did not arrive. The rule 3 section below calls these the unclear damage tickets. The
other kind is "never came" on an order that the record shows as Delivered.

Both changes decreased the weak judge's own pass rate. Thus the loop reverted both changes, and no harmful change
stayed. By the answer key, the round 1 version was 8.1 points worse than the baseline on holdout. Of this, 5.9 points
were on these two kinds of ticket. The other 2.2 points were on tickets that the policy rules decide. The round 2
version was 4.4 points worse, all on these two kinds of ticket. Thus that loss depends on the answer key's reading.

After two rounds with no kept change, the guide's stall step asked the correct question. This step is a round that sorts failures by cause, not a change. It sorted the remaining train
failures by cause. It put 34 of the weak judge's 57 failures in a "grader disagreement" group. By the answer key, all
34 were judge errors. The step recommended that I measure the judge's TPR and TNR before more tuning. The climb needed
that step first, but it came last.

This agrees with the primer. With J near zero, the verdicts gave almost no information, and the analyzer changed them
into wrong rules for the agent.

### Rule 3 holds only if TPR and TNR are the same for each kind of output

The primer says that TPR and TNR do not depend on the mix of good and bad outputs. That is still true. But they do
depend on the kind of output, and a change affects only a few kinds. Thus the judge's accuracy on the outputs that a
change affects can be far from its overall accuracy. Fig 4 shows this. If TPR and TNR were the same for each kind of
output, each round of a judge would be at one point. That point is on the diagonal, at the judge's overall J. Only
the answer key's rounds are at that point.

Two kinds of ticket show this most clearly.

- **The lenient judge and the correct escalation.** For an out-of-stock order over $500, the policy requires the agent
  to escalate. The lenient judge passes the correct escalation on only 1 of 18 such tickets. Its TPR on this kind of
  output is almost zero. A calibration on the baseline could not show this, because the baseline agent never gave the
  correct escalation.
- **The strong judge and the unclear damage tickets.** On these tickets, a customer reports damage on an order that is
  Lost, or that shipped more than 14 days ago and did not arrive. The policy does not say which rule applies. The
  answer key says reply. The strong judge passes the action of policy rule 3 on all 13 tickets of this kind. This
  action is reship, or refund or escalate when the item is out of stock. The judge passes reply on only 1 of them. Thus
  on these tickets, the judge's "errors" are disagreements with the answer key's reading of an unclear case.

**Added to the primer (rule 3):** calibrate the judge on each kind of output that is important. Include correct
outputs that the app does not give yet. A small number of labels is sufficient. The lenient judge fails the correct
escalation on 17 of 18 tickets, so a few labeled escalations show the problem before the climb.

### Rule 4 holds, and a climb needs it in each round

The primer says: when the outputs change, label a new sample and check the judge again. In a hill climb, the outputs
change in each round. Each round changed 44 to 97 of its 480 train and validation outputs, and the keep or revert
choice depends only on these. If you label a small random sample of them, you can estimate the real change without the
judge.

To learn how small the sample can be, I calculated an exact probability for each round. Select k changed outputs at
random, without replacement, and label them with the answer key. The probability is that fixes minus breaks in the
sample has the same sign as fixes minus breaks in all the changed outputs. With k = 20, the probability was at least
81% in 17 of the 18 rounds, and 98% or more in 9 rounds. The exception was round 2 of the strong judge's climb 2. It
fixed 45 outputs and broke 37, a net change of +8 in 86 changed outputs. For such a small net change, a sample often
gets the sign wrong. With 20 labels, the sign is correct 64% of the time. With 30 labels, it is correct 70% of the
time. With k = 30, each other round was 91% or more.

<!-- figure:labels -->
![Fig 5: probability that k labeled outputs give the correct direction, for each round](figures/labels.png)

These rounds come from one task. Thus they show that the method can work, not that 20 labels are always sufficient.
For this task, a review of 20 outputs takes a few minutes. The same labels also show where J on fixes and J on breaks
are different. With these labels, you can see the lenient judge's wrong reverts. You can also see that the strong judge
showed only a small decrease in round 2 of climb 1.

**Added to the primer (rule 4):** in a hill climb, label a small sample of the changed outputs in each round. This
evidence comes from completed climbs. I did not test it in a running loop.

### Rule 5 holds only if the change keeps the same kinds of output

The primer says that a comparison of two versions with the same judge, on the same kind of data, is more reliable
than one pass rate. The reason
is that the judge's mistakes affect both versions in almost the same way. Each keep or revert choice is such a
comparison.

But a change usually alters which kinds of output the agent gives on the same tickets. Then the judge's mistakes do
not affect both versions in the same way. The two judges show this in opposite directions.

**The lenient judge reverted a real fix.** On the outputs that the two rounds of its first climb fixed, its J was 0.00.
Round 2 applied the $500 refund limit to every refund, as the policy requires. The change fixed 36 outputs and
broke 10. For 7 of the 10 broken outputs, the judge's verdict changed from pass to fail. But for the 36 fixed outputs, the
number of passes did not increase:

- 4 changed from fail to pass.
- 4 changed from pass to fail.
- 5 passed before and after, because the judge already passed the old wrong output.
- 23 failed before and after.

The last group is the main cause. Most of these outputs are the correct escalations from the rule 3 section, which
this judge fails. After the change, the judge failed 27 of the fixed outputs. Of these 27, 26 are escalations.

Thus the change was a real improvement, but the judge showed it as a loss. The loop reverted it, as its rule says.
Round 1 tried the same fix. In round 1 also, the number of passes did not increase for its 36 fixed outputs.

<!-- figure:waffle -->
![Fig 6: what the lenient judge did with each output that round 2 fixed or broke](figures/waffle.png)

The repeat climbs gave the same result. All six lenient rounds applied the $500 limit to the out-of-stock refund. Each
time, the over-$500 out-of-stock tickets alone increased the real holdout pass rate by 2.5 points. The strong judge
kept the same fix in round 1 of all three of its climbs. In all six lenient rounds, J on fixes was between −0.08 and
0.00. The judge showed a validation decrease of 2.5 to 4.6 points, and each interval excluded zero. The loop reverted
each change. All six changes really fixed more outputs than they broke. The same keep rule with the answer key's verdicts
would keep five of them. The best reverted round of each climb had a real holdout pass rate 5.0, 3.8 and 9.1 points
above the baseline.

Each climb then stopped in the same way. The analyzer read the history. It saw two rounds that tried the $500 limit,
and the judge showed both rounds as losses. Thus the analyzer proposed no change. The analyzer in climb 1 described the
over-limit refunds as a behavior "that two artifact rounds already failed to move." The analyzer in climb 3 said that the same
behavior "has already resisted both in-scope levers." But on the over-$500 out-of-stock tickets, the fix worked each
time. The judge's mistake became the analyzer's conclusion about the agent. In this study, the analyzer did not see
the transcripts of reverted rounds. This possibly contributed to its conclusion.

Two different problems hid the fixes, and each problem needs a different repair. First, if the judge already passed
the old wrong output (a low TNR on it), a fix gets no credit. Second, if the judge fails the new correct output (a low
TPR on it), a fix can even decrease the pass rate. The judge's overall TPR and TNR do not show these problems.

**The strong judge scored breaks as fixes.** Its first climb reported a gain of +4.6 points on validation. The real
gain was +4.2 points on validation and +5.0 points on holdout. In that climb, its J on breaks was much lower than its
overall J: 0.50, 0.41 and 0.10 in the three rounds. Most of the breaks that it did not detect were on the unclear
damage tickets.

In round 3, the analyzer read the judge's verdicts. Then it wrote the judge's reading into the agent's instructions.
These instructions use the numbers of the policy rules. They said: "Rule 3 applies to every ticket on it, including
damaged or wrong-item reports and tickets that only ask for a status update: reship if stock is above 0, otherwise
refund." The change broke 20 outputs. For the 11 ordinary breaks, the judge's verdict changed from pass to fail. For the
9 breaks on the unclear damage tickets, it changed from fail to pass, as for a fix. Round 2 did the same on more
tickets. Of its 46 breaks, 10 were on the unclear damage tickets, and the judge changed each of them from fail to pass.

The repeat climbs gave the same result. Each climb kept the $500 fix in round 1. Then each climb kept a change that
applied policy rule 3 to the unclear damage tickets. The instructions in climb 2 added a rule for orders that shipped more
than 14 days ago: "rule 3, whatever the ticket reports, including damage, a wrong item or only a request for an
update." The instructions in climb 3 said: "reship if stock is above 0, otherwise refund, even when the ticket reports a
damaged or wrong item." In the seven strong rounds of the three climbs, changes broke 43 outputs on the unclear damage
tickets. The judge changed all 43 from fail to pass, as for a fix. For 105 of the other 127 breaks, it changed the
verdict from pass to fail.

<!-- figure:breaks -->
![Fig 7: the outputs that each strong round broke, by what the judge did](figures/breaks.png)

This is selection. The loop keeps the changes that get a higher pass rate from the judge. Thus the loop can move the agent toward
the judge's reading where the judge and the answer key disagree. This is Goodhart's law (Wikipedia): when the judge's
pass rate becomes the target, the loop optimizes the judge's opinion together with the agent's quality.

This argument does not depend on which reading is correct. The loop decided an unclear part of the policy with the
judge's reading, and no person saw that decision. No number from the loop shows that it decided a policy question.

This is the main finding of the study. **A judge can have good TPR and TNR on the baseline and still make wrong keep or
revert choices.** The judge's accuracy on the outputs that each change affects decides the choice. Its overall
accuracy does not.

**Added to the primer (rule 5):** a comparison with the same judge is more reliable only if the change keeps the same kinds
of output. If it does not, label a sample of the outputs that changed.

### Rule 6 holds, but the climb itself moved the rates

The climb changed which mistakes the agent makes. Thus the judge's baseline TPR and TNR no longer describe it on the
final version. In the three strong climbs, the number of wrong outputs on validation and holdout decreased from 116 at baseline.
At the final versions of climbs 1, 2 and 3, it was 90, 84 and 74. But on the unclear damage tickets, wrong outputs increased from 2 to 14, 16
and 12, and the judge passed each of them. At each final version, most of the judge's false passes were on these
tickets: 14 of 14, 16 of 22 and 12 of 12. On validation and holdout, the strong judge's TNR decreased from 0.94 at baseline to 0.84, 0.74 and 0.84. At
baseline, it failed 109 of 116 wrong outputs. At the final versions, it failed 76 of 90, 62 of 84 and 62 of 74.

The two repetitions of a ticket are not independent. Thus I also counted only one repetition for each ticket. Then the judge failed
53 of 57 wrong outputs at baseline, and 38 of 45, 32 of 43 and 33 of 39 at the three final versions. When you examine
each climb separately, only the decrease in climb 2 is unlikely to be chance (p = 0.02). For climbs 1 and 3, p is 0.2 and
0.3. Three climbs from the same baseline do not prove the result. But the decrease has the same direction and the same
cause each time.

<!-- figure:drift -->
![Fig 8: wrong outputs on the unclear damage tickets, and the share that the judge passed, before and after each strong climb](figures/drift.png)

I corrected the final holdout pass rates with the baseline TPR and TNR. The result was too high each time: 86.7%,
92.4% and 89.9%. The real values were 84.4%, 86.2% and 87.2%. The raw pass rates, 83.1%, 88.1% and 85.9%, were nearer
to the real values each time.

The primer already warns that the correction is wrong when the judge's rates drift. In a hill climb, the climb itself
causes the drift, through the selection that the rule 5 section describes.

**Added to the primer (rule 4):** after a climb, calibrate the judge again on the final version. Do this before you
correct or report its pass rate.

### Where the effects come from

- **The judge's overall J.** The order of the judges by J predicted the order of the results. The answer key improved
  the agent the most, the strong judge less, and the lenient and weak judges kept no change.
- **The outputs that each change affects.** J on fixes and J on breaks were far from the overall J (Fig 4). They
  explain the specific wrong choices: the lenient judge's reverts, and the strong judge's gains that were too large.
- **The analyzer's proposals.** The three climbs with each judge had different proposals in different words, but the
  same kinds of change. Each lenient round tried the $500 fix. Each strong climb kept the $500 fix, and then a change
  that applied policy rule 3 to the unclear damage tickets. Thus the analyzer changed the size of the results, but not
  their direction.

## 6. How to use TPR and TNR in a hill climb

The rules from Section 5 give checks at three times: before the climb, in each round, and after the climb. This study
shows some of the steps. For other steps, it gives support but not proof. Each step says which.

<!-- figure:procedure -->
![Fig 9: the steps, before, during and after a climb](figures/procedure.png)

**Before the climb: calibrate the judge.** *Shown in this study.* Label outputs from the baseline, with at least about
30 wrong outputs, and measure TPR and TNR with intervals. Do not use only agreement on a random sample, because it
mostly measures TPR (rule 1). If J is not clearly more than zero, improve the judge or replace it (rule 2). More cases
or repetitions do not help, because the judge's pass rate changes very little when the real quality changes. If J is clearly
more than zero, divide the noise of a paired comparison by J. The result is about the smallest real gain that the loop
can detect. Compare it with the gain that you expect. *This value is only a guide*, because the J that is important is
the J on the outputs that a change affects.

**Before the climb: calibrate the judge on each kind of output.** *Shown in this study.* A judge can be good overall
and have J near zero on one kind of output (rule 3). Often you cannot see this on the baseline, because the app never
gives the correct output there. Label a correct output for each main branch of the policy. The lenient judge fails the
correct escalation on 17 of 18 tickets, and a few labels find this. In this study, each lenient climb used two rounds
on a fix that the judge almost never passed.

**During the climb: label a sample of the changed outputs.** *Supported by a check after the climbs, not tested in a
loop.* The keep or revert choice depends only on the outputs that the change affects (rules 4 and 5). With 20 labeled
changed outputs, the probability of the correct direction was at least 81% in 17 of 18 rounds. Use these labels
together with the judge's pass rate when you make the choice.

**During the climb: if a change breaks the policy, examine the judge.** *A hypothesis from a small number of
examples.* The analyzer can propose a change that the policy does not allow. It can also decide a case that the policy
leaves open. If the analyzer proposes such a change because of the judge's verdicts, examine the judge. This occurred at
the start of both rounds of the weak judge. It also occurred in the rounds of each strong climb that applied policy
rule 3 to the unclear damage tickets.

**After the climb: calibrate the judge again on the final version.** *The same result in three climbs, significant in
one.* The climb changes which mistakes the agent makes, so the judge's rates on the final version can be different
from its rates on the baseline (rule 6). Label a sample of the final version's outputs, and include outputs that the
judge passed. Measure TPR and TNR again, and report these rates with the gain. Do not correct the final pass rate with
the baseline rates.

## 7. Limitations

- I used one task, one agent and a policy written as code. This task is easy for a good judge: the answer-key climb
  finished in three rounds. The study shows how these problems occur, not how often they occur in other tasks.
- The strong and lenient judges each ran three climbs. The answer key and the weak judge each ran one climb. The
  repeat climbs have the same baseline, sets and judge verdicts. Thus only the analyzer's proposals could be different.
  Three climbs show which results repeat, not how often they repeat.
- I scored each ticket and action one time. Thus a judge always gave the same verdict to the same output. In a real
  climb, the verdicts also vary, in addition to the effects here.
- Each judge scored one output at a time. When there is a baseline, the article recommends a judge that compares two
  outputs. I did not test that setup.
- The lenient judge is an earlier version of the strong judge. I selected its threshold to make it lenient.
- The analyzer was a Claude Opus 5.5 subagent that followed the text of the guide. It was not the guide that runs in
  Claude Code. After a reverted round, the guide gives the analyzer the transcripts of that round. My analyzer did not
  get them. These transcripts possibly help the analyzer see that the lenient judge fails the correct escalations.
  Without them, all three lenient climbs ended with the analyzer's conclusion that the fix did not work.
- The analyzer in the answer-key climb saw the expected action for each case. No judge gives this information. Thus
  this climb shows an upper limit, and it is not directly comparable with the other climbs.
- The loop used the same validation set in each round. Thus a gain on validation is not an independent measure after
  many rounds. The holdout set is.
- The answer key gives one reading of the unclear damage tickets. The argument in the rule 5 section does not depend on
  which reading is correct. The size of the TNR decrease in the rule 6 section does depend on it, because most of the
  new false passes are on these tickets. The loss in round 2 of the weak judge also depends on it.
- I measured J on fixes and J on breaks with the answer key. A real climb does not have an answer key. The label step
  in Section 6 estimates these values without it. I tested that step only on completed climbs.

## Next study

The next study will add the steps in Section 6 to the loop. Then it will run the same climbs again, with the same
agent, tickets and judges. It will examine these questions:

- Does a calibration before the climb find the lenient judge's problem?
- With labels in each round, does the loop keep a real fix that the judge does not see?
- Can the loop stop a change that decides a case that the policy leaves open?
- How many labels does each round need?

## How this was made

I selected the question, the answer key and the three judges. Claude (Opus 5.5) built the harness, ran the loop, wrote
the analysis scripts and wrote the draft of this paper from their output. A separate Claude agent then checked each
number in the findings against the raw data, and the paper includes its corrections. An external reviewer read the
first draft, and the second draft follows that review. The reviewer recommended repeat climbs as the most useful
addition. I added them after the review, and a separate Claude agent checked their numbers in the same way. The fourth
draft rewrote the text in ASD-STE100 Simplified Technical English. The fifth draft sorted the results by the six rules
of the primer. The sixth draft uses the primer's terms and plainer words. The judges, agent runs and analysis are in
the repo. The `data` branch has the data for each run.

## References

- Anthropic. `claude-api` skill, [`shared/evals/eval-hillclimb.md`](https://github.com/anthropics/skills/tree/main/skills/claude-api), commit `dbd4588`. 2026.
- Falkowski. [Can You Trust Your Judge's Score? A Primer on TPR and TNR for LLM Judges](https://bfalkowski.github.io/writing/judge-score.html). 2026a.
- Falkowski. [Is This Run Valid? Attributing Pipeline Failures Before Scoring LLM Evaluations](https://bfalkowski.github.io/writing/run-valid.html). 2026b.
- Martin. [Automating eval design and hillclimbing with Claude](https://claude.dev/blog/automating-eval-design-and-hillclimbing/). claude.dev, September 2026.
- Wikipedia. [Goodhart's law](https://en.wikipedia.org/wiki/Goodhart%27s_law).
- Youden. Index for rating diagnostic tests. Cancer, 1950.
