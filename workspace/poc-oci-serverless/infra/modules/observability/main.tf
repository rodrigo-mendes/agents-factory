# ==============================================================================
# Module: Observability
# ==============================================================================
# OCI Logging (Log Group + Service Logs) + Monitoring (Alarms + Notifications)
# ==============================================================================

locals {
  apps = merge(
    var.functions_application_id != "" ? { "default" = var.functions_application_id } : {},
    var.functions_applications
  )
}

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------

resource "oci_logging_log_group" "this" {
  count = var.enable_logging ? 1 : 0

  compartment_id = var.compartment_ocid
  display_name   = "lg-${var.project_name}-${var.environment}"
  description    = "Log group for serverless infrastructure (${var.project_name}-${var.environment})"

  freeform_tags = var.tags
}

resource "oci_logging_log" "functions_invoke" {
  for_each = var.enable_logging ? local.apps : {}

  display_name = "log-functions-invoke-${each.key}-${var.environment}"
  log_group_id = oci_logging_log_group.this[0].id
  log_type     = "SERVICE"
  is_enabled   = true

  configuration {
    compartment_id = var.compartment_ocid

    source {
      category    = "invoke"
      resource    = each.value
      service     = "functions"
      source_type = "OCISERVICE"
    }
  }

  freeform_tags = var.tags
}

resource "oci_logging_log" "apigw_access" {
  count = var.enable_logging ? 1 : 0

  display_name = "log-apigw-access-${var.environment}"
  log_group_id = oci_logging_log_group.this[0].id
  log_type     = "SERVICE"
  is_enabled   = true

  configuration {
    compartment_id = var.compartment_ocid

    source {
      category    = "access"
      resource    = var.api_deployment_id
      service     = "apigateway"
      source_type = "OCISERVICE"
    }
  }

  freeform_tags = var.tags
}

resource "oci_logging_log" "apigw_execution" {
  count = var.enable_logging ? 1 : 0

  display_name = "log-apigw-execution-${var.environment}"
  log_group_id = oci_logging_log_group.this[0].id
  log_type     = "SERVICE"
  is_enabled   = true

  configuration {
    compartment_id = var.compartment_ocid

    source {
      category    = "execution"
      resource    = var.api_deployment_id
      service     = "apigateway"
      source_type = "OCISERVICE"
    }
  }

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Monitoring — Notification Topic
# ------------------------------------------------------------------------------

resource "oci_ons_notification_topic" "alerts" {
  count = var.enable_monitoring_alarms ? 1 : 0

  compartment_id = var.compartment_ocid
  name           = "${var.notification_topic_name}-${var.project_name}-${var.environment}"
  description    = "Alertas de infraestrutura serverless (${var.project_name}-${var.environment})"

  freeform_tags = var.tags
}

# Subscription de email para o tópico de alertas.
# Sem uma subscription confirmada, os alarmes disparam mas ninguém é notificado.
# A OCI envia um email de confirmação; a subscription fica PENDING até o clique no link.
resource "oci_ons_subscription" "alarm_email" {
  count = var.enable_monitoring_alarms && var.alarm_notification_email != "" ? 1 : 0

  compartment_id = var.compartment_ocid
  topic_id       = oci_ons_notification_topic.alerts[0].id
  protocol       = "EMAIL"
  endpoint       = var.alarm_notification_email

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Monitoring — Alarms
# ------------------------------------------------------------------------------

resource "oci_monitoring_alarm" "function_errors" {
  for_each = var.enable_monitoring_alarms ? local.apps : {}

  compartment_id        = var.compartment_ocid
  display_name          = "alarm-fn-errors-${each.key}-${var.project_name}-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_faas"
  severity              = "CRITICAL"

  query = "FunctionErrorCount[5m]{applicationId = \"${each.value}\"}.sum() > 0"

  body                                          = "Function invocation errors detected in application ${each.key} (${var.project_name}-${var.environment})"
  message_format                                = "ONS_OPTIMIZED"
  pending_duration                              = "PT5M"
  repeat_notification_duration                  = "PT15M"
  is_notifications_per_metric_dimension_enabled = false

  destinations = var.enable_monitoring_alarms ? [oci_ons_notification_topic.alerts[0].id] : []

  freeform_tags = var.tags
}

resource "oci_monitoring_alarm" "function_duration" {
  for_each = var.enable_monitoring_alarms ? local.apps : {}

  compartment_id        = var.compartment_ocid
  display_name          = "alarm-fn-latency-${each.key}-${var.project_name}-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_faas"
  severity              = "WARNING"

  query = "FunctionExecutionDuration[5m]{applicationId = \"${each.value}\"}.percentile(0.95) > ${var.alarm_duration_threshold_ms}"

  body                                          = "Function P95 latency exceeds ${var.alarm_duration_threshold_ms}ms in application ${each.key} (${var.project_name}-${var.environment})"
  message_format                                = "ONS_OPTIMIZED"
  pending_duration                              = "PT5M"
  repeat_notification_duration                  = "PT30M"
  is_notifications_per_metric_dimension_enabled = false

  destinations = var.enable_monitoring_alarms ? [oci_ons_notification_topic.alerts[0].id] : []

  freeform_tags = var.tags
}

resource "oci_monitoring_alarm" "function_throttle" {
  for_each = var.enable_monitoring_alarms ? local.apps : {}

  compartment_id        = var.compartment_ocid
  display_name          = "alarm-fn-throttle-${each.key}-${var.project_name}-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_faas"
  severity              = "WARNING"

  query = "FunctionThrottleCount[5m]{applicationId = \"${each.value}\"}.sum() > 0"

  body                                          = "Function throttling detected in application ${each.key} (${var.project_name}-${var.environment})"
  message_format                                = "ONS_OPTIMIZED"
  pending_duration                              = "PT5M"
  repeat_notification_duration                  = "PT30M"
  is_notifications_per_metric_dimension_enabled = false

  destinations = var.enable_monitoring_alarms ? [oci_ons_notification_topic.alerts[0].id] : []

  freeform_tags = var.tags
}

resource "oci_monitoring_alarm" "apigw_5xx" {
  count = var.enable_monitoring_alarms ? 1 : 0

  compartment_id        = var.compartment_ocid
  display_name          = "alarm-apigw-5xx-${var.project_name}-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_apigateway"
  severity              = "CRITICAL"

  # A dimensão httpStatusCategory="5xx" casa no MQL do OCI; o regex httpStatusCode=~"5.." NÃO casa.
  query = "HttpResponses[5m]{httpStatusCategory = \"5xx\"}.sum() > 5"

  body                                          = "API Gateway 5xx errors detected in ${var.project_name}-${var.environment}"
  message_format                                = "ONS_OPTIMIZED"
  pending_duration                              = "PT5M"
  repeat_notification_duration                  = "PT15M"
  is_notifications_per_metric_dimension_enabled = false

  destinations = var.enable_monitoring_alarms ? [oci_ons_notification_topic.alerts[0].id] : []

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Monitoring — Service Connector Hub Alarms (pub/sub fan-out)
# ------------------------------------------------------------------------------
# Skill: provisioning-oci-connector-hub — Anti-Pattern 3 (no alarm = silent data
# loss). Um SCH em FAILED não emite métrica de "falha" e para de entregar em
# silêncio; sem alarme a perda de dados só é notada dias depois. Um alarme por
# connector (for_each sobre var.service_connector_ids), reusando o ONS topic dos
# demais alarmes. Escopo por connectorId no MQL. Gated por enable_monitoring_alarms
# (garante que o ONS topic [0] existe).

# ErrorsAtSource > 0 — o SCH não consegue LER o stream (pool privado, IAM
# STREAM_READ/STREAM_CONSUME ausente/mal-escopada). CRITICAL.
resource "oci_monitoring_alarm" "sch_errors_at_source" {
  for_each = var.enable_monitoring_alarms ? var.service_connector_ids : {}

  compartment_id        = var.compartment_ocid
  display_name          = "alarm-sch-errsource-${each.key}-${var.project_name}-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_service_connector_hub"
  severity              = "CRITICAL"

  query = "ErrorsAtSource[1m]{connectorId = \"${each.value}\"}.sum() > 0"

  body                                          = "Service Connector '${each.key}' has ErrorsAtSource > 0 (cannot read the stream — check pool endpoint / STREAM_READ policy) in ${var.project_name}-${var.environment}"
  message_format                                = "ONS_OPTIMIZED"
  pending_duration                              = "PT1M"
  repeat_notification_duration                  = "PT15M"
  is_notifications_per_metric_dimension_enabled = false

  destinations = var.enable_monitoring_alarms ? [oci_ons_notification_topic.alerts[0].id] : []

  freeform_tags = var.tags
}

# ErrorsAtTarget > 0 — o SCH não consegue INVOCAR a Function target (fn-function/
# fn-invocation ausente, cold-start > deadline, função com erro). CRITICAL.
resource "oci_monitoring_alarm" "sch_errors_at_target" {
  for_each = var.enable_monitoring_alarms ? var.service_connector_ids : {}

  compartment_id        = var.compartment_ocid
  display_name          = "alarm-sch-errtarget-${each.key}-${var.project_name}-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_service_connector_hub"
  severity              = "CRITICAL"

  query = "ErrorsAtTarget[1m]{connectorId = \"${each.value}\"}.sum() > 0"

  body                                          = "Service Connector '${each.key}' has ErrorsAtTarget > 0 (cannot invoke the target Function — check fn-function/fn-invocation policy or function health) in ${var.project_name}-${var.environment}"
  message_format                                = "ONS_OPTIMIZED"
  pending_duration                              = "PT1M"
  repeat_notification_duration                  = "PT15M"
  is_notifications_per_metric_dimension_enabled = false

  destinations = var.enable_monitoring_alarms ? [oci_ons_notification_topic.alerts[0].id] : []

  freeform_tags = var.tags
}

# MessagesFromSource == 0 por 5m — o connector está ACTIVE mas não lê nada
# (sintoma de FAILED silencioso ou source vazia). WARNING (pode ser tráfego zero
# legítimo no POC; por isso não é CRITICAL).
resource "oci_monitoring_alarm" "sch_no_throughput" {
  for_each = var.enable_monitoring_alarms ? var.service_connector_ids : {}

  compartment_id        = var.compartment_ocid
  display_name          = "alarm-sch-nothroughput-${each.key}-${var.project_name}-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_service_connector_hub"
  severity              = "WARNING"

  query = "MessagesFromSource[5m]{connectorId = \"${each.value}\"}.sum() == 0"

  body                                          = "Service Connector '${each.key}' read zero messages from source in 5m (silent FAILED state or no traffic) in ${var.project_name}-${var.environment}"
  message_format                                = "ONS_OPTIMIZED"
  pending_duration                              = "PT5M"
  repeat_notification_duration                  = "PT30M"
  is_notifications_per_metric_dimension_enabled = false

  destinations = var.enable_monitoring_alarms ? [oci_ons_notification_topic.alerts[0].id] : []

  freeform_tags = var.tags
}
