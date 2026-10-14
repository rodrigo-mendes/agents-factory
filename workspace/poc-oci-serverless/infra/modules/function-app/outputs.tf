output "application_id" {
  value       = oci_functions_application.this.id
  description = "OCID da Functions Application"
}

output "function_id" {
  value       = oci_functions_function.this.id
  description = "OCID da Function"
}

output "invoke_endpoint" {
  value       = oci_functions_function.this.invoke_endpoint
  description = "Invoke endpoint da Function"
  sensitive   = true
}
