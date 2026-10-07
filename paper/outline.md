# Paper outline (working)

Working title: **Is This Judge Valid? Measuring and Correcting an LLM Judge Against Labels It Has Not Seen**

Status: phase 0 done from existing data. Nothing below has been run on the real API yet.

## Research questions

1. **RQ1.** What are the paper 2 judge's TPR and TNR on held-out tickets, and how much of its error does the two-call repeat check catch?
2. **RQ2.** Tuned on dev only (rule-by-rule criteria, few-shot examples from train, threshold on the raw `noul` score), does a judge reach TPR and TNR above 90% on the test split?
3. **RQ3.** Does the corrected pass rate, and its interval, contain the true pass rate across agent runs whose true rates differ?
4. **RQ4.** How many labeled tickets does the correction need before its interval is narrow enough to use?

## Sections and what each needs

| Section | Needs | Status |
|---|---|---|
| 1. Problem: a consistent judge can be consistently wrong | Paper 2 Section 6.9; phase 0 | Have it |
| 2. Related work: the course method, Rogan and Gladen style correction, judge consistency (Haldar and Hockenmaier; Ding), juries (Verga et al.) | Reading | Not started |
| 3. Phase 0: the paper 2 judge, measured | `phase0/RESULTS.md` | Done |
| 4. Setup: judge items, labels, splits, freeze | `data/build.py`, split, freeze | Built for v2; v3 not written |
| 5. RQ1: p2 on dev, then on test | p2 dev run; p2 test run after v3 and a freeze of p2 | Not run |
| 6. RQ2: tuning on dev | New variants in `judge/judges.py`, dev runs, threshold sweep | Not started |
| 7. RQ3: correcting agent runs | Agent runs with known truth at several true pass rates; the frozen judge run on each run's (ticket, action) pairs | Needs a way to judge agent-run items (see below) |
| 8. RQ4: labeled set size | Subsample the test tickets; interval width and coverage against size | Analysis only, after RQ1 |
| 9. Hand audit of the reference | Disagreement tickets reviewed by hand; any reference errors reported | Not started |
| 10. Limitations | | |

## Open decisions

- **v3 tickets.** About 50 new tickets under the same policy, written before any judge sees them, and committed (with checksums) before the first test run. Same difficulty tags as v2 so results can be compared by tag.
- **Agent runs for RQ3.** Paper 2's agent can produce runs at different true pass rates with configs it already has: clean, the declared control (stock removed), and the edited decision instructions. Each run's (ticket, action) pairs then go through the frozen judge. This repo needs a small adapter that turns an agent run's `items.jsonl` into judge items. The run's tickets must not overlap the labeled test set.
- **Second judge model.** Whether to add a judge from another model family, to see if the low TNR belongs to Jev or to the prompt. Optional.
- **Which call counts.** Paper 2 used the first of two calls. Keep that for comparability; report the second call and the repeat check alongside.

## Results already in hand (phase 0)

- TPR 0.873, TNR 0.176 on 600 items; TPR + TNR - 1 = 0.050.
- 66 distinct ticket/action pairs; 13 tickets ever wrong; judge errors on 19 tickets, 11 of them in every run.
- Correction on held-out halves: undefined in 33.5% of 2,000 splits; where defined, median error 19.3 points against 4.7 for the raw rate.
- 95% interval for one run, 128 of 200 splits where the correction is defined: ticket-level bootstrap covers 96% but is about 100 points wide; judgy's item-level interval covers 44%.
