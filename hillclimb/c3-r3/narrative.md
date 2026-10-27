| round | change (one line) | test | train | decision |
|---|---|---|---|---|
| 0 | baseline | 0.771 | 0.779 | |
| 1 | Make the $500 refund cap (rule 4) explicitly cover the out-of-stock re | 0.787 | 0.854 | keep |
| 2 | Replace the decision instructions with a status-first decision table ( | 0.829 | 0.942 | keep |

Best so far: v2 (test 0.829). Grader: the frozen judge c3 (Claude Haiku 4.5), threshold 0.5; test TPR 0.927, TNR 0.919

Stall categorization: {"artifact_gap": 0, "grader_disagreement": 4, "harness": 0, "structural": 6, "variance": 4}
