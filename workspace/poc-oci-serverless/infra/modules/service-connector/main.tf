# ==============================================================================
# Module: Service Connector — OCI Service Connector Hub (pub/sub fan-out)
# ==============================================================================
# Skill: provisioning-oci-connector-hub
# Cria um oci_sch_service_connector por entry em var.connectors, todos com a MESMA
# source streaming (var.stream_id). Cada connector mantém seu próprio cursor →
# fan-out real (N consumers recebem a mesma mensagem). Target = functions.
#
# ✅ Always Do (skill): IAM antes da ativação (var.iam_dependencies → depends_on),
#    tunar batch_size_in_kbs/batch_time_in_sec, tags em todo connector,
#    validação de OCIDs/enums no plan.
# 🚫 Never Do (skill): connector sem IAM (FAILED + descarte silencioso de dados),
#    batch default sem tuning (cold-start storm vs latência).
# ==============================================================================

locals {
  common_tags = merge(var.tags, {
    "Component" = "service-connector"
  })
}

resource "oci_sch_service_connector" "this" {
  for_each = var.connectors

  compartment_id = var.compartment_ocid
  display_name   = each.value.display_name
  state          = var.connector_state

  # Source: streaming — mesmo stream_id em todos os connectors; cursor por connector.
  source {
    kind      = "streaming"
    stream_id = var.stream_id

    cursor {
      kind = var.cursor_kind
    }
  }

  # Target: functions — invoca o consumer correspondente com batch tuning.
  target {
    kind              = "functions"
    function_id       = each.value.function_id
    batch_size_in_kbs = coalesce(each.value.batch_size_in_kbs, var.default_batch_size_in_kbs)
    batch_time_in_sec = coalesce(each.value.batch_time_in_sec, var.default_batch_time_in_sec)
  }

  freeform_tags = local.common_tags

  # IAM deve existir ANTES da ativação — sem a policy o connector fica FAILED e
  # descarta dados em silêncio (skill Pattern 4). A ordem é injetada pelo caller.
  depends_on = [var.iam_dependencies]
}
