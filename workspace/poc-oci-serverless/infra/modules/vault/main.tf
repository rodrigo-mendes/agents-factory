# ==============================================================================
# Module: Vault
# ==============================================================================
# OCI Vault + Master Encryption Key for secrets management
# ==============================================================================

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
  protection_mode     = var.key_protection_mode

  key_shape {
    algorithm = "AES"
    length    = 32
  }

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Object Storage Bucket (for API Facade /store route)
# ------------------------------------------------------------------------------

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
