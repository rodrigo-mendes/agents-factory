---
kind: review
id: review-<nn>
from: <reviewer-agent>
to: <orchestrator-or-author-agent>
change: <change-id>          # profile scope_key: `change` or `capability`
task: <task-id>
refs: [<report-id>]
requirements: [R1]
outcome: approved            # approved | changes-requested
createdAt: <ISO 8601 UTC>
---

## Findings

Read-only review of the diff. One line per finding: `SEVERITY file:line - problem - fix`.

- HIGH <file>:<line> - <problem> - <required fix>
- MEDIUM <file>:<line> - <problem> - <fix or justification accepted>
- LOW <file>:<line> - <suggestion>

Any HIGH means `outcome: changes-requested`.

## ADR check

- <ADR id>: respected | violated (a violation is always HIGH) | not applicable
