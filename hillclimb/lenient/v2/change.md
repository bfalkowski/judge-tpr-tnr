Put the composed "rule 3 out-of-stock refund + rule 4 over-$500 limit = escalate" condition into the escalate and refund action descriptions in state-field terms, add "total does not matter" guards to reply and reship, and leave decision_instructions unchanged.

## Behavior

When an order is missing (status Lost, or Shipped more than 14 days ago with no delivery date) and stock is 0, policy rule 3 says refund. Rule 4 then says any refund over $500 must be escalated. Jev stops at rule 3 and picks refund even when the total is over $500, often at 0.9 or higher confidence. It does apply rule 4 to rule-2 (damaged or wrong item) refunds: every over-$500 rule-2 refund on train is escalated and passes (for example Y025, Y081, Y076, Y088, Y131, Y166, Y180). It never makes that link for the rule-3 fallback, probably because rule 3's text never mentions escalation, so the model has to chain two rules and doesn't.

## Size

All 16 train cases that reach the rule-3 out-of-stock fallback:
- total $500 or less (Y024, Y290, Y312, Y323, Y371): refund, all pass 2/2.
- total over $500: 9 cases at 0/2 (Y013, Y050, Y054, Y083, Y124, Y192, Y343, Y346, Y385) and Y119 at 1/2 (rep0 refund failed, rep1 reply passed under the lenient judge). In every failing rep except Y119 rep1 the action was refund.

Cost: 19 of 240 train rows, which is 9.5 of 120 case-means, or about 7.9 points of `pass` (baseline 0.8375). That is the ceiling for this fix. One more case, Y027 (Shipped 35 days, $501, stock 0, wrong-item claim, 0/2 with `reply`), reaches the same composed condition through a different wrong action. If the new escalate description catches it too, the ceiling rises to about 8.75 points.

The ceiling clears the ±6.5 noise floor only by about 1.4 to 2.3 points. A partial fix (6 or 7 of the 9.5 cases) would land inside the noise. This is the only failure cluster on train big enough to clear the floor. The rest are smaller and mostly look like judge variance: reship on Delivered or ≤14-day orders (Y194, Y338, Y282, half of Y344, about 2.9 points), changed-mind replies failing (Y061, Y169), and $500 or ≤30-day damaged items graded inconsistently (Y084, Y007, Y039).

## Why this lever and not v1's

v1 went after the same behavior. It added an instruction to "look for an overriding rule after reaching an outcome" and described refund and escalate in abstract terms ("totals within the limit", "over-limit refunds"). It recovered only Y385 among the over-limit fallback cases. Y013, Y050, Y054, Y083, Y124, Y192, Y343 and Y346 stayed at 0.00 in v1. It also regressed reply cases: Y030 1.00 to 0.00, Y273 1.00 to 0.00, Y327 1.00 to 0.50, Y362 1.00 to 0.50, Y344 0.50 to 0.00, and Y119 0.50 to 0.00. Most of those are low-value reply cases (Y030 $249, Y362 $189, Y327 $500) that no refund limit should touch. That points to the general "look for an override" instruction pushing the model off `reply`, not to the limit itself.

This change:
1. Leaves decision_instructions exactly as baseline, which removes v1's source of reply regressions.
2. Puts the composed condition into the escalate description in terms of the state fields Jev actually sees (status Lost or shipped more than 14 days ago with no delivery date, stock 0, total over $500), so the model can match the state to escalate directly instead of chaining rule 3 into rule 4.
3. Gives the refund description the concrete threshold ($500 or less, exactly $500 still refunded) in place of v1's "within the limit".
4. Adds "the order total does not matter" to reply and reship, so the over-$500 wording doesn't spread to over-$500 reply cases (the Y273 pattern) or over-$500 in-stock reships.

$500 is policy rule 4's own threshold, not content from a train case. The policy is fixed across splits.

## Evidence

Over-limit fallback, picked refund, failed:

`traces/Y050_rep0.json` (grade pass 0)
```
 "ticket": "Hi, just checking on order #5050. No rush on the projector.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-08-29",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 0.99)
```

`traces/Y124_rep0.json` (grade pass 0)
```
 "ticket": "Order #5124: the projector tracking says 'exception' and nothing since.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-09-16",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 0.99)
```

`traces/Y013_rep1.json` (grade pass 0)
```
 "ticket": "Tracking for order #5013 (gaming chair) hasn't moved in a while.",
  "total": 501.0,
  "status": "Lost",
  "shipped_on": "2026-08-29",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 0.97)
```

`traces/Y346_rep0.json` (grade pass 0)
```
 "ticket": "Where is order #5346? I ordered the gaming chair.",
  "total": 501.0,
  "status": "Lost",
  "shipped_on": "2026-09-17",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 0.97)
```

`traces/Y054_rep0.json` (grade pass 0). Status Shipped, 16 days ago, not delivered:
```
 "ticket": "My projector from order #5054 never came.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-15",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 0.67)
```

`traces/Y343_rep0.json` (grade pass 0)
```
 "ticket": "Why can't anyone tell me where order #5343 is? I want my projector.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-08-28",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 0.87)
```

`traces/Y083_rep0.json` (grade pass 0). Lost, shipped 5 days ago, and the customer asks for escalation, but the model still refunds:
```
 "ticket": "My projector from order #5083 never came. Escalate this to a manager.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-09-26",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 0.87)
```

`traces/Y385_rep1.json` (grade pass 0)
```
 "ticket": "Can you check on order #5385 (projector)? Ship me another one.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-09-23",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 0.99)
```

`traces/Y192_rep0.json` (grade pass 0)
```
 "ticket": "Order #5192: the gaming chair tracking says 'exception' and nothing since.",
  "total": 501.0,
  "status": "Lost",
  "shipped_on": "2026-09-16",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 0.87)
```

`traces/Y119_rep0.json` (grade pass 0) and `traces/Y119_rep1.json` (grade pass 1):
```
 "ticket": "Order #5119, the projector. Just making sure it's on the way.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-07",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 0.29)      <- rep0
assistant: reply (confidence 0.31)       <- rep1
```

Contrast: the same fallback at $500 or less is refunded and passes. `traces/Y290_rep0.json` (grade pass 1):
```
 "ticket": "My bluetooth earbuds from order #5290 never came. I want a full refund.",
  "total": 79.0,
  "status": "Lost",
  "shipped_on": "2026-09-17",
  "delivered_on": null
 "stock": 0
assistant: refund (confidence 1.0)
```

Contrast: an over-$500 rule-2 refund is escalated and passes, so the model knows rule 4 and only misses it on the rule-3 path. `traces/Y081_rep0.json` (grade pass 1):
```
 "ticket": "Order #5081: the gaming chair is broken. Refund me.",
  "total": 501.0,
  "status": "Delivered",
  "shipped_on": "2026-08-31",
  "delivered_on": "2026-09-04"
 "stock": 0
assistant: escalate (confidence 0.81)
```

Contrast: an over-$500 missing order that is in stock is reshipped and passes. The reship guard is there to keep these. `traces/Y026_rep0.json` (grade pass 1):
```
 "ticket": "Quick question, any update on order #5026? The robot vacuum hasn't shown up yet.",
  "total": 549.0,
  "status": "Lost",
  "shipped_on": "2026-09-19",
  "delivered_on": null
 "stock": 2
assistant: reship (confidence 0.99)
```

Possible extra gain, same composed condition reached through a different wrong action. `traces/Y027_rep0.json` (grade pass 0):
```
 "ticket": "I received the wrong item on order #5027. It is not the gaming chair I ordered. Get a supervisor on this.",
  "total": 501.0,
  "status": "Shipped",
  "shipped_on": "2026-08-27",
  "delivered_on": null
 "stock": 0
assistant: reply (confidence 0.51)
```

## Expected regressions

The change adds wording to all four descriptions and removes nothing that the baseline relies on. These cases are at risk:
- **Y273** (Shipped 12 days, $899, stock 0, `reply` at 0.61 and 0.37). This is the closest lookalike: undelivered, out of stock, over $500, but not yet past 14 days. v1 took it to 0.00. The escalate description only names "Lost" or "shipped more than 14 days", and reply now says the total does not matter, but this is still the most likely casualty. Y270 and Y063 ($549, Shipped 14 and 15 days, `reply` passing) carry the same risk.
- **Y112** (Lost, $649, stock 6, customer demands escalation, `reship` passing). The new over-$500 wording in escalate plus the customer's demand could pull it off reship. The reship guard is aimed at it. Y026, Y031, Y237, Y243, Y383 and Y123/Y244 (over-$500 in-stock reships) carry a smaller version of the same risk.
- **Y017, Y315, Y138** (exactly $500, `refund` passing). These could flip to escalate if the model reads $500 as over the limit. The refund description says exactly $500 is still refunded.
- **Y119 rep1** currently passes with `reply`. If it moves to `escalate` it should still pass, since escalate is the policy answer.

If Y273 and Y112 both regress fully, that is 2 points against a 7.9 to 8.75 point ceiling.

## Files read

All inside /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient/v2/:
- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- all 240 files in traces/ (read with a script to tabulate action, grade, order fields and stock):
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
