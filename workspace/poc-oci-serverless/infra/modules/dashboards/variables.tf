# ==============================================================================
# Module: dashboards — Variables
# ==============================================================================

variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment onde os Management Dashboards e Saved Searches serão criados."

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid deve ser um OCID válido iniciando com ocid1.compartment."
  }
}

variable "application_id" {
  type        = string
  description = "OCID da Application do func-rr-rest-proxy — usado como resourceId nas MQL do namespace oci_faas."

  validation {
    condition     = can(regex("^ocid1\\.fnapp\\.", var.application_id))
    error_message = "application_id deve ser um OCID de Application válido iniciando com ocid1.fnapp."
  }
}

variable "apm_domain_id" {
  type        = string
  description = "OCID do APM Domain — usado como apmDomainId nas queries APM QL (dependências upstream)."

  validation {
    condition     = can(regex("^ocid1\\.apmdomain\\.", var.apm_domain_id))
    error_message = "apm_domain_id deve ser um OCID de APM Domain válido iniciando com ocid1.apmdomain."
  }
}

variable "api_deployment_id" {
  type        = string
  description = "OCID do API Gateway Deployment — usado como deploymentId nas MQL do namespace oci_apigateway."

  validation {
    condition     = can(regex("^ocid1\\.apideployment\\.", var.api_deployment_id))
    error_message = "api_deployment_id deve ser um OCID de API Gateway Deployment válido iniciando com ocid1.apideployment."
  }
}

variable "metric_namespace" {
  type        = string
  description = "Namespace de métricas customizadas emitidas pelo func-rr-rest-proxy (PostMetricData)."
  default     = "rest_proxy_analytics"

  validation {
    condition     = length(var.metric_namespace) > 0 && length(var.metric_namespace) <= 256
    error_message = "metric_namespace não pode ser vazio e deve ter no máximo 256 caracteres."
  }
}

variable "environment" {
  type        = string
  description = "Nome do ambiente (dev, staging, prod) — usado em display names e tags."

  validation {
    condition     = length(var.environment) > 0
    error_message = "environment não pode ser vazio."
  }
}

variable "freeform_tags" {
  type        = map(string)
  description = "Freeform tags aplicadas aos Management Dashboards e Saved Searches."
  default     = {}
}

# ------------------------------------------------------------------------------
# Event pub/sub — inputs do 04-transaction-path.json
# ------------------------------------------------------------------------------
# Function OCIDs (não Application) porque as MQL oci_faas do dashboard filtram por
# resourceId = OCID da Function (producer/notify/audit vivem em 3 Applications
# distintas, então resourceId é o seletor por-função correto). Todos com default
# vazio para não afetar os 3 dashboards existentes do rest-proxy quando não
# fornecidos; a regex aceita "" (feature off) OU um OCID ocid1.fnfunc. válido.

variable "producer_function_id" {
  type        = string
  description = "OCID da Function func-event-producer — resourceId na MQL oci_faas de publish rate. Vazio desativa a tile."
  default     = ""

  validation {
    condition     = var.producer_function_id == "" || can(regex("^ocid1\\.fnfunc\\.", var.producer_function_id))
    error_message = "producer_function_id deve ser vazio ou um OCID de Function válido iniciando com ocid1.fnfunc."
  }
}

variable "notify_function_id" {
  type        = string
  description = "OCID da Function func-evt-consumer-notify — resourceId na MQL oci_faas de consume rate. Vazio desativa a tile."
  default     = ""

  validation {
    condition     = var.notify_function_id == "" || can(regex("^ocid1\\.fnfunc\\.", var.notify_function_id))
    error_message = "notify_function_id deve ser vazio ou um OCID de Function válido iniciando com ocid1.fnfunc."
  }
}

variable "audit_function_id" {
  type        = string
  description = "OCID da Function func-evt-consumer-audit — resourceId na MQL oci_faas de consume rate. Vazio desativa a tile."
  default     = ""

  validation {
    condition     = var.audit_function_id == "" || can(regex("^ocid1\\.fnfunc\\.", var.audit_function_id))
    error_message = "audit_function_id deve ser vazio ou um OCID de Function válido iniciando com ocid1.fnfunc."
  }
}

variable "events_metric_namespace" {
  type        = string
  description = "Namespace de métricas customizadas do pub/sub (EventConsumeLagMs, AuditEventProcessed). Distinto de metric_namespace (rest-proxy) para não quebrar 01/03."
  default     = "event_pubsub_analytics"

  validation {
    condition     = length(var.events_metric_namespace) > 0 && length(var.events_metric_namespace) <= 256
    error_message = "events_metric_namespace não pode ser vazio e deve ter no máximo 256 caracteres."
  }
}
