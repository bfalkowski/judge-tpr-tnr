Make the over-limit refund rule apply to every refund, including the out-of-stock fallback refund, by telling Jev to check each refund against the order-total limit and choose escalate when the total is over it (instructions plus the refund and escalate descriptions).

## Behavior

When a never-arrived or lost order is out of stock, the policy's fallback is refund (rule 3). If the order total is over $500, rule 4 should turn that refund into escalate. Jev stops at rule 3 and answers `refund`, often with high confidence. It does apply rule 4 when refund is the main action of the damaged/wrong-item rule (rule 2), so the problem is specific to a refund reached through a fallback branch: the override is never checked there.

Relevant policy lines (the same in every trace), quoted from `traces/Y013_rep0.json`:

> 3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.
> 4. Any refund over $500 must be escalated instead of refunded.

## Size and cost

- Train baseline: 201/240 rows pass (83.75).
- 10 of 120 train cases show the behavior: Y013, Y050, Y054, Y083, Y119, Y124, Y192, Y343, Y346, Y385. Every one is not delivered, has stock 0, and has a total over $500 ($501 or $899).
- They fail 19 of their 20 rows. All 19 failures are `refund`. The one passing row is Y119 rep1, which answered `reply` with confidence 0.31.
- Cost: 19/240 = 7.9 points of train `pass`. That is the most a full fix can gain.
- Across the whole train set, Jev chose `refund` on a non-delivered order over $500 in exactly these 19 rows. It never chose `escalate` on such an order.
- Noise floor: 7.9 points is above the ±6.5 floor, but not by much. The change clears it only if it fixes nearly all of the cluster without regressions, so it is worth trying with that caveat.

The other failures don't share one cause, and each group is smaller than this one:
- Y061 and Y169: change-of-mind tickets answered `reply`, 4 rows.
- Y007 and Y039: in-window damage where the customer asks for escalation, 3 rows.
- Y027, Y084, Y133, Y194, Y282, Y338 and Y344: 1 or 2 rows each, mixed causes.

## Evidence (failing cluster)

`traces/Y013_rep0.json`
```
 "ticket": "Tracking for order #5013 (gaming chair) hasn't moved in a while.",
  "total": 501.0,
  "status": "Lost",
  "shipped_on": "2026-08-29",
  "delivered_on": null
 "stock": 0
ASSISTANT: refund (confidence 0.91)
```

`traces/Y050_rep0.json`
```
 "ticket": "Hi, just checking on order #5050. No rush on the projector.",
  "total": 899.0,
  "status": "Lost",
 "stock": 0
ASSISTANT: refund (confidence 0.99)
```

`traces/Y054_rep1.json` (status Shipped, shipped 16 days ago, so rule 3 applies through the "more than 14 days" branch)
```
 "ticket": "My projector from order #5054 never came.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-15",
  "delivered_on": null
 "stock": 0
ASSISTANT: refund (confidence 0.76)
```

`traces/Y083_rep0.json` (the customer even asks for escalation)
```
 "ticket": "My projector from order #5083 never came. Escalate this to a manager.",
  "total": 899.0,
  "status": "Lost",
 "stock": 0
ASSISTANT: refund (confidence 0.87)
```

`traces/Y124_rep0.json`
```
 "ticket": "Order #5124: the projector tracking says 'exception' and nothing since.",
  "total": 899.0,
  "status": "Lost",
 "stock": 0
ASSISTANT: refund (confidence 0.99)
```

`traces/Y192_rep1.json`
```
 "ticket": "Order #5192: the gaming chair tracking says 'exception' and nothing since.",
  "total": 501.0,
  "status": "Lost",
 "stock": 0
ASSISTANT: refund (confidence 0.96)
```

`traces/Y343_rep0.json`
```
 "ticket": "Why can't anyone tell me where order #5343 is? I want my projector.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-08-28",
  "delivered_on": null
 "stock": 0
ASSISTANT: refund (confidence 0.87)
```

`traces/Y346_rep0.json`
```
 "ticket": "Where is order #5346? I ordered the gaming chair.",
  "total": 501.0,
  "status": "Lost",
 "stock": 0
ASSISTANT: refund (confidence 0.97)
```

`traces/Y385_rep0.json`
```
 "ticket": "Can you check on order #5385 (projector)? Ship me another one.",
  "total": 899.0,
  "status": "Lost",
 "stock": 0
ASSISTANT: refund (confidence 0.99)
```

`traces/Y119_rep0.json` (fails) and `traces/Y119_rep1.json` (passes with a low-confidence `reply`)
```
 "ticket": "Order #5119, the projector. Just making sure it's on the way.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-07",
 "stock": 0
ASSISTANT: refund (confidence 0.29)      [rep0]
ASSISTANT: reply (confidence 0.31)       [rep1]
```

## Contrast (passing)

Jev applies rule 4 when refund is rule 2's main action. All of these are delivered within 30 days, over $500, and answered `escalate`:

`traces/Y025_rep0.json`
```
 "ticket": "I received the wrong item on order #5025. It is not the gaming chair I ordered.",
  "total": 501.0,
  "status": "Delivered",
  "delivered_on": "2026-09-01"
ASSISTANT: escalate (confidence 0.88)
```

`traces/Y081_rep0.json`
```
 "ticket": "Order #5081: the gaming chair is broken. Refund me.",
  "total": 501.0,
  "delivered_on": "2026-09-04"
ASSISTANT: escalate (confidence 0.81)
```

`traces/Y131_rep0.json`
```
 "ticket": "My home theater soundbar (order #5131) has a cracked housing and doesn't work. Just send a new one.",
  "total": 649.0,
  "delivered_on": "2026-09-01"
ASSISTANT: escalate (confidence 0.81)
```

Fallback refunds under the limit are correct today, and the change must keep them:

`traces/Y290_rep0.json`
```
 "ticket": "My bluetooth earbuds from order #5290 never came. I want a full refund.",
  "total": 79.0,
  "status": "Lost",
 "stock": 0
ASSISTANT: refund (confidence 1.0)
```

`traces/Y371_rep0.json`
```
 "ticket": "Order #5371 (ergonomic keyboard) hasn't arrived.",
  "total": 159.0,
  "status": "Shipped",
  "shipped_on": "2026-09-15",
 "stock": 0
ASSISTANT: refund (confidence 0.73)
```

Over-limit orders with stock are reshipped, which is correct because rule 4 only touches refunds:

`traces/Y383_rep0.json`
```
 "ticket": "Order #5383 (home theater soundbar) hasn't arrived.",
  "total": 649.0,
  "status": "Lost",
 "stock": 6
ASSISTANT: reship (confidence 1.0)
```

## The change

All three edits serve one behavior: applying the refund limit to every refund.

- `decision_instructions`: keep the question. Add an explicit check after the matching rule is found: compare any resulting refund against the policy's limit on refunds by order total, including a refund given only as an out-of-stock fallback, and choose escalate when the total is over the limit. The new text also scopes the check so it does not over-fire: it changes only refunds, never reships or replies, and a total equal to the limit is not over it.
- `criteria["0"]` (refund): add "only when the order total is within the policy's refund limit".
- `criteria["2"]` (escalate): add that escalate is also the action for any refund whose total is over the limit.

The current artifact gives no instruction beyond the question and bare action labels. Nothing in it tells Jev to check an override after the first matching rule. This change adds that missing step instead of rewording an existing line.

## Cases I expect could regress

- **Y273**: Shipped 12 days ago, $899, stock 0. The correct answer is `reply` by rule 1, and Jev currently answers it with low confidence (`traces/Y273_rep0.json` reply 0.61, `traces/Y273_rep1.json` reply 0.37). The stronger link between escalate and totals over the limit could pull it to `escalate`. This is the most likely regression.
- **Over-limit reship cases with stock**: Y026, Y031, Y112, Y123, Y237, Y243, Y244, Y383. Jev could over-apply the limit to non-refund actions. Y244 is the weakest (reship 0.56 and 0.64). The "never reships or replies" clause targets this risk.
- **Refunds at exactly $500**: Y017 (refund 0.36/0.49), Y315 and Y138 could flip to escalate if Jev reads "limit" as inclusive. The "exactly equal is not over" clause targets this.
- **Fallback refunds under the limit**: Y024, Y290, Y312, Y323, Y371. Low risk, but they would regress if Jev escalates every out-of-stock fallback.
- **Over-limit replies on Processing orders**: Y110, Y118, Y386, Y200, Y209, Y309, Y342. Low risk, since they currently answer at 0.9 to 1.0 confidence.

Possible gain outside the cluster: Y027 ($501, Shipped 35 days ago, not delivered, stock 0, currently `reply`, failing both reps) may move to `escalate` if Jev routes it through rule 3. I did not count it.

## Files read

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- out/an.py, out/an2.py, out/table.txt, out/traces_read.txt (my scratch files)
- All 240 trace files under traces/. I parsed every one programmatically and printed some lines directly:
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
