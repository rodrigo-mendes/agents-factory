### 🚫 Never Do

## Contents
1. Secret Content in Terraform State Without Protection
2. `manage keys`/`manage vaults` for Workload Dynamic Groups
3. Using `data.oci_secrets_secretbundle` in Terraform (Secret Value in State)
4. Default Vault for Production Workloads
5. Secrets Without Expiry Rules

---

**Anti-Pattern**: Secret Content in Terraform State Without Protection

```hcl
# 🚫 WRONG: Hardcoded secret + no lifecycle protection — value persists in state plaintext
# Terraform state file contains the base64 value — any state access exposes the secret
# Terraform OCI Provider v6.x+
resource "oci_vault_secret" "db_password" {
  compartment_id = var.compartment_ocid
  key_id         = oci_kms_key.secrets.id
  secret_name    = "db-password"
  vault_id       = oci_kms_vault.main.id

  secret_content {
    content_type = "BASE64"
    content      = base64encode("SuperSecretPassword123!")  # Hardcoded + in state
  }
}

# ✅ CORRECT: Use sensitive variable, ignore after creation
# Terraform OCI Provider v6.x+
variable "initial_db_password" {
  type      = string
  sensitive = true
}

resource "oci_vault_secret" "db_password" {
  compartment_id = var.compartment_ocid
  key_id         = oci_kms_key.secrets.id
  secret_name    = "db-password-${var.project_name}-${var.environment}"
  vault_id       = oci_kms_vault.main.id

  secret_content {
    content_type = "BASE64"
    content      = base64encode(var.initial_db_password)
    stage        = "CURRENT"
  }

  lifecycle {
    ignore_changes = [secret_content]  # Content managed by rotation
  }
}
```

**Why it is prohibited**: Terraform state stores ALL resource attributes as JSON plaintext including `secret_content.content`. Any state file access = full credential exposure.
**Actual impact**: **CRITICAL** — Full credential exposure via state file access.
**Source**: https://developer.hashicorp.com/terraform/language/state/sensitive-data

---

**Anti-Pattern**: `manage keys`/`manage vaults` for Workload Dynamic Groups

```hcl
# 🚫 WRONG: Functions with manage keys = can DELETE keys (permanent data loss)
# Terraform OCI Provider v6.x+
resource "oci_identity_policy" "functions_vault" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-vault"
  statements = [
    "Allow dynamic-group dg-functions to manage keys in compartment ${var.compartment_name}",
    "Allow dynamic-group dg-functions to manage vaults in compartment ${var.compartment_name}",
    "Allow dynamic-group dg-functions to manage secrets in compartment ${var.compartment_name}",
  ]
}

# ✅ CORRECT: Minimal permissions — use keys + read secret-bundles
# Terraform OCI Provider v6.x+
resource "oci_identity_policy" "functions_vault" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-vault-${var.project_name}-${var.environment}"
  statements = [
    "Allow dynamic-group ${var.functions_dg_name} to use keys in compartment ${var.compartment_name}",
    "Allow dynamic-group ${var.functions_dg_name} to read secret-bundles in compartment ${var.compartment_name}",
  ]
}
```

**Why it is prohibited**: `manage keys` includes DisableKey and ScheduleKeyDeletion. Compromised Function can destroy ALL encryption infrastructure permanently.
**Actual impact**: **CRITICAL** — Permanent data loss, complete encryption infrastructure compromise.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/keypolicyreference.htm

---

**Anti-Pattern**: Using `data.oci_secrets_secretbundle` in Terraform (Secret Value in State)

```hcl
# 🚫 WRONG: Retrieves secret VALUE into Terraform state — value stored in state file
# Terraform OCI Provider v6.x+
data "oci_secrets_secretbundle" "db_password" {
  secret_id = oci_vault_secret.db_password.id
  stage     = "CURRENT"
}

output "db_password_value" {
  value = base64decode(data.oci_secrets_secretbundle.db_password.secret_bundle_content[0].content)
}

# ✅ CORRECT: Only output the secret OCID — retrieve value at RUNTIME via SDK
# Terraform OCI Provider v6.x+
output "db_password_secret_id" {
  value       = oci_vault_secret.db_password.id
  description = "OCID — retrieve value via OCI SDK at runtime"
  sensitive   = true
}
# Application (Function) retrieves the secret value at runtime via OCI SDK.
# 📎 See skill `developing-oci-functions-java` for Java secret retrieval patterns.
```

**Why it is prohibited**: Data source retrieves actual secret VALUE and stores it in state. State file becomes single point of compromise.
**Actual impact**: **HIGH** — Secret values exposed in state file, plan output, and logs.
**Source**: https://developer.hashicorp.com/terraform/language/state/sensitive-data

---

**Anti-Pattern**: Default Vault for Production Workloads

```hcl
# 🚫 WRONG: Default vault for production — insufficient isolation, no DR
# Terraform OCI Provider v6.x+
resource "oci_kms_vault" "production" {
  compartment_id = var.compartment_ocid
  display_name   = "vault-production"
  vault_type     = "DEFAULT"  # 10 keys max, shared HSM, no replication
}

# ✅ CORRECT: Virtual Private Vault for production
# Terraform OCI Provider v6.x+
resource "oci_kms_vault" "production" {
  compartment_id = var.compartment_ocid
  display_name   = "vault-${var.project_name}-prod"
  vault_type     = "VIRTUAL_PRIVATE"
  freeform_tags  = var.tags
  lifecycle { prevent_destroy = true }
}
```

**Why it is prohibited**: Default Vault: 10 keys max, shared HSM, no cross-region replication, 200 ops/sec. Cannot upgrade to VIRTUAL_PRIVATE (immutable).
**Actual impact**: **HIGH** — Insufficient isolation, capacity limits, no DR capability.
**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

**Anti-Pattern**: Vault/Key Resources Without `prevent_destroy`

```hcl
# 🚫 WRONG: No lifecycle protection — terraform destroy schedules key deletion
# Terraform OCI Provider v6.x+
resource "oci_kms_key" "production" {
  compartment_id      = var.compartment_ocid
  display_name        = "key-prod"
  management_endpoint = oci_kms_vault.main.management_endpoint
  protection_mode     = "HSM"
  key_shape { algorithm = "AES"; length = 32 }
  # NO lifecycle block — accidental destroy = permanent data loss
}

# ✅ CORRECT: prevent_destroy blocks accidental terraform destroy
# Terraform OCI Provider v6.x+
resource "oci_kms_key" "production" {
  compartment_id      = var.compartment_ocid
  display_name        = "key-prod"
  management_endpoint = oci_kms_vault.main.management_endpoint
  protection_mode     = "HSM"
  key_shape { algorithm = "AES"; length = 32 }

  lifecycle {
    prevent_destroy = true
  }
}
```

**Why it is prohibited**: Key deletion and Vault deletion are PERMANENT and IRREVERSIBLE. OCI enforces 7–30 day pending period, but once elapsed, data encrypted with that key is lost forever.
**Actual impact**: **CRITICAL** — Permanent and irreversible data loss.
**Source**: https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle

---

**Anti-Pattern**: Secrets Without Expiry Rules

```hcl
# 🚫 WRONG: No expiry, no rotation — credential lives forever
# Terraform OCI Provider v6.x+
resource "oci_vault_secret" "api_key" {
  compartment_id = var.compartment_ocid
  key_id         = oci_kms_key.secrets.id
  secret_name    = "external-api-key"
  vault_id       = oci_kms_vault.main.id
  secret_content {
    content_type = "BASE64"
    content      = base64encode(var.api_key)
  }
  # No secret_rules — credential lives forever
}

# ✅ CORRECT: Always add expiry rules — Terraform OCI Provider v6.x+
resource "oci_vault_secret" "api_key" {
  compartment_id = var.compartment_ocid
  key_id         = oci_kms_key.secrets.id
  secret_name    = "external-api-key-${var.project_name}-${var.environment}"
  vault_id       = oci_kms_vault.main.id
  secret_content {
    content_type = "BASE64"
    content      = base64encode(var.api_key)
  }
  secret_rules {
    rule_type                                     = "SECRET_EXPIRY_RULE"
    secret_version_expiry_interval                = "P90D"
    is_secret_content_retrieval_blocked_on_expiry = true
  }
  lifecycle { ignore_changes = [secret_content] }
}
```

**Why it is prohibited**: Secrets without expiration become static long-lived credentials. NIST 800-63B and PCI-DSS mandate rotation.
**Actual impact**: **HIGH** — Long-lived static credentials, compliance violation.
**Detection**:
```bash
# Find secrets without rotation config
oci vault secret list --compartment-id <comp-ocid> | \
  jq '.data[] | select(.["rotation-config"] == null) | .["secret-name"]'
```
**Source**: https://docs.oracle.com/en-us/iaas/Content/Vault/Tasks/managingsecrets.htm
