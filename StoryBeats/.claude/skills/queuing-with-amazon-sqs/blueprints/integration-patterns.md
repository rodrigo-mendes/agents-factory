# Integration Patterns — Amazon SQS

> Complete integration examples for SQS with Lambda, SNS, and S3 (Extended Client).

---

## SQS ↔ Lambda (Event Source Mapping)

**Official Library**: `boto3` (AWS SDK) + Lambda event source mapping (managed by AWS)
**Compatibility**: Lambda runtime any version; SQS Standard and FIFO

Lambda polls the SQS queue on your behalf. You do not call `ReceiveMessage` or `DeleteMessage` manually — Lambda handles polling and deletion of successfully processed messages.

```python
# Lambda function — SQS consumer with partial batch failure reporting
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Processes a batch of SQS messages.
    Returns failed message IDs so Lambda retries only those (not the full batch).
    Requires: FunctionResponseTypes = ["ReportBatchItemFailures"] on the ESM.
    """
    batch_failures = []

    for record in event["Records"]:
        message_id = record["messageId"]
        try:
            body = json.loads(record["body"])
            process_event(body)
            logger.info("Processed message %s", message_id)
        except Exception as exc:
            logger.error("Failed message %s: %s", message_id, exc)
            batch_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_failures}


def process_event(body: dict) -> None:
    # Your business logic here — must be idempotent
    pass
```

```bash
# Create ESM with recommended settings
aws lambda create-event-source-mapping \
  --function-name my-consumer \
  --event-source-arn <QUEUE_ARN> \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5 \
  --function-response-types ReportBatchItemFailures
```

**Required configuration**:
- Lambda `Timeout` must be set to match or exceed the queue's `VisibilityTimeout`; otherwise Lambda times out and SQS re-delivers the batch
- Lambda function and SQS queue must be in the **same Region** (cross-account is allowed)
- Enable `ReportBatchItemFailures` to avoid retrying successfully processed messages in a partial-failure batch

**Common issues**:
- **Lambda does not scale fast enough** → Enable provisioned pollers (see [Ask-First Decisions](./ask-first-decisions.md) — Decision 4)
- **All messages in batch retried after one failure** → `FunctionResponseTypes = ["ReportBatchItemFailures"]` is missing on the ESM
- **Messages loop forever in the queue** → DLQ is not configured; add a redrive policy with `maxReceiveCount` ≥ 5

Sources: [Using Lambda with Amazon SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html), [Configuring scaling](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html) (accessed 2026-07-31)

---

## SQS ↔ SNS (Fan-Out)

**Pattern**: One SNS topic → multiple SQS queues; each queue receives an independent durable copy.

**When to use**: Multiple independent services each need to react to the same event (e.g., order_created → inventory, billing, notifications each get their own copy and process independently).

```bash
# Step 1: create SNS topic and SQS queues
TOPIC_ARN=$(aws sns create-topic --name order-events --query TopicArn --output text)

aws sqs create-queue --queue-name inventory-queue
aws sqs create-queue --queue-name billing-queue
aws sqs create-queue --queue-name notifications-queue

# Step 2: allow SNS to send to each SQS queue
for QUEUE in inventory-queue billing-queue notifications-queue; do
  QUEUE_URL=$(aws sqs get-queue-url --queue-name $QUEUE --query QueueUrl --output text)
  QUEUE_ARN=$(aws sqs get-queue-attributes --queue-url $QUEUE_URL \
    --attribute-names QueueArn --query Attributes.QueueArn --output text)

  aws sqs set-queue-attributes --queue-url $QUEUE_URL --attributes "{
    \"Policy\": \"{\\\"Version\\\":\\\"2012-10-17\\\",\\\"Statement\\\":[{
      \\\"Effect\\\":\\\"Allow\\\",
      \\\"Principal\\\":{\\\"Service\\\":\\\"sns.amazonaws.com\\\"},
      \\\"Action\\\":\\\"sqs:SendMessage\\\",
      \\\"Resource\\\":\\\"$QUEUE_ARN\\\",
      \\\"Condition\\\":{\\\"ArnEquals\\\":{\\\"aws:SourceArn\\\":\\\"$TOPIC_ARN\\\"}}}]}\"
  }"

  # Step 3: subscribe queue to SNS topic
  aws sns subscribe --topic-arn $TOPIC_ARN --protocol sqs --notification-endpoint $QUEUE_ARN
done

# Step 4: publish — all three queues receive a copy
aws sns publish --topic-arn $TOPIC_ARN \
  --message '{"event":"order_created","orderId":"ord-001"}'
```

**FIFO fan-out**: use a FIFO SNS topic (`--attributes FifoTopic=true`) with FIFO SQS queues; queue names must end in `.fifo`.

**Common issues**:
- **Queue does not receive SNS messages** → Queue policy is missing the `sqs:SendMessage` allow for `sns.amazonaws.com`; add the policy before subscribing
- **Raw message vs SNS envelope** → By default, SQS receives the full SNS JSON envelope; enable `RawMessageDelivery` on the subscription if consumers expect the plain message body

Source: [Welcome — fanout pattern](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (accessed 2026-07-31)

---

## SQS ↔ S3 (Extended Client — Payloads > 1 MiB)

**When to use**: Payloads that exceed 1,048,576 bytes (the inline SQS limit). The Extended Client stores the body in S3 and puts a reference pointer in the SQS message; the receiving side fetches the body transparently.

**Constraint**: sync clients only (not compatible with async frameworks or SQS-managed polling in Lambda ESM without custom receive-side logic).

```bash
pip install amazon-sqs-python-extended-client-lib
```

```python
import boto3
from amazon_sqs_extended_client import SQSExtendedClientSession

# Producer side
session = SQSExtendedClientSession()
producer = session.client("sqs", region_name="us-east-1")
producer.large_payload_support = "my-sqs-payloads-bucket"
producer.message_size_threshold = 1_048_576   # use S3 only when body exceeds 1 MiB
producer.always_through_s3 = False

large_body = generate_large_payload()   # > 1 MiB
producer.send_message(QueueUrl=QUEUE_URL, MessageBody=large_body)
# → SQS message contains: {"s3BucketName":"my-sqs-payloads-bucket","s3Key":"<uuid>"}

# Consumer side — extended client fetches from S3 transparently
consumer = session.client("sqs", region_name="us-east-1")
consumer.large_payload_support = "my-sqs-payloads-bucket"

response = consumer.receive_message(QueueUrl=QUEUE_URL, WaitTimeSeconds=20)
for msg in response.get("Messages", []):
    body = msg["Body"]   # ← already fetched and decoded from S3
    process(body)
    consumer.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])
```

**Required S3 configuration**:
```bash
# Bucket must be in the same Region as the SQS queue
aws s3 mb s3://my-sqs-payloads-bucket --region us-east-1

# Apply lifecycle rule to expire old payloads (match message retention)
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-sqs-payloads-bucket \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "expire-sqs-payloads",
      "Status": "Enabled",
      "Filter": {"Prefix": ""},
      "Expiration": {"Days": 14}
    }]
  }'
```

**Common issues**:
- **Consumer receives pointer JSON instead of body** → Consumer side does not use the Extended Client; configure `large_payload_support` on the consumer too
- **S3 objects accumulate without expiry** → Add an S3 lifecycle rule matching the DLQ retention (14 days); objects are not auto-deleted when the SQS message is deleted

Source: [SQS message quotas — Message size](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html) (accessed 2026-07-31)
