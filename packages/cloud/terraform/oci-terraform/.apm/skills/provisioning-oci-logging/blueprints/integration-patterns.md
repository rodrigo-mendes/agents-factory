# Integration Patterns — OCI Logging (Terraform oracle/oci ~> 8.15)

## Integration 1: OCI Logging ↔ IAM (Dynamic Groups + Policies)

**Required for**: Every `oci_logging_unified_agent_configuration` resource.

**Key gotcha**: Dynamic groups always live in the **tenancy** compartment (not child compartments). `matching_rule` must use `instance.compartment.id` — not the compartment display name.

```hcl
# Dynamic group lives in tenancy
resource "oci_identity_dynamic_group" "log_agents" {
  compartment_id = var.tenancy_ocid  # NOT var.compartment_id
  name           = "${var.app_name}-${var.environment}-log-agents"
  description    = "Compute instances authorized to send logs"
  matching_rule  = "ALL {instance.compartment.id = '${var.compartment_id}'}"
}

# Policy scoped to the working compartment
resource "oci_identity_policy" "log_agents" {
  compartment_id = var.compartment_id
  name           = "${var.app_name}-${var.environment}-log-agent-policy"
  description    = "UMA agent logging permissions"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.log_agents.name} to use log-content in compartment id ${var.compartment_id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.log_agents.name} to read log-groups in compartment id ${var.compartment_id}"
  ]
}
```

| Resource | Min Provider |
|---|---|
| `oci_identity_dynamic_group` | >= 8.0 |
| `oci_identity_policy` | >= 8.0 |

---

## Integration 2: OCI Logging ↔ OCI Connector Hub (Log Export Pipeline)

**Required for**: Long-term retention, SIEM integration, routing logs to Object Storage or Functions.

**Key gotcha**: SCH requires `request.principal.type='serviceconnector'` in the IAM policy targeting the destination. Without it, SCH shows INACTIVE state with no clear error message.

```hcl
resource "oci_sch_service_connector" "log_archive" {
  compartment_id = var.compartment_id
  display_name   = "${var.app_name}-${var.environment}-log-archive"
  description    = "Archives app logs to Object Storage for long-term retention"

  source {
    kind = "logging"

    log_sources {
      compartment_id = var.compartment_id
      log_group_id   = oci_logging_log_group.app_logs.id
      log_id         = oci_logging_log.app_custom.id
    }
  }

  target {
    kind        = "objectStorage"
    bucket_name = var.archive_bucket_name
    namespace   = data.oci_objectstorage_namespace.ns.namespace

    batch_rollover_size_in_mbs = 100
    batch_rollover_time_in_ms  = 60000
    object_name_prefix         = "${var.app_name}/${var.environment}/logs/"
  }
}

# IAM policy for Connector Hub → Object Storage writes
resource "oci_identity_policy" "sch_objectstorage" {
  compartment_id = var.compartment_id
  name           = "${var.app_name}-sch-objectstorage-policy"
  description    = "Allow SCH to write to archive bucket"

  statements = [
    "Allow any-user to manage objects in compartment id ${var.compartment_id} where all {request.principal.type='serviceconnector', target.bucket.name='${var.archive_bucket_name}'}"
  ]
}
```

---

## Integration 3: OCI Logging ↔ OCI Object Storage (Long-Term Archival)

**Required for**: Compliance frameworks requiring >180-day log retention (PCI-DSS, SOC2, HIPAA).

**Key gotcha**: Connector Hub captures only **new** log data from activation onwards — it does NOT retroactively export data already in OCI Logging. Configure before log data exceeds the OCI Logging retention window.

```hcl
data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_id
}

resource "oci_objectstorage_bucket" "log_archive" {
  compartment_id = var.compartment_id
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "${var.app_name}-${var.environment}-log-archive"

  access_type  = "NoPublicAccess"
  versioning   = "Enabled"
  storage_tier = "Standard"

  freeform_tags = local.common_tags
}

resource "oci_objectstorage_object_lifecycle_policy" "log_archive" {
  namespace = data.oci_objectstorage_namespace.ns.namespace
  bucket    = oci_objectstorage_bucket.log_archive.name

  rules {
    name        = "transition-to-ia"
    action      = "INFREQUENT_ACCESS"
    is_enabled  = true
    target      = "objects"
    time_amount = 30
    time_unit   = "DAYS"
  }

  rules {
    name        = "delete-at-retention-horizon"
    action      = "DELETE"
    is_enabled  = true
    target      = "objects"
    time_amount = var.archive_retention_days  # e.g., 2557 (7 years)
    time_unit   = "DAYS"
  }
}
```

---

## Integration 4: OCI Logging ↔ OCI Compute / OKE (UMA Deployment)

**For Compute**: UMA agent is pre-installed on OCI platform images. Terraform deploys the UMA configuration resource; the agent polls for config every 30 seconds. Config changes apply without instance restart.

**For OKE**: Use `parser_type = "CRI"` with `is_merge_cri_fields = true` for container logs at `/var/log/pods/**/*.log`.

```hcl
# OKE node pool log collection
resource "oci_identity_dynamic_group" "oke_nodes" {
  compartment_id = var.tenancy_ocid
  name           = "${var.cluster_name}-oke-nodes"
  description    = "OKE worker nodes for log collection"
  matching_rule  = "ALL {instance.compartment.id = '${var.compartment_id}', tag.oke-cluster-id.value = '${var.cluster_id}'}"
}

resource "oci_logging_unified_agent_configuration" "oke_logs" {
  compartment_id = var.compartment_id
  display_name   = "${var.cluster_name}-oke-container-logs"
  description    = "Collects container logs from OKE worker nodes"
  is_enabled     = true
  freeform_tags  = local.common_tags

  group_association {
    group_list = [oci_identity_dynamic_group.oke_nodes.id]
  }

  service_configuration {
    configuration_type = "LOGGING"

    sources {
      name        = "container-logs"
      source_type = "LOG_TAIL"
      paths       = ["/var/log/pods/**/*.log"]

      parser {
        parser_type         = "CRI"
        is_merge_cri_fields = true
      }
    }

    destination {
      log_object_id = oci_logging_log.oke_app.id
    }
  }

  depends_on = [oci_identity_policy.oke_nodes]
}
```

**Issues**:
- OKE worker nodes require a dynamic group matching tag rule (cluster ID) to distinguish nodes from unrelated compute in the same compartment.
- `is_merge_cri_fields = true` is required — without it, Kubernetes stream/logtag metadata fields are not flattened into the log record.
