# Terraform AWS SNS — IaC Knowledge Base

---

## Metadata

```yaml
Full_Name: "Terraform AWS Provider - SNS (Simple Notification Service)"
Cloud_Provider: "AWS"
Target_Service: "SNS (Topics, Subscriptions, Topic Policies, Data Protection Policies, SMS Preferences, Platform Applications)"
Terraform_Version: "1.7"
Provider_Version: "aws v6.x (6.47.0 verified via registry 2026-05-28)"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"
Release_Date: "2026-05-28"
Support_Status: "Active"
Last_Updated: "2026-05-28"
Research_Date: "2026-05-28"
Domain_Complexity: "Standard"
V6x_Notable_Changes: |
  - aws_sns_topic: region argument added (optional, overrides provider region)
  - aws_sns_topic_subscription: region argument added (optional, overrides provider region)
  - aws_sns_topic_policy: region argument added (optional, overrides provider region)
  - aws_sns_topic_data_protection_policy: region argument added (optional, overrides provider region)
  - import blocks with identity attribute supported (Terraform v1.12.0+) for all SNS resources
  - aws_sns_topic: fifo_throughput_scope added for high-throughput FIFO mode
  - aws_sns_topic: archive_policy added for FIFO message archiving/replay
  - aws_sns_topic_subscription: replay_policy added for FIFO subscriber replay
  - aws_sns_topic_subscription: filter_policy_scope added (MessageAttributes | MessageBody)
  - FIFO topics support up to 3,000 msg/s (Topic scope) or 300 msg/s (MessageGroup scope)
```

---

## Executive Summary

Amazon SNS (Simple Notification Service) is AWS's fully managed publish-subscribe (pub/sub) messaging service that enables asynchronous fan-out delivery from publishers to multiple subscribers through topics. SNS supports two topic types: **Standard** (virtually unlimited throughput, best-effort ordering, at-least-once delivery, all protocols) and **FIFO** (strict ordering per message group, exactly-once deduplication, SQS FIFO-only subscribers). The Terraform `aws` provider v6.x covers the complete SNS resource surface: `aws_sns_topic`, `aws_sns_topic_subscription`, `aws_sns_topic_policy`, `aws_sns_topic_data_protection_policy`, `aws_sns_sms_preferences`, and `aws_sns_platform_application`, plus the `data.aws_sns_topic` data source and `aws_sns_publish` action resource.

The SNS provider resource surface is organized across four layers: **(1) Topic management** — `aws_sns_topic` controls encryption (`kms_master_key_id`), delivery status feedback roles, FIFO settings (`fifo_topic`, `content_based_deduplication`, `fifo_throughput_scope`), archiving (`archive_policy`), data protection, tracing, and delivery policy; **(2) Access control** — `aws_sns_topic_policy` manages the resource-based access policy with `aws_iam_policy_document` for least-privilege enforcement; **(3) Subscriptions** — `aws_sns_topic_subscription` manages per-endpoint configuration including protocol, filter policy (`filter_policy`, `filter_policy_scope`), DLQ (`redrive_policy`), raw message delivery, and replay policy; **(4) Data protection** — `aws_sns_topic_data_protection_policy` enforces PII/PHI scanning, auditing, and message masking. Cross-account subscriptions require provider aliasing with one provider per account/region combination and explicit SQS queue policies allowing SNS delivery.

Three non-negotiable guardrails for SNS deployments with Terraform: **(1) Always configure `redrive_policy` on every `aws_sns_topic_subscription`** — without a DLQ, messages that exhaust the retry policy are permanently lost with no recovery path; the DLQ must be an SQS queue in the same account and region as the subscription; **(2) Always set `kms_master_key_id` on production `aws_sns_topic` resources** — message bodies containing PII or business data are stored transiently during delivery; SSE with a customer-managed KMS key (CMK) provides at-rest encryption with full audit trail; `alias/aws/sns` is the minimum acceptable, a CMK is preferred; **(3) Never use a wildcard Principal (`"*"`) in `aws_sns_topic_policy` without a restrictive condition** — open topic policies allow unauthorized publishing (message injection), subscription enumeration, and data exfiltration via rogue subscriptions; always scope to `aws:SourceAccount` or explicit IAM principal ARNs. This service is classified **Standard** due to multi-resource composition (topic + policy + subscriptions + DLQ), cross-service IAM dependencies (Lambda, SQS, Firehose), cross-account provider aliasing complexity, FIFO vs Standard architectural decisions, and sensitive data handling via MDP.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

---

#### Pattern: Terraform Configuration Block with Version Constraints

**Why**: Pins provider version to prevent accidental upgrades that could introduce breaking changes. Defines the deployment contract for all team members and CI pipelines.

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
    key            = "prod/sns/terraform.tfstate"
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

**Why**: Credentials must never be hardcoded. `assume_role` enables cross-account SNS management. `default_tags` enforces compliance tagging on IAM roles, KMS keys, SQS DLQs, and all supporting infrastructure. SNS topics themselves support `tags` directly on `aws_sns_topic`.

```hcl
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "terraform-sns-deploy"
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

- **Source**: [AWS Provider Configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration) | [assume_role docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#assume_role)

---

#### Pattern: KMS Encryption on SNS Topic (SSE)

**Why**: SNS stores messages transiently during delivery. Without SSE, message bodies containing PII, credentials, or business data are unencrypted at rest. `kms_master_key_id` enables server-side encryption. For production, use a customer-managed key (CMK) to enable key rotation, fine-grained access control, and CloudTrail audit of every decrypt operation.

```hcl
resource "aws_kms_key" "sns" {
  description             = "KMS key for SNS topic encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = data.aws_iam_policy_document.sns_kms_policy.json

  tags = {
    Name        = "${var.topic_name}-kms"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "sns" {
  name          = "alias/${var.environment}/sns/${var.topic_name}"
  target_key_id = aws_kms_key.sns.key_id
}

data "aws_iam_policy_document" "sns_kms_policy" {
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
    sid    = "Allow SNS to use the key"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    actions = [
      "kms:GenerateDataKey",
      "kms:Decrypt",
    ]
    resources = ["*"]
  }
}

resource "aws_sns_topic" "main" {
  name              = var.topic_name
  kms_master_key_id = aws_kms_key.sns.arn

  tags = {
    Name        = var.topic_name
    Environment = var.environment
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_sns_topic kms_master_key_id](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic) | [SNS SSE Docs](https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html)

---

#### Pattern: Least-Privilege Topic Access Policy with aws_iam_policy_document

**Why**: Without an explicit resource-based policy, SNS defaults to account-owner access only. Using `aws_iam_policy_document` (instead of raw JSON strings) ensures type-safe policy composition, prevents JSON syntax errors, and enables `aws:SourceArn`/`aws:SourceAccount` condition keys to prevent confused deputy attacks when AWS services publish to the topic.

```hcl
data "aws_iam_policy_document" "sns_topic_policy" {
  policy_id = "__default_policy_ID"

  # Allow account owner full control
  statement {
    sid    = "AccountOwnerAccess"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:root"]
    }
    actions = [
      "SNS:GetTopicAttributes",
      "SNS:SetTopicAttributes",
      "SNS:AddPermission",
      "SNS:RemovePermission",
      "SNS:DeleteTopic",
      "SNS:Subscribe",
      "SNS:ListSubscriptionsByTopic",
      "SNS:Publish",
    ]
    resources = [aws_sns_topic.main.arn]
  }

  # Allow CloudWatch Alarms to publish (example AWS service publisher)
  statement {
    sid    = "AllowCloudWatchAlarms"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.main.arn]

    # Prevent confused deputy attack
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "main" {
  arn    = aws_sns_topic.main.arn
  policy = data.aws_iam_policy_document.sns_topic_policy.json
}
```

> **Note**: If a Principal is specified as just an AWS account ID rather than an ARN, AWS silently converts it to the ARN for the root user, causing future Terraform plans to show a diff. Always use full ARNs: `arn:aws:iam::123456789012:root`.

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_sns_topic_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_policy) | [aws_iam_policy_document](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document)

---

#### Pattern: Subscription with DLQ (Dead-Letter Queue) — `redrive_policy`

**Why**: Without a DLQ configured on the subscription, messages that fail delivery after the retry policy exhausts are **permanently and silently lost**. DLQs must be configured per-subscription (not per-topic) because each endpoint can fail independently. For FIFO topic subscriptions, the DLQ must be a FIFO SQS queue. For standard topics, use a standard SQS queue.

```hcl
resource "aws_sqs_queue" "dlq" {
  name                       = "${var.topic_name}-${var.subscriber_name}-dlq"
  message_retention_seconds  = 1209600 # 14 days (maximum)
  kms_master_key_id          = aws_kms_key.sqs.arn

  tags = {
    Name        = "${var.topic_name}-${var.subscriber_name}-dlq"
    Environment = var.environment
  }
}

# DLQ must allow SNS to send messages to it
data "aws_iam_policy_document" "dlq_policy" {
  statement {
    sid    = "AllowSNSRedrive"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    actions   = ["SQS:SendMessage"]
    resources = [aws_sqs_queue.dlq.arn]
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sns_topic.main.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id
  policy    = data.aws_iam_policy_document.dlq_policy.json
}

resource "aws_sqs_queue" "main" {
  name              = "${var.topic_name}-${var.subscriber_name}"
  kms_master_key_id = aws_kms_key.sqs.arn

  tags = {
    Name        = "${var.topic_name}-${var.subscriber_name}"
    Environment = var.environment
  }
}

# SQS queue must allow SNS delivery
data "aws_iam_policy_document" "sqs_queue_policy" {
  statement {
    sid    = "AllowSNSDelivery"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    actions   = ["SQS:SendMessage"]
    resources = [aws_sqs_queue.main.arn]
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sns_topic.main.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "main" {
  queue_url = aws_sqs_queue.main.id
  policy    = data.aws_iam_policy_document.sqs_queue_policy.json
}

resource "aws_sns_topic_subscription" "sqs" {
  topic_arn            = aws_sns_topic.main.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.main.arn
  raw_message_delivery = true  # Deliver message body without SNS envelope

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
  })

  depends_on = [
    aws_sqs_queue_policy.main,
    aws_sqs_queue_policy.dlq,
  ]
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [aws_sns_topic_subscription redrive_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription) | [SNS DLQ Docs](https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html)

---

#### Pattern: Variable Validation and Type Safety

**Why**: Prevents invalid configurations at `terraform plan` time, before any infrastructure is modified. Catches protocol mismatches, missing FIFO naming, and unsupported cross-protocol combinations early.

```hcl
variable "topic_name" {
  type        = string
  description = "SNS topic name. Must end with .fifo if fifo_topic = true."

  validation {
    condition     = length(var.topic_name) >= 1 && length(var.topic_name) <= 256
    error_message = "Topic name must be between 1 and 256 characters."
  }

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+(\\.fifo)?$", var.topic_name))
    error_message = "Topic name must contain only alphanumeric characters, hyphens, underscores, and optionally end with .fifo."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment."

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "subscription_protocol" {
  type        = string
  description = "SNS subscription protocol."

  validation {
    condition     = contains(["sqs", "lambda", "firehose", "application", "sms", "email", "email-json", "http", "https"], var.subscription_protocol)
    error_message = "Protocol must be one of: sqs, lambda, firehose, application, sms, email, email-json, http, https."
  }
}
```

- **Terraform Version**: >= 1.7
- **Source**: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

#### Pattern: Output Definitions for Stack Interdependencies

**Why**: SNS topic ARN and subscription ARN are consumed by Lambda event source mappings, SQS queue policies, CloudWatch alarms, and IAM policies in downstream stacks. Marking outputs as non-sensitive is acceptable for ARNs, but mark subscription IDs as `description`-only since they contain account metadata.

```hcl
output "topic_arn" {
  value       = aws_sns_topic.main.arn
  description = "ARN of the SNS topic. Used by publishers (IAM policies) and subscribers (SQS queue policies, Lambda event source mappings)."
}

output "topic_name" {
  value       = aws_sns_topic.main.name
  description = "Name of the SNS topic."
}

output "subscription_arns" {
  value       = { for k, v in aws_sns_topic_subscription.subscribers : k => v.arn }
  description = "Map of subscription name to subscription ARN."
}

output "dlq_arns" {
  value       = { for k, v in aws_sqs_queue.dlqs : k => v.arn }
  description = "Map of subscriber name to DLQ ARN. Use for monitoring alarms."
}
```

- **Source**: [Terraform Output Values](https://developer.hashicorp.com/terraform/language/values/outputs)

---

#### Pattern: Delivery Status Feedback Roles (CloudWatch)

**Why**: Without delivery status feedback roles, failed deliveries produce no observable signal in CloudWatch. You cannot distinguish between "no messages published" and "all deliveries silently failing." This pattern enables per-protocol success/failure logging.

```hcl
resource "aws_iam_role" "sns_feedback" {
  name = "${var.topic_name}-sns-feedback-role"

  assume_role_policy = data.aws_iam_policy_document.sns_assume_role.json
}

data "aws_iam_policy_document" "sns_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role_policy_attachment" "sns_feedback" {
  role       = aws_iam_role.sns_feedback.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonSNSRole"
}

resource "aws_sns_topic" "main" {
  name              = var.topic_name
  kms_master_key_id = aws_kms_key.sns.arn

  # SQS delivery status feedback
  sqs_success_feedback_role_arn    = aws_iam_role.sns_feedback.arn
  sqs_failure_feedback_role_arn    = aws_iam_role.sns_feedback.arn
  sqs_success_feedback_sample_rate = 100  # 100% sampling in prod for observability

  # Lambda delivery status feedback
  lambda_success_feedback_role_arn    = aws_iam_role.sns_feedback.arn
  lambda_failure_feedback_role_arn    = aws_iam_role.sns_feedback.arn
  lambda_success_feedback_sample_rate = 5  # 5% sampling reduces CloudWatch costs

  # HTTP/HTTPS delivery status feedback
  http_success_feedback_role_arn    = aws_iam_role.sns_feedback.arn
  http_failure_feedback_role_arn    = aws_iam_role.sns_feedback.arn
  http_success_feedback_sample_rate = 5

  tags = {
    Name        = var.topic_name
    Environment = var.environment
  }
}
```

- **Terraform Version**: >= 1.7
- **Provider Version**: aws ~> 6.0
- **Source**: [SNS Message Delivery Status](https://docs.aws.amazon.com/sns/latest/dg/sns-topic-attributes.html#message-delivery-status) | [aws_sns_topic arguments](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic)

---

### ⚠️ Conditional Patterns

---

#### Decision: Standard Topic vs. FIFO Topic

| Option | Optimizes | Sacrifices | Protocols | Throughput | Best When |
|--------|-----------|------------|-----------|------------|-----------|
| **Standard** | Max throughput, multi-protocol | Ordering guarantee, dedup | SQS, Lambda, HTTP/S, email, SMS, mobile push, Firehose | ~30,000 msg/s (us-east-1) | Event notifications, fan-out, alerts, broad delivery |
| **FIFO** | Strict ordering per group, exactly-once | Protocol flexibility, throughput ceiling | SQS FIFO only | 3,000 msg/s (Topic scope) / 300 msg/s (MessageGroup scope) | Financial transactions, ordered state changes, inventory updates |

**FIFO topic rules**:
- Name **must** end with `.fifo`
- Subscribers **must** be SQS FIFO queues (Lambda/HTTP/email/SMS **not supported**)
- Requires `message_group_id` on every Publish call
- `content_based_deduplication` or per-message `MessageDeduplicationId` required

```hcl
# Standard topic
resource "aws_sns_topic" "standard" {
  name              = "order-events"
  kms_master_key_id = aws_kms_key.sns.arn
}

# FIFO topic
resource "aws_sns_topic" "fifo" {
  name                        = "order-events.fifo"
  fifo_topic                  = true
  content_based_deduplication = true
  kms_master_key_id           = aws_kms_key.sns.arn

  # High-throughput FIFO (3,000 msg/s) - available in aws v6.x
  fifo_throughput_scope = "Topic"  # or "MessageGroup" for 300 msg/s per group
}
```

- **Agent**: "Ask user: Does message delivery order matter per logical entity (per-customer, per-order)? Do all consumers support SQS FIFO queues? What is peak messages-per-second requirement?"
- **Source**: [SNS FIFO Topics](https://docs.aws.amazon.com/sns/latest/dg/sns-fifo-topics.html) | [aws_sns_topic fifo_topic](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic)

---

#### Decision: Filter Policy Scope — MessageAttributes vs. MessageBody

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **MessageAttributes** (default) | Performance (no body parsing), works with non-JSON payloads | Requires publishers to set attributes | Routing metadata known at publish time |
| **MessageBody** | Flexibility (payload-based routing), no publisher changes | Performance (JSON parsing), payload must be valid JSON | Existing systems where attributes cannot be added |

```hcl
# Filter on message attributes (recommended)
resource "aws_sns_topic_subscription" "filtered_by_attr" {
  topic_arn            = aws_sns_topic.main.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.orders.arn
  raw_message_delivery = true

  filter_policy_scope = "MessageAttributes"
  filter_policy = jsonencode({
    event_type = ["order.placed", "order.updated"]
    region     = ["us-east-1", "eu-west-1"]
  })

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
  })
}

# Filter on message body (use when payload control is needed)
resource "aws_sns_topic_subscription" "filtered_by_body" {
  topic_arn            = aws_sns_topic.main.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.high_value_orders.arn
  raw_message_delivery = true

  filter_policy_scope = "MessageBody"
  filter_policy = jsonencode({
    order_value = [{ numeric = [">", 1000] }]
    status      = ["CONFIRMED"]
  })

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.high_value_orders_dlq.arn
  })
}
```

- **Agent**: "Ask user: Can publishers set message attributes? Is the payload always valid JSON? Is routing metadata available at publish time or only in the payload?"
- **Source**: [SNS Message Filtering](https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html) | [filter_policy_scope](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription)

---

#### Decision: Raw Message Delivery on SQS Subscriptions

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **raw_message_delivery = true** | Clean payload (no SNS envelope), SQS attributes preserved, lower downstream parsing overhead | SNS metadata (TopicArn, UnsubscribeURL) not delivered | Consumer only needs the message body; SQS FIFO + SNS combos |
| **raw_message_delivery = false** (default) | Full SNS context (TopicArn, Signature, UnsubscribeURL) available to consumer | Consumer must unwrap SNS JSON envelope, message attributes not mapped to SQS attributes | Consumer needs SNS metadata for routing, deduplication via MessageId |

- **Agent**: "Ask user: Does the consumer process the raw payload or does it need SNS envelope metadata (TopicArn, Subject, Signature)?"
- **Source**: [Raw Message Delivery](https://docs.aws.amazon.com/sns/latest/dg/sns-large-payload-raw-message-delivery.html)

---

#### Decision: Cross-Account SNS Subscriptions

Cross-account SNS → SQS requires three aligned configurations: SNS topic policy, SQS queue policy, and Terraform provider aliasing. The provider must be in the region of the SNS topic, using credentials for the account that owns the SQS queue.

| Scenario | Provider Location | Credentials Account |
|----------|-------------------|---------------------|
| SNS and SQS same account + region | Single provider | Either |
| SNS and SQS same account + different region | Provider in SNS region | Either |
| SNS and SQS different accounts + same region | Provider in SQS account, SNS region | SQS account |
| SNS and SQS different accounts + different regions | Provider in SNS region, SQS account credentials | SQS account |

```hcl
# Two providers required for cross-account
provider "aws" {
  alias  = "sns_account"
  region = "us-east-1"
  assume_role { role_arn = "arn:aws:iam::111111111111:role/TerraformRole" }
}

provider "aws" {
  alias  = "sqs_account"
  region = "us-east-1"
  assume_role { role_arn = "arn:aws:iam::222222222222:role/TerraformRole" }
}

# Third provider for the subscription resource (SQS account, SNS region)
provider "aws" {
  alias  = "sns2sqs"
  region = "us-east-1"  # must match SNS topic region
  assume_role { role_arn = "arn:aws:iam::222222222222:role/TerraformRole" }
}

resource "aws_sns_topic_subscription" "cross_account" {
  provider  = aws.sns2sqs  # SQS account credentials, SNS region
  topic_arn = aws_sns_topic.main.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.consumer.arn
}
```

- **Agent**: "Ask user: Are SNS topic and SQS queue in the same account? Same region? Confirm provider alias setup before creating cross-account subscriptions."
- **Source**: [aws_sns_topic_subscription cross-account notes](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription)

---

#### Decision: Message Data Protection Policy

Use `aws_sns_topic_data_protection_policy` when topics carry PII, PHI, or financial data that must be audited, masked, or denied.

```hcl
resource "aws_sns_topic_data_protection_policy" "pii_protection" {
  arn = aws_sns_topic.main.arn

  policy = jsonencode({
    Name        = "${var.topic_name}-data-protection"
    Description = "Deny inbound messages containing PII data identifiers"
    Version     = "2021-06-01"
    Statement = [
      {
        # Audit: log findings without blocking
        Sid           = "AuditSensitiveData"
        DataDirection = "Inbound"
        Principal     = ["*"]
        DataIdentifier = [
          "arn:aws:dataprotection::aws:data-identifier/EmailAddress",
          "arn:aws:dataprotection::aws:data-identifier/CreditCardNumber",
        ]
        Operation = {
          Audit = {
            FindingsDestination = {
              CloudWatchLogs = {
                LogGroup = "/aws/sns/${var.topic_name}/data-protection"
              }
            }
          }
        }
      },
      {
        # Deny: block messages containing SSN
        Sid           = "DenySSNInbound"
        DataDirection = "Inbound"
        Principal     = ["*"]
        DataIdentifier = [
          "arn:aws:dataprotection::aws:data-identifier/USSocialSecurityNumber",
        ]
        Operation = {
          Deny = {}
        }
      },
    ]
  })
}
```

- **Agent**: "Ask user: Does this topic handle PII, PHI, or financial data? What data types must be blocked vs. audited? Is masking required at the subscription level?"
- **Source**: [aws_sns_topic_data_protection_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_data_protection_policy) | [SNS MDP Docs](https://docs.aws.amazon.com/sns/latest/dg/sns-message-data-protection.html)

---

### 🚫 Forbidden Patterns

---

#### Anti-Pattern: Hardcoded Credentials in Provider Block

```hcl
# DON'T
provider "aws" {
  region     = "us-east-1"
  access_key = "AKIAIOSFODNN7EXAMPLE"      # NEVER
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # NEVER
}
```

**Why**: Credentials in code are committed to version control, visible in CI logs, and accessible to all repo readers. Terraform state files containing resources provisioned this way also retain credentials in plaintext.

```hcl
# DO - Use IAM role assumption (preferred in CI/CD and production)
provider "aws" {
  region = var.aws_region
  assume_role {
    role_arn     = "arn:aws:iam::${var.account_id}:role/TerraformDeployRole"
    session_name = "terraform-deploy"
  }
  # Credentials resolved from environment: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
  # Or from EC2/ECS/Lambda instance profile automatically
}
```

- **Impact**: CRITICAL — Full AWS account compromise
- **Severity**: CRITICAL
- **Source**: [AWS Security Best Practices](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)

---

#### Anti-Pattern: Wildcard Principal Without Condition in Topic Policy

```hcl
# DON'T
data "aws_iam_policy_document" "bad_policy" {
  statement {
    effect    = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["*"]  # NEVER without a restrictive condition
    }
    actions   = ["SNS:Publish", "SNS:Subscribe"]
    resources = [aws_sns_topic.main.arn]
  }
}
```

**Why**: An unrestricted wildcard Principal allows any AWS principal in any account to publish messages (message injection attacks), create subscriptions (data exfiltration via rogue subscriber endpoints), and enumerate subscribers.

```hcl
# DO - Scope to specific services with source account condition
data "aws_iam_policy_document" "safe_policy" {
  statement {
    sid    = "AllowCloudWatchPublish"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.main.arn]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.account_id]
    }
  }
}
```

- **Impact**: Message injection, unauthorized subscription, data exfiltration
- **Severity**: CRITICAL
- **Source**: [SNS Access Control](https://docs.aws.amazon.com/sns/latest/dg/sns-access-control.html) | [Confused Deputy Prevention](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html)

---

#### Anti-Pattern: SNS Subscription Without DLQ

```hcl
# DON'T
resource "aws_sns_topic_subscription" "no_dlq" {
  topic_arn = aws_sns_topic.main.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.main.arn
  # No redrive_policy — messages lost on delivery failure
}
```

**Why**: When a delivery fails after all retries (e.g., SQS queue deleted, Lambda function throttled, HTTP endpoint unreachable), SNS discards the message permanently. There is no way to recover lost messages without a DLQ.

```hcl
# DO - Always configure redrive_policy with a DLQ
resource "aws_sns_topic_subscription" "with_dlq" {
  topic_arn            = aws_sns_topic.main.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.main.arn
  raw_message_delivery = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
  })
}
```

- **Impact**: Silent, unrecoverable message loss on delivery failures
- **Severity**: HIGH
- **Source**: [SNS Dead-Letter Queues](https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html)

---

#### Anti-Pattern: SNS Topic Without Encryption (`kms_master_key_id`)

```hcl
# DON'T
resource "aws_sns_topic" "unencrypted" {
  name = "payment-events"
  # No kms_master_key_id — messages unencrypted at rest
}
```

**Why**: SNS messages are stored transiently during delivery. Without SSE, message bodies (which may contain PII, payment data, or credentials) are readable by anyone with access to AWS storage. Compliance requirements (PCI-DSS, HIPAA, SOC 2) mandate encryption at rest.

```hcl
# DO - Always specify encryption for production topics
resource "aws_sns_topic" "encrypted" {
  name              = "payment-events"
  kms_master_key_id = aws_kms_key.sns.arn  # Customer-managed CMK preferred

  # Minimum acceptable alternative (AWS-managed key, no custom rotation/audit)
  # kms_master_key_id = "alias/aws/sns"
}
```

- **Impact**: PII/payment data exposure, compliance violation (PCI-DSS, HIPAA)
- **Severity**: HIGH
- **Source**: [SNS SSE](https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html)

---

#### Anti-Pattern: FIFO Topic Name Without `.fifo` Suffix

```hcl
# DON'T
resource "aws_sns_topic" "bad_fifo" {
  name       = "order-events"  # WRONG — Terraform apply will fail
  fifo_topic = true
}
```

**Why**: AWS requires FIFO topic names to end with `.fifo`. Terraform will attempt to create the topic but AWS will reject it with an InvalidParameter error. This is a deploy-time failure with no plan-time warning.

```hcl
# DO - FIFO topic name must end with .fifo
resource "aws_sns_topic" "correct_fifo" {
  name       = "order-events.fifo"  # Required suffix
  fifo_topic = true
  content_based_deduplication = true
  kms_master_key_id = aws_kms_key.sns.arn
}
```

- **Impact**: Deploy-time failure, broken CI/CD pipeline
- **Severity**: HIGH
- **Source**: [FIFO Topic Requirements](https://docs.aws.amazon.com/sns/latest/dg/sns-fifo-topics.html)

---

#### Anti-Pattern: Bare AWS Account ID as Principal (Causes Perpetual Drift)

```hcl
# DON'T
data "aws_iam_policy_document" "drifty" {
  statement {
    principals {
      type        = "AWS"
      identifiers = ["123456789012"]  # Bare account ID — AWS converts to root ARN silently
    }
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.main.arn]
  }
}
```

**Why**: AWS silently converts bare account IDs to `arn:aws:iam::123456789012:root`. Terraform sees the converted value as a diff on every subsequent plan, causing perpetual false-drift.

```hcl
# DO - Always use full ARN
data "aws_iam_policy_document" "stable" {
  statement {
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:root"]  # Full ARN
    }
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.main.arn]
  }
}
```

- **Impact**: Perpetual Terraform plan diffs, operator confusion, CI noise
- **Severity**: MEDIUM
- **Source**: [aws_sns_topic_policy NOTE](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_policy)

---

#### Anti-Pattern: Missing State File Encryption

```hcl
# DON'T
terraform {
  backend "s3" {
    bucket = "my-tf-state"
    key    = "sns/terraform.tfstate"
    region = "us-east-1"
    # No encrypt = true — state stored in plaintext
    # No dynamodb_table — no state locking
  }
}
```

**Why**: The Terraform state file for an SNS deployment contains topic ARNs, subscription ARNs, KMS key IDs, IAM role ARNs, and SQS queue ARNs — sufficient information to enumerate and attack your messaging infrastructure.

```hcl
# DO
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/sns/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

- **Impact**: Infrastructure enumeration, targeted attacks against messaging topology
- **Severity**: HIGH
- **Source**: [Terraform State Security](https://developer.hashicorp.com/terraform/language/state/sensitive-data)

---

#### Anti-Pattern: Unconfirmable Subscriptions (email/http without auto-confirm)

```hcl
# DON'T - Creates unmanageable state
resource "aws_sns_topic_subscription" "email_sub" {
  topic_arn = aws_sns_topic.main.arn
  protocol  = "email"
  endpoint  = "alerts@example.com"
  # SNS sends confirmation email — Terraform cannot delete until confirmed
  # terraform destroy will orphan this subscription in AWS
}
```

**Why**: Email, email-json, and HTTP/S (without `endpoint_auto_confirms`) subscriptions require out-of-band confirmation. Until confirmed, Terraform cannot delete the subscription. Running `terraform destroy` removes it from state but leaves the subscription in AWS.

```hcl
# DO - Use HTTPS with auto-confirm for programmatic endpoints
resource "aws_sns_topic_subscription" "https_auto" {
  topic_arn              = aws_sns_topic.main.arn
  protocol               = "https"
  endpoint               = "https://my-service.example.com/sns/confirm"
  endpoint_auto_confirms = true  # Endpoint handles confirmation automatically
}

# For email alerts, consider CloudWatch Alarm Actions or SES instead of SNS email subscriptions
```

- **Impact**: Unmanaged AWS resources, broken destroy workflows, state drift
- **Severity**: MEDIUM
- **Source**: [aws_sns_topic_subscription partially-supported protocols](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription)

---

## State Management Deep Dive

### Local Development State
```hcl
# Use local state only for individual dev experiments
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
  # No backend block = local state
}
```
- **Risk**: Single point of failure, no team sharing, no locking, state includes topic ARNs
- **When**: Solo dev, learning, throwaway environments only

### Production Remote State (S3 + DynamoDB)

```hcl
# Bootstrap: DynamoDB table for state locking (create once, manage separately)
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = { Name = "terraform-locks", ManagedBy = "terraform" }
}

# Backend configuration
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/sns/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

# State bucket hardening (manage in a separate bootstrap workspace)
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = "my-org-terraform-state"
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = "my-org-terraform-state"
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.state_bucket.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket                  = "my-org-terraform-state"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

- **Benefit**: Team sharing, state locking prevents concurrent apply conflicts, version history enables rollback
- **Source**: [Terraform S3 Backend](https://developer.hashicorp.com/terraform/language/settings/backends/s3)

---

## Module Architecture

### Standard Module Structure
```
modules/
└── sns-topic/
    ├── main.tf          # aws_sns_topic, aws_sns_topic_policy, aws_sns_topic_data_protection_policy
    ├── variables.tf     # topic_name, environment, kms_key_arn, fifo settings, feedback roles
    ├── outputs.tf       # topic_arn, topic_name, topic_owner
    ├── versions.tf      # required_version, required_providers constraints
    └── README.md        # Module usage, input/output documentation

modules/
└── sns-subscription/
    ├── main.tf          # aws_sns_topic_subscription, aws_sqs_queue (dlq), aws_sqs_queue_policy
    ├── variables.tf     # topic_arn, protocol, endpoint_arn, filter_policy, raw_message_delivery
    ├── outputs.tf       # subscription_arn, dlq_arn
    ├── versions.tf
    └── README.md
```

### Module Definition Example

```hcl
# modules/sns-topic/variables.tf
variable "topic_name" {
  type        = string
  description = "SNS topic name. Must end with .fifo if fifo_topic = true."

  validation {
    condition     = length(var.topic_name) >= 1 && length(var.topic_name) <= 256
    error_message = "Topic name must be 1-256 characters."
  }
}

variable "kms_key_arn" {
  type        = string
  description = "ARN of the KMS key for SNS SSE. Required for production."

  validation {
    condition     = can(regex("^arn:aws:kms:", var.kms_key_arn))
    error_message = "kms_key_arn must be a valid KMS key ARN."
  }
}

variable "fifo_topic" {
  type        = bool
  description = "Whether to create a FIFO topic. If true, topic_name must end with .fifo."
  default     = false
}

variable "allowed_publisher_arns" {
  type        = list(string)
  description = "List of IAM principal ARNs allowed to publish to this topic."
  default     = []
}

# modules/sns-topic/outputs.tf
output "topic_arn" {
  value       = aws_sns_topic.this.arn
  description = "SNS topic ARN."
}

output "topic_name" {
  value       = aws_sns_topic.this.name
  description = "SNS topic name."
}

# root/main.tf - Using the module
module "order_events_topic" {
  source = "./modules/sns-topic"

  topic_name  = "order-events"
  kms_key_arn = module.kms.sns_key_arn
  environment = var.environment

  allowed_publisher_arns = [
    module.order_service_role.arn,
  ]
}

module "order_sqs_subscription" {
  source = "./modules/sns-subscription"

  topic_arn   = module.order_events_topic.topic_arn
  protocol    = "sqs"
  endpoint    = module.order_processor_queue.queue_arn
  environment = var.environment

  filter_policy = jsonencode({
    event_type = ["order.placed", "order.updated"]
  })
}
```

---

## Integration Patterns

### Integration: Terraform ↔ SQS

**Pattern**: Fan-out to multiple SQS queues from a single SNS topic with filter policies.

```hcl
# SQS queue with inline policy allowing SNS delivery
resource "aws_sqs_queue" "order_processor" {
  name              = "order-processor"
  kms_master_key_id = "alias/aws/sqs"
}

data "aws_iam_policy_document" "order_processor_policy" {
  statement {
    sid    = "AllowSNSDelivery"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    actions   = ["SQS:SendMessage"]
    resources = [aws_sqs_queue.order_processor.arn]
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sns_topic.order_events.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "order_processor" {
  queue_url = aws_sqs_queue.order_processor.id
  policy    = data.aws_iam_policy_document.order_processor_policy.json
}

resource "aws_sns_topic_subscription" "to_order_processor" {
  topic_arn            = aws_sns_topic.order_events.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.order_processor.arn
  raw_message_delivery = true

  filter_policy_scope = "MessageAttributes"
  filter_policy = jsonencode({
    event_type = ["order.placed"]
  })

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.order_processor_dlq.arn
  })

  depends_on = [aws_sqs_queue_policy.order_processor]
}
```

**Issues**:
- SQS queue must have a resource-based policy allowing `sns.amazonaws.com` to send before the subscription is created; use `depends_on` to enforce ordering
- For FIFO: SNS FIFO → SQS FIFO only; `raw_message_delivery` with FIFO preserves `MessageGroupId` and `MessageDeduplicationId`
- Cross-region not supported for SNS → SQS

**Versions**:
| Resource | Min Provider | Notes |
|----------|-------------|-------|
| aws_sqs_queue | ~> 6.0 | |
| aws_sqs_queue_policy | ~> 6.0 | |
| aws_sns_topic_subscription | ~> 6.0 | filter_policy_scope available |

**Source**: [SNS SQS Integration](https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html)

---

### Integration: Terraform ↔ Lambda

**Pattern**: SNS triggers Lambda function for event processing.

```hcl
resource "aws_lambda_function" "event_processor" {
  function_name = "sns-event-processor"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "index.handler"
  runtime       = "nodejs20.x"
  filename      = data.archive_file.lambda.output_path
}

# Lambda must grant SNS permission to invoke it
resource "aws_lambda_permission" "sns" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.event_processor.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.main.arn
}

resource "aws_sns_topic_subscription" "lambda" {
  topic_arn = aws_sns_topic.main.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.event_processor.arn

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.lambda_dlq.arn
  })

  depends_on = [aws_lambda_permission.sns]
}
```

**Issues**:
- Lambda resource policy (`aws_lambda_permission`) must exist before the subscription; use `depends_on`
- Lambda DLQ must be an SQS queue; FIFO topics cannot subscribe Lambda (not supported)
- Lambda concurrency throttle causes delivery failures → DLQ is critical
- `raw_message_delivery` is NOT supported for Lambda subscriptions (always delivers SNS envelope)

**Source**: [SNS Lambda Subscriber](https://docs.aws.amazon.com/sns/latest/dg/sns-lambda-as-subscriber.html)

---

### Integration: Terraform ↔ KMS

**Pattern**: Customer-managed KMS key for SNS topic encryption with key policy scoped to SNS service.

```hcl
resource "aws_kms_key" "sns" {
  description             = "CMK for SNS topic ${var.topic_name}"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = data.aws_iam_policy_document.kms_policy.json
}

data "aws_iam_policy_document" "kms_policy" {
  statement {
    sid     = "EnableRootAccess"
    effect  = "Allow"
    principals { type = "AWS"; identifiers = ["arn:aws:iam::${var.account_id}:root"] }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid     = "AllowSNS"
    effect  = "Allow"
    principals { type = "Service"; identifiers = ["sns.amazonaws.com"] }
    actions   = ["kms:GenerateDataKey", "kms:Decrypt"]
    resources = ["*"]
  }

  # Allow CloudWatch to use the key if it publishes to encrypted SNS
  statement {
    sid     = "AllowCloudWatch"
    effect  = "Allow"
    principals { type = "Service"; identifiers = ["cloudwatch.amazonaws.com"] }
    actions   = ["kms:GenerateDataKey", "kms:Decrypt"]
    resources = ["*"]
  }
}

resource "aws_sns_topic" "main" {
  name              = var.topic_name
  kms_master_key_id = aws_kms_key.sns.arn
}
```

**Issues**:
- If CloudWatch Alarms publish to an SSE-encrypted topic using CMK, CloudWatch must be granted `kms:GenerateDataKey` and `kms:Decrypt` in the key policy — without this, alarm notifications fail silently
- EventBridge, Config, and other AWS services publishing to encrypted topics have the same requirement
- `alias/aws/sns` (AWS-managed key) does NOT require explicit key policy entries — but provides no custom rotation or access audit

**Source**: [SNS SSE with CMK](https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html#sse-key-terms)

---

### Integration: Terraform ↔ IAM

**Pattern**: IAM policies for publishers and the IAM roles for SNS delivery status feedback.

```hcl
# IAM policy for application services that publish to SNS
data "aws_iam_policy_document" "publisher_policy" {
  statement {
    sid    = "AllowSNSPublish"
    effect = "Allow"
    actions = [
      "sns:Publish",
      "sns:GetTopicAttributes",
    ]
    resources = [aws_sns_topic.main.arn]
  }

  # Allow KMS operations for encrypted topics
  statement {
    sid    = "AllowKMSForSNS"
    effect = "Allow"
    actions = [
      "kms:GenerateDataKey",
      "kms:Decrypt",
    ]
    resources = [aws_kms_key.sns.arn]
  }
}

resource "aws_iam_policy" "publisher" {
  name   = "${var.topic_name}-publisher"
  policy = data.aws_iam_policy_document.publisher_policy.json
}

# IAM role for SNS delivery status feedback to CloudWatch
resource "aws_iam_role" "sns_feedback" {
  name = "${var.topic_name}-feedback"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "sns_feedback" {
  role       = aws_iam_role.sns_feedback.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonSNSRole"
}
```

**Issues**:
- Publishers need both SNS publish permission AND KMS permissions for encrypted topics
- The SNS feedback role must use the AWS-managed `AmazonSNSRole` policy exactly — custom policies will not work
- Never grant `sns:Subscribe` to application services — subscriptions should be managed by Terraform only

**Source**: [SNS IAM Policies](https://docs.aws.amazon.com/sns/latest/dg/sns-access-control.html)

---

### Integration: Terraform ↔ CloudWatch

**Pattern**: DLQ depth alarm to alert on delivery failures.

```hcl
resource "aws_cloudwatch_metric_alarm" "dlq_depth" {
  for_each = aws_sqs_queue.dlqs

  alarm_name          = "${each.key}-dlq-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = each.value.name
  }

  alarm_actions = [aws_sns_topic.ops_alerts.arn]
  ok_actions    = [aws_sns_topic.ops_alerts.arn]

  tags = { Environment = var.environment }
}

# CloudWatch alarm for SNS delivery failures (requires failure feedback role)
resource "aws_cloudwatch_metric_alarm" "sns_delivery_failures" {
  alarm_name          = "${var.topic_name}-delivery-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "NumberOfNotificationsFailed"
  namespace           = "AWS/SNS"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    TopicName = aws_sns_topic.main.name
  }

  alarm_actions = [aws_sns_topic.ops_alerts.arn]
}
```

**Source**: [SNS CloudWatch Metrics](https://docs.aws.amazon.com/sns/latest/dg/sns-monitoring-using-cloudwatch.html)

---

### Integration: Terraform ↔ EventBridge

**Pattern**: EventBridge rule sends events to SNS for fan-out to multiple subscribers.

```hcl
# EventBridge → SNS: SNS topic must have policy allowing events.amazonaws.com to publish
data "aws_iam_policy_document" "allow_eventbridge" {
  statement {
    sid    = "AllowEventBridgePublish"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.main.arn]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.account_id]
    }
  }
}

resource "aws_cloudwatch_event_rule" "order_placed" {
  name        = "order-placed-rule"
  description = "Capture order.placed events"
  event_pattern = jsonencode({
    source      = ["myapp.orders"]
    detail-type = ["OrderPlaced"]
  })
}

resource "aws_cloudwatch_event_target" "sns" {
  rule      = aws_cloudwatch_event_rule.order_placed.name
  target_id = "sns-fanout"
  arn       = aws_sns_topic.main.arn
}
```

**Issues**:
- EventBridge requires SNS topic policy to explicitly allow `events.amazonaws.com` to publish — this is not automatic even within the same account
- For encrypted SNS topics with CMK, EventBridge must also be granted `kms:GenerateDataKey` and `kms:Decrypt` in the key policy

**Source**: [EventBridge SNS Target](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-targets.html#targets-sns)

---

## Quality Control

### Verification Commands

```bash
# Format check — must pass before commit
terraform fmt -recursive -check=true
# Expected: Exit code 0, no formatting errors

# Validate configuration
terraform validate
# Expected: "Success! The configuration is valid."

# Initialize with provider upgrade
terraform init -upgrade
# Expected: "Terraform has been successfully initialized!"

# Security scan (tfsec)
tfsec . --format sarif --minimum-severity HIGH
# Expected: No HIGH or CRITICAL findings

# Policy-as-code scan (checkov)
checkov -d . --framework terraform --quiet --compact
# Expected: Passed checks count > Failed checks

# Dry run with lock
terraform plan -out=tfplan -lock=true
terraform show tfplan
# Expected: Plan shows expected resource changes

# Verify state after apply
terraform state list | grep sns
# Expected: aws_sns_topic.main, aws_sns_topic_policy.main, aws_sns_topic_subscription.*

# Show topic details from state
terraform state show aws_sns_topic.main
# Expected: arn, kms_master_key_id, fifo_topic, tags_all populated

# Outputs
terraform output
# Expected: topic_arn, subscription_arns populated
```

### Testing with Terratest

```go
package test

import (
  "encoding/json"
  "testing"

  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/stretchr/testify/assert"
)

func TestSNSTopicDeployment(t *testing.T) {
  opts := &terraform.Options{
    TerraformDir: "../examples/sns-topic",
    Vars: map[string]interface{}{
      "topic_name":  "test-topic",
      "environment": "dev",
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  topicArn := terraform.Output(t, opts, "topic_arn")
  assert.Contains(t, topicArn, "arn:aws:sns:")
  assert.Contains(t, topicArn, "test-topic")
}

func TestSNSTopicEncryption(t *testing.T) {
  opts := &terraform.Options{
    TerraformDir: "../examples/sns-topic",
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  // Verify KMS key is set
  topicAttrs := terraform.OutputMap(t, opts, "topic_attributes")
  assert.NotEmpty(t, topicAttrs["kms_master_key_id"], "Topic must have KMS encryption enabled")
}
```

---

## Production Readiness

### Performance and Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Standard topic throughput | ~30,000 msg/s (us-east-1) | Soft limit, request increase via AWS Support |
| FIFO topic throughput (Topic scope) | 3,000 msg/s or 20 MB/s | Set `fifo_throughput_scope = "Topic"` |
| FIFO topic throughput (MessageGroup scope) | 300 msg/s per group | Default FIFO throughput |
| Topics per account | 100,000 | Soft limit |
| Subscriptions per topic (Standard) | 12,500,000 | Includes pending |
| Subscriptions per topic (FIFO) | 100 | Hard limit |
| Filter policies per topic | 200 | Across all subscriptions |
| Message size | 256 KB | Hard limit |

### Scalability

```hcl
# Use for_each for multiple subscriptions to avoid state reordering issues
locals {
  subscribers = {
    "order-processor" = {
      protocol    = "sqs"
      endpoint    = aws_sqs_queue.order_processor.arn
      dlq_arn     = aws_sqs_queue.order_processor_dlq.arn
      filter      = jsonencode({ event_type = ["order.placed"] })
    }
    "inventory-updater" = {
      protocol    = "sqs"
      endpoint    = aws_sqs_queue.inventory.arn
      dlq_arn     = aws_sqs_queue.inventory_dlq.arn
      filter      = jsonencode({ event_type = ["order.placed", "order.cancelled"] })
    }
  }
}

resource "aws_sns_topic_subscription" "subscribers" {
  for_each = local.subscribers

  topic_arn            = aws_sns_topic.main.arn
  protocol             = each.value.protocol
  endpoint             = each.value.endpoint
  raw_message_delivery = true
  filter_policy        = each.value.filter

  redrive_policy = jsonencode({
    deadLetterTargetArn = each.value.dlq_arn
  })
}
```

### Security Checklist

- [ ] All production topics have `kms_master_key_id` set (CMK preferred over `alias/aws/sns`)
- [ ] `aws_sns_topic_policy` uses `aws_iam_policy_document` with full ARN Principals (not bare account IDs)
- [ ] No wildcard `*` Principal without `aws:SourceAccount` or `aws:SourceArn` condition
- [ ] Every `aws_sns_topic_subscription` has `redrive_policy` with DLQ ARN
- [ ] DLQ SQS queues have resource policies allowing `sns.amazonaws.com` to send
- [ ] Lambda subscribers have `aws_lambda_permission` granting SNS invoke before subscription
- [ ] State file backend uses `encrypt = true` and `dynamodb_table` for locking
- [ ] KMS key policy grants `kms:GenerateDataKey` + `kms:Decrypt` to all AWS services publishing to encrypted topic
- [ ] All resources tagged with Environment, Owner, ManagedBy, CostCenter
- [ ] CloudWatch alarms on DLQ depth and SNS `NumberOfNotificationsFailed`
- [ ] Failure feedback IAM role configured on topic for all active protocols

### Disaster Recovery Runbook

```bash
# 1. Topic accidentally destroyed — recreate via import if ARN still exists
terraform import aws_sns_topic.main arn:aws:sns:us-east-1:123456789012:my-topic

# 2. State corruption — restore from S3 versioned backup
aws s3api list-object-versions \
  --bucket my-org-terraform-state \
  --prefix prod/sns/terraform.tfstate \
  --query 'Versions[*].[VersionId,LastModified]' \
  --output table

aws s3api get-object \
  --bucket my-org-terraform-state \
  --key prod/sns/terraform.tfstate \
  --version-id <version-id> \
  terraform.tfstate.restore

terraform state push terraform.tfstate.restore

# 3. Drift detection — compare state vs. real infrastructure
terraform plan -refresh-only
# Expected: "No changes" if no drift; lists changes if manual modifications detected

# 4. Import existing subscription
terraform import aws_sns_topic_subscription.main \
  arn:aws:sns:us-east-1:123456789012:my-topic:8a21d249-4329-4871-acc6-7be709c6ea7f

# 5. Replay archived messages to FIFO subscription (Terraform managed)
# Set replay_policy on the subscription and apply
resource "aws_sns_topic_subscription" "fifo_sub" {
  # ... existing config ...
  replay_policy = jsonencode({
    startingPosition = "LATEST"  # or "EARLIEST" or specific timestamp
  })
}
```

---

## Reference Implementations

### Complete Working Example (Standard Topic + SQS Fan-out)

```hcl
# variables.tf
variable "environment" { type = string }
variable "account_id"  { type = string }
variable "aws_region"  { type = string; default = "us-east-1" }

# main.tf
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/sns/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

resource "aws_kms_key" "sns" {
  description             = "SNS order-events CMK"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  policy                  = data.aws_iam_policy_document.kms_policy.json
}

data "aws_iam_policy_document" "kms_policy" {
  statement {
    sid       = "Root"
    effect    = "Allow"
    principals { type = "AWS"; identifiers = ["arn:aws:iam::${var.account_id}:root"] }
    actions   = ["kms:*"]
    resources = ["*"]
  }
  statement {
    sid       = "SNS"
    effect    = "Allow"
    principals { type = "Service"; identifiers = ["sns.amazonaws.com"] }
    actions   = ["kms:GenerateDataKey", "kms:Decrypt"]
    resources = ["*"]
  }
}

resource "aws_sns_topic" "order_events" {
  name              = "order-events"
  kms_master_key_id = aws_kms_key.sns.arn

  sqs_success_feedback_role_arn    = aws_iam_role.sns_feedback.arn
  sqs_failure_feedback_role_arn    = aws_iam_role.sns_feedback.arn
  sqs_success_feedback_sample_rate = 100

  lambda_success_feedback_role_arn    = aws_iam_role.sns_feedback.arn
  lambda_failure_feedback_role_arn    = aws_iam_role.sns_feedback.arn
  lambda_success_feedback_sample_rate = 5

  tags = { Name = "order-events" }
}

resource "aws_sns_topic_policy" "order_events" {
  arn    = aws_sns_topic.order_events.arn
  policy = data.aws_iam_policy_document.topic_policy.json
}

data "aws_iam_policy_document" "topic_policy" {
  statement {
    sid    = "AccountOwner"
    effect = "Allow"
    principals { type = "AWS"; identifiers = ["arn:aws:iam::${var.account_id}:root"] }
    actions   = ["SNS:GetTopicAttributes", "SNS:SetTopicAttributes", "SNS:Publish", "SNS:Subscribe", "SNS:ListSubscriptionsByTopic", "SNS:DeleteTopic"]
    resources = [aws_sns_topic.order_events.arn]
  }
}

# DLQ
resource "aws_sqs_queue" "processor_dlq" {
  name                      = "order-processor-dlq"
  message_retention_seconds = 1209600
}

resource "aws_sqs_queue" "processor" {
  name = "order-processor"
}

data "aws_iam_policy_document" "processor_queue_policy" {
  statement {
    effect    = "Allow"
    principals { type = "Service"; identifiers = ["sns.amazonaws.com"] }
    actions   = ["SQS:SendMessage"]
    resources = [aws_sqs_queue.processor.arn]
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sns_topic.order_events.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "processor" {
  queue_url = aws_sqs_queue.processor.id
  policy    = data.aws_iam_policy_document.processor_queue_policy.json
}

resource "aws_sns_topic_subscription" "processor" {
  topic_arn            = aws_sns_topic.order_events.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.processor.arn
  raw_message_delivery = true

  filter_policy_scope = "MessageAttributes"
  filter_policy = jsonencode({ event_type = ["order.placed"] })

  redrive_policy = jsonencode({ deadLetterTargetArn = aws_sqs_queue.processor_dlq.arn })

  depends_on = [aws_sqs_queue_policy.processor]
}

# IAM feedback role
resource "aws_iam_role" "sns_feedback" {
  name               = "order-events-sns-feedback"
  assume_role_policy = data.aws_iam_policy_document.sns_assume.json
}

data "aws_iam_policy_document" "sns_assume" {
  statement {
    effect    = "Allow"
    principals { type = "Service"; identifiers = ["sns.amazonaws.com"] }
    actions   = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role_policy_attachment" "sns_feedback" {
  role       = aws_iam_role.sns_feedback.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonSNSRole"
}

# outputs.tf
output "topic_arn"       { value = aws_sns_topic.order_events.arn }
output "processor_dlq_url" { value = aws_sqs_queue.processor_dlq.url }
```

**Example `terraform.tfvars`**:
```hcl
environment = "prod"
account_id  = "123456789012"
aws_region  = "us-east-1"
```

---

## Source Bibliography

### Primary Sources
- [aws_sns_topic Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic) — All arguments, FIFO, SSE, feedback roles
- [aws_sns_topic_subscription Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription) — Protocol list, filter_policy_scope, redrive_policy, replay_policy
- [aws_sns_topic_policy Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_policy) — Policy management, bare-ID drift warning
- [aws_sns_topic_data_protection_policy Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_data_protection_policy) — MDP policy structure
- [data.aws_sns_topic Data Source](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/sns_topic) — Cross-stack ARN lookup
- [GitHub: sns_topic.html.markdown](https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/sns_topic.html.markdown) — Source of truth for argument list (v6.47.0, 2026-05-28)
- [GitHub: sns_topic_subscription.html.markdown](https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/sns_topic_subscription.html.markdown) — Subscription arguments, cross-account notes
- [AWS SNS Developer Guide](https://docs.aws.amazon.com/sns/latest/dg/welcome.html) — Service architecture, FIFO, MDP, filtering

### Validation & Tools
- [tfsec GitHub](https://github.com/aquasecurity/tfsec) — SNS-specific checks: unencrypted topics, open policies
- [Checkov](https://www.checkov.io/) — Policy-as-code for SNS resource compliance
- [Terratest](https://terratest.gruntwork.io/) — Go-based integration testing
- [GitHub Issues: hashicorp/terraform-provider-aws](https://github.com/hashicorp/terraform-provider-aws/issues?q=sns) — Known SNS provider bugs, v6.x regressions

---

## Research Gaps

```
Gap: aws_sns_platform_application resource (mobile push: APNS, GCM/FCM, ADM, Baidu, WNS)
Impact: Mobile push notification deployments cannot reference this document
Workaround: Use aws_sns_platform_application resource directly; arguments are: name, platform, platform_credential; not covered in depth here
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_platform_application

Gap: aws_sns_sms_preferences resource (SMS settings: DefaultSMSType, MonthlySpendLimit, DeliveryStatusIAMRole)
Impact: SMS-heavy deployments (OTP, alerts) need additional configuration not covered here
Workaround: Use aws_sns_sms_preferences directly; one resource per account/region
Follow-up: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_sms_preferences

Gap: Sandbox → Production SNS access progression (AWS Support request required)
Impact: New accounts are in SNS Sandbox by default; SMS sending and email require manual AWS Support escalation
Workaround: Document requirement in runbook; cannot be automated via Terraform
Follow-up: https://docs.aws.amazon.com/sns/latest/dg/sns-sms-sandbox.html
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Standard topic creation with encryption, policy, and feedback roles
- SQS subscription with DLQ and filter policy
- Lambda subscription with resource permission
- Topic policy using `aws_iam_policy_document`
- State backend and locking configuration
- CloudWatch alarms for DLQ depth and delivery failures

### Medium Confidence (Validate with user)
- FIFO vs. Standard topic selection
- `filter_policy_scope` MessageAttributes vs. MessageBody
- `fifo_throughput_scope` Topic vs. MessageGroup
- Cross-account subscription provider aliasing
- Data protection policy scope (audit vs. deny)

### Low Confidence (Must ask user)
- FIFO topic archiving and replay policy configuration
- SMS preferences (spend limits, DefaultSMSType)
- Mobile push (Platform Application credentials)
- Cross-region subscription topology
- Compliance-specific MDP data identifiers (HIPAA, PCI-DSS)

### Emergency Stop
- Halt if `kms_master_key_id` omitted on production topic
- Halt if `redrive_policy` missing from any subscription
- Halt if wildcard Principal without condition detected in topic policy
- Halt if `terraform destroy` includes production SNS topics without explicit confirmation
- Halt if credentials found in provider block or `.tfvars` files in version control
