# Always Do Patterns — OCI Service Connector Hub

Mandatory patterns for every `oci_sch_service_connector` resource. Auto-execute without waiting for user confirmation.

---

## Pattern 1 — Terraform Configuration Block with Provider Constraint

**Why**: Pins the provider to the `8.x` series, blocking unreviewed major-version breaking changes. `>= 1.7` enables `nullable` variable support, `check` blocks (1.8+), and the `terraform test` command.

```hcl
terraform {
  required_version = ">= 1.7"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 8.0"
    }
  }
}
```

---

## Pattern 2 — Provider Configuration with IAM Authentication

**Why**: OCI provider authentication must use instance principal (compute/Functions), resource principal (OCI Resource Manager), or API key path (CI/CD). Never hardcode API keys or private key content in Terraform code.

```hcl
# Option A: API key path (CI/CD pipelines) — path only, never inline content
provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path  # Path to file, never the key content
  region           = var.region
}

# Option B: Resource Principal (OCI Resource Manager) — recommended for production automation
provider "oci" {
  auth   = "ResourcePrincipal"
  region = var.region
}

# Option C: Instance Principal (OCI Compute) — no credentials needed
provider "oci" {
  auth   = "InstancePrincipal"
  region = var.region
}
```

**Security**: Option B (ResourcePrincipal) is the production standard — no credentials in code or environment variables.

---

## Pattern 3 — Variable Validation for OCIDs and Enum Values

**Why**: Catches invalid OCID formats, unsupported source/target kind values, and empty required fields at `terraform validate` — before any API call is made.

```hcl
variable "compartment_ocid" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid must start with 'ocid1.compartment.'"
  }
}

variable "source_kind" {
  type    = string
  default = "logging"
  validation {
    condition     = contains(["logging", "streaming", "monitoring", "plugin"], var.source_kind)
    error_message = "source_kind must be one of: logging, streaming, monitoring, plugin"
  }
}

variable "connector_state" {
  type    = string
  default = "ACTIVE"
  validation {
    condition     = contains(["ACTIVE", "INACTIVE"], var.connector_state)
    error_message = "connector_state must be ACTIVE or INACTIVE"
  }
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod"
  }
}
```

---

## Pattern 4 — IAM Policies Before Connector Activation

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

## Pattern 5 — Scope Logging Source to Minimum Required Boundary

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

## Pattern 6 — Set Object Name Prefix on Object Storage Target

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

## Pattern 7 — Tag Every Connector

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

## Pattern 8 — Deploy Error Monitoring Alarm per Production Connector

**Why**: A connector that transitions to FAILED emits no visible OCI Monitoring metrics — data pipeline failures are invisible until downstream systems report missing data. Deploy two alarms alongside every production connector: one for errors, one for absence of throughput.

```hcl
# Alarm 1: any error count (connector operational failures)
resource "oci_monitoring_alarm" "connector_error" {
  compartment_id        = var.connector_compartment_ocid
  display_name          = "${var.connector_display_name}-error-alarm"
  metric_compartment_id = var.connector_compartment_ocid
  namespace             = "oci_service_connector_hub"
  query                 = "ErrorCount[1m].sum() > 0"
  severity              = "CRITICAL"
  destinations          = [oci_ons_notification_topic.ops_alerts.id]
  is_enabled            = true
}

# Alarm 2: absence of throughput (catches silent FAILED where ErrorCount = 0)
resource "oci_monitoring_alarm" "connector_no_throughput" {
  compartment_id        = var.connector_compartment_ocid
  display_name          = "${var.connector_display_name}-no-throughput-alarm"
  metric_compartment_id = var.connector_compartment_ocid
  namespace             = "oci_service_connector_hub"
  query                 = "BytesTransferred[5m].sum() == 0"
  severity              = "WARNING"
  destinations          = [oci_ons_notification_topic.ops_alerts.id]
  is_enabled            = true
  pending_duration      = "PT5M"  # Avoid flapping from brief idle periods
}
```

**Verification**:
```bash
oci monitoring alarm list \
  --compartment-id <COMPARTMENT_OCID> \
  --query 'data[?contains("query-text", `ErrorCount`)].{name:"display-name",enabled:"is-enabled"}'
# Expected: at least one alarm with enabled = true
```
