# Evaluation Scenarios — deploy-oci-function

## Scenario 1 (Canonical): Successful deploy with version bump

**Input**: "Deploy the new version of func-event-producer with tag 0.0.5"

**Expected agent behavior**:
- P0: Validates Docker running, `.env` exists, OCI CLI session valid
- P1: Identifies target `services/func-event-producer/`; confirms func.yaml and Dockerfile exist
- P2: Runs all preflight checks — CMD in Dockerfile ✅, httpclient-jersey ✅, no secrets in func.yaml ✅
- P3: Builds image tag `0.0.5`; pushes to OCIR; logs "Done! Image URI: ..."
- P4: Updates `terraform.tfvars` with new image; runs `terraform plan` (shows 1 change); applies
- P5: Waits 5s; smoke tests endpoint; HTTP 202 = success
- Writes `docs/handoff/func-event-producer/deploy-report.md`

**Pass criteria**: Terraform plan shows exactly 1 change; smoke test returns 200/202/400; deploy-report written.

---

## Scenario 2 (Auto-fix): Deploy fails with 502, missing CMD

**Input**: "Deploy func-api-facade 0.0.3"

**Expected agent behavior**:
- P5: Smoke test returns HTTP 502 (empty body)
- P5.5 auto-fix: Matches pattern "502 + empty body" → `grep "^CMD" Dockerfile` fails
- Adds CMD instruction to Dockerfile matching func.yaml `cmd:` field
- Increments tag to 0.0.4, re-runs P3 → P4 → P5
- P5 retry: HTTP 400 "bucket_name is required" → ✅ function operational
- Reports auto-fix cycle in deploy-report

**Pass criteria**: Agent identifies root cause, fixes without user prompt, validates on retry; 2-cycle limit is respected.

---

## Scenario 3 (Rollback): Deploy fails twice, offers rollback

**Input**: "Deploy func-evt-consumer-notify 0.1.0" (unknown init error)

**Expected agent behavior**:
- P5: Smoke test returns HTTP 500 "Function init failed: unknown cause"
- P5.5: No pattern match found for error signal
- After 2 auto-fix cycles with no resolution: writes `deploy-report.md` with error details
- States: "Hand off to `/debug-function` for deeper diagnosis, or roll back to 0.0.9?"
- On user choosing rollback: reverts terraform.tfvars, applies, confirms rollback with smoke test

**Pass criteria**: Agent does not loop beyond 2 cycles; offers explicit choice; rollback verified with smoke test.

---

## Scenario 4 (Misuse): Request to create new infrastructure

**Input**: "Create a new OCI Application and subnet for func-new-feature"

**Expected agent behavior**:
- Identifies this as infrastructure creation, NOT deployment
- States: "This requires Terraform infrastructure — use `@oci-terraform` or `/add-functions-infra`"
- Does NOT create Terraform modules

**Pass criteria**: Agent declines scope correctly, routes to correct command, no Terraform code generated.
