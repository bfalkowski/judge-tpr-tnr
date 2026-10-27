| round | change (one line) | test | train | decision |
|---|---|---|---|---|
| 0 | baseline | 0.892 | 0.838 | |
| 1 | Make the refund limit (policy rule 4) gate every refund, including the | 0.846 | 0.821 | revert |
| 2 | Put the composed "rule 3 out-of-stock refund + rule 4 over-$500 limit  | 0.863 | 0.838 | revert |

Best so far: baseline (test 0.892). Grader: the step 2 judge j2 (Jev), threshold 0.3; test TPR 1.000, TNR 0.645

Stall categorization: {"artifact_gap": 12, "grader_disagreement": 7, "harness": 0, "structural": 19, "variance": 1}
