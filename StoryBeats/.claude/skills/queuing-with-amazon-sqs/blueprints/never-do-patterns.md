# Never-Do Patterns — Amazon SQS

> 10 anti-patterns with wrong code and correct alternatives. Each item traces to an official AWS source.

---

## Anti-pattern 1 — Short Polling in a Busy Consumer Loop

```python
# 🚫 WRONG: tight loop with short polling
while True:
    response = sqs.receive_message(QueueUrl=QUEUE_URL)  # WaitTimeSeconds defaults to 0
    for msg in response.get("Messages", []):
        process(msg)
    # Result: many empty responses, inflated bill, false-empty responses

# ✅ CORRECT: long polling — queries all servers, waits up to 20 s
while True:
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        WaitTimeSeconds=20,        # ← required
        MaxNumberOfMessages=10,
    )
    for msg in response.get("Messages", []):
        process(msg)
```

Source: [Short and long polling](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html) (accessed 2026-07-31)

---

## Anti-pattern 2 — Assuming Exactly-Once on a Standard Queue

```python
# 🚫 WRONG: non-idempotent side effect assuming single delivery
def handle(message):
    charge_card(message["card_token"], message["amount"])   # duplicate charge if redelivered

# ✅ CORRECT: guard with an idempotency key
def handle(message):
    key = f"charge:{message['order_id']}"
    if not idempotency_store.exists(key):
        charge_card(message["card_token"], message["amount"])
        idempotency_store.set(key, ttl=86400)
```

Standard queues guarantee at-least-once delivery with best-effort ordering. Duplicates are normal, not an edge case.
Source: [Welcome — Durability](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (accessed 2026-07-31)

---

## Anti-pattern 3 — Visibility Timeout Shorter Than Processing Time

```python
# 🚫 WRONG: 30-second default timeout for a job that takes 5 minutes
#   → message becomes visible again at t=30s; second consumer picks it up
sqs.receive_message(QueueUrl=QUEUE_URL)   # VisibilityTimeout defaults to queue setting (30 s)
do_five_minute_job(message)               # redelivered to another consumer at second 31

# ✅ CORRECT: set timeout to match actual processing time + buffer
sqs.change_message_visibility(
    QueueUrl=QUEUE_URL,
    ReceiptHandle=message["ReceiptHandle"],
    VisibilityTimeout=600,   # 10 minutes; extend further with heartbeat if needed
)
```

Source: [Visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) (accessed 2026-07-31)

---

## Anti-pattern 4 — Expecting to Extend Beyond the 12-Hour Hard Cap

```python
# 🚫 WRONG: loop that tries to hold the message invisible for days
while still_processing:
    sqs.change_message_visibility(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=receipt_handle,
        VisibilityTimeout=43200,   # 12 hours, but clock started at first receipt
    )
    time.sleep(40000)   # this call will fail: cap already reached

# ✅ CORRECT: break long work into shorter tasks or use Step Functions
# For work exceeding 12 hours, use AWS Step Functions with SQS tasks,
# or split the job so each SQS message covers ≤ 12 hours of processing.
```

The 12-hour ceiling is measured from first receipt and is never reset by extension calls.
Source: [Visibility timeout — Best practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) (accessed 2026-07-31)

---

## Anti-pattern 5 — Forgetting DeleteMessage / Ignoring the In-Flight Limit

```python
# 🚫 WRONG: process but never delete
def bad_consumer():
    response = sqs.receive_message(QueueUrl=QUEUE_URL, WaitTimeSeconds=20)
    for msg in response.get("Messages", []):
        process(msg)
    # No DeleteMessage → message reappears after VisibilityTimeout
    # In-flight count grows toward ~120,000; OverLimit blocks future receives

# ✅ CORRECT: always delete on success; use batch delete for throughput
def good_consumer():
    response = sqs.receive_message(QueueUrl=QUEUE_URL, WaitTimeSeconds=20,
                                   MaxNumberOfMessages=10)
    for msg in response.get("Messages", []):
        process(msg)
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])
```

Monitor `ApproximateNumberOfMessagesNotVisible` in CloudWatch to detect accumulation.
Sources: [Message lifecycle](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html), [Visibility timeout — in-flight](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) (accessed 2026-07-31)

---

## Anti-pattern 6 — maxReceiveCount = 1 (No Retry Tolerance)

```json
// 🚫 WRONG: single receive attempt before dead-lettering
{
  "deadLetterTargetArn": "arn:aws:sqs:...:my-dlq",
  "maxReceiveCount": "1"
}
// One transient network hiccup sends the message to the DLQ permanently.

// ✅ CORRECT: allow several attempts to absorb transient errors
{
  "deadLetterTargetArn": "arn:aws:sqs:...:my-dlq",
  "maxReceiveCount": "5"
}
// 5 attempts filter transient failures while still catching genuinely bad messages.
```

Source: [Using dead-letter queues — redrive policy](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31)

---

## Anti-pattern 7 — DLQ on a FIFO Queue When Ordering Is a Correctness Requirement

```
# 🚫 WRONG: FIFO queue (ordered video edit events) + DLQ enabled
# A failed "Cut at frame 500" event is moved to DLQ.
# The next event "Dissolve at frame 500" is processed out of context.
# The edit timeline is now corrupt.

# ✅ CORRECT options when ordering matters:
# Option A: retry in place (ChangeMessageVisibility to 0 for immediate retry)
# Option B: redesign so out-of-order handling is safe (idempotent sequence numbers)
# Option C: only use a DLQ when downstream can tolerate gaps in the FIFO sequence
```

Per AWS documentation: do not use a DLQ with a FIFO queue if reordering changes the meaning of the events.
Source: [Using dead-letter queues — Note on FIFO](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31)

---

## Anti-pattern 8 — DLQ Retention Equal to or Shorter Than Source Queue

```python
# 🚫 WRONG: source = 4 days, DLQ = 4 days
# A message enqueued at t=0 fails once (moved to DLQ at t=1 day).
# DLQ retention starts from original enqueue time (t=0).
# Message expires from DLQ at t=4 days → only 3 days to inspect.

# ✅ CORRECT: DLQ retention strictly longer than source
sqs.set_queue_attributes(
    QueueUrl=SOURCE_URL,
    Attributes={"MessageRetentionPeriod": "345600"},   # 4 days
)
sqs.set_queue_attributes(
    QueueUrl=DLQ_URL,
    Attributes={"MessageRetentionPeriod": "1209600"},  # 14 days (max)
)
```

Source: [Using dead-letter queues — retention periods](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31)

---

## Anti-pattern 9 — Payload > 1 MiB Sent Inline (or Still Assuming 256 KiB Cap)

```python
# 🚫 WRONG: attempt to send 2 MiB body directly
sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody=two_mib_json_string,  # raises InvalidParameterValue; max is 1,048,576 bytes
)

# 🚫 ALSO WRONG (stale pattern): artificially cap at 256 KiB
if len(body) > 256 * 1024:  # old limit; stale since 2025-08-04
    offload_to_s3()

# ✅ CORRECT: use inline for ≤ 1 MiB; Extended Client for larger payloads
if len(body.encode()) <= 1_048_576:
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=body)
else:
    # Use amazon-sqs-java-extended-client-lib or sqs-extended-client (Python)
    # Stores body in S3, puts pointer in SQS message; up to 2 GB; sync clients only
    extended_client.send_message(QueueUrl=QUEUE_URL, MessageBody=body)
```

Sources: [SQS message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html), [1 MiB payload announcement (2025-08-04)](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib) (accessed 2026-07-31)

---

## Anti-pattern 10 — DLQ or Lambda Consumer in a Different Region Than the Source Queue

```
# 🚫 WRONG: DLQ in eu-west-1 for a source queue in us-east-1
# → AWS rejects the redrive policy; cross-Region DLQ is not supported.

# 🚫 WRONG: Lambda function in eu-west-1 with event source mapping to SQS in us-east-1
# → Cross-Region Lambda ESM is not supported.

# ✅ CORRECT:
# - DLQ: same account + same Region + same queue type as source
# - Lambda ESM: Lambda function in the SAME Region as the SQS queue
# - Cross-account Lambda ESM: allowed (same Region required)
```

Sources: [Using dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html), [Using Lambda with SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) (accessed 2026-07-31)
