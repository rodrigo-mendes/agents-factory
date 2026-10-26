---
name: designing-oci-connector-hub
description: "Designs OCI Connector Hub data pipelines (source/target topology, routing rules, log-derived metrics, SIEM/worker integration) following Oracle Cloud best practices. Use when designing observability data pipelines, routing logs to Object Storage or Logging Analytics, integrating with external SIEMs via Functions, configuring log-derived custom metrics, or building queue-draining worker pipelines on OCI. For the Terraform HCL, see provisioning-oci-connector-hub."
---

## Version Context

**Technology**: Oracle Cloud (OCI) Connector Hub (API namespace: `sch`)
**Target version**: API v20200909 / OCI Best Practices (current stable)
**Release date**: GA (current stable)
**Support status**: Active

**Important changes in this version**:
- **QueueSource plugin** added: OCI Queue can now be a connector source via the plugin framework — no custom consumer code required
- **Connector Plugin model** expanded: third-party and Oracle-managed plugins available via `ListConnectorPlugins` API
- **Private endpoint metadata** (RCE): connectors can reach private-network targets via reverse connection endpoints
- Branding renamed to "Connector Hub" — all Terraform resources, API paths, and IAM verbs remain under `sch` namespace

**Deprecated**: None — the `oci_sch_service_connector` Terraform resource is the current and only connector resource.

⚠️ **CRITICAL — Agent Warning**:
This skill targets API v20200909. The `source.kind = "plugin"` (QueueSource) and RCE support are v20200909+ features. Do not apply streaming-only or pre-plugin patterns to queue-based architectures.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 5 mandatory patterns with Terraform HCL and OCI CLI
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural crossroads with tradeoff matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 6 anti-patterns with ❌ wrong / ✅ correct examples
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Log archival, SIEM, custom metrics, queue-draining pipelines
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 5 scenarios: canonical pipeline, FAILED state, queue plugin, loop anti-pattern, TRIM_HORIZON replay
- **[Verification Loop](#verification-loop)** — OCI CLI validation commands
- **[Quick Reference](#quick-reference)** — Service limits and critical values
- **[External Resources](#external-resources)** — Official OCI documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with Terraform HCL and OCI CLI, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (all 5 required — Complex tier due to security-critical IAM and silent data loss risk):
- **IAM policies before connector activation** — Create and verify `oci_identity_policy` (or dynamic group policy) before `oci_sch_service_connector` is ACTIVE; a connector lacking policies enters FAILED state and **silently drops all data** — no retry, no buffer.
- **Scope Logging source to log group or log level** — Always set `log_group_id` in `log_sources`; omitting it reads ALL compartment logs (including `_Audit`), causing cost overrun and unintended cross-boundary data exposure.
- **Set `object_name_prefix` on Object Storage targets** — Required for organization and collision avoidance; use convention `{domain}/{purpose}/{env}/` (e.g., `observability/api-logs/prod/`).
- **Tag every connector with environment, owner, and cost-center** — Connector processing costs are data-volume proportional; untagged connectors cannot be attributed in OCI Cost Analysis or cleaned up via governance automation.
- **Use `depends_on` in Terraform to enforce IAM → connector ordering** — Terraform may create the connector before its policy without an explicit dependency, triggering immediate FAILED lifecycle state.

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points** (ask before implementing):
- **Source type** — Logging (native log pull, seconds latency) vs. Streaming (high-throughput, cursor control) vs. Monitoring (metric data) vs. Queue Plugin (work-queue draining); choice depends on where the upstream system already publishes data.
- **Target type** — Object Storage (archival/compliance) vs. Logging Analytics (search/ML) vs. Functions (external SIEM/format conversion) vs. Notifications (alerting) vs. Monitoring (custom metrics) vs. Streaming (fan-out hub); ask "who consumes this data — humans, automated systems, or compliance storage?"
- **In-flight transformation** — No task (passthrough) vs. logRule (JMESPath filter — cost/noise reduction) vs. function task (full transformation/enrichment); logRule is stateless and cheap; function task adds cold-start latency and code maintenance.
- **Fan-out architecture** — Parallel connectors (N connectors sharing same source, simple) vs. Streaming hub (1→Stream→N connectors, decoupled, replayable) vs. Functions routing (conditional routing, max flexibility); ask count of targets and whether routing logic is static or conditional.
- **Streaming source cursor strategy** — LATEST (real-time, discard historical) vs. TRIM_HORIZON (replay from oldest retained, up to 7 days); TRIM_HORIZON on reactivation replays all retained data — downstream must be idempotent.

### 🚫 Never Do

For complete anti-patterns with side-by-side code, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns**:
- **Connector without pre-existing IAM policies** — CRITICAL: connector enters FAILED state silently, dropping all pipeline data with no recovery; always verify ACTIVE state post-apply.
- **Logging source without `log_group_id` in production** — HIGH: ingests all compartment logs including `_Audit`; cross-team data leakage and unbounded ingestion cost.
- **No error monitoring on connector lifecycle state** — HIGH: FAILED connectors produce no metrics; data pipeline degrades silently until downstream systems report missing data; always deploy an `ErrorCount > 0` OCI Monitoring alarm.
- **Overly broad IAM policy for connector service principal** — HIGH: `manage all-resources in tenancy` gives blast radius far beyond the pipeline's needs; scope to minimum resource-type verbs with `where` conditions on named resources.
- **Connector loop: Logging source + Logging target in same compartment** — CRITICAL: target log group events re-trigger the source, creating exponential log amplification and tenancy-wide cost explosion.
- **Function task without batch size tuning** — MEDIUM: default batch parameters cause either thousands of tiny cold-start invocations (cost overrun) or high latency batches; tune `batch_size_in_kbs` and `batch_time_in_sec` to workload.

---

## Integration Patterns

For complete integration code, see [Integration Patterns](./blueprints/integration-patterns.md).

**Supported integrations**:
- **Connector Hub ↔ OCI Logging + Object Storage** — Centralized log archival pipeline with WORM compliance (Object Storage Retention Rules + CMEK)
- **Connector Hub ↔ OCI Logging + OCI Functions** — External SIEM adapter (Splunk HEC / Datadog API / ELK via HTTP POST from Function; API key from OCI Vault)
- **Connector Hub ↔ OCI Logging + OCI Monitoring** — Log-derived custom metrics via JMESPath dimension extraction (no application code change required)
- **Connector Hub ↔ OCI Queue (plugin) + OCI Functions** — Queue-draining worker pipeline replacing dedicated consumer daemon code
- **Connector Hub ↔ OCI Logging + Logging Analytics** — Multi-compartment log centralization for unified search and ML anomaly detection

**Common problems**:
- **Connector in FAILED state after `terraform apply`** → IAM policy not created before connector; check `depends_on`; run `oci sch service-connector get` to read `lifecycle-details`.
- **Object Storage objects landing at bucket root with random names** → `object_name_prefix` not set; add prefix and reapply — objects already written will not be renamed.
- **Function task invoking function thousands of times per minute** → `batch_time_in_sec` set too low or `batch_size_in_kbs` set too small; increase to reduce invocation frequency.
- **No data in Logging Analytics after connector activation** → Verify Logging Analytics log source entity and log group exist in the target compartment; connector does not auto-create LA resources.

---

## Verification Loop

Run after every `terraform apply` or connector configuration change:

### 1. Connector Lifecycle State Check
```bash
oci sch service-connector get \
  --service-connector-id <CONNECTOR_OCID> \
  --query 'data.{"state":"lifecycle-state","details":"lifecycle-details"}'
# Expected: state = "ACTIVE" | If FAILED: check lifecycle-details for IAM error
```

### 2. IAM Policy Audit
```bash
# List all FAILED connectors in a compartment
oci sch service-connector list \
  --compartment-id <COMPARTMENT_OCID> \
  --lifecycle-state FAILED \
  --query 'data[].{id:id,name:"display-name"}'
# Expected: empty array
```

### 3. Logging Source Scope Validation
```bash
oci sch service-connector get \
  --service-connector-id <CONNECTOR_OCID> \
  --query 'data.source.{"kind":"kind","log-sources":"log-sources"}'
# Expected: each log-source has non-null log-group-id
```

### 4. Object Storage Target Prefix Check
```bash
oci sch service-connector get \
  --service-connector-id <CONNECTOR_OCID> \
  --query 'data.target.{"kind":"kind","prefix":"object-name-prefix","bucket":"bucket"}'
# Expected: prefix is non-null and matches naming convention {domain}/{purpose}/{env}/
```

### 5. Error Monitoring Alarm Existence
```bash
oci monitoring alarm list \
  --compartment-id <COMPARTMENT_OCID> \
  --query 'data[?contains(query-text, `ErrorCount`)].{name:"display-name",enabled:"is-enabled"}'
# Expected: at least one alarm with enabled = true
```

**Troubleshooting**:
- `lifecycle-state = FAILED` + `lifecycle-details` mentions IAM → restore missing policy, then `oci sch service-connector activate`
- `lifecycle-state = FAILED` + `lifecycle-details` mentions target → verify target resource exists (bucket, LA log group, ONS topic)
- Data gap after INACTIVE period with Streaming source + TRIM_HORIZON → expected behavior; ensure downstream deduplication handles replayed events

---

## Quick Reference

**Essential Terraform resource**:
```hcl
resource "oci_sch_service_connector" "example" {
  compartment_id = var.compartment_ocid
  display_name   = "<name>"
  source { ... }
  target { ... }
  state          = "ACTIVE"
  depends_on     = [oci_identity_policy.connector_policy]
}
```

**Service limits**:

| Parameter | Limit | Scope |
|-----------|-------|-------|
| Object Storage batch rollover size | 100 MB max | Per connector target |
| Object Storage batch rollover time | 60,000 ms (60 sec) max | Per connector target |
| Function task batch size | 6,000 KB max | Per task |
| Function task batch time | 600 sec max | Per task |
| OCI Streaming retention (cursor replay) | 7 days max | Per stream |
| ONS message size | 64 KB max | Per notification |
| Connector sources | 1 per connector | Per connector |
| Connector targets | 1 per connector | Per connector |

**IAM policy minimum pattern** (Logging → Object Storage):
```
allow service serviceconnectors to read log-content in compartment <source>
allow service serviceconnectors to manage objects in compartment <target>
  where target.bucket.name = '<bucket-name>'
```

---

## External Resources

### Official Documentation
- [OCI Connector Hub Overview](https://docs.oracle.com/iaas/Content/connector-hub/home.htm) (verified 2026-07-26)
- [Create a Service Connector](https://docs.oracle.com/iaas/Content/connector-hub/create-service-connector.htm) (verified 2026-07-26)
- [IAM Policies for Connector Hub](https://docs.oracle.com/iaas/Content/connector-hub/iam-policies.htm) (verified 2026-07-26)
- [API Reference v20200909](https://docs.oracle.com/en-us/iaas/api/#/en/serviceconnectors/20200909/) (verified 2026-07-26)
- [Terraform Resource: oci_sch_service_connector](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/sch_service_connector) (verified 2026-07-26)

### Source & Target Configuration Guides
- [Logging Source](https://docs.oracle.com/iaas/Content/connector-hub/create-service-connector-logging-source.htm) (verified 2026-07-26)
- [Streaming Source](https://docs.oracle.com/iaas/Content/connector-hub/create-service-connector-streaming-source.htm) (verified 2026-07-26)
- [Object Storage Target](https://docs.oracle.com/iaas/Content/connector-hub/create-service-connector-objectstorage-target.htm) (verified 2026-07-26)
- [Functions Target](https://docs.oracle.com/iaas/Content/connector-hub/create-service-connector-functions-target.htm) (verified 2026-07-26)
- [Logging Analytics Target](https://docs.oracle.com/iaas/Content/connector-hub/create-service-connector-logginganalytics-target.htm) (verified 2026-07-26)
- [Monitoring Target](https://docs.oracle.com/iaas/Content/connector-hub/create-service-connector-monitoring-target.htm) (verified 2026-07-26)
- [Connector Plugin API (QueueSource)](https://docs.oracle.com/en-us/iaas/api/#/en/serviceconnectors/latest/ConnectorPlugin/GetConnectorPlugin) (verified 2026-07-26)
