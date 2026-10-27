Make the refund limit (policy rule 4) gate every refund, including the rule-3 out-of-stock fallback: the instructions now say to look for an overriding rule after reaching an outcome, the refund action says it is only for totals within the limit, and the escalate action names over-limit refunds as a trigger but not over-limit reships or replies.

## Behavior

When an order never arrived (rule 3) and the item is out of stock, Jev follows rule 3 to its fallback ("otherwise refund it") and stops there. It never applies rule 4 ("Any refund over $500 must be escalated instead of refunded"), so it refunds orders of $501 and $899 that should be escalated. Jev usually does this with high confidence (0.84 to 0.99). That suggests a reasoning gap, not a close call between two actions: Jev treats rule 4 as a separate rule for some other ticket type, not as an override on the outcome of rule 3.

Jev does apply rule 4 when the refund comes from rule 2 (damaged or wrong item). For example, Y081, Y025, Y012, Y166 and Y206 all escalate correctly. The gap is specific to the case where a refund is the fallback of another rule.

## Size and cost

- Cases showing it: 10 of 120 train cases (Y013, Y050, Y054, Y083, Y119, Y124, Y192, Y343, Y346, Y385).
- Rows: 19 of 240. Every rep of these cases chose refund, except Y119 rep1, which chose reply and passed.
- All 19 rows fail. Baseline is 201/240 = 83.75% pass, so a full fix is worth at most +19 rows = +7.9 points on train.
- This is the largest single failure mode: 19 of the 39 failing rows.
- +7.9 is above the ±6.5 noise floor, but only just. Even a perfect fix of this behavior will only barely be detectable on test.

Every case in train that takes this path with a total ≤ $500 refunds and passes (Y024, Y290, Y312, Y323, Y371, 10/10 rows). Every case that takes it with a total > $500 refunds and fails. The order total alone separates pass from fail.

Related, but not counted: Y027 ($501, Shipped 35 days, not delivered, stock 0, "wrong item" claim) picks reply in both reps and fails. Its policy outcome is also refund over the limit, so escalate is the right answer. The change may help it, but Jev is making a different mistake there (reply, not refund), so I leave it out of the ceiling.

## Evidence

Policy text, identical in every trace (for example traces/Y050_rep0.json):
> `3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.`
> `4. Any refund over $500 must be escalated instead of refunded.`

Current action list sent to Jev (traces/Y050_rep0.json):
> `Actions:\n0. refund: refund the order\n1. reship: send a replacement\n2. escalate: hand the ticket to a supervisor\n3. reply: reply to the customer and take no other action`

Failing rows (Lost or shipped more than 14 days ago, stock 0, total > $500, refund chosen):

traces/Y050_rep0.json
> `\"ticket\": \"Hi, just checking on order #5050. No rush on the projector.\"`
> `\"total\": 899.0` / `\"status\": \"Lost\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.99)"`

traces/Y124_rep1.json
> `\"ticket\": \"Order #5124: the projector tracking says 'exception' and nothing since.\"`
> `\"total\": 899.0` / `\"status\": \"Lost\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.99)"`

traces/Y385_rep0.json
> `\"ticket\": \"Can you check on order #5385 (projector)? Ship me another one.\"`
> `\"total\": 899.0` / `\"status\": \"Lost\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.99)"`

traces/Y346_rep0.json
> `\"ticket\": \"Where is order #5346? I ordered the gaming chair.\"`
> `\"total\": 501.0` / `\"status\": \"Lost\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.97)"`

traces/Y013_rep1.json
> `\"ticket\": \"Tracking for order #5013 (gaming chair) hasn't moved in a while.\"`
> `\"total\": 501.0` / `\"status\": \"Lost\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.97)"`

traces/Y192_rep0.json
> `\"ticket\": \"Order #5192: the gaming chair tracking says 'exception' and nothing since.\"`
> `\"total\": 501.0` / `\"status\": \"Lost\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.87)"`

traces/Y083_rep0.json. The customer even asks for escalation, and Jev still refunds:
> `\"ticket\": \"My projector from order #5083 never came. Escalate this to a manager.\"`
> `\"total\": 899.0` / `\"status\": \"Lost\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.87)"`

traces/Y343_rep0.json. Shipped, not Lost: shipped 2026-08-28, today 2026-10-01, so 34 days:
> `\"ticket\": \"Why can't anyone tell me where order #5343 is? I want my projector.\"`
> `\"total\": 899.0` / `\"status\": \"Shipped\"` / `\"shipped_on\": \"2026-08-28\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.87)"`

traces/Y054_rep1.json. Shipped 2026-09-15, so 16 days:
> `\"ticket\": \"My projector from order #5054 never came.\"`
> `\"total\": 899.0` / `\"status\": \"Shipped\"` / `\"shipped_on\": \"2026-09-15\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.76)"`

traces/Y119_rep0.json (fail) and traces/Y119_rep1.json (pass), same input:
> `\"total\": 899.0` / `\"status\": \"Shipped\"` / `\"shipped_on\": \"2026-09-07\"` / `\"stock\": 0`
> rep0: `"content": "refund (confidence 0.29)"`; rep1: `"content": "reply (confidence 0.31)"`

Contrast 1: same rule-3 refund path, total ≤ $500, passes.

traces/Y312_rep0.json (pass)
> `\"ticket\": \"Why can't anyone tell me where order #5312 is? I want my bluetooth earbuds.\"`
> `\"total\": 79.0` / `\"status\": \"Lost\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.99)"`

traces/Y371_rep0.json (pass)
> `\"total\": 159.0` / `\"status\": \"Shipped\"` / `\"shipped_on\": \"2026-09-15\"` / `\"stock\": 0`
> `"content": "refund (confidence 0.73)"`

Contrast 2: rule-2 refund, total > $500. Jev applies rule 4 correctly here.

traces/Y081_rep0.json (pass)
> `\"ticket\": \"Order #5081: the gaming chair is broken. Refund me.\"`
> `\"total\": 501.0` / `\"status\": \"Delivered\"` / `\"delivered_on\": \"2026-09-04\"`
> `"content": "escalate (confidence 0.81)"`

traces/Y025_rep0.json (pass)
> `\"total\": 501.0` / `\"status\": \"Delivered\"` / `\"delivered_on\": \"2026-09-01\"`
> `"content": "escalate (confidence 0.88)"`

Contrast 3: rule 3 with the item in stock and total > $500. The right answer is reship, and the change must not push this to escalate.

traces/Y112_rep0.json (pass)
> `\"ticket\": \"My home theater soundbar from order #5112 never came. Escalate this to a manager.\"`
> `\"total\": 649.0` / `\"status\": \"Lost\"` / `\"stock\": 6`
> `"content": "reship (confidence 0.89)"`

## The change

The current artifact has no account of how the rules interact. The instruction is one generic sentence, and the action descriptions are bare labels. So the change works on the root cause: it adds the missing step (check for an overriding rule once an outcome is reached) and puts the gate on the action it governs. Three parts, all aimed at this one behavior:

1. `decision_instructions`: follow the matching rule to its outcome, including its fallback. Then check whether another rule overrides that outcome. The refund limit applies to every refund, whichever rule produced it.
2. `criteria["0"]` (refund): only when the total is within the refund limit. A total exactly at the limit is not over it. This protects the $500 refunds that pass now. Over the limit, choose escalate, and this explicitly covers the out-of-stock fallback for an order that never arrived.
3. `criteria["2"]` (escalate): an over-limit refund is a trigger. An over-limit reship or reply is not.

The text refers to "the policy's refund limit", not the dollar figure, and uses no product or ticket wording from train. It should therefore carry over to held-out tickets and to a policy whose threshold differs.

## Cases I expect might regress

- **Orders of exactly $500 that are correctly refunded**: Y017, Y138, Y315 (pass now). Risk: Jev reads "$500" as over the limit and escalates. Part 2 says a total exactly at the limit is not over it, to guard against this.
- **Totals over $500 where the right answer is reship**: Y026, Y031, Y112, Y123, Y237, Y243, Y244, Y383. Risk: the stronger emphasis on the limit spills into escalating every high-value order. Part 3 rules this out, but it is the most likely regression.
- **Totals over $500 where the right answer is reply** (Processing orders, change of mind, shipped 14 days ago or less): Y063, Y085, Y110, Y118, Y200, Y209, Y270, Y273, Y303, Y334, Y342, Y386. These carry the same spill-over risk.
- **Y007** (0.50 now). Rep0 passed with `"escalate (confidence 0.39)"` and rep1 failed with `"refund (confidence 0.36)"` on a $79 order the customer asked to escalate. If the escalate description pulls Jev away from escalating on customer demand, rep0 could flip. The description does not say "only", so I expect little effect.
- **Y119 rep1** passes with reply. If it moves to escalate, I expect it to still pass, since escalate is what the policy calls for. Low risk.

## Files read

- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient/v1/BRIEF.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient/v1/artifact.json
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient/v1/history.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient/v1/scores_train.tsv
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient/v1/results_train.jsonl
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient/v1/traces/ (all 240 files, `<case>_rep0.json` and `<case>_rep1.json` for every train case listed in scores_train.tsv, read by script)
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient/v1/out/_table.txt (a scratch summary I generated from the traces, since deleted)
