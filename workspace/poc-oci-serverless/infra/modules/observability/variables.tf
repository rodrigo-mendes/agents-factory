variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid deve ser um OCID válido (ocid1.compartment.*)."
  }
}

variable "functions_application_id" {
  type        = string
  description = "OCID da Functions Application (para log source)"
  default     = ""

  validation {
    condition     = var.functions_application_id == "" || can(regex("^ocid1\\.fnapp\\.", var.functions_application_id))
    error_message = "functions_application_id deve ser um OCID válido de Functions Application (ocid1.fnapp.*)."
  }
}

variable "functions_applications" {
  type        = map(string)
  description = "Mapa de nomes de Functions Applications para seus OCIDs"
  default     = {}

  validation {
    condition     = alltrue([for k, v in var.functions_applications : can(regex("^ocid1\\.fnapp\\.", v))])
    error_message = "Todos os valores no mapa functions_applications devem ser OCIDs válidos de Functions Application (ocid1.fnapp.*)."
  }
}

variable "api_deployment_id" {
  type        = string
  description = "OCID do API Gateway Deployment (para log source)"

  validation {
    condition     = can(regex("^ocid1\\.apideployment\\.", var.api_deployment_id))
    error_message = "api_deployment_id deve ser um OCID válido de API Deployment (ocid1.apideployment.*)."
  }
}

variable "service_connector_ids" {
  type        = map(string)
  description = "Mapa nome-lógico → OCID dos Service Connectors (SCH). Gera alarmes de erro por connector (ErrorsAtSource/ErrorsAtTarget + no-throughput) reusando o ONS topic. Vazio = nenhum alarme SCH."
  default     = {}

  validation {
    condition     = alltrue([for v in values(var.service_connector_ids) : can(regex("^ocid1\\.serviceconnector\\.", v))])
    error_message = "Todos os valores em service_connector_ids devem ser OCIDs válidos de Service Connector (ocid1.serviceconnector.*)."
  }
}

variable "enable_logging" {
  type        = bool
  description = "Habilitar OCI Logging"
  default     = true
}

variable "enable_monitoring_alarms" {
  type        = bool
  description = "Habilitar OCI Monitoring Alarms"
  default     = true
}

variable "alarm_duration_threshold_ms" {
  type        = number
  description = "Threshold em ms para alarme de latência P95"
  default     = 25000

  validation {
    condition     = var.alarm_duration_threshold_ms > 0 && var.alarm_duration_threshold_ms <= 300000
    error_message = "alarm_duration_threshold_ms deve ser entre 1 e 300000."
  }
}

variable "notification_topic_name" {
  type        = string
  description = "Nome base do Notification Topic"
  default     = "serverless-alerts"
}

variable "alarm_notification_email" {
  type        = string
  description = "Email que recebe as notificações de alarme (subscription EMAIL no tópico ONS). Vazio desabilita a subscription."
  default     = ""

  validation {
    condition     = var.alarm_notification_email == "" || can(regex("^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$", var.alarm_notification_email))
    error_message = "alarm_notification_email deve ser vazio ou um endereço de email válido."
  }
}

variable "environment" {
  type        = string
  description = "Nome do ambiente"
}

variable "project_name" {
  type        = string
  description = "Nome do projeto"
}

variable "tags" {
  type        = map(string)
  description = "Tags para os recursos"
  default     = {}
}
