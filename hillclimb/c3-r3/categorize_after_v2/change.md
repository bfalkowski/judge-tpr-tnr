# v2 categorization: no change this round

## Counts

14 failing train rows (9 cases).

| Bucket | Count | Cases |
|---|---|---|
| artifact_gap | 0 | |
| grader_disagreement | 4 | Y194 x2, Y338 x2 |
| harness | 0 | |
| structural | 6 | Y007 x2, Y039 x2, Y273 x2 |
| variance | 4 | Y114 r0, Y144 r1, Y282 r0, Y331 r1 |

## What each non-empty bucket needs instead of another content round

- grader_disagreement: fix the grading side. Y194 ("waiting forever") and Y338 ("hasn't arrived") are Delivered orders more than 30 days old with no damage or wrong item reported, so no policy rule calls for escalate and the agent's reply matches the artifact, but the Haiku judge applies rule 2's 30-day escalation anyway. Have a person label these two, then either correct the judge prompt (rule 2 needs a reported damaged or wrong item) or pin the expected action in the case data. If the intended answer really is escalate, that is a policy change, not an artifact change.
- structural: stop adding text and change how the decision is made. The rules Jev breaks are already stated plainly (supervisor requests never change the action; the $500 limit never touches reply; 30 days or less refunds), and Y007, Y039 and Y273 have failed in every round since content was aimed at them. Jev is anchoring on surface cues (an escalation demand in the ticket, a total over $500). Options: compute the status and day-count branch in code and pass Jev only the matching step, strip the customer's requested action from the ticket before the choice, or split it into two typed questions (which step, then whether the $500 cap applies).
- variance: these are coin flips near the decision boundaries (13, 14 and 16 days since shipping; a wrong-item refund) with confidence 0.35 to 0.48 on both sides. Run more reps per case (or majority-vote three calls) and widen the noise band before treating a 0.5 case as a regression or a win. More wording will not move a model that is already split on the same input.

## Files read

All under /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3-r3/v2-categorize/:

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- traces/Y007_rep0.json
- traces/Y007_rep1.json
- traces/Y039_rep0.json
- traces/Y039_rep1.json
- traces/Y114_rep0.json
- traces/Y114_rep1.json
- traces/Y144_rep0.json
- traces/Y144_rep1.json
- traces/Y194_rep0.json
- traces/Y194_rep1.json
- traces/Y273_rep0.json
- traces/Y273_rep1.json
- traces/Y282_rep0.json
- traces/Y282_rep1.json
- traces/Y331_rep0.json
- traces/Y331_rep1.json
- traces/Y338_rep0.json
- traces/Y338_rep1.json
- out/categorize.json (written, then re-read to check it parses)

The directory listings of the sandbox root, traces/ and out/ were also viewed.
