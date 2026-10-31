# Always-Do — Policies (Queue Policy, SNS Producer, Encrypted Queue)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23. ARNs, names and variables are `# example` values.

## 4. Queue Policy with Explicit Version

`aws_sqs_queue_policy` requires `queue_url` and `policy` (JSON); `region` is optional; no attributes
are exported. Set `Version = "2012-10-17"` explicitly: AWS can hang indefinitely
(`timeout while waiting`) when creating or updating a queue with an associated policy whose
`Version` is not explicit. The queue page recommends this resource instead of the inline `policy`
argument, and says drift for the inline argument is detected only when it is set.

```hcl
resource "aws_sqs_queue" "events" {
  name = "events"   # example
}

resource "aws_sqs_queue_policy" "events" {
  queue_url = aws_sqs_queue.events.id   # id is the queue URL
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
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown
```

The provider page also has an S3-to-SQS example with an S3 principal and explicit `Version`. AWS security best practices also say to
enforce TLS with `aws:SecureTransport` in the queue policy, to use least privilege, and to
consider VPC endpoints with endpoint or VPC conditions. Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-security-best-practices.html

Security Hub SQS.3 (critical severity) checks that access policies do not allow public access; wildcards or
variables in conditions are not evaluated as PASSED, so use fixed condition values.
Source: https://docs.aws.amazon.com/securityhub/latest/userguide/sqs-controls.html

## 5. SNS Producer Policy

Per the SNS documentation: `Principal.Service = sns.amazonaws.com`, `Action = sqs:SendMessage`,
condition `ArnEquals` on `aws:SourceArn` set to the topic ARN. Use `aws:SourceAccount` if the queue
is subscribed to multiple topics; use one statement per topic. Same-account owner subscriptions
auto-confirm; cross-account needs confirmation. The subscription itself belongs to
`provisioning-aws-sns-v6`.

```hcl
variable "topic_arn" {
  type    = string
  default = "arn:aws:sns:eu-west-1:123456789012:orders-topic" # example
}

resource "aws_sqs_queue_policy" "from_sns" {
  queue_url = aws_sqs_queue.events.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.events.arn
      Condition = { ArnEquals = { "aws:SourceArn" = var.topic_arn } }
    }]
  })
}
# Source: https://docs.aws.amazon.com/sns/latest/dg/subscribe-sqs-queue-to-sns-topic.html
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown
```

## 6. Encrypted Queue with Service Producers

For an encrypted queue that SNS, S3 or EventBridge send to: create a **customer managed** KMS key
and allow the service principal (`sns`, `s3` or `events` `.amazonaws.com`) `kms:Decrypt` and
`kms:GenerateDataKey` in the key policy (key policy lives in `provisioning-aws-kms-v6`). The AWS
managed key policy cannot be modified. Use `aws:SourceArn` or `aws:SourceAccount` in key policies
for confused-deputy protection. A queue encrypted with the AWS managed key cannot invoke a Lambda in
another account; all SSE requests need HTTPS and SigV4.

```hcl
variable "kms_key_id" {
  type    = string
  default = "alias/orders-queue"   # example: customer managed key alias
}

resource "aws_sqs_queue" "encrypted" {
  name                              = "encrypted-events"   # example
  kms_master_key_id                 = var.kms_key_id
  kms_data_key_reuse_period_seconds = 300
}
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html
```
