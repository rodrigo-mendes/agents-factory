---
kind: report
from: "@oci-deployer"
to: "@oci-debugger"
refs: <report-java.md | report-terraform-integration.md | diagnosis-report.md>
capability: <capability-slug>
outcome: <success | partial | failed>
createdAt: <ISO 8601>
---

## What changed

- Built + pushed image: `gru.ocir.io/<ns>/serverless-app/<function>:<version>`
- Updated `infra/environments/<env>/terraform.tfvars` image ref
- `terraform apply` — <N> change(s)

## Resources / OCIDs

- Image: `<function>:<version>`
- Function OCID: `ocid1.fnfunc...`
- App OCID: `ocid1.fnapp...`
- Endpoint: `https://<gw>/<path>`

## Validation

- Smoke test → HTTP <status> body: `<body>`
- Observability validation → <passed | failed | not run>

## Acceptance status

- [ ] Smoke test 2xx/400 → ✅ / ❌

## Next action

<On success> Deploy complete — no handoff needed.
<On failure> Hand off: run `/debug-function` (`@oci-debugger`) — <symptom> needs diagnosis. Context: this file.

## Open issues / blockers

- Auto-fix cycles attempted: <list what was tried, or "none">.
