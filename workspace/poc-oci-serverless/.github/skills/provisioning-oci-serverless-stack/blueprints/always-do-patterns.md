### ✅ Always Do

**Terraform Configuration Block**: Required for reproducibility and version contracts between provider and Terraform. Defines backend, provider source, and version constraints.

```hcl
# ✅ CORRECT: Version-pinned Terraform config with encrypted remote backend (OCI Provider v6.x+)
terraform {
  required_version = ">= 1.7"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0, < 9.0"
    }
  }

  backend "s3" {
    bucket                      = "terraform-state-bucket"
    key                         = "serverless/prod/terraform.tfstate"
    region                      = "sa-saopaulo-1"
    endpoint                    = "https://<namespace>.compat.objectstorage.sa-saopaulo-1.oraclecloud.com"
    encrypt                     = true
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    force_path_style            = true
  }
}
```

**Why it is mandatory**: Without version constraints, provider upgrades can introduce breaking changes silently. Without encrypted remote backend, state files containing OCIDs and connection strings are exposed.
**Failure if omitted**: Non-reproducible builds, state data leaks, team collaboration issues.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs

---

**Provider Authentication — Never Hardcode Credentials**: Production environments MUST use Instance Principal or Resource Principal. Local development uses `~/.oci/config` file or environment variables.

```hcl
# ✅ CORRECT: Instance Principal for production (OCI Provider v6.x+)
provider "oci" {
  auth   = "InstancePrincipal"
  region = var.region
}

# ✅ CORRECT: Resource Principal inside OCI Functions / Resource Manager
provider "oci" {
  auth   = "ResourcePrincipal"
  region = var.region
}

# ✅ CORRECT: Config file for local development (credentials in ~/.oci/config, NOT in code)
provider "oci" {
  region           = var.region
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
}
```

**Why it is mandatory**: Hardcoded credentials in Terraform code leak through VCS history, CI/CD logs, and state files.
**Failure if omitted**: Complete tenancy compromise if credentials are exposed.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs#authentication

---

**Variable Validation & Type Safety**: Use `validation` blocks to catch invalid configurations at `terraform plan` time, before any infrastructure is provisioned.

```hcl
# ✅ CORRECT: Validate OCIDs and configuration values at plan time (Terraform >= 1.7)
variable "compartment_ocid" {
  type        = string
  description = "OCID of the compartment for resource creation"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid must be a valid compartment OCID (ocid1.compartment.*)."
  }
}

variable "function_memory_in_mbs" {
  type        = number
  description = "Function memory in MB"
  default     = 256

  validation {
    condition     = contains([128, 256, 512, 1024, 2048], var.function_memory_in_mbs)
    error_message = "function_memory_in_mbs must be 128, 256, 512, 1024, or 2048."
  }
}

variable "function_timeout_in_seconds" {
  type        = number
  description = "Function timeout in seconds"
  default     = 30

  validation {
    condition     = var.function_timeout_in_seconds >= 5 && var.function_timeout_in_seconds <= 300
    error_message = "function_timeout_in_seconds must be between 5 and 300 seconds."
  }
}

variable "api_gateway_endpoint_type" {
  type        = string
  description = "API Gateway endpoint type"
  default     = "PUBLIC"

  validation {
    condition     = contains(["PUBLIC", "PRIVATE"], var.api_gateway_endpoint_type)
    error_message = "api_gateway_endpoint_type must be PUBLIC or PRIVATE."
  }
}
```

**Why it is mandatory**: Without validation, invalid OCIDs or unsupported memory sizes cause cryptic API errors during `apply` instead of clear errors during `plan`.
**Failure if omitted**: Failed applies, wasted time debugging OCI API error codes.
**Source**: https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules

---

**Tagging Strategy**: All resources MUST have freeform tags for cost tracking, ownership, compliance, and automation.

```hcl
# ✅ CORRECT: Centralized tags applied to all resources (OCI Provider v6.x+)
locals {
  common_tags = {
    "Environment" = var.environment
    "Project"     = var.project_name
    "ManagedBy"   = "terraform"
    "Owner"       = var.owner
    "CostCenter"  = var.cost_center
  }
}

# Usage in every resource
resource "oci_functions_application" "app" {
  compartment_id = var.compartment_ocid
  display_name   = "app-${var.project_name}-${var.environment}"
  subnet_ids     = [var.subnet_private_id]
  shape          = "GENERIC_X86"
  freeform_tags  = local.common_tags
}

resource "oci_apigateway_gateway" "this" {
  compartment_id = var.compartment_ocid
  display_name   = "gw-${var.project_name}-${var.environment}"
  endpoint_type  = var.api_gateway_endpoint_type
  subnet_id      = var.subnet_public_id
  freeform_tags  = local.common_tags
}
```

**Why it is mandatory**: Without tags, cost attribution, compliance auditing, and resource lifecycle automation are impossible.
**Failure if omitted**: Untrackable cloud spend, compliance violations, orphaned resources.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm

---

**Granular IAM Policies with Dynamic Groups**: Functions use Resource Principal via Dynamic Groups. Policies MUST be scoped to specific resource types and compartments — never tenancy-wide wildcards.

```hcl
# ✅ CORRECT: Dynamic Group matching Functions in a specific compartment (OCI Provider v6.x+)
resource "oci_identity_dynamic_group" "functions" {
  compartment_id = var.tenancy_ocid  # Dynamic Groups are tenancy-level
  name           = "dg-${var.project_name}-functions-${var.environment}"
  description    = "Dynamic group for ${var.project_name} Functions in ${var.environment}"

  matching_rule = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"

  freeform_tags = local.common_tags
}

# ✅ CORRECT: Least-privilege policies scoped to compartment
resource "oci_identity_policy" "functions" {
  compartment_id = var.compartment_ocid
  name           = "policy-${var.project_name}-functions-${var.environment}"
  description    = "Policies for ${var.project_name} Functions"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use fn-invocation in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read secret-bundles in compartment ${var.compartment_name}",
  ]

  freeform_tags = local.common_tags
}
```

**Why it is mandatory**: Overly broad IAM policies violate least-privilege and create privilege escalation risks.
**Failure if omitted**: Any compromised function gains unrestricted tenancy access.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm

---

