Make the order record (status, shipped_on, delivered_on, stock), not the ticket's framing, pick the policy rule: add a status-first decision table to the instructions and state in the reship and reply descriptions which record states they cover, keeping the v1 refund-limit check as the last step.

## Behavior

Jev chooses the rule from what the customer says instead of from the order record. It runs in two directions:

1. **Rule 3 fires because the ticket says lost / not arrived / where is it, even though the record does not qualify.** Jev reships (or takes rule 3's out-of-stock refund path to escalate) on orders that are Shipped 14 days ago or less, or that are Delivered. The policy calls for reply (rule 1) on the first. On the second the judge wants reply when delivered 30 days ago or less, and escalate when delivered more than 30 days ago.
2. **Rule 3 does not fire because the ticket reads as damage / wrong item / a status question, even though the record qualifies.** On orders Shipped more than 14 days ago with no delivered_on, Jev replies. Damage or a wrong item on an undelivered order can't use rule 2, so Jev falls back to reply. A plain "any update?" gets treated as a status request (rule 1). The judge wants rule 3 (reship, since stock > 0) in every such case.

The current instructions and action descriptions only cover the refund-limit check. Nothing tells Jev that status and dates decide which rule applies, so it keys on the ticket's words.

## Size and cost

- Direction 1: 9 cases, 18 failing rows. Y258, Y304, Y114, Y282, Y273 (Shipped 12 to 14 days) and Y030, Y344, Y338, Y194 (Delivered).
- Direction 2: 5 cases, 9 failing rows. Y063, Y089, Y144, Y396 (0/2 each) and Y133 (1/2). All are Shipped 15 to 30 days with no delivered_on.
- Total: 14 of 120 train cases, 27 of 240 rows, so 11.25 points of `pass` on train. The current train pass is 205/240 (85.4%). A full fix lands at 232/240 (96.7%). That clears the ±6.5 noise floor if the behavior occurs on test at a similar rate. A partial fix (say two thirds of it) would be about 7.5 points, which is near the floor.

The other 8 failing rows are not this behavior, and this change does not target them:
- Y138, Y179, Y318 (6 rows): Delivered damage or wrong item 31 to 33 days ago, and Jev refunds instead of escalating. This is a 30-day-window miss. It costs 2.5 points, which is under the noise floor by itself.
- Y017 (2 rows): a $500 refund that the judge fails as "equals the limit and must be escalated". That contradicts the judge's own passes on Y084 and Y315 ("this is exactly $500, not over it, so refund is permitted"). It is grader noise and can't be fixed without regressing those two.

## Evidence

All traces share this policy text in the user message (verbatim): `1. If the order has not shipped yet (status Processing), or it shipped 14 days ago or less and has not been delivered, reply with the order status. Take no other action.` and `3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.` Today is `"today": "2026-10-01"`.

### Direction 1: the ticket's claim triggers rule 3 on a record that does not qualify

traces/Y258_rep0.json (Shipped 13 days, the customer asserts lost; Jev is near certain)
```
 "ticket": "The air purifier from order #5258 is lost, I'm sure of it.",
  "status": "Shipped",
  "shipped_on": "2026-09-18",
  "delivered_on": null
 "stock": 5
assistant: "reship (confidence 0.97)"
```
Judge: "13 days is 14 days or less and the order has not been delivered, the policy requires a reply with order status, not a reship."

traces/Y304_rep1.json (Shipped 12 days)
```
 "ticket": "My desk lamp was lost in the mail, order #5304.",
  "status": "Shipped",
  "shipped_on": "2026-09-19",
  "delivered_on": null
 "stock": 30
assistant: "reship (confidence 0.92)"
```

traces/Y114_rep0.json (Shipped 13 days; the customer even asks only for an update)
```
 "ticket": "Order #5114 (espresso machine) hasn't arrived. An update is all I need.",
  "status": "Shipped",
  "shipped_on": "2026-09-18",
  "delivered_on": null
 "stock": 3
assistant: "reship (confidence 0.59)"
```

traces/Y282_rep1.json (Shipped exactly 14 days)
```
 "ticket": "Where is order #5282? I ordered the robot vacuum.",
  "status": "Shipped",
  "shipped_on": "2026-09-17",
  "delivered_on": null
 "stock": 2
assistant: "reship (confidence 0.69)"
```

traces/Y273_rep0.json (Shipped 12 days. Jev took rule 3, then out of stock gives refund, then $899 gives escalate. The limit check fired on a rule that should not have applied.)
```
 "ticket": "Can you check on order #5273 (projector)?",
  "total": 899.0,
  "status": "Shipped",
  "shipped_on": "2026-09-19",
  "delivered_on": null
 "stock": 0
assistant: "escalate (confidence 0.51)"
```

traces/Y030_rep0.json (Delivered 28 days ago, the customer asks where it is)
```
 "ticket": "Where is order #5030? I ordered the document scanner.",
  "status": "Delivered",
  "shipped_on": "2026-09-01",
  "delivered_on": "2026-09-03"
 "stock": 0
assistant: "reship (confidence 0.43)"
```
Judge: "the order record shows it was already delivered. The policy requires a reply with order status, not a reship."

traces/Y344_rep1.json (Delivered 28 days ago)
```
 "ticket": "Why can't anyone tell me where order #5344 is? I want my portable monitor.",
  "status": "Delivered",
  "shipped_on": "2026-08-28",
  "delivered_on": "2026-09-03"
 "stock": 8
assistant: "reship (confidence 0.48)"
```

traces/Y338_rep0.json (Delivered 32 days ago, the customer says it hasn't arrived)
```
 "ticket": "Order #5338 (espresso machine) hasn't arrived.",
  "status": "Delivered",
  "shipped_on": "2026-08-25",
  "delivered_on": "2026-08-30"
 "stock": 3
assistant: "reship (confidence 0.52)"
```
Judge: "The order status shows Delivered, so it is not Lost. The policy requires escalation for items not arrived/lost when delivered more than 30 days ago, not a reship."

traces/Y194_rep1.json (Delivered 33 days ago)
```
 "ticket": "I've been waiting FOREVER for my countertop oven, order #5194.",
  "status": "Delivered",
  "shipped_on": "2026-08-27",
  "delivered_on": "2026-08-29"
 "stock": 0
assistant: "reship (confidence 0.44)"
```
Judge: "The policy requires escalation for issues outside the 30-day window, not a reship."

### Direction 2: the ticket's framing hides a rule 3 record

traces/Y089_rep0.json (Shipped 28 days, not delivered, reported damaged)
```
 "ticket": "The box for order #5089 was crushed and the espresso machine inside rattles.",
  "status": "Shipped",
  "shipped_on": "2026-09-03",
  "delivered_on": null
 "stock": 3
assistant: "reply (confidence 0.73)"
```
Judge: "Since the order shipped more than 14 days ago and has not been delivered, the policy requires reship if in stock (3 units available)".

traces/Y144_rep1.json (Shipped 16 days, not delivered, reported damaged)
```
 "ticket": "The box for order #5144 was crushed and the air purifier inside rattles.",
  "status": "Shipped",
  "shipped_on": "2026-09-15",
  "delivered_on": null
 "stock": 5
assistant: "reply (confidence 0.81)"
```

traces/Y396_rep0.json (Shipped 23 days, not delivered, reported damaged, the customer demands escalation)
```
 "ticket": "My portable monitor (order #5396) has a cracked housing and doesn't work. Escalate this to a manager.",
  "status": "Shipped",
  "shipped_on": "2026-09-08",
  "delivered_on": null
 "stock": 8
assistant: "reply (confidence 0.68)"
```

traces/Y133_rep1.json (Shipped 30 days, not delivered, wrong item). In the other rep, traces/Y133_rep0.json, the same input gives `"reship (confidence 0.43)"`, so Jev is split.
```
 "ticket": "My earlier order #2619 was fine. Order #5133 has someone else's item, not my espresso machine.",
  "status": "Shipped",
  "shipped_on": "2026-09-01",
  "delivered_on": null
 "stock": 3
assistant: "reply (confidence 0.29)"
```

traces/Y063_rep0.json (Shipped 15 days, phrased as a status question)
```
 "ticket": "Any update on order #5063? The robot vacuum is for a gift.",
  "status": "Shipped",
  "shipped_on": "2026-09-16",
  "delivered_on": null
 "stock": 2
assistant: "reply (confidence 0.52)"
```

### Contrast: passing cases where the record and the ticket point the same way

traces/Y016_rep0.json (status Lost, 12 days: rule 3 by status, which Jev gets right)
```
 "ticket": "Order #5016 (air purifier) hasn't arrived. Just tell me what's going on.",
  "status": "Lost",
  "shipped_on": "2026-09-19",
  "delivered_on": null
 "stock": 5
assistant: "reship (confidence 1.0)"
```

traces/Y327_rep0.json (Shipped 12 days. The ticket is a mild status check, so reply is correct.)
```
 "ticket": "Order #5327, the air purifier. Just making sure it's on the way.",
  "status": "Shipped",
  "shipped_on": "2026-09-19",
  "delivered_on": null
 "stock": 5
assistant: "reply (confidence 0.6)"
```

traces/Y033_rep0.json (Shipped 15 days. The ticket says "never came", so rule 3 is correct.)
```
 "ticket": "My portable monitor from order #5033 never came. Let me know the status.",
  "status": "Shipped",
  "shipped_on": "2026-09-16",
  "delivered_on": null
 "stock": 8
assistant: "reship (confidence 0.57)"
```

The pattern holds across these. Y327 (12 days) and Y304 (12 days) have the same ship date and opposite outcomes, and Y033 (15 days) and Y063 (15 days) do too. The difference in each pair is only the ticket wording ("making sure it's on the way" vs "lost in the mail", "never came" vs "any update"). The day count is not what Jev is getting wrong. The ticket's words choose the rule.

traces/Y027_rep0.json (wrong item on an undelivered order Shipped 35 days, out of stock, $501) passes, but at `"escalate (confidence 0.19)"`. It is the same direction-2 confusion, sitting just on the passing side.

## The change

- **decision_instructions**: The single refund-limit paragraph becomes three parts.
  1. A rule that the record's status, shipped_on, delivered_on and stock pick the rule, and the ticket only says which kind of problem is reported. It includes three explicit don'ts: the customer saying "lost" is not status Lost, "never arrived" doesn't override Delivered, and damage or a wrong item with no delivered_on isn't rule 2.
  2. A status-first table that covers every status: Processing; Shipped ≤14 days; Shipped >14 days (rule 3 whatever the ticket reports, including damage, a wrong item or only an update request); Lost at any age; Delivered with damage or a wrong item; Delivered change of mind; Delivered "never arrived" (reply if delivered ≤30 days ago, escalate if >30, matching the judge's reasoning on Y030/Y344 and Y338/Y194); Delivered anything else, which gets reply.
  3. The v1 refund-limit check, kept as the last step with its wording intact. The only difference is that the rule 3 refund case now says "Lost or Shipped more than 14 days ago" instead of "never arrived or is Lost".
- **criteria**: The action words and keys are unchanged. Reship now says which record states it covers and that it never applies to Processing, Delivered, or Shipped ≤14 days. Reply now lists the record states it covers. Refund names the record states for its rule 2 and rule 3 paths and keeps the limit clause. Escalate adds "Delivered more than 30 days ago and reported damaged, wrong, or never received" next to the existing over-limit clause.

Every addition is about one thing: deriving the rule from the record. No product names, order numbers or ticket phrases from train cases appear in the artifact.

One caveat: the "Delivered, never arrived, more than 30 days ago means escalate" branch is not written in the policy. It follows the judge's reading on Y338 and Y194. If held-out judging is not consistent on that branch, those cases may not move.

## Cases I expect could regress

- **Lost orders with 14 days or fewer since shipping**, which pass today only because Jev treats Lost as rule 3: Y214 (Lost, 3 days), Y243 (5), Y083 (5, escalate), Y385 (8, escalate), Y323 (9, refund), Y016, Y055, Y112, Y358 (12), Y237, Y400 (13), Y082, Y290, Y346 (14). The new sentence "A customer saying the order is lost does not make its status Lost" could make Jev wary of rule 3 on short-age orders in general. The table's "Lost, however many days since shipping: rule 3" line is there to stop that, but these are the first rows to check.
- **Y362** (Delivered 33 days, "Can you check on order #5362 (countertop oven)? Refund me.", currently reply at 0.43/0.47). If Jev reads "check on" as "has not received it", the new branch sends it to escalate instead of reply.
- **Y027** (currently escalate at 0.19). The table should firm this up, but at that confidence it could flip either way.
- **Direction-1 boundary cases at exactly 14 days** that pass today (Y270 reply, Y082/Y290/Y346 Lost) depend on "exactly 14 counts as 14 or less" being read correctly.

Nothing in the v1 refund-limit logic is removed, so I don't expect regressions among the cases v1 recovered (Y013, Y027, Y039, Y050, Y054, Y083, Y124, Y192, Y343, Y346, Y385).

## Files read

All paths are under /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3-r2/v2/:

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- traces/<case>_rep0.json and traces/<case>_rep1.json for every train case, 240 files, all read by a script that built a per-case table: Y007 Y011 Y012 Y013 Y016 Y017 Y024 Y025 Y026 Y027 Y028 Y030 Y031 Y033 Y039 Y046 Y050 Y052 Y054 Y055 Y061 Y063 Y064 Y068 Y076 Y080 Y081 Y082 Y083 Y084 Y085 Y088 Y089 Y110 Y112 Y114 Y116 Y118 Y119 Y121 Y123 Y124 Y131 Y133 Y138 Y144 Y148 Y149 Y161 Y162 Y166 Y169 Y179 Y180 Y188 Y190 Y192 Y193 Y194 Y200 Y206 Y209 Y212 Y214 Y215 Y222 Y225 Y231 Y232 Y237 Y240 Y243 Y244 Y247 Y250 Y251 Y252 Y255 Y258 Y263 Y265 Y266 Y270 Y273 Y277 Y282 Y290 Y292 Y293 Y303 Y304 Y309 Y312 Y315 Y318 Y323 Y327 Y331 Y333 Y334 Y338 Y342 Y343 Y344 Y346 Y354 Y356 Y358 Y360 Y362 Y364 Y365 Y371 Y380 Y383 Y385 Y386 Y389 Y396 Y400
- out/artifact.json, my own output, re-read to validate it.
- I also wrote and then deleted two scratch files in out/: table.py and tracelist.txt.
