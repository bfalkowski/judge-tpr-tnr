# Hill-Climb Study Overview

Anthropic's hill-climbing loop, run with LLM judges of known TPR and TNR

Bryan Falkowski · October 2026 · Code and data: [github.com/bfalkowski/judge-tpr-tnr](https://github.com/bfalkowski/judge-tpr-tnr) (`hillclimb/`)

**Summary.** My primer, [Can You Trust Your Judge's Score?](https://bfalkowski.github.io/writing/judge-score.html),
shows how to calibrate an LLM judge. You label a set of outputs, run the judge on them, and measure TPR and TNR. This
study asks a second question: if a judge calibrates well, can it also control a hill climb?

Anthropic's article [Automating eval design and hillclimbing with
Claude](https://claude.dev/blog/automating-eval-design-and-hillclimbing/) describes a hill-climbing loop. In each
round, an analyzer proposes one change to the app. The loop keeps the change only if the pass rate increases on two
sets of cases. When an LLM judge gives the pass rates, the judge decides which changes stay.

I ran this loop on a support agent with three judges of known TPR and TNR. An answer key gave the correct output for
every ticket. Thus I could see each mistake of each judge, in each round.

**The result:** a judge can calibrate well on the baseline and still make bad choices in the loop. Each change
affects only a small number of outputs. On those outputs, the judge can be much less accurate than its overall TPR and
TNR show. One judge reverted a real fix six times. Another judge kept changes that moved the agent's mistakes to
tickets where the judge does not see them.

The six rules in Section 9 of the primer stay correct. But one calibration before the climb is not sufficient.
Check the judge with labeled outputs three times: before the climb, in each round, and after the climb.

## 1. Why I ran this study

The article says that grading errors are a common cause of a bad eval. It tells you to read graded transcripts before
you trust the grader. In its own example, one phase of the work was "fixing graders."

My primer calibrates a judge on a fixed set of outputs. A hill climb is different. The outputs change in each round,
and the judge's scores decide which changes stay. I wanted to know two things. Do the primer's rules still hold in
this loop? And what more must you measure?

**Terms.** I use the primer's terms where I can. A *judge* is an LLM that scores an output as pass or fail. The
*answer key* is code that gives the correct output. To *calibrate* a judge is to label outputs, run the judge on them,
and measure TPR and TNR. The article uses the word *grader* for a judge and for code that scores. The support policy
also has numbered rules. I call them "policy rule 1" to "policy rule 5." Plain "rule 1" to "rule 6" are the primer's
rules.

## 2. The six rules and the results

Section 9 of the primer lists six rules. Each rule comes from a point in the primer's earlier sections. The table gives
each point as the primer stated it before this study. After the study, I added what it found to rules 3, 4 and 5 of
the primer. The section numbers in the table refer to the primer.

| Rule, as the primer stated it before this study | In a hill climb | Result |
|---|---|---|
| **1.** Measure TPR and TNR separately. One accuracy number hides which kind of mistake the judge makes. (Section 3) | Calibrate the judge before the climb | <span class="chip ok">Holds</span> |
| **2.** If J = TPR + TNR − 1 is near zero, the correction cannot help. Improve the judge first. (Section 6) | A judge with J near zero cannot control the loop | <span class="chip ok">Holds</span> |
| **3.** TPR and TNR do not depend on the mix of good and bad outputs. Thus you can use them on new data. (Section 5) | The baseline TPR and TNR apply to each new version | <span class="chip cond">Holds, if TPR and TNR are the same for each kind of output</span> |
| **4.** When the outputs change, label a new sample and check the judge again. (Section 8) | The outputs change in each round | <span class="chip mod">Holds; a climb needs it in each round</span> |
| **5.** Compare two versions with the same judge, on the same kind of data. The judge's mistakes then affect both versions in almost the same way. (Section 7) | Each keep or revert choice compares two versions | <span class="chip cond">Holds, if the change keeps the same kinds of output</span> |
| **6.** Correct the pass rate with TPR and TNR. If the judge's rates on new outputs drift, the corrected number is wrong. (Sections 5 and 8) | Correct the final pass rate with the baseline rates | <span class="chip cond">Holds; the climb itself moved the rates</span> |

## 3. How the study worked

**The agent.** A support agent from my earlier work reads a ticket and selects one of four actions: refund, reship,
escalate or reply. A written policy with five rules gives the correct action. The answer key is that policy, written
as code. The loop could change only the agent's instructions and its descriptions of the four actions.

**The tickets.** I made 400 new tickets and divided them into three sets:

| Set | Tickets | Use |
|---|---|---|
| Train | 120 | The analyzer reads these results to propose a change |
| Validation | 120 | The loop scores this set in each round to make its choice. The article calls it the test set. It has the role of the primer's dev set |
| Holdout | 160 | The loop does not use this set. I scored it one time, after the climbs. It has the role of the primer's test set |

The agent ran each ticket two times. Thus each set has two outputs for each ticket.

**The loop.** Each round has four steps:

1. A new analyzer reads the train results. The analyzer is a Claude agent (Claude Opus 5.5) with file and shell
   tools.
2. It proposes one change.
3. The agent runs all the tickets again, and the judge scores each output.
4. If the pass rate increases on train and on validation, the loop keeps the change. If not, it reverts the change.

<!-- figure:loop -->

**The judges.** I calibrated each judge on the 240 train outputs of the baseline, as in the primer. Of these outputs,
46 were wrong.

| Judge | What it is | TPR | TNR | J |
|---|---|---|---|---|
| answer key | the policy as code | 1.00 | 1.00 | 1.00 |
| strong | Claude Haiku 4.5, with a prompt that I refined on labeled tickets | 0.95 | 0.93 | 0.88 |
| lenient | an earlier version of the same judge, on Jev, with a low threshold | 0.95 | 0.65 | 0.61 |
| weak | the judge from my run-validity paper, on Jev | 0.76 | 0.24 | 0.00 |

A team can calibrate a judge before a climb. I calculated these numbers after the climbs, from the answer key, so the
loop could not use them. Before the climbs, I had numbers only from my earlier judge study, on different tickets. For
the strong and lenient judges, those numbers were similar to the numbers above. For the weak judge, J was 0.32 there.

**The climbs.** A climb is one full run of the loop. There were eight climbs, with 18 rounds in total. The strong and
lenient judges each ran three climbs, because the analyzer can propose different changes each time. The answer key and
the weak judge each ran one climb.

**Where I am different from the article.** I kept the article's loop and its keep rule. I changed some details, so that
the judge's mistakes are the only thing that changes between climbs:

- The loop could change only the agent's instructions. The article also lets the loop change the model, the tools,
  the API settings and the code.
- Each judge scored one output at a time, as pass or fail. When there is a baseline, the article recommends a judge
  that compares two outputs in random order.
- I calculated the article's checks of the grader, but the loop did not fix the judge. The purpose was to see what the
  judge's mistakes do.
- I scored each ticket and action one time, before the climbs. Thus the judges had no run-to-run noise.
- After a reverted round, the analyzer did not see the transcripts of that round.
- I added the holdout set, and the answer key scored every output of every version.

**Two new numbers: J on fixes and J on breaks.** A change fixes some outputs and breaks some others. I calibrated the
judge on only those outputs:

- **J on fixes** is the judge's J on the outputs that the change fixed. TPR is how often it passes the new correct
  output. TNR is how often it failed the old wrong output.
- **J on breaks** is the judge's J on the outputs that the change broke. TPR is how often it passed the old correct
  output. TNR is how often it fails the new wrong output.

If J on fixes is near zero, the judge gives no credit for real fixes. If J on breaks is near zero, it gives no penalty
for real breaks. If TPR and TNR were the same for each kind of output, both numbers would be equal to the judge's
overall J.

## 4. What I found, rule by rule

### Rule 1 holds: measure TPR and TNR separately

The usual checks did not separate the lenient judge from the strong judge:

- The `claude-api` skill, which the article describes, says to read the lowest-scoring cases. If more than about 1 in
  10 is a grader error, fix the grader. Both judges had about 2 errors in their 10 lowest cases. This check flagged the
  lenient judge in 79% of samples and the strong judge in 69%. It did not show which judge was worse.
- On 40 random outputs, the lenient judge reached 90% agreement in 60% of samples. The strong judge reached it in 95%.
  Most random outputs are correct, so this check mostly measures TPR. Both judges had TPR 0.95.

TNR showed the difference clearly: 0.93 for the strong judge and 0.65 for the lenient judge.

### Rule 2 holds: a judge with J near zero cannot control the loop

The weak judge had J = 0.00. Thus its scores gave almost no information about which outputs were correct. The analyzer
could not know this. It found patterns in the scores and wrote them into the agent. For example, it told the agent to
escalate when a customer asks for a supervisor. The policy does not allow that. Both of its changes made the agent
worse. The loop reverted both, because the judge's own pass rate also decreased.

### Rule 3 holds only if TPR and TNR are the same for each kind of output

TPR and TNR do not depend on the mix of good and bad outputs. That is still true. But they do depend on the kind of
output, and a change affects only a few kinds. Thus the judge's accuracy on the outputs that a change affects can be
far from its overall accuracy. Fig 2 shows J on fixes and J on breaks for each round. If TPR and TNR were the same for
each kind of output, each round of a judge would be at one point on the diagonal: the judge's overall J. Only the
answer key's rounds are at that point.

<!-- figure:jscatter -->

Two kinds of ticket show this:

- **The lenient judge and the correct escalation.** For an out-of-stock order over $500, the policy says escalate. The
  lenient judge passes the correct escalation on only 1 of 18 such tickets. The baseline agent never gave this output.
  Thus a calibration on baseline outputs could not find the problem.
- **The strong judge and the unclear damage tickets.** On these tickets, a customer reports damage on an order that is
  Lost, or that shipped more than 14 days ago and did not arrive. The policy does not say which rule applies. The
  answer key says reply. The strong judge passes the action of policy rule 3. These are disagreements on an unclear
  case, not clear judge errors.

**Added to the primer (rule 3):** calibrate the judge on each kind of output that is important. Include correct outputs
that the app does not give yet.

### Rule 4 holds, and a climb needs it in each round

The primer says: when the outputs change, label a new sample and check the judge again. In a hill climb, the outputs
change in each round. Each round changed 44 to 97 of the 480 train and validation outputs. The keep or revert choice
depends only on these changed outputs.

Thus you can label a few of them. After the climbs, I calculated how often 20 changed outputs show the correct
direction of the real change. The 20 outputs are selected at random and labeled correctly. In 17 of 18 rounds, the
chance was at least 81%. In the one exception, the net change was near zero. Fig 3 shows the results for 10, 20 and 30
labels.

<!-- figure:labels -->

**Added to the primer (rule 4):** in a hill climb, label a small sample of the changed outputs in each round. I tested
this only on completed climbs, not in a running loop.

### Rule 5 holds only if the change keeps the same kinds of output

The primer says that a comparison of two versions with the same judge is more reliable than one pass rate. The reason
is that the judge's mistakes affect both versions in almost the same way. Each keep or revert choice is such a
comparison.

But a change usually changes which kinds of output the agent gives on the same tickets. Then the judge's mistakes do
not affect both versions in the same way:

- **The lenient judge reverted a real fix.** Each lenient round tried the same fix: apply the $500 limit to
  out-of-stock refunds. The fix changed wrong refunds into correct escalations. The judge fails the correct
  escalation, so most fixes got no credit. The breaks still decreased the pass rate. The judge showed a decrease of 2.5
  to 4.6 points in all six rounds. But each change fixed more outputs than it broke.
- **The strong judge scored breaks as fixes.** In the seven rounds of its three climbs, changes broke 43 outputs on the unclear damage
  tickets, by the answer key. The judge scored all 43 as fixes. Each strong climb kept such a change. Thus the
  judge's gain on holdout was larger than the real gain in all three climbs: +6.6, +11.6 and +9.4 points, against a
  real +5.0, +6.9 and +7.8 points.

<!-- figure:outcomes -->

This is the main finding. **A judge can calibrate well on the baseline and still make wrong keep or revert choices.**
The judge's accuracy on the outputs that each change affects decides the choice. Its overall accuracy does not.

**Added to the primer (rule 5):** a comparison with the same judge is reliable only if the change keeps the same kinds
of output. If it does not, label a sample of the outputs that changed.

### Rule 6 holds, but the climb itself moved the rates

The climb changed which mistakes the agent makes. On validation and holdout, the number of wrong outputs decreased
from 116 to 90, 84 and 74. But on the unclear damage tickets, wrong outputs increased from 2 to 14, 16 and 12, and the
judge passes them. Thus the judge's TNR decreased from 0.94 to 0.84, 0.74 and 0.84. The decrease has the same
direction in all three climbs, but it is statistically significant only in the second climb.

<!-- figure:drift -->

I corrected the final pass rates with the baseline TPR and TNR. The result was too high in all three climbs: 86.7%,
92.4% and 89.9%, against a real 84.4%, 86.2% and 87.2%. The raw pass rates were nearer to the real values.

The primer already warns that the correction is wrong when the judge's rates drift. In a hill climb, the climb itself
causes the drift. This is a form of Goodhart's law: when the judge's pass rate becomes the target, the loop moves the
agent toward the judge's blind spots.

**Added to the primer (rule 4):** after a climb, calibrate the judge again on the final version. Do this before you
correct or report its pass rate.

### Where the effects come from

- **The judge's overall J.** The order of the judges by J predicted the order of the results. The answer key improved
  the agent the most, the strong judge less, and the lenient and weak judges kept no change.
- **The outputs that each change affects.** J on fixes and J on breaks explain the specific wrong choices: the lenient
  judge's reverts, and the strong judge's gains that were too large.
- **The analyzer.** The three climbs with each judge used different words, but they made the same kinds of change.
  Thus the analyzer changed the size of the results, but not their direction.

## 5. What to do in a hill climb

| When | What to do | Why |
|---|---|---|
| Before the climb | Calibrate the judge, as in the primer. Include at least 30 wrong outputs | A random sample is mostly correct outputs. It measures TPR, but not TNR |
| Before the climb | Include a correct output for each important kind of case, also kinds that the app does not give yet | A judge can have J near zero on one kind of output |
| In each round | Label a small sample of the outputs that the change affected | The keep or revert choice depends only on these outputs |
| In each round | Examine each change that breaks the policy, or that decides a case the policy leaves open | The loop can move the app toward the judge's blind spots |
| After the climb | Calibrate the judge again on the final version | The climb can change the judge's TPR and TNR |

## 6. What the study does not show

- **How often this occurs.** I used one task, one agent and one policy. The study shows how these problems occur, not
  how often they occur.
- **How often the results repeat.** Each judge ran in three climbs at most.
- **Which reading of the unclear damage tickets is correct.** The answer key gives one reading. The size of the TNR
  decrease depends on it. The main point does not: the loop decided an unclear case, and no person saw the decision.
- **Whether the labels work in a running loop.** I tested the labels only on completed climbs, with random samples and
  correct labels.
- **An independent validation result.** The loop used the same validation set in each round. Only the holdout set
  gives an independent number.
- **Judges that compare two outputs.** Each judge here scored one output at a time.

## 7. The next study

The next study will add the checks from Section 5 to the loop. Then it will run the same climbs again, with the same
agent, tickets and judges. It will examine these questions:

- Does a calibration before the climb find the lenient judge's problem?
- With labels in each round, does the loop keep a real fix that the judge does not see?
- Can the loop stop a change that decides an unclear case?
- How many labels does each round need?

## Sources

- Falkowski. [Can You Trust Your Judge's Score? A Primer on TPR and TNR for LLM Judges](https://bfalkowski.github.io/writing/judge-score.html). bfalkowski.github.io, October 2026.
- Martin, Lance. [Automating eval design and hillclimbing with Claude](https://claude.dev/blog/automating-eval-design-and-hillclimbing/). claude.dev, September 28, 2026.
- The full results: [`hillclimb/RESULTS.md`](https://github.com/bfalkowski/judge-tpr-tnr/blob/main/hillclimb/RESULTS.md), generated by `hillclimb/analyze.py`.
- Wikipedia. [Goodhart's law](https://en.wikipedia.org/wiki/Goodhart%27s_law).
