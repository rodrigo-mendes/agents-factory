# ==============================================================================
# Module: API Gateway
# ==============================================================================
# OCI API Gateway + Deployment com JWT, CORS, Rate Limiting
# Routes definidas via route_backends (per-route function targeting)
# ==============================================================================

resource "oci_apigateway_gateway" "this" {
  compartment_id             = var.compartment_ocid
  endpoint_type              = var.endpoint_type
  subnet_id                  = var.subnet_id
  display_name               = "${var.gateway_name}-${var.environment}"
  network_security_group_ids = var.nsg_ids

  freeform_tags = var.tags
}

resource "oci_apigateway_deployment" "this" {
  compartment_id = var.compartment_ocid
  gateway_id     = oci_apigateway_gateway.this.id
  path_prefix    = var.deployment_path_prefix
  display_name   = "api-${var.project_name}-${var.environment}"

  lifecycle {
    precondition {
      condition     = length(var.route_backends) > 0
      error_message = "route_backends deve conter pelo menos uma rota."
    }
    precondition {
      condition     = !var.jwt_auth_enabled || (var.jwt_jwks_uri != "" && can(regex("^https://", var.jwt_jwks_uri)))
      error_message = "jwt_jwks_uri é obrigatório e deve começar com https:// quando jwt_auth_enabled = true."
    }
  }

  specification {
    logging_policies {
      access_log {
        is_enabled = true
      }
      execution_log {
        is_enabled = true
        log_level  = var.environment == "prod" ? "ERROR" : "INFO"
      }
    }

    request_policies {
      dynamic "authentication" {
        for_each = var.jwt_auth_enabled ? [1] : []
        content {
          type                        = "JWT_AUTHENTICATION"
          token_header                = "Authorization"
          token_auth_scheme           = "Bearer"
          issuers                     = var.jwt_issuers
          audiences                   = var.jwt_audiences
          is_anonymous_access_allowed = true
          max_clock_skew_in_seconds   = 60

          public_keys {
            type                        = "REMOTE_JWKS"
            uri                         = var.jwt_jwks_uri
            max_cache_duration_in_hours = 24
            is_ssl_verify_disabled      = false
          }
        }
      }

      dynamic "rate_limiting" {
        for_each = var.rate_limit_requests_per_second > 0 ? [1] : []
        content {
          rate_in_requests_per_second = var.rate_limit_requests_per_second
          rate_key                    = "CLIENT_IP"
        }
      }

      dynamic "cors" {
        for_each = length(var.cors_allowed_origins) > 0 ? [1] : []
        content {
          allowed_origins              = var.cors_allowed_origins
          allowed_methods              = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
          allowed_headers              = ["Content-Type", "Authorization"]
          is_allow_credentials_enabled = true
          max_age_in_seconds           = 3600
        }
      }
    }

    dynamic "routes" {
      for_each = var.route_backends
      content {
        path    = routes.value.path
        methods = routes.value.methods

        backend {
          type        = "ORACLE_FUNCTIONS_BACKEND"
          function_id = routes.value.function_id
        }

        dynamic "request_policies" {
          for_each = var.jwt_auth_enabled && routes.value.auth_type != "ANONYMOUS" ? [1] : []
          content {
            authorization {
              type = routes.value.auth_type
            }
          }
        }
      }
    }

    # Health check route (sempre anônimo)
    routes {
      path    = "/health"
      methods = ["GET"]

      backend {
        type   = "STOCK_RESPONSE_BACKEND"
        status = 200
        body   = jsonencode({ status = "healthy", environment = var.environment })

        headers {
          name  = "Content-Type"
          value = "application/json"
        }
      }

      dynamic "request_policies" {
        for_each = var.jwt_auth_enabled ? [1] : []
        content {
          authorization {
            type = "ANONYMOUS"
          }
        }
      }
    }
  }

  freeform_tags = var.tags
}
