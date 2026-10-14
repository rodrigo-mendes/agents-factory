# ==============================================================================
# Variables: prod environment
# ==============================================================================

# --- Required ---

variable "tenancy_ocid" {
  type        = string
  description = "OCID do tenancy"

  validation {
    condition     = can(regex("^ocid1\\.tenancy\\.", var.tenancy_ocid))
    error_message = "tenancy_ocid must be a valid tenancy OCID (ocid1.tenancy.*)."
  }
}

variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid must be a valid compartment OCID (ocid1.compartment.*)."
  }
}

variable "compartment_name" {
  type        = string
  description = "Nome do compartment"

  validation {
    condition     = length(var.compartment_name) > 0 && length(var.compartment_name) <= 100
    error_message = "compartment_name must be non-empty and at most 100 characters."
  }
}

variable "region" {
  type        = string
  description = "OCI Region"
  default     = "sa-saopaulo-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]+$", var.region))
    error_message = "region must be a valid OCI region identifier (e.g., sa-saopaulo-1)."
  }
}

# --- Function Images ---

variable "api_handler_image" {
  type        = string
  description = "OCIR image URI for api-handler function"

  validation {
    condition     = can(regex("^[a-z]{2,4}\\.ocir\\.io/", var.api_handler_image))
    error_message = "api_handler_image must be a valid OCIR URI (e.g., gru.ocir.io/namespace/repo/image:tag)."
  }
}

variable "api_facade_image" {
  type        = string
  description = "OCIR image URI for func-api-facade function"

  validation {
    condition     = can(regex("^[a-z]{2,4}\\.ocir\\.io/", var.api_facade_image))
    error_message = "api_facade_image must be a valid OCIR URI (e.g., gru.ocir.io/namespace/repo/image:tag)."
  }
}

variable "rest_proxy_image" {
  type        = string
  description = "OCIR image URI for func-rr-rest-proxy function"

  validation {
    condition     = can(regex("^[a-z]{2,4}\\.ocir\\.io/", var.rest_proxy_image))
    error_message = "rest_proxy_image must be a valid OCIR URI (e.g., gru.ocir.io/namespace/repo/image:tag)."
  }
}

# --- Functions (shared) ---

variable "function_shape" {
  type        = string
  description = "Arquitetura do processador"
  default     = "GENERIC_X86"

  validation {
    condition     = contains(["GENERIC_X86", "GENERIC_ARM", "GENERIC_X86_ARM"], var.function_shape)
    error_message = "function_shape must be one of: GENERIC_X86, GENERIC_ARM, GENERIC_X86_ARM."
  }
}

variable "trace_enabled" {
  type        = bool
  description = "Habilitar tracing nas Functions"
  default     = true
}

variable "provisioned_concurrency" {
  type        = number
  description = "Instâncias pre-aquecidas por Function (0 = desabilitado)"
  default     = 0

  validation {
    condition     = var.provisioned_concurrency >= 0 && var.provisioned_concurrency <= 40
    error_message = "provisioned_concurrency must be between 0 and 40."
  }
}

# --- Networking ---

variable "vcn_cidr_block" {
  type    = string
  default = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vcn_cidr_block, 0))
    error_message = "vcn_cidr_block must be a valid CIDR notation (e.g., 10.0.0.0/16)."
  }
}

variable "subnet_public_cidr" {
  type    = string
  default = "10.0.0.0/24"

  validation {
    condition     = can(cidrhost(var.subnet_public_cidr, 0))
    error_message = "subnet_public_cidr must be a valid CIDR notation (e.g., 10.0.0.0/24)."
  }
}

variable "subnet_private_cidr" {
  type    = string
  default = "10.0.1.0/24"

  validation {
    condition     = can(cidrhost(var.subnet_private_cidr, 0))
    error_message = "subnet_private_cidr must be a valid CIDR notation (e.g., 10.0.1.0/24)."
  }
}

variable "create_nat_gateway" {
  type    = bool
  default = true
}

variable "use_nsg" {
  type    = bool
  default = true
}

# --- API Gateway ---

variable "api_gateway_name" {
  type    = string
  default = "apigw-serverless"
}

variable "api_gateway_endpoint_type" {
  type    = string
  default = "PUBLIC"

  validation {
    condition     = contains(["PUBLIC", "PRIVATE"], var.api_gateway_endpoint_type)
    error_message = "api_gateway_endpoint_type must be PUBLIC or PRIVATE."
  }
}

variable "deployment_path_prefix" {
  type    = string
  default = "/v1"
}

variable "rate_limit_requests_per_second" {
  type    = number
  default = 100

  validation {
    condition     = var.rate_limit_requests_per_second >= 0 && var.rate_limit_requests_per_second <= 10000
    error_message = "rate_limit_requests_per_second must be between 0 and 10000."
  }
}

variable "cors_allowed_origins" {
  type    = list(string)
  default = []
}

variable "jwt_auth_enabled" {
  type    = bool
  default = false
}

variable "jwt_issuers" {
  type    = list(string)
  default = []
}

variable "jwt_audiences" {
  type    = list(string)
  default = []
}

variable "jwt_jwks_uri" {
  type    = string
  default = ""
}

# --- REST Proxy ---

variable "rest_proxy_store_source_base_url" {
  type    = string
  default = ""
}

variable "rest_proxy_store_destination_base_url" {
  type    = string
  default = ""
}

variable "rest_proxy_store_timeout_ms" {
  type    = string
  default = "10000"
}

variable "rest_proxy_store_oauth_token_url" {
  type    = string
  default = ""
}

variable "rest_proxy_store_oauth_scope" {
  type    = string
  default = ""
}

variable "rest_proxy_store_oauth_client_id" {
  type      = string
  sensitive = true
  default   = ""
}

variable "rest_proxy_store_oauth_client_secret" {
  type      = string
  sensitive = true
  default   = ""
}

# --- General ---

variable "environment" {
  type    = string
  default = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  type    = string
  default = "serverless"
}

variable "freeform_tags" {
  type    = map(string)
  default = {}
}
