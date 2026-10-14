# ==============================================================================
# Module: Vault — Outputs
# ==============================================================================

output "vault_id" {
  description = "OCID do Vault"
  value       = oci_kms_vault.this.id
}

output "vault_crypto_endpoint" {
  description = "Endpoint para operações de criptografia"
  value       = oci_kms_vault.this.crypto_endpoint
}

output "vault_management_endpoint" {
  description = "Endpoint para gerenciamento de chaves e secrets"
  value       = oci_kms_vault.this.management_endpoint
}

output "key_id" {
  description = "OCID da Master Encryption Key"
  value       = oci_kms_key.this.id
}

output "bucket_name" {
  description = "Nome do bucket Object Storage"
  value       = var.create_bucket ? oci_objectstorage_bucket.this[0].name : null
}

output "namespace" {
  description = "Object Storage namespace"
  value       = data.oci_objectstorage_namespace.this.namespace
}
