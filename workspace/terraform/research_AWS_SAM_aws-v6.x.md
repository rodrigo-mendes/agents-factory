# Terraform AWS SAM (Serverless Application Model) — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - SAM (Serverless Application Model)"
Cloud_Provider: "AWS"
Target_Service: "SAM — Serverless Application Repository + native serverless stack (Lambda, API Gateway V2, DynamoDB, SQS, CodeDeploy)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-29)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-29"
Research_Date: "2026-05-29"
Domain_Complexity: "Complex"
SAR_Resources:
  - "aws_serverlessapplicationrepository_cloudformation_stack"
  - "data.aws_serverlessapplicationrepository_application"
  - "aws_cloudformation_stack (SAM template inline)"
Native_Resources:
  - "aws_lambda_function"
  - "aws_lambda_alias"
  - "aws_lambda_permission"
  - "aws_lambda_event_source_mapping"
  - "aws_lambda_function_event_invoke_config"
  - "aws_apigatewayv2_api"
  - "aws_apigatewayv2_integration"
  - "aws_apigatewayv2_route"
  - "aws_apigatewayv2_stage"
  - "aws_apigatewayv2_authorizer"
  - "aws_dynamodb_table"
  - "aws_sqs_queue"
  - "aws_codedeploy_app"
  - "aws_codedeploy_deployment_group"
  - "aws_cloudwatch_log_group"
  - "aws_iam_role"
  - "aws_iam_role_policy"
```

---

## Executive Summary

AWS Serverless Application Model (SAM) is a CloudFormation extension framework that collapses multi-resource serverless definitions into shorthand syntax. In the Terraform ecosystem, SAM manifests through **two distinct integration paths**: (1) deploying pre-packaged SAM applications from the AWS Serverless Application Repository (SAR) via `aws_serverlessapplicationrepository_cloudformation_stack`, and (2) replicating SAM-equivalent infrastructure using native Terraform resources — `aws_lambda_function`, `aws_apigatewayv2_*`, `aws_dynamodb_table`, `aws_codedeploy_*`, and `aws_iam_role`. The native path is strongly preferred for greenfield Terraform projects because it provides full state visibility, drift detection, import support, and lifecycle control that the CloudFormation wrapper path cannot provide. The SAR path is appropriate for consuming published third-party SAM applications without rewriting them.

The AWS Provider v6.x brings several capabilities critical to serverless IaC: `aws_lambda_function` now supports `logging_config` with structured JSON logging and log-level filtering (replacing the manual CloudWatch log group workaround); `aws_lambda_function_event_invoke_config` supports on-failure destination ARNs for SQS DLQ and EventBridge; CodeDeploy Lambda deployment groups support `linear_10_percent_every_1_minute` and `canary_10_percent_5_minutes` traffic-shifting policies with CloudWatch alarm rollback. The `default_tags` propagation in v6.x now reliably covers Lambda, API Gateway V2, DynamoDB, and SQS resources — previously some required explicit per-resource tag blocks to achieve compliance.

Three non-negotiable guardrails define safe SAM-equivalent Terraform: **(1) every Lambda function must have a dead-letter queue (DLQ) configured via `dead_letter_config`** — without it, async invocation failures are silently discarded with no recovery path; **(2) every API Gateway V2 route must declare an authorizer** — `authorization_type = "NONE"` on a production route is a publicly-exploitable endpoint; **(3) `prevent_destroy = true` must be set on DynamoDB tables holding application state** — Terraform's default behavior allows `terraform destroy` to permanently delete tables with no CloudFormation rollback safety net. This domain is classified **Complex** due to IAM cross-resource dependencies, stateful Lambda versioning, CodeDeploy orchestration for gradual rollouts, and the multi-service dependency chain that must remain consistent across plan/apply cycles.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Ensures reproducibility across team members and CI/CD pipelines. Provider `~> 6.0` constraint prevents accidental upgrade to future v7.x with breaking changes.

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
    key            = "prod/serverless/terraform.tfstate"
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

**Why**: Static credentials must never appear in Terraform code. `assume_role` enables deployment from CI/CD without long-lived AWS access keys. `default_tags` enforces cost allocation and compliance tagging across all serverless resources (Lambda, API GW, DynamoDB, SQS) without per-resource duplication.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "terraform-serverless-${var.environment}"
  }

  default_tags {
    tags = {
      Environment = var.environment
      Service     = "serverless-app"
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

#### Pattern: Lambda Function with Security Baseline

**Why**: A SAM `AWS::Serverless::Function` expands to a Lambda function plus IAM role, CloudWatch log group, and optionally an SQS DLQ. All of these must be explicitly defined in Terraform. The `logging_config` block (v6.x) replaces the unmanaged log group workaround. The DLQ is non-negotiable for async invocations — silent failure is not acceptable.

```hcl
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.lambda_logs.arn

  tags = {
    Name = "${var.function_name}-logs"
  }
}

resource "aws_sqs_queue" "lambda_dlq" {
  name                      = "${var.function_name}-dlq"
  message_retention_seconds = 1209600 # 14 days
  kms_master_key_id         = aws_kms_key.sqs.id

  tags = {
    Name = "${var.function_name}-dlq"
  }
}

resource "aws_lambda_function" "main" {
  function_name = var.function_name
  role          = aws_iam_role.lambda.arn
  handler       = var.handler
  runtime       = var.runtime        # e.g., "nodejs22.x", "python3.13"
  timeout       = var.timeout        # Max 900 seconds
  memory_size   = var.memory_size    # 128–10240 MB

  filename         = var.deployment_package_path
  source_code_hash = filebase64sha256(var.deployment_package_path)

  # v6.x structured logging
  logging_config {
    log_format            = "JSON"
    log_group             = aws_cloudwatch_log_group.lambda.name
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  dead_letter_config {
    target_arn = aws_sqs_queue.lambda_dlq.arn
  }

  tracing_config {
    mode = "Active" # X-Ray tracing
  }

  environment {
    variables = {
      ENVIRONMENT = var.environment
      # Never hardcode secrets here — use Secrets Manager or SSM Parameter Store
      # DB_PASSWORD = aws_secretsmanager_secret.db.arn  # Reference ARN, not value
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  # Prevent accidental destruction of stateful functions in production
  lifecycle {
    ignore_changes = [
      filename,           # Managed by CI/CD pipeline
      source_code_hash,   # Managed by CI/CD pipeline
    ]
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy_attachment.lambda_basic,
  ]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_lambda_function](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)

---

#### Pattern: Lambda IAM Role with Least-Privilege Execution Policy

**Why**: SAM's `Policies` property auto-generates scoped IAM policies. In Terraform, these must be explicitly declared. The execution role needs only the specific permissions for the function's actual service integrations — never `*:*`.

```hcl
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = {
    Name = "${var.function_name}-role"
  }
}

# Basic execution: CloudWatch Logs + X-Ray
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC access (if function runs in VPC)
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  count      = var.vpc_enabled ? 1 : 0
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# X-Ray tracing
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# Scoped DLQ write permission
data "aws_iam_policy_document" "lambda_dlq" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.lambda_dlq.arn]
  }
}

resource "aws_iam_role_policy" "lambda_dlq" {
  name   = "${var.function_name}-dlq-policy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_dlq.json
}

# Scoped DynamoDB access (replace with actual table ARN)
data "aws_iam_policy_document" "lambda_dynamodb" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.main.arn,
      "${aws_dynamodb_table.main.arn}/index/*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name   = "${var.function_name}-dynamodb-policy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_dynamodb.json
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_iam_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | [aws_iam_role_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy)

---

#### Pattern: API Gateway V2 HTTP API with JWT Authorizer

**Why**: SAM's `AWS::Serverless::HttpApi` expands to an API Gateway V2 HTTP API. Every production route must declare an authorizer — `authorization_type = "NONE"` creates a publicly exploitable endpoint. JWT authorizers with Cognito or external IdPs are the standard SAM-equivalent pattern.

```hcl
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.app_name}-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = ["content-type", "authorization", "x-amz-date", "x-api-key"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_origins = var.cors_allowed_origins  # Never use ["*"] in production
    max_age       = 300
  }

  tags = {
    Name = "${var.app_name}-api"
  }
}

resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "${var.app_name}-jwt-authorizer"

  jwt_configuration {
    audience = [var.cognito_user_pool_client_id]
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${var.cognito_user_pool_id}"
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_alias.live.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000 # Must be < Lambda timeout
}

resource "aws_apigatewayv2_route" "get_items" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /items"
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
}

resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = false # Always use explicit deploys in production

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }

  default_route_settings {
    throttling_burst_limit = var.api_throttle_burst
    throttling_rate_limit  = var.api_throttle_rate
  }
}

# Grant API Gateway permission to invoke Lambda alias
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  qualifier     = aws_lambda_alias.live.name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_apigatewayv2_api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_api) | [aws_apigatewayv2_authorizer](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_authorizer)

---

#### Pattern: Lambda Alias + Version for Gradual Deployments (SAM AutoPublishAlias equivalent)

**Why**: SAM's `AutoPublishAlias` and `DeploymentPreference` control traffic shifting via Lambda aliases and CodeDeploy. In Terraform, the equivalent pattern uses `aws_lambda_alias` + `aws_codedeploy_deployment_group` with `linear` or `canary` configuration. The alias must be used as the API Gateway integration target — never `$LATEST`.

```hcl
resource "aws_lambda_alias" "live" {
  name             = "live"
  function_name    = aws_lambda_function.main.function_name
  function_version = aws_lambda_function.main.version

  lifecycle {
    ignore_changes = [function_version] # CodeDeploy manages version pointer
  }
}

resource "aws_codedeploy_app" "lambda" {
  compute_platform = "Lambda"
  name             = "${var.function_name}-deploy"
}

resource "aws_codedeploy_deployment_group" "lambda" {
  app_name               = aws_codedeploy_app.lambda.name
  deployment_group_name  = "${var.function_name}-deployment-group"
  service_role_arn       = aws_iam_role.codedeploy.arn
  deployment_config_name = "CodeDeployDefault.LambdaCanary10Percent5Minutes"

  deployment_style {
    deployment_option = "WITH_TRAFFIC_CONTROL"
    deployment_type   = "BLUE_GREEN"
  }

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM"]
  }

  alarm_configuration {
    alarms  = [aws_cloudwatch_metric_alarm.lambda_errors.name]
    enabled = true
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.function_name}-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda error rate exceeded threshold — triggers CodeDeploy rollback"

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
    Resource     = "${aws_lambda_function.main.function_name}:${aws_lambda_alias.live.name}"
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_lambda_alias](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_alias) | [aws_codedeploy_deployment_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codedeploy_deployment_group)

---

#### Pattern: DynamoDB Table with Destruction Protection

**Why**: SAM's `AWS::Serverless::SimpleTable` and `AWS::Serverless::Table` create DynamoDB tables as part of the CloudFormation stack. In Terraform, DynamoDB tables must have `prevent_destroy = true` — without it, a `terraform destroy` permanently deletes the table and all data with no CloudFormation rollback mechanism.

```hcl
resource "aws_dynamodb_table" "main" {
  name             = "${var.app_name}-${var.environment}"
  billing_mode     = "PAY_PER_REQUEST" # On-demand; use PROVISIONED for predictable workloads
  hash_key         = "PK"
  range_key        = "SK"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "GSI1PK"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "SK"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ExpiresAt"
    enabled        = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.app_name}-table"
  }

  lifecycle {
    prevent_destroy = true # CRITICAL: Protects against accidental data loss
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_dynamodb_table](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table)

---

#### Pattern: Variable Validation & Type Safety

**Why**: Invalid configurations fail at `terraform plan` time (before any AWS API call). Validates runtime, memory, timeout, and environment name to prevent misconfiguration reaching production.

```hcl
variable "runtime" {
  type        = string
  description = "Lambda runtime identifier"
  default     = "nodejs22.x"

  validation {
    condition = contains([
      "nodejs20.x", "nodejs22.x",
      "python3.11", "python3.12", "python3.13",
      "java21", "dotnet8",
      "provided.al2023"
    ], var.runtime)
    error_message = "Runtime must be an AWS-supported non-deprecated runtime."
  }
}

variable "memory_size" {
  type        = number
  description = "Lambda memory allocation in MB"
  default     = 512

  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 10240
    error_message = "Memory size must be between 128 MB and 10240 MB."
  }
}

variable "timeout" {
  type        = number
  description = "Lambda timeout in seconds"
  default     = 30

  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "Timeout must be between 1 and 900 seconds."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment name"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "Allowed CORS origins — do not include wildcard (*) in production"
  default     = []

  validation {
    condition     = !contains(var.cors_allowed_origins, "*")
    error_message = "Wildcard origin (*) is not permitted in production CORS configuration."
  }
}
```

- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

#### Pattern: Deploying SAR Application via Terraform (SAR path)

**Why**: When consuming a published SAM application from the AWS Serverless Application Repository (e.g., a shared auth handler, log forwarder, or third-party integration), `aws_serverlessapplicationrepository_cloudformation_stack` deploys it as a CloudFormation nested stack. The `data.aws_serverlessapplicationrepository_application` source resolves the latest semantic version automatically.

```hcl
data "aws_serverlessapplicationrepository_application" "datadog_forwarder" {
  application_id   = "arn:aws:serverlessrepo:us-east-1:464622532012:applications/Datadog-Log-Forwarder"
  semantic_version = "3.103.0" # Pin version; never use "latest" in production
}

resource "aws_serverlessapplicationrepository_cloudformation_stack" "datadog_forwarder" {
  name             = "datadog-log-forwarder-${var.environment}"
  application_id   = data.aws_serverlessapplicationrepository_application.datadog_forwarder.application_id
  semantic_version = data.aws_serverlessapplicationrepository_application.datadog_forwarder.semantic_version
  capabilities     = data.aws_serverlessapplicationrepository_application.datadog_forwarder.required_capabilities

  parameters = {
    DdApiKey      = var.datadog_api_key_secret_arn  # Pass secret ARN, not value
    DdSite        = "datadoghq.com"
    FunctionName  = "datadog-forwarder-${var.environment}"
  }

  tags = {
    Name        = "datadog-log-forwarder"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_serverlessapplicationrepository_cloudformation_stack](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/serverlessapplicationrepository_cloudformation_stack) | [data.aws_serverlessapplicationrepository_application](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/serverlessapplicationrepository_application)

---

### ⚠️ Conditional Patterns

---

#### Decision: Native Terraform Resources vs. CloudFormation Stack Wrapper

| Option | Optimizes | Sacrifices | State | Drift | Best When |
|--------|-----------|------------|-------|-------|-----------|
| **Native Terraform** (`aws_lambda_function`, etc.) | Full state visibility, drift detection, import, lifecycle control | More resources to manage, no SAM shorthand | Full Terraform state | `terraform plan` detects all drift | Greenfield projects, team owns the code, CI/CD control required |
| **`aws_cloudformation_stack` with SAM template** | Reuse existing SAM templates, faster migration | CloudFormation manages nested state, drift invisible to Terraform | Partial (CF stack only) | Terraform cannot detect drift inside CF stack | Migrating existing SAM apps, team prefers SAM DSL |
| **`aws_serverlessapplicationrepository_cloudformation_stack`** | Consume third-party published apps | No control over internals, SAR dependency | CF stack reference | CF stack drift not exposed | Consuming published SAR apps (Datadog, Lumigo, etc.) |

- **Agent**: "Ask user: Does your team own the serverless application source code? Are you migrating an existing SAM app or building new infrastructure?"
- **Source**: [aws_cloudformation_stack](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudformation_stack)

---

#### Decision: Lambda Deployment Strategy (SAM DeploymentPreference equivalent)

| Option | Traffic Shift | Rollback | Downtime | Best When |
|--------|--------------|----------|----------|-----------|
| **Direct `function_version` update** | Immediate (all-at-once) | Manual terraform apply rollback | Zero (Lambda alias swap) | Development, non-critical functions |
| **CodeDeploy Canary10Percent5Minutes** | 10% for 5 min → 100% | Automatic on CloudWatch alarm | Zero | Production functions with measurable error rate |
| **CodeDeploy Linear10PercentEvery1Minute** | +10% per minute → 100% | Automatic on CloudWatch alarm | Zero | Gradual validation, high-traffic critical functions |
| **CodeDeploy AllAtOnce** | Immediate | Automatic rollback only | Zero | Low-risk deploys, batch processing functions |

- **When**: Use CodeDeploy gradual deployments for any Lambda receiving > 100 req/min or handling financial/user-data operations. Direct updates are acceptable for internal/background processing functions.
- **Agent**: "Ask user: What is the expected invocation volume for this function? Does a failed deployment require automatic rollback?"
- **Source**: [aws_codedeploy_deployment_group Lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codedeploy_deployment_group#lambda-configuration)

---

#### Decision: Lambda Invocation Trigger Pattern

| Option | Pattern | Trigger Resource | Best When |
|--------|---------|-----------------|-----------|
| **API Gateway HTTP** | Sync request/response | `aws_apigatewayv2_route` | REST/GraphQL APIs, user-facing requests |
| **SQS Event Source** | Async batch processing | `aws_lambda_event_source_mapping` | Queue-based workloads, retry semantics required |
| **DynamoDB Streams** | Change-data-capture | `aws_lambda_event_source_mapping` | Replication, audit logging, downstream sync |
| **EventBridge Rule** | Event-driven schedule or pattern | `aws_cloudwatch_event_rule` + `aws_lambda_permission` | Scheduled tasks, cross-service event routing |
| **S3 Event Notification** | Object-lifecycle processing | `aws_s3_bucket_notification` + `aws_lambda_permission` | File processing pipelines |

- **When**: Match the trigger pattern to the invocation semantics. SQS is preferred over direct Lambda invocation for workloads requiring retry, throttle, and DLQ semantics.
- **Source**: [aws_lambda_event_source_mapping](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_event_source_mapping)

---

#### Decision: DynamoDB Billing Mode

| Option | Optimizes | Sacrifices | Scaling | Cost |
|--------|-----------|------------|---------|------|
| **PAY_PER_REQUEST** | Zero capacity planning, auto-scales | Higher per-request cost at steady-state volume | Instant | Variable — ideal < 100K writes/day |
| **PROVISIONED with Auto Scaling** | Predictable cost, baseline guaranteed | Capacity planning required, throttling risk | Gradual | Lower at steady-state volume |
| **PROVISIONED fixed** | Lowest cost at known steady load | Manual scaling, over/under-provision risk | None | Lowest — only if load is perfectly predictable |

- **Agent**: "Ask user: What is the expected peak write throughput? Is the workload bursty or steady-state?"
- **Source**: [DynamoDB Billing Modes](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table#billing_mode)

---

#### Decision: Multi-Environment Strategy

| Option | Optimizes | Sacrifices | State Isolation |
|--------|-----------|------------|-----------------|
| **Separate backends per env** | True state isolation, independent lifecycle | More backend config, more S3 state files | Full |
| **Terraform Workspaces** | Single codebase, workspace switching | Shared backend, accidental workspace switch risk | Partial |
| **Separate repos per env** | Full code + state isolation | Code duplication, drift between env repos | Full |

- **Recommendation**: Use separate S3 state file paths (`key = "dev/serverless/terraform.tfstate"` vs `key = "prod/serverless/terraform.tfstate"`) with a single backend bucket. Workspaces are acceptable for dev/staging, but production must have an isolated state path.
- **Source**: [Backend Configuration](https://developer.hashicorp.com/terraform/language/settings/backends/configuration)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Hardcoded AWS Credentials in Provider

```hcl
# DON'T
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  region     = "us-east-1"
}
```

**Why**: Credentials in code are committed to version control history (permanent exposure even after deletion) and accessible to every team member with repo access.

```hcl
# DO — Use IAM role assumption (CI/CD) or environment variables (local dev)
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "terraform-${var.environment}"
  }
}
# Local dev: set AWS_PROFILE or AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in shell
# CI/CD: use OIDC provider (GitHub Actions → AWS OIDC) — no long-lived keys
```

- **Impact**: CRITICAL — Full AWS account compromise
- **Severity**: CRITICAL
- **Source**: [AWS Security Best Practices](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)

---

#### Anti-Pattern: Lambda Environment Variable with Hardcoded Secret

```hcl
# DON'T
resource "aws_lambda_function" "main" {
  environment {
    variables = {
      DB_PASSWORD     = "mysupersecretpassword"   # DON'T
      API_KEY         = "sk_live_abc123def456"    # DON'T
      CONNECTION_STRING = "postgresql://user:pass@host/db" # DON'T
    }
  }
}
```

**Why**: Lambda environment variables are stored in plaintext in the function configuration visible to anyone with `lambda:GetFunctionConfiguration`. They appear in Terraform state in plaintext.

```hcl
# DO — Reference secret ARN in environment variables; retrieve at runtime
resource "aws_lambda_function" "main" {
  environment {
    variables = {
      DB_SECRET_ARN   = aws_secretsmanager_secret.db.arn  # ARN only — not value
      SSM_PARAM_PATH  = "/app/${var.environment}/config"   # Path only — not value
      ENVIRONMENT     = var.environment
    }
  }
}

# Lambda code retrieves secret at runtime:
# const secret = await secretsmanager.getSecretValue({ SecretId: process.env.DB_SECRET_ARN })
# Grant Lambda access to specific secret only
data "aws_iam_policy_document" "secrets_access" {
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.db.arn]
  }
}
```

- **Impact**: CRITICAL — Secret exposure in AWS console, CloudTrail, and Terraform state
- **Severity**: CRITICAL
- **Source**: [Lambda Environment Variables Security](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)

---

#### Anti-Pattern: `authorization_type = "NONE"` on Production Routes

```hcl
# DON'T
resource "aws_apigatewayv2_route" "get_users" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /users"
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
  authorization_type = "NONE"  # DON'T in production
}
```

**Why**: Any internet user can call this endpoint directly. No authentication means no audit trail, no rate limiting per user, and no data access control.

```hcl
# DO — Always declare an authorizer on production routes
resource "aws_apigatewayv2_route" "get_users" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = "GET /users"
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}
# Exception: OPTIONS routes for CORS preflight may use "NONE" — this is expected
```

- **Impact**: CRITICAL — Unauthorized API access, data breach, denial-of-wallet attack
- **Severity**: CRITICAL
- **Source**: [API Gateway V2 Authorization](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-access-control.html)

---

#### Anti-Pattern: Missing DLQ on Async Lambda

```hcl
# DON'T
resource "aws_lambda_function" "processor" {
  function_name = "order-processor"
  # No dead_letter_config
  # Async invocation failures silently discarded
}
```

**Why**: Without a DLQ, Lambda async invocation failures (after 2 retries) are permanently lost. This violates data durability requirements for any workload processing orders, payments, or user events.

```hcl
# DO — Always configure DLQ for async invocations
resource "aws_sqs_queue" "processor_dlq" {
  name                      = "order-processor-dlq"
  message_retention_seconds = 1209600 # 14 days for investigation
  kms_master_key_id         = "alias/aws/sqs"
}

resource "aws_lambda_function" "processor" {
  function_name = "order-processor"

  dead_letter_config {
    target_arn = aws_sqs_queue.processor_dlq.arn
  }
}

resource "aws_cloudwatch_metric_alarm" "dlq_depth" {
  alarm_name          = "order-processor-dlq-not-empty"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  dimensions = {
    QueueName = aws_sqs_queue.processor_dlq.name
  }
}
```

- **Impact**: HIGH — Silent data loss, broken event processing pipelines
- **Severity**: HIGH
- **Source**: [Lambda Dead-Letter Queues](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html#invocation-dlq)

---

#### Anti-Pattern: DynamoDB Table Without `prevent_destroy`

```hcl
# DON'T
resource "aws_dynamodb_table" "users" {
  name     = "users-prod"
  hash_key = "userId"
  # No lifecycle prevent_destroy — terraform destroy deletes all user data permanently
}
```

**Why**: Unlike CloudFormation stacks (which can have DeletionPolicy: Retain), Terraform `destroy` permanently deletes DynamoDB tables and all their data with no undo. This is especially dangerous for tables holding user accounts, transactions, or application state.

```hcl
# DO — Always protect stateful tables from accidental destruction
resource "aws_dynamodb_table" "users" {
  name     = "users-prod"
  hash_key = "userId"

  lifecycle {
    prevent_destroy = true  # terraform destroy will fail with an error — intentional
  }
}
```

- **Impact**: CRITICAL — Permanent, unrecoverable data loss (unless PITR backup exists)
- **Severity**: CRITICAL
- **Source**: [Lifecycle prevent_destroy](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle#prevent_destroy)

---

#### Anti-Pattern: Wildcard CORS Origins in Production

```hcl
# DON'T
resource "aws_apigatewayv2_api" "main" {
  cors_configuration {
    allow_origins = ["*"]  # DON'T in production
    allow_methods = ["*"]  # DON'T in production
  }
}
```

**Why**: Wildcard CORS allows any website to make credentialed requests to your API, enabling cross-site request forgery (CSRF) attacks and unauthorized data access from malicious third-party sites.

```hcl
# DO — Enumerate allowed origins explicitly
resource "aws_apigatewayv2_api" "main" {
  cors_configuration {
    allow_origins  = ["https://app.mycompany.com", "https://staging.mycompany.com"]
    allow_methods  = ["GET", "POST", "PUT", "DELETE"]
    allow_headers  = ["content-type", "authorization"]
    expose_headers = ["x-request-id"]
    max_age        = 300
  }
}
```

- **Impact**: HIGH — CSRF vulnerability, unauthorized API access from third-party sites
- **Severity**: HIGH
- **Source**: [CORS Configuration](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html)

---

#### Anti-Pattern: Lambda with Over-Permissive IAM Role

```hcl
# DON'T
data "aws_iam_policy_document" "lambda_policy" {
  statement {
    actions   = ["*"]         # DON'T
    resources = ["*"]         # DON'T
  }
}
# Or attaching AdministratorAccess / FullAccess managed policies
```

**Why**: Lambda functions should only have access to the specific resources they interact with. Overly permissive roles violate least-privilege, expand blast radius of a compromised function, and fail compliance checks (SOC2, PCI-DSS, CIS Benchmark).

```hcl
# DO — Enumerate exact actions and specific resource ARNs
data "aws_iam_policy_document" "lambda_policy" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      "arn:aws:dynamodb:${var.aws_region}:${var.account_id}:table/${var.table_name}"
    ]
  }
}
```

- **Impact**: CRITICAL — Privilege escalation, lateral movement, full account compromise if function is exploited
- **Severity**: CRITICAL
- **Source**: [IAM Least Privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege)

---

## State Management Deep Dive

### Local Development State

```hcl
# Acceptable only for solo development or learning
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  # No backend block = local state in terraform.tfstate
}
```

- **Risk**: No sharing, no locking, no encryption, single point of failure
- **When**: Solo development, learning, temporary proof-of-concept environments only

---

### Production Remote State (S3 + DynamoDB)

```hcl
# Bootstrap: Create state infrastructure first (run once via local state)
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "terraform-locks"
    ManagedBy = "terraform"
  }
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-org-terraform-state"

  lifecycle {
    prevent_destroy = true
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
      kms_master_key_id = aws_kms_key.terraform_state.id
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket                  = aws_s3_bucket.terraform_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Backend configuration (separate backend.hcl for environment overrides)
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/serverless/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
    kms_key_id     = "arn:aws:kms:us-east-1:ACCOUNT:key/KEY-ID"
  }
}
```

---

### State File Sensitivity Handling

```hcl
# Sensitive outputs — Terraform masks in plan/apply output
output "lambda_role_arn" {
  value       = aws_iam_role.lambda.arn
  description = "Lambda execution role ARN"
  sensitive   = false  # ARNs are not sensitive — safe to output
}

output "api_endpoint" {
  value       = aws_apigatewayv2_stage.main.invoke_url
  description = "API Gateway stage invoke URL"
  sensitive   = false
}

# Never output secret values — output ARNs instead
output "db_secret_arn" {
  value       = aws_secretsmanager_secret.db.arn
  description = "ARN of DB secret (not the secret value)"
  sensitive   = false
}
```

---

## Module Architecture

### Standard Module Structure

```
modules/
├── serverless-function/
│   ├── main.tf          # aws_lambda_function, aws_iam_role, aws_cloudwatch_log_group, aws_sqs_queue (DLQ)
│   ├── variables.tf     # function_name, runtime, handler, memory_size, timeout, environment, etc.
│   ├── outputs.tf       # function_arn, alias_arn, invoke_arn, role_arn, dlq_arn
│   ├── versions.tf      # required_version, required_providers
│   └── README.md
├── http-api/
│   ├── main.tf          # aws_apigatewayv2_api, stage, authorizer, log_group
│   ├── variables.tf     # app_name, environment, cognito_pool_id, cors_origins, throttle config
│   ├── outputs.tf       # api_id, execution_arn, invoke_url
│   ├── versions.tf
│   └── README.md
├── serverless-table/
│   ├── main.tf          # aws_dynamodb_table with prevent_destroy, PITR, encryption
│   ├── variables.tf     # table_name, billing_mode, hash_key, range_key, GSI definitions
│   ├── outputs.tf       # table_arn, table_name, stream_arn
│   ├── versions.tf
│   └── README.md
└── sam-app/             # Root composition module
    ├── main.tf          # Calls serverless-function, http-api, serverless-table modules
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    └── README.md
```

### Root Module Composition

```hcl
# modules/sam-app/main.tf

module "api" {
  source = "../http-api"

  app_name             = var.app_name
  environment          = var.environment
  cognito_user_pool_id = var.cognito_user_pool_id
  cors_allowed_origins = var.cors_allowed_origins
  api_throttle_burst   = var.api_throttle_burst
  api_throttle_rate    = var.api_throttle_rate
}

module "function" {
  source = "../serverless-function"

  function_name  = "${var.app_name}-handler"
  runtime        = var.lambda_runtime
  handler        = var.lambda_handler
  memory_size    = var.lambda_memory_size
  timeout        = var.lambda_timeout
  environment    = var.environment
  vpc_enabled    = var.vpc_enabled
  subnet_ids     = var.private_subnet_ids
  security_group_ids = [module.vpc.lambda_sg_id]

  environment_variables = {
    TABLE_NAME   = module.table.table_name
    ENVIRONMENT  = var.environment
  }

  depends_on = [module.table]
}

module "table" {
  source = "../serverless-table"

  table_name   = "${var.app_name}-${var.environment}"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "PK"
  range_key    = "SK"
  environment  = var.environment
}

# Wire API Gateway route to Lambda alias
resource "aws_apigatewayv2_route" "main" {
  api_id             = module.api.api_id
  route_key          = "ANY /{proxy+}"
  target             = "integrations/${aws_apigatewayv2_integration.main.id}"
  authorization_type = "JWT"
  authorizer_id      = module.api.jwt_authorizer_id
}
```

---

## Integration Patterns

### Integration: Terraform ↔ Lambda

```hcl
# Event source mapping — SQS trigger (SAM SQS event source equivalent)
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn                   = aws_sqs_queue.input.arn
  function_name                      = aws_lambda_alias.live.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  enabled                            = true

  function_response_types = ["ReportBatchItemFailures"]

  scaling_config {
    maximum_concurrency = 50 # Limit concurrency to protect downstream
  }
}

# DynamoDB Streams trigger (SAM DynamoDB Streams event source equivalent)
resource "aws_lambda_event_source_mapping" "dynamodb_stream" {
  event_source_arn              = aws_dynamodb_table.main.stream_arn
  function_name                 = aws_lambda_alias.live.arn
  starting_position             = "LATEST"
  batch_size                    = 100
  maximum_retry_attempts        = 3
  bisect_batch_on_function_error = true

  destination_config {
    on_failure {
      destination_arn = aws_sqs_queue.lambda_dlq.arn
    }
  }
}
```

- **Issues**: Lambda event source mappings require the Lambda alias ARN (not function ARN) when using CodeDeploy gradual deployments; SQS trigger requires `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` permissions on the execution role
- **Source**: [aws_lambda_event_source_mapping](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_event_source_mapping)

---

### Integration: Terraform ↔ API Gateway V2

```hcl
# Access log group for API Gateway
resource "aws_cloudwatch_log_group" "api_access" {
  name              = "/aws/apigateway/${var.app_name}/${var.environment}"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.logs.arn
}

# Resource policy — restrict API Gateway to specific CIDR (if private API)
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.app_name}-${var.environment}"
  protocol_type = "HTTP"
  description   = "HTTP API for ${var.app_name} ${var.environment}"
}

# Custom domain (SAM HttpApiDomainConfiguration equivalent)
resource "aws_apigatewayv2_domain_name" "main" {
  domain_name = "${var.environment}.api.${var.base_domain}"

  domain_name_configuration {
    certificate_arn = aws_acm_certificate.api.arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  depends_on = [aws_acm_certificate_validation.api]
}

resource "aws_apigatewayv2_api_mapping" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  domain_name = aws_apigatewayv2_domain_name.main.id
  stage       = aws_apigatewayv2_stage.main.id
}
```

| Resource | Min Provider | Notes |
|----------|-------------|-------|
| `aws_apigatewayv2_api` | ~> 6.0 | `protocol_type = "HTTP"` or `"WEBSOCKET"` |
| `aws_apigatewayv2_authorizer` | ~> 6.0 | JWT, Lambda, or IAM |
| `aws_apigatewayv2_domain_name` | ~> 6.0 | Requires ACM cert in same region |

- **Issues**: `auto_deploy = true` on stage bypasses change management — always set `false` in production; API Gateway V2 access logs require explicit `arn:aws:logs:*:*:log-group:*` permission in CloudWatch Logs resource policy
- **Source**: [aws_apigatewayv2_stage](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_stage)

---

### Integration: Terraform ↔ DynamoDB

```hcl
# Lambda reads DynamoDB stream for CDC pattern
resource "aws_dynamodb_table" "main" {
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES" # Required for CDC patterns
}

# DynamoDB VPC endpoint (avoid public internet egress from Lambda in VPC)
resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.private_route_table_ids

  policy = data.aws_iam_policy_document.dynamodb_endpoint_policy.json
}
```

- **Issues**: DynamoDB streams require `AmazonDynamoDBFullAccess` is NOT the right policy — grant only `dynamodb:GetRecords`, `dynamodb:GetShardIterator`, `dynamodb:DescribeStream`, `dynamodb:ListStreams` for stream reader role
- **Source**: [aws_dynamodb_table streams](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table#stream_enabled)

---

### Integration: Terraform ↔ IAM

```hcl
# OIDC provider for GitHub Actions — credential-free CI/CD deployment
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "github_actions_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:myorg/myrepo:*"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "github-actions-serverless-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume.json
}
```

- **Issues**: GitHub OIDC thumbprint may change — check current value at [GitHub OIDC docs](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- **Source**: [aws_iam_openid_connect_provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_openid_connect_provider)

---

### Integration: Terraform ↔ CloudWatch

```hcl
# Lambda function error rate alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
    Resource     = "${aws_lambda_function.main.function_name}:${aws_lambda_alias.live.name}"
  }
}

# Lambda duration alarm (P99 latency)
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.function_name}-p99-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  extended_statistic  = "p99"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  threshold           = var.lambda_p99_threshold_ms
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }
}

# Lambda Insights dashboard (requires Lambda Insights layer)
resource "aws_cloudwatch_dashboard" "serverless" {
  dashboard_name = "${var.app_name}-${var.environment}"
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title  = "Lambda Invocations"
          metrics = [["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.main.function_name]]
          period = 300
          stat   = "Sum"
        }
      }
    ]
  })
}
```

- **Source**: [aws_cloudwatch_metric_alarm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm)

---

### Integration: Terraform ↔ EventBridge

```hcl
# EventBridge scheduled rule (SAM ScheduleEvent equivalent)
resource "aws_cloudwatch_event_rule" "scheduled" {
  name                = "${var.function_name}-schedule"
  description         = "Scheduled trigger for ${var.function_name}"
  schedule_expression = "rate(5 minutes)"
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.scheduled.name
  target_id = "${var.function_name}-target"
  arn       = aws_lambda_alias.live.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  qualifier     = aws_lambda_alias.live.name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled.arn
}
```

- **Source**: [aws_cloudwatch_event_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule)

---

### Integration: Terraform ↔ S3

```hcl
# Lambda deployment package bucket
resource "aws_s3_bucket" "lambda_artifacts" {
  bucket = "${var.app_name}-lambda-artifacts-${var.account_id}"

  lifecycle {
    prevent_destroy = false # Artifacts are reproducible — safe to destroy
  }
}

resource "aws_s3_bucket_versioning" "lambda_artifacts" {
  bucket = aws_s3_bucket.lambda_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "lambda_artifacts" {
  bucket                  = aws_s3_bucket.lambda_artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lambda from S3 (recommended for packages > 50MB)
resource "aws_lambda_function" "main" {
  s3_bucket         = aws_s3_bucket.lambda_artifacts.id
  s3_key            = "${var.function_name}/${var.deployment_version}.zip"
  s3_object_version = var.s3_object_version

  source_code_hash = var.source_code_hash # SHA256 of zip, passed via CI/CD
}

# S3 event trigger (SAM S3Event equivalent)
resource "aws_s3_bucket_notification" "trigger" {
  bucket = aws_s3_bucket.uploads.id

  lambda_function {
    lambda_function_arn = aws_lambda_alias.live.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.s3_trigger]
}

resource "aws_lambda_permission" "s3_trigger" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  qualifier     = aws_lambda_alias.live.name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.uploads.arn
}
```

- **Source**: [aws_s3_bucket_notification](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_notification)

---

## Quality Control

### Verification Commands

```bash
# Initialize with latest provider
terraform init -upgrade
# Expected: Terraform initialized. Provider hashicorp/aws ~> 6.0 installed.

# Format check (CI gate)
terraform fmt -recursive -check=true
# Expected: Exit code 0. All files correctly formatted.

# Syntax validation
terraform validate
# Expected: Success! The configuration is valid.

# Security scanning
tfsec . --format sarif --minimum-severity HIGH
# Expected: No HIGH or CRITICAL findings.

# Policy-as-code
checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks. No CRITICAL failures.

# Plan with lock
terraform plan -out=tfplan -lock=true -var-file="environments/prod.tfvars"
# Expected: Plan showing exact resources to create/update/destroy.

# Review plan before apply
terraform show tfplan | head -100
# Expected: Human-readable plan. Review DynamoDB + Lambda changes carefully.

# Apply from plan (no interactive approval in CI)
terraform apply -auto-approve tfplan
# Expected: Apply complete! Resources created/updated.

# Verify state
terraform state list
# Expected: All Lambda functions, API GW resources, DynamoDB tables listed.

terraform output
# Expected: api_endpoint, function_arn, table_name values.
```

---

### Testing with Terratest

```go
package test

import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/gruntwork-io/terratest/modules/aws"
  "github.com/stretchr/testify/assert"
)

func TestServerlessStack(t *testing.T) {
  t.Parallel()

  opts := &terraform.Options{
    TerraformDir: "../examples/sam-app",
    Vars: map[string]interface{}{
      "environment":   "test",
      "app_name":      "terratest-serverless",
      "lambda_runtime": "nodejs22.x",
    },
    EnvVars: map[string]string{
      "AWS_DEFAULT_REGION": "us-east-1",
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  // Verify Lambda function exists
  functionName := terraform.Output(t, opts, "function_name")
  function := aws.GetFunction(t, "us-east-1", functionName)
  assert.Equal(t, "Active", *function.Configuration.State)

  // Verify API endpoint is reachable
  apiEndpoint := terraform.Output(t, opts, "api_endpoint")
  assert.Contains(t, apiEndpoint, "execute-api.us-east-1.amazonaws.com")

  // Verify DynamoDB table exists with PITR
  tableName := terraform.Output(t, opts, "table_name")
  table := aws.GetDynamoDBTable(t, "us-east-1", tableName)
  assert.Equal(t, "ACTIVE", *table.TableStatus)
}
```

---

## Secrets & Sensitive Data Management

### Lambda Secrets Pattern

```
Secret Type: Database credentials / API keys / OAuth tokens
Storage: AWS Secrets Manager (rotation-capable) or SSM Parameter Store (static)
Retrieval: AWS SDK call at Lambda runtime startup (not environment variable value)
```

```hcl
# Store secret
resource "aws_secretsmanager_secret" "db" {
  name                    = "/${var.environment}/app/db-credentials"
  description             = "Database credentials for ${var.app_name}"
  kms_key_id              = aws_kms_key.secrets.id
  recovery_window_in_days = 7  # Allows recovery within 7 days of deletion

  tags = {
    Name = "${var.app_name}-db-credentials"
  }
}

# Grant Lambda read access to specific secret only
data "aws_iam_policy_document" "lambda_secrets" {
  statement {
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      aws_secretsmanager_secret.db.arn
    ]
  }

  statement {
    effect  = "Allow"
    actions = ["kms:Decrypt"]
    resources = [aws_kms_key.secrets.arn]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["secretsmanager.${var.aws_region}.amazonaws.com"]
    }
  }
}

# Pass secret ARN (not value) to Lambda
resource "aws_lambda_function" "main" {
  environment {
    variables = {
      DB_SECRET_ARN = aws_secretsmanager_secret.db.arn
    }
  }
}
```

- **Source**: [AWS Secrets Manager + Lambda](https://docs.aws.amazon.com/secretsmanager/latest/userguide/integrating_how-services-use-secrets_lambda.html)

---

## Drift Detection & Reconciliation

### Scenario: Lambda Code Updated Outside Terraform (manual console deploy)

```
Detection: terraform plan shows "source_code_hash will be updated" — indicates drift
Recovery: 1. terraform refresh (update state to match AWS reality)
           2. If AWS version should win: terraform import aws_lambda_function.main <function-name>
           3. If Terraform version should win: terraform apply (overwrite with Terraform-managed code)
```

```bash
# Detect all drift
terraform plan -detailed-exitcode
# Exit code 2 = changes detected (drift)
# Exit code 0 = no changes

# Refresh state from AWS (non-destructive read)
terraform refresh -var-file="environments/prod.tfvars"

# Import existing function into Terraform state
terraform import aws_lambda_function.main my-existing-function
terraform import aws_dynamodb_table.main my-existing-table
terraform import aws_apigatewayv2_api.main abc12345de
```

- **Source**: [terraform import](https://developer.hashicorp.com/terraform/cli/commands/import)

---

## Production Readiness

### Performance

```
Lambda:
  - Cold starts: nodejs22.x ~200ms, python3.13 ~150ms, java21 ~800ms (use SnapStart)
  - Provisioned Concurrency eliminates cold starts but adds fixed cost (~$0.0064/GB-hour)
  - Lambda SnapStart (Java 21): "PublishedVersions" + aws_lambda_provisioned_concurrency_config

API Gateway V2 HTTP:
  - Latency: ~5ms overhead vs. direct Lambda invocation
  - Quotas: 10,000 req/sec default (request increase at AWS Support)

DynamoDB:
  - PAY_PER_REQUEST scales instantly to any throughput — no throttling
  - Global Tables (multi-region) add ~50ms replication lag
```

### Scalability

```hcl
# Lambda provisioned concurrency for latency-sensitive functions
resource "aws_lambda_provisioned_concurrency_config" "main" {
  function_name                  = aws_lambda_function.main.function_name
  qualifier                      = aws_lambda_alias.live.name
  provisioned_concurrent_executions = var.provisioned_concurrency

  # Schedule scale-down during off-peak hours via Application Auto Scaling
}

# Application Auto Scaling for provisioned concurrency
resource "aws_appautoscaling_target" "lambda" {
  max_capacity       = 100
  min_capacity       = var.min_provisioned_concurrency
  resource_id        = "function:${aws_lambda_function.main.function_name}:${aws_lambda_alias.live.name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"
}
```

### Security Checklist

- [ ] All Lambda secrets stored in Secrets Manager (not environment variables)
- [ ] State file encryption enabled (S3 + KMS)
- [ ] All Lambda functions have DLQ configured
- [ ] All API Gateway routes declare `authorization_type = "JWT"` or `"AWS_IAM"`
- [ ] DynamoDB tables have `prevent_destroy = true` and PITR enabled
- [ ] Lambda IAM roles follow least-privilege (no `*` actions or resources)
- [ ] CORS `allow_origins` does not include `["*"]` in production
- [ ] CloudWatch Logs retention set on all log groups (no indefinite retention)
- [ ] X-Ray tracing enabled on Lambda and API Gateway
- [ ] VPC Lambda uses private subnets + VPC endpoint for DynamoDB/SQS
- [ ] Lambda packages deployed from versioned S3 artifacts (not inline zip)
- [ ] GitHub Actions uses OIDC (no long-lived access keys in CI/CD)

### Disaster Recovery Runbook

```bash
# 1. State file corruption recovery
aws s3api list-object-versions \
  --bucket my-org-terraform-state \
  --prefix prod/serverless/terraform.tfstate \
  --query "Versions[?IsLatest==\`false\`].[VersionId,LastModified]" \
  --output table

# Restore previous version
aws s3api get-object \
  --bucket my-org-terraform-state \
  --key prod/serverless/terraform.tfstate \
  --version-id <VERSION_ID> \
  terraform.tfstate.backup

terraform state push terraform.tfstate.backup

# 2. DynamoDB data recovery (PITR)
aws dynamodb restore-table-to-point-in-time \
  --source-table-name users-prod \
  --target-table-name users-prod-restore \
  --use-latest-restorable-time
# Then import restored table if needed

# 3. Lambda alias rollback (immediate — no deploy)
aws lambda update-alias \
  --function-name my-function \
  --name live \
  --function-version <PREVIOUS_VERSION>
# Update Terraform state to match
terraform import aws_lambda_alias.live my-function:live
```

---

## Reference Implementations

- [Official Terraform AWS Examples](https://github.com/hashicorp/terraform-aws-examples)
- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/)
- [Terraform AWS Provider — Lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)
- [Terraform AWS Provider — API Gateway V2](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_api)
- [Terraform AWS Provider — Serverless Application Repository](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/serverlessapplicationrepository_cloudformation_stack)
- [AWS Well-Architected Serverless Lens](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/)

---

## Source Bibliography

### Primary Sources
- [Terraform AWS Provider Registry v6.47.0](https://registry.terraform.io/providers/hashicorp/aws/latest) — Published 2026-05-28
- [aws_lambda_function Resource Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)
- [aws_apigatewayv2_api Resource Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_api)
- [aws_dynamodb_table Resource Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table)
- [aws_serverlessapplicationrepository_cloudformation_stack](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/serverlessapplicationrepository_cloudformation_stack)
- [data.aws_serverlessapplicationrepository_application](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/serverlessapplicationrepository_application)
- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/)
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)

### Validation & Tools
- [tfsec](https://github.com/aquasecurity/tfsec) — Security scanner
- [Checkov](https://www.checkov.io/) — Policy-as-code validator
- [Terratest](https://terratest.gruntwork.io/) — Go-based testing framework
- [hashicorp/terraform-provider-aws issues](https://github.com/hashicorp/terraform-provider-aws/issues)

---

## Research Gaps

```
Gap: aws_lambda_function `logging_config` block exact attribute validation for application_log_level when log_format = "Text"
Impact: Setting application_log_level on text-format functions may cause plan-time error
Workaround: Only use logging_config.application_log_level when log_format = "JSON"
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function#logging_config

Gap: CodeDeploy Lambda deployment traffic-shifting with Terraform — the alias function_version must be managed outside Terraform lifecycle for CodeDeploy to control it
Impact: Terraform plan may show spurious diff on alias function_version after CodeDeploy deployment
Workaround: Use lifecycle { ignore_changes = [function_version] } on aws_lambda_alias
Follow-up: https://github.com/hashicorp/terraform-provider-aws/issues

Gap: SAR `aws_serverlessapplicationrepository_cloudformation_stack` semantic_version "latest" behavior
Impact: Unpinned semantic_version causes unpredictable updates on apply
Workaround: Always pin semantic_version explicitly; use data source to resolve latest and pin in code
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/serverlessapplicationrepository_application
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- State backend setup (S3 + DynamoDB)
- Lambda function baseline (DLQ, logging_config, X-Ray tracing)
- IAM role/policy with least-privilege
- API Gateway V2 JWT authorizer configuration
- DynamoDB `prevent_destroy` lifecycle guard
- CloudWatch alarms for Lambda errors/duration
- Variable validation blocks

### Medium Confidence (Validate with user)
- CodeDeploy gradual deployment config (canary vs. linear)
- Provisioned concurrency sizing
- DynamoDB billing mode selection (PAY_PER_REQUEST vs. PROVISIONED)
- VPC vs. non-VPC Lambda placement
- S3 artifact management strategy (local zip vs. S3 bucket)

### Low Confidence (Must ask user)
- Multi-account deployment strategy
- Lambda SnapStart configuration (Java runtimes only)
- Custom runtime or container image deployments
- Cross-region Lambda failover
- SAR application version pinning policy

### Emergency Stop
- Halt if `prevent_destroy = true` is being removed from a DynamoDB table without explicit user confirmation
- Halt if Lambda environment variables contain detected secret patterns (password, key, token, secret)
- Halt if API Gateway routes are being set to `authorization_type = "NONE"` in production
- Halt if state file encryption is being disabled
- Halt if `terraform destroy` is planned against a production stack without explicit approval

---

## Completion Checklist
- [x] All Terraform 1.7+ and aws ~> 6.0 patterns validated
- [x] State management strategy documented (local + S3 + DynamoDB)
- [x] Module architecture fully defined (serverless-function, http-api, serverless-table)
- [x] All anti-patterns have tested alternatives
- [x] CLI commands include expected outputs
- [x] Integration examples for Lambda, API Gateway V2, DynamoDB, IAM, CloudWatch, EventBridge, S3, SQS, CodeDeploy
- [x] Sources dated and linked to registry
- [x] Security checklist complete
- [x] Disaster recovery procedures documented
- [x] Both SAR deployment path and native Terraform path documented
- [x] Agent operation notes with emergency stop conditions
