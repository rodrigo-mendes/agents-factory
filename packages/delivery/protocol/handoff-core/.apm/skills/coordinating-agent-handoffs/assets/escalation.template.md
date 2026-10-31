---
kind: escalation
id: escalation-<nn>
from: <orchestrator-agent>
to: user
change: <change-id>          # profile scope_key: `change` or `capability`
task: <task-id>
limit: <limit name that was reached, e.g. review_rounds>
refs: [<ids of the records of each attempt>]
status: open                 # open | answered
createdAt: <ISO 8601 UTC>
# when the user answers: set `status: answered` and add `answeredAt: <ISO 8601 UTC>`;
# the answer is recorded verbatim under "## Answer". Answering resets the counter of that task.
---

## Attempts

1. Attempt 1 - what was tried, which record holds it.
2. Attempt 2 - ...

## Evidence

- The error or finding that persists: command output, `file:line`.

## Hypothesis

Most likely cause, and how confident (evidence, not intuition).

## Options

- A: <concrete option> - impact: <cost, risk, what changes in the spec or ADRs>
- B: <concrete option> - impact: ...
- C (optional): ...

## Answer

(filled in verbatim with the user's reply)
