### ✅ Always Do

## Contents
1. Provider Version Constraint
2. Compartment-Scoped Dynamic Groups
3. Least-Privilege Policies with Minimum Verb
4. Service Policies at Tenancy-Level
5. Compartment Hierarchy with Terraform
6. Variable Validation for OCIDs
7. Explicit depends_on for Downstream Modules
8. Tags on All IAM Resources
9. Outputs for Inter-Module Dependencies

---

**Provider Version Constraint**: Lock the OCI provider to a tested range to prevent breaking changes in security-critical IAM resources.

```hcl
# ✅ CORRECT: Constrained provider version for IAM stability (OCI Provider v6.x+)
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
**Why it is mandatory**: IAM resources govern all authorization. An untested provider upgrade could silently change policy behavior.
**Failure if omitted**: Uncontrolled provider upgrades may introduce breaking changes to `oci_identity_policy` or `oci_identity_dynamic_group` resources.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs

---

**Compartment-Scoped Dynamic Groups**: Dynamic Groups MUST use `ALL {}` matching rules scoped to a specific compartment. This is the authentication mechanism for resource-to-service access (Resource Principal).

```hcl
# ✅ CORRECT: Dynamic Group scoped to compartment (OCI Provider v6.x+)
# compartment_id MUST be tenancy_ocid — Dynamic Groups are tenancy-level resources
resource "oci_identity_dynamic_group" "functions" {
  compartment_id = var.tenancy_ocid
  name           = "dg-functions-${var.project_name}-${var.environment}"
  description    = "Dynamic group for Functions in compartment ${var.compartment_name}"

  # ALL{} with compartment constraint = least-privilege scoping
  matching_rule = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"

  freeform_tags = local.iam_tags
}

# ✅ CORRECT: Separate Dynamic Group for API Gateway (OCI Provider v6.x+)
resource "oci_identity_dynamic_group" "api_gateway" {
  compartment_id = var.tenancy_ocid
  name           = "dg-apigw-${var.project_name}-${var.environment}"
  description    = "Dynamic group for API Gateways in compartment ${var.compartment_name}"

  # 'ApiGateway' is PascalCase — case-sensitive!
  matching_rule = "ALL {resource.type = 'ApiGateway', resource.compartment.id = '${var.compartment_ocid}'}"

  freeform_tags = local.iam_tags
}
```
**Why it is mandatory**: Without compartment scoping, ANY resource of that type across the entire tenancy receives the associated permissions — cross-compartment privilege escalation.
**Failure if omitted**: A compromised compartment grants attacker access to all resources of that type tenancy-wide.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm

---

**Least-Privilege Policies with Minimum Verb**: Use the most restrictive verb that satisfies the requirement. Verb hierarchy: `inspect` < `read` < `use` < `manage`.

```hcl
# ✅ CORRECT: Granular policies with minimum verb (OCI Provider v6.x+)
resource "oci_identity_policy" "functions_access_services" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-services-${var.project_name}-${var.environment}"
  description    = "Permits Functions to access OCI services via Resource Principal"

  statements = [
    # read (NOT manage) — Functions only read secrets, never create them
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read secret-bundles in compartment ${var.compartment_name}",
    # manage objects — Functions need create/read/update/delete on objects
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to manage objects in compartment ${var.compartment_name}",
    # use (NOT manage) — Functions write logs, don't manage log groups
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use log-content in compartment ${var.compartment_name}",
  ]

  freeform_tags = local.iam_tags
}

# ✅ CORRECT: API Gateway only needs fn-invocation (not functions-family)
resource "oci_identity_policy" "apigw_invoke_functions" {
  compartment_id = var.compartment_ocid
  name           = "policy-apigw-invoke-${var.project_name}-${var.environment}"
  description    = "Permits API Gateway to invoke Functions"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.api_gateway.name} to use fn-invocation in compartment ${var.compartment_name}",
  ]

  freeform_tags = local.iam_tags
}
```
**Why it is mandatory**: OCI policies are additive (no deny). Over-permissioning via `manage all-resources` means a compromised Function owns the entire compartment.
**Failure if omitted**: Privilege escalation — attacker can delete VCN, create users, exfiltrate data from a single compromised Function.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/policyreference.htm

---

**Service Policies at Tenancy-Level**: OCI managed services (FaaS, API Gateway) require platform-level policies in the root compartment (`tenancy_ocid`). These are distinct from Dynamic Group policies.

```hcl
# ✅ CORRECT: Service policy at tenancy level (OCI Provider v6.x+)
# 'Allow service FaaS' refers to the OCI platform service — NOT a Dynamic Group
resource "oci_identity_policy" "faas_network" {
  compartment_id = var.tenancy_ocid  # MUST be tenancy — service policies are platform-level
  name           = "policy-faas-network-${var.project_name}-${var.environment}"
  description    = "Permits FaaS service to use VCN and OCIR"

  statements = [
    "Allow service FaaS to use virtual-network-family in compartment ${var.compartment_name}",
    "Allow service FaaS to read repos in tenancy",
  ]

  freeform_tags = local.iam_tags
}
```
**Why it is mandatory**: Without this policy, Function Application creation fails — FaaS cannot attach to VCN subnets or pull images from OCIR. Service names are case-sensitive: `FaaS`, `ApiGateway`.
**Failure if omitted**: Functions cannot deploy to private subnets; API Gateway returns 502 Bad Gateway.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingpolicies.htm

---

**Compartment Hierarchy with Terraform**: Compartments isolate resources, scope policies, and control blast radius. Always set `enable_delete = true` for Terraform lifecycle management.

```hcl
# ✅ CORRECT: Compartment hierarchy with lifecycle control (OCI Provider v6.x+)
resource "oci_identity_compartment" "project" {
  compartment_id = var.tenancy_ocid  # Parent compartment
  name           = "${var.project_name}-${var.environment}"
  description    = "Compartment for ${var.project_name} (${var.environment})"
  enable_delete  = true  # Permits terraform destroy

  freeform_tags = local.iam_tags
}

# Sub-compartments for additional isolation
resource "oci_identity_compartment" "network" {
  compartment_id = oci_identity_compartment.project.id
  name           = "network"
  description    = "Network resources for ${var.project_name}"
  enable_delete  = true

  freeform_tags = local.iam_tags
}

resource "oci_identity_compartment" "security" {
  compartment_id = oci_identity_compartment.project.id
  name           = "security"
  description    = "Security resources (Vault, Keys) for ${var.project_name}"
  enable_delete  = true

  freeform_tags = local.iam_tags
}
```
**Why it is mandatory**: Compartments are the primary isolation boundary in OCI. Without `enable_delete = true`, Terraform will NOT delete compartments on destroy — it only removes from state, leaving orphaned resources.
**Failure if omitted**: Orphaned compartments accumulate; Terraform state diverges from reality. Compartment names must be unique within parent. Delete takes up to 90 minutes (async operation).
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_compartment

---

**Variable Validation for OCIDs**: Validate OCID format at plan-time to catch misconfigurations before apply.

```hcl
# ✅ CORRECT: OCID format validation catches errors at plan-time (Terraform >= 1.7)
variable "tenancy_ocid" {
  type        = string
  description = "OCID of the OCI tenancy"

  validation {
    condition     = can(regex("^ocid1\\.tenancy\\.", var.tenancy_ocid))
    error_message = "tenancy_ocid must be a valid OCID (ocid1.tenancy.*)."
  }
}

variable "compartment_ocid" {
  type        = string
  description = "OCID of the target compartment"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid must be a valid compartment OCID."
  }
}

variable "compartment_name" {
  type        = string
  description = "Name of the compartment (used in policy statements)"

  validation {
    condition     = length(var.compartment_name) > 0 && length(var.compartment_name) <= 100
    error_message = "compartment_name must be between 1 and 100 characters."
  }
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}
```
**Why it is mandatory**: Invalid OCIDs in policy statements cause apply-time errors that are harder to diagnose than plan-time validation failures.
**Failure if omitted**: Terraform apply fails with cryptic OCI API errors instead of clear validation messages.
**Source**: https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules

---

**Explicit `depends_on` for Downstream Modules**: IAM policy propagation takes up to 60 seconds. Resources that depend on policies must wait.

```hcl
# ✅ CORRECT: Explicit dependency chain (OCI Provider v6.x+)
module "iam" {
  source           = "./modules/iam"
  tenancy_ocid     = var.tenancy_ocid
  compartment_ocid = var.compartment_ocid
  compartment_name = var.compartment_name
  environment      = var.environment
  project_name     = var.project_name
  tags             = local.tags
}

module "app_my_function" {
  source    = "../../modules/function-app"
  subnet_id = module.network.subnet_private_id
  depends_on = [module.iam]  # CRITICAL: wait for policy propagation
}

module "api_gateway" {
  source         = "../../modules/api-gateway"
  route_backends = [{ path = "/hello", methods = ["GET"], function_id = module.app_my_function.function_id }]
  depends_on     = [module.iam]  # CRITICAL: fn-invocation policy needed
}
```
**Why it is mandatory**: Terraform may create resources in parallel without explicit dependency. If Functions deploy before IAM policies propagate, deployments fail with authorization errors.
**Failure if omitted**: Intermittent deployment failures, 502 errors from API Gateway, permission denied from Functions.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm

---

**Tags on All IAM Resources**: IAM resources (Dynamic Groups, Policies) exist at tenancy level and can proliferate. Tags ensure traceability and ownership.

```hcl
# ✅ CORRECT: Standard tags for all IAM resources (OCI Provider v6.x+)
locals {
  iam_tags = merge(var.tags, {
    "Environment" = var.environment
    "Project"     = var.project_name
    "ManagedBy"   = "terraform"
    "Module"      = "iam"
  })
}
```
**Why it is mandatory**: Without tags, orphaned Dynamic Groups and Policies accumulate and become impossible to trace or clean up.
**Failure if omitted**: Resource sprawl with no audit trail.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm

---

**Outputs for Inter-Module Dependencies**: IAM module creates Dynamic Groups and Policies that are prerequisites for Functions and API Gateway. Outputs allow validation and downstream referencing.

```hcl
# ✅ CORRECT: outputs.tf — Required for downstream modules (OCI Provider v6.x+)
output "dynamic_group_functions_id" {
  value       = oci_identity_dynamic_group.functions.id
  description = "OCID of the Functions Dynamic Group"
}

output "dynamic_group_functions_name" {
  value       = oci_identity_dynamic_group.functions.name
  description = "Name of the Functions Dynamic Group (for policy references)"
}

output "dynamic_group_apigw_id" {
  value       = oci_identity_dynamic_group.api_gateway.id
  description = "OCID of the API Gateway Dynamic Group"
}

output "dynamic_group_apigw_name" {
  value       = oci_identity_dynamic_group.api_gateway.name
  description = "Name of the API Gateway Dynamic Group"
}

output "policy_faas_network_id" {
  value       = oci_identity_policy.faas_network.id
  description = "OCID of the FaaS network policy"
}
```
**Why it is mandatory**: Without outputs, downstream modules cannot reference IAM resources or validate their creation.
**Failure if omitted**: No visibility into IAM resource creation; downstream modules cannot validate prerequisites.
**Source**: https://developer.hashicorp.com/terraform/language/values/outputs
