# Terraform AWS API Gateway — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - API Gateway"
Cloud_Provider: "AWS"
Target_Service: "API Gateway (REST API v1 + HTTP/WebSocket API v2)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-28"
Domain_Complexity: "Complex"
New_V6_Resources_Noted: "ip_address_type dualstack, aws_api_gateway_domain_name_access_association, aws_apigatewayv2_routing_rule"
```

---

## Executive Summary

Amazon API Gateway is AWS's fully managed service for creating, publishing, securing, and monitoring REST, HTTP, and WebSocket APIs. Terraform manages it through two parallel namespaces: **API Gateway V1** (`aws_api_gateway_*`) for REST APIs and **API Gateway V2** (`aws_apigatewayv2_*`) for HTTP APIs and WebSocket APIs. The distinction is not cosmetic — they differ in pricing (~3.5x cost difference), feature sets (WAF, caching, and request validation exist only in V1), and underlying infrastructure. Choosing the wrong type for a production workload creates irreversible architectural debt that cannot be fixed by Terraform resource updates.

The AWS Provider v6.x introduces several critical changes relevant to API Gateway: `default_tags` propagation now covers all API Gateway resources (previously some were excluded), the `aws_api_gateway_account` resource no longer requires a destroy/recreate cycle when updating CloudWatch role ARN, and the `disable_execute_api_endpoint` attribute can now be set at creation time without a subsequent apply cycle. Provider constraint `~> 6.0` is recommended; the `>= 5.0, < 7.0` range is the minimum acceptable for compatibility without manual migration effort. Terraform `>= 1.7` is required for `terraform test` framework and enhanced import block support.

The three non-negotiable guardrails for any API Gateway deployment managed by Terraform: **(1) every method/route must declare an authorizer** — an `authorization = "NONE"` on a production method is a publicly-exploitable endpoint the moment the stage is deployed; **(2) `access_log_settings` and `xray_tracing_enabled` must be enabled on every stage** — without these, there is no forensic trail for security incidents or integration failures; **(3) `create_before_destroy = true` must be set on every `aws_api_gateway_deployment`** — without it, Terraform deletes the active deployment before creating the replacement, causing a production outage window. This service is classified **Complex** due to IAM, multi-resource dependency chains, security-critical authorization, and stateful deployment management.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Ensures reproducibility, prevents accidental provider upgrades that break API Gateway configuration, and defines the deployment contract for all team members and CI pipelines.

```hcl
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/api-gateway/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Terraform Settings Block](https://developer.hashicorp.com/terraform/language/settings) | [AWS Provider Registry](https://registry.terraform.io/providers/hashicorp/aws/latest)

---

#### Pattern: Provider Configuration with IAM Role Assumption and Default Tags

**Why**: Credentials must never be hardcoded. `assume_role` enables cross-account deployments and CI/CD pipelines without static credentials. `default_tags` enforces tagging compliance on all API Gateway resources without per-resource tag blocks.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "terraform-api-gateway-${var.environment}"
  }

  default_tags {
    tags = {
      Environment = var.environment
      Service     = "api-gateway"
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [AWS Provider Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference)

---

#### Pattern: REST API with Regional Endpoint and Managed Deployment Trigger

**Why**: The `triggers` block using `sha1(jsonencode(...))` is the official pattern to force a new deployment whenever the API configuration changes. Without it, Terraform will not create a new deployment when methods, integrations, or resources are updated — leaving the stage pointing to stale configuration. `create_before_destroy` prevents downtime.

```hcl
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.service_name}-${var.environment}"
  description = "REST API for ${var.service_name} in ${var.environment}"

  endpoint_configuration {
    types = ["REGIONAL"]
    # ip_address_type: "ipv4" (default) or "dualstack" (IPv4+IPv6 — added in provider v6.x)
    # For PRIVATE endpoint type, only "dualstack" is supported.
    # ip_address_type = "dualstack"
  }

  # Disable the default execute-api endpoint to force custom domain usage
  disable_execute_api_endpoint = var.enforce_custom_domain

  tags = {
    Name = "${var.service_name}-api-${var.environment}"
  }
}

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  # Trigger redeployment on any API config change
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.root.id,
      aws_api_gateway_method.root_get.id,
      aws_api_gateway_integration.root_get.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_api_gateway_rest_api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api) | [aws_api_gateway_deployment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_deployment)

---

#### Pattern: Stage with Access Logging, X-Ray Tracing, and Method-Level Settings

**Why**: Access logging and X-Ray are the only forensic tools available for API Gateway incidents. CloudWatch log group must be created with `depends_on` to prevent a race condition where API Gateway creates the log group before Terraform, causing a drift conflict on subsequent applies.

```hcl
resource "aws_cloudwatch_log_group" "api_gateway_access_logs" {
  name              = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.main.id}/${var.environment}"
  retention_in_days = 90

  tags = {
    Name = "api-gateway-access-logs-${var.environment}"
  }
}

resource "aws_api_gateway_stage" "main" {
  depends_on = [aws_cloudwatch_log_group.api_gateway_access_logs]

  rest_api_id   = aws_api_gateway_rest_api.main.id
  deployment_id = aws_api_gateway_deployment.main.id
  stage_name    = var.environment

  xray_tracing_enabled = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_access_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      sourceIp       = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      protocol       = "$context.protocol"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
      errorMessage   = "$context.error.message"
      authorizerError = "$context.authorizer.error"
    })
  }

  tags = {
    Name = "${var.service_name}-stage-${var.environment}"
  }
}

resource "aws_api_gateway_method_settings" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled        = true
    logging_level          = "INFO"
    data_trace_enabled     = false # Set true only for debugging, very verbose
    throttling_burst_limit = var.stage_throttle_burst
    throttling_rate_limit  = var.stage_throttle_rate
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_api_gateway_stage](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_stage) | [API Gateway Logging](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html)

---

#### Pattern: Authorization on Every Method (Never NONE in Production)

**Why**: `authorization = "NONE"` makes an endpoint publicly accessible with zero authentication. Every production method must declare an authorizer. Use Cognito for user-facing APIs, Lambda authorizer for custom auth, and IAM for service-to-service.

```hcl
# Cognito User Pool Authorizer (preferred for user-facing APIs)
resource "aws_api_gateway_authorizer" "cognito" {
  name            = "${var.service_name}-cognito-authorizer-${var.environment}"
  rest_api_id     = aws_api_gateway_rest_api.main.id
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [aws_cognito_user_pool.main.arn]

  # Cache authorization result for 300 seconds (5 minutes)
  authorizer_result_ttl_in_seconds = 300
}

# Method secured with Cognito
resource "aws_api_gateway_method" "items_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.items.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id

  request_parameters = {
    "method.request.header.Authorization" = true
  }
}

# Lambda TOKEN authorizer (for custom JWT/OAuth validation)
resource "aws_api_gateway_authorizer" "lambda_token" {
  name                   = "${var.service_name}-lambda-authorizer-${var.environment}"
  rest_api_id            = aws_api_gateway_rest_api.main.id
  type                   = "TOKEN"
  authorizer_uri         = aws_lambda_function.authorizer.invoke_arn
  authorizer_credentials = aws_iam_role.authorizer_invocation.arn

  identity_source                  = "method.request.header.Authorization"
  identity_validation_expression   = "^Bearer [-0-9a-zA-Z._]*$"
  authorizer_result_ttl_in_seconds = 300
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_api_gateway_authorizer](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_authorizer) | [API Gateway Authorization](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html)

---

#### Pattern: IAM Role for API Gateway CloudWatch Logging (Account-Level)

**Why**: API Gateway cannot write CloudWatch logs without an account-level IAM role configured in `aws_api_gateway_account`. This is a one-time account setup but must be managed by Terraform to prevent drift. Missing this silently disables all execution logging without an error at deployment time.

```hcl
data "aws_iam_policy_document" "api_gateway_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api_gateway_cloudwatch" {
  name               = "api-gateway-cloudwatch-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.api_gateway_assume_role.json

  tags = {
    Name = "api-gateway-cloudwatch-${var.environment}"
  }
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn

  depends_on = [aws_iam_role_policy_attachment.api_gateway_cloudwatch]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_api_gateway_account](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_account) | [Enable CloudWatch Logging](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html#set-up-access-logging-permissions)

---

#### Pattern: Variable Validation and Type Safety

**Why**: Catches invalid configurations at `terraform plan` time before any AWS API calls, preventing partial resource creation and state corruption from invalid inputs.

```hcl
variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  type        = string
  description = "AWS region for API Gateway deployment"
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "AWS region must be a valid region identifier (e.g., us-east-1, eu-west-1)."
  }
}

variable "stage_throttle_rate" {
  type        = number
  description = "Steady-state requests per second for the stage (account limit is 10000)"
  default     = 1000

  validation {
    condition     = var.stage_throttle_rate >= 1 && var.stage_throttle_rate <= 10000
    error_message = "Throttle rate must be between 1 and 10000 RPS (account limit)."
  }
}

variable "stage_throttle_burst" {
  type        = number
  description = "Maximum concurrent requests (burst) for the stage"
  default     = 2000

  validation {
    condition     = var.stage_throttle_burst >= 1 && var.stage_throttle_burst <= 5000
    error_message = "Throttle burst must be between 1 and 5000."
  }
}

variable "enforce_custom_domain" {
  type        = bool
  description = "Disable default execute-api endpoint and require custom domain"
  default     = false
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

#### Pattern: WAF Web ACL Association with REST API Stage

**Why**: WAF is the only mechanism to protect API Gateway from OWASP Top 10 attacks, IP-based blocking, rate limiting per IP, and geo-restriction. Only available for REST APIs (V1) — not HTTP APIs. Must be associated at the stage level, not the API level.

```hcl
resource "aws_wafv2_web_acl" "api_gateway" {
  name  = "${var.service_name}-api-waf-${var.environment}"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimitRule"
    priority = 2

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 1000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRuleMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.service_name}-api-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Name = "${var.service_name}-api-waf-${var.environment}"
  }
}

resource "aws_wafv2_web_acl_association" "api_gateway" {
  resource_arn = aws_api_gateway_stage.main.arn
  web_acl_arn  = aws_wafv2_web_acl.api_gateway.arn
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_wafv2_web_acl_association](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl_association) | [WAF with API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html)

---

#### Pattern: Lambda Permission for API Gateway Invocation

**Why**: Without the `aws_lambda_permission`, API Gateway cannot invoke the Lambda function and all requests will return `500 Internal Server Error`. The `source_arn` must include the stage, method, and path to follow least-privilege — do not use `*` in production.

```hcl
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke-${var.environment}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_handler.function_name
  principal     = "apigateway.amazonaws.com"

  # Least-privilege: restrict to specific API, stage, method, and path
  # Format: arn:aws:execute-api:region:account-id:api-id/stage/method/resource-path
  source_arn = "${aws_api_gateway_rest_api.main.execution_arn}/${var.environment}/GET/items"
}

# For Lambda authorizer invocation
resource "aws_iam_role" "authorizer_invocation" {
  name = "${var.service_name}-authorizer-invocation-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "apigateway.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "authorizer_invocation" {
  name = "invoke-authorizer-lambda"
  role = aws_iam_role.authorizer_invocation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = "lambda:InvokeFunction"
      Effect   = "Allow"
      Resource = aws_lambda_function.authorizer.arn
    }]
  })
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_lambda_permission](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | [API Gateway Lambda Integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html)

---

#### Pattern: Custom Domain Name with ACM Certificate

**Why**: The default `{api-id}.execute-api.{region}.amazonaws.com` endpoint leaks internal API IDs, cannot be cached at DNS layer, and breaks if the API is recreated. Custom domains with ACM provide stable URLs, TLS termination, and enable base path mapping for API versioning.

```hcl
resource "aws_acm_certificate" "api" {
  domain_name       = "api.${var.domain_name}"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "api-certificate-${var.environment}"
  }
}

resource "aws_api_gateway_domain_name" "main" {
  domain_name              = "api.${var.domain_name}"
  regional_certificate_arn = aws_acm_certificate.api.arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  security_policy = "TLS_1_2"

  tags = {
    Name = "api-domain-${var.environment}"
  }

  depends_on = [aws_acm_certificate_validation.api]
}

resource "aws_api_gateway_base_path_mapping" "v1" {
  api_id      = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  domain_name = aws_api_gateway_domain_name.main.domain_name
  base_path   = "v1"
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_api_gateway_domain_name](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_domain_name) | [Custom Domain Names](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html)

---

### ⚠️ Conditional Patterns

---

#### Decision: REST API (V1) vs. HTTP API (V2)

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **REST API (V1)** | Full feature set: WAF, caching, request validation, usage plans, resource policies, per-client throttling | Cost (~$3.50/million vs ~$1.00), complexity | External-facing APIs, B2B APIs, APIs requiring WAF/caching, compliance requirements |
| **HTTP API (V2)** | Cost (~70% cheaper), latency (~60% lower P50), simplicity, automatic deployments | No WAF, no API key usage plans, no response caching, no request body validation, no edge-optimized endpoints | Internal microservice routing, Lambda proxy with JWT auth, simple CRUD APIs with low traffic |

**Tradeoff Matrix**:

| Capability | REST API (V1) | HTTP API (V2) |
|------------|:---:|:---:|
| WAF Integration | ✅ | ❌ |
| Response Caching | ✅ | ❌ |
| Request Validation | ✅ | ❌ |
| Usage Plans / API Keys | ✅ | ❌ |
| Lambda Authorizer | ✅ | ✅ |
| JWT Authorizer (native) | ❌ | ✅ |
| Cognito Authorizer | ✅ | ✅ (JWT) |
| Private Integration (VPC Link) | ✅ (NLB) | ✅ (NLB+ALB) |
| OpenAPI Import | ✅ | ✅ |
| Canary Deployments | ✅ | ❌ |
| Pricing (per million requests) | ~$3.50 | ~$1.00 |

- **When**: Default to REST API for production external APIs. Use HTTP API only for internal service mesh routing or greenfield projects with explicit cost constraints.
- **Agent**: "Ask user: Is this API externally accessible? Does it require WAF protection, response caching, or per-client throttling?"
- **Source**: [Choosing REST or HTTP API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)

---

#### Decision: Local vs. Remote Backend for State

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Local** | Simplicity, offline dev | Sharing, locking, audit history, safety | Solo dev, PoC, learning |
| **S3 + DynamoDB** | Team sharing, state locking, audit, versioning | AWS dependency, bootstrap complexity | Team dev, production, CI/CD |
| **Terraform Cloud** | SaaS ease, policy enforcement, run history | Cost, vendor lock-in | Enterprise, distributed teams, Sentinel policies |

- **Agent**: "Ask user: Is this a team deployment? Is this production? Does your organization have a Terraform Cloud subscription?"
- **Source**: [Backend Configuration](https://developer.hashicorp.com/terraform/language/settings/backends/configuration)

---

#### Decision: OpenAPI Body Import vs. Individual Terraform Resources

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **OpenAPI `body` import** | Single source of truth, portable, API-first design, smaller TF state | Mixing concerns (OpenAPI + HCL), complex redeployment triggers | API-first workflows, OpenAPI-driven development, large APIs with many routes |
| **Individual `aws_api_gateway_*` resources** | Full Terraform state tracking, drift detection, fine-grained `depends_on` | Large state files, complex dependency ordering, verbose HCL | Terraform-first teams, small APIs (< 10 routes), auditable resource-level changes |

**Critical Note**: When using `body` import, set `put_rest_api_mode = "merge"` to prevent deletion of configurations not explicitly defined in the OpenAPI spec. Do NOT manage `aws_api_gateway_resource`, `aws_api_gateway_method`, etc., as separate resources when using `body` — they will conflict.

- **Agent**: "Ask user: Does your team have an existing OpenAPI specification? Is the API defined API-first or infrastructure-first?"
- **Source**: [OpenAPI Import](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-import-api.html)

---

#### Decision: Usage Plan Throttling Strategy

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Account-level only** | Simplicity | No per-client control | Internal APIs, single-tenant |
| **Stage-level throttling** | Per-environment limits | No per-client differentiation | Multi-env with identical consumers |
| **Usage Plans + API Keys** | Per-client/tier throttling and quotas | Operational overhead (key management) | B2B APIs, multi-tier products, partner integrations |

- **Agent**: "Ask user: Do you need to rate-limit individual API consumers differently? Is this a multi-tenant or B2B API?"
- **Source**: [API Gateway Throttling](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html)

---

#### Decision: VPC Link (Private Integration) vs. Public Lambda Integration

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Public Lambda** | Simplicity, no VPC dependency | All traffic traverses public AWS network | Serverless-first architectures, non-sensitive data |
| **VPC Link + NLB** | Private connectivity, no internet egress for backend | NLB cost, VPC design complexity | ECS/EC2 backends, compliance requirements, PCI/HIPAA |

- **Agent**: "Ask user: Is your backend service in a VPC? Does your compliance policy require that API-to-backend traffic stays within the AWS network?"
- **Source**: [VPC Link](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-private-integration.html)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: `authorization = "NONE"` on Production Methods

```hcl
# DON'T — publicly exploitable endpoint
resource "aws_api_gateway_method" "items" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.items.id
  http_method   = "GET"
  authorization = "NONE"  # ← NEVER in production
}
```

**Why**: Any internet user can call this endpoint. API Gateway does not require authentication for `NONE` methods. The endpoint is live the moment the stage is deployed.

```hcl
# DO — require Cognito authorization
resource "aws_api_gateway_method" "items" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.items.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}
```

- **Impact**: CRITICAL — Unauthorized data access, API abuse, data exfiltration
- **Severity**: CRITICAL
- **Source**: [API Gateway Access Control](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html)

---

#### Anti-Pattern: Deployment Without `create_before_destroy`

```hcl
# DON'T — causes production outage during redeployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  # No lifecycle block
}
```

**Why**: Without `create_before_destroy`, Terraform deletes the existing deployment before creating the new one. Since the stage points to the deployment, this creates a window where the stage has no valid deployment and all API calls return 500.

```hcl
# DO
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([...]))
  }

  lifecycle {
    create_before_destroy = true
  }
}
```

- **Impact**: HIGH — Production outage during every deployment
- **Severity**: HIGH
- **Source**: [aws_api_gateway_deployment lifecycle](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_deployment)

---

#### Anti-Pattern: Stage Without Throttling Configuration

```hcl
# DON'T — no throttling allows a single client to exhaust account quota
resource "aws_api_gateway_method_settings" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled = true
    logging_level   = "INFO"
    # No throttling_burst_limit or throttling_rate_limit
  }
}
```

**Why**: Default account-level throttling is 10,000 RPS. A single misconfigured client or attack can consume the entire quota, causing throttling for all other APIs in the account/region.

```hcl
# DO — always set explicit throttle limits
resource "aws_api_gateway_method_settings" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled        = true
    logging_level          = "INFO"
    throttling_burst_limit = 500
    throttling_rate_limit  = 100
  }
}
```

- **Impact**: HIGH — Account-wide API throttling, cascading service failures
- **Severity**: HIGH
- **Source**: [API Gateway Throttling](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html)

---

#### Anti-Pattern: Hardcoded Credentials in Provider Block

```hcl
# DON'T
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"           # ← NEVER
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfi"  # ← NEVER
  region     = "us-east-1"
}
```

**Why**: Credentials stored in code are committed to version control history and are exposed to any team member, CI system, or attacker with repository access.

```hcl
# DO — use IAM role assumption or environment variables
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
  }
}
# Credentials supplied via:
# - AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY env vars (CI)
# - IAM Instance Profile / ECS Task Role (compute)
# - AWS SSO / aws-vault (developer workstations)
```

- **Impact**: CRITICAL — Full AWS account compromise
- **Severity**: CRITICAL
- **Source**: [AWS Security Best Practices](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)

---

#### Anti-Pattern: Missing State File Encryption

```hcl
# DON'T
backend "s3" {
  bucket = "my-tf-state"
  key    = "api-gateway/terraform.tfstate"
  region = "us-east-1"
  # No encrypt = true — state contains IAM credentials, API keys, and resource details
}
```

```hcl
# DO
backend "s3" {
  bucket         = "my-org-terraform-state"
  key            = "prod/api-gateway/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-locks"
  kms_key_id     = "arn:aws:kms:us-east-1:123456789:key/mrk-abc123"  # Optional CMK
}
```

- **Impact**: CRITICAL — Complete infrastructure and secrets exposure via state file
- **Severity**: CRITICAL
- **Source**: [Terraform State Security](https://developer.hashicorp.com/terraform/language/state/sensitive-data)

---

#### Anti-Pattern: Using API Keys as the Sole Security Mechanism

```hcl
# DON'T — API keys are identifiers, NOT authenticators
resource "aws_api_gateway_method" "items" {
  rest_api_id      = aws_api_gateway_rest_api.main.id
  resource_id      = aws_api_gateway_resource.items.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true  # ← This alone does NOT authenticate the caller
}
```

**Why**: API keys can be easily shared, leaked via logs, or brute-forced. They are identifiers for usage tracking and throttling, not authentication tokens.

```hcl
# DO — combine API keys with a proper authorizer
resource "aws_api_gateway_method" "items" {
  rest_api_id      = aws_api_gateway_rest_api.main.id
  resource_id      = aws_api_gateway_resource.items.id
  http_method      = "GET"
  authorization    = "COGNITO_USER_POOLS"
  authorizer_id    = aws_api_gateway_authorizer.cognito.id
  api_key_required = true  # For usage tracking on top of proper auth
}
```

- **Impact**: HIGH — Unauthorized API access, data exposure
- **Severity**: HIGH
- **Source**: [API Gateway API Keys](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html)

---

#### Anti-Pattern: `data_trace_enabled = true` in Production

```hcl
# DON'T in production
settings {
  data_trace_enabled = true  # Logs full request/response body to CloudWatch
}
```

**Why**: `data_trace_enabled` logs the full request and response body to CloudWatch Execution Logs. This captures PII, authentication tokens, and sensitive payloads in plain text in CloudWatch, violating GDPR, HIPAA, and PCI-DSS requirements.

```hcl
# DO — use access logs format to capture only metadata
settings {
  metrics_enabled    = true
  logging_level      = "INFO"
  data_trace_enabled = false  # Never true in production
}
```

- **Impact**: CRITICAL — PII/sensitive data exposure in logs, compliance violation
- **Severity**: CRITICAL
- **Source**: [API Gateway Logging](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html)

---

#### Anti-Pattern: No `depends_on` for CloudWatch Log Group

```hcl
# DON'T — race condition causes drift
resource "aws_api_gateway_stage" "main" {
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
  }
  # No depends_on — API Gateway may create the log group first
}
```

```hcl
# DO
resource "aws_api_gateway_stage" "main" {
  depends_on = [aws_cloudwatch_log_group.api_logs]

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
  }
}
```

- **Impact**: MEDIUM — State drift, inconsistent log group retention settings
- **Severity**: MEDIUM
- **Source**: [aws_api_gateway_stage example](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_stage#managing-the-api-logging-cloudwatch-log-group)

---

## State Management Deep Dive

### Local Development State

```hcl
# For learning/dev only — NOT for team/production use
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  # No backend block = local state
}
```

- **Risk**: No locking, no sharing, single point of failure, state in working directory
- **When**: Solo exploration, Terratest environments (with cleanup), local scratch work

---

### Production Remote State (S3 + DynamoDB)

```hcl
# One-time bootstrap (run separately from main Terraform configuration)
resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-org-terraform-state"

  lifecycle {
    prevent_destroy = true  # Protects against accidental state bucket deletion
  }

  tags = {
    Name      = "terraform-state"
    ManagedBy = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name      = "terraform-locks"
    ManagedBy = "terraform"
  }
}
```

**Backend config for API Gateway state**:

```hcl
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/api-gateway/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
    kms_key_id     = "arn:aws:kms:us-east-1:123456789:key/mrk-abc123"
  }
}
```

- **Scenario**: Production remote state (team dev, CI/CD)
- **Backend**: S3 + DynamoDB
- **Locking**: DynamoDB `LockID` attribute
- **Encryption**: KMS CMK (recommended) or AES256
- **Source**: [S3 Backend](https://developer.hashicorp.com/terraform/language/settings/backends/s3)

---

### State File Sensitivity Handling

```hcl
# API Gateway API keys ARE stored in state — mark as sensitive
output "api_gateway_api_key" {
  value       = aws_api_gateway_api_key.main.value
  sensitive   = true
  description = "API key value - retrieve via: terraform output -raw api_gateway_api_key"
}

# Stage invoke URL is safe to expose
output "api_invoke_url" {
  value       = aws_api_gateway_stage.main.invoke_url
  description = "API Gateway invoke URL for ${var.environment}"
}
```

---

### State Corruption Recovery

```bash
# 1. List state backup versions in S3
aws s3api list-object-versions \
  --bucket my-org-terraform-state \
  --prefix "prod/api-gateway/terraform.tfstate"

# 2. Restore from a specific version
aws s3api get-object \
  --bucket my-org-terraform-state \
  --key "prod/api-gateway/terraform.tfstate" \
  --version-id "VERSION_ID" \
  terraform.tfstate.backup

# 3. Force-push the restored state (requires DynamoDB lock release first)
terraform state push terraform.tfstate.backup

# 4. Re-import a specific resource if needed
terraform import aws_api_gateway_rest_api.main <REST_API_ID>
terraform import aws_api_gateway_stage.main <REST_API_ID>/<STAGE_NAME>
```

---

## Module Architecture

### Standard Module Structure

```
modules/
└── api-gateway/
    ├── main.tf           # REST API, deployment, stage, method settings
    ├── variables.tf      # Input variables with validation
    ├── outputs.tf        # invoke_url, execution_arn, api_id
    ├── authorizer.tf     # Cognito / Lambda authorizer resources
    ├── domain.tf         # Custom domain, base path mapping
    ├── waf.tf            # WAF Web ACL and association
    ├── versions.tf       # required_providers version constraints
    └── README.md         # Input/output documentation
```

### Module Definition Example

```hcl
# modules/api-gateway/variables.tf
variable "service_name" {
  type        = string
  description = "Name of the service this API belongs to"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.service_name))
    error_message = "Service name must be lowercase alphanumeric with hyphens."
  }
}

variable "environment" {
  type        = string
  description = "Target environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "endpoint_type" {
  type        = string
  description = "API Gateway endpoint type"
  default     = "REGIONAL"

  validation {
    condition     = contains(["EDGE", "REGIONAL", "PRIVATE"], var.endpoint_type)
    error_message = "Endpoint type must be EDGE, REGIONAL, or PRIVATE."
  }
}

variable "cognito_user_pool_arn" {
  type        = string
  description = "ARN of the Cognito User Pool for authorization"
  default     = null
}

variable "lambda_handler_arn" {
  type        = string
  description = "ARN of the Lambda function handling API requests"
}

variable "domain_name" {
  type        = string
  description = "Custom domain name for the API (e.g., api.example.com)"
  default     = null
}

variable "enable_waf" {
  type        = bool
  description = "Whether to associate a WAF Web ACL with the API stage"
  default     = true
}

variable "throttle_rate_limit" {
  type    = number
  default = 1000

  validation {
    condition     = var.throttle_rate_limit >= 1 && var.throttle_rate_limit <= 10000
    error_message = "Throttle rate must be 1-10000 RPS."
  }
}

variable "throttle_burst_limit" {
  type    = number
  default = 2000

  validation {
    condition     = var.throttle_burst_limit >= 1 && var.throttle_burst_limit <= 5000
    error_message = "Throttle burst must be 1-5000."
  }
}

variable "log_retention_days" {
  type    = number
  default = 90

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention must be a valid CloudWatch Logs retention value."
  }
}

# modules/api-gateway/outputs.tf
output "invoke_url" {
  value       = aws_api_gateway_stage.main.invoke_url
  description = "Base URL to invoke the API"
}

output "execution_arn" {
  value       = aws_api_gateway_rest_api.main.execution_arn
  description = "Execution ARN for use in lambda_permission source_arn"
}

output "rest_api_id" {
  value       = aws_api_gateway_rest_api.main.id
  description = "REST API ID"
}

output "stage_arn" {
  value       = aws_api_gateway_stage.main.arn
  description = "Stage ARN (for WAF association)"
}
```

### Root Module Consumption

```hcl
# root/main.tf
module "api_gateway" {
  source = "./modules/api-gateway"

  service_name          = "payment-service"
  environment           = var.environment
  endpoint_type         = "REGIONAL"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  lambda_handler_arn    = module.lambda.function_arn
  domain_name           = "api.${var.domain_name}"
  enable_waf            = var.environment == "prod"
  throttle_rate_limit   = var.environment == "prod" ? 5000 : 500
  throttle_burst_limit  = var.environment == "prod" ? 2000 : 200
  log_retention_days    = var.environment == "prod" ? 365 : 30

  depends_on = [module.cognito, module.lambda]
}
```

---

## Provider Configuration & Credentials

### Authentication Methods (Precedence Order)

```
1. Static credentials in provider block (NEVER use in production)
2. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
3. AWS profile (~/.aws/credentials): profile = "my-profile"
4. EC2 instance metadata (IAM Instance Profile)
5. ECS task IAM role
6. Lambda execution role
7. assume_role in provider block (recommended for CI/CD)
```

### Recommended: IAM Role Assumption with OIDC (CI/CD)

```hcl
# GitHub Actions OIDC provider for credential-free CI/CD
resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions_deploy" {
  name = "github-actions-terraform-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github_actions.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:my-org/my-repo:*"
        }
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}
```

```hcl
# Provider using assume_role (for CI/CD pipelines)
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = var.deploy_role_arn
    session_name = "terraform-${var.environment}-${formatdate("YYYYMMDDHHmm", timestamp())}"
    external_id  = var.external_id  # For cross-account deployments
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

- **Auth Method**: OIDC / IAM Role Assumption
- **Priority**: Environment variables (CI) > IAM role (compute) > Profile (local)
- **Security**: Role assumption provides short-lived credentials; no long-lived keys stored
- **Source**: [AWS Provider Auth](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration)

---

## Integration Patterns

### Integration: Terraform ↔ Lambda

```hcl
# Lambda function for API handler
resource "aws_lambda_function" "api_handler" {
  function_name = "${var.service_name}-api-handler-${var.environment}"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "index.handler"
  runtime       = "nodejs22.x"
  filename      = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name = "${var.service_name}-api-handler-${var.environment}"
  }
}

# Lambda proxy integration
resource "aws_api_gateway_integration" "lambda_proxy" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.items.id
  http_method             = aws_api_gateway_method.items_get.http_method
  integration_http_method = "POST"  # Lambda invocations always use POST
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

# Permission to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGateway-${var.environment}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/${var.environment}/*/*"
}
```

**Versions**:

| Resource | Min Provider | Notes |
|----------|:---:|-------|
| `aws_api_gateway_integration` | ~> 5.0 | `AWS_PROXY` type preferred |
| `aws_lambda_permission` | ~> 5.0 | Required for every integration |
| `aws_lambda_function` | ~> 5.0 | `source_code_hash` required for updates |

**Issues**: Lambda cold start adds 100ms-3s to first request. Lambda `source_code_hash` must change for Terraform to detect new code versions. Lambda proxy expects response in `{ statusCode, headers, body }` format.

- **Source**: [API Gateway Lambda Proxy Integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html)

---

### Integration: Terraform ↔ Cognito

```hcl
resource "aws_cognito_user_pool" "main" {
  name = "${var.service_name}-users-${var.environment}"

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  tags = {
    Name = "${var.service_name}-users-${var.environment}"
  }
}

resource "aws_cognito_user_pool_client" "api" {
  name         = "${var.service_name}-api-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret                      = false
  explicit_auth_flows                  = ["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  prevent_user_existence_errors        = "ENABLED"
  enable_token_revocation              = true
  access_token_validity                = 60   # minutes
  id_token_validity                    = 60   # minutes
  refresh_token_validity               = 30   # days
}

resource "aws_api_gateway_authorizer" "cognito" {
  name          = "${var.service_name}-cognito-${var.environment}"
  rest_api_id   = aws_api_gateway_rest_api.main.id
  type          = "COGNITO_USER_POOLS"
  provider_arns = [aws_cognito_user_pool.main.arn]

  # identity_source defaults to method.request.header.Authorization
  authorizer_result_ttl_in_seconds = 300
}
```

**Issues**: Cognito authorizer validates ID and Access tokens but not Refresh tokens. Token expiry (default 60 min) means cached authorizer results may outlive the token — set `authorizer_result_ttl_in_seconds` ≤ token validity.

- **Source**: [API Gateway Cognito Authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)

---

### Integration: Terraform ↔ VPC (Private Integration via VPC Link)

```hcl
# NLB for private backend
resource "aws_lb" "private_backend" {
  name               = "${var.service_name}-nlb-${var.environment}"
  internal           = true
  load_balancer_type = "network"
  subnets            = var.private_subnet_ids

  tags = {
    Name = "${var.service_name}-nlb-${var.environment}"
  }
}

# VPC Link connecting API Gateway to NLB
resource "aws_api_gateway_vpc_link" "main" {
  name        = "${var.service_name}-vpc-link-${var.environment}"
  description = "VPC Link to private ${var.service_name} backend"
  target_arns = [aws_lb.private_backend.arn]

  tags = {
    Name = "${var.service_name}-vpc-link-${var.environment}"
  }
}

# HTTP proxy integration via VPC Link
resource "aws_api_gateway_integration" "private_http" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.items.id
  http_method             = aws_api_gateway_method.items_get.http_method
  integration_http_method = "GET"
  type                    = "HTTP_PROXY"
  uri                     = "http://${aws_lb.private_backend.dns_name}/items"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.main.id
}
```

**Issues**: VPC Link creation takes 10-15 minutes. NLB must be in the same region as API Gateway. VPC Link does not support HTTPS to backend — use HTTP internally (rely on TLS termination at NLB). NLB incurs ~$16/month base cost.

- **Source**: [API Gateway VPC Link](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-private-integration.html)

---

### Integration: Terraform ↔ CloudWatch

```hcl
# CloudWatch alarm for 5xx error rate
resource "aws_cloudwatch_metric_alarm" "api_5xx_rate" {
  alarm_name          = "${var.service_name}-api-5xx-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  treat_missing_data  = "notBreaching"
  alarm_description   = "High 5xx error rate on ${var.service_name} API"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiName  = aws_api_gateway_rest_api.main.name
    Stage    = aws_api_gateway_stage.main.stage_name
  }
}

# CloudWatch alarm for latency
resource "aws_cloudwatch_metric_alarm" "api_latency_p99" {
  alarm_name          = "${var.service_name}-api-latency-p99-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "IntegrationLatency"
  namespace           = "AWS/ApiGateway"
  period              = "60"
  extended_statistic  = "p99"
  threshold           = "3000"  # 3 seconds
  alarm_description   = "P99 backend latency > 3s"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.name
    Stage   = aws_api_gateway_stage.main.stage_name
  }
}

# CloudWatch alarm for throttle count
resource "aws_cloudwatch_metric_alarm" "api_throttle" {
  alarm_name          = "${var.service_name}-api-throttle-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Count"
  namespace           = "AWS/ApiGateway"
  period              = "60"
  statistic           = "Sum"
  threshold           = "100"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiName  = aws_api_gateway_rest_api.main.name
    Stage    = aws_api_gateway_stage.main.stage_name
    Resource = "/items"
    Method   = "GET"
  }
}
```

- **Source**: [API Gateway CloudWatch Metrics](https://docs.aws.amazon.com/apigateway/latest/developerguide/monitoring-cloudwatch.html)

---

### Integration: Terraform ↔ WAF

See [Mandatory Patterns — WAF Web ACL Association](#pattern-waf-web-acl-association-with-rest-api-stage) above.

**Key constraints**:
- WAF v2 (`aws_wafv2_web_acl`) with `scope = "REGIONAL"` — regional APIs only
- Edge-optimized APIs require CloudFront WAF (scope `CLOUDFRONT`, us-east-1 region)
- WAF association is stage-level (`aws_wafv2_web_acl_association` with `resource_arn = stage.arn`)

---

### Integration: Terraform ↔ ACM + Route53

```hcl
# ACM certificate
resource "aws_acm_certificate" "api" {
  domain_name       = "api.${var.domain_name}"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# Route53 DNS validation records
resource "aws_route53_record" "api_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main.zone_id
}

resource "aws_acm_certificate_validation" "api" {
  certificate_arn         = aws_acm_certificate.api.arn
  validation_record_fqdns = [for record in aws_route53_record.api_cert_validation : record.fqdn]
}

# Route53 A record pointing to API Gateway custom domain
resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_api_gateway_domain_name.main.regional_domain_name
    zone_id                = aws_api_gateway_domain_name.main.regional_zone_id
    evaluate_target_health = false
  }
}
```

**Issues**: ACM certificate validation can take up to 30 minutes. The `aws_acm_certificate_validation` resource blocks Terraform until DNS validation completes — this is the correct behavior. For edge-optimized APIs, the ACM certificate must be in `us-east-1`.

- **Source**: [ACM DNS Validation](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)

---

## Executable Verification (CLI)

```bash
# Project initialization
terraform init -upgrade
# Expected: ✓ Terraform initialized, working directory prepared

# Format validation (CI gate)
terraform fmt -recursive -check=true
# Expected: Exit code 0, no output (all files formatted)

# Syntax and configuration validation
terraform validate
# Expected: Success! The configuration is valid.

# Security scanning with tfsec
tfsec . --minimum-severity HIGH
# Expected: 0 HIGH/CRITICAL findings

# Policy-as-code scanning
checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks, 0 CRITICAL

# Dry run with saved plan
terraform plan -out=tfplan -lock=true -var-file="environments/${TF_ENV}.tfvars"
terraform show -json tfplan | jq '.resource_changes[] | {address, action: .change.actions}'
# Expected: Only intended resources in the plan, no unexpected deletions

# Apply with plan file (no interactive prompt)
terraform apply tfplan
# Expected: All resources applied successfully, exit code 0

# Verify state matches infrastructure
terraform state list | grep api_gateway
# Expected: All API Gateway resources enumerated

terraform state show aws_api_gateway_stage.main
# Expected: Stage details including invoke_url and deployment_id

# Output the API endpoint
terraform output api_invoke_url
# Expected: https://{api-id}.execute-api.{region}.amazonaws.com/{stage}

# Safe destroy (with plan review)
terraform plan -destroy -out=destroy.tfplan -var-file="environments/${TF_ENV}.tfvars"
terraform show destroy.tfplan
# Review carefully — then:
terraform apply destroy.tfplan
```

---

## Configuration Validation & Type Safety

```hcl
variable "service_name" {
  type        = string
  description = "Service name used in resource naming"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,28}[a-z0-9]$", var.service_name))
    error_message = "Service name must be 3-30 chars, lowercase alphanumeric with hyphens, no leading/trailing hyphens."
  }
}

variable "api_type" {
  type        = string
  description = "API type: rest (V1) or http/websocket (V2)"
  default     = "rest"

  validation {
    condition     = contains(["rest", "http", "websocket"], var.api_type)
    error_message = "API type must be 'rest', 'http', or 'websocket'."
  }
}

variable "authorizer_ttl" {
  type        = number
  description = "Authorizer cache TTL in seconds (0 = no caching)"
  default     = 300

  validation {
    condition     = var.authorizer_ttl >= 0 && var.authorizer_ttl <= 3600
    error_message = "Authorizer TTL must be 0-3600 seconds."
  }
}

variable "tags" {
  type        = map(string)
  description = "Additional resource tags"
  default     = {}

  validation {
    condition = alltrue([
      for k, v in var.tags : can(regex("^[\\w\\s_.:/=+@-]{1,128}$", k)) && can(regex("^[\\w\\s_.:/=+@-]{0,256}$", v))
    ])
    error_message = "Tag keys (1-128 chars) and values (0-256 chars) must match AWS tag character constraints."
  }
}

variable "log_format" {
  type        = string
  description = "Access log format string for API Gateway"
  default     = ""
  sensitive   = false
}
```

---

## Drift Detection & Reconciliation

### Scenario: Method Created Outside Terraform (AWS Console)

```
Detection: terraform plan will show:
  ~ resource "aws_api_gateway_rest_api" "main" {
      ~ body = ... # divergence if using OpenAPI body
    }
  (or no detection if using individual resources — drift is silent)

Recovery for individual resources:
  # Import the manually-created method
  terraform import aws_api_gateway_method.new_method <REST_API_ID>/<RESOURCE_ID>/<HTTP_METHOD>

Recovery for OpenAPI body:
  # Force re-import of entire OpenAPI spec
  terraform apply  # body will overwrite console changes on next apply
```

### Scenario: Stage Variables Modified Outside Terraform

```bash
# Detect drift
terraform plan -refresh-only
# Expected: Plan shows stage variable changes

# Reconcile (restore Terraform state)
terraform apply -refresh-only   # Updates state to match real infra
terraform apply                  # Reverts infra to match Terraform config
```

### Lifecycle Rules for Sensitive Resources

```hcl
# Protect the API Gateway deployment from accidental replacement
resource "aws_api_gateway_stage" "main" {
  # ... configuration ...

  lifecycle {
    # Prevent stage from being destroyed and recreated (would cause URL change)
    prevent_destroy = var.environment == "prod" ? true : false
  }
}
```

---

## Secrets & Sensitive Data Management

```hcl
# API keys stored in Secrets Manager (not hardcoded)
data "aws_secretsmanager_secret_version" "third_party_key" {
  secret_id = "prod/api-gateway/third-party-api-key"
}

locals {
  third_party_api_key = jsondecode(data.aws_secretsmanager_secret_version.third_party_key.secret_string)["api_key"]
}

# Stage variable referencing the key (avoids key in state)
resource "aws_api_gateway_stage" "main" {
  # ... configuration ...

  variables = {
    third_party_endpoint = var.third_party_endpoint
    # Do NOT store secrets in stage variables — they appear in CloudTrail and state
  }
}

# Correct pattern: pass secrets via Lambda environment (with KMS encryption)
resource "aws_lambda_function" "api_handler" {
  # ...
  kms_key_arn = aws_kms_key.lambda.arn

  environment {
    variables = {
      SECRET_ARN = data.aws_secretsmanager_secret_version.third_party_key.arn
      # Let Lambda fetch the secret at runtime — not the value
    }
  }
}
```

**Secret Type → Storage Mapping**:

| Secret Type | Storage | Retrieval |
|-------------|---------|-----------|
| API keys | AWS Secrets Manager | `data.aws_secretsmanager_secret_version` |
| Lambda env secrets | SSM Parameter Store (SecureString) | `data.aws_ssm_parameter` |
| Cognito client secret | Secrets Manager | Lambda runtime fetch |
| TLS certificates | ACM | `aws_acm_certificate_validation` |
| Terraform state | S3 + KMS | `backend "s3"` with `kms_key_id` |

```bash
# Ensure .tfvars files with secrets are gitignored
cat >> .gitignore << 'EOF'
*.tfvars
*.tfvars.json
!example.tfvars
terraform.tfstate
terraform.tfstate.backup
.terraform/
EOF
```

---

## Testing & Validation Frameworks

### Static Analysis

```bash
# Framework: terraform fmt (built-in)
# Purpose: Code style consistency
terraform fmt -recursive -check=true
# Expected: Exit 0, no output

# Framework: terraform validate (built-in)
# Purpose: Configuration syntax and type correctness
terraform validate
# Expected: Success! The configuration is valid.

# Framework: tfsec (aquasecurity/tfsec)
# Purpose: Security policy scanner
tfsec . --minimum-severity MEDIUM --format sarif --out tfsec-results.sarif
# Expected: 0 CRITICAL, 0 HIGH findings

# Framework: Checkov (bridgecrew/checkov)
# Purpose: Policy-as-code, CIS benchmarks, SAST
checkov -d . --framework terraform --output cli --quiet
# Expected: Passed > Failed, 0 CRITICAL
```

### Unit Testing with terraform test (Terraform 1.7+)

```hcl
# tests/api_gateway.tftest.hcl
variables {
  service_name = "test-api"
  environment  = "dev"
  aws_region   = "us-east-1"
}

run "validate_api_configuration" {
  command = plan

  assert {
    condition     = aws_api_gateway_rest_api.main.endpoint_configuration[0].types[0] == "REGIONAL"
    error_message = "API Gateway must use REGIONAL endpoint type"
  }

  assert {
    condition     = aws_api_gateway_stage.main.xray_tracing_enabled == true
    error_message = "X-Ray tracing must be enabled on all stages"
  }

  assert {
    condition     = aws_api_gateway_method_settings.main.settings[0].throttling_rate_limit > 0
    error_message = "Stage throttling must be configured"
  }
}
```

### Integration Testing with Terratest (Go)

```go
package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/gruntwork-io/terratest/modules/http-helper"
    "github.com/stretchr/testify/assert"
    "time"
)

func TestAPIGatewayDeployment(t *testing.T) {
    t.Parallel()

    opts := &terraform.Options{
        TerraformDir: "../examples/api-gateway",
        Vars: map[string]interface{}{
            "service_name": "terratest-api",
            "environment":  "dev",
        },
    }

    defer terraform.Destroy(t, opts)
    terraform.InitAndApply(t, opts)

    invokeURL := terraform.Output(t, opts, "api_invoke_url")
    assert.Contains(t, invokeURL, "execute-api")

    // Verify the API responds (with auth header)
    statusCode, _ := http_helper.HttpGetWithRetry(
        t,
        invokeURL+"/v1/health",
        nil,
        3,
        10*time.Second,
    )
    assert.Equal(t, 401, statusCode) // Expect 401 (unauthorized) — auth is configured
}
```

---

## Production Readiness

### Performance

```
Scenario: High-Traffic Production API (>1M requests/day)
Challenge: Default account throttle (10,000 RPS) shared across all APIs in region
Solution:
  - Request throttle limit increase via AWS Support (up to 160,000 RPS for regional)
  - Use HTTP API (V2) for latency-critical paths (40% lower P50 vs REST API)
  - Enable response caching (REST API only) for read-heavy endpoints: 0.5GB to 237GB cache
  - Use Lambda provisioned concurrency to eliminate cold starts on critical paths

Metrics to monitor:
  - Count (total requests)
  - 4XXError (client errors — auth failures, bad requests)
  - 5XXError (integration failures — Lambda errors, timeouts)
  - Latency (end-to-end)
  - IntegrationLatency (backend-only)
  - CacheHitCount / CacheMissCount (if caching enabled)
```

### Scalability

```
API Gateway auto-scales with zero configuration. Limits to monitor:
  - Account default: 10,000 RPS (soft limit — request increase via Support)
  - Default burst: 5,000 RPS
  - Resources per REST API: 300 (soft limit)
  - Stages per REST API: 10 (soft limit)
  - Lambda concurrent executions: 1,000/region default (request increase)
  - State file: Terraform scales to ~10,000 resources; split large APIs into modules
```

### Canary Deployments (REST API Only)

```hcl
resource "aws_api_gateway_stage" "main" {
  # ... base configuration ...

  canary_settings {
    deployment_id  = aws_api_gateway_deployment.canary.id
    percent_traffic = 10  # 10% to new version
  }
}
```

### Disaster Recovery Runbook

```bash
# Scenario: API stage lost / deployment corrupted

# 1. List all existing deployments
aws apigateway get-deployments --rest-api-id <API_ID>

# 2. Get deployment details
aws apigateway get-deployment --rest-api-id <API_ID> --deployment-id <DEPLOYMENT_ID>

# 3. Re-point stage to a previous deployment (bypasses Terraform — create import block after)
aws apigateway update-stage \
  --rest-api-id <API_ID> \
  --stage-name <STAGE_NAME> \
  --patch-operations op=replace,path=/deploymentId,value=<PREV_DEPLOYMENT_ID>

# 4. Import the stage back into Terraform state
terraform import aws_api_gateway_stage.main <API_ID>/<STAGE_NAME>

# 5. Run plan to detect any drift
terraform plan

# Scenario: Accidental API deletion
# 1. State file still has resource — run import
terraform import aws_api_gateway_rest_api.main <NEW_API_ID>
# Note: If API is deleted, it must be recreated — no restore mechanism
# This highlights the importance of OpenAPI export as backup:
aws apigateway get-export \
  --rest-api-id <API_ID> \
  --stage-name prod \
  --export-type swagger \
  --accepts application/json \
  api-backup.json
```

---

## Security Checklist

- [ ] All methods declare an authorizer (`authorization != "NONE"` in production)
- [ ] WAF Web ACL associated with all production REST API stages
- [ ] Access logs enabled with structured JSON format
- [ ] X-Ray tracing enabled on all stages
- [ ] `data_trace_enabled = false` in production stage settings
- [ ] State file encryption enabled (`encrypt = true` + KMS key)
- [ ] State file access restricted to Terraform service accounts via S3 bucket policy
- [ ] No credentials in provider block — using IAM role assumption or env vars
- [ ] All resources tagged with Environment, ManagedBy, Owner, CostCenter
- [ ] Throttling configured at stage and method level
- [ ] Custom domain with TLS 1.2 minimum security policy
- [ ] `disable_execute_api_endpoint = true` in production (force custom domain)
- [ ] CloudWatch log group retention set (not "Never expire")
- [ ] API keys combined with authorizer (never sole security mechanism)
- [ ] `.tfvars` files with secrets in `.gitignore`
- [ ] `prevent_destroy = true` on production stages
- [ ] `create_before_destroy = true` on all deployment resources
- [ ] Lambda permission `source_arn` uses specific path (not `*`)

---

## Complete Root Module Example

```hcl
# terraform.tfvars (DO NOT COMMIT — add to .gitignore)
# service_name    = "payment-api"
# environment     = "prod"
# aws_region      = "us-east-1"
# account_id      = "123456789012"
# owner           = "platform-team"
# cost_center     = "cc-platform-001"
# domain_name     = "example.com"
# deploy_role_arn = "arn:aws:iam::123456789012:role/TerraformDeployRole"

# variables.tf
variable "service_name"    { type = string }
variable "environment"     { type = string }
variable "aws_region"      { type = string }
variable "account_id"      { type = string }
variable "owner"           { type = string }
variable "cost_center"     { type = string }
variable "domain_name"     { type = string }
variable "deploy_role_arn" { type = string }

# main.tf
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/api-gateway/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = var.deploy_role_arn
    session_name = "terraform-${var.service_name}-${var.environment}"
  }

  default_tags {
    tags = {
      Environment = var.environment
      Service     = var.service_name
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}

# CloudWatch role (account-level, one-time)
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
  depends_on          = [aws_iam_role_policy_attachment.api_gateway_cloudwatch]
}

# REST API
resource "aws_api_gateway_rest_api" "main" {
  name                         = "${var.service_name}-${var.environment}"
  disable_execute_api_endpoint = var.environment == "prod"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "access_logs" {
  name              = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.main.id}/${var.environment}"
  retention_in_days = var.environment == "prod" ? 365 : 30
}

# Deployment with redeployment trigger
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.main.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Stage with logging, tracing, throttling
resource "aws_api_gateway_stage" "main" {
  depends_on    = [aws_cloudwatch_log_group.access_logs]
  rest_api_id   = aws_api_gateway_rest_api.main.id
  deployment_id = aws_api_gateway_deployment.main.id
  stage_name    = var.environment

  xray_tracing_enabled = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.access_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      sourceIp       = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      errorMessage   = "$context.error.message"
    })
  }

  lifecycle {
    prevent_destroy = var.environment == "prod"
  }
}

# Method settings with throttling
resource "aws_api_gateway_method_settings" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled        = true
    logging_level          = "INFO"
    data_trace_enabled     = false
    throttling_burst_limit = var.environment == "prod" ? 2000 : 200
    throttling_rate_limit  = var.environment == "prod" ? 5000 : 500
  }
}

# outputs.tf
output "api_invoke_url" {
  value       = aws_api_gateway_stage.main.invoke_url
  description = "API Gateway invoke URL"
}

output "api_execution_arn" {
  value       = aws_api_gateway_rest_api.main.execution_arn
  description = "Execution ARN prefix for Lambda permissions"
}

output "rest_api_id" {
  value       = aws_api_gateway_rest_api.main.id
  description = "REST API ID"
}
```

---

## Reference Implementations

- [Official Terraform AWS Examples — API Gateway OpenAPI](https://github.com/hashicorp/terraform-provider-aws/tree/main/examples/api-gateway-rest-api-openapi)
- [AWS Provider Registry — API Gateway V1 Resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#api-gateway)
- [AWS Provider Registry — API Gateway V2 Resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#api-gateway-v2)
- [AWS Well-Architected Framework — Serverless Lens](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html)
- [Terraform Best Practices](https://developer.hashicorp.com/terraform/cloud-adopt/best-practices)

---

## Source Bibliography

### Primary Sources (Validated 2026-05-28)

- [Terraform AWS Provider v6.47.0 Registry](https://registry.terraform.io/providers/hashicorp/aws/6.47.0)
- [aws_api_gateway_rest_api Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api)
- [aws_api_gateway_stage Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_stage)
- [aws_api_gateway_authorizer Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_authorizer)
- [aws_api_gateway_deployment Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_deployment)
- [aws_apigatewayv2_api Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_api)
- [AWS API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html)
- [API Gateway Access Control](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html)
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)

### Validation Tools

- [tfsec](https://github.com/aquasecurity/tfsec) — Security scanner for Terraform
- [Checkov](https://www.checkov.io/) — Policy-as-code validator
- [Terratest](https://terratest.gruntwork.io/) — Go testing framework
- [terraform test](https://developer.hashicorp.com/terraform/cli/commands/test) — Built-in testing (>= 1.7)

---

## Research Gaps

```
Gap: API Gateway V2 (HTTP API) WAF support
Impact: HTTP APIs cannot be associated with WAF Web ACLs directly — requires CloudFront in front
Workaround: Place CloudFront distribution in front of HTTP API endpoint and attach WAF to CloudFront
Follow-up: https://github.com/hashicorp/terraform-provider-aws/issues (search "apigatewayv2 waf")

Gap: API Gateway mutual TLS (mTLS) Terraform resource
Impact: mTLS truststore configuration requires S3 bucket with certificate bundle
Workaround: Use aws_api_gateway_domain_name with mutual_tls_authentication block (V1 only)
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_domain_name

Gap: API Gateway Developer Portal
Impact: No native Terraform resource for Developer Portal configuration (as of v6.x)
Workaround: Provision via AWS Console or AWS CLI; manage portal configuration outside Terraform
Follow-up: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-developer-portal.html

Gap: ip_address_type dualstack (IPv6) in endpoint_configuration — v6.47.0
Impact: REST APIs and HTTP APIs now support dualstack (IPv4+IPv6) invocation. The ip_address_type
  argument was added to aws_api_gateway_rest_api endpoint_configuration and aws_apigatewayv2_api
  in provider v6.x. PRIVATE endpoint type only supports dualstack (ipv4 not allowed).
  Current patterns in this file default to ipv4 (REGIONAL endpoint, no ip_address_type set).
  For IPv6-capable APIs, add: ip_address_type = "dualstack" in endpoint_configuration.
Workaround: Default behavior (ipv4) is safe; add ip_address_type = "dualstack" explicitly for
  dual-stack deployments. Validated from registry docs (published 2026-05-28).
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api#ip_address_type

Gap: aws_api_gateway_domain_name_access_association — v6.x new resource
Impact: New resource for associating private custom domain names with VPC endpoints. Required for
  PRIVATE endpoint type custom domain configurations. Not covered in this document.
Workaround: For public REGIONAL custom domains, aws_api_gateway_domain_name remains correct.
  For private APIs with custom domains, investigate aws_api_gateway_domain_name_access_association.
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_domain_name_access_association

Gap: aws_apigatewayv2_routing_rule — v6.x new resource
Impact: New V2-only resource for fine-grained request routing rules within an HTTP API stage.
  Enables header/path based routing to multiple integrations without creating separate APIs.
  Not covered in the HTTP API section of this document.
Workaround: Use separate routes (aws_apigatewayv2_route) per integration target.
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_routing_rule

Gap: Terraform v1.12.0 identity-based import blocks
Impact: Terraform v1.12.0 introduced identity-based import block syntax using the identity attribute.
  Current import examples in this file use the older id-based syntax (valid for >= v1.5.0).
  Identity blocks provide stronger semantic clarity for multi-field resource identities.
  Example for aws_api_gateway_rest_api:
    import {
      to = aws_api_gateway_rest_api.main
      identity = { id = "12345abcde" }
    }
Workaround: Both syntaxes (id-based and identity-based) are valid with provider v6.x.
  Use identity-based blocks for new code when targeting Terraform >= 1.12.0.
Follow-up: https://developer.hashicorp.com/terraform/language/import
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- State backend configuration (S3 + DynamoDB)
- `create_before_destroy = true` on deployments
- Access logging and X-Ray enablement
- CloudWatch IAM role for API Gateway account
- Lambda permission `source_arn` scoping
- WAF association on REST API stages
- TLS 1.2 minimum security policy on custom domains

### Medium Confidence (Validate with user)
- REST API vs. HTTP API choice
- Throttle limit values (depend on expected traffic)
- Authorizer TTL (depends on token expiry and security posture)
- Module decomposition strategy
- Canary deployment percentage

### Low Confidence (Must ask user)
- Cost optimization decisions (REST vs HTTP API tradeoff)
- Compliance-specific requirements (HIPAA, PCI-DSS WAF rules)
- Multi-region API Gateway deployment strategy
- Private API with custom domain (complex Route53 private hosted zone setup)
- WebSocket API for real-time features

### Emergency Stop Conditions
- `authorization = "NONE"` detected on any production method
- `data_trace_enabled = true` in production stage
- `encrypt = false` or missing on S3 backend
- Credentials detected in provider block or `.tfvars` files
- `terraform destroy` planned on production stage without explicit `prevent_destroy = false`
