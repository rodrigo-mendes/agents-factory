---
kind: review
id: review-<nn>
from: quarkus-code-reviewer       # or stripe-advisor (orchestrator wraps its notes)
to: building-quarkus-aws-saas
change: <change-id>
task: <task-id>                   # added by the orchestrator when it saves the record
# role: stripe   # Stripe tasks only
refs: [wo-<nn>-review]
requirements: [R1]
outcome: approved                 # approved | changes-requested (any HIGH or open MEDIUM => changes-requested)
round: <n>
createdAt: <ISO 8601 UTC>
---

## Summary

Files reviewed, ADRs checked, skills applied, counts per severity.

## Traceability

| Requirement | Scenario | Test (file:line) | Status |
|---|---|---|---|
| R1 | <scenario> | `<File>.java:<line>` | covered / missing |

## Findings

One block per finding; `Findings` is the section the profile requires. ADR violations are HIGH.

### F1 HIGH - <title>
- Location: `path/File.java:42`
- Evidence: <quoted line or grep result>
- Violates: <rule | skill + Never-Do item | ADR NNN | scenario>
- Fix hint: <smallest change; no rewrite>

## Caveats

`(unverified)` items relied on; areas not reviewed and why (the reviewer cannot run builds).
