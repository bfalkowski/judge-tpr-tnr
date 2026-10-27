| round | change (one line) | test | train | decision |
|---|---|---|---|---|
| 0 | baseline | 0.771 | 0.779 | |
| 1 | Make the rule 4 refund-limit check an explicit last step for every ref | 0.792 | 0.854 | keep |
| 2 | Make the order record (status, shipped_on, delivered_on, stock), not t | 0.867 | 0.929 | keep |
| 3 | No change proposed: the top failure behavior (Jev misjudging whether s | | | no change proposed |

Best so far: v2 (test 0.867). Grader: the frozen judge c3 (Claude Haiku 4.5), threshold 0.5; test TPR 0.927, TNR 0.919

Stopped: the analyzer proposed no change.
