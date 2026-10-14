# Worked Examples — provisioning-oci-vault

Source: `workspace/poc-oci-serverless/infra/modules/vault/`

---

## Worked example (from the reference PoC)

### Vault + KMS Key + Object Storage bucket — `infra/modules/vault/main.tf`

The PoC co-locates the KMS vault, a master AES-256 encryption key, and an optional Object Storage
bucket in a single module. The bucket is conditional (`var.create_bucket`) so the vault module can
be used without creating storage.

```hcl
# from infra/modules/vault/main.tf

resource "oci_kms_vault" "this" {
  compartment_id = var.compartment_ocid
  display_name   = "vault-${var.project_name}-${var.environment}"
  vault_type     = "DEFAULT"

  freeform_tags = var.tags
}

resource "oci_kms_key" "this" {
  compartment_id      = var.compartment_ocid
  display_name        = "key-${var.project_name}-${var.environment}"
  management_endpoint = oci_kms_vault.this.management_endpoint
  protection_mode     = var.key_protection_mode   # SOFTWARE or HSM

  key_shape {
    algorithm = "AES"
    length    = 32   # 256-bit AES
  }

  freeform_tags = var.tags
}

# Optional bucket (used by the API Facade /store route)
data "oci_objectstorage_namespace" "this" {
  compartment_id = var.compartment_ocid
}

resource "oci_objectstorage_bucket" "this" {
  count = var.create_bucket ? 1 : 0

  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.this.namespace
  name           = "bucket-${var.bucket_name}-${var.environment}"
  access_type    = "NoPublicAccess"
  storage_tier   = "Standard"
  versioning     = "Enabled"
  auto_tiering   = "InfrequentAccess"

  freeform_tags = var.tags
}
```

**Key patterns from this example:**
- `management_endpoint` is read from the vault resource — never supply a hardcoded endpoint URL.
- `protection_mode = "SOFTWARE"` is used for PoC to avoid HSM costs; use `"HSM"` in production.
- Bucket `versioning = "Enabled"` + `auto_tiering = "InfrequentAccess"` matches cost-optimization best practice.
- Namespace is fetched via data source — never hardcoded.
- `count = var.create_bucket ? 1 : 0` allows vault-only deployments without the bucket dependency.
