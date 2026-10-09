# Preliminary results: p2 on dev (not held out)

Run `gh37892108418-p2-v2-dev` on the `data` branch. Paper 2's judge, verbatim, on the 51 dev tickets of v2
paired with all four actions (204 items: 51 pass, 153 fail), two calls each, real Jev (`jev-latest`),
2026-10-09. 408 calls, 0 errors, $0.011. Verdict: first call, threshold 0.5.
Reproduce: `python analysis/rates.py runs/<id>` and `python analysis/by_source.py runs/<id>`.

## Headline

| | Judge PASS | Judge FAIL |
|---|---|---|
| Correct (51) | 37 | 14 |
| Wrong (153) | 13 | 140 |

TPR 0.725 [0.608, 0.843], TNR 0.915 [0.876, 0.954], ticket-level 95% intervals. Calls disagree on 2.5% of items.

## TNR depends on where the wrong answers come from

| Wrong resolutions | Pairs | TNR |
|---|---|---|
| The paper 2 agent's own mistakes (from phase 0) | 12 | 0.167 (0.130 weighted by how often the agent made each one) |
| The other wrong actions added by the all-actions build | 141 | 0.979 |

The agent and the judge are the same model. The judge rejects wrong actions the agent would not choose and
passes the ones it does choose. All-actions items measure a TNR of 0.915 that does not hold for the failures
that occur in practice (phase 0: 0.176). A correction built on the all-actions TNR would overstate how well
the judge catches real failures.

On the 12 shared pairs the judge's verdict agrees with its phase 0 votes on 475 of 510 items.

## Threshold

| Threshold | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|---|---|---|---|
| TPR | 0.980 | 0.941 | 0.863 | 0.784 | 0.725 | 0.667 | 0.510 | 0.510 | 0.235 |
| TNR | 0.490 | 0.667 | 0.771 | 0.830 | 0.915 | 0.941 | 0.974 | 0.993 | 1.000 |

No threshold gives both above 0.9 on all-actions items. The agent's own mistakes score `noul` 0.41 to 0.82,
inside the range of correct resolutions, so moving the threshold cannot separate them.

## Consequences for the design

- The labeled set has to contain the failures the agent actually makes, not only constructed ones. v3 needs
  agent runs on its tickets, with each wrong action labeled, alongside the all-actions items.
- Report TNR separately for real and constructed failures in every table.
- A judge from a different model is no longer optional: it is the direct test of whether the blind spot
  comes from sharing a model with the agent.
