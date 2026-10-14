variable "tenancy_ocid" {
  type        = string
  description = "OCID da tenancy"

  validation {
    condition     = can(regex("^ocid1\\.tenancy\\.", var.tenancy_ocid))
    error_message = "tenancy_ocid deve ser um OCID válido (ocid1.tenancy.*)."
  }
}

variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid deve ser um OCID válido (ocid1.compartment.*)."
  }
}

variable "compartment_name" {
  type        = string
  description = "Nome do compartment (usado nas policies)"
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

variable "dashboard_viewers_all_users" {
  type        = bool
  description = "Se true, concede leitura dos Management Dashboards a todos os usuários humanos da tenancy (any-user where request.principal.type = 'user')."
  default     = false
}

variable "dashboard_viewer_groups" {
  type        = list(string)
  description = "Grupos IAM adicionais que recebem leitura dos Management Dashboards (nomes exatos)."
  default     = []
}

variable "readonly_viewer_group_name" {
  type        = string
  description = "Nome do grupo IAM read-only do compartment (vazio = não cria)."
  default     = ""
}

variable "readonly_viewer_user_ids" {
  type        = list(string)
  description = "OCIDs de usuários adicionados ao grupo read-only do compartment."
  default     = []

  validation {
    condition     = alltrue([for u in var.readonly_viewer_user_ids : can(regex("^ocid1\\.user\\.", u))])
    error_message = "Cada readonly_viewer_user_ids deve ser um OCID de usuário (ocid1.user.*)."
  }
}
