# Always-Do Patterns — Amazon SQS

> Mandatory patterns for every SQS implementation. All examples use boto3 (Python) and AWS CLI v2.
> Source: [What is Amazon SQS?](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (accessed 2026-07-31)

---

## Pattern 1 — Enable Long Polling on Every Consumer

**Why:** Short polling (default `WaitTimeSeconds = 0`) samples only a subset of servers, causing empty responses, inflated API bills, and false-empty responses. Long polling queries all servers and waits up to 20 seconds for a message.

```python
import boto3

sqs = boto3.client("sqs", region_name="us-east-1")

# ✅ Option A: enable at the queue level (applies to all receivers)
sqs.set_queue_attributes(
    QueueUrl=QUEUE_URL,
    Attributes={"ReceiveMessageWaitTimeSeconds": "20"},
)

# ✅ Option B: enable per ReceiveMessage call
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20,   # ← always set this; max is 20
)
```

Source: [Short and long polling](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html) (accessed 2026-07-31)

---

## Pattern 2 — Configure a Dead-Letter Queue with Sensible maxReceiveCount

**Why:** Isolates poison messages for debugging; stops them from cycling through the main queue indefinitely.

```bash
# Step 1: create the DLQ (same Region, same account, same queue type)
aws sqs create-queue --queue-name my-service-dlq \
  --attributes MessageRetentionPeriod=1209600   # 14 days

DLQ_ARN=$(aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/my-service-dlq \
  --attribute-names QueueArn --query Attributes.QueueArn --output text)

# Step 2: attach redrive policy to source queue
aws sqs set-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/my-service \
  --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"5\\\"}\"}"
```

Source: [Using dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31)

---

## Pattern 3 — Set DLQ Retention Longer Than Source Queue

**Why:** For Standard queues the message keeps its original enqueue timestamp when moved to the DLQ. A DLQ retention equal to or shorter than the source silently expires messages before you can inspect them.

```python
# ✅ Correct: source = 4 days, DLQ = 14 days
sqs.set_queue_attributes(
    QueueUrl=SOURCE_QUEUE_URL,
    Attributes={"MessageRetentionPeriod": str(4 * 24 * 3600)},   # 345600 s
)
sqs.set_queue_attributes(
    QueueUrl=DLQ_URL,
    Attributes={"MessageRetentionPeriod": str(14 * 24 * 3600)},  # 1209600 s
)
```

Source: [Using dead-letter queues — retention periods](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31)

---

## Pattern 4 — Match Visibility Timeout to Processing Time (Use a Heartbeat)

**Why:** A timeout shorter than actual processing time causes the message to reappear mid-processing; a second consumer picks it up, causing duplicate work. The hard cap is 12 hours from first receipt and is NOT reset by any extension call.

```python
import threading

def extend_visibility(sqs, queue_url, receipt_handle, stop_event, interval=60):
    """Heartbeat: extend visibility every `interval` seconds while processing."""
    while not stop_event.wait(interval):
        try:
            sqs.change_message_visibility(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=120,   # reset to 2 minutes from now
            )
        except Exception:
            break  # message may have been deleted or cap reached; stop gracefully

def process_with_heartbeat(sqs, queue_url, message):
    stop = threading.Event()
    t = threading.Thread(target=extend_visibility,
                         args=(sqs, queue_url, message["ReceiptHandle"], stop))
    t.start()
    try:
        do_actual_work(message)
        sqs.delete_message(QueueUrl=queue_url,
                           ReceiptHandle=message["ReceiptHandle"])
    finally:
        stop.set()
        t.join()
```

Source: [Visibility timeout — Best practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) (accessed 2026-07-31)

---

## Pattern 5 — Delete Messages Promptly After Successful Processing

**Why:** SQS never removes a message on receipt — only on `DeleteMessage`. Forgetting to delete causes reprocessing after the timeout and pushes the queue toward the ~120,000 Standard in-flight limit.

```python
# ✅ Single message
sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])

# ✅ Batch delete (up to 10 at once)
entries = [
    {"Id": str(i), "ReceiptHandle": msg["ReceiptHandle"]}
    for i, msg in enumerate(messages)
]
sqs.delete_message_batch(QueueUrl=QUEUE_URL, Entries=entries)

# ✅ Lambda: report only failed items so SQS retries only those
def lambda_handler(event, context):
    failures = []
    for record in event["Records"]:
        try:
            process(record)
        except Exception:
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
```

Source: [Message lifecycle](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (accessed 2026-07-31)

---

## Pattern 6 — Make Consumers Idempotent (Design for At-Least-Once)

**Why:** Standard queues guarantee at-least-once delivery. Even Lambda SQS event source mappings explicitly document that "duplicate processing of records can occur." Non-idempotent side effects (charging a card, inserting a row) must be guarded.

```python
import hashlib

def process_idempotent(message_body: dict, idempotency_store: dict) -> None:
    # Derive a stable key from business data, not the SQS MessageId
    key = hashlib.sha256(
        f"{message_body['order_id']}:{message_body['action']}".encode()
    ).hexdigest()

    if key in idempotency_store:
        return  # already processed — safe no-op

    # Perform the side effect
    apply_action(message_body)
    idempotency_store[key] = True  # commit key atomically with the side effect
```

Use DynamoDB with a conditional write, or a transactional DB write, as the production idempotency store.

Sources: [Welcome — Durability](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html), [Using Lambda with SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) (accessed 2026-07-31)

---

## Pattern 7 — Batch Send/Receive/Delete (Up to 10 Messages)

**Why:** A single batch handles up to 10 messages, reducing API calls and cost. For FIFO, batching multiplies per-partition throughput from ~300/s toward ~3,000/s.

```python
import uuid

# ✅ Batch send
entries = [
    {
        "Id": str(i),
        "MessageBody": json.dumps({"event": "order_created", "orderId": order_id}),
        # For FIFO: add MessageGroupId and MessageDeduplicationId
    }
    for i, order_id in enumerate(order_ids[:10])  # max 10 per call
]
response = sqs.send_message_batch(QueueUrl=QUEUE_URL, Entries=entries)

# Check for failures in the batch response
if response.get("Failed"):
    for failure in response["Failed"]:
        logger.error("Batch send failed: %s — %s", failure["Id"], failure["Message"])
```

Sources: [SQS message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html), [High throughput for FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html) (accessed 2026-07-31)

---

## Pattern 8 — Encrypt Sensitive Queues with Server-Side Encryption

**Why:** SQS supports SQS-managed SSE (baseline) and SSE-KMS with a customer-managed key (CMK) for regulated data. Pair with IAM and queue policy for least-privilege access.

```bash
# ✅ Create queue with SQS-managed SSE (baseline — free)
aws sqs create-queue --queue-name secure-queue \
  --attributes SqsManagedSseEnabled=true

# ✅ Create queue with SSE-KMS (customer-managed key — regulated data)
KMS_KEY_ID="arn:aws:kms:us-east-1:123456789012:key/mrk-xxxxxxxx"
aws sqs create-queue --queue-name regulated-queue \
  --attributes KmsMasterKeyId=$KMS_KEY_ID,KmsDataKeyReusePeriodSeconds=300
```

```json
// ✅ Minimal queue policy granting least-privilege send to a specific role
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::123456789012:role/producer-role"},
    "Action": "sqs:SendMessage",
    "Resource": "arn:aws:sqs:us-east-1:123456789012:regulated-queue"
  }]
}
```

Source: [Welcome — Security](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (accessed 2026-07-31)
