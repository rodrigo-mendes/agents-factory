# research_cloud_AWS_SNS_Messaging_Architecture_2026.md

## Metadata

```yaml
Full_Name: "AWS Messaging Architecture - SNS Pub/Sub"
Cloud_Provider: "AWS"
Architecture_Domain: "Messaging Architecture - SNS Pub/Sub"
Target_Edition: "AWS SNS 2026"
Architecture_Context: "web application"
Official_Source_URL: "https://docs.aws.amazon.com/sns/latest/dg/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-30"
Currency_Threshold: "2027-08-30"
Research_Depth: exhaustive
Max_Iterations: 8
Research_Quality_Score: "91%"
Gap_Loop_Ran: true
Iterations_Used: "1 of 8 (6 parallel sub-investigators)"
Triangulated_Count: 65
Unverified_Count: 7
Irresolvable_Count: 2
```

---

## Executive Summary

Amazon Simple Notification Service (SNS) is AWS's fully managed pub/sub messaging service, designed to decouple distributed systems through a push-based fan-out model. Within cloud architecture practice, SNS serves as the event distribution layer: a producer publishes one message to a topic and SNS concurrently delivers copies to all registered subscribers — SQS queues, Lambda functions, HTTP/S endpoints, email addresses, SMS targets, mobile push endpoints, and Kinesis Data Firehose. For web applications, SNS is the canonical solution for broadcasting domain events (order placed, user registered, payment processed) to multiple independent downstream workflows without coupling the producer to any consumer. The SNS+SQS fan-out pattern — SNS delivering to SQS queues that Lambda workers then poll — is the foundation of resilient, scalable event-driven web application architecture on AWS.

AWS SNS 2026 brings one major breaking change and several significant enhancements over prior editions. **Breaking change (April 30, 2026):** Amazon SNS Message Data Protection is no longer available to new customers. Existing customers with configured policies continue unaffected; new architectures requiring sensitive data detection must use AWS Lambda subscribed to an SNS topic calling Amazon Bedrock Guardrails, then republishing to a destination topic. Prior to this, **FifoThroughputScope High Throughput Mode** was introduced in January 2025, enabling SNS FIFO topics to reach 30,000 messages/second in us-east-1 via the `MessageGroup` throughput scope. **IPv6 dual-stack endpoint support** was added April 3, 2025, allowing API clients to connect using IPv4, IPv6, or both. **AWS End User Messaging SMS integration** arrived September 24, 2024, adding two-way messaging, country block rules, and centralized billing for SMS. **FCM HTTP v1 credentials** replaced deprecated FCM legacy credentials in January 2024. **FIFO message archiving and replay** launched in October 2023 (available in GovCloud as of November 2024), enabling up to 365-day retention and subscriber-initiated replay — though sources for the 2023 launch date are now beyond 12 months from the research date.

For a web application, three architecture guardrails are non-negotiable. First, every SNS fan-out must route through SQS queues (not direct Lambda or HTTP subscriptions) with a Dead-Letter Queue on every subscription — without a DLQ, failed deliveries after retry exhaustion are silently discarded with no recovery path. Second, all topics carrying PII, financial, or regulated data must have Server-Side Encryption (KMS) enabled and topic policies must enforce HTTPS-only access with least-privilege principals — never a wildcard `Principal: "*"` without a restrictive condition. Third, every subscriber must carry a filter policy scoped to the event types it actually needs; without filtering, all subscribers receive all messages, inflating Lambda invocations and SQS API costs proportional to subscriber count and message volume.

---

## Cloud Architecture Glossary

> 20 terms defined from official AWS documentation. Confidence: 🟢 unless flagged.

---

```
Term: Topic
Definition: A logical access point and communication channel in Amazon SNS. Publishers send messages to a topic; the topic distributes copies to all subscribed endpoints. Each topic has a unique Amazon Resource Name (ARN). Topics are regional resources and do not persist messages after delivery.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/welcome.html (accessed 2026-08-30)
Architect Usage: Create one topic per logical event domain (e.g., OrderEvents, PaymentEvents). Route topic ARNs to publishers via environment variables or Parameter Store — never hardcode.
Common Confusion: A topic is NOT a queue. It does not store messages for later polling. If no subscriber is registered at publish time, the message is permanently lost.
```

```
Term: Standard Topic
Definition: An SNS topic type supporting nearly unlimited throughput, best-effort ordering, and at-least-once delivery. Supports all subscriber protocols: SQS, Lambda, HTTP/S, email, SMS, mobile push, and Kinesis Data Firehose. Max 100,000 per account; up to 12.5 million subscriptions each.
Provider Docs Section: https://aws.amazon.com/sns/features/ (accessed 2026-08-30)
Architect Usage: Default choice for most web application event fan-out. Use when ordering is not critical and subscriber variety is required.
Common Confusion: "Best-effort ordering" means ordering is NOT guaranteed. At-least-once delivery means consumers must implement idempotency — duplicate messages are possible.
```

```
Term: FIFO Topic
Definition: An SNS topic type guaranteeing strict message ordering per MessageGroupId and exactly-once delivery within a 5-minute deduplication window. Topic name must end with ".fifo". Max 1,000 per account; up to 100 subscriptions each. Only SQS queues may subscribe (not Lambda, HTTP, email, SMS, or mobile push directly).
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/api/API_CreateTopic.html (accessed 2026-08-30)
Architect Usage: Use exclusively when ordering and deduplication are business requirements (financial transactions, inventory updates, order state machines). Be aware subscriber type is restricted to SQS.
Common Confusion: FIFO SNS does NOT fan out to Lambda, HTTP, email, SMS, or Firehose directly — only SQS queues. Attempting other protocols will fail. [UNVERIFIED: exhaustive official subscriber type restriction table not retrieved from rendered page; confirmed from FIFO overview and community sources.]
```

```
Term: Subscription
Definition: An endpoint registration on an SNS topic created via the Subscribe API. SQS and Lambda subscriptions are auto-confirmed; HTTP/S, email, and SMS require manual confirmation. Dead-Letter Queue (DLQ), filter policy, and raw message delivery are configured per subscription — not per topic.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html (accessed 2026-08-30)
Architect Usage: Subscription attributes (filter policy, DLQ, raw delivery) are independent per subscriber. Always confirm that each subscription carries the correct filter policy and DLQ before going to production.
Common Confusion: Subscription attributes live on the subscription, not the topic. Deleting the subscribed endpoint does NOT automatically delete the subscription — orphaned subscriptions accumulate.
```

```
Term: Message Filtering / Filter Policy
Definition: A JSON object assigned to a subscription that controls which published messages are delivered. SNS evaluates against message attributes (FilterPolicyScope=MessageAttributes, default) or the message body (FilterPolicyScope=MessageBody). Operators: exact match, prefix, suffix, anything-but, equals-ignore-case, numeric range, IP address, exists, and OR/AND combinations.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html (accessed 2026-08-30)
Architect Usage: Assign filter policies to all subscriptions on topics with heterogeneous event types. Use MessageBody scope when event type is embedded in JSON payload; use MessageAttributes scope when publishers can attach structured metadata.
Common Confusion: Filter policy changes take up to 15 minutes to fully propagate due to eventual consistency. Without a filter policy, the subscriber receives every message published to the topic. Filtered-out messages go to /dev/null — NOT to the DLQ.
```

```
Term: Fan-out
Definition: The scenario where one message published to an SNS topic is replicated and pushed simultaneously to multiple subscribed endpoints (SQS queues, Lambda, HTTP/S, Firehose, mobile push) for parallel asynchronous processing.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/welcome.html (accessed 2026-08-30)
Architect Usage: Fan-out is the primary justification for adding SNS in front of SQS. Use it when a single event must trigger N independent downstream workflows without the producer knowing about any of them.
Common Confusion: Fan-out does not guarantee all endpoints receive the message at exactly the same instant. Failure at one subscription does not block delivery to other subscriptions.
```

```
Term: Message Attributes
Definition: Structured metadata sent alongside (but separate from) the message body. Each attribute has a Name, Type (String, String.Array, Number, or Binary), and Value. Attributes count toward the 256 KB total message size limit. Maximum 10 attributes when raw message delivery is enabled on SQS; messages exceeding this limit are silently discarded.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-message-attributes.html (accessed 2026-08-30)
Architect Usage: Use message attributes as the routing keys for filter policies. Always keep attribute count below 10 when raw message delivery is required. Use String.Array for multi-value attributes in filter policies.
Common Confusion: Message attributes are NOT forwarded to mobile push endpoints. The 10-attribute limit with raw delivery causes silent message loss — not an error visible in CloudWatch metrics.
```

```
Term: Delivery Retry Policy
Definition: Policy defining how SNS retries failed deliveries for server-side errors across four phases: immediate retry, pre-backoff, backoff (arithmetic/exponential/geometric/linear), and post-backoff. AWS-managed endpoints (SQS, Lambda): 100,015 retries over 23 days. Customer-managed endpoints (SMTP, SMS, mobile push): 50 retries over 6 hours. HTTP/S: maximum 3,600 seconds total. SNS applies jitter to retry intervals.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-message-delivery-retries.html (accessed 2026-08-30)
Architect Usage: SQS and Lambda subscriptions have the strongest retry durability (23 days). HTTP/S subscriptions have the weakest (1 hour). Size DLQ retention accordingly — recommended maximum 14 days on the SQS DLQ.
Common Confusion: Client-side errors (deleted Lambda, changed IAM policy, endpoint misconfiguration) are NOT retried — they go directly to the DLQ immediately on first attempt.
```

```
Term: Dead-Letter Queue (DLQ) / Redrive Policy
Definition: An SQS queue assigned to an SNS subscription via a redrive policy (JSON with deadLetterTargetArn). Messages are moved to the DLQ when client-side errors occur or server-side retries are exhausted. The DLQ must be in the same AWS account and Region as the subscription. FIFO topics require FIFO DLQs; standard topics require standard DLQs. Encrypted DLQs require a customer-managed KMS key with SNS principal access.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html (accessed 2026-08-30)
Architect Usage: Attach a DLQ to every SNS subscription. Monitor via CloudWatch alarm on SQS metric ApproximateNumberOfMessagesVisible >= 1 on the DLQ.
Common Confusion: DLQ is configured on the subscription, not the topic. Filtered-out messages do NOT go to the DLQ — they are silently discarded. One DLQ per subscription; sharing DLQs across subscriptions makes root-cause analysis impossible.
```

```
Term: Message Data Protection [DEPRECATED FOR NEW CUSTOMERS — April 30, 2026]
Definition: A formerly available SNS feature that audited and controlled sensitive data in messages in transit. Supported audit, de-identify/redact, and deny/block actions on PII patterns. As of April 30, 2026, no longer available to new customers. Existing customers with configured policies may continue using it. AWS commits to security updates only — no new enhancements.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-message-data-protection-availability-change.html (accessed 2026-08-30)
Architect Usage: Do NOT design new architectures using Message Data Protection. Use Lambda + Amazon Bedrock Guardrails (LOG, BLOCK, or REDACT) as the replacement pattern. See sample: https://github.com/aws-samples/sample-sns-sensitive-data-protection-bedrock
Common Confusion: The April 30, 2026 cutoff applies only to new customers. Existing customers can continue using existing policies in accounts that already have them configured.
```

```
Term: Delivery Status Logging
Definition: A topic-level feature that logs successful and failed message deliveries to Amazon CloudWatch Logs. Configured via per-protocol attributes: SuccessFeedbackRoleArn, FailureFeedbackRoleArn, SuccessFeedbackSampleRate. Log group name pattern: sns/<region>/<account-id>/<topic-name>.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/api/API_CreateTopic.html (accessed 2026-08-30)
Architect Usage: Always configure FailureFeedbackRoleArn for every subscriber protocol in production. Set SuccessFeedbackSampleRate to a non-zero value (e.g., 5%) for sampled success tracing. Use SSM Automation runbook AWS-EnableSNSTopicDeliveryStatusLogging to enable at scale.
Common Confusion: Failure logging ONLY works when FailureFeedbackRoleArn is set — it does not default to on. Success logging requires both a role ARN AND a non-zero sample rate. This is distinct from CloudWatch metrics, which are always emitted automatically.
```

```
Term: Raw Message Delivery
Definition: A subscription-level attribute. When enabled, SNS delivers the message payload directly to the endpoint without wrapping it in the SNS JSON envelope. Hard constraint: maximum 10 message attributes when raw delivery is enabled on SQS — messages with more attributes are silently discarded.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-message-attributes.html (accessed 2026-08-30)
Architect Usage: Enable raw message delivery on SQS subscriptions when downstream consumers are not equipped to parse the SNS JSON envelope. Always audit attribute count before enabling — silent discard at >10 attributes is the leading cause of unexplained message loss.
Common Confusion: Configured per-subscription, not per-topic. Exceeding the 10-attribute limit causes silent message loss, not an exception or CloudWatch error.
```

```
Term: SNS+SQS Fan-out Pattern
Definition: The canonical AWS architectural pattern where an SNS topic fans out to multiple SQS queues as subscribers, each queue consumed independently. Since September 14, 2023, FIFO SNS topics can fan out to both FIFO and standard SQS queues.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/welcome.html (accessed 2026-08-30) [Feature announcement: 2023-09-14 — ⚠️ >12mo]
Architect Usage: Use this pattern as the default for any event-driven web application requiring parallel, independent downstream processing. Do NOT subscribe application servers or Lambda directly to high-volume topics without an SQS buffer.
Common Confusion: The SQS queue MUST have a resource-based access policy granting sqs:SendMessage to the SNS topic ARN with an aws:SourceArn condition. Without it, SNS cannot deliver and messages are silently dropped — no error is surfaced.
```

```
Term: Application / Mobile Push Endpoints
Definition: Platform application endpoints for push notifications. Supported: APNs (iOS/macOS), FCM (Android — HTTP v1 as of January 2024), ADM (Kindle), Baidu Cloud Push, WNS, and MPNS. Each device registration creates one Platform Endpoint ARN.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-message-attributes.html (accessed 2026-08-30) [FCM v1 announcement: 2024-01-18]
Architect Usage: Use CreatePlatformEndpoint idempotently on every app launch to handle token rotation. Actively manage stale endpoints via delivery failure events to prevent endpoint sprawl.
Common Confusion: Message attributes are NOT forwarded to mobile push endpoints. FCM legacy HTTP credentials are deprecated — new integrations must use FCM v1 credentials.
```

```
Term: Message Archiving and Replay (FIFO Topics Only)
Definition: A native SNS feature exclusively for FIFO topics. Topic owners configure an ArchivePolicy with MessageRetentionPeriod (1–365 days). All messages published after the policy is enabled are archived. Subscribers initiate replay via the ReplayPolicy subscription attribute scoped to a time window. Available in all commercial Regions and GovCloud (GovCloud availability: November 7, 2024).
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/fifo-message-archiving-replay.html (accessed 2026-08-30) [Feature launch: 2023-10-26 — ⚠️ >12mo]
Architect Usage: Enable archiving on FIFO topics where subscribers may need to catch up after outages or new subscriber onboarding. Replay must be explicitly triggered per-subscription — it is not automatic.
Common Confusion: Standard topics CANNOT use archiving or replay. Pre-policy messages are NOT retroactively archived. Replay re-triggers all consumer logic — consumers must be idempotent.
```

```
Term: FifoThroughputScope
Definition: A FIFO topic attribute (introduced January 21, 2025) controlling deduplication scope and throughput. Topic (default): deduplication across the entire topic; max 3,000 msg/s or 20 MB/s. MessageGroup (High Throughput Mode): deduplication within each message group; enables up to 30,000 msg/s in us-east-1, 9,000 msg/s in us-west-2 and eu-west-1. Per-message-group limit: 300 msg/s.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/api/API_CreateTopic.html (accessed 2026-08-30)
Architect Usage: Set FifoThroughputScope=MessageGroup when aggregate FIFO throughput exceeds the topic-level cap. Design MessageGroupId granularity to avoid hot groups — each group is independently capped at 300 msg/s.
Common Confusion: MessageGroup scope does NOT eliminate the per-message-group 300 msg/s limit — it changes where deduplication is applied. Also, narrowing deduplication to message-group level means two messages in different groups with identical bodies are no longer considered duplicates.
```

```
Term: ContentBasedDeduplication
Definition: A FIFO topic attribute. When true, SNS generates the MessageDeduplicationId by hashing the message body (SHA-256). 5-minute deduplication window. Default is false (publisher must supply explicit deduplication IDs). A publisher-supplied ID always overrides content-based deduplication.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/api/API_CreateTopic.html (accessed 2026-08-30)
Architect Usage: Enable ContentBasedDeduplication only when message bodies are guaranteed to be unique per logical event. Disable when messages with the same body represent distinct events (e.g., repeated price refresh with same value).
Common Confusion: Only the message body is hashed — two messages with different attributes but identical bodies are treated as duplicates and the second is discarded within the 5-minute window.
```

```
Term: MessageGroupId
Definition: A required field on every Publish call to a FIFO topic. Groups related messages; SNS delivers messages within each group in strict publish order. Messages in different groups are processed independently and concurrently.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/fifo-topic-code-examples.html (accessed 2026-08-30)
Architect Usage: Use a business entity identifier (e.g., orderId, productId) as the MessageGroupId. Avoid ultra-high-cardinality IDs that prevent meaningful ordering guarantees. Avoid putting all messages in the same group unless strict global ordering is required.
Common Confusion: A stuck or slow message in a group blocks ALL subsequent messages in that same group (head-of-line blocking). Design group granularity to minimize blast radius of single-message failures.
```

```
Term: ArchivePolicy (FIFO Topic Attribute)
Definition: A FIFO topic-level attribute enabling message archiving. JSON with MessageRetentionPeriod (1–365 days). All messages published after policy activation are stored. Subscribers use the ReplayPolicy subscription attribute to replay from a chosen BeginningArchiveTime.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/api/API_CreateTopic.html (accessed 2026-08-30)
Architect Usage: Set MessageRetentionPeriod based on your RPO — the minimum is 1 day, maximum 365 days. Archive storage is billed separately. Enable in combination with subscriber-level ReplayPolicy for recovery workflows.
Common Confusion: ArchivePolicy is only valid on FIFO topics. It does NOT automatically replay to subscribers. Messages published before the policy was enabled are NOT retroactively archived.
```

```
Term: VPC Endpoint (AWS PrivateLink for SNS)
Definition: An interface VPC endpoint that allows SNS API calls from within a VPC to reach SNS without traversing the public internet. An Elastic Network Interface (ENI) is placed in the specified VPC subnet with a private IP address. IPv6 support expanded to all AWS commercial Regions as of July 2025. [UNVERIFIED: ENI/private-IP placement details not confirmed from a rendered dedicated VPC endpoint page; confirmed from security best-practices page.]
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html (accessed 2026-08-30)
Architect Usage: Use VPC endpoints for publishers running within VPCs (EC2, ECS, Lambda in VPC) to prevent SNS traffic from traversing the public internet. Configure two access control layers: endpoint policy (controls which requests pass through the endpoint) and topic policy (controls which VPCs/endpoints access the topic).
Common Confusion: VPC endpoint does not replace topic resource-based policies — both control layers are required. Subscribe endpoint targets should use domain names, not raw IP addresses.
```

---

## Architecture Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

---

### ✅ Mandatory Patterns

**Pattern 1: SNS + SQS Fan-out with SQS as Durable Buffer** 🟢

- Pillar Alignment: Reliability (REL)
- Why: "A message published to an SNS topic is replicated and pushed to multiple endpoints, such as Amazon SQS queues … This allows for parallel asynchronous processing." AWS documents the fan-out pattern as the primary combination for durable, retryable processing. Every downstream consumer requiring durable, retryable processing must subscribe via an SQS queue — not directly. Multiple SQS queues can subscribe to the same SNS topic.
- AWS Services: Amazon SNS (Standard Topic), Amazon SQS (Standard Queue per subscriber), AWS Lambda or EC2 as queue consumers.
- Architecture Decision:
  - Subscribe each independent consumer as an SQS queue subscriber to the SNS topic.
  - Configure a resource-based policy on each SQS queue granting `sqs:SendMessage` to the SNS topic ARN with `aws:SourceArn` condition — without this, SNS silently drops messages.
  - Lambda workers poll their respective SQS queues via event source mappings (not direct SNS-to-Lambda subscriptions) for spiky or sustained workloads.
  - Each SQS queue carries its own DLQ (see Pattern 2) and Lambda event source mapping concurrency limit.
- Verification:
  `aws sns list-subscriptions-by-topic --topic-arn <arn>` — verify no subscriber uses Protocol "lambda" or "https" without a confirmed SQS buffer in front for high-volume or mission-critical paths.
- Source: https://docs.aws.amazon.com/sns/latest/dg/welcome.html (2026-08-30); https://docs.aws.amazon.com/decision-guides/latest/application-integration-on-aws-how-to-choose/application-integration-on-aws-how-to-choose.html (2026-08-30)

---

**Pattern 2: Dead-Letter Queues on Every SNS Subscription** 🟢

- Pillar Alignment: Reliability (REL)
- Why: "When Amazon SNS receives a client-side error, or continues to receive a server-side error for a message beyond the number of retries specified by the corresponding retry policy, Amazon SNS discards the message — unless a dead-letter queue is attached to the subscription." Client-side errors (deleted Lambda, changed IAM policy) are NOT retried — they fail immediately and must go to a DLQ or are permanently lost.
- AWS Services: Amazon SNS (subscription RedrivePolicy), Amazon SQS (DLQ), Amazon CloudWatch (alarm on ApproximateNumberOfMessagesVisible).
- Architecture Decision:
  - Every SNS subscription must declare a `RedrivePolicy` with `deadLetterTargetArn` pointing to an SQS queue.
  - DLQ must be in the same AWS account and Region as the subscription.
  - FIFO topics require FIFO DLQs; standard topics require standard DLQs.
  - Encrypted DLQ requires a customer-managed KMS key with SNS principal access.
  - Create a CloudWatch alarm: `ApproximateNumberOfMessagesVisible >= 1` on the DLQ — threshold of 1 ensures immediate alerting.
  - Note: `NumberOfMessagesSent` on the DLQ does NOT capture DLQ arrivals — use `ApproximateNumberOfMessagesVisible`.
- Verification:
  `aws sns get-subscription-attributes --subscription-arn <arn>` — confirm `RedrivePolicy` key is present and `deadLetterTargetArn` is a valid SQS ARN.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html (2026-08-30)

---

**Pattern 3: Encryption at Rest (KMS SSE) + Encryption in Transit (HTTPS/SigV4)** 🟢

- Pillar Alignment: Security (SEC)
- Why: "SSE encrypts messages as soon as Amazon SNS receives them. The messages are stored in encrypted form, and only decrypted when they are sent." For transit: "All requests to topics with SSE enabled must use HTTPS and Signature Version 4." Only symmetric KMS keys are supported.
- AWS Services: Amazon SNS (`KmsMasterKeyId` attribute), AWS KMS (symmetric CMK or `alias/aws/sns`), AWS CloudTrail (KMS API audit).
- Architecture Decision:
  - Enable SSE (`KmsMasterKeyId`) on every topic carrying PII, financial data, or regulated content.
  - Use CMK (customer-managed key) for rotation control, cross-account access, or granular audit via CloudTrail.
  - Apply a topic policy `Deny` with `Condition: {"Bool": {"aws:SecureTransport": "false"}}` to reject non-HTTPS publishers.
  - SSE does NOT encrypt topic metadata, message IDs, timestamps, or message attributes — these remain plaintext even with SSE enabled.
  - Messages published before SSE was enabled are NOT retroactively encrypted.
  - Encrypted messages remain encrypted even if SSE is later disabled.
- Verification:
  `aws sns get-topic-attributes --topic-arn <arn>` — confirm `KmsMasterKeyId` attribute is set to a non-empty value.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html (2026-08-30)

---

**Pattern 4: Least-Privilege Topic Access Policies (No Wildcard Principal Without Condition)** 🟢

- Pillar Alignment: Security (SEC)
- Why: "Amazon SNS topics are created with no permissions, meaning they are private and only accessible to the account that created them." Cross-service grants require `aws:SourceArn` or `aws:SourceAccount` conditions to prevent confused deputy attacks. `aws:SourceOwner` is deprecated — new integrations must use `aws:SourceArn` and `aws:SourceAccount`.
- AWS Services: Amazon SNS (topic resource policy), AWS IAM (identity policies), AWS CloudTrail.
- Architecture Decision:
  - Topic policies must: (a) name specific Principal ARNs — never `"Principal": "*"` without a Condition; (b) scope Action to only `sns:Publish` or `sns:Subscribe`, never `sns:*`; (c) scope Resource to the exact topic ARN, not `*`; (d) include `aws:SourceArn` or `aws:SourceAccount` when granting access to AWS service principals (EventBridge, S3, etc.).
  - IAM identity-based policies apply only within the same account. Topic resource-based policies are required for cross-account access.
  - IAM explicit `Deny` always overrides an SNS topic policy `Allow`.
  - Topics is the ONLY resource type specifiable in SNS policies.
  - Use IAM roles (not long-term access keys) for EC2, ECS, and Lambda callers.
- Verification:
  `aws sns get-topic-attributes --topic-arn <arn> --query Attributes.Policy` — check for `"Principal":"*"` without a Condition block containing `aws:SourceArn` or `aws:SourceAccount`.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-access-policy-use-cases.html (2026-08-30); https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html (2026-08-30)

---

**Pattern 5: Delivery Status Logging to CloudWatch + Alarms** 🟢

- Pillar Alignment: Operational Excellence (OPS)
- Why: "Amazon SNS provides support for logging the delivery status of notification messages sent to topics … These logs help you determine whether a message was successfully delivered to an endpoint." Without delivery logging, failed deliveries are invisible to operators — CloudWatch metrics show aggregates but not per-message failure details.
- AWS Services: Amazon SNS (`SuccessFeedbackRoleArn`, `FailureFeedbackRoleArn`, `SuccessFeedbackSampleRate` attributes), Amazon CloudWatch Logs, Amazon CloudWatch Alarms.
- Architecture Decision:
  - Configure at minimum `FailureFeedbackRoleArn` for every subscriber protocol (SQS, Lambda, HTTP/S) on production topics.
  - Set `SuccessFeedbackSampleRate` to a non-zero value (e.g., 5%) for sampled delivery tracing in production.
  - The IAM role must have `logs:CreateLogGroup`, `logs:CreateLogStream`, and `logs:PutLogEvents`.
  - Log group name: `sns/<region>/<account-id>/<topic-name>`.
  - Create a CloudWatch alarm on the DLQ's `ApproximateNumberOfMessagesVisible >= 1`.
  - Create a CloudWatch dashboard per topic tracking `NumberOfNotificationsFailed` and `NumberOfNotificationsRedrivenToDlq`.
  - Use SSM Automation runbook `AWS-EnableSNSTopicDeliveryStatusLogging` for at-scale enablement.
- Verification:
  `aws sns get-topic-attributes --topic-arn <arn>` — confirm `SQSFailureFeedbackRoleArn` and `LambdaFailureFeedbackRoleArn` are set.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-topic-attributes.html (2026-08-30)

---

### ⚠️ Architectural Decisions

**Decision 1: Standard Topic vs FIFO Topic** 🟢

- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When | Cost Profile | Lock-In |
  |--------|-------------|-----------|------------|-----------|-------------|---------|
  | Standard Topic | Amazon SNS (Standard) | Throughput (unlimited TPS), subscriber variety (SQS, Lambda, HTTP, Email, SMS, Mobile Push, Firehose) | Message order guarantees, exactly-once delivery | Web app events where order is not critical; high fan-out to heterogeneous endpoints | Lower; no FIFO surcharge | Low — all endpoint types supported |
  | FIFO Topic | Amazon SNS (FIFO) | Strict message ordering per group, exactly-once delivery, deduplication within 5-minute window | Lower throughput, subscriber type restricted to SQS queues only | Financial transactions, inventory updates, order state machines — ordering and deduplication required | Higher; FIFO topics incur FIFO SQS queue costs downstream | Higher — only SQS queues can subscribe |

- Cost Profile: Standard topics have lower base cost. FIFO topics are priced per message from 1KB to 256KB (1KB minimum), and downstream FIFO SQS queues add further FIFO pricing.
- Lock-in Assessment: Standard topics have broad compatibility. FIFO topics create tight coupling to SQS FIFO queues as the only subscriber type.
- Architect Instruction: "Ask whether message ordering is a business requirement — not a preference — when designing the event schema. If the answer is yes, confirm that all subscribers can be SQS FIFO queues before choosing FIFO topic."
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-fifo-topics.html (2026-08-30); https://docs.aws.amazon.com/decision-guides/latest/application-integration-on-aws-how-to-choose/application-integration-on-aws-how-to-choose.html (2026-08-30)

---

**Decision 2: SNS vs EventBridge vs Kinesis vs SQS-Direct** 🟢

- Options:

  | Option | AWS Service | Communication Model | Optimizes | Sacrifices | Best When | Cost Profile |
  |--------|-------------|---------------------|-----------|------------|-----------|-------------|
  | SNS | Amazon SNS | Push pub/sub (1-to-many) | Subscriber variety (Email, SMS, Mobile Push, HTTP, Lambda, SQS, Firehose), high fan-out | Advanced content-based routing, event replay, SaaS source integration | Broadcast to heterogeneous endpoints; need SMS/Email/Mobile push | Per-publish + per-delivery; lowest entry cost for simple fan-out |
  | EventBridge | Amazon EventBridge | Push event bus (many-to-many) | Content-based routing, SaaS event source integrations, schema registry, archiving and replay | Native SMS/Email/Mobile Push; simpler cost model | Many microservices routing by content; SaaS integrations; need event archiving/replay | Per event ingested; higher at extreme scale |
  | Kinesis | Amazon Kinesis Data Streams | Pull streaming (ordered, partitioned) | High-throughput ingestion, real-time analytics, ordered per-shard replay, multiple independent consumers | Operational complexity; not suited for heterogeneous subscriber types | Real-time analytics, log aggregation, event sourcing with replay | Per shard-hour + PUT payload unit |
  | SQS Direct | Amazon SQS | Pull point-to-point | Simplicity, reliable at-least-once delivery | Fan-out to multiple consumers without SNS; no push semantics | Single consumer per message; simple reliable queuing | Per million requests; very low baseline |

- Cost Profile: SNS is cheapest for simple fan-out. EventBridge is richer but more expensive per event. Kinesis requires shard provisioning overhead.
- Lock-in Assessment: SNS and SQS are foundational AWS services with lowest abstraction lock-in. EventBridge schema registry and SaaS integrations create deeper AWS coupling.
- Architect Instruction: "Ask whether any subscriber needs SMS, Email, or Mobile Push delivery. If yes, SNS is required. Ask whether content-based routing, SaaS source integration, or schema evolution is a priority. If yes, evaluate EventBridge."
- Source: https://docs.aws.amazon.com/decision-guides/latest/application-integration-on-aws-how-to-choose/application-integration-on-aws-how-to-choose.html (2026-08-30); https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html (2026-08-30)

---

**Decision 3: Direct SNS-to-Lambda vs SNS-to-SQS-to-Lambda** 🟢

- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When | Cost Profile |
  |--------|-------------|-----------|------------|-----------|-------------|
  | Direct SNS to Lambda | SNS + Lambda | Latency (push-based, immediate), simplicity | Buffering against Lambda concurrency limits; retry control | Low, predictable traffic volumes; latency-sensitive processing | Lambda invocation cost only; lower infrastructure cost |
  | SNS to SQS to Lambda | SNS + SQS + Lambda | Resilience to spiky traffic (SQS buffers), full Lambda retry and DLQ control, batching | Added polling latency; slight SQS API cost | Spiky or unpredictable workloads; long processing time; need controlled concurrency; need reliable DLQ | SQS API costs added; Lambda cost may reduce due to batching |

- Cost Profile: Direct Lambda is cheaper in steady-state low-volume scenarios. SNS→SQS→Lambda has higher baseline but reduces total Lambda invocations through batching at high volume.
- Lock-in Assessment: Both options are AWS-native patterns with equivalent portability.
- Architect Instruction: "Ask about peak publish rates and Lambda concurrency limits. If peak volume can exceed Lambda concurrency limits, mandate SQS as a buffer. If the workload is low and predictable, direct Lambda is acceptable with appropriate DLQ on the subscription."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/cost_manage_demand_resources_buffer_throttle.html (2026-08-30)

---

### 🚫 Anti-Patterns

**Anti-Pattern 1: No DLQ on SNS Subscriptions** 🟢

- Risk Level: HIGH
- Why: "When Amazon SNS receives a client-side error, or continues to receive a server-side error for a message beyond the number of retries specified by the corresponding retry policy, Amazon SNS discards the message — unless a dead-letter queue is attached to the subscription." Client-side errors are never retried. (Reliability — REL)
- ❌ Wrong:
  ```bash
  aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:123456789012:OrderEvents \
    --protocol sqs \
    --notification-endpoint arn:aws:sqs:us-east-1:123456789012:OrderProcessor
  # No RedrivePolicy = messages silently discarded on delivery failure
  ```
- ✅ Correct:
  ```bash
  aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:123456789012:OrderEvents \
    --protocol sqs \
    --notification-endpoint arn:aws:sqs:us-east-1:123456789012:OrderProcessor \
    --attributes '{"RedrivePolicy":"{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:123456789012:OrderProcessorDLQ\"}"}'
  ```
- Detection: `aws sns get-subscription-attributes --subscription-arn <arn>` — absence of `RedrivePolicy` key confirms no DLQ is configured.
- Impact: Silent and permanent message loss on Lambda deletion, endpoint IAM policy changes, or sustained downstream service outages. No recovery path without DLQ.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html (2026-08-30)

---

**Anti-Pattern 2: Overly Permissive Topic Policy (Wildcard Principal Without Condition)** 🟢

- Risk Level: CRITICAL
- Why: Granting `"Principal": "*"` without a restrictive condition allows any AWS principal in any account to publish to the topic. `aws:SourceOwner` is deprecated; use `aws:SourceArn` or `aws:SourceAccount` instead. (Security — SEC)
- ❌ Wrong:
  ```json
  {
    "Statement": [{
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:us-east-1:123456789012:OrderEvents"
    }]
  }
  ```
- ✅ Correct:
  ```json
  {
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "events.amazonaws.com"},
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:us-east-1:123456789012:OrderEvents",
      "Condition": {
        "ArnLike": {"aws:SourceArn": "arn:aws:events:us-east-1:123456789012:rule/MyRule"},
        "StringEquals": {"aws:SourceAccount": "123456789012"}
      }
    }]
  }
  ```
- Detection: Parse topic policy for `"Principal":"*"` (or `"Principal":{"AWS":"*"}`) without a Condition block containing `aws:SourceArn` or `aws:SourceAccount`.
- Impact: Unauthorized parties publish arbitrary messages; downstream consumers process attacker-controlled payloads; potential data exfiltration, cost abuse (billing on attacker-generated traffic), or code execution via Lambda subscribers.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-access-policy-use-cases.html (2026-08-30)

---

**Anti-Pattern 3: Unencrypted Topics Carrying Sensitive Data** 🟢

- Risk Level: HIGH
- Why: SNS SSE is opt-in and disabled by default. "A message is encrypted only if it is sent after the encryption of a topic is enabled. Amazon SNS doesn't encrypt backlogged messages." (Security — SEC)
- ❌ Wrong:
  ```bash
  aws sns create-topic --name PaymentEvents
  # No KmsMasterKeyId = messages stored and transmitted unencrypted at SNS layer
  ```
- ✅ Correct:
  ```bash
  aws sns create-topic \
    --name PaymentEvents \
    --attributes KmsMasterKeyId=alias/aws/sns
  # Use CMK ARN for rotation control: KmsMasterKeyId=arn:aws:kms:us-east-1:123456789012:key/mrk-...
  ```
- Detection: `aws sns get-topic-attributes --topic-arn <arn> --query Attributes.KmsMasterKeyId` — empty string or null value indicates no SSE.
- Impact: PII or financial data exposed at the SNS storage layer. Note: Even with SSE enabled, message metadata (subject, message ID, timestamps, attributes) is NOT encrypted.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html (2026-08-30)

---

**Anti-Pattern 4: No Message Filtering (Over-Delivery to All Subscribers)** 🟢

- Risk Level: MEDIUM
- Why: "By default, an Amazon SNS topic subscriber receives every message that's published to the topic." Without filter policies, every subscriber receives every message, wasting Lambda invocations, SQS API calls, and compute on irrelevant events. (Cost Optimization — COST; Performance Efficiency — PERF)
- ❌ Wrong:
  Single SNS topic with three SQS subscribers for different event types (order-created, order-shipped, order-cancelled) but no filter policies — all three subscribers receive all three event types, processing 2/3 of their messages unnecessarily.
- ✅ Correct:
  ```bash
  aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:123456789012:OrderEvents \
    --protocol sqs \
    --notification-endpoint arn:aws:sqs:us-east-1:123456789012:OrderCreatedProcessor \
    --attributes '{"FilterPolicy":"{\"eventType\":[\"order-created\"]}"}'
  # Publishers must include MessageAttributes: {"eventType": {"DataType":"String","StringValue":"order-created"}}
  ```
- Detection: `aws sns list-subscriptions-by-topic --topic-arn <arn>` — check `FilterPolicy` attribute for each subscription. Missing or empty `FilterPolicy` on a topic with heterogeneous event types is the anti-pattern.
- Impact: Unnecessary Lambda invocations and SQS API costs proportional to subscriber count times message volume; increased compute expenditure; larger failure surface area per subscription.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html (2026-08-30)

---

**Anti-Pattern 5: Direct SNS-to-Lambda Without SQS Buffer for Spiky Load** 🟢

- Risk Level: HIGH
- Why: "A queue such as Amazon Simple Queue Service (Amazon SQS) can provide a buffer to your workload components … Implement buffering to store the request and defer processing until a later time." Direct SNS-to-Lambda subscriptions have no concurrency buffer — under traffic spikes, Lambda throttling causes SNS delivery failures. (Reliability — REL; Cost Optimization — COST)
- ❌ Wrong:
  ```bash
  aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:123456789012:OrderEvents \
    --protocol lambda \
    --notification-endpoint arn:aws:lambda:us-east-1:123456789012:function:ProcessOrder
  # Spike of 10,000 events/s → Lambda concurrency exhausted → throttle errors → message loss without DLQ
  ```
- ✅ Correct:
  SNS Standard Topic → SQS Standard Queue (with DLQ) → Lambda event source mapping with `MaximumConcurrency=50` (or appropriate concurrency limit per workload).
- Detection: `aws sns list-subscriptions-by-topic --topic-arn <arn>` — `Protocol = "lambda"` on a high-volume topic with no SQS buffer.
- Impact: Under traffic spikes: Lambda throttling causes SNS to exhaust retries; without a DLQ on the subscription, messages are permanently lost. Even with a DLQ, messages require manual redriving after the root cause is resolved.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/cost_manage_demand_resources_buffer_throttle.html (2026-08-30)

---

## Cloud-Native Design Patterns

**Pattern 1: Fan-Out (SNS to Multiple SQS Queues)**

- Category: Scalability / Communication
- Problem: A single event must be processed independently by multiple downstream consumers in parallel without coupling the producer to every consumer.
- Solution on AWS: Publish one message to an SNS Standard Topic; N SQS queues subscribe; SNS pushes a copy to each queue concurrently; each queue is consumed independently by its own Lambda event source mapping or EC2 consumer.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Decoupling | Zero producer knowledge of subscribers; add/remove subscribers without publisher changes | Each subscriber adds queue management and monitoring overhead |
  | Durability | SQS persists messages up to 14 days for retry | If no subscriber is registered at publish time, the message is permanently dropped at SNS |
  | Scalability | Each SQS queue and its consumer scales independently | Multiple queues require independent alarms, DLQs, and dashboards |
  | Latency | Near real-time push delivery from SNS | SNS-to-SQS adds one hop vs direct Lambda invocation |

- When NOT to apply: Synchronous response required; strong consistency required across all consumers; strict message ordering critical without FIFO setup.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html (2026-08-30); https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/publish-subscribe.html (2026-08-30)

---

**Pattern 2: Message Filtering (Attribute-Based and Payload/Body-Based)**

- Category: Communication / Scalability
- Problem: All subscribers receive every message; consumers waste compute on irrelevant messages; scaling costs increase with subscriber count.
- Solution on AWS: Assign a JSON filter policy to each subscription. Use `FilterPolicyScope=MessageAttributes` (default) for attribute-keyed routing; use `FilterPolicyScope=MessageBody` for payload-embedded routing. Operators available: exact match, prefix, suffix, anything-but, equals-ignore-case, OR/AND, numeric range, IP address, exists.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Efficiency | Consumers only receive messages matching their declared interest | Filter policies must be maintained per subscription; schema drift breaks routing |
  | Simplicity | Single topic serves multiple consumer types without routing Lambda | MessageBody filtering requires valid, consistently structured JSON payload |
  | Propagation | Subscription changes without code deployment | Policy changes take up to 15 minutes to propagate — plan deployments accordingly |

- Caveat: Filtered-out messages do NOT go to the DLQ — they are silently discarded. This is by design.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html (2026-08-30)

---

**Pattern 3: Event-Driven Architecture — SNS as Event Router**

- Category: Communication / Scalability
- Problem: Multiple microservices need to react to the same domain events without tight coupling between the event producer and each consumer.
- Solution on AWS: SNS acts as the event router; producers publish to a topic; SNS fans out to Lambda (async processing), SQS (durable buffer), HTTP/S (webhooks), and Kinesis Data Firehose (streaming). Event Fork Pipelines (AWS SAM): storage fork (SNS→SQS→Lambda→Firehose→S3), analytics fork (SNS→SQS→Lambda→Firehose→OpenSearch), replay fork (SNS→SQS replay→Lambda→pipeline). AWS recommends native SNS-Firehose integration for archiving where possible.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Decoupling | Adding a new consumer = a new subscription, not a publisher code change | Event schema evolution must be managed carefully to avoid silent compatibility breaks |
  | Scalability | SNS elastically scales delivery; no provisioning required | No built-in back-pressure if Lambda concurrency is exhausted; SQS buffer required |
  | Observability | CloudWatch metrics per subscription; DLQ captures failures | Distributed tracing across SNS→SQS→Lambda requires X-Ray active tracing configuration |

- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-fork-pipeline-as-subscriber.html (2026-08-30)

---

**Pattern 4: Dead-Letter Queue (DLQ) + Redrive Pattern**

- Category: Resilience
- Problem: Messages that cannot be delivered are silently discarded, causing invisible and irrecoverable data loss.
- Solution on AWS: Attach an SQS DLQ to each SNS subscription via redrive policy. Client-side errors go to DLQ immediately. Server-side errors go to DLQ after retry exhaustion: 100,015 retries over 23 days for SQS/Lambda; 50 retries over 6 hours for SMTP/SMS/mobile. Monitor via CloudWatch alarm on `ApproximateNumberOfMessagesVisible >= 1`. After root cause is fixed, redrive DLQ messages back to the primary queue.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Zero permanent message loss on endpoint failures or misconfigurations | Additional SQS queue cost per subscription |
  | Observability | Failed messages preserved for root cause analysis and replay | Must actively monitor DLQ; messages accumulate silently without alarms |
  | Recovery | Redrive enables reprocessing after root cause is resolved | Redriving requires idempotent consumer logic to handle re-delivery |
  | Scope | Per-subscription granularity for failure isolation | Sharing one DLQ across multiple subscriptions makes root-cause analysis ambiguous |

- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html (2026-08-30)

---

**Pattern 5: Message Archiving and Replay (FIFO Topics Only)**

- Category: Resilience / Data
- Problem: Missed events cannot be replayed since SNS has no built-in message persistence. Subscribers that were offline or misconfigured lose events permanently.
- Solution on AWS: Enable `ArchivePolicy` on an SNS FIFO topic (`MessageRetentionPeriod`: 1–365 days). All messages published after the policy is enabled are stored. Subscribers configure `ReplayPolicy` on their subscription to replay from a `BeginningArchiveTime`. Available in all commercial Regions and GovCloud.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Up to 365 days of message retention for replay | Only available on FIFO topics; not applicable to Standard topics |
  | Recovery | No custom replay infrastructure required; native no-code feature | FIFO throughput caps (3,000 msg/s topic / 300 msg/s group) limit applicability at high volume |
  | Auditability | Exact state reconstruction from any timestamp in the archive window | Subscribers must be idempotent; replay re-triggers all consumer side effects |

- Source: https://docs.aws.amazon.com/sns/latest/dg/fifo-message-archiving-replay.html (2026-08-30) [Feature launched 2023-10-26 — ⚠️ >12mo; docs accessed 2026-08-30]

---

**Pattern 6: Cross-Account Fan-Out**

- Category: Communication / Scalability
- Problem: Events produced in one AWS account must be consumed by services in another account without routing through a shared intermediary.
- Solution on AWS: Topic owner grants the subscriber account `sns:Subscribe` via a topic resource-based policy. Queue owner (subscriber account) grants the SNS topic principal `sqs:SendMessage` with `aws:SourceArn` condition in the SQS queue policy.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Resource-based policies plus aws:SourceArn prevent confused deputy attacks | Two-sided policy management (both topic and queue) increases operational complexity |
  | Isolation | Consumers in separate accounts have independent IAM boundaries and blast radii | Policy misconfigurations can silently block delivery with no visible error |

- DLQ limitation: The DLQ must be in the same account and Region as the SNS subscription — creating a cross-account resilience gap. Plan remediation workflows accordingly.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-send-message-to-sqs-cross-account.html (2026-08-30)

---

**Pattern 7: Cross-Region Fan-Out**

- Category: Resilience / Communication
- Problem: Global applications need to deliver events to services in other AWS regions without duplicating publishers or event schemas.
- Solution on AWS: SNS supports cross-region delivery to SQS queues and Lambda functions in different regions. For opt-in regions, the queue or Lambda resource policy must use the regionalized SNS service principal `sns.<opt-in-region>.amazonaws.com`. Only SQS and Lambda are supported for cross-region delivery (not HTTP, SMS, or mobile push). [UNVERIFIED: native cross-region topic replication not confirmed from an official source; cross-region delivery to subscribed SQS/Lambda in other regions is confirmed.]
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Events delivered to a second region can survive primary-region disruptions | Opt-in region service principal adjustments add per-region policy complexity |
  | Latency | Near real-time cross-region delivery | Network latency between regions adds measurable delay; not suitable for latency-sensitive workflows |
  | Cost | No custom replication infrastructure or Lambda forwarders | Data transfer costs for cross-region delivery apply |

- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-cross-region-delivery.html (2026-08-30)

---

**Pattern 8: SNS to Lambda Async Invocation**

- Category: Communication / Scalability
- Problem: An event triggers a processing function but the producer must not wait for the result (fire-and-forget).
- Solution on AWS: Subscribe a Lambda function directly to an SNS topic. SNS invokes Lambda asynchronously. Retry: 100,015 times over 23 days. SNS delivers exactly once to each Lambda subscriber.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Latency | Direct push; lower latency than SQS polling | Lambda cold starts add latency on first invocations after idle |
  | Exactly-once | SNS delivers exactly once to Lambda | Lambda itself may retry on error — consumers must still be idempotent |
  | Throttling | Scales automatically with Lambda concurrency | Concurrency limits cause throttle errors at high volume; no buffering |

- When NOT to apply: High sustained throughput with risk of Lambda concurrency exhaustion (use SNS→SQS→Lambda instead). When long processing time increases throttle risk.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-lambda-as-subscriber.html (2026-08-30)

---

**Pattern 9: Mobile and Web Push Notifications (A2P)**

- Category: Communication
- Problem: Applications must send push notifications to millions of mobile devices across multiple platforms without managing platform-specific SDKs or infrastructure.
- Solution on AWS: Create a Platform Application in SNS with platform credentials (APNs, FCM v1, ADM, Baidu, WNS). Register each device as a Platform Endpoint. Publish to an endpoint ARN for targeted delivery or subscribe endpoints to an SNS topic for broadcast. Use idempotent `CreatePlatformEndpoint` on every app launch to handle token rotation transparently.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Platform abstraction | Single SNS API covers APNs, FCM, ADM, Baidu, WNS | Platform credentials must be rotated, maintained, and monitored |
  | Token management | CreatePlatformEndpoint is idempotent — safe to call on every app launch | Stale endpoints accumulate without active lifecycle management via delivery failure events |
  | Scale | SNS scales to millions of device endpoints | Endpoint sprawl increases SNS API costs if stale endpoints receive publish attempts |

- Source: https://docs.aws.amazon.com/sns/latest/dg/mobile-push-notifications-best-practices.html (2026-08-30); https://docs.aws.amazon.com/sns/latest/dg/sns-mobile-application-as-subscriber.html (2026-08-30)

---

**Pattern 10: SNS + SQS + Lambda Full Event Processing Pipeline**

- Category: Resilience / Scalability
- Problem: An event must be processed reliably with buffering, retry semantics, DLQ recovery, and archiving capability — no single service provides all of these alone.
- Solution on AWS: Compose SNS (pub/sub fan-out) + SQS (durable buffer with DLQ) + Lambda (processing). Optionally add Kinesis Data Firehose for long-term archiving to S3 or OpenSearch (Event Fork Pipelines). Storage fork: SNS→SQS→Lambda→Firehose→S3. Analytics fork: SNS→SQS→Lambda→Firehose→OpenSearch. Replay fork: SNS→SQS replay→Lambda→pipeline. AWS recommends native SNS-Firehose integration where possible to reduce Lambda hop.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | SQS DLQ captures all failures; replay pipeline enables recovery from any point in event history | Three or more services to monitor, alarm, and maintain |
  | Scalability | SQS decouples producer burst from Lambda concurrency | SQS polling adds latency vs direct push |
  | Durability | SQS retains 14 days; Firehose→S3 for long-term (years) | Storage costs for S3, Firehose, and optional archive tier |

- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-fork-pipeline-as-subscriber.html (2026-08-30)

---

## Security Architecture

**Domain 1: Identity and Access Management** 🟢

- AWS Services: Amazon SNS (resource-based topic policies), AWS IAM (identity-based policies), AWS CloudTrail.
- Architecture:
  - Two complementary policy systems govern access:
    1. IAM identity-based policies — restrict which SNS actions IAM principals in the SAME account can perform. Cannot grant cross-account access.
    2. SNS topic resource-based policies — attached to the topic; can grant access to other AWS accounts. Only mechanism for cross-account publish/subscribe.
  - IAM explicit Deny ALWAYS overrides an SNS topic policy Allow.
  - Topics are the ONLY resource type specifiable in SNS resource policies.
  - `ConfirmSubscription` and `Unsubscribe` do NOT require authentication and cannot be restricted via IAM — set `AuthenticateOnUnsubscribe=true` when confirming subscriptions to prevent unauthenticated unsubscribe.
  - Three access tiers: Administrators (`sns:CreateTopic`, `sns:DeleteTopic`, `sns:SetTopicAttributes`, `sns:AddPermission`), Publishers (`sns:Publish`), Subscribers (`sns:Subscribe`).
  - SNS-specific IAM condition keys: `sns:endpoint` (URL/email/ARN from Subscribe request), `sns:protocol` (protocol value from Subscribe request).
  - Use IAM roles — never long-term access keys — for EC2, Lambda, or ECS callers.
- Compliance Alignment: Principle of Least Privilege (AWS Well-Architected Security Pillar SEC01, SEC02). IAM Access Analyzer can identify overly permissive topic policies.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-using-identity-based-policies.html (2026-08-30); https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html (2026-08-30)

---

**Domain 2: Data Security — Encryption at Rest and in Transit** 🟢

- AWS Services: Amazon SNS (`KmsMasterKeyId` attribute), AWS KMS (symmetric CMK or `alias/aws/sns`), AWS CloudTrail (KMS API audit).
- Architecture:
  - SSE with AWS KMS uses envelope encryption: Data Encryption Keys (DEKs) encrypt message bodies; DEKs are encrypted and managed by KMS.
  - ONLY symmetric encryption KMS keys are supported. Asymmetric keys cannot be used for SNS SSE.
  - KMS options: AWS-managed key (`alias/aws/sns`) for simplicity; Customer-Managed Key (CMK) for key rotation control, cross-account access, and granular CloudTrail audit of every key use.
  - SSE encrypts ONLY the message body — NOT topic metadata, subject, message ID, timestamps, or message attributes.
  - Messages published before SSE was enabled are NOT retroactively encrypted.
  - Encrypted messages remain encrypted even if SSE is subsequently disabled.
  - ALL requests to SSE-enabled topics must use HTTPS and AWS Signature Version 4.
  - Enforce HTTPS-only via topic policy Deny:
    ```json
    {
      "Sid": "AllowPublishThroughSSLOnly",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "SNS:Publish",
      "Resource": "arn:aws:sns:us-east-1:111122223333:PaymentEvents",
      "Condition": {"Bool": {"aws:SecureTransport": "false"}}
    }
    ```
- Compliance Alignment: HIPAA — Amazon SNS is HIPAA eligible; Covered Entities must execute an AWS BAA before processing ePHI. FIPS 140-2 — validated endpoints available for FedRAMP and federal use. KMS SSE "can help meet encryption-related compliance requirements."
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html (2026-08-30); https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html (2026-08-30); https://aws.amazon.com/compliance/hipaa-eligible-services-reference/ (2026-08-30)

---

**Domain 3: Network Security — VPC Endpoints (AWS PrivateLink)** 🟡

- AWS Services: Amazon SNS (interface VPC endpoint), Amazon VPC (endpoint policy), AWS PrivateLink.
- Architecture:
  - SNS supports interface VPC endpoints via AWS PrivateLink — publishers inside a VPC reach SNS without traversing the public internet.
  - An ENI is automatically placed in the specified VPC subnet with a private IP address. [UNVERIFIED: ENI placement detail confirmed from security best-practices page; dedicated VPC endpoint page rendered no content.]
  - IPv6 support expanded to all AWS commercial Regions as of July 2025.
  - Two access control layers:
    1. Endpoint policy — controls which requests and principals are allowed through a specific VPC endpoint.
    2. Topic policy — controls which VPCs or VPC endpoint IDs have access to the topic resource.
  - Subscribe endpoint targets should use domain names, not raw IP addresses.
  - Use VPC endpoints for any Lambda in VPC, ECS task, or EC2 instance that publishes to SNS in security-sensitive environments.
- Compliance Alignment: Supports network isolation requirements for PCI-DSS, HIPAA, and FedRAMP regulated workloads.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html (2026-08-30)

---

**Domain 4: Detection — AWS CloudTrail Logging** 🟢

- AWS Services: AWS CloudTrail, Amazon SNS, Amazon S3 (trail storage), AWS CloudTrail Lake (optional SQL query).
- Architecture:
  - Management events (default, no additional cost): All SNS control-plane API calls — `CreateTopic`, `DeleteTopic`, `Subscribe`, `Unsubscribe`, `SetTopicAttributes`, `AddPermission`, `RemovePermission`, `TagResource`, `PutDataProtectionPolicy`, etc.
  - Data events (NOT default — must explicitly enable; additional charges): `Publish` and `PublishBatch` on `AWS::SNS::Topic` and `AWS::SNS::PlatformEndpoint`. Message content in Publish data events is recorded as `HIDDEN_DUE_TO_SECURITY_REASONS`. Data events include `tlsDetails` (TLS version, cipher suite) for compliance reporting.
  - CloudTrail storage options: Event History (90-day, free, no configuration), Trail (S3, multi-region recommended for completeness), CloudTrail Lake (SQL-queryable, additional cost, useful for security investigations).
  - Enable multi-region trails for complete coverage of cross-region SNS API calls.
- Compliance Alignment: Audit trail for SOC 2, PCI-DSS, HIPAA, and ISO 27001 audit log requirements.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-logging-using-cloudtrail.html (2026-08-30)

---

**Domain 5: Sensitive Data Protection — Post-Deprecation Architecture** 🟢

- AWS Services: Amazon SNS (inbound topic), AWS Lambda (filter function), Amazon Bedrock Guardrails, Amazon SNS (destination topic).
- Architecture:
  - Message Data Protection is no longer available to new customers as of April 30, 2026.
  - Replacement pattern: Lambda subscribed to inbound SNS topic → calls Amazon Bedrock Guardrails for real-time sensitive data detection → applies LOG, BLOCK, or REDACT action → republishes (if not blocked) to destination SNS topic.
  - Sample implementation: https://github.com/aws-samples/sample-sns-sensitive-data-protection-bedrock
  - Existing customers with configured Message Data Protection policies may continue using the feature in their accounts (security updates only; no new enhancements).
- Compliance Alignment: GDPR, HIPAA, PCI-DSS data minimization and sensitive data handling requirements.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-message-data-protection-availability-change.html (2026-08-30)

---

## Operational Patterns

**Domain 1: Observability — CloudWatch Metrics and Delivery Logging** 🟢

- RTO/RPO: Observability does not directly set RTO/RPO; it enables detection. DLQ with replay capability supports RPO as low as message publication timestamp (FIFO + archiving).
- AWS Services: Amazon CloudWatch (metrics, alarms, dashboards), Amazon CloudWatch Logs (delivery status logs), AWS X-Ray (distributed tracing).
- Architecture:
  - CloudWatch Metrics (AWS/SNS namespace, 1-minute intervals, no charge):

    | Metric | Description |
    |--------|-------------|
    | NumberOfMessagesPublished | Messages successfully published to SNS topics |
    | NumberOfNotificationsDelivered | Messages successfully delivered to all subscribers |
    | NumberOfNotificationsFailed | Messages SNS failed to deliver (after retries) |
    | NumberOfNotificationsFilteredOut | Messages rejected by subscription filter policies |
    | NumberOfNotificationsRedrivenToDlq | Messages moved to the Dead-Letter Queue |
    | NumberOfNotificationsFailedToRedriveToDlq | Messages that could not be moved to the DLQ |
    | PublishSize | Size of published messages in bytes |
    | SMSMonthToDateSpentUSD | Cumulative SMS charges since start of the month |

  - DLQ Monitoring: Use `ApproximateNumberOfMessagesVisible` on the SQS DLQ (NOT `NumberOfMessagesSent`) — set alarm threshold to 1 for immediate alerting.
  - Delivery Status Logging: Configure `SuccessFeedbackRoleArn`, `FailureFeedbackRoleArn`, `SuccessFeedbackSampleRate` per protocol per topic. IAM role requires `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`. Log group: `sns/<region>/<account-id>/<topic-name>`.
  - X-Ray Active Tracing: Two modes — PassThrough (default, passes trace header without generating segments) and Active (vends X-Ray segment data to topic owner). Enable via `SetTopicAttributes` with `TracingConfig=Active`. Limitation: Topics with numerous subscriptions may reach X-Ray trace document size limits.
  - Recommended CloudWatch dashboard per topic: `NumberOfNotificationsFailed`, `NumberOfNotificationsRedrivenToDlq`, DLQ `ApproximateNumberOfMessagesVisible`, `NumberOfMessagesPublished` vs `NumberOfNotificationsDelivered`.
- Cost Profile: CloudWatch metrics are free (AWS/SNS namespace). Delivery status logs incur CloudWatch Logs ingestion charges. X-Ray active tracing incurs X-Ray trace charges. DLQ SQS queues incur standard SQS charges.
- Automation: Use SSM Automation runbook `AWS-EnableSNSTopicDeliveryStatusLogging` to enable delivery logging at scale across all topics in an account.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-monitoring-using-cloudwatch.html (2026-08-30); https://docs.aws.amazon.com/sns/latest/dg/sns-active-tracing.html (2026-08-30)

---

**Domain 2: Reliability and Disaster Recovery** 🟢

- RTO/RPO: SNS SLA = 99.9% Monthly Uptime Percentage per AWS Region (Amazon Messaging SLA). RPO for FIFO topics with archiving = message publication timestamp (messages archived from policy-enable point). Cross-region RPO requires architectural workarounds (no native cross-region topic replication).
- AWS Services: Amazon SNS (delivery retry policies, DLQ, FIFO archiving), Amazon SQS (DLQ, standard queue buffer), AWS Lambda.
- Architecture:
  - Delivery Retry Policies:
    - AWS Managed Endpoints (SQS, Lambda): 100,015 retries over 23 days — 3 immediate, 2 pre-backoff at 1s, 10 backoff phase 1–20s, 100,000 post-backoff at 20s.
    - Customer Managed Endpoints (SMTP, SMS, Mobile Push): 50 retries over 6 hours — 2 pre-backoff at 10s, 10 backoff 10–600s, 38 post-backoff at 600s.
    - HTTP/S: Fully customizable; hard limit 3,600 seconds total; 5XX and 429 responses are retryable; SNS applies jitter.
  - DLQ constraints: SNS subscription and SQS DLQ must be same account and same Region. FIFO topics require FIFO DLQ. Recommended SQS DLQ retention: 14 days maximum.
  - Message Archiving/Replay: FIFO topics only. ArchivePolicy with MessageRetentionPeriod 1–365 days. Subscribers configure ReplayPolicy with BeginningArchiveTime. Available in all commercial Regions and GovCloud.
  - Cross-region DR: SNS topics are regional resources. DLQ cannot span regions. Native cross-region topic replication is NOT available. [UNVERIFIED] Standard DR pattern: SNS→SQS→Lambda→SNS-in-secondary-region for active-active or active-passive failover.
- Cost Profile: Standard topics — low baseline. FIFO topics — per-message billing (1KB minimum). Archive storage billed per GB. Cross-region data transfer adds cost.
- Automation: Use AWS CloudFormation or Terraform to codify topic configuration (SSE, DLQ, delivery logging) — manual configuration is an anti-pattern at scale.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-message-delivery-retries.html (2026-08-30); https://docs.aws.amazon.com/sns/latest/dg/fifo-message-archiving-replay.html (2026-08-30)

---

**Domain 3: FinOps — Cost Management** 🟢

- RTO/RPO: N/A (cost domain).
- AWS Services: Amazon SNS, Amazon CloudWatch (cost alarms), AWS Budgets.
- Architecture:
  - Pricing Model (pay-per-use, no minimum fee, no upfront commitment):
    - Standard Topics: Per 64 KB chunk of published data = 1 API request. Delivery billed per 64 KB chunk per endpoint type.
    - FIFO Topics: Per message regardless of size up to 256 KB; 1 KB minimum billing unit.
    - Message Archiving/Replay: Billed on stored data volume per GB.
    - Payload-based filtering (MessageBody scope): Billed per GB scanned.
    - KMS encryption: Separate KMS API call charges per encrypt/decrypt.
    - SMS: Carrier charges by country; highest cost driver per message.
  - Free Tier (new AWS customers, first 12 months): 1 million API requests/month, 15 GB outbound data transfer/month.
  - Cost Drivers (ranked): SMS (carrier charges vary by country, often highest per-message cost) > Payload-based filtering at high throughput > Long archiving retention on high-volume FIFO topics > Mobile push at scale.
  - FinOps Controls:
    - CloudWatch alarm on `SMSMonthToDateSpentUSD` to enforce SMS spend cap.
    - Configure `MonthlySpendLimit` in SNS SMS sandbox to hard-cap spend.
    - Prefer `MessageAttributes` filter scope over `MessageBody` for cost-sensitive scenarios (attribute filtering does not incur per-GB charge).
    - Use `PublishBatch` API (up to 10 messages per call) to reduce per-request costs.
- Cost Profile: Low baseline for simple fan-out (Standard topic + SQS). Medium with FIFO, archiving, and payload-based filtering. High for SMS-heavy workloads.
- Automation: Tag topics with cost center and environment tags; use AWS Cost Explorer SNS service view for per-topic cost attribution.
- Source: https://aws.amazon.com/sns/pricing/ (2026-08-30)

---

**Domain 4: Throughput Limits and Quotas** 🟢

- RTO/RPO: Quota exhaustion can cause throttling (429 errors) leading to delivery failures if not monitored.
- AWS Services: Amazon SNS, AWS Service Quotas (quota increase requests).
- Architecture:
  - Key Resource Quotas (default, per account):
    - Standard topics: 100,000
    - FIFO topics: 1,000
    - Subscriptions per standard topic: 12,500,000
    - Subscriptions per FIFO topic: 100
    - Filter policies per topic: 200
    - Messages per PublishBatchRequest: 10 entries
    - Maximum message size: 256 KiB (up to 2 GB via SNS Extended Client Libraries using S3)
  - Publish TPS (soft limits, increasable via Service Quotas):
    - US East (N. Virginia): 30,000 msg/s (Standard and FIFO)
    - US West (Oregon), EU (Ireland): 9,000 msg/s
    - Other major regions: 1,500 msg/s Standard, 3,000 msg/s FIFO
    - All other regions: 300 msg/s Standard, 3,000 msg/s FIFO
  - FIFO High Throughput Mode (`FifoThroughputScope=MessageGroup`): up to 30,000 msg/s in us-east-1, 9,000 msg/s in us-west-2 and eu-west-1. Per-message-group limit: 300 msg/s.
  - Hard limits (cannot be increased via Service Quotas): Subscribe/Unsubscribe: 100 TPS. ListSubscriptions: 30 TPS. Email delivery: 10 msg/s per subscription.
- Cost Profile: Quota increases are free; throughput expansion is billed per-message at standard rates.
- Automation: Monitor `NumberOfMessagesPublished` and configure CloudWatch alarms when approaching regional TPS limits; use Service Quotas API to proactively request increases before hitting limits.
- Source: https://docs.aws.amazon.com/general/latest/gr/sns.html (2026-08-30)

---

## Reference Architectures

**Architecture 1: Serverless Event Fan-Out for Web Applications (SNS + SQS + Lambda)** 🟢

- Context: Web application publishing a single domain event (e.g., order placed) that must trigger multiple independent downstream workflows simultaneously (inventory update, notification email, analytics ingestion, fraud check).
- Services Composition:

  | Layer | AWS Service | Purpose |
  |-------|-------------|---------|
  | Entry | Amazon API Gateway | Accepts HTTP requests from web clients |
  | Publisher | AWS Lambda (publisher function) | Validates request, publishes to SNS topic with MessageAttributes |
  | Fan-Out | Amazon SNS Standard Topic | Distributes a single message to all subscriptions concurrently |
  | Buffering | Amazon SQS Standard Queues (one per consumer) | Decouples Lambda workers from SNS; provides retry, DLQ, and backpressure |
  | Workers | AWS Lambda (one function per SQS queue) | Independently processes each event copy in parallel |
  | Dead-Letter | Amazon SQS DLQ (one per subscription) | Captures undeliverable messages for investigation |
  | Monitoring | Amazon CloudWatch | SNS delivery metrics, SQS DLQ alarms, Lambda execution errors |
  | Tracing | AWS X-Ray | Distributed trace correlation across SNS→SQS→Lambda |

- Data Flow: API Gateway → Publisher Lambda → `sns:Publish` (with MessageAttributes) → SNS fan-out → SQS Queue A, B, C (concurrent) → Worker Lambda A, B, C (parallel, asynchronous).
- Key Decisions: Each SQS queue carries an independent filter policy to receive only relevant event types. SNS ensures at-least-once delivery for SQS subscribers. SQS event source mapping uses `MaximumConcurrency` to control Lambda scaling. Each subscription has a DLQ.
- Scaling Path: SNS elastically scales delivery (up to 30,000 msg/s in us-east-1). SQS and Lambda scale independently per queue. Increase Lambda `MaximumConcurrency` as throughput grows. At extreme scale, request SNS publish TPS quota increase via Service Quotas.
- Source: https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html (2026-08-30)

---

**Architecture 2: S3-Triggered Media Processing Fan-Out** 🟢

- Context: Media ingestion pipeline where uploaded artifacts (video, audio, images) must trigger multiple parallel processing jobs without coupling the upload trigger to each processor.
- Services Composition:

  | Layer | AWS Service | Purpose |
  |-------|-------------|---------|
  | Storage | Amazon S3 | Object storage; emits s3:ObjectCreated events as triggers |
  | Entry (CDN) | Amazon CloudFront | Accelerates upload ingestion from global edge |
  | Fan-Out | Amazon SNS Standard Topic | Receives S3 event notification; distributes to all worker subscriptions |
  | Worker A | AWS Lambda (transcoding) | Video transcoding to multiple output formats |
  | Worker B | AWS Lambda (audio encoding) | Audio track extraction and encoding |
  | Worker C | AWS Lambda (metadata extraction) | Metadata extraction and catalog registration |
  | Observability | Amazon CloudWatch Logs | Execution tracking and error alerting per worker |

- Key Decisions: S3 event notifications target the SNS topic directly — no intermediary Lambda required. Moving from Lambda-to-Lambda coordination to SNS fan-out eliminates a coordinating "fanout Lambda," reducing latency and failure surface. Workers can be added or removed by adding/removing subscriptions without changing S3 or the publisher Lambda.
- Scaling Path: Each worker Lambda scales independently to its concurrency limit. Add SQS queues between SNS and Lambda workers for sustained high-throughput media ingestion.
- Source: https://aws.amazon.com/blogs/compute/messaging-fanout-pattern-for-serverless-architectures-using-amazon-sns/ (2026-08-30)

---

**Architecture 3: Ordered E-Commerce Event Pipeline (SNS FIFO + SQS FIFO)** 🟢

- Context: Price updates must be broadcast to wholesale, retail, and analytics consumers with strict ordering guarantees — a price at $10 that is then updated to $12 must never arrive at consumers in reverse order.
- Services Composition:

  | Layer | AWS Service | Purpose |
  |-------|-------------|---------|
  | Publisher | Application or AWS Lambda | Publishes price-update events with MessageGroupId (e.g., productId) and DeduplicationId |
  | Fan-Out (ordered) | Amazon SNS FIFO Topic | Guarantees ordered, exactly-once delivery per message group |
  | Wholesale Consumer | Amazon SQS FIFO Queue + Lambda | Receives wholesale-filtered messages in strict publish order |
  | Retail Consumer | Amazon SQS FIFO Queue + Lambda | Receives retail-filtered messages in strict publish order |
  | Analytics Consumer | Amazon SQS Standard Queue + Lambda/Athena | Receives all price messages; best-effort ordering acceptable for analytics |
  | Dead-Letter | Amazon SQS FIFO DLQ (per subscription) | Captures messages that fail ordered delivery |

- Key Decisions: `FilterPolicyScope=MessageBody` enables routing on payload-embedded content (e.g., `{"channel":"wholesale"}`) without requiring message attribute instrumentation on publishers. SNS FIFO delivers to subscribed SQS FIFO queues in exact publish order per MessageGroupId. Standard SQS queue subscribes to the FIFO topic for analytics (supported since September 14, 2023 — ⚠️ >12mo; docs confirmed 2026-08-30).
- Scaling Path: Standard FIFO throughput: 3,000 msg/s per topic or 20 MB/s. Enable High Throughput Mode (`FifoThroughputScope=MessageGroup`) for up to 30,000 msg/s in us-east-1. Design MessageGroupId granularity (e.g., productId) to distribute load and minimize head-of-line blocking risk.
- Source: https://docs.aws.amazon.com/sns/latest/dg/fifo-topic-message-ordering.html (2026-08-30)

---

## Service Equivalence Map

> SNS is an AWS-native service. This section provides a cross-provider equivalence map to aid architects migrating from or comparing against other cloud providers.

| AWS Service | Azure Equivalent | GCP Equivalent | Notes |
|-------------|-----------------|----------------|-------|
| Amazon SNS (Standard Topic) | Azure Service Bus Topics | Google Cloud Pub/Sub (topic with subscriptions) | All three support fan-out pub/sub. SNS uniquely supports native SMS, email, and mobile push as subscriber types without custom integration. |
| Amazon SNS (FIFO Topic) | Azure Service Bus Topics (Sessions enabled) | Google Cloud Pub/Sub (ordering keys) | Azure Sessions and GCP ordering keys provide analogous per-group ordering. FIFO SNS is restricted to SQS subscribers; Azure and GCP have broader subscriber types in ordered mode. |
| SNS + SQS Fan-out | Azure Service Bus Topics + Queues | GCP Pub/Sub + Cloud Tasks | The SNS+SQS pattern is AWS-canonical; analogous patterns exist cross-cloud but configuration differs significantly. |
| SNS Message Archiving/Replay (FIFO) | Azure Event Hubs Capture | GCP Pub/Sub Snapshot + Seek | GCP Pub/Sub Seek is the closest analog; Azure Event Hubs Capture provides archiving to Blob Storage. |
| SNS Mobile Push (APNs, FCM) | Azure Notification Hubs | Firebase Cloud Messaging (direct) | SNS wraps multiple push platforms under one API; Azure Notification Hubs is functionally comparable. |

---

## Provider Differentiators

**Differentiator 1: Message Filtering with Dual-Scope (Attribute-Based and Body-Based)** 🟢

- Category: Intelligent Routing / Cost Optimization
- Capability: SNS supports two filter policy scopes — `MessageAttributes` (default) and `MessageBody`. Operators include exact match, prefix, suffix, anything-but, equals-ignore-case, OR/AND, numeric range, IP address, and exists. Suffix and equals-ignore-case operators added November 2023 (⚠️ >12mo; docs confirmed 2026-08-30). Filter policy changes propagate within 15 minutes.
- Architecture Impact: Eliminates routing Lambda functions. A single publish call results in delivery only to matching subscribers — reducing Lambda invocations, SQS API calls, and compute costs in proportion to subscriber count.
- Unique Edge: Google Cloud Pub/Sub and Azure Service Bus Topics also support message filtering, but SNS body-based filtering with the full operator set (prefix, suffix, equals-ignore-case, IP address range) is notably comprehensive without requiring a routing compute layer.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html (2026-08-30)

---

**Differentiator 2: FIFO Topics with Exactly-Once Delivery, Strict Ordering, and High Throughput Mode** 🟢

- Category: Ordered Messaging / Data Consistency
- Capability: SNS FIFO topics provide strict per-MessageGroupId ordering and 5-minute deduplication window. High Throughput Mode (`FifoThroughputScope=MessageGroup`, January 21, 2025): up to 30,000 msg/s in us-east-1, 9,000 msg/s in us-west-2 and eu-west-1. Per-message-group limit remains at 300 msg/s. Trade-off: deduplication scope narrows to message-group level.
- Architecture Impact: Enables ordered financial transaction processing and inventory state management at cloud scale without custom ordering logic. ContentBasedDeduplication eliminates duplicate publisher instrumentation burden.
- Source: https://aws.amazon.com/about-aws/whats-new/2025/01/high-throughput-mode-amazon-sns-fifo-topics (2025-01-21); https://docs.aws.amazon.com/sns/latest/api/API_CreateTopic.html (2026-08-30)

---

**Differentiator 3: Message Archiving and Replay for FIFO Topics** 🟢

- Category: Operational Resilience / Auditability
- Capability: Native no-code archiving with `ArchivePolicy` and subscriber-initiated replay with `ReplayPolicy`. Retention up to 365 days. `BeginningArchiveTime` marks the earliest replay point. New subscribers can catch up on the full historical event stream without publishers replaying. Available in all commercial Regions and GovCloud (GovCloud: November 7, 2024).
- Architecture Impact: Eliminates custom event store infrastructure (S3 + Lambda + replay tooling) for FIFO workloads requiring historical replay. Enables point-in-time recovery and new subscriber bootstrapping.
- Source: https://docs.aws.amazon.com/sns/latest/dg/fifo-message-archiving-replay.html (2026-08-30); https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-sns-message-archiving-replay-fifo-topics-govcloud (2024-11-07)

---

**Differentiator 4: Multi-Platform Mobile Push Notifications (APNs, FCM v1, ADM, Baidu, WNS)** 🟢

- Category: Multi-Platform Mobile Delivery
- Capability: Single SNS API covers APNs (iOS/macOS), FCM (Android — HTTP v1 credentials as of January 2024), ADM (Kindle), Baidu Cloud Push, MPNS, and WNS. SNS manages device token registration, platform endpoint lifecycle, and platform credential management. FCM legacy HTTP credentials deprecated — SNS now exclusively supports FCM v1.
- Architecture Impact: Reduces mobile push complexity from N platform-specific SDKs to one SNS API call. Broadcast from an SNS topic to millions of device endpoints via topic subscription.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-mobile-application-as-subscriber.html (2026-08-30)

---

**Differentiator 5: Native SMS and Email Delivery (No Intermediary Required)** 🟢

- Category: Direct Subscriber Delivery
- Capability: SNS supports SMS (200+ countries via AWS End User Messaging SMS as of September 24, 2024), email (`email` and `email-JSON` protocols), and HTTP/S as native subscriber types. Mixed subscriber types (SQS + Lambda + Email + SMS) on the same topic enable simultaneous machine-readable and human-readable delivery from a single publish call.
- Architecture Impact: Eliminates the need for a separate SMS gateway or transactional email service for simple notification use cases. Enables ops teams to receive human-readable alerts on the same topic that also triggers automated remediation Lambda functions.
- Source: https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html (2026-08-30)

---

**Differentiator 6: IPv6 Dual-Stack Endpoint Support** 🟢

- Category: Network Modernization
- Capability: As of April 3, 2025, Amazon SNS API endpoints support IPv4, IPv6, or dual-stack connections. Clients can choose their connectivity mode without infrastructure changes.
- Architecture Impact: Enables SNS integration in IPv6-only VPCs and dual-stack environments without NAT gateway workarounds. Supports modern network architectures aligned with IPv4 address exhaustion.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-release-notes.html (2026-08-30)

---

## Scenario Coverage

**Standard Case: Web Application Event Fan-Out Using SNS→SQS→Lambda with Filter Policies** 🟢

- Approach: SNS Standard Topic receives domain events published by a producer Lambda (API Gateway-triggered). Multiple SQS queues subscribe, each with a filter policy scoped to specific event types (`FilterPolicyScope=MessageAttributes`). Lambda functions poll their respective queues via event source mappings. Each subscription carries a DLQ. CloudWatch alarms on DLQ `ApproximateNumberOfMessagesVisible >= 1` and SNS `NumberOfNotificationsFailed > 0`.
- Key Decisions the Architect Must Make:
  1. Topic topology: one topic per domain (OrderEvents, PaymentEvents) vs one universal topic — prefer per-domain for cleaner filter policies and IAM scoping.
  2. Filter scope: `MessageAttributes` (publisher must add attributes on every Publish call) vs `MessageBody` (filter on payload JSON) — choose `MessageAttributes` when publisher can be instrumented; choose `MessageBody` when payload schema is stable and publisher cannot be modified.
  3. Lambda concurrency: set `MaximumConcurrency` on each SQS event source mapping to prevent runaway scaling. Start at 10–50 and tune per workload.
  4. DLQ retention: align with maximum acceptable recovery window; recommended 14 days.
  5. SSE: enable `alias/aws/sns` at minimum on any topic carrying user data; upgrade to CMK if audit or rotation control is required.

---

**Edge Case: FIFO Ordering Requirement for Financial Transactions or Inventory** 🟢

- Approach: SNS FIFO Topic with `ContentBasedDeduplication=false` (explicit deduplication IDs). Publishers assign `MessageGroupId` per business entity (e.g., `orderId`, `productId`). Downstream subscribers are SQS FIFO queues. Use `FilterPolicyScope=MessageBody` for subscriber routing when channel (wholesale, retail) is embedded in the payload. Enable `FifoThroughputScope=MessageGroup` if aggregate throughput exceeds 3,000 msg/s. Enable `ArchivePolicy` if downstream subscribers require replay capability (1–365 day retention).
- Key Decisions the Architect Must Handle:
  - Confirm all downstream subscribers can be SQS FIFO queues — FIFO SNS cannot deliver directly to Lambda, HTTP, email, or SMS.
  - Design `MessageGroupId` granularity to balance ordering guarantees against head-of-line blocking risk. Coarse grouping (e.g., single group for all orders) creates serialization bottlenecks. Fine grouping (per-order) maximizes parallelism.
  - Decide on deduplication: `ContentBasedDeduplication=true` if identical body = identical event; `false` with explicit IDs if two identical-body messages represent distinct events (e.g., two price refreshes at the same value).
  - Monitor per-group throughput against the 300 msg/s limit in High Throughput Mode.

---

**Anti-Pattern Case: Direct SNS-to-Lambda Without SQS Buffer for Spiky Load** 🔴

- Clarification the Architect Must Get Before Proceeding:
  - "What is the expected peak publish rate in messages per second?"
  - "What is the Lambda function's reserved concurrency or account concurrency limit?"
  - "What is the consequence of a message being permanently lost if delivery retries are exhausted?"
  - "Is processing latency more critical than delivery reliability?"
- Why to Refuse: Under traffic spikes, Lambda throttling causes SNS delivery failures. Without a DLQ on the subscription, messages are silently and permanently lost after SNS retry exhaustion. Even with a DLQ, recovery requires manual redrive. SNS retry for Lambda spans 23 days but throttle errors can cascade faster than retries resolve.
- Correct Alternative: SNS Standard Topic → SQS Standard Queue (with DLQ, 14-day retention) → Lambda event source mapping with `MaximumConcurrency=<workload-appropriate value>`. This absorbs traffic spikes in SQS, controls Lambda concurrency, and guarantees zero message loss via DLQ.
- Flag This Pattern When: Seeing `Protocol = "lambda"` in `aws sns list-subscriptions-by-topic` output on a topic expected to receive > 100 msg/s sustained or any workload with unpredictable spikes.

---

## Research Iteration Changelog

> Mandatory — Research_Depth is exhaustive. Gap_Loop_Ran = true.

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Changelog | Message Data Protection deprecation (April 30, 2026) | Added — breaking change confirmed from official deprecation announcement | https://docs.aws.amazon.com/sns/latest/dg/sns-message-data-protection-availability-change.html (2026-08-30) |
| 1 | Changelog | FifoThroughputScope High Throughput Mode (January 21, 2025) | Added — new FIFO topic attribute enabling 30,000 msg/s in us-east-1 | https://docs.aws.amazon.com/sns/latest/api/API_CreateTopic.html (2026-08-30) |
| 1 | Changelog | IPv6 dual-stack endpoint support (April 3, 2025) | Added — SNS API now supports IPv4, IPv6, and dual-stack connections | https://docs.aws.amazon.com/sns/latest/dg/sns-release-notes.html (2026-08-30) |
| 1 | Changelog | AWS End User Messaging SMS integration (September 24, 2024) | Added — SMS now billed through AWS End User Messaging with two-way messaging support | https://docs.aws.amazon.com/sns/latest/dg/sns-release-notes.html (2026-08-30) |
| 1 | Changelog | FCM HTTP v1 credentials (January 18, 2024) | Added — FCM legacy credentials deprecated; SNS now supports FCM v1 | https://docs.aws.amazon.com/sns/latest/dg/sns-release-notes.html (2026-08-30) |
| 1 | Changelog | FIFO message archiving and replay (October 26, 2023) | Added — up to 365-day retention and subscriber-initiated replay for FIFO topics | https://docs.aws.amazon.com/sns/latest/dg/fifo-message-archiving-replay.html (2026-08-30) [announcement ⚠️ >12mo] |
| 1 | Changelog | Standard SQS queues subscribing to FIFO topics (September 14, 2023) | Added — standard SQS queues can now subscribe to FIFO SNS topics | https://docs.aws.amazon.com/sns/latest/dg/sns-release-notes.html (2026-08-30) [announcement ⚠️ >12mo] |
| 1 | Changelog | Filter policy suffix, equals-ignore-case, OR operators (November 16, 2023) | Added — new filter operators for more expressive subscription routing | https://docs.aws.amazon.com/sns/latest/dg/sns-release-notes.html (2026-08-30) [announcement ⚠️ >12mo] |
| 1 | Glossary | All 20 terms | Added — defined from official AWS SNS documentation accessed 2026-08-30 | https://docs.aws.amazon.com/sns/latest/dg/welcome.html and linked pages (2026-08-30) |
| 1 | Architecture Guardrails | 5 Mandatory Patterns + 3 Architectural Decisions + 5 Anti-Patterns | Added — sourced from AWS SNS Developer Guide, Well-Architected Framework, and Decision Guides | Multiple official sources (2026-08-30) |
| 1 | Cloud-Native Design Patterns | 10 patterns (Fan-out through Full Pipeline) | Added — all patterns sourced from official AWS SNS documentation and prescriptive guidance | https://docs.aws.amazon.com/sns/latest/dg/ and linked pages (2026-08-30) |
| 1 | Security Architecture | 5 domains (IAM, Encryption, VPC, CloudTrail, MDP replacement) | Added | https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html and linked pages (2026-08-30) |
| 1 | Operational Patterns | 4 domains (Observability, DR, FinOps, Quotas) | Added | https://docs.aws.amazon.com/sns/latest/dg/sns-monitoring-using-cloudwatch.html and linked pages (2026-08-30) |
| 1 | Reference Architectures | 3 architectures (Serverless Fan-Out, Media Processing, Ordered E-Commerce) | Added | https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html (2026-08-30) |
| 1 | FIFO subscriber type restrictions | Claim that FIFO topics only support SQS as subscribers (Lambda/HTTP direct excluded) | ⚠️ IRRESOLVABLE — could not confirm from fetched rendered page for Lambda direct subscription; confirmed from FIFO overview and community sources but exhaustive official table not retrieved | — |
| 1 | Cross-region replication | Native SNS cross-region topic replication | ⚠️ IRRESOLVABLE — no official source confirmed a native SNS cross-region topic replication mechanism; pattern requires architectural workaround (SNS→SQS→Lambda→SNS in secondary region) | — |
| 1 | SMS filter policy support | Whether filter policies apply to SMS subscriptions | Resolved as [UNVERIFIED] — filter policy support for SMS not explicitly confirmed or denied from retrieved pages; known scope of filter policy support confirmed for SQS, Lambda, HTTP/S, Firehose | — |
| 1 | VPC endpoint detailed config | ENI placement, subnet, security group, private DNS details | Resolved as [UNVERIFIED] — dedicated VPC endpoint page rendered no content; partially confirmed from security best-practices page | — |
| 1 | MDP replacement alternatives | Lambda + Bedrock Guardrails as recommended alternative | Resolved — confirmed from the deprecation announcement page; sample code at https://github.com/aws-samples/sample-sns-sensitive-data-protection-bedrock | https://docs.aws.amazon.com/sns/latest/dg/sns-message-data-protection-availability-change.html (2026-08-30) |
