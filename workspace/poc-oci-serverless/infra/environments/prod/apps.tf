# ==============================================================================
# Environment: prod — Application Deployments
# ==============================================================================

# ------------------------------------------------------------------------------
# Function App: api-handler
# ------------------------------------------------------------------------------

module "app_api_handler" {
  source = "../../modules/function-app"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_private_id
  nsg_ids          = var.use_nsg ? [module.network.nsg_functions_id] : []

  application_name   = "app-api-handler"
  function_name      = "api-handler"
  function_image     = var.api_handler_image
  memory_in_mbs      = 256
  timeout_in_seconds = 60
  function_config = {
    LOG_LEVEL    = "WARN"
    SERVICE_NAME = "api-handler"
  }
  function_shape          = var.function_shape
  provisioned_concurrency = var.provisioned_concurrency
  trace_enabled           = var.trace_enabled
  environment             = var.environment
  tags                    = local.tags

  depends_on = [module.iam]
}

# ------------------------------------------------------------------------------
# Function App: func-api-facade
# ------------------------------------------------------------------------------

module "app_api_facade" {
  source = "../../modules/function-app"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_private_id
  nsg_ids          = var.use_nsg ? [module.network.nsg_functions_id] : []

  application_name   = "app-api-facade"
  function_name      = "func-api-facade"
  function_image     = var.api_facade_image
  memory_in_mbs      = 256
  timeout_in_seconds = 60
  function_config = {
    COMPARTMENT_OCID = var.compartment_ocid
    METRIC_NAMESPACE = "serverless_facade"
  }
  function_shape          = var.function_shape
  provisioned_concurrency = var.provisioned_concurrency
  trace_enabled           = var.trace_enabled
  environment             = var.environment
  tags                    = local.tags

  depends_on = [module.iam]
}

# ------------------------------------------------------------------------------
# Function App: func-rr-rest-proxy
# ------------------------------------------------------------------------------

module "app_rest_proxy" {
  source = "../../modules/function-app"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_private_id
  nsg_ids          = var.use_nsg ? [module.network.nsg_functions_id] : []

  application_name   = "app-rest-proxy"
  function_name      = "func-rr-rest-proxy"
  function_image     = var.rest_proxy_image
  memory_in_mbs      = 256
  timeout_in_seconds = 60
  function_config = {
    STORE_SOURCE_BASE_URL          = var.rest_proxy_store_source_base_url
    STORE_DESTINATION_BASE_URL     = var.rest_proxy_store_destination_base_url
    STORE_TIMEOUT_MS               = var.rest_proxy_store_timeout_ms
    STORE_OAUTH_TOKEN_URL          = var.rest_proxy_store_oauth_token_url
    STORE_OAUTH_SCOPE              = var.rest_proxy_store_oauth_scope
    STORE_OAUTH_CLIENT_ID_OCID     = length(oci_vault_secret.rest_proxy_oauth_client_id) > 0 ? oci_vault_secret.rest_proxy_oauth_client_id[0].id : ""
    STORE_OAUTH_CLIENT_SECRET_OCID = length(oci_vault_secret.rest_proxy_oauth_client_secret) > 0 ? oci_vault_secret.rest_proxy_oauth_client_secret[0].id : ""
  }
  function_shape          = var.function_shape
  provisioned_concurrency = var.provisioned_concurrency
  trace_enabled           = var.trace_enabled
  environment             = var.environment
  tags                    = local.tags

  depends_on = [module.iam]
}

# ------------------------------------------------------------------------------
# Vault Secrets — OAuth Credentials for REST Proxy
# ------------------------------------------------------------------------------

resource "oci_vault_secret" "rest_proxy_oauth_client_id" {
  count = var.rest_proxy_store_oauth_client_id != "" ? 1 : 0

  compartment_id = var.compartment_ocid
  vault_id       = module.vault.vault_id
  key_id         = module.vault.key_id
  secret_name    = "rest-proxy-oauth-client-id-${var.environment}"

  secret_content {
    content_type = "BASE64"
    content      = base64encode(var.rest_proxy_store_oauth_client_id)
  }

  freeform_tags = local.tags

  lifecycle {
    ignore_changes = [secret_content]
  }
}

resource "oci_vault_secret" "rest_proxy_oauth_client_secret" {
  count = var.rest_proxy_store_oauth_client_secret != "" ? 1 : 0

  compartment_id = var.compartment_ocid
  vault_id       = module.vault.vault_id
  key_id         = module.vault.key_id
  secret_name    = "rest-proxy-oauth-client-secret-${var.environment}"

  secret_content {
    content_type = "BASE64"
    content      = base64encode(var.rest_proxy_store_oauth_client_secret)
  }

  freeform_tags = local.tags

  lifecycle {
    ignore_changes = [secret_content]
  }
}

# ------------------------------------------------------------------------------
# API Gateway
# ------------------------------------------------------------------------------

module "api_gateway" {
  source = "../../modules/api-gateway"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_public_id
  nsg_ids          = var.use_nsg ? [module.network.nsg_apigw_id] : []

  route_backends = [
    {
      path        = "/hello"
      methods     = ["GET", "POST"]
      function_id = module.app_api_handler.function_id
      auth_type   = "ANONYMOUS"
    },
    {
      path        = "/facade/hello"
      methods     = ["GET", "POST"]
      function_id = module.app_api_facade.function_id
      auth_type   = "ANONYMOUS"
    },
    {
      path        = "/facade/secret"
      methods     = ["POST"]
      function_id = module.app_api_facade.function_id
      auth_type   = "AUTHENTICATION_ONLY"
    },
    {
      path        = "/facade/store"
      methods     = ["POST"]
      function_id = module.app_api_facade.function_id
      auth_type   = "AUTHENTICATION_ONLY"
    },
    {
      path        = "/proxy/store/create"
      methods     = ["POST"]
      function_id = module.app_rest_proxy.function_id
      auth_type   = "AUTHENTICATION_ONLY"
    },
    {
      path        = "/proxy/store/update"
      methods     = ["POST"]
      function_id = module.app_rest_proxy.function_id
      auth_type   = "AUTHENTICATION_ONLY"
    },
  ]

  gateway_name                   = var.api_gateway_name
  endpoint_type                  = var.api_gateway_endpoint_type
  deployment_path_prefix         = var.deployment_path_prefix
  rate_limit_requests_per_second = var.rate_limit_requests_per_second
  cors_allowed_origins           = var.cors_allowed_origins
  jwt_auth_enabled               = var.jwt_auth_enabled
  jwt_issuers                    = var.jwt_issuers
  jwt_audiences                  = var.jwt_audiences
  jwt_jwks_uri                   = var.jwt_jwks_uri
  environment                    = var.environment
  project_name                   = var.project_name
  tags                           = local.tags

  depends_on = [module.iam]
}
