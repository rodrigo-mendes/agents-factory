# Always-Do — Queues (Terraform Block, Encryption, Tags, FIFO)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23. Names, tags and sizes are `# example` values.

## 1. Terraform Block and Standard Queue

All `aws_sqs_queue` arguments are optional. Documented defaults: `visibility_timeout_seconds` 30,
`message_retention_seconds` 345,600, `delay_seconds` 0, `receive_wait_time_seconds` 0 (short polling).

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}

resource "aws_sqs_queue" "orders" {
  name                       = "orders"   # example
  visibility_timeout_seconds = 30         # example; provider default is 30
  message_retention_seconds  = 345600     # example; default 4 days, max 1,209,600
  receive_wait_time_seconds  = 20         # example; range 0-20, default 0
  max_message_size           = 262144     # example; set explicitly (docs disagree on default) (medium confidence)
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown
```

Changing `message_retention_seconds` can take up to 15 minutes on the AWS side and reducing it can
expire existing messages. Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html

## 2. Encryption and Tags

Security Hub SQS.1 (medium severity) checks that queues are encrypted with SSE-SQS or SSE-KMS; SQS.2 (low severity)
checks that queues carry the configured `requiredTagKeys`. Each queue below uses **one** encryption
option. SSE encrypts the message body only, not queue metadata, message metadata or metrics.

```hcl
# SSE-SQS
resource "aws_sqs_queue" "sse_sqs" {
  name                    = "orders-sse-sqs"   # example
  sqs_managed_sse_enabled = true
  tags = {
    Environment = "prod"   # example
    Owner       = "team-a" # example
  }
}

# SSE-KMS with the AWS managed key
resource "aws_sqs_queue" "sse_kms" {
  name                              = "orders-sse-kms"   # example
  kms_master_key_id                 = "alias/aws/sqs"
  kms_data_key_reuse_period_seconds = 300                # default 300, range 60-86,400
  tags                              = { Environment = "prod" } # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/sqs-controls.html
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html
```

With provider `default_tags`, keys matching resource `tags` are overridden by the resource; `tags_all` is exported.
Messages already in the backlog are not encrypted retroactively. Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html

Producers need `kms:Decrypt` and `kms:GenerateDataKey`; consumers need `kms:Decrypt`. Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html

## 3. FIFO Queue

FIFO names must end in `.fifo`. `content_based_deduplication` is FIFO only and hashes the message
body with SHA-256 (not attributes); an explicit `MessageDeduplicationId` overrides it; without
either, the send fails.

```hcl
resource "aws_sqs_queue" "payments" {
  name                        = "payments.fifo"   # example
  fifo_queue                  = true
  content_based_deduplication = true
}

# High-throughput FIFO: both settings together
resource "aws_sqs_queue" "payments_ht" {
  name                        = "payments-ht.fifo"   # example
  fifo_queue                  = true
  content_based_deduplication = true
  deduplication_scope         = "messageGroup"       # default "queue"
  fifo_throughput_limit       = "perMessageGroupId"  # default "perQueue"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html
```

High throughput applies per partition (up to 3,000 messages/s with batching or 300 messages/s per
operation); use many distinct message group IDs. Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html
