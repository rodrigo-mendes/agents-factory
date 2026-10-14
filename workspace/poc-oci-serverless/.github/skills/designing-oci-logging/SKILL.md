---
name: provisioning-oci-logging
description: "Provisions OCI Logging resources (Log Groups, Log objects, Unified Monitoring Agent configurations) following Oracle Cloud best practices. Use when designing observability pipelines, configuring log collection from OCI services or compute instances, setting log retention policies, or architecting log archival and alerting for OCI workloads."
---

## Function
Specialist in OCI Logging Service architecture and infrastructure-as-code for Oracle Cloud Infrastructure workloads requiring centralized log management, compliance archival, and security observability.

## Version Context

**Technology**: Oracle Cloud Infrastructure (OCI) Logging Service
**API Version**: `20200531` (stable, GA)
**Target Edition**: OCI Best Practices 2024
**Support Status**: Active — API endpoint `https://logging.{region}.oci.oraclecloud.com`

**Key capabilities in this edition**:
- `OPENMETRICS` parser type — Prometheus endpoint scraping via UMA
- `CUSTOM_PLUGIN` source type — custom Fluentd plugin configuration
- UMA dual-mode: `LOGGING` (files → OCI Logging) + `MONITORING` (metrics → OCI Monitoring)

**Terraform resources**: `oci_logging_log`, `oci_logging_log_group`, `oci_logging_unified_agent_configuration`, `oci_logging_log_saved_search`

⚠️ **Version Lock**: Do not mix patterns from OCI Logging Analytics (separate service, different OCID prefix `oci_logan_*`, different IAM verbs).

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory guardrails with Terraform examples
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with compliant alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Connector Hub, IAM, Monitoring integrations
- **[Verification Loop](#verification-loop)** — OCI CLI validation commands
- **[Quick Reference](#quick-reference)** — Limits, parser types, service log matrix

---

## Blueprints & Guardrails

### ✅ Always Do

For complete Terraform examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Domain complexity: Complex** — 7 mandatory patterns (security-critical, multi-layer, compliance):

- **Separate Log Groups by compliance domain** — One log group per access boundary: `app-logs` (developers), `infra-platform-logs` (platform team), `security-audit-logs` (security team). IAM policies and Connector Hub sources are log-group-scoped; mixing domains collapses access control.
- **Set `retention_duration` explicitly at creation time** — Default is 30 days; OCI Logging max is 180 days. Data deleted at 30 days is permanently unrecoverable. Set at create time — not retroactively. For >180 days: deploy Connector Hub → Object Storage archival **before** the log is created.
- **Deploy UMA via Dynamic Group association, not instance OCIDs** — Associate `oci_logging_unified_agent_configuration.group_association` with a dynamic group matching `instance.compartment.id`. New instances (auto-scaling, rolling deploy) inherit config automatically.
- **Set `is_enabled = true` via a variable, never hardcode `false` for production** — A disabled Log object silently discards all events from the source service. Gate with `var.logging_enabled` defaulting to `true`.
- **Enable Operational Metrics Configuration on every production UMA** — Without UMA self-health metrics, a full buffer or permission failure is invisible until downstream consumers report missing data. Emit to a dedicated namespace (e.g., `oci_logging_agent_health`) and alarm on `BufferQueueLength`.
- **Deploy Connector Hub archival pipeline before enabling high-volume service logs** — Use `depends_on` in Terraform: bucket → connector → log. Once the log is enabled, data older than `retention_duration` is permanently lost. VCN flow logs and Object Storage write logs require pre-existing archival from day 1.
- **Apply three-tier IAM policy** — `use log-content` for instances (write-only), `read log-content` in specific compartment for operators, `manage logging-family` for IaC pipeline. Never grant IaC `read log-content` (prevents pipeline from reading sensitive data).

### ⚠️ Ask First

For complete decision matrices, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**4 architectural decision points requiring user context:**

- **Log ingestion method** — Ask: "Does the application write logs to disk files, or emit programmatically?" → File-based: UMA `LOG_TAIL`; programmatic/Functions/Container Instances: OCI SDK PutLogs direct API; TCP/UDP/HTTP: `CUSTOM_PLUGIN` Fluentd source.
- **UMA parser type** — Ask: "What format does the application write log lines in?" → Structured JSON: `JSON` parser (zero config, all fields searchable); fixed-format text with known structure: `GROK`; Java stack traces / multi-line errors: `MULTILINE_GROK`; Kubernetes CRI format (OKE): `CRI`. Never default to `NONE` in production.
- **Retention beyond 180 days** — Ask: "Will archived log data ever need to be searched, or purely produce-on-demand for compliance?" → Active search: Connector Hub → Logging Analytics; audit-only WORM compliance: Connector Hub → Object Storage + Retention Rules (cheaper); dual need: both (highest cost).
- **Service log enablement scope** — Ask: "What is the daily log volume estimate and data retention budget?" → Always enable: VCN flow (`reject` on most subnets), LB access+error, API Gateway execution, DB audit, Bastion access. High-volume (`all` category on busy subnets, Object Storage write logs): evaluate volume first and ensure archival pipeline is in place.

### 🚫 Never Do

For wrong/correct code side-by-side, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**6 prohibited patterns:**

- **Never create production Log objects without explicit `retention_duration`** — Default 30 days causes irreversible compliance data loss. Set `retention_duration = 90` minimum; `180` for security/compliance logs.
- **Never use `parser_type = "NONE"` in production UMA configurations** — Raw string blobs cannot be field-searched, JMESPath-filtered in Connector Hub, or used for log-derived metrics. Use `JSON`, `GROK`, or `REGEXP` minimum.
- **Never place all log types in a single log group** — Mixing app logs, infrastructure logs, and audit events collapses IAM scope. Any developer with app log access also reads VCN flow and audit events.
- **Never enable high-volume service logs without a pre-deployed archival pipeline** — Enabling Object Storage write logs or VCN flow at `all` category on a busy subnet without Connector Hub → Object Storage means all data beyond `retention_duration` is permanently lost.
- **Never enable VCN Flow Logs at `all` category on every subnet** — Generates millions of events/day on busy subnets, causing cost overrun and pipeline saturation. Use `reject` category for most subnets; `all` only on perimeter/compliance-required subnets.
- **Never associate UMA configurations with individual instance OCIDs** — Instance replacement (auto-scaling, rolling deploy) breaks log collection silently. Always use `group_association` with a dynamic group.

---

## Integration Patterns

For complete Terraform + CLI examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**4 core integrations:**
- **OCI Logging ↔ OCI Connector Hub** — Log archival (→ Object Storage), SIEM routing (→ Functions), alerting (→ ONS via logRule filter), log-derived metrics (→ OCI Monitoring custom namespace)
- **OCI Logging ↔ OCI IAM** — Three-tier policy model: Dynamic Groups for UMA auto-enrollment + `use/read/manage` verb separation
- **OCI Logging ↔ OCI Monitoring** — UMA operational metrics (`oci_logging_agent_health` namespace), log-derived alarms via Connector Hub logRule → Monitoring custom metric
- **OCI Logging ↔ OCI Logging Analytics** — Connector Hub source for cross-compartment search, ML anomaly detection, long-term indexed retention (separate service — different resource types, different costs)

**Common problems:**
- **Problem**: Service logs enabled but no data flowing → **Solution**: Verify source service (LB, API GW) has logging explicitly enabled in its own config, referencing the Log object OCID — enabling the Log object alone is not sufficient.
- **Problem**: UMA configuration applied but instances not shipping logs → **Solution**: Verify Oracle Cloud Agent "Logging" plugin is enabled on the compute shape; check dynamic group matching rule against instance compartment; confirm `use log-content` IAM policy exists.
- **Problem**: `_Audit` used as `log_group_id` in `oci_logging_log` Terraform resource → **Solution**: `_Audit` is a Connector Hub sentinel value only. Use real log group OCIDs in OCI Logging API; use `_Audit` / `_Audit_Include_Subcompartment` only in `oci_sch_service_connector` log source configuration.

---

## Verification Loop

Run after each Terraform apply for OCI Logging resources:

### 1. Terraform Plan — Detect Forced Replacements
```bash
terraform plan -out=tfplan
# Expected: No "must be replaced" on oci_logging_log or oci_logging_unified_agent_configuration
# Forced replacement = log collection gap during apply
```

### 2. Verify Log Group & Log Object State
```bash
oci logging log list --log-group-id <log-group-ocid> \
  --query 'data[].{name:"display-name",enabled:"is-enabled",retention:"retention-duration",state:"lifecycle-state"}'
# Expected: lifecycleState = ACTIVE, isEnabled = true, retentionDuration ≥ 60 (not default 30)
```

### 3. Verify UMA Configuration
```bash
oci logging unified-agent-configuration get \
  --unified-agent-configuration-id <ocid> \
  --query 'data.{"state":"configuration-state","groups":"group-association"}'
# Expected: configurationState = SUCCEEDED; group-association not empty
```

### 4. Verify Log Data Flowing
```bash
# Wait 2-3 minutes after UMA config apply, then search for recent events
oci logging-search search-logs \
  --search-query 'search "<compartment-ocid>/<log-group-ocid>/<log-ocid>"' \
  --time-start "$(date -u -v-5M +%Y-%m-%dT%H:%M:%SZ)" \
  --time-end "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
# Expected: results array non-empty
```

**Troubleshooting:**
- `configurationState = FAILED` on UMA → Check Oracle Cloud Agent Logging plugin enabled: `oci compute instance get-instance-plugin --instance-id <ocid> --plugin-name "Logging"`
- Log object `lifecycleState = INACTIVE` → Source service (LB, API GW) has logging disabled; enable it in the source service config referencing this Log object's OCID
- Zero results in log search → Verify `is_enabled = true`; check UMA `group_association` matches instance's compartment; confirm `use log-content` IAM policy

---

## Quick Reference

**Critical limits:**

| Resource | Limit | Scope |
|----------|-------|-------|
| Log retention | 30–180 days (30-day increments) | Per Log object |
| Max retention without archival | 180 days | Hard ceiling — Connector Hub required for >180 days |
| UMA source types (LOGGING) | LOG_TAIL, WINDOWS_EVENT_LOG, CUSTOM_PLUGIN | Per configuration |
| UMA source types (MONITORING) | KUBERNETES, URL, TAIL | Per configuration |
| `_Audit` sentinel | Connector Hub only | Not valid in OCI Logging API |

**Parser types matrix:**

| Format | Parser | Notes |
|--------|--------|-------|
| Structured JSON | `JSON` | All fields searchable; preferred |
| Fixed-format text | `GROK` | Named capture groups; requires pattern authoring |
| Simple fixed-format | `REGEXP` | Regex capture; no pattern library |
| Java stack traces | `MULTILINE_GROK` | Requires `multi_line_start_regexp` |
| Kubernetes CRI | `CRI` | OKE worker nodes; supports nested parser |
| Prometheus metrics | `OPENMETRICS` | MONITORING config type only |
| Raw blob | `NONE` | **Production: forbidden** |

**Retention decision baseline:**

| Log Category | Minimum | Recommended | Action |
|---|---|---|---|
| Debug/trace | 30d | 30d | Operational only |
| App error/warn | 30d | 60d | Incident investigation |
| LB/API Gateway | 30d | 90d | Request tracing |
| VCN flow logs | 30d | 90d | Network forensics |
| DB audit / Security | 30d | 180d + archival | Compliance |

---

## External Resources

### Official Documentation
- [OCI Logging Overview](https://docs.oracle.com/iaas/Content/Logging/Concepts/loggingoverview.htm)
- [OCI Logging Management API v20200531](https://docs.oracle.com/en-us/iaas/api/#/en/logging-management/20200531/)
- [UnifiedAgentConfiguration API Reference](https://docs.oracle.com/en-us/iaas/api/#/en/logging-management/20200531/UnifiedAgentConfiguration)
- [Top-Level Logging Summary (service log categories)](https://docs.oracle.com/iaas/Content/Logging/Reference/top_level_logging_summary.htm)
- [Connector Hub — Logging Source Configuration](https://docs.oracle.com/iaas/Content/connector-hub/create-service-connector-logging-source.htm)

### Security & Compliance
- [CIS OCI Foundations Benchmark](https://www.cisecurity.org/benchmark/oracle_cloud)
- [OCI IAM Policy Reference — Logging Verbs](https://docs.oracle.com/iaas/Content/Identity/Reference/loggingpolicyreference.htm)
