# ==============================================================================
# Module: Vault — Variables
# ==============================================================================

variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment onde o Vault será criado"
}

variable "project_name" {
  type        = string
  description = "Nome do projeto (usado no naming)"
  default     = "serverless"
}

variable "environment" {
  type        = string
  description = "Ambiente (dev, staging, prod)"
  default     = "dev"
}

variable "key_protection_mode" {
  type        = string
  description = "Modo de proteção da chave: SOFTWARE (dev) ou HSM (prod)"
  default     = "SOFTWARE"

  validation {
    condition     = contains(["SOFTWARE", "HSM"], var.key_protection_mode)
    error_message = "key_protection_mode deve ser SOFTWARE ou HSM."
  }
}

variable "create_bucket" {
  type        = bool
  description = "Criar bucket Object Storage para API Facade"
  default     = true
}

variable "bucket_name" {
  type        = string
  description = "Nome base do bucket (será sufixado com environment)"
  default     = "api-facade"
}

variable "tags" {
  type        = map(string)
  description = "Freeform tags aplicadas a todos os recursos"
  default     = {}
}
