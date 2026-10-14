# ==============================================================================
# Variables: dev environment
# ==============================================================================

# --- Required (sem default) ---

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

variable "event_producer_image" {
  type        = string
  description = "OCIR image URI for func-event-producer function"
  default     = "gru.ocir.io/placeholder/serverless/func-event-producer:latest"

  validation {
    condition     = can(regex("^[a-z]{2,4}\\.ocir\\.io/", var.event_producer_image))
    error_message = "event_producer_image must be a valid OCIR URI (e.g., gru.ocir.io/namespace/repo/image:tag)."
  }
}

# --- Event pub/sub consumer Function images (OCIR) ---
# Consumers são OCI Functions (ConnectorHubFunction), targets do SCH. As imagens
# apontam para as versões native (0.0.3-native) no deploy; o default 0.0.2
# mantém validate/plan sãos — o deployer sobrescreve a tag via -var no apply.

variable "evt_consumer_notify_image" {
  type        = string
  description = "OCIR image URI para a Function func-evt-consumer-notify (ConnectorHubFunction, target do SCH notify)"
  default     = "gru.ocir.io/placeholder/serverless/func-evt-consumer-notify:0.0.2"

  validation {
    condition     = can(regex("^[a-z]{2,4}\\.ocir\\.io/", var.evt_consumer_notify_image))
    error_message = "evt_consumer_notify_image must be a valid OCIR URI (e.g., gru.ocir.io/namespace/repo/image:tag)."
  }
}

variable "evt_consumer_audit_image" {
  type        = string
  description = "OCIR image URI para a Function func-evt-consumer-audit (ConnectorHubFunction, target do SCH audit)"
  default     = "gru.ocir.io/placeholder/serverless/func-evt-consumer-audit:0.0.2"

  validation {
    condition     = can(regex("^[a-z]{2,4}\\.ocir\\.io/", var.evt_consumer_audit_image))
    error_message = "evt_consumer_audit_image must be a valid OCIR URI (e.g., gru.ocir.io/namespace/repo/image:tag)."
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

variable "alarm_notification_email" {
  type        = string
  description = "Email que recebe as notificações de alarme (subscription EMAIL no tópico ONS)."
  default     = "rodrigo.mendes@brxretail.com"

  validation {
    condition     = var.alarm_notification_email == "" || can(regex("^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$", var.alarm_notification_email))
    error_message = "alarm_notification_email deve ser vazio ou um endereço de email válido."
  }
}

# --- Networking ---

variable "vcn_cidr_block" {
  type        = string
  description = "CIDR block para o VCN"
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vcn_cidr_block, 0))
    error_message = "vcn_cidr_block must be a valid CIDR notation (e.g., 10.0.0.0/16)."
  }
}

variable "subnet_public_cidr" {
  type        = string
  description = "CIDR block para subnet pública (API Gateway)"
  default     = "10.0.0.0/24"

  validation {
    condition     = can(cidrhost(var.subnet_public_cidr, 0))
    error_message = "subnet_public_cidr must be a valid CIDR notation (e.g., 10.0.0.0/24)."
  }
}

variable "subnet_private_cidr" {
  type        = string
  description = "CIDR block para subnet privada (Functions)"
  default     = "10.0.1.0/24"

  validation {
    condition     = can(cidrhost(var.subnet_private_cidr, 0))
    error_message = "subnet_private_cidr must be a valid CIDR notation (e.g., 10.0.1.0/24)."
  }
}

variable "create_nat_gateway" {
  type        = bool
  description = "Criar NAT Gateway para egress das Functions"
  default     = true
}

variable "use_nsg" {
  type        = bool
  description = "Criar Network Security Groups"
  default     = true
}

# --- API Gateway ---

variable "api_gateway_name" {
  type        = string
  description = "Nome do API Gateway"
  default     = "apigw-serverless"
}

variable "api_gateway_endpoint_type" {
  type        = string
  description = "Tipo de endpoint: PUBLIC ou PRIVATE"
  default     = "PUBLIC"

  validation {
    condition     = contains(["PUBLIC", "PRIVATE"], var.api_gateway_endpoint_type)
    error_message = "api_gateway_endpoint_type must be PUBLIC or PRIVATE."
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
    error_message = "rate_limit_requests_per_second must be between 0 and 10000."
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

# --- Vault ---

variable "vault_key_protection_mode" {
  type        = string
  description = "Modo de proteção da chave KMS: SOFTWARE (dev) ou HSM (prod)"
  default     = "SOFTWARE"

  validation {
    condition     = contains(["SOFTWARE", "HSM"], var.vault_key_protection_mode)
    error_message = "vault_key_protection_mode must be SOFTWARE or HSM."
  }
}

# --- Event-Driven Pub/Sub (Pattern 02) — Streaming + Service Connector Hub ---

variable "streaming_use_cmek" {
  type        = bool
  description = "Se true, criptografa o Stream Pool com a KMS Key do módulo vault (CMEK). Default false = chave gerenciada pela Oracle."
  default     = false
}

# Service Connector Hub — batch tuning dos 2 connectors (target Functions).

variable "sch_batch_size_in_kbs" {
  type        = number
  description = "Batch size (KB) default dos connectors do SCH (target functions). Tunar p/ evitar cold-start storm vs latência. Máx 6000."
  default     = 128

  validation {
    condition     = var.sch_batch_size_in_kbs >= 1 && var.sch_batch_size_in_kbs <= 6000
    error_message = "sch_batch_size_in_kbs must be between 1 and 6000."
  }
}

variable "sch_batch_time_in_sec" {
  type        = number
  description = "Batch time (segundos) default dos connectors do SCH (target functions). Máx 600."
  default     = 60

  validation {
    condition     = var.sch_batch_time_in_sec >= 1 && var.sch_batch_time_in_sec <= 600
    error_message = "sch_batch_time_in_sec must be between 1 and 600."
  }
}

variable "notify_target_url" {
  type        = string
  description = "URL de destino do consumer notify (forward REST). Default = echo endpoint público."
  default     = "https://httpbin.org/post"

  validation {
    condition     = can(regex("^https?://", var.notify_target_url))
    error_message = "notify_target_url must be a valid http(s) URL."
  }
}

# --- REST Proxy (Pattern 01a) ---

variable "rest_proxy_store_source_base_url" {
  type        = string
  description = "URL base do sistema origem (RMS)"
  default     = "https://rex-npe.retail.sa-vinhedo-1.ocs.oraclecloud.com/rgbu-rex-brxs-par1-mfcs/RmsReSTServices"
}

variable "rest_proxy_store_destination_base_url" {
  type        = string
  description = "URL base do sistema destino (BrxServices)"
  default     = "http://129.148.63.45:8080/ords/brxoper/BrxServices/Store"
}

variable "rest_proxy_store_timeout_ms" {
  type        = string
  description = "Timeout em ms para chamadas REST"
  default     = "10000"
}

variable "rest_proxy_store_oauth_token_url" {
  type        = string
  description = "URL do token endpoint OAuth2"
  default     = "https://idcs-a23fd2fe5f18408c865bfc16a04cddb8.identity.oraclecloud.com/oauth2/v1/token"
}

variable "rest_proxy_store_oauth_scope" {
  type        = string
  description = "OAuth2 scope"
  default     = "rgbu:merch:MFCS-PAR1"
}

variable "rest_proxy_store_oauth_client_id" {
  type        = string
  description = "OAuth2 Client ID (armazenado no Vault)"
  sensitive   = true
  default     = ""
}

variable "rest_proxy_store_oauth_client_secret" {
  type        = string
  description = "OAuth2 Client Secret (armazenado no Vault)"
  sensitive   = true
  default     = ""
}

# --- General ---

variable "environment" {
  type        = string
  description = "Nome do ambiente"
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  type        = string
  description = "Nome do projeto"
  default     = "serverless"
}

variable "dashboard_viewers_all_users" {
  type        = bool
  description = "Concede leitura dos Management Dashboards a todos usuários humanos da tenancy."
  default     = true
}

variable "readonly_viewer_group_name" {
  type        = string
  description = "Grupo IAM read-only do compartment dev."
  default     = "grp-readonly-serverless-dev"
}

variable "readonly_viewer_user_ids" {
  type        = list(string)
  description = "OCIDs de usuários read-only do compartment dev."
  # claudio.parralego@brxretail.com
  default = ["ocid1.user.oc1..aaaaaaaamv2mjqjfcp4axnu3pbaco6gjv7pyayqpgn54td3tu7ycvaz6boha"]

  validation {
    condition     = alltrue([for u in var.readonly_viewer_user_ids : can(regex("^ocid1\\.user\\.", u))])
    error_message = "Cada readonly_viewer_user_ids deve ser um OCID de usuário (ocid1.user.*)."
  }
}

variable "freeform_tags" {
  type        = map(string)
  description = "Tags adicionais"
  default     = {}
}
