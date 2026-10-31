### ✅ Always Do

**Provider Version Constraint**: Lock the OCI provider to a tested range to prevent breaking changes in long-lived Streaming resources.

```hcl
# ✅ CORRECT: Constrained provider version for Streaming stability (OCI Provider v6.x+)
terraform {
  required_version = ">= 1.7"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0, < 9.0"
    }
  }
}
```
**Why it is mandatory**: Streaming resources contain data in transit. An untested provider upgrade could silently change immutable attribute handling, triggering unexpected destroy/recreate.
**Failure if omitted**: Uncontrolled provider upgrades may force pool recreation, destroying all streams and in-flight messages.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs

---

**Private Stream Pool with Custom Encryption**: Stream Pool defines network and encryption for ALL Streams within it. Private endpoint restricts access to the VCN only. Custom KMS key is required for compliance (PCI-DSS, SOC2).

```hcl
# ✅ CORRECT: Private Stream Pool with KMS encryption (OCI Provider v6.x+)
resource "oci_streaming_stream_pool" "this" {
  compartment_id = var.compartment_ocid
  name           = "sp-${var.project_name}-${var.environment}"

  # Customer-managed encryption key — required for compliance
  custom_encryption_key {
    kms_key_id = var.kms_key_ocid
  }

  # Kafka compatibility settings — disable auto-create in production
  kafka_settings {
    auto_create_topics_enable = false
    log_retention_hours       = var.retention_hours
    num_partitions            = var.default_partitions
  }

  # Private endpoint — accessible only from within the VCN
  private_endpoint_settings {
    subnet_id = var.subnet_private_id
    nsg_ids   = var.nsg_ids
  }

  freeform_tags = var.tags
}
```
**Why it is mandatory**: Public pool exposes Kafka endpoint to the internet. Oracle-managed key provides no customer control over rotation or revocation. Both violate production security posture.
**Failure if omitted**: Data exposure via public endpoint; compliance gaps with Oracle-managed encryption; no network-level access control.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream_pool

---

**Stream with Explicit Partitions and Retention in Stream Pool**: Streams MUST be created within an explicit Stream Pool (not standalone) to inherit network and encryption settings. Both `partitions` and `retention_in_hours` are immutable — plan carefully.

```hcl
# ✅ CORRECT: Stream in explicit pool with planned partitions (OCI Provider v6.x+)
resource "oci_streaming_stream" "events" {
  name               = "stream-events-${var.project_name}-${var.environment}"
  partitions         = var.stream_partitions       # Immutable after creation!
  retention_in_hours = var.stream_retention_hours   # Read-only after creation!
  stream_pool_id     = oci_streaming_stream_pool.this.id

  freeform_tags = var.tags
}
```
**Why it is mandatory**: Standalone streams (using `compartment_id` only) create a public default pool without encryption or private endpoint. Changing partitions or retention forces destroy/recreate with data loss.
**Failure if omitted**: OCI creates a public default pool; immutable attribute changes cause data loss in production.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream

---

**Variable Validation for Immutable Attributes**: Partitions and retention are immutable — incorrect values require destroy/recreate with data loss. Validate at plan time.

```hcl
# ✅ CORRECT: Validation prevents costly mistakes (Terraform v1.7+)
variable "stream_partitions" {
  type        = number
  description = "Number of partitions (immutable after creation, 1-50)"
  default     = 1

  validation {
    condition     = var.stream_partitions >= 1 && var.stream_partitions <= 50
    error_message = "stream_partitions must be between 1 and 50."
  }
}

variable "stream_retention_hours" {
  type        = number
  description = "Retention in hours (immutable after creation, 24-168)"
  default     = 24

  validation {
    condition     = var.stream_retention_hours >= 24 && var.stream_retention_hours <= 168
    error_message = "stream_retention_hours must be between 24 and 168 (7 days max)."
  }
}

variable "default_partitions" {
  type        = number
  description = "Default partitions for Kafka auto-created topics in Stream Pool"
  default     = 1

  validation {
    condition     = var.default_partitions >= 1 && var.default_partitions <= 50
    error_message = "default_partitions must be between 1 and 50."
  }
}

variable "retention_hours" {
  type        = number
  description = "Default Kafka log retention in Stream Pool (hours)"
  default     = 24

  validation {
    condition     = var.retention_hours >= 24 && var.retention_hours <= 168
    error_message = "retention_hours must be between 24 and 168."
  }
}
```
**Why it is mandatory**: Plan-time validation prevents deploying streams with invalid partition/retention values that would require destroy/recreate to fix.
**Failure if omitted**: Invalid values are only caught at apply time; correcting them forces data-losing recreation.
**Source**: https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules

---

**Lifecycle Prevent Destroy for Critical Streams**: Streams carrying business events or audit logs must be protected from accidental destruction caused by modifying immutable attributes.

```hcl
# ✅ CORRECT: Prevent accidental destroy of audit stream (OCI Provider v6.x+)
resource "oci_streaming_stream" "audit" {
  name               = "stream-audit-${var.project_name}-${var.environment}"
  partitions         = 5
  retention_in_hours = 168  # 7 days max retention
  stream_pool_id     = oci_streaming_stream_pool.this.id

  freeform_tags = var.tags

  lifecycle {
    prevent_destroy = true
  }
}
```
**Why it is mandatory**: Modifying immutable attributes (partitions, retention) triggers destroy/recreate. `prevent_destroy` blocks this, forcing explicit acknowledgment before data loss.
**Failure if omitted**: `terraform apply` silently destroys stream with unconsumed messages when immutable attributes change.
**Source**: https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle

---

**Tagging Strategy for Cost Attribution**: Streaming is billed per partition-hour. Without tags, cost attribution across teams/projects is impossible.

```hcl
# ✅ CORRECT: Tags on both Stream Pool and individual Streams (OCI Provider v6.x+)
locals {
  common_tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "ManagedBy"   = "terraform"
    "Team"        = var.team_name
    "CostCenter"  = var.cost_center
  }
}

resource "oci_streaming_stream_pool" "this" {
  # ...
  freeform_tags = local.common_tags
}

resource "oci_streaming_stream" "this" {
  # ...
  freeform_tags = local.common_tags
}
```
**Why it is mandatory**: High-throughput streams with many partitions generate significant costs. Tags enable cost visibility and chargeback.
**Failure if omitted**: Unattributable costs; compliance gaps in cost governance.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm

---

