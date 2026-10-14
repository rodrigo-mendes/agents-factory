---
name: provisioning-custom-dashboard-oci-observability
description: Provisions OCI custom Management Dashboards, APM domains, logging, and monitoring alarms with Terraform oracle/oci v8.x. Use when building observability infrastructure including APM tracing, log routing to Log Analytics, and metric-based alerting for OCI applications.
---

## Function
Specialist in OCI observability infrastructure: Management Dashboards, APM (tracing), OCI Logging, Monitoring Alarms, and Service Connector Hub routing — using Terraform oracle/oci v8.x.

## Version Context

**Technology**: Oracle Cloud Infrastructure (OCI) — oracle/oci Terraform Provider
**Target version**: v8.x (8.21.0 verified 2026-07-06)
**Release date**: 2026-07-02
**Support status**: Active

**Key resources in v8.x**:
- `oci_management_dashboard_management_saved_search` — CRUD lifecycle (added ~v8.6)
- `oci_monitoring_alarm` `overrides` block — multi-severity rules in one alarm
- `oci_apm_apm_domain` `log_group_id` — trace-to-log correlation

**Deprecated**: None in this version. Provider follows rapid release cycle (210 versions); pin `~> 8.0`.

⚠️ **CRITICAL — Version Lock**: This skill targets oracle/oci ~> 8.0 + Terraform >= 1.9.
Reject patterns from versions < 8.0. Do not mix with older provider schemas.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory HCL with full code examples
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions with trade-off matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with secure alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — APM ↔ Logging ↔ Dashboards ↔ Alarms
- **[Verification Loop](#verification-loop)** — Terraform validation commands
- **[Quick Reference](#quick-reference)** — Limits, namespaces, accepted values
- **[External Resources](#external-resources)** — Official OCI and Terraform docs

---

## Blueprints & Guardrails

### ✅ Always Do

For full HCL examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (Complex domain — all 9 required):

1. **Terraform config block with `~> 8.0` constraint** — Prevents breaking changes from provider rapid release cycle; use OCI Object Storage S3-compatible backend; prefer HCP Terraform or OCI Resource Manager for team state locking.
2. **Instance Principal / SecurityToken auth** — Never embed API keys in CI/CD; use `auth = "InstancePrincipal"` on OCI compute, `auth = "SecurityToken"` in pipelines.
3. **APM domain with `log_group_id`** — Links trace data to OCI Logging for cross-service correlation in dashboards; without it, traces and logs are siloed and cannot be joined in dashboard views.
4. **APM Config resources** — Always provision SPAN_FILTER (limits noise), APDEX (SLA thresholds), and METRIC_GROUP (custom metrics for alarms); all must reference the same `apm_domain_id`.
5. **Logging with explicit `retention_duration`** — OCI Logging does not support infinite retention; accepted values: `30 | 60 | 90 | 180`; always set explicitly to meet compliance requirements.
6. **Monitoring alarm with `pending_duration` and ONS topic** — `pending_duration` prevents flapping from momentary spikes; `repeat_notification_duration` prevents alert spam; use `overrides` for multi-severity escalation.
7. **Saved Search (CRUD) for IaC-managed widgets** — Use `oci_management_dashboard_management_saved_search` for programmatically managed tiles; never hardcode OCIDs in `data_config` JSON — use Terraform resource references.
8. **Dashboard import via tracked JSON file** — Use `import_details_file` pointing to a committed `.json` file; never use inline `import_details` variable; note: this resource has no Update/Delete lifecycle.
9. **Variable validation for OCI-specific enum values** — Validate `retention_duration`, `alarm_severity`, `compartment_ocid` format at plan time; OCI server-side validation only fails at apply, wasting pipeline runs.

### ⚠️ Ask First

For trade-off matrices and decision code, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points** (Complex domain — all 4 required):

- **Dashboard import vs. saved search CRUD** — Import (`oci_management_dashboard_management_dashboards_import`) is write-once with no drift detection; saved search (`oci_management_dashboard_management_saved_search`) is fully managed CRUD. Ask: "Are dashboards being migrated from Console, or built from scratch in Terraform?"
- **APM free tier vs. paid** — Free tier caps at 1,000 spans/hr with 7-day retention and no Apdex analytics; paid tier has 500K spans/hr and 30-day retention. Ask: "Is this production with SLA requirements?"
- **Per-service vs. shared log groups** — Per-service provides IAM isolation and per-service retention but multiplies IAM policies; shared is simpler but all-or-nothing. Ask: "Do different services have separate retention or access requirements?"
- **Alarm namespace selection** — `oracle_apm_rum` (RUM), `oracle_apm_synthetics` (synthetic), `oci_computeagent` (host), custom METRIC_GROUP namespace; choice depends on what signal needs alerting. Ask: "What data source — RUM traces, synthetic monitors, host metrics, or custom APM metric groups?"

### 🚫 Never Do

For full anti-pattern examples with correct alternatives, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns** (Complex domain — all 7 required):

- **APM data key hardcoded in HCL or tfvars** — Data keys are write-access credentials; store in OCI Vault Secret, reference by OCID. Impact: CRITICAL — trace injection, topology exposure.
- **Dashboard JSON inline in `import_details` variable** — Bypasses version control diff review; complex JSON changes are undetectable in `terraform plan`. Impact: HIGH — unreviewed dashboard changes.
- **`oci_logging_log` without `retention_duration`** — Silent 30-day default may violate compliance requirements (e.g., 90-day PCI DSS). Impact: HIGH — unexpected log deletion.
- **Monitoring alarm without `pending_duration`** — Every momentary spike fires; causes alert fatigue and missed real incidents. Impact: MEDIUM.
- **API key auth in CI/CD pipelines** — OCI API keys never expire; leaked key = full tenancy compromise. Use `InstancePrincipal` or `SecurityToken`. Impact: CRITICAL.
- **APM domain deployed without IAM policy** — Applications receive HTTP 403 on data upload and fail silently; no traces means no observability. Impact: HIGH.
- **Hardcoded OCIDs in saved search `data_config` JSON** — Dashboards break when moved between environments; always use `oci_apm_apm_domain.main.id` references. Impact: MEDIUM — portability failure.

---

## Integration Patterns

For full HCL examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Key integrations**:
- **APM Domain ↔ OCI Vault** — Store APM private data key as `oci_vault_secret`; application retrieves by secret OCID at runtime (never by value)
- **OCI Logging ↔ Log Analytics** — Route via `oci_sch_service_connector` (kind=`logging` → kind=`loggingAnalytics`); required for Log Analytics widget type in Management Dashboards
- **APM Config ↔ OCI Monitoring** — `METRIC_GROUP` config maps span attributes to custom metric namespace; then `oci_monitoring_alarm` queries that namespace via MQL
- **Management Dashboards ↔ All sources** — Saved searches reference `provider_id`: `apm` | `log-analytics` | `monitoring`

**Common problems**:
- **Service connector enters FAILED state** → Target Log Analytics group OCID must exist before connector is created; add `depends_on`
- **APM domain creation timeout** → Creation takes 2-5 minutes; add `timeouts { create = "10m" }` in CI/CD
- **`defined_tags` permanent drift on log groups** → OCI auto-applies namespace tags; add `lifecycle { ignore_changes = [defined_tags] }`
- **Alarm MQL fails at apply** → OCI does not validate MQL at plan time; test queries in OCI Console Metrics Explorer first

---

## Verification Loop

After each code generation, the agent MUST execute:

### 1. Format & Syntax
```bash
terraform fmt -recursive -check=true
# Expected: Exit code 0

terraform validate
# Expected: Success! The configuration is valid.
```

### 2. Security Scan
```bash
tfsec . --format json
# Expected: No HIGH or CRITICAL findings

checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks
```

### 3. Plan (Dry Run)
```bash
terraform plan -out=tfplan -lock=true
terraform show tfplan | grep -E "will be created|will be updated|will be destroyed"
# Expected: APM domain, log groups, alarms in additions; no unexpected deletions
```

### 4. State Verification (Post-Apply)
```bash
terraform state list | grep -E "oci_apm|oci_logging|oci_monitoring|oci_management_dashboard"
terraform show oci_apm_apm_domain.main | grep "lifecycle_state"
# Expected: lifecycle_state = "ACTIVE"
```

**Troubleshooting**:
- `Error: 403 on APM data upload` → Missing IAM policy for dynamic group on APM domain
- `Error: service_connector FAILED state` → Log Analytics target group doesn't exist yet
- `Error: Invalid retention_duration` → Must be one of 30, 60, 90, 180 — not arbitrary values
- `Error: namespace not found on alarm` → Namespace string is case-sensitive; verify exact string from OCI Monitoring docs

---

## Quick Reference

**Essential commands**:
```bash
terraform init -upgrade          # Initialize / update oracle/oci provider
terraform fmt -recursive         # Format all HCL files
terraform validate               # Validate configuration
terraform plan -out=tfplan       # Dry run
terraform apply tfplan           # Apply approved plan
```

**OCI Log retention accepted values**:

| Value | Days |
|-------|------|
| 30    | 1 month |
| 60    | 2 months |
| 90    | 3 months |
| 180   | 6 months |

**APM domain limits (production)**:

| Resource | Free Tier | Paid Tier |
|----------|-----------|-----------|
| Spans/hour | 1,000 | 500,000 (default) |
| Trace retention | 7 days | 30 days |
| Apdex analytics | ❌ | ✅ |

**Common alarm namespaces**:

| Namespace | Signal |
|-----------|--------|
| `oracle_apm_rum` | RUM error rate, page load |
| `oracle_apm_synthetics` | Synthetic monitor pass/fail |
| `oci_computeagent` | CPU, memory, disk |
| `oracle_oci_functions` | Function errors, duration |

---

## Blueprints Directory Structure

```
.github/skills/provisioning-custom-dashboard-oci-observability/
├── SKILL.md                         ← This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md        ← ✅ Full HCL for all 9 mandatory patterns
    ├── ask-first-decisions.md       ← ⚠️ Decision matrices + option code examples
    ├── never-do-patterns.md         ← 🚫 Anti-patterns with ❌/✅ examples
    ├── integration-patterns.md     ← APM ↔ Logging ↔ Dashboards ↔ Alarms HCL
    └── evaluation-scenarios.md     ← 📋 Test scenarios for skill validation
```

---

## External Resources

- [OCI Terraform Provider Registry](https://registry.terraform.io/providers/oracle/oci/latest) — v8.21.0 docs
- [terraform-provider-oci GitHub](https://github.com/oracle/terraform-provider-oci) — Source + examples
- [OCI APM Documentation](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/application-performance-monitoring.html)
- [OCI Management Dashboard API](https://docs.oracle.com/en-us/iaas/api/#/en/dashboard/20210731/)
- [OCI Monitoring MQL Reference](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Reference/mql.htm)
- [OCI Monitoring Namespaces](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Reference/supported-metrics.htm)
- [Service Connector Hub Overview](https://docs.oracle.com/en-us/iaas/Content/service-connector-hub/overview.htm)
- [OCI Provider Auth Configuration](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/terraformproviderconfiguration.htm)
- [APM IAM Policies](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/iam-policies-required-apm.html)
