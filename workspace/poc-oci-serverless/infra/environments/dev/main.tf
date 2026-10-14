# ==============================================================================
# Environment: dev — Shared Infrastructure
# ==============================================================================
# Composes platform modules (network, iam, vault, observability).
# Application modules are in apps.tf.
# ==============================================================================

locals {
  tags = merge(var.freeform_tags, {
    "Environment" = var.environment
    "Project"     = var.project_name
    "ManagedBy"   = "terraform"
  })
}

# ------------------------------------------------------------------------------
# Network
# ------------------------------------------------------------------------------

module "network" {
  source = "../../modules/network"

  compartment_ocid    = var.compartment_ocid
  vcn_cidr_block      = var.vcn_cidr_block
  subnet_public_cidr  = var.subnet_public_cidr
  subnet_private_cidr = var.subnet_private_cidr
  create_nat_gateway  = var.create_nat_gateway
  use_nsg             = var.use_nsg
  environment         = var.environment
  project_name        = var.project_name
  tags                = local.tags
}

# ------------------------------------------------------------------------------
# IAM
# ------------------------------------------------------------------------------

module "iam" {
  source = "../../modules/iam"

  tenancy_ocid                = var.tenancy_ocid
  compartment_ocid            = var.compartment_ocid
  compartment_name            = var.compartment_name
  environment                 = var.environment
  project_name                = var.project_name
  dashboard_viewers_all_users = var.dashboard_viewers_all_users
  readonly_viewer_group_name  = var.readonly_viewer_group_name
  readonly_viewer_user_ids    = var.readonly_viewer_user_ids
  tags                        = local.tags
}

# ------------------------------------------------------------------------------
# Vault (KMS + Object Storage)
# ------------------------------------------------------------------------------

module "vault" {
  source = "../../modules/vault"

  compartment_ocid    = var.compartment_ocid
  project_name        = var.project_name
  environment         = var.environment
  key_protection_mode = var.vault_key_protection_mode
  create_bucket       = true
  bucket_name         = "api-facade"
  tags                = local.tags
}

# ------------------------------------------------------------------------------
# APM
# ------------------------------------------------------------------------------

module "apm" {
  source = "../../modules/apm"

  compartment_ocid = var.compartment_ocid
  project_name     = var.project_name
  environment      = var.environment
  tags             = local.tags
}

# ------------------------------------------------------------------------------
# Observability
# ------------------------------------------------------------------------------

module "observability" {
  source = "../../modules/observability"

  compartment_ocid         = var.compartment_ocid
  api_deployment_id        = module.api_gateway.deployment_id
  enable_logging           = true
  enable_monitoring_alarms = true
  alarm_notification_email = var.alarm_notification_email
  environment              = var.environment
  project_name             = var.project_name
  tags                     = local.tags

  functions_applications = {
    "api-handler"             = module.app_api_handler.application_id
    "func-api-facade"         = module.app_api_facade.application_id
    "rest-proxy"              = module.app_rest_proxy.application_id
    "app-event-producer"      = module.app_event_producer.application_id
    "app-evt-consumer-notify" = module.app_evt_consumer_notify.application_id
    "app-evt-consumer-audit"  = module.app_evt_consumer_audit.application_id
  }

  # Service Connector Hub — alarmes de erro por connector (ErrorsAtSource/
  # ErrorsAtTarget CRITICAL + no-throughput WARNING). Sem alarme, um SCH em FAILED
  # descarta dados em silêncio (connector-hub Anti-Pattern 3). Reusa o ONS topic.
  service_connector_ids = module.service_connector.connector_ids
}

# ------------------------------------------------------------------------------
# Dashboards — Custom Management Dashboards for func-rr-rest-proxy
# ------------------------------------------------------------------------------

module "dashboards" {
  source = "../../modules/dashboards"

  compartment_ocid  = var.compartment_ocid
  application_id    = module.app_rest_proxy.application_id
  apm_domain_id     = module.apm.apm_domain_id
  api_deployment_id = module.api_gateway.deployment_id
  metric_namespace  = "rest_proxy_analytics"
  environment       = var.environment
  freeform_tags     = local.tags

  # Event pub/sub — alimenta o 04-transaction-path.json (APM QL por txnId + MQL de
  # publish/consume rate por Function OCID e métricas custom do namespace do pub/sub).
  # apm_domain_id (acima) é o mesmo APM Domain compartilhado pelo trace distribuído.
  producer_function_id    = module.app_event_producer.function_id
  notify_function_id      = module.app_evt_consumer_notify.function_id
  audit_function_id       = module.app_evt_consumer_audit.function_id
  events_metric_namespace = "event_pubsub_analytics"
}

# ------------------------------------------------------------------------------
# Streaming — OCI Streaming (Kafka-compatible) backbone do pub/sub
# ------------------------------------------------------------------------------
# Private endpoint na subnet privada das Functions; reusa o NSG de Functions
# (egress já é all→0.0.0.0/0 e a subnet privada roteia p/ Service Gateway, então
# o endpoint privado do pool é alcançável). CMEK opcional via module.vault.
module "streaming" {
  source = "../../modules/streaming"

  # Pool público (sem private endpoint) — subnet_id/nsg_ids não são mais passados.
  # O SCH gerenciado (fora do VCN) precisa de um endpoint público para ler o stream.
  compartment_ocid   = var.compartment_ocid
  kms_key_id         = var.streaming_use_cmek ? module.vault.key_id : ""
  stream_name        = "event-stream"
  partitions         = 3
  retention_in_hours = 168
  project_name       = var.project_name
  environment        = var.environment
  tags               = local.tags
}

# ------------------------------------------------------------------------------
# IAM-SCH — policy least-privilege do Service Connector Hub (relocada do módulo iam)
# ------------------------------------------------------------------------------
# Módulo dedicado (quebra de ciclo): escopa as statements do serviceconnector a
# target.stream.id (STREAM_READ/STREAM_CONSUME) e target.function.id (fn-function +
# fn-invocation, ambos exigidos pelo target Functions). Referenciar os function_id
# aqui — e NÃO no módulo base `iam` — evita o ciclo iam → app → iam (as apps têm
# depends_on = [module.iam]). depends_on explícito garante que stream + Functions
# existam antes de a policy ser resolvida. Ver modules/iam-sch/main.tf.
module "iam_sch" {
  source = "../../modules/iam-sch"

  compartment_ocid   = var.compartment_ocid
  compartment_name   = var.compartment_name
  stream_id          = module.streaming.stream_id
  notify_function_id = module.app_evt_consumer_notify.function_id
  audit_function_id  = module.app_evt_consumer_audit.function_id
  project_name       = var.project_name
  environment        = var.environment
  tags               = local.tags

  depends_on = [
    module.streaming,
    module.app_evt_consumer_notify,
    module.app_evt_consumer_audit,
  ]
}

# ------------------------------------------------------------------------------
# Service Connector Hub — fan-out do stream para os 2 consumers (Functions)
# ------------------------------------------------------------------------------
# Dois connectors (notify, audit) com a MESMA source streaming (event-stream) e
# cursores independentes → fan-out real (cada consumer recebe todas as mensagens).
# Target = a Function consumer correspondente. As policies IAM (producer stream-push
# em module.iam + serviceconnector STREAM_READ/STREAM_CONSUME/fn-function/fn-invocation
# escopadas em module.iam_sch) DEVEM existir antes da ativação — injetadas via
# iam_dependencies → depends_on.
module "service_connector" {
  source = "../../modules/service-connector"

  compartment_ocid = var.compartment_ocid
  stream_id        = module.streaming.stream_id
  cursor_kind      = "TRIM_HORIZON"

  default_batch_size_in_kbs = var.sch_batch_size_in_kbs
  default_batch_time_in_sec = var.sch_batch_time_in_sec

  connectors = {
    notify = {
      display_name = "sch-event-notify-${var.environment}"
      function_id  = module.app_evt_consumer_notify.function_id
    }
    audit = {
      display_name = "sch-event-audit-${var.environment}"
      function_id  = module.app_evt_consumer_audit.function_id
    }
  }

  connector_state = "ACTIVE"
  iam_dependencies = [
    module.iam,
    module.iam_sch,
  ]

  tags = local.tags
}
