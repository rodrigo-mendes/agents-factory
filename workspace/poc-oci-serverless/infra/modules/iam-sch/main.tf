# ==============================================================================
# Module: IAM-SCH — Least-privilege policy do Service Connector Hub (pub/sub)
# ==============================================================================
# Skill: provisioning-oci-iam + provisioning-oci-connector-hub (IAM verb reference).
#
# POR QUE ESTE MÓDULO É SEPARADO DO módulo base `iam` (quebra de ciclo):
#   As statements do serviceconnector precisam escopar target.stream.id e
#   target.function.id — ou seja, referenciar module.streaming.stream_id e
#   module.app_evt_consumer_*.function_id. As Functions consumer já declaram
#   `depends_on = [module.iam]`. Se o módulo base `iam` referenciasse os
#   function_id, criaria o ciclo iam → app → iam e o `terraform validate`
#   falharia. Solução: este módulo dedicado depende (via depends_on no caller)
#   de streaming + apps e NÃO é referenciado por elas → DAG sem ciclo.
#   O statement do producer (stream-push, que referencia só a Dynamic Group) fica
#   no módulo base `iam` — não tem ciclo.
#
# SEMÂNTICA PRESERVADA (apenas ESCOPO adicionado, nada removido):
#   - request.principal.type='serviceconnector' em TODAS as statements (inalterado).
#   - fn-function MANTIDO além de fn-invocation — o target Functions do SCH exige
#     os DOIS verbos; remover fn-function = ErrorsAtTarget + descarte silencioso
#     (provisioning-oci-connector-hub, Anti-Pattern 4 / never-do). Só foi ADICIONADO
#     o escopo target.function.id (least-privilege).
#   - STREAM_READ/STREAM_CONSUME agora restritos a target.stream.id = <stream>.
#
# ⚠️ compartment_name é referenciado NAS statements (Allow ... in compartment
#    <name>). Valor errado reescreve as statements p/ um compartment inexistente
#    → o SCH perde permissão (outage). Conferir contra o display name real.
# ==============================================================================

locals {
  common_tags = merge(var.tags, {
    "Component" = "iam-sch"
  })
}

resource "oci_identity_policy" "streaming_sch" {
  compartment_id = var.compartment_ocid
  name           = "policy-streaming-sch-${var.project_name}-${var.environment}"
  description    = "Service Connector Hub lê o stream (STREAM_READ/STREAM_CONSUME em target.stream.id) e invoca as Functions consumer (fn-function + fn-invocation em target.function.id) — least-privilege"

  statements = [
    # Service Connector Hub lê APENAS o stream de eventos (source streaming) —
    # escopo target.stream.id restringe o STREAM_READ/STREAM_CONSUME a este stream.
    "Allow any-user to {STREAM_READ, STREAM_CONSUME} in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector', target.stream.id = '${var.stream_id}'}",
    # SCH resolve a Function target — fn-function é OBRIGATÓRIO (além de fn-invocation);
    # escopo target.function.id restringe às 2 Functions consumer (notify + audit).
    "Allow any-user to use fn-function in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector', target.function.id in ('${var.notify_function_id}', '${var.audit_function_id}')}",
    # SCH invoca a Function target — mesmo escopo target.function.id.
    "Allow any-user to use fn-invocation in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector', target.function.id in ('${var.notify_function_id}', '${var.audit_function_id}')}",
  ]

  freeform_tags = local.common_tags
}
