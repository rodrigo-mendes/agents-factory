# Always-Do — Topic (Provider, Standard/FIFO Topic, Key Policy, Feedback)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23. Names, ARNs and numbers are `# example`.

## 1. Terraform Block and Provider

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
# Source (versions): https://releases.hashicorp.com/terraform/ and https://releases.hashicorp.com/terraform-provider-aws/
# Source (root modules use ~>): https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```

Every SNS resource documents an optional `region`; changing it forces replacement and import uses
`id@region`. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

## 2. Standard Topic with a Customer Managed Key

`kms_master_key_id` takes an AWS-managed or customer managed key ID; SNS supports symmetric keys only.
Security Hub SNS.1 is "SNS topics should be encrypted at-rest using AWS KMS". SNS.3 uses a
`requiredTagKeys` parameter.

```hcl
resource "aws_kms_key" "sns" {
  description = "SNS topic key" # example
  # incomplete fragment: key policy, rotation etc. defined elsewhere; see section 4 and provisioning-aws-kms-v6
}

resource "aws_sns_topic" "orders" {
  name              = "orders-events"        # example
  kms_master_key_id = aws_kms_key.sns.id
  tags              = { Team = "payments" }  # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown
# Source: https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/sns-controls.html
```

Provider `default_tags` with matching keys are overridden by resource `tags`
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown).

## 3. FIFO Topic

The name must end in `.fifo`. AWS: a FIFO topic cannot be converted to standard (or the reverse).
`fifo_throughput_scope` defaults to `Topic`; `MessageGroup` enables high throughput and cannot be
reverted to `Topic`; AWS recommends setting it at creation. FIFO topics deliver to SQS FIFO and SQS
standard queues, not to email, mobile, SMS or HTTP(S).

```hcl
resource "aws_sns_topic" "orders_fifo" {
  name                        = "orders-events.fifo" # example
  fifo_topic                  = true
  content_based_deduplication = true # example
  fifo_throughput_scope       = "Topic" # example; MessageGroup is irreversible (Ask First)
  kms_master_key_id           = aws_kms_key.sns.id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown
# Source: https://docs.aws.amazon.com/sns/latest/dg/fifo-high-throughput.html
# Source: https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html
```

## 4. Key Policy for AWS Service Publishers

For AWS event sources (for example CloudWatch `cloudwatch.amazonaws.com`) use a customer managed key
and grant the service principal `kms:GenerateDataKey*` and `kms:Decrypt`; AWS also says to add
`aws:SourceAccount`/`aws:SourceArn` conditions. Those conditions are **not supported** for
EventBridge publishing (see never-do). Some sources (EC2 Auto Scaling, CodePipeline, AWS Config,
and others) need an IAM role in the key policy instead of the service principal.

```hcl
# FRAGMENT, not a complete key policy: the full key policy must also keep the key-administration
# statements. See provisioning-aws-kms-v6.
data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "sns_key" {
  statement {
    sid       = "AllowCloudWatchPublish"
    actions   = ["kms:GenerateDataKey*", "kms:Decrypt"]
    resources = ["*"]
    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
  # fragment: key-administration statements defined elsewhere (see provisioning-aws-kms-v6)
}
# Source: https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html
```

Merge this statement into the complete key policy of `aws_kms_key.sns`; do not attach this fragment
alone. KMS resources: see `provisioning-aws-kms-v6`.

## 5. Delivery Status Logging and Data Protection

Per-protocol feedback arguments (`application_`, `http_`, `lambda_`, `sqs_`, `firehose_` prefixed
`success_feedback_role_arn`, `failure_feedback_role_arn`, `success_feedback_sample_rate` 0–100) let SNS
write delivery status to CloudWatch Logs; a failure role logs all failed deliveries.

```hcl
resource "aws_sns_topic" "with_feedback" {
  name                           = "orders-feedback"                    # example
  sqs_success_feedback_role_arn  = aws_iam_role.sns_feedback.arn # placeholder: role defined elsewhere
  sqs_failure_feedback_role_arn  = aws_iam_role.sns_feedback.arn # placeholder
  sqs_success_feedback_sample_rate = 10 # example, 0-100
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown

resource "aws_sns_topic_data_protection_policy" "orders" {
  arn    = aws_sns_topic.orders.arn
  policy = file("${path.module}/data-protection.json") # example path
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_data_protection_policy.html.markdown
```

The IAM role itself is defined elsewhere (not covered by the sources read for this skill).
