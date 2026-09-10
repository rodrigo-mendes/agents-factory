---
name: architecting-aws-sns-pubsub
description: "Architects AWS SNS pub/sub messaging for event-driven web applications using fan-out, filter policies, DLQs, and FIFO ordering (AWS SNS 2026). Use when designing or reviewing SNS-based messaging topology, selecting between Standard and FIFO topics, configuring subscription security, or integrating SNS with SQS and Lambda in serverless architectures."
---

## Function

Specialist in AWS SNS pub/sub messaging architecture for event-driven web applications — covering fan-out patterns, FIFO ordering, message filtering, encryption, access control, and operational observability.

---

## Version Context

**Service**: Amazon Simple Notification Service (SNS)
**Target edition**: AWS SNS 2026
**Research date**: 2026-08-30
**Currency threshold**: 2027-08-30

**Critical 2026 changes**:
- **BREAKING (April 30, 2026)**: Message Data Protection no longer available to new customers. Replacement: Lambda + Amazon Bedrock Guardrails (see Never-Do #3).
- **FifoThroughputScope High Throughput Mode** (January 21, 2025): up to 30,000 msg/s in us-east-1 via `MessageGroup` scope.
- **IPv6 dual-stack** (April 3, 2025): SNS API endpoints now support IPv4, IPv6, and dual-stack.
- **FCM HTTP v1 credentials** (January 2024): FCM legacy credentials deprecated — use FCM v1 for mobile push.

**Deprecated**: Message Data Protection (new customers); FCM legacy HTTP credentials.

> Agent warning: Do not design new architectures using Message Data Protection — it is unavailable to new AWS customers as of April 30, 2026.

---

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 three-tier operational rules
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases (canonical, edge, misuse)
- **[Integration Patterns](#integration-patterns)** — Fan-out, FIFO pipeline, cross-account, cross-region
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands with expected output
- **[Quick Reference](#quick-reference)** — Quotas, limits, key commands at a glance
- **[External Resources](#external-resources)** — Dated official AWS documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**1. Route all fan-out through SQS queues — never subscribe producers directly to critical consumers**

Every independent downstream consumer must subscribe via an SQS queue. This provides durable retry (up to 23 days for SQS), concurrency control, and backpressure. Lambda workers poll their queue via event source mappings.

SQS queues subscribing to SNS require an explicit resource-based policy:
```json
{
  "Effect": "Allow",
  "Principal": {"Service": "sns.amazonaws.com"},
  "Action": "sqs:SendMessage",
  "Resource": "<sqs-arn>",
  "Condition": {"ArnEquals": {"aws:SourceArn": "<sns-topic-arn>"}}
}
```
Without this policy, SNS silently drops messages with no error surfaced.

---

**2. Attach a DLQ to every SNS subscription via RedrivePolicy**

Client-side errors (deleted Lambda, changed IAM policy, endpoint misconfiguration) are NOT retried — they fail immediately and are permanently lost without a DLQ. FIFO topics require FIFO DLQs; standard topics require standard DLQs.

```bash
# Configure DLQ on subscribe
aws sns subscribe \
  --topic-arn <topic-arn> --protocol sqs \
  --notification-endpoint <queue-arn> \
  --attributes '{"RedrivePolicy":"{\"deadLetterTargetArn\":\"<dlq-arn>\"}"}'
```

Set a CloudWatch alarm: `ApproximateNumberOfMessagesVisible >= 1` on the DLQ (threshold of 1 = immediate alerting). Use this metric — NOT `NumberOfMessagesSent` — to detect DLQ arrivals.

---

**3. Enable SSE (KMS) on every topic carrying PII, financial, or regulated data**

SSE is opt-in and disabled by default. Messages published before SSE is enabled are NOT retroactively encrypted. SSE encrypts the message body only — NOT message IDs, attributes, timestamps, or subject.

```bash
aws sns create-topic --name PaymentEvents \
  --attributes KmsMasterKeyId=alias/aws/sns
# Use CMK ARN for rotation control and cross-account access
```

Enforce HTTPS-only via topic policy Deny on `aws:SecureTransport: "false"`.

---

**4. Apply least-privilege topic access policies — no wildcard Principal without a restrictive condition**

Never use `"Principal": "*"` without a Condition block. Use `aws:SourceArn` or `aws:SourceAccount` for service principals (EventBridge, S3). `aws:SourceOwner` is deprecated — do not use it in new policies. Scope Action to `sns:Publish` or `sns:Subscribe` only; Resource to the exact topic ARN.

Verify: `aws sns get-topic-attributes --topic-arn <arn> --query Attributes.Policy` — check for unguarded `"Principal":"*"`.

---

**5. Enable delivery status logging (FailureFeedbackRoleArn) on all production topics**

Failure logging is NOT on by default. Without `FailureFeedbackRoleArn`, failed deliveries are invisible to operators — CloudWatch metrics show aggregates but not per-message failure details.

Configure per protocol (SQS, Lambda, HTTP/S):
```bash
aws sns set-topic-attributes --topic-arn <arn> \
  --attribute-name SQSFailureFeedbackRoleArn \
  --attribute-value <iam-role-arn>
```

IAM role requires `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`. Set `SuccessFeedbackSampleRate` to 5 for sampled success tracing. Use SSM Automation runbook `AWS-EnableSNSTopicDeliveryStatusLogging` for at-scale enablement.

---

### ⚠️ Ask First

**1. Standard Topic vs FIFO Topic**

Ask: "Is message ordering a non-negotiable business requirement — not a preference?" Then confirm all subscribers can be SQS queues (FIFO topics cannot fan out to Lambda, HTTP, email, SMS, or Firehose directly).

| Criterion | Standard Topic | FIFO Topic |
|-----------|---------------|-----------|
| Throughput | Unlimited TPS | 3,000 msg/s (topic) / 30,000 msg/s (High Throughput Mode, us-east-1) |
| Ordering | Best-effort | Strict per MessageGroupId |
| Deduplication | None | 5-minute window |
| Subscriber types | SQS, Lambda, HTTP, Email, SMS, Firehose, Mobile Push | SQS queues only |
| Cost | Lower | Higher (per-message, 1 KB minimum) |

Default to Standard unless ordering or deduplication is a stated business requirement.

---

**2. SNS vs EventBridge vs Kinesis vs SQS-Direct**

Ask: "Does any subscriber need SMS, Email, or Mobile Push delivery?" If yes → SNS required. Ask: "Is content-based routing, SaaS event source integration, or schema evolution a priority?" If yes → evaluate EventBridge. Ask: "Is high-throughput ordered streaming or replay for analytics the primary need?" If yes → Kinesis.

| Service | Best When | Avoid When |
|---------|-----------|------------|
| SNS | Heterogeneous subscribers (SMS, email, mobile push, SQS, Lambda) | Deep content-based routing; SaaS sources |
| EventBridge | Content-based routing; SaaS integrations; schema registry | SMS/email/mobile push native delivery |
| Kinesis | Real-time analytics; ordered streaming; multiple independent consumers | Simple fan-out to N queues |
| SQS Direct | Single consumer per message | Fan-out to multiple independent consumers |

---

**3. Direct SNS-to-Lambda vs SNS-to-SQS-to-Lambda**

Ask: "What is the peak publish rate? Can it exceed Lambda reserved concurrency?" If yes → mandate SQS as a buffer.

| Option | Best When | Risk |
|--------|-----------|------|
| Direct SNS → Lambda | Low, predictable traffic; latency-critical | Concurrency exhaustion causes throttle errors and message loss under spikes |
| SNS → SQS → Lambda | Spiky or unpredictable load; long processing time; need batching | Added polling latency; SQS API cost |

---

### 🚫 Never Do

**1. Subscribe without a DLQ**
```bash
# 🚫 WRONG — messages silently lost on client-side errors
aws sns subscribe --protocol sqs --notification-endpoint <queue-arn> --topic-arn <arn>

# ✅ CORRECT — always include RedrivePolicy
aws sns subscribe --protocol sqs --notification-endpoint <queue-arn> --topic-arn <arn> \
  --attributes '{"RedrivePolicy":"{\"deadLetterTargetArn\":\"<dlq-arn>\"}"}'
```
Impact: Permanent, silent message loss on endpoint misconfiguration, deleted Lambda, or IAM policy changes. No recovery path.

---

**2. Use `"Principal": "*"` without a condition in the topic policy**
```json
// 🚫 WRONG — any AWS principal in any account can publish
{"Effect":"Allow","Principal":"*","Action":"sns:Publish","Resource":"<arn>"}

// ✅ CORRECT — scope with aws:SourceArn and aws:SourceAccount
{"Effect":"Allow","Principal":{"Service":"events.amazonaws.com"},
 "Action":"sns:Publish","Resource":"<arn>",
 "Condition":{"ArnLike":{"aws:SourceArn":"<rule-arn>"},"StringEquals":{"aws:SourceAccount":"<account-id>"}}}
```
Impact: Unauthorized publish from any AWS account; attacker-controlled payloads processed by downstream Lambda; data exfiltration; cost abuse.

---

**3. Design new architectures using Message Data Protection**
Message Data Protection is unavailable to new customers as of April 30, 2026. Existing customers may continue, but no new enhancements will be made.

✅ Correct alternative: Lambda subscribed to inbound SNS topic → Amazon Bedrock Guardrails (LOG/BLOCK/REDACT) → republish to destination topic. See: https://github.com/aws-samples/sample-sns-sensitive-data-protection-bedrock

---

**4. Deploy topics with no filter policies when event types are heterogeneous**
Without filter policies, every subscriber receives every message. This inflates Lambda invocations, SQS API costs, and compute proportionally to subscriber count × message volume.

```bash
# ✅ CORRECT — scope each subscription to its needed event types
aws sns subscribe --topic-arn <arn> --protocol sqs \
  --notification-endpoint <queue-arn> \
  --attributes '{"FilterPolicy":"{\"eventType\":[\"order-created\"]}"}'
# Publisher must include: {"eventType": {"DataType":"String","StringValue":"order-created"}}
```
Note: Filter policy changes take up to 15 minutes to propagate. Filtered-out messages are silently discarded — they do NOT go to the DLQ.

---

**5. Subscribe Lambda directly to high-volume or spiky SNS topics without an SQS buffer**
```bash
# 🚫 WRONG — Lambda concurrency exhaustion under spikes → message loss
aws sns subscribe --protocol lambda --notification-endpoint <lambda-arn> --topic-arn <arn>

# ✅ CORRECT — buffer with SQS + controlled concurrency
# SNS → SQS Standard Queue (DLQ attached) → Lambda event source mapping (MaximumConcurrency=50)
```
Impact: Under traffic spikes, Lambda throttling causes SNS to exhaust retries; messages are permanently lost without DLQ. Even with DLQ, recovery requires manual redrive.

Flag when: `Protocol = "lambda"` appears in `aws sns list-subscriptions-by-topic` for topics expected to receive > 100 msg/s or with unpredictable spike patterns.

---

## Integration Patterns

**SNS ↔ SQS** — Canonical fan-out pattern. One publish distributes to N SQS queues concurrently. Requires explicit SQS resource policy granting `sqs:SendMessage` to SNS topic ARN with `aws:SourceArn` condition. Since September 2023, FIFO SNS topics can fan out to both FIFO and standard SQS queues.

**SNS ↔ Lambda** — Async fire-and-forget for low, predictable traffic. SNS retries 100,015 times over 23 days for Lambda endpoints. Add SQS buffer for spiky workloads.

**SNS ↔ EventBridge** — Use EventBridge as a source, publishing to SNS for SMS/email/mobile push delivery when EventBridge does not natively support those subscriber types.

**SNS ↔ Kinesis Data Firehose** — Direct native integration (no Lambda hop required) for archiving to S3 or OpenSearch as part of Event Fork Pipelines.

**SNS ↔ S3 (Event Notifications)** — S3 can publish object-created events directly to an SNS topic. Requires SNS topic policy granting `sns:Publish` to `s3.amazonaws.com` with `aws:SourceArn` condition scoped to the bucket ARN.

**Common problems**:
- **SQS receives no messages from SNS** → SQS resource policy missing `sqs:SendMessage` for SNS principal; check `aws:SourceArn` condition.
- **Messages silently dropped on Lambda subscriber** → Lambda concurrency exhausted and DLQ not configured on subscription; check `RedrivePolicy` attribute.
- **Filter policy not taking effect** → policy changes take up to 15 minutes to propagate; re-check `FilterPolicyScope` matches where event type is located (attributes vs body).

---

## Verification Loop

Execute these checks after configuring any SNS topic or subscription:

```bash
# 1. Verify subscription has DLQ (RedrivePolicy key present)
aws sns get-subscription-attributes --subscription-arn <sub-arn> \
  --query Attributes.RedrivePolicy
# Expected: non-null value containing deadLetterTargetArn

# 2. Verify SSE is enabled on the topic
aws sns get-topic-attributes --topic-arn <topic-arn> \
  --query Attributes.KmsMasterKeyId
# Expected: non-empty string (key alias or ARN)

# 3. Verify topic policy has no unguarded wildcard Principal
aws sns get-topic-attributes --topic-arn <topic-arn> \
  --query Attributes.Policy | grep -c '"Principal":"\*"'
# Expected: 0 (or if 1, verify a Condition block with aws:SourceArn or aws:SourceAccount follows)

# 4. Verify delivery logging role is set
aws sns get-topic-attributes --topic-arn <topic-arn> \
  --query 'Attributes.SQSFailureFeedbackRoleArn'
# Expected: valid IAM role ARN

# 5. Verify subscription filter policy is set (on mixed-event-type topics)
aws sns get-subscription-attributes --subscription-arn <sub-arn> \
  --query Attributes.FilterPolicy
# Expected: non-null JSON filter object

# 6. Check for direct Lambda subscriptions on high-volume topics
aws sns list-subscriptions-by-topic --topic-arn <topic-arn> \
  --query 'Subscriptions[?Protocol==`lambda`]'
# Review: confirm acceptable traffic volume before allowing direct Lambda subscription
```

**Troubleshooting**:
- `AuthorizationError` on SNS publish from S3/EventBridge → topic policy missing `aws:SourceArn` condition.
- Messages disappearing with no DLQ entries → check if messages are being filtered out (filtered messages go to /dev/null, not DLQ).
- FIFO topic subscription fails → confirm subscriber is an SQS queue; FIFO topics do not support Lambda/HTTP/email/SMS direct subscription.

---

## Quick Reference

**Critical limits**:

| Resource | Default Limit | Notes |
|----------|--------------|-------|
| Standard topics per account | 100,000 | Soft limit |
| FIFO topics per account | 1,000 | Soft limit |
| Subscriptions per standard topic | 12,500,000 | — |
| Subscriptions per FIFO topic | 100 | — |
| Max message size | 256 KiB | Up to 2 GB via SNS Extended Client Libraries + S3 |
| Standard topic TPS (us-east-1) | 30,000 msg/s | Soft limit |
| FIFO topic TPS (us-east-1, HTM) | 30,000 msg/s | FifoThroughputScope=MessageGroup required |
| Per-MessageGroup TPS (FIFO) | 300 msg/s | Hard limit even in High Throughput Mode |
| SQS/Lambda retry window | 23 days / 100,015 retries | Server-side errors only |
| HTTP/S retry window | 3,600 seconds max | Fully customizable |
| Filter policy attributes | 10 max | Per subscription |
| Message attributes (raw delivery) | 10 max | Exceeding causes silent discard |

**Key topic attributes**:
- `KmsMasterKeyId` — SSE encryption key
- `FifoThroughputScope` — `Topic` (default) or `MessageGroup` (High Throughput Mode)
- `ContentBasedDeduplication` — FIFO only; hash body for deduplication ID
- `ArchivePolicy` — FIFO only; enables message archiving (1–365 days)

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-aws-sns-pubsub/
├── SKILL.md                              ← This file (summary + guardrails)
└── blueprints/
    └── evaluation-scenarios.md           ← 6 test scenarios for skill-evaluator
```

---

## External Resources

### Official Documentation (accessed 2026-08-30)
- [SNS Developer Guide](https://docs.aws.amazon.com/sns/latest/dg/welcome.html) — Primary reference
- [SNS Dead-Letter Queues](https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html)
- [SNS Message Filtering](https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html)
- [SNS FIFO Topics](https://docs.aws.amazon.com/sns/latest/dg/sns-fifo-topics.html)
- [SNS Server-Side Encryption](https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html)
- [SNS Security Best Practices](https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html)
- [SNS Message Archiving and Replay](https://docs.aws.amazon.com/sns/latest/dg/fifo-message-archiving-replay.html)
- [SNS Delivery Status Logging](https://docs.aws.amazon.com/sns/latest/dg/sns-topic-attributes.html)
- [Message Data Protection Availability Change](https://docs.aws.amazon.com/sns/latest/dg/sns-message-data-protection-availability-change.html) — Breaking change April 30, 2026
- [SNS vs SQS vs EventBridge Decision Guide](https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html)
- [SNS Pricing](https://aws.amazon.com/sns/pricing/)
- [SNS Service Quotas](https://docs.aws.amazon.com/general/latest/gr/sns.html)

### Feature Announcements
- [FIFO High Throughput Mode](https://aws.amazon.com/about-aws/whats-new/2025/01/high-throughput-mode-amazon-sns-fifo-topics) — 2025-01-21
- [Message Archiving/Replay in GovCloud](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-sns-message-archiving-replay-fifo-topics-govcloud) — 2024-11-07
