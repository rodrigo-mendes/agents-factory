# Always Do Patterns — OCI Logging (Terraform oracle/oci ~> 8.15)

## Pattern 1: Terraform Provider Constraint

```hcl
terraform {
  required_version = ">= 1.9"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 8.15"
    }
  }
}
```
**Why**: Pins to v8.x major line; prevents silent breaking changes from v9.x.

---

## Pattern 2: Provider Authentication (No Hardcoded Credentials)

```hcl
# Production: Instance Principal (no credentials in code or state)
provider "oci" {
  auth   = "InstancePrincipal"
  region = var.region
}

# CI/CD / Local dev: API Key via config file profile
provider "oci" {
  auth             = "ApiKey"
  config_file_path = "~/.oci/config"
  profile          = var.oci_profile  # default: "DEFAULT"
  region           = var.region
}
```
**Why**: Inline credentials (`tenancy_ocid`, `fingerprint`, `private_key_path`) expose audit identity and break CI/CD pipelines.

---

## Pattern 3: Dedicated Log Group per Access Control Boundary

```hcl
resource "oci_logging_log_group" "app_logs" {
  compartment_id = var.compartment_id
  display_name   = "${var.app_name}-${var.environment}-app-logs"
  description    = "Application logs for ${var.app_name}"
  freeform_tags  = local.common_tags
  defined_tags   = var.defined_tags
}

resource "oci_logging_log_group" "infra_logs" {
  compartment_id = var.compartment_id
  display_name   = "${var.app_name}-${var.environment}-infra-logs"
  description    = "Infrastructure logs (VCN flow, LB access)"
  freeform_tags  = local.common_tags
  defined_tags   = var.defined_tags
}
```
**Why**: Log Groups are IAM policy targets. Mixing audit, app, and infra logs in one group forces overly broad policies and prevents selective Connector Hub routing.

---

## Pattern 4: Log Object with Explicit `retention_duration` and `is_enabled = true`

```hcl
# SERVICE log (OCI platform-generated)
resource "oci_logging_log" "lb_access" {
  display_name       = "${var.app_name}-${var.environment}-lb-access"
  log_group_id       = oci_logging_log_group.infra_logs.id
  log_type           = "SERVICE"
  is_enabled         = true                    # MUST be explicit
  retention_duration = var.log_retention_days  # MUST be explicit

  configuration {
    source {
      source_type = "OCISERVICE"
      service     = "loadbalancer"
      resource    = var.load_balancer_ocid
      category    = "access"
    }
    compartment_id = var.compartment_id
  }

  freeform_tags = local.common_tags
}

# CUSTOM log (application logs via UMA)
resource "oci_logging_log" "app_custom" {
  display_name       = "${var.app_name}-${var.environment}-app-custom"
  log_group_id       = oci_logging_log_group.app_logs.id
  log_type           = "CUSTOM"
  is_enabled         = true
  retention_duration = var.log_retention_days
  freeform_tags      = local.common_tags
}
```
**Why**: Default `retention_duration` is 30 days — data is permanently deleted and unrecoverable. `is_enabled = false` silently stops ingestion with no alarm.

---

## Pattern 5: Variable Validation for `retention_duration`

```hcl
variable "log_retention_days" {
  type        = number
  description = "Log retention in days. OCI supports 30-day increments: 30, 60, 90, 120, 150, 180."
  default     = 90

  validation {
    condition     = contains([30, 60, 90, 120, 150, 180], var.log_retention_days)
    error_message = "log_retention_days must be 30, 60, 90, 120, 150, or 180."
  }
}

variable "region" {
  type        = string
  description = "OCI region identifier (e.g., us-ashburn-1)."

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.region))
    error_message = "Region must follow OCI format: us-ashburn-1."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment."

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}
```
**Why**: Invalid `retention_duration` causes an apply-time API error. Validation surfaces it at plan time.

---

## Pattern 6: UMA Dynamic Group + IAM Policy + Configuration Trio

```hcl
# Step 1: Dynamic group (always in tenancy compartment)
resource "oci_identity_dynamic_group" "log_agents" {
  compartment_id = var.tenancy_ocid
  name           = "${var.app_name}-${var.environment}-log-agents"
  description    = "Compute instances authorized to send logs"
  matching_rule  = "ALL {instance.compartment.id = '${var.compartment_id}'}"
}

# Step 2: IAM policy
resource "oci_identity_policy" "log_agents" {
  compartment_id = var.compartment_id
  name           = "${var.app_name}-${var.environment}-log-agent-policy"
  description    = "Allows UMA agents to write logs"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.log_agents.name} to use log-content in compartment id ${var.compartment_id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.log_agents.name} to read log-groups in compartment id ${var.compartment_id}"
  ]
}

# Step 3: UMA configuration
resource "oci_logging_unified_agent_configuration" "app" {
  compartment_id = var.compartment_id
  display_name   = "${var.app_name}-${var.environment}-ua-config"
  description    = "Collects app logs from compute instances"
  is_enabled     = true
  freeform_tags  = local.common_tags

  group_association {
    group_list = [oci_identity_dynamic_group.log_agents.id]
  }

  service_configuration {
    configuration_type = "LOGGING"

    sources {
      name        = "app-json-logs"
      source_type = "LOG_TAIL"
      paths       = ["/var/log/${var.app_name}/*.log"]

      parser {
        parser_type = "JSON"
      }
    }

    destination {
      log_object_id = oci_logging_log.app_custom.id
    }
  }

  depends_on = [oci_identity_policy.log_agents]
}
```
**Why**: UMA silently fails to write logs without the IAM policy. Dynamic group membership auto-includes new compute instances — no Terraform re-apply required when scaling.

---

## Pattern 7: `lifecycle { prevent_destroy = true }` on Production Log Groups

```hcl
resource "oci_logging_log_group" "audit_logs" {
  compartment_id = var.compartment_id
  display_name   = "${var.app_name}-${var.environment}-audit-logs"
  description    = "Audit and compliance logs — deletion protected"
  freeform_tags  = merge(local.common_tags, { "compliance" = "true" })

  lifecycle {
    prevent_destroy = true
  }
}
```
**Why**: Deleting a Log Group permanently destroys all child Log objects and in-flight buffered data. `prevent_destroy` forces an explicit lifecycle block removal before any deletion can proceed.

---

## Pattern 8: Output Definitions for Cross-Stack OCID Dependencies

```hcl
output "app_log_group_id" {
  value       = oci_logging_log_group.app_logs.id
  description = "OCID of the application log group — reference in Connector Hub source"
}

output "app_custom_log_id" {
  value       = oci_logging_log.app_custom.id
  description = "OCID of the custom app log — reference in UMA destination and API Gateway"
}

output "infra_log_group_id" {
  value       = oci_logging_log_group.infra_logs.id
  description = "OCID of the infra log group"
}
```
**Why**: Log Group and Log OCIDs are consumed by Connector Hub, API Gateway, Load Balancer, and other stacks. Outputs avoid hardcoding OCIDs across modules.

---

## Pattern 9: Mandatory `freeform_tags` via `locals`

```hcl
locals {
  common_tags = {
    "managed_by"  = "terraform"
    "environment" = var.environment
    "app"         = var.app_name
    "cost_center" = var.cost_center
    "owner"       = var.owner
  }
}

# Apply to every resource
resource "oci_logging_log_group" "app_logs" {
  compartment_id = var.compartment_id
  display_name   = "${var.app_name}-${var.environment}-app-logs"
  freeform_tags  = local.common_tags
  defined_tags   = var.defined_tags
}
```
**Why**: OCI Logging has no native tag enforcement. `local.common_tags` ensures all resources carry consistent traceability, cost attribution, and automation labels.
