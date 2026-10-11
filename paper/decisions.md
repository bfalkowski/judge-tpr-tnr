# Decisions made before the test run

Recorded 2026-10-11, before the frozen judge was run on the test split.

1. **Frozen judge.** c3 (Claude Haiku 4.5, `claude-haiku-4-5-20251001`, step 3 of the climb), threshold 0.5,
   fingerprint `1b1bebcddff9f66c`, chosen on dev run `gh38104945965-c3-labeled-dev`
   (dev TPR 0.954, TNR 0.972). Climbing stopped because both rates passed the 0.9 target; the remaining
   dev errors were 2 items each of three kinds, too few to tune on without fitting dev.

2. **Labels are not changed.** On dev, the judge disagreed with the answer key on items where a customer
   reports damage on an order the record shows as shipped but not delivered. The reference policy
   returns reply (rule 2 covers delivered orders only; no rule covers this case). The judge, told to trust
   the order record, applied rule 3 (not delivered more than 14 days after shipping: reship or refund).
   The policy text does not settle it. The reference was fixed before any judge was built and is the
   same function paper 2 used, so it is kept. Changing it after reading the judge's disagreements would
   move the answer key toward the judge.

   Reported instead: test TPR and TNR with all items, and with the damaged-or-wrong-item, not-delivered,
   Shipped items set aside (4 on dev, 12 on test).

3. **Correction runs.** The pass-rate correction is evaluated on a new ticket batch (v4) that is in no
   split and that no judge version has seen, with TPR and TNR taken from the test run.
