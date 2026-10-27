| round | change (one line) | test | train | decision |
|---|---|---|---|---|
| 0 | baseline | 0.838 | 0.762 | |
| 1 | Make escalate selectable outside the numbered rules: the escalate desc | 0.767 | 0.725 | revert |
| 2 | Add the missing rule for tickets that contradict the order record abou | 0.808 | 0.758 | revert |
| 3 | No change this round: no single agent behavior that artifact.json can  | | | no change proposed |

Best so far: baseline (test 0.838). Grader: paper 2's judge p2 (Jev), threshold 0.5; test TPR 0.792, TNR 0.532

Stall categorization: {"artifact_gap": 0, "grader_disagreement": 34, "harness": 0, "structural": 22, "variance": 1}

Stopped: the analyzer proposed no change.
