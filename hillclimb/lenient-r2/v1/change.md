Make the refund limit a required second step after any rule gives refund (including rule 3's out-of-stock fallback), and say so in both the instructions and the refund/escalate action descriptions.

## Behavior

When an undelivered order is Lost (or shipped more than 14 days ago) and the item is out of stock, rule 3 falls back to "refund it". If the order total is over $500, rule 4 ("Any refund over $500 must be escalated instead of refunded.") turns that refund into escalate. Jev stops at rule 3's fallback and answers refund, mostly with high confidence (0.84 to 0.99), and the judge fails it. It never applies the refund limit to a refund that comes from a fallback.

Jev does apply the limit when the refund comes from rule 2 (damaged or wrong item, delivered 30 days ago or less). All 11 such train cases with totals over $500 (22 rows) chose escalate, and all passed. So the model can do the check. It only skips it when the refund is the second branch of rule 3. The current artifact gives no hint that a refund from any rule still has to be checked against the limit. `refund: refund the order` reads as final.

Some cases in this group also hit rule 1's reply branch (shipped 14 days ago or less but Lost: Y083, Y385). The judge still fails refund on those, so whatever the judge expects there, refund is wrong.

## Size

- 10 of 120 train cases show it: Y013, Y050, Y054, Y083, Y119, Y124, Y192, Y343, Y346, Y385. All 10 are undelivered with stock 0 and total over $500.
- 19 of 240 rows fail because of it. Y119 rep1 answered reply and passed. Every other row in the 10 cases answered refund and failed.
- That costs 19/240 = 7.9 points of train `pass`. Current train pass is 201/240 = 83.75%, and a full fix would take it to 91.7%. 7.9 points is above the ±6.5 noise floor, though not by much.
- This is the largest single failure group. The other 20 failing rows are spread across smaller, unrelated behaviors: delivered orders where the customer says the item never arrived get reship (Y194, Y338, Y344 rep1), the 14-day boundary (Y282), a wrong-item claim on an undelivered order (Y027), changed-mind returns over $500 (Y061, Y169), and judge-inconsistent refunds at exactly $500 or under (Y007 rep1, Y039, Y084, Y133).

## Evidence

Policy text, identical in every trace (from the user message `policy` field):
`3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.`
`4. Any refund over $500 must be escalated instead of refunded.`

Current system message, identical in every trace:
`"content": "Which action does the support policy call for on this ticket?\n\nActions:\n0. refund: refund the order\n1. reship: send a replacement\n2. escalate: hand the ticket to a supervisor\n3. reply: reply to the customer and take no other action"`

Failures. State lines are from the JSON user message. The last line is the assistant turn, verbatim. All are grade pass 0.

traces/Y050_rep0.json
```
 "ticket": "Hi, just checking on order #5050. No rush on the projector.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-08-29",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.99)"
```

traces/Y013_rep0.json
```
 "ticket": "Tracking for order #5013 (gaming chair) hasn't moved in a while.",
  "total": 501.0,
  "status": "Lost",
  "shipped_on": "2026-08-29",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.91)"
```

traces/Y343_rep0.json (Shipped, 34 days, not Lost)
```
 "ticket": "Why can't anyone tell me where order #5343 is? I want my projector.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-08-28",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.87)"
```

traces/Y054_rep0.json
```
 "ticket": "My projector from order #5054 never came.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-15",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.67)"
```

traces/Y124_rep0.json
```
 "ticket": "Order #5124: the projector tracking says 'exception' and nothing since.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-09-16",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.99)"
```

traces/Y192_rep0.json
```
 "ticket": "Order #5192: the gaming chair tracking says 'exception' and nothing since.",
  "total": 501.0,
  "status": "Lost",
  "shipped_on": "2026-09-16",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.87)"
```

traces/Y346_rep0.json
```
 "ticket": "Where is order #5346? I ordered the gaming chair.",
  "total": 501.0,
  "status": "Lost",
  "shipped_on": "2026-09-17",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.97)"
```

traces/Y385_rep0.json. The customer asks for a replacement, there is no stock, Jev falls back to refund, and the limit is ignored.
```
 "ticket": "Can you check on order #5385 (projector)? Ship me another one.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-09-23",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.99)"
```

traces/Y083_rep0.json. The customer even asks for escalation.
```
 "ticket": "My projector from order #5083 never came. Escalate this to a manager.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-09-26",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.87)"
```

traces/Y119_rep0.json (fail) and traces/Y119_rep1.json (pass) have the same state. Jev is split between refund and reply.
```
 "ticket": "Order #5119, the projector. Just making sure it's on the way.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-07",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.29)"      <- rep0
  "content": "reply (confidence 0.31)"       <- rep1
```

Contrast (pass). Rule 2 refunds over $500 are escalated correctly.

traces/Y081_rep0.json
```
 "ticket": "Order #5081: the gaming chair is broken. Refund me.",
  "total": 501.0,
  "status": "Delivered",
  "shipped_on": "2026-08-31",
  "delivered_on": "2026-09-04"
 "stock": 0
  "content": "escalate (confidence 0.81)"
```

traces/Y012_rep0.json
```
 "ticket": "My robot vacuum (order #5012) has a cracked housing and doesn't work.",
  "total": 549.0,
  "status": "Delivered",
  "shipped_on": "2026-08-17",
  "delivered_on": "2026-08-21"
 "stock": 2
  "content": "escalate (confidence 0.87)"
```

Contrast (pass). The same rule 3 fallback at $500 or under should stay refund, and does.

traces/Y290_rep0.json
```
 "ticket": "My bluetooth earbuds from order #5290 never came. I want a full refund.",
  "total": 79.0,
  "status": "Lost",
  "shipped_on": "2026-09-17",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 1.0)"
```

Contrast (pass). The same rule 3 over $500 with stock should stay reship.

traces/Y031_rep0.json
```
 "ticket": "Order #5031 (robot vacuum) hasn't arrived.",
  "total": 549.0,
  "status": "Lost",
  "shipped_on": "2026-09-15",
  "delivered_on": null
 "stock": 2
  "content": "reship (confidence 0.92)"
```

## The change

The change is to the `decision_instructions` and to the descriptions for `0` (refund) and `2` (escalate). The text says "the policy's refund limit" and does not hardcode $500, so it carries over if the limit changes. All three edits serve the same behavior: Jev must check every refund against the limit, including a refund that comes from a fallback.

- Instructions: a two-step procedure. Step 1 picks the rule's action, including an in-rule fallback. Step 2 runs only when that action is refund: if the total is over the limit, escalate. It says explicitly that this covers a refund that a rule gives as its fallback, and that the limit never turns reship or reply into escalate.
- `0`: refund is only for totals not over the limit.
- `2`: escalate is also the action whenever any rule would give a refund but the total is over the limit.

## Cases I expect could regress

- Refunds at $500 or under that pass now could flip to escalate if Jev over-applies the new emphasis: Y024, Y290, Y312, Y323, Y371 (rule 3 fallback), Y046, Y052, Y179, Y188, Y331, Y356, Y365, Y318 (rule 2). The exactly-$500 ones are at most risk because "over $500" sits right at their boundary: Y017, Y138, Y315, and Y225 at $499. The text keeps the comparison to "over the limit" so that $500 stays a refund. Y084 at $500 already fails with refund, so a flip to escalate there could pass or fail.
- Reships over $500 with stock that pass now could flip to escalate if Jev reads "over the limit means escalate" broadly: Y026, Y031, Y112, Y123, Y237, Y243, Y244, Y383, Y011 ($500). The sentence "it never changes a reship or a reply into escalate" is there to guard against this.
- Replies over $500 under rule 1 or rule 5 could flip to escalate: Y063, Y273, Y085, and the Processing rows over $500 (Y110, Y118, Y200, Y209, Y250, Y309, Y334, Y342, Y386). The same guard sentence covers these.
- Y119 rep1 passes now with reply. If Jev moves it to escalate, the outcome depends on the judge.

Possible side gain, not counted above: Y027 (Shipped 35 days, $501, stock 0, wrong-item claim plus a supervisor request) fails with reply. Rule 3 plus rule 4 lead to escalate, so it may recover.

## Files read

All of these are under /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v1/.

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- out/rows.json, out/table.txt (my own scratch extracts of the traces)
- out/extract.py, out/table.py, out/tracelist.txt (my own scratch scripts and list)
- All 240 trace files, parsed by a script. The files I opened individually for the quotes above are Y007_rep0, Y013_rep0, Y013_rep1, Y050_rep0, Y050_rep1, Y054_rep0, Y054_rep1, Y083_rep0, Y083_rep1, Y124_rep0, Y124_rep1, Y192_rep0, Y192_rep1, Y343_rep0, Y343_rep1, Y346_rep0, Y346_rep1, Y385_rep0, Y385_rep1, Y119_rep0, Y119_rep1, Y027_rep0, Y081_rep0, Y081_rep1, Y012_rep0, Y290_rep0, Y290_rep1, Y371_rep0, Y031_rep0, Y017_rep0. The full list:
- traces/Y007_rep0.json
- traces/Y007_rep1.json
- traces/Y011_rep0.json
- traces/Y011_rep1.json
- traces/Y012_rep0.json
- traces/Y012_rep1.json
- traces/Y013_rep0.json
- traces/Y013_rep1.json
- traces/Y016_rep0.json
- traces/Y016_rep1.json
- traces/Y017_rep0.json
- traces/Y017_rep1.json
- traces/Y024_rep0.json
- traces/Y024_rep1.json
- traces/Y025_rep0.json
- traces/Y025_rep1.json
- traces/Y026_rep0.json
- traces/Y026_rep1.json
- traces/Y027_rep0.json
- traces/Y027_rep1.json
- traces/Y028_rep0.json
- traces/Y028_rep1.json
- traces/Y030_rep0.json
- traces/Y030_rep1.json
- traces/Y031_rep0.json
- traces/Y031_rep1.json
- traces/Y033_rep0.json
- traces/Y033_rep1.json
- traces/Y039_rep0.json
- traces/Y039_rep1.json
- traces/Y046_rep0.json
- traces/Y046_rep1.json
- traces/Y050_rep0.json
- traces/Y050_rep1.json
- traces/Y052_rep0.json
- traces/Y052_rep1.json
- traces/Y054_rep0.json
- traces/Y054_rep1.json
- traces/Y055_rep0.json
- traces/Y055_rep1.json
- traces/Y061_rep0.json
- traces/Y061_rep1.json
- traces/Y063_rep0.json
- traces/Y063_rep1.json
- traces/Y064_rep0.json
- traces/Y064_rep1.json
- traces/Y068_rep0.json
- traces/Y068_rep1.json
- traces/Y076_rep0.json
- traces/Y076_rep1.json
- traces/Y080_rep0.json
- traces/Y080_rep1.json
- traces/Y081_rep0.json
- traces/Y081_rep1.json
- traces/Y082_rep0.json
- traces/Y082_rep1.json
- traces/Y083_rep0.json
- traces/Y083_rep1.json
- traces/Y084_rep0.json
- traces/Y084_rep1.json
- traces/Y085_rep0.json
- traces/Y085_rep1.json
- traces/Y088_rep0.json
- traces/Y088_rep1.json
- traces/Y089_rep0.json
- traces/Y089_rep1.json
- traces/Y110_rep0.json
- traces/Y110_rep1.json
- traces/Y112_rep0.json
- traces/Y112_rep1.json
- traces/Y114_rep0.json
- traces/Y114_rep1.json
- traces/Y116_rep0.json
- traces/Y116_rep1.json
- traces/Y118_rep0.json
- traces/Y118_rep1.json
- traces/Y119_rep0.json
- traces/Y119_rep1.json
- traces/Y121_rep0.json
- traces/Y121_rep1.json
- traces/Y123_rep0.json
- traces/Y123_rep1.json
- traces/Y124_rep0.json
- traces/Y124_rep1.json
- traces/Y131_rep0.json
- traces/Y131_rep1.json
- traces/Y133_rep0.json
- traces/Y133_rep1.json
- traces/Y138_rep0.json
- traces/Y138_rep1.json
- traces/Y144_rep0.json
- traces/Y144_rep1.json
- traces/Y148_rep0.json
- traces/Y148_rep1.json
- traces/Y149_rep0.json
- traces/Y149_rep1.json
- traces/Y161_rep0.json
- traces/Y161_rep1.json
- traces/Y162_rep0.json
- traces/Y162_rep1.json
- traces/Y166_rep0.json
- traces/Y166_rep1.json
- traces/Y169_rep0.json
- traces/Y169_rep1.json
- traces/Y179_rep0.json
- traces/Y179_rep1.json
- traces/Y180_rep0.json
- traces/Y180_rep1.json
- traces/Y188_rep0.json
- traces/Y188_rep1.json
- traces/Y190_rep0.json
- traces/Y190_rep1.json
- traces/Y192_rep0.json
- traces/Y192_rep1.json
- traces/Y193_rep0.json
- traces/Y193_rep1.json
- traces/Y194_rep0.json
- traces/Y194_rep1.json
- traces/Y200_rep0.json
- traces/Y200_rep1.json
- traces/Y206_rep0.json
- traces/Y206_rep1.json
- traces/Y209_rep0.json
- traces/Y209_rep1.json
- traces/Y212_rep0.json
- traces/Y212_rep1.json
- traces/Y214_rep0.json
- traces/Y214_rep1.json
- traces/Y215_rep0.json
- traces/Y215_rep1.json
- traces/Y222_rep0.json
- traces/Y222_rep1.json
- traces/Y225_rep0.json
- traces/Y225_rep1.json
- traces/Y231_rep0.json
- traces/Y231_rep1.json
- traces/Y232_rep0.json
- traces/Y232_rep1.json
- traces/Y237_rep0.json
- traces/Y237_rep1.json
- traces/Y240_rep0.json
- traces/Y240_rep1.json
- traces/Y243_rep0.json
- traces/Y243_rep1.json
- traces/Y244_rep0.json
- traces/Y244_rep1.json
- traces/Y247_rep0.json
- traces/Y247_rep1.json
- traces/Y250_rep0.json
- traces/Y250_rep1.json
- traces/Y251_rep0.json
- traces/Y251_rep1.json
- traces/Y252_rep0.json
- traces/Y252_rep1.json
- traces/Y255_rep0.json
- traces/Y255_rep1.json
- traces/Y258_rep0.json
- traces/Y258_rep1.json
- traces/Y263_rep0.json
- traces/Y263_rep1.json
- traces/Y265_rep0.json
- traces/Y265_rep1.json
- traces/Y266_rep0.json
- traces/Y266_rep1.json
- traces/Y270_rep0.json
- traces/Y270_rep1.json
- traces/Y273_rep0.json
- traces/Y273_rep1.json
- traces/Y277_rep0.json
- traces/Y277_rep1.json
- traces/Y282_rep0.json
- traces/Y282_rep1.json
- traces/Y290_rep0.json
- traces/Y290_rep1.json
- traces/Y292_rep0.json
- traces/Y292_rep1.json
- traces/Y293_rep0.json
- traces/Y293_rep1.json
- traces/Y303_rep0.json
- traces/Y303_rep1.json
- traces/Y304_rep0.json
- traces/Y304_rep1.json
- traces/Y309_rep0.json
- traces/Y309_rep1.json
- traces/Y312_rep0.json
- traces/Y312_rep1.json
- traces/Y315_rep0.json
- traces/Y315_rep1.json
- traces/Y318_rep0.json
- traces/Y318_rep1.json
- traces/Y323_rep0.json
- traces/Y323_rep1.json
- traces/Y327_rep0.json
- traces/Y327_rep1.json
- traces/Y331_rep0.json
- traces/Y331_rep1.json
- traces/Y333_rep0.json
- traces/Y333_rep1.json
- traces/Y334_rep0.json
- traces/Y334_rep1.json
- traces/Y338_rep0.json
- traces/Y338_rep1.json
- traces/Y342_rep0.json
- traces/Y342_rep1.json
- traces/Y343_rep0.json
- traces/Y343_rep1.json
- traces/Y344_rep0.json
- traces/Y344_rep1.json
- traces/Y346_rep0.json
- traces/Y346_rep1.json
- traces/Y354_rep0.json
- traces/Y354_rep1.json
- traces/Y356_rep0.json
- traces/Y356_rep1.json
- traces/Y358_rep0.json
- traces/Y358_rep1.json
- traces/Y360_rep0.json
- traces/Y360_rep1.json
- traces/Y362_rep0.json
- traces/Y362_rep1.json
- traces/Y364_rep0.json
- traces/Y364_rep1.json
- traces/Y365_rep0.json
- traces/Y365_rep1.json
- traces/Y371_rep0.json
- traces/Y371_rep1.json
- traces/Y380_rep0.json
- traces/Y380_rep1.json
- traces/Y383_rep0.json
- traces/Y383_rep1.json
- traces/Y385_rep0.json
- traces/Y385_rep1.json
- traces/Y386_rep0.json
- traces/Y386_rep1.json
- traces/Y389_rep0.json
- traces/Y389_rep1.json
- traces/Y396_rep0.json
- traces/Y396_rep1.json
- traces/Y400_rep0.json
- traces/Y400_rep1.json
