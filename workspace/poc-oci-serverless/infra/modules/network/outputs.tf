output "vcn_id" {
  value       = oci_core_vcn.this.id
  description = "OCID da VCN"
}

output "subnet_public_id" {
  value       = oci_core_subnet.public.id
  description = "OCID da subnet pública (API Gateway)"
}

output "subnet_private_id" {
  value       = oci_core_subnet.private.id
  description = "OCID da subnet privada (Functions)"
}

output "nsg_apigw_id" {
  value       = var.use_nsg ? oci_core_network_security_group.apigw[0].id : null
  description = "OCID do NSG do API Gateway"
}

output "nsg_functions_id" {
  value       = var.use_nsg ? oci_core_network_security_group.functions[0].id : null
  description = "OCID do NSG de Functions"
}
