| round | change (one line) | test | train | decision |
|---|---|---|---|---|
| 0 | baseline | 0.771 | 0.779 | |
| 1 | Make the $500 refund cap a step that applies to every refund, includin | 0.800 | 0.854 | keep |
| 2 | Make rule selection record-first: compute today-minus-14 and today-min | 0.775 | 0.875 | revert |
| 3 | Pick the order's delivery state (not yet due / never arrived / deliver | 0.817 | 0.900 | keep |

Best so far: v3 (test 0.817). Grader: the frozen judge c3 (Claude Haiku 4.5), threshold 0.5; test TPR 0.927, TNR 0.919

Stall categorization: {"artifact_gap": 16, "grader_disagreement": 6, "harness": 0, "structural": 12, "variance": 1}

Stopped: three rounds without a rise of 0.065 in the best test score.
