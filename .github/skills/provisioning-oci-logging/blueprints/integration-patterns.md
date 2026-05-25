# Integration Patterns — OCI Logging

## OCI Logging ↔ OCI Connector Hub

**Purpose**: Route log data to archival storage, SIEM, alerting, or log-derived metrics.

**Log archival → Object Storage:**
```hcl
resource "oci_sch_service_connector" "log_archiver" {
  compartment_id = var.app_compartment_ocid
  display_name   = "prod-log-archival"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = oci_logging_log_group.infra_logs.id
      # Omit log_id to route all logs in the group; specify log_id for selective routing
    }
  }

  target {
    kind               = "objectStorage"
    bucket             = oci_objectstorage_bucket.log_archive.name
    object_name_prefix = "logs/prod/infra/"
    # OCI batches objects by time — each file ~1000 records or 1 minute, whichever first
  }
}
```

**Security event alerting → ONS (with logRule filter):**
```hcl
resource "oci_sch_service_connector" "audit_alerter" {
  compartment_id = var.security_compartment_ocid
  display_name   = "prod-audit-iam-alerts"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.tenancy_ocid
      log_group_id   = "_Audit"  # Sentinel — only valid in Connector Hub, NOT in oci_logging_log
    }
  }

  tasks {
    kind = "logRule"
    # Filter to high-risk IAM operations only
    condition = "logContent.type='com.oraclecloud.identity.createpolicy' OR logContent.type='com.oraclecloud.identity.updatepolicy' OR logContent.type='com.oraclecloud.identity.deletepolicy'"
  }

  target {
    kind                      = "notifications"
    topic_id                  = oci_ons_notification_topic.security_alerts.id
    enable_formatted_messaging = true  # Human-readable for email; false for webhook JSON
  }
}
```

**Log-derived metric → OCI Monitoring (for alarms):**
```hcl
resource "oci_sch_service_connector" "error_metric" {
  compartment_id = var.app_compartment_ocid
  display_name   = "app-error-rate-metric"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = oci_logging_log_group.app_logs.id
      log_id         = oci_logging_log.api_access_log.id
    }
  }

  tasks {
    kind      = "logRule"
    condition = "logContent.data.level = 'ERROR'"
  }

  target {
    kind             = "monitoring"
    compartment_id   = var.app_compartment_ocid
    metric           = "ApplicationErrorCount"
    metric_namespace = "custom_app_metrics"
  }
}
# Create OCI Monitoring alarm on custom_app_metrics.ApplicationErrorCount > threshold
```

**Common problems:**
- `_Audit` fails in `oci_logging_log` resource → `_Audit` is Connector Hub-only. Use real log group OCID in Logging API.
- Connector Hub delivery delay up to 2-3 minutes — not sub-second. For near-real-time alerting, OCI Events Service is more appropriate.
- ONS subscription must be confirmed before alerts flow — Connector Hub silently drops to unconfirmed subscriptions.

---

## OCI Logging ↔ OCI IAM

**Purpose**: Dynamic group auto-enrollment + three-tier access model.

**Dynamic group for OKE node pool (Kubernetes worker nodes):**
```hcl
resource "oci_identity_dynamic_group" "oke_nodes" {
  compartment_id = var.tenancy_ocid
  name           = "prod-oke-nodes"
  # Match by node pool OCID for cluster-specific enrollment
  matching_rule  = "ALL {instance.compartment.id = '${var.oke_compartment_ocid}', tag.oke-cluster-id.value = '${var.cluster_id}'}"
}
```

**Full three-tier policy:**
```hcl
resource "oci_identity_policy" "logging_access" {
  compartment_id = var.tenancy_ocid
  name           = "logging-access-policy"
  statements = [
    # Compute instances → ship logs only
    "allow dynamic-group prod-app-instances to use log-content in compartment prod-app",
    # OKE nodes → ship logs only
    "allow dynamic-group prod-oke-nodes to use log-content in compartment prod-app",
    # Connector Hub service → read and route logs
    "allow any-user to use log-content in compartment prod-app where request.principal.type = 'serviceconnector'",
    # SRE team → investigate incidents
    "allow group platform-sre to read log-content in compartment prod-app",
    "allow group platform-sre to read logging-family in compartment prod-app",
    # IaC → manage infrastructure only (no log data access)
    "allow group terraform-pipeline to manage logging-family in compartment prod-app",
    # Security team → audit compartment logs
    "allow group security-auditors to read log-content in compartment security"
  ]
}
```

---

## OCI Logging ↔ OCI Monitoring

**Purpose**: UMA operational health metrics + log-derived alarms.

**Alarm on UMA buffer overflow:**
```hcl
resource "oci_monitoring_alarm" "uma_buffer_overflow" {
  compartment_id        = var.app_compartment_ocid
  display_name          = "prod-uma-buffer-overflow"
  metric_compartment_id = var.app_compartment_ocid
  namespace             = "oci_logging_agent_health"
  query                 = "BufferQueueLength[5m].max() > 1000"
  severity              = "CRITICAL"
  destinations          = [oci_ons_notification_topic.ops_alerts.id]
  message_format        = "ONS_OPTIMIZED"
  is_enabled            = true
  # BufferQueueLength > 1000 indicates UMA cannot ship logs fast enough
  # Investigate: network issues, IAM policy, log-content quota
}
```

**Verify UMA health metrics are flowing:**
```bash
oci monitoring metric-data summarize-metrics-data \
  --compartment-id <ocid> \
  --namespace oci_logging_agent_health \
  --query-text 'BufferQueueLength[5m].max()' \
  --start-time "$(date -u -v-15M +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
# Empty result = UMA operational metrics not configured or agent not running
```

---

## OCI Logging ↔ OCI Logging Analytics

**Purpose**: Cross-compartment indexed search, ML anomaly detection, long-term active retention.

> **Important**: OCI Logging Analytics is a **separate service** with different resource types (`oci_logan_*`), different IAM verbs, and separate per-GB ingestion pricing. Do not confuse `oci_logging_log_group` (OCI Logging) with OCI Logging Analytics Log Groups.

**Route logs to Logging Analytics via Connector Hub:**
```hcl
resource "oci_sch_service_connector" "to_logging_analytics" {
  compartment_id = var.app_compartment_ocid
  display_name   = "prod-logs-to-analytics"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid
      log_group_id   = oci_logging_log_group.security_logs.id
    }
  }

  target {
    kind                       = "loggingAnalytics"
    log_group_id               = oci_log_analytics_log_analytics_log_group.security.id
    # ^ This is oci_log_analytics_log_analytics_log_group — different service, different OCID prefix
  }
}
```

**Common confusion:**
- `oci_logging_log_group` OCID prefix: `ocid1.loggroup.oc1.*`
- `oci_log_analytics_log_analytics_log_group` OCID prefix: `ocid1.loganloggroup.oc1.*`
- Different query languages: OCI Logging uses SQL-like syntax; Logging Analytics uses its own query language
- Different retention: OCI Logging max 180 days; Logging Analytics configurable up to years (at cost)
