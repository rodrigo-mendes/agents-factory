variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment onde os Service Connectors são criados"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid deve ser um OCID válido (ocid1.compartment.*)."
  }
}

variable "stream_id" {
  type        = string
  description = "OCID do Stream (source) lido por TODOS os connectors. Cada connector mantém seu próprio cursor → fan-out real."

  validation {
    condition     = can(regex("^ocid1\\.stream\\.", var.stream_id))
    error_message = "stream_id deve ser um OCID válido de stream (ocid1.stream.*)."
  }
}

variable "connectors" {
  type = map(object({
    display_name      = string
    function_id       = string
    batch_size_in_kbs = optional(number)
    batch_time_in_sec = optional(number)
  }))
  description = <<-EOT
    Mapa de connectors (chave estável = nome lógico) para fan-out via for_each.
    Cada entry: display_name, function_id (consumer target) e batch settings opcionais
    (fallback para var.default_batch_size_in_kbs / var.default_batch_time_in_sec).
  EOT

  validation {
    condition = alltrue([
      for c in values(var.connectors) : can(regex("^ocid1\\.fnfunc\\.", c.function_id))
    ])
    error_message = "Cada connector.function_id deve ser um OCID válido de function (ocid1.fnfunc.*)."
  }
}

variable "cursor_kind" {
  type        = string
  description = "Estratégia de cursor da source streaming. TRIM_HORIZON = reprocessa desde o mais antigo retido (downstream deve ser idempotente); LATEST = apenas novos."
  default     = "TRIM_HORIZON"

  validation {
    condition     = contains(["TRIM_HORIZON", "LATEST"], var.cursor_kind)
    error_message = "cursor_kind deve ser TRIM_HORIZON ou LATEST."
  }
}

variable "default_batch_size_in_kbs" {
  type        = number
  description = "Batch size (KB) default do target functions quando não definido por connector. Tunar p/ evitar cold-start storm vs latência. Máx 6000."
  default     = 128

  validation {
    condition     = var.default_batch_size_in_kbs >= 1 && var.default_batch_size_in_kbs <= 6000
    error_message = "default_batch_size_in_kbs deve ser entre 1 e 6000."
  }
}

variable "default_batch_time_in_sec" {
  type        = number
  description = "Batch time (segundos) default do target functions quando não definido por connector. Máx 600."
  default     = 60

  validation {
    condition     = var.default_batch_time_in_sec >= 1 && var.default_batch_time_in_sec <= 600
    error_message = "default_batch_time_in_sec deve ser entre 1 e 600."
  }
}

variable "connector_state" {
  type        = string
  description = "Estado dos connectors após o apply (ACTIVE | INACTIVE)"
  default     = "ACTIVE"

  validation {
    condition     = contains(["ACTIVE", "INACTIVE"], var.connector_state)
    error_message = "connector_state deve ser ACTIVE ou INACTIVE."
  }
}

variable "iam_dependencies" {
  type        = list(any)
  description = <<-EOT
    Handles de dependência (ex.: policy IAM do serviceconnector) que DEVEM existir
    antes da ativação dos connectors. Sem a policy o SCH entra em FAILED e descarta
    dados em silêncio (skill provisioning-oci-connector-hub, Pattern 4).
  EOT
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "Freeform tags aplicadas aos Service Connectors"
  default     = {}
}
