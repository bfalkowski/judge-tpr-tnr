Make escalate selectable outside the numbered rules: the escalate description now covers explicit requests for a supervisor/manager/escalation and tickets that contradict the order record, and the instructions say to check those conditions before applying the rules.

## Behavior

Jev chooses escalate only when a numbered rule's date or price check produces it on a Delivered order. Across all 240 train rows it picked escalate 45 times. Every one of those rows was a Delivered order, and all 45 passed. It never escalated a Processing, Shipped or Lost order, and it never escalated when the order was not Delivered, even if the customer asked for a supervisor. That costs two kinds of ticket:

1. **Explicit escalation request ignored.** The customer asks for a supervisor or manager, or asks for the ticket to be escalated, and Jev applies the rule as if the request weren't there (reply, refund or reship). The judge failed 19 of the 27 rows where this happened. All 3 rows where Jev did escalate on a request passed.
2. **Ticket contradicts the order record, and no numbered rule covers it.** Either the customer says the item never arrived (or asks where it is) but the status is Delivered, or the customer reports a damaged or wrong item but the order has a ship date and no delivery date. Jev picks between reply and reship, often with low confidence, and the judge failed 20 of 22 such rows. Escalate was never tried.

**Size:** 20 cases, 39 failing rows (Y007 1 row; Y027, Y030, Y089, Y112, Y133, Y148, Y194, Y212, Y225, Y263, Y266, Y270, Y303, Y338, Y342, Y344, Y360, Y362, Y396 2 rows each). That is 39 of the 57 failing train rows, or 16.25 points of `pass` (train is 183/240 = 76.25% now). A full fix gains at most 16.25 points, which is well outside the 6.5-point noise floor.

The other 18 failing rows (Y046, Y063, Y119, Y149, Y161, Y169, Y222, Y273, Y293) are cases where Jev mostly followed the literal policy and the judge still failed it, or where rule 4 was missed. They are not addressed here.

## Evidence

All paths are under `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/p2/v1/`. Today in every trace is `Today is 2026-10-01`.

### Explicit escalation request ignored

Same ticket, two reps. Escalate passed and refund failed:

- `traces/Y007_rep0.json` (pass): `\"ticket\": \"The bluetooth earbuds from order #5007 arrived damaged. I want this escalated.\"`, `\"status\": \"Delivered\"`, `\"delivered_on\": \"2026-09-03\"`, `"content": "escalate (confidence 0.39)"`
- `traces/Y007_rep1.json` (fail): same ticket and order, `"content": "refund (confidence 0.36)"`

Processing orders where the request was ignored. All failed:

- `traces/Y148_rep0.json`: `\"ticket\": \"Can you check on order #5148 (bluetooth earbuds)? Escalate this to a manager.\"`, `\"status\": \"Processing\"`, `"content": "reply (confidence 0.99)"`
- `traces/Y212_rep0.json`: `\"ticket\": \"My electric kettle (order #5212) has a cracked housing and doesn't work. Escalate this to a manager.\"`, `\"status\": \"Processing\"`, `"content": "reply (confidence 0.96)"`
- `traces/Y342_rep0.json`: `\"ticket\": \"My home theater soundbar (order #5342) has a cracked housing and doesn't work. Escalate this to a manager.\"`, `\"status\": \"Processing\"`, `"content": "reply (confidence 0.92)"`

Change-of-mind, refund-in-window and Lost orders where the request was ignored. All failed:

- `traces/Y303_rep0.json`: `\"ticket\": \"I don't need the espresso machine from order #5303 anymore. Can I return it? I want this escalated.\"`, `\"status\": \"Delivered\"`, `"content": "reply (confidence 0.93)"`
- `traces/Y360_rep0.json`: `\"ticket\": \"Order #5360: the portable monitor works but I changed my mind. Escalate this to a manager.\"`, `\"status\": \"Delivered\"`, `"content": "reply (confidence 0.97)"`
- `traces/Y225_rep0.json`: `\"ticket\": \"Order #5225 should have been my espresso machine, but you sent something else. Escalate this to a manager.\"`, `\"status\": \"Delivered\"`, `\"delivered_on\": \"2026-09-15\"`, `\"total\": 499.0`, `"content": "refund (confidence 0.75)"`
- `traces/Y112_rep0.json`: `\"ticket\": \"My home theater soundbar from order #5112 never came. Escalate this to a manager.\"`, `\"status\": \"Lost\"`, `\"stock\": 6`, `"content": "reship (confidence 0.89)"`

A Delivered order where the request was honored (pass):

- `traces/Y039_rep0.json`: `\"ticket\": \"My ergonomic keyboard (order #5039) has a cracked housing and doesn't work. Escalate this to a manager.\"`, `\"status\": \"Delivered\"`, `\"delivered_on\": \"2026-09-01\"`, `"content": "escalate (confidence 0.45)"`. Rule 2 alone gives refund here (30 days, $159), and the judge passed escalate anyway.

### Customer says the item hasn't arrived but the status is Delivered

All of these failed. Confidence is low and the choice changes between reps:

- `traces/Y030_rep0.json`: `\"ticket\": \"Where is order #5030? I ordered the document scanner.\"`, `\"status\": \"Delivered\"`, `\"delivered_on\": \"2026-09-03\"`, `"content": "reply (confidence 0.33)"`
- `traces/Y338_rep0.json`: `\"ticket\": \"Order #5338 (espresso machine) hasn't arrived.\"`, `\"status\": \"Delivered\"`, `\"delivered_on\": \"2026-08-30\"`, `"content": "reship (confidence 0.24)"`
- `traces/Y344_rep0.json`: `\"ticket\": \"Why can't anyone tell me where order #5344 is? I want my portable monitor.\"`, `\"status\": \"Delivered\"`, `"content": "reply (confidence 0.49)"`
- `traces/Y344_rep1.json`: same ticket and order, `"content": "reship (confidence 0.31)"`
- `traces/Y194_rep1.json`: `\"ticket\": \"I've been waiting FOREVER for my countertop oven, order #5194.\"`, `\"status\": \"Delivered\"`, `\"delivered_on\": \"2026-08-29\"`, `"content": "reship (confidence 0.43)"`
- `traces/Y362_rep1.json`: `\"ticket\": \"Can you check on order #5362 (countertop oven)? Refund me.\"`, `\"status\": \"Delivered\"`, `"content": "reply (confidence 0.4)"`

### Damaged or wrong item reported on an order with no delivery date

All of these failed:

- `traces/Y089_rep0.json`: `\"ticket\": \"The box for order #5089 was crushed and the espresso machine inside rattles.\"`, `\"status\": \"Shipped\"`, `\"delivered_on\": null`, `"content": "reply (confidence 0.79)"`
- `traces/Y133_rep1.json`: `\"ticket\": \"My earlier order #2619 was fine. Order #5133 has someone else's item, not my espresso machine.\"`, `\"status\": \"Shipped\"`, `\"delivered_on\": null`, `"content": "reship (confidence 0.45)"`
- `traces/Y263_rep0.json`: `\"ticket\": \"Order #5263: the label says air purifier but the box has a phone case in it.\"`, `\"status\": \"Shipped\"`, `\"shipped_on\": \"2026-09-25\"`, `\"delivered_on\": null`, `"content": "reply (confidence 0.84)"`
- `traces/Y266_rep0.json`: `\"ticket\": \"You sent me the WRONG thing for order #5266. Where is my bluetooth earbuds?\"`, `\"status\": \"Shipped\"`, `\"delivered_on\": null`, `"content": "reply (confidence 0.75)"`
- `traces/Y270_rep1.json`: `\"ticket\": \"Order #5270 should have been my robot vacuum, but you sent something else.\"`, `\"status\": \"Shipped\"`, `\"delivered_on\": null`, `"content": "reply (confidence 0.6)"`
- `traces/Y027_rep0.json` (also contains a request): `\"ticket\": \"I received the wrong item on order #5027. It is not the gaming chair I ordered. Get a supervisor on this.\"`, `\"status\": \"Shipped\"`, `\"delivered_on\": null`, `"content": "reply (confidence 0.51)"`
- `traces/Y396_rep0.json` (also contains a request): `\"ticket\": \"My portable monitor (order #5396) has a cracked housing and doesn't work. Escalate this to a manager.\"`, `\"status\": \"Shipped\"`, `\"delivered_on\": null`, `"content": "reply (confidence 0.57)"`

### Best cases, for contrast

When a rule outputs escalate, or the record matches the ticket, Jev is confident and the judge passes it:

- `traces/Y088_rep0.json`: `\"ticket\": \"The projector from order #5088 came yesterday and it's broken.\"`, `\"status\": \"Delivered\"`, `\"delivered_on\": \"2026-08-30\"`, `\"total\": 899.0`, `"content": "escalate (confidence 0.89)"`
- `traces/Y012_rep0.json`: `\"ticket\": \"My robot vacuum (order #5012) has a cracked housing and doesn't work.\"`, `\"status\": \"Delivered\"`, `\"delivered_on\": \"2026-08-21\"`, `"content": "escalate (confidence 0.87)"`
- `traces/Y383_rep0.json`: `\"ticket\": \"Order #5383 (home theater soundbar) hasn't arrived.\"`, `\"status\": \"Lost\"`, `"content": "reship (confidence 1.0)"`
- `traces/Y364_rep0.json`: `\"ticket\": \"Can you check on order #5364 (standing desk mat)?\"`, `\"status\": \"Processing\"`, `"content": "reply (confidence 1.0)"`

The failing groups differ from these in one way: no numbered rule covers them, or the customer asked for something no rule mentions. When that happens, escalate is never a candidate.

## The change

Only `decision_instructions` and `criteria["2"]` change. Keys and action words are unchanged.

- `decision_instructions`: "Choose the action to take on this ticket. Check the escalate conditions in the action list first; if one holds, choose escalate. Otherwise choose the action that the support policy's matching numbered rule gives."
- `criteria["2"]`: "escalate: hand the ticket to a supervisor. Besides the cases where a policy rule says to escalate, choose this when (a) the customer explicitly asks for a supervisor or a manager, or asks for the ticket to be escalated, whatever action the rules would otherwise give; or (b) the ticket contradicts the order record about whether the customer has the item: they report a damaged or wrong item but the order shows a ship date and no delivery date, or they say it has not arrived or ask where it is but the status is Delivered. A Processing order is not a contradiction, and neither is a not-arrived report on an order with no delivery date."

The two exclusions at the end are there to protect cases that pass now: Processing orders with damage or wrong-item complaints that are answered with reply (`traces/Y309_rep0.json`, `traces/Y190_rep0.json`, `traces/Y334_rep0.json`), and Shipped or Lost not-arrived tickets that go to reship or refund.

## Expected regressions

- **Explicit requests that currently pass without escalating (8 rows):** Y082 (Lost, reship), Y083 (Lost, refund), Y193 (Shipped 16 days, reship) and Y209 (Processing, reply). Under the new rule these become escalate. The judge passed the non-escalate answer here but failed the same pattern in Y148, Y212, Y342 and Y112, so it may also accept escalate. The worst case is 8 rows lost.
  - `traces/Y082_rep0.json`: `\"ticket\": \"Where is order #5082? I ordered the coffee grinder. Get a supervisor on this.\"`, `\"status\": \"Lost\"`, `"content": "reship (confidence 0.97)"`
  - `traces/Y083_rep0.json`: `\"ticket\": \"My projector from order #5083 never came. Escalate this to a manager.\"`, `\"status\": \"Lost\"`, `"content": "refund (confidence 0.87)"`
  - `traces/Y193_rep0.json`: `\"ticket\": \"My standing desk mat from order #5193 never came. Escalate this to a manager.\"`, `\"status\": \"Shipped\"`, `"content": "reship (confidence 0.72)"`
  - `traces/Y209_rep0.json`: `\"ticket\": \"I received the wrong item on order #5209. It is not the home theater soundbar I ordered. Get a supervisor on this.\"`, `\"status\": \"Processing\"`, `"content": "reply (confidence 0.92)"`
- **Contradiction that currently passes with reply (2 rows):** Y144 has the same ticket shape as the failing Y089 (both Shipped), and the judge passed reply here. It becomes escalate.
  - `traces/Y144_rep0.json`: `\"ticket\": \"The box for order #5144 was crushed and the air purifier inside rattles.\"`, `\"status\": \"Shipped\"`, `\"delivered_on\": null`, `"content": "reply (confidence 0.88)"`
- **Possible spillover:** a longer escalate description may pull low-confidence refunds on Delivered damaged or wrong-item orders toward escalate. The at-risk rows are Y017 (0.36/0.49), Y084 (0.39), Y188 (0.53/0.57) and Y331 (0.53/0.44), all at 27–28 days and $500 or less, where the judge passes refund now.
- **Untested assumption:** escalate was never tried on the 20 contradiction rows. The judge failed reply and reship there. If it wanted refund instead (for example on Y362, which says "Refund me"), those rows won't recover.

Net: up to 39 rows recoverable against up to 10 rows at direct risk, plus the spillover rows above.

## Files read

- `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/p2/v1/BRIEF.md`
- `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/p2/v1/artifact.json`
- `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/p2/v1/history.md`
- `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/p2/v1/scores_train.tsv`
- `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/p2/v1/results_train.jsonl`
- `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/p2/v1/traces/*.json`: all 240 traces, parsed by script (Y007 through Y400, rep0 and rep1)
- `/root/.claude/projects/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/tool-results/b2jxbsaxy.txt`: the harness saved my own trace-tabulation command's output to this file because it was too large, and I read it from there. It contains only data derived from the traces and results above.
