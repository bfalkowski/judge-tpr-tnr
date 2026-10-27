Make the record decide the branch: compare shipped_on/delivered_on to 14- and 30-day cutoff dates, gate each rule on the record status, and say that the customer's account and demands do not change status or action. Mirror this in all four action descriptions.

## Behavior

Jev picks the policy branch without checking the record fields that gate it: the status, and whether shipped_on or delivered_on falls inside the 14-day or 30-day window. It fills that gap in one of three ways:

1. It misjudges the day count near a window edge when the dates cross a month boundary. The ticket is neutral in these cases.
2. It takes the customer's account as the record. "Lost" or "never came" leads to reship even when the status is Shipped within 14 days or Delivered. "Wrong item" leads to reship or escalate on an order that is not Delivered.
3. It follows the customer's demand ("Refund me", "Escalate this").

All three are the same failure: the branch is not tied to status, shipped_on, delivered_on and stock. Every failing train row shows it. I checked this by running a record-only procedure (status, day counts, stock, total, plus the request type from the ticket) over all 120 train cases, and it reproduces all 120 expected labels.

## Cases and cost

v1 scores 211/240 on train (87.9). All 29 failing rows (17 cases) show the behavior, so a full fix gains at most 29/240 = **12.1 points**, which is above the 6.5-point noise floor.

| Sub-pattern | Cases (failing reps) | Rows |
|---|---|---|
| Day count wrong at the 14/30-day edge | Y063 (2), Y114 (2), Y282 (2), Y273 (2), Y138 (2), Y179 (2), Y318 (2), Y046 (1) | 15 |
| Customer's account overrides status | Y258 (2), Y304 (2), Y338 (2), Y344 (2), Y030 (1), Y027 (1), Y133 (1) | 11 |
| Customer's demand overrides the action | Y362 (2), Y039 (1) | 3 |

The day-count sub-pattern alone is 15/240 = 6.25 points, which is inside the noise floor. That is why the change targets the shared root, which is that the branch is not read off the record, and not the date arithmetic alone.

Jev returns no reasoning tokens (`output_tokens: 0` in every results row). The day math therefore has to be made easy to do implicitly. The change turns "count the days" into "compare the date to a cutoff date", gives the cutoffs for the policy's fixed today (2026-10-01 is the only `today` in any train trace, and it comes from the off-limits policy text), and states the inclusive edges.

## Evidence

Today is 2026-10-01 in every trace. The cutoffs are 2026-09-17 for 14 days and 2026-09-01 for 30 days.

**Day count at the 14-day edge.** The ticket is neutral, and the answer flips on whether shipped_on is before 09-17.

traces/Y114_rep0.json (13 days, expected reply):
```
\"ticket\": \"Order #5114 (espresso machine) hasn't arrived. An update is all I need.\",
\"total\": 499.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-18\",\n  \"delivered_on\": null
"content": "reship (confidence 0.45)"
```
traces/Y282_rep0.json (exactly 14 days, expected reply):
```
\"ticket\": \"Where is order #5282? I ordered the robot vacuum.\",
\"total\": 549.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-17\",\n  \"delivered_on\": null
"content": "reship (confidence 0.68)"
```
traces/Y063_rep0.json (15 days, expected reship; this is the same error in the other direction):
```
\"ticket\": \"Any update on order #5063? The robot vacuum is for a gift.\",
\"total\": 549.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-16\",\n  \"delivered_on\": null
"content": "reply (confidence 0.52)"
```
traces/Y273_rep0.json (12 days and stock 0, so Jev went to rule 3, then refund, then escalate; expected reply):
```
\"ticket\": \"Can you check on order #5273 (projector)?\",
\"total\": 899.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-19\",\n  \"delivered_on\": null
\"stock\": 0
"content": "escalate (confidence 0.37)"
```

**Day count at the 30-day edge.** Each of these is delivered in late August, 31 to 33 days ago, and each is expected to escalate.

traces/Y318_rep0.json:
```
\"ticket\": \"I returned a different item last year (order #1069). This espresso machine, order #5318, smells like burning when I switch it on.\",
\"total\": 499.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-29\",\n  \"delivered_on\": \"2026-08-31\"
"content": "refund (confidence 0.79)"
```
traces/Y179_rep0.json:
```
\"ticket\": \"Order #5179: the label says smart speaker but the box has a phone case in it.\",
\"total\": 99.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-27\",\n  \"delivered_on\": \"2026-08-30\"
"content": "refund (confidence 0.35)"
```
traces/Y138_rep0.json:
```
\"ticket\": \"My air purifier (order #5138) has a cracked housing and doesn't work.\",
\"total\": 500.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-25\",\n  \"delivered_on\": \"2026-08-29\"
"content": "refund (confidence 0.76)"
```
traces/Y046_rep0.json (29 days, expected refund; the other rep refunds at 0.47):
```
\"ticket\": \"Order #5046 should have been my standing desk mat, but you sent something else. Just send a new one.\",
\"total\": 69.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-30\",\n  \"delivered_on\": \"2026-09-02\"
"content": "escalate (confidence 0.32)"
```

**Customer's account overrides status.**

traces/Y304_rep0.json (customer says lost, but the status is Shipped 12 days ago; expected reply):
```
\"ticket\": \"My desk lamp was lost in the mail, order #5304.\",
\"total\": 45.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-19\",\n  \"delivered_on\": null
"content": "reship (confidence 0.85)"
```
traces/Y258_rep0.json (same pattern, at the highest confidence of any failure):
```
\"ticket\": \"The air purifier from order #5258 is lost, I'm sure of it.\",
\"total\": 500.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-18\",\n  \"delivered_on\": null
"content": "reship (confidence 0.96)"
```
traces/Y338_rep0.json (customer says not arrived, but the record says Delivered; expected reply):
```
\"ticket\": \"Order #5338 (espresso machine) hasn't arrived.\",
\"total\": 499.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-25\",\n  \"delivered_on\": \"2026-08-30\"
"content": "reship (confidence 0.4)"
```
traces/Y344_rep1.json:
```
\"ticket\": \"Why can't anyone tell me where order #5344 is? I want my portable monitor.\",
\"total\": 299.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-28\",\n  \"delivered_on\": \"2026-09-03\"
"content": "reship (confidence 0.6)"
```
traces/Y133_rep1.json (wrong-item claim on an order that is not Delivered; expected reply):
```
\"ticket\": \"My earlier order #2619 was fine. Order #5133 has someone else's item, not my espresso machine.\",
\"total\": 499.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-09-01\",\n  \"delivered_on\": null
"content": "reship (confidence 0.29)"
```
traces/Y027_rep1.json:
```
\"ticket\": \"I received the wrong item on order #5027. It is not the gaming chair I ordered. Get a supervisor on this.\",
\"total\": 501.0,\n  \"status\": \"Shipped\",\n  \"shipped_on\": \"2026-08-27\",\n  \"delivered_on\": null
"content": "escalate (confidence 0.32)"
```

**Customer's demand overrides the action.**

traces/Y362_rep0.json (status-check ticket on a Delivered order; expected reply):
```
\"ticket\": \"Can you check on order #5362 (countertop oven)? Refund me.\",
\"total\": 189.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-25\",\n  \"delivered_on\": \"2026-08-29\"
"content": "refund (confidence 0.27)"
```
traces/Y039_rep1.json (delivered exactly 30 days ago, so rule 2 gives refund; expected refund):
```
\"ticket\": \"My ergonomic keyboard (order #5039) has a cracked housing and doesn't work. Escalate this to a manager.\",
\"total\": 159.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-30\",\n  \"delivered_on\": \"2026-09-01\"
"content": "escalate (confidence 0.55)"
```

**Contrast: when status alone settles the branch, Jev is right and confident.**

traces/Y016_rep0.json:
```
\"ticket\": \"Order #5016 (air purifier) hasn't arrived. Just tell me what's going on.\",
\"total\": 500.0,\n  \"status\": \"Lost\",\n  \"shipped_on\": \"2026-09-19\",\n  \"delivered_on\": null
"content": "reship (confidence 1.0)"
```
traces/Y354_rep0.json (delivered 56 days ago, far from the edge):
```
\"ticket\": \"The smart speaker from order #5354 arrived damaged. Let me know the status.\",
\"total\": 99.0,\n  \"status\": \"Delivered\",\n  \"shipped_on\": \"2026-08-04\",\n  \"delivered_on\": \"2026-08-06\"
"content": "escalate (confidence 0.8)"
```
Passing rows near an edge or with a misleading ticket pass only at low confidence, which suggests the same weakness: traces/Y327_rep1.json `"content": "reply (confidence 0.39)"` (Shipped 2026-09-19), traces/Y194_rep0.json `"content": "reply (confidence 0.23)"` (says "waiting FOREVER", Delivered), traces/Y133_rep0.json `"content": "reply (confidence 0.25)"`.

## The change

- **decision_instructions** is rewritten around the record. It names the gating fields and says the ticket is used only to classify the request as (a) not arrived or where is it, (b) damaged or wrong item, or (c) change of mind. It says a customer's "lost" or "never came" does not change the status, and that demands do not change the action. Step 1 replaces day counting with a date comparison against 14- and 30-day cutoffs, with inclusive edges and the cutoffs for the policy's today. Step 2 is a status-gated branch table covering Processing, (c), (b) when Delivered or not, and (a) when Delivered, Lost or Shipped within or past 14 days. Step 3 is the v1 rule-4 override, kept word for word.
- **criteria** carries each action's record preconditions: refund (window plus stock 0 plus total ≤ $500), reship (not arrived, Lost or Shipped more than 14 days ago, stock above 0, never for a damaged or wrong item, never for Processing or Delivered), escalate (v1 text plus "a customer asking for a supervisor is not a reason"), and reply (the record states that lead to reply).

Every part serves the same behavior, which is tying the branch to the record. The rule-4 handling from v1 is unchanged.

## Expected regressions

- **Lost orders shipped 14 days ago or less** (reship, or escalate when stock is 0 and the total is over $500): Y016, Y026, Y055, Y082, Y112, Y214, Y237, Y243, Y358, Y400, Y083, Y385. The new emphasis on the 14-day cutoff could pull these to reply if Jev applies the window without first checking status. The instructions say Lost applies "however recently it shipped" to guard against this, but this is the main risk.
- **Damaged or wrong item delivered within 30 days with a demand for a supervisor or replacement**, expected refund: Y007, Y225, Y084, Y017 (Y017 currently passes at 0.47). These should hold, but the longer descriptions shift the prompt.
- **Status-check tickets on Shipped orders past 14 days that say "Refund me"** (Y080, Y162 expect reship) or have stock 0 (Y024 expects refund). The demand clause should help, but they move from a short prompt to a longer one.
- Generalization note: the worked cutoff dates assume the policy's today, 2026-10-01, which is fixed in the off-limits policy text and is the only `today` in train. If held-out rows use another today, the method still applies but the example cutoffs will not match it.

## Files read

All paths are under `/tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v2/`:

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- All 240 trace files, `traces/<case>_rep0.json` and `traces/<case>_rep1.json`, for these cases: Y007, Y011, Y012, Y013, Y016, Y017, Y024, Y025, Y026, Y027, Y028, Y030, Y031, Y033, Y039, Y046, Y050, Y052, Y054, Y055, Y061, Y063, Y064, Y068, Y076, Y080, Y081, Y082, Y083, Y084, Y085, Y088, Y089, Y110, Y112, Y114, Y116, Y118, Y119, Y121, Y123, Y124, Y131, Y133, Y138, Y144, Y148, Y149, Y161, Y162, Y166, Y169, Y179, Y180, Y188, Y190, Y192, Y193, Y194, Y200, Y206, Y209, Y212, Y214, Y215, Y222, Y225, Y231, Y232, Y237, Y240, Y243, Y244, Y247, Y250, Y251, Y252, Y255, Y258, Y263, Y265, Y266, Y270, Y273, Y277, Y282, Y290, Y292, Y293, Y303, Y304, Y309, Y312, Y315, Y318, Y323, Y327, Y331, Y333, Y334, Y338, Y342, Y343, Y344, Y346, Y354, Y356, Y358, Y360, Y362, Y364, Y365, Y371, Y380, Y383, Y385, Y386, Y389, Y396, Y400
