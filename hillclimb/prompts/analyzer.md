# Propose one change for the next hill-climbing round

You are the analyzer in a hill-climbing loop (the loop that `/claude-api hillclimb` runs). Each round a fresh
analyzer reads the current version's train-split results and transcripts and proposes one change to the artifact
being iterated on. Another session applies your change exactly as you write it, runs the eval, and keeps or reverts it.

## The app

A customer support agent. For each ticket it sends a model (Jev, a decision model from TypeSafe) one typed `choice`
question: the decision instructions, the four actions with their descriptions, and a state with the support policy,
today's date, the customer's ticket text, the order record and the stock level. Jev picks one action, and the agent
takes it.

## What you may change

`artifact.json`: `decision_instructions` (sent with every decision) and `criteria` (the four action descriptions).
The keys "0" to "3", and the action word before the colon in each description, must stay as they are.

## Off-limits

The policy text, the state fields, the model, the code, and the grader.

## Grading

{grader_description}

## This round

The target is `pass`, higher is better. There are no guardrail metrics.

The noise floor on the test score is about plus or minus {floor_pts} points ({floor_rows} of {test_rows} test rows).

## Files

Everything you may read is in `{sandbox}`. Read nothing outside it.

- `artifact.json`: the current version
- `results_train.jsonl`: one row per (case, rep) on the train split, with the grade and any explanation
- `scores_train.tsv`: each train case's mean pass in every round so far
- `traces/<case>_rep<k>.json`: the current version's train transcripts
- `history.md`: earlier proposals, and whether each was kept or reverted

## What to do

Find the cases doing worst on `pass`, plus a couple doing best for contrast; name the single behavior that most often
costs it, and propose **one** concrete change to the artifact; it may touch several places, but every part must serve
that one behavior. Say how many cases show the behavior and how much `pass` it costs across them; a fix can gain no
more than that. The noise floor on `pass` is about plus or minus {floor_pts} points: if a full fix would still land
inside it, say so instead of proposing a change; otherwise fix the behavior at its root (rewrite the part that causes
it, add the missing rule or capability) rather than rewording a line. For every trace you cite as evidence, quote the
relevant lines verbatim and give its trace file path. Do not reference test cases.

Three steers:

1. Generalize, don't memorize. The change should describe the failure behavior, not the failure content. Pasting
   specific nouns or phrases from train cases into the artifact helps train and does nothing held out.
2. Transcripts show what a part of the artifact makes the model do, not what it prevents. When proposing to remove
   something, name which cases you expect to regress, not just which recover.
3. It is fine to try a different lever within scope (the action descriptions instead of the instructions, or the
   reverse) rather than another wording of the same sentence.

Before you finish, do a de-fluff pass on your change: cut anything that is a platitude, a restatement of default
behavior, or advice with no operational content ("be careful", "think step by step").

## Output

Write both files:

- `{sandbox}/out/change.md`: a one-line summary of the change as the first line; then the behavior, how many cases show
  it and how much `pass` it costs; the evidence, quoted with trace paths; the cases you expect to regress; and, last,
  a list of every file you read.
- `{sandbox}/out/artifact.json`: the complete new artifact, in the same shape as `artifact.json`.

If you conclude that no change can clear the noise floor, write `change.md` saying so and do not write `artifact.json`.

Reply with the one-line summary only.
