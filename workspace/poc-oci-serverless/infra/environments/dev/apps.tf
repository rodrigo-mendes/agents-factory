# ==============================================================================
# Environment: dev — Application Deployments
# ==============================================================================
# Each function gets its own Application via the function-app module.
# Routes are composed and passed to the API Gateway module.
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
    LOG_LEVEL        = "INFO"
    SERVICE_NAME     = "api-handler"
    ENVIRONMENT      = var.environment
    COMPARTMENT_OCID = var.compartment_ocid
    METRIC_NAMESPACE = "api_handler_analytics"
    APM_DOMAIN_URL   = module.apm.data_upload_endpoint
    APM_DATA_KEY     = module.apm.private_data_key
  }
  apm_domain_id           = module.apm.apm_domain_id
  function_shape          = var.function_shape
  provisioned_concurrency = 0
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
    ENVIRONMENT      = var.environment
    COMPARTMENT_OCID = var.compartment_ocid
    METRIC_NAMESPACE = "serverless_facade"
    LOG_LEVEL        = "INFO"
    SERVICE_NAME     = "func-api-facade"
    APM_DOMAIN_URL   = module.apm.data_upload_endpoint
    APM_DATA_KEY     = module.apm.private_data_key
  }
  apm_domain_id           = module.apm.apm_domain_id
  function_shape          = var.function_shape
  provisioned_concurrency = 0
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
    ENVIRONMENT                    = var.environment
    COMPARTMENT_OCID               = var.compartment_ocid
    METRIC_NAMESPACE               = "rest_proxy_analytics"
    STORE_SOURCE_BASE_URL          = var.rest_proxy_store_source_base_url
    STORE_DESTINATION_BASE_URL     = var.rest_proxy_store_destination_base_url
    STORE_TIMEOUT_MS               = var.rest_proxy_store_timeout_ms
    STORE_OAUTH_TOKEN_URL          = var.rest_proxy_store_oauth_token_url
    STORE_OAUTH_SCOPE              = var.rest_proxy_store_oauth_scope
    LOG_LEVEL                      = "INFO"
    SERVICE_NAME                   = "func-rr-rest-proxy"
    STORE_OAUTH_CLIENT_ID_OCID     = length(oci_vault_secret.rest_proxy_oauth_client_id) > 0 ? oci_vault_secret.rest_proxy_oauth_client_id[0].id : ""
    STORE_OAUTH_CLIENT_SECRET_OCID = length(oci_vault_secret.rest_proxy_oauth_client_secret) > 0 ? oci_vault_secret.rest_proxy_oauth_client_secret[0].id : ""
    APM_DOMAIN_URL                 = module.apm.data_upload_endpoint
    APM_DATA_KEY                   = module.apm.private_data_key
  }
  apm_domain_id           = module.apm.apm_domain_id
  function_shape          = var.function_shape
  provisioned_concurrency = 0
  trace_enabled           = var.trace_enabled
  environment             = var.environment
  tags                    = local.tags

  depends_on = [module.iam]
}

# ------------------------------------------------------------------------------
# Function App: func-event-producer (Pattern 02 — Event-Driven Pub/Sub)
# ------------------------------------------------------------------------------
# Recebe POST /v1/events (JWT) → monta DomainEvent (com trace injetado) →
# PutMessages no Stream event-stream. Config STREAM_* consumida pelo código Java.

module "app_event_producer" {
  source = "../../modules/function-app"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_private_id
  nsg_ids          = var.use_nsg ? [module.network.nsg_functions_id] : []

  application_name   = "app-event-producer"
  function_name      = "func-event-producer"
  function_image     = var.event_producer_image
  memory_in_mbs      = 256
  timeout_in_seconds = 60
  function_config = {
    ENVIRONMENT              = var.environment
    COMPARTMENT_OCID         = var.compartment_ocid
    METRIC_NAMESPACE         = "event_pubsub_analytics"
    LOG_LEVEL                = "INFO"
    SERVICE_NAME             = "func-event-producer"
    APM_DOMAIN_URL           = module.apm.data_upload_endpoint
    APM_DATA_KEY             = module.apm.private_data_key
    STREAM_OCID              = module.streaming.stream_id
    STREAM_MESSAGES_ENDPOINT = module.streaming.messages_endpoint
  }
  apm_domain_id           = module.apm.apm_domain_id
  function_shape          = var.function_shape
  provisioned_concurrency = 0
  trace_enabled           = var.trace_enabled
  environment             = var.environment
  tags                    = local.tags

  depends_on = [module.iam]
}

# ------------------------------------------------------------------------------
# Function App: func-evt-consumer-notify (Pattern 02 — consumer notify)
# ------------------------------------------------------------------------------
# ConnectorHubFunction target do SCH sch-event-notify. Recebe o batch do stream,
# extrai o traceparent do envelope (span CONSUMER re-parented) e faz forward REST
# p/ NOTIFY_TARGET_URL. Memória 1024 / timeout 300 / PC 0 (pay-per-use).

module "app_evt_consumer_notify" {
  source = "../../modules/function-app"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_private_id
  nsg_ids          = var.use_nsg ? [module.network.nsg_functions_id] : []

  application_name   = "app-evt-consumer-notify"
  function_name      = "func-evt-consumer-notify"
  function_image     = var.evt_consumer_notify_image
  memory_in_mbs      = 1024
  timeout_in_seconds = 300
  function_config = {
    ENVIRONMENT       = var.environment
    COMPARTMENT_OCID  = var.compartment_ocid
    METRIC_NAMESPACE  = "event_pubsub_analytics"
    LOG_LEVEL         = "INFO"
    SERVICE_NAME      = "func-evt-consumer-notify"
    APM_DOMAIN_URL    = module.apm.data_upload_endpoint
    APM_DATA_KEY      = module.apm.private_data_key
    NOTIFY_TARGET_URL = var.notify_target_url
  }
  apm_domain_id           = module.apm.apm_domain_id
  function_shape          = var.function_shape
  provisioned_concurrency = 0
  trace_enabled           = var.trace_enabled
  environment             = var.environment
  tags                    = local.tags

  depends_on = [module.iam]
}

# ------------------------------------------------------------------------------
# Function App: func-evt-consumer-audit (Pattern 02 — consumer audit)
# ------------------------------------------------------------------------------
# ConnectorHubFunction target do SCH sch-event-audit. Log/persist + métricas
# custom (AuditEventProcessed, EventConsumeLagMs) no namespace event_pubsub_analytics.
# Memória 1024 / timeout 300 / PC 0 (pay-per-use).

module "app_evt_consumer_audit" {
  source = "../../modules/function-app"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_private_id
  nsg_ids          = var.use_nsg ? [module.network.nsg_functions_id] : []

  application_name   = "app-evt-consumer-audit"
  function_name      = "func-evt-consumer-audit"
  function_image     = var.evt_consumer_audit_image
  memory_in_mbs      = 1024
  timeout_in_seconds = 300
  function_config = {
    ENVIRONMENT      = var.environment
    COMPARTMENT_OCID = var.compartment_ocid
    METRIC_NAMESPACE = "event_pubsub_analytics"
    LOG_LEVEL        = "INFO"
    SERVICE_NAME     = "func-evt-consumer-audit"
    APM_DOMAIN_URL   = module.apm.data_upload_endpoint
    APM_DATA_KEY     = module.apm.private_data_key
  }
  apm_domain_id           = module.apm.apm_domain_id
  function_shape          = var.function_shape
  provisioned_concurrency = 0
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
# API Gateway — Routing all functions
# ------------------------------------------------------------------------------

module "api_gateway" {
  source = "../../modules/api-gateway"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_public_id
  nsg_ids          = var.use_nsg ? [module.network.nsg_apigw_id] : []

  route_backends = [
    # api-handler routes
    {
      path        = "/hello"
      methods     = ["GET", "POST"]
      function_id = module.app_api_handler.function_id
      auth_type   = "ANONYMOUS"
    },
    {
      path        = "/handler/health"
      methods     = ["GET"]
      function_id = module.app_api_handler.function_id
      auth_type   = "ANONYMOUS"
    },
    # api-facade routes
    {
      path        = "/facade/hello"
      methods     = ["GET", "POST"]
      function_id = module.app_api_facade.function_id
      auth_type   = "ANONYMOUS"
    },
    {
      path        = "/facade/health"
      methods     = ["GET"]
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
    # rest-proxy routes
    {
      path        = "/proxy/health"
      methods     = ["GET"]
      function_id = module.app_rest_proxy.function_id
      auth_type   = "ANONYMOUS"
    },
    {
      path        = "/proxy/item/webhook"
      methods     = ["POST"]
      function_id = module.app_rest_proxy.function_id
      auth_type   = "ANONYMOUS"
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
    # event-producer route (Pattern 02 — Event-Driven Pub/Sub) → POST /v1/events
    {
      path        = "/events"
      methods     = ["POST"]
      function_id = module.app_event_producer.function_id
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
