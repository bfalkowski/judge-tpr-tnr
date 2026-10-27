| round | change (one line) | test | train | decision |
|---|---|---|---|---|
| 0 | baseline | 0.892 | 0.838 | |
| 1 | Make the over-limit refund rule apply to every refund, including the o | 0.850 | 0.808 | revert |
| 2 | Rewrite the refund and escalate descriptions as complete condition lis | 0.846 | 0.833 | revert |
| 3 | No change proposed: the only behavior big enough to clear the noise fl | | | no change proposed |

Best so far: baseline (test 0.892). Grader: the step 2 judge j2 (Jev), threshold 0.3; test TPR 1.000, TNR 0.645

Stall categorization: {"artifact_gap": 9, "grader_disagreement": 7, "harness": 0, "structural": 23, "variance": 0}

Stopped: the analyzer proposed no change.
