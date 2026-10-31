---
kind: report
from: "@<source-agent>"
to: "@<consuming-agent>"
refs: <work-order-or-report-this-answers>.md
capability: <capability-slug>
outcome: <success | partial | failed | needs-input>
createdAt: <ISO 8601>
---

<!-- File name: result-java.md | result-terraform-infra.md | result-terraform-integration.md | result-observability.md.
     Naming convention: result-<role>.md, never a name starting with "report" (a write guard was
     observed, unverified); the kind inside the frontmatter stays `report`. -->

## What changed

- Files created/modified (paths)

## Resources / OCIDs

- Image tag, function OCID, vault/bucket/api-deployment OCIDs (or "none")

## Validation

- Command run → result (e.g. `mvn compile` → ✅, smoke test → HTTP 400)

## Acceptance status

- [ ] Criterion 1 → ✅ / ❌
- [ ] Criterion 2 → ✅ / ❌

## Next action

Hand off: run `/<command>` (`@<agent>`) — <one-line why>. Context: this file.

## Open issues / blockers

- None.
