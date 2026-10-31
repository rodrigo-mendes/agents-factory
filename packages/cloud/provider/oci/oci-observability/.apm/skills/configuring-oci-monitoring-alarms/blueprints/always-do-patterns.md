# ✅ Always Do Patterns — OCI Monitoring Alarms

---

## 1. Set `pending_duration` on Every Production Alarm

Default PT1M fires on any single aberrant data point. Set based on metric volatility.

```hcl
resource "oci_monitoring_alarm" "cpu_high" {
  compartment_id        = var.app_compartment_ocid
  display_name          = "api-fleet-cpu-critical"
  namespace             = "oci_computeagent"
  metric_compartment_id = var.app_compartment_ocid
  query                 = "CpuUtilization[1m].groupBy(resourceId).percentile(0.9) > 90"
  severity              = "CRITICAL"
  is_enabled            = true
  destinations          = [oci_ons_notification_topic.oncall_pagerduty.id]

  pending_duration          = "PT5M"   # MANDATORY — never leave at default PT1M
  evaluation_slack_duration = "PT5M"   # guard against ingestion latency false positives
  repeat_notification_duration = "PT15M"

  body = "CPU utilization above 90% for 5+ minutes on API fleet."
  defined_tags = { "operations.environment" = "prod", "operations.team" = "api-platform" }
}
```

**Pending duration decision matrix**:

| Metric Type | Recommended | Rationale |
|---|---|---|
| CPU / Memory (compute) | PT3M–PT5M | Natural variance from GC, startup bursts |
| HTTP error rate (LB/APIGW) | PT2M–PT3M | Sustained errors = real incident |
| Queue depth (Streaming/Queue) | PT5M | Buildup is gradual; transient spikes normal |
| Absence detection (heartbeat) | PT2M–PT5M | One missed window = possible flap |
| Custom app business metric | PT2M–PT5M | Depends on emission frequency |

---

## 2. Enable `evaluation_slack_duration`

Prevents false positives when metric ingestion is delayed (high-cardinality namespaces, custom metrics, OKE pods).

```hcl
resource "oci_monitoring_alarm" "custom_queue_depth" {
  compartment_id        = var.app_compartment_ocid
  display_name          = "worker-queue-depth-warning"
  namespace             = "myapp_worker"
  metric_compartment_id = var.app_compartment_ocid
  query                 = "QueueDepth[5m]{resourceGroup=\"batch-workers\"}.mean() > 500"
  severity              = "WARNING"
  is_enabled            = true
  destinations          = [oci_ons_notification_topic.ops_email.id]
  pending_duration      = "PT5M"

  # Custom metrics: allow for agent flush + ingestion pipeline latency
  evaluation_slack_duration = "PT10M"

  message_format = "ONS_OPTIMIZED"
}
```

- OCI service metrics (oci_computeagent, oci_lbaas): PT5M is sufficient
- Custom namespaces (PostMetricData, UMA MONITORING): PT10M recommended
- High-cardinality namespaces (OKE pods, auto-scaling groups): PT5M–PT10M

---

## 3. Scope Alarms to Environment-Specific Compartments

`metric_compartment_id_in_subtree = true` at tenancy root evaluates prod, staging, and dev simultaneously — dev CPU spikes page production on-call.

```hcl
# ✅ CORRECT: one alarm per environment, scoped to environment compartment
resource "oci_monitoring_alarm" "prod_cpu" {
  compartment_id        = var.prod_compartment_ocid
  metric_compartment_id = var.prod_compartment_ocid
  metric_compartment_id_in_subtree = false   # explicit false
  display_name          = "prod-api-cpu-critical"
  namespace             = "oci_computeagent"
  query                 = "CpuUtilization[1m].groupBy(resourceId).percentile(0.9) > 90"
  severity              = "CRITICAL"
  is_enabled            = true
  destinations          = [var.prod_oncall_topic_ocid]
  pending_duration      = "PT5M"
}

# ❌ WRONG — never use tenancy root with in_subtree = true
# metric_compartment_id        = var.tenancy_ocid
# metric_compartment_id_in_subtree = true
```

**Alarm compartment strategy**:

| Environment | `compartment_id` | `metric_compartment_id` | `in_subtree` | Destinations |
|---|---|---|---|---|
| Production | prod-compartment | prod-compartment | false | PagerDuty ONS topic |
| Staging | staging-compartment | staging-compartment | false | Email ONS topic |
| Development | dev-compartment | dev-compartment | false | Optional |

---

## 4. Configure Recurring Suppressions for Maintenance Windows

Disable/enable is error-prone — use `oci_monitoring_alarm_suppression`. Alarm continues evaluating; only notifications are suppressed.

```hcl
# Recurring weekly suppression: Sunday 02:00–04:00 UTC
resource "oci_monitoring_alarm_suppression" "sunday_maintenance" {
  display_name = "weekly-sunday-maintenance-window"
  description  = "Suppress compute alarms during weekly DB maintenance"

  alarm_suppression_target {
    target_type    = "COMPARTMENT"
    compartment_id = var.app_compartment_ocid
    compartment_id_in_subtree = false
  }

  level = "ALARM"

  time_suppress_from  = "2026-06-01T02:00:00.000Z"   # anchor date (first occurrence)
  time_suppress_until = "2026-06-01T04:00:00.000Z"

  suppression_conditions {
    condition_type         = "RECURRENCE"
    suppression_recurrence = "FREQ=WEEKLY;BYDAY=SU;BYHOUR=2;BYMINUTE=0;BYSECOND=0"
    suppression_duration   = "PT2H"
  }
}

# Dimension-scoped suppression: one instance during patching
resource "oci_monitoring_alarm_suppression" "instance_patch" {
  display_name = "instance-abc123-patching"
  description  = "Patch deployment CHG-2026-0551"

  alarm_suppression_target {
    target_type = "ALARM"
    alarm_id    = oci_monitoring_alarm.cpu_high.id
  }

  level      = "DIMENSION"
  dimensions = { "resourceId" = "ocid1.instance.oc1.phx.exampleuniqueID" }

  time_suppress_from  = "2026-06-10T03:00:00.000Z"
  time_suppress_until = "2026-06-10T05:00:00.000Z"
}
```

- `level = "ALARM"` silences the entire alarm
- `level = "DIMENSION"` silences only the resource matching the `dimensions` map
- `target_type = "COMPARTMENT"` suppresses all alarms in the compartment

---

## 5. Use Alarm Overrides for Multi-Threshold Alerting

One resource with sequential override evaluation eliminates alarm sprawl and simplifies suppression.

```hcl
resource "oci_monitoring_alarm" "api_error_rate" {
  compartment_id        = var.app_compartment_ocid
  display_name          = "api-gateway-error-rate"
  namespace             = "oci_apigateway"
  metric_compartment_id = var.app_compartment_ocid
  query                 = "HttpRequests5xx[1m].rate() > 1"   # base: WARNING
  severity              = "WARNING"
  is_enabled            = true
  pending_duration      = "PT3M"
  destinations          = [oci_ons_notification_topic.ops_email.id]
  body                  = "API Gateway error rate elevated."

  # Override index 0 (evaluated first) — CRITICAL at ≥50 errors/min
  overrides {
    rule_name        = "critical-threshold"
    query            = "HttpRequests5xx[1m].rate() > 50"
    severity         = "CRITICAL"
    pending_duration = "PT1M"
    body             = "CRITICAL: API Gateway error rate above 50/min. Invoke P1 runbook."
  }

  # Override index 1 (evaluated second) — ERROR at ≥10 errors/min
  overrides {
    rule_name        = "error-threshold"
    query            = "HttpRequests5xx[1m].rate() > 10"
    severity         = "ERROR"
    pending_duration = "PT2M"
    body             = "ERROR: API Gateway error rate above 10/min."
  }

  # Base rule (evaluated last): WARNING at any 5xx rate > 1
  rule_name = "BASE"
}
```

⚠️ Override evaluation is **ordered** — `overrides[0]` wins first. Always place higher-severity overrides at lower array indices. If override[0] matches, override[1] and BASE are skipped for that cycle.

---

## 6. Authorize PostMetricData via Dynamic Group + Namespace-Scoped IAM Policy

Instance/resource principals eliminate credential management and enable OCI Audit traceability per resource.

```hcl
resource "oci_identity_dynamic_group" "app_metric_emitters" {
  compartment_id = var.tenancy_ocid
  name           = "app-metric-emitters"
  description    = "Compute instances and Functions authorized to post custom metrics"
  matching_rule  = "Any {instance.compartment.id = '${var.app_compartment_ocid}', resource.type = 'fnfunc', resource.compartment.id = '${var.app_compartment_ocid}'}"
}

# Namespace-scoped write-only policy — cannot read other metrics or manage alarms
resource "oci_identity_policy" "app_metric_write" {
  compartment_id = var.app_compartment_ocid
  name           = "app-metric-emitters-write-policy"
  description    = "Allow app fleet to post custom metrics to myapp_api namespace only"
  statements = [
    "allow dynamic-group ${oci_identity_dynamic_group.app_metric_emitters.name} to use metrics in compartment id ${var.app_compartment_ocid} where target.metrics.namespace = 'myapp_api'"
  ]
}
```

**SDK usage (Python — instance principal, zero credentials)**:
```python
import oci
signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
monitoring_client = oci.monitoring.MonitoringClient(
    config={},
    service_endpoint="https://telemetry-ingestion.us-ashburn-1.oraclecloud.com",
    signer=signer
)
```

**IAM verb matrix**:

| Verb | Operations | Use For |
|---|---|---|
| `inspect metrics` | ListMetrics (definitions only) | Discovery tooling |
| `read metrics` | ListMetrics + GetMetricData | Dashboards, read-only observers |
| `use metrics` | All read + PostMetricData | Application metric emitters |
| `manage alarms` | Full alarm CRUD + suppressions | SRE/platform teams |
