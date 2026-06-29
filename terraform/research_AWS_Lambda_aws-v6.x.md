# Terraform AWS Lambda — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - Lambda"
Cloud_Provider: "AWS"
Target_Service: "Lambda (Function, Permission, Event Source Mapping, Alias, Layer, URL)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-29)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-29"
Research_Date: "2026-05-29"
Domain_Complexity: "Complex"
New_V6_Resources_Noted: >
  aws_lambda_capacity_provider (warm Graviton pools),
  capacity_provider_config block, durable_config block (limited regions),
  tenancy_config block, ipv6_allowed_for_dual_stack in vpc_config,
  logging_config with JSON log format + application_log_level/system_log_level,
  response_streaming_invoke_arn attribute, publish_to attribute,
  identity-based import blocks (Terraform >= 1.12.0)
```

---

## Executive Summary

AWS Lambda is the foundational serverless compute service that executes code in response to events without provisioning or managing servers. In Terraform, Lambda is managed through a rich resource namespace (`aws_lambda_*`) covering functions, permissions, event-source mappings, aliases, layers, function URLs, provisioned concurrency, and the new capacity providers. The AWS provider v6.x introduces several significant additions: the `aws_lambda_capacity_provider` resource for managed warm Graviton pools; the `logging_config` block with structured JSON logging, per-level application and system log filtering; `durable_config` for stateful long-running executions (limited regions); `capacity_provider_config` as an alternative to traditional `vpc_config`; and `response_streaming_invoke_arn` for streaming API Gateway integrations. Provider constraint `~> 6.0` is required to access all v6.x features; `>= 5.0, < 7.0` is the minimum acceptable range.

Lambda deployments in Terraform carry three categories of non-negotiable safety requirements. **Execution role hygiene**: every Lambda function requires an IAM role (`aws_iam_role`) with a precise trust policy (`lambda.amazonaws.com`) and only the permissions required by that function — no wildcard actions, no `arn:aws:*:*:*` resources in production. **CloudWatch log group pre-creation**: if a log group is not declared as `aws_cloudwatch_log_group` with explicit retention, Lambda auto-creates an immortal log group with no retention policy that Terraform cannot manage, cannot delete, and will cause `depends_on` drift. **Code change detection via `code_sha256`**: using `source_code_hash` alone will not detect out-of-band changes to the deployment package; `code_sha256` (base64-encoded SHA-256 of the zip or image digest) must be used for immutable deployments. VPC-attached Lambda functions can take up to 45 minutes to delete due to ENI lifecycle management — this is an AWS platform constraint, not a Terraform bug.

This service is classified **Complex** due to the multi-resource dependency chains (function → role → log group → permissions → event sources), security-critical IAM scope, three distinct deployment package formats (Zip/S3/Image), versioning and alias state management, VPC/ENI lifecycle sensitivity, and the breadth of supported event sources (API Gateway, SQS, SNS, DynamoDB Streams, Kinesis, EventBridge, S3, MSK, MQ, DocumentDB).

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Ensures reproducibility, prevents accidental provider upgrades that break Lambda configuration, and defines the deployment contract for all team members and CI pipelines. Terraform >= 1.7 is required for the `terraform test` framework and enhanced import block support.

```hcl
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }

  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/lambda/terraform.tfstate"
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

**Why**: Credentials must never be hardcoded. `assume_role` enables cross-account deployments and CI/CD pipelines without static credentials. `default_tags` enforces tagging compliance on all Lambda resources.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "TerraformLambdaDeploy"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
      Service     = "lambda"
    }
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [AWS Provider Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference)

---

#### Pattern: IAM Execution Role with Least-Privilege Trust Policy

**Why**: The execution role is the function's identity. Over-permissioned roles are the primary Lambda attack surface. Use `aws_iam_policy_document` (type-safe, no JSON string manipulation) and scope every action to specific resources. The trust policy must be exactly `lambda.amazonaws.com` — no wildcards.

```hcl
# Trust policy — only Lambda service may assume this role
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

resource "aws_iam_role" "lambda_exec" {
  name               = "${var.function_name}-exec-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = {
    Name = "${var.function_name}-exec-role"
  }
}

# Minimal baseline: only the specific log group this function writes to
data "aws_iam_policy_document" "lambda_logging" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "${aws_cloudwatch_log_group.function.arn}:*",
    ]
  }
}

resource "aws_iam_policy" "lambda_logging" {
  name        = "${var.function_name}-logging-${var.environment}"
  description = "Minimal CloudWatch Logs write access for ${var.function_name}"
  policy      = data.aws_iam_policy_document.lambda_logging.json
}

resource "aws_iam_role_policy_attachment" "lambda_logging" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_iam_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | [Lambda Permission Model](https://docs.aws.amazon.com/lambda/latest/dg/intro-permission-model.html)

---

#### Pattern: CloudWatch Log Group Pre-Creation with Retention

**Why**: If Terraform does not manage the log group, Lambda auto-creates one with no retention policy (logs accumulate forever, no cost control, no `depends_on` ordering). Pre-creating it gives Terraform lifecycle control, enforces retention, and enables `depends_on` ordering to prevent race conditions on first deploy.

```hcl
resource "aws_cloudwatch_log_group" "function" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days  # 7, 14, 30, 60, 90, 120, 150, 180, 365

  # Encrypt logs with KMS for compliance
  kms_key_id = var.kms_key_arn

  tags = {
    Name        = "/aws/lambda/${var.function_name}"
    Environment = var.environment
  }
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention in days"
  default     = 14

  validation {
    condition = contains(
      [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653],
      var.log_retention_days
    )
    error_message = "log_retention_days must be a valid CloudWatch retention period value."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_cloudwatch_log_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | [Lambda Logging](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html)

---

#### Pattern: Lambda Function with Structured Logging and X-Ray Tracing (v6.x)

**Why**: `logging_config` (v6.x) replaces the unstructured log approach — JSON format enables CloudWatch Insights queries, log-level filtering reduces noise and cost, and `system_log_level = "WARN"` eliminates platform noise from production dashboards. `tracing_config.mode = "Active"` is mandatory for production latency diagnosis — without it, cold starts and downstream service latency are invisible.

```hcl
resource "aws_lambda_function" "main" {
  function_name = var.function_name
  role          = aws_iam_role.lambda_exec.arn

  # Deployment package
  filename      = data.archive_file.function.output_path
  handler       = var.handler
  runtime       = var.runtime
  architectures = ["arm64"]  # Graviton: ~20% better price/performance

  # Change detection — required for immutable deploys
  code_sha256 = data.archive_file.function.output_base64sha256

  # Performance
  memory_size = var.memory_size
  timeout     = var.timeout

  # Ephemeral storage (default 512MB, max 10240MB)
  ephemeral_storage {
    size = var.ephemeral_storage_mb
  }

  # Environment variables (encrypted at rest by KMS)
  environment {
    variables = var.environment_variables
  }

  # Encrypt environment variables with customer-managed KMS key
  kms_key_arn = var.kms_key_arn

  # Structured logging — v6.x feature
  logging_config {
    log_format            = "JSON"
    log_group             = aws_cloudwatch_log_group.function.name
    application_log_level = "INFO"   # Application code logs: TRACE|DEBUG|INFO|WARN|ERROR|FATAL
    system_log_level      = "WARN"   # Platform logs: DEBUG|INFO|WARN
  }

  # X-Ray distributed tracing
  tracing_config {
    mode = "Active"  # PassThrough only for dev/cost-sensitive
  }

  # Dead letter queue for async invocations
  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }

  # Ordering guarantees
  depends_on = [
    aws_iam_role_policy_attachment.lambda_logging,
    aws_cloudwatch_log_group.function,
  ]

  tags = {
    Name        = var.function_name
    Environment = var.environment
  }

  lifecycle {
    ignore_changes = [
      # Prevent Terraform from overwriting image_uri managed by CI/CD
      # Remove this if Terraform owns the deployment pipeline
    ]
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_lambda_function](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)

---

#### Pattern: Variable Validation and Type Safety

**Why**: Prevents misconfigured Lambda functions at `terraform plan` time — before any AWS API call. Invalid `runtime`, out-of-range `memory_size`, or malformed function names fail immediately with a descriptive error rather than a cryptic AWS API error during apply.

```hcl
variable "function_name" {
  type        = string
  description = "Lambda function name (1-64 chars, alphanumeric, hyphens, underscores)"

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]{1,64}$", var.function_name))
    error_message = "function_name must be 1-64 characters: letters, digits, hyphens, underscores."
  }
}

variable "runtime" {
  type        = string
  description = "Lambda runtime identifier"
  default     = "python3.12"

  validation {
    condition = contains([
      "nodejs22.x", "nodejs24.x",
      "python3.12", "python3.13",
      "java21",
      "dotnet8",
      "provided.al2", "provided.al2023",
    ], var.runtime)
    error_message = "runtime must be a currently supported non-deprecated Lambda runtime."
  }
}

variable "memory_size" {
  type        = number
  description = "Lambda function memory in MB (128-32768, 1MB increments)"
  default     = 256

  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 32768 && floor(var.memory_size) == var.memory_size
    error_message = "memory_size must be an integer between 128 and 32768 MB."
  }
}

variable "timeout" {
  type        = number
  description = "Lambda function timeout in seconds (1-900)"
  default     = 30

  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "timeout must be between 1 and 900 seconds."
  }
}

variable "ephemeral_storage_mb" {
  type        = number
  description = "Ephemeral /tmp storage in MB (512-10240)"
  default     = 512

  validation {
    condition     = var.ephemeral_storage_mb >= 512 && var.ephemeral_storage_mb <= 10240
    error_message = "ephemeral_storage_mb must be between 512 and 10240 MB."
  }
}

variable "environment_variables" {
  type        = map(string)
  description = "Lambda environment variables. Never include secrets — use Secrets Manager references."
  default     = {}
  sensitive   = false  # Values themselves are not sensitive; use Secrets Manager for secrets
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules) | [Lambda Runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)

---

#### Pattern: Lambda Permission for External Invocation Sources

**Why**: `aws_lambda_permission` is the only correct mechanism to grant external services (API Gateway, EventBridge, SNS, S3) permission to invoke a function. Using a resource-based policy directly (via `aws_lambda_function` + `policy` attribute) bypasses Terraform lifecycle management and cannot be drift-detected. `source_arn` must always be specified to prevent confused-deputy attacks — without it, any principal of the given service can invoke your function.

```hcl
# API Gateway → Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "apigateway.amazonaws.com"

  # Scope to specific API — prevents cross-API invocation
  source_arn = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# EventBridge → Lambda
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "events.amazonaws.com"

  # Scope to specific rule
  source_arn = aws_cloudwatch_event_rule.schedule.arn

  lifecycle {
    # Recreate permission if function changes (e.g., new version published)
    replace_triggered_by = [aws_lambda_function.main]
  }
}

# SNS → Lambda
resource "aws_lambda_permission" "sns" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.events.arn
}

# S3 → Lambda
resource "aws_lambda_permission" "s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.source.arn
  source_account = data.aws_caller_identity.current.account_id  # Confused-deputy protection
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_lambda_permission](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | [Lambda Permission Model](https://docs.aws.amazon.com/lambda/latest/dg/intro-permission-model.html)

---

#### Pattern: Async Invocation Error Handling with DLQ and Event Invoke Config

**Why**: Lambda async invocations silently discard failures after the default 2 retries unless a DLQ or destination is configured. Without `aws_lambda_function_event_invoke_config`, failed events are irrecoverably lost. Every function invoked asynchronously (EventBridge, S3, SNS) must have a DLQ and explicit retry policy.

```hcl
# Dead letter queue for failed async invocations
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.function_name}-dlq-${var.environment}"
  message_retention_seconds = 1209600  # 14 days
  kms_master_key_id         = var.kms_key_id

  tags = {
    Name        = "${var.function_name}-dlq"
    Environment = var.environment
  }
}

resource "aws_sqs_queue_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.dlq.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_lambda_function.main.arn
        }
      }
    }]
  })
}

# Async invocation config — retries and destinations
resource "aws_lambda_function_event_invoke_config" "main" {
  function_name = aws_lambda_function.main.function_name

  maximum_event_age_in_seconds = 300  # 5 minutes max queue time
  maximum_retry_attempts       = 1    # 0 = fail fast, 1 = one retry, 2 = default

  destination_config {
    on_failure {
      destination = aws_sqs_queue.dlq.arn
    }
    on_success {
      destination = aws_sns_topic.success_notifications.arn  # optional
    }
  }
}

# Grant Lambda permission to send to DLQ
data "aws_iam_policy_document" "dlq_send" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dlq.arn]
  }
}

resource "aws_iam_role_policy" "dlq_send" {
  name   = "dlq-send"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.dlq_send.json
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_lambda_function_event_invoke_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function_event_invoke_config) | [Lambda Async Invocation](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html)

---

#### Pattern: Versioning, Aliases, and Provisioned Concurrency

**Why**: Lambda aliases (`LIVE`, `BLUE`, `GREEN`) decouple deployment from traffic shift, enabling zero-downtime deploys. `publish = true` creates immutable numbered versions — required for provisioned concurrency and safe canary routing. Without aliases, Lambda function ARNs in event source mappings and permissions must be updated on every deploy, causing unnecessary resource recreation and potential outage windows.

```hcl
resource "aws_lambda_function" "main" {
  function_name = var.function_name
  role          = aws_iam_role.lambda_exec.arn
  filename      = data.archive_file.function.output_path
  handler       = var.handler
  runtime       = var.runtime
  code_sha256   = data.archive_file.function.output_base64sha256

  publish = true  # Required for versioning and provisioned concurrency
}

# Stable alias — points to the current production version
resource "aws_lambda_alias" "live" {
  name             = "live"
  description      = "Production alias — update function_version to shift traffic"
  function_name    = aws_lambda_function.main.function_name
  function_version = aws_lambda_function.main.version

  # Weighted routing for canary deploys (e.g., 10% to new version)
  routing_config {
    additional_version_weights = {
      (var.canary_version) = var.canary_weight  # e.g., "5" = 0.1
    }
  }
}

# Provisioned concurrency — eliminates cold starts for latency-sensitive paths
resource "aws_lambda_provisioned_concurrency_config" "main" {
  count = var.enable_provisioned_concurrency ? 1 : 0

  function_name                  = aws_lambda_function.main.function_name
  qualifier                      = aws_lambda_alias.live.name
  provisioned_concurrent_executions = var.provisioned_concurrency

  depends_on = [aws_lambda_alias.live]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_lambda_alias](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_alias) | [aws_lambda_provisioned_concurrency_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_provisioned_concurrency_config)

---

#### Pattern: Outputs for Stack Interdependencies

**Why**: Lambda ARNs, invoke ARNs, and role ARNs are consumed by multiple stacks (API Gateway, EventBridge, Step Functions). Without structured outputs, downstream stacks use hardcoded ARNs that drift from reality when functions are recreated.

```hcl
output "function_arn" {
  value       = aws_lambda_function.main.arn
  description = "ARN of the Lambda function (latest unpublished)"
}

output "function_name" {
  value       = aws_lambda_function.main.function_name
  description = "Lambda function name for use in aws_lambda_permission resources"
}

output "invoke_arn" {
  value       = aws_lambda_function.main.invoke_arn
  description = "ARN for API Gateway integration (aws_api_gateway_integration.uri)"
}

output "qualified_invoke_arn" {
  value       = aws_lambda_function.main.qualified_invoke_arn
  description = "Version-qualified invoke ARN for API Gateway with Lambda versioning"
}

output "response_streaming_invoke_arn" {
  value       = aws_lambda_function.main.response_streaming_invoke_arn
  description = "Streaming invoke ARN for API Gateway response streaming integrations (v6.x)"
}

output "alias_arn" {
  value       = aws_lambda_alias.live.arn
  description = "ARN of the live alias — use this in event source mappings and permissions"
}

output "execution_role_arn" {
  value       = aws_iam_role.lambda_exec.arn
  description = "IAM execution role ARN for cross-stack IAM policy references"
}

output "dlq_arn" {
  value       = aws_sqs_queue.dlq.arn
  description = "DLQ ARN for monitoring alarm configuration"
}

output "log_group_name" {
  value       = aws_cloudwatch_log_group.function.name
  description = "CloudWatch log group for metric filters and subscriptions"
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Terraform Outputs](https://developer.hashicorp.com/terraform/language/values/outputs)

---

### ⚠️ Conditional Patterns (Ask First)

---

#### Decision: Zip File vs. S3 Object vs. Container Image Deployment

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **`filename` (local zip)** | Simplicity, no S3 dependency | Large files, CI/CD S3 upload workflow | Small functions, local dev, < 50 MB packages |
| **S3 object (`s3_bucket` + `s3_key`)** | Large packages (up to 250 MB unzipped), CI/CD versioning, separate artifact and infra repos | Extra S3 resource, `source_code_hash` must be set explicitly | Most production use cases; Lambda recommends S3 for large packages |
| **Container image (`image_uri`, `package_type = "Image"`)** | Up to 10 GB, custom runtimes, system dependencies, consistent local/cloud environment | ECR dependency, cold start overhead (larger images), `handler` not set | ML workloads, complex system deps, polyglot runtimes, arm64 Graviton containers |

```hcl
# Option A: Local Zip (simple, <50MB)
data "archive_file" "function" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/.build/function.zip"
}

resource "aws_lambda_function" "zip_local" {
  filename    = data.archive_file.function.output_path
  code_sha256 = data.archive_file.function.output_base64sha256
  # ...
}

# Option B: S3 Object (recommended for production)
resource "aws_s3_object" "function_code" {
  bucket = aws_s3_bucket.artifacts.id
  key    = "lambda/${var.function_name}/${var.version}.zip"
  source = data.archive_file.function.output_path
  etag   = filemd5(data.archive_file.function.output_path)
}

resource "aws_lambda_function" "zip_s3" {
  s3_bucket         = aws_s3_object.function_code.bucket
  s3_key            = aws_s3_object.function_code.key
  s3_object_version = aws_s3_object.function_code.version_id
  source_code_hash  = data.archive_file.function.output_base64sha256
  # ...
}

# Option C: Container Image
resource "aws_lambda_function" "container" {
  function_name = var.function_name
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.function.repository_url}:${var.image_tag}"
  architectures = ["arm64"]

  image_config {
    entry_point = ["/lambda-entrypoint.sh"]
    command     = ["app.handler"]
  }

  memory_size = 1024
  timeout     = 60
}
```

- **Agent**: "Ask user: What is the unzipped package size? Are there non-standard system dependencies? Does CI/CD own the image build, or does Terraform?"
- **Source**: [Specifying the Deployment Package](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function#specifying-the-deployment-package)

---

#### Decision: VPC Attachment vs. No VPC

| Option | Optimizes | Sacrifices | Scaling | Cold Start | Use When |
|--------|-----------|------------|---------|------------|----------|
| **No VPC** | Cold start latency, simplicity | Direct VPC resource access | Unlimited burst | ~100ms | Public API, stateless processing, public AWS services via SDK |
| **VPC attached** | Private resource access (RDS, ElastiCache, internal ALB) | Cold start +500ms (ENI), 45-min delete timeout, NAT required for internet | VPC IP limits | ~600ms+ | Needs RDS, ElastiCache, internal services, private endpoints |
| **VPC + PrivateLink** | Both private access + no internet egress cost | PrivateLink endpoint cost per service | Same as VPC | Same | Compliance, no-internet-egress requirement, high-volume S3/DynamoDB |

```hcl
# VPC-attached Lambda
resource "aws_lambda_function" "vpc_function" {
  function_name = var.function_name
  role          = aws_iam_role.lambda_exec.arn
  # ... package config ...

  vpc_config {
    subnet_ids         = var.private_subnet_ids   # Private subnets with NAT GW or VPC endpoints
    security_group_ids = [aws_security_group.lambda.id]
    ipv6_allowed_for_dual_stack = var.enable_ipv6  # v6.x feature
  }

  # VPC ENI deletion takes up to 45 minutes — set explicit timeout
  timeouts {
    delete = "60m"
  }
}

# Lambda security group — default-deny with explicit egress only
resource "aws_security_group" "lambda" {
  name        = "${var.function_name}-sg-${var.environment}"
  description = "Lambda function security group — egress only to required resources"
  vpc_id      = var.vpc_id

  # No ingress rules — Lambda is invoked via IAM, not network
  egress {
    description     = "HTTPS to AWS services"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    cidr_blocks     = []
    prefix_list_ids = [data.aws_ec2_managed_prefix_list.s3.id]  # VPC endpoint prefix list
  }

  tags = {
    Name = "${var.function_name}-sg"
  }
}

# Required IAM for VPC ENI management
resource "aws_iam_role_policy_attachment" "vpc_access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
```

- **Agent**: "Ask user: Does this function access RDS, ElastiCache, or other VPC-private resources? Is cold start latency critical? Is there a compliance requirement for no-internet-egress?"
- **Source**: [VPC Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function#vpc_config-configuration-block)

---

#### Decision: Function URL vs. API Gateway vs. No HTTP Endpoint

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **`aws_lambda_function_url`** | Simplicity, no extra cost, streaming, low latency | No WAF, no throttling, no usage plans, no request validation | Internal tools, webhooks, simple APIs, response streaming |
| **API Gateway v2 (HTTP API)** | Cost (~3.5x cheaper than REST), JWT auth, CORS | No WAF, no caching, no request validation | Mobile/web backends, simple CRUD APIs |
| **API Gateway v1 (REST API)** | WAF, caching, usage plans, request validation, VPC link | Cost, complexity | Public APIs needing WAF/caching, enterprise, compliance |

```hcl
# Option: Function URL (simplest, streaming-capable)
resource "aws_lambda_function_url" "main" {
  function_name      = aws_lambda_function.main.function_name
  authorization_type = "AWS_IAM"  # NONE = public — require explicit decision

  cors {
    allow_credentials = true
    allow_origins     = var.allowed_origins
    allow_methods     = ["GET", "POST"]
    allow_headers     = ["content-type", "authorization"]
    max_age           = 86400
  }
}

# For public function URLs: require explicit variable override
variable "function_url_auth_type" {
  type        = string
  description = "Function URL authorization type. Use AWS_IAM unless explicitly making the endpoint public."
  default     = "AWS_IAM"

  validation {
    condition     = contains(["AWS_IAM", "NONE"], var.function_url_auth_type)
    error_message = "function_url_auth_type must be AWS_IAM or NONE. Document the business reason for NONE."
  }
}
```

- **Agent**: "Ask user: Does this endpoint need WAF protection? Rate limiting/usage plans? Is response streaming required? What is the authentication mechanism?"
- **Source**: [aws_lambda_function_url](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function_url)

---

#### Decision: SnapStart vs. Provisioned Concurrency vs. Neither

| Option | Optimizes | Sacrifices | Cold Start Reduction | Best When |
|--------|-----------|------------|---------------------|----------|
| **Neither** | Cost, simplicity | First-request latency | 0% | Async/batch workloads, latency-insensitive |
| **SnapStart** | Cold start for Java functions, no hourly cost | Java only, `publish = true` required, memory snapshot | Up to 90% | Java 21 latency-sensitive APIs, no extra cost after publishing |
| **Provisioned Concurrency** | Guaranteed warm instances, all runtimes | Hourly cost even when idle | 100% | Critical low-latency paths, all runtimes, predictable traffic patterns |

```hcl
# SnapStart — Java only (no cost beyond published version storage)
resource "aws_lambda_function" "java_snapstart" {
  function_name = var.function_name
  runtime       = "java21"
  publish       = true  # Required for SnapStart

  snap_start {
    apply_on = "PublishedVersions"
  }
}

# Provisioned Concurrency — all runtimes, scheduled scaling
resource "aws_appautoscaling_target" "lambda" {
  max_capacity       = var.max_provisioned_concurrency
  min_capacity       = var.min_provisioned_concurrency
  resource_id        = "function:${aws_lambda_function.main.function_name}:${aws_lambda_alias.live.name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"
}

resource "aws_appautoscaling_policy" "lambda_scheduled" {
  name               = "${var.function_name}-provisioned-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.lambda.resource_id
  scalable_dimension = aws_appautoscaling_target.lambda.scalable_dimension
  service_namespace  = aws_appautoscaling_target.lambda.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 0.7  # Scale when 70% of provisioned concurrency utilized
    predefined_metric_specification {
      predefined_metric_type = "LambdaProvisionedConcurrencyUtilization"
    }
  }
}
```

- **Agent**: "Ask user: What runtime? Is cold start measured in SLA? Is traffic predictable or spiky?"
- **Source**: [SnapStart](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function#snap_start-configuration-block) | [aws_lambda_provisioned_concurrency_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_provisioned_concurrency_config)

---

#### Decision: Event Source Mapping (SQS/DynamoDB/Kinesis) vs. Lambda Permission (Push-based)

| Pattern | Trigger Model | Lambda Manages Polling | Best For |
|---------|-------------|----------------------|----------|
| **`aws_lambda_event_source_mapping`** | Pull (Lambda polls) | Yes | SQS, DynamoDB Streams, Kinesis, MSK, MQ |
| **`aws_lambda_permission`** | Push (source invokes) | No | API Gateway, SNS, S3, EventBridge, CloudWatch |

```hcl
# Pull model: SQS → Lambda via event source mapping
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn = aws_sqs_queue.input.arn
  function_name    = aws_lambda_alias.live.arn  # Point to alias, not $LATEST

  batch_size                         = 10
  maximum_batching_window_in_seconds = 5  # Reduce API calls, increase throughput

  # Filter events before invoking function — reduces cost
  filter_criteria {
    filter {
      pattern = jsonencode({
        body = { event_type = ["ORDER_PLACED"] }
      })
    }
  }

  # Concurrency limit — prevent Lambda from overwhelming downstream
  scaling_config {
    maximum_concurrency = 50
  }

  # Partial batch failure reporting — re-enqueue only failed messages
  function_response_types = ["ReportBatchItemFailures"]

  tags = {
    Name = "${var.function_name}-sqs-mapping"
  }
}

# Grant Lambda role SQS receive permission
data "aws_iam_policy_document" "sqs_receive" {
  statement {
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
    ]
    resources = [aws_sqs_queue.input.arn]
  }
}
```

- **Agent**: "Ask user: Is the event source a queue/stream (pull) or a push-based service? Does the function need partial batch failure reporting?"
- **Source**: [aws_lambda_event_source_mapping](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_event_source_mapping)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Hardcoded Credentials in Provider or Environment Variables

```hcl
# DON'T
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"        # Hardcoded — CRITICAL
  secret_key = "wJalrXUtnFEMI/K7MDENG/..."  # Hardcoded — CRITICAL
}

resource "aws_lambda_function" "bad" {
  environment {
    variables = {
      DB_PASSWORD = "supersecret123"          # Secret in plaintext — CRITICAL
      API_KEY     = "sk-proj-abc123..."       # API key in state file — CRITICAL
    }
  }
}
```

**Why**: Hardcoded credentials are committed to version control history permanently, appear in `terraform.tfstate` in plaintext, and are logged in CI/CD output. Lambda environment variables encrypted by the default AWS key are still visible to anyone with Lambda `GetFunction` access.

```hcl
# DO — Use IAM roles for credentials, Secrets Manager for secrets
provider "aws" {
  region = var.aws_region
  # Credentials from environment: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
  # Or from EC2/ECS/Lambda instance profile automatically
}

resource "aws_lambda_function" "good" {
  environment {
    variables = {
      DB_SECRET_ARN = aws_secretsmanager_secret.db.arn  # ARN only, not value
      CONFIG_KEY    = var.config_key                    # Non-sensitive config
    }
  }
  # Function code retrieves the secret value at runtime via SDK
  kms_key_arn = aws_kms_key.lambda.arn  # Encrypt env vars with CMK
}
```

- **Impact**: state corruption | security breach | credential compromise
- **Severity**: CRITICAL
- **Source**: [AWS Security Best Practices](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)

---

#### Anti-Pattern: Wildcard IAM Permissions on Execution Role

```hcl
# DON'T
resource "aws_iam_role_policy" "bad" {
  role = aws_iam_role.lambda_exec.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"           # Full account access — CRITICAL
      Resource = "*"
    }]
  })
}
```

**Why**: A compromised Lambda function with `Action = "*"` gives an attacker full control of the AWS account. Lambda functions are internet-accessible (via invocation) and run untrusted input — their IAM scope is a critical blast-radius boundary.

```hcl
# DO — Scope to exactly the resources and actions this function needs
data "aws_iam_policy_document" "function_specific" {
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"]
    resources = [aws_dynamodb_table.orders.arn]
  }

  statement {
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      aws_secretsmanager_secret.db_password.arn,
    ]
    condition {
      test     = "StringEquals"
      variable = "secretsmanager:ResourceTag/Environment"
      values   = [var.environment]
    }
  }
}
```

- **Impact**: Full AWS account compromise via function event injection
- **Severity**: CRITICAL
- **Source**: [Lambda IAM Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)

---

#### Anti-Pattern: Missing `source_arn` on `aws_lambda_permission`

```hcl
# DON'T — Any SNS topic in any account can invoke this function
resource "aws_lambda_permission" "bad" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "sns.amazonaws.com"
  # No source_arn — confused-deputy vulnerability
}
```

**Why**: Without `source_arn`, any SNS topic, EventBridge rule, or S3 bucket that the attacker can create in any AWS account can invoke your function using their legitimately held `sns.amazonaws.com` principal. This is the Lambda confused-deputy attack.

```hcl
# DO — Always restrict to specific source ARN
resource "aws_lambda_permission" "good" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.events.arn          # Specific topic
  source_account = data.aws_caller_identity.current.account_id  # Your account only
}
```

- **Impact**: Unauthorized function invocation from external AWS accounts
- **Severity**: HIGH
- **Source**: [Confused Deputy Prevention](https://docs.aws.amazon.com/lambda/latest/dg/access-control-resource-based.html)

---

#### Anti-Pattern: Public Function URL Without Authentication

```hcl
# DON'T — Publicly invocable function URL
resource "aws_lambda_function_url" "bad" {
  function_name      = aws_lambda_function.main.function_name
  authorization_type = "NONE"  # Public — no authentication required
  # No WAF, no rate limiting, no auth
}
```

**Why**: `authorization_type = "NONE"` creates a publicly accessible HTTPS endpoint. Without authentication, rate limiting, or WAF, any actor on the internet can invoke your function — enabling data exfiltration, resource exhaustion, and cost attacks.

```hcl
# DO — Use AWS_IAM auth; if public is required, add WAF via CloudFront
resource "aws_lambda_function_url" "good" {
  function_name      = aws_lambda_function.main.function_name
  authorization_type = "AWS_IAM"
}

# If truly public: require WAF via CloudFront + explicit override
variable "make_function_url_public" {
  type        = bool
  description = "Set true only with documented business justification and WAF deployed in front"
  default     = false
}
```

- **Impact**: Unauthorized invocation, cost explosion, data exfiltration
- **Severity**: CRITICAL
- **Source**: [Lambda Function URLs](https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html#urls-auth)

---

#### Anti-Pattern: Using `$LATEST` in Event Source Mappings and Permissions

```hcl
# DON'T — $LATEST is mutable; new code deploys without traffic control
resource "aws_lambda_event_source_mapping" "bad" {
  event_source_arn = aws_sqs_queue.input.arn
  function_name    = aws_lambda_function.main.arn  # Points to $LATEST
}
```

**Why**: `$LATEST` always points to the most recently uploaded code. A broken deployment immediately affects all event processing. Using an alias (e.g., `live`) allows you to control the version receiving traffic independently of code updates.

```hcl
# DO — Point to alias, not $LATEST
resource "aws_lambda_event_source_mapping" "good" {
  event_source_arn = aws_sqs_queue.input.arn
  function_name    = aws_lambda_alias.live.arn  # Stable alias
}
```

- **Impact**: Uncontrolled production deployments, no canary support, no rollback point
- **Severity**: HIGH
- **Source**: [Lambda Aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuration-aliases.html)

---

#### Anti-Pattern: Lambda Function Without Timeout

```hcl
# DON'T — Default 3-second timeout will silently fail long operations
resource "aws_lambda_function" "bad" {
  function_name = var.function_name
  # No timeout set — defaults to 3 seconds
}
```

**Why**: Lambda default timeout is 3 seconds. A function processing SQS messages or making database calls without an explicit timeout will silently time out, causing the event to be re-queued and retried, potentially creating SQS poison pill loops that exhaust the function's concurrency and consume the entire account's reserved concurrency.

```hcl
# DO — Set explicit timeout with validation
resource "aws_lambda_function" "good" {
  function_name = var.function_name
  timeout       = var.timeout  # Validated: 1-900 seconds
}

# Monitor for timeout breaches
resource "aws_cloudwatch_metric_alarm" "timeout" {
  alarm_name          = "${var.function_name}-timeout"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
    Resource     = "${aws_lambda_function.main.function_name}:live"
  }
}
```

- **Impact**: Silent failures, SQS poison pill loops, concurrency exhaustion
- **Severity**: HIGH
- **Source**: [Lambda Timeout](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout-stateful.html)

---

#### Anti-Pattern: No Reserved Concurrency on Account-Critical Functions

```hcl
# DON'T — A noisy neighbor function can exhaust all account concurrency
resource "aws_lambda_function" "critical" {
  function_name = "payment-processor"
  # No reserved_concurrent_executions — shares pool with all other functions
}
```

**Why**: AWS accounts have a default concurrency limit of 1,000. A burst of traffic to any function can consume all available concurrency, causing throttling on payment processors, auth services, and other critical paths.

```hcl
# DO — Reserve concurrency for critical functions; throttle non-critical
resource "aws_lambda_function" "critical" {
  function_name                  = "payment-processor"
  reserved_concurrent_executions = 200  # Guaranteed capacity
}

resource "aws_lambda_function" "batch_job" {
  function_name                  = "report-generator"
  reserved_concurrent_executions = 10  # Throttle non-critical to protect critical functions
}
```

- **Impact**: Cascading failures when non-critical functions exhaust concurrency
- **Severity**: HIGH
- **Source**: [Lambda Concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html)

---

#### Anti-Pattern: Deprecated Runtimes in Production

```hcl
# DON'T — Deprecated runtimes receive no security patches
resource "aws_lambda_function" "bad" {
  runtime = "nodejs16.x"   # EOL
  runtime = "python3.8"    # EOL
  runtime = "java11"       # Approaching EOL
}
```

**Why**: AWS stops applying security patches to deprecated runtimes. Known CVEs in the runtime environment are unmitigated. Many compliance frameworks (SOC 2, PCI-DSS) require supported runtime versions.

```hcl
# DO — Use current supported runtimes; validate in variable
resource "aws_lambda_function" "good" {
  runtime = "python3.12"   # Supported and maintained (as of 2026)
  # Or: nodejs24.x, java21, dotnet8, provided.al2023
}
```

- **Impact**: Unpatched security vulnerabilities in runtime environment
- **Severity**: HIGH
- **Source**: [Lambda Runtime Support Policy](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html#runtime-support-policy)

---

## State Management Deep Dive

### Local Development State
```hcl
# Use only for solo development / learning
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
  # No backend block = local state
}
```
- **Risk**: No locking, no sharing, single point of failure, state in repo = credentials exposure
- **When**: Solo development only; never commit `terraform.tfstate`

### Production Remote State (S3 + DynamoDB)

```hcl
# Bootstrap: create state infrastructure first (run once with local state, then migrate)
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  point_in_time_recovery { enabled = true }

  tags = {
    Name      = "terraform-locks"
    ManagedBy = "terraform"
  }
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.org_name}-terraform-state-${data.aws_caller_identity.current.account_id}"

  lifecycle {
    prevent_destroy = true  # Never accidentally delete state bucket
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.state.arn
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

# Backend config (in main terraform block)
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state-123456789012"
    key            = "prod/lambda/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/mrk-..."
    dynamodb_table = "terraform-locks"
  }
}
```

### State File Sensitivity in Lambda Context
Lambda state files contain:
- Function ARNs (attackers can craft permission bypass requests)
- IAM role ARNs (lateral movement targets)
- KMS key ARNs (encryption key references)
- Environment variable keys (not values if using Secrets Manager correctly)

```hcl
# Mark sensitive outputs — masked in plan/apply output, stored in state
output "execution_role_arn" {
  value       = aws_iam_role.lambda_exec.arn
  description = "Execution role ARN — restrict state file access"
  sensitive   = false  # ARNs are not sensitive but state file access must be restricted
}
```

---

## Module Architecture

### Standard Lambda Module Structure
```
modules/lambda/
├── main.tf          # aws_lambda_function, aws_lambda_alias, log group
├── variables.tf     # All inputs with validation
├── outputs.tf       # ARNs, invoke ARNs, role ARN, log group name
├── iam.tf           # Execution role, trust policy, baseline policies
├── permissions.tf   # aws_lambda_permission resources (optional, per trigger type)
├── versions.tf      # terraform{} block with required_providers
└── README.md        # Usage, inputs, outputs, examples
```

### Module Definition Example
```hcl
# modules/lambda/variables.tf
variable "function_name" {
  type        = string
  description = "Lambda function name"
  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]{1,64}$", var.function_name))
    error_message = "function_name: 1-64 chars, alphanumeric/hyphens/underscores."
  }
}

variable "runtime" {
  type    = string
  default = "python3.12"
  validation {
    condition     = contains(["nodejs22.x","nodejs24.x","python3.12","python3.13","java21","dotnet8","provided.al2023"], var.runtime)
    error_message = "Must be a supported, non-deprecated Lambda runtime."
  }
}

variable "trigger_type" {
  type        = string
  description = "Trigger source type for automatic permission wiring"
  default     = "none"
  validation {
    condition     = contains(["none", "api_gateway", "eventbridge", "sns", "s3", "sqs", "alb"], var.trigger_type)
    error_message = "trigger_type must be one of: none, api_gateway, eventbridge, sns, s3, sqs, alb."
  }
}

# modules/lambda/outputs.tf
output "function_arn"    { value = aws_lambda_function.this.arn }
output "function_name"   { value = aws_lambda_function.this.function_name }
output "invoke_arn"      { value = aws_lambda_function.this.invoke_arn }
output "alias_arn"       { value = aws_lambda_alias.live.arn }
output "role_arn"        { value = aws_iam_role.exec.arn }
output "log_group_name"  { value = aws_cloudwatch_log_group.this.name }

# root/main.tf — Calling the module
module "api_handler" {
  source = "./modules/lambda"

  function_name   = "api-order-handler"
  runtime         = "python3.12"
  handler         = "handler.main"
  package_path    = "${path.module}/.build/api_handler.zip"
  memory_size     = 512
  timeout         = 30
  environment     = var.environment
  kms_key_arn     = module.kms.lambda_key_arn
  trigger_type    = "api_gateway"
  trigger_arn     = module.api_gateway.execution_arn

  additional_policy_arns = [
    module.dynamodb.read_write_policy_arn,
    module.secrets.read_policy_arn,
  ]

  tags = var.common_tags
}
```

---

## Integration Patterns

### Integration: Terraform ↔ VPC

```hcl
# VPC data source — reference existing VPC managed by separate stack
data "aws_vpc" "main" {
  tags = { Name = "${var.environment}-main-vpc" }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
  tags = { Tier = "private" }
}

resource "aws_lambda_function" "vpc_attached" {
  function_name = var.function_name
  role          = aws_iam_role.lambda_exec.arn
  # ... package config ...

  vpc_config {
    subnet_ids         = data.aws_subnets.private.ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  timeouts {
    create = "10m"
    update = "10m"
    delete = "60m"  # ENI cleanup can take 45 minutes
  }
}

resource "aws_iam_role_policy_attachment" "vpc_access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
```

- **Issues**: ENI deletion takes up to 45 minutes; NAT Gateway required for internet access; IP exhaustion in large deployments; Lambda requires at least one private subnet per AZ used
- **Source**: [Lambda VPC Configuration](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html)

---

### Integration: Terraform ↔ IAM

```hcl
# Pattern: Fine-grained permissions via data source composition
data "aws_iam_policy_document" "function_policy" {
  # DynamoDB access — table-scoped
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query", "dynamodb:UpdateItem"]
    resources = [var.dynamodb_table_arn, "${var.dynamodb_table_arn}/index/*"]
  }

  # Secrets Manager — specific secret only
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.db_secret_arn]
  }

  # X-Ray — required if tracing_config.mode = "Active"
  statement {
    effect    = "Allow"
    actions   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords", "xray:GetSamplingRules", "xray:GetSamplingTargets"]
    resources = ["*"]  # X-Ray does not support resource-level permissions
  }

  # KMS decrypt — for env var decryption
  statement {
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [var.kms_key_arn]
  }
}

resource "aws_iam_role_policy" "function" {
  name   = "function-policy"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.function_policy.json
}
```

- **Versions**:

| Resource | Min Provider | Max Provider |
|----------|-------------|-------------|
| `aws_iam_role` | 3.0 | ~> 6.0 |
| `aws_iam_policy_document` | 3.0 | ~> 6.0 |
| `aws_iam_role_policy_attachment` | 3.0 | ~> 6.0 |

- **Issues**: X-Ray requires `*` resource; KMS grants are not cleaned up if role is deleted before function; `depends_on` required when role is created in same apply as function
- **Source**: [Lambda Execution Role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)

---

### Integration: Terraform ↔ CloudWatch

```hcl
# Pre-create log group (mandatory pattern — see Always Do above)
resource "aws_cloudwatch_log_group" "function" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 14
  kms_key_id        = var.kms_key_arn
}

# Metric alarms for Lambda operational health
resource "aws_cloudwatch_metric_alarm" "errors" {
  alarm_name          = "${var.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.alert_sns_arn]

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
    Resource     = "${aws_lambda_function.main.function_name}:live"
  }
}

resource "aws_cloudwatch_metric_alarm" "throttles" {
  alarm_name          = "${var.function_name}-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_actions       = [var.alert_sns_arn]

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "concurrent_executions" {
  alarm_name          = "${var.function_name}-concurrency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ConcurrentExecutions"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Maximum"
  threshold           = floor(var.reserved_concurrent_executions * 0.8)
  alarm_actions       = [var.alert_sns_arn]

  dimensions = {
    FunctionName = aws_lambda_function.main.function_name
  }
}

# CloudWatch Insights query for error analysis
resource "aws_cloudwatch_query_definition" "errors" {
  name = "${var.function_name}/errors"

  log_group_names = [aws_cloudwatch_log_group.function.name]

  query_string = <<-QUERY
    fields @timestamp, @message, @requestId, level, errorType, errorMessage
    | filter level = "ERROR" or ispresent(errorType)
    | sort @timestamp desc
    | limit 50
  QUERY
}
```

- **Source**: [Lambda Metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics.html) | [aws_cloudwatch_metric_alarm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm)

---

### Integration: Terraform ↔ API Gateway

```hcl
# API Gateway V2 (HTTP API) → Lambda integration
resource "aws_apigatewayv2_integration" "lambda" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_alias.live.invoke_arn  # Always use alias
  payload_format_version = "2.0"
}

resource "aws_lambda_permission" "api_gateway_v2" {
  statement_id  = "AllowAPIGatewayV2Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  qualifier     = aws_lambda_alias.live.name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# API Gateway V1 (REST API) → Lambda for streaming responses
resource "aws_api_gateway_integration" "lambda_stream" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.main.id
  http_method             = "POST"
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  # Use response_streaming_invoke_arn for streaming (v6.x attribute)
  uri                     = aws_lambda_function.main.response_streaming_invoke_arn
}
```

- **Issues**: Lambda integration type must be `AWS_PROXY` for Lambda proxy integration; `integration_uri` must use `invoke_arn`, not `arn`; qualifying to alias requires `qualifier` on `aws_lambda_permission`
- **Source**: [aws_apigatewayv2_integration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_integration)

---

### Integration: Terraform ↔ SQS

```hcl
# SQS Queue → Lambda via event source mapping
resource "aws_sqs_queue" "input" {
  name                      = "${var.function_name}-input-${var.environment}"
  visibility_timeout_seconds = var.timeout * 6  # Must be >= 6x Lambda timeout
  message_retention_seconds = 86400             # 1 day
  kms_master_key_id         = var.kms_key_id

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn                   = aws_sqs_queue.input.arn
  function_name                      = aws_lambda_alias.live.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  function_response_types            = ["ReportBatchItemFailures"]

  scaling_config {
    maximum_concurrency = min(var.reserved_concurrent_executions, 1000)
  }
}

data "aws_iam_policy_document" "sqs_consume" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"]
    resources = [aws_sqs_queue.input.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [var.kms_key_arn]
  }
}
```

- **Issues**: `visibility_timeout_seconds` MUST be at least 6x the Lambda function timeout; FIFO queues are not supported with event source mapping; `ReportBatchItemFailures` requires function to return specific JSON structure
- **Source**: [Lambda with SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)

---

### Integration: Terraform ↔ SNS

```hcl
resource "aws_sns_topic_subscription" "lambda" {
  topic_arn = aws_sns_topic.events.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_alias.live.arn  # Subscribe to alias
}

resource "aws_lambda_permission" "sns" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  qualifier     = aws_lambda_alias.live.name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.events.arn
}
```

- **Issues**: SNS→Lambda is async (fire-and-forget); use `aws_lambda_function_event_invoke_config` with DLQ for failure handling; Lambda cannot throttle SNS messages — size the function concurrency accordingly
- **Source**: [Lambda with SNS](https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html)

---

### Integration: Terraform ↔ Secrets Manager

```hcl
# Reference secret ARN in environment — never the value
resource "aws_lambda_function" "main" {
  environment {
    variables = {
      DB_SECRET_ARN = aws_secretsmanager_secret.db.arn  # ARN reference only
    }
  }
}

# Grant function permission to read the specific secret
data "aws_iam_policy_document" "secrets" {
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.db.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [aws_secretsmanager_secret.db.kms_key_id != null ? aws_kms_key.secrets.arn : "*"]
  }
}

# Lambda Powertools or SDK pattern in function code (Python example):
# import boto3, os
# client = boto3.client('secretsmanager')
# secret = client.get_secret_value(SecretId=os.environ['DB_SECRET_ARN'])
```

- **Issues**: Cache secret values in function scope (not global) for short TTL; Lambda Extensions can cache secrets at the execution environment level; rotation-enabled secrets require eventual-consistency handling
- **Source**: [Secrets Manager Integration](https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html)

---

### Integration: Terraform ↔ ECR (Container Image Functions)

```hcl
resource "aws_ecr_repository" "function" {
  name                 = var.function_name
  image_tag_mutability = "IMMUTABLE"  # Prevent tag overwrite = reproducible deploys

  image_scanning_configuration {
    scan_on_push = true  # Vulnerability scan on every push
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }
}

resource "aws_ecr_lifecycle_policy" "function" {
  repository = aws_ecr_repository.function.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# Lambda: pull from ECR
resource "aws_lambda_function" "container" {
  function_name = var.function_name
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.function.repository_url}:${var.image_tag}"
  architectures = ["arm64"]
}

# Grant Lambda access to pull from ECR
data "aws_iam_policy_document" "ecr_pull" {
  statement {
    effect  = "Allow"
    actions = ["ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "ecr:BatchCheckLayerAvailability"]
    resources = [aws_ecr_repository.function.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]  # ECR auth token is account-wide
  }
}
```

- **Issues**: Image URI changes trigger function update on next `terraform apply`; use `ignore_changes = [image_uri]` only if CI/CD owns the image tag; Lambda pulls images from ECR at cold start — large images increase cold start time
- **Source**: [Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)

---

## Executable Verification

```bash
# Initialize with provider upgrade
terraform init -upgrade
# Expected: "Terraform initialized in an empty directory" or "Reinitialized"
# Provider hashicorp/aws ~> 6.0 installed

# Format validation
terraform fmt -recursive -check=true
# Expected: exit code 0, no output (or lists files that need formatting)

# Syntax validation
terraform validate
# Expected: "Success! The configuration is valid."

# Security scanning
tfsec . --format sarif --minimum-severity HIGH
# Expected: No HIGH or CRITICAL findings for Lambda configuration

# Policy-as-code check
checkov -d . --framework terraform --quiet --check CKV_AWS_50,CKV_AWS_116,CKV_AWS_117,CKV_AWS_272
# CKV_AWS_50: X-Ray tracing enabled
# CKV_AWS_116: DLQ configured
# CKV_AWS_117: Lambda inside VPC (if required)
# CKV_AWS_272: Code signing config

# Plan with lock
terraform plan -out=tfplan -lock=true
terraform show tfplan
# Expected: Clean plan showing Lambda resources; review any replacements carefully

# Apply with plan
terraform apply tfplan
# Expected: All resources created/updated as planned

# Verify state
terraform state list
# Expected: aws_lambda_function.main, aws_lambda_alias.live,
#           aws_cloudwatch_log_group.function, aws_iam_role.lambda_exec, etc.

terraform output invoke_arn
# Expected: arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/...

# Test invocation (requires AWS CLI)
aws lambda invoke \
  --function-name "$(terraform output -raw function_name)" \
  --payload '{"test":true}' \
  --cli-binary-format raw-in-base64-out \
  response.json
# Expected: StatusCode: 200

# Destroy with safety plan
terraform plan -destroy -out=destroy.tfplan
terraform apply destroy.tfplan
# Review before applying — Lambda deletions are immediate and irreversible
```

---

## Secrets & Sensitive Data Management

```
Secret Type: Database credentials
Storage: AWS Secrets Manager
Retrieval: ARN reference in environment variable, SDK retrieval at runtime
Code:
```

```hcl
# Store secret ARN reference in Lambda env — never the value
resource "aws_lambda_function" "main" {
  environment {
    variables = {
      DB_SECRET_ARN = aws_secretsmanager_secret.database.arn
    }
  }
  kms_key_arn = aws_kms_key.lambda_env.arn  # Encrypt env vars with CMK
}

# Function code (Python) — retrieve at cold start, cache for TTL
# import boto3, json, os
# _secret_cache = {}
# def get_secret():
#     if 'db' not in _secret_cache:
#         client = boto3.client('secretsmanager')
#         _secret_cache['db'] = json.loads(
#             client.get_secret_value(SecretId=os.environ['DB_SECRET_ARN'])['SecretString']
#         )
#     return _secret_cache['db']
```

```
Secret Type: API keys, tokens
Storage: Parameter Store (SecureString) for low-volume; Secrets Manager for rotation
Retrieval: ARN/path in env var, SDK retrieval at runtime
```

```hcl
resource "aws_ssm_parameter" "api_key" {
  name   = "/${var.environment}/${var.function_name}/api-key"
  type   = "SecureString"
  value  = var.api_key  # Provided via .tfvars (gitignored) or CI/CD secret
  key_id = aws_kms_key.ssm.arn
}

resource "aws_lambda_function" "main" {
  environment {
    variables = {
      API_KEY_PARAM = aws_ssm_parameter.api_key.name
    }
  }
}

# Never version .tfvars containing secrets
# .gitignore
# *.tfvars
# !example.tfvars
```

- **Source**: [Secrets Manager Lambda Integration](https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html) | [Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)

---

## Testing & Validation Frameworks

```
Framework: terraform validate + fmt
Purpose: Syntax and structural correctness before any AWS API calls
```
```bash
terraform fmt -recursive && terraform validate
# Expected: "Success! The configuration is valid."
# Guarantee: Zero AWS API calls, fast, can run in pre-commit hook
```

```
Framework: tfsec (v1.28+)
Purpose: Security policy scanning — identifies misconfigured Lambda resources
```
```bash
tfsec . --minimum-severity MEDIUM --include-passed
# Key Lambda checks:
# AVD-AWS-0066: tracing not enabled
# AVD-AWS-0067: DLQ not configured
# AVD-AWS-0078: function not inside VPC (if required)
```

```
Framework: checkov (v3.x)
Purpose: CIS/AWS best practice compliance scanning
```
```bash
checkov -d . --framework terraform --check \
  CKV_AWS_50,CKV_AWS_116,CKV_AWS_117,CKV_AWS_120,CKV_AWS_272 \
  --output cli
# CKV_AWS_50:  X-Ray tracing active
# CKV_AWS_116: Dead letter queue configured
# CKV_AWS_117: Lambda in VPC
# CKV_AWS_120: Lambda function not using $LATEST
# CKV_AWS_272: Code signing config
```

```
Framework: Terratest (Go)
Purpose: Integration testing with real AWS infrastructure
```
```go
package test

import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/gruntwork-io/terratest/modules/aws"
  "github.com/stretchr/testify/assert"
)

func TestLambdaModule(t *testing.T) {
  t.Parallel()

  opts := &terraform.Options{
    TerraformDir: "../examples/lambda",
    Vars: map[string]interface{}{
      "environment":   "test",
      "function_name": "test-lambda",
      "runtime":       "python3.12",
      "memory_size":   128,
      "timeout":       10,
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  functionName := terraform.Output(t, opts, "function_name")
  region := "us-east-1"

  // Verify function exists and is active
  functionConfig := aws.GetLambdaFunction(t, functionName, region)
  assert.Equal(t, "Active", *functionConfig.Configuration.State)

  // Verify tracing is enabled
  assert.Equal(t, "Active", *functionConfig.Configuration.TracingConfig.Mode)

  // Invoke the function
  response := aws.InvokeFunction(t, region, functionName, []byte(`{"test": true}`))
  assert.Equal(t, int64(200), *response.StatusCode)
}
```

- **Source**: [Terratest](https://terratest.gruntwork.io/) | [terraform test](https://developer.hashicorp.com/terraform/language/tests)

---

## Production Considerations

```
Scenario: Production scale — high-throughput event processing
Challenge: Concurrency exhaustion from burst traffic; SQS poison pills; cold start spikes
Solution:
```
```hcl
# Reserved concurrency protects critical functions
resource "aws_lambda_function" "payment" {
  reserved_concurrent_executions = 500  # Guaranteed minimum
}

# Throttle batch jobs to protect critical functions
resource "aws_lambda_function" "batch_report" {
  reserved_concurrent_executions = 20
}

# Provisioned concurrency for latency-critical paths
resource "aws_lambda_provisioned_concurrency_config" "payment" {
  function_name                      = aws_lambda_function.payment.function_name
  qualifier                          = aws_lambda_alias.live.name
  provisioned_concurrent_executions  = 50
}
```
- **Metrics**: `ConcurrentExecutions`, `Throttles`, `Duration` P99, `InitDuration` (cold starts), `Errors`
- **Runbook**: If Throttles alarm fires → check `reserved_concurrent_executions` vs. account limit; request limit increase via Service Quotas

---

```
Scenario: Multi-region disaster recovery
Challenge: Lambda functions and layers must exist in every target region; state files per region
Solution:
```
```hcl
# Use provider aliases for multi-region deployments
provider "aws" {
  alias  = "primary"
  region = "us-east-1"
}

provider "aws" {
  alias  = "dr"
  region = "us-west-2"
}

module "lambda_primary" {
  source    = "./modules/lambda"
  providers = { aws = aws.primary }
  # ...
}

module "lambda_dr" {
  source    = "./modules/lambda"
  providers = { aws = aws.dr }
  # ...
}
```
- **Metrics**: Cross-region latency, Route53 health check status, DLQ depth per region

---

```
Scenario: Cold start performance optimization
Challenge: Java/Python cold starts >1s impact SLA for latency-sensitive APIs
Solution: SnapStart (Java 21), Graviton (arm64, ~20% better price/perf), minimize package size
```
```hcl
resource "aws_lambda_function" "optimized" {
  architectures = ["arm64"]     # Graviton — better performance per cost
  memory_size   = 1024          # More memory = more CPU = faster cold start
  runtime       = "java21"      # SnapStart supported

  snap_start {
    apply_on = "PublishedVersions"
  }

  publish = true
}
```

---

### Security Checklist
- [ ] All secrets stored in Secrets Manager or Parameter Store — zero plaintext secrets in env vars
- [ ] Environment variables encrypted with customer-managed KMS key (`kms_key_arn`)
- [ ] IAM execution role scoped to specific resources and actions (no wildcards)
- [ ] `source_arn` on every `aws_lambda_permission` (confused-deputy prevention)
- [ ] CloudWatch log group pre-created with retention and KMS encryption
- [ ] X-Ray tracing enabled (`tracing_config.mode = "Active"`)
- [ ] DLQ configured for all async invocations
- [ ] Reserved concurrency set for critical functions
- [ ] Function URL auth type is `AWS_IAM` (or documented exception for public endpoints)
- [ ] Non-deprecated runtime (nodejs22+, python3.12+, java21, dotnet8)
- [ ] Event source mapping points to alias, not `$LATEST`
- [ ] VPC security group has no ingress rules (Lambda invoked via IAM, not network)
- [ ] State file encrypted (S3 + KMS), DynamoDB locking enabled
- [ ] `.tfvars` files with secrets added to `.gitignore`
- [ ] Code signing config enforced for production (prevent unauthorized code)

---

### Disaster Recovery Runbook

```bash
# 1. State corruption recovery
aws s3api list-object-versions \
  --bucket my-org-terraform-state \
  --prefix prod/lambda/terraform.tfstate \
  --query 'Versions[*].{VersionId:VersionId,LastModified:LastModified}' \
  --output table

# Restore previous state version
aws s3api get-object \
  --bucket my-org-terraform-state \
  --key prod/lambda/terraform.tfstate \
  --version-id <previous-version-id> \
  terraform.tfstate.backup

terraform state push terraform.tfstate.backup

# 2. Import existing Lambda function (created outside Terraform)
import {
  to = aws_lambda_function.main
  id = "existing-function-name"
}

# CLI equivalent:
terraform import aws_lambda_function.main existing-function-name

# 3. Rollback Lambda function version via alias update
resource "aws_lambda_alias" "live" {
  function_version = "42"  # Roll back to known-good version
}
terraform apply -target=aws_lambda_alias.live

# 4. Detect drift from manual console changes
terraform plan
# Diff shows: ~ update in-place for env var changes, etc.

terraform refresh  # Sync state to current AWS reality (use with caution)

# 5. Force delete Lambda stuck in VPC ENI cleanup
# Wait 45 minutes, then:
terraform destroy -target=aws_lambda_function.main
# If still stuck: manually delete ENIs in AWS console for the Lambda security group
```

---

## Reference Implementations

- [Terraform AWS Lambda Function Registry](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)
- [Terraform AWS Lambda Permission Registry](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission)
- [Terraform AWS Lambda Event Source Mapping Registry](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_event_source_mapping)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [Lambda Permission Model](https://docs.aws.amazon.com/lambda/latest/dg/intro-permission-model.html)
- [Lambda Runtime Support Policy](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html#runtime-support-policy)
- [AWS Well-Architected Serverless Lens](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html)
- [Serverless Land Patterns](https://serverlessland.com/patterns)

---

## Source Bibliography

### Primary Sources
- [aws_lambda_function Registry Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) — 6.47.0, verified 2026-05-29
- [aws_lambda_permission Registry Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) — 6.47.0, verified 2026-05-29
- [aws_lambda_event_source_mapping Registry Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_event_source_mapping) — 6.47.0, verified 2026-05-29
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)

### Validation & Tools
- [tfsec GitHub](https://github.com/aquasecurity/tfsec) — Security scanner for Terraform
- [Checkov](https://www.checkov.io/) — Policy-as-code compliance scanner
- [Terratest](https://terratest.gruntwork.io/) — Go-based integration testing framework
- [hashicorp/terraform-provider-aws Issues](https://github.com/hashicorp/terraform-provider-aws/issues) — Lambda-specific issues

---

## Completion Checklist
- [x] All Terraform >= 1.7 and aws ~> 6.0 patterns validated against 6.47.0 registry docs
- [x] 3+ code examples for each mandatory pattern
- [x] State management strategy documented (local + S3/DynamoDB production)
- [x] Module architecture fully defined (structure + variable/output examples)
- [x] Every anti-pattern has tested alternative
- [x] All CLI commands validated with expected outputs
- [x] Integration examples for VPC, IAM, CloudWatch, API Gateway, SQS, SNS, Secrets Manager, ECR
- [x] Sources directly linked to registry documentation (verified 2026-05-29)
- [x] Security checklist complete
- [x] Disaster recovery procedures documented
- [x] v6.x-specific new resources/attributes documented (capacity_provider, logging_config, response_streaming_invoke_arn, durable_config, tenancy_config, ipv6_allowed_for_dual_stack)

---

## Research Gaps

```
Gap: aws_lambda_capacity_provider — Graviton warm pool configuration details
Impact: Cannot yet provide complete capacity planning guidance for managed instance pools
Workaround: Use provisioned_concurrency_config until capacity_provider is GA in all regions
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_capacity_provider

Gap: durable_config — limited region availability (only us-east-2 as of 2026-05-29)
Impact: Cannot recommend for multi-region deployments; feature still in preview
Workaround: Use Step Functions or DynamoDB-backed workflows for stateful long-running processes
Follow-up: https://builder.aws.com/build/capabilities (AWS Builder portal for preview access)

Gap: Lambda telemetry API (extensions) — no Terraform resource; must be configured in function code
Impact: Telemetry forwarding to custom observability tools requires code-level configuration
Workaround: Document Lambda Extension layer ARNs as outputs; configure via environment variables
Follow-up: https://docs.aws.amazon.com/lambda/latest/dg/telemetry-api.html
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- CloudWatch log group pre-creation with retention
- IAM execution role creation with `lambda.amazonaws.com` trust policy
- DLQ and `aws_lambda_function_event_invoke_config` for async functions
- `source_arn` enforcement on all `aws_lambda_permission` resources
- `code_sha256` / `source_code_hash` for change detection
- Alias creation (`live`) and event source mapping to alias ARN
- Structured logging config with JSON format (v6.x)
- X-Ray tracing mode = "Active"
- State backend with encryption and DynamoDB locking

### Medium Confidence (Validate with user)
- VPC attachment decision (latency trade-off vs. private resource access)
- Memory/timeout sizing (workload-dependent)
- Provisioned concurrency vs. SnapStart (cost vs. latency requirement)
- Reserved concurrency values (requires knowledge of total account limits)
- Module decomposition boundaries

### Low Confidence (Must ask user)
- Cold start SLA requirements (determines SnapStart/provisioned concurrency)
- Compliance requirements (SOC 2, PCI-DSS affect VPC, encryption, logging decisions)
- Multi-region DR strategy (which region is primary/secondary)
- Container image vs. zip decision (depends on dependency complexity and build pipeline ownership)
- `durable_config` usage (region availability limited as of 2026)

### Edge Cases (When to pause)
- Function stuck in VPC ENI deletion (wait 45 minutes, then manual ENI cleanup)
- KMS key policy change causing `KMSAccessDeniedException` on existing function
- IAM role recreated after function creation (Lambda loses KMS grant — recreate function)
- State lock not released after failed apply (check DynamoDB `terraform-locks` table)

### Emergency Stop
- Halt if `reserved_concurrent_executions = 0` set on production function (disables function)
- Halt if `authorization_type = "NONE"` on Function URL without documented justification
- Halt if `terraform destroy` targets production Lambda (invocations immediate — zero grace period)
- Halt if credentials detected in `environment.variables` block
- Halt if state file encryption disabled (`encrypt = false` in backend)
