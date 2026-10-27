# Proposed changes to the claude-api skill's hillclimb guide

`eval-hillclimb.md` and `eval-audit.md` here are the vendored copies (`vendor/claude-api-evals/`, anthropics/skills
`dbd4588`) with the changes proposed in `../FINDINGS.md`. `skill.patch` is the diff. Each change and the finding behind it:

| Change | File and place | Finding |
|---|---|---|
| Measure a judge's TPR and TNR, per branch, before round 1; grade a reference output where the app never produces one; run the categorization once on the baseline as a screen | eval-hillclimb.md, Step 0.5 | 2, 4, 5 |
| A fourth analyzer steer: the spec outranks the grader | eval-hillclimb.md, Step 4 | 2, 3 |
| After a revert, show the analyzer the changed cases with old and new grades | eval-hillclimb.md, Step 4 | 4 |
| Re-check the judge on the winner and report its rates next to the headline | eval-hillclimb.md, Step 5 | 2 |
| Read a sample of the grader's passes, not only its failures | eval-audit.md, section 4 | 5 |
| Calibrate per class (TPR and TNR) instead of one agreement number | eval-audit.md, section 4 | 4, 5 |

None of these has been tested by rerunning the loop with the patched guide.
