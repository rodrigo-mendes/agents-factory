# Never-Do — Access and KMS (Principals, Keys, Archive Destroy)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23. Names and ARNs are `# example`.

## 1. Bare Account ID as Principal

If a Principal is a bare account ID, AWS converts it to the root ARN and later plans show a diff.

```hcl
# WRONG — bare account ID
data "aws_iam_policy_document" "bad" {
  statement {
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.orders.arn]
    principals {
      type        = "AWS"
      identifiers = ["123456789012"] # WRONG — example account, converted by AWS
    }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_policy.html.markdown

# CORRECT — root ARN
#   identifiers = ["arn:aws:iam::123456789012:root"] # example
```

## 2. AWS Managed Key for AWS Service Publishers

To let AWS event sources publish to an encrypted topic, AWS says to use a customer managed key and
grant the service principal in its key policy.

```hcl
# WRONG — AWS-managed alias for a topic that CloudWatch/EventBridge publish to
resource "aws_sns_topic" "alerts_bad" {
  name              = "alerts"         # example
  kms_master_key_id = "alias/aws/sns"  # WRONG for AWS service event sources
}
# Source: https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html

# CORRECT — customer managed key with the service principal in its key policy
resource "aws_sns_topic" "alerts" {
  name              = "alerts" # example
  kms_master_key_id = aws_kms_key.sns.id
}
```

## 3. SourceAccount and SourceArn Conditions for EventBridge

`aws:SourceAccount`, `aws:SourceArn` and `aws:SourceOrgID` in the KMS key policy are not supported for
EventBridge publishing to encrypted topics.

```hcl
# WRONG — source condition on the EventBridge statement
data "aws_iam_policy_document" "key_bad" {
  statement {
    actions   = ["kms:GenerateDataKey*", "kms:Decrypt"]
    resources = ["*"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    condition {                       # WRONG — not supported for EventBridge
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = ["123456789012"]     # example
    }
  }
}
# Source: https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html

# CORRECT — same statement without the condition block
```

EventBridge rules and targets: see `provisioning-aws-eventbridge-v6`.

## 4. Destroying a Topic with an Active Archive Policy

AWS: a topic with an active archive policy cannot be deleted, so deactivate the policy first.
(How to deactivate it from Terraform is an Ask First item in SKILL.md, since AWS says `{}` also deletes the archive.)

```hcl
# WRONG — archive active, then terraform destroy
resource "aws_sns_topic" "archived" {
  name           = "orders-events.fifo" # example
  fifo_topic     = true
  archive_policy = jsonencode({ MessageRetentionPeriod = "30" }) # example
}
# Source: https://docs.aws.amazon.com/sns/latest/dg/message-archiving-and-replay-topic-owner.html

# CORRECT — deactivate the archive policy first (confirm the plan; the archive may be deleted), then destroy
```
