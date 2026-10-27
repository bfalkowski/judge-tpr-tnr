Make the $500 refund cap (policy rule 4) an explicit second step that applies to every refund, including the out-of-stock refund on never-arrived/Lost orders, and say in the refund/escalate descriptions that refund is only for totals of $500 or less.

## Behavior

Jev applies policy rule 4 ("Any refund over $500 must be escalated instead of refunded") only when the refund comes from rule 2 (damaged or wrong item). When the refund comes from rule 3 (never arrived or Lost, item out of stock), it stops at "refund" and never checks the total. Every train row where the never-arrived branch lands on refund with a total over $500 fails; every row where the damaged/wrong-item branch lands on a refund over $500 passes.

## Size

- Cases showing it: 10 of 120 train cases (Y013, Y050, Y054, Y083, Y119, Y124, Y192, Y343, Y346, Y385). All are undelivered (status Lost, or Shipped more than 14 days ago), stock 0, total $501 to $899, expected escalate.
- Rows failed: 20 of 240 (19 answered refund, 1 answered reply). Every one of the 10 cases scores 0.00.
- Cost: 20/240 = 8.3 points of `pass` (baseline 194/240 = 80.8%). A full fix is worth at most about +8.3 points, which is above the 6.5-point noise floor, but not by much. It is still the largest single failure cluster on train. The next largest are the 14-day "reply vs reship" boundary (5 cases, 10 rows, 4.2 points) and delivered-more-than-30-days damage claims refunded instead of escalated (3 cases, 6 rows, 2.5 points), both inside the noise floor on their own.

## Evidence

In each quote, the ticket/order/stock lines are lines of the user message content (the JSON state, shown decoded), and the "content" line is the assistant message as it appears in the trace file.

Failures (never-arrived branch, total over $500, out of stock, Jev refunds instead of escalating):

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y050_rep0.json
```
 "ticket": "Hi, just checking on order #5050. No rush on the projector.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-08-29",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.99)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y346_rep1.json
```
 "ticket": "Where is order #5346? I ordered the gaming chair.",
  "total": 501.0,
  "status": "Lost",
  "shipped_on": "2026-09-17",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.95)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y343_rep0.json (status Shipped, shipped 34 days ago, so rule 3 applies through the "more than 14 days" clause, not only through Lost)
```
 "ticket": "Why can't anyone tell me where order #5343 is? I want my projector.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-08-28",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.87)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y083_rep0.json (customer even asks for escalation; Jev still refunds, so it is not ignoring the escalate option, it believes refund is what the policy says)
```
 "ticket": "My projector from order #5083 never came. Escalate this to a manager.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-09-26",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.87)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y013_rep1.json
```
 "ticket": "Tracking for order #5013 (gaming chair) hasn't moved in a while.",
  "total": 501.0,
  "status": "Lost",
  "shipped_on": "2026-08-29",
 "stock": 0
  "content": "refund (confidence 0.97)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y119_rep0.json and /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y119_rep1.json (same case, split between refund and reply at low confidence)
```
 "ticket": "Order #5119, the projector. Just making sure it's on the way.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-07",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.29)"   <- (rep0)
  "content": "reply (confidence 0.31)"   <- (rep1)
```

Contrast, passing (the cap is applied when the refund comes from the damaged/wrong-item rule):

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y081_rep0.json (expected escalate, passes)
```
 "ticket": "Order #5081: the gaming chair is broken. Refund me.",
  "total": 501.0,
  "status": "Delivered",
  "shipped_on": "2026-08-31",
  "delivered_on": "2026-09-04"
 "stock": 0
  "content": "escalate (confidence 0.81)"
```

Contrast, passing (same never-arrived branch, but the total is under $500, or the item is in stock so the answer is reship):

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y290_rep0.json (expected refund, passes)
```
 "ticket": "My bluetooth earbuds from order #5290 never came. I want a full refund.",
  "total": 79.0,
  "status": "Lost",
  "shipped_on": "2026-09-17",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 1.0)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y026_rep0.json (expected reship, passes)
```
 "ticket": "Quick question, any update on order #5026? The robot vacuum hasn't shown up yet.",
  "total": 549.0,
  "status": "Lost",
  "shipped_on": "2026-09-19",
  "delivered_on": null
 "stock": 2
  "content": "reship (confidence 0.99)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/traces/Y315_rep0.json (expected refund at exactly $500.0, passes)
```
 "ticket": "Order #5315: the air purifier is broken. Refund me.",
  "total": 500.0,
  "status": "Delivered",
  "shipped_on": "2026-09-16",
  "delivered_on": "2026-09-22"
 "stock": 5
  "content": "refund (confidence 0.93)"
```

## The change

Root cause: the instructions give Jev only "Which action does the support policy call for on this ticket?", so it picks the rule that matches the ticket and stops at that rule's action. Rule 4 is a modifier on another rule's output, and Jev only connects it to the rule it sits next to semantically (damaged/wrong item, where refunds are the main outcome). The change turns rule 4 into an explicit second step that runs after any rule produces a refund, and puts the same constraint on the action descriptions so it is visible at the moment of choosing.

1. `decision_instructions`: add a two-step procedure. Step 1, find the rule and its action. Step 2, rule 4 overrides: refund with a total over $500 becomes escalate, whichever rule produced the refund, including the out-of-stock refund for a never-arrived or Lost order. State that exactly $500 is not over $500, and that rule 4 never changes a reship or a reply.
2. `criteria["0"]` (refund): add that it is only for totals of $500 or less.
3. `criteria["2"]` (escalate): add that it is also the answer whenever the policy would refund an order over $500, from either the damaged/wrong-item rule or the never-arrived out-of-stock rule.

New artifact is in out/artifact.json.

## Cases I expect could regress

The edits push toward escalate on orders over $500 and near $500, so these currently passing cases are at risk if Jev over-applies the cap:

- Reship expected on totals over $500 (cap must not touch reship): Y026, Y031, Y112, Y123, Y237, Y243, Y244. Currently high confidence (0.56 to 1.0); the "reship stays" sentence is there to protect them.
- Reply expected on totals over $500, with low current confidence: Y273 ($899, shipped 12 days, reply at 0.61/0.37), Y027 ($501, shipped 35 days, reply at 0.51/0.52), Y270 ($549, reply at 0.56/0.60). Other reply cases over $500 (Y061, Y085, Y110, Y118, Y169, Y200, Y209, Y250, Y309, Y334, Y342, Y386) are at 0.91 or higher and less likely to move.
- Refund expected at exactly $500.0, with low current confidence: Y017 (0.36/0.49) and Y084 (0.39/0.39). Y315 (0.93/0.92) is safer. The "exactly $500 is not over $500" sentence is there to protect them.

Cases not expected to change: Y138 ($500.0, delivered 33 days, expected escalate under the 30-day rule, currently refund) is a different failure (30-day counting) and this change does not target it.

## Files read

All under /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v1/

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
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
