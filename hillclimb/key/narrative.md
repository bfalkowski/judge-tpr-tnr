| round | change (one line) | test | train | decision |
|---|---|---|---|---|
| 0 | baseline | 0.792 | 0.808 | |
| 1 | Make the $500 refund cap (policy rule 4) an explicit second step that  | 0.817 | 0.879 | keep |
| 2 | Make the record decide the branch: compare shipped_on/delivered_on to  | 0.879 | 0.929 | keep |

Best so far: v2 (test 0.879). Grader: the answer key (judge/policy.py), as a programmatic check
