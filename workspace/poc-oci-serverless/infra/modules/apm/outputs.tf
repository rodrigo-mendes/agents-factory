output "apm_domain_id" {
  description = "OCID do APM Domain"
  value       = oci_apm_apm_domain.this.id
}

output "data_upload_endpoint" {
  description = "Endpoint de upload de dados APM (APM_DOMAIN_URL)"
  value       = oci_apm_apm_domain.this.data_upload_endpoint
}

output "private_data_key" {
  description = "Private Data Key para instrumentação (APM_DATA_KEY)"
  value       = data.oci_apm_data_keys.private.data_keys[0].value
  sensitive   = true
}
