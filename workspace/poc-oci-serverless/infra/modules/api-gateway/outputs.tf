output "gateway_id" {
  value       = oci_apigateway_gateway.this.id
  description = "OCID do API Gateway"
}

output "gateway_hostname" {
  value       = oci_apigateway_gateway.this.hostname
  description = "Hostname do API Gateway"
}

output "gateway_ip_addresses" {
  value       = oci_apigateway_gateway.this.ip_addresses
  description = "IPs do API Gateway"
}

output "deployment_id" {
  value       = oci_apigateway_deployment.this.id
  description = "OCID do Deployment"
}

output "deployment_endpoint" {
  value       = oci_apigateway_deployment.this.endpoint
  description = "Endpoint completo do deployment (URL base)"
}
