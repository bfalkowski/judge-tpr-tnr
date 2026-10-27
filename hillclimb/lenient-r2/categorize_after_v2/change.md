# Categorization of remaining train failures (baseline artifact)

39 failing rows out of 240 (120 cases x 2 reps).

| Bucket | Rows | Cases |
|---|---|---|
| structural | 22 | Y013, Y050, Y054, Y083, Y124, Y192, Y343, Y346, Y385 (both reps, rule 4 cap missed); Y039, Y282 (both reps, day boundary missed) |
| artifact_gap | 8 | Y027, Y133, Y194, Y338 (both reps) |
| grader_disagreement | 7 | Y007 r1, Y061, Y084, Y169 (both reps) |
| variance | 2 | Y119 r0, Y344 r1 |
| harness | 0 | All 240 traces end in a valid action |

## What each bucket needs instead of another content round

- **structural (22):** Move the logic out of the prompt. Apply rule 4 in code after Jev picks (refund with total > $500 becomes escalate), and put precomputed `days_since_shipped` and `days_since_delivered` in the state so the model doesn't have to do date math at the 14 and 30 day boundaries. v1 and v2 both put the cap into the artifact and only fixed Y385.
- **artifact_gap (8):** The policy owner has to decide what happens when the ticket contradicts the order record, and that rule has to go into the policy that both the agent and the judge read. The two cases are a delivered order reported missing (Y194, Y338) and a wrong or damaged item on an order that was never delivered (Y027, Y133). Elsewhere the judge passes reply for delivered-but-missing (Y030, Y362, Y344 r0), but the policy never says that.
- **grader_disagreement (7):** Calibrate the judge before trusting more score movement. It fails actions the policy calls for: rule 5 replies on Y061 and Y169, rule 2 refunds on Y084 ($500 is not over $500) and Y007. It also passes 16 rows that break the policy, for example refunds on Y138, Y179 and Y318 delivered more than 30 days ago, reships inside 14 days on Y114, Y258 and Y304, and reply on Y063 and Y119 r1. Hand-label these rows, measure judge TPR/TNR against the labels, and have the judge return a reason. Or grade against a deterministic policy oracle, since every rule here can be computed from the order record.
- **variance (2):** Run more reps on these cases and count them inside the noise band. Both are low-confidence flips (0.29 to 0.49), and they belong to the cap family (Y119) and the delivered-but-missing gap (Y344). They will settle once those buckets are fixed.

## Files read

- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2-categorize/BRIEF.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2-categorize/artifact.json
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2-categorize/history.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2-categorize/scores_train.tsv
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2-categorize/results_train.jsonl
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2-categorize/traces/ (all 240 files, Y007_rep0.json through Y400_rep1.json, parsed by script; Y007, Y013, Y027, Y039, Y050, Y054, Y061, Y063, Y083, Y084, Y114, Y119, Y124, Y133, Y138, Y169, Y179, Y192, Y194, Y282, Y318, Y338, Y343, Y344, Y346, Y385 read in detail)
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2-categorize/out/all_rows.txt (my own scratch table of all 240 rows)
- Scratch scripts I wrote and ran, in the same out/ folder: oracle.py, write_categorize.py
