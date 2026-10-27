# Decisions made during the hill-climbing study

Each entry is recorded when it is made, with what was known at the time.

1. **2026-10-27, after the baseline: the split is not re-drawn for p2.** The skill (Step 3) says to check that
   train and test means agree within noise at baseline and to re-draw if they don't. Under p2's grader the baseline
   train and test pass rates differ by 0.075, against a noise floor of 0.065. Under the answer key the same rows
   differ by 0.017, and under the lenient judge by 0.054. All arms climb the same split, so the arms stay comparable;
   p2 is not re-drawn, and the gap is reported as one of the skill's checks that fired.

2. **2026-10-27, p2 round 1: an out-of-sandbox read, accepted.** The p2 round 1 analyzer listed one file outside its
   sandbox: the harness's saved copy of its own command output (a table it computed from the sandbox's traces and
   results), which the harness wrote elsewhere because it was too large to show inline. It holds only data derived
   from the sandbox, so the proposal is applied as written.

3. **2026-10-27, after key's categorization round: the next analyzers see the categorization.** The skill says to
   dispatch per bucket after a categorization rather than run another content round blind. In this study the only
   way to act on a bucket is through the next analyzer, so from here on, in every arm, a content round after a
   categorization gets its summary (`categorization.md` in the sandbox). Its suggestion to move date arithmetic into
   code is outside the scope and is not acted on by the outer session.

4. **2026-10-27, lenient categorization: helper files outside the sandbox, accepted.** The analyzer wrote a script and
   its output to a scratch folder of its own outside the sandbox and read them back. They are derived from the
   sandbox only. From here on, analyzers are told to keep scratch files in the sandbox's out/ folder.

5. **2026-10-27, after key v3 (train 1.000, test 0.975), before key v4's analyzer runs: a round with no proposal ends
   the arm.** The design's stop rule assumes every round has a change to run. The analyzer prompt allows it to report
   that no change can clear the noise floor. When it does, the arm stops there, rather than running more analyzers
   that will find nothing on a train split with few or no failures. This applies to every arm.

6. **Recorded after the runs, from the independent check: the analyzers saw the current version's traces, which
   departs from the skill's text after a revert.** The skill hands the analyzer "the previous round's train-split trace
   files". After a reverted round, that is the reverted version. `hc.py sandbox` gave the current (best kept) version's
   traces instead, with a one-line history of each earlier proposal. DESIGN.md described this choice, but it was not
   flagged as a departure from the skill when it was made. It matters for the lenient arm (FINDINGS.md, finding 4).

7. **2026-10-27, after the external review and before any replicate run: two more climbs each for c3 and lenient.**
   Arms `c3-r2`, `c3-r3`, `lenient-r2` and `lenient-r3` (arms.json) repeat the original c3 and lenient climbs exactly:
   the same baseline agent run (gh40542493329), the same precomputed judge verdicts and threshold, the same analyzer
   prompt and sandbox (the current version's train traces, decisions 3 and 4 included), and the same keep, stall and
   stop rules, including decision 5. Only the analyzer's proposals can differ, so the replicates measure how much of
   each finding depends on one trajectory. The p2 and key arms are not repeated. The original arms count as run 1.
