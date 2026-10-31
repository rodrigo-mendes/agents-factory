# Ask First Decisions — OCI Connector Hub

Present these options to the user, explain trade-offs, and wait for a decision before generating Terraform.

---

## Decision 1 — Source Type

**Ask**: "Is the data already flowing through OCI Logging, or does the upstream system publish to a Stream or Queue?"

| Option | Kind | Latency | Best When |
|--------|------|---------|-----------|
| Logging source | `logging` | Seconds | Log archival, SIEM ingestion, audit trails, log-based metrics — data already in OCI Logging |
| Streaming source | `streaming` | Sub-second | High-throughput event pipelines, IoT, microservice event buses — upstream publishes to Stream |
| Monitoring source | `monitoring` | Minutes | Forwarding OCI-native metric data to analytics — metric data only, not logs |
| Queue plugin | `plugin` (`QueueSource`) | Seconds | Work-queue draining, batch job triggering — data in OCI Queue; check regional availability first |

**HCL stubs**:
```hcl
# Logging source
source {
  kind = "logging"
  log_sources {
    compartment_id = var.compartment_ocid
    log_group_id   = oci_logging_log_group.app_logs.id
  }
}

# Streaming source
source {
  kind = "streaming"
  stream_id   = oci_streaming_stream.events.id
  cursor_kind = "LATEST"  # or "TRIM_HORIZON" — see Decision 5
}

# Queue plugin (verify regional availability before designing)
source {
  kind        = "plugin"
  plugin_name = "QueueSource"
  config_map  = jsonencode({ queueId = var.queue_ocid })
}
```

**Region check for Queue plugin**:
```bash
oci sch connector-plugin list --compartment-id <TENANCY_OCID> \
  --query 'data[?name==`QueueSource`].{name:name,status:status}'
```

---

## Decision 2 — Target Type

**Ask**: "Who is the primary consumer of this data — humans (search/dashboards), automated systems (APIs/alerting), or compliance storage?"

| Option | Kind | Cost | Best When |
|--------|------|------|-----------|
| Object Storage | `objectStorage` | Lowest | Compliance archival, data lake, long-term retention — storage-optimized |
| Logging Analytics | `loggingAnalytics` | Medium-High | Operational intelligence, security investigation, ML anomaly detection |
| Functions | `functions` | Variable | External SIEM forwarding (Splunk, Datadog), format conversion, cross-cloud routing |
| Notifications (ONS) | `notifications` | Low | Alert delivery via email/Slack/PagerDuty/webhook — max 64 KB per message |
| Monitoring | `monitoring` | Low-Medium | Log-derived custom metrics, SLO instrumentation — no application code change needed |
| Streaming | `streaming` | Medium | Fan-out hub, Kafka-compatible consumption, decoupled multi-consumer pipelines |
| Logging | `logging` | Low | Cross-compartment log aggregation — ⚠️ Never same compartment as source (loop risk) |

**HCL stubs**:
```hcl
# Object Storage target
target {
  kind                       = "objectStorage"
  bucket                     = var.bucket_name
  namespace                  = data.oci_objectstorage_namespace.ns.namespace
  object_name_prefix         = "observability/app-logs/prod/"
  batch_rollover_size_in_mbs = 100
  batch_rollover_time_in_ms  = 60000
}

# Functions target (for SIEM forwarding)
target {
  kind              = "functions"
  function_id       = oci_functions_function.siem_forwarder.id
  batch_size_in_kbs = 5000  # max 6000 KB
  batch_time_in_sec = 62    # max 600 sec
}

# Monitoring target (log-derived custom metrics)
target {
  kind             = "monitoring"
  compartment_id   = var.compartment_ocid
  metric           = "ApplicationErrorCount"
  metric_namespace = "app_observability"
  dimensions {
    name = "service"
    dimension_value {
      kind = "jmesPath"
      path = "logContent.data.serviceName"
    }
  }
}
```

---

## Decision 3 — In-Flight Transformation Strategy

**Ask**: "Will ALL events from the source be useful at the target, or is there a filterable subset? Does the format need to change?"

| Option | Kind | Complexity | Best When |
|--------|------|-----------|-----------|
| No task | (none) | Zero | All events needed; source format matches target — simplest path |
| logRule filter | `logRule` | Low | High-volume source where only a subset matters — drop irrelevant events before target to reduce cost |
| Function task | `function` | High | Format conversion, field enrichment, conditional routing, external data join |

⚠️ **Function task vs. Functions target**: A `function` task transforms data **in-flight before the target**. A `functions` target **is the final destination**. These are different resources.

```hcl
# logRule: only pass ERROR-level events (JMESPath — root is logContent)
tasks {
  kind      = "logRule"
  condition = "logContent.data.level='ERROR'"
}

# Function task: transform before target (tune batch parameters)
tasks {
  kind              = "function"
  function_id       = oci_functions_function.transformer.id
  batch_size_in_kbs = 5000  # Tune to workload
  batch_time_in_sec = 62
}
```

---

## Decision 4 — Fan-Out Architecture (One Source → Multiple Targets)

**Ask**: "How many targets need this data? Do all targets receive identical data, or is routing conditional?"

| Option | Pattern | Best When |
|--------|---------|-----------|
| Parallel connectors | N connectors, same source config, independent targets | 2–3 targets, all receive same data, simple IAM |
| Streaming hub | 1 connector (source → Stream), N connectors (Stream → targets) | 4+ targets, replayability needed, targets at different processing rates |
| Functions routing | 1 connector (source → Function), function routes internally | Conditional routing, cross-cloud forwarding, dynamic target selection |

```hcl
# Pattern A: parallel connectors (simple fan-out to 2 targets)
resource "oci_sch_service_connector" "archive" {
  # source: logging (app log group)
  # target: objectStorage
}

resource "oci_sch_service_connector" "analytics" {
  # source: logging (same app log group)
  # target: loggingAnalytics
}

# Pattern B: Streaming hub (decouple producers from consumers)
resource "oci_sch_service_connector" "to_stream" {
  # source: logging
  # target: streaming (acts as durable buffer + fan-out point)
}
# Then N connectors with streaming source from the hub stream
```

---

## Decision 5 — Streaming Source Cursor Strategy

**Ask**: "If the connector goes INACTIVE and is reactivated, should it recover missed messages or start fresh?"

| Option | Cursor Kind | Behavior | Risk |
|--------|------------|----------|------|
| Real-time only | `LATEST` | Reads new messages only after activation | No risk of duplicate processing; missed events during INACTIVE are permanently lost |
| Full replay | `TRIM_HORIZON` | Reads from the oldest retained message (up to 7 days) | Reactivation replays all retained data — downstream **must be idempotent** |

```hcl
# LATEST: real-time monitoring, alerting — historical data not needed
source {
  kind        = "streaming"
  stream_id   = oci_streaming_stream.events.id
  cursor_kind = "LATEST"
}

# TRIM_HORIZON: backfill, compliance audit, recovery after downtime
source {
  kind        = "streaming"
  stream_id   = oci_streaming_stream.events.id
  cursor_kind = "TRIM_HORIZON"
}
```

⚠️ Cursor kind only takes effect at connector creation or reactivation — a running connector is not affected. Deactivating and reactivating with `TRIM_HORIZON` will reprocess all retained stream data and can cause duplicate writes to Object Storage or duplicate function invocations.
