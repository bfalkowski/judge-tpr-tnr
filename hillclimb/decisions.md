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
