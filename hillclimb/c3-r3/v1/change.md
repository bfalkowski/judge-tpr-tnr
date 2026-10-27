Make the $500 refund cap (rule 4) explicitly cover the out-of-stock refund for lost/undelivered orders (rule 3), in the instructions and in the refund/escalate action descriptions, while saying the cap does not touch reship or reply.

## Behavior

When an order is lost or undelivered past 14 days, the item is out of stock, and the order total is over $500, Jev picks `refund` and stops there. It does not apply rule 4 ("Any refund over $500 must be escalated instead of refunded."), so it never picks `escalate`. It does this with high confidence (0.67 to 0.99). The same model does apply rule 4 when the refund comes from rule 2 (damaged or wrong item on a delivered order). Every delivered order over $500 inside the 30-day window is escalated and passes. So the cap is being read as attached to rule 2 only. Nothing in the current artifact links "refund" to the cap: the refund description is just "refund the order", and the escalate description is just "hand the ticket to a supervisor".

## Size and cost

- 9 train cases show it: Y013, Y050, Y054, Y083, Y124, Y192, Y343, Y346, Y385. That is 18 of 18 rows, all `refund`, all graded Fail. The judge's reasoning is the same every time: refund is right under rule 3, "However, the refund ... exceeds the $500 limit, so the policy requires escalation instead of refund."
- Cost: 18 of 240 train rows, which is 7.5 points of `pass`. The baseline is 187/240 = 77.9%. A full fix gives 205/240 = 85.4% at most.
- That is just above the plus or minus 6.5 point noise floor, so the margin is thin. One possible extra: Y027 (2 rows, picks `reply`). It is an undelivered, out-of-stock $501 order where the judge wants escalate through the same rule 3 then rule 4 chain. Its main error is not reaching rule 3 at all, so I do not count it.
- This is the largest failure group with a single cause and a single direction. The other failures split into smaller groups that pull in opposite directions. Errors on the 14-day undelivered threshold: Y114, Y258, Y282 and Y304 reship too early (8 rows), while Y063, Y089, Y144 and Y396 reply too late (8 rows). Errors on the 30-day delivered threshold: Y007, Y039, Y138, Y179, Y318, Y194, Y338 and Y344, about 13 rows going both ways.

## Evidence

All quotes are verbatim from the trace files. The user message is a JSON string, so its quotes appear escaped.

The system message every trace gets (same in all 240). Nothing in it ties refund to a cap:
traces/Y050_rep0.json
```
"content": "Which action does the support policy call for on this ticket?\n\nActions:\n0. refund: refund the order\n1. reship: send a replacement\n2. escalate: hand the ticket to a supervisor\n3. reply: reply to the customer and take no other action"
```
The policy in the state contains the rule the model skips:
```
4. Any refund over $500 must be escalated instead of refunded.
```

Failing: lost, out of stock, over $500, refund picked:

traces/Y050_rep0.json
```
\"ticket\": \"Hi, just checking on order #5050. No rush on the projector.\"
\"total\": 899.0
\"status\": \"Lost\"
\"delivered_on\": null
\"stock\": 0
"content": "refund (confidence 0.99)"
```
traces/Y124_rep1.json
```
\"ticket\": \"Order #5124: the projector tracking says 'exception' and nothing since.\"
\"total\": 899.0
\"status\": \"Lost\"
\"stock\": 0
"content": "refund (confidence 0.99)"
```
traces/Y346_rep0.json (just over the cap)
```
\"ticket\": \"Where is order #5346? I ordered the gaming chair.\"
\"total\": 501.0
\"status\": \"Lost\"
\"stock\": 0
"content": "refund (confidence 0.97)"
```
traces/Y192_rep0.json
```
\"ticket\": \"Order #5192: the gaming chair tracking says 'exception' and nothing since.\"
\"total\": 501.0
\"status\": \"Lost\"
\"stock\": 0
"content": "refund (confidence 0.87)"
```
traces/Y083_rep0.json (the customer even asks for escalation, and it still refunds)
```
\"ticket\": \"My projector from order #5083 never came. Escalate this to a manager.\"
\"total\": 899.0
\"status\": \"Lost\"
\"stock\": 0
"content": "refund (confidence 0.87)"
```

Failing: shipped, not delivered, more than 14 days, out of stock, over $500, refund picked:

traces/Y054_rep0.json (shipped 2026-09-15, 16 days)
```
\"ticket\": \"My projector from order #5054 never came.\"
\"total\": 899.0
\"status\": \"Shipped\"
\"shipped_on\": \"2026-09-15\"
\"delivered_on\": null
\"stock\": 0
"content": "refund (confidence 0.67)"
```
traces/Y343_rep1.json (shipped 2026-08-28, 34 days)
```
\"ticket\": \"Why can't anyone tell me where order #5343 is? I want my projector.\"
\"total\": 899.0
\"status\": \"Shipped\"
\"shipped_on\": \"2026-08-28\"
\"stock\": 0
"content": "refund (confidence 0.84)"
```

Best cases, for contrast. These pass 2/2.

The model applies the cap correctly when the refund comes from rule 2 (delivered, damaged or wrong item, within 30 days):
traces/Y081_rep0.json
```
\"ticket\": \"Order #5081: the gaming chair is broken. Refund me.\"
\"total\": 501.0
\"status\": \"Delivered\"
\"delivered_on\": \"2026-09-04\"
"content": "escalate (confidence 0.81)"
```
traces/Y265_rep0.json
```
\"ticket\": \"Order #5265 should have been my home theater soundbar, but you sent something else. Refund me.\"
\"total\": 649.0
\"status\": \"Delivered\"
"content": "escalate (confidence 0.87)"
```
The rule 3 branch itself is handled right when the cap does not bite (under $500), or when stock means reship:
traces/Y323_rep0.json
```
\"ticket\": \"Can you check on order #5323 (ergonomic keyboard)?\"
\"total\": 159.0
\"status\": \"Lost\"
\"stock\": 0
"content": "refund (confidence 0.99)"
```
traces/Y383_rep0.json
```
\"ticket\": \"Order #5383 (home theater soundbar) hasn't arrived.\"
\"total\": 649.0
\"status\": \"Lost\"
\"stock\": 6
"content": "reship (confidence 1.0)"
```
So the only missing step is applying rule 4 after a rule 3 refund.

## The change

- `decision_instructions`: add that rule 4 applies to every refund the policy gives, naming the rule 3 out-of-stock refund for lost or undelivered orders. If the matching rule says refund and the total is over $500, choose escalate. Also add that the cap changes only refunds, so reship and reply stand at any total. That last sentence is there to guard the regression cases below.
- `criteria["0"]`: "refund: refund the order, only when the order total is $500 or less". This puts the cap on the action Jev picks, not only in the policy text.
- `criteria["2"]`: "escalate: hand the ticket to a supervisor, including any case where the policy gives a refund and the order total is over $500".
- `criteria["1"]` and `criteria["3"]` are unchanged. Keys and action words are unchanged.

The full artifact is in out/artifact.json.

## Cases I expect to regress

- Y119: rep0 passes today with `refund` (confidence 0.29) on an $899 undelivered, out-of-stock order. In that case the judge did not apply rule 4 ("so the required action is refund"). If the change makes Jev escalate here, which is policy-correct, this judge may fail it. Risk: -1 row. rep1 (`reply`, failing) could flip either way.
- Over-$500 orders where the right answer is reship or reply. They pass today, but the model could over-apply "over $500, escalate". The low-confidence ones are most at risk:
  - Y244 (reship 0.64/0.56)
  - Y270 (reply 0.56/0.60)
  - Y273 (reply 0.61/0.37)
  - Y123 (reship 0.80/0.73)
  - The higher-confidence reship/reply cases over $500 are probably safe: Y026, Y031, Y112, Y237, Y243, Y383, Y061, Y085, Y110, Y118, Y169, Y200, Y209, Y250, Y309, Y334, Y342, Y386.
  - The added sentence "The $500 limit changes only refunds; when the matching rule says reship or reply, choose that at any order total" is aimed at these.
- Refunds at exactly $500 that pass today: Y084 (0.39/0.39) and Y315. The new refund description, "$500 or less", should keep these as refund. I did not add an exact-$500 rule because the judge is inconsistent there: Y017 fails at $500 on "equals the limit and must be escalated", while Y084 and Y315 pass on "exactly $500, not over".
- Small refunds under rule 3 (Y024, Y290, Y312, Y323, Y371): these should hold, because the cap does not apply.

## Files read

All inside /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3-r3/v1/:
- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- out/an.py and out/rows.json (my own scratch files: a per-row table built from the results and traces)
- out/tracelist.txt (my own scratch file: the list of trace files)
- All 240 trace files in traces/. Each one was loaded by script to build the per-row table, and the cited ones were also grepped directly:
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
