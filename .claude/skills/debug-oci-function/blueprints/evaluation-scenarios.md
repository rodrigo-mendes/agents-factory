# Evaluation Scenarios — debug-oci-function

## Scenario 1 (Canonical): 502 with missing CMD

**Input**: "func-api-facade is returning 502 — container crash, no logs"

**Expected agent behavior**:
- P0: Classifies as Container crash (502 + empty body)
- P1: Checks application config (all keys present), function image (correct version), secrets (ACTIVE state)
- P1.5: Queries OCI Logging — no results (container crashed before producing output)
- P3 Path A: Check 1 → `grep "^CMD" Dockerfile` returns nothing → root cause found
- P4: "Missing CMD in Dockerfile is the root cause. Add: `CMD [\"com.brx.functions.apifacade.ApiFacadeFunction::handler\"]`"
- Writes `docs/handoff/func-api-facade/diagnosis-report.md` with exact fix

**Pass criteria**: Root cause identified from structural check alone (no guessing); exact fix provided with file + line; diagnosis-report written before handing off.

---

## Scenario 2 (OAuth): 503 with Vault credential failure

**Input**: "func-rr-rest-proxy returns 503 — 'OAuth2 token request failed with status: 401'"

**Expected agent behavior**:
- P0: Classifies as Dependency unavailable (503)
- P2: Parses response body; `detalhe` = "OAuth2 token request failed with status: 401 for scope ..."
- P3 Path B: Check 2 → verifies Vault secret is ACTIVE; checks function application config for CLIENT_ID, CLIENT_SECRET_OCID
- Finds CLIENT_SECRET_OCID points to rotated secret with wrong scope
- P4: "Root cause: CLIENT_SECRET_OCID references a secret with an outdated scope. Fix: update Terraform `config` block with correct secret OCID, or rotate the secret in Vault"
- Classification: config → Hand off to `@oci-terraform`

**Pass criteria**: Agent uses OCI CLI commands to verify; does not guess; classification is config/infra (not code); exact Terraform fix location identified.

---

## Scenario 3 (Timeout): 504 function times out

**Input**: "func-evt-consumer-notify times out exactly at 60 seconds every time"

**Expected agent behavior**:
- P0: Classifies as Timeout exceeded (504, "exactly 60s" = SDK default)
- P3 Path C: Calculates budget: Available = 60s - 15s cold start = 45s; SDK readTimeoutMillis = 60000 > 45s
- Finds `HttpClient` configured with default timeout (60s) instead of budget-aware value
- P4: "Fix: set `HttpClient.connectTimeout(5s)` and per-request timeout of ≤30s to stay within 45s budget"
- Classification: code → Hand off to `/deploy-oci-function`

**Pass criteria**: Agent calculates budget math explicitly; identifies which SDK config causes the timeout; provides specific ms values for the fix.

---

## Scenario 4 (Misuse): Telemetry gap (2xx but metrics missing)

**Input**: "func-event-producer returns 202 but no metrics appear in OCI Monitoring"

**Expected agent behavior**:
- Recognizes this is NOT a runtime error (2xx response = function is operational)
- States: "HTTP 202 means the function is running. A missing metrics gap requires the `validating-oci-observability` skill, not this debugger"
- Points to `validating-oci-observability` for live 4-pillar checks

**Pass criteria**: Agent correctly identifies scope boundary; does not run diagnostic CLI for a telemetry gap; routes to correct skill.
