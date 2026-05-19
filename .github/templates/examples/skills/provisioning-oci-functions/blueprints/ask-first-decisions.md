### ⚠️ Ask First

> 📎 **Architecture decisions**: For detailed trade-off analysis of Provisioned Concurrency vs On-Demand, Sync vs Detached Mode, and X86 vs ARM shapes, consult the skill `architecting-oci-serverless`. This section covers only the **Terraform implementation** of each option.

**Decision Point**: Provisioned Concurrency vs On-Demand

> 📎 See `architecting-oci-serverless` for architecture decision factors (SLA, cold starts, cost analysis).

**Agent Behavior**:
"Before implementing, ask the user:
'Does this function serve user-facing API requests with latency SLA, or is it for background/event processing?'"

```hcl
# Provisioned Concurrency: pre-warmed instances (OCI Provider v6.x+)
resource "oci_functions_function" "api_handler" {
  application_id     = oci_functions_application.this.id
  display_name       = "api-handler"
  image              = var.function_image
  memory_in_mbs      = 512
  timeout_in_seconds = 30

  # Dynamic block — only creates if provisioned_concurrency > 0
  dynamic "provisioned_concurrency_config" {
    for_each = var.provisioned_concurrency > 0 ? [1] : []
    content {
      strategy = "CONSTANT"
      count    = var.provisioned_concurrency  # Max 40 per function
    }
  }

  freeform_tags = var.tags
}

variable "provisioned_concurrency" {
  type        = number
  description = "Pre-warmed instances (0 = on-demand)"
  default     = 0

  validation {
    condition     = var.provisioned_concurrency >= 0 && var.provisioned_concurrency <= 40
    error_message = "provisioned_concurrency must be between 0 and 40."
  }
}
```

**Decision Factors**:
- Invocation frequency (> 1/10min → consider provisioned for Java)
- Latency SLA (P99 < 200ms requires provisioned)
- Budget (provisioned = 25% of execution rate for idle instances)

**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingprovisionedconcurrency.htm

---

**Decision Point**: Synchronous vs Detached Mode (Async)

> 📎 See `architecting-oci-serverless` for architecture decision factors (duration, caller patterns, result routing).

**Agent Behavior**:
"Before implementing, ask the user:
'Does this function need to execute longer than 300 seconds, or does the caller not need to wait for the response?'"

```hcl
# Detached Mode: async execution with destinations (OCI Provider v6.x+)
resource "oci_functions_function" "batch_processor" {
  application_id     = oci_functions_application.this.id
  display_name       = "batch-processor"
  image              = var.batch_function_image
  memory_in_mbs      = 1024
  timeout_in_seconds = 300

  # Detached mode timeout is SEPARATE from execution timeout
  detached_mode_timeout_in_seconds = 900  # 15 minutes

  success_destination {
    kind      = "STREAM"
    stream_id = var.result_stream_ocid
  }

  failure_destination {
    kind     = "NOTIFICATION"
    topic_id = var.error_topic_ocid
  }

  freeform_tags = var.tags
}
```

**Decision Factors**:
- Expected execution duration (> 60s for API GW → detached)
- Caller needs synchronous response or just acknowledgment
- Need for result routing (success/failure to different destinations)

**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_function

---

**Decision Point**: Processor Architecture — GENERIC_X86 vs GENERIC_ARM vs GENERIC_X86_ARM

> 📎 See `architecting-oci-serverless` for architecture decision factors (compatibility, cost savings, multi-arch).

**Agent Behavior**:
"Before implementing, ask the user:
'Does your function use any x86-specific native libraries?
GENERIC_ARM is ~20% cheaper but requires ARM-compatible dependencies.
Note: Shape is set at the Application level — ALL functions in the same Application share the same architecture.'"

```hcl
# Shape variable with validation (OCI Provider v6.x+)
variable "function_shape" {
  type        = string
  description = "Processor architecture (Application-level)"
  default     = "GENERIC_ARM"

  validation {
    condition     = contains(["GENERIC_X86", "GENERIC_ARM", "GENERIC_X86_ARM"], var.function_shape)
    error_message = "function_shape must be GENERIC_X86, GENERIC_ARM, or GENERIC_X86_ARM."
  }
}
```

**Decision Factors**:
- Native library compatibility (x86-only deps → GENERIC_X86)
- Cost sensitivity (ARM is ~20% cheaper)
- Multi-arch Docker images available?

**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_application

---

**Decision Point**: Image Signature Verification (Image Policy)

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| **Disabled** (default) | Speed — any image deploys immediately | Security — no supply chain verification | Development, prototypes, fast iteration |
| **Enabled** with KMS key | Security — only signed images deploy | Speed — CI/CD must include signing step | Production, regulated environments (PCI-DSS, SOC2) |

**Agent Behavior**:
"Before implementing, ask the user:
'Does this environment require image signature verification (e.g., production, compliance)?
Enabling image policy blocks deployment of unsigned images. CI/CD pipeline must include `oci artifacts container image sign`.'"

```hcl
# Image policy with KMS key (OCI Provider v6.x+)
resource "oci_functions_application" "secure" {
  compartment_id = var.compartment_ocid
  display_name   = "app-secure-${var.environment}"
  subnet_ids     = [var.subnet_private_id]
  shape          = "GENERIC_ARM"

  image_policy_config {
    is_policy_enabled = true

    key_details {
      kms_key_id = var.image_signing_key_ocid
    }
  }

  freeform_tags = var.tags
}
```

**Decision Factors**:
- Compliance requirements (PCI-DSS, SOC2 → enable)
- CI/CD pipeline maturity (must support image signing)
- Environment tier (prod → enable, dev → optional)

**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingimagesignatureverification.htm

---

**Decision Point**: Custom Function vs Pre-Built Function (PBF)

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| **Custom Function** | Full flexibility — any logic | Dev effort — must write and maintain code | Custom business logic |
| **Pre-Built Function (PBF)** | Speed — zero code | Flexibility — only predefined configuration | Standard OCI operations (resize, backup, etc.) |

**Agent Behavior**:
"Before implementing, ask the user:
'Is this a standard OCI operation (e.g., compute resize, backup) or custom business logic?
Pre-Built Functions are ready-made and require zero code, but only support predefined operations.'"

```hcl
# Pre-Built Function (OCI Provider v6.x+)
data "oci_functions_pbf_listings" "available" {}

resource "oci_functions_function" "pbf_example" {
  application_id = oci_functions_application.this.id
  display_name   = "pbf-object-processor"
  memory_in_mbs  = 256

  source_details {
    source_type    = "PBF"
    pbf_listing_id = data.oci_functions_pbf_listings.available.pbf_listings_collection[0].items[0].id
  }

  freeform_tags = var.tags
}
```

**Decision Factors**:
- Standard vs custom operation
- Time-to-deploy priority
- Maintenance overhead tolerance

**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/functions_pbf_listings

---

