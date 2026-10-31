## Integration Patterns

## Contents
1. [Terraform ↔ OCI Functions (Secret Retrieval at Runtime)](#terraform--oci-functions-secret-retrieval-at-runtime)
2. [Terraform ↔ Object Storage (CMEK)](#terraform--object-storage-cmek)
3. [Terraform ↔ OCI Events (Vault Monitoring)](#terraform--oci-events-vault-monitoring)
4. [Terraform ↔ Network (Service Gateway for Private Vault Access)](#terraform--network-service-gateway-for-private-vault-access)
5. [Terraform ↔ Cross-Region Replication (DR)](#terraform--cross-region-replication-dr)

### Terraform ↔ OCI Functions (Secret Retrieval at Runtime)

**Pattern**: Terraform provisions secret and injects OCID into Function config. Function retrieves value at runtime via OCI SDK + Resource Principal.

```hcl
# ✅ CORRECT: Function receives secret OCID as config (NOT value)
# Terraform OCI Provider v6.x+
resource "oci_functions_application" "api" {
  compartment_id = var.compartment_ocid
  display_name   = "app-${var.project_name}-${var.environment}"
  subnet_ids     = [var.subnet_private_id]

  config = {
    "DB_SECRET_OCID"        = oci_vault_secret.db_password.id
    "VAULT_CRYPTO_ENDPOINT" = oci_kms_vault.main.crypto_endpoint
  }
}

resource "oci_identity_policy" "functions_vault" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-vault-${var.project_name}-${var.environment}"
  statements = [
    "Allow dynamic-group ${var.functions_dg_name} to use keys in compartment ${var.compartment_name}",
    "Allow dynamic-group ${var.functions_dg_name} to read secret-bundles in compartment ${var.compartment_name}",
  ]
}
```

**Common Issues**: IAM policy propagation (60s) — use `depends_on`. Cold-start latency (+50-100ms for first secret retrieval).
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm

---

### Terraform ↔ Object Storage (CMEK)

**Pattern**: Buckets encrypted with customer-managed key. Requires service-level IAM policy.

```hcl
# ✅ CORRECT: Bucket with CMK + service policy — Terraform OCI Provider v6.x+
resource "oci_objectstorage_bucket" "sensitive_data" {
  compartment_id = var.compartment_ocid
  name           = "sensitive-data-${var.project_name}-${var.environment}"
  namespace      = var.object_storage_namespace
  kms_key_id     = oci_kms_key.storage_encryption.id
  access_type    = "NoPublicAccess"
}

# REQUIRED: Allow Object Storage service to use the key
resource "oci_identity_policy" "objectstorage_cmek" {
  compartment_id = var.tenancy_ocid
  name           = "policy-objectstorage-cmek-${var.project_name}-${var.environment}"
  statements = [
    "Allow service objectstorage-${var.region} to use keys in compartment ${var.compartment_name}",
  ]
}
```

**Key Constraint**: Key must be in SAME region as bucket. Key must be AES algorithm.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/managingencryption.htm

---

### Terraform ↔ OCI Events (Vault Monitoring)

**Pattern**: Events rules detect critical vault operations and alert via ONS.

```hcl
# ✅ CORRECT: Alert on key deletion and rotation failures — Terraform OCI Provider v6.x+
resource "oci_ons_notification_topic" "security_alerts" {
  compartment_id = var.compartment_ocid
  name           = "security-alerts-${var.project_name}-${var.environment}"
}

resource "oci_events_rule" "key_deletion_alert" {
  compartment_id = var.compartment_ocid
  display_name   = "vault-key-deletion-alert"
  is_enabled     = true

  condition = jsonencode({
    eventType = [
      "com.oraclecloud.kms.schedulekeydeletion",
      "com.oraclecloud.kms.schedulevaultdeletion",
      "com.oraclecloud.kms.disablekey"
    ]
  })

  actions {
    actions {
      action_type = "ONS"
      topic_id    = oci_ons_notification_topic.security_alerts.id
      is_enabled  = true
    }
  }
}

resource "oci_events_rule" "secret_rotation_failure" {
  compartment_id = var.compartment_ocid
  display_name   = "vault-rotation-failure-alert"
  is_enabled     = true

  condition = jsonencode({
    eventType = ["com.oraclecloud.vault.rotatesecret.end"]
    data = { additionalDetails = { rotationStatus = ["FAILED"] } }
  })

  actions {
    actions {
      action_type = "ONS"
      topic_id    = oci_ons_notification_topic.security_alerts.id
      is_enabled  = true
    }
  }
}
```

**Source**: https://docs.oracle.com/en-us/iaas/Content/Events/Concepts/eventsoverview.htm

---

### Terraform ↔ Network (Service Gateway for Private Vault Access)

**Pattern**: Functions in private subnet access Vault via Service Gateway — no internet exposure.

```hcl
# ✅ CORRECT: Service Gateway for Oracle Services including Vault KMS
# Terraform OCI Provider v6.x+
data "oci_core_services" "all_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

resource "oci_core_service_gateway" "main" {
  compartment_id = var.compartment_ocid
  display_name   = "sgw-${var.project_name}-${var.environment}"
  vcn_id         = var.vcn_id

  services {
    service_id = data.oci_core_services.all_services.services[0].id
  }
}

resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_ocid
  display_name   = "rt-private-${var.project_name}-${var.environment}"
  vcn_id         = var.vcn_id

  route_rules {
    destination       = data.oci_core_services.all_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.main.id
  }
}
```

**Critical**: Functions MUST be in subnet with Service Gateway route. Without it, Vault API calls fail from private subnets.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/servicegateway.htm

---

### Terraform ↔ Cross-Region Replication (DR)

**Pattern**: Secrets replicated to DR region. Requires Virtual Private Vault + keys in BOTH regions.

```hcl
# ✅ CORRECT: DR vault + key + replicated secret — Terraform OCI Provider v6.x+
resource "oci_kms_vault" "dr" {
  provider       = oci.dr_region
  compartment_id = var.compartment_ocid
  display_name   = "vault-${var.project_name}-${var.environment}-dr"
  vault_type     = "VIRTUAL_PRIVATE"
  lifecycle { prevent_destroy = true }
}

resource "oci_kms_key" "dr_secrets" {
  provider            = oci.dr_region
  compartment_id      = var.compartment_ocid
  display_name        = "key-secrets-${var.project_name}-${var.environment}-dr"
  management_endpoint = oci_kms_vault.dr.management_endpoint
  protection_mode     = "HSM"
  key_shape { algorithm = "AES"; length = 32 }
  is_auto_rotation_enabled = true
  auto_key_rotation_details { rotation_interval_in_days = 90 }
  lifecycle { prevent_destroy = true }
}

resource "oci_vault_secret" "db_password_replicated" {
  compartment_id = var.compartment_ocid
  key_id         = oci_kms_key.secrets_encryption.id
  secret_name    = "db-password-replicated-${var.project_name}-${var.environment}"
  vault_id       = oci_kms_vault.main.id

  secret_content {
    content_type = "BASE64"
    content      = base64encode(var.initial_db_password)
    stage        = "CURRENT"
  }

  replication_config {
    replication_targets {
      target_region   = var.dr_region
      target_vault_id = oci_kms_vault.dr.id
      target_key_id   = oci_kms_key.dr_secrets.id
    }
    is_write_forward_enabled = false  # Read-only replica
  }

  lifecycle { ignore_changes = [secret_content] }
}
```

**Key Constraints**:
- Requires VIRTUAL_PRIVATE vault in BOTH regions (~$530/month each)
- Keys CANNOT be replicated — create equivalent keys in each region
- Maximum 3 replication targets per secret
- Replication is eventually consistent

**Source**: https://docs.oracle.com/en-us/iaas/Content/Vault/Tasks/managingsecrets.htm
