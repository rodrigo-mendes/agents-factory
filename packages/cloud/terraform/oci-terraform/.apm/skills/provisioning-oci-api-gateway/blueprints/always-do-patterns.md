### ✅ Always Do

## Contents
1. Provider Version Constraint
2. Gateway Resource with NSG and Tags
3. Deployment with JWT Authentication, CORS, and Rate Limiting
4. Variable Validation with OCID Regex
5. IAM Dependencies with depends_on

---

**Provider Version Constraint**: Lock the OCI provider to a tested range to prevent breaking changes on API Gateway resources.

```hcl
# ✅ CORRECT: Constrained provider version for API Gateway stability (OCI Provider v6.x+)
terraform {
  required_version = ">= 1.7"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0, < 9.0"
    }
  }

  # Production: remote state with encryption
  backend "s3" {
    bucket                      = "terraform-state-prod"
    key                         = "apigateway/prod/terraform.tfstate"
    region                      = "sa-saopaulo-1"
    endpoint                    = "https://<namespace>.compat.objectstorage.sa-saopaulo-1.oraclecloud.com"
    encrypt                     = true
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    force_path_style            = true
  }
}

# ✅ CORRECT: Credentials via env vars or OCI config — NEVER hardcoded (OCI Provider v6.x+)
provider "oci" {
  region = var.region
  # Reads from: ~/.oci/config (dev), env vars (CI/CD), Instance/Resource Principal (OCI)
}
```
**Why it is mandatory**: API Gateway resources manage public-facing endpoints. Uncontrolled provider upgrades may silently change deployment behavior or policy validation.
**Failure if omitted**: `terraform init` could pull an incompatible provider version, breaking gateway configurations.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs

---

**Gateway Resource with NSG and Tags**: Gateway is the public entry point — Network Security Groups restrict traffic to HTTPS (443) only. Tags are required for cost tracking and compliance.

```hcl
# ✅ CORRECT: API Gateway with NSG restriction and tags (OCI Provider v6.x+)
resource "oci_apigateway_gateway" "this" {
  compartment_id             = var.compartment_ocid
  endpoint_type              = var.endpoint_type  # "PUBLIC" or "PRIVATE"
  subnet_id                  = var.public_subnet_id
  display_name               = "${var.gateway_name}-${var.environment}"
  network_security_group_ids = var.nsg_ids

  freeform_tags = local.tags

  lifecycle {
    # Prevent accidental deletion of production gateway
    prevent_destroy = var.environment == "prod"
  }
}

locals {
  tags = merge(var.freeform_tags, {
    "Environment" = var.environment
    "Project"     = var.project_name
    "ManagedBy"   = "terraform"
  })
}
```
**Why it is mandatory**: Without NSG, the gateway subnet is open to all traffic. Without tags, resources are invisible to cost tracking and auditability.
**Failure if omitted**: Unauthorized port access; unattributable cloud costs; compliance violations.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apigateway_gateway

---

**Deployment with JWT Authentication, CORS, and Rate Limiting**: Cross-cutting concerns MUST be applied at the deployment level (not per-route) for complete coverage. Rate limiting prevents DDoS and cost explosion. JWT validates tokens at the edge (fail-fast).

```hcl
# ✅ CORRECT: Deployment with all cross-cutting policies (OCI Provider v6.x+)
resource "oci_apigateway_deployment" "this" {
  compartment_id = var.compartment_ocid
  gateway_id     = oci_apigateway_gateway.this.id
  path_prefix    = var.deployment_path_prefix
  display_name   = "api-${var.project_name}-${var.environment}"

  specification {
    # ✅ Logging — mandatory for observability
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
      # ✅ JWT Authentication at deployment level (OCI Provider v6.x+)
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
            is_ssl_verify_disabled      = false  # NEVER disable — prevents MITM
          }
        }
      }

      # ✅ Rate Limiting — prevents DDoS and cost explosion (OCI Provider v6.x+)
      dynamic "rate_limiting" {
        for_each = var.rate_limit_requests_per_second > 0 ? [1] : []
        content {
          rate_in_requests_per_second = var.rate_limit_requests_per_second
          rate_key                    = "CLIENT_IP"
        }
      }

      # ✅ CORS — required for browser-based consumers
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

    # ✅ Business routes with per-route function backends
    dynamic "routes" {
      for_each = var.route_backends
      content {
        path    = routes.value.path
        methods = routes.value.methods

        backend {
          type        = "ORACLE_FUNCTIONS_BACKEND"
          function_id = routes.value.function_id
        }

        request_policies {
          authorization {
            type = try(routes.value.auth_type, var.jwt_auth_enabled ? "AUTHENTICATION_ONLY" : "ANONYMOUS")
          }
        }
      }
    }

    # ✅ Health check route — always anonymous
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

      request_policies {
        authorization {
          type = "ANONYMOUS"
        }
      }
    }
  }

  freeform_tags = local.tags
}
```
**Why it is mandatory**: Rate limiting prevents cost explosion (Functions are billed per invocation). JWT at deployment level ensures no route is accidentally unprotected. Logging is the only way to diagnose API issues.
**Failure if omitted**: DDoS causes unbounded Function invocations and cost; unprotected routes allow unauthorized access; no logs means blind debugging.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apigateway_deployment

---

**Variable Validation with OCID Regex**: Prevent misconfiguration errors at plan-time (before apply) by validating OCI-specific formats.

```hcl
# ✅ CORRECT: Validate OCIDs and OCI-specific constraints at plan-time (Terraform >= 1.7)
variable "compartment_ocid" {
  type        = string
  description = "OCID of the compartment for API Gateway resources"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid must be a valid compartment OCID (ocid1.compartment.*)."
  }
}

variable "api_gateway_endpoint_type" {
  type        = string
  description = "Gateway endpoint type: PUBLIC or PRIVATE"
  default     = "PUBLIC"

  validation {
    condition     = contains(["PUBLIC", "PRIVATE"], var.api_gateway_endpoint_type)
    error_message = "api_gateway_endpoint_type must be PUBLIC or PRIVATE."
  }
}

variable "rate_limit_requests_per_second" {
  type        = number
  description = "Rate limit in requests per second (0 = disabled)"
  default     = 100

  validation {
    condition     = var.rate_limit_requests_per_second >= 0 && var.rate_limit_requests_per_second <= 10000
    error_message = "rate_limit_requests_per_second must be between 0 and 10000."
  }
}

variable "route_backends" {
  type = list(object({
    path        = string
    methods     = list(string)
    function_id = string
    auth_type   = optional(string, "AUTHENTICATION_ONLY")
  }))
  description = "List of route backends with per-route function targeting"
  # Required — no default

  validation {
    condition     = alltrue([for r in var.route_backends : can(regex("^/", r.path))])
    error_message = "All route paths must start with /."
  }

  validation {
    condition = alltrue([
      for r in var.route_backends : alltrue([
        for m in r.methods : contains(["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"], m)
      ])
    ])
    error_message = "Methods must be valid HTTP methods: GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD."
  }
}
```
**Why it is mandatory**: OCIDs have a fixed format. Catching invalid values at plan-time prevents wasted apply cycles and cryptic OCI API errors.
**Failure if omitted**: `terraform apply` fails with unclear OCI API errors; misconfigured rate limits go undetected.
**Source**: https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules

---

**IAM Dependencies with depends_on**: API Gateway Deployments with Functions backends MUST explicitly depend on IAM policy resources. IAM policies take up to 60 seconds to propagate.

```hcl
# ✅ CORRECT: Explicit dependency on IAM before creating API Gateway (OCI Provider v6.x+)
module "api_gateway" {
  source = "./modules/api-gateway"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_public_id
  function_id      = module.functions.function_id
  nsg_ids          = [module.network.nsg_apigw_id]

  # Without this, Gateway may try to invoke Functions before the policy exists → 502
  depends_on = [module.iam]
}
```
**Why it is mandatory**: Without `depends_on`, Terraform may create the Gateway Deployment before IAM policies propagate, causing intermittent 502 Bad Gateway errors on all Function-backed routes.
**Failure if omitted**: Race condition — 502 errors on deployment until IAM propagation completes (~60s). In CI/CD, this causes flaky pipelines.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm

---

