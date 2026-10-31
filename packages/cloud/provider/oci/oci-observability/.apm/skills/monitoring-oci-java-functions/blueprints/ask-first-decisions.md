# Ask First Decisions — monitoring-oci-java-functions

## Decision 1: Custom Metric Namespace Strategy

**Ask**: "Will multiple functions need a shared dashboard for a single business domain?"

| Option | Namespace Pattern | Best When |
|--------|-----------------|-----------|
| **Per-function** | `fn_order_processor` | Independent teams; unrelated domains |
| **Per-application** | `myapp_functions` | Small-to-medium apps; shared dashboards; < 5 functions |
| **Per-domain** | `order_system_prod` | Microservice domains; business-level SLO dashboards |
| ❌ **Flat `custom_metrics`** | `custom_metrics` | Never — causes MQL ambiguity at scale |

**Decision guide**:
1. Multiple functions sharing a business domain SLO? → **Per-domain** namespace
2. Functions developed by independent teams? → **Per-function** namespace
3. Starting fresh with < 5 functions? → **Per-application** namespace (simplest)

**Environment isolation rule**: Always suffix with environment — `order_system_prod` vs `order_system_staging`. Dev load MUST NOT appear in prod metric series.

---

## Decision 2: Batched vs Per-Event Metric Posts

**Ask**: "Does each processed item require individual metric timing, or can metrics be aggregated per invocation?"

| Option | Latency Added | API TPS Cost | Best When |
|--------|--------------|-------------|-----------|
| **Per-event** | 20–50 ms × N items | High | Low-volume functions (< 100 events/invocation); per-item timing required |
| **Batched at end** | 20–50 ms once | Low | High-volume functions; batch processors; aggregated counts |
| **Batched mid-invocation** | 20–50 ms × batches | Medium | Long-running functions near timeout; streaming processors |

**Decision guide**:
1. Per-item timing needed? → Per-event post
2. Function processes > 50 metric types per invocation? → Multiple batched requests (max 50 `MetricDataDetails` per request)
3. Function timeout < 15s? → Single batched post at end; leave 5s buffer for metric post

> At 60 concurrent invocations all posting once each: 60 TPS → exceeds 50 TPS limit. Mitigate by batching multiple `MetricDataDetails` per request.

---

## Decision 3: Alarm Notification Destination

**Ask**: "Does this alarm require human response in < 5 minutes, or automated remediation?"

| Option | Delivery Latency | Human Alert | Automation | Best When |
|--------|-----------------|------------|------------|-----------|
| **ONS → Email** | 1–3 min | Yes (email) | No | Dev/staging awareness-only |
| **ONS → HTTPS webhook** | 1–3 min | Via downstream tool | Yes | Slack, PagerDuty, ServiceNow |
| **ONS → PagerDuty** (native) | 1–3 min | Yes (PagerDuty) | Yes | Production on-call workflows |
| **OCI Streaming** | < 30s | No | Yes | Event-driven auto-remediation |
| **ONS → OCI Functions** | 2–5 min | No | Yes | Auto-scale, restart remediation |

**Decision guide**:
1. CRITICAL alarm, human response < 5 min? → ONS → PagerDuty or HTTPS webhook
2. Automated remediation needed? → ONS → OCI Functions
3. Real-time alarm event processing? → OCI Streaming endpoint
4. Monitoring-only / awareness alarm? → ONS → Email

---

## Decision 4: Alarm Suppression Strategy

**Ask**: "Is this a one-time event, or is there a recurring maintenance schedule?"

| Option | Recurrence | Scope | Best When |
|--------|-----------|-------|-----------|
| **Manual suppression** (`oci_monitoring_alarm_suppression`) | One-time | Alarm or dimension | Unplanned maintenance; ad-hoc deployments |
| **Recurring suppression** (iCalendar RRULE) | Repeating | Alarm or dimension | Scheduled weekly/daily maintenance windows |
| **Alarm disabled** (`is_enabled = false`) | Manual toggle | Entire alarm | Extended planned downtime > 24 hours |

**Recurring suppression example** (every Sunday 02:00–04:00 UTC):
```hcl
resource "oci_monitoring_alarm_suppression" "weekly_maintenance" {
  alarm_id     = oci_monitoring_alarm.fn_error_rate.id
  display_name = "weekly-maintenance-window"

  time_suppress_from  = "2026-06-01T02:00:00Z"
  time_suppress_until = "2026-06-01T04:00:00Z"

  suppression_recurrence = "FREQ=WEEKLY;BYDAY=SU;BYHOUR=2;BYMINUTE=0;BYSECOND=0"
  description            = "Sunday 02:00-04:00 UTC maintenance window"
}
```

**Decision guide**:
1. One-time deployment window? → Manual suppression
2. Fixed weekly/daily maintenance? → Recurring iCalendar RRULE via Terraform
3. Offline > 24 hours? → Disable alarm (`is_enabled = false`)

---

## Decision 5: Metric Streams for Real-Time Routing

**Ask**: "Does the team use Grafana/Prometheus, or need metric retention beyond 90 days?"

| Option | Latency | Target Systems | Setup | Best When |
|--------|---------|---------------|-------|-----------|
| **OCI Metrics Explorer + Dashboards** | 1-min aggregation | OCI Console | None | OCI-native teams; standard SLO monitoring |
| **Connector Hub → Streaming** | < 30s | Grafana, Flink, Kafka consumers | Medium | Real-time anomaly detection; external dashboards |
| **Connector Hub → Object Storage** | ~5 min | Batch analytics (Spark, data warehouse) | Low | FinOps; long-term retention > 90 days |
| **Connector Hub → Functions** | 1–2 min | Prometheus push, Splunk HEC | High | Custom transformations; non-native integrations |

**Connector Hub rule for oci_faas + custom metrics** (Streaming target):
```hcl
resource "oci_sch_service_connector" "fn_metrics_stream" {
  compartment_id = var.compartment_ocid
  display_name   = "fn-metrics-to-stream"

  source {
    kind = "monitoring"
    monitoring_sources {
      compartment_id = var.compartment_ocid
      namespace_details {
        kind = "selected"
        namespaces {
          metrics { kind = "all" }
          namespace = "oci_faas"
        }
        namespaces {
          metrics { kind = "all" }
          namespace = var.custom_metric_namespace
        }
      }
    }
  }

  target {
    kind      = "streaming"
    stream_id = oci_streaming_stream.metrics_stream.id
  }
}
```

**Decision guide**:
1. Grafana/Prometheus? → Connector Hub → Streaming
2. Retention > 90 days? → Connector Hub → Object Storage
3. OCI-native only? → OCI Dashboards (no Connector Hub needed)
