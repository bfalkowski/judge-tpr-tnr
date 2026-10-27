Keep the instructions as they are and put the $500 refund limit into the refund and escalate action descriptions: refund is only allowed on orders of $500 or less, and escalate takes over every refund above $500, including rule 3's out-of-stock refund.

## Behavior

When a ticket is about an order that never arrived (rule 3), the order is Lost or shipped more than 14 days ago and still not delivered, and the item is out of stock, Jev picks `refund` even when the order total is over $500. Rule 4 says any refund over $500 must be escalated. Jev applies rule 4 correctly when the refund comes from rule 2 (damaged or wrong item). It skips rule 4 when the refund comes from rule 3's out-of-stock fallback.

## How many cases and how much it costs

Ten train cases show it. Every rule-3, out-of-stock case with a total over $500 is in this group, and none of them passes with `refund`.

- 9 cases fail on both reps, always with `refund`: Y013, Y050, Y054, Y083, Y124, Y192, Y343, Y346, Y385
- 1 case fails on one rep with `refund`: Y119 rep0 (rep1 picked `reply` and passed)

That is 19 of 240 train rows, or 7.9 points of `pass`. A full fix would raise train from 83.75 to about 91.7. This only clears the ±6.5 noise floor if the fix is nearly complete: it has to recover at least 16 of the 19 rows with no regressions.

Y027 (a wrong-item claim on an order that shipped 35 days ago, was never delivered, total $501, stock 0; Jev picked `reply` on both reps) may also be this behavior, since rule 3 leads to refund there and rule 4 then leads to escalate. It is not counted above.

This is the same behavior v1 targeted, so the lever is deliberately different. v1 made the limit a "required second step after any rule gives refund" and put that in the instructions as well as the descriptions. It recovered only Y385. It regressed eight reply-type cases: Y030, Y273, Y362, Y119, Y344, Y327, Y266, Y007. Six of those eight have totals of $500 or less, so the $500 rule did not cause them. More likely, adding a refund step to the instructions pulled "where is my order" and "refund me" tickets toward refund. This change leaves the instructions alone. It does not describe a procedure. It makes refund unavailable above $500, using the order total as the test, and states that the replacement covers the refund from whichever rule produced it.

## Evidence

The same rule 3 and rule 4 text appears in every trace:

> `3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.`
> `4. Any refund over $500 must be escalated instead of refunded.`

Failing cases (rule 3, out of stock, over $500, `refund` picked):

- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y013_rep0.json
  `\"ticket\": \"Tracking for order #5013 (gaming chair) hasn't moved in a while.\"` / `\"total\": 501.0` / `\"status\": \"Lost\"` / `\"stock\": 0` / `"content": "refund (confidence 0.91)"`
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y050_rep0.json
  `\"ticket\": \"Hi, just checking on order #5050. No rush on the projector.\"` / `\"total\": 899.0` / `\"status\": \"Lost\"` / `\"stock\": 0` / `"content": "refund (confidence 0.99)"`
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y054_rep0.json
  `\"ticket\": \"My projector from order #5054 never came.\"` / `\"total\": 899.0` / `\"status\": \"Shipped\"` / `\"shipped_on\": \"2026-09-15\"` / `\"delivered_on\": null` / `\"stock\": 0` / `"content": "refund (confidence 0.67)"`
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y083_rep0.json
  `\"ticket\": \"My projector from order #5083 never came. Escalate this to a manager.\"` / `\"total\": 899.0` / `\"status\": \"Lost\"` / `\"stock\": 0` / `"content": "refund (confidence 0.87)"`
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y124_rep1.json
  `\"ticket\": \"Order #5124: the projector tracking says 'exception' and nothing since.\"` / `\"total\": 899.0` / `\"status\": \"Lost\"` / `\"stock\": 0` / `"content": "refund (confidence 0.99)"`
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y192_rep1.json
  `\"ticket\": \"Order #5192: the gaming chair tracking says 'exception' and nothing since.\"` / `\"total\": 501.0` / `\"status\": \"Lost\"` / `\"stock\": 0` / `"content": "refund (confidence 0.96)"`
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y343_rep0.json
  `\"ticket\": \"Why can't anyone tell me where order #5343 is? I want my projector.\"` / `\"total\": 899.0` / `\"status\": \"Shipped\"` / `\"shipped_on\": \"2026-08-28\"` / `\"stock\": 0` / `"content": "refund (confidence 0.87)"`
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y346_rep0.json
  `\"ticket\": \"Where is order #5346? I ordered the gaming chair.\"` / `\"total\": 501.0` / `\"status\": \"Lost\"` / `\"stock\": 0` / `"content": "refund (confidence 0.97)"`
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y385_rep0.json
  `\"ticket\": \"Can you check on order #5385 (projector)? Ship me another one.\"` / `\"total\": 899.0` / `\"status\": \"Lost\"` / `\"stock\": 0` / `"content": "refund (confidence 0.99)"`
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y119_rep0.json
  `\"ticket\": \"Order #5119, the projector. Just making sure it's on the way.\"` / `\"total\": 899.0` / `\"shipped_on\": \"2026-09-07\"` / `\"stock\": 0` / `"content": "refund (confidence 0.29)"`

Contrast 1: the same rule 3 out-of-stock path at $500 or less passes with `refund`. This shows the stock check works and only the limit is missed.

- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y312_rep0.json
  `\"ticket\": \"Why can't anyone tell me where order #5312 is? I want my bluetooth earbuds.\"` / `\"total\": 79.0` / `\"stock\": 0` / `"content": "refund (confidence 0.99)"` (pass). Compare Y343 above: same ticket wording, total $899, `refund`, fail.
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y323_rep0.json
  `\"ticket\": \"Can you check on order #5323 (ergonomic keyboard)?\"` / `\"total\": 159.0` / `\"status\": \"Lost\"` / `\"stock\": 0` / `"content": "refund (confidence 0.99)"` (pass)

Contrast 2: Jev already applies rule 4 when the refund comes from rule 2.

- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y081_rep0.json
  `\"ticket\": \"Order #5081: the gaming chair is broken. Refund me.\"` / `\"total\": 501.0` / `\"status\": \"Delivered\"` / `"content": "escalate (confidence 0.81)"` (pass; delivered 2026-09-04, inside 30 days)

Contrast 3: a rule 3 case over $500 that is in stock passes with `reship`. The new escalate text must not take these cases.

- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/Y383_rep0.json
  `\"ticket\": \"Order #5383 (home theater soundbar) hasn't arrived.\"` / `\"total\": 649.0` / `\"status\": \"Lost\"` / `\"stock\": 6` / `"content": "reship (confidence 1.0)"` (pass)

## The change

`decision_instructions` is unchanged. Only criteria "0" and "2" change:

- "0": `refund: refund the order. Only for an order whose total is $500 or less. If the policy's outcome is a refund and the order total is over $500, the action is escalate (rule 4), whichever rule produced the refund.`
- "2": `escalate: hand the ticket to a supervisor. Besides the cases the policy sends to a supervisor directly, this replaces every refund over $500, including rule 3's refund for a Lost order, or one shipped more than 14 days ago and not delivered, whose item is out of stock.`

The opening clause "Besides the cases the policy sends to a supervisor directly" is there on purpose. Without it, escalate could read as being only for refunds over $500. That could pull rule-2 escalations of orders delivered more than 30 days ago at $500 or less (Y232, Y354) back to refund.

## Cases I expect could regress

- Y273 (reply, total $899, stock 0, shipped 12 days ago) and Y119 rep1 (reply passed, total $899, stock 0). Both regressed under v1. Both are reply tickets over $500 with stock 0, the state most likely to be pulled to escalate.
- Y017 and Y315 (refund passes, total exactly 500.0). They are at risk if Jev reads "$500 or less" or "over $500" loosely at the boundary.
- Y266 (reply, stock 0, shipped 5 days ago) and the Processing, stock 0, over $500 reply cases (Y110, Y118, Y386). Risk is low, since these are currently at confidence 0.75 to 1.0.
- Rule-3 reship cases over $500 (Y026, Y031, Y112, Y123, Y237, Y243, Y244, Y383) are low risk. The text ties escalate to a refund, not a reship, and none of these moved under v1.

## Files read

- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/BRIEF.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/artifact.json
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/history.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/scores_train.tsv
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/results_train.jsonl
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/traces/*.json. All 240 traces (120 cases × rep0 and rep1) were parsed by script. The ones quoted above were also grepped directly.
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/out/scan.py and /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v2/out/group.py (my own scratch scripts)
