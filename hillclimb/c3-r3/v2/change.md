Replace the decision instructions with a status-first decision table (Processing / Lost / Shipped up to 14 days / Shipped over 14 days / Delivered) driven by the order record and an explicit day-count method, saying the ticket's story and requests never override the record, and tighten the four action descriptions to the same status and day gates.

## Behavior

Jev picks the policy rule from the ticket's story, or from a rough sense of elapsed time, instead of from the order record's status and exact day count. Five forms of it show up in the train results:

- A. Shipped 14 days ago or less and not delivered, and the ticket says "lost" or "hasn't arrived": Jev applies rule 3 (reship, or escalate for an out-of-stock order over $500) when rule 1 says reply. 5 cases: Y258, Y304, Y114, Y282, Y273.
- B. Shipped more than 14 days ago and not delivered, and the ticket reports a damaged or wrong item (or is a vague status check): Jev replies as if rule 1 applied, when rule 3 says reship or refund. 6 cases: Y089, Y144, Y396, Y133, Y027, Y063.
- C. Delivered 31 to 33 days ago with a damaged or wrong item: Jev refunds as if it were inside the 30-day window. The dates cross a month boundary (late August to October 1). 3 cases: Y138, Y318, Y179.
- D. Status Delivered, and the ticket says it never arrived or asks where it is: Jev reships as if the order were Lost. 2 cases: Y344, Y338.
- E. Delivered damaged item inside 30 days, under $500, and the customer demands a supervisor: Jev escalates because the ticket asked. 2 cases: Y039, Y007.

## How much it costs

The train split has 120 cases x 2 reps = 240 rows; v1 passes 205 (85.4%). 35 rows fail.

The behavior covers 18 cases and 31 failing rows, which is 12.9 points of `pass`.

- A: 10 rows (each case at 0.00)
- B: 9 rows (Y089, Y144, Y396 at 0.00; Y133, Y027, Y063 at 0.50)
- C: 6 rows (all at 0.00)
- D: 4 rows (Y344, Y338 at 0.00)
- E: 2 rows (Y039, Y007 at 0.50)

Y338 will not recover. Its judge reasoning makes up an escalate rule for a Delivered order the customer says never arrived. The policy-faithful action (reply) is what the change asks for, and the same judge passed reply on Y030 and Y362. That makes the realistic ceiling 29 rows, or 12.1 points, which is well outside the plus or minus 6.5 noise floor. The ticket-over-record part alone (A, B, D, E without Y338) is 23 rows, or 9.6 points. The day-count part (C) is 6 rows, or 2.5 points.

The other 4 failing rows are not this behavior, and the change does not target them:
- Y017 (2 rows): the judge treats $500 as over the $500 limit. The same judge passed refund at $500 on Y084.
- Y194 (2 rows): the judge invents an escalate rule for a Delivered order the customer is waiting on.

Why this happens: v1's instructions only talk about rule 4. Nothing tells Jev that status plus day count, not the ticket, picks the rule. v1's line "including the out-of-stock refund in rule 3 for a lost or undelivered order" also made Jev reach for rule 3 without the 14-day gate. Y273 went from 1.00 at baseline to 0.00 under v1, and Y344 went from 0.50 to 0.00. The fix is structural. The instructions now route by status first, gate rule 3 on Lost or on Shipped over 14 days, give a mechanical day count, and keep v1's rule-4 sentence attached to the refund steps.

## Evidence

All traces use today = 2026-10-01 and the same policy text.

A. The ticket says lost, but the record says Shipped 12 to 14 days ago, so Jev should reply.

traces/Y258_rep0.json
```
    "ticket": "The air purifier from order #5258 is lost, I'm sure of it.",
     "status": "Shipped",
     "shipped_on": "2026-09-18",
     "delivered_on": null
   assistant: "reship (confidence 0.96)"
```
Judge: "Shipped 2026-09-18, today is 2026-10-01: 13 days, not delivered. Since 13 days is 14 days or less and the order has not been delivered, the policy requires a reply with order status, not a reship."

traces/Y304_rep0.json
```
    "ticket": "My desk lamp was lost in the mail, order #5304.",
     "status": "Shipped",
     "shipped_on": "2026-09-19",
     "delivered_on": null
   assistant: "reship (confidence 0.91)"
```

traces/Y282_rep0.json (exactly 14 days)
```
    "ticket": "Where is order #5282? I ordered the robot vacuum.",
     "status": "Shipped",
     "shipped_on": "2026-09-17",
     "delivered_on": null
   assistant: "reship (confidence 0.63)"
```

traces/Y273_rep0.json (v1's rule-3/rule-4 wording, applied without the 14-day gate)
```
    "ticket": "Can you check on order #5273 (projector)?",
     "total": 899.0,
     "status": "Shipped",
     "shipped_on": "2026-09-19",
     "delivered_on": null
    "stock": 0
   assistant: "escalate (confidence 0.39)"
```
Judge: "Shipped 2026-09-19, today is 2026-10-01: 12 days, not delivered. Since 12 days is 14 days or less and the order has not been delivered, the policy requires a reply with order status. The agent's escalation is not the required action."

traces/Y114_rep0.json
```
    "ticket": "Order #5114 (espresso machine) hasn't arrived. An update is all I need.",
     "status": "Shipped",
     "shipped_on": "2026-09-18",
     "delivered_on": null
   assistant: "reship (confidence 0.57)"
```

B. The ticket says damaged or wrong item, but the record says Shipped more than 14 days ago and never delivered, so Jev should reship.

traces/Y089_rep0.json
```
    "ticket": "The box for order #5089 was crushed and the espresso machine inside rattles.",
     "status": "Shipped",
     "shipped_on": "2026-09-03",
     "delivered_on": null
    "stock": 3
   assistant: "reply (confidence 0.73)"
```
Judge: "Shipped 2026-09-03, today is 2026-10-01: 28 days, not yet delivered. Since the order shipped more than 14 days ago and has not been delivered, the policy requires reship if in stock (3 units available) or refund if out of stock. The agent's reply action does not match the required action."

traces/Y144_rep0.json
```
    "ticket": "The box for order #5144 was crushed and the air purifier inside rattles.",
     "status": "Shipped",
     "shipped_on": "2026-09-15",
     "delivered_on": null
    "stock": 5
   assistant: "reply (confidence 0.8)"
```

traces/Y396_rep0.json
```
    "ticket": "My portable monitor (order #5396) has a cracked housing and doesn't work. Escalate this to a manager.",
     "status": "Shipped",
     "shipped_on": "2026-09-08",
     "delivered_on": null
    "stock": 8
   assistant: "reply (confidence 0.47)"
```

traces/Y133_rep0.json and traces/Y133_rep1.json (the same input gets a different answer on each rep, both at low confidence)
```
    "ticket": "My earlier order #2619 was fine. Order #5133 has someone else's item, not my espresso machine.",
     "status": "Shipped",
     "shipped_on": "2026-09-01",
     "delivered_on": null
   rep0 assistant: "reply (confidence 0.2)"
   rep1 assistant: "reship (confidence 0.28)"
```

traces/Y027_rep1.json
```
    "ticket": "I received the wrong item on order #5027. It is not the gaming chair I ordered. Get a supervisor on this.",
     "total": 501.0,
     "status": "Shipped",
     "shipped_on": "2026-08-27",
     "delivered_on": null
    "stock": 0
   assistant: "reply (confidence 0.36)"
```

traces/Y063_rep0.json (pass) and traces/Y063_rep1.json (fail), 15 days shipped
```
    "ticket": "Any update on order #5063? The robot vacuum is for a gift.",
     "shipped_on": "2026-09-16",
   rep0 assistant: "reship (confidence 0.37)"
   rep1 assistant: "reply (confidence 0.43)"
```

C. A month-boundary day count (31 to 33 days) gets treated as inside the 30-day window.

traces/Y138_rep0.json
```
    "ticket": "My air purifier (order #5138) has a cracked housing and doesn't work.",
     "status": "Delivered",
     "shipped_on": "2026-08-25",
     "delivered_on": "2026-08-29"
   assistant: "refund (confidence 0.83)"
```
Judge: "Delivered 2026-08-29, today is 2026-10-01: 33 days, outside the 30-day window. Although the item is damaged, the policy requires escalation for damaged items delivered more than 30 days ago, not a refund."

traces/Y318_rep0.json (31 days)
```
    "ticket": "I returned a different item last year (order #1069). This espresso machine, order #5318, smells like burning when I switch it on.",
     "status": "Delivered",
     "delivered_on": "2026-08-31"
   assistant: "refund (confidence 0.87)"
```

traces/Y179_rep0.json (32 days)
```
    "ticket": "Order #5179: the label says smart speaker but the box has a phone case in it.",
     "status": "Delivered",
     "delivered_on": "2026-08-30"
   assistant: "refund (confidence 0.48)"
```

D. The ticket says it never arrived, but the record says Delivered.

traces/Y344_rep0.json
```
    "ticket": "Why can't anyone tell me where order #5344 is? I want my portable monitor.",
     "status": "Delivered",
     "shipped_on": "2026-08-28",
     "delivered_on": "2026-09-03"
   assistant: "reship (confidence 0.41)"
```
Judge: "... The order shows Delivered status, so it is not lost and did arrive. ... The policy does not authorize a reship for a delivered order."

traces/Y338_rep0.json
```
    "ticket": "Order #5338 (espresso machine) hasn't arrived.",
     "status": "Delivered",
     "delivered_on": "2026-08-30"
   assistant: "reship (confidence 0.67)"
```

E. The customer's request for a supervisor overrides a within-window refund.

traces/Y039_rep0.json
```
    "ticket": "My ergonomic keyboard (order #5039) has a cracked housing and doesn't work. Escalate this to a manager.",
     "total": 159.0,
     "status": "Delivered",
     "delivered_on": "2026-09-01"
   assistant: "escalate (confidence 0.57)"
```

traces/Y007_rep1.json
```
    "ticket": "The bluetooth earbuds from order #5007 arrived damaged. I want this escalated.",
     "total": 79.0,
     "status": "Delivered",
     "delivered_on": "2026-09-03"
   assistant: "escalate (confidence 0.43)"
```

Contrast: these cases pass when the record and the ticket agree, or when the dates are far from a threshold.

traces/Y327_rep0.json (12 days, the ticket only checks status)
```
    "ticket": "Order #5327, the air purifier. Just making sure it's on the way.",
     "status": "Shipped",
     "shipped_on": "2026-09-19",
   assistant: "reply (confidence 0.48)"
```

traces/Y354_rep0.json (56 days, far from the boundary)
```
    "ticket": "The smart speaker from order #5354 arrived damaged. Let me know the status.",
     "delivered_on": "2026-08-06"
   assistant: "escalate (confidence 0.93)"
```

traces/Y214_rep0.json (status Lost at 3 days, which correctly goes to rule 3)
```
    "ticket": "Hi, just checking on order #5214. No rush on the smart speaker.",
     "status": "Lost",
     "shipped_on": "2026-09-28",
    "stock": 40
   assistant: "reship (confidence 0.96)"
```

traces/Y033_rep0.json (15 days, the ticket says it never came, so record and ticket agree)
```
    "ticket": "My portable monitor from order #5033 never came. Let me know the status.",
     "shipped_on": "2026-09-16",
   assistant: "reship (confidence 0.52)"
```

The low confidences near the thresholds (Y327 0.48, Y033 0.52, Y063 0.37 and 0.43, Y133 0.2 and 0.28) show that Jev has no firm rule for the status and day gates today. It relies on the ticket's wording, and the passing contrasts pass because the wording happens to point the right way.

## Cases expected to regress

Nothing in v1's behavior is removed. The rule-4 sentence that recovered the out-of-stock-over-$500 cases (Y013, Y050, Y054, Y083, Y124, Y192, Y343, Y346, Y385) is kept and attached to the Lost step and the Shipped-over-14-days step. If restructuring the instructions into a table weakens it, those are the cases to watch.

Currently passing cases that sit at low confidence near a threshold, and could flip if the longer instructions shift Jev's weighting:
- Y327 (Shipped 12 days, reply 0.48 and 0.52)
- Y270 (Shipped 14 days, wrong item, reply 0.67 and 0.61)
- Y033 (Shipped 15 days, reship 0.52 and 0.59)
- Y046 (Delivered 30 days, refund 0.2 and 0.51)
- Y039 rep1 (Delivered 30 days, refund 0.52)
- Y007 rep0 (refund 0.45)
- Y027 rep0 (escalate 0.44)
- Y133 rep1 (reship 0.28)
- Y030 (Delivered 28 days, "where is", reply 0.59 and 0.45)
- Y362 (Delivered 33 days, "check on, refund me", reply 0.4 and 0.32)

Y362 is the one case where the new "Status Delivered ... damaged or wrong item delivered more than 30 days ago, escalate" line sits next to a non-damage ticket. If Jev misreads it, Y362 could move to escalate.

Not expected to recover: Y338 and Y194 (the judge wants escalate for a Delivered "never arrived" order, which the policy does not say), and Y017 (the judge treats $500 as over the limit).

## Files read

All paths are relative to /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3-r3/v2/

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- out/allrows.txt (my own scratch table, built from results_train.jsonl and traces)
- traces/ (all 240 files, loaded programmatically for the tabulation; the ones quoted above were read line by line):
  traces/Y007_rep0.json traces/Y007_rep1.json traces/Y011_rep0.json traces/Y011_rep1.json traces/Y012_rep0.json traces/Y012_rep1.json traces/Y013_rep0.json traces/Y013_rep1.json traces/Y016_rep0.json traces/Y016_rep1.json traces/Y017_rep0.json traces/Y017_rep1.json traces/Y024_rep0.json traces/Y024_rep1.json traces/Y025_rep0.json traces/Y025_rep1.json traces/Y026_rep0.json traces/Y026_rep1.json traces/Y027_rep0.json traces/Y027_rep1.json traces/Y028_rep0.json traces/Y028_rep1.json traces/Y030_rep0.json traces/Y030_rep1.json traces/Y031_rep0.json traces/Y031_rep1.json traces/Y033_rep0.json traces/Y033_rep1.json traces/Y039_rep0.json traces/Y039_rep1.json traces/Y046_rep0.json traces/Y046_rep1.json traces/Y050_rep0.json traces/Y050_rep1.json traces/Y052_rep0.json traces/Y052_rep1.json traces/Y054_rep0.json traces/Y054_rep1.json traces/Y055_rep0.json traces/Y055_rep1.json traces/Y061_rep0.json traces/Y061_rep1.json traces/Y063_rep0.json traces/Y063_rep1.json traces/Y064_rep0.json traces/Y064_rep1.json traces/Y068_rep0.json traces/Y068_rep1.json traces/Y076_rep0.json traces/Y076_rep1.json traces/Y080_rep0.json traces/Y080_rep1.json traces/Y081_rep0.json traces/Y081_rep1.json traces/Y082_rep0.json traces/Y082_rep1.json traces/Y083_rep0.json traces/Y083_rep1.json traces/Y084_rep0.json traces/Y084_rep1.json traces/Y085_rep0.json traces/Y085_rep1.json traces/Y088_rep0.json traces/Y088_rep1.json traces/Y089_rep0.json traces/Y089_rep1.json traces/Y110_rep0.json traces/Y110_rep1.json traces/Y112_rep0.json traces/Y112_rep1.json traces/Y114_rep0.json traces/Y114_rep1.json traces/Y116_rep0.json traces/Y116_rep1.json traces/Y118_rep0.json traces/Y118_rep1.json traces/Y119_rep0.json traces/Y119_rep1.json traces/Y121_rep0.json traces/Y121_rep1.json traces/Y123_rep0.json traces/Y123_rep1.json traces/Y124_rep0.json traces/Y124_rep1.json traces/Y131_rep0.json traces/Y131_rep1.json traces/Y133_rep0.json traces/Y133_rep1.json traces/Y138_rep0.json traces/Y138_rep1.json traces/Y144_rep0.json traces/Y144_rep1.json traces/Y148_rep0.json traces/Y148_rep1.json traces/Y149_rep0.json traces/Y149_rep1.json traces/Y161_rep0.json traces/Y161_rep1.json traces/Y162_rep0.json traces/Y162_rep1.json traces/Y166_rep0.json traces/Y166_rep1.json traces/Y169_rep0.json traces/Y169_rep1.json traces/Y179_rep0.json traces/Y179_rep1.json traces/Y180_rep0.json traces/Y180_rep1.json traces/Y188_rep0.json traces/Y188_rep1.json traces/Y190_rep0.json traces/Y190_rep1.json traces/Y192_rep0.json traces/Y192_rep1.json traces/Y193_rep0.json traces/Y193_rep1.json traces/Y194_rep0.json traces/Y194_rep1.json traces/Y200_rep0.json traces/Y200_rep1.json traces/Y206_rep0.json traces/Y206_rep1.json traces/Y209_rep0.json traces/Y209_rep1.json traces/Y212_rep0.json traces/Y212_rep1.json traces/Y214_rep0.json traces/Y214_rep1.json traces/Y215_rep0.json traces/Y215_rep1.json traces/Y222_rep0.json traces/Y222_rep1.json traces/Y225_rep0.json traces/Y225_rep1.json traces/Y231_rep0.json traces/Y231_rep1.json traces/Y232_rep0.json traces/Y232_rep1.json traces/Y237_rep0.json traces/Y237_rep1.json traces/Y240_rep0.json traces/Y240_rep1.json traces/Y243_rep0.json traces/Y243_rep1.json traces/Y244_rep0.json traces/Y244_rep1.json traces/Y247_rep0.json traces/Y247_rep1.json traces/Y250_rep0.json traces/Y250_rep1.json traces/Y251_rep0.json traces/Y251_rep1.json traces/Y252_rep0.json traces/Y252_rep1.json traces/Y255_rep0.json traces/Y255_rep1.json traces/Y258_rep0.json traces/Y258_rep1.json traces/Y263_rep0.json traces/Y263_rep1.json traces/Y265_rep0.json traces/Y265_rep1.json traces/Y266_rep0.json traces/Y266_rep1.json traces/Y270_rep0.json traces/Y270_rep1.json traces/Y273_rep0.json traces/Y273_rep1.json traces/Y277_rep0.json traces/Y277_rep1.json traces/Y282_rep0.json traces/Y282_rep1.json traces/Y290_rep0.json traces/Y290_rep1.json traces/Y292_rep0.json traces/Y292_rep1.json traces/Y293_rep0.json traces/Y293_rep1.json traces/Y303_rep0.json traces/Y303_rep1.json traces/Y304_rep0.json traces/Y304_rep1.json traces/Y309_rep0.json traces/Y309_rep1.json traces/Y312_rep0.json traces/Y312_rep1.json traces/Y315_rep0.json traces/Y315_rep1.json traces/Y318_rep0.json traces/Y318_rep1.json traces/Y323_rep0.json traces/Y323_rep1.json traces/Y327_rep0.json traces/Y327_rep1.json traces/Y331_rep0.json traces/Y331_rep1.json traces/Y333_rep0.json traces/Y333_rep1.json traces/Y334_rep0.json traces/Y334_rep1.json traces/Y338_rep0.json traces/Y338_rep1.json traces/Y342_rep0.json traces/Y342_rep1.json traces/Y343_rep0.json traces/Y343_rep1.json traces/Y344_rep0.json traces/Y344_rep1.json traces/Y346_rep0.json traces/Y346_rep1.json traces/Y354_rep0.json traces/Y354_rep1.json traces/Y356_rep0.json traces/Y356_rep1.json traces/Y358_rep0.json traces/Y358_rep1.json traces/Y360_rep0.json traces/Y360_rep1.json traces/Y362_rep0.json traces/Y362_rep1.json traces/Y364_rep0.json traces/Y364_rep1.json traces/Y365_rep0.json traces/Y365_rep1.json traces/Y371_rep0.json traces/Y371_rep1.json traces/Y380_rep0.json traces/Y380_rep1.json traces/Y383_rep0.json traces/Y383_rep1.json traces/Y385_rep0.json traces/Y385_rep1.json traces/Y386_rep0.json traces/Y386_rep1.json traces/Y389_rep0.json traces/Y389_rep1.json traces/Y396_rep0.json traces/Y396_rep1.json traces/Y400_rep0.json traces/Y400_rep1.json
