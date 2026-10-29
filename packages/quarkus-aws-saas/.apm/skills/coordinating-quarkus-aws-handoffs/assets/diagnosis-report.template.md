---
kind: diagnosis-report
id: diagnosis-<nn>
from: aws-lambda-debugger         # returned inline; the orchestrator saves it and adds `task`
to: building-quarkus-aws-saas
change: <change-id>
task: deploy                      # added by the orchestrator, copied from the debug work-order (deploy for an E7 diagnosis)
refs: [result-<nn>-deploy]
requirements: [R1]
outcome: success                  # success = root cause found | partial | failed = not determined | needs-input
spec_impact: none                 # none | divergence | ambiguity (set by the orchestrator when the proposed fix changes behaviour)
debug_rounds: <n>
createdAt: <ISO 8601 UTC>
---

## Symptom

What was observed (status, error text), entry type, window, function, executed version.

## Verdict

Branch letter of `debugging-aws-lambda` and one root cause, or `not determined` with the next read-only step.

## Evidence

- Command (allowlisted) -> redacted output -> what it proves. RequestId, REPORT fields, metric values.

## Confidence

high | medium | low, with the reason; every `(unverified)` / `(medium confidence)` tag relied on, kept exactly.

## Fix work-order proposal

- Fix required: <exact setting, line or file>
- Owner: code | infra | deploy
- Reason: <branch, evidence>
- Risk: <...>
- Verify after: <read-only checks>

## Suggested next step

<owner role> applies the fix through a new work-order; the orchestrator routes. Context: this file.
