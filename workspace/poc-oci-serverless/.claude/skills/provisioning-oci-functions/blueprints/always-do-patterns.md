### ✅ Always Do

**Provider Version Constraint**: Lock the OCI provider to a tested range to prevent breaking changes in Functions infrastructure.

```hcl
# ✅ CORRECT: Constrained provider version for Functions (OCI Provider v6.x+)
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
**Why it is mandatory**: Functions depend on networking, IAM, and OCIR. Untested provider upgrades could change resource behavior silently.
**Failure if omitted**: Uncontrolled upgrades may break `oci_functions_application` or `oci_functions_function` resources.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs

---

**Functions Application in Private Subnet with NSGs**: Application defines the network context for ALL functions. Private subnet ensures zero internet ingress. NSGs implement microsegmentation — only API Gateway can invoke.

```hcl
# ✅ CORRECT: Application in private subnet with NSGs (OCI Provider v6.x+)
resource "oci_functions_application" "this" {
  compartment_id = var.compartment_ocid
  display_name   = "app-${var.project_name}-${var.environment}"
  subnet_ids     = [var.subnet_private_id]  # PRIVATE subnet only
  shape          = var.function_shape        # GENERIC_ARM (cost-effective) or GENERIC_X86

  network_security_group_ids = var.nsg_ids   # Restrictive NSG

  config = {
    "ENVIRONMENT" = var.environment
  }

  trace_config {
    domain_id  = var.apm_domain_id
    is_enabled = true
  }

  freeform_tags = var.tags
}
```
**Why it is mandatory**: Application cannot change subnet after creation without destroy/recreate. Private subnet + NSGs prevent unauthorized invocation and DDoS exposure.
**Failure if omitted**: Functions exposed directly to internet, bypassing API Gateway auth, rate limiting, and WAF.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_application

---

**Function with Image, Memory, Timeout, and Config**: Each function is an independent executable unit. `image` points to OCIR, `memory_in_mbs` defines capacity (and proportional CPU), `timeout_in_seconds` prevents runaway executions.

```hcl
# ✅ CORRECT: Function with explicit image, memory, timeout (OCI Provider v6.x+)
resource "oci_functions_function" "api_handler" {
  application_id = oci_functions_application.this.id
  display_name   = "api-handler"
  image          = "${var.ocir_region}.ocir.io/${var.ocir_namespace}/${var.ocir_repo}:${var.image_tag}"
  image_digest   = var.image_digest  # sha256:... — MUST be updated together with image
  memory_in_mbs  = var.function_memory_in_mbs

  timeout_in_seconds = var.function_timeout_in_seconds  # Explicit — never rely on default

  config = {
    "VAULT_SECRET_OCID" = var.vault_secret_ocid  # Reference to Vault, NOT the secret value
    "BUCKET_NAME"       = var.bucket_name
  }

  trace_config {
    is_enabled = true
  }

  freeform_tags = var.tags
}
```
**Why it is mandatory**: `image` and `image_digest` must be updated atomically. Without explicit timeout, buggy functions can run up to 300s, consuming resources and increasing costs.
**Failure if omitted**: Inconsistent deploys (wrong image version running), cost overrun from runaway executions.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_function

---

**OCIR Image URI Format**: Docker images must be in OCI Container Registry in the same region as the function. URI follows OCIR-specific convention.

```hcl
# ✅ CORRECT: OCIR image URI with namespace lookup (OCI Provider v6.x+)
# Format: <region-key>.ocir.io/<tenancy-namespace>/<repo>:<tag>
data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_ocid
}

locals {
  function_image = "${var.region_key}.ocir.io/${data.oci_objectstorage_namespace.ns.namespace}/${var.ocir_repo}/${var.function_name}:${var.image_tag}"
}

resource "oci_functions_function" "this" {
  application_id = oci_functions_application.this.id
  display_name   = var.function_name
  image          = local.function_image
  memory_in_mbs  = 256
  # ...
}
```
**Why it is mandatory**: Incorrect URI format causes image pull failures (502 on invocation). Region keys: `gru` (São Paulo), `iad` (Ashburn), `phx` (Phoenix), `fra` (Frankfurt), `lhr` (London).
**Failure if omitted**: Function invocation returns 502 — image not found in OCIR.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryoverview.htm

---

**Variable Validation for Timeout and Memory**: Prevent invalid values from reaching the OCI API by validating at the Terraform layer.

```hcl
# ✅ CORRECT: Validated variables for Functions (OCI Provider v6.x+)
variable "function_timeout_in_seconds" {
  type        = number
  description = "Function timeout in seconds (5-300)"
  default     = 30

  validation {
    condition     = var.function_timeout_in_seconds >= 5 && var.function_timeout_in_seconds <= 300
    error_message = "function_timeout_in_seconds must be between 5 and 300 seconds."
  }
}

variable "function_memory_in_mbs" {
  type        = number
  description = "Function memory in MB (128, 256, 512, 1024, 2048)"
  default     = 256

  validation {
    condition     = contains([128, 256, 512, 1024, 2048], var.function_memory_in_mbs)
    error_message = "function_memory_in_mbs must be 128, 256, 512, 1024, or 2048."
  }
}
```
**Why it is mandatory**: Without validation, invalid values fail at apply time — late and expensive. Memory determines cost proportionally (2048MB = 16x cost of 128MB).
**Failure if omitted**: Plan succeeds but apply fails, wasting pipeline time.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsconcepts.htm

---

**Tagging Strategy**: Functions are billed per invocation + per GB-second. Without tags, cost tracking per team/project/environment is impossible.

```hcl
# ✅ CORRECT: Consistent tagging for cost and ownership tracking (OCI Provider v6.x+)
locals {
  common_tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "ManagedBy"   = "terraform"
    "Team"        = var.team_name
    "CostCenter"  = var.cost_center
  }
}

resource "oci_functions_application" "this" {
  # ...
  freeform_tags = local.common_tags
}

resource "oci_functions_function" "this" {
  # ...
  freeform_tags = local.common_tags
}
```
**Why it is mandatory**: OCI billing aggregation requires tags. Functions are ephemeral — without tags, costs are unattributable.
**Failure if omitted**: Impossible to trace costs by team/project/environment.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm

---

