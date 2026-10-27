Replace every "N days ago" condition in the instructions and all four action descriptions with a field-named comparison of shipped_on/delivered_on against the cutoff date, and spell out how to compare two dates (year, then month, then day), so Jev reads the branch off the date instead of estimating elapsed days.

## Behavior

Jev decides the date conditions by guessing elapsed days, and near a cutoff it guesses the wrong side. Every train case has today = 2026-10-01 (the fixed policy text says so), so the cutoffs are 2026-09-17 (14 days) and 2026-09-01 (30 days). Two failure shapes, both the same behavior:

- Damaged/wrong item, status Delivered, delivered_on 2026-09-02 to 2026-09-04 (27 to 29 days ago, on or after the 30-day cutoff, so refund): Jev answers escalate, as if delivered more than 30 days ago.
- Not arrived, status Shipped, shipped_on 2026-09-15 or 2026-09-16 (15 to 16 days ago, before the 14-day cutoff, so reship or refund): Jev answers reply, as if shipped 14 days ago or less.

All 240 rows have `"output_tokens": 0`, so the v2 "Step 1: work out two cutoff dates" is never carried out as written work. What Jev sees at decision time is still the elapsed-days wording: v2's Step 2 says "Delivered 30 days ago or less: refund. More than 30 days ago: escalate" and "shipped 14 days ago or less, reply", and the four action descriptions say the same. None of these name which date field to use. Confidence on every failing row is low (0.33 to 0.64).

The scores show the model is guessing rather than comparing. v1 and v2 moved the error from one side of each cutoff to the other instead of removing it (case means from scores_train.tsv, summed over the near-cutoff cases):

| Near-cutoff group | cases | v1 | v2 |
|---|---|---|---|
| Delivered damaged/wrong, 27 to 30 days (refund expected) | 7 | 6.0 | 2.0 |
| Delivered damaged/wrong, 31 to 33 days (escalate expected) | 3 | 0.0 | 3.0 |
| Shipped not-arrived, 12 to 14 days (reply expected) | 6 | 1.0 | 6.0 |
| Shipped not-arrived, 15 to 18 days (reship/refund/escalate expected) | 11 | 10.0 | 7.5 |

## How many cases, and the cost

11 of 120 train cases show it; they are all 17 failing rows.

- Fail both reps (6): Y007, Y017, Y046, Y084 (Delivered band, escalate instead of refund); Y033, Y333 (Shipped band, reply instead of reship).
- Fail one rep (5): Y188, Y331 (Delivered band); Y063, Y244, Y371 (Shipped band).

Cost: 6 x 1.0 + 5 x 0.5 = 8.5 case-points = 17/240 rows = 7.1 points of pass (v2 train is 223/240 = 92.9). A full fix can gain at most 7.1 points. That is only just outside the 6.5-point noise floor, so a partial fix will not show as a significant gain on test by itself. I propose the change anyway because this is the only failure behavior left on train, and the v1/v2 swing above shows the date logic is what moves this score. The part that is likely to read as signal is whether it stops the seesaw: both sides of each cutoff passing at once.

## The change

Root cause: every date condition is phrased as elapsed days ("30 days ago or less"), and a model that answers in one step with no output tokens has to estimate 27 vs 30 or 15 vs 14 days in its head. The fix removes elapsed days from the decision path completely:

1. Step 1 now says not to estimate days ago, and to decide only by comparing the record date with the cutoff date. It gives the comparison method (year, then month, then day; the first part that differs decides; equal counts as on or after). The existing worked example (today 2026-10-01, cutoffs 2026-09-17 and 2026-09-01) is extended to show what the method gives: which months fall on which side, and which day numbers within the cutoff month. Today comes from the fixed policy text, which is off-limits, and the general method is stated first, so a different today still works.
2. Step 2 names the field and the cutoff in each date branch ("delivered_on on or after the 30-day cutoff: refund", "shipped_on before the 14-day cutoff, rule 3"). It no longer says "N days ago". The (b) branch now names delivered_on, so Jev cannot read shipped_on against the 30-day cutoff. Most failing Delivered rows have a shipped_on in August, before the 30-day cutoff (for example Y007 shipped 2026-08-28, delivered 2026-09-03).
3. The four action descriptions use the same field-and-cutoff wording, so the descriptions do not reintroduce "N days ago". Nothing else changes: the request types, the Lost and Processing handling, the $500 step and the supervisor-demand line stay as they are.

## Evidence

Failing, Delivered band (expected refund, total $500 or less, delivered_on on or after the 2026-09-01 cutoff):

- traces/Y007_rep0.json: `\"ticket\": \"The bluetooth earbuds from order #5007 arrived damaged. I want this escalated.\"`, `\"total\": 79.0`, `\"status\": \"Delivered\"`, `\"shipped_on\": \"2026-08-28\"`, `\"delivered_on\": \"2026-09-03\"`, answer `"content": "escalate (confidence 0.63)"`
- traces/Y007_rep1.json: same record, `"content": "escalate (confidence 0.64)"`
- traces/Y017_rep0.json: `\"ticket\": \"I received the wrong item on order #5017. It is not the air purifier I ordered. Refund me.\"`, `\"total\": 500.0`, `\"status\": \"Delivered\"`, `\"shipped_on\": \"2026-08-30\"`, `\"delivered_on\": \"2026-09-04\"`, `"content": "escalate (confidence 0.45)"`
- traces/Y046_rep0.json: `\"ticket\": \"Order #5046 should have been my standing desk mat, but you sent something else. Just send a new one.\"`, `\"total\": 69.0`, `\"status\": \"Delivered\"`, `\"shipped_on\": \"2026-08-30\"`, `\"delivered_on\": \"2026-09-02\"`, `"content": "escalate (confidence 0.39)"`
- traces/Y084_rep1.json: `\"ticket\": \"My air purifier (order #5084) has a cracked housing and doesn't work. Just send a new one.\"`, `\"total\": 500.0`, `\"status\": \"Delivered\"`, `\"shipped_on\": \"2026-08-28\"`, `\"delivered_on\": \"2026-09-03\"`, `"content": "escalate (confidence 0.37)"`
- traces/Y188_rep0.json vs traces/Y188_rep1.json: same record (`\"status\": \"Delivered\"`, `\"shipped_on\": \"2026-09-02\"`, `\"delivered_on\": \"2026-09-04\"`, `\"total\": 99.0`) gives `"content": "escalate (confidence 0.37)"` on rep0 and `"content": "refund (confidence 0.35)"` on rep1. The answer is a coin flip.
- traces/Y331_rep1.json: `\"status\": \"Delivered\"`, `\"shipped_on\": \"2026-08-31\"`, `\"delivered_on\": \"2026-09-04\"`, `\"total\": 69.0`, `"content": "escalate (confidence 0.43)"`

Failing, Shipped band (expected reship or refund, shipped_on before the 2026-09-17 cutoff):

- traces/Y033_rep0.json: `\"ticket\": \"My portable monitor from order #5033 never came. Let me know the status.\"`, `\"total\": 299.0`, `\"status\": \"Shipped\"`, `\"shipped_on\": \"2026-09-16\"`, `\"stock\": 8`, `"content": "reply (confidence 0.39)"`
- traces/Y333_rep1.json: `\"ticket\": \"Order #5333 (espresso machine) hasn't arrived.\"`, `\"total\": 499.0`, `\"status\": \"Shipped\"`, `\"shipped_on\": \"2026-09-15\"`, `\"stock\": 3`, `"content": "reply (confidence 0.35)"`
- traces/Y063_rep0.json vs traces/Y063_rep1.json: `\"status\": \"Shipped\"`, `\"shipped_on\": \"2026-09-16\"`, `\"stock\": 2`; rep0 `"content": "reply (confidence 0.35)"`, rep1 `"content": "reship (confidence 0.48)"`
- traces/Y244_rep0.json: `\"status\": \"Shipped\"`, `\"shipped_on\": \"2026-09-15\"`, `\"stock\": 2`, `"content": "reply (confidence 0.52)"`
- traces/Y371_rep0.json vs traces/Y371_rep1.json: `\"ticket\": \"Order #5371 (ergonomic keyboard) hasn't arrived.\"`, `\"status\": \"Shipped\"`, `\"shipped_on\": \"2026-09-15\"`, `\"stock\": 0`; rep0 `"content": "reply (confidence 0.33)"`, rep1 `"content": "refund (confidence 0.43)"`

All of these traces contain the current worked example verbatim: `For example, when today is 2026-10-01 they are 2026-09-17 and 2026-09-01.` Jev has the correct cutoffs and still decides on the wrong side.

Contrast, passing cases far from a cutoff, with high confidence:

- traces/Y232_rep0.json: `\"status\": \"Delivered\"`, `\"delivered_on\": \"2026-08-10\"`, `"content": "escalate (confidence 0.99)"`
- traces/Y356_rep0.json: `\"status\": \"Delivered\"`, `\"delivered_on\": \"2026-09-25\"`, `"content": "refund (confidence 0.93)"`
- traces/Y222_rep0.json: `\"status\": \"Shipped\"`, `\"shipped_on\": \"2026-09-28\"`, `"content": "reply (confidence 1.0)"`
- traces/Y064_rep0.json: `\"status\": \"Shipped\"`, `\"shipped_on\": \"2026-09-02\"`, `"content": "reship (confidence 0.97)"`

The request-type logic, the Lost and Processing rules, and the $500 step are all working. Only the near-cutoff date decision fails.

## Cases I expect to regress

There are no removals, so the risk is that the new wording moves the bias near each cutoff back the other way, as v1 to v2 did. The rows at risk are the near-cutoff rows that v2 got right, most of them at low confidence:

- Shipped 12 to 14 days, reply expected (v1 failed 5 of these 6): Y273 (traces/Y273_rep0.json `"content": "reply (confidence 0.37)"`), Y258 (traces/Y258_rep0.json `"content": "reply (confidence 0.44)"`), Y304, Y114, Y282, Y327. They have shipped_on 2026-09-17 to 2026-09-19. The new text puts these days explicitly on the reply side ("day is 17 or higher"), which should protect them, but they are the first place to look if the score drops.
- Delivered 31 to 33 days, escalate expected (v1 failed all 3): Y318, Y179, Y138 (traces/Y138_rep1.json `\"delivered_on\": \"2026-08-29\"`, `"content": "escalate (confidence 0.6)"`). They have delivered_on in August, which the new text puts on the escalate side.
- Low-confidence passes on the right side of a cutoff: Y039 (traces/Y039_rep0.json `\"delivered_on\": \"2026-09-01\"`, `"content": "refund (confidence 0.49)"`; delivered exactly on the cutoff day), Y052 (traces/Y052_rep0.json `"content": "refund (confidence 0.32)"`), Y193 (traces/Y193_rep0.json `"content": "reship (confidence 0.43)"`), Y024 (traces/Y024_rep0.json `"content": "refund (confidence 0.43)"`), Y080, Y162, Y380.

If the same model still cannot compare dates without output tokens, the gain will be small. The lasting fix is outside this artifact's scope (categorization.md: precompute the day counts or the cutoff booleans in the state). That would be the next step if this round lands inside the noise.

## Files read

All paths are under /tmp/claude-0/-home-claude/40fc5258-ce58-5aa5-962d-6bf6187ebc29/scratchpad/sb/key/v3/

- BRIEF.md
- artifact.json
- history.md
- categorization.md
- scores_train.tsv
- results_train.jsonl
- out/ (directory listing only; it was empty)
- out/artifact.json (my own output, read back to check it)
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
