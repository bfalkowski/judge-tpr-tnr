| round | change (one line) | test | train | decision |
|---|---|---|---|---|
| 0 | baseline | 0.792 | 0.808 | |
| 1 | Make the $500 refund cap (policy rule 4) an explicit second step that  | 0.817 | 0.879 | keep |
| 2 | Make the record decide the branch: compare shipped_on/delivered_on to  | 0.879 | 0.929 | keep |
| 3 | Replace every "N days ago" condition in the instructions and all four  | 0.975 | 1.000 | keep |

Best so far: v3 (test 0.975). Grader: the answer key (judge/policy.py), as a programmatic check

Stall categorization: {"artifact_gap": 0, "grader_disagreement": 0, "harness": 0, "structural": 12, "variance": 5}
