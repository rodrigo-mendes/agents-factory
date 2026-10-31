# Always-Do — Dead-Letter Queue, Redrive and Import

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23. Names and URLs are `# example` values.

## 7. Dead-Letter Queue and Redrive

AWS rules: the DLQ must be in the same account and Region as the source, SQS does not create it
automatically, and the type must match (FIFO source with FIFO DLQ; standard with standard).
`maxReceiveCount` has a console range of 1–1,000 and an API default of 10; set it high enough for
retries. Standard queues keep the **original enqueue timestamp** in the DLQ, so give the DLQ longer
retention than the source (FIFO resets the timestamp on move). Standard queues with
`maxReceiveCount` above 3 move messages received at least 3 times without deletion to the back of
the queue. Encryption is not changed by the move ([SSE page](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html)); DLQ consumers need `kms:Decrypt` on the source
queue's key too ([key management page](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html)).

```hcl
resource "aws_sqs_queue" "orders_dlq" {
  name                      = "orders-dlq"   # example
  message_retention_seconds = 1209600        # example; 14 days, longer than the source
  sqs_managed_sse_enabled   = true
  tags                      = { Environment = "prod" } # example
}

resource "aws_sqs_queue" "orders" {
  name                    = "orders"   # example
  sqs_managed_sse_enabled = true
  tags                    = { Environment = "prod" } # example
}

resource "aws_sqs_queue_redrive_policy" "orders" {
  queue_url = aws_sqs_queue.orders.id   # source queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
    maxReceiveCount     = 5   # example; integer, not "5"
  })
}

# On the DLQ: allow only the named source queue (up to 10 ARNs)
resource "aws_sqs_queue_redrive_allow_policy" "orders_dlq" {
  queue_url = aws_sqs_queue.orders_dlq.id   # the DLQ
  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.orders.arn]
  })
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown (maxReceiveCount is an integer)
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_policy.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_allow_policy.html.markdown
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-configure-dead-letter-queue.html
```

The redrive allow policy values are `allowAll` (default, same account/Region), `denyAll` and
`byQueue`. Do not use a DLQ with FIFO if exact order must never break. Source:
https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html

## 8. Import

The import ID is the queue URL for all four resources. Identity attribute: `url` on
`aws_sqs_queue`, `queue_url` on `aws_sqs_queue_policy`, `aws_sqs_queue_redrive_policy` and
`aws_sqs_queue_redrive_allow_policy` (the `identity` block needs Terraform >= 1.12). The `import`
block needs Terraform >= 1.5.

```hcl
import {
  to = aws_sqs_queue.orders
  id = "https://queue.amazonaws.com/80398EXAMPLE/MyQueue"   # example queue URL
}
# CLI: terraform import aws_sqs_queue.orders https://queue.amazonaws.com/80398EXAMPLE/MyQueue
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_policy.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_policy.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue_redrive_allow_policy.html.markdown
```
