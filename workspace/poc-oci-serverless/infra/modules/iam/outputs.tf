output "dynamic_group_functions_id" {
  value       = oci_identity_dynamic_group.functions.id
  description = "OCID do Dynamic Group de Functions"
}

output "dynamic_group_functions_name" {
  value       = oci_identity_dynamic_group.functions.name
  description = "Nome do Dynamic Group de Functions"
}

output "dynamic_group_apigw_id" {
  value       = oci_identity_dynamic_group.api_gateway.id
  description = "OCID do Dynamic Group do API Gateway"
}

output "dynamic_group_apigw_name" {
  value       = oci_identity_dynamic_group.api_gateway.name
  description = "Nome do Dynamic Group do API Gateway"
}

output "policy_streaming_id" {
  value       = oci_identity_policy.streaming.id
  description = "OCID da policy de Streaming do PRODUCER (stream-push). Statements do SCH foram relocados p/ modules/iam-sch (least-privilege, quebra de ciclo)."
}
