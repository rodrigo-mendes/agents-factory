# Integration Patterns — OCI Connector Hub

Complete Terraform examples for the most common Connector Hub integration scenarios.

---

## Pattern 1 — Centralized Log Archival Pipeline (Logging → Object Storage)

**Use when**: Compliance or operational log retention is required. Combines Connector Hub with Object Storage Retention Rules for WORM-compliant archival.

```hcl
# Data source: namespace
data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_ocid
}

# IAM policy (always before connector)
resource "oci_identity_policy" "archive_policy" {
  compartment_id = var.tenancy_ocid
  name           = "log-archive-connector-policy"
  statements = [
    "allow service serviceconnectors to read log-content in compartment ${var.app_compartment_name}",
    "allow service serviceconnectors to manage objects in compartment ${var.observability_compartment_name} where target.bucket.name = '${var.archive_bucket_name}'",
  ]
}

# Log archive connector
resource "oci_sch_service_connector" "api_log_archive" {
  depends_on     = [oci_identity_policy.archive_policy]
  compartment_id = var.connector_compartment_ocid
  display_name   = "api-service-log-archive-prod"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = oci_logging_log_group.api_logs.id
    }
  }

  target {
    kind                       = "objectStorage"
    bucket                     = var.archive_bucket_name
    namespace                  = data.oci_objectstorage_namespace.ns.namespace
    object_name_prefix         = "api-service/prod/"
    batch_rollover_size_in_mbs = 100
    batch_rollover_time_in_ms  = 60000
  }

  defined_tags = {
    "operations.environment" = "prod"
    "operations.owner"       = "platform-team"
  }
  state = "ACTIVE"
}

# Error monitoring alarm
resource "oci_monitoring_alarm" "archive_connector_error" {
  compartment_id        = var.connector_compartment_ocid
  display_name          = "api-log-archive-error"
  metric_compartment_id = var.connector_compartment_ocid
  namespace             = "oci_service_connector_hub"
  query                 = "ErrorCount[1m].sum() > 0"
  severity              = "CRITICAL"
  destinations          = [oci_ons_notification_topic.ops_alerts.id]
  is_enabled            = true
}
```

---

## Pattern 2 — External SIEM Integration via Functions Adapter (Logging → Functions → Splunk/Datadog)

**Use when**: Enterprise SIEM (Splunk HEC, Datadog Logs API, Elasticsearch) requires OCI log delivery in vendor-specific format.

**Architecture**:
```
OCI Logging → [logRule task: filter to relevant types] → OCI Connector Hub → OCI Functions → External SIEM
                                                                                      ↑
                                                                              API key from OCI Vault
```

```hcl
# IAM policy for Functions target
resource "oci_identity_policy" "siem_connector_policy" {
  compartment_id = var.tenancy_ocid
  name           = "siem-connector-policy"
  statements = [
    "allow service serviceconnectors to read log-content in compartment ${var.app_compartment_name}",
    "allow service serviceconnectors to use fn-invocation in compartment ${var.functions_compartment_name} where target.function.id = '${oci_functions_function.siem_forwarder.id}'",
  ]
}

resource "oci_sch_service_connector" "siem_integration" {
  depends_on     = [oci_identity_policy.siem_connector_policy]
  compartment_id = var.connector_compartment_ocid
  display_name   = "app-logs-to-splunk-prod"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = oci_logging_log_group.app_logs.id
    }
  }

  # Pre-filter: only forward ERROR and WARN — reduce function invocation cost
  tasks {
    kind      = "logRule"
    condition = "logContent.data.level='ERROR' || logContent.data.level='WARN'"
  }

  target {
    kind              = "functions"
    function_id       = oci_functions_function.siem_forwarder.id
    batch_size_in_kbs = 5000
    batch_time_in_sec = 30
  }

  state = "ACTIVE"
}
```

**OCI Function implementation pattern** (pseudocode — adapt for your SIEM):
```python
# The function receives a list of OCI log records, transforms to vendor format, POSTs to SIEM
# API key retrieved from OCI Vault via resource principal — never hardcoded
import oci
from oci.auth.signers import get_resource_principals_signer

def handler(ctx, data: io.BytesIO = None):
    signer = get_resource_principals_signer()
    secrets_client = oci.secrets.SecretsClient(config={}, signer=signer)
    api_key = get_secret(secrets_client, VAULT_SECRET_OCID)
    
    log_records = json.loads(data.getvalue())
    # Transform to Splunk HEC format and POST to HEC endpoint
```

---

## Pattern 3 — Log-Derived Custom Metrics (Logging → Monitoring)

**Use when**: Application logs contain business signals (error counts, latency bins) that need to surface as OCI Monitoring metrics for alerting — without modifying application code.

```hcl
resource "oci_identity_policy" "metrics_connector_policy" {
  compartment_id = var.tenancy_ocid
  name           = "log-metrics-connector-policy"
  statements = [
    "allow service serviceconnectors to read log-content in compartment ${var.app_compartment_name}",
    "allow service serviceconnectors to use metrics in compartment ${var.observability_compartment_name}",
  ]
}

resource "oci_sch_service_connector" "error_rate_metrics" {
  depends_on     = [oci_identity_policy.metrics_connector_policy]
  compartment_id = var.connector_compartment_ocid
  display_name   = "app-error-rate-metrics-prod"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = oci_logging_log_group.app_logs.id
    }
  }

  # Only pass ERROR events to the Monitoring target
  tasks {
    kind      = "logRule"
    condition = "logContent.data.level='ERROR'"
  }

  target {
    kind             = "monitoring"
    compartment_id   = var.observability_compartment_ocid
    metric           = "ApplicationErrorCount"
    metric_namespace = "app_custom_metrics"
    dimensions {
      name = "service"
      dimension_value {
        kind = "jmesPath"
        path = "logContent.data.serviceName"  # Dynamic from log field
      }
    }
    dimensions {
      name = "environment"
      dimension_value {
        kind  = "static"
        value = "production"
      }
    }
  }

  state = "ACTIVE"
}
```

⚠️ **JMESPath errors** produce `SCH_EVAL_INVALID_VALUE` in connector metrics — monitor the `oci_service_connector_hub` namespace for this error code when using dynamic dimension extraction.

---

## Pattern 4 — Queue-Draining Worker Pipeline (Queue Plugin → Functions)

**Use when**: OCI Queue holds work items that need serverless processing — replacing a dedicated consumer daemon. Only available in regions where QueueSource plugin is listed by `ListConnectorPlugins`.

```hcl
# Verify plugin availability in target region first
# oci sch connector-plugin list --compartment-id <TENANCY_OCID> --query 'data[?name==`QueueSource`]'

resource "oci_identity_policy" "queue_processor_policy" {
  compartment_id = var.tenancy_ocid
  name           = "queue-processor-connector-policy"
  statements = [
    "allow service serviceconnectors to use queues in compartment ${var.queue_compartment_name} where target.queue.id = '${var.queue_ocid}'",
    "allow service serviceconnectors to use fn-invocation in compartment ${var.functions_compartment_name}",
  ]
}

resource "oci_sch_service_connector" "queue_processor" {
  depends_on     = [oci_identity_policy.queue_processor_policy]
  compartment_id = var.connector_compartment_ocid
  display_name   = "work-queue-to-function-processor"

  source {
    kind        = "plugin"
    plugin_name = "QueueSource"
    config_map  = jsonencode({ queueId = var.queue_ocid })
  }

  target {
    kind              = "functions"
    function_id       = oci_functions_function.work_processor.id
    batch_size_in_num = 10    # Process up to 10 messages per invocation
    batch_time_in_sec = 30    # Invoke every 30 seconds if batch not full
  }

  state = "ACTIVE"
}
```

⚠️ **Idempotency required**: connector batching does not guarantee exactly-once delivery. OCI Functions must implement check-then-process idempotency. Configure an OCI Queue DLQ for messages that fail function processing repeatedly.

---

## Pattern 5 — Multi-Compartment Log Centralization (Logging → Logging Analytics)

**Use when**: Multiple application compartments need unified log search, correlation, and ML anomaly detection from a single Logging Analytics workspace.

```
app-compartment-1 ──[Connector 1]──┐
app-compartment-2 ──[Connector 2]──┤──► Logging Analytics Log Group (observability-compartment)
app-compartment-3 ──[Connector 3]──┘
```

```hcl
# Template module — instantiate once per application compartment
resource "oci_identity_policy" "la_connector_policy" {
  compartment_id = var.tenancy_ocid
  name           = "la-connector-${var.app_name}-policy"
  statements = [
    "allow service serviceconnectors to read log-content in compartment ${var.app_compartment_name}",
    "allow service serviceconnectors to use log-analytics in compartment ${var.observability_compartment_name}",
  ]
}

resource "oci_sch_service_connector" "app_to_la" {
  depends_on     = [oci_identity_policy.la_connector_policy]
  compartment_id = var.connector_compartment_ocid
  display_name   = "${var.app_name}-to-logging-analytics"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = var.app_log_group_id
    }
  }

  target {
    kind                  = "loggingAnalytics"
    log_group_id          = var.la_log_group_ocid  # Pre-created in observability compartment
    log_source_identifier = var.app_name            # Used for log source identification in LA
  }

  state = "ACTIVE"
}
```

**Runbook — Connector to Logging Analytics FAILED**:
1. `oci sch service-connector get --service-connector-id <OCID> --query 'data."lifecycle-details"'`
2. Common causes: LA log group deleted, LA compartment policy revoked, LA service not enabled in the region
3. Resolution: restore LA log group → reactivate connector → verify data gap in LA for compliance assessment
