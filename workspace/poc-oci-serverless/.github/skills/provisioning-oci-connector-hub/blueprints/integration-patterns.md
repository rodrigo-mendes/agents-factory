# Integration Patterns — OCI Service Connector Hub

Complete Terraform HCL examples for each supported source/target combination. Provider: `oracle/oci ~> 8.0`, Terraform `>= 1.7`.

---

## Pattern: OCI Logging → Object Storage (Log Archival)

**Use case**: Compliance archival, data lake, long-term log retention (7-year audit trail).

```hcl
data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.tenancy_ocid
}

resource "oci_objectstorage_bucket" "log_archive" {
  compartment_id = var.observability_compartment_ocid
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "${var.environment}-log-archive"
  access_type    = "NoPublicAccess"
  versioning     = "Enabled"
}

resource "oci_identity_policy" "connector_policy" {
  compartment_id = var.tenancy_ocid
  name           = "log-archive-connector-policy-${var.environment}"
  statements = [
    "allow service serviceconnectors to read log-content in compartment ${var.app_compartment_name}",
    "allow service serviceconnectors to manage objects in compartment ${var.observability_compartment_name} where target.bucket.name = '${oci_objectstorage_bucket.log_archive.name}'",
  ]
}

resource "oci_sch_service_connector" "api_log_archive" {
  depends_on     = [oci_identity_policy.connector_policy]
  compartment_id = var.observability_compartment_ocid
  display_name   = "api-log-archive-${var.environment}"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = var.api_log_group_ocid  # Always scope to log group
    }
  }

  target {
    kind                       = "objectStorage"
    bucket                     = oci_objectstorage_bucket.log_archive.name
    namespace                  = data.oci_objectstorage_namespace.ns.namespace
    object_name_prefix         = "api-service/${var.environment}/"
    batch_rollover_size_in_mbs = 100    # Max: cost-optimized
    batch_rollover_time_in_ms  = 60000  # Max: cost-optimized
  }

  defined_tags  = var.defined_tags
  freeform_tags = { "managed-by" = "terraform" }
  state         = "ACTIVE"
}
```

**Notes**: `namespace` must be fetched via data source — it is an Oracle-assigned per-tenancy identifier and cannot be hardcoded.

---

## Pattern: OCI Logging → OCI Functions → External SIEM

**Use case**: Forward filtered ERROR/WARN logs to Splunk, Datadog, or any external HTTP endpoint.

```hcl
resource "oci_identity_policy" "siem_connector_policy" {
  compartment_id = var.tenancy_ocid
  name           = "siem-connector-policy-${var.environment}"
  statements = [
    "allow service serviceconnectors to read log-content in compartment ${var.app_compartment_name}",
    "allow service serviceconnectors to use fn-invocation in compartment ${var.functions_compartment_name} where target.function.id = '${oci_functions_function.siem_forwarder.id}'",
  ]
}

resource "oci_sch_service_connector" "siem_integration" {
  depends_on     = [oci_identity_policy.siem_connector_policy]
  compartment_id = var.connector_compartment_ocid
  display_name   = "app-logs-to-siem-${var.environment}"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = var.app_log_group_ocid
    }
  }

  # Pre-filter: forward only ERROR/WARN to reduce function invocation cost
  tasks {
    kind      = "logRule"
    condition = "logContent.data.level='ERROR' || logContent.data.level='WARN'"
  }

  target {
    kind              = "functions"
    function_id       = oci_functions_function.siem_forwarder.id
    batch_size_in_kbs = 5000  # max 6000 KB — tune to average log batch size
    batch_time_in_sec = 30    # max 600 sec — tune to SIEM freshness requirement
  }

  state = "ACTIVE"
}
```

**Security**: The SIEM API key must be stored in OCI Vault and retrieved by the Function via resource principal at runtime — never hardcoded in function code or environment variables.

**Note**: `batch_size_in_kbs` and `batch_size_in_num` are mutually exclusive — specify only one.

---

## Pattern: OCI Logging → OCI Monitoring (Log-Derived Custom Metrics)

**Use case**: Create custom OCI Monitoring metrics from log events without modifying application code.

```hcl
resource "oci_identity_policy" "metrics_connector_policy" {
  compartment_id = var.tenancy_ocid
  name           = "metrics-connector-policy-${var.environment}"
  statements = [
    "allow service serviceconnectors to read log-content in compartment ${var.app_compartment_name}",
    "allow service serviceconnectors to use metrics in compartment ${var.observability_compartment_name}",
  ]
}

resource "oci_sch_service_connector" "log_metrics" {
  depends_on     = [oci_identity_policy.metrics_connector_policy]
  compartment_id = var.connector_compartment_ocid
  display_name   = "error-count-metrics-${var.environment}"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = var.app_log_group_ocid
    }
  }

  tasks {
    kind      = "logRule"
    condition = "logContent.data.level='ERROR'"
  }

  target {
    kind             = "monitoring"
    compartment_id   = var.observability_compartment_ocid
    metric           = "ApplicationErrorCount"
    metric_namespace = "custom_app_observability"

    dimensions {
      name = "service"
      dimension_value {
        kind = "jmesPath"
        path = "logContent.data.serviceName"
      }
    }
    dimensions {
      name = "environment"
      dimension_value {
        kind  = "static"
        value = var.environment
      }
    }
  }

  state = "ACTIVE"
}
```

**Notes**: Reserved dimension names (`connectorId`, `connectorName`, `connectorSourceType`) cannot be used in custom dimensions. Metric namespace must match OCI namespace pattern.

---

## Pattern: OCI Streaming → Object Storage (High-Throughput Event Archival)

**Use case**: Archive high-throughput event streams to Object Storage with cursor control.

```hcl
resource "oci_identity_policy" "stream_connector_policy" {
  compartment_id = var.tenancy_ocid
  name           = "stream-connector-policy-${var.environment}"
  statements = [
    "allow service serviceconnectors to use stream-pull in compartment ${var.streaming_compartment_name} where target.stream.id = '${oci_streaming_stream.events.id}'",
    "allow service serviceconnectors to manage objects in compartment ${var.observability_compartment_name} where target.bucket.name = '${var.events_archive_bucket_name}'",
  ]
}

resource "oci_sch_service_connector" "stream_to_object" {
  depends_on     = [oci_identity_policy.stream_connector_policy]
  compartment_id = var.connector_compartment_ocid
  display_name   = "event-stream-archive-${var.environment}"

  source {
    kind      = "streaming"
    stream_id = oci_streaming_stream.events.id
    cursor {
      kind = "LATEST"  # Use TRIM_HORIZON for backfill — see Ask First Decision 6
    }
  }

  target {
    kind                       = "objectStorage"
    bucket                     = var.events_archive_bucket_name
    namespace                  = data.oci_objectstorage_namespace.ns.namespace
    object_name_prefix         = "events/${var.environment}/"
    batch_rollover_size_in_mbs = 100
    batch_rollover_time_in_ms  = 60000
  }

  state = "ACTIVE"
}
```

**Warning**: `TRIM_HORIZON` cursor on reactivation replays all retained stream data (up to 7 days). Downstream systems must handle duplicate events.

---

## Pattern: OCI Logging → Logging Analytics (Multi-Compartment Centralization)

**Use case**: Unified log search, ML anomaly detection, security investigation.

```hcl
resource "oci_identity_policy" "la_connector_policy" {
  compartment_id = var.tenancy_ocid
  name           = "la-connector-policy-${var.environment}"
  statements = [
    "allow service serviceconnectors to read log-content in compartment ${var.app_compartment_name}",
    "allow service serviceconnectors to use log-analytics in compartment ${var.observability_compartment_name}",
  ]
}

resource "oci_sch_service_connector" "logs_to_la" {
  depends_on     = [oci_identity_policy.la_connector_policy]
  compartment_id = var.connector_compartment_ocid
  display_name   = "app-logs-to-la-${var.environment}"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = var.app_log_group_ocid
    }
  }

  target {
    kind                  = "loggingAnalytics"
    log_group_id          = var.la_log_group_ocid       # OCI Logging Analytics log group OCID
    log_source_identifier = var.la_log_source_name      # Applicable when source is Streaming
  }

  state = "ACTIVE"
}
```

**Notes**: The Logging Analytics target `log_group_id` is a **Logging Analytics** log group OCID — distinct from an OCI Logging `oci_logging_log_group`. The LA log group and log source entity must exist before `terraform apply` — the connector does not auto-create LA resources.

---

## Common Problems

| Problem | Root Cause | Solution |
|---------|-----------|---------|
| Connector in FAILED after apply | IAM policy not applied before connector | Verify `depends_on`; check `lifecycle_details`; re-run `oci sch service-connector activate` |
| Objects at bucket root with random names | `object_name_prefix` not set | Add prefix and reapply — already-written objects are not renamed |
| Function invoked thousands of times/min | `batch_time_in_sec` too low | Increase `batch_size_in_kbs` and `batch_time_in_sec`; check `FunctionInvocationCount` metric |
| No data in Logging Analytics | LA log group or source entity doesn't exist | Create LA log group and source entity before `terraform apply` |
| Streaming TRIM_HORIZON causes duplicate events | Reactivation replays retained data | Ensure downstream systems deduplicate on event ID |
