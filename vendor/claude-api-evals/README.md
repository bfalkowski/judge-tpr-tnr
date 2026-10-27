# Vendored: claude-api skill, eval files

Unmodified copies of three files from the `claude-api` skill in [anthropics/skills](https://github.com/anthropics/skills),
licensed under Apache 2.0 (see `skills/claude-api/LICENSE.txt`). They are kept here because the hill-climbing study in
`hillclimb/` follows them and the upstream files can change. The commit, each file's git blob hash and SHA-256 are in
`SOURCE.json`; `tests/test_judge.py` fails if a copy is edited.

- `skills/claude-api/shared/evals/eval-hillclimb.md`: the loop that `/claude-api hillclimb` runs. The study follows it.
- `skills/claude-api/shared/evals/eval-audit.md`: the eval health checklist the loop runs before round 1.
- `skills/claude-api/shared/evals/build-eval.md`: how `/claude-api build-eval` builds and validates a grader.

How the study follows and departs from the loop: `hillclimb/DESIGN.md`.
