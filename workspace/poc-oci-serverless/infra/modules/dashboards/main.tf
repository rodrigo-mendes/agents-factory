# ==============================================================================
# Module: dashboards
# ==============================================================================
# Custom OCI Management Dashboards:
#   01 operations-overview   — golden signals (oci_faas + oci_apigateway MQL) [rest-proxy]
#   02 upstream-dependencies — dependências downstream via APM QL [rest-proxy]
#   03 route-analytics       — métricas customizadas (${metric_namespace} MQL) [rest-proxy]
#   04 transaction-path      — caminho de uma transação pub/sub: APM QL (tracesDataSource,
#                              filtro txnId) + MQL (publish/consume rate, lag, auditoria) [events]
#
# Cada dashboard é provisionado via bulk import (write-once). OCIDs/namespace
# são injetados via templatefile — nunca hardcoded no JSON.
#
# ⚠️ oci_management_dashboard_management_dashboards_import NÃO possui ciclo
# Update/Delete: mudanças no JSON não são detectadas por `terraform plan`.
# Para re-importar com o mesmo nome, override_same_name = true força overwrite.
# ==============================================================================

locals {
  # Vars injetadas em cada templatefile. resourceId/deploymentId/apmDomainId/
  # namespace vêm de referências de módulo — nunca hardcoded.
  template_vars = {
    compartment_ocid  = var.compartment_ocid
    application_id    = var.application_id
    apm_domain_id     = var.apm_domain_id
    api_deployment_id = var.api_deployment_id
    metric_namespace  = var.metric_namespace
    environment       = var.environment

    # Event pub/sub (04-transaction-path.json) — Function OCIDs (resourceId nas MQL
    # oci_faas por função, pois producer/notify/audit estão em 3 Applications
    # distintas) + namespace custom dedicado do pub/sub. Defaults vazios/placeholder
    # nas variables mantêm os 3 dashboards do rest-proxy inalterados.
    producer_function_id    = var.producer_function_id
    notify_function_id      = var.notify_function_id
    audit_function_id       = var.audit_function_id
    events_metric_namespace = var.events_metric_namespace
  }

  # Mapa de dashboards → arquivo template. for_each garante chaves estáveis.
  dashboards = {
    "operations-overview" = {
      file         = "01-operations-overview.json"
      display_name = "REST Proxy — Operations Overview (${var.environment})"
    }
    "upstream-dependencies" = {
      file         = "02-upstream-dependencies.json"
      display_name = "REST Proxy — Upstream Dependencies (${var.environment})"
    }
    "route-analytics" = {
      file         = "03-route-analytics.json"
      display_name = "REST Proxy — Route Analytics (${var.environment})"
    }
    "transaction-path" = {
      file         = "04-transaction-path.json"
      display_name = "Events — Transaction Path (${var.environment})"
    }
  }
}

resource "oci_management_dashboard_management_dashboards_import" "this" {
  for_each = local.dashboards

  import_details = templatefile(
    "${path.module}/dashboards/${each.value.file}",
    local.template_vars
  )

  # Garante que dashboard e saved searches sejam criados no compartment alvo,
  # independente do compartment gravado no JSON exportado.
  override_dashboard_compartment_ocid    = var.compartment_ocid
  override_saved_search_compartment_ocid = var.compartment_ocid
  override_same_name                     = true

  lifecycle {
    # O import não possui leitura de drift; ignora mudanças no payload após criação.
    ignore_changes = [import_details]
  }
}
