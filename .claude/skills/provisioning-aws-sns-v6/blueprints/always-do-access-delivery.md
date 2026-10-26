# Always-Do — Access and Delivery (Topic Policy, Subscriptions, DLQ)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23. Names, ARNs and numbers are `# example`.

## 6. Topic Policy

`aws_sns_topic_policy` requires `arn` and `policy` (full IAM policy JSON). Write a bare account
Principal as the root ARN. Avoid a `*` principal (Security Hub SNS.4 is Critical; a `*` principal with
fixed-value conditions can pass, wildcard or variable conditions are not evaluated). AWS recommends
denying `SNS:Publish` when `aws:SecureTransport` is `false`.

```hcl
data "aws_iam_policy_document" "topic" {
  statement {
    sid       = "AllowAccountPublish"
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.orders.arn]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::123456789012:root"] # example account
    }
  }
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.orders.arn]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_sns_topic_policy" "orders" {
  arn    = aws_sns_topic.orders.arn
  policy = data.aws_iam_policy_document.topic.json
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_policy.html.markdown
# Source: https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/sns-controls.html
```

## 7. SQS Subscription with a DLQ

The DLQ is an SQS queue in the same account and region as the subscription; for the DLQ, FIFO topic
subscriptions use FIFO queues and standard topic subscriptions standard queues. An encrypted DLQ needs a custom KMS key
whose policy grants the SNS service principal. Set DLQ retention to 14 days and alarm on
`ApproximateNumberOfMessagesVisible`, not `NumberOfMessagesSent`. Without a DLQ SNS discards a message
after a client-side error or after retries run out.

```hcl
# FRAGMENT: queue policies that let SNS send to the queues, the main queue
# `aws_sqs_queue.orders` and DLQ encryption are defined elsewhere: see provisioning-aws-sqs-v6.
resource "aws_sqs_queue" "dlq" {
  name                      = "orders-dlq"      # example
  message_retention_seconds = 1209600           # 14 days
}

resource "aws_sns_topic_subscription" "orders_to_queue" {
  topic_arn     = aws_sns_topic.orders.arn
  protocol      = "sqs"
  endpoint      = aws_sqs_queue.orders.arn
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
  })
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown
# Source: https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html
```

Queue and alarm resources: see `provisioning-aws-sqs-v6` and `provisioning-aws-cloudwatch-v6`.

## 8. Cross-Region or Cross-Account Subscription

The subscription must use a provider in the **topic's region**, or creation fails. Cross-account in the
same region: use the **SQS queue account's** provider, otherwise Terraform recreates it on every apply.
Cross-account and cross-region: queue account provider, topic region.

```hcl
# FRAGMENT: the queue and any topic/queue policies are defined elsewhere (see provisioning-aws-sqs-v6).
provider "aws" {
  alias  = "queue_account_topic_region"
  region = "us-east-1" # example: the topic's region
  assume_role {
    role_arn = "arn:aws:iam::210987654321:role/terraform" # example queue account
  }
}

resource "aws_sns_topic_subscription" "cross_account" {
  provider  = aws.queue_account_topic_region
  topic_arn = "arn:aws:sns:us-east-1:123456789012:orders-events" # example
  protocol  = "sqs"
  endpoint  = "arn:aws:sqs:eu-west-1:210987654321:orders"        # example, queue may be in another region
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown
```

## 9. Firehose and HTTPS Subscriptions

`subscription_role_arn` is required only for `protocol = "firehose"`. A subscription owner can
subscribe up to five Firehose streams per topic. Required role permissions are not detailed on the
page read (unverified). For HTTP(S), AWS advises domain names over raw-IP endpoints. HTTP(S)-only
arguments: `confirmation_timeout_in_minutes` (default 1), `delivery_policy` (not wrapped in `"http"`),
`endpoint_auto_confirms` (default `false`).

```hcl
resource "aws_sns_topic_subscription" "to_firehose" {
  topic_arn             = aws_sns_topic.orders.arn
  protocol              = "firehose"
  endpoint              = aws_kinesis_firehose_delivery_stream.orders.arn # placeholder: defined elsewhere
  subscription_role_arn = aws_iam_role.sns_to_firehose.arn                # placeholder: defined elsewhere
}

resource "aws_sns_topic_subscription" "to_https" {
  topic_arn = aws_sns_topic.orders.arn
  protocol  = "https"
  endpoint  = "https://hooks.example.com/sns" # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown
# Source: https://docs.aws.amazon.com/sns/latest/dg/sns-firehose-as-subscriber.html
# Source: https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html
```
