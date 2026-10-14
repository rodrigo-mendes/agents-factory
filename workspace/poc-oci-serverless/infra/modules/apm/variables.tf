variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment onde o APM Domain será criado"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid deve ser um OCID válido (ocid1.compartment.*)."
  }
}

variable "project_name" {
  type        = string
  description = "Nome do projeto (usado na composição do display_name)"

  validation {
    condition     = length(var.project_name) > 0
    error_message = "project_name não pode ser vazio."
  }
}

variable "environment" {
  type        = string
  description = "Nome do ambiente (dev, prod)"

  validation {
    condition     = contains(["dev", "prod", "staging"], var.environment)
    error_message = "environment deve ser dev, prod ou staging."
  }
}

variable "tags" {
  type        = map(string)
  description = "Freeform tags para os recursos"
  default     = {}
}
