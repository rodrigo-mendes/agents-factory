---
tech: Amazon SQS
category: aws-messaging
depth: standard
pinned-to: GA 2026-07
generated: 2026-07-31
skill-anti-hallucination: true
---

# Research: Amazon SQS (Simple Queue Service) — current GA edition (2026-07)

## Metadata

```yaml
Full_Name: "Amazon Simple Queue Service (Amazon SQS)"
Cloud_Provider: "AWS"
Architecture_Domain: "Messaging / Queueing (asynchronous decoupling)"
Target_Edition: "SQS current GA feature set (2026-07) — SQS has no numbered versions; it is a continuously-updated managed service"
Access_Date: "2026-07-31"
Primary_Source_URL: "https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html"
Primary_Audience: "Cloud Architects and Tech Leads"
Currency_Threshold: "2027-07-31 (re-verify after this date; SQS quotas/limits evolve — the 256 KiB→1 MiB change landed 2025-08)"
Confidence: "High — every claim below traces to an official AWS URL fetched 2026-07-31"
```

---

## 1. Overview & Version Pinning

Amazon SQS is AWS's fully managed message-queue service that lets you decouple and scale distributed
software components. Producers send messages to a queue; consumers poll and process them
independently, so a slow or failed consumer never blocks a producer. SQS stores every message
redundantly across multiple servers for durability and provides a generic web-services API reachable
from any AWS SDK. Source: [What is Amazon SQS?](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (accessed 2026-07-31).

**Version pinning.** SQS is a managed service with **no numbered/semantic version** — there is one
continuously-updated GA service. "Version absolutism" here means pinning to the **current documented
quotas and behaviors as of the access date 2026-07-31**, because these values change over time. The
most significant recent change: on **2025-08-04** AWS raised the maximum message payload from
**256 KiB to 1 MiB (1,048,576 bytes)** across all AWS commercial Regions and AWS GovCloud (US), for
**both Standard and FIFO queues**. Any pattern that still assumes a 256 KiB ceiling is now stale.
Source: [Amazon SQS increases max payload to 1 MiB](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib) (2025-08-04, accessed 2026-07-31).

**Current pinned quotas (accessed 2026-07-31), all from [SQS message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html):**

| Attribute | Value |
|---|---|
| Message size | min 1 byte, **max 1,048,576 bytes (1 MiB)** |
| Message retention | default **4 days**; min **60 seconds**; max **1,209,600 seconds (14 days)** |
| Visibility timeout | default **30 seconds**; min **0**; max **12 hours** |
| Delay (delay queue / message timer) | default/min **0 seconds**; max **15 minutes** |
| Long-poll wait (`WaitTimeSeconds`) | max **20 seconds** |
| Batch request size | max **10 messages** per batch API call |
| Message metadata attributes | up to **10** per message |
| In-flight messages (Standard) | ~**120,000** (returns `OverLimit` on short polling) |
| Queue policy | max **8,192 bytes**, 20 statements, 50 principals, 10 conditions |

To send payloads larger than 1 MiB, use the **Amazon SQS Extended Client Library** (Java / Python),
which stores the body in Amazon S3 (up to 2 GB) and keeps a pointer in the SQS message; the extended
library works only for synchronous clients. Source: [SQS message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html) (accessed 2026-07-31).

---

## 2. Core Concepts & Architecture

### Distributed-queue model and message lifecycle

A distributed SQS system has three parts: **producers**, the **queue** (distributed redundantly across
SQS servers), and the **messages**. Lifecycle (source: [Welcome → Message lifecycle](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html), accessed 2026-07-31):

1. A producer sends a message; SQS stores it redundantly across multiple servers.
2. A consumer receives the message. While it is being processed the message **remains in the queue**
   but is hidden from other consumers for the duration of the **visibility timeout**.
3. The consumer **explicitly deletes** the message (via `DeleteMessage`) so it is not processed again
   after the visibility timeout expires. If it is not deleted in time, it becomes visible again.

SQS automatically deletes messages older than the queue's retention period (default 4 days).

### Queue types — Standard vs FIFO

| Dimension | Standard queue | FIFO queue |
|---|---|---|
| Delivery guarantee | **At-least-once** (duplicates possible) | **Exactly-once processing** |
| Ordering | **Best-effort** ordering | **Strict FIFO** within a message group |
| Throughput | **Very high, nearly unlimited** API calls/sec per action | **300 TPS** non-batched / **3,000/sec** with batching per partition; higher with high-throughput mode |
| Required attributes | none | `MessageGroupId` required; `MessageDeduplicationId` (or content-based dedup) |

Sources: [Welcome — Durability](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html), [SQS message quotas — Message throughput](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html), [High throughput for FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html) (all accessed 2026-07-31).

**FIFO throughput detail:** "Each partition supports up to 3,000 messages per second with batching,
or up to 300 messages per second for send, receive, and delete operations in supported regions."
Throughput scales with the number of distinct `MessageGroupId` values, so AWS recommends message group
IDs with a large number of distinct values. Source: [High throughput for FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html) (accessed 2026-07-31).

### Visibility timeout

When a consumer receives a message it stays in the queue but becomes temporarily invisible to other
consumers. Default **30 seconds**, min **0**, max **12 hours**. Use `ChangeMessageVisibility` to extend
or shorten it per message; setting it to `0` returns the message to the queue immediately. The **12-hour
cap is measured from first receipt and is NOT reset by extending** — if you need longer, use AWS Step
Functions or split the work. Because SQS is at-least-once, the visibility timeout prevents *concurrent*
duplicate processing but does not guarantee a message is delivered only once. Source: [Visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) (accessed 2026-07-31).

### Dead-letter queues (DLQ)

A DLQ is a **separate queue** that a source queue targets for messages that fail processing repeatedly,
so you can isolate and debug them. Configured via a **redrive policy** with a `maxReceiveCount`: the
number of times a consumer may receive a message before SQS moves it to the DLQ. The DLQ **must be in
the same AWS account and Region** as the source queue and (per AWS guidance) the **same queue type**
(FIFO source → FIFO DLQ, Standard → Standard). A **redrive allow policy** controls which source queues
may use the DLQ (allow all / up to 10 named `byQueue` / `denyAll`). Best practice: set the DLQ retention
period **longer** than the source queue's, because for Standard queues the message keeps its original
enqueue timestamp when moved. Source: [Using dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31).

### Long polling vs short polling

- **Short polling (default):** `ReceiveMessage` samples a subset of servers and returns immediately,
  even with no messages — causing empty responses and wasted API calls.
- **Long polling:** set `WaitTimeSeconds > 0` (**max 20 seconds**). SQS queries all servers and waits
  until at least one message is available (or the wait expires), reducing empty responses, reducing
  false-empty responses, and lowering cost. Enable per-request via `WaitTimeSeconds` or per-queue via
  the `ReceiveMessageWaitTimeSeconds` attribute.

Source: [SQS short and long polling](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html) (accessed 2026-07-31).

### Delay queues

Delay queues postpone delivery of **new** messages for a set period: default/min **0 seconds**, max
**15 minutes**. Difference from visibility timeout: a delay hides a message **when first added** to the
queue, whereas visibility timeout hides it **after it is received**. Per-queue delay is **not
retroactive for Standard** queues but **is retroactive for FIFO** queues. To delay individual messages
rather than the whole queue, use **message timers** (`DelaySeconds` on `SendMessage`). For scheduling
beyond 15 minutes, AWS recommends EventBridge Scheduler. Source: [SQS delay queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-delay-queues.html) (accessed 2026-07-31).

---

## 3. ✅ Always-Do Patterns

### ✅ Pattern 1 — Enable long polling on every consumer

**Why:** reduces empty responses, false-empty responses, and API cost; queries all servers.

```text
❌ Wrong: ReceiveMessage with WaitTimeSeconds = 0 (short polling) in a tight loop → empty responses, higher cost.
✅ Correct: set the queue attribute ReceiveMessageWaitTimeSeconds = 20 (or WaitTimeSeconds = 20 per request).
```
Source: [SQS short and long polling](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html) (accessed 2026-07-31).

### ✅ Pattern 2 — Configure a dead-letter queue with a sensible maxReceiveCount

**Why:** isolates poison messages for debugging and stops them from cycling through the main queue.

```text
✅ Correct: create a DLQ (same account, Region, and queue type), attach a redrive policy such as
   { "deadLetterTargetArn": "arn:aws:sqs:us-east-1:123456789012:my-dlq", "maxReceiveCount": 5 }.
   Set maxReceiveCount high enough to allow legitimate retries but low enough to catch failures.
```
Source: [Using dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31).

### ✅ Pattern 3 — Set the DLQ retention period longer than the source queue's

**Why:** for Standard queues the message keeps its **original** enqueue timestamp when moved to the DLQ,
so a short DLQ retention can silently expire failed messages before you inspect them.

```text
❌ Wrong: source retention = 4 days, DLQ retention = 4 days → a message that spent 1 day in the source
   is deleted from the DLQ after only 3 days.
✅ Correct: DLQ retention (e.g., 14 days) > source retention (e.g., 4 days).
```
Source: [Using dead-letter queues → retention periods](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31).

### ✅ Pattern 4 — Match visibility timeout to processing time (and use a heartbeat for long tasks)

**Why:** too-short a timeout causes duplicate processing; too-long delays retries after a crash.

```text
✅ Correct: start visibility timeout ≈ the max time to process + delete a message (e.g., 2 minutes),
   then use ChangeMessageVisibility as a heartbeat to extend while still working. Remember the hard
   12-hour ceiling from first receipt is NOT reset by extending.
```
Source: [Visibility timeout → Best practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) (accessed 2026-07-31).

### ✅ Pattern 5 — Delete messages promptly after successful processing

**Why:** SQS does not remove a message on receipt — only on `DeleteMessage`. Failing to delete causes
reprocessing after the visibility timeout and pushes the queue toward the ~120,000 in-flight limit.

```text
❌ Wrong: process the message but never call DeleteMessage → message reappears and is processed again;
   in-flight count grows until OverLimit.
✅ Correct: call DeleteMessage (or DeleteMessageBatch) immediately after successful processing; with
   Lambda, return ReportBatchItemFailures so only failures are retried.
```
Source: [Welcome → Message lifecycle](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) and [Visibility timeout → in-flight messages](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) (accessed 2026-07-31).

### ✅ Pattern 6 — Make consumers idempotent (design for at-least-once)

**Why:** Standard queues guarantee at-least-once delivery, and even Lambda SQS event source mappings
"process each event at least once, and duplicate processing of records can occur."

```text
❌ Wrong: assume each message is delivered exactly once and perform non-idempotent side effects
   (e.g., "charge card" without a dedup key).
✅ Correct: key writes on a business idempotency key / MessageDeduplicationId so replays are no-ops.
```
Sources: [Welcome → Durability](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html), [Using Lambda with SQS (idempotency warning)](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) (accessed 2026-07-31).

### ✅ Pattern 7 — Batch send/receive/delete (up to 10) to cut cost and lift throughput

**Why:** a single batch request handles up to 10 messages, reducing API calls; for FIFO it multiplies
per-partition throughput from ~300/s toward ~3,000/s.

```text
✅ Correct: use SendMessageBatch / DeleteMessageBatch / set MaxNumberOfMessages = 10 on ReceiveMessage,
   and batch the returned receipt handles.
```
Sources: [SQS message quotas → Message batch](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html), [High throughput for FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html) (accessed 2026-07-31).

### ✅ Pattern 8 — Encrypt sensitive queues with server-side encryption

**Why:** SQS supports default SQS-managed SSE or custom keys in AWS KMS to protect message contents.

```text
✅ Correct: enable SSE (SQS-managed) for baseline, or SSE-KMS with a customer-managed key for regulated
   data; control who can send/receive with IAM and the queue policy.
```
Source: [Welcome → Security (SSE / KMS)](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (accessed 2026-07-31).

---

## 4. 🚫 Never-Do Anti-Patterns

### 🚫 Anti-pattern 1 — Relying on short polling in a busy consumer loop
```text
❌ Wrong: ReceiveMessage with WaitTimeSeconds = 0, polling in a tight loop → many empty responses,
   inflated request bills, and false-empty responses (messages exist but a sampled subset misses them).
✅ Correct: set WaitTimeSeconds/ReceiveMessageWaitTimeSeconds to 20 (long polling).
```
Source: [SQS short and long polling](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html) (accessed 2026-07-31).

### 🚫 Anti-pattern 2 — Assuming exactly-once delivery on a Standard queue
```text
❌ Wrong: treat Standard-queue delivery as exactly-once and skip idempotency.
✅ Correct: Standard queues are at-least-once with best-effort ordering — make consumers idempotent, or
   use a FIFO queue when exactly-once processing / strict order is required.
```
Source: [Welcome → Durability](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (accessed 2026-07-31).

### 🚫 Anti-pattern 3 — Setting the visibility timeout shorter than processing time
```text
❌ Wrong: visibility timeout = 30 s for a job that takes 5 minutes → the message reappears mid-processing
   and a second consumer picks it up (duplicate work).
✅ Correct: size the visibility timeout to the expected processing time and extend it with
   ChangeMessageVisibility (heartbeat) for variable durations.
```
Source: [Visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) (accessed 2026-07-31).

### 🚫 Anti-pattern 4 — Expecting to extend visibility beyond the 12-hour hard cap
```text
❌ Wrong: keep calling ChangeMessageVisibility hoping to hold a message invisible for days.
✅ Correct: the 12-hour ceiling from first receipt is NOT reset by extension; for longer workflows use
   AWS Step Functions or break the task into smaller steps.
```
Source: [Visibility timeout → Best practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) (accessed 2026-07-31).

### 🚫 Anti-pattern 5 — Never deleting messages / ignoring the in-flight limit
```text
❌ Wrong: process without DeleteMessage → in-flight count climbs to ~120,000 (Standard) and SQS returns
   OverLimit; no new messages can be received (short polling) until some are deleted.
✅ Correct: delete after processing, monitor ApproximateNumberOfMessagesNotVisible in CloudWatch, and
   request a quota increase only if genuinely needed.
```
Source: [Visibility timeout → in-flight messages and quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) (accessed 2026-07-31).

### 🚫 Anti-pattern 6 — Setting maxReceiveCount = 1 (no retry tolerance)
```text
❌ Wrong: redrive policy with maxReceiveCount = 1 → a single transient failure dumps the message to the
   DLQ, defeating SQS's built-in retry resilience.
✅ Correct: set maxReceiveCount high enough to absorb transient errors (e.g., 5) while still catching
   genuinely poison messages.
```
Source: [Using dead-letter queues → redrive policy](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31).

### 🚫 Anti-pattern 7 — Using a DLQ on a FIFO queue when strict order must be preserved
```text
❌ Wrong: attach a DLQ to a FIFO queue whose downstream logic depends on strict ordering (e.g., an Edit
   Decision List for a video suite) → moving a failed message to the DLQ breaks the order/context.
✅ Correct: per AWS guidance, don't use a DLQ with FIFO when reordering changes meaning; handle failures
   in-order (retry in place) or redesign so out-of-order handling is safe.
```
Source: [Using dead-letter queues → Note on FIFO](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31).

### 🚫 Anti-pattern 8 — DLQ retention equal to or shorter than the source queue
```text
❌ Wrong: source retention = DLQ retention → failed messages expire from the DLQ before you can inspect
   them (Standard queues keep the original enqueue timestamp on move).
✅ Correct: DLQ retention strictly longer than the source retention.
```
Source: [Using dead-letter queues → retention periods](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31).

### 🚫 Anti-pattern 9 — Cramming payloads > 1 MiB inline (or still assuming the old 256 KiB cap)
```text
❌ Wrong: attempt to send a 3 MiB body directly (rejected — max is 1,048,576 bytes), or artificially
   cap at 256 KiB per an outdated pattern.
✅ Correct: for ≤ 1 MiB send inline; for larger, use the SQS Extended Client Library (store body in S3,
   up to 2 GB, keep a pointer in the message) or split into smaller messages.
```
Sources: [SQS message quotas → Message size](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html), [1 MiB payload announcement (2025-08-04)](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib) (accessed 2026-07-31).

### 🚫 Anti-pattern 10 — Placing the DLQ (or Lambda consumer) in a different account/Region than the source
```text
❌ Wrong: DLQ in a different Region/account than the source queue → invalid; a Lambda ESM in a different
   Region than the queue → unsupported.
✅ Correct: DLQ must be same account + Region + queue type as the source; a Lambda function and its SQS
   queue must be in the same Region (cross-account is allowed for Lambda ESM, cross-Region is not).
```
Sources: [Using dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html), [Using Lambda with SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) (accessed 2026-07-31).

---

## 5. ⚠️ Ask-First Decisions

### ⚠️ Decision 1 — Standard vs FIFO queue

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **Standard** | Nearly unlimited throughput, lowest cost | Only best-effort ordering; at-least-once (duplicates) | High volume, order-tolerant, idempotent consumers |
| **FIFO** | Exactly-once processing, strict order per group | ~300 TPS (3,000 batched) per partition unless high-throughput mode | Order/uniqueness are correctness requirements (payments, sequential state) |

**Ask the architect:** "Is strict ordering or exactly-once processing a *correctness* requirement, or can
the consumer be made idempotent and tolerate best-effort order? What peak TPS must the queue sustain?"
Sources: [Welcome](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html), [Message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html), [High throughput FIFO](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html) (accessed 2026-07-31).

### ⚠️ Decision 2 — Fan-out to multiple consumers (SNS→SQS) vs single SQS queue

SQS delivers a message to typically a **single** consumer; SNS pushes to **many** subscribers. For
one-to-many distribution AWS recommends the **fanout pattern**: an SNS topic with multiple SQS queues
subscribed, so each downstream service gets its own durable copy (and SQS buffers messages if a
subscriber is offline).

**Ask the architect:** "Does exactly one worker fleet consume this event (plain SQS), or must several
independent services each receive their own copy (SNS→SQS fanout)?" Source: [Welcome → SQS vs SNS vs MQ + fanout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) (accessed 2026-07-31).

### ⚠️ Decision 3 — Payloads larger than 1 MiB

| Option | Trade-off | Best when |
|---|---|---|
| Inline (≤ 1 MiB) | Simplest; no extra service | Payload fits under 1,048,576 bytes |
| Extended Client Library (S3 pointer, up to 2 GB) | Adds S3 dependency; sync clients only | Large blobs; keep queue as coordination layer |
| Split into smaller messages | App-level reassembly complexity | Payload is naturally divisible |

**Ask the architect:** "What is the realistic max payload? If it can exceed 1 MiB, do we offload to S3
via the Extended Client, or split messages — and can we accept the sync-only limitation of the Extended
Client?" Source: [Message quotas → Message size](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html) (accessed 2026-07-31).

### ⚠️ Decision 4 — Lambda SQS event source mapping: on-demand (default) vs provisioned mode

| Option | Scaling behavior | Best when |
|---|---|---|
| **On-demand (default)** | Starts at **5** concurrent invokes, adds up to **300** more/minute, max **1,250** concurrent (gated by account concurrency quota, default 1,000); scales back to 5 (optimizes to as few as 2) | Most workloads; cost-efficient; bursty-but-tolerant latency |
| **Provisioned mode** | Dedicated event pollers; scales **3× faster** (up to **1,000** concurrency/min) and **16× higher** (up to **20,000** concurrent); MinimumPollers 2–200 (default 2), MaximumPollers 2–2,000 (default 200); each poller ≈ 1 MB/s, 10 concurrent invokes, 10 polls/s | Strict low-latency SLAs (market data, real-time recommendations, live gaming); adds cost |

Note: provisioned mode and the **maximum concurrency** setting (range 2–1,000) are mutually exclusive.
**Ask the architect:** "Does this consumer have a strict latency SLA and spiky traffic that justifies
paying for provisioned pollers, or is default on-demand scaling sufficient? Do we need a maximum
concurrency cap to protect other functions' concurrency?" Sources: [Configuring scaling for SQS ESM](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html), [Using Lambda with SQS → provisioned mode](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) (accessed 2026-07-31).

### ⚠️ Decision 5 — DLQ retention period and maxReceiveCount

Retention ranges 60 seconds to 14 days (default 4 days); `maxReceiveCount` sets retry tolerance before
a message is dead-lettered. These are coupled correctness/observability choices: DLQ retention must
exceed source retention, and `maxReceiveCount` must balance retry resilience against fast failure
isolation.

**Ask the architect:** "How many transient retries should a message get before it is quarantined
(maxReceiveCount), and how long must failed messages remain inspectable in the DLQ (retention, longer
than the source)?" Source: [Using dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (accessed 2026-07-31).

---

## 6. Source Registry

All URLs below were fetched and verified on **2026-07-31**. AWS `/latest/` developer-guide pages
represent the current GA documentation (no >12-month recency flag needed); the What's New post is dated.

| # | Title | URL | Date |
|---|---|---|---|
| 1 | Amazon SQS increases maximum message payload to 1 MiB | https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib | Published 2025-08-04; accessed 2026-07-31 |
| 2 | What is Amazon SQS? (Welcome) | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html | Accessed 2026-07-31 |
| 3 | Amazon SQS visibility timeout | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html | Accessed 2026-07-31 |
| 4 | Amazon SQS short and long polling | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html | Accessed 2026-07-31 |
| 5 | Using dead-letter queues in Amazon SQS | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html | Accessed 2026-07-31 |
| 6 | High throughput for FIFO queues | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html | Accessed 2026-07-31 |
| 7 | Amazon SQS delay queues | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-delay-queues.html | Accessed 2026-07-31 |
| 8 | Amazon SQS message quotas | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html | Accessed 2026-07-31 |
| 9 | Using Lambda with Amazon SQS | https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html | Accessed 2026-07-31 |
| 10 | Configuring scaling behavior for SQS event source mappings | https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-scaling.html | Accessed 2026-07-31 |

### Confidence gaps (flagged, not asserted)

- **FIFO in-flight message limit:** the visibility-timeout page states FIFO in-flight limits "depend on
  active message groups" without a single fixed number; a specific FIFO in-flight numeric cap is
  `[unverified — confirm against official docs]`. The Standard ~120,000 figure is confirmed.
- **Lambda visibility-timeout "≥ 6× function timeout" rule of thumb:** commonly cited but not present in
  the official pages fetched here — `[unverified — confirm against official docs]`.
- **Exact per-Region FIFO high-throughput-mode TPS numbers:** the quotas page defers the full table to
  the AWS General Reference (not fetched); only the per-partition 300/3,000 figures are asserted here.
- **Pricing:** intentionally excluded (organization- and Region-specific); surfaced as Ask-First.

---

**Recommended next step:** run `/skill-best-practices-validator` on any SKILL.md authored from this
file, or pass this file to `/skill-creator StoryBeats/docs/research_cloud_AWS_SQS_2026-07.md` to generate
a production-ready SQS architecture skill. Supply an `ARCHITECTURE_CONTEXT` (event-driven microservices,
order processing, fanout, Lambda-consumed) to re-weight the Ask-First decisions.
