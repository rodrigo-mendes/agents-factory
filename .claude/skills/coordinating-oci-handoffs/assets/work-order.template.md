---
kind: work-order
from: "@<source-agent>"
to: "@<target-agent>"
capability: <capability-slug>
stream: <a-java | b-terraform-infra | c-terraform-integration>
dependsOn: <none | [stream-a, stream-b]>
status: pending
createdAt: <ISO 8601 — placeholder OK if writer has no Bash>
---

## Scope

Brief description of what this stream accomplishes.

## Components

- [ ] Component 1 — description
- [ ] Component 2 — description

## Constraints

- Naming conventions to follow
- Resource sizing limits
- Security boundaries

## Dependencies

What must already exist before this stream can execute:
- Existing resources to reference
- Outputs from other streams (stream-c only)

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
