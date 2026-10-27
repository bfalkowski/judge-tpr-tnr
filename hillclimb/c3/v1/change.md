Make the $500 refund cap a step that applies to every refund, including never-arrived/out-of-stock refunds, in both decision_instructions and the refund/escalate descriptions.

## Behavior

Jev applies policy rule 4 ("Any refund over $500 must be escalated instead of refunded") only when the refund comes from rule 2 (damaged or wrong item, delivered). When the refund comes from rule 3 (never arrived or Lost, item out of stock), Jev stops at "refund" and never checks the order total. It does this with high confidence (0.76 to 0.99) and the same way on both reps.

The current artifact never mentions the cap, so the refund description ("refund the order") and the escalate description ("hand the ticket to a supervisor") give Jev nothing to link a rule-3 refund to escalation.

## How many cases, and how much `pass` it costs

- 9 train cases, all at 0.00 on both reps: Y013, Y050, Y054, Y083, Y124, Y192, Y343, Y346, Y385.
- That is 18 of 240 train rows, so 7.5 points of `pass`. All 18 rows picked refund. In every one the judge says the policy result is refund but the total is over $500, so it must be escalate.
- This is the largest single failure cluster: 18 of the 53 failing rows. The next largest is the 14-day shipped-window miscount in both directions (Y114, Y258, Y282, Y304 reship too early; Y063, Y089, Y144, Y396 reply too late). That cluster is date arithmetic rather than one missing rule.
- A full fix gains at most 7.5 points. That is above the ±6.5 noise floor, but not by much. If the fix only lands on part of the cluster, the gain will fall inside the noise.

Contrast: on the rule-2 path Jev already applies the cap correctly. Y081, Y206, Y025, Y116, Y131, Y166, Y251, Y255, Y265 and Y292 are all at 1.00 with escalate. So the knowledge is there, and only the rule-3 path skips it. On rule-3 refunds under $500 (Y024, Y290, Y312, Y323, Y371) Jev refunds correctly.

## Evidence (verbatim from trace files)

Policy text as sent, `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y050_rep0.json`:
```
3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.\\n4. Any refund over $500 must be escalated instead of refunded.
```

Failing: rule-3 refund over $500, Jev refunds.

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y050_rep0.json`
```
\"ticket\": \"Hi, just checking on order #5050. No rush on the projector.\"
\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-08-29\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.99)"
```
Judge: "Stock is 0, so refund is correct. However, the total is $899.0, which exceeds the $500 limit for refunds, so the policy requires escalation instead."

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y013_rep1.json`
```
\"ticket\": \"Tracking for order #5013 (gaming chair) hasn't moved in a while.\"
\"total\": 501.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-08-29\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.97)"
```

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y343_rep0.json` (status Shipped, not Lost, so the behavior covers both rule-3 triggers)
```
\"ticket\": \"Why can't anyone tell me where order #5343 is? I want my projector.\"
\"total\": 899.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-08-28\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.87)"
```

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y054_rep1.json`
```
\"ticket\": \"My projector from order #5054 never came.\"
\"total\": 899.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-15\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.76)"
```

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y346_rep1.json`
```
\"ticket\": \"Where is order #5346? I ordered the gaming chair.\"
\"total\": 501.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-17\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.95)"
```

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y083_rep0.json` (customer even asks for escalation; Jev still refunds)
```
\"ticket\": \"My projector from order #5083 never came. Escalate this to a manager.\"
\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-26\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.87)"
```

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y124_rep0.json`, `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y192_rep0.json`, `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y385_rep0.json`
```
\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-16\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.99)"

\"total\": 501.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-16\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.87)"

\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-23\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.99)"
```

Passing contrast: rule-2 refund over $500, Jev escalates.

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y081_rep0.json`
```
\"ticket\": \"Order #5081: the gaming chair is broken. Refund me.\"
\"total\": 501.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-31\",\n  \"delivered_on\": \"2026-09-04\"\n },\n \"stock\": 0
"content": "escalate (confidence 0.81)"
```

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y206_rep0.json`
```
\"ticket\": \"I received the wrong item on order #5206. It is not the home theater soundbar I ordered. I want a full refund.\"
\"total\": 649.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-09-05\",\n  \"delivered_on\": \"2026-09-09\"\n },\n \"stock\": 6
"content": "escalate (confidence 0.89)"
```

Passing contrast: rule-3 over $500 but in stock, so reship (the cap must not touch it).

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y383_rep0.json`
```
\"ticket\": \"Order #5383 (home theater soundbar) hasn't arrived.\"
\"total\": 649.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-08-28\",\n  \"delivered_on\": null\n },\n \"stock\": 6
"content": "reship (confidence 1.0)"
```
Judge: "Since a reship is not affected by the $500 limit (rule 4 specifies the limit applies to refunds only), reship is the correct action."

Passing contrast: rule-3 refund under $500, so refund stays correct.

`/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/Y312_rep0.json`
```
\"total\": 79.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-15\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.99)"
```

## The change

The cap becomes a check that runs after the matching rule. It is stated once in `decision_instructions` and tied to the two actions it moves between, so Jev sees it when it weighs refund. The scope is named in general terms (which rules can produce a refund) with no products, amounts or ticket wording from train. It also says outright that the cap never moves reship or reply, to protect the in-stock over-$500 reship cases. "Over the limit" follows the policy's wording, so exactly $500 stays a refund.

- `decision_instructions`: "Which action does the support policy call for on this ticket? If the matching rule gives refund, compare the order total with the policy's refund limit: a refund over the limit becomes escalate, whichever rule produced it (damaged or wrong item, or never arrived and out of stock). The limit applies only to refunds. It never turns reship or reply into escalate."
- `criteria["0"]`: "refund: refund the order. Not when the order total is over the policy's refund limit; that refund is escalated instead"
- `criteria["2"]`: "escalate: hand the ticket to a supervisor. This is also the action when a policy rule gives a refund but the order total is over the policy's refund limit, including never-arrived orders that are out of stock"
- `criteria["1"]` and `criteria["3"]` are unchanged.

## Cases expected to regress

- Y119 (now 0.50): rule-3, $899, out of stock. Jev refunded on rep0 and the judge passed it ("The item is out of stock (0 units), so the required action is refund."), so the judge skipped rule 4 on this case. If Jev now escalates, which is the policy-correct action, this judge may fail it. That costs 1 row.
- Over-$500 reship cases at 1.00 (Y026, Y031, Y112, Y123, Y237, Y243, Y244, Y383, plus Y011, Y016, Y162, Y252, Y389 at exactly $500): these are at risk if Jev reads the new text as "large total means escalate". The explicit "never turns reship or reply into escalate" clause is there to prevent that.
- Exactly-$500 refunds at 1.00 (Y084, Y315): at risk if Jev treats $500 as over the limit. The judge passes refund at exactly $500 on these two.
- Not expected to change: Y017 ($500 wrong item, refund, judge wants escalate). The judge reads "$500 equals the limit" as over, which conflicts with Y084/Y315. That is judge noise and this change does not chase it.

## Files read

- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/BRIEF.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/artifact.json
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/history.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/scores_train.tsv
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/results_train.jsonl
- All 240 files in /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3/v1/traces/ (Y007_rep0.json through Y400_rep1.json), parsed by script to tabulate action, order fields and stock. Individually inspected: Y013_rep0, Y013_rep1, Y050_rep0, Y050_rep1, Y054_rep1, Y083_rep0, Y124_rep0, Y192_rep0, Y343_rep0, Y343_rep1, Y346_rep1, Y385_rep0, Y027_rep0, Y119_rep0, Y119_rep1, Y081_rep0, Y025_rep0, Y206_rep0, Y026_rep0, Y112_rep0, Y383_rep0, Y312_rep0, Y323_rep0, Y371_rep0, Y084_rep0, Y315_rep0, Y110_rep0, Y273_rep0
