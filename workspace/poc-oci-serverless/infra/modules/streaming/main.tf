# ==============================================================================
# Module: Streaming — OCI Streaming (Kafka-compatible backbone)
# ==============================================================================
# Skill: provisioning-oci-streaming
# Provisions a PUBLIC Stream Pool (endpoint público OCI regional) e um Stream
# (topic) para o padrão event-driven pub/sub. Um único Stream é lido por N
# Service Connectors (cada um com seu próprio cursor) para fan-out real.
#
# ⚠️ TRADE-OFF ACEITO PELO USUÁRIO: pool PÚBLICO (sem isolamento de rede, seguro
#    apenas por IAM/auth) foi escolhido deliberadamente porque o Service Connector
#    Hub gerenciado pela Oracle roda FORA do nosso VCN e não consegue ler um pool
#    com private endpoint (10.0.1.131) — causava ErrorsAtSource=1.0 em cada poll.
#    Ver docs/handoff/event-pubsub/diagnosis-report-sch-source.md.
#
# ✅ Always Do (skill): CMEK opcional, auto_create_topics=false, stream dentro do
#    pool (nunca compartment_id direto), tags para custo.
# 🚫 Never Do (skill): compartment_id no stream, alterar partitions/retention
#    (imutáveis → destroy/recreate com perda de dados).
# ==============================================================================

locals {
  common_tags = merge(var.tags, {
    "Component" = "streaming"
  })
}

resource "oci_streaming_stream_pool" "this" {
  compartment_id = var.compartment_ocid
  name           = "sp-${var.project_name}-${var.environment}"

  # Pool PÚBLICO — sem bloco private_endpoint_settings. O messages endpoint é um
  # host regional OCI público, alcançável pelo SCH gerenciado (fora do VCN) e pelo
  # producer via egress NAT. IMUTÁVEL: adicionar/remover private_endpoint_settings
  # força destroy/recreate do pool + streams (perda de mensagens em buffer).
  #
  # ⚠️ SEM prevent_destroy NO POOL (decisão deliberada — trade-off):
  #    private_endpoint_settings é optional+computed; um flip público↔privado NÃO
  #    é aplicável in-place e exige `terraform apply -replace='module.streaming.
  #    oci_streaming_stream_pool.this'`. Um prevent_destroy no pool bloquearia esse
  #    -replace legítimo. Por isso a proteção prevent_destroy fica APENAS no
  #    oci_streaming_stream (portador de dados), não no pool. O -replace do pool
  #    cascateia p/ o stream e p/ os connectors SCH — revisar o plano antes.
  #
  # COMPENSATING CONTROLS do endpoint público (o pool não tem isolamento de rede):
  #   1. IAM least-privilege do serviceconnector — STREAM_READ/STREAM_CONSUME
  #      escopados a target.stream.id em modules/iam-sch (não compartment-wide);
  #      producer restrito ao DG Functions via stream-push.
  #   2. CMEK (custom_encryption_key abaixo) — criptografia com chave do cliente
  #      quando var.kms_key_id != "" (habilitar via streaming_use_cmek no env).
  #   3. OCI Audit — todas as chamadas de management/data plane do Streaming são
  #      auditadas (retenção do serviço Audit); investigar acesso anômalo por lá.
  #   4. Kafka SASL/PLAIN + IAM auth — sem credencial válida o endpoint público
  #      rejeita conexão (auto_create_topics=false impede criação de topic ad-hoc).

  # Kafka compatibility — nunca auto-criar topics (bypassa naming/partition/tags).
  kafka_settings {
    auto_create_topics_enable = false
  }

  # CMEK opcional — chave gerenciada pelo cliente (compliance). Vazio = Oracle-managed.
  # Wiring confirmado no env: kms_key_id = var.streaming_use_cmek ? module.vault.key_id : ""
  # (infra/environments/dev/main.tf → module.streaming). Compensating control #2.
  dynamic "custom_encryption_key" {
    for_each = var.kms_key_id != "" ? [1] : []
    content {
      kms_key_id = var.kms_key_id
    }
  }

  freeform_tags = local.common_tags
}

resource "oci_streaming_stream" "event_stream" {
  name               = var.stream_name
  partitions         = var.partitions         # IMUTÁVEL após criação
  retention_in_hours = var.retention_in_hours # Read-only após criação
  stream_pool_id     = oci_streaming_stream_pool.this.id

  freeform_tags = local.common_tags

  # PROTEÇÃO DE DADOS — o stream carrega os eventos em buffer (retention até 7d) e
  # os cursores dos 2 connectors SCH. partitions e retention_in_hours são IMUTÁVEIS:
  # qualquer alteração forçaria destroy/recreate com PERDA de todas as mensagens
  # retidas e reset dos cursores. prevent_destroy exige que uma migração seja
  # planejada explicitamente (remover este bloco de forma deliberada) antes de
  # qualquer destroy — evita perda acidental num `terraform destroy` ou num plan
  # que recrie o stream. (skill provisioning-oci-event-driven-pubsub — Always Do.)
  lifecycle {
    prevent_destroy = true
  }
}
