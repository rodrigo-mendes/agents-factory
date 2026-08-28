# AWS SNS — Messaging Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS SNS — Messaging Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Messaging Architecture"
Target_Edition: "AWS SNS 2024"
Architecture_Context: "Distributed applications requiring publish-subscribe messaging — covering fan-out patterns, event-driven architectures, application-to-application (A2A) messaging, application-to-person (A2P) notifications, message filtering, FIFO ordering, and multi-protocol delivery"
Official_Source_URL: "https://docs.aws.amazon.com/sns/latest/dg/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to SNS feature updates and integration changes"
```

---

## Executive Summary

Amazon Simple Notification Service (Amazon SNS) is AWS's fully managed publish-subscribe (pub/sub) messaging service that enables asynchronous message delivery from publishers (producers) to subscribers (consumers) through topics. SNS supports both Application-to-Application (A2A) messaging — delivering to Amazon SQS queues, AWS Lambda functions, Amazon Data Firehose delivery streams, and HTTP/S endpoints — and Application-to-Person (A2P) messaging — delivering to mobile push notifications, SMS, and email. SNS stores published messages redundantly across multiple geographically separated servers and data centers, providing high durability and availability. Standard topics support virtually unlimited throughput (up to 30,000 messages/second in us-east-1, soft limit), while FIFO topics support up to 3,000 messages/second per topic (with `FifoThroughputScope` set to `Topic`) or 300 messages/second per message group.

The 2024 edition's most architecturally significant advances are: (1) **FIFO topics with high-throughput mode and `FifoThroughputScope`** — enabling per-topic throughput of 3,000 messages/second (or 20 MB/second, whichever is reached first) when scope is set to `Topic`, dramatically increasing FIFO viability for high-volume ordered workloads; (2) **Message Data Protection (MDP)** — a native feature that scans messages for sensitive data (PII, PHI, financial data), provides audit logging of sensitive content flowing through topics, and enables content masking/redaction without custom code; (3) **Payload-based message filtering** — filter policies can now operate on the message body (JSON payload) in addition to message attributes, enabling more flexible content-based routing; (4) **Message archiving and replay for FIFO topics** — a no-code, in-place archive that lets topic owners store messages and subscribers replay them back to subscribed endpoints for recovery or reprocessing scenarios. These changes position SNS as a fully-featured event backbone capable of handling compliance (MDP), ordered delivery (FIFO + high-throughput), and event replay (archive) without auxiliary infrastructure.

The three most critical architecture guardrails for SNS are: (1) **always configure Dead-Letter Queues (DLQs) on every subscription** — without a DLQ, messages that fail delivery after the retry policy exhausts are permanently lost with no recovery path; (2) **enable server-side encryption (SSE) on all production topics** — message bodies may contain sensitive data, and SSE with AWS KMS keys protects at rest with audit trail; (3) **never use wildcard (`*`) Principal in topic access policies without restrictive conditions** — an open topic policy enables unauthorized publishing (message injection), subscription creation, and data exfiltration via rogue subscriptions.

---

## Cloud Architecture Glossary

```
Term: Standard Topic
Definition: The default Amazon SNS topic type that offers maximum throughput (virtually unlimited publishes per second, soft-limited per region/account), best-effort ordering, and at-least-once message delivery to all confirmed subscribers. Messages may occasionally be delivered out of order or more than once.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-create-topic.html
Architect Usage: Use Standard topics when ordering is not required and subscriber protocols include HTTP/S, email, SMS, or mobile push. Standard topics support all delivery protocols. Choose Standard when maximum throughput and broad protocol support are priorities over strict ordering or deduplication.
Common Confusion: "At-least-once delivery" applies per subscription — each subscription independently receives the message. This is different from SQS at-least-once where a single consumer may receive duplicates. SNS delivers to ALL subscribers; the "at-least-once" qualifier means a single subscriber may receive the same message more than once in rare cases.

Term: FIFO Topic
Definition: An Amazon SNS topic type that guarantees strict message ordering within a message group and message deduplication within the 5-minute deduplication window. FIFO topic names must end with the `.fifo` suffix. FIFO topics can only deliver to Amazon SQS FIFO queues as subscribers (not HTTP/S, Lambda, email, SMS, or mobile push).
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-fifo-topics.html
Architect Usage: Use FIFO topics when event ordering per logical entity (per-customer, per-order, per-device) is a business requirement AND all subscribers can use SQS FIFO queues. FIFO topics support up to 100 subscriptions per topic (vs 12.5M for standard). Enable high-throughput mode with FifoThroughputScope=Topic for workloads needing > 300 msgs/sec per group.
Common Confusion: FIFO topics deliver ONLY to SQS FIFO queues — Lambda, HTTP/S, email, and SMS are NOT supported subscriber protocols for FIFO topics. This is the most common misconception. If you need FIFO ordering with Lambda, subscribe the Lambda to the SQS FIFO queue (SNS FIFO → SQS FIFO → Lambda ESM).

Term: Topic
Definition: A logical access point and communication channel to which publishers send messages. Topics decouple publishers from subscribers — publishers send to the topic without knowledge of who subscribes. A topic has an ARN (Amazon Resource Name) as its unique identifier, supports access policies, encryption settings, and delivery policies.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-create-topic.html
Architect Usage: Topics are the central routing construct in SNS. Design one topic per event type or domain event (e.g., "order-placed", "payment-completed", "user-registered"). Avoid "god topics" that multiplex unrelated events — use message filtering if subscribers need subsets, or separate topics for fundamentally different domains.
Common Confusion: A topic is NOT a queue. Messages are not stored in a topic for later retrieval (unlike SQS). Messages published to a topic are immediately pushed to all confirmed subscribers. If no subscribers exist or all deliveries fail, the message is lost unless DLQs are configured on subscriptions.

Term: Subscription
Definition: An association between a topic and an endpoint (SQS queue, Lambda function, HTTP/S URL, email address, SMS number, mobile push, or Firehose delivery stream) that defines how and where messages are delivered. Each subscription has its own filter policy, delivery policy, DLQ configuration, and raw message delivery setting.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-create-subscribe-endpoint-to-topic.html
Architect Usage: Subscriptions are per-endpoint configurations. Each subscription independently receives messages, applies its own filter policy, and handles delivery failures independently. DLQs are configured at the subscription level (not topic level) because delivery failures are subscription-specific. Use Raw Message Delivery for SQS and HTTP/S subscribers to avoid SNS JSON envelope wrapping overhead.
Common Confusion: Subscription confirmation is required for HTTP/S, email, and SMS endpoints — the subscriber must confirm before receiving messages. SQS, Lambda, and Firehose subscriptions within the same account are auto-confirmed. Cross-account SQS subscriptions require queue policy allowing SNS to send.

Term: Filter Policy
Definition: A JSON object attached to a subscription that defines which messages the subscriber receives. Filters can be applied to message attributes (MessageAttributes scope) or message body (MessageBody scope). Only messages matching ALL conditions in the filter policy are delivered to the subscription. A subscription without a filter policy receives ALL messages.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html
Architect Usage: Use filter policies to avoid unnecessary message delivery and processing at subscriber endpoints. Filter on message attributes for routing metadata (event_type, region, priority). Filter on message body for payload-level routing (JSON field matching). Maximum 200 filter policies per topic, 10,000 per account. Design attribute schemas upfront — changing filter dimensions requires republishing messages with new attributes.
Common Confusion: Filter policies use AND logic between attributes (all conditions must match) but OR logic within attribute values (any value can match). An empty filter policy ({}) matches ALL messages — it does NOT block all messages. The MessageBody scope requires the payload to be valid JSON.

Term: Message Attributes
Definition: Structured metadata (up to 10 attributes per message) attached to a published message. Each attribute has a Name (string, max 256 chars), DataType (String, Number, Binary, or String.Array), and Value. Message attributes are used for filtering, routing, and metadata without requiring payload parsing.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-message-attributes.html
Architect Usage: Use message attributes for routing and filtering metadata — event_type, source_service, priority_level, region, tenant_id. This enables subscribers to filter without parsing the message body. Attributes are NOT encrypted by SSE (only message body is encrypted). Do not put sensitive data in message attributes.
Common Confusion: Message attributes (SNS) are different from message metadata (subject, message ID, timestamp). Attributes are user-defined key-value pairs. They are delivered alongside the message body to subscribers. SQS subscribers receive attributes as SQS message attributes when Raw Message Delivery is enabled.

Term: Dead-Letter Queue (DLQ) for Subscriptions
Definition: An Amazon SQS queue configured on an SNS subscription (not on the topic) that receives messages that cannot be delivered to the subscription's endpoint after all retry attempts are exhausted. The DLQ captures messages that would otherwise be permanently lost.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html
Architect Usage: Every production subscription MUST have a DLQ configured. DLQs are set per-subscription because each endpoint may fail independently. For FIFO topic subscriptions, use FIFO DLQs. For standard topic subscriptions, use standard DLQs. Set DLQ retention to 14 days (maximum). Monitor DLQ with CloudWatch alarm on ApproximateNumberOfMessagesVisible.
Common Confusion: SNS DLQs are SQS queues configured on the SUBSCRIPTION, not on the topic. This is different from SQS DLQs (which are configured on the source queue). The SNS DLQ receives messages after the delivery retry policy is exhausted — the subscription must be in the same account and region as the DLQ.

Term: Delivery Policy
Definition: A JSON configuration that defines how Amazon SNS retries failed message deliveries to HTTP/S endpoints. Configurable parameters include: number of retries, retry delay, backoff function (linear, geometric, exponential), minimum/maximum delay, and throttle rate. Default: 3 retries with 20-second intervals for HTTP/S.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-message-delivery-retries.html
Architect Usage: Customize delivery policies for HTTP/S endpoints based on the endpoint's expected recovery time. For AWS-managed endpoints (SQS, Lambda), SNS retries up to 100,015 times over 23 days — this is not configurable. For SMTP, SMS, and mobile push, SNS uses internal policy of 50 retries over 6 hours. Only HTTP/S delivery policies are customer-customizable.
Common Confusion: Delivery retry policies apply to individual subscriptions, not to the topic. Different subscriptions on the same topic can have different retry behavior. SQS and Lambda subscribers use AWS-internal retry (23 days, 100,015 attempts) that cannot be modified — only HTTP/S endpoints have customer-configurable retry.

Term: Raw Message Delivery
Definition: A subscription attribute (RawMessageDelivery: true) that delivers the published message body directly to SQS or HTTP/S subscribers without wrapping it in the SNS JSON notification envelope. When disabled (default), subscribers receive the message wrapped in SNS metadata JSON (Type, MessageId, TopicArn, Subject, Message, Timestamp, etc.).
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-large-payload-raw-message-delivery.html
Architect Usage: Enable Raw Message Delivery for SQS and HTTP/S subscribers to: (1) reduce payload overhead (no SNS envelope), (2) preserve original message format for consumers, (3) enable message attributes to flow as SQS message attributes (for SQS subscribers). Disable Raw Message Delivery when consumers need SNS metadata (TopicArn, UnsubscribeURL, etc.).
Common Confusion: Raw Message Delivery is only supported for SQS and HTTP/S subscribers — NOT for Lambda, email, SMS, or mobile push. When enabled for SQS, SNS message attributes are mapped to SQS message attributes. Without Raw Message Delivery, the entire SNS notification JSON is placed in the SQS message body.

Term: Message Data Protection (MDP)
Definition: A feature that enables data protection policies on SNS topics to audit, mask, or deny messages containing sensitive data (PII, PHI, financial data). MDP uses pattern matching and machine learning to identify sensitive data types (credit card numbers, SSNs, email addresses, etc.) and can log findings to CloudWatch, S3, or Firehose.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-message-data-protection.html
Architect Usage: Enable MDP on topics that transit PII or financial data. Use audit operations to log sensitive data presence without blocking delivery. Use deny operations (inbound) to reject messages containing disallowed data types. Use de-identify operations (outbound) to mask sensitive data before delivery to specific subscriptions. MDP operates on both message body and message attributes.
Common Confusion: MDP is configured at the topic level (data protection policy) but can apply different rules for inbound (publish) vs outbound (delivery) operations. MDP is NOT encryption — it is data classification and access control. MDP does not replace SSE; both should be enabled for comprehensive data protection.

Term: Message Archiving and Replay (FIFO Topics)
Definition: A feature exclusive to FIFO topics that stores published messages in an in-place archive within the topic. Subscribers can replay archived messages to their endpoints for recovery, reprocessing, or testing. Archive retention is configurable up to 365 days.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/fifo-message-archiving-replay.html
Architect Usage: Enable archiving on FIFO topics when message replay is needed for disaster recovery, subscriber catch-up, or testing. Replay is per-subscription — each subscriber can independently replay without affecting other subscribers. Archive and replay is NOT available for Standard topics — use Firehose subscriber + S3 for standard topic archival.
Common Confusion: Message archiving is NOT a retention mechanism for undelivered messages — it is an intentional archive of all published messages regardless of delivery success. Replay sends archived messages as new deliveries (subscribers must be idempotent). Archive storage contributes to SNS costs.

Term: Fan-Out Pattern
Definition: An architectural pattern where a single message published to an SNS topic is replicated and delivered to multiple subscriber endpoints simultaneously. Each subscriber receives an independent copy and processes it independently at its own rate.
Provider Docs Section: https://docs.aws.amazon.com/sns/latest/dg/sns-common-scenarios.html
Architect Usage: Fan-out is the primary architectural justification for SNS. Use it when a single event must trigger multiple independent downstream processes. The canonical pattern is SNS → multiple SQS queues, where each queue feeds an independent consumer. This decouples the producer from all consumers and allows adding/removing consumers without code changes.
Common Confusion: Fan-out delivers the SAME message to ALL subscribers (after filter policy evaluation). It is not routing (one message to one subscriber based on content). For content-based routing to a single destination, use filter policies or EventBridge rules instead.
```

---

## Architecture Framework Analysis: AWS Well-Architected — Messaging Pillar Alignment

```
Pillar: Reliability
Definition: The ability of a workload to perform its intended function correctly and consistently when it's expected to.
Key Design Principles:
  - Automatically recover from failure (DLQ captures undeliverable messages for reprocessing)
  - Test recovery procedures (FIFO message replay, DLQ processing runbooks)
  - Scale horizontally to increase aggregate workload availability (SNS scales automatically, subscribers scale independently)
  - Stop guessing capacity (SNS standard topics have virtually unlimited throughput)
  - Manage change in automation (IaC for topic configuration, subscriptions, filter policies)
Applies To Pub/Sub Messaging: SNS is the primary AWS mechanism for implementing reliable fan-out and event distribution. DLQs on every subscription ensure no message loss. For AWS-managed endpoints (SQS, Lambda), SNS retries delivery up to 100,015 times over 23 days. Topic message durability is guaranteed through multi-AZ storage immediately upon publish.
Assessment Questions:
  1. Is every subscription configured with a Dead-Letter Queue (SQS) for failed deliveries?
  2. Are all subscribers designed to be idempotent (safe to receive the same message multiple times)?
  3. For FIFO topics, is message archiving enabled for replay/recovery scenarios?
Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_prevent_interaction_failure_loosely_coupled_system.html

Pillar: Security
Definition: The ability to protect data, systems, and assets while delivering business value through risk assessments and mitigation strategies.
Key Design Principles:
  - Apply security at all layers (topic access policies, IAM roles, encryption, VPC endpoints, MDP)
  - Enable traceability (CloudTrail for SNS API calls, delivery status logging)
  - Implement least privilege (per-topic IAM policies with specific actions and resource ARNs)
  - Protect data in transit and at rest (TLS mandatory for HTTPS publishing, SSE-KMS for at-rest)
  - Automate security best practices (SCP guardrails, Config rules for encryption validation)
Applies To Pub/Sub Messaging: Every SNS topic must have SSE enabled with KMS keys. Topic access policies must use specific principal ARNs — never wildcard Principal without conditions. Enforce HTTPS-only publishing via aws:SecureTransport condition. Use VPC endpoints for topics accessed from private subnets. Enable Message Data Protection for topics transiting PII/PHI.
Assessment Questions:
  1. Is server-side encryption (SSE) with KMS enabled on every SNS topic?
  2. Do topic access policies use specific principal ARNs and condition keys — never open wildcards?
  3. Is HTTPS-only publishing enforced via aws:SecureTransport condition in the topic policy?
Source: https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html

Pillar: Performance Efficiency
Definition: The ability to use computing resources efficiently to meet system requirements and to maintain that efficiency as demand changes and technologies evolve.
Key Design Principles:
  - Use serverless architectures (SNS + Lambda eliminates consumer infrastructure management)
  - Consider mechanical sympathy (batch publishing with PublishBatch, message filtering to reduce unnecessary deliveries)
  - Democratize advanced technologies (use managed pub/sub — no self-hosted RabbitMQ/Kafka overhead)
Applies To Pub/Sub Messaging: Use PublishBatch API (up to 10 messages per batch) to maximize throughput per API call. Use message filtering at the subscription level to reduce unnecessary message delivery and downstream processing. For FIFO topics, use high-cardinality message group IDs to maximize parallelism. Enable Raw Message Delivery for SQS/HTTP/S subscribers to reduce payload size.
Assessment Questions:
  1. Are publishers using PublishBatch for high-volume scenarios (10 messages per API call)?
  2. Are filter policies configured on subscriptions to prevent unnecessary message delivery?
  3. For FIFO topics, are message group IDs designed for maximum parallelism?
Source: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/perf_data_selecting.html

Pillar: Cost Optimization
Definition: The ability to run systems to deliver business value at the lowest price point.
Key Design Principles:
  - Adopt a consumption model (SNS charges per publish + per delivery — pay only for what you use)
  - Measure overall efficiency (cost per event distributed, deliveries per publish)
  - Analyze and attribute expenditure (per-topic tagging, delivery cost per protocol)
  - Stop spending money on undifferentiated heavy lifting (managed SNS vs self-hosted event bus)
Applies To Pub/Sub Messaging: Use message filtering to avoid delivering messages to subscribers that don't need them (each delivery is billable). Use PublishBatch to reduce API call count. Choose appropriate subscriber protocols — SQS delivery ($0) is free within same region vs HTTP/S ($0.60/M) vs SMS (variable, expensive). Standard topic first 1M publishes/month are free.
Assessment Questions:
  1. Are filter policies used to eliminate unnecessary deliveries to subscribers?
  2. Are batch publish operations used to minimize API call costs?
  3. Are delivery protocols selected with cost awareness (SQS free vs HTTP/S $0.60/M)?
Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost_decomissioning_resources.html

Pillar: Operational Excellence
Definition: The ability to support development and run workloads effectively, gain insight into their operations, and continuously improve.
Key Design Principles:
  - Perform operations as code (IaC for topics, subscriptions, filter policies, DLQ configurations)
  - Make frequent, small, reversible changes (filter policy updates, subscription additions)
  - Anticipate failure (DLQ + CloudWatch alarms + delivery status logging)
  - Learn from all operational failures (DLQ analysis, delivery failure logging)
Applies To Pub/Sub Messaging: All topic and subscription configurations must be IaC-managed. Enable delivery status logging for all endpoint types (CloudWatch Logs). Configure CloudWatch alarms on NumberOfNotificationsFailed metric. DLQ monitoring must trigger on-call notification. Filter policy changes must be deployed via IaC — console changes create drift.
Assessment Questions:
  1. Are all SNS topic/subscription configurations managed via Infrastructure as Code?
  2. Is delivery status logging enabled for all subscription protocols?
  3. Are CloudWatch alarms configured on NumberOfNotificationsFailed and DLQ depth?
Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/ops_ready_to_support_operations_as_code.html

Pillar: Sustainability
Definition: Minimizing the environmental impact of running cloud workloads.
Key Design Principles:
  - Minimize unnecessary processing (filter policies reduce unnecessary deliveries and downstream compute)
  - Use managed services (SNS eliminates self-hosted message broker infrastructure)
  - Maximize utilization (batch publishing reduces per-message network overhead)
Applies To Pub/Sub Messaging: Filter policies eliminate deliveries to subscribers that would discard the message — reducing network, compute, and storage waste. PublishBatch reduces network round trips. SNS + Lambda subscribers have zero idle compute footprint. Avoid over-subscribing (creating subscriptions that filter out >90% of messages — consider separate topics instead).
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Dead-Letter Queue on Every Subscription**
- Pillar Alignment: Reliability, Operational Excellence
- Why: Without a DLQ, messages that fail delivery after retry exhaustion are permanently lost. For HTTP/S endpoints, SNS retries per the delivery policy (configurable). For SQS/Lambda, SNS retries up to 100,015 times over 23 days. After all retries fail, the message is discarded with no recovery. DLQs capture these messages for analysis and manual reprocessing.
- AWS Services: Amazon SNS (subscription), Amazon SQS (DLQ), Amazon CloudWatch (alarms)
- Architecture Decision:
  Every subscription must have a redrive policy (`deadLetterTargetArn`) pointing to an SQS queue. Standard topic subscriptions use Standard SQS DLQs; FIFO topic subscriptions use FIFO SQS DLQs. Set DLQ message retention to 14 days (maximum). Configure CloudWatch alarm on `ApproximateNumberOfMessagesVisible > 0` for the DLQ. The DLQ must be in the same AWS account and region as the subscription. Grant SNS service principal `sqs:SendMessage` permission on the DLQ via queue policy.
- Verification:
  ```bash
  aws sns get-subscription-attributes --subscription-arn <SUBSCRIPTION_ARN>
  # Check for RedrivePolicy attribute with valid deadLetterTargetArn
  ```
- Trade-offs: Adds one SQS queue per subscription (minor cost). DLQ messages require manual intervention or automated Lambda-driven reprocessing. DLQ SQS queue policy must grant SNS access.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html

**Server-Side Encryption (SSE) on All Topics**
- Pillar Alignment: Security
- Why: SNS message bodies may contain PII, financial data, or business-sensitive payloads. SSE encrypts messages at rest using AWS KMS keys. All requests to SSE-enabled topics must use HTTPS and Signature Version 4. Without encryption, message bodies stored in SNS infrastructure are accessible in plaintext at rest.
- AWS Services: Amazon SNS (KmsMasterKeyId attribute), AWS KMS (symmetric encryption keys)
- Architecture Decision:
  All topics must have `KmsMasterKeyId` set — either to the AWS-managed key (`alias/aws/sns`) for simplicity or a customer-managed CMK for key rotation control and cross-account scenarios. Use customer-managed CMK when: compliance requires key control, cross-account subscribers need access (key policy must grant Decrypt), or CloudTrail key-usage audit is required. Note: SSE-KMS adds KMS API call costs per publish and delivery.
- Verification:
  ```bash
  aws sns get-topic-attributes --topic-arn <TOPIC_ARN>
  # Check for KmsMasterKeyId attribute — must be present and valid
  ```
- Trade-offs: AWS-managed key is free (included in SNS cost). Customer-managed CMK adds $1/month + $0.03 per 10,000 KMS API calls. Cross-account subscribers with encrypted topics require KMS key policy granting Decrypt to the subscriber's account/role. Services publishing to encrypted topics (S3, CloudWatch, etc.) need kms:GenerateDataKey and kms:Decrypt permissions.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html

**HTTPS-Only Publishing Enforcement**
- Pillar Alignment: Security
- Why: Publishing over HTTP (without TLS) exposes message contents in transit to network-level eavesdropping and man-in-the-middle attacks. While SNS supports HTTP, it is never acceptable for production workloads. The Well-Architected Security pillar mandates encryption in transit for all data paths.
- AWS Services: Amazon SNS (topic access policy with aws:SecureTransport condition)
- Architecture Decision:
  Add a Deny statement in the topic access policy for `SNS:Publish` when `aws:SecureTransport` is `false`. This prevents any publish attempt over HTTP. All AWS SDKs use HTTPS by default, but this guardrail catches misconfigured custom clients or legacy integrations.
  ```json
  {
    "Sid": "DenyHTTPPublish",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "SNS:Publish",
    "Resource": "<TOPIC_ARN>",
    "Condition": { "Bool": { "aws:SecureTransport": "false" } }
  }
  ```
- Verification:
  ```bash
  aws sns get-topic-attributes --topic-arn <TOPIC_ARN> --query 'Attributes.Policy'
  # Parse JSON — verify Deny statement with aws:SecureTransport condition exists
  ```
- Trade-offs: None — HTTPS is universally supported by all AWS SDKs and CLI. This guardrail adds zero operational overhead and blocks only misconfigured non-TLS clients.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html

**Message Filtering at Subscription Level**
- Pillar Alignment: Cost Optimization, Performance Efficiency
- Why: Without filter policies, every subscriber receives every message published to the topic. This generates unnecessary deliveries (billable), unnecessary downstream processing (wasted compute), and forces consumers to implement discard logic that SNS can handle natively. Filter policies enable content-based routing at the infrastructure level.
- AWS Services: Amazon SNS (subscription filter policies), CloudWatch (NumberOfNotificationsFilteredOut metric)
- Architecture Decision:
  Define filter policies on subscriptions when subscribers need a subset of topic messages. Use `FilterPolicyScope: MessageAttributes` (default) for routing metadata (event_type, priority, region). Use `FilterPolicyScope: MessageBody` for payload-level filtering (JSON field matching). Design message attribute schemas as a shared contract between publishers and subscribers. Maximum 200 filter policies per topic.
- Verification:
  ```bash
  aws sns get-subscription-attributes --subscription-arn <SUBSCRIPTION_ARN>
  # Check FilterPolicy attribute — should be set for subscriptions that don't need all messages
  ```
  CloudWatch: Monitor `NumberOfNotificationsFilteredOut` metric — high values confirm filtering is active and saving unnecessary deliveries.
- Trade-offs: Filter policies add publish-time evaluation overhead (negligible). Maximum filter policy complexity has constraints (5 attribute names, 150 value combinations). Very complex filtering may require EventBridge instead.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html

**Delivery Status Logging Enabled**
- Pillar Alignment: Operational Excellence
- Why: Without delivery status logging, failed deliveries are invisible — you cannot determine which messages failed, why they failed, or which endpoints are experiencing issues. Delivery status logging records both successful and failed deliveries to CloudWatch Logs, enabling operational visibility and troubleshooting.
- AWS Services: Amazon SNS (delivery status logging attributes), Amazon CloudWatch Logs, AWS IAM (logging role)
- Architecture Decision:
  Enable delivery status logging for all subscription protocols used on the topic. Configure per-protocol: `HTTPSuccessFeedbackRoleArn`, `HTTPFailureFeedbackRoleArn`, `LambdaSuccessFeedbackRoleArn`, `LambdaFailureFeedbackRoleArn`, `SQSSuccessFeedbackRoleArn`, `SQSFailureFeedbackRoleArn`, `FirehoseSuccessFeedbackRoleArn`, `FirehoseFailureFeedbackRoleArn`. Set sample rate (`HTTPSuccessFeedbackSampleRate`) to 100% for debugging or 1-10% for cost optimization in production.
- Verification:
  ```bash
  aws sns get-topic-attributes --topic-arn <TOPIC_ARN>
  # Check for *SuccessFeedbackRoleArn and *FailureFeedbackRoleArn attributes per protocol
  ```
- Trade-offs: CloudWatch Logs ingestion cost ($0.50/GB ingested). Set success sample rate lower (1-5%) for high-volume topics to control cost. Always log failures at 100% — failed deliveries must always be visible.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-topic-attributes.html

**Raw Message Delivery for SQS Subscribers**
- Pillar Alignment: Performance Efficiency, Cost Optimization
- Why: Without Raw Message Delivery, SNS wraps the original message in a JSON envelope containing metadata (Type, MessageId, TopicArn, Timestamp, Message, etc.). For SQS subscribers, this means the consumer must parse the SNS envelope to extract the actual message body — adding complexity, increasing payload size, and preventing direct use of message attributes for filtering at the SQS level.
- AWS Services: Amazon SNS (subscription RawMessageDelivery attribute), Amazon SQS
- Architecture Decision:
  Set `RawMessageDelivery: true` on all SQS and HTTP/S subscriptions unless the consumer explicitly requires SNS envelope metadata (TopicArn, UnsubscribeURL, etc.). With Raw Message Delivery enabled, SNS message attributes are mapped directly to SQS message attributes — enabling Lambda Event Source Mapping filtering on SQS.
- Verification:
  ```bash
  aws sns get-subscription-attributes --subscription-arn <SUBSCRIPTION_ARN>
  # Check RawMessageDelivery = true for SQS and HTTP/S subscriptions
  ```
- Trade-offs: Consumers lose access to SNS metadata (TopicArn, Subject, Timestamp, UnsubscribeURL) which is included in the envelope. If consumers need to know which topic the message came from, either keep envelope or add a message attribute.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-large-payload-raw-message-delivery.html

---

### ⚠️ Architectural Decisions

**Standard Topic vs FIFO Topic**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Standard Topic | SNS Standard | Throughput (virtually unlimited), protocol flexibility (all protocols), subscription scale (12.5M/topic) | Ordering, exactly-once delivery | No ordering requirement; need HTTP/S, email, SMS, mobile push delivery; throughput > 3K msgs/sec |
  | FIFO Topic | SNS FIFO (.fifo) | Ordering per group, deduplication | Protocol support (SQS FIFO only), subscription limit (100/topic), throughput ceiling (3K msgs/sec per topic) | Strict per-entity ordering required; all subscribers are SQS FIFO queues; throughput ≤ 3K msgs/sec |

- Cost Profile: Standard: $0.50 per million publishes (first 1M free). FIFO: $0.50 per million publishes. Delivery to SQS is free. Delivery to HTTP/S is $0.60 per million. SMS and mobile push have separate per-delivery charges. FIFO archive/replay adds storage cost.
- Lock-in Assessment: Both topic types are SNS-specific. Cannot convert between Standard and FIFO in-place (must create new topic). FIFO subscribers are locked to SQS FIFO queues only.
- Architect Instruction: "Ask 'Do all subscribers use SQS FIFO queues, and is strict ordering per-entity required?' — if NO to either, use Standard. If YES to both and throughput is < 3K msgs/sec, use FIFO."
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-fifo-topics.html

**SNS vs EventBridge for Event Distribution**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | SNS Standard Topic | Amazon SNS | Throughput, protocol flexibility (SQS/Lambda/HTTP/email/SMS/push), low cost, fan-out simplicity | Complex routing rules, event schema, archive/replay for standard | Simple fan-out to known subscribers; A2P notifications needed; high throughput (30K+ msgs/sec) |
  | EventBridge Event Bus | Amazon EventBridge | Content-based routing (300+ rules), schema registry, event archive/replay, 3rd-party SaaS integration | Throughput ceiling (varies by region), higher per-event cost ($1/M), fewer delivery protocols | Complex event routing; multiple targets per rule with different filtering; SaaS event integration; archive/replay for standard events |
  | SNS FIFO Topic | Amazon SNS FIFO | Strict ordering + fan-out + deduplication + replay | Protocol limited to SQS FIFO, 100 subs max, 3K msgs/sec ceiling | Ordered fan-out to multiple FIFO queues with replay capability |

- Cost Profile: SNS Standard: $0.50/M publishes + delivery cost per protocol. EventBridge: $1.00/M events. SNS is 2x cheaper per event at base level. EventBridge adds cost for schema registry, archive storage.
- Scaling Characteristics: SNS Standard scales to 30K msgs/sec (us-east-1, soft limit). EventBridge varies by region (400-2,400 PutEvents/sec base). Both support quota increases.
- Operational Burden: SNS is simpler (topic → subscriptions with filter policies). EventBridge has more operational surface (rules, targets, connections, API destinations, schemas, archives).
- Architect Instruction: "Ask 'Does the event routing require rules with more than 5 attribute conditions, content-based routing to different target types per rule, or SaaS event integration?' — if YES, use EventBridge. If simple fan-out to SQS/Lambda, use SNS."
- Source: https://docs.aws.amazon.com/sns/latest/dg/welcome-features.html

**Direct SNS → Lambda vs SNS → SQS → Lambda**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | SNS → Lambda (direct) | SNS + Lambda | Latency (immediate invocation), simplicity | Backpressure control, batch processing, retry visibility | Low-volume events; processing time < 15 min; immediate processing required; no batching needed |
  | SNS → SQS → Lambda (buffered) | SNS + SQS + Lambda ESM | Backpressure (SQS absorbs bursts), batching (up to 10K per invocation), retry control (visibility timeout), DLQ visibility (SQS DLQ) | Additional hop latency (~10-50ms), additional infrastructure | High-volume events; need burst absorption; batch processing; fine-grained retry control; need to pause processing |

- Cost Profile: Direct SNS→Lambda: SNS delivery cost + Lambda invocation per message. Buffered: SNS delivery (free to SQS) + SQS API cost + Lambda invocation (batched = fewer invocations). Buffered is cheaper at high volume due to batching.
- Scaling Characteristics: Direct: Lambda concurrency scales per message (1 message = 1 invocation). Buffered: Lambda ESM batches messages (configurable 1-10K) = fewer concurrent executions, better fan-in.
- Architect Instruction: "Ask 'Will this subscription receive bursts > 1000 messages/second, or does the Lambda need batch processing?' — if YES to either, use SNS→SQS→Lambda. If < 100 msgs/sec steady-state, direct SNS→Lambda is simpler."
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-lambda-as-subscriber.html

**Encryption: AWS-Managed Key vs Customer-Managed CMK**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | AWS-Managed Key (alias/aws/sns) | SNS + KMS (aws-managed) | Simplicity (zero key management), lower cost | Key rotation control, cross-account usage, CloudTrail key-usage audit granularity | No cross-account subscribers; compliance accepts AWS-managed rotation; no key-usage audit requirement |
  | Customer-Managed CMK | SNS + KMS (customer CMK) | Full key control, custom rotation schedule, cross-account key sharing, detailed CloudTrail audit | Higher cost ($1/mo per key + API calls), key management overhead, requires key policy maintenance | Cross-account subscribers need encrypted topic access; compliance mandates customer-managed keys; audit trail for key usage required |

- Cost Profile: AWS-Managed = minimal additional cost (KMS calls included). Customer-Managed = $1/month per CMK + $0.03 per 10,000 KMS API calls (significant at 1M+ publishes/day). Each publish and each delivery generates KMS API calls.
- Architect Instruction: "Ask 'Do any subscribers exist in different AWS accounts, or does compliance require customer-managed encryption keys with rotation audit trail?' — if NO to both, use AWS-managed key. If YES, use customer-managed CMK."
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html

**Single Topic with Filtering vs Multiple Topics**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Single Topic + Filter Policies | SNS (one topic, filtered subscriptions) | Topic management simplicity, publisher simplicity (publish to one endpoint) | Filter policy complexity limits (200 per topic), coupling all events to one topic's access policy | ≤ 200 subscriber filter patterns; events share same publishing context; filter criteria are simple attribute matches |
  | Multiple Topics (per event type) | SNS (multiple topics) | Clear topic ownership, independent access policies, independent scaling, no filter complexity | Publisher must know target topic; more infrastructure to manage; cross-topic correlation harder | Event types have fundamentally different publishers, access patterns, or security requirements; > 200 subscribers per event type |

- Architect Instruction: "Ask 'Do these events share the same publisher, access control requirements, and encryption settings?' — if YES and total subscriber filters ≤ 200, use one topic with filters. If events have different security boundaries or different publishing services, use separate topics."
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html

---

### 🚫 Anti-Patterns

**Wildcard Principal in Topic Access Policy Without Conditions**
- Risk Level: CRITICAL
- Why: Violates Security pillar. A topic policy with `"Principal": "*"` without restrictive conditions allows any AWS account or unauthenticated entity to publish messages (injection), subscribe (data exfiltration), or list subscriptions (information disclosure). This is the SNS equivalent of a publicly writable endpoint.
- Instead: Use specific principal ARNs (`"Principal": {"AWS": "arn:aws:iam::123456789012:role/ServiceRole"}`). For service integrations (S3, CloudWatch, EventBridge), use `aws:SourceArn` and `aws:SourceAccount` conditions. For cross-account access, specify the external account's principal explicitly.
- Detection:
  ```bash
  aws sns get-topic-attributes --topic-arn <TOPIC_ARN> --query 'Attributes.Policy'
  # Parse JSON — alert if any statement has Principal: "*" without restrictive Condition keys
  ```
  Use IAM Access Analyzer to identify publicly accessible topics across the account.
- Impact: Message injection (publishing malicious data), data exfiltration (subscribing and receiving all messages), topic abuse (DoS via flooding), compliance violation.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html

**No Dead-Letter Queue on Subscriptions**
- Risk Level: CRITICAL
- Why: Violates Reliability pillar. Without a DLQ, messages that fail delivery after all retry attempts are permanently lost. For HTTP/S endpoints with default retry policy, this happens after 3 retries (within seconds). For SQS/Lambda endpoints (23-day retry), this is rare but catastrophic when it occurs. Either way, there is zero recovery path without a DLQ.
- Instead: Configure a redrive policy (`deadLetterTargetArn`) on every subscription pointing to an SQS queue. Set DLQ retention to 14 days. Configure CloudWatch alarm on DLQ depth. Grant SNS service principal `sqs:SendMessage` on the DLQ.
- Detection:
  ```bash
  aws sns list-subscriptions-by-topic --topic-arn <TOPIC_ARN>
  # For each subscription:
  aws sns get-subscription-attributes --subscription-arn <SUB_ARN>
  # Alert if RedrivePolicy is absent
  ```
- Impact: Silent permanent message loss, no operational visibility into delivery failures, no recovery mechanism for subscriber outages.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html

**Encryption Disabled on Topics**
- Risk Level: CRITICAL
- Why: Violates Security pillar. Topic message bodies stored without encryption at rest expose sensitive data if underlying storage is compromised. Since SNS SSE with the AWS-managed key has minimal additional cost, there is no valid justification for unencrypted production topics.
- Instead: Enable SSE on all topics with `KmsMasterKeyId` set to at minimum `alias/aws/sns` (AWS-managed). For topics requiring cross-account subscriber access or compliance audit, use a customer-managed CMK.
- Detection:
  ```bash
  aws sns get-topic-attributes --topic-arn <TOPIC_ARN>
  # Alert if KmsMasterKeyId attribute is absent or empty
  ```
  AWS Config Rule: Use Security Hub control `SNS.1` (SNS topics should be encrypted at rest using AWS KMS).
- Impact: Data breach (message contents exposed at rest), compliance violation (HIPAA, PCI-DSS, SOC2, GDPR).
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html

**HTTP Subscriber Endpoints Without HTTPS**
- Risk Level: HIGH
- Why: Violates Security pillar. Delivering messages to HTTP (non-TLS) endpoints exposes message contents in transit. Network-level attackers can eavesdrop on message payloads, intercept subscription confirmation tokens, or perform man-in-the-middle attacks. AWS explicitly recommends never using raw HTTP for endpoint delivery.
- Instead: Always use HTTPS endpoints for HTTP/S subscriptions. Verify SSL certificates are valid on receiving endpoints. Use raw IP addresses (e.g., `http://1.2.3.4/path`) is also prohibited — always use domain names with HTTPS.
- Detection:
  ```bash
  aws sns list-subscriptions-by-topic --topic-arn <TOPIC_ARN>
  # Alert if any subscription Endpoint starts with "http://" (not "https://")
  ```
- Impact: Data breach (message contents exposed in transit), subscription hijacking (confirmation token interception), man-in-the-middle (message manipulation).
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html

**Publishing Sensitive Data Without Message Data Protection**
- Risk Level: HIGH
- Why: Violates Security and Compliance pillars. Publishing PII, PHI, or financial data (credit card numbers, SSNs, email addresses) through topics without MDP means no audit trail of sensitive data flow, no ability to mask data for specific subscribers, and no prevention of accidental sensitive data exposure to unauthorized subscriptions.
- Instead: Enable Message Data Protection policies on topics that transit sensitive data. Configure audit operations (log sensitive data findings to CloudWatch), de-identify operations (mask data before delivery to specific subscriptions), and deny operations (reject messages containing disallowed data types at publish time).
- Detection:
  ```bash
  aws sns get-data-protection-policy --resource-arn <TOPIC_ARN>
  # Alert if policy is empty for topics flagged as PII/PHI-transiting
  ```
- Impact: Compliance violation (GDPR, HIPAA, PCI-DSS), unaudited sensitive data flow, accidental PII exposure to unauthorized subscribers.
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-message-data-protection.html

**Overly Broad Subscriptions Without Filtering**
- Risk Level: MEDIUM
- Why: Violates Cost Optimization and Performance Efficiency pillars. Subscribers that receive all messages but discard most of them waste delivery costs (each delivery is billable for HTTP/S/SMS/mobile), waste downstream compute (Lambda invocations, SQS processing), and increase attack surface (more data delivered to more endpoints than necessary).
- Instead: Implement subscription filter policies that match only the messages the subscriber needs. Use MessageAttributes scope for routing metadata filters, or MessageBody scope for payload-level JSON filtering. If a subscriber discards > 50% of received messages, a filter policy is overdue.
- Detection:
  Monitor CloudWatch metrics: `NumberOfNotificationsDelivered` vs actual consumer processing rate. If consumers discard > 50% of received messages, filter policies should be applied.
- Impact: Cost overrun (unnecessary deliveries), wasted compute (processing then discarding), increased attack surface (more data flowing to more endpoints).
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html

**Single Message Group ID for All FIFO Messages**
- Risk Level: HIGH
- Why: Violates Performance Efficiency pillar. A single Message Group ID serializes ALL message delivery — only one message at a time can be in-flight per group. This caps throughput at 300 messages/second per group (hard limit), negating parallelism across independent logical entities.
- Instead: Use high-cardinality Message Group IDs (customer-id, order-id, tenant-id). Each message group processes independently and in parallel. With `FifoThroughputScope=MessageGroup`, each group gets 300 msgs/sec. With `FifoThroughputScope=Topic`, the topic gets 3,000 msgs/sec shared across groups.
- Detection:
  Audit publisher code for hardcoded or constant `MessageGroupId` values. Monitor CloudWatch `NumberOfMessagesPublished` — if approaching 300/sec with single group, parallelism is bottlenecked.
- Impact: Throughput collapse (300 msgs/sec cap), delivery delays, inability to scale FIFO workload.
- Source: https://docs.aws.amazon.com/sns/latest/dg/fifo-message-grouping.html

---

## Cloud-Native Design Patterns

**Fan-Out Pattern (SNS → Multiple SQS)**
- Category: Communication
- Problem: A single domain event (order placed, payment completed, user registered) must trigger multiple independent downstream processes without coupling the publisher to each consumer. Adding or removing consumers must not require publisher code changes.
- Solution on AWS:
  Publisher publishes to an SNS topic. Multiple SQS queues subscribe to the topic, each feeding an independent consumer (Lambda, ECS, EC2). Each subscriber queue has its own DLQ, scaling policy, and processing rate. Filter policies on subscriptions enable selective message delivery.
- Services Used: Amazon SNS (fan-out hub), Amazon SQS (per-consumer queues), AWS Lambda or Amazon ECS (consumers), CloudWatch (monitoring)
- When to Apply: Multiple independent services need the same event. Services process at different rates. Adding/removing consumers must be zero-impact to publishers. Services have different reliability/SLA requirements.
- When NOT to Apply: Single consumer (use direct SQS instead — no SNS needed). Need content-based routing to a single target (use EventBridge). Need message replay/archive for standard topics (use EventBridge with archive or Firehose subscriber).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Decoupling | Publisher knows nothing about consumers | Additional SNS hop adds ~ms latency |
  | Scalability | Each consumer scales independently | Message duplicated per subscriber (storage) |
  | Reliability | One consumer failure doesn't affect others | More queues and DLQs to monitor |
  | Flexibility | Add/remove consumers without code changes | SNS topic access policy management |

- Complements: Dead-Letter Queue per subscription, Message Filtering, Raw Message Delivery, Queue-Based Load Leveling
- Source: https://aws.amazon.com/getting-started/hands-on/send-fanout-event-notifications/

**Event-Driven Notification Pattern**
- Category: Communication
- Problem: System events (CloudWatch Alarms, S3 object creation, Auto Scaling lifecycle, CodePipeline state change) must notify multiple consumers (operations teams, monitoring systems, downstream workflows) without building custom notification infrastructure.
- Solution on AWS:
  AWS services publish events to SNS topics natively. Subscribe appropriate endpoints: SQS for queue-based processing, Lambda for automated remediation, email/SMS for human notification, HTTP/S for external system integration. Use filter policies to route specific event types to specific subscribers.
- Services Used: Amazon SNS (notification hub), Amazon CloudWatch (alarm actions → SNS), Amazon S3 (event notifications → SNS), AWS Lambda (automated response), email/SMS (human notification)
- When to Apply: AWS service events need multi-channel notification. Operations teams need alerts across multiple channels (email + PagerDuty + Slack). Multiple automated systems need to react to the same infrastructure event.
- When NOT to Apply: Single notification channel (use direct service integration — e.g., CloudWatch → Lambda directly). Complex event correlation required (use EventBridge). Need event history/replay (use EventBridge with archive).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Multi-channel | Single event → email + SMS + Lambda + SQS simultaneously | Multiple delivery protocols to manage and monitor |
  | AWS Integration | Native service integration (S3, CloudWatch, ASG) | Topic policy must grant each service permission |
  | Operational | Real-time notification without polling | SMS/email costs per delivery; potential alert fatigue |
  | Simplicity | No custom notification code needed | Topic configuration and subscription management |

- Complements: CloudWatch Alarms, AWS Chatbot (Slack integration), Lambda (automated remediation)
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-common-scenarios.html

**FIFO Fan-Out with Ordered Processing**
- Category: Communication
- Problem: Multiple downstream services need the same ordered event stream (e.g., order state changes, financial transactions) with exactly-once delivery guarantee and strict per-entity ordering, without coupling the publisher to each consumer's queue.
- Solution on AWS:
  Publisher publishes to an SNS FIFO topic with Message Group ID (per-entity identifier). Multiple SQS FIFO queues subscribe to the FIFO topic. Each subscriber FIFO queue receives messages in the exact order published, per message group. Deduplication prevents duplicate delivery. Each consumer processes independently while maintaining order within each entity.
- Services Used: Amazon SNS FIFO (ordered fan-out), Amazon SQS FIFO (per-consumer ordered queue), AWS Lambda (consumer via ESM on FIFO queue)
- When to Apply: Multiple services need the same event stream with ordering (e.g., order service + analytics service + audit service all need order events in sequence). Business requirement: per-entity ordering + multi-consumer delivery.
- When NOT to Apply: Subscribers need non-SQS protocols (Lambda direct, HTTP/S, email). More than 100 subscribers needed. Throughput > 3K msgs/sec. Ordering not required (use Standard topic).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Ordering | Strict per-group ordering guaranteed across all subscribers | Throughput limited to 3K msgs/sec per topic |
  | Deduplication | Exactly-once semantics within 5-min window | 5-min deduplication window is a hard limit |
  | Fan-out | Multiple ordered consumers from single publish | Max 100 subscriptions; SQS FIFO only |
  | Replay | Built-in message archive and replay for recovery | Archive storage cost; replay requires idempotent consumers |

- Complements: Message Archiving and Replay, Dead-Letter Queues (FIFO), High-Throughput Mode
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-fifo-topics.html

**Claim-Check Pattern (Large Payloads via S3)**
- Category: Communication
- Problem: Event payloads exceed the SNS message size limit (256 KB) or are large enough that duplicating them across multiple fan-out subscribers is wasteful and expensive.
- Solution on AWS:
  Publisher stores the full payload in S3, then publishes a "claim check" message to SNS containing the S3 object reference (bucket, key, version). Subscribers receive the lightweight reference and retrieve the full payload from S3 only when needed. SNS Extended Client Library automates this pattern.
- Services Used: Amazon SNS (claim-check distribution), Amazon S3 (payload storage), SNS Extended Client Library (automation)
- When to Apply: Payloads > 256 KB. Large payloads fanned out to many subscribers (storing once in S3 is cheaper than duplicating in each delivery). Some subscribers don't need the full payload (can filter on claim-check metadata).
- When NOT to Apply: All payloads < 256 KB. All subscribers always need the full payload immediately. Latency-critical path (S3 GET adds latency vs inline message).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Payload size | Up to 2 GB payloads supported | S3 PUT + GET latency per retrieval |
  | Cost efficiency | Store once, reference many times | S3 storage + API call costs |
  | Complexity | Extended Client Library handles transparently | Library dependency; S3 lifecycle management |
  | Selective retrieval | Subscribers can inspect metadata before downloading | Additional logic in consumers |

- Complements: Fan-Out Pattern, Raw Message Delivery, S3 Event Notifications
- Source: https://docs.aws.amazon.com/sns/latest/dg/large-message-payloads.html

**Content-Based Routing Pattern**
- Category: Communication
- Problem: A single event stream contains multiple event types or categories, and different subscribers need different subsets. Without filtering, all subscribers receive all messages and must implement discard logic.
- Solution on AWS:
  Publish all events to a single SNS topic with well-defined message attributes (event_type, priority, source_region, tenant_id). Each subscription defines a filter policy matching only the messages it needs. SNS evaluates filter policies server-side and only delivers matching messages to each subscriber.
- Services Used: Amazon SNS (topic + filter policies), message attributes (routing metadata), Amazon SQS or Lambda (filtered consumers)
- When to Apply: Multiple event types share a publishing context. Subscribers need predictable subsets. Filter criteria can be expressed as attribute equality, prefix, numeric range, or exists checks. Total filter patterns ≤ 200 per topic.
- When NOT to Apply: Complex routing logic (> 5 attribute conditions, nested payload matching). More than 200 distinct filter patterns per topic. Different event types have fundamentally different security boundaries.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost savings | Only matching messages delivered (reduces delivery + processing cost) | Filter policy evaluation on every publish |
  | Simplicity | Routing logic in infrastructure, not consumer code | Filter policy schema must be designed upfront |
  | Flexibility | Add/modify filters without code deploy | Filter policy constraints (150 value combinations) |
  | Debugging | NumberOfNotificationsFilteredOut metric visible | Mismatched filters silently drop messages |

- Complements: Fan-Out Pattern, Message Attributes Schema, Dead-Letter Queue
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html

**Cross-Region Event Replication**
- Category: Resilience
- Problem: Events published in one AWS region need to be replicated to another region for disaster recovery, multi-region processing, or geo-local consumer delivery.
- Solution on AWS:
  Primary region: Publisher → SNS topic → SQS subscription. A Lambda function (or SQS consumer) in the primary region reads from the queue and publishes to an SNS topic in the secondary region. Alternative: Use SNS → Firehose → S3 (with cross-region replication) for async archive-based replication.
- Services Used: Amazon SNS (per-region topics), Amazon SQS (buffering), AWS Lambda (replication logic), Amazon S3 (optional cross-region archive)
- When to Apply: Multi-region active-active or active-passive architectures. Compliance requires data residency with cross-region backup. Consumer latency requirements demand geo-local event delivery.
- When NOT to Apply: Single-region workload with no DR requirement. SNS FIFO topics (ordering across regions adds significant latency and complexity). Low-value events where loss during regional failure is acceptable.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Events available in multiple regions | Cross-region data transfer cost |
  | Latency | Geo-local delivery to regional consumers | Replication delay (seconds to minutes) |
  | Complexity | DR capability for event-driven systems | Replication logic to build and maintain |
  | Ordering | N/A for standard topics | Cross-region FIFO ordering is extremely complex |

- Complements: Multi-Region DynamoDB (state replication), Route 53 (traffic routing), S3 Cross-Region Replication
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/sns-pub-sub.html

---

## Security Architecture

**Identity & Access Management for SNS**
- AWS Services: AWS IAM (identity policies), SNS Topic Policies (resource policies), AWS Organizations SCPs (guardrails), VPC Endpoints (network restriction)
- Architecture:
  Three-layer access control: (1) IAM identity policies on the publisher/subscriber role — specify allowed SNS actions (sns:Publish, sns:Subscribe, sns:Unsubscribe) and topic ARN resource; (2) SNS resource policy on the topic — specify which principals can interact, with conditions (aws:SourceArn, aws:SourceAccount, aws:sourceVpce, aws:SecureTransport); (3) SCP guardrails at the organization level — deny SNS operations without encryption, deny public topic policies, deny subscriptions to external accounts without approval. Three distinct access roles: Administrator (create/delete/configure topics), Publisher (publish messages only), Subscriber (subscribe/unsubscribe, receive messages).
- Configuration Essentials:
  - Publisher IAM role: Allow `sns:Publish` on specific topic ARN only
  - Subscriber IAM role: Allow `sns:Subscribe`, `sns:Unsubscribe` on specific topic ARN; allow `sns:ConfirmSubscription` for pending subscriptions
  - Topic policy for S3 integration: Allow `sns:Publish` with condition `aws:SourceArn` = S3 bucket ARN and `aws:SourceAccount` = account ID
  - Topic policy for CloudWatch: Allow `sns:Publish` with condition `aws:SourceArn` = CloudWatch alarm ARN
  - VPC Endpoint policy: Restrict topic access to specific VPC endpoints
  - HTTPS enforcement: Deny `sns:Publish` when `aws:SecureTransport = false`
- Verification:
  ```bash
  # Check topic policy
  aws sns get-topic-attributes --topic-arn <TOPIC_ARN> --query 'Attributes.Policy'
  # Verify no public access via Access Analyzer
  aws accessanalyzer list-findings --analyzer-arn <ANALYZER_ARN> --filter '{"resourceType":{"eq":["AWS::SNS::Topic"]}}'
  # Simulate publisher permissions
  aws iam simulate-principal-policy --policy-source-arn <ROLE_ARN> --action-names sns:Publish --resource-arns <TOPIC_ARN>
  ```
- Compliance Alignment: SOC2 CC6.1 (logical access controls), PCI-DSS Requirement 7 (restrict access to need-to-know), HIPAA Access Controls (§ 164.312(a))
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html

**Data Protection (Encryption & MDP)**
- AWS Services: Amazon SNS (SSE with KMS, Message Data Protection), AWS KMS (key management), AWS CloudTrail (API audit), Amazon CloudWatch Logs (MDP audit findings)
- Architecture:
  Two complementary data protection layers: (1) SSE encrypts message bodies at rest using KMS keys — messages encrypted on receipt, decrypted on delivery; (2) Message Data Protection (MDP) scans message content for sensitive data patterns (PII, PHI, financial data) and can audit, mask, or deny based on findings. Both should be enabled for comprehensive protection. For MDP: configure inbound audit (log when sensitive data is published), inbound deny (reject messages with disallowed data types), and outbound de-identify (mask sensitive data before delivery to specific subscriptions).
- Configuration Essentials:
  - SSE: `KmsMasterKeyId: alias/aws/sns` (AWS-managed) or `KmsMasterKeyId: arn:aws:kms:region:account:key/key-id` (customer-managed)
  - KMS Key Policy for cross-account: Allow `kms:Decrypt`, `kms:GenerateDataKey*` to subscriber accounts and AWS services that publish to the encrypted topic
  - MDP Policy: JSON policy specifying `Statement` with `Operation` (Audit/Deny/Deidentify), `DataDirection` (Inbound/Outbound), `DataIdentifier` (PII types), `Principal` (which publishers/subscribers)
  - All HTTPS enforcement: `aws:SecureTransport` condition in topic policy
- Verification:
  ```bash
  # Check SSE
  aws sns get-topic-attributes --topic-arn <TOPIC_ARN> | jq '.Attributes.KmsMasterKeyId'
  # Check MDP
  aws sns get-data-protection-policy --resource-arn <TOPIC_ARN>
  ```
- Compliance Alignment: GDPR Article 32 (encryption), HIPAA §164.312(a)(2)(iv) (encryption), PCI-DSS Requirement 3 (protect stored data), SOC2 CC6.7 (restrict transmission)
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html

**Network Security (VPC Endpoints)**
- AWS Services: Amazon SNS (VPC endpoint support), AWS PrivateLink (com.amazonaws.region.sns), VPC Endpoint Policies
- Architecture:
  SNS VPC endpoints (Interface type) enable publishing and subscribing to topics without internet access — traffic stays on the AWS private network. VPC endpoint policies restrict which topics can be accessed from the VPC. Topic policies can restrict access to specific VPC endpoints using `aws:sourceVpce` condition. Combine VPC endpoints with topic policy conditions to ensure topics are only accessible from authorized VPCs.
- Configuration Essentials:
  - Create Interface VPC Endpoint for `com.amazonaws.<region>.sns`
  - VPC Endpoint Policy: Restrict allowed actions and topic ARNs
  - Topic policy condition: `"aws:sourceVpce": "vpce-1234567890abcdef0"`
  - Security group on VPC endpoint: Allow HTTPS (443) from application subnets only
  - Private DNS enabled: Allows using standard SNS endpoint URLs from within VPC
- Verification:
  ```bash
  # List VPC endpoints
  aws ec2 describe-vpc-endpoints --filters "Name=service-name,Values=com.amazonaws.<region>.sns"
  # Check endpoint policy
  aws ec2 describe-vpc-endpoints --vpc-endpoint-ids <ENDPOINT_ID> --query 'VpcEndpoints[].PolicyDocument'
  ```
- Compliance Alignment: PCI-DSS Requirement 1 (network segmentation), HIPAA §164.312(e)(1) (transmission security), SOC2 CC6.6 (system boundaries)
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-internetwork-traffic-privacy.html

---

## Operational Patterns

**Delivery Monitoring & Alerting**
- Operational Domain: Observability
- AWS Services: Amazon SNS (delivery status logging), Amazon CloudWatch (metrics + alarms), Amazon CloudWatch Logs (delivery logs)
- Architecture:
  Three monitoring layers: (1) CloudWatch Metrics — `NumberOfMessagesPublished`, `NumberOfNotificationsDelivered`, `NumberOfNotificationsFailed`, `NumberOfNotificationsFilteredOut`, `PublishSize`; (2) Delivery Status Logging — per-protocol success/failure logging to CloudWatch Logs with message ID, subscription ARN, delivery status, provider response; (3) DLQ Monitoring — CloudWatch alarm on `ApproximateNumberOfMessagesVisible` for each subscription's DLQ.
- Cost Profile: Medium — CloudWatch Metrics are free (included with SNS). Delivery status logging costs: CloudWatch Logs ingestion ($0.50/GB). Reduce cost by sampling success logs (1-10%) and always logging failures (100%).
- Automation:
  - Automated: CloudWatch alarms on `NumberOfNotificationsFailed > 0` → SNS alert to ops team
  - Automated: DLQ alarm `ApproximateNumberOfMessagesVisible > 0` → trigger DLQ processing Lambda
  - Manual: DLQ message analysis (inspect failed messages, determine root cause)
  - Manual: Delivery log investigation (correlate message ID with subscriber failure)
- Runbook Skeleton:
  1. Alert triggers on `NumberOfNotificationsFailed > threshold`
  2. Check delivery status logs: identify failing subscription ARN and error type
  3. Classify failure: client-side (endpoint deleted/misconfigured) vs server-side (endpoint unavailable)
  4. Client-side: Fix subscription endpoint or remove dead subscription
  5. Server-side: Verify endpoint health; messages will retry automatically (23 days for SQS/Lambda)
  6. Check DLQ for messages that exhausted retries — analyze and reprocess
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-monitoring-using-cloudwatch.html

**Subscription Management & Lifecycle**
- Operational Domain: Change Management
- AWS Services: Amazon SNS (subscription management), AWS CloudFormation/CDK (IaC), AWS Config (drift detection)
- Architecture:
  Subscription lifecycle: Create → Pending Confirmation → Confirmed → Active → (optional) Unsubscribe. For HTTP/S and email/SMS, subscription requires explicit confirmation from the endpoint owner. For SQS/Lambda/Firehose (same account), subscription is auto-confirmed. Cross-account SQS subscriptions require queue policy granting SNS. All subscriptions should be managed via IaC to prevent drift and ensure DLQ/filter policy consistency.
- Cost Profile: Low — subscription operations are free (no per-subscription charge). Cost is per-delivery once confirmed.
- Automation:
  - Automated: IaC deployment for subscription creation/modification/deletion
  - Automated: AWS Config rule to detect subscriptions without DLQs or filter policies
  - Manual: Subscription confirmation for HTTP/S endpoints (owner must click confirm URL)
  - Manual: Review and cleanup of pending subscriptions (5,000 limit per account)
- Runbook Skeleton:
  1. New subscription needed: Add to IaC (CloudFormation/CDK/Terraform) with DLQ + filter policy
  2. Deploy via CI/CD pipeline → subscription created
  3. For HTTP/S: Verify endpoint receives confirmation request and responds with SubscribeURL
  4. Monitor `NumberOfNotificationsDelivered` for new subscription — confirm messages flowing
  5. Decommission: Remove from IaC → subscription deleted automatically
  6. Regular audit: List all subscriptions per topic, verify all have DLQs and appropriate filters
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-create-subscribe-endpoint-to-topic.html

**Cross-Account Topic Sharing**
- Operational Domain: Governance
- AWS Services: Amazon SNS (topic access policy), AWS IAM (cross-account roles), AWS KMS (cross-account key sharing for encrypted topics), AWS Organizations (sharing via organizational conditions)
- Architecture:
  Cross-account patterns: (1) Cross-account publishing — external account's role publishes to your topic (topic policy grants sns:Publish with condition aws:SourceAccount); (2) Cross-account subscribing — external account subscribes their SQS/Lambda to your topic (topic policy grants sns:Subscribe + topic delivers to their endpoint); (3) For encrypted topics, the KMS key policy must grant kms:Decrypt and kms:GenerateDataKey* to the external account.
- Cost Profile: Low — cross-account operations have no additional charge beyond standard SNS pricing. KMS cross-account access may add API call costs in both accounts.
- Automation:
  - Automated: Topic policy managed via IaC with explicit external account ARNs
  - Automated: KMS key policy grants managed alongside topic policy
  - Manual: Approval process for adding new external accounts to topic policy
  - Manual: Regular audit of cross-account access (who can publish/subscribe from external accounts)
- Runbook Skeleton:
  1. External team requests access to topic (publish or subscribe)
  2. Security review: Validate the external account and intended access pattern
  3. Update topic policy via IaC: Add explicit principal ARN with appropriate conditions
  4. For encrypted topics: Update KMS key policy to grant external account access
  5. For cross-account SQS subscriber: External team updates their queue policy to allow SNS delivery
  6. Verify end-to-end: Publish test message → confirm delivery to cross-account endpoint
  7. Regular audit: Review all cross-account principals in topic policy quarterly
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-send-message-to-sqs-cross-account.html

---

## Reference Architectures

**Event-Driven Microservices with SNS Fan-Out**
- Context: Microservices architecture where domain events trigger multiple independent downstream processes
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Event Publishing | Amazon SNS (Standard topic per domain event) | Fan-out hub for domain events |
  | Event Buffering | Amazon SQS (per-consumer queue) | Rate decoupling, failure isolation |
  | Event Processing | AWS Lambda (per-queue consumer) | Stateless event handlers |
  | Dead Letters | Amazon SQS (DLQ per subscription) | Failed delivery capture |
  | Monitoring | Amazon CloudWatch (metrics + logs) | Delivery visibility |
  | Security | AWS KMS (topic encryption) | At-rest encryption |

- Key Decisions:
  - One topic per domain event type (order-placed, payment-completed) vs multiplexed topic with filtering
  - Raw Message Delivery enabled on all SQS subscriptions
  - Filter policies for subscribers that don't need all events from a multiplexed topic
  - DLQ per subscription with CloudWatch alarm
- Scaling Path:
  - Initial: Single topic → 2-3 SQS subscribers → Lambda consumers
  - Growth: Multiple topics per domain, filter policies, dedicated DLQ monitoring Lambda
  - Scale: Regional topic replication, FIFO topics for ordered domains, EventBridge for complex routing
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/sns-pub-sub.html

**Multi-Channel Notification System**
- Context: Application needs to send notifications across multiple channels (email, SMS, push, webhook) from a single publish action
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Publishing | Amazon SNS (Standard topic) | Multi-channel notification hub |
  | Email Delivery | SNS Email subscription | Direct email notification |
  | SMS Delivery | SNS SMS subscription | Direct SMS notification |
  | Mobile Push | SNS Platform Application + Endpoints | iOS/Android push notifications |
  | Webhook Delivery | SNS HTTPS subscription | External system integration |
  | Processing | SNS → SQS → Lambda | Complex notification logic (templating, throttling) |
  | Monitoring | CloudWatch (delivery status logging) | Per-protocol delivery visibility |

- Key Decisions:
  - Direct SNS delivery for simple notifications vs SQS-buffered Lambda for complex formatting
  - SMS spending limits and sandbox mode for development
  - Mobile push platform application configuration (APNS, FCM)
  - Delivery status logging per protocol for troubleshooting
- Scaling Path:
  - Initial: Email + SMS + one webhook endpoint
  - Growth: Mobile push platforms, message filtering by notification type, template Lambda
  - Scale: Migrate SMS to AWS End User Messaging for advanced features; add Firehose subscriber for notification analytics
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-common-scenarios.html

**FIFO Event Processing Pipeline**
- Context: Financial or e-commerce workload requiring strict per-entity event ordering with multiple downstream consumers
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Publishing | Amazon SNS FIFO Topic | Ordered fan-out with deduplication |
  | Buffering | Amazon SQS FIFO Queues (per consumer) | Per-consumer ordered queue |
  | Processing | AWS Lambda (ESM on FIFO queue) | Ordered event handlers (batch size 1-10) |
  | Archive | SNS FIFO Message Archive | In-place message storage for replay |
  | Dead Letters | Amazon SQS FIFO DLQ (per subscription) | Failed ordered delivery capture |
  | Monitoring | Amazon CloudWatch | Throughput and failure monitoring |

- Key Decisions:
  - Message Group ID strategy: per-customer, per-order, or per-account (determines parallelism)
  - FifoThroughputScope: Topic (3K msgs/sec shared) vs MessageGroup (300/sec per group)
  - Archive retention period (1-365 days) and replay strategy
  - Content-based deduplication vs explicit Deduplication ID
- Scaling Path:
  - Initial: Single FIFO topic → 2-3 FIFO queue subscribers → Lambda consumers
  - Growth: High-throughput mode, high-cardinality message groups, archive enabled
  - Scale: Multiple FIFO topics for different domains, cross-region replication via Lambda bridge
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-fifo-topics.html

---

## Scenario Coverage

**Standard Case**: Event-driven microservices fan-out
- Approach: SNS Standard Topic → multiple SQS queues (with filter policies) → Lambda consumers. Raw Message Delivery enabled. DLQ on every subscription. SSE with AWS-managed key. HTTPS enforcement in topic policy.
- Key Decisions: Topic-per-event-type vs multiplexed topic with filters; direct Lambda vs SQS-buffered Lambda; CloudWatch alarm thresholds for failed deliveries.

**Edge Case**: Strict ordering required across multiple consumers + payload > 256 KB
- Approach: SNS FIFO Topic with Message Group IDs + Claim-Check pattern (large payload in S3, reference in SNS message). High-throughput mode with FifoThroughputScope=Topic. Archive enabled for replay. All subscribers are SQS FIFO queues feeding Lambda ESMs.
- Special considerations: SQS FIFO in-flight message limit (20,000); FIFO topic subscription limit (100); cross-region replay not natively supported.

**Anti-Pattern Case**: Team proposes using a single SNS Standard topic for all microservice events across the entire platform (100+ event types, 50+ subscribers, mix of security boundaries)
- Clarification: "How many distinct security boundaries and access control policies are needed? Are there event types that should NEVER be visible to certain subscribers?" — if events have different security requirements, they belong in separate topics. If subscriber count will exceed 200 filter policies, split by domain. A "god topic" creates blast radius and management issues.
