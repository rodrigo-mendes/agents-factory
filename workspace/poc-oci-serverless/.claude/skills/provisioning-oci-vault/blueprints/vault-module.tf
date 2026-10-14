# =============================================================================
# OCI Vault Terraform Module Blueprint — Terraform OCI Provider v6.x+
# Complete reusable module: main.tf + variables.tf + outputs.tf + iam.tf
# =============================================================================

# ─── versions.tf ─────────────────────────────────────────────────────────────
terraform {
  required_version = ">= 1.7"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0, < 9.0"
    }
  }
}

# ─── variables.tf ────────────────────────────────────────────────────────────

variable "compartment_ocid" {
  type        = string
  description = "OCID of the compartment for vault resources"
}

variable "compartment_name" {
  type        = string
  description = "Name of the compartment (used in IAM policy statements)"
}

variable "tenancy_ocid" {
  type        = string
  description = "Tenancy OCID (required for tenancy-level IAM policies like Object Storage CMEK)"
}

variable "project_name" {
  type        = string
  description = "Project name for naming convention"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "project_name must be lowercase alphanumeric with hyphens."
  }
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "vault_type" {
  type        = string
  description = "Vault type: DEFAULT (dev/test) or VIRTUAL_PRIVATE (production). IMMUTABLE."
  default     = "VIRTUAL_PRIVATE"

  validation {
    condition     = contains(["DEFAULT", "VIRTUAL_PRIVATE"], var.vault_type)
    error_message = "vault_type must be DEFAULT or VIRTUAL_PRIVATE."
  }
}

variable "key_protection_mode" {
  type        = string
  description = "Key protection mode: HSM (production) or SOFTWARE (dev/test). IMMUTABLE."
  default     = "HSM"

  validation {
    condition     = contains(["HSM", "SOFTWARE", "EXTERNAL"], var.key_protection_mode)
    error_message = "key_protection_mode must be HSM, SOFTWARE, or EXTERNAL."
  }
}

variable "key_rotation_interval_days" {
  type        = number
  description = "Auto-rotation interval in days (60-365)"
  default     = 90

  validation {
    condition     = var.key_rotation_interval_days >= 60 && var.key_rotation_interval_days <= 365
    error_message = "key_rotation_interval_days must be between 60 and 365."
  }
}

variable "secrets" {
  type = map(object({
    description          = string
    initial_value        = string
    sensitivity          = optional(string, "high")
    expiry_interval      = optional(string, "P35D")
    rotation_interval    = optional(string)
    rotation_function_id = optional(string)
  }))
  description = "Map of secrets to create. Key = secret name suffix."
  default     = {}
  sensitive   = true
}

variable "functions_dynamic_group_name" {
  type        = string
  description = "Name of dynamic group for Functions vault access"
  default     = ""
}

variable "vault_admin_group_name" {
  type        = string
  description = "Name of the admin group for vault management"
  default     = ""
}

variable "terraform_group_name" {
  type        = string
  description = "Name of the Terraform service account group"
  default     = ""
}

variable "region" {
  type        = string
  description = "OCI region identifier (e.g., sa-saopaulo-1) — required for Object Storage CMEK policies"
  default     = ""
}

variable "tags" {
  type        = map(string)
  description = "Freeform tags for all resources"
  default     = {}
}

# ─── main.tf ─────────────────────────────────────────────────────────────────

# --- Vault ---

resource "oci_kms_vault" "main" {
  compartment_id = var.compartment_ocid
  display_name   = "vault-${var.project_name}-${var.environment}"
  vault_type     = var.vault_type

  freeform_tags = merge(var.tags, {
    "Environment" = var.environment
    "ManagedBy"   = "terraform"
    "Sensitivity" = "critical"
  })

  lifecycle {
    prevent_destroy = true
  }
}

# --- Encryption Keys ---

resource "oci_kms_key" "secrets" {
  compartment_id      = var.compartment_ocid
  display_name        = "key-secrets-${var.project_name}-${var.environment}"
  management_endpoint = oci_kms_vault.main.management_endpoint
  protection_mode     = var.key_protection_mode

  key_shape {
    algorithm = "AES"
    length    = 32
  }

  is_auto_rotation_enabled = true
  auto_key_rotation_details {
    rotation_interval_in_days = var.key_rotation_interval_days
  }

  freeform_tags = merge(var.tags, {
    "Purpose"  = "secrets-encryption"
    "Rotation" = "${var.key_rotation_interval_days}-days"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "oci_kms_key" "storage" {
  compartment_id      = var.compartment_ocid
  display_name        = "key-storage-${var.project_name}-${var.environment}"
  management_endpoint = oci_kms_vault.main.management_endpoint
  protection_mode     = var.key_protection_mode

  key_shape {
    algorithm = "AES"
    length    = 32
  }

  is_auto_rotation_enabled = true
  auto_key_rotation_details {
    rotation_interval_in_days = var.key_rotation_interval_days
  }

  freeform_tags = merge(var.tags, {
    "Purpose"  = "storage-encryption"
    "Rotation" = "${var.key_rotation_interval_days}-days"
  })

  lifecycle {
    prevent_destroy = true
  }
}

# --- Secrets ---

resource "oci_vault_secret" "secrets" {
  for_each = var.secrets

  compartment_id = var.compartment_ocid
  key_id         = oci_kms_key.secrets.id
  secret_name    = "${each.key}-${var.project_name}-${var.environment}"
  vault_id       = oci_kms_vault.main.id
  description    = each.value.description

  secret_content {
    content_type = "BASE64"
    content      = base64encode(each.value.initial_value)
    stage        = "CURRENT"
  }

  # Rotation config — only if rotation_function_id is provided
  dynamic "rotation_config" {
    for_each = each.value.rotation_function_id != null ? [1] : []
    content {
      target_system_details {
        target_system_type = "FUNCTION"
        function_id        = each.value.rotation_function_id
      }
      is_scheduled_rotation_enabled = true
      rotation_interval             = each.value.rotation_interval != null ? each.value.rotation_interval : "P30D"
    }
  }

  # Expiry rule — always applied
  secret_rules {
    rule_type                                     = "SECRET_EXPIRY_RULE"
    secret_version_expiry_interval                = each.value.expiry_interval
    is_secret_content_retrieval_blocked_on_expiry = each.value.sensitivity == "high" ? true : false
  }

  # Reuse rule — prevent reuse of old versions
  secret_rules {
    rule_type                              = "SECRET_REUSE_RULE"
    is_enforced_on_deleted_secret_versions = true
  }

  freeform_tags = merge(var.tags, {
    "Sensitivity" = each.value.sensitivity
    "ManagedBy"   = "terraform"
  })

  lifecycle {
    ignore_changes = [secret_content]
  }
}

# ─── iam.tf ──────────────────────────────────────────────────────────────────

# Functions — crypto operations and secret retrieval only
resource "oci_identity_policy" "functions_vault" {
  count = var.functions_dynamic_group_name != "" ? 1 : 0

  compartment_id = var.compartment_ocid
  name           = "policy-functions-vault-${var.project_name}-${var.environment}"
  description    = "Least-privilege vault access for functions"

  statements = [
    "Allow dynamic-group ${var.functions_dynamic_group_name} to use keys in compartment ${var.compartment_name}",
    "Allow dynamic-group ${var.functions_dynamic_group_name} to read secret-bundles in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}

# Vault Admin group — full management
resource "oci_identity_policy" "vault_admins" {
  count = var.vault_admin_group_name != "" ? 1 : 0

  compartment_id = var.compartment_ocid
  name           = "policy-vault-admins-${var.project_name}-${var.environment}"
  description    = "Vault administration — key and secret lifecycle"

  statements = [
    "Allow group ${var.vault_admin_group_name} to manage vaults in compartment ${var.compartment_name}",
    "Allow group ${var.vault_admin_group_name} to manage keys in compartment ${var.compartment_name}",
    "Allow group ${var.vault_admin_group_name} to manage secrets in compartment ${var.compartment_name}",
    "Allow group ${var.vault_admin_group_name} to read secret-bundles in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}

# Terraform service account — manage for IaC lifecycle
resource "oci_identity_policy" "terraform_vault" {
  count = var.terraform_group_name != "" ? 1 : 0

  compartment_id = var.compartment_ocid
  name           = "policy-terraform-vault-${var.project_name}-${var.environment}"
  description    = "Terraform management of vault resources"

  statements = [
    "Allow group ${var.terraform_group_name} to manage vaults in compartment ${var.compartment_name}",
    "Allow group ${var.terraform_group_name} to manage keys in compartment ${var.compartment_name}",
    "Allow group ${var.terraform_group_name} to manage secrets in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}

# Object Storage CMEK service policy (tenancy-level)
resource "oci_identity_policy" "objectstorage_cmek" {
  count = var.region != "" ? 1 : 0

  compartment_id = var.tenancy_ocid
  name           = "policy-objectstorage-cmek-${var.project_name}-${var.environment}"
  description    = "Allow Object Storage service to use vault keys for CMEK"

  statements = [
    "Allow service objectstorage-${var.region} to use keys in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}

# ─── outputs.tf ──────────────────────────────────────────────────────────────

# Vault
output "vault_id" {
  value       = oci_kms_vault.main.id
  description = "OCID of the Vault"
}

output "vault_crypto_endpoint" {
  value       = oci_kms_vault.main.crypto_endpoint
  description = "Endpoint for crypto operations (Encrypt/Decrypt/Sign/Verify)"
}

output "vault_management_endpoint" {
  value       = oci_kms_vault.main.management_endpoint
  description = "Endpoint for key management operations"
}

# Keys
output "key_secrets_id" {
  value       = oci_kms_key.secrets.id
  description = "OCID of the secrets encryption key"
}

output "key_storage_id" {
  value       = oci_kms_key.storage.id
  description = "OCID of the storage encryption key (CMEK)"
}

# Secrets — OCID only, NEVER values
output "secret_ids" {
  value       = { for k, v in oci_vault_secret.secrets : k => v.id }
  description = "Map of secret name → OCID (retrieve values via OCI SDK at runtime)"
  sensitive   = true
}
