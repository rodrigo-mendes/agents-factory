# Never-Do — Policies and Access (Version, Public Principal, AWS Managed Key)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23. ARNs and names are `# example` values.

## 1. Queue Policy without Explicit Version

The provider page warns that AWS can hang indefinitely (`timeout while waiting`) when creating or
updating a queue with an associated `aws_sqs_queue_policy` whose `Version` is not explicitly `"2012-10-17"`.

```hcl
# WRONG — no Version in the policy document
resource "aws_sqs_queue_policy" "bad" {
  queue_url = aws_sqs_queue.events.id
  policy = jsonencode({
    Statement = [{                                  # WRONG — Version missing
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.events.arn
    }]
  })
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown

# CORRECT — explicit Version
resource "aws_sqs_queue_policy" "good" {
  queue_url = aws_sqs_queue.events.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.events.arn
      Condition = { ArnEquals = { "aws:SourceArn" = "arn:aws:sns:eu-west-1:123456789012:orders-topic" } } # example
    }]
  })
}
```

## 2. Public Principal in a Queue Policy

The AWS security best practices page says to avoid public queues (`Principal` `"*"`). Security Hub
SQS.3 (critical severity) is the control for access policies that allow public access. The WRONG
example has no restricting condition at all.

```hcl
# WRONG — wildcard principal, no condition
resource "aws_sqs_queue_policy" "public" {
  queue_url = aws_sqs_queue.events.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = "*"                   # WRONG — no restricting condition
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.events.arn
    }]
  })
}
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-security-best-practices.html
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/sqs-controls.html

# CORRECT — named service principal with a fixed source condition
resource "aws_sqs_queue_policy" "scoped" {
  queue_url = aws_sqs_queue.events.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.events.arn
      Condition = { ArnEquals = { "aws:SourceArn" = "arn:aws:sns:eu-west-1:123456789012:orders-topic" } } # example
    }]
  })
}
```

## 3. AWS Managed Key with Service Producers

The AWS managed key policy cannot be modified, so it cannot grant `sns`, `s3` or `events`
principals `kms:Decrypt` and `kms:GenerateDataKey`. AWS documents creating a customer managed key.

```hcl
# WRONG — AWS managed key on a queue that AWS services must send to
resource "aws_sqs_queue" "bad" {
  name              = "events-from-sns"        # example
  kms_master_key_id = "alias/aws/sqs"          # WRONG — key policy cannot be edited
}
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html

# CORRECT — customer managed key (key policy grants the service principal; see provisioning-aws-kms-v6)
resource "aws_sqs_queue" "good" {
  name              = "events-from-sns"        # example
  kms_master_key_id = "alias/events-queue"     # example customer managed key alias
}
```
