# AWS SQS — Messaging Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS SQS — Messaging Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Messaging Architecture"
Target_Edition: "AWS SQS 2024"
Architecture_Context: "Distributed applications requiring reliable asynchronous message processing — covering decoupled microservices, task queues, event-driven workflows, load leveling, fan-out patterns, and exactly-once ordered processing"
Official_Source_URL: "https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to SQS feature updates and integration changes"
```

---

## Executive Summary

Amazon Simple Queue Service (SQS) is AWS's fully managed message queuing service that enables decoupling and scaling of distributed software systems and components. SQS eliminates the complexity and overhead of managing message-oriented middleware, while providing a durable, highly available, and scalable queuing mechanism that supports virtually unlimited throughput for Standard queues and up to 70,000 messages per second (with batching in high-throughput mode) for FIFO queues. SQS stores messages redundantly across multiple Availability Zones, guaranteeing 99.999999999% (11 nines) durability and at least 99.9% service availability.

The 2024 edition's most architecturally significant advances are: (1) **FIFO high-throughput mode GA with increased partition limits** — enabling up to 70,000 messages/second with batching (7,000 without batching) per FIFO queue, eliminating throughput as a barrier for FIFO adoption in high-volume workloads; (2) **Fair Queues for Standard queues** — enabling per-message-group-ID fair scheduling that prevents noisy-neighbor problems without requiring FIFO queue semantics; (3) **Dead-letter queue redrive** — allowing messages to be moved back from DLQ to source queue via console or API, closing the operational gap for poison-pill recovery; (4) **SSE-SQS as default encryption** — all new queues are encrypted at rest by default using SQS-managed keys, without cost or configuration overhead. These changes shift SQS from a "configure encryption" to "encrypted by default" posture and make FIFO queues viable for workloads previously forced into Standard queues due to throughput limits.

The three most critical architecture guardrails for SQS are: (1) **always configure a Dead-Letter Queue (DLQ) for every production queue** — without a DLQ, messages that repeatedly fail processing are silently discarded after exceeding the retention period, creating data loss scenarios invisible to monitoring; (2) **set visibility timeout to at least 6x the average processing time** — a timeout shorter than processing time causes duplicate processing and amplifies downstream load; (3) **always use long polling (WaitTimeSeconds > 0) on receive operations** — short polling generates empty responses that consume API quota and increase cost without delivering messages.

---

## Cloud Architecture Glossary

```
Term: Standard Queue
Definition: The default Amazon SQS queue type that offers maximum throughput (virtually unlimited API calls per second per action), best-effort ordering, and at-least-once message delivery. Messages may occasionally be delivered more than once or out of the order in which they were sent.
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html
Architect Usage: Use Standard queues when throughput is the primary concern and the consumer can handle duplicate or out-of-order messages. Design consumers to be idempotent. Standard queues are the default choice unless ordering or exactly-once guarantees are non-negotiable business requirements.
Common Confusion: "At-least-once delivery" does not mean every message is delivered exactly twice — duplicates are infrequent (Amazon's internal deduplication catches most). However, architects must design for the possibility. Standard queue ≠ unreliable — it is highly reliable with a statistical (not contractual) ordering guarantee.

Term: FIFO Queue
Definition: An Amazon SQS queue type that guarantees First-In-First-Out delivery order and exactly-once message processing within the 5-minute deduplication window. FIFO queue names must end with the `.fifo` suffix. Supports Message Group IDs for parallel ordered processing across independent logical streams.
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fifo-queues.html
Architect Usage: Use FIFO queues when strict ordering within a logical group (e.g., per-customer, per-order, per-device) is a business requirement OR when exactly-once processing is cheaper than building client-side deduplication. Enable high-throughput mode for FIFO queues that need more than 300 TPS per action.
Common Confusion: FIFO ordering is per Message Group ID, NOT per queue. Messages in different message groups are processed independently and in parallel. A single-group FIFO queue (one Message Group ID for all messages) serializes all processing — use multiple Message Group IDs for parallelism.

Term: Visibility Timeout
Definition: The period of time (0 seconds to 12 hours, default 30 seconds) during which a received message is invisible to other consumers. If the consumer does not delete the message before the visibility timeout expires, the message becomes visible again and can be received by another consumer.
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html
Architect Usage: Set visibility timeout to at least 6x the average processing time to account for retries, downstream latency, and variance. Use ChangeMessageVisibility to extend the timeout for long-running processing (heartbeat pattern). The maximum cumulative visibility timeout for a message is 12 hours from first receipt.
Common Confusion: Visibility timeout ≠ message TTL. Visibility timeout controls how long a message is hidden after receipt. Message retention period (default 4 days, max 14 days) controls how long a message lives in the queue before automatic deletion. A message can be received multiple times within its retention period if visibility timeouts expire without deletion.

Term: Dead-Letter Queue (DLQ)
Definition: A separate SQS queue configured to receive messages that fail processing after a specified number of receive attempts (maxReceiveCount). The DLQ is associated with a source queue via a redrive policy. DLQ must be the same queue type as the source (Standard DLQ for Standard queue, FIFO DLQ for FIFO queue).
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
Architect Usage: Every production queue MUST have a DLQ. Set maxReceiveCount high enough (typically 3-5 for most workloads) to allow legitimate retries before moving to DLQ. Set DLQ retention period longer than source queue retention period. Configure CloudWatch alarms on ApproximateNumberOfMessagesVisible in the DLQ.
Common Confusion: DLQ does not automatically retry or reprocess messages. Messages in a DLQ require manual intervention — either DLQ redrive (move back to source queue) or manual processing. For Standard queues, the message's original enqueue timestamp is preserved in the DLQ — the retention countdown does NOT reset.

Term: Message Group ID
Definition: A tag (up to 128 characters) that specifies the logical grouping of messages within a FIFO queue. Messages within the same Message Group ID are delivered in strict FIFO order. Messages in different groups are processed independently and in parallel. Required for FIFO queues; optional for Standard queues (enables Fair Queues feature).
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-key-terms.html
Architect Usage: Design Message Group IDs around the entity that requires ordering (customer-id, order-id, account-id, device-id). High-cardinality Message Group IDs enable maximum parallelism. A single Message Group ID creates a global ordering bottleneck — avoid unless true global ordering is required.
Common Confusion: Message Group ID ≠ topic or routing key. Messages are not "filtered" by group — all consumers see all groups. The group controls ordering and blocking: if a message in a group is in-flight, subsequent messages in that same group are not delivered until the in-flight message is processed or its visibility timeout expires.

Term: Deduplication ID
Definition: A token (up to 128 characters) used by FIFO queues to detect and reject duplicate messages within the 5-minute deduplication interval. Can be explicitly provided (MessageDeduplicationId) or automatically generated from a SHA-256 hash of the message body (content-based deduplication, enabled at queue level).
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html
Architect Usage: Use explicit Deduplication IDs when the same logical message might have different payloads (e.g., includes timestamps). Use content-based deduplication when message bodies are deterministic representations of the intended action. The 5-minute window means duplicates sent more than 5 minutes apart are NOT detected.
Common Confusion: Deduplication is per Message Group ID, not per queue. Two messages with the same Deduplication ID but different Message Group IDs are both accepted. The 5-minute deduplication window is a hard limit — it cannot be extended or shortened.

Term: Long Polling
Definition: A receive behavior where the ReceiveMessage API call waits up to WaitTimeSeconds (1-20 seconds) for messages to become available before returning an empty response. Reduces the number of empty responses, decreases latency for message delivery, and reduces SQS API costs.
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html
Architect Usage: ALWAYS use long polling (WaitTimeSeconds = 20 is the standard recommendation). Short polling (WaitTimeSeconds = 0) returns immediately even if no messages are available, generating unnecessary API calls and cost. Long polling queries all SQS servers, reducing the chance of missing messages that exist on a server not yet queried.
Common Confusion: Long polling latency (up to 20 seconds per receive call) does NOT mean messages wait 20 seconds to be processed. If a message arrives during the long-poll wait, the API returns immediately with that message. The 20-second wait only applies when no messages are available.

Term: Delay Queue
Definition: A queue configuration (DelaySeconds: 0-900 seconds / 15 minutes) that makes all messages sent to the queue invisible for the specified delay period before becoming available for consumption. Per-message delay (MessageTimer) overrides queue-level delay for individual messages.
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-delay-queues.html
Architect Usage: Use delay queues for scheduled processing (e.g., "process this payment in 5 minutes"), rate limiting (throttle downstream services), or retry-after patterns (re-queue with increasing delay). Per-message delay is NOT supported on FIFO queues — only queue-level delay applies.
Common Confusion: Delay queue delay ≠ visibility timeout. Delay applies BEFORE first receipt (message is invisible to all consumers). Visibility timeout applies AFTER receipt (message is invisible only to other consumers while being processed). They serve fundamentally different purposes.

Term: Redrive Policy
Definition: A JSON configuration on a source queue that specifies the Dead-Letter Queue ARN (deadLetterTargetArn) and the maximum number of receive attempts (maxReceiveCount) before a message is moved to the DLQ. Each time a consumer receives and does not delete a message, the receive count increments.
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
Architect Usage: Set maxReceiveCount based on the application's retry tolerance. A maxReceiveCount of 1 means one failed processing attempt triggers DLQ routing — too aggressive for most applications. Values of 3-5 are typical. Combine with exponential backoff in the consumer for transient failures before the message hits the DLQ threshold.
Common Confusion: maxReceiveCount counts receive operations, not processing failures. If a consumer receives a message and then the visibility timeout expires (without deletion or explicit failure), that counts as a receive. A poorly tuned visibility timeout can cause messages to reach maxReceiveCount without ever being "processed."

Term: Redrive Allow Policy
Definition: A JSON configuration on the DLQ that specifies which source queues are allowed to use it as their dead-letter target. Options: allowAll (default), denyAll, or byQueue (up to 10 specific source queue ARNs).
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
Architect Usage: In multi-team environments, restrict DLQ access using byQueue to prevent unauthorized queues from routing to shared DLQs. This prevents a runaway producer from flooding a DLQ that belongs to another team's monitoring scope.
Common Confusion: Redrive allow policy is set on the DLQ (destination), not on the source queue. The redrive policy (maxReceiveCount + DLQ ARN) is set on the source queue. These are two separate policy types on two different queues.

Term: In-Flight Messages
Definition: Messages that have been received by a consumer but not yet deleted (or whose visibility timeout has not yet expired). Standard queues support approximately 120,000 in-flight messages. FIFO queues support approximately 20,000 in-flight messages. Exceeding this quota returns OverLimit errors.
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html
Architect Usage: Monitor ApproximateNumberOfMessagesNotVisible (CloudWatch metric) to track in-flight messages. If approaching 120,000 (standard) or 20,000 (FIFO), either consumers are too slow, visibility timeout is too long, or the queue needs horizontal scaling (multiple queues). Request quota increase via AWS Support if architecturally justified.
Common Confusion: In-flight ≠ "being processed." A message is in-flight from the moment it's received until it's deleted — regardless of whether the consumer is actively processing it. A consumer that crashes without deleting holds the message in-flight until the visibility timeout expires.

Term: Server-Side Encryption (SSE)
Definition: Encryption of message bodies at rest in SQS. Two options: SSE-SQS (SQS-managed keys, no cost, default for new queues) and SSE-KMS (customer-managed AWS KMS keys, KMS API call costs apply). Encryption does NOT apply to queue metadata, message attributes, or per-queue/per-message identifiers.
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html
Architect Usage: SSE-SQS is the default and sufficient for most workloads. Use SSE-KMS when you need key rotation control, cross-account key sharing, CloudTrail audit of key usage, or compliance requirements mandating customer-managed keys. Note: SSE-KMS adds per-message KMS API call cost that can be significant at high volume.
Common Confusion: SSE encrypts message body only — queue URLs, message IDs, receipt handles, and message attributes are NOT encrypted. SSE-KMS does not mean the SQS API calls are encrypted — all SQS API calls already use TLS (in-transit encryption is always present). SSE addresses at-rest encryption.

Term: SQS Access Policy (Resource-Based Policy)
Definition: A JSON-based resource policy attached to an SQS queue that defines which AWS principals (accounts, IAM users, roles, services) can perform which SQS actions on the queue. Supports conditions based on source ARN, source account, VPC endpoint, IP address, and encryption context.
Provider Docs Section: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-overview-of-managing-access.html
Architect Usage: Use resource-based policies for cross-account access (allowing another account's role to send/receive), service integrations (allowing SNS, S3, EventBridge, or Lambda to interact with the queue), and VPC endpoint restrictions (restricting queue access to specific VPC endpoints).
Common Confusion: SQS access policies AND IAM policies both apply — the effective permission is the union of both (for same-account access with no explicit deny). For cross-account access, BOTH the resource policy on the queue AND the IAM policy on the calling principal must allow the action.
```

---

## Architecture Framework Analysis: AWS Well-Architected — Reliability Pillar (Loosely Coupled Dependencies)

```
Pillar: Reliability
Definition: The ability of a workload to perform its intended function correctly and consistently when it's expected to.
Key Design Principles:
  - Automatically recover from failure (DLQ captures failed messages for later reprocessing)
  - Test recovery procedures (DLQ redrive, message replay, queue purge scenarios)
  - Scale horizontally to increase aggregate workload availability (multiple consumers per queue)
  - Stop guessing capacity (SQS scales automatically — no pre-provisioning required)
  - Manage change in automation (IaC for queue configuration, DLQ policies, CloudWatch alarms)
Applies To Distributed Messaging: SQS is the primary AWS mechanism for implementing REL04-BP02 (loosely coupled dependencies). Message queues absorb producer-consumer rate mismatches, isolate failures, and enable independent scaling. Every synchronous inter-service call should be evaluated for asynchronous conversion via SQS.
Assessment Questions:
  1. Is every asynchronous processing path configured with a Dead-Letter Queue and CloudWatch alarm?
  2. Is the visibility timeout set to at least 6x the average message processing time?
  3. Are consumers designed to be idempotent (safe to process the same message multiple times)?
Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_prevent_interaction_failure_loosely_coupled_system.html

Pillar: Security
Definition: The ability to protect data, systems, and assets while delivering business value through risk assessments and mitigation strategies.
Key Design Principles:
  - Apply security at all layers (queue access policies, IAM roles, encryption, VPC endpoints)
  - Enable traceability (CloudTrail for SQS API calls, CloudWatch for queue metrics)
  - Implement least privilege (per-queue IAM policies with specific actions and resource ARNs)
  - Protect data in transit and at rest (TLS for all API calls, SSE-SQS or SSE-KMS for at-rest)
  - Automate security best practices (SCP guardrails, Config rules for encryption validation)
Applies To Distributed Messaging: Every SQS queue must have encryption at rest enabled (SSE-SQS minimum). Queue access policies must use specific principal ARNs — never wildcard (*) principals. Cross-account access must use explicit condition keys (aws:SourceAccount, aws:SourceArn). VPC endpoints restrict queue access to private network paths.
Assessment Questions:
  1. Is server-side encryption enabled on every SQS queue in the account?
  2. Do queue access policies use specific principal ARNs and condition keys — never wildcard principals?
  3. Are SQS VPC endpoints configured for queues accessed from private subnets?
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_rest.html

Pillar: Performance Efficiency
Definition: The ability to use computing resources efficiently to meet system requirements and to maintain that efficiency as demand changes and technologies evolve.
Key Design Principles:
  - Use serverless architectures (SQS + Lambda eliminates consumer fleet management)
  - Experiment more often (A/B test Standard vs FIFO, batch sizes, polling strategies)
  - Consider mechanical sympathy (batch API operations, long polling, message batching)
  - Democratize advanced technologies (use managed messaging — no self-hosted RabbitMQ/Kafka overhead)
Applies To Distributed Messaging: Always use batch API operations (SendMessageBatch, DeleteMessageBatch, ReceiveMessage with MaxNumberOfMessages=10) to maximize throughput per API call. Use long polling to reduce empty responses. For FIFO queues, enable high-throughput mode when exceeding 300 TPS per action.
Assessment Questions:
  1. Are all producer and consumer operations using batch APIs (10 messages per batch)?
  2. Is long polling enabled with WaitTimeSeconds = 20 on all ReceiveMessage calls?
  3. For FIFO queues, is high-throughput mode enabled if throughput exceeds 300 TPS?
Source: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/perf_data_selecting.html

Pillar: Cost Optimization
Definition: The ability to run systems to deliver business value at the lowest price point.
Key Design Principles:
  - Adopt a consumption model (SQS charges per API call — pay only for what you use)
  - Measure overall efficiency (cost per message processed, API calls per message lifecycle)
  - Analyze and attribute expenditure (per-queue cost allocation tags)
  - Stop spending money on undifferentiated heavy lifting (managed SQS vs self-hosted message broker)
Applies To Distributed Messaging: Minimize API calls via batch operations (10 messages per request = 10x cost reduction vs individual calls). Use long polling to eliminate empty ReceiveMessage responses. Choose SSE-SQS over SSE-KMS unless compliance requires customer-managed keys — KMS adds per-message API call cost. Standard queues are approximately the same cost as FIFO — choose based on requirements, not cost.
Assessment Questions:
  1. Are batch operations used to minimize the number of SQS API calls?
  2. Is SSE-SQS (free) used instead of SSE-KMS unless customer-managed keys are explicitly required?
  3. Are empty ReceiveMessage responses minimized through long polling and appropriate consumer scaling?
Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost_decomissioning_resources.html

Pillar: Operational Excellence
Definition: The ability to support development and run workloads effectively, gain insight into their operations, and continuously improve supporting processes and procedures.
Key Design Principles:
  - Perform operations as code (IaC for queue configuration, DLQ policies, alarms)
  - Make frequent, small, reversible changes (queue attribute updates are non-destructive)
  - Refine operations procedures frequently (DLQ redrive runbooks, poison-pill analysis)
  - Anticipate failure (DLQ + CloudWatch alarms + operational dashboards)
  - Learn from all operational failures (DLQ message analysis, dead-letter redrive)
Applies To Distributed Messaging: All queue configurations must be managed via IaC (CloudFormation/CDK/Terraform). DLQ alarm thresholds must trigger on-call notification. DLQ redrive procedures must be documented in runbooks. Queue metrics (ApproximateNumberOfMessagesVisible, ApproximateAgeOfOldestMessage) must be on operational dashboards.
Assessment Questions:
  1. Are all SQS queue configurations managed via Infrastructure as Code?
  2. Are CloudWatch alarms configured for DLQ message arrival and oldest message age?
  3. Is there a documented and tested DLQ redrive runbook?
Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/ops_ready_to_support_operations_as_code.html

Pillar: Sustainability
Definition: Minimizing the environmental impact of running cloud workloads.
Key Design Principles:
  - Minimize idle compute (SQS is serverless — no idle consumer infrastructure when using Lambda)
  - Maximize utilization (batch processing reduces per-message compute overhead)
  - Use managed services (SQS vs self-hosted broker eliminates always-on EC2 instances)
Applies To Distributed Messaging: SQS + Lambda is the most sustainable consumer pattern — zero idle compute. Batch processing (processing 10 messages per Lambda invocation) reduces total compute time. Long polling reduces network calls. Avoid overprovisioned EC2-based consumer fleets that idle between traffic bursts.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Dead-Letter Queue for Every Production Queue**
- Pillar Alignment: Reliability, Operational Excellence
- Why: Without a DLQ, messages that repeatedly fail processing are silently discarded after reaching the queue's retention period (default 4 days). This creates invisible data loss. The Well-Architected Reliability pillar mandates "automatically recover from failure" — DLQs capture failures for later analysis and reprocessing.
- AWS Services: Amazon SQS (source queue + DLQ), Amazon CloudWatch (alarms), AWS Lambda (optional automated redrive)
- Architecture Decision:
  Every source queue must have a redrive policy with `deadLetterTargetArn` pointing to a dedicated DLQ of the same type (Standard→Standard, FIFO→FIFO). Set `maxReceiveCount` between 3-5 for most workloads. Set DLQ retention period to 14 days (maximum). Configure CloudWatch alarm on `ApproximateNumberOfMessagesVisible > 0` for the DLQ with SNS notification to the on-call team.
- Verification:
  ```bash
  aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names RedrivePolicy
  # Must return a valid RedrivePolicy JSON with deadLetterTargetArn and maxReceiveCount
  ```
- Trade-offs: Adds a second queue per source queue (minor cost, no operational overhead beyond initial setup). DLQ messages require manual intervention — they do not self-heal.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html

**Server-Side Encryption on All Queues**
- Pillar Alignment: Security
- Why: The Well-Architected Security pillar requires encryption at rest for all data stores. SQS message bodies may contain PII, financial data, or business-sensitive payloads. SSE-SQS is free and adds no latency — there is no valid reason to leave encryption disabled.
- AWS Services: Amazon SQS (SSE-SQS or SSE-KMS), AWS KMS (for customer-managed keys)
- Architecture Decision:
  All queues must have `SqsManagedSseEnabled: true` (SSE-SQS, default for new queues) as the minimum. Use SSE-KMS (`KmsMasterKeyId`) only when compliance requires customer-managed key rotation, cross-account key sharing, or CloudTrail key-usage audit. For SSE-KMS, set `KmsDataKeyReusePeriodSeconds` to 300-3600 seconds to reduce KMS API call costs.
- Verification:
  ```bash
  aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names SqsManagedSseEnabled KmsMasterKeyId
  # Must return SqsManagedSseEnabled=true OR a valid KmsMasterKeyId
  ```
- Trade-offs: SSE-SQS is free. SSE-KMS adds $0.03 per 10,000 KMS API calls — significant at high message volumes. KmsDataKeyReusePeriodSeconds reduces calls but delays key rotation granularity.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html

**Long Polling on All Receive Operations**
- Pillar Alignment: Cost Optimization, Performance Efficiency
- Why: Short polling (WaitTimeSeconds=0) returns empty responses when no messages are available, consuming API quota and generating cost with zero value. Long polling queries all SQS servers and waits for messages to arrive — reducing empty responses by 90%+ and delivering messages with lower latency (message arrives during wait → immediate return).
- AWS Services: Amazon SQS (ReceiveMessage API)
- Architecture Decision:
  Set `ReceiveMessageWaitTimeSeconds: 20` at queue level (applies as default for all ReceiveMessage calls on the queue) OR set `WaitTimeSeconds: 20` on every ReceiveMessage API call. For Lambda Event Source Mappings, long polling is automatically configured by AWS — no manual setting required.
- Verification:
  ```bash
  aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names ReceiveMessageWaitTimeSeconds
  # Should return 20 (or at minimum > 0)
  ```
- Trade-offs: Long polling adds up to 20 seconds latency for the *first* message when the queue is empty (irrelevant for steady-state traffic). For use cases requiring sub-second empty-queue detection, use SQS → Lambda (event-driven, no polling overhead on your side).
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html

**Idempotent Consumer Design**
- Pillar Alignment: Reliability
- Why: SQS Standard queues guarantee at-least-once delivery — messages can be delivered more than once. Even FIFO queues can deliver duplicates in edge cases (consumer receives, processes, but crashes before DeleteMessage — message becomes visible again after visibility timeout). All SQS consumers MUST be idempotent.
- AWS Services: Amazon SQS, Amazon DynamoDB (idempotency table), AWS Lambda Powertools (idempotency utility)
- Architecture Decision:
  Implement idempotency at the consumer level using one of: (1) DynamoDB conditional writes with message ID as the idempotency key; (2) AWS Lambda Powertools idempotency decorator (Python/TypeScript/Java); (3) Database unique constraints on the business operation key; (4) Conditional state machine transitions (only process if current state allows). Choose the mechanism that matches your data store.
- Verification:
  Send the same message twice to the queue with the same logical ID. Verify that the downstream side effect occurs exactly once (e.g., single database record, single payment charge, single notification sent).
- Trade-offs: Idempotency adds a lookup/write per message (DynamoDB read+conditional write = ~2ms latency). For extremely high-throughput, low-latency paths, consider FIFO queues with content-based deduplication as the first-line defense.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_prevent_interaction_failure_loosely_coupled_system.html

**Visibility Timeout Aligned to Processing Time**
- Pillar Alignment: Reliability, Performance Efficiency
- Why: If visibility timeout is shorter than processing time, the message becomes visible again while still being processed — causing duplicate processing by a second consumer. If too long, failed messages take too long to become available for retry. The Well-Architected Framework mandates alignment between timeout and actual processing characteristics.
- AWS Services: Amazon SQS (VisibilityTimeout queue attribute, ChangeMessageVisibility API)
- Architecture Decision:
  Set visibility timeout = 6x average processing time (accounts for P99 latency, retries, downstream timeouts). For Lambda consumers, set visibility timeout ≥ Lambda function timeout (AWS documentation recommendation). Implement heartbeat pattern (ChangeMessageVisibility extension) for variable-duration processing. Maximum visibility timeout is 12 hours.
- Verification:
  ```bash
  aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names VisibilityTimeout
  # Compare against measured P99 processing time — timeout should be ≥ 6x average
  ```
- Trade-offs: Longer timeout delays reprocessing of genuinely failed messages. Shorter timeout risks duplicates. The heartbeat pattern adds complexity but handles variable processing time gracefully.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html

**Batch API Operations for All Producers and Consumers**
- Pillar Alignment: Cost Optimization, Performance Efficiency
- Why: SQS charges per API request. Each SendMessage, ReceiveMessage, or DeleteMessage is one request. Batch operations (SendMessageBatch, DeleteMessageBatch) process up to 10 messages per single API request — reducing cost by up to 10x and improving throughput by reducing network round trips.
- AWS Services: Amazon SQS (SendMessageBatch, DeleteMessageBatch, ReceiveMessage with MaxNumberOfMessages=10)
- Architecture Decision:
  Producers must use `SendMessageBatch` (up to 10 messages, total payload ≤ 256 KB per batch). Consumers must call `ReceiveMessage` with `MaxNumberOfMessages=10` and `DeleteMessageBatch` for processed messages. For Lambda Event Source Mappings, batch size is configured in the event source mapping (max 10,000 for standard, 10 for FIFO).
- Verification:
  Monitor CloudWatch metric `NumberOfMessagesSent` vs `NumberOfEmptyReceives`. Ratio should indicate batch usage. Audit application code for individual SendMessage/DeleteMessage calls — replace with batch equivalents.
- Trade-offs: Batching adds complexity to error handling — partial batch failures require per-message retry logic. SendMessageBatch returns individual success/failure per message in the batch.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-batch-api-actions.html

---

### ⚠️ Architectural Decisions

**Standard Queue vs FIFO Queue**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Standard Queue | SQS Standard | Throughput (unlimited TPS), cost efficiency | Ordering guarantees, exactly-once delivery | Message ordering is not required or consumer is idempotent; throughput > 70K msgs/sec |
  | FIFO Queue | SQS FIFO (.fifo) | Ordering per group, exactly-once processing | Throughput ceiling (70K TPS with batching in high-throughput mode) | Strict per-entity ordering required; deduplication needed; throughput ≤ 70K msgs/sec |
  | FIFO High-Throughput | SQS FIFO + High Throughput Mode | Throughput + ordering | Partition-level ordering (ordering per message group, not global) | Need both ordering and high throughput; multiple independent message groups |

- Cost Profile: Identical per-request pricing ($0.40 per million requests for Standard, $0.50 per million for FIFO — first 1M requests/month free). FIFO's slightly higher price is negligible. SSE-KMS cost is the primary cost differentiator at scale.
- Lock-in Assessment: Both queue types are SQS-specific. Migration between Standard and FIFO requires creating a new queue (cannot convert in-place). Application code changes are minimal (add MessageGroupId + DeduplicationId for FIFO).
- Architect Instruction: "Ask 'Does this workflow require per-entity strict ordering or exactly-once processing?' — if NO to both, use Standard. If YES to either, use FIFO with high-throughput mode."
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html

**Consumer Pattern: Lambda Event Source vs EC2/ECS Polling**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Lambda Event Source Mapping | Lambda + SQS ESM | Zero infrastructure management, auto-scaling, pay-per-invocation | Execution duration limit (15 min), cold starts, VPC attach latency | Processing time < 15 min, stateless processing, variable load |
  | ECS/Fargate Consumer | ECS + SQS SDK | Long-running processing, persistent connections, full runtime control | Infrastructure management, always-on cost, scaling configuration | Processing > 15 min, requires local state, GPU/special hardware |
  | EC2 Auto Scaling Consumer | EC2 + ASG + SQS SDK | Maximum control, custom scaling, spot instances | Full infrastructure management, AMI maintenance, scaling lag | Cost-sensitive high-volume steady-state, specialized runtime requirements |

- Cost Profile: Lambda is cheapest for sporadic/bursty traffic. ECS/Fargate is optimal for steady-state medium-volume. EC2 with Spot is cheapest for sustained high-volume with failure tolerance.
- Scaling Characteristics: Lambda scales to 1000 concurrent by default (configurable to tens of thousands). ECS requires target tracking scaling policy on SQS queue depth. EC2 ASG uses custom CloudWatch metrics (ApproximateNumberOfMessagesVisible / NumberOfConsumers).
- Operational Burden: Lambda = none. ECS = container image management, task definition updates. EC2 = AMI, patching, instance lifecycle, scaling policies.
- Architect Instruction: "Ask 'What is the P99 processing time for a single message?' — if < 15 minutes, default to Lambda. If > 15 minutes or requires persistent state, use ECS."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html

**Single Queue vs Fan-Out (SNS + SQS)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Direct SQS Queue | SQS | Simplicity, single consumer path | Multi-consumer flexibility | One producer, one consumer processing pipeline |
  | SNS → Multiple SQS (Fan-Out) | SNS Topic + SQS Subscriptions | Multi-consumer decoupling, independent processing rates | Additional SNS hop latency (~ms), SNS cost | Multiple independent consumers need the same message |
  | EventBridge → SQS | EventBridge + SQS | Content-based filtering, schema registry, archive/replay | Higher per-event cost, 5 targets per rule limit | Complex routing rules, event schema evolution, replay capability |

- Cost Profile: Direct SQS = lowest (one API call). SNS→SQS = SNS publish ($0.50/M) + SQS per subscription. EventBridge = $1.00/M events + SQS.
- Lock-in Assessment: All patterns are AWS-specific. SNS→SQS is the most established and portable pattern. EventBridge adds event schema capabilities but higher vendor coupling.
- Architect Instruction: "Ask 'How many independent consumers need this message?' — if 1, use direct SQS. If 2+, use SNS→SQS fan-out. If consumers need content-based filtering, use EventBridge→SQS."
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html

**Message Size: Inline vs Extended Client (S3)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Inline Message (≤ 256 KB) | SQS | Latency, simplicity, single API call | Message size limit (256 KB max) | Messages fit within 256 KB |
  | Extended Client (S3 pointer) | SQS + S3 + Extended Client Library | Payload size (up to 2 GB) | Latency (S3 read/write), additional S3 cost, library dependency | Messages > 256 KB (large payloads, files, images) |
  | Claim-Check Pattern | SQS (metadata) + S3/DynamoDB (payload) | Decoupled payload storage, flexible retrieval | Implementation complexity, additional storage cost | Variable-size payloads, some consumers don't need full payload |

- Cost Profile: Inline = SQS request cost only. Extended Client = SQS + S3 PUT + S3 GET per message (significant at high volume). Claim-check = SQS + storage cost (amortized if consumers selectively retrieve).
- Architect Instruction: "Ask 'What is the maximum message payload size?' — if ≤ 256 KB always, use inline. If sometimes > 256 KB, use Extended Client Library. If payloads are large and not all consumers need the full payload, use claim-check pattern."
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-s3-messages.html

**Encryption: SSE-SQS vs SSE-KMS**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | SSE-SQS (SQS-managed keys) | SQS | Zero cost, zero configuration, automatic | Key rotation control, audit visibility, cross-account key sharing | No compliance requirement for customer-managed keys |
  | SSE-KMS (Customer-managed CMK) | SQS + KMS | Key control, rotation policy, CloudTrail audit of key usage, cross-account sharing | KMS API cost ($0.03/10K calls), slightly higher latency | Compliance requires CMK, need key usage audit trail, cross-account access to encrypted queues |

- Cost Profile: SSE-SQS = $0. SSE-KMS = $1/month per CMK + $0.03 per 10,000 KMS API calls. At 1M messages/day, SSE-KMS adds ~$9/day in KMS costs (mitigated by KmsDataKeyReusePeriodSeconds).
- Architect Instruction: "Ask 'Does compliance require customer-managed encryption keys with audit trail?' — if NO, use SSE-SQS. If YES, use SSE-KMS with KmsDataKeyReusePeriodSeconds=300 minimum."
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html

---

### 🚫 Anti-Patterns

**Short Polling Without WaitTimeSeconds**
- Risk Level: HIGH
- Why: Violates Cost Optimization and Performance Efficiency pillars. Short polling returns empty responses 90%+ of the time for queues with intermittent traffic, generating API costs with zero value delivery. Also increases message delivery latency because short polling queries a random subset of SQS servers — messages on non-queried servers are missed.
- Instead: Set `ReceiveMessageWaitTimeSeconds: 20` at queue level. For Lambda Event Source Mappings, long polling is automatic.
- Detection:
  ```bash
  aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names ReceiveMessageWaitTimeSeconds
  # Alert if value is 0
  ```
  CloudWatch: Monitor `NumberOfEmptyReceives` metric — high values indicate short polling waste.
- Impact: Cost overrun (unnecessary API calls), increased message delivery latency, missed messages on non-queried servers.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html

**No Dead-Letter Queue Configured**
- Risk Level: CRITICAL
- Why: Violates Reliability and Operational Excellence pillars. Without a DLQ, messages that repeatedly fail processing consume receive attempts until the retention period expires — then disappear permanently. This creates silent data loss with no operational visibility. Poison-pill messages (malformed, unparseable) block processing indefinitely if consumers retry without limits.
- Instead: Configure a redrive policy with `maxReceiveCount: 3-5` and a dedicated DLQ. Set CloudWatch alarm on DLQ `ApproximateNumberOfMessagesVisible > 0`. Set DLQ retention to 14 days.
- Detection:
  ```bash
  aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names RedrivePolicy
  # Alert if RedrivePolicy is empty/null
  ```
  AWS Config Rule: `sqs-dead-letter-queue-enabled` (custom rule).
- Impact: Silent data loss, poison-pill queue blocking, no operational visibility into processing failures.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html

**Wildcard Principal in Queue Access Policy**
- Risk Level: CRITICAL
- Why: Violates Security pillar. A queue policy with `"Principal": "*"` without conditions allows any AWS account to send messages to or receive messages from the queue. This enables queue poisoning (injecting malicious messages), message theft (reading sensitive data), and DoS (flooding the queue with garbage).
- Instead: Use specific principal ARNs (`"Principal": {"AWS": "arn:aws:iam::123456789012:role/ServiceRole"}`). For service integrations (SNS, S3, EventBridge), use `aws:SourceArn` and `aws:SourceAccount` conditions.
- Detection:
  ```bash
  aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names Policy
  # Parse JSON — alert if any statement has Principal: "*" without restrictive Condition
  ```
  AWS Config Rule: `sqs-queue-public-accessibility` (custom rule using IAM Access Analyzer).
- Impact: Data breach (message contents exposed), queue poisoning (malicious message injection), DoS (queue flooding), unauthorized message deletion.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-overview-of-managing-access.html

**Single Message Group ID for All FIFO Messages**
- Risk Level: HIGH
- Why: Violates Performance Efficiency pillar. A single Message Group ID serializes ALL message processing — only one message at a time can be in-flight for that group. This converts a FIFO queue into a single-threaded serial processor, negating parallelism and capping throughput at one message per visibility-timeout cycle.
- Instead: Use high-cardinality Message Group IDs (customer-id, order-id, tenant-id) to enable parallel processing across independent logical streams while maintaining ordering within each stream.
- Detection:
  Audit producer code for hardcoded or constant `MessageGroupId` values. Monitor CloudWatch metric `NumberOfMessagesSent` vs `ApproximateNumberOfMessagesVisible` — if visible messages grow while send rate is stable, processing is serialization-bottlenecked.
- Impact: Throughput collapse (queue becomes single-threaded), message processing delays, consumer underutilization, scalability ceiling.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-key-terms.html

**Visibility Timeout Shorter Than Processing Time**
- Risk Level: HIGH
- Why: Violates Reliability pillar. If the visibility timeout expires before the consumer finishes processing, the message becomes visible again — another consumer picks it up, resulting in duplicate processing. This amplifies downstream load, causes data inconsistencies, and wastes compute resources.
- Instead: Set visibility timeout ≥ 6x average processing time. For Lambda, set queue visibility timeout ≥ Lambda function timeout. Implement heartbeat pattern (ChangeMessageVisibility) for variable-duration processing.
- Detection:
  Compare CloudWatch metrics: `ApproximateAgeOfOldestMessage` trending up while `NumberOfMessagesReceived` is high indicates messages being received multiple times. Monitor Lambda ESM metric `IteratorAge` or application-level duplicate detection.
- Impact: Duplicate processing, downstream data inconsistency, amplified compute cost, cascading load under backpressure.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html

**Processing Messages Without Deletion**
- Risk Level: HIGH
- Why: Violates Reliability and Cost Optimization pillars. If a consumer processes a message but does not call DeleteMessage (or DeleteMessageBatch), the message becomes visible again after the visibility timeout and is reprocessed indefinitely until hitting maxReceiveCount (DLQ) or retention expiry. This wastes compute and creates infinite retry loops.
- Instead: Always delete messages after successful processing. Use `DeleteMessageBatch` for efficiency. For Lambda consumers, successful handler return automatically deletes the message (managed by the Event Source Mapping). Report partial batch failures for Lambda ESM.
- Detection:
  Monitor `ApproximateNumberOfMessagesNotVisible` + `ApproximateNumberOfMessagesVisible` — if both are high and growing, messages are being received but not deleted. DLQ filling up with properly-processed messages is another indicator.
- Impact: Infinite reprocessing, DLQ pollution, compute waste, cost escalation.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html

**Encryption Disabled on Queue**
- Risk Level: CRITICAL
- Why: Violates Security pillar. Unencrypted message bodies at rest expose sensitive data if the underlying storage is compromised. Since SSE-SQS is free and adds no operational overhead, there is zero justification for unencrypted queues in production.
- Instead: Enable SSE-SQS on all queues (`SqsManagedSseEnabled: true`). New queues default to SSE-SQS enabled — legacy queues may need explicit enablement.
- Detection:
  ```bash
  aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names SqsManagedSseEnabled KmsMasterKeyId
  # Alert if both are empty/false
  ```
  AWS Config Rule: custom rule checking encryption attributes across all queues.
- Impact: Data breach (message contents exposed at rest), compliance violation (HIPAA, PCI-DSS, SOC2, GDPR).
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html

---

## Cloud-Native Design Patterns

**Queue-Based Load Leveling**
- Category: Scalability
- Problem: A producer generates messages at a rate that exceeds the consumer's processing capacity during peak periods, causing consumer overload, timeouts, or dropped requests.
- Solution on AWS:
  SQS acts as a buffer between producer (API Gateway, application) and consumer (Lambda, ECS, EC2). Messages accumulate in the queue during peaks and drain during valleys. Consumer scales based on queue depth (ApproximateNumberOfMessagesVisible) rather than producer rate.
- Services Used: Amazon SQS (buffer), AWS Lambda or Amazon ECS (consumer), Amazon CloudWatch (queue-depth-based scaling metric), Application Auto Scaling (consumer scaling)
- When to Apply: Producer rate is bursty (>10x ratio between peak and average). Consumer has fixed throughput limits (database write capacity, third-party API rate limits). Acceptable to trade latency for availability.
- When NOT to Apply: Real-time processing requirement (latency < 100ms end-to-end). Producer needs synchronous response with processing result.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Producer never blocked — always accepts messages | Added end-to-end latency (queue dwell time) |
  | Scalability | Consumer scales independently of producer | Requires monitoring/alerting on queue depth |
  | Cost | No over-provisioning of consumer for peak capacity | SQS per-request charges + storage |
  | Complexity | Simple pattern, well-understood | Need DLQ, visibility timeout tuning, idempotency |

- Complements: Dead-Letter Queue, Circuit Breaker, Auto-Scaling
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_prevent_interaction_failure_loosely_coupled_system.html

**Fan-Out Pattern (SNS → SQS)**
- Category: Communication
- Problem: A single event (order placed, user registered, payment completed) needs to trigger multiple independent downstream processes (send email, update analytics, provision resources) without coupling the producer to each consumer.
- Solution on AWS:
  Producer publishes to an SNS Topic. Multiple SQS queues subscribe to the topic. Each subscriber queue receives a copy of every message. Each consumer processes independently at its own rate, with its own DLQ, scaling, and retry strategy.
- Services Used: Amazon SNS (fan-out hub), Amazon SQS (per-consumer queue), AWS Lambda or Amazon ECS (per-queue consumer)
- When to Apply: Multiple independent services need the same event. Services process at different rates. Adding/removing consumers should not impact the producer. Services have different reliability requirements.
- When NOT to Apply: Single consumer. Consumers need content-based filtering (use EventBridge instead). Consumers need message replay/archive (use EventBridge with archive or Kinesis).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Decoupling | Producer knows nothing about consumers | Additional SNS service + cost |
  | Scalability | Each consumer scales independently | Message duplicated per subscriber (storage cost) |
  | Reliability | One consumer failure doesn't affect others | More queues to monitor and maintain |
  | Flexibility | Add/remove consumers without code changes | SNS message filtering has limits vs EventBridge |

- Complements: Dead-Letter Queue per subscriber, Message Filtering (SNS filter policies), Content-Based Routing
- Source: https://aws.amazon.com/getting-started/hands-on/send-fanout-event-notifications/

**Competing Consumers Pattern**
- Category: Scalability
- Problem: Message processing throughput from a single consumer is insufficient to keep up with production rate. Need to scale processing horizontally while ensuring each message is processed exactly once.
- Solution on AWS:
  Multiple consumer instances (Lambda concurrent executions, ECS tasks, EC2 instances) receive messages from the same SQS queue. SQS's visibility timeout ensures each message is processed by only one consumer at a time. Consumer fleet scales based on queue depth metric.
- Services Used: Amazon SQS (work queue), AWS Lambda (auto-scaling consumers) or Amazon ECS with Application Auto Scaling, Amazon CloudWatch (scaling signal)
- When to Apply: Single consumer cannot keep up with message production rate. Processing is stateless or can be made stateless. Messages are independent (no ordering requirement within Standard queue).
- When NOT to Apply: Strict global ordering required (use FIFO with single Message Group ID — but accept serialization). Messages have complex dependencies requiring orchestration (use Step Functions).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Throughput | Linear scale with consumer count | More infrastructure to manage (unless Lambda) |
  | Reliability | Consumer failure only affects one message | Must handle duplicate delivery (at-least-once) |
  | Cost | Scale precisely to demand | Multiple consumers running concurrently |
  | Ordering | Maximum parallelism | No ordering guarantee (Standard) or per-group ordering only (FIFO) |

- Complements: Queue-Based Load Leveling, Idempotent Consumer, Auto-Scaling
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/queue-messages.html

**Saga Pattern with SQS (Choreography)**
- Category: Data
- Problem: A business transaction spans multiple microservices (e.g., Order → Payment → Inventory → Shipping). Each step must be independently reversible if a subsequent step fails, without requiring a distributed transaction coordinator.
- Solution on AWS:
  Each service publishes completion/failure events to SQS queues. Downstream services listen to queues and react accordingly. On failure, compensating transactions are triggered via the same messaging mechanism. Each service manages its own local transaction + event publication atomically (Transactional Outbox pattern).
- Services Used: Amazon SQS (inter-service communication), Amazon DynamoDB or RDS (local state + outbox table), AWS Lambda (event processing), Amazon SNS (optional fan-out of saga events)
- When to Apply: Business process spans 3+ services. Each step is independently reversible. Services are owned by different teams. Eventual consistency is acceptable.
- When NOT to Apply: Steps < 3 (use simpler request-reply). Strong consistency required across services (consider Step Functions orchestration). Team doesn't have capacity to implement compensating transactions for every step.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Decoupling | Services are fully independent | Saga flow is implicit — harder to visualize |
  | Resilience | Partial failures handled via compensation | Compensation logic adds code complexity |
  | Scalability | Each service scales independently | Debugging distributed failures is difficult |
  | Consistency | Eventual consistency without distributed locks | Intermediate inconsistent states are visible |

- Complements: Dead-Letter Queue (per step), Outbox Pattern, Idempotent Consumer, Circuit Breaker
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/saga-pattern.html

**Priority Queue Pattern**
- Category: Scalability
- Problem: Not all messages have equal urgency. High-priority messages (e.g., payment failures, critical alerts) must be processed before low-priority messages (e.g., analytics events, batch reports) — but a single FIFO queue processes in strict arrival order.
- Solution on AWS:
  Create multiple SQS queues (high-priority, medium-priority, low-priority). Producer routes messages to the appropriate queue based on priority classification. Consumer fleet prioritizes polling from the high-priority queue, then medium, then low. Alternatively: separate consumer pools per priority queue with different scaling policies.
- Services Used: Amazon SQS (multiple priority-level queues), AWS Lambda or Amazon ECS (consumers per priority), Amazon CloudWatch (priority-specific alarms)
- When to Apply: Clear business priority tiers exist. High-priority messages must not wait behind a backlog of low-priority messages. Different SLAs per message type.
- When NOT to Apply: All messages have equal priority. Volume is low enough that a single queue processes all messages within SLA. Adding queue complexity exceeds the benefit.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Latency | High-priority messages processed immediately | Multiple queues to manage and monitor |
  | Complexity | Clear priority separation | Producer must classify priority correctly |
  | Resource utilization | Scale consumers per priority independently | Low-priority queue may starve under load |
  | Cost | Right-sized infrastructure per tier | More queues + consumers = more resources |

- Complements: Queue-Based Load Leveling, Competing Consumers, Auto-Scaling per queue
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/queue-messages.html

**Request-Reply Pattern (Temporary Queue)**
- Category: Communication
- Problem: An asynchronous workflow requires a response to the caller — the producer sends a request message and needs to receive a correlated response, but standard queue patterns are fire-and-forget.
- Solution on AWS:
  Producer creates (or reuses) a reply queue and includes the reply queue URL in the message attributes of the request message. Consumer processes the request and sends the response to the specified reply queue with a correlation ID matching the original request's MessageId. Producer polls the reply queue filtered by correlation ID.
- Services Used: Amazon SQS (request queue + reply queue), message attributes (ReplyTo + CorrelationId)
- When to Apply: Need async request-reply with decoupled services. Synchronous API call is not suitable (long processing, multiple retries). Multiple requests in flight simultaneously.
- When NOT to Apply: Pure fire-and-forget events (no response needed). Real-time request-reply (use API Gateway + Lambda or Step Functions for synchronous). Single request-response (use Step Functions callback pattern).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Decoupling | Producer and consumer communicate without direct connection | Reply queue management complexity |
  | Scalability | Multiple requests in flight concurrently | Correlation logic in producer/consumer code |
  | Reliability | Requests and replies are durable | Reply queue cleanup responsibility |
  | Latency | Async — producer not blocked | Higher end-to-end latency than synchronous |

- Complements: Dead-Letter Queue (for unreplied requests), Correlation ID, Message TTL
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-temporary-queues.html

---

## Security Architecture

**Identity & Access Management for SQS**
- AWS Services: AWS IAM (identity policies), SQS Queue Policies (resource policies), AWS Organizations SCPs (guardrails), VPC Endpoints (network-level restriction)
- Architecture:
  Three-layer access control: (1) IAM identity policies on the producer/consumer role — specify allowed SQS actions and queue ARN resource; (2) SQS resource policy on the queue — specify which principals can interact, with conditions (aws:SourceArn, aws:SourceAccount, aws:sourceVpce); (3) SCP guardrails at the organization level — deny SQS operations without encryption, deny public queue policies. For cross-account access, BOTH the resource policy (on queue) and identity policy (on calling principal) must grant permission.
- Configuration Essentials:
  - Producer IAM role: Allow `sqs:SendMessage`, `sqs:SendMessageBatch` on specific queue ARN only
  - Consumer IAM role: Allow `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:DeleteMessageBatch`, `sqs:ChangeMessageVisibility` on specific queue ARN only
  - Queue policy for SNS integration: Allow `sqs:SendMessage` with condition `aws:SourceArn` = SNS topic ARN
  - Queue policy for S3 integration: Allow `sqs:SendMessage` with condition `aws:SourceAccount` = account ID
  - VPC Endpoint policy: Restrict queue access to specific VPC endpoint ID
- Verification:
  ```bash
  # Check IAM role permissions
  aws iam simulate-principal-policy --policy-source-arn <ROLE_ARN> --action-names sqs:SendMessage --resource-arns <QUEUE_ARN>
  # Check queue policy
  aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names Policy
  # Verify no public access
  aws accessanalyzer list-findings --analyzer-arn <ANALYZER_ARN> --filter '{"resourceType":{"eq":["AWS::SQS::Queue"]}}'
  ```
- Compliance Alignment: SOC2 CC6.1 (logical access controls), PCI-DSS Requirement 7 (restrict access), HIPAA Access Controls (§ 164.312(a))
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-overview-of-managing-access.html

**Data Protection (Encryption)**
- AWS Services: Amazon SQS (SSE-SQS, SSE-KMS), AWS KMS (customer-managed CMKs), AWS CloudTrail (key usage audit)
- Architecture:
  All messages encrypted at rest via SSE-SQS (default) or SSE-KMS (for compliance). In-transit encryption via TLS (mandatory for all SQS API calls — HTTP endpoints deprecated). For SSE-KMS: message bodies encrypted with a Data Key generated from the CMK. Data Key is cached for `KmsDataKeyReusePeriodSeconds` (default 300s, max 86400s) to reduce KMS API calls. Cross-account encrypted queues require KMS key policy granting Decrypt to the consumer's account.
- Configuration Essentials:
  - SSE-SQS: `SqsManagedSseEnabled: true` (default for new queues)
  - SSE-KMS: `KmsMasterKeyId: alias/my-sqs-key` + `KmsDataKeyReusePeriodSeconds: 600`
  - KMS Key Policy for cross-account: Allow `kms:Decrypt`, `kms:GenerateDataKey` to consumer account/role
  - Condition key for enforcing encryption: `"Condition": {"Bool": {"aws:SecureTransport": "true"}}` in queue policy
- Verification:
  ```bash
  aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names SqsManagedSseEnabled KmsMasterKeyId KmsDataKeyReusePeriodSeconds
  ```
- Compliance Alignment: SOC2 CC6.7 (encryption at rest), PCI-DSS Requirement 3 (protect stored data), HIPAA § 164.312(a)(2)(iv) (encryption), GDPR Art. 32 (security of processing)
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html

**Network Security (VPC Endpoints)**
- AWS Services: Amazon VPC (Interface Endpoint for SQS), AWS PrivateLink, Security Groups, VPC Endpoint Policies
- Architecture:
  Create an Interface VPC Endpoint for SQS (`com.amazonaws.<region>.sqs`). All SQS API traffic from resources in the VPC routes through the endpoint privately — never traversing the public internet. VPC Endpoint Policy restricts which queues can be accessed through the endpoint. Security groups on the endpoint ENI control which VPC resources can reach SQS. Queue policy conditions (`aws:sourceVpce`) restrict queue access to specific VPC endpoints only.
- Configuration Essentials:
  - VPC Endpoint: Interface type, `com.amazonaws.<region>.sqs`, private DNS enabled
  - VPC Endpoint Policy: Allow specific queue ARNs only
  - Queue Policy condition: `"Condition": {"StringEquals": {"aws:sourceVpce": "vpce-0123456789abcdef0"}}`
  - Security Group on endpoint: Allow inbound 443 from application subnets only
- Verification:
  ```bash
  aws ec2 describe-vpc-endpoints --filters "Name=service-name,Values=com.amazonaws.*.sqs"
  # Verify endpoint exists with correct policy
  # Test: from within VPC, resolve sqs.<region>.amazonaws.com — should resolve to private IP
  ```
- Compliance Alignment: SOC2 CC6.6 (network controls), PCI-DSS Requirement 1 (firewall/network segmentation), HIPAA § 164.312(e)(1) (transmission security)
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-internetwork-traffic-privacy.html

---

## Operational Patterns

**Observability: SQS Queue Monitoring**
- AWS Services: Amazon CloudWatch (metrics, alarms, dashboards), AWS CloudTrail (API audit), Amazon SNS (alarm notifications)
- Key Metrics:
  - `ApproximateNumberOfMessagesVisible` — messages available for retrieval (queue depth)
  - `ApproximateNumberOfMessagesNotVisible` — messages in-flight (being processed)
  - `ApproximateNumberOfMessagesDelayed` — messages waiting for delay period to expire
  - `ApproximateAgeOfOldestMessage` — time since oldest message was enqueued (processing lag indicator)
  - `NumberOfMessagesSent` — producer throughput
  - `NumberOfMessagesReceived` — consumer throughput
  - `NumberOfMessagesDeleted` — successful processing throughput
  - `NumberOfEmptyReceives` — wasted API calls (short polling indicator)
  - `SentMessageSize` — average message payload size
- Critical Alarms:
  1. DLQ `ApproximateNumberOfMessagesVisible > 0` → immediate alert (failed messages)
  2. Source queue `ApproximateAgeOfOldestMessage > threshold` → processing lag (consumer too slow)
  3. Source queue `ApproximateNumberOfMessagesVisible > threshold` → backlog building (scale consumers)
  4. `NumberOfEmptyReceives / NumberOfMessagesReceived > 0.9` → short polling waste
- Cost Profile: CloudWatch metrics for SQS are free (included with SQS). Custom dashboards and alarms cost standard CloudWatch pricing ($0.10/alarm/month).
- Automation:
  Auto-scale consumers based on `ApproximateNumberOfMessagesVisible` per consumer target. Alert on DLQ arrival for immediate investigation. Auto-disable producer if `ApproximateAgeOfOldestMessage` exceeds system SLA (circuit breaker).
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-available-cloudwatch-metrics.html

**Dead-Letter Queue Operations & Redrive**
- Operational Domain: Incident Management
- AWS Services: Amazon SQS (DLQ, redrive), AWS Lambda (automated analysis), Amazon CloudWatch (DLQ alarms), AWS Console (redrive UI)
- Architecture:
  DLQ messages represent processing failures requiring human analysis. Operational flow: (1) CloudWatch alarm triggers on DLQ message arrival → SNS notification to on-call; (2) Operator inspects DLQ messages (console or CLI) to identify failure pattern; (3) Fix root cause (code bug, downstream service outage, schema change); (4) Redrive messages back to source queue (console UI or StartMessageMoveTask API); (5) Monitor source queue to confirm successful reprocessing.
- Runbook Skeleton:
  1. **Detection**: CloudWatch alarm fires for DLQ `ApproximateNumberOfMessagesVisible > 0`
  2. **Triage**: Inspect first 10 DLQ messages — identify common failure pattern (parse error? downstream timeout? permission denied?)
  3. **Root Cause**: Check source application logs for error correlating with DLQ message timestamps
  4. **Fix**: Deploy code fix or restore downstream dependency
  5. **Redrive**: Use `StartMessageMoveTask` to move DLQ messages back to source queue
  6. **Verify**: Monitor source queue — `ApproximateNumberOfMessagesVisible` should decrease as messages are reprocessed
  7. **Post-mortem**: Document failure mode, add defensive code, improve visibility
- Cost Profile: Low — DLQ is a standard SQS queue with standard pricing. Redrive uses SQS API calls (batched).
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-configure-dead-letter-queue-redrive.html

**Cost Optimization: SQS FinOps**
- Operational Domain: FinOps
- AWS Services: Amazon SQS (cost allocation tags), AWS Cost Explorer (per-queue cost analysis), Amazon CloudWatch (efficiency metrics)
- Architecture:
  SQS pricing is per-request: $0.40 per million Standard requests, $0.50 per million FIFO requests (first 1M/month free). Primary cost levers: (1) Batch operations — up to 10x reduction; (2) Long polling — eliminates empty receive costs; (3) SSE-SQS over SSE-KMS — eliminates KMS API call costs; (4) Right-sized polling frequency — avoid over-polling empty queues.
- Cost Optimization Checklist:
  1. All operations batched (SendMessageBatch, DeleteMessageBatch, ReceiveMessage MaxNumberOfMessages=10)
  2. Long polling enabled (WaitTimeSeconds=20)
  3. SSE-SQS used unless KMS compliance-required
  4. Empty queues not being polled by idle consumers (use Lambda ESM — no polling cost when idle)
  5. Cost allocation tags on all queues (team, service, environment)
  6. Monitor `NumberOfEmptyReceives` — each empty receive costs the same as a message receive
- Cost Profile: Low base cost. SQS becomes cost-significant only at >100M messages/month or with SSE-KMS at high volume.
- Source: https://aws.amazon.com/sqs/pricing/

**High Availability & Disaster Recovery**
- Operational Domain: HA / DR
- RTO/RPO: SQS is a regional service with built-in multi-AZ redundancy. RTO: N/A (service is always available within a region at 99.9%+ SLA). RPO: Messages are stored redundantly across multiple AZs — no data loss within a region.
- AWS Services: Amazon SQS (regional, multi-AZ by default), Amazon SNS (cross-region fan-out for DR), AWS Lambda (cross-region replication)
- Architecture:
  SQS is inherently highly available within a region (multi-AZ storage, no single point of failure). For cross-region DR: (1) Producers dual-write to queues in primary and DR region (active-active); (2) OR use SNS cross-region subscriptions to replicate messages; (3) OR use Lambda to replicate messages from primary to secondary region queue. Note: SQS does NOT have built-in cross-region replication — this must be application-managed.
- Cross-Region DR Pattern:
  - Active-Active: Producer writes to both regions. Consumers in both regions process. Requires idempotency to handle duplicates from dual-write.
  - Active-Passive: Primary region processes. On failover, Route 53 health check redirects producers to secondary region queue. Messages in primary region queue may be lost if region is unrecoverable before retention period.
- Cost Profile: Cross-region replication doubles SQS costs + cross-region data transfer charges. Active-active also doubles consumer compute costs.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html

---

## Reference Architectures

**Decoupled Microservices with SQS**
- Context: Microservices architecture where services communicate asynchronously via message queues to achieve loose coupling, independent scaling, and fault isolation.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | API | API Gateway + Lambda | Accept external requests, validate, publish to SQS |
  | Queue | Amazon SQS (Standard or FIFO) | Buffer and decouple between API layer and processing layer |
  | DLQ | Amazon SQS (DLQ) | Capture failed messages for analysis and redrive |
  | Processing | AWS Lambda (Event Source Mapping) | Process messages, call downstream services |
  | Data | Amazon DynamoDB | Store processing results, idempotency table |
  | Monitoring | CloudWatch + SNS | Queue depth alarms, DLQ alerts, operational dashboards |

- Key Decisions:
  - Standard vs FIFO: Based on ordering requirements per business entity
  - Lambda vs ECS consumer: Based on processing duration and statefulness
  - Batch size: Lambda ESM batch size 10 (standard) or 10 (FIFO with max concurrency per group)
  - Visibility timeout: 6x Lambda function timeout
- Scaling Path:
  Low traffic → single Lambda consumer with default concurrency. Medium traffic → Lambda concurrent executions scale automatically with queue depth. High traffic (>1000 concurrent) → increase Lambda reserved concurrency or migrate to ECS with queue-depth-based auto-scaling. Extreme traffic → multiple queues with partitioned routing.
- Cost Baseline: Low-to-medium. At 1M messages/day: ~$12/month (SQS) + Lambda compute (varies by processing time).
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/queue-messages.html

**Event-Driven Order Processing Pipeline**
- Context: E-commerce order processing where order placement triggers payment, inventory reservation, and fulfillment — each handled by an independent service with different processing characteristics and SLAs.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Ingress | API Gateway + Lambda | Accept order, validate, publish order event |
  | Fan-Out | Amazon SNS | Distribute order event to multiple subscribers |
  | Payment Queue | SQS FIFO (.fifo) | Ordered payment processing per customer (MessageGroupId = customer-id) |
  | Inventory Queue | SQS Standard | Inventory reservation (order doesn't matter, idempotent) |
  | Fulfillment Queue | SQS Standard + Delay (300s) | Ship after payment confirmed (delayed start) |
  | DLQs | SQS (per source queue) | Failed message capture per service |
  | Payment Service | Lambda | Process payment, publish result to SNS |
  | Inventory Service | Lambda | Reserve inventory, update stock table |
  | Fulfillment Service | ECS Fargate | Long-running fulfillment coordination |
  | Data | DynamoDB (orders, idempotency) | Order state, payment idempotency |

- Key Decisions:
  - Payment queue is FIFO (prevent duplicate charges per customer via deduplication + ordering)
  - Inventory queue is Standard (idempotent reservation, throughput over ordering)
  - Fulfillment queue uses 300s delay (wait for payment confirmation before shipping)
  - Each service has independent DLQ and alarm
- Scaling Path:
  Normal: Lambda handles all queues. Peak (Black Friday): Lambda scales automatically. Extreme: consider provisioned concurrency for payment Lambda, ECS horizontal scaling for fulfillment.
- Cost Baseline: Medium. At 100K orders/day: ~$5/month (SQS all queues) + SNS + Lambda + DynamoDB.
- Source: https://aws.amazon.com/getting-started/hands-on/send-fanout-event-notifications/

**SQS + Lambda with Partial Batch Failure Handling**
- Context: Lambda processing batches of SQS messages where some messages in a batch may fail while others succeed — requiring granular failure reporting without reprocessing the entire batch.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Queue | Amazon SQS (Standard or FIFO) | Source queue with messages |
  | DLQ | Amazon SQS | Capture messages that exhaust maxReceiveCount |
  | Consumer | AWS Lambda (Event Source Mapping) | Process message batches with partial failure reporting |
  | Config | Lambda ESM `FunctionResponseTypes: [ReportBatchItemFailures]` | Enable partial batch failure |
  | Monitoring | CloudWatch | Batch success/failure metrics |

- Key Decisions:
  - Enable `ReportBatchItemFailures` on the Event Source Mapping
  - Lambda handler returns `{"batchItemFailures": [{"itemIdentifier": "<messageId>"}]}` for failed messages
  - Only failed messages are retried (not the entire batch)
  - Visibility timeout must exceed function timeout
  - For FIFO queues: failed message blocks subsequent messages in the same Message Group ID
- Scaling Path:
  Adjust `BatchSize` (1-10,000 for Standard, 1-10 for FIFO) and `MaximumBatchingWindowSeconds` (0-300s) to optimize throughput vs latency.
- Cost Baseline: Low. Lambda invocation cost per batch (not per message).
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html

---

## Service Equivalence Map

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **Standard Queue** | SQS Standard | Cloud Tasks | Service Bus Queue (Standard) | OCI Queue |
| **FIFO Queue** | SQS FIFO | Cloud Tasks (with deduplication) | Service Bus Queue (Sessions) | OCI Queue (not FIFO-native) |
| **Pub/Sub Messaging** | SNS | Pub/Sub | Service Bus Topics | OCI Streaming / Notifications |
| **Event Bus** | EventBridge | Eventarc | Event Grid | OCI Events |
| **Streaming** | Kinesis Data Streams | Pub/Sub (streaming mode) | Event Hubs | OCI Streaming |
| **Dead-Letter Queue** | SQS DLQ | Cloud Tasks DLQ | Service Bus DLQ | OCI Queue DLQ |
| **Message Size Limit** | 256 KB (2 GB with Extended Client) | 1 MB (Cloud Tasks) / 10 MB (Pub/Sub) | 256 KB (Standard) / 100 MB (Premium) | 128 KB |
| **Retention** | 4 days (default) / 14 days (max) | 7 days (Cloud Tasks) / 31 days (Pub/Sub) | 14 days (max) | 7 days (max) |
| **Encryption** | SSE-SQS / SSE-KMS | Google-managed / CMEK | Microsoft-managed / CMK | Oracle-managed / Vault |

> **⚠️ Important**: Service equivalence does NOT mean feature parity. SQS Standard's unlimited throughput and at-least-once delivery model differs fundamentally from Azure Service Bus's broker-mediated sessions or Google Cloud Pub/Sub's push-based subscriber model. Always validate integration patterns against specific service documentation.

---

## Provider Differentiators

**SQS Standard Queue — Virtually Unlimited Throughput**
- Category: Messaging
- Unique Value: SQS Standard queues have no practical throughput limit — they support nearly unlimited API calls per second per action (SendMessage, ReceiveMessage, DeleteMessage) without pre-provisioning, capacity planning, or partition management. No other major cloud provider offers an equivalent managed queue with truly unlimited throughput.
- Architecture Impact: Architects can use SQS Standard as a universal buffer without capacity concerns. No need to pre-shard queues, configure partitions, or worry about throughput ceilings. This eliminates an entire category of scaling decisions from architecture design.
- When to Leverage: Any workload where throughput requirements are unpredictable, bursty, or potentially very high (>100K msgs/sec). Load-leveling for unpredictable traffic patterns. Buffer between services with vastly different processing rates.
- Caveat: "Unlimited throughput" applies to the queue's API rate. Per-consumer throughput is still bound by consumer processing speed and concurrency limits (Lambda concurrency, ECS task count). In-flight message limit is ~120,000.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html

**FIFO High-Throughput Mode**
- Category: Messaging
- Unique Value: FIFO high-throughput mode enables up to 70,000 messages/second (with batching) while maintaining strict per-group ordering and exactly-once delivery. This eliminates the historical trade-off between ordering guarantees and throughput that forced architects to choose Standard queues for high-volume workloads.
- Architecture Impact: Architects can now use FIFO queues for high-volume workloads that require ordering (financial transactions, inventory management, multi-tenant operations) without building custom deduplication/ordering layers on top of Standard queues.
- When to Leverage: Workloads needing both high throughput (>300 TPS) AND strict per-entity ordering. Multi-tenant systems where per-tenant ordering is critical. Financial systems requiring both deduplication and ordering.
- Caveat: High-throughput mode requires multiple Message Group IDs (ordering is per-group, not global). Single Message Group ID still caps at 300 TPS. Requires `DeduplicationScope: messageGroup` and `FifoThroughputLimit: perMessageGroupId` settings.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html

**Lambda Event Source Mapping with SQS**
- Category: Compute + Messaging Integration
- Unique Value: Native, zero-infrastructure integration between SQS and Lambda. AWS manages all polling, scaling, error handling, and batch processing. Supports partial batch failure reporting, maximum concurrency limits, and automatic scaling based on queue depth — all without any consumer infrastructure to manage.
- Architecture Impact: Eliminates consumer fleet management entirely. No EC2 instances, no ECS tasks, no polling code, no scaling policies. Architect only defines the business logic; AWS handles the plumbing.
- When to Leverage: Any SQS consumer workload where processing time < 15 minutes and processing is stateless. Particularly effective for variable-load workloads where idle consumer infrastructure would waste money.
- Caveat: 15-minute function timeout limits processing time per message. Cold starts add latency for first message in a batch. VPC-attached Lambda adds network setup latency. Maximum 10 messages per batch for FIFO queues.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html

**SQS Fair Queues (Standard Queue with MessageGroupId)**
- Category: Messaging
- Unique Value: Standard queues now support optional Message Group IDs that enable fair scheduling — messages from different groups are delivered equitably, preventing a single high-volume group from monopolizing consumer capacity. This brings FIFO-like fairness to Standard queues without the throughput or ordering constraints.
- Architecture Impact: Multi-tenant systems can use a single Standard queue while guaranteeing that one noisy tenant doesn't starve message delivery for other tenants. Eliminates the need for per-tenant queues in many scenarios.
- When to Leverage: Multi-tenant systems where per-tenant fairness is needed but strict ordering is not. Workloads where one producer type generates 100x more messages than others but all must be served equitably.
- Caveat: Fair queues are best-effort — not a strict guarantee. Still uses at-least-once delivery. Does not provide ordering within a group (use FIFO for that). Requires consumer to handle the optional MessageGroupId attribute.
- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fair-queues.html

---

## Scenario Coverage

**Standard Case**: Decoupled microservice communication with asynchronous processing
- Approach: API Gateway → Lambda (validate & publish) → SQS Standard Queue → Lambda (Event Source Mapping, batch size 10) → DynamoDB. DLQ with maxReceiveCount=5. CloudWatch alarm on DLQ. Long polling at queue level. SSE-SQS encryption. Batch API operations throughout.
- Key Decisions: Standard vs FIFO (ask: is ordering required per entity?), Lambda vs ECS consumer (ask: is processing > 15 min?), single queue vs fan-out (ask: multiple independent consumers?).

**Edge Case**: Multi-tenant SaaS with per-tenant ordering and 50K+ msgs/sec
- Approach: SQS FIFO with high-throughput mode enabled. MessageGroupId = tenant-id (high cardinality for parallelism). DeduplicationScope = messageGroup. FifoThroughputLimit = perMessageGroupId. Lambda ESM with maximum concurrency per function. Priority routing for premium tenants via separate high-priority FIFO queue.
- Key Considerations: Monitor per-tenant queue depth. Ensure no single tenant's Message Group ID creates a hot partition. Content-based deduplication vs explicit DeduplicationId (prefer explicit if messages may have identical bodies).

**Anti-Pattern Case**: Producer sending messages with `"Principal": "*"` queue policy, no DLQ, short polling, inline credentials
- Clarification: "Does any queue in this architecture have a resource policy with wildcard Principal? Are DLQs configured for all production queues? Is long polling enabled? Are credentials stored outside of message bodies?" — Flag and refuse to deploy until all four issues are resolved. These represent CRITICAL security and reliability risks that must be addressed before production.
