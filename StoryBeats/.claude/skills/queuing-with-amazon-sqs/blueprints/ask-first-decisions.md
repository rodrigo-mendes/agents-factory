# Ask-First Decisions — Amazon SQS

> Architectural crossroads that require explicit confirmation before implementation.
> Present the trade-off matrix, ask the question, and wait for the architect's answer.

---

## Decision 1 — Standard vs FIFO Queue

| Dimension | Standard | FIFO |
|---|---|---|
| Delivery | At-least-once (duplicates possible) | Exactly-once processing |
| Ordering | Best-effort | Strict FIFO within a message group |
| Throughput | Nearly unlimited API calls/sec | 300 TPS / 3,000/s batched per partition |
| Required attrs | None | `MessageGroupId`; `MessageDeduplicationId` or content-based dedup |
| Cost | Lower | Slightly higher |
| Best when | High volume, order-tolerant, idempotent consumers | Payments, sequential state machines, compliance-grade ordering |

**Ask the architect:**
> "Is strict ordering or exactly-once processing a *correctness* requirement, or can the consumer be made idempotent and tolerate best-effort ordering? What peak TPS must the queue sustain?"

If idempotency is achievable → Standard (simpler, cheaper, scales higher).
If ordering or dedup must be guaranteed → FIFO (requires `MessageGroupId` on every send).

```python
# FIFO: required attributes
sqs.send_message(
    QueueUrl=FIFO_QUEUE_URL,
    MessageBody=json.dumps(event),
    MessageGroupId="order-123",           # groups related messages for FIFO ordering
    MessageDeduplicationId=str(uuid.uuid4()),  # or enable content-based dedup on the queue
)
```

Sources: [Welcome](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html), [SQS message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html), [High throughput FIFO](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html) (accessed 2026-07-31)

---

## Decision 2 — Fan-Out: SNS→SQS vs Single SQS Queue

| Option | Delivers to | Use when |
|---|---|---|
| **Single SQS queue** | One consumer fleet | Exactly one worker fleet processes each event |
| **SNS topic → SQS queues** | Many independent subscribers | Multiple services each need their own durable copy |

SQS alone delivers each message to **one** consumer. If multiple independent services must each receive a copy, add an SNS topic: each subscriber gets its own SQS queue, which buffers messages if the service is offline.

**Ask the architect:**
> "Does exactly one worker fleet consume this event (plain SQS), or must several independent services each receive their own copy (SNS→SQS fanout)?"

```bash
# Fanout setup: SNS topic with two SQS subscribers
aws sns create-topic --name my-events
aws sqs create-queue --queue-name service-a-queue
aws sqs create-queue --queue-name service-b-queue

# Subscribe each queue to the topic
aws sns subscribe --topic-arn <TOPIC_ARN> --protocol sqs \
  --notification-endpoint <SERVICE_A_QUEUE_ARN>
aws sns subscribe --topic-arn <TOPIC_ARN> --protocol sqs \
  --notification-endpoint <SERVICE_B_QUEUE_ARN>
# Each queue now receives an independent copy of every SNS message.
```

Source: [Welcome — SQS vs SNS vs MQ and fanout pattern](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (accessed 2026-07-31)

---

## Decision 3 — Payloads Larger Than 1 MiB

| Option | Max size | Trade-off | Constraint |
|---|---|---|---|
| **Inline** | 1,048,576 bytes | Simplest; no extra service | Must fit under 1 MiB |
| **Extended Client Library** | 2 GB | Adds S3 dependency | Sync clients only (Java / Python) |
| **Split into smaller messages** | No hard limit | App-level reassembly complexity | Payload must be naturally divisible |

**Ask the architect:**
> "What is the realistic maximum payload size? If it can exceed 1 MiB, do we offload to S3 via the Extended Client Library, or split messages — and can we accept the sync-only limitation of the Extended Client?"

```python
# Extended Client Library (Python — pip install amazon-sqs-python-extended-client-lib)
import boto3
from amazon_sqs_extended_client import SQSExtendedClientSession

session = SQSExtendedClientSession()
sqs = session.client("sqs", region_name="us-east-1")

# Configure to always store in S3 when payload > threshold
sqs.large_payload_support = S3_BUCKET_NAME
sqs.always_through_s3 = False          # True = always use S3 regardless of size
sqs.message_size_threshold = 1_048_576  # only offload when > 1 MiB

sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=large_json_string)
# SQS message contains an S3 pointer; receiving side fetches body from S3 transparently.
```

Source: [SQS message quotas — Message size](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html) (accessed 2026-07-31)

---

## Decision 4 — Lambda ESM: On-Demand vs Provisioned Pollers

| Dimension | On-demand (default) | Provisioned mode |
|---|---|---|
| Initial concurrency | 5 concurrent invokes | Configurable MinimumPollers (2–200, default 2) |
| Scale-up rate | +300 concurrency/min | 3× faster; up to +1,000 concurrency/min |
| Max concurrency | 1,250 (account quota gated) | Up to 20,000 concurrent invocations |
| Scale to zero | Yes | No (MinimumPollers always active) |
| Cost | Lower; pay per invocation | Higher; pollers charged continuously |
| Mutually exclusive with | Nothing | `MaximumConcurrency` setting |
| Best when | Most workloads; bursty-but-latency-tolerant | Strict low-latency SLAs; spiky high-volume traffic |

**Ask the architect:**
> "Does this consumer have a strict latency SLA with spiky traffic that justifies paying for provisioned pollers, or is default on-demand scaling sufficient? Do we need a `MaximumConcurrency` cap to protect other functions' concurrency headroom?"

```bash
# Enable provisioned mode on an existing ESM
aws lambda update-event-source-mapping \
  --uuid <ESM_UUID> \
  --metrics-config '{"Metrics":["EventCount"]}' \
  --provisioned-poller-config '{"MinimumPollers":10,"MaximumPollers":200}'

# Enable maximum concurrency (mutually exclusive with provisioned mode)
aws lambda update-event-source-mapping \
  --uuid <ESM_UUID> \
  --scaling-config '{"MaximumConcurrency":100}'
```

Sources: [Configuring scaling for SQS ESM](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html), [Using Lambda with SQS — provisioned mode](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) (accessed 2026-07-31)

---

## Decision 5 — DLQ maxReceiveCount and Retention Period

These two values are coupled correctness decisions and must be chosen together.

| Parameter | Too low | Too high |
|---|---|---|
| `maxReceiveCount` | Single transient error dead-letters a good message | Poison messages cycle too long before quarantine |
| DLQ retention | Failed messages expire before inspection | Storage cost; not a real risk in practice |

**Guidance**:
- `maxReceiveCount`: 3–10 is typical; match to how many transient-failure retries are tolerable for the workload.
- DLQ retention: always set to **14 days** (max) for production unless there is a specific compliance reason to shorten.
- DLQ retention must be **strictly longer** than the source queue's retention.

**Ask the architect:**
> "How many transient retries should a message get before it is quarantined (maxReceiveCount)? How long must failed messages remain inspectable in the DLQ, and what is the source queue's retention so we can ensure the DLQ is longer?"

```python
# Set both values explicitly when creating the queue
import json

source_retention = 345600   # 4 days in seconds
dlq_retention = 1209600     # 14 days in seconds — always longer than source

sqs.create_queue(
    QueueName="my-service-dlq",
    Attributes={"MessageRetentionPeriod": str(dlq_retention)},
)
sqs.create_queue(
    QueueName="my-service",
    Attributes={
        "MessageRetentionPeriod": str(source_retention),
        "RedrivePolicy": json.dumps({
            "deadLetterTargetArn": DLQ_ARN,
            "maxReceiveCount": 5,   # confirm with architect
        }),
        "VisibilityTimeout": "120",
        "ReceiveMessageWaitTimeSeconds": "20",
    },
)
```

Source: [Using dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31)
