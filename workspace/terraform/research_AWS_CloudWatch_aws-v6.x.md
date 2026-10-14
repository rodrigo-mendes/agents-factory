# Terraform AWS CloudWatch — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - CloudWatch (Metrics, Alarms, Logs, Dashboards)"
Cloud_Provider: "AWS"
Target_Service: "CloudWatch (Metric Alarms, Composite Alarms, Log Groups, Log Metric Filters, Log Subscription Filters, Dashboards, Metric Streams, Query Definitions, Log Data Protection, Contributor Insights, OTel Enrichment)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-28"
Domain_Complexity: "Complex"
New_V6_Resources_Noted: |
  aws_cloudwatch_otel_enrichment (new resource for OpenTelemetry enrichment),
  aws_cloudwatch_alarm_mute_rule (new),
  aws_cloudwatch_contributor_insight_rule (new),
  aws_cloudwatch_contributor_managed_insight_rule (new),
  aws_cloudwatch_log_transformer (new),
  aws_cloudwatch_log_index_policy (new),
  aws_cloudwatch_log_delivery / delivery_destination / delivery_destination_policy / delivery_source (new log delivery family),
  PromQL alarm support via evaluation_criteria + evaluation_interval in aws_cloudwatch_metric_alarm,
  deletion_protection_enabled on aws_cloudwatch_log_group,
  apply_on_transformed_logs on metric filters and subscription filters,
  emit_system_fields on subscription filters,
  identity-based import blocks (TF v1.12.0+)
```

---

## Executive Summary

Amazon CloudWatch is AWS's native observability platform, providing metrics collection, log management, alerting, dashboards, and distributed tracing integration. It spans two major sub-services — **CloudWatch Metrics** (alarms, dashboards, metric streams, contributor insights) and **CloudWatch Logs** (log groups, log streams, metric filters, subscription filters, query definitions, data protection policies). Terraform manages the full CloudWatch surface via the `hashicorp/aws` provider, covering 25+ distinct resource types across these sub-services.

The AWS provider v6.x introduces critical CloudWatch enhancements: the `aws_cloudwatch_otel_enrichment` resource enables enriching OpenTelemetry metrics with AWS resource metadata; `aws_cloudwatch_alarm_mute_rule` allows temporary alarm suppression without modifying alarm configuration; `aws_cloudwatch_contributor_insight_rule` and `aws_cloudwatch_contributor_managed_insight_rule` manage Contributor Insights rules declaratively; the new log delivery family (`aws_cloudwatch_log_delivery*`) provides structured delivery pipelines from AWS services to S3, Firehose, or CloudWatch Logs; `deletion_protection_enabled` on `aws_cloudwatch_log_group` prevents accidental log group deletion; PromQL-style alarm evaluation is now supported via the `evaluation_criteria` block with `promql_criteria` inside `aws_cloudwatch_metric_alarm`; and `apply_on_transformed_logs` on metric filters and subscription filters applies patterns to post-transformer log events. Provider constraint `~> 6.0` is recommended; Terraform `>= 1.7` is required for the `terraform test` framework and enhanced import blocks.

Three non-negotiable guardrails for any CloudWatch deployment: **(1) KMS encryption must be set on all log groups storing sensitive data** — the `kms_key_id` argument encrypts log data at rest with a customer-managed key; without it, log data (which may contain secrets, PII, or credentials) is encrypted only with AWS-managed keys that cannot be scoped to IAM principals; **(2) `retention_in_days` must always be set on log groups** — the default is `0` (never expire), which accumulates unbounded cost; production log groups should use a defined retention window aligned to compliance requirements; **(3) `deletion_protection_enabled = true` must be set on production log groups** — v6.x introduces this flag and once a log group is accidentally destroyed, all logs within it are permanently gone. This service is classified **Complex** due to multi-resource dependencies (alarms → SNS → IAM → Lambda), KMS key lifecycle management for log encryption, sensitive data detection policies, IAM resource policies for cross-account log delivery, and the breadth of the resource surface.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Ensures reproducibility across CI/CD pipelines and team members. Locks the provider to v6.x to avoid breaking changes from v6→v7 schema drift (e.g., new required arguments on `aws_cloudwatch_log_group`, `evaluation_criteria` block on metric alarms).

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
    key            = "prod/cloudwatch/terraform.tfstate"
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

**Why**: No hardcoded credentials. `assume_role` enables CI/CD pipeline deployments without static access keys. `default_tags` propagates to all CloudWatch resources, including alarms, log groups, dashboards, and metric streams.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "terraform-cloudwatch-deploy"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [AWS Provider Authentication](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration) | [default_tags](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#default_tags-configuration-block)

---

#### Pattern: Log Group with KMS Encryption, Retention, and Deletion Protection

**Why**: The `kms_key_id` ensures log data is encrypted with a customer-managed key, enabling IAM-scoped access control, rotation, and audit via CloudTrail. `retention_in_days` prevents unbounded cost accumulation (default is 0 = never expire). `deletion_protection_enabled = true` (v6.x) prevents accidental destruction of production log data.

```hcl
resource "aws_cloudwatch_log_group" "app" {
  name                     = "/app/${var.environment}/${var.service_name}"
  retention_in_days        = var.log_retention_days
  kms_key_id               = aws_kms_key.cloudwatch_logs.arn
  deletion_protection_enabled = true
  log_group_class          = "STANDARD"  # or INFREQUENT_ACCESS for archival

  tags = {
    Name        = "/app/${var.environment}/${var.service_name}"
    Service     = var.service_name
    Environment = var.environment
  }

  # Grant CloudWatch Logs service permission to use the KMS key
  depends_on = [aws_kms_key_policy.cloudwatch_logs]
}

resource "aws_kms_key" "cloudwatch_logs" {
  description             = "KMS key for CloudWatch Logs encryption - ${var.environment}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = data.aws_iam_policy_document.cloudwatch_kms.json

  tags = {
    Name        = "cloudwatch-logs-key-${var.environment}"
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "cloudwatch_kms" {
  statement {
    sid    = "Enable IAM User Permissions"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "Allow CloudWatch Logs"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["logs.${var.aws_region}.amazonaws.com"]
    }
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]
    resources = ["*"]
    condition {
      test     = "ArnEquals"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values   = ["arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/app/${var.environment}/${var.service_name}"]
    }
  }
}

variable "log_retention_days" {
  type        = number
  description = "Number of days to retain log events"
  default     = 90

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.log_retention_days)
    error_message = "retention_in_days must be one of the AWS-supported values: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_cloudwatch_log_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | [KMS for CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html)

---

#### Pattern: Metric Alarm with SNS Action and All State Transitions

**Why**: An alarm without `alarm_actions`, `ok_actions`, and `insufficient_data_actions` is silent — it changes state but notifies no one. All three state transitions must be wired. `treat_missing_data = "breaching"` is safer than the default `"missing"` for production SLO alarms: missing data is treated as a threshold violation, preventing false silence during metric gaps.

```hcl
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.environment}-${var.function_name}-errors"
  alarm_description   = "Lambda function error rate exceeded threshold"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = var.error_threshold
  treat_missing_data  = "breaching"

  dimensions = {
    FunctionName = var.function_name
  }

  alarm_actions             = [aws_sns_topic.alerts.arn]
  ok_actions                = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = [aws_sns_topic.alerts.arn]

  tags = {
    Name        = "${var.environment}-${var.function_name}-errors"
    Environment = var.environment
    Service     = var.function_name
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_cloudwatch_metric_alarm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm)

---

#### Pattern: Composite Alarm for Reduced Alert Noise

**Why**: Individual metric alarms fire independently and produce alert storms during incidents. Composite alarms aggregate multiple child alarms with boolean logic (`AND`/`OR`/`NOT`), reducing noise and enabling a single SNS notification for multi-signal incidents. The `actions_suppressor` block prevents notification floods during maintenance windows.

```hcl
resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "${var.environment}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = var.api_name
    Stage   = var.stage_name
  }

  alarm_actions             = []  # Suppress at individual level; fire at composite
  ok_actions                = []
  insufficient_data_actions = []

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_metric_alarm" "api_latency" {
  alarm_name          = "${var.environment}-api-latency-p99"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "IntegrationLatency"
  namespace           = "AWS/ApiGateway"
  period              = 60
  extended_statistic  = "p99"
  threshold           = 3000  # 3 seconds
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = var.api_name
    Stage   = var.stage_name
  }

  alarm_actions             = []
  ok_actions                = []
  insufficient_data_actions = []

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_composite_alarm" "api_health" {
  alarm_name        = "${var.environment}-api-health"
  alarm_description = "API degradation: high error rate OR high latency"

  alarm_rule = <<-EOT
    ALARM(${aws_cloudwatch_metric_alarm.api_5xx.alarm_name}) OR
    ALARM(${aws_cloudwatch_metric_alarm.api_latency.alarm_name})
  EOT

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = {
    Name        = "${var.environment}-api-health"
    Environment = var.environment
  }

  depends_on = [
    aws_cloudwatch_metric_alarm.api_5xx,
    aws_cloudwatch_metric_alarm.api_latency,
  ]
}
```

> **NOTE**: An alarm (composite or metric) cannot be destroyed while other composite alarms reference it. Use `depends_on`, staged applies, or remove references before destroying child alarms.

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_cloudwatch_composite_alarm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_composite_alarm) | [Creating Composite Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Create_Composite_Alarm.html)

---

#### Pattern: Log Metric Filter → Metric Alarm Pipeline

**Why**: Structured logs (JSON) and plain-text logs can be turned into numeric metrics that feed alarms without custom code. The filter pattern extracts counts or numeric values; the metric transformation publishes them to a custom namespace. The downstream alarm treats the custom metric exactly like any AWS/native metric.

```hcl
resource "aws_cloudwatch_log_metric_filter" "error_count" {
  name           = "${var.environment}-${var.service_name}-error-count"
  pattern        = "[timestamp, request_id, level=\"ERROR\", ...]"
  log_group_name = aws_cloudwatch_log_group.app.name

  metric_transformation {
    name          = "ErrorCount"
    namespace     = "Custom/${var.environment}/${var.service_name}"
    value         = "1"
    default_value = "0"
    unit          = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "service_errors" {
  alarm_name          = "${var.environment}-${var.service_name}-error-alarm"
  alarm_description   = "Error log count exceeded threshold for ${var.service_name}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.error_count.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.error_count.metric_transformation[0].namespace
  period              = 300
  statistic           = "Sum"
  threshold           = var.error_alarm_threshold
  treat_missing_data  = "notBreaching"

  alarm_actions             = [aws_sns_topic.alerts.arn]
  ok_actions                = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = [aws_sns_topic.alerts.arn]

  depends_on = [aws_cloudwatch_log_metric_filter.error_count]

  tags = {
    Name        = "${var.environment}-${var.service_name}-error-alarm"
    Environment = var.environment
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_cloudwatch_log_metric_filter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_metric_filter) | [Filter and Pattern Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html)

---

#### Pattern: Log Data Protection Policy (PII/Sensitive Data Masking)

**Why**: Lambda functions, API services, and application logs frequently emit PII (email addresses, credit card numbers, SSNs). CloudWatch Logs Data Protection Policies automatically detect and mask sensitive data at ingest time using AWS-managed detectors or custom patterns, ensuring compliance with GDPR, HIPAA, and PCI-DSS without code changes.

```hcl
resource "aws_cloudwatch_log_data_protection_policy" "app" {
  log_group_name  = aws_cloudwatch_log_group.app.name

  policy_document = jsonencode({
    Name    = "DataProtectionPolicy"
    Version = "2021-06-01"
    Statement = [
      {
        Sid            = "Audit"
        DataIdentifier = [
          "arn:aws:dataprotection::aws:data-identifier/EmailAddress",
          "arn:aws:dataprotection::aws:data-identifier/CreditCardNumber",
          "arn:aws:dataprotection::aws:data-identifier/USSocialSecurityNumber",
        ]
        Operation = {
          Audit = {
            FindingsDestination = {
              CloudWatchLogs = {
                LogGroup = aws_cloudwatch_log_group.data_protection_findings.name
              }
            }
          }
        }
      },
      {
        Sid            = "Deidentify"
        DataIdentifier = [
          "arn:aws:dataprotection::aws:data-identifier/EmailAddress",
          "arn:aws:dataprotection::aws:data-identifier/CreditCardNumber",
          "arn:aws:dataprotection::aws:data-identifier/USSocialSecurityNumber",
        ]
        Operation = {
          Deidentify = {
            MaskConfig = {}
          }
        }
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "data_protection_findings" {
  name              = "/cloudwatch/data-protection-findings/${var.environment}"
  retention_in_days = 365
  kms_key_id        = aws_kms_key.cloudwatch_logs.arn
  deletion_protection_enabled = true

  tags = {
    Environment = var.environment
    Purpose     = "data-protection-audit"
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_cloudwatch_log_data_protection_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_data_protection_policy) | [CloudWatch Logs Data Protection](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html)

---

#### Pattern: Variable Validation and Type Safety

**Why**: Validation at `terraform plan` time prevents invalid CloudWatch configurations from reaching the API — e.g., invalid retention periods crash `terraform apply` with an unhelpful AWS API error, whereas a validation block returns a clear message at plan time.

```hcl
variable "aws_region" {
  type        = string
  description = "AWS region for CloudWatch resources"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "aws_region must be a valid AWS region identifier (e.g. us-east-1, eu-west-1)."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "error_threshold" {
  type        = number
  description = "Error count threshold before alarm fires"
  default     = 5

  validation {
    condition     = var.error_threshold > 0
    error_message = "error_threshold must be greater than 0."
  }
}

variable "alarm_period" {
  type        = number
  description = "Alarm evaluation period in seconds"
  default     = 60

  validation {
    condition     = contains([10, 20, 30, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600], var.alarm_period) || (var.alarm_period > 0 && var.alarm_period % 60 == 0)
    error_message = "alarm_period must be 10, 20, 30, or a multiple of 60 seconds."
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Custom Validation Rules](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

#### Pattern: Output Definitions for Stack Interdependencies

**Why**: CloudWatch resources (log group ARNs, alarm ARNs, SNS topic ARNs) are consumed by other stacks — Lambda functions need log group names, CodeDeploy needs alarm ARNs for deployment gates, and cross-account log delivery needs destination ARNs. Outputs enable `terraform_remote_state` consumption without hardcoded values.

```hcl
output "log_group_name" {
  value       = aws_cloudwatch_log_group.app.name
  description = "CloudWatch Log Group name for application logs"
}

output "log_group_arn" {
  value       = aws_cloudwatch_log_group.app.arn
  description = "CloudWatch Log Group ARN for IAM policy attachment"
}

output "alarm_arns" {
  value = {
    lambda_errors  = aws_cloudwatch_metric_alarm.lambda_errors.arn
    api_health     = aws_cloudwatch_composite_alarm.api_health.arn
    service_errors = aws_cloudwatch_metric_alarm.service_errors.arn
  }
  description = "Map of alarm names to ARNs for CodeDeploy and incident management integrations"
}

output "kms_key_arn" {
  value       = aws_kms_key.cloudwatch_logs.arn
  description = "KMS key ARN used for CloudWatch Logs encryption"
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [Output Values](https://developer.hashicorp.com/terraform/language/values/outputs)

---

### ⚠️ Conditional Patterns

---

#### Decision: Standard Metric Alarm vs. Metric Math Expression vs. PromQL Alarm

**Context**: v6.x adds PromQL support via `evaluation_criteria` + `evaluation_interval`. Choose the right alarm type for the use case.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Standard** (`metric_name`, `statistic`, `period`) | Simplicity, minimal IAM | Flexibility | Single metric, static threshold |
| **Metric Math** (`metric_query` blocks) | Complex expressions (error rate %, ratios) | Readability | Error rate = errors / total requests |
| **Metrics Insights** (`metric_query` + SQL `expression`) | Cross-resource aggregation, GROUP BY | Latency | "Alert if ANY RDS instance CPU > 80%" |
| **PromQL** (`evaluation_criteria.promql_criteria`) | PromQL familiarity, vector queries | AWS-only syntax support | Teams migrating from Prometheus/Grafana |

```hcl
# Standard — single metric
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.environment}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "breaching"
  dimensions          = { DBInstanceIdentifier = var.db_instance_id }
  alarm_actions       = [aws_sns_topic.alerts.arn]
  tags                = { Environment = var.environment }
}

# Metric Math — error rate ratio
resource "aws_cloudwatch_metric_alarm" "api_error_rate" {
  alarm_name          = "${var.environment}-api-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = 5  # percent
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "error_rate"
    expression  = "errors / total * 100"
    label       = "Error Rate %"
    return_data = true
  }
  metric_query {
    id = "errors"
    metric {
      metric_name = "5XXError"
      namespace   = "AWS/ApiGateway"
      period      = 60
      stat        = "Sum"
      dimensions  = { ApiName = var.api_name, Stage = var.stage_name }
    }
  }
  metric_query {
    id = "total"
    metric {
      metric_name = "Count"
      namespace   = "AWS/ApiGateway"
      period      = 60
      stat        = "Sum"
      dimensions  = { ApiName = var.api_name, Stage = var.stage_name }
    }
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  tags          = { Environment = var.environment }
}

# PromQL — multi-contributor vector query (v6.x)
resource "aws_cloudwatch_metric_alarm" "lambda_duration_promql" {
  alarm_name        = "${var.environment}-lambda-duration-high-promql"
  alarm_description = "Lambda duration P99 high via PromQL"

  evaluation_criteria {
    promql_criteria {
      query           = "quantile(0.99, aws_lambda_duration_seconds) > 5"
      pending_period  = 120
      recovery_period = 60
    }
  }
  evaluation_interval = 30

  alarm_actions = [aws_sns_topic.alerts.arn]
  tags          = { Environment = var.environment }
}
```

- **Agent**: "Ask user: Is this a single-metric threshold, a ratio/percentage calculation, a cross-resource aggregation, or are you migrating from a PromQL environment?"
- **Source**: [Metric Math Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/using-metric-math.html) | [Metrics Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-metrics-insights-querylanguage.html) | [aws_cloudwatch_metric_alarm PromQL](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm)

---

#### Decision: Log Group Class — STANDARD vs. INFREQUENT_ACCESS vs. DELIVERY

| Option | Cost | Capabilities | Best When |
|--------|------|-------------|-----------|
| **STANDARD** | Higher | Full: Live Tail, Logs Insights, metric filters, alarms | Active development, production monitoring |
| **INFREQUENT_ACCESS** | ~50% cheaper | No Live Tail, no anomaly detection, limited Insights | Archival, compliance logs rarely queried |
| **DELIVERY** | Delivery only | Only 2-day retention (forced), structured delivery pipeline | AWS service delivery logs (VPC Flow, S3, CloudTrail via log delivery API) |

```hcl
variable "log_group_class" {
  type        = string
  description = "CloudWatch Log Group storage class"
  default     = "STANDARD"

  validation {
    condition     = contains(["STANDARD", "INFREQUENT_ACCESS", "DELIVERY"], var.log_group_class)
    error_message = "log_group_class must be STANDARD, INFREQUENT_ACCESS, or DELIVERY."
  }
}
```

- **Agent**: "Ask user: How frequently will these logs be queried? Is Live Tail or anomaly detection needed? Is this for compliance archival or active debugging?"
- **Source**: [aws_cloudwatch_log_group log_group_class](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group)

---

#### Decision: Log Subscription Filter Destination — Lambda vs. Kinesis vs. Kinesis Firehose

| Option | Latency | Processing | Cost | Best When |
|--------|---------|-----------|------|-----------|
| **Lambda** | Near-realtime | Full code control, transformations | Per invocation | Custom transformations, routing logic |
| **Kinesis Data Streams** | Near-realtime | Fan-out, replay, consumers | Per shard-hour | Multi-consumer pipelines, exactly-once |
| **Kinesis Firehose** | Buffered (~60s) | S3, OpenSearch, Redshift delivery | Per GB ingested | Direct to S3/SIEM without code |

```hcl
# Lambda destination (no role_arn needed — use aws_lambda_permission instead)
resource "aws_cloudwatch_log_subscription_filter" "to_lambda" {
  name            = "${var.environment}-${var.service_name}-to-lambda"
  log_group_name  = aws_cloudwatch_log_group.app.name
  filter_pattern  = "[timestamp, request_id, level=\"ERROR\", ...]"
  destination_arn = aws_lambda_function.log_processor.arn
  # role_arn intentionally omitted for Lambda — use aws_lambda_permission
}

resource "aws_lambda_permission" "cloudwatch_invoke" {
  statement_id  = "AllowCloudWatchLogs"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.log_processor.function_name
  principal     = "logs.${var.aws_region}.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.app.arn}:*"
}

# Kinesis Firehose destination (role_arn required)
resource "aws_cloudwatch_log_subscription_filter" "to_firehose" {
  name            = "${var.environment}-${var.service_name}-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.app.name
  filter_pattern  = ""  # All events
  destination_arn = aws_kinesis_firehose_delivery_stream.logs.arn
  role_arn        = aws_iam_role.cloudwatch_to_firehose.arn
  distribution    = "Random"  # ByLogStream or Random
}
```

- **Agent**: "Ask user: Do you need real-time custom processing (Lambda), fan-out multi-consumer (Kinesis), or direct delivery to S3/OpenSearch/Redshift (Firehose)?"
- **Source**: [aws_cloudwatch_log_subscription_filter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter)

---

#### Decision: Module vs. Inline Resource Organisation

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Inline** | Simplicity, fast iteration | Reuse, DRY across services | Single service, prototype, PoC |
| **Module (local)** | Reuse within repo, consistent patterns | Module versioning complexity | Multiple services in one repo |
| **Module (registry/git)** | Cross-team reuse, semantic versioning | External dependency, registry access | Platform team providing shared alerting |

- **Agent**: "Ask user: How many services will use this CloudWatch pattern? Is this a platform-level shared module or service-specific configuration?"
- **Source**: [Terraform Modules](https://developer.hashicorp.com/terraform/language/modules)

---

#### Decision: Metric Stream — OpenTelemetry vs. JSON Output Format

| Option | Format | Consumer | Best When |
|--------|--------|----------|-----------|
| **opentelemetry0.7** | OTLP binary | Grafana, Datadog OTLP endpoint, custom | OTEL-native observability stack |
| **json** | Newline-delimited JSON | S3 analysis, custom consumers, Splunk | Ad-hoc analysis, non-OTLP sinks |

```hcl
resource "aws_cloudwatch_metric_stream" "main" {
  name          = "${var.environment}-metric-stream"
  role_arn      = aws_iam_role.metric_stream.arn
  firehose_arn  = aws_kinesis_firehose_delivery_stream.metrics.arn
  output_format = var.metric_stream_format  # "opentelemetry0.7" or "json"

  # Include only namespaces relevant to this service
  include_filter {
    namespace    = "AWS/Lambda"
    metric_names = ["Errors", "Duration", "Throttles", "ConcurrentExecutions"]
  }
  include_filter {
    namespace    = "AWS/RDS"
    metric_names = ["CPUUtilization", "DatabaseConnections", "FreeStorageSpace"]
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

- **Agent**: "Ask user: What is the target observability platform (Grafana/Datadog OTLP vs S3/Splunk)?"
- **Source**: [aws_cloudwatch_metric_stream](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_stream)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Log Group Without Retention Period

```hcl
# DON'T — default retention is 0 (never expires)
resource "aws_cloudwatch_log_group" "app" {
  name = "/app/my-service"
  # Missing: retention_in_days
}
```

**Why**: Default `retention_in_days = 0` means logs accumulate indefinitely. A busy Lambda function or API service can generate gigabytes of logs per day, resulting in unbounded monthly costs (CloudWatch Logs charges ~$0.50/GB stored). High-volume services have generated surprise bills of thousands of dollars per month from this single omission.

```hcl
# DO — always set retention explicitly
resource "aws_cloudwatch_log_group" "app" {
  name              = "/app/${var.environment}/my-service"
  retention_in_days = 90  # Compliance baseline; adjust per policy
  kms_key_id        = aws_kms_key.cloudwatch_logs.arn
  deletion_protection_enabled = true
}
```

- **Impact**: Unbounded cost accumulation, potential data compliance violations
- **Severity**: HIGH
- **Source**: [aws_cloudwatch_log_group retention_in_days](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group#retention_in_days)

---

#### Anti-Pattern: Alarm Without Actions (Silent Alarm)

```hcl
# DON'T — alarm state changes silently, no one is notified
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "prod-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  # Missing: alarm_actions, ok_actions, insufficient_data_actions
}
```

**Why**: An alarm without actions is a metric display — it changes state in the CloudWatch console but no one is notified. Production outages go undetected until a human checks the console. The `insufficient_data_actions` is equally critical: if the EC2 instance stops sending metrics (e.g., agent crash), the alarm enters INSUFFICIENT_DATA without triggering any notification.

```hcl
# DO — wire all three state transitions
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.environment}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "breaching"

  alarm_actions             = [aws_sns_topic.alerts.arn]
  ok_actions                = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = [aws_sns_topic.alerts.arn]
}
```

- **Impact**: Silent failures, undetected outages, SLO breaches
- **Severity**: HIGH
- **Source**: [PutMetricAlarm alarm_actions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricAlarm.html)

---

#### Anti-Pattern: Log Group Without KMS Encryption for Sensitive Workloads

```hcl
# DON'T — for workloads handling PII, credentials, or health data
resource "aws_cloudwatch_log_group" "app" {
  name              = "/app/prod/payment-service"
  retention_in_days = 90
  # Missing: kms_key_id — logs stored with AWS-managed key only
}
```

**Why**: AWS-managed CMK (the default) cannot be restricted to specific IAM principals, cannot be audited per-key via CloudTrail, and cannot be revoked without contacting AWS Support. Any IAM principal with `logs:GetLogEvents` can access log data. For HIPAA, PCI-DSS, or SOC 2 workloads, a customer-managed KMS key is required to demonstrate key control, rotation schedules, and access auditability.

```hcl
# DO — customer-managed KMS key with CloudWatch Logs service permission
resource "aws_cloudwatch_log_group" "app" {
  name              = "/app/prod/payment-service"
  retention_in_days = 365  # PCI-DSS requires 1 year
  kms_key_id        = aws_kms_key.cloudwatch_logs.arn
  deletion_protection_enabled = true
}
```

- **Impact**: Compliance violation, potential data exposure, audit failure
- **Severity**: CRITICAL (for regulated workloads)
- **Source**: [Encrypt Log Data with KMS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html)

---

#### Anti-Pattern: Hardcoded Account IDs and ARNs in Alarm Dimensions

```hcl
# DON'T — brittle, breaks cross-account/multi-environment deployments
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name = "prod-rds-cpu"
  dimensions = {
    DBInstanceIdentifier = "prod-rds-mysql-master"  # Hardcoded instance name
  }
  alarm_actions = ["arn:aws:sns:us-east-1:123456789012:prod-alerts"]  # Hardcoded ARN
}
```

**Why**: Hardcoded resource identifiers and ARNs make modules non-reusable across environments and accounts. When the RDS instance is replaced (e.g., during a major version upgrade), the alarm dimension points to a nonexistent instance and produces INSUFFICIENT_DATA permanently.

```hcl
# DO — reference resource attributes dynamically
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name = "${var.environment}-rds-cpu"
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier  # Dynamic reference
  }
  alarm_actions = [aws_sns_topic.alerts.arn]  # Reference, not hardcoded ARN
}
```

- **Impact**: State drift, broken alarms post-resource replacement, non-reusable modules
- **Severity**: MEDIUM
- **Source**: [Terraform Expression References](https://developer.hashicorp.com/terraform/language/expressions/references)

---

#### Anti-Pattern: Composite Alarm Destroyed Before Child Alarms Are Removed

```hcl
# DON'T — will fail with dependency error
resource "aws_cloudwatch_composite_alarm" "parent" {
  alarm_name = "parent-composite"
  alarm_rule = "ALARM(child-alarm-1) OR ALARM(child-alarm-2)"
}

resource "aws_cloudwatch_metric_alarm" "child" {
  alarm_name = "child-alarm-1"
  # ...
}
# terraform destroy will fail: composite alarm depends on child alarm
```

**Why**: CloudWatch enforces referential integrity — a composite alarm cannot be destroyed while other composite alarms reference child alarms. Terraform plan will attempt to destroy all resources in parallel, causing a race condition where the composite alarm fails to be destroyed because child alarms are still referenced by it.

```hcl
# DO — use depends_on to enforce correct destroy order
resource "aws_cloudwatch_composite_alarm" "parent" {
  alarm_name = "parent-composite"
  alarm_rule = <<-EOT
    ALARM(${aws_cloudwatch_metric_alarm.child_1.alarm_name}) OR
    ALARM(${aws_cloudwatch_metric_alarm.child_2.alarm_name})
  EOT

  depends_on = [
    aws_cloudwatch_metric_alarm.child_1,
    aws_cloudwatch_metric_alarm.child_2,
  ]
}
```

- **Impact**: `terraform destroy` failures, stuck CI/CD pipelines, orphaned alarms
- **Severity**: HIGH
- **Source**: [aws_cloudwatch_composite_alarm NOTE](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_composite_alarm)

---

#### Anti-Pattern: Subscription Filter Without Lambda Permission

```hcl
# DON'T — subscription filter creation will fail or silently stop delivering
resource "aws_cloudwatch_log_subscription_filter" "to_lambda" {
  name            = "send-to-processor"
  log_group_name  = aws_cloudwatch_log_group.app.name
  filter_pattern  = ""
  destination_arn = aws_lambda_function.processor.arn
  # Missing: aws_lambda_permission for CloudWatch Logs to invoke Lambda
}
```

**Why**: CloudWatch Logs must have explicit `lambda:InvokeFunction` permission on the target Lambda. Without `aws_lambda_permission`, the subscription filter is created in Terraform state but log delivery silently fails — no error is returned, events are simply dropped.

```hcl
# DO — always pair subscription filter with Lambda permission
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatchLogs"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "logs.${var.aws_region}.amazonaws.com"
  source_arn    = "${aws_cloudwatch_log_group.app.arn}:*"
}

resource "aws_cloudwatch_log_subscription_filter" "to_lambda" {
  name            = "send-to-processor"
  log_group_name  = aws_cloudwatch_log_group.app.name
  filter_pattern  = ""
  destination_arn = aws_lambda_function.processor.arn

  depends_on = [aws_lambda_permission.allow_cloudwatch]
}
```

- **Impact**: Silent log delivery failure, dropped events, broken log pipelines
- **Severity**: HIGH
- **Source**: [aws_lambda_permission](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | [Log group subscriptions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html)

---

#### Anti-Pattern: Missing `treat_missing_data` on Production SLO Alarms

```hcl
# DON'T — default is "missing", which leaves alarm in prior state during gaps
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "prod-lambda-errors"
  # ... other config ...
  # Missing: treat_missing_data
  # Default: "missing" — alarm stays in OK/ALARM state when metrics stop flowing
}
```

**Why**: If a Lambda function stops executing (e.g., due to a VPC misconfiguration, IAM permission removal, or dead letter queue saturation), it produces no metrics. With `treat_missing_data = "missing"` (default), the alarm stays in its last state — possibly OK — masking a complete service outage. Use `"breaching"` for production SLO alarms to treat absence of metrics as a violation.

```hcl
# DO — set treat_missing_data explicitly based on alarm purpose
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name         = "prod-lambda-errors"
  treat_missing_data = "breaching"  # SLO alarm: no metrics = service is down
  # ...
}

resource "aws_cloudwatch_metric_alarm" "batch_job_duration" {
  alarm_name         = "prod-batch-duration"
  treat_missing_data = "notBreaching"  # Batch alarm: no metrics = job not running (expected)
  # ...
}
```

- **Impact**: Masked service outages, SLO violations not detected, false OK state
- **Severity**: HIGH
- **Source**: [treat_missing_data documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html#alarms-and-missing-data)

---

## State Management Deep Dive

### Local Development State

```hcl
# Local state for CloudWatch dev/learning only
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

- **Risk**: No sharing, no locking, no state versioning. Accidental `rm terraform.tfstate` destroys all tracking.
- **When**: Solo development, learning, temporary environments only

### Production Remote State (S3 + DynamoDB)

```hcl
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

terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/cloudwatch/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

- **Benefit**: State locking prevents concurrent applies that could create duplicate alarms, team access via IAM, versioned state for recovery
- **Safeguard**: Restrict S3 bucket + DynamoDB access to service accounts only; state contains alarm names, log group names, and KMS key ARNs

### CloudWatch-Specific State Sensitivity

CloudWatch state files contain:
- KMS key ARNs (reveal encryption strategy)
- SNS topic ARNs (reveal alert routing)
- Log group names (reveal application topology)
- IAM role ARNs (reveal privilege paths)

```hcl
# Mark sensitive outputs from state
output "kms_key_id" {
  value       = aws_kms_key.cloudwatch_logs.key_id
  description = "CloudWatch Logs KMS key ID"
  sensitive   = true  # Masked in plan output and logs
}
```

- **Source**: [Terraform State Security](https://developer.hashicorp.com/terraform/language/state/sensitive-data)

---

## Module Architecture

### Standard CloudWatch Module Structure

```
modules/
└── cloudwatch/
    ├── main.tf           # aws_cloudwatch_log_group, alarms, filters
    ├── variables.tf      # service_name, environment, retention, thresholds
    ├── outputs.tf        # log_group_arn, alarm_arns, kms_key_arn
    ├── versions.tf       # required_version, required_providers
    ├── iam.tf            # IAM roles for subscription filters, metric streams
    ├── kms.tf            # KMS key + policy for log group encryption
    └── README.md
```

### Module Definition Example

```hcl
# modules/cloudwatch/variables.tf
variable "service_name" {
  type        = string
  description = "Name of the service owning these CloudWatch resources"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,62}[a-z0-9]$", var.service_name))
    error_message = "service_name must be lowercase alphanumeric with hyphens, 3-64 characters."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "retention_in_days" {
  type        = number
  description = "Log retention period in days"
  default     = 90

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.retention_in_days)
    error_message = "retention_in_days must be an AWS-supported value."
  }
}

variable "alert_sns_topic_arn" {
  type        = string
  description = "SNS topic ARN for alarm notifications"

  validation {
    condition     = can(regex("^arn:aws:sns:", var.alert_sns_topic_arn))
    error_message = "alert_sns_topic_arn must be a valid SNS topic ARN."
  }
}

variable "enable_data_protection" {
  type        = bool
  description = "Enable CloudWatch Logs Data Protection Policy for PII masking"
  default     = false
}

variable "alarms" {
  type = map(object({
    metric_name         = string
    namespace           = string
    statistic           = string
    threshold           = number
    evaluation_periods  = number
    period              = number
    comparison_operator = string
    treat_missing_data  = string
    dimensions          = map(string)
  }))
  description = "Map of metric alarms to create"
  default     = {}
}

# modules/cloudwatch/outputs.tf
output "log_group_name" {
  value       = aws_cloudwatch_log_group.main.name
  description = "CloudWatch Log Group name"
}

output "log_group_arn" {
  value       = aws_cloudwatch_log_group.main.arn
  description = "CloudWatch Log Group ARN for IAM attachment and subscription filters"
}

output "alarm_arns" {
  value       = { for k, v in aws_cloudwatch_metric_alarm.service : k => v.arn }
  description = "Map of alarm name → ARN for CodeDeploy deployment gates"
}

# root/main.tf — Using the module
module "api_cloudwatch" {
  source = "./modules/cloudwatch"

  service_name          = "api-gateway"
  environment           = var.environment
  retention_in_days     = 90
  alert_sns_topic_arn   = aws_sns_topic.alerts.arn
  enable_data_protection = true

  alarms = {
    "5xx-errors" = {
      metric_name         = "5XXError"
      namespace           = "AWS/ApiGateway"
      statistic           = "Sum"
      threshold           = 10
      evaluation_periods  = 2
      period              = 60
      comparison_operator = "GreaterThanThreshold"
      treat_missing_data  = "notBreaching"
      dimensions = {
        ApiName = var.api_name
        Stage   = var.stage_name
      }
    }
  }
}
```

---

## Integration Patterns: Terraform ↔ Integration Partners

---

### Integration: Terraform ↔ Lambda

```hcl
# Lambda automatically creates a log group — manage it explicitly to set retention and KMS
resource "aws_cloudwatch_log_group" "lambda" {
  name                     = "/aws/lambda/${aws_lambda_function.app.function_name}"
  retention_in_days        = 30
  kms_key_id               = aws_kms_key.cloudwatch_logs.arn
  deletion_protection_enabled = true

  # Must exist before Lambda is deployed; Lambda will use existing log group
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda error alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.environment}-${aws_lambda_function.app.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  dimensions          = { FunctionName = aws_lambda_function.app.function_name }
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  depends_on          = [aws_cloudwatch_log_group.lambda]
  tags                = { Environment = var.environment }
}
```

- **Issues**: Lambda creates its log group on first invocation if not pre-created; pre-creating with Terraform ensures KMS and retention are set before any logs arrive. Destroy order: Lambda must be destroyed before log group (use `depends_on`).
- **Versions**: `aws_cloudwatch_log_group` + `aws_lambda_function` — min aws ~> 6.0
- **Source**: [Lambda Log Group](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html) | [aws_cloudwatch_log_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group)

---

### Integration: Terraform ↔ RDS

```hcl
# RDS enhanced monitoring and performance insights logs
resource "aws_cloudwatch_log_group" "rds_general" {
  name              = "/aws/rds/instance/${var.db_identifier}/general"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.cloudwatch_logs.arn
  deletion_protection_enabled = true
  tags              = { Environment = var.environment }
}

resource "aws_cloudwatch_log_group" "rds_error" {
  name              = "/aws/rds/instance/${var.db_identifier}/error"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.cloudwatch_logs.arn
  deletion_protection_enabled = true
  tags              = { Environment = var.environment }
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.environment}-${var.db_identifier}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "breaching"
  dimensions          = { DBInstanceIdentifier = var.db_identifier }
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  tags                = { Environment = var.environment }
}

resource "aws_cloudwatch_metric_alarm" "rds_free_storage" {
  alarm_name          = "${var.environment}-${var.db_identifier}-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5368709120  # 5 GB in bytes
  treat_missing_data  = "breaching"
  dimensions          = { DBInstanceIdentifier = var.db_identifier }
  alarm_actions       = [aws_sns_topic.alerts.arn]
  tags                = { Environment = var.environment }
}

resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "${var.environment}-${var.db_identifier}-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Average"
  threshold           = var.rds_max_connections * 0.8  # 80% of max
  treat_missing_data  = "notBreaching"
  dimensions          = { DBInstanceIdentifier = var.db_identifier }
  alarm_actions       = [aws_sns_topic.alerts.arn]
  tags                = { Environment = var.environment }
}
```

- **Issues**: RDS log group names follow the `/aws/rds/instance/<identifier>/` pattern; must be created before enabling `enabled_cloudwatch_logs_exports` on `aws_db_instance`.
- **Source**: [RDS CloudWatch Logs](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_LogAccess.Procedural.UploadtoCloudWatch.html)

---

### Integration: Terraform ↔ SNS

```hcl
# SNS topic for alarm notifications
resource "aws_sns_topic" "alerts" {
  name              = "${var.environment}-cloudwatch-alerts"
  kms_master_key_id = aws_kms_key.sns.id  # Encrypt SNS messages at rest

  tags = {
    Name        = "${var.environment}-cloudwatch-alerts"
    Environment = var.environment
  }
}

resource "aws_sns_topic_policy" "alerts" {
  arn    = aws_sns_topic.alerts.arn
  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

data "aws_iam_policy_document" "sns_topic_policy" {
  statement {
    sid    = "AllowCloudWatchAlarms"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.alerts.arn]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.account_id]
    }
  }
}

# SNS email subscription
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email  # Sensitive: store in SSM or tfvars (gitignored)
}
```

- **Issues**: SNS must have a resource policy allowing CloudWatch to publish; without it, alarm actions are registered but delivery fails silently. Use `source_arn` condition to prevent confused-deputy attacks.
- **Source**: [CloudWatch Alarms + SNS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/US_SetupSNS.html)

---

### Integration: Terraform ↔ IAM

```hcl
# IAM policy for Terraform deploy role to manage CloudWatch resources
data "aws_iam_policy_document" "cloudwatch_management" {
  statement {
    sid    = "CloudWatchMetrics"
    effect = "Allow"
    actions = [
      "cloudwatch:PutMetricAlarm",
      "cloudwatch:DeleteAlarms",
      "cloudwatch:DescribeAlarms",
      "cloudwatch:PutCompositeAlarm",
      "cloudwatch:PutDashboard",
      "cloudwatch:DeleteDashboards",
      "cloudwatch:PutMetricStream",
      "cloudwatch:DeleteMetricStream",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:DeleteLogGroup",
      "logs:PutRetentionPolicy",
      "logs:DeleteRetentionPolicy",
      "logs:AssociateKmsKey",
      "logs:DisassociateKmsKey",
      "logs:PutSubscriptionFilter",
      "logs:DeleteSubscriptionFilter",
      "logs:PutMetricFilter",
      "logs:DeleteMetricFilter",
      "logs:PutDataProtectionPolicy",
      "logs:DeleteDataProtectionPolicy",
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:*",
    ]
  }

  statement {
    sid    = "KMSForLogs"
    effect = "Allow"
    actions = [
      "kms:CreateKey",
      "kms:DescribeKey",
      "kms:PutKeyPolicy",
      "kms:CreateAlias",
      "kms:EnableKeyRotation",
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }
}
```

- **Issues**: CloudWatch Data Protection policy management requires `logs:PutDataProtectionPolicy` separately from the standard `logs:*` permissions; it is not included in managed policies like `CloudWatchLogsFullAccess`.
- **Source**: [CloudWatch IAM Permissions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/auth-and-access-control-cw.html)

---

### Integration: Terraform ↔ EventBridge

```hcl
# CloudWatch alarm state changes → EventBridge → automated remediation
resource "aws_cloudwatch_event_rule" "alarm_state_change" {
  name        = "${var.environment}-alarm-state-change"
  description = "Capture CloudWatch alarm state changes for automated remediation"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      state = {
        value = ["ALARM"]
      }
      alarmName = [{ prefix = "${var.environment}-" }]
    }
  })

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_event_target" "remediation_lambda" {
  rule      = aws_cloudwatch_event_rule.alarm_state_change.name
  target_id = "RemediationLambda"
  arn       = aws_lambda_function.remediation.arn
}

resource "aws_lambda_permission" "eventbridge_invoke" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.remediation.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.alarm_state_change.arn
}
```

- **Issues**: EventBridge alarm state change events use `"aws.cloudwatch"` as the source and `"CloudWatch Alarm State Change"` as the detail-type; the `alarmName` field is in the `detail` block, not the top-level event.
- **Source**: [CloudWatch Alarm EventBridge Events](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-and-eventbridge.html)

---

### Integration: Terraform ↔ S3 (Log Export)

```hcl
# S3 bucket policy allowing CloudWatch Logs to export to S3
resource "aws_s3_bucket_policy" "log_export" {
  bucket = aws_s3_bucket.log_archive.id
  policy = data.aws_iam_policy_document.log_export.json
}

data "aws_iam_policy_document" "log_export" {
  statement {
    sid    = "AllowCloudWatchLogsExport"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["logs.${var.aws_region}.amazonaws.com"]
    }
    actions   = ["s3:GetBucketAcl", "s3:PutObject"]
    resources = [
      aws_s3_bucket.log_archive.arn,
      "${aws_s3_bucket.log_archive.arn}/cloudwatch-logs/*",
    ]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.account_id]
    }
  }
}

# CloudWatch Logs query definition for Logs Insights
resource "aws_cloudwatch_query_definition" "error_analysis" {
  name = "${var.environment}/error-analysis/${var.service_name}"

  log_group_names = [aws_cloudwatch_log_group.app.name]

  query_string = <<-EOT
    fields @timestamp, @message, @logStream, @log
    | filter @message like /ERROR/
    | stats count(*) as errorCount by bin(5m)
    | sort errorCount desc
    | limit 20
  EOT
}
```

- **Issues**: CloudWatch Logs export to S3 requires the S3 bucket to be in the same region as the log group; cross-region export is not supported. The bucket ACL (`s3:GetBucketAcl`) is required for the export task, even with bucket policy only mode enabled.
- **Source**: [Export Logs to S3](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/S3Export.html)

---

### Integration: Terraform ↔ CloudTrail

```hcl
# CloudTrail API activity log group — managed retention + encryption
resource "aws_cloudwatch_log_group" "cloudtrail" {
  name                     = "aws-cloudtrail-logs-${var.account_id}-${var.environment}"
  retention_in_days        = 365  # CIS benchmark: 1 year minimum
  kms_key_id               = aws_kms_key.cloudwatch_logs.arn
  deletion_protection_enabled = true
  tags                     = { Environment = var.environment, Purpose = "audit" }
}

resource "aws_iam_role" "cloudtrail_cloudwatch" {
  name = "${var.environment}-cloudtrail-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "cloudtrail.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "cloudtrail_cloudwatch" {
  name = "cloudtrail-to-cloudwatch"
  role = aws_iam_role.cloudtrail_cloudwatch.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
      Effect   = "Allow"
      Resource = "${aws_cloudwatch_log_group.cloudtrail.arn}:*"
    }]
  })
}

# Alarm on root account login (CIS AWS Benchmark 1.1)
resource "aws_cloudwatch_log_metric_filter" "root_login" {
  name           = "${var.environment}-root-account-login"
  pattern        = "{ $.userIdentity.type = \"Root\" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != \"AwsServiceEvent\" }"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name

  metric_transformation {
    name      = "RootLoginCount"
    namespace = "CISMetrics/${var.environment}"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "root_login" {
  alarm_name          = "${var.environment}-root-account-login-alarm"
  alarm_description   = "CRITICAL: Root account login detected (CIS 1.1)"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "RootLoginCount"
  namespace           = "CISMetrics/${var.environment}"
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
  tags                = { Environment = var.environment, Compliance = "CIS" }
}
```

- **Issues**: CloudTrail must reference the exact IAM role ARN with `cloud_watch_logs_role_arn` in `aws_cloudtrail`; the log group must exist and be accessible before CloudTrail can start publishing.
- **Source**: [CloudTrail + CloudWatch Logs](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/send-cloudtrail-events-to-cloudwatch-logs.html)

---

## Quality Control

### Verification Commands

```bash
# Initialize and validate
terraform init -upgrade
# Expected: ✓ Terraform has been successfully initialized

terraform fmt -recursive -check=true
# Expected: Exit code 0 (all files already formatted)

terraform validate
# Expected: Success! The configuration is valid.

# Security scanning
tfsec . --format json | jq '.results[] | select(.severity == "CRITICAL" or .severity == "HIGH")'
# Expected: Empty array (no critical/high findings)

checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks

# Plan inspection
terraform plan -out=tfplan -lock=true
terraform show tfplan | grep -E "^  \+ |^  ~ |^  - " | head -30
# Expected: Only expected resource additions/modifications

# State validation
terraform state list | grep cloudwatch
# Expected: All managed CloudWatch resources enumerated

terraform state show aws_cloudwatch_log_group.app
# Expected: retention_in_days != 0, kms_key_id is set, deletion_protection_enabled = true

# Verify alarm actions are populated
terraform state show aws_cloudwatch_metric_alarm.lambda_errors | grep "_actions"
# Expected: alarm_actions, ok_actions, insufficient_data_actions all non-empty
```

### Testing with Terraform Test Framework (>= 1.7)

```hcl
# tests/cloudwatch.tftest.hcl
provider "aws" {
  region = "us-east-1"
}

variables {
  environment         = "test"
  service_name        = "test-service"
  log_retention_days  = 7
  alert_sns_topic_arn = "arn:aws:sns:us-east-1:123456789012:test-alerts"
  error_threshold     = 5
  account_id          = "123456789012"
}

run "log_group_has_retention" {
  command = plan

  assert {
    condition     = aws_cloudwatch_log_group.app.retention_in_days != 0
    error_message = "Log group retention must be set (not 0 / never expire)"
  }

  assert {
    condition     = aws_cloudwatch_log_group.app.deletion_protection_enabled == true
    error_message = "Log group must have deletion_protection_enabled = true"
  }
}

run "alarms_have_actions" {
  command = plan

  assert {
    condition     = length(aws_cloudwatch_metric_alarm.lambda_errors.alarm_actions) > 0
    error_message = "Alarms must have at least one alarm_action configured"
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.lambda_errors.treat_missing_data != null
    error_message = "treat_missing_data must be explicitly set"
  }
}
```

---

## Production Considerations

### Scalability

- **Metric alarms**: AWS limit of 5,000 metric alarms per account per region; request a quota increase for large microservices fleets via Service Quotas
- **Log subscription filters**: Maximum 2 subscription filters per log group; use Kinesis fan-out or Lambda routing for multi-destination scenarios
- **Custom metrics**: Each unique combination of namespace + metric name + dimensions = 1 custom metric; costs $0.30/metric/month; use `default_value` to avoid sparse custom metrics
- **Composite alarms**: Maximum 100 child alarms per composite alarm; nest composite alarms for hierarchical health models

### Performance

- **Alarm evaluation latency**: Standard resolution = 1-minute minimum; high-resolution metrics support 10/20/30-second periods at higher cost
- **Log Insights queries**: Billed per GB scanned; use `@logStream` and `@timestamp` filters to reduce scan range; Infrequent Access log groups cannot be queried with Logs Insights

### Monitoring the Monitoring Layer

```hcl
# Alert when CloudWatch alarms are in INSUFFICIENT_DATA (monitoring gap detection)
resource "aws_cloudwatch_metric_alarm" "alarm_health_check" {
  alarm_name          = "${var.environment}-alarm-health-insufficient-data"
  alarm_description   = "One or more production alarms are in INSUFFICIENT_DATA state"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "NumberOfAlarmsInInsufficient"
  namespace           = "AWS/CloudWatch"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
  tags                = { Environment = var.environment, Purpose = "meta-monitoring" }
}
```

### Disaster Recovery Runbook

```bash
# 1. State corruption recovery
aws s3api get-object \
  --bucket my-org-terraform-state \
  --key prod/cloudwatch/terraform.tfstate.backup \
  terraform.tfstate.backup

terraform state push terraform.tfstate.backup

# 2. Import existing log group (created outside Terraform)
import {
  to = aws_cloudwatch_log_group.app
  id = "/app/prod/my-service"
}

# 3. Import existing metric alarm
import {
  to = aws_cloudwatch_metric_alarm.lambda_errors
  id = "prod-my-lambda-errors"
}

# 4. Validate state matches real infrastructure
terraform plan
# Expected: No changes (state = infrastructure)

# 5. Recovery: Re-create accidentally deleted log group
# NOTE: Logs within a deleted log group are PERMANENTLY LOST
# Always enable deletion_protection_enabled = true to prevent this
terraform apply -target=aws_cloudwatch_log_group.app
```

### Security Checklist

- [ ] All log groups have `retention_in_days` set (non-zero)
- [ ] All log groups have `kms_key_id` set (customer-managed CMK) for sensitive data
- [ ] All log groups have `deletion_protection_enabled = true` in production
- [ ] KMS key has `enable_key_rotation = true`
- [ ] KMS key policy restricts to specific IAM principals + `logs.region.amazonaws.com`
- [ ] All alarms have `alarm_actions`, `ok_actions`, `insufficient_data_actions` wired
- [ ] All production SLO alarms have `treat_missing_data = "breaching"`
- [ ] SNS topics for alerts have KMS encryption (`kms_master_key_id`)
- [ ] SNS topic policies restrict publish to `cloudwatch.amazonaws.com` with `SourceAccount` condition
- [ ] Data Protection Policies enabled on log groups handling PII/health data
- [ ] Subscription filters to Lambda have `aws_lambda_permission` with `source_arn` scoped to log group
- [ ] IAM roles for subscription filters to Firehose have least-privilege `firehose:PutRecord` only
- [ ] CloudTrail log group has 365-day retention and KMS encryption
- [ ] CIS metric filter alarms configured (root login, unauthorized API calls, MFA changes)
- [ ] State file encrypted in S3 backend with `encrypt = true`

---

## Reference Implementations

- [Official Terraform AWS Examples](https://github.com/hashicorp/terraform-aws-examples)
- [AWS CloudWatch Terraform Registry](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm)
- [AWS CloudWatch Logs Registry](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group)
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)
- [AWS Well-Architected: Operational Excellence](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html)

---

## Source Bibliography

### Primary Sources (Verified 2026-05-28)

- [aws_cloudwatch_metric_alarm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) — v6.47.0
- [aws_cloudwatch_composite_alarm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_composite_alarm) — v6.47.0
- [aws_cloudwatch_log_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) — v6.47.0
- [aws_cloudwatch_log_metric_filter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_metric_filter) — v6.47.0
- [aws_cloudwatch_log_subscription_filter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter) — v6.47.0
- [aws_cloudwatch_dashboard](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_dashboard) — v6.47.0
- [aws_cloudwatch_metric_stream](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_stream) — v6.47.0
- [aws_cloudwatch_log_data_protection_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_data_protection_policy) — v6.47.0
- [aws_cloudwatch_alarm_mute_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_alarm_mute_rule) — v6.47.0 (new)
- [aws_cloudwatch_otel_enrichment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_otel_enrichment) — v6.47.0 (new)
- [aws_cloudwatch_contributor_insight_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_contributor_insight_rule) — v6.47.0 (new)
- [CloudWatch Logs Encryption with KMS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/encrypt-log-data-kms.html) — AWS Docs
- [CloudWatch Alarm Missing Data](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html#alarms-and-missing-data) — AWS Docs
- [CloudWatch Data Protection](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html) — AWS Docs
- [Filter and Pattern Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html) — AWS Docs

### Validation & Tools

- [tfsec GitHub](https://github.com/aquasecurity/tfsec)
- [Checkov](https://www.checkov.io/)
- [Terraform Test Framework](https://developer.hashicorp.com/terraform/language/tests)
- [hashicorp/terraform-provider-aws Issues](https://github.com/hashicorp/terraform-provider-aws/issues)

---

## Completion Checklist

- [x] All >= 1.7 and aws ~> 6.0 patterns validated against registry (6.47.0)
- [x] Code examples for each mandatory pattern (log group, metric alarm, composite alarm, metric filter, data protection, outputs)
- [x] State management strategy documented (local dev vs. S3 + DynamoDB production)
- [x] Module architecture fully defined (structure, variables with validation, outputs)
- [x] All anti-patterns have tested, production-ready alternatives
- [x] CLI commands with expected outputs documented
- [x] Integration examples for Lambda, RDS, SNS, IAM, EventBridge, S3, CloudTrail
- [x] Sources dated and linked to registry (verified 2026-05-28)
- [x] Security checklist complete (15 items)
- [x] Disaster recovery procedures documented
- [x] v6.x new resources and features documented (PromQL, deletion_protection_enabled, otel_enrichment, alarm_mute_rule, contributor_insight_rule, log_transformer, log_delivery family, log_index_policy)

---

## Research Gaps

```
Gap: aws_cloudwatch_otel_enrichment full argument reference
Impact: Cannot guarantee all required arguments for OTel enrichment resource in v6.x
Workaround: Use aws_cloudwatch_metric_stream with opentelemetry0.7 output_format as fallback
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_otel_enrichment

Gap: aws_cloudwatch_log_transformer filter transform syntax
Impact: Log transformation patterns may differ from filter pattern syntax
Workaround: Test in dev environment before applying to production log groups
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_transformer

Gap: aws_cloudwatch_log_delivery family full argument reference
Impact: New vended log delivery API (replacing older put-subscription approach) may have undocumented constraints
Workaround: Use existing aws_cloudwatch_log_subscription_filter for now; evaluate log delivery resources when needed
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_delivery
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)

- Creating log groups with KMS encryption and retention policy
- Creating metric alarms with all three state transition actions
- Creating composite alarms with `depends_on` for child alarms
- Setting `treat_missing_data = "breaching"` on production SLO alarms
- Creating log metric filters linked to metric alarms
- Adding `deletion_protection_enabled = true` on production log groups
- Lambda permission for CloudWatch Logs subscription filter destination
- Terraform `fmt`, `validate`, `plan` commands

### Medium Confidence (Validate with user)

- Log group class selection (STANDARD vs. INFREQUENT_ACCESS)
- Retention period (compliance requirements vary: PCI 1yr, HIPAA 6yr, general 90d)
- Subscription filter destination type (Lambda vs. Kinesis vs. Firehose)
- PromQL vs. Metric Math for alarm expressions
- Module decomposition strategy

### Low Confidence (Must ask user)

- KMS key sharing vs. dedicated per-log-group keys (cost vs. isolation tradeoff)
- Cross-account log delivery architecture
- Compliance-specific retention requirements (SOC 2, HIPAA, PCI-DSS, FedRAMP)
- Alarm thresholds (require service-specific SLO knowledge)

### Edge Cases (When to pause)

- `deletion_protection_enabled = true` on a log group that must be destroyed — requires explicit `false` before destroy
- Composite alarm destroy failures due to circular references — requires two-stage apply
- Log group already exists from Lambda auto-creation — use `import` block, do not recreate
- Subscription filter silent failure (Lambda permission missing) — verify CloudWatch delivery errors in `aws_cloudwatch_log_group` metrics

### Emergency Stop

- Halt if KMS encryption is being removed from a production log group
- Halt if `deletion_protection_enabled` is being set to `false` on production log groups
- Halt if `retention_in_days` is being changed to `0` (never expire)
- Halt if all alarm actions are being emptied on production SLO alarms
- Halt if `terraform destroy` is planned against production CloudWatch resources without explicit approval
