### ✅ Always Do

## Contents
1. Provider Version Constraint
2. Virtual Private Vault for Production with prevent_destroy
3. Purpose-Specific Keys with HSM Protection and Auto-Rotation
4. Secrets with Rotation, Expiry Rules, and State Protection
5. Least-Privilege IAM Policies for Vault Access
6. Variable Validation for Immutable Properties

---

**Provider Version Constraint**: Vault is security-critical — provider version must be pinned to prevent force-replacement of immutable resources during uncontrolled upgrades.

```hcl
# ✅ CORRECT: Constrained provider version — Terraform OCI Provider v6.x+
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

**Why it is mandatory**: Vaults and keys are immutable in many properties. Uncontrolled provider upgrades can cause force-replacement of security-critical resources.
**Failure if omitted**: Provider upgrade triggers destroy/recreate of vault or key — permanent data loss.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs

---

**Virtual Private Vault for Production with prevent_destroy**: Default Vault is multi-tenant (shared HSM), limited to 10 keys, 200 ops/sec, and does NOT support cross-region replication. Production workloads MUST use Virtual Private Vault.

```hcl
# ✅ CORRECT: Virtual Private Vault with lifecycle protection — Terraform OCI Provider v6.x+
resource "oci_kms_vault" "main" {
  compartment_id = var.compartment_ocid
  display_name   = "vault-${var.project_name}-${var.environment}"
  vault_type     = "VIRTUAL_PRIVATE"

  freeform_tags = merge(var.tags, {
    "Environment" = var.environment
    "ManagedBy"   = "terraform"
    "Sensitivity" = "critical"
  })

  # CRITICAL: Vault deletion is IRREVERSIBLE — blocks terraform destroy
  lifecycle {
    prevent_destroy = true
  }
}

# Expose endpoints for downstream modules
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
```

**Why it is mandatory**: Default Vault: 10 key limit, shared HSM, 200 ops/sec rate limit, no DR. Virtual Private: 1000 keys, dedicated HSM, 1000+ ops/sec, cross-region replication. `vault_type` is IMMUTABLE — cannot upgrade from DEFAULT to VIRTUAL_PRIVATE.
**Failure if omitted**: Insufficient isolation, capacity limits, no DR capability in production.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/kms_vault | https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

**Purpose-Specific Keys with HSM Protection and Auto-Rotation**: Separate keys by purpose for independent rotation schedules and minimal blast radius. HSM protection mode guarantees FIPS 140-2 Level 3 crypto operations in hardware.

```hcl
# ✅ CORRECT: Secrets encryption key — AES-256, HSM, 90-day rotation
# Terraform OCI Provider v6.x+
resource "oci_kms_key" "secrets_encryption" {
  compartment_id      = var.compartment_ocid
  display_name        = "key-secrets-${var.project_name}-${var.environment}"
  management_endpoint = oci_kms_vault.main.management_endpoint
  protection_mode     = "HSM"

  key_shape {
    algorithm = "AES"
    length    = 32  # 256-bit
  }

  is_auto_rotation_enabled = true
  auto_key_rotation_details {
    rotation_interval_in_days = 90
  }

  freeform_tags = merge(var.tags, {
    "Purpose"  = "secrets-encryption"
    "Rotation" = "90-days"
  })

  # CRITICAL: Key deletion = PERMANENT DATA LOSS
  lifecycle {
    prevent_destroy = true
  }
}

# ✅ CORRECT: Storage encryption key — separate rotation from secrets
resource "oci_kms_key" "storage_encryption" {
  compartment_id      = var.compartment_ocid
  display_name        = "key-storage-${var.project_name}-${var.environment}"
  management_endpoint = oci_kms_vault.main.management_endpoint
  protection_mode     = "HSM"

  key_shape {
    algorithm = "AES"
    length    = 32
  }

  is_auto_rotation_enabled = true
  auto_key_rotation_details {
    rotation_interval_in_days = 90
  }

  freeform_tags = merge(var.tags, { "Purpose" = "storage-encryption" })
  lifecycle { prevent_destroy = true }
}

# ✅ CORRECT: JWT signing key — ECDSA P-256 with longer rotation
resource "oci_kms_key" "signing" {
  compartment_id      = var.compartment_ocid
  display_name        = "key-signing-${var.project_name}-${var.environment}"
  management_endpoint = oci_kms_vault.main.management_endpoint
  protection_mode     = "HSM"

  key_shape {
    algorithm = "ECDSA"
    length    = 32  # P-256
  }

  is_auto_rotation_enabled = true
  auto_key_rotation_details {
    rotation_interval_in_days = 180
  }

  freeform_tags = merge(var.tags, { "Purpose" = "jwt-signing" })
  lifecycle { prevent_destroy = true }
}
```

**Why it is mandatory**: Single key for all purposes amplifies blast radius — compromise affects ALL services. Separate keys enable independent rotation (60 days for secrets, 180 for signing) and clear audit attribution. `protection_mode` and `key_shape` are IMMUTABLE.
**Failure if omitted**: Key compromise affects ALL services. Cannot tune rotation per sensitivity. Audit attribution impossible.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/kms_key | https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Tasks/managingkeys.htm

---

**Secrets with Rotation, Expiry Rules, and State Protection**: Secrets without rotation become long-lived static credentials. Secret content MUST be ignored in Terraform state after initial creation.

```hcl
# ✅ CORRECT: Secret with auto-rotation via Function — Terraform OCI Provider v6.x+
variable "initial_db_password" {
  type        = string
  description = "Initial DB password — will be rotated after creation"
  sensitive   = true  # Masks in plan output and logs
}

resource "oci_vault_secret" "db_password" {
  compartment_id = var.compartment_ocid
  key_id         = oci_kms_key.secrets_encryption.id
  secret_name    = "db-password-${var.project_name}-${var.environment}"
  vault_id       = oci_kms_vault.main.id
  description    = "Database password — managed by rotation function"

  secret_content {
    content_type = "BASE64"
    content      = base64encode(var.initial_db_password)
    stage        = "CURRENT"
  }

  rotation_config {
    target_system_details {
      target_system_type = "FUNCTION"
      function_id        = var.rotation_function_id
    }
    is_scheduled_rotation_enabled = true
    rotation_interval             = "P30D"  # ISO 8601: 30 days
  }

  secret_rules {
    rule_type                                     = "SECRET_EXPIRY_RULE"
    secret_version_expiry_interval                = "P35D"  # Expire 5 days after rotation
    is_secret_content_retrieval_blocked_on_expiry = true
  }

  secret_rules {
    rule_type                              = "SECRET_REUSE_RULE"
    is_enforced_on_deleted_secret_versions = true
  }

  freeform_tags = merge(var.tags, {
    "Sensitivity" = "high"
    "Rotation"    = "30-days"
  })

  # CRITICAL: Ignore secret_content after creation — rotation function manages content
  lifecycle {
    ignore_changes = [secret_content]
  }
}

# ✅ CORRECT: Secret without auto-rotation (third-party API keys)
resource "oci_vault_secret" "external_api_key" {
  compartment_id = var.compartment_ocid
  key_id         = oci_kms_key.secrets_encryption.id
  secret_name    = "external-api-key-${var.project_name}-${var.environment}"
  vault_id       = oci_kms_vault.main.id

  secret_content {
    content_type = "BASE64"
    content      = base64encode(var.external_api_key)
    stage        = "CURRENT"
  }

  secret_rules {
    rule_type                                     = "SECRET_EXPIRY_RULE"
    secret_version_expiry_interval                = "P90D"
    is_secret_content_retrieval_blocked_on_expiry = false
  }

  freeform_tags = merge(var.tags, { "Sensitivity" = "high" })

  lifecycle {
    ignore_changes = [secret_content]
  }
}
```

**Why it is mandatory**: NIST 800-63B and PCI-DSS mandate credential rotation. Without `lifecycle { ignore_changes }`, Terraform overwrites rotated values on every apply. `secret_content` is stored in state file as base64 plaintext.
**Failure if omitted**: Extended credential exposure, compliance violation, Terraform reverts rotated secrets.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/vault_secret | https://docs.oracle.com/en-us/iaas/Content/Vault/Tasks/managingsecrets.htm

---

**Least-Privilege IAM Policies for Vault Access**: Workloads MUST receive `use keys` (crypto) and `read secret-bundles` (retrieval) only. `manage` is reserved for human admin groups.

```hcl
# ✅ CORRECT: Functions — crypto operations and secret retrieval only
# Terraform OCI Provider v6.x+
resource "oci_identity_policy" "functions_vault_access" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-vault-${var.project_name}-${var.environment}"
  description    = "Least-privilege vault access for functions"

  statements = [
    # use keys = Encrypt, Decrypt, Sign, Verify, GenerateDataEncryptionKey
    "Allow dynamic-group ${var.functions_dynamic_group_name} to use keys in compartment ${var.compartment_name}",
    # read secret-bundles = GetSecretBundle (retrieve secret values)
    "Allow dynamic-group ${var.functions_dynamic_group_name} to read secret-bundles in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}

# ✅ CORRECT: Vault Admins — full management (human users only)
resource "oci_identity_policy" "vault_admins" {
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

# ✅ CORRECT: Terraform service account — manage for IaC lifecycle
resource "oci_identity_policy" "terraform_vault" {
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
```

**Why it is mandatory**: `manage keys` includes DisableKey and ScheduleKeyDeletion. A compromised Function with `manage keys` can destroy ALL encryption infrastructure permanently.
**Failure if omitted**: Data destruction via key deletion, unauthorized decryption, secret exfiltration.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/keypolicyreference.htm

---

**Variable Validation for Immutable Properties**: Errors in `vault_type`, `protection_mode`, or `algorithm` require destroy/recreate — validate at plan-time to prevent costly mistakes.

```hcl
# ✅ CORRECT: Validate immutable properties before creation — Terraform OCI Provider v6.x+
variable "vault_type" {
  type        = string
  description = "Vault type: DEFAULT (dev/test) or VIRTUAL_PRIVATE (production)"
  default     = "VIRTUAL_PRIVATE"

  validation {
    condition     = contains(["DEFAULT", "VIRTUAL_PRIVATE"], var.vault_type)
    error_message = "vault_type must be DEFAULT or VIRTUAL_PRIVATE."
  }
}

variable "key_protection_mode" {
  type        = string
  description = "Protection mode: HSM (production) or SOFTWARE (dev/test)"
  default     = "HSM"

  validation {
    condition     = contains(["HSM", "SOFTWARE", "EXTERNAL"], var.key_protection_mode)
    error_message = "key_protection_mode must be HSM, SOFTWARE, or EXTERNAL."
  }
}

variable "key_algorithm" {
  type        = string
  description = "Key algorithm: AES (symmetric), RSA (asymmetric), ECDSA (signing)"
  default     = "AES"

  validation {
    condition     = contains(["AES", "RSA", "ECDSA"], var.key_algorithm)
    error_message = "key_algorithm must be AES, RSA, or ECDSA."
  }
}

variable "key_length" {
  type        = number
  description = "Key length in bytes (AES: 16/24/32, RSA: 256/384/512, ECDSA: 32/48/66)"

  validation {
    condition     = contains([16, 24, 32, 48, 66, 256, 384, 512], var.key_length)
    error_message = "key_length invalid. AES: 16/24/32, RSA: 256/384/512, ECDSA: 32/48/66."
  }
}

variable "rotation_interval_days" {
  type        = number
  description = "Auto-rotation interval in days (60-365)"
  default     = 90

  validation {
    condition     = var.rotation_interval_days >= 60 && var.rotation_interval_days <= 365
    error_message = "rotation_interval_days must be between 60 and 365."
  }
}

variable "secret_rotation_interval" {
  type        = string
  description = "Secret rotation interval in ISO 8601 format (P1D to P360D)"
  default     = "P30D"

  validation {
    condition     = can(regex("^P[0-9]+D$", var.secret_rotation_interval))
    error_message = "secret_rotation_interval must be in ISO 8601 format (e.g., P30D, P90D)."
  }
}
```

**Why it is mandatory**: Vault type, protection mode, and key shape are immutable. Wrong value = destroy/recreate = potential data loss.
**Failure if omitted**: Terraform attempts destroy/recreate of vault or key without warning.
**Source**: https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules

---

**State Isolation — Separate State for Vault vs. Application**: Vault resources must live in separate Terraform state to prevent accidental destruction during application redeployment.

```hcl
# ✅ CORRECT: Application reads vault outputs via remote state data source
# Terraform OCI Provider v6.x+ — loose coupling between vault and app lifecycle
data "terraform_remote_state" "vault" {
  backend = "s3"
  config = {
    bucket = "my-org-terraform-state"
    key    = "vault/${var.environment}/terraform.tfstate"
    region = "us-east-1"
  }
}

# Use vault outputs without managing vault lifecycle
resource "oci_functions_application" "main" {
  compartment_id = var.compartment_ocid
  display_name   = "app-${var.project_name}-${var.environment}"
  subnet_ids     = [var.subnet_private_id]

  config = {
    "DB_SECRET_OCID"        = data.terraform_remote_state.vault.outputs.secret_db_password_id
    "VAULT_CRYPTO_ENDPOINT" = data.terraform_remote_state.vault.outputs.vault_crypto_endpoint
  }
}
```

**Why it is mandatory**: `terraform destroy` on application module cascades to vault resources if in same state. Vault destruction = permanent key/secret loss.
**Failure if omitted**: Accidental destruction of vault during application redeployment.
**Source**: https://developer.hashicorp.com/terraform/language/state/sensitive-data
