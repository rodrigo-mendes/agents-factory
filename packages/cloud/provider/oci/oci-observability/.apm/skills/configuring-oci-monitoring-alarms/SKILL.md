---
name: configuring-oci-monitoring-alarms
description: "Designs and implements OCI Monitoring alarms, suppressions, custom metric ingestion, and IAM authorization following OCI Monitoring API v20180401 best practices. Use when creating or reviewing OCI Monitoring alarms, multi-threshold alerting, maintenance window suppressions, or custom metric pipelines via PostMetricData."
---

## Version Context

**Technology**: Oracle Cloud Infrastructure (OCI) Monitoring Service
**Target Version**: API v20180401
**Support Status**: Active (current stable)

**Important changes in this version**:
- **Alarm Overrides**: `overrides` array on `oci_monitoring_alarm` — sequential multi-threshold evaluation in one resource
- **Recurring Suppressions**: `oci_monitoring_alarm_suppression` supports iCalendar RFC 5545 RRULE (FREQ=DAILY/WEEKLY)
- **Per-Dimension Notifications**: `is_notifications_per_metric_dimension_enabled` enables per-resource alarm splits

**Deprecated**: None in v20180401

⚠️ **Version Lock**: This skill targets OCI Monitoring API v20180401. Do not mix with patterns that predate `overrides` or recurring suppression support.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory alarm guardrails with Terraform code
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions with tradeoff matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with correct alternatives
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Test cases: multi-threshold CPU alarm, custom metric IAM, recurring suppression
- **[Verification Loop](#verification-loop)** — OCI CLI validation commands
- **[Quick Reference](#quick-reference)** — Critical limits and endpoint map
- **[External Resources](#external-resources)** — Official documentation

---

## Blueprints & Guardrails

### ✅ Always Do

For full Terraform code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **Set `pending_duration` explicitly on every production alarm** — Default PT1M fires on any single aberrant data point; volatile metrics (CPU, memory, error rate) produce alert fatigue. Use PT3M–PT5M minimum.
- **Enable `evaluation_slack_duration`** — Default PT3M causes false FIRING alarms during metric ingestion delays. Set PT5M for service metrics, PT10M for custom namespace metrics.
- **Scope alarms to environment-specific compartments** — `metric_compartment_id_in_subtree = true` at tenancy root evaluates prod + staging + dev simultaneously; violates least-privilege and creates blast-radius risk.
- **Use recurring suppressions for maintenance windows** — `oci_monitoring_alarm_suppression` with iCalendar RRULE suppresses notifications without disabling alarm evaluation; alarm history remains intact for post-maintenance forensics.
- **Use alarm `overrides` for multi-threshold alerting** — Consolidate CRITICAL/ERROR/WARNING thresholds in one `oci_monitoring_alarm` resource; eliminates alarm proliferation and simplifies suppression management.
- **Authorize PostMetricData via Dynamic Group + IAM policy** — Never use hardcoded user credentials or API keys; use instance principal (Compute) or resource principal (Functions) with namespace-scoped `use metrics` policy.
- **For `oci_faas` (OCI Functions) metrics, filter by `applicationId` or `resourceId` — never `functionId`** — In the `oci_faas` namespace the dimensions are `applicationId` (the Application/fnapp OCID) and `resourceId` (the individual Function/fnfunc OCID); `functionId` does NOT exist. Alarm/aggregate per Application with `applicationId="<fnapp ocid>"`; per single Function with `resourceId="<fnfunc ocid>"`. Filtering a per-application query by `resourceId="<app ocid>"` silently matches nothing. (Confirmed live.)

### ⚠️ Ask First

For complete decision matrices, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Notification delivery: ONS vs OCI Streaming** — ONS for human on-call (email, PagerDuty, Slack); Streaming for high-throughput automation pipelines, SIEM integration, or Kafka fan-out. Ask: "Is the response human or automated?"
- **Custom metric ingestion method: PostMetricData SDK vs UMA MONITORING vs OCI APM** — UMA when a `/metrics` endpoint already exists on Compute/OKE; SDK for business-logic-derived metrics or serverless; APM when trace correlation is needed.
- **Per-dimension notification split** — `is_notifications_per_metric_dimension_enabled = true` identifies individual resources in pages but multiplies notification volume by fleet size. Ask: "How many resources does this alarm cover, and does on-call need per-resource identity?"

### 🚫 Never Do

For wrong/correct code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

- **Never hardcode OCI credentials for PostMetricData** — Credential leak exposes full OCI API access; use dynamic group + instance/resource principal. Risk: CRITICAL.
- **Never leave `pending_duration` at default PT1M for threshold alarms** — Alert fatigue desensitizes on-call; genuine CRITICAL incidents get ignored as noise. Risk: HIGH.
- **Never disable an alarm for planned maintenance** — `is_enabled = false` stops evaluation; if not re-enabled, creates a silent monitoring gap. Use `oci_monitoring_alarm_suppression` instead. Risk: HIGH.
- **Never POST custom metrics to the `telemetry` endpoint** — Only `telemetry-ingestion.{region}` accepts PostMetricData; using the wrong endpoint silently drops metrics with HTTP 404. Risk: MEDIUM.
- **Never omit `repeat_notification_duration` on CRITICAL alarms** — Default delivers one notification per state transition; a missed page on a P1 burns SLA time silently. Set PT15M for CRITICAL. Risk: MEDIUM.

---

## Integration Patterns

For full code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md) and [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **OCI Monitoring ↔ OCI Notifications (ONS)** — Alarm destinations → ONS Topic → email/PagerDuty/Slack/HTTPS webhook; use separate topics per severity tier
- **OCI Monitoring ↔ OCI Streaming** — Alarm destinations → Streaming stream → Kafka consumer or Functions trigger for automated remediation
- **OCI Monitoring ↔ OCI Functions** — ONS HTTPS subscription → Functions invoke URL; function parses alarm payload and executes remediation (scale-out, restart)
- **OCI Monitoring ↔ Connector Hub** — Monitoring source → Object Storage or Streaming for metric archival beyond the 90-day retention limit
- **PostMetricData ↔ OCI IAM Dynamic Groups** — `use metrics` policy scoped to namespace + compartment; instance/resource principal removes credential management

**Common problems**:
- **Problem**: PostMetricData returns HTTP 404 → **Solution**: Switch to `telemetry-ingestion.{region}` endpoint (not `telemetry`)
- **Problem**: Alarm fires immediately on single spike → **Solution**: Set `pending_duration` to PT3M–PT5M
- **Problem**: False alarms during metric ingestion delays → **Solution**: Increase `evaluation_slack_duration` to PT5M–PT10M

---

## Verification Loop

Execute after each Terraform alarm configuration:

### 1. Validate Terraform
```bash
terraform validate
# Expected: Success! The configuration is valid.
# Exit code: 0
```

### 2. Check Pending Duration Compliance
```bash
oci monitoring alarm list \
  --compartment-id $COMPARTMENT_OCID \
  --query 'data[?"pending-duration"==`"PT1M"` && "is-enabled"==`true` && severity!=`"INFO"`].{name:"display-name",severity:severity}'
# Expected: empty array [] — any result = alarm needs pending_duration update
```

### 3. Check for Disabled Alarms (Maintenance Anti-Pattern)
```bash
oci monitoring alarm list \
  --compartment-id $COMPARTMENT_OCID \
  --query 'data[?"is-enabled"==`false`].{id:id,name:"display-name",updated:"time-updated"}'
# Expected: empty array [] — any result = potential forgotten post-maintenance alarm
```

### 4. Verify PostMetricData Endpoint
```bash
curl -I https://telemetry-ingestion.${OCI_REGION}.oraclecloud.com/20180401/metrics \
  2>/dev/null | head -3
# Expected: HTTP/2 401 or 405 — NOT 404 (404 = wrong endpoint)
```

### 5. Verify Active Suppressions (No Lingering)
```bash
oci monitoring alarm-suppression list \
  --compartment-id $COMPARTMENT_OCID \
  --target-type ALARM \
  --query 'data[?"lifecycle-state"==`"ACTIVE"`].{id:id,name:"display-name",until:"time-suppress-until"}'
# Review: confirm all active suppressions have expected expiry dates
```

**Troubleshooting**:
- `oci: command not found` → Install OCI CLI: `pip install oci-cli`
- `Authorization failed` → Verify dynamic group matching rule and `use metrics` IAM policy
- `namespace not found` → Confirm `telemetry-ingestion` endpoint and namespace string (must start with letter, alphanumeric + underscores)

---

## Quick Reference

**Terraform resources**:
```
oci_monitoring_alarm
oci_monitoring_alarm_suppression
oci_ons_notification_topic
oci_ons_subscription
oci_identity_dynamic_group
oci_identity_policy
```

**API endpoints**:
```
Reads / Alarms:   https://telemetry.{region}.oraclecloud.com
Custom Metrics:   https://telemetry-ingestion.{region}.oraclecloud.com  ← PostMetricData ONLY
```

**Critical limits**:

| Resource | Limit | Scope |
|----------|-------|-------|
| Alarms per compartment | 50 (soft) | Per compartment |
| PostMetricData batch | 50 data points | Per request |
| PostMetricData TPS | 50 TPS (soft) | Per namespace per compartment |
| Metric data retention | 90 days | Raw + aggregated |
| `pending_duration` range | PT1M – PT1H | Per alarm |
| `evaluation_slack_duration` range | PT3M – PT2H | Per alarm |

**Pending duration matrix**:

| Metric Type | Recommended `pending_duration` |
|---|---|
| CPU / Memory (compute) | PT3M–PT5M |
| HTTP error rate (LB/APIGW) | PT2M–PT3M |
| Queue depth | PT5M |
| Absence detection (heartbeat) | PT2M–PT5M |
| Custom app business metric | PT2M–PT5M |

**`repeat_notification_duration` by severity**:

| Severity | Recommended |
|---|---|
| CRITICAL | PT15M |
| ERROR | PT30M |
| WARNING | PT1H or omit |
| INFO | omit |

---

## External Resources

### Official Documentation
- [OCI Monitoring Overview](https://docs.oracle.com/iaas/Content/Monitoring/Concepts/monitoringoverview.htm) (verified 2026-07-26)
- [OCI Monitoring API Reference v20180401](https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/) (verified 2026-07-26)
- [Create Alarm](https://docs.oracle.com/iaas/Content/Monitoring/Tasks/create-alarm.htm) (verified 2026-07-26)
- [Alarm Suppression](https://docs.oracle.com/iaas/Content/Monitoring/Tasks/add-alarm-suppression.htm) (verified 2026-07-26)
- [MQL Reference](https://docs.oracle.com/iaas/Content/Monitoring/Reference/mql.htm) (verified 2026-07-26)
- [PostMetricData (Custom Metrics)](https://docs.oracle.com/iaas/Content/Monitoring/Tasks/publishingcustommetrics.htm) (verified 2026-07-26)

### Security & Best Practices
- [OCI Monitoring Security Reference](https://docs.oracle.com/iaas/Content/Security/Reference/monitoring_security.htm) (verified 2026-07-26)
- [OCI IAM Policies for Monitoring](https://docs.oracle.com/iaas/Content/Monitoring/Concepts/monitoringoverview.htm#permissions) (verified 2026-07-26)
- [Alarm Override Reference](https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/datatypes/AlarmOverride) (verified 2026-07-26)
- [Absence Detection](https://docs.oracle.com/iaas/Content/Monitoring/Tasks/create-edit-alarm-query-absence-detection-period.htm) (verified 2026-07-26)

---

## Related Skills

**Scope of this skill**: OCI Monitoring alarms (multi-threshold, suppression/maintenance windows, MQL, custom metric ingestion, IAM).

- `observing-oci-java-functions` — all three observability pillars at the function level; start here for an overview.
- `monitoring-oci-java-functions` — custom metric emission via PostMetricData (the source of the metrics being alarmed).
- `monitoring-oci-apm` — alarms over APM domain metrics.
- Live validation: `validating-oci-observability`.
- Evaluation scenarios: [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md)
