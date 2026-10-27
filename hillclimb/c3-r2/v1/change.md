Make the rule 4 refund-limit check an explicit last step for every refund outcome (including rule 3's out-of-stock fallback) in the instructions and in the refund and escalate action descriptions, and say that the limit never converts reship or reply.

## Behavior

When rule 3 (never arrived / Lost) sends an order to its out-of-stock fallback ("otherwise refund it") and the order total is over $500, Jev picks `refund` and stops. It does not apply rule 4 ("Any refund over $500 must be escalated instead of refunded"), so the correct answer, `escalate`, is never chosen. Jev does apply rule 4 when the refund comes from rule 2 (damaged or wrong item within 30 days). The gap is specific to refunds reached through rule 3's fallback branch. The current artifact gives no ordering between rules, and the `refund` description ("refund the order") has no limit attached. So the first rule that yields an action wins.

## How many cases, how much it costs

- 9 train cases show it: Y013, Y050, Y054, Y083, Y124, Y192, Y343, Y346, Y385.
- All 18 of their 18 rows fail, every one with `refund`, at confidence 0.67 to 0.99. This is a systematic error, not run-to-run noise.
- Cost: 18 of 240 train rows = 7.5 points of `pass` (baseline train pass is 187/240 = 77.9%). A full fix tops out near 85.4%.
- This is the largest single coherent failure behavior in the train set. A full fix (7.5 points) clears the ±6.5 noise floor, but only narrowly. If the test split holds a smaller share of over-limit, out-of-stock, never-arrived orders, the real gain could land inside the floor.

Other failure groups, considered and not chosen:
- Undelivered orders on the wrong side of the 14-day line: reship at 12 to 14 days in Y114, Y258, Y282, Y304, and reply after more than 14 days in Y063, Y089, Y144, Y396, Y119 rep1, Y027. That is 19 rows, but they split into two opposite directions with different triggers. Fixing them would also need date arithmetic that Jev shows no sign of doing, since it emits no reasoning tokens. Each direction alone is 8 to 11 rows, which is inside the noise floor.
- Delivered just past 30 days but refunded (Y138, Y179, Y318): 6 rows. Escalating a request the customer made when the policy says refund (Y007 rep0, Y039): 3 rows. Both are inside the noise floor.

## Evidence

The policy text and the system prompt are identical in all 240 traces. From `traces/Y050_rep0.json`:

```
3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.\\n4. Any refund over $500 must be escalated instead of refunded.\
```
```
"content": "Which action does the support policy call for on this ticket?\n\nActions:\n0. refund: refund the order\n1. reship: send a replacement\n2. escalate: hand the ticket to a supervisor\n3. reply: reply to the customer and take no other action"
```

Failing traces. Each one is out of stock, over $500, and goes down rule 3's refund branch, and each one answers `refund`:

`traces/Y050_rep0.json`
```
\"ticket\": \"Hi, just checking on order #5050. No rush on the projector.\",
\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-08-29\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.99)"
```
Grader (results_train.jsonl, Y050 rep 0): "Stock is 0, so refund is correct. However, the total is $899.0, which exceeds the $500 limit for refunds, so the policy requires escalation instead."

`traces/Y013_rep0.json`
```
\"ticket\": \"Tracking for order #5013 (gaming chair) hasn't moved in a while.\",
\"total\": 501.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-08-29\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.91)"
```

`traces/Y054_rep1.json` (status Shipped, more than 14 days, not delivered)
```
\"ticket\": \"My projector from order #5054 never came.\",
\"total\": 899.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-15\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.76)"
```

`traces/Y343_rep0.json`
```
\"ticket\": \"Why can't anyone tell me where order #5343 is? I want my projector.\",
\"total\": 899.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-08-28\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.87)"
```

`traces/Y346_rep0.json`
```
\"ticket\": \"Where is order #5346? I ordered the gaming chair.\",
\"total\": 501.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-17\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.97)"
```

`traces/Y083_rep0.json` (the customer even asks for escalation, and Jev still refunds)
```
\"ticket\": \"My projector from order #5083 never came. Escalate this to a manager.\",
\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-26\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.87)"
```

`traces/Y124_rep1.json`
```
\"ticket\": \"Order #5124: the projector tracking says 'exception' and nothing since.\",
\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-16\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.99)"
```

`traces/Y192_rep0.json`
```
\"ticket\": \"Order #5192: the gaming chair tracking says 'exception' and nothing since.\",
\"total\": 501.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-16\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.87)"
```

`traces/Y385_rep1.json`
```
\"ticket\": \"Can you check on order #5385 (projector)? Ship me another one.\",
\"total\": 899.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-23\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.99)"
```

Contrast 1: the same $501 total reached through rule 2 is escalated correctly, so Jev can do the comparison. It just does not do it after rule 3.

`traces/Y081_rep0.json` (pass)
```
\"ticket\": \"Order #5081: the gaming chair is broken. Refund me.\",
\"total\": 501.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-31\",\n  \"delivered_on\": \"2026-09-04\"\n },\n \"stock\": 0
"content": "escalate (confidence 0.81)"
```
`traces/Y116_rep0.json` (pass)
```
\"ticket\": \"My gaming chair (order #5116) has a cracked housing and doesn't work. Ship me another one.\",
\"total\": 501.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-09-02\",\n  \"delivered_on\": \"2026-09-04\"\n },\n \"stock\": 0
"content": "escalate (confidence 0.65)"
```

Contrast 2: the same rule 3 fallback under the limit passes with refund. The fix must keep these as refund.

`traces/Y290_rep0.json` (pass)
```
\"ticket\": \"My bluetooth earbuds from order #5290 never came. I want a full refund.\",
\"total\": 79.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-17\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 1.0)"
```
`traces/Y323_rep0.json` (pass)
```
\"ticket\": \"Can you check on order #5323 (ergonomic keyboard)?\",
\"total\": 159.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-22\",\n  \"delivered_on\": null\n },\n \"stock\": 0
"content": "refund (confidence 0.99)"
```

Contrast 3: over $500 but in stock, so the correct answer is reship. The limit must not touch these.

`traces/Y031_rep0.json` (pass)
```
\"ticket\": \"Order #5031 (robot vacuum) hasn't arrived.\",
\"total\": 549.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-15\",\n  \"delivered_on\": null\n },\n \"stock\": 2
"content": "reship (confidence 0.92)"
```
`traces/Y383_rep0.json` (pass)
```
\"ticket\": \"Order #5383 (home theater soundbar) hasn't arrived.\",
\"total\": 649.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-08-28\",\n  \"delivered_on\": null\n },\n \"stock\": 6
"content": "reship (confidence 1.0)"
```

## The change

One behavior, three places:

1. `decision_instructions`: keep the question, and add a fixed last step. Find the action the matching rule gives. If it is refund, compare the total to the rule 4 limit and switch to escalate when the total is over it. Name rule 3's out-of-stock fallback explicitly as a refund path, because that is the branch Jev skips. Add two guard clauses so the step cannot overreach: the limit only converts refunds (never reship or reply), and a total equal to the limit is not over it.
2. `criteria["0"]` (refund): attach the limit condition to the action itself, so the option Jev is about to pick carries the constraint.
3. `criteria["2"]` (escalate): name over-limit refunds as part of escalate's scope, so the alternative is visible at selection time.

The descriptions in `criteria` are a different lever from the instructions. Jev picks among option texts, and today the refund option says nothing about a limit. Everything is stated in terms of the policy's own rule structure (rule 4, the refund limit, the out-of-stock fallback). No product names, ticket phrases, or dollar figures from train cases are added.

## Cases I expect to regress (or to watch)

- Y119 (rep0 currently passes with refund). It is $899, shipped 24 days ago, not delivered, out of stock. By the policy the answer is escalate, but the grader passed `refund` on rep 0 ("so the required action is refund"). If the change works, Jev should answer escalate here, and this grader may fail it. Expect Y119 to drop from 0.5 to as low as 0.0 from grader inconsistency, not a model error.
- Over-$500 reship cases that pass today: Y026, Y031, Y112, Y123, Y237, Y243, Y244, Y383. Over-reach would flip them to escalate. Y112 is the most exposed ($649, and the ticket asks to escalate), and so are Y123 and Y244 (reship confidence 0.56 to 0.8). The "never turns a reship ... into escalate" clause is there to protect them.
- Over-$500 reply cases that pass today, especially low-confidence ones: Y273 ($899, out of stock, 12 days, reply at 0.61 and 0.37) and Y270 ($549, reply at 0.56 and 0.6). Also Y209 and Y342, where the order is still Processing and the customer demands escalation. The "or a reply" clause guards these.
- Exactly-$500 refunds that pass: Y084 and Y315. The "equal to the limit is not over it" clause keeps them as refund. Y017 ($500, refund) will keep failing because the grader there treats $500 as over the limit, the opposite of its own Y084 and Y315 verdicts. This change does not chase it.
- Under-limit rule 3 refunds (Y024, Y290, Y312, Y323, Y371) should be unaffected. If any of them flips to escalate, the instruction is being read as "out of stock means escalate", and the reverter should note that.

Possible bonus, not counted: Y027 ($501, out of stock, undelivered after 35 days, grader wants escalate) currently answers reply. That is a routing miss as well as the limit, so I do not count it.

## Files read

All paths are relative to /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3-r2/v1/

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- out/_evidence.txt (my own scratch: verbatim excerpts extracted from the traces quoted above)
- out/_tracelist.txt (my own scratch: listing of traces/)
- every trace file in traces/ (all 240, read programmatically to tabulate action, order, stock and dates per row):
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
