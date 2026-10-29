---
kind: escalation
id: escalation-<nn>
from: building-quarkus-aws-saas
to: user
change: <change-id>
task: <task-id>
limit: <build_attempts | review_rounds | deploy_cycles | delta_revisions | record_rejections>
refs: [<ids of the record of each attempt>]
status: open                 # open | answered
createdAt: <ISO 8601 UTC>
# on the user's reply: status: answered + answeredAt: <ISO 8601 UTC>; the reply goes verbatim under ## Answer.
---

## Attempts

1. Attempt 1 - what was tried; record `<id>`.
2. Attempt 2 - ...

## Evidence

- The error or finding that persists: command output, `file:line`.

## Hypothesis

Most likely cause and the evidence behind it.

## Options

- A: relax the requirement - impact: <spec delta, scenarios dropped>
- B: new ADR / change of approach - impact: <ADR superseded, rework>
- C: accept the risk or raise the limit for this run - impact: <cost, risk> (run arg `limits.<name>=<n>`)
- D (optional): <...>

## Answer

(the user's reply, verbatim)
