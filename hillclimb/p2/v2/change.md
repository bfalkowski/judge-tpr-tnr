Add the missing rule for tickets that contradict the order record about receipt (damaged/wrong item in hand but record not Delivered, or "never came" but record Delivered, status not Processing): choose refund, stated in the instructions and in the refund description.

## The behavior

The policy has no rule for a ticket that contradicts the order record about whether the customer has the order. There are two kinds:

1. The customer describes a damaged or wrong item they have in hand, but the record says Shipped with `delivered_on: null`. Rule 2 needs a delivery date, so Jev falls back to rule 1 or rule 3 and picks `reply` (or `reship`).
2. The customer says the order never came, but the record says Delivered. No rule covers a delivered order that "never arrived", so Jev guesses between `reply` and `reship` at low confidence (0.24 to 0.49).

The current instructions only ask "Which action does the support policy call for on this ticket?", so nothing tells Jev what to do when no rule fits. It reaches for `reply` or `reship`, and the judge fails both.

## How many cases, and what it costs

- 13 of 120 train cases (26 of 240 rows) show it: 8 of kind 1 (Y027, Y089, Y133, Y144, Y263, Y266, Y270, Y396) and 5 of kind 2 (Y030, Y194, Y338, Y344, Y362). Processing-status tickets are excluded; there rule 1 already decides and the judge mostly passes `reply` (12 of 18 rows).
- 24 of the 26 rows fail. Only Y144 passes (2 rows, `reply`). These 24 rows are 42% of all 57 failing train rows and 12 of the 29 cases with any failure.
- Cost: 24/240 = 10.0 points of train `pass` (baseline 183/240 = 76.25%). A full fix gains at most +10.0 points; if Y144 flips to fail, the ceiling is +9.2. That clears the ±6.5 noise floor only if most of the 24 rows recover. If only about two thirds recover, the gain (about 6.7 points) sits at the edge of the noise.

### Why refund

The judge gives no explanations, so the target action comes from elimination:

- `reply` was chosen in 10 of the 13 cases and failed in 17 of its 19 rows. Y144 (2 rows) is the only pass.
- `reship` fails on all 4 cases where Jev picked it (Y133, Y194, Y338, Y344 rep1), even with stock on hand (Y338 stock 3, Y344 stock 8).
- `escalate` was v1's instruction for "tickets that contradict the order record". Under v1, all 12 failing cases here stayed at 0.00 in `scores_train.tsv` (Y027, Y030, Y089, Y133, Y194, Y263, Y266, Y270, Y338, Y344, Y362, Y396), and Y144 dropped from 1.00 to 0.00. There are no v1 traces, so this assumes v1 actually moved those cases to `escalate`. The Y144 drop suggests it did.
- `refund` has not been tried on any of them. It is also the action rule 2 gives once you accept that the customer has the item (kind 1). For kind 2, it is rule 3's fallback with no shipment in transit to wait on.

Two of the 13 cases are over $500 (Y027 $501, Y270 $549). The new rule says refund regardless of total for two reasons. Y027 stayed failing under v1's escalate. The judge also passes `refund` on undelivered orders over $500 in 18 of 19 rows (Lost: 14/14, Shipped: 4/5), even though rule 4 literally says escalate.

### How this differs from v1

v1 sent contradictions and explicit "get me a supervisor" requests to `escalate`, and it was reverted. Most of its regressions were explicit-request cases (Y082, Y083, Y193, Y209 went from 1.00 to 0.00). Y144 also dropped, and Y282 and Y327 went to 0.50. This change does not touch explicit escalation requests. It uses a different action, `refund`, and a different lever: a rule in the instructions plus a matching clause in the refund description, with the escalate description left alone.

## The change

`decision_instructions` gains a check that runs before the rules. It defines the two contradictions in terms of the record's fields (status, `delivered_on`), not ticket wording. It routes both to `refund`, excludes Processing, and says that a disagreement only about when the order arrived is not a contradiction. Criterion "0" (refund) gains the same condition, so the option text matches the instruction. Criteria 1 to 3 are unchanged. No product names, phrasings, or case content from train appear in the artifact.

## The rest of the failures (not addressed, and why)

The other 33 failing rows are mostly cases where Jev already picked the literal policy action and the judge failed it (23 rows). Nearly identical cases with the same action get opposite verdicts, for example Y046 and Y188 (both delivered wrong item, delivered 27 to 29 days ago, under $100, refund) and Y169 and Y061 (both change-of-mind, delivered, reply). Meanwhile the judge passes policy-violating actions such as refund over $500 (Y346, Y083) and reship within 14 days (Y282). Nothing in the artifact can move Jev toward the judge's verdict on these without memorizing cases. The quotes are at the end of the evidence section.

## Evidence (verbatim; state lines from the trace's user message, action from the assistant message)

The policy text is identical in every trace. The lines this behavior falls between, quoted from `traces/Y089_rep0.json`:

```
1. If the order has not shipped yet (status Processing), or it shipped 14 days ago or less and has not been delivered, reply with the order status. Take no other action.
2. Damaged or wrong item: if the order was delivered 30 days ago or less, refund it. If it was delivered more than 30 days ago, escalate.
3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.
```

The current instructions, from the system message of every trace (e.g. `traces/Y089_rep0.json`):

```
"content": "Which action does the support policy call for on this ticket?\n\nActions:\n0. refund: refund the order\n1. reship: send a replacement\n2. escalate: hand the ticket to a supervisor\n3. reply: reply to the customer and take no other action"
```

#### Kind 1. Customer has a damaged or wrong item in hand, record says Shipped with delivered_on null (8 cases, 14 of 16 rows fail)

`traces/Y089_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "The box for order #5089 was crushed and the espresso machine inside rattles.",
"total": 499.0,
"status": "Shipped",
"shipped_on": "2026-09-03",
"delivered_on": null
"stock": 3
assistant "content": "reply (confidence 0.79)"
```

`traces/Y263_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "Order #5263: the label says air purifier but the box has a phone case in it.",
"total": 500.0,
"status": "Shipped",
"shipped_on": "2026-09-25",
"delivered_on": null
"stock": 5
assistant "content": "reply (confidence 0.84)"
```

`traces/Y266_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "You sent me the WRONG thing for order #5266. Where is my bluetooth earbuds?",
"total": 79.0,
"status": "Shipped",
"shipped_on": "2026-09-26",
"delivered_on": null
"stock": 0
assistant "content": "reply (confidence 0.75)"
```

`traces/Y270_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "Order #5270 should have been my robot vacuum, but you sent something else.",
"total": 549.0,
"status": "Shipped",
"shipped_on": "2026-09-17",
"delivered_on": null
"stock": 2
assistant "content": "reply (confidence 0.56)"
```

`traces/Y396_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "My portable monitor (order #5396) has a cracked housing and doesn't work. Escalate this to a manager.",
"total": 299.0,
"status": "Shipped",
"shipped_on": "2026-09-08",
"delivered_on": null
"stock": 8
assistant "content": "reply (confidence 0.57)"
```

`traces/Y027_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "I received the wrong item on order #5027. It is not the gaming chair I ordered. Get a supervisor on this.",
"total": 501.0,
"status": "Shipped",
"shipped_on": "2026-08-27",
"delivered_on": null
"stock": 0
assistant "content": "reply (confidence 0.51)"
```

`traces/Y133_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "My earlier order #2619 was fine. Order #5133 has someone else's item, not my espresso machine.",
"total": 499.0,
"status": "Shipped",
"shipped_on": "2026-09-01",
"delivered_on": null
"stock": 3
assistant "content": "reship (confidence 0.32)"
```

#### Contrast inside the behavior. Same wording as Y089, same reply, passes (the only passing contradiction case)

`traces/Y144_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "The box for order #5144 was crushed and the air purifier inside rattles.",
"total": 500.0,
"status": "Shipped",
"shipped_on": "2026-09-15",
"delivered_on": null
"stock": 5
assistant "content": "reply (confidence 0.88)"
```

#### Kind 2. Customer says the order never came, record says Delivered (5 cases, 10 of 10 rows fail; reply and reship both fail)

`traces/Y030_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "Where is order #5030? I ordered the document scanner.",
"total": 249.0,
"status": "Delivered",
"shipped_on": "2026-09-01",
"delivered_on": "2026-09-03"
"stock": 0
assistant "content": "reply (confidence 0.33)"
```

`traces/Y338_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "Order #5338 (espresso machine) hasn't arrived.",
"total": 499.0,
"status": "Delivered",
"shipped_on": "2026-08-25",
"delivered_on": "2026-08-30"
"stock": 3
assistant "content": "reship (confidence 0.24)"
```

`traces/Y344_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "Why can't anyone tell me where order #5344 is? I want my portable monitor.",
"total": 299.0,
"status": "Delivered",
"shipped_on": "2026-08-28",
"delivered_on": "2026-09-03"
"stock": 8
assistant "content": "reply (confidence 0.49)"
```

`traces/Y344_rep1.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "Why can't anyone tell me where order #5344 is? I want my portable monitor.",
"total": 299.0,
"status": "Delivered",
"shipped_on": "2026-08-28",
"delivered_on": "2026-09-03"
"stock": 8
assistant "content": "reship (confidence 0.31)"
```

`traces/Y194_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "I've been waiting FOREVER for my countertop oven, order #5194.",
"total": 189.0,
"status": "Delivered",
"shipped_on": "2026-08-27",
"delivered_on": "2026-08-29"
"stock": 0
assistant "content": "reship (confidence 0.31)"
```

`traces/Y362_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "Can you check on order #5362 (countertop oven)? Refund me.",
"total": 189.0,
"status": "Delivered",
"shipped_on": "2026-08-25",
"delivered_on": "2026-08-29"
"stock": 0
assistant "content": "reply (confidence 0.25)"
```

#### Contrast outside the behavior. Status Processing, same kind of ticket, reply passes (the change leaves these alone)

`traces/Y309_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "My robot vacuum (order #5309) has a cracked housing and doesn't work.",
"total": 549.0,
"status": "Processing",
"shipped_on": null,
"delivered_on": null
"stock": 2
assistant "content": "reply (confidence 0.96)"
```

`traces/Y209_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "I received the wrong item on order #5209. It is not the home theater soundbar I ordered. Get a supervisor on this.",
"total": 649.0,
"status": "Processing",
"shipped_on": null,
"delivered_on": null
"stock": 6
assistant "content": "reply (confidence 0.92)"
```

`traces/Y190_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "My earlier order #1725 was fine. Order #5190 has someone else's item, not my ergonomic keyboard.",
"total": 159.0,
"status": "Processing",
"shipped_on": null,
"delivered_on": null
"stock": 0
assistant "content": "reply (confidence 1.0)"
```

#### Best cases, for contrast. Ticket and record agree, high confidence, pass

`traces/Y166_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "The home theater soundbar from order #5166 arrived damaged.",
"total": 649.0,
"status": "Delivered",
"shipped_on": "2026-08-31",
"delivered_on": "2026-09-03"
"stock": 6
assistant "content": "escalate (confidence 0.95)"
```

`traces/Y383_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "Order #5383 (home theater soundbar) hasn't arrived.",
"total": 649.0,
"status": "Lost",
"shipped_on": "2026-08-28",
"delivered_on": null
"stock": 6
assistant "content": "reship (confidence 1.0)"
```

#### Expected-regression risk. Delivered damage tickets whose wording gives a different arrival time than the record; escalate passes today

`traces/Y088_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "The projector from order #5088 came yesterday and it's broken.",
"total": 899.0,
"status": "Delivered",
"shipped_on": "2026-08-25",
"delivered_on": "2026-08-30"
"stock": 0
assistant "content": "escalate (confidence 0.89)"
```

`traces/Y215_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "Got order #5215 last week and the home theater soundbar already stopped working.",
"total": 649.0,
"status": "Delivered",
"shipped_on": "2026-08-27",
"delivered_on": "2026-08-29"
"stock": 6
assistant "content": "escalate (confidence 0.87)"
```

`traces/Y240_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "Order #5240 just arrived and the home theater soundbar is damaged.",
"total": 649.0,
"status": "Delivered",
"shipped_on": "2026-08-23",
"delivered_on": "2026-08-25"
"stock": 6
assistant "content": "escalate (confidence 0.85)"
```

`traces/Y277_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "Got order #5277 last week and the gaming chair already stopped working.",
"total": 501.0,
"status": "Delivered",
"shipped_on": "2026-08-25",
"delivered_on": "2026-08-30"
"stock": 0
assistant "content": "escalate (confidence 0.88)"
```

#### Nearest neighbours that should not change. Customer asserts loss, record Shipped

`traces/Y258_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "The air purifier from order #5258 is lost, I'm sure of it.",
"total": 500.0,
"status": "Shipped",
"shipped_on": "2026-09-18",
"delivered_on": null
"stock": 5
assistant "content": "reship (confidence 0.8)"
```

`traces/Y304_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "My desk lamp was lost in the mail, order #5304.",
"total": 45.0,
"status": "Shipped",
"shipped_on": "2026-09-19",
"delivered_on": null
"stock": 30
assistant "content": "reship (confidence 0.76)"
```

#### Judge context (not targeted by this change). Near-twins with the same action and opposite verdicts, and passes on policy-violating actions

`traces/Y046_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "Order #5046 should have been my standing desk mat, but you sent something else. Just send a new one.",
"total": 69.0,
"status": "Delivered",
"shipped_on": "2026-08-30",
"delivered_on": "2026-09-02"
"stock": 22
assistant "content": "refund (confidence 0.49)"
```

`traces/Y188_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "Order #5188 should have been my smart speaker, but you sent something else. Ship me another one.",
"total": 99.0,
"status": "Delivered",
"shipped_on": "2026-09-02",
"delivered_on": "2026-09-04"
"stock": 40
assistant "content": "refund (confidence 0.53)"
```

`traces/Y169_rep0.json` (results_train.jsonl: `"grade": {"pass": 0}`)
```
"ticket": "I don't need the home theater soundbar from order #5169 anymore. Can I return it? Let me know the status.",
"total": 649.0,
"status": "Delivered",
"shipped_on": "2026-08-05",
"delivered_on": "2026-08-11"
"stock": 6
assistant "content": "reply (confidence 0.97)"
```

`traces/Y061_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "I don't need the gaming chair from order #5061 anymore. Can I return it? Let me know the status.",
"total": 501.0,
"status": "Delivered",
"shipped_on": "2026-08-28",
"delivered_on": "2026-08-30"
"stock": 0
assistant "content": "reply (confidence 0.95)"
```

`traces/Y346_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "Where is order #5346? I ordered the gaming chair.",
"total": 501.0,
"status": "Lost",
"shipped_on": "2026-09-17",
"delivered_on": null
"stock": 0
assistant "content": "refund (confidence 0.97)"
```

`traces/Y083_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "My projector from order #5083 never came. Escalate this to a manager.",
"total": 899.0,
"status": "Lost",
"shipped_on": "2026-09-26",
"delivered_on": null
"stock": 0
assistant "content": "refund (confidence 0.87)"
```

`traces/Y282_rep0.json` (results_train.jsonl: `"grade": {"pass": 1}`)
```
"ticket": "Where is order #5282? I ordered the robot vacuum.",
"total": 549.0,
"status": "Shipped",
"shipped_on": "2026-09-17",
"delivered_on": null
"stock": 2
assistant "content": "reship (confidence 0.6)"
```


## Cases I expect to regress

- **Y144** (2 rows, passes today with `reply`). Its ticket and record have the same shape as Y089, which fails with `reply`, so the new rule will move it to `refund`. It dropped to 0.00 under v1, which presumably moved it to `escalate`. If `refund` is also not what the judge wants here, this costs 2 rows (0.8 points). It is the only passing case inside the behavior.
- **Delivered damage tickets whose wording implies a different arrival date than the record**: Y088 ("came yesterday", record delivered 32 days ago), Y215 and Y277 ("Got order ... last week", 33 and 32 days), Y240 ("just arrived", 37 days). All 8 rows pass today with `escalate`. If Jev reads the date mismatch as a contradiction, it will refund and they will fail. The timing clause in the new rule is there to prevent this. These are the most likely collateral regressions.
- **Processing-status tickets reporting damage, a wrong item, or a return**: Y190, Y200, Y209, Y250, Y309, Y334 (12 rows pass today with `reply`). They are excluded by "This check does not apply when the status is Processing", but if Jev over-applies the new rule they would flip to `refund`. Y209 is the one to watch: it fell to 0.00 under v1.
- **Shipped tickets where the customer only asserts loss**: Y258 ("is lost, I'm sure of it"), Y304 ("lost in the mail"). Both pass with `reship`. They are not contradictions under the new definition (customer has not received the order, status is not Delivered), so I expect no change. I list them because they are the nearest neighbours.

## Files read

All paths are under `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/p2/v2/`:

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- all 240 trace files, parsed with scripts; the cited ones are quoted above:

```
traces/Y007_rep0.json traces/Y007_rep1.json traces/Y011_rep0.json traces/Y011_rep1.json traces/Y012_rep0.json traces/Y012_rep1.json traces/Y013_rep0.json traces/Y013_rep1.json traces/Y016_rep0.json 
traces/Y016_rep1.json traces/Y017_rep0.json traces/Y017_rep1.json traces/Y024_rep0.json traces/Y024_rep1.json traces/Y025_rep0.json traces/Y025_rep1.json traces/Y026_rep0.json traces/Y026_rep1.json 
traces/Y027_rep0.json traces/Y027_rep1.json traces/Y028_rep0.json traces/Y028_rep1.json traces/Y030_rep0.json traces/Y030_rep1.json traces/Y031_rep0.json traces/Y031_rep1.json traces/Y033_rep0.json 
traces/Y033_rep1.json traces/Y039_rep0.json traces/Y039_rep1.json traces/Y046_rep0.json traces/Y046_rep1.json traces/Y050_rep0.json traces/Y050_rep1.json traces/Y052_rep0.json traces/Y052_rep1.json 
traces/Y054_rep0.json traces/Y054_rep1.json traces/Y055_rep0.json traces/Y055_rep1.json traces/Y061_rep0.json traces/Y061_rep1.json traces/Y063_rep0.json traces/Y063_rep1.json traces/Y064_rep0.json 
traces/Y064_rep1.json traces/Y068_rep0.json traces/Y068_rep1.json traces/Y076_rep0.json traces/Y076_rep1.json traces/Y080_rep0.json traces/Y080_rep1.json traces/Y081_rep0.json traces/Y081_rep1.json 
traces/Y082_rep0.json traces/Y082_rep1.json traces/Y083_rep0.json traces/Y083_rep1.json traces/Y084_rep0.json traces/Y084_rep1.json traces/Y085_rep0.json traces/Y085_rep1.json traces/Y088_rep0.json 
traces/Y088_rep1.json traces/Y089_rep0.json traces/Y089_rep1.json traces/Y110_rep0.json traces/Y110_rep1.json traces/Y112_rep0.json traces/Y112_rep1.json traces/Y114_rep0.json traces/Y114_rep1.json 
traces/Y116_rep0.json traces/Y116_rep1.json traces/Y118_rep0.json traces/Y118_rep1.json traces/Y119_rep0.json traces/Y119_rep1.json traces/Y121_rep0.json traces/Y121_rep1.json traces/Y123_rep0.json 
traces/Y123_rep1.json traces/Y124_rep0.json traces/Y124_rep1.json traces/Y131_rep0.json traces/Y131_rep1.json traces/Y133_rep0.json traces/Y133_rep1.json traces/Y138_rep0.json traces/Y138_rep1.json 
traces/Y144_rep0.json traces/Y144_rep1.json traces/Y148_rep0.json traces/Y148_rep1.json traces/Y149_rep0.json traces/Y149_rep1.json traces/Y161_rep0.json traces/Y161_rep1.json traces/Y162_rep0.json 
traces/Y162_rep1.json traces/Y166_rep0.json traces/Y166_rep1.json traces/Y169_rep0.json traces/Y169_rep1.json traces/Y179_rep0.json traces/Y179_rep1.json traces/Y180_rep0.json traces/Y180_rep1.json 
traces/Y188_rep0.json traces/Y188_rep1.json traces/Y190_rep0.json traces/Y190_rep1.json traces/Y192_rep0.json traces/Y192_rep1.json traces/Y193_rep0.json traces/Y193_rep1.json traces/Y194_rep0.json 
traces/Y194_rep1.json traces/Y200_rep0.json traces/Y200_rep1.json traces/Y206_rep0.json traces/Y206_rep1.json traces/Y209_rep0.json traces/Y209_rep1.json traces/Y212_rep0.json traces/Y212_rep1.json 
traces/Y214_rep0.json traces/Y214_rep1.json traces/Y215_rep0.json traces/Y215_rep1.json traces/Y222_rep0.json traces/Y222_rep1.json traces/Y225_rep0.json traces/Y225_rep1.json traces/Y231_rep0.json 
traces/Y231_rep1.json traces/Y232_rep0.json traces/Y232_rep1.json traces/Y237_rep0.json traces/Y237_rep1.json traces/Y240_rep0.json traces/Y240_rep1.json traces/Y243_rep0.json traces/Y243_rep1.json 
traces/Y244_rep0.json traces/Y244_rep1.json traces/Y247_rep0.json traces/Y247_rep1.json traces/Y250_rep0.json traces/Y250_rep1.json traces/Y251_rep0.json traces/Y251_rep1.json traces/Y252_rep0.json 
traces/Y252_rep1.json traces/Y255_rep0.json traces/Y255_rep1.json traces/Y258_rep0.json traces/Y258_rep1.json traces/Y263_rep0.json traces/Y263_rep1.json traces/Y265_rep0.json traces/Y265_rep1.json 
traces/Y266_rep0.json traces/Y266_rep1.json traces/Y270_rep0.json traces/Y270_rep1.json traces/Y273_rep0.json traces/Y273_rep1.json traces/Y277_rep0.json traces/Y277_rep1.json traces/Y282_rep0.json 
traces/Y282_rep1.json traces/Y290_rep0.json traces/Y290_rep1.json traces/Y292_rep0.json traces/Y292_rep1.json traces/Y293_rep0.json traces/Y293_rep1.json traces/Y303_rep0.json traces/Y303_rep1.json 
traces/Y304_rep0.json traces/Y304_rep1.json traces/Y309_rep0.json traces/Y309_rep1.json traces/Y312_rep0.json traces/Y312_rep1.json traces/Y315_rep0.json traces/Y315_rep1.json traces/Y318_rep0.json 
traces/Y318_rep1.json traces/Y323_rep0.json traces/Y323_rep1.json traces/Y327_rep0.json traces/Y327_rep1.json traces/Y331_rep0.json traces/Y331_rep1.json traces/Y333_rep0.json traces/Y333_rep1.json 
traces/Y334_rep0.json traces/Y334_rep1.json traces/Y338_rep0.json traces/Y338_rep1.json traces/Y342_rep0.json traces/Y342_rep1.json traces/Y343_rep0.json traces/Y343_rep1.json traces/Y344_rep0.json 
traces/Y344_rep1.json traces/Y346_rep0.json traces/Y346_rep1.json traces/Y354_rep0.json traces/Y354_rep1.json traces/Y356_rep0.json traces/Y356_rep1.json traces/Y358_rep0.json traces/Y358_rep1.json 
traces/Y360_rep0.json traces/Y360_rep1.json traces/Y362_rep0.json traces/Y362_rep1.json traces/Y364_rep0.json traces/Y364_rep1.json traces/Y365_rep0.json traces/Y365_rep1.json traces/Y371_rep0.json 
traces/Y371_rep1.json traces/Y380_rep0.json traces/Y380_rep1.json traces/Y383_rep0.json traces/Y383_rep1.json traces/Y385_rep0.json traces/Y385_rep1.json traces/Y386_rep0.json traces/Y386_rep1.json 
traces/Y389_rep0.json traces/Y389_rep1.json traces/Y396_rep0.json traces/Y396_rep1.json traces/Y400_rep0.json traces/Y400_rep1.json
```
