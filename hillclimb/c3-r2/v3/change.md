No change proposed: the top failure behavior (Jev misjudging whether shipped_on or delivered_on falls inside the 14-day or 30-day window when the date is within a few days of the cutoff) costs only 14 of 240 train rows (5.8 points), which is inside the 6.5-point noise floor even if fully fixed.

## Where v2 stands

- Train pass is 223 of 240 rows (92.9%). Only 17 rows fail, across 10 cases, so there are 7.1 points of headroom in total.
- The noise floor is about 15 rows. No single behavior accounts for 15 failing rows, so no one-behavior change can produce a gain that can be told apart from noise.

## The behavior

When a ticket's outcome depends on the 14-day shipping window or the 30-day delivery window, and the relevant date is close to the cutoff, Jev puts the date on the wrong side of the line. It does this in both directions. In-window dates get read as out of window (27, 28 and 30 days read as more than 30; 12 and 14 days read as more than 14), and one out-of-window date gets read as in window (31 days read as 30 or less). The results show `"output_tokens": 0` on every row, so Jev makes the window call in one shot with no visible arithmetic.

Cases showing it: 8 (Y007, Y039, Y331, Y318, Y273, Y282 fail both reps; Y188 and Y052 fail one rep each).
Cost: 14 failing rows of 240, or 5.8 points of train pass. That is the most a full fix could recover, and it is below the roughly 15-row noise floor.

The same uncertainty shows in confidence. I bucketed every row by how far its relevant date is from the cutoff (computed with today = 2026-10-01 from the state):

| Bucket | Rows | Pass | Mean confidence |
|---|---|---|---|
| Processing or Lost (no window check) | 80 | 80 | 0.98 |
| Delivered, more than 7.5 days from the 30-day cutoff | 30 | 30 | 0.87 |
| Delivered, within 3.5 days of the 30-day cutoff | 60 | 49 | 0.72 |
| Shipped, more than 7.5 days from the 14-day cutoff | 26 | 25 | 0.83 |
| Shipped, within 3.5 days of the 14-day cutoff | 38 | 34 | 0.49 |

43 rows that currently pass sit within 7.5 days of a cutoff with confidence below 0.6. They pass, but they would be exposed to flips from any change that moves where Jev draws the line.

The history points the same way. The v1 to v2 change flipped exactly Y007, Y039, Y052, Y188 and Y331 from pass to fail. All five are in-window Delivered damage or wrong-item cases at 24 to 30 days. v2 did not touch the window wording, so Jev's call at the boundary moves with unrelated edits to the prompt.

## Other failing rows (not this behavior)

- Y194, 2 rows: a Delivered order delivered 33 days ago, with the ticket "I've been waiting FOREVER for my countertop oven". Jev answers reply (0.44, 0.41) and the judge expects escalate. Other orders with the same delivered_on (2026-08-29), Y138 and Y215, get escalate with confidence 0.68 to 0.88, so Jev does see this date as more than 30 days. The miss is that it does not read "waiting forever" as a not-received claim.
- Y396, 1 row: damage reported on a Shipped order shipped 23 days ago. rep0 reships (correct, 0.39) and rep1 replies (0.36).

Fixing every failing row would recover 17 rows, but they come from three unrelated behaviors.

## Evidence

State lines are from the user message in each trace, unescaped from its JSON string. The decision line is the assistant message. Today is 2026-10-01 in every trace.

In-window refund read as out of window, so Jev escalates (policy rule 2 says refund; every total is under $500):

traces/Y007_rep0.json (delivered 28 days ago)
```
"ticket": "The bluetooth earbuds from order #5007 arrived damaged. I want this escalated.",
"total": 79.0,
"status": "Delivered",
"shipped_on": "2026-08-28",
"delivered_on": "2026-09-03"
"content": "escalate (confidence 0.43)"
```

traces/Y039_rep1.json (delivered exactly 30 days ago)
```
"ticket": "My ergonomic keyboard (order #5039) has a cracked housing and doesn't work. Escalate this to a manager.",
"total": 159.0,
"status": "Delivered",
"shipped_on": "2026-08-30",
"delivered_on": "2026-09-01"
"content": "escalate (confidence 0.41)"
```

traces/Y331_rep0.json (delivered 27 days ago; the ticket asks for money back, so the ticket's demand did not cause the escalate)
```
"ticket": "Order #5331 should have been my standing desk mat, but you sent something else. Give me my money back.",
"total": 69.0,
"status": "Delivered",
"shipped_on": "2026-08-31",
"delivered_on": "2026-09-04"
"content": "escalate (confidence 0.47)"
```

traces/Y188_rep0.json and traces/Y188_rep1.json (delivered 27 days ago; same input, reps split)
```
"ticket": "Order #5188 should have been my smart speaker, but you sent something else. Ship me another one.",
"total": 99.0,
"status": "Delivered",
"delivered_on": "2026-09-04"
rep0: "content": "escalate (confidence 0.41)"
rep1: "content": "refund (confidence 0.31)"
```

traces/Y052_rep0.json and traces/Y052_rep1.json (delivered 24 days ago; reps split)
```
"ticket": "My portable monitor (order #5052) has a cracked housing and doesn't work. Give me my money back.",
"total": 299.0,
"status": "Delivered",
"shipped_on": "2026-09-01",
"delivered_on": "2026-09-07"
rep0: "content": "refund (confidence 0.36)"
rep1: "content": "escalate (confidence 0.39)"
```

Out-of-window date read as in window, so Jev refunds (should escalate):

traces/Y318_rep0.json (delivered 31 days ago)
```
"ticket": "I returned a different item last year (order #1069). This espresso machine, order #5318, smells like burning when I switch it on.",
"total": 499.0,
"status": "Delivered",
"shipped_on": "2026-08-29",
"delivered_on": "2026-08-31"
"content": "refund (confidence 0.32)"
```
Judge (results_train.jsonl, Y318 rep 0): "Delivered 2026-08-31, today is 2026-10-01: 31 days, outside the 30-day window."

Shipped 14 days ago or less read as more than 14, so Jev takes the rule 3 path:

traces/Y273_rep0.json (shipped 12 days ago, stock 0, total over the limit, so rule 3 would end in escalate)
```
"ticket": "Can you check on order #5273 (projector)?",
"total": 899.0,
"status": "Shipped",
"shipped_on": "2026-09-19",
"delivered_on": null
"stock": 0
"content": "escalate (confidence 0.36)"
```

traces/Y282_rep1.json (shipped exactly 14 days ago)
```
"ticket": "Where is order #5282? I ordered the robot vacuum.",
"total": 549.0,
"status": "Shipped",
"shipped_on": "2026-09-17",
"delivered_on": null
"stock": 2
"content": "reship (confidence 0.39)"
```

Contrast (passing). The same shipped_on date as Y282 gets the right answer, but at near-coin-flip confidence. Dates far from the cutoff are confident:

traces/Y270_rep0.json (same shipped_on as Y282, passes)
```
"status": "Shipped",
"shipped_on": "2026-09-17",
"delivered_on": null
"content": "reply (confidence 0.4)"
```

traces/Y327_rep0.json (same shipped_on as Y273, passes)
```
"status": "Shipped",
"shipped_on": "2026-09-19",
"delivered_on": null
"content": "reply (confidence 0.55)"
```

traces/Y356_rep0.json (delivered 6 days ago, damage, under the limit, passes)
```
"ticket": "My countertop oven (order #5356) has a cracked housing and doesn't work. Ship me another one.",
"total": 189.0,
"status": "Delivered",
"delivered_on": "2026-09-25"
"content": "refund (confidence 0.79)"
```

traces/Y046_rep1.json (delivered 29 days ago, wrong item, under the limit, passes only barely)
```
"ticket": "Order #5046 should have been my standing desk mat, but you sent something else. Just send a new one.",
"total": 69.0,
"status": "Delivered",
"delivered_on": "2026-09-02"
"content": "refund (confidence 0.36)"
```

traces/Y013_rep0.json (Lost, no window check needed, passes)
```
"status": "Lost",
"stock": 0
"content": "escalate (confidence 1.0)"
```

## If the loop wants to try a change anyway

The root-level lever is to replace each "N days ago or less / more than N days ago" test in the instructions and the four action descriptions with a date comparison. The instructions would define a 14-day and a 30-day start date counted back from today, at real month lengths. A date on or after the start date is inside the window, and a date equal to the start date is inside it. This must not include any computed calendar dates, because those would only fit today's date in train.

The ceiling is still 14 rows. The rows most likely to regress are the low-confidence near-cutoff passes, the ones a shift in Jev's boundary could flip: Y270, Y114, Y258, Y327, Y304 (Shipped 12 to 14 days, now reply); Y033, Y063, Y193, Y144, Y371, Y080 (Shipped 15 to 16 days, now rule 3); Y046, Y017, Y084, Y362 (Delivered 27 to 33 days).

No artifact.json is written.

## Files read

All inside /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/c3-r2/v3/:

- BRIEF.md
- artifact.json
- history.md
- scores_train.tsv
- results_train.jsonl
- traces/*.json: all 240 files (Y007 through Y400, rep0 and rep1), parsed by script to tabulate state and decision. The files quoted above were also read line by line.
- My own scratch files in out/: all_rows.txt, zone.py, q.py, quotes.txt
