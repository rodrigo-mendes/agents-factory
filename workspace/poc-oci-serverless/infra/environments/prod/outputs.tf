# ==============================================================================
# Outputs: prod environment
# ==============================================================================

output "api_base_url" {
  value       = module.api_gateway.deployment_endpoint
  description = "URL base da API"
}

output "health_check_url" {
  value       = "${module.api_gateway.deployment_endpoint}/health"
  description = "URL do health check"
}

output "api_gateway_hostname" {
  value       = module.api_gateway.gateway_hostname
  description = "Hostname do API Gateway"
}

output "api_handler_function_id" {
  value       = module.app_api_handler.function_id
  description = "OCID da Function api-handler"
}

output "api_facade_function_id" {
  value       = module.app_api_facade.function_id
  description = "OCID da Function func-api-facade"
}

output "rest_proxy_function_id" {
  value       = module.app_rest_proxy.function_id
  description = "OCID da Function func-rr-rest-proxy"
}
