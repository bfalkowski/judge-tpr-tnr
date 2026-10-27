| round | change (one line) | test | train | decision |
|---|---|---|---|---|
| 0 | baseline | 0.892 | 0.838 | |
| 1 | Make the over-limit refund rule apply to every refund, including the o | 0.850 | 0.808 | revert |
| 2 | Rewrite the refund and escalate descriptions as complete condition lis | 0.846 | 0.833 | revert |

Best so far: baseline (test 0.892). Grader: the step 2 judge j2 (Jev), threshold 0.3; test TPR 1.000, TNR 0.645
