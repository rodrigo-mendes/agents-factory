variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment onde a policy do Service Connector Hub é criada"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid deve ser um OCID válido (ocid1.compartment.*)."
  }
}

variable "compartment_name" {
  type        = string
  description = "Nome (display name) do compartment — referenciado NAS statements da policy (Allow ... in compartment <name>). Um valor errado reescreve as statements p/ um compartment inexistente e o SCH perde permissão."

  validation {
    condition     = length(var.compartment_name) > 0 && length(var.compartment_name) <= 100
    error_message = "compartment_name deve ser não-vazio e no máximo 100 caracteres."
  }
}

variable "stream_id" {
  type        = string
  description = "OCID do Stream (source) que o Service Connector Hub lê. Usado no escopo target.stream.id do STREAM_READ/STREAM_CONSUME (least-privilege)."

  validation {
    condition     = can(regex("^ocid1\\.stream\\.", var.stream_id))
    error_message = "stream_id deve ser um OCID válido de stream (ocid1.stream.*)."
  }
}

variable "notify_function_id" {
  type        = string
  description = "OCID da Function consumer notify (target do SCH). Usado no escopo target.function.id de fn-function/fn-invocation."

  validation {
    condition     = can(regex("^ocid1\\.fnfunc\\.", var.notify_function_id))
    error_message = "notify_function_id deve ser um OCID válido de function (ocid1.fnfunc.*)."
  }
}

variable "audit_function_id" {
  type        = string
  description = "OCID da Function consumer audit (target do SCH). Usado no escopo target.function.id de fn-function/fn-invocation."

  validation {
    condition     = can(regex("^ocid1\\.fnfunc\\.", var.audit_function_id))
    error_message = "audit_function_id deve ser um OCID válido de function (ocid1.fnfunc.*)."
  }
}

variable "project_name" {
  type        = string
  description = "Nome do projeto (usado no naming da policy)"
}

variable "environment" {
  type        = string
  description = "Nome do ambiente (dev, staging, prod)"
}

variable "tags" {
  type        = map(string)
  description = "Freeform tags aplicadas à policy"
  default     = {}
}
