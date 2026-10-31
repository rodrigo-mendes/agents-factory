---
kind: work-order
id: wo-<nn>-<role>
from: <orchestrator-or-author-agent>
to: <assignee-agent>
change: <change-id>          # profile scope_key: `change` or `capability`
task: <task-id>
refs: []
requirements: [R1]
status: pending              # pending | in-progress | done | blocked | cancelled
createdAt: <ISO 8601 UTC>
---

## Scope

One or two sentences: what must exist when this work-order is done. One task, one ordered cycle.

## Skills

- <skill-name> - load these before starting; do not rely on conversation history.

## Requirements

- R1: <requirement text, copied from the spec> - scenarios: <scenario names>

## Constraints

- Decision records that apply (ADR ids), forbidden approaches, limits (timeouts, budgets).

## Acceptance criteria

- [ ] Each scenario of the linked requirements has a passing test.
- [ ] <measurable criterion with the command that proves it>
