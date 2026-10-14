# Terraform AWS X-Ray — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - X-Ray (Distributed Tracing)"
Cloud_Provider: "AWS"
Target_Service: "X-Ray (Encryption Config, Groups, Sampling Rules, Indexing Rules, Resource Policies, Trace Segment Destination)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-29)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-29"
Research_Date: "2026-05-29"
Domain_Complexity: "Standard"
New_V6_Resources_Noted: |
  aws_xray_indexing_rule (new - probabilistic trace ID sampling for indexing),
  aws_xray_resource_policy (new - cross-account/service resource policies),
  aws_xray_trace_segment_destination (new - route PutTraceSegments to XRay or CloudWatchLogs),
  identity-based import blocks (TF v1.12.0+) for all X-Ray resources,
  region argument on all resources for explicit regional management
```

---

## Executive Summary

AWS X-Ray is a distributed tracing service that collects segment data from instrumented applications, assembles traces across microservice boundaries, and generates service graphs to identify latency bottlenecks, error hotspots, and performance regressions. Each service emits segments with request/response metadata; downstream subsegments track calls to AWS services (Lambda, DynamoDB, SQS) and external APIs. The X-Ray daemon buffers and uploads segments in batches, decoupling instrumentation from transmission overhead. Trace data is retained for 30 days; service graph data for 30 days as well.

The Terraform AWS provider v6.x manages six X-Ray resource types: `aws_xray_encryption_config` (KMS-based at-rest encryption for trace data), `aws_xray_group` (named filter expression sets with Insights support), `aws_xray_sampling_rule` (priority-ordered rules controlling what percentage of requests are traced), `aws_xray_indexing_rule` (new in v6.x — probabilistic sampling of trace IDs for the trace index), `aws_xray_resource_policy` (new in v6.x — resource-based policies for cross-account and cross-service X-Ray access), and `aws_xray_trace_segment_destination` (new in v6.x — routes `PutTraceSegments` output to either the native X-Ray service or CloudWatch Logs). Provider constraint `~> 6.0` is recommended; Terraform `>= 1.7` is required. Three critical notes: removing `aws_xray_encryption_config`, `aws_xray_indexing_rule`, or `aws_xray_trace_segment_destination` from Terraform state has **no effect** on the actual AWS configuration — the resources continue operating. Destroy-time behaviour must be managed via explicit AWS API calls or re-application.

This service is classified **Standard** in domain complexity: it spans six resource types with inter-dependencies (encryption config depends on KMS key, groups emit CloudWatch metrics, sampling rules require IAM `xray:GetSamplingRules` for SDKs), security considerations (KMS CMK key policy, resource-based access policies, IAM role for daemon), and moderate tradeoff decisions (sampling rates, group filter expressions, trace destination routing). It does not carry the stateful management risk of databases or the breadth of CloudWatch, but the security surface around cross-account access and encryption key lifecycle makes it more than foundational.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Locks provider to `~> 6.0` to prevent silent schema drift when the provider ships `aws_xray_indexing_rule`, `aws_xray_resource_policy`, or `aws_xray_trace_segment_destination` in future v7.x with breaking argument renames. State backend isolation prevents X-Ray configuration from being accidentally destroyed by other workspaces.

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
    key            = "prod/xray/terraform.tfstate"
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

#### Pattern: Provider Configuration with IAM Role and Default Tags

**Why**: X-Ray Daemon and SDK assume IAM roles to call `PutTraceSegments`, `PutTelemetryRecords`, and `GetSamplingRules`. Terraform must also have `xray:*` permissions to manage groups, sampling rules, and encryption config. No credentials in code — rely on `assume_role` or environment credentials.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformXRayRole"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Service     = "xray"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}
```

**Minimum IAM permissions for Terraform role**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "xray:CreateGroup",
        "xray:DeleteGroup",
        "xray:GetGroup",
        "xray:UpdateGroup",
        "xray:CreateSamplingRule",
        "xray:DeleteSamplingRule",
        "xray:GetSamplingRules",
        "xray:UpdateSamplingRule",
        "xray:GetEncryptionConfig",
        "xray:PutEncryptionConfig",
        "xray:PutResourcePolicy",
        "xray:GetResourcePolicies",
        "xray:DeleteResourcePolicy",
        "xray:UpdateIndexingRule",
        "xray:ListIndexingRules",
        "xray:UpdateTraceSegmentDestination",
        "xray:GetTraceSegmentDestination",
        "kms:CreateGrant",
        "kms:DescribeKey"
      ],
      "Resource": "*"
    }
  ]
}
```

- **Source**: [AWS Provider Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#aws-configuration-reference) | [X-Ray IAM Actions](https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html)

---

#### Pattern: KMS Encryption for X-Ray Trace Data

**Why**: By default, X-Ray uses AWS-managed keys (`NONE` type) that cannot be scoped to specific IAM principals, cannot be rotated on a custom schedule, and cannot be audited per-service in CloudTrail KMS events. Customer-managed keys (`KMS` type) enable key policy scoping (only authorised roles can decrypt traces), automatic rotation, and key deletion with a configurable window. Trace data may contain PII, credentials in query strings, or sensitive request payloads.

```hcl
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "xray_kms_policy" {
  statement {
    sid    = "EnableIAMUserPermissions"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowXRayService"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["xray.amazonaws.com"]
    }

    actions = [
      "kms:GenerateDataKey*",
      "kms:Decrypt"
    ]
    resources = ["*"]
  }
}

resource "aws_kms_key" "xray" {
  description             = "KMS key for X-Ray trace data encryption - ${var.environment}"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.xray_kms_policy.json

  tags = {
    Name = "xray-encryption-${var.environment}"
  }
}

resource "aws_kms_alias" "xray" {
  name          = "alias/xray-${var.environment}"
  target_key_id = aws_kms_key.xray.key_id
}

resource "aws_xray_encryption_config" "main" {
  type   = "KMS"
  key_id = aws_kms_key.xray.arn
}
```

> **CRITICAL NOTE**: Removing `aws_xray_encryption_config` from Terraform state does **not** revert encryption to `NONE`. The encryption config persists in AWS. To change encryption, update `type` to `"NONE"` and apply, then optionally remove the resource.

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_xray_encryption_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_encryption_config) | [X-Ray Security](https://docs.aws.amazon.com/xray/latest/devguide/security-data-protection.html)

---

#### Pattern: Sampling Rule with Priority Ordering and Validation

**Why**: X-Ray SDKs evaluate sampling rules in ascending priority order (1 = highest). Without explicit rules, all traffic uses the default rule (reservoir=1/sec, rate=5%). High-volume services (Lambda, API Gateway) will generate disproportionate costs and noise. Production sampling rules must be declarative and version-controlled to prevent sampling policy drift from console edits.

```hcl
variable "service_name" {
  type        = string
  description = "Name of the service to create sampling rule for"

  validation {
    condition     = length(var.service_name) >= 1 && length(var.service_name) <= 32
    error_message = "Service name must be between 1 and 32 characters."
  }
}

variable "sampling_fixed_rate" {
  type        = number
  description = "Percentage of requests to trace after reservoir is exhausted (0.0 to 1.0)"
  default     = 0.05

  validation {
    condition     = var.sampling_fixed_rate >= 0 && var.sampling_fixed_rate <= 1
    error_message = "Fixed rate must be between 0.0 (0%) and 1.0 (100%)."
  }
}

# High-priority rule: trace all errors (HTTP 5xx)
resource "aws_xray_sampling_rule" "errors" {
  rule_name      = "${var.service_name}-errors"
  priority       = 100
  version        = 1
  reservoir_size = 5
  fixed_rate     = 1.0  # 100% of error traces
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = var.service_name
  resource_arn   = "*"

  attributes = {
    "http.status" = "5??"
  }

  tags = {
    Name        = "${var.service_name}-errors"
    Environment = var.environment
    Purpose     = "full-error-tracing"
  }
}

# Standard traffic rule
resource "aws_xray_sampling_rule" "standard" {
  rule_name      = "${var.service_name}-standard"
  priority       = 9000
  version        = 1
  reservoir_size = 10
  fixed_rate     = var.sampling_fixed_rate
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = var.service_name
  resource_arn   = "*"

  tags = {
    Name        = "${var.service_name}-standard"
    Environment = var.environment
    Purpose     = "standard-sampling"
  }
}

# Health check exclusion (priority lower = checked first)
resource "aws_xray_sampling_rule" "health_checks" {
  rule_name      = "${var.service_name}-health-exclude"
  priority       = 50
  version        = 1
  reservoir_size = 0
  fixed_rate     = 0  # Never sample health checks
  url_path       = "/health"
  host           = "*"
  http_method    = "GET"
  service_type   = "*"
  service_name   = var.service_name
  resource_arn   = "*"

  tags = {
    Name    = "${var.service_name}-health-exclude"
    Purpose = "exclude-health-checks"
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_xray_sampling_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_sampling_rule) | [Configuring Sampling Rules](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html)

---

#### Pattern: X-Ray Group with CloudWatch Insights

**Why**: Groups define named subsets of traces based on filter expressions. Once created, X-Ray publishes CloudWatch metrics per group every minute (trace count, error/fault/throttle rates, response time). Enabling Insights allows X-Ray to automatically detect anomalies and surface root-cause recommendations — critical for production observability.

```hcl
resource "aws_xray_group" "errors" {
  group_name        = "${var.environment}-errors"
  filter_expression = "fault = true OR error = true"

  insights_configuration {
    insights_enabled      = true
    notifications_enabled = true
  }

  tags = {
    Name        = "${var.environment}-errors"
    Environment = var.environment
    Purpose     = "error-trace-group"
  }
}

resource "aws_xray_group" "slow_requests" {
  group_name        = "${var.environment}-slow"
  filter_expression = "responsetime > 2"

  insights_configuration {
    insights_enabled      = true
    notifications_enabled = true
  }

  tags = {
    Name        = "${var.environment}-slow"
    Environment = var.environment
    Purpose     = "latency-trace-group"
  }
}

resource "aws_xray_group" "service_specific" {
  group_name        = "${var.environment}-${var.service_name}"
  filter_expression = "service(\"${var.service_name}\") AND responsetime > 1"

  insights_configuration {
    insights_enabled      = var.enable_xray_insights
    notifications_enabled = var.enable_xray_insights
  }

  tags = {
    Name        = "${var.environment}-${var.service_name}"
    Environment = var.environment
    Service     = var.service_name
  }
}
```

> **Note**: Updating a group's `filter_expression` does not re-process already-stored traces. The update applies only to subsequent incoming traces. To avoid merged service graph data, delete and recreate the group.

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_xray_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_group) | [Configuring Groups](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-groups.html)

---

#### Pattern: Trace Segment Destination (v6.x New Resource)

**Why**: `aws_xray_trace_segment_destination` controls where segments submitted via `PutTraceSegments` are stored. Default is `XRay` (native X-Ray storage, 30-day retention). Routing to `CloudWatchLogs` enables long-term retention, CloudWatch Logs Insights queries, and unified log/trace correlation. This is a singleton account-level resource — removing it from Terraform state does **not** change the destination in AWS.

```hcl
variable "xray_trace_destination" {
  type        = string
  description = "Destination for X-Ray trace segments"
  default     = "XRay"

  validation {
    condition     = contains(["XRay", "CloudWatchLogs"], var.xray_trace_destination)
    error_message = "Destination must be 'XRay' or 'CloudWatchLogs'."
  }
}

resource "aws_xray_trace_segment_destination" "main" {
  destination = var.xray_trace_destination
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_xray_trace_segment_destination](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_trace_segment_destination)

---

#### Pattern: Variable Validation and Type Safety

**Why**: Prevents invalid configurations at `terraform plan` time — before any AWS API calls. Priority conflicts between sampling rules, invalid filter expressions, and out-of-range fixed rates are caught early.

```hcl
variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "xray_reservoir_size" {
  type        = number
  description = "Fixed number of requests to trace per second before applying fixed_rate"
  default     = 5

  validation {
    condition     = var.xray_reservoir_size >= 0 && var.xray_reservoir_size <= 10000
    error_message = "Reservoir size must be between 0 and 10000."
  }
}

variable "enable_xray_insights" {
  type        = bool
  description = "Whether to enable X-Ray Insights anomaly detection for groups"
  default     = true
}

variable "aws_region" {
  type        = string
  description = "AWS region for X-Ray resources"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "Region must match pattern like 'us-east-1', 'eu-west-2'."
  }
}
```

- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

### ⚠️ Conditional Patterns

---

#### Decision: XRay vs. CloudWatchLogs Trace Segment Destination

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **XRay** | Native service map, trace analytics, Insights | 30-day retention cap, no cross-service log correlation | Standard distributed tracing, short-term debugging |
| **CloudWatchLogs** | Long-term retention, CWL Insights queries, log+trace correlation | Additional CloudWatch costs, no native X-Ray service map from CWL | Compliance requiring >30d retention, unified observability |

- **Agent**: "Ask user: Do you require trace retention beyond 30 days? Do you need to correlate traces with application logs in CloudWatch Logs Insights?"
- **Source**: [aws_xray_trace_segment_destination](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_trace_segment_destination)

---

#### Decision: KMS CMK vs. AWS-Managed Key for Trace Encryption

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **NONE (AWS-managed)** | Zero config, no KMS costs, immediate setup | No IAM scoping, no custom rotation, no per-service CloudTrail | Dev/test, non-sensitive traces, quick start |
| **KMS CMK** | Full IAM control, custom rotation, cross-account key sharing, audit in CloudTrail | KMS API costs, key policy management complexity, key deletion risk | Production, compliance (HIPAA/PCI/SOC2), sensitive trace data |

```hcl
# Conditional encryption: KMS for prod, NONE for dev
resource "aws_xray_encryption_config" "main" {
  type   = var.environment == "prod" ? "KMS" : "NONE"
  key_id = var.environment == "prod" ? aws_kms_key.xray[0].arn : null
}

resource "aws_kms_key" "xray" {
  count                   = var.environment == "prod" ? 1 : 0
  description             = "KMS key for X-Ray - ${var.environment}"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.xray_kms_policy.json
}
```

- **Agent**: "Ask user: Is this a production environment with compliance requirements (HIPAA, PCI-DSS, SOC2)? Do trace payloads potentially contain PII or sensitive request data?"
- **Source**: [aws_xray_encryption_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_encryption_config) | [X-Ray Data Protection](https://docs.aws.amazon.com/xray/latest/devguide/security-data-protection.html)

---

#### Decision: Sampling Rate Strategy

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Conservative (5%, reservoir=1)** | Low cost, minimal overhead | Misses infrequent errors, poor root-cause visibility | High-traffic APIs (>1000 req/s), cost-sensitive environments |
| **Aggressive (50%+, reservoir=10)** | High error visibility, accurate latency P99 | Higher cost, SDK overhead | Low-traffic critical services, debugging sessions |
| **Rule-based (100% errors, 5% success)** | Full error visibility + cost control | Rule management complexity, priority ordering risk | Production best practice — separate error and success rules |
| **Service-specific rules** | Granular per-service control | Many rules, rule limit (25 custom rules per account) | Microservices with heterogeneous traffic patterns |

- **When**: Rule-based (100% errors + 5% success) is the recommended production pattern. Conservative for batch/background services. Service-specific when SLA differs across services.
- **Agent**: "Ask user: What is the expected request rate? Are there specific services requiring 100% trace coverage for compliance?"
- **Source**: [Configuring Sampling Rules](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html)

---

#### Decision: X-Ray Resource Policy for Cross-Account Access

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **No resource policy** | Simplicity, single-account | No cross-account trace sharing | Single-account deployments |
| **Cross-account resource policy** | Centralised observability account, trace aggregation | Policy management, `bypass_policy_lockout_check` risk | Multi-account organisations, shared observability platform |

```hcl
data "aws_iam_policy_document" "xray_cross_account" {
  statement {
    sid    = "AllowCrossAccountXRayAccess"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = var.trusted_account_arns
    }

    actions = [
      "xray:GetGroups",
      "xray:GetGroup",
      "xray:GetSamplingRules",
      "xray:GetSamplingTargets",
      "xray:GetSamplingStatisticSummaries",
      "xray:GetTraceGraph",
      "xray:GetTraceSummaries",
      "xray:BatchGetTraces"
    ]

    resources = ["*"]
  }
}

resource "aws_xray_resource_policy" "cross_account" {
  policy_name                 = "cross-account-observability"
  policy_document             = data.aws_iam_policy_document.xray_cross_account.json
  bypass_policy_lockout_check = false  # Never set true in production
}
```

- **Agent**: "Ask user: Does your architecture use a central observability account? Do other AWS accounts need to read traces from this account?"
- **Source**: [aws_xray_resource_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_resource_policy)

---

#### Decision: Indexing Rule Sampling Percentage

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Low (0.1–1%)** | Minimal storage costs for trace index | Reduced searchability of historical traces | Very high-volume services, cost-optimised |
| **Medium (5–10%)** | Balance of searchability and cost | Moderate ongoing index cost | Standard production services |
| **High (50–100%)** | Full historical trace search | Higher storage costs | Low-traffic critical services, compliance audit trails |

```hcl
resource "aws_xray_indexing_rule" "main" {
  name = "Default"  # Must be "Default" — only one indexing rule per account

  rule {
    probabilistic {
      desired_sampling_percentage = var.indexing_sampling_percentage
    }
  }
}
```

> **Note**: Removing `aws_xray_indexing_rule` from Terraform state does **not** change the indexing rule in AWS — it continues operating at its last configured value.

- **Agent**: "Ask user: What percentage of traces need to be searchable in the trace index? What is the expected monthly trace volume?"
- **Source**: [aws_xray_indexing_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_indexing_rule)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Default (No) Encryption for Production Trace Data

```hcl
# DON'T - Uses AWS-managed key, no IAM scoping
resource "aws_xray_encryption_config" "bad" {
  type = "NONE"
}
```

**Why**: AWS-managed keys cannot be scoped to specific IAM principals, cannot have custom key policies, cannot be disabled or scheduled for deletion independently, and do not generate per-key CloudTrail events for compliance audits. Traces may contain sensitive request payloads, query parameters with tokens/credentials, or PII.

```hcl
# DO - Always use KMS CMK for production
resource "aws_xray_encryption_config" "good" {
  type   = "KMS"
  key_id = aws_kms_key.xray.arn

  depends_on = [aws_kms_key.xray]
}
```

- **Impact**: `HIGH` — Sensitive trace data accessible to any IAM principal with `xray:BatchGetTraces`
- **Severity**: HIGH
- **Source**: [X-Ray Data Protection](https://docs.aws.amazon.com/xray/latest/devguide/security-data-protection.html)

---

#### Anti-Pattern: Hardcoded Credentials in Provider

```hcl
# DON'T
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  region     = "us-east-1"
}
```

**Why**: Credentials in code are exposed in version control history, build logs, and team access logs. An X-Ray management role with `xray:PutEncryptionConfig` and `xray:PutResourcePolicy` can reconfigure the entire tracing infrastructure.

```hcl
# DO - Use IAM role assumption or environment variables
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformXRayRole"
  }
}
# Credentials come from AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY env vars,
# EC2 instance profile, ECS task role, or Lambda execution role — never hardcoded.
```

- **Impact**: `CRITICAL` — Full AWS account compromise
- **Severity**: CRITICAL
- **Source**: [AWS Security Best Practices](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)

---

#### Anti-Pattern: Resource Policy with Wildcard Principal

```hcl
# DON'T - Grants any AWS account read access to all traces
resource "aws_xray_resource_policy" "bad" {
  policy_name   = "open-access"
  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = "*" }     # DON'T - Wildcard principal
      Action    = ["xray:*"]        # DON'T - Wildcard actions
      Resource  = "*"
    }]
  })
  bypass_policy_lockout_check = true  # DON'T - Bypasses safety check
}
```

**Why**: A wildcard principal (`"*"`) exposes all trace data — including request payloads, response bodies, annotations, and metadata — to any authenticated AWS principal. `bypass_policy_lockout_check = true` removes the safety net preventing you from locking yourself out of policy management.

```hcl
# DO - Scope to specific account ARNs and least-privilege actions
resource "aws_xray_resource_policy" "good" {
  policy_name                 = "cross-account-readonly"
  policy_document             = data.aws_iam_policy_document.xray_cross_account.json
  bypass_policy_lockout_check = false
}
```

- **Impact**: `CRITICAL` — All trace data (including sensitive payloads) exposed to any AWS account
- **Severity**: CRITICAL
- **Source**: [aws_xray_resource_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_resource_policy) | [IAM Policy Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

---

#### Anti-Pattern: Missing Tags on X-Ray Resources

```hcl
# DON'T - Groups and sampling rules without tags
resource "aws_xray_group" "bad" {
  group_name        = "prod-errors"
  filter_expression = "fault = true"
  # No tags
}

resource "aws_xray_sampling_rule" "bad" {
  rule_name      = "prod-standard"
  priority       = 9000
  version        = 1
  reservoir_size = 5
  fixed_rate     = 0.05
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"
  # No tags
}
```

**Why**: Untagged X-Ray groups and sampling rules cannot be attributed to services/teams for cost allocation, cannot be targeted by tag-based IAM policies, and cannot be discovered by automated compliance scanners.

```hcl
# DO - All X-Ray resources must carry standard tags
resource "aws_xray_group" "good" {
  group_name        = "${var.environment}-errors"
  filter_expression = "fault = true"

  tags = {
    Name        = "${var.environment}-errors"
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
    Service     = var.service_name
  }
}
```

- **Impact**: `HIGH` — Cost blindness, compliance gaps, unattributed resource sprawl
- **Severity**: HIGH
- **Source**: [Resource Tagging Strategy](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)

---

#### Anti-Pattern: Sampling Rule Priority Conflicts

```hcl
# DON'T - Multiple rules with same priority (evaluation order is undefined)
resource "aws_xray_sampling_rule" "rule_a" {
  rule_name = "service-a"
  priority  = 1000
  # ...
}

resource "aws_xray_sampling_rule" "rule_b" {
  rule_name = "service-b"
  priority  = 1000  # DON'T - Duplicate priority
  # ...
}
```

**Why**: When two sampling rules share the same priority, the evaluation order is non-deterministic. This can result in some services being over-sampled (higher cost) or under-sampled (missed errors) depending on which rule is evaluated first.

```hcl
# DO - Assign unique, spaced priorities
locals {
  sampling_priorities = {
    health_exclude = 50
    error_trace    = 100
    api_gateway    = 500
    lambda         = 600
    standard       = 9000
  }
}

resource "aws_xray_sampling_rule" "error_trace" {
  rule_name = "error-trace"
  priority  = local.sampling_priorities.error_trace
  # ...
}
```

- **Impact**: `MEDIUM` — Non-deterministic trace coverage, unexpected cost spikes or visibility gaps
- **Severity**: MEDIUM
- **Source**: [X-Ray Sampling Rule Priority](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html#xray-console-sampling-precedence)

---

#### Anti-Pattern: Using `count` for Sampling Rules (Map-Style Resources)

```hcl
# DON'T - count causes state index issues when rules are inserted/removed
variable "services" {
  default = ["service-a", "service-b", "service-c"]
}

resource "aws_xray_sampling_rule" "services" {
  count     = length(var.services)
  rule_name = "${var.services[count.index]}-rule"
  priority  = 1000 + count.index
  # ...
}
```

**Why**: Using `count` with a list means inserting a service at index 0 shifts all subsequent rules, causing Terraform to destroy and recreate them. Sampling rules being destroyed during a deploy means traces are dropped during that window.

```hcl
# DO - Use for_each with a map keyed by stable identifiers
variable "service_sampling_rules" {
  type = map(object({
    priority       = number
    reservoir_size = number
    fixed_rate     = number
  }))
  default = {
    "service-a" = { priority = 1000, reservoir_size = 5,  fixed_rate = 0.05 }
    "service-b" = { priority = 1100, reservoir_size = 10, fixed_rate = 0.10 }
    "service-c" = { priority = 1200, reservoir_size = 3,  fixed_rate = 0.02 }
  }
}

resource "aws_xray_sampling_rule" "services" {
  for_each = var.service_sampling_rules

  rule_name      = "${each.key}-rule"
  priority       = each.value.priority
  version        = 1
  reservoir_size = each.value.reservoir_size
  fixed_rate     = each.value.fixed_rate
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = each.key
  resource_arn   = "*"

  tags = {
    Name    = "${each.key}-rule"
    Service = each.key
  }
}
```

- **Impact**: `MEDIUM` — Trace drops during deploy, unexpected resource recreation
- **Severity**: MEDIUM
- **Source**: [for_each Meta-Argument](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)

---

## State Management Deep Dive

### Local Development State

```hcl
# Use local state only for development/learning
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

- **Risk**: Single point of failure, no team sharing, no locking, no encryption
- **When**: Solo development, temporary environments, learning

### Production Remote State (S3 + DynamoDB)

```hcl
# Bootstrap: create locking table (run once in separate bootstrap state)
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

# X-Ray module backend config
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/xray/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### State File Sensitivity

X-Ray state files contain KMS key ARNs, sampling rule configurations, and group filter expressions — not application secrets, but infrastructure topology that should be restricted.

```hcl
# Mark sensitive outputs
output "xray_encryption_key_arn" {
  value       = aws_kms_key.xray.arn
  description = "ARN of the KMS key used for X-Ray encryption"
  sensitive   = true
}

output "xray_group_arns" {
  value = {
    for k, v in aws_xray_group.groups : k => v.arn
  }
  description = "ARNs of X-Ray groups by name"
}
```

### State Backup and Recovery

```bash
# Backup current state
aws s3 cp \
  s3://my-org-terraform-state/prod/xray/terraform.tfstate \
  terraform.tfstate.backup

# Recover from backup
terraform state push terraform.tfstate.backup

# Import existing encryption config if state is lost
terraform import aws_xray_encryption_config.main us-east-1

# Import existing group by ARN
terraform import aws_xray_group.errors \
  arn:aws:xray:us-east-1:123456789012:group/prod-errors/ABCDEFGHIJKLMNOP

# Import sampling rule by name
terraform import aws_xray_sampling_rule.standard prod-standard

# Import indexing rule by name
terraform import aws_xray_indexing_rule.main Default

# Import trace segment destination by region
terraform import aws_xray_trace_segment_destination.main us-east-1
```

---

## Module Architecture

### Standard Module Structure

```
modules/
└── xray/
    ├── main.tf          # Resources: encryption_config, groups, sampling_rules, indexing_rule
    ├── variables.tf     # Input variables with validation
    ├── outputs.tf       # Group ARNs, sampling rule ARNs, encryption config type
    ├── versions.tf      # required_version and required_providers
    └── README.md        # Usage, inputs, outputs
```

### Module Definition

```hcl
# modules/xray/variables.tf
variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "enable_kms_encryption" {
  type        = bool
  description = "Whether to use KMS CMK for trace encryption (required for prod)"
  default     = false
}

variable "kms_key_arn" {
  type        = string
  description = "ARN of KMS key for X-Ray encryption (required when enable_kms_encryption = true)"
  default     = null

  validation {
    condition     = var.enable_kms_encryption ? var.kms_key_arn != null : true
    error_message = "kms_key_arn must be provided when enable_kms_encryption is true."
  }
}

variable "groups" {
  type = map(object({
    filter_expression     = string
    insights_enabled      = bool
    notifications_enabled = bool
  }))
  description = "Map of X-Ray group name to configuration"
  default     = {}
}

variable "sampling_rules" {
  type = map(object({
    priority       = number
    reservoir_size = number
    fixed_rate     = number
    service_name   = string
    url_path       = optional(string, "*")
    http_method    = optional(string, "*")
  }))
  description = "Map of sampling rule name to configuration"
  default     = {}
}

variable "trace_destination" {
  type        = string
  description = "Trace segment destination: XRay or CloudWatchLogs"
  default     = "XRay"

  validation {
    condition     = contains(["XRay", "CloudWatchLogs"], var.trace_destination)
    error_message = "trace_destination must be XRay or CloudWatchLogs."
  }
}

variable "indexing_sampling_percentage" {
  type        = number
  description = "Percentage of trace IDs to index (0.0 to 100.0)"
  default     = 5.0

  validation {
    condition     = var.indexing_sampling_percentage >= 0 && var.indexing_sampling_percentage <= 100
    error_message = "Indexing sampling percentage must be between 0 and 100."
  }
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to all X-Ray resources"
  default     = {}
}

# modules/xray/outputs.tf
output "group_arns" {
  value = {
    for k, v in aws_xray_group.groups : k => v.arn
  }
  description = "ARNs of created X-Ray groups keyed by group name"
}

output "sampling_rule_arns" {
  value = {
    for k, v in aws_xray_sampling_rule.rules : k => v.arn
  }
  description = "ARNs of created sampling rules keyed by rule name"
}

output "encryption_config_type" {
  value       = aws_xray_encryption_config.main.type
  description = "Type of X-Ray encryption config: KMS or NONE"
}

output "trace_destination" {
  value       = aws_xray_trace_segment_destination.main.destination
  description = "Active trace segment destination"
}
```

### Root Module Consuming X-Ray Module

```hcl
# root/main.tf
module "xray" {
  source = "./modules/xray"

  environment           = var.environment
  enable_kms_encryption = var.environment == "prod"
  kms_key_arn           = var.environment == "prod" ? aws_kms_key.xray.arn : null
  trace_destination     = "XRay"

  indexing_sampling_percentage = var.environment == "prod" ? 10.0 : 2.0

  groups = {
    errors = {
      filter_expression     = "fault = true OR error = true"
      insights_enabled      = true
      notifications_enabled = true
    }
    slow = {
      filter_expression     = "responsetime > 2"
      insights_enabled      = true
      notifications_enabled = false
    }
  }

  sampling_rules = {
    health-exclude = {
      priority       = 50
      reservoir_size = 0
      fixed_rate     = 0
      service_name   = "*"
      url_path       = "/health"
      http_method    = "GET"
    }
    errors = {
      priority       = 100
      reservoir_size = 5
      fixed_rate     = 1.0
      service_name   = var.service_name
    }
    standard = {
      priority       = 9000
      reservoir_size = 10
      fixed_rate     = 0.05
      service_name   = var.service_name
    }
  }

  tags = {
    Project = var.project_name
    Owner   = var.owner
  }
}
```

---

## Integration Patterns

### Integration: Terraform ↔ IAM

X-Ray Daemon and SDK require IAM permissions to send and retrieve traces. Terraform manages the IAM role and policy.

```hcl
data "aws_iam_policy_document" "xray_daemon" {
  statement {
    sid    = "XRayDaemonWriteAccess"
    effect = "Allow"

    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
      "xray:GetSamplingRules",
      "xray:GetSamplingTargets",
      "xray:GetSamplingStatisticSummaries"
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "xray_daemon" {
  name        = "XRayDaemonWriteAccess-${var.environment}"
  description = "Allows X-Ray daemon to write trace segments and read sampling rules"
  policy      = data.aws_iam_policy_document.xray_daemon.json

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Attach to Lambda execution role
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.xray_daemon.arn
}

# Or use AWS-managed policy for daemon write access
resource "aws_iam_role_policy_attachment" "lambda_xray_managed" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}
```

- **Versions**: `aws_iam_policy` min v5.0, `aws_iam_role_policy_attachment` min v5.0
- **Issues**: IAM changes are eventually consistent — add `depends_on` between role and Lambda function if Lambda creation fails with permission errors
- **Source**: [X-Ray IAM Examples](https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html)

---

### Integration: Terraform ↔ Lambda

Lambda has built-in X-Ray tracing support. Set `tracing_config` to `Active` to trace all invocations or `PassThrough` to honour the calling service's sampling decision.

```hcl
resource "aws_lambda_function" "api" {
  function_name = "${var.service_name}-${var.environment}"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "index.handler"
  runtime       = "nodejs20.x"
  filename      = data.archive_file.lambda.output_path

  tracing_config {
    mode = "Active"  # Always trace; or "PassThrough" to inherit sampling decision
  }

  environment {
    variables = {
      AWS_XRAY_TRACING_NAME = var.service_name  # Set service name in traces
    }
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_xray]
}
```

- **Versions**:

| Resource | Min | Notes |
|----------|-----|-------|
| `aws_lambda_function` | aws ~> 6.0 | `tracing_config` block stable since v2.x |
| `aws_xray_sampling_rule` | aws ~> 6.0 | Lambda uses account-level sampling rules |

- **Issues**: Lambda `Active` mode always creates a trace segment regardless of sampling; `PassThrough` respects the upstream header sampling decision. Lambda service map nodes appear even when Lambda itself doesn't send full trace data.
- **Source**: [Lambda X-Ray Integration](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html)

---

### Integration: Terraform ↔ API Gateway

API Gateway REST API and HTTP API support X-Ray tracing natively.

```hcl
# REST API
resource "aws_api_gateway_stage" "prod" {
  stage_name    = "prod"
  rest_api_id   = aws_api_gateway_rest_api.main.id
  deployment_id = aws_api_gateway_deployment.main.id

  xray_tracing_enabled = true

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# HTTP API (API Gateway V2)
resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "prod"
  auto_deploy = false

  default_route_settings {
    detailed_metrics_enabled = true
    logging_level            = "INFO"
    data_trace_enabled       = true
    throttling_burst_limit   = 5000
    throttling_rate_limit    = 10000
  }

  # Note: HTTP API V2 traces via Lambda integration — tracing enabled at Lambda level
  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

- **Issues**: API Gateway sampling is controlled by X-Ray sampling rules. REST API starts a new trace; Lambda continuation requires `tracing_config.mode = "Active"` or `"PassThrough"`.
- **Source**: [API Gateway X-Ray Tracing](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-xray.html)

---

### Integration: Terraform ↔ CloudWatch

X-Ray Groups automatically publish CloudWatch metrics. Create alarms on those metrics for production monitoring.

```hcl
# X-Ray Group CloudWatch metrics namespace: AWS/XRay
resource "aws_cloudwatch_metric_alarm" "xray_error_rate" {
  alarm_name          = "${var.environment}-xray-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorRate"
  namespace           = "AWS/XRay"
  period              = 300
  statistic           = "Average"
  threshold           = 5
  alarm_description   = "X-Ray error rate exceeds 5% for ${var.environment}"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    GroupName = aws_xray_group.errors.group_name
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_cloudwatch_metric_alarm" "xray_fault_rate" {
  alarm_name          = "${var.environment}-xray-fault-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FaultRate"
  namespace           = "AWS/XRay"
  period              = 300
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "X-Ray fault rate (5xx) exceeds 1% for ${var.environment}"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    GroupName = aws_xray_group.errors.group_name
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

- **Issues**: CloudWatch metrics from X-Ray groups are published at 1-minute intervals with up to a 1-minute delay. `ErrorRate` = 4xx errors; `FaultRate` = 5xx faults; `ThrottleRate` = 429 throttles.
- **Source**: [X-Ray CloudWatch Metrics](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html#xray-concepts-groups)

---

### Integration: Terraform ↔ KMS

```hcl
# KMS key with X-Ray service principal allowed to generate/decrypt data keys
data "aws_iam_policy_document" "xray_kms" {
  statement {
    sid    = "EnableIAMPermissions"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowXRayServiceEncryption"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["xray.amazonaws.com"]
    }

    actions = [
      "kms:GenerateDataKey",
      "kms:GenerateDataKeyWithoutPlaintext",
      "kms:Decrypt"
    ]

    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_kms_key" "xray" {
  description             = "X-Ray trace data encryption - ${var.environment}"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.xray_kms.json

  tags = {
    Name        = "xray-${var.environment}"
    Environment = var.environment
    Service     = "xray"
    ManagedBy   = "terraform"
  }
}

resource "aws_xray_encryption_config" "main" {
  type   = "KMS"
  key_id = aws_kms_key.xray.arn

  depends_on = [aws_kms_key.xray]
}
```

- **Issues**: KMS key deletion is asynchronous (7–30 day window). If the key is scheduled for deletion, X-Ray cannot encrypt new traces and `PutTraceSegments` calls will fail. Always set `deletion_window_in_days = 30` and `enable_key_rotation = true`.
- **Source**: [KMS Key Policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)

---

### Integration: Terraform ↔ ECS

ECS tasks with Fargate or EC2 launch type require the X-Ray daemon as a sidecar container to receive UDP trace data from SDKs.

```hcl
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.service_name}-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = var.service_name
      image     = "${aws_ecr_repository.app.repository_url}:latest"
      essential = true

      environment = [
        {
          name  = "AWS_XRAY_DAEMON_ADDRESS"
          value = "127.0.0.1:2000"
        }
      ]
    },
    {
      name      = "xray-daemon"
      image     = "amazon/aws-xray-daemon:latest"
      essential = false

      portMappings = [
        {
          containerPort = 2000
          protocol      = "udp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/xray-daemon/${var.environment}"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "xray"
        }
      }
    }
  ])

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
    Service     = var.service_name
  }
}
```

- **Issues**: The X-Ray daemon container must have `AWSXRayDaemonWriteAccess` attached to the ECS task role. The daemon listens on UDP 2000 — ensure security group allows intra-task UDP traffic if using bridge networking mode.
- **Source**: [X-Ray Daemon on ECS](https://docs.aws.amazon.com/xray/latest/devguide/xray-daemon-ecs.html)

---

## Quality Control

### Verification Commands

```bash
# Initialize and upgrade providers
terraform init -upgrade
# Expected: ✓ Terraform initialized, provider hashicorp/aws 6.47.0 installed

# Format check
terraform fmt -recursive -check=true
# Expected: exit code 0 (no formatting issues)

# Syntax validation
terraform validate
# Expected: "Success! The configuration is valid."

# Security scanning
tfsec . --format json 2>/dev/null | jq '[.results[] | select(.severity == "CRITICAL" or .severity == "HIGH")]'
# Expected: [] (empty array - no CRITICAL or HIGH findings)

# Policy-as-code
checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks

# Plan with explicit lock
terraform plan -out=tfplan -lock=true
# Expected: Plan shows only intended additions/changes

# Review plan output
terraform show tfplan | grep -E "(will be|must be|# aws_xray)"
# Expected: Explicit list of resources to create/modify

# Apply with plan file
terraform apply tfplan
# Expected: All resources created without errors

# Verify state
terraform state list | grep xray
# Expected:
#   aws_xray_encryption_config.main
#   aws_xray_group.errors
#   aws_xray_group.slow_requests
#   aws_xray_sampling_rule.errors
#   aws_xray_sampling_rule.health_checks
#   aws_xray_sampling_rule.standard
#   aws_xray_indexing_rule.main
#   aws_xray_trace_segment_destination.main

# Verify encryption config
terraform state show aws_xray_encryption_config.main
# Expected: type = "KMS", key_id = "arn:aws:kms:..."

# Check outputs
terraform output
# Expected: group_arns, sampling_rule_arns, encryption_config_type, trace_destination
```

### Testing with Terratest

```go
package test

import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/stretchr/testify/assert"
)

func TestXRayDeployment(t *testing.T) {
  opts := &terraform.Options{
    TerraformDir: "../examples/xray",
    Vars: map[string]interface{}{
      "environment":           "test",
      "enable_kms_encryption": false,
      "trace_destination":     "XRay",
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  // Verify encryption config
  encType := terraform.Output(t, opts, "encryption_config_type")
  assert.Equal(t, "NONE", encType)

  // Verify trace destination
  dest := terraform.Output(t, opts, "trace_destination")
  assert.Equal(t, "XRay", dest)

  // Verify group ARNs are populated
  groupARNs := terraform.OutputMap(t, opts, "group_arns")
  assert.Contains(t, groupARNs["errors"], "arn:aws:xray:")
}
```

---

## Production Readiness

### Performance

- **Sampling overhead**: X-Ray SDK adds <1ms latency per request for segment creation. Sampling rule evaluation is local (cached from `GetSamplingTargets` polling every 10 seconds).
- **Daemon UDP queue**: X-Ray daemon buffers segments in memory (default 32 MB). High-volume services should monitor daemon memory and tune `--buffer-memory` flag.
- **Trace data retention**: 30 days — plan S3 export if longer retention is required.
- **Service graph**: Generated from trace data, retained 30 days. Groups with Insights enabled publish CloudWatch metrics every 60 seconds.

### Scalability

- **Sampling rules**: Account limit is 25 custom rules + 1 default rule (26 total). Use service-specific attributes (`service_name`, `url_path`) to multiplex within a single rule.
- **Groups**: No documented hard limit, but each group emits CloudWatch metrics — be mindful of CloudWatch PutMetricData API limits.
- **Trace throughput**: X-Ray service is designed for millions of traces per second account-wide. The daemon is the typical bottleneck — scale daemon horizontally on high-traffic EC2/ECS deployments.
- **KMS API calls**: X-Ray calls KMS `GenerateDataKey` for each trace segment batch. High-volume services may hit KMS request quotas (default 10,000 requests/second/region for symmetric CMKs).

### Security Checklist

- [ ] `aws_xray_encryption_config` set to `KMS` with customer-managed key in production
- [ ] KMS key has `enable_key_rotation = true`
- [ ] KMS key policy scopes `GenerateDataKey`/`Decrypt` to `xray.amazonaws.com` with source account condition
- [ ] Terraform role uses `assume_role` — no hardcoded credentials
- [ ] `aws_xray_resource_policy` scoped to specific account ARNs (no wildcard principal)
- [ ] `bypass_policy_lockout_check = false` on all resource policies
- [ ] All X-Ray resources tagged with Environment, Owner, ManagedBy
- [ ] Sampling rules use `for_each`, not `count`, to prevent accidental rule recreation
- [ ] State file in S3 with `encrypt = true` and DynamoDB locking
- [ ] State file access restricted to service accounts via S3 bucket policy

### Disaster Recovery Runbook

```bash
# 1. State corruption recovery
aws s3api get-object \
  --bucket my-org-terraform-state \
  --key prod/xray/terraform.tfstate \
  --version-id <last-good-version-id> \
  terraform.tfstate.backup

terraform state push terraform.tfstate.backup

# 2. Re-import singleton resources (encryption config, indexing rule, trace destination)
terraform import aws_xray_encryption_config.main us-east-1
terraform import aws_xray_indexing_rule.main Default
terraform import aws_xray_trace_segment_destination.main us-east-1

# 3. Re-import groups by ARN
aws xray get-groups --query 'Groups[*].GroupARN' --output text
terraform import aws_xray_group.errors arn:aws:xray:us-east-1:123456789012:group/prod-errors/XXXX

# 4. Re-import sampling rules by name
aws xray get-sampling-rules --query 'SamplingRuleRecords[*].SamplingRule.RuleName' --output text
terraform import aws_xray_sampling_rule.standard prod-standard

# 5. Verify current state matches infrastructure
terraform plan
# Expected: "No changes. Your infrastructure matches the configuration."
```

---

## Reference Implementations

Copy-paste root module example with `.tfvars`:

```hcl
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
    key            = "prod/xray/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/TerraformRole"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Project     = var.project
    }
  }
}

data "aws_caller_identity" "current" {}

# KMS key for trace encryption (prod only)
resource "aws_kms_key" "xray" {
  count                   = var.enable_kms_encryption ? 1 : 0
  description             = "X-Ray trace encryption - ${var.environment}"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "Enable IAM"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "Allow X-Ray"
        Effect    = "Allow"
        Principal = { Service = "xray.amazonaws.com" }
        Action    = ["kms:GenerateDataKey", "kms:Decrypt"]
        Resource  = "*"
        Condition = {
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        }
      }
    ]
  })

  tags = { Name = "xray-${var.environment}" }
}

resource "aws_xray_encryption_config" "main" {
  type   = var.enable_kms_encryption ? "KMS" : "NONE"
  key_id = var.enable_kms_encryption ? aws_kms_key.xray[0].arn : null
}

resource "aws_xray_group" "errors" {
  group_name        = "${var.environment}-errors"
  filter_expression = "fault = true OR error = true"

  insights_configuration {
    insights_enabled      = true
    notifications_enabled = true
  }
}

resource "aws_xray_sampling_rule" "health_exclude" {
  rule_name      = "${var.environment}-health-exclude"
  priority       = 50
  version        = 1
  reservoir_size = 0
  fixed_rate     = 0
  url_path       = "/health"
  host           = "*"
  http_method    = "GET"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"
}

resource "aws_xray_sampling_rule" "standard" {
  rule_name      = "${var.environment}-standard"
  priority       = 9000
  version        = 1
  reservoir_size = 10
  fixed_rate     = var.sampling_fixed_rate
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"
}

resource "aws_xray_indexing_rule" "main" {
  name = "Default"
  rule {
    probabilistic {
      desired_sampling_percentage = var.indexing_percentage
    }
  }
}

resource "aws_xray_trace_segment_destination" "main" {
  destination = var.trace_destination
}
```

```hcl
# variables.tf
variable "aws_region"            { type = string }
variable "account_id"            { type = string }
variable "environment"           { type = string }
variable "project"               { type = string }
variable "enable_kms_encryption" { type = bool; default = false }
variable "sampling_fixed_rate"   { type = number; default = 0.05 }
variable "indexing_percentage"   { type = number; default = 5.0 }
variable "trace_destination"     { type = string; default = "XRay" }
```

```hcl
# prod.tfvars
aws_region            = "us-east-1"
account_id            = "123456789012"
environment           = "prod"
project               = "my-app"
enable_kms_encryption = true
sampling_fixed_rate   = 0.05
indexing_percentage   = 10.0
trace_destination     = "XRay"
```

---

## Source Bibliography

### Primary Sources
- [aws_xray_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_group) — Registry docs, verified 2026-05-29
- [aws_xray_sampling_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_sampling_rule) — Registry docs, verified 2026-05-29
- [aws_xray_encryption_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_encryption_config) — Registry docs, verified 2026-05-29
- [aws_xray_indexing_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_indexing_rule) — Registry docs, verified 2026-05-29
- [aws_xray_resource_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_resource_policy) — Registry docs, verified 2026-05-29
- [aws_xray_trace_segment_destination](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_trace_segment_destination) — Registry docs, verified 2026-05-29
- [AWS X-Ray Developer Guide](https://docs.aws.amazon.com/xray/latest/devguide/aws-xray.html)
- [AWS X-Ray Concepts](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html)
- [Configuring Sampling Rules](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html)
- [X-Ray IAM Policies](https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html)
- [X-Ray Data Protection](https://docs.aws.amazon.com/xray/latest/devguide/security-data-protection.html)

### Validation & Tools
- [tfsec GitHub](https://github.com/aquasecurity/tfsec) — Security scanner
- [Checkov](https://www.checkov.io/) — Policy-as-code validator
- [Terratest](https://terratest.gruntwork.io/) — Infrastructure testing framework
- [Terraform AWS Provider GitHub](https://github.com/hashicorp/terraform-provider-aws) — Source and issues

---

## Research Gaps

```
Gap: aws_xray_indexing_rule actual_sampling_percentage vs desired_sampling_percentage
Impact: The 'actual_sampling_percentage' attribute is listed as Optional input with no
        clear documentation on read-back behaviour. Unknown if Terraform tracks drift
        between desired and actual.
Workaround: Monitor via AWS Console or CLI: aws xray list-indexing-rules
Follow-up: https://github.com/hashicorp/terraform-provider-aws/issues (search xray_indexing_rule)

Gap: aws_xray_resource_policy policy_revision_id conflict resolution
Impact: Using policy_revision_id = 0 fails if a policy already exists. The behaviour
        when omitting vs. providing this argument is not fully documented for all scenarios.
Workaround: Omit policy_revision_id on initial creation; only set if you need atomic updates.
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/xray_resource_policy

Gap: X-Ray group filter expression syntax validation at terraform plan time
Impact: Invalid filter expressions (e.g. typos in annotation keys) are only caught at
        apply time when the AWS API rejects the CreateGroup/UpdateGroup call.
Workaround: Test filter expressions in AWS Console X-Ray trace filter bar before adding to Terraform.
Follow-up: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-filters.html
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Adding KMS encryption to existing X-Ray deployment
- Creating sampling rules with validated priority ordering
- Adding X-Ray group with filter expression and Insights enabled
- Importing singleton resources (encryption_config, indexing_rule, trace_segment_destination)
- Attaching `AWSXRayDaemonWriteAccess` to Lambda/ECS task roles
- Setting `tracing_config { mode = "Active" }` on Lambda functions

### Medium Confidence (Validate with user)
- Changing `trace_destination` from `XRay` to `CloudWatchLogs` (impacts cost and retention)
- Adjusting sampling `fixed_rate` (impacts tracing cost and visibility)
- Changing KMS key for encryption (requires key policy review)
- Adding `aws_xray_resource_policy` for cross-account access

### Low Confidence (Must ask user)
- Deleting X-Ray groups with Insights enabled (may affect downstream CloudWatch alarms)
- Setting `bypass_policy_lockout_check = true` on resource policies
- Changing `indexing_sampling_percentage` in production (impacts trace search)
- Cross-account/cross-region X-Ray trace sharing strategies

### Emergency Stop
- Halt if `aws_xray_encryption_config.type = "NONE"` is about to be applied to production
- Halt if `bypass_policy_lockout_check = true` in resource policy
- Halt if KMS key `deletion_window_in_days < 7` (minimum AWS limit)
- Halt if removing `aws_xray_trace_segment_destination` — this does **not** revert destination in AWS
