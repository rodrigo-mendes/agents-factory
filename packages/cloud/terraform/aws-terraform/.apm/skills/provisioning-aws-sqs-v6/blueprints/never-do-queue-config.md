# Never-Do — Queue Configuration (maxReceiveCount, FIFO, DLQ Rules)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23. Names are `# example` values.
Numbering continues from [never-do-policies-access](./never-do-policies-access.md).

## 4. maxReceiveCount as a String

The queue page states `maxReceiveCount` must be an integer (`5`), not a string (`"5"`).

```hcl
# WRONG — inline redrive_policy on aws_sqs_queue
resource "aws_sqs_queue" "bad" {
  name = "orders-bad"   # example
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
    maxReceiveCount     = "5"   # WRONG — string
  })
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown

# CORRECT
resource "aws_sqs_queue" "good" {
  name = "orders-good"   # example
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
    maxReceiveCount     = 5   # example; integer
  })
}
```

## 5. FIFO Name without .fifo Suffix

```hcl
# WRONG
resource "aws_sqs_queue" "bad" {
  name       = "payments"   # WRONG — FIFO names must end in .fifo
  fifo_queue = true
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sqs_queue.html.markdown

# CORRECT
resource "aws_sqs_queue" "good" {
  name       = "payments.fifo"   # example
  fifo_queue = true
}
```

## 6. perMessageGroupId without messageGroup Scope

AWS allows `perMessageGroupId` only when `DeduplicationScope = messageGroup`. High throughput is
both set; other combinations give normal throughput.

```hcl
# WRONG
resource "aws_sqs_queue" "bad" {
  name                  = "payments-ht.fifo"   # example
  fifo_queue            = true
  fifo_throughput_limit = "perMessageGroupId"  # WRONG — deduplication_scope is still "queue"
}
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html

# CORRECT
resource "aws_sqs_queue" "good" {
  name                  = "payments-ht.fifo"   # example
  fifo_queue            = true
  deduplication_scope   = "messageGroup"
  fifo_throughput_limit = "perMessageGroupId"
}
```

## 7. DLQ Type Mismatch

FIFO source queues need a FIFO DLQ; standard source queues need a standard DLQ.

```hcl
# WRONG — FIFO source, standard DLQ
resource "aws_sqs_queue" "dlq_bad" { name = "payments-dlq" }                          # example; WRONG — standard
resource "aws_sqs_queue" "src_bad" {
  name       = "payments.fifo"                                                         # example
  fifo_queue = true
  redrive_policy = jsonencode({ deadLetterTargetArn = aws_sqs_queue.dlq_bad.arn, maxReceiveCount = 5 })
}
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-configure-dead-letter-queue.html
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SetQueueAttributes.html

# CORRECT — FIFO DLQ (use a fresh source queue name in a real module)
resource "aws_sqs_queue" "dlq_good" {
  name       = "payments-dlq.fifo"   # example
  fifo_queue = true
}
resource "aws_sqs_queue" "src_good" {
  name       = "payments.fifo"   # example; no inline redrive_policy
  fifo_queue = true
}
resource "aws_sqs_queue_redrive_policy" "good" {
  queue_url = aws_sqs_queue.src_good.id
  redrive_policy = jsonencode({ deadLetterTargetArn = aws_sqs_queue.dlq_good.arn, maxReceiveCount = 5 })   # example
}
```

## 8. DLQ in Another Account or Region

The DLQ must be in the same account and Region as the source queue; SQS does not create it.

```hcl
# WRONG — DLQ ARN from another Region (and account)
resource "aws_sqs_queue_redrive_policy" "bad" {
  queue_url = aws_sqs_queue.orders.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = "arn:aws:sqs:us-east-1:210987654321:orders-dlq"   # WRONG — example ARN, other Region/account
    maxReceiveCount     = 5
  })
}
# Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html

# CORRECT — DLQ created in the same account and Region
resource "aws_sqs_queue" "orders_dlq" { name = "orders-dlq" }   # example
resource "aws_sqs_queue_redrive_policy" "good" {
  queue_url = aws_sqs_queue.orders.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
    maxReceiveCount     = 5   # example
  })
}
```
