variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid deve ser um OCID válido (ocid1.compartment.*)."
  }
}

variable "subnet_id" {
  type        = string
  description = "OCID da subnet privada para a Application"

  validation {
    condition     = can(regex("^ocid1\\.subnet\\.", var.subnet_id))
    error_message = "subnet_id deve ser um OCID válido (ocid1.subnet.*)."
  }
}

variable "nsg_ids" {
  type        = list(string)
  description = "Lista de NSG IDs para a Application"
  default     = []
}

variable "application_name" {
  type        = string
  description = "Nome da Functions Application"
}

variable "function_name" {
  type        = string
  description = "Nome da Function"
}

variable "function_image" {
  type        = string
  description = "URI da imagem Docker no OCIR (region.ocir.io/namespace/repo:tag)"

  validation {
    condition     = can(regex("^[a-z]{2,4}\\.ocir\\.io/", var.function_image))
    error_message = "function_image deve ser uma URI válida do OCIR (region.ocir.io/namespace/repo:tag)."
  }
}

variable "memory_in_mbs" {
  type        = number
  description = "Memória da Function em MB"
  default     = 256

  validation {
    condition     = contains([128, 256, 512, 1024, 2048], var.memory_in_mbs)
    error_message = "memory_in_mbs deve ser 128, 256, 512, 1024, ou 2048."
  }
}

variable "timeout_in_seconds" {
  type        = number
  description = "Timeout da Function em segundos"
  default     = 60

  validation {
    condition     = var.timeout_in_seconds >= 5 && var.timeout_in_seconds <= 300
    error_message = "timeout_in_seconds deve ser entre 5 e 300."
  }
}

variable "function_config" {
  type        = map(string)
  description = "Variáveis de configuração da Function (application-level config)"
  default     = {}
}


variable "function_shape" {
  type        = string
  description = "Arquitetura do processador. Deve ser compatível com a imagem Docker."
  default     = "GENERIC_X86"

  validation {
    condition     = contains(["GENERIC_X86", "GENERIC_ARM", "GENERIC_X86_ARM"], var.function_shape)
    error_message = "function_shape deve ser GENERIC_X86, GENERIC_ARM, ou GENERIC_X86_ARM."
  }
}

variable "provisioned_concurrency" {
  type        = number
  description = "Número de instâncias pre-aquecidas (0 = desabilitado)"
  default     = 0

  validation {
    condition     = var.provisioned_concurrency >= 0 && var.provisioned_concurrency <= 40
    error_message = "provisioned_concurrency deve ser entre 0 e 40."
  }
}

variable "trace_enabled" {
  type        = bool
  description = "Habilitar tracing na Function"
  default     = true
}

variable "apm_domain_id" {
  type        = string
  description = "OCID do APM Domain para trace_config (vazio = sem APM vinculado)"
  default     = ""
}

variable "environment" {
  type        = string
  description = "Nome do ambiente (dev, prod)"
}

variable "tags" {
  type        = map(string)
  description = "Freeform tags para os recursos"
  default     = {}
}
