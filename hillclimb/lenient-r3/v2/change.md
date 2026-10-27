Rewrite the refund and escalate descriptions as complete condition lists, so an undelivered order that is Lost or shipped more than 14 days ago, has stock 0 and a total over $500 matches escalate, and refund only matches totals of $500 or less.

## Behavior

When a customer says an order never arrived or asks where it is, the order is Lost or shipped more than 14 days ago without being delivered, and stock is 0, policy rule 3 says refund. Rule 4 then turns any refund over $500 into escalate. Jev stops after rule 3 and picks refund. The over-$500 step is never applied on this path.

The rule-4 step only fails on this path. When rule 2 (damaged or wrong item, delivered 30 days ago or less) produces a refund over $500, Jev escalates every time: 12 cases, 24 of 24 rows escalate and pass (Y025, Y081, Y116, Y131, Y166, Y180, Y206, Y231, Y251, Y255, Y265, Y292). Rule 2 names escalate itself, so escalate is already in play there. On rule 3 the chain is reship, then refund, then rule 4 escalate, and Jev stops one step short.

The current action descriptions have nothing that ties a state to an action ("refund: refund the order", "escalate: hand the ticket to a supervisor"). So the refund description matches whatever rule 3 produced, and the escalate description has nothing for the over-limit state to match.

## How many cases and what it costs

- 10 train cases show it: Y013, Y050, Y054, Y083, Y119, Y124, Y192, Y343, Y346, Y385. That is 20 rows. Jev picks refund on 19 and all 19 fail. The other row (Y119 rep1) picked reply at confidence 0.31 and passed.
- Every refund Jev picked on an order over $500 in train failed: 19 of 19 rows, all from these 10 cases.
- Cost: 19 rows of 240, or 7.9 points of train `pass` (baseline is 201/240 = 83.75%). A full fix gains at most that. It clears the 6.5-point noise floor, but not by much, so any regression eats into it directly.
- Not counted: Y027 (Shipped 35 days ago, not delivered, stock 0, total $501, ticket reports a wrong item and asks for a supervisor). Jev replied and failed on both reps. The ticket reports a wrong item and does not say the order never arrived, so the new conditions do not clearly cover it. I expect it to stay as it is.

v1 targeted this same behavior and was reverted. Per scores_train.tsv, v1 left Y013, Y050, Y054, Y083, Y124, Y192, Y343 and Y346 at 0.00 and fixed only Y385. So telling Jev to "check each refund against the limit" did not move it. This change uses a different lever. It does not ask Jev to run a check after choosing refund. Instead, the escalate description states the target state directly (not arrived + Lost or stale + stock 0 + over $500), and the refund description is limited to totals of $500 or less. That way the target state matches escalate in one step and stops matching refund. The decision instructions and the reship and reply descriptions stay as they are, to limit the drift v1 caused on low-confidence reply rows.

## Evidence

The policy text is the same in every trace, for example traces/Y050_rep0.json:

> `3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.\\n4. Any refund over $500 must be escalated instead of refunded.`

The action list Jev sees, traces/Y050_rep0.json:

> `"content": "Which action does the support policy call for on this ticket?\n\nActions:\n0. refund: refund the order\n1. reship: send a replacement\n2. escalate: hand the ticket to a supervisor\n3. reply: reply to the customer and take no other action"`

### Failing: rule-3 refund over $500, picked refund (fail)

traces/Y050_rep0.json
> `\"ticket\": \"Hi, just checking on order #5050. No rush on the projector.\"`
> `\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-08-29\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> `"content": "refund (confidence 0.99)"`

traces/Y013_rep1.json
> `\"ticket\": \"Tracking for order #5013 (gaming chair) hasn't moved in a while.\"`
> `\"total\": 501.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-08-29\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> `"content": "refund (confidence 0.97)"`

traces/Y124_rep0.json
> `\"ticket\": \"Order #5124: the projector tracking says 'exception' and nothing since.\"`
> `\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-16\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> `"content": "refund (confidence 0.99)"`

traces/Y346_rep0.json
> `\"ticket\": \"Where is order #5346? I ordered the gaming chair.\"`
> `\"total\": 501.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-17\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> `"content": "refund (confidence 0.97)"`

traces/Y192_rep0.json
> `\"ticket\": \"Order #5192: the gaming chair tracking says 'exception' and nothing since.\"`
> `\"total\": 501.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-16\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> `"content": "refund (confidence 0.87)"`

The customer explicitly asked for escalation, and Jev still picked refund. traces/Y083_rep0.json
> `\"ticket\": \"My projector from order #5083 never came. Escalate this to a manager.\"`
> `\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-26\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> `"content": "refund (confidence 0.87)"`

traces/Y385_rep0.json
> `\"ticket\": \"Can you check on order #5385 (projector)? Ship me another one.\"`
> `\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-23\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> `"content": "refund (confidence 0.99)"`

Shipped, not Lost, more than 14 days ago. traces/Y343_rep1.json
> `\"ticket\": \"Why can't anyone tell me where order #5343 is? I want my projector.\"`
> `\"total\": 899.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-08-28\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> `"content": "refund (confidence 0.84)"`

traces/Y054_rep1.json
> `\"ticket\": \"My projector from order #5054 never came.\"`
> `\"total\": 899.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-15\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> `"content": "refund (confidence 0.76)"`

traces/Y119_rep0.json (fail) and traces/Y119_rep1.json (pass)
> `\"ticket\": \"Order #5119, the projector. Just making sure it's on the way.\"`
> `\"total\": 899.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-07\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> rep0: `"content": "refund (confidence 0.29)"`
> rep1: `"content": "reply (confidence 0.31)"`

### Contrast: best-doing cases on the same rules (all pass)

Rule-2 refund over $500, escalated correctly. traces/Y081_rep0.json
> `\"ticket\": \"Order #5081: the gaming chair is broken. Refund me.\"`
> `\"total\": 501.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-31\",\n  \"delivered_on\": \"2026-09-04\"\n },\n \"stock\": 0\n`
> `"content": "escalate (confidence 0.81)"`

traces/Y292_rep0.json
> `\"ticket\": \"Order #5292: the label says projector but the box has a phone case in it.\"`
> `\"total\": 899.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-09-05\",\n  \"delivered_on\": \"2026-09-10\"\n },\n \"stock\": 0\n`
> `"content": "escalate (confidence 0.77)"`

Rule-3 refund under the limit, correct (5 cases, 10 of 10 rows pass: Y024, Y290, Y312, Y323, Y371). traces/Y323_rep0.json
> `\"ticket\": \"Can you check on order #5323 (ergonomic keyboard)?\"`
> `\"total\": 159.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-22\",\n  \"delivered_on\": null\n },\n \"stock\": 0\n`
> `"content": "refund (confidence 0.99)"`

Rule-3 reship with stock above 0 and total over $500 is correct, because the limit only applies to refunds. traces/Y383_rep0.json
> `\"ticket\": \"Order #5383 (home theater soundbar) hasn't arrived.\"`
> `\"total\": 649.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-08-28\",\n  \"delivered_on\": null\n },\n \"stock\": 6\n`
> `"content": "reship (confidence 1.0)"`

## The change

Only `criteria["0"]` (refund) and `criteria["2"]` (escalate) change. The decision instructions and the reship and reply descriptions stay word-for-word the same. The refund description gets an explicit `$500 or less` condition on both of its policy paths. The escalate description lists all three states that call for it, with the rule-3 over-$500 out-of-stock state written out in full. Both descriptions name the order status (Lost, Shipped, Delivered) and compare dates to today. That keeps them from matching Delivered orders where the customer asks where the order is, and recent shipments.

The new text has no product names or ticket wording. It restates the policy's own conditions and thresholds ($500, 14 days, 30 days). Those are identical in all 240 train traces, and the policy is fixed for this loop.

## Cases I expect to regress

These are passing rows whose state partly matches the new refund or escalate conditions. Several are low-confidence reply picks of the kind v1 flipped (v1 dropped Y030, Y273, Y327, Y344, Y362 and Y007).

- Y030 (traces/Y030_rep0.json `"content": "reply (confidence 0.33)"`, Delivered, stock 0, $249, "Where is order #5030?") and Y362 (traces/Y362_rep0.json `"content": "reply (confidence 0.25)"`, Delivered, stock 0, $189, "Can you check on order #5362 (countertop oven)? Refund me."). The new refund condition (a) mentions "asks where it is" and "stock is 0". Jev may match on those words and skip the status requirement. Up to 4 rows.
- Y273 (traces/Y273_rep0.json `"content": "reply (confidence 0.61)"`, rep1 `0.37`, Shipped 12 days ago, stock 0, $899). This state matches every part of escalate (a) except the over-14-days condition. Up to 2 rows.
- Y007 (traces/Y007_rep0.json `"content": "escalate (confidence 0.39)"` passes, traces/Y007_rep1.json `"content": "refund (confidence 0.36)"` fails, Delivered 28 days ago, $79, damaged, customer asks for escalation). The new refund (b) matches it exactly, and the judge failed refund here. Up to 1 row.
- Y138, Y179, Y318 (damaged or wrong item delivered 31 to 33 days ago; Jev picks refund and passes, for example traces/Y138_rep0.json `"content": "refund (confidence 0.55)"`). The new escalate (c) matches them, and escalate is what the policy calls for. They should still pass, but a judge that accepted refund here is a lenient judge, so this is not certain. Up to 6 rows.
- Y327 and Y344 rep0 (low-confidence reply passes; stock above 0, so neither new condition fits). Lower risk.

Possible incidental recovery: Y039 (Delivered 30 days ago, $159, damaged; escalate fails on both reps). The new refund (b) matches it.

## Files read

All paths are under /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r3/v2/.

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- My own scratch files in out/: out/oracle.py, out/expect.py, out/table_sim.py, out/rows.json, out/rows2.json, out/table.txt, out/byintent.txt
- Every trace in traces/ (240 files, parsed by script; the ones quoted above were also read directly):
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
