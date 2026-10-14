# ==============================================================================
# Module: dashboards — Outputs
# ==============================================================================

output "dashboard_ids" {
  description = "Mapa dashboard key -> { display_name, import_id }. O recurso de import não expõe o OCID individual do dashboard criado (write-once, sem read); import_id é o id do recurso Terraform de import."
  value = {
    for k, v in oci_management_dashboard_management_dashboards_import.this : k => {
      display_name = local.dashboards[k].display_name
      import_id    = v.id
    }
  }
}
