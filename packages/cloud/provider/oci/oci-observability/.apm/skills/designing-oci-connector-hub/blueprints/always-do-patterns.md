# Always Do Patterns — OCI Connector Hub

Mandatory patterns for every `oci_sch_service_connector` resource. Auto-execute without waiting for user confirmation.

---

## Pattern 1 — IAM Policies Before Connector Activation

**Why**: A connector without proper source-read / target-write policies enters FAILED state immediately upon activation and **silently drops all data** — no retry, no queue, no recovery for the missed period.

**Two IAM approaches**:

**Pattern A — Service-wide grant** (simpler, acceptable for non-production):
```hcl
resource "oci_identity_policy" "connector_hub_policy" {
  compartment_id = var.compartment_ocid
  name           = "connector-hub-service-policy"
  description    = "Grants Connector Hub service principal minimum required access"
  statements = [
    "allow service serviceconnectors to read log-content in compartment ${var.source_compartment_name}",
    "allow service serviceconnectors to manage objects in compartment ${var.target_compartment_name} where target.bucket.name = '${var.log_archive_bucket_name}'",
  ]
}

# Always enforce ordering with depends_on
resource "oci_sch_service_connector" "log_archive" {
  depends_on = [oci_identity_policy.connector_hub_policy]
  # ...
}
```

**Pattern B — Dynamic group scoped to connector OCID** (preferred for production):
```hcl
resource "oci_identity_dynamic_group" "connector_dg" {
  name           = "connector-hub-prod-dg"
  compartment_id = var.tenancy_ocid
  description    = "Scoped to production connector hub connectors"
  matching_rule  = "ALL {resource.type = 'serviceconnector', resource.compartment.id = '${var.connector_compartment_ocid}'}"
}

resource "oci_identity_policy" "connector_dg_policy" {
  compartment_id = var.tenancy_ocid
  name           = "connector-hub-prod-policy"
  statements = [
    "allow dynamic-group connector-hub-prod-dg to read log-content in compartment ${var.source_compartment_name}",
    "allow dynamic-group connector-hub-prod-dg to manage objects in compartment ${var.target_compartment_name} where target.bucket.name = '${var.log_archive_bucket_name}'",
  ]
}
```

**Verification**:
```bash
oci sch service-connector get \
  --service-connector-id <CONNECTOR_OCID> \
  --query 'data."lifecycle-state"'
# Must return "ACTIVE" — "FAILED" means IAM policy is missing or incorrect
```

---

## Pattern 2 — Scope Logging Source to Minimum Required Boundary

**Why**: Omitting `log_group_id` reads ALL logs in the compartment — service logs, application logs, and `_Audit` events. This causes unintended cross-boundary data exposure at targets, cost overrun from unbounded log ingestion, and audit log contamination of non-audit pipelines.

```hcl
# ✅ Correct: scoped to log group (recommended default)
source {
  kind = "logging"
  log_sources {
    compartment_id = var.compartment_ocid
    log_group_id   = oci_logging_log_group.app_logs.id
    # log_id omitted = all logs in group (acceptable)
  }
}

# ✅ Correct: scoped to individual log (maximum precision)
source {
  kind = "logging"
  log_sources {
    compartment_id = var.compartment_ocid
    log_group_id   = oci_logging_log_group.app_logs.id
    log_id         = oci_logging_log.api_access_log.id
  }
}

# ✅ Correct: audit-only connector (use _Audit sentinel — dedicated connector only)
source {
  kind = "logging"
  log_sources {
    compartment_id = var.tenancy_ocid
    log_group_id   = "_Audit"
  }
}
```

---

## Pattern 3 — Set Object Name Prefix on Object Storage Target

**Why**: Without a prefix, objects land at bucket root with auto-generated names. Multiple connectors in the same bucket produce colliding or unidentifiable objects. Queries without a prefix require listing all objects — impractical at scale.

**Naming convention**: `{domain}/{connector-purpose}/{environment}/`

```hcl
target {
  kind                       = "objectStorage"
  bucket                     = oci_objectstorage_bucket.log_archive.name
  namespace                  = data.oci_objectstorage_namespace.ns.namespace
  object_name_prefix         = "observability/api-access-logs/prod/"
  batch_rollover_size_in_mbs = 100   # Max: 100 MB
  batch_rollover_time_in_ms  = 60000 # Max: 60,000 ms — balance cost vs. latency
}
```

**Batch rollover tuning guidelines**:
- Compliance archival (cost optimized): `size = 100`, `time = 60000`
- Near-real-time search: `size = 10`, `time = 5000`

---

## Pattern 4 — Tag Every Connector

**Why**: Connector processing cost is proportional to data volume. Without cost allocation tags, it is impossible to attribute pipeline costs to teams, environments, or applications. Tag-based governance also enables automated stale-connector cleanup.

```hcl
resource "oci_sch_service_connector" "app_log_archive" {
  compartment_id = var.compartment_ocid
  display_name   = "app-log-archive-prod"

  defined_tags = {
    "operations.environment"    = "prod"
    "operations.owner"          = "platform-team"
    "cost-tracking.cost-center" = "engineering"
    "cost-tracking.application" = "log-pipeline"
  }
  freeform_tags = {
    "managed-by" = "terraform"
  }
  # source, target, tasks...
}
```

---

## Pattern 5 — Use ACTIVE/INACTIVE State Management for Maintenance Windows

**Why**: Connectors can be paused (INACTIVE) without deletion. During infrastructure maintenance, deactivation prevents downstream targets from receiving partial or corrupted data mid-migration.

```hcl
# Terraform: maintenance mode toggle
resource "oci_sch_service_connector" "example" {
  # ...
  state = var.maintenance_mode ? "INACTIVE" : "ACTIVE"
}
```

```bash
# CLI: deactivate before maintenance
oci sch service-connector deactivate --service-connector-id <OCID>

# CLI: reactivate after maintenance
# ⚠️ Note: if source is Streaming with TRIM_HORIZON cursor, reactivation replays all retained data
oci sch service-connector activate --service-connector-id <OCID>
```
