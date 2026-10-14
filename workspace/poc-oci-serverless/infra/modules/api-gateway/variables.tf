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
  description = "OCID da subnet pública para o Gateway"

  validation {
    condition     = can(regex("^ocid1\\.subnet\\.", var.subnet_id))
    error_message = "subnet_id deve ser um OCID válido (ocid1.subnet.*)."
  }
}

variable "nsg_ids" {
  type        = list(string)
  description = "Lista de NSG IDs para o Gateway"
  default     = []
}

variable "route_backends" {
  type = list(object({
    path        = string
    methods     = list(string)
    function_id = string
    auth_type   = optional(string, "AUTHENTICATION_ONLY")
  }))
  description = "Lista de routes com function_id individual por rota."

  validation {
    condition     = alltrue([for r in var.route_backends : can(regex("^ocid1\\.fnfunc\\.", r.function_id))])
    error_message = "Cada route_backend.function_id deve ser um OCID válido (ocid1.fnfunc.*)."
  }
}

variable "gateway_name" {
  type        = string
  description = "Nome do API Gateway"
  default     = "apigw-serverless"
}

variable "endpoint_type" {
  type        = string
  description = "Tipo de endpoint: PUBLIC ou PRIVATE"
  default     = "PUBLIC"

  validation {
    condition     = contains(["PUBLIC", "PRIVATE"], var.endpoint_type)
    error_message = "endpoint_type deve ser PUBLIC ou PRIVATE."
  }
}

variable "deployment_path_prefix" {
  type        = string
  description = "Path prefix do deployment"
  default     = "/v1"
}

variable "rate_limit_requests_per_second" {
  type        = number
  description = "Rate limit em requests por segundo (0 = desabilitado)"
  default     = 100

  validation {
    condition     = var.rate_limit_requests_per_second >= 0 && var.rate_limit_requests_per_second <= 10000
    error_message = "rate_limit_requests_per_second deve ser entre 0 e 10000."
  }
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "Origins permitidos no CORS"
  default     = []
}

variable "jwt_auth_enabled" {
  type        = bool
  description = "Habilitar autenticação JWT"
  default     = false
}

variable "jwt_issuers" {
  type        = list(string)
  description = "Issuers válidos para JWT"
  default     = []
}

variable "jwt_audiences" {
  type        = list(string)
  description = "Audiences válidos para JWT"
  default     = []
}

variable "jwt_jwks_uri" {
  type        = string
  description = "URI do JWKS endpoint"
  default     = ""
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
