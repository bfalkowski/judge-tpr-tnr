# The loop has stalled: categorize the remaining failures

You are an analyzer in a hill-climbing loop (the loop that `/claude-api hillclimb` runs). The test score has not
cleared the noise band for two rounds, so this round makes no change. Instead, bucket every remaining train-split
failure by root cause, reading each transcript far enough to tell which.

## The app

A customer support agent. For each ticket it sends a model (Jev, a decision model from TypeSafe) one typed `choice`
question: the decision instructions, the four actions with their descriptions, and a state with the support policy,
today's date, the customer's ticket text, the order record and the stock level. Jev picks one action, and the agent
takes it. The artifact being tuned is `artifact.json`: the decision instructions and the four action descriptions.

## Grading

{grader_description}

## Buckets

| Bucket | Tell |
|---|---|
| artifact_gap | The model never had the rule or fact it needed in the artifact; the transcript shows it guessing |
| grader_disagreement | The agent's action looks correct to you under the policy, but the grader marks it wrong; or the policy and the grader ask for different things |
| harness | The case errored before the model produced a scorable output |
| structural | The rule exists in the artifact but the model did not apply it; or the same failure recurs across rounds despite content aimed at it |
| variance | The case passes in one rep and fails in the other with the same artifact |

## Files

Everything you may read is in `{sandbox}`. Read nothing outside it: `artifact.json`, `results_train.jsonl`,
`scores_train.tsv`, `traces/`, `history.md`.

## Output

Write `{sandbox}/out/categorize.json`:

```json
{"counts": {"artifact_gap": 0, "grader_disagreement": 0, "harness": 0, "structural": 0, "variance": 0},
 "failures": [{"case": "<case id>", "rep": 0, "bucket": "<bucket>", "reason": "<one line>"}]}
```

with one entry for every train row whose `pass` is 0. Then write `{sandbox}/out/change.md`: the counts, one line on
what each non-empty bucket needs instead of another content round, and, last, a list of every file you read.

Reply with the counts only.
