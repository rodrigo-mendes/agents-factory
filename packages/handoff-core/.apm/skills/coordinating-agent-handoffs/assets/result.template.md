---
kind: report
id: result-<nn>-<role>
from: <author-agent>
to: <consumer-agent>
change: <change-id>          # profile scope_key: `change` or `capability`
task: <task-id>
refs: [<work-order-id>]
requirements: [R1]
outcome: success             # success | partial | failed | needs-input
spec_impact: none            # none | divergence | ambiguity
createdAt: <ISO 8601 UTC>
---

## Done

- What was implemented, per step or acceptance criterion.

## Evidence

- Command run -> result (build, tests, coverage). Paste the relevant output lines.

## Spec impact

- Implemented: <requirement ids>.
- Divergences: <behaviour that differs from the spec, or "none">.
- Ambiguities: <questions the spec does not answer, or "none">.
- Files: `<path/of/each/changed/file>`

## Suggested next step

<role or agent + one-line why>. Context: this file.
