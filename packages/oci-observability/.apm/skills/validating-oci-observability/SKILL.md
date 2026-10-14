---
name: validating-oci-observability
description: "Validates LIVE observability of OCI serverless workloads across 5 pillars (Logging, Metrics, APM Traces, Alarms, Dashboards render-readiness) via OCI CLI and executable scripts. Use when validating after deploy, diagnosing missing logs/metrics/traces/alarms or blank dashboards, or proving end-to-end alarm→notification flow."
---

## Version Context

**Technology**: OCI CLI + OCI Observability stack
**Target Version**: OCI CLI 3.x (current stable); Terraform OCI provider >= 5.x
**Support Status**: Active (OCI CLI 3.x is current stable as of 2026)
**Runtime Requirements**: `jq` >= 1.6; `git` (used to locate repo root); Bash 4+

**Key API / namespace facts (version-locked)**:
- Alarm dimensions valid for `oci_faas`: `applicationId` (Application OCID) or `resourceId` (Function OCID) — `functionId` does NOT exist
- MQL filter `httpStatusCode =~ "5.."` does NOT match; use `httpStatusCategory = "5xx"` or exact `httpStatusCode = "500"`
- APM OTLP ingestion endpoint: `/20200101/opentelemetry/private/v1/traces` — NOT `/20200101/observations/private`
- OCI session token TTL: ~1 hour; renew before long-running tests (alarm test ~8 min)

⚠️ **Version Lock**: Patterns target OCI CLI 3.x. Do not mix alarm dimension names from older documentation.

## Quick Navigation

- **[Decision Guide — which script to use](#decision-guide--which-script-to-use)**
- **[Script Reference](#script-reference)**
- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅ Always Do / ⚠️ Ask First / 🚫 Never Do
- **[Diagnostic Recipes — validated gotchas](#diagnostic-recipes--validated-gotchas)**
- **[Integration](#integration)**
- **[External Resources](#external-resources)**
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**

---

## Prerequisites

- Active OCI session (token expires ~1h; renew before long tests such as alarm test):
  `oci session authenticate --profile poc --region sa-saopaulo-1`
- `jq` installed; `git` (used to locate the repo).
- Access to `terraform output` from `infra/environments/dev` (scripts read via `terraform output -json`, with fallback to OCIDs from state).
- Env overrides: `OCI_PROFILE` (poc), `OCI_REGION` (sa-saopaulo-1), `TF_DIR`, `LOOKBACK_MIN` (15).

---

## Decision Guide — which script to use

| Situation | Script |
|-----------|--------|
| Just deployed; want to validate everything | `validate-observability.sh` |
| Traffic already exists; revalidate without generating load | `validate-observability.sh --no-smoke` |
| Suspect ONE specific pillar | `check-logs.sh` / `check-metrics.sh` / `check-traces.sh` / `check-alarms.sh` |
| Dashboard imported but widget blank / "adding widget" | `check-dashboards.sh` (5th pillar — render-readiness) |
| Need to populate dashboards with data before validating | `scripts/generate-dashboard-traffic.sh` (bundled — run BEFORE `check-dashboards.sh`) |
| Need to generate traffic only (warm up / generate telemetry) | `smoke-invoke.sh` |
| Prove alarm fires and sends email | `trigger-alarm-test.sh` |
| Build + push + apply + end-to-end validation | `deploy-and-validate.sh` |

Base path: `.claude/skills/validating-oci-observability/scripts/`.

---

## Script Reference

### `validate-observability.sh` — orchestrator (entry point)
- **When**: general post-deploy validation; CI/CD gate.
- **How**: `./validate-observability.sh [--no-smoke] [--wait SEC]` (default: generates traffic, waits 120s, validates 4 pillars).
- **Reads**: `terraform output` (URLs, OCIDs), OCI profile.
- **PASS**: final table with no FAIL; `exit 0`. FAIL on metrics/traces → see diagnostic recipes below.

### `smoke-invoke.sh` — traffic generator
- **When**: warm cold start / produce logs, metrics, and traces before validating.
- **How**: `./smoke-invoke.sh [N_REPEAT]` (default 3 per route).
- **Reads**: `api_base_url` from outputs.
- **PASS**: HTTP 2xx expected per route. Does not depend on ingestion.

### `check-logs.sh` — Logs pillar
- **When**: confirm service invoke logs are capturing entries.
- **How**: `./check-logs.sh` (window `LOOKBACK_MIN`).
- **Reads**: `log_group_id`, compartment. Uses `oci logging-search`.
- **PASS**: ≥1 entry; bonus: structured fields (`opcRequestId`, `service`).

### `check-metrics.sh` — Metrics pillar
- **When**: confirm `oci_faas` (platform) + custom namespaces.
- **How**: `./check-metrics.sh`.
- **Reads**: application/function OCIDs; custom namespaces.
- **PASS**: datapoints > 0 in `oci_faas` and custom namespaces. Diagnoses alarm dimension (`applicationId`).
- **Common failure**: custom empty → see recipe *Custom metrics empty*.

### `check-traces.sh` — Traces pillar
- **When**: confirm span ingestion in APM.
- **How**: `./check-traces.sh`.
- **Reads**: `apm_domain_id`; app config; `oci_apm` metrics.
- **PASS**: `IngestedBytes>0` and `PayloadRejections=0`. Also checks APM_* in config.
- **Common failure**: rejections → see recipe *Missing traces*.

### `check-alarms.sh` — Alarms/Notification pillar
- **When**: confirm alarms enabled + subscription confirmed.
- **How**: `./check-alarms.sh`.
- **Reads**: compartment, `notification_topic_id`.
- **PASS**: alarms enabled + status; subscription `ACTIVE`.
- **Common failure**: subscription `PENDING` → confirm the email sent by OCI.

### `check-dashboards.sh` — Dashboards pillar (5th · render-readiness)
- **When**: dashboard imported but Console shows blank widget or "internal error while adding widget".
- **How**: `./check-dashboards.sh [--name-filter "REST Proxy"]`.
- **Reads**: compartment; lists `management-dashboard dashboard`/`saved-search`.
- **Validates**: dashboard `ACTIVE`; each saved-search has `widget-template`+`widget-vm` (non-empty); `data-config[].type` ∈ {`monitoringDataSource`, `tracesDataSource`}; metric widget declares **`regionName`** parameter (absent → blank — postmortem P10); cross-checks ingestion (oci_faas + custom namespace have datapoints).
- **PASS**: no FAIL. WARN = function has no traffic (run `scripts/generate-dashboard-traffic.sh`).

### `trigger-alarm-test.sh` — proves alarm→FIRING→email
- **When**: prove metric→alarm→notification end-to-end. **Injects real errors in dev.**
- **How**: `./trigger-alarm-test.sh [N_ERRORS] [POLL_MAX_MIN]` (default 15, 8). Needs ~8 min of continuous OCI session.
- **Reads**: `api_base_url`; polls `alarm-status`.
- **PASS**: alarm (apigw-5xx / fn-errors) transitions to `FIRING`. Alarm returns to OK on its own after errors stop.

### `deploy-and-validate.sh` — full runbook
- **When**: end-to-end build → push → `terraform apply` → validation cycle.
- **How**: `./deploy-and-validate.sh [--skip-build] [--plan-only]`. Requires Docker + OCI session + `services/.env`.
- **Reads**: `services/*/func.yaml` (tags), OCIR, `terraform`.
- **PASS**: apply OK + `validate-observability.sh` with no FAIL.

### `generate-dashboard-traffic.sh` — dashboard-traffic precondition
- **When**: dashboard widgets are blank or show "adding widget"; run BEFORE `check-dashboards.sh` to ensure time-series data exists.
- **How**: `./generate-dashboard-traffic.sh [--rounds N] [--sleep SEC] [--url API_BASE_URL]`
- **Parametrized**: all values exposed as env vars (`ROUNDS`, `SLEEP`, `API_BASE_URL`, `TF_DIR`, `SIM`) or CLI flags. No hardcoded OCIDs or profile names.
- **Reads**: `api_base_url` from `terraform output` (fallback: `--url` flag or `API_BASE_URL` env var).
- **PASS**: rounds complete with HTTP responses logged per wave. Wait ~3 min after completion before validating.
- **Note**: `simulate-webhook.sh` is optional; the script falls back to `curl` if not present.

### `lib-common.sh` — shared library (DO NOT execute directly)
`source`-d by the other scripts: config (profile/region/compartment), color/assert helpers, `tf_out`, repo resolution via `git`. Edit here to change all scripts.

---

## Verification Loop

Run the orchestrator to validate the deployed observability stack end-to-end:

```bash
cd .claude/skills/validating-oci-observability/scripts

# Full post-deploy validation (generates traffic, waits, checks 4 pillars)
./validate-observability.sh              # expected exit code 0 = PASS (final table, no FAIL)

# Re-validate an environment that already has traffic (no synthetic invocations)
./validate-observability.sh --no-smoke   # expected exit code 0 = PASS

# Dashboard render-readiness (5th pillar, not covered by the orchestrator)
./check-dashboards.sh                    # expected exit code 0 = PASS
```

A non-zero exit means at least one pillar FAILed — see [Diagnostic Recipes](#diagnostic-recipes--validated-gotchas). Requires an active OCI session (see Prerequisites).

---

## Blueprints & Guardrails

### ✅ Always Do

- Run `validate-observability.sh` as a CI/CD gate after every observability-touching deploy (`exit != 0` breaks the pipeline).
- Renew the OCI session token before running `trigger-alarm-test.sh` — the test takes ~8 min and token TTL is ~1 hour.
- Use `--no-smoke` when replaying against an environment that already has traffic — prevents polluting metrics with synthetic invocations.
- Check `lib-common.sh` first when `tf_out` or profile/region resolution fails — it is the single source of config for all scripts.
- Use `check-dashboards.sh` separately from `validate-observability.sh` — dashboard render-readiness requires the 5th pillar check, which is not included in the 4-pillar orchestrator.
- Confirm subscription is `ACTIVE` (not `PENDING`) before trusting alarm→notification results.

### ⚠️ Ask First

**Validate all pillars vs. targeted pillar**
- All pillars: `validate-observability.sh` — use for post-deploy gate or full health check.
- Single pillar: individual scripts — use when a specific signal is missing and you want to avoid triggering smoke traffic.
- Ask: "Is this a post-deploy gate check, or targeted diagnosis of a specific pillar?"

**Generate traffic before validating vs. validate existing traffic**
- Generate traffic: default `validate-observability.sh` (calls `smoke-invoke.sh`).
- Validate only: `validate-observability.sh --no-smoke`.
- Ask: "Does the environment currently have recent traffic? Generating unnecessary smoke invocations can skew metrics."

**Full deploy cycle vs. validation only**
- Full cycle: `deploy-and-validate.sh` — rebuilds Docker image, pushes, applies Terraform, then validates.
- Validation only: `validate-observability.sh` — use when infra is already up-to-date.
- Ask: "Has the infra or function image changed since the last deploy? If not, skip `deploy-and-validate.sh`."

**Dashboard validation scope**
- Single dashboard: `check-dashboards.sh --name-filter "<name>"`.
- All dashboards: `check-dashboards.sh` (no filter) — may be slow in compartments with many dashboards.
- Ask: "Is the issue specific to one dashboard or are all dashboards blank?"

### 🚫 Never Do

**Never skip the alarm dimension validation before assuming alarm config is correct**
```bash
# 🚫 WRONG — uses non-existent dimension
--query-text 'FunctionErrorCount[1m]{functionId = "<ocid>"}.sum()'

# ✅ CORRECT — valid dimensions are applicationId or resourceId
--query-text 'FunctionInvocationCount[1m]{applicationId = "<fnapp-ocid>"}.sum()'
```
Impact: alarm silently never fires; no error returned by OCI.

**Never use regex MQL filter for HTTP status**
```bash
# 🚫 WRONG — regex does not match in OCI MQL
httpStatusCode =~ "5.."

# ✅ CORRECT — use category or exact match
httpStatusCategory = "5xx"
# or: httpStatusCode = "500"
```
Impact: alarm never fires on 5xx responses.

**Never post OTLP spans to the observations endpoint**
```java
// 🚫 WRONG — traces silently rejected
exporter.setEndpoint(".../20200101/observations/private")

// ✅ CORRECT — OTLP endpoint
exporter.setEndpoint(".../20200101/opentelemetry/private/v1/traces")
```
Impact: `PayloadRejections>0`, `IngestedBytes=0`; no error in function logs.

**Never execute lib-common.sh directly**
```bash
# 🚫 WRONG
./lib-common.sh

# ✅ CORRECT — source it from another script
source ./lib-common.sh
```
Impact: script exits immediately with no useful output; config is not applied.

---

## Diagnostic Recipes — validated gotchas

All confirmed LIVE against OCI, contradicting the documentation:

### Custom metrics empty (namespace without datapoints)
Cause: `MonitoringClient` missing the **ingestion** endpoint → `PostMetricData` fails SILENTLY.
- Fix: `client.setEndpoint("https://telemetry-ingestion.<region>.oraclecloud.com")` after `build(provider)` (see `monitoring-oci-java-functions`).
- Verify: `oci monitoring metric list --compartment-id <cid> --namespace <custom_ns>` → empty ⇒ post is not reaching OCI.

### Missing traces in APM
Cause: OTLP exporter pointing to wrong endpoint.
```bash
oci monitoring metric-data summarize-metrics-data --compartment-id <cid> \
  --namespace oci_apm --query-text 'PayloadRejections[1m].sum()' --start-time <ISO> --end-time <ISO>
```
`RejectionCause=MISSING_DATA_FORMAT` ⇒ posting OTLP to `/20200101/observations/private`. Correct: `/20200101/opentelemetry/private/v1/traces` (SDK `OtlpHttpSpanExporter`). Ingestion OK = `IngestedBytes>0`.

### oci_faas alarm never fires
Cause: wrong dimension. Valid: **`applicationId`** (Application OCID) or **`resourceId`** (Function OCID) — **`functionId` does not exist**. `FunctionErrorCount` only counts execution failures (not handled 500s).
```bash
oci monitoring metric-data summarize-metrics-data --compartment-id <cid> --namespace oci_faas \
  --query-text 'FunctionInvocationCount[1m]{applicationId = "<fnapp-ocid>"}.sum()' ...
```

### apigw-5xx alarm never fires
Cause: regex filter. In OCI MQL `httpStatusCode =~ "5.."` **does NOT match**. Use `httpStatusCategory = "5xx"` (or `httpStatusCode = "500"` exact) on metric `HttpResponses` (namespace `oci_apigateway`).

### Subscription PENDING
Alarm fires but does not notify until the email link is clicked. Verify: `oci ons subscription list ... | jq '.data[].["lifecycle-state"]'` = `ACTIVE`.

---

## Integration

- **Post-deploy**: `oci-deployer` (P5) runs `validate-observability.sh`; or use `deploy-and-validate.sh`.
- **CI/CD**: `validate-observability.sh --no-smoke` as gate (failure → `exit != 0` breaks the pipeline).
- **Debug**: `oci-debugger` delegates here when the function returns 2xx but telemetry is missing.

---

## Cross-references

- Code instrumentation: `observing-oci-java-functions`, `monitoring-oci-java-functions`, `logging-oci-java-functions`, `monitoring-oci-apm`.
- Design/provisioning: `configuring-oci-monitoring-alarms`, `provisioning-oci-logging`, `provisioning-oci-apm`, `provisioning-oci-api-gateway`.
- Gotcha source of truth: the **[Diagnostic Recipes](#diagnostic-recipes--validated-gotchas)** section above (self-contained).

---

## External Resources

- [OCI CLI Command Reference](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/) — logging-search, monitoring, ons commands (verified 2026-07-26)
- [OCI Logging Search docs](https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/loggingoverview.htm) — log query syntax (verified 2026-07-26)
- [OCI Monitoring MQL reference](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Reference/mql.htm) — dimension names, filter operators (verified 2026-07-26)
- [OCI APM OTLP ingestion](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/configure-open-standards-tracing.html) — correct endpoint paths (verified 2026-07-26)
- [OCI Notifications ONS](https://docs.oracle.com/en-us/iaas/Content/Notification/Concepts/notificationoverview.htm) — subscription lifecycle states (verified 2026-07-26)
- [OCI Pricing](https://www.oracle.com/cloud/pricing/) — current pricing for Logging, Monitoring, APM (verified 2026-07-26)
