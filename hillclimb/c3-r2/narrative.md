| round | change (one line) | test | train | decision |
|---|---|---|---|---|
| 0 | baseline | 0.771 | 0.779 | |
| 1 | Make the rule 4 refund-limit check an explicit last step for every ref | 0.792 | 0.854 | keep |

Best so far: v1 (test 0.792). Grader: the frozen judge c3 (Claude Haiku 4.5), threshold 0.5; test TPR 0.927, TNR 0.919
