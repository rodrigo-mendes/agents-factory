output "connector_ids" {
  description = "Mapa nome-lógico → OCID do Service Connector"
  value       = { for k, c in oci_sch_service_connector.this : k => c.id }
}

output "connector_states" {
  description = "Mapa nome-lógico → lifecycle_state do Service Connector (verificar ACTIVE pós-apply)"
  value       = { for k, c in oci_sch_service_connector.this : k => c.state }
}
