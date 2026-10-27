No change: the only failure big enough to clear the noise floor (the $500 cap skipped after rule 3's out-of-stock refund, 10 cases, 19 rows, 7.9 points) was already targeted through every in-scope lever in v1 and v2 for a net gain of 1 row, and every other failure costs 7 rows or fewer.

## Verdict

I am not proposing a change and did not write `out/artifact.json`.

By the brief's arithmetic, a full fix of the top behavior (19 rows, 7.9 points) sits just above the 6.5-point floor. To clear the floor it would have to gain more than 15 rows net, which means recovering at least 16 of the 19 rows with almost no regressions. That fix is not reachable from the artifact:

- v1 put the cap into the instructions and the refund/escalate descriptions. v2 put it into the descriptions only. Those are the only two levers in scope, and both have been used. In the family, both versions recovered Y385 (2 rows) and lost Y119 rep 1 (1 row), for a net of +1 row out of 19. Outside the family they lost 9 rows (v1) and 3 rows (v2). Both were reverted.
- The model is confident in the wrong answer. 16 of the 19 failing rows are `refund` at confidence 0.84 or higher, so wording nudges have had nothing to move.
- The root fix is to apply rule 4 after the model picks (a refund on a total over $500 becomes escalate). That is in the code, which is off-limits. categorization.md reaches the same conclusion and lists this family under "structural".

Every other remaining failure is under the floor on its own (table below), and most of them can't be fixed from the artifact either.

## The behavior, how many cases, what it costs

When rule 3 (never arrived) leads to refund because stock is 0, Jev stops there and picks `refund` without applying rule 4 ("Any refund over $500 must be escalated instead of refunded."). The judge fails every one of these refunds.

- Cases: Y013, Y050, Y054, Y083, Y119, Y124, Y192, Y343, Y346, Y385 (10 cases).
- Rows: 19 of 20 fail. Y119 rep 1 passes because it replied, which the policy doesn't call for, but the judge passed it.
- Cost: 19 of 240 rows, 7.9 points of `pass` (9.5 of 120 case means). A fix can gain no more than that.

For contrast, Jev does apply the cap after rule 2. On damaged or wrong items delivered 30 days ago or less with a total over $500, it escalates on 24 of 24 rows and all of them pass (Y025, Y081, Y116, Y131, Y166, Y180, Y206, Y231, Y251, Y255, Y265, Y292). It also applies rule 3's out-of-stock refund correctly at $500 or less: 10 of 10 rows refund and pass (Y024, Y290, Y312, Y323, Y371). The failure is specific to chaining rule 4 after rule 3. My hypothesis is that rule 2's text names escalate as one of its outcomes and rule 3's text names only reship and refund, so escalate never becomes a candidate on a never-arrived ticket. I can't test that from here.

## Every other remaining failure, each under the floor

| Behavior | Cases (failing rows) | Rows | Points | Fixable in the artifact? |
|---|---|---|---|---|
| Judge fails an action the policy calls for | Y007 r1, Y061, Y084, Y169 | 7 | 2.9 | No. It would mean encoding the judge's errors |
| Delivered order reported as not arrived; policy has no rule | Y194, Y338, Y344 r1 | 5 | 2.1 | No. Needs a policy decision |
| Damaged or wrong item on an order never delivered; policy has no rule | Y027, Y133 | 4 | 1.7 | No. Needs a policy decision |
| Day-count boundary at exactly 14 or 30 days | Y039, Y282 | 4 | 1.7 | Maybe, but the ceiling is 1.7 points |

Total failing rows: 19 + 7 + 5 + 4 + 4 = 39, which matches the 39 failing rows in results_train.jsonl.

## Evidence

The state is a JSON string inside the user message. Below, the policy and state lines are quoted from that string as decoded. The assistant lines are verbatim from line 12 of each file.

Policy text, identical in every trace (from the user message of /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y050_rep0.json):

```
2. Damaged or wrong item: if the order was delivered 30 days ago or less, refund it. If it was delivered more than 30 days ago, escalate.
3. Never arrived, or the customer asks where the order is: if the order is Lost, or it shipped more than 14 days ago and has not been delivered, reship it if the item is in stock, otherwise refund it.
4. Any refund over $500 must be escalated instead of refunded.
```

Failing: rule 3 refund over $500, with rule 4 skipped.

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y050_rep0.json
```
"ticket": "Hi, just checking on order #5050. No rush on the projector.",
"total": 899.0,
"status": "Lost",
"stock": 0
"content": "refund (confidence 0.99)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y013_rep0.json
```
"ticket": "Tracking for order #5013 (gaming chair) hasn't moved in a while.",
"total": 501.0,
"status": "Lost",
"stock": 0
"content": "refund (confidence 0.91)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y343_rep0.json
```
"ticket": "Why can't anyone tell me where order #5343 is? I want my projector.",
"total": 899.0,
"status": "Shipped",
"shipped_on": "2026-08-28",
"delivered_on": null
"stock": 0
"content": "refund (confidence 0.87)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y385_rep0.json (the one case v1 and v2 both recovered)
```
"ticket": "Can you check on order #5385 (projector)? Ship me another one.",
"total": 899.0,
"status": "Lost",
"stock": 0
"content": "refund (confidence 0.99)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y119_rep0.json and /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y119_rep1.json (same state; rep 0 fails, rep 1 passes with an action the policy doesn't call for)
```
"ticket": "Order #5119, the projector. Just making sure it's on the way.",
"total": 899.0,
"status": "Shipped",
"shipped_on": "2026-09-07",
"stock": 0
rep0: "content": "refund (confidence 0.29)"
rep1: "content": "reply (confidence 0.31)"
```

Passing contrast: the cap is applied after rule 2.

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y081_rep0.json
```
"ticket": "Order #5081: the gaming chair is broken. Refund me.",
"total": 501.0,
"status": "Delivered",
"delivered_on": "2026-09-04"
"content": "escalate (confidence 0.81)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y025_rep0.json
```
"ticket": "I received the wrong item on order #5025. It is not the gaming chair I ordered.",
"total": 501.0,
"status": "Delivered",
"delivered_on": "2026-09-01"
"content": "escalate (confidence 0.88)"
```

Passing contrast: rule 3's out-of-stock refund at $500 or less.

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y290_rep0.json
```
"ticket": "My bluetooth earbuds from order #5290 never came. I want a full refund.",
"total": 79.0,
"status": "Lost",
"stock": 0
"content": "refund (confidence 1.0)"
```

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y371_rep0.json
```
"ticket": "Order #5371 (ergonomic keyboard) hasn't arrived.",
"total": 159.0,
"status": "Shipped",
"shipped_on": "2026-09-15",
"stock": 0
"content": "refund (confidence 0.73)"
```

Prior attempts, from /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/scores_train.tsv (columns: case, baseline, v1, v2). These are the rows that moved:

```
Y007	0.50	0.00	0.00
Y030	1.00	0.00	0.00
Y039	0.00	0.50	0.50
Y119	0.50	0.00	0.00
Y266	1.00	0.50	1.00
Y273	1.00	0.00	0.00
Y327	1.00	0.50	1.00
Y344	0.50	0.00	1.00
Y362	1.00	0.00	1.00
Y385	0.00	1.00	1.00
```

Totals over 120 cases: baseline 100.5, v1 96.5, v2 99.5. The other eight cases in the family stayed at 0.00 in both versions.

Regression exposure for any cap wording: Y273 is inside rule 1 (shipped 12 days ago, so reply), but it has a total over $500 and stock 0. It lost both reps in v1 and in v2.

/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/Y273_rep0.json
```
"ticket": "Can you check on order #5273 (projector)?",
"total": 899.0,
"status": "Shipped",
"shipped_on": "2026-09-19",
"stock": 0
"content": "reply (confidence 0.61)"
```

## Cases expected to regress

None. No change is proposed.

If someone tries the cap a third time anyway, these are the cases at risk. Y273 regressed under both v1 and v2. Y030 and Y007 regressed under both. Y362, Y266 and Y327 regressed under v1. More broadly, 42 passing rows are on orders over $500 where the policy calls for something other than escalate: reply on Processing or shipped 14 days or less, reship when in stock, and rule 5 reply.

## What would move the score (all outside the artifact)

- Apply rule 4 in code after the model picks: a refund with total over $500 becomes escalate. This is the fix for the 19 rows.
- Calibrate the judge before reading further score movement. In this run it passes 16 rows the policy doesn't support (Y007 r0, Y063, Y114, Y119 r1, Y138, Y179, Y258, Y304, Y318) and fails 7 rows the policy does support (Y007 r1, Y061, Y084, Y169).

## Files read

- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/BRIEF.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/artifact.json
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/history.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/categorization.md
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/scores_train.tsv
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/results_train.jsonl
- /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/traces/ (all 240 files, Y007_rep0.json through Y400_rep1.json, parsed by script; Y013, Y025, Y030, Y031, Y050, Y054, Y081, Y083, Y119, Y124, Y180, Y192, Y244, Y273, Y290, Y343, Y346, Y362, Y371, Y383, Y385 printed and read in detail)
- My own scratch files in /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/lenient-r2/v3/out/: table.py, rows.tsv (one line per train row), oracle.py (policy oracle over rows.tsv), quote.py (prints state lines from traces)
