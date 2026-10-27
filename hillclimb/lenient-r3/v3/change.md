No change proposed: the only behavior big enough to clear the noise floor (Jev skips the $500 limit on the rule-3 out-of-stock refund, 19 rows, 7.9 points) has already resisted both in-scope levers, and every other behavior costs 3 points or less.

## Summary

Baseline train pass is 201 of 240 rows (83.75%). The 39 failing rows split into five behaviors. Only one of them is large enough that a full fix would clear the plus or minus 6.5 point noise floor, and it clears it by 1.4 points. Clearing the floor needs a net gain of at least 16 rows, so a change would have to recover at least 16 of that behavior's 19 failing rows with no regressions anywhere else. Rounds v1 and v2 both aimed at this same behavior, between them used both levers in scope (decision_instructions and the action descriptions), and recovered one case (Y385) while losing Y119's lucky pass. They regressed other cases (v1 net -7 rows, v2 net -1 row). The categorization round traced the behavior to a structural cause that needs a code-side fix. I do not expect a third wording of the same rule to reach 16 of 19 rows without regressions, so I am not writing artifact.json.

## The behavior

When a non-arrival ticket falls under policy rule 3 ("if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it"), stock is 0, and the order total is over $500, Jev picks refund. It does not apply rule 4 ("Any refund over $500 must be escalated instead of refunded"). The judge fails every one of these rows.

- Cases: 10 (Y013, Y050, Y054, Y083, Y119, Y124, Y192, Y343, Y346, Y385).
- Failing rows: 19 of 20. Y119 rep 1 picked reply at confidence 0.31 and the lenient judge passed it.
- Cost: 19 of 240 rows, or 7.9 points of train pass. This is the most a fix can gain.
- Confidence is high: 0.84 to 0.99 on 16 of the 19 failing rows. Jev is confident in these picks, not uncertain between refund and escalate.

The same rule-4 check works on the damage path. In the 12 cases (24 rows) where rule 2 calls for a refund (delivered 30 days ago or less) and the total is over $500, Jev picks escalate in all 24 rows and all 24 pass. Under the limit on the rule-3 path, it gets the refund right too: all 10 rule-3 out-of-stock rows with a total of $500 or less pick refund and pass. Across all 122 non-arrival rows, Jev never picks escalate once, even on the five non-arrival tickets that ask for a supervisor or manager. The failure is specific: rule 4 is chained onto rule 2's refund and never onto rule 3's fallback refund.

## Why no change is proposed

1. The margin is thin. The full fix is worth 19 rows; the floor is about 15 to 16 rows. Any partial fix, or any full fix with three or more rows of regression, lands inside the noise.
2. Both levers have been tried on this exact behavior. v1 changed the instructions and the refund and escalate descriptions. v2 rewrote the refund and escalate descriptions as complete condition lists, including the over-$500 out-of-stock case. Per scores_train.tsv, the cluster went from 0.5 of 10 cases at baseline to 1.0 of 10 in both v1 and v2 (Y385 passed, Y119 dropped from 0.5 to 0). Train mean went from 0.8375 to 0.8083 (v1) and 0.8333 (v2).
3. The regressions those rounds caused are the predictable side effect of this rule. Y273 (Shipped 12 days ago, total 899.0, stock 0, correct action reply) failed both reps in both v1 and v2. Text that ties "over $500 and stock 0" to escalate pulls Jev off rule 1 on high-value orders that are still in transit. v1 also lost Y030, Y362, Y344 and Y327 and v2 lost Y318, which are neighboring non-arrival or boundary cases. A third attempt would put the same cases at risk (see "Cases expected to regress" below).
4. The root fix is out of scope. The categorization round recommends enforcing rule 4 in code after Jev picks an action, so any refund over $500 becomes escalate. The code is off-limits for this loop.

## Other behaviors (all inside the noise floor)

| Behavior | Cases | Failing rows | Points |
|---|---|---|---|
| Rule-3 out-of-stock refund over $500 not escalated (above) | 10 | 19 | 7.9 |
| Order record says Delivered, customer says it never came: Jev reships (judge passes reply on Y030, Y362, Y344 rep 0) | 3 (Y194, Y338, Y344) | 5 | 2.1 |
| Policy-correct action failed by the judge (Y007 rep 1 refund, Y061 and Y169 reply to changed-mind, Y084 refund at exactly $500) | 4 | 7 | 2.9 |
| Damage or wrong-item claim on an order that was never delivered (no policy rule) | 2 (Y027, Y133) | 4 | 1.7 |
| Day boundary: shipped exactly 14 days ago (Y282, reship instead of reply); delivered exactly 30 days ago (Y039, escalate instead of refund) | 2 | 4 | 1.7 |

The judge-disagreement rows should not be chased from the agent side: the agent's action already matches the policy. The other three behaviors each cost at most 2.1 points, so a full fix of any one of them still lands inside the floor.

## Evidence

Policy rules 3 and 4 as Jev sees them (identical in every trace; quoted from the user message in traces/Y050_rep0.json):

```
3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.
4. Any refund over $500 must be escalated instead of refunded.
```

The decoded lines below come from each trace's user message (order and stock fields). The last line is the trace's assistant message, quoted verbatim from the file.

### Failing: rule-3 out-of-stock, over $500, Jev refunds

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y050_rep0.json (pass 0)
```
 "ticket": "Hi, just checking on order #5050. No rush on the projector.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-08-29",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.99)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y013_rep1.json (pass 0)
```
 "ticket": "Tracking for order #5013 (gaming chair) hasn't moved in a while.",
  "total": 501.0,
  "status": "Lost",
  "shipped_on": "2026-08-29",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.97)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y054_rep0.json (pass 0; shipped 16 days before today 2026-10-01)
```
 "ticket": "My projector from order #5054 never came.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-15",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.67)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y343_rep0.json (pass 0; shipped 34 days before today)
```
 "ticket": "Why can't anyone tell me where order #5343 is? I want my projector.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-08-28",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.87)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y083_rep0.json (pass 0; even an explicit escalation demand does not move Jev off refund on this path)
```
 "ticket": "My projector from order #5083 never came. Escalate this to a manager.",
  "total": 899.0,
  "status": "Lost",
  "shipped_on": "2026-09-26",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.87)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y119_rep0.json (pass 0; shipped 24 days ago)
```
 "ticket": "Order #5119, the projector. Just making sure it's on the way.",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-07",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.29)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y119_rep1.json (pass 1 through judge leniency; the policy calls for escalate). Same ticket and order fields as rep 0.
```
  "content": "reply (confidence 0.31)"
```

### Passing contrast: rule 2 refund over $500, Jev escalates

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y081_rep0.json (pass 1; delivered 27 days ago, so rule 2 says refund and rule 4 turns it into escalate)
```
 "ticket": "Order #5081: the gaming chair is broken. Refund me.",
  "total": 501.0,
  "status": "Delivered",
  "shipped_on": "2026-08-31",
  "delivered_on": "2026-09-04"
 "stock": 0
  "content": "escalate (confidence 0.81)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y180_rep0.json (pass 1; delivered 13 days ago)
```
 "ticket": "Order #5180: the label says home theater soundbar but the box has a phone case in it.",
  "total": 649.0,
  "status": "Delivered",
  "shipped_on": "2026-09-15",
  "delivered_on": "2026-09-18"
 "stock": 6
  "content": "escalate (confidence 0.99)"
```

### Passing contrast: rule-3 out-of-stock at or under $500, Jev refunds

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y312_rep0.json (pass 1)
```
 "ticket": "Why can't anyone tell me where order #5312 is? I want my bluetooth earbuds.",
  "total": 79.0,
  "status": "Lost",
  "shipped_on": "2026-09-15",
  "delivered_on": null
 "stock": 0
  "content": "refund (confidence 0.99)"
```

### The neighbor that v1 and v2 both broke

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/traces/Y273_rep0.json (pass 1 at baseline; 0 in v1 and v2 per scores_train.tsv; shipped 12 days ago, so rule 1 says reply)
```
 "ticket": "Can you check on order #5273 (projector)?",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-19",
  "delivered_on": null
 "stock": 0
  "content": "reply (confidence 0.61)"
```

Its fields match the failing cluster on total and stock and differ only on the ship date. This is why text keyed to "over $500, out of stock" moves it.

## Cases expected to regress

None, because no artifact change is proposed. If the loop overrides this and tries a third over-limit rule anyway, expect Y273 to regress (it did in both v1 and v2). Y030, Y362, Y344, Y327 (v1) and Y318 (v2) are also at risk. Y119 rep 1 would likely lose its lucky reply pass.

## Recommendation outside this loop

Enforce rule 4 in code after Jev picks an action (refund with total > 500 becomes escalate). That recovers up to 19 rows without touching any other case, because Jev already escalates correctly on the rule-2 path. Separately, fix or recalibrate the judge for the 7 policy-correct rows it fails, and measure its TPR and TNR. The categorization round counted 14 policy-contradicting rows that this lenient judge passed (Y007 rep 0, Y063, Y114, Y119 rep 1, Y138, Y258, Y304, Y318), and that leniency keeps small agent-side gains inside the noise.

## Files read

All paths are under /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v3/.

- BRIEF.md
- artifact.json
- history.md
- categorization.md
- scores_train.tsv
- results_train.jsonl
- out/rows.tsv (my own scratch table built from the traces and results)
- out/exp.tsv (my own scratch table: the policy-expected action per row)
- traces/ (all 240 files, read by script):
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
