# AWS EventBridge Event-Driven Architecture — Cloud Architecture Research

## Metadata
```yaml
Full_Name: "AWS Serverless Patterns — Amazon EventBridge Event-Driven Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Serverless Patterns - EventBridge Event-Driven Architecture"
Target_Edition: "AWS EventBridge 2026"
Architecture_Context: "Generic — broad event-driven microservices default (choreography, fan-out, point-to-point integration, scheduled workloads)"
Official_Source_URL: "https://docs.aws.amazon.com/eventbridge/latest/userguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-28"
Currency_Threshold: "2027-08-28"
Research_Depth: "exhaustive"
Max_Iterations: 5
Confidence_Level: "High (predominantly official AWS documentation, triangulated with What's New announcements dated 2022-2025)"
Source_Count: 46
Research_Quality_Score: "92%"
# Research_Quality_Score = (total_claims - unverified - irresolvable) / total_claims * 100
Gap_Loop_Ran: true
Iterations_Used: "5 of 5"
Triangulated_Count: 71
Unverified_Count: 3
Irresolvable_Count: 1
```

---

## Executive Summary

Amazon EventBridge is AWS's serverless event bus and the backbone of event-driven architecture (EDA) on AWS. It receives events from AWS services, custom applications, and SaaS partners, then routes them — based on JSON content-matching rules — to as many as five targets each, spanning 30+ AWS service integrations (AWS Lambda, Amazon SQS, Amazon SNS, AWS Step Functions, Amazon Kinesis Data Streams, Amazon Data Firehose, Amazon ECS, API Destinations, and more). Beyond the classic bus-and-rules model, EventBridge now spans four distinct primitives that cover the full EDA design space: **event buses** (many-to-many routing), **EventBridge Pipes** (point-to-point source→filter→enrich→target integration), **EventBridge Scheduler** (time-based one-time and recurring invocation of 270+ services), and the **Schema Registry** (discovery, versioning, and typed code bindings). Within cloud architecture practice, EventBridge occupies the choreography, fan-out, content-based routing, and workflow-triggering tiers of virtually every AWS serverless reference architecture.

The 2024–2026 period was defined by three vectors of change: **security**, **observability**, and **filtering power**. AWS KMS customer managed key (CMK) encryption reached the event bus (GA 2024-05-14), then archives and replay (2025-04), then rule filter patterns and input transformers (2025-09-17), closing the at-rest encryption story for sensitive payloads. Enhanced logging to Amazon CloudWatch Logs, Amazon S3, and Amazon Data Firehose (GA 2025-07) added first-class observability that previously required custom targets. Filtering gained wildcard matching (2023-10), then combined `anything-but` with prefix/suffix/wildcard (2024-05), and the `$or` cross-field operator. An enhanced visual rule builder with an integrated event catalog across 200+ services (2025-11) and Amazon SQS fair-queue targets (2025-11) rounded out the modern surface. **Critically, the maximum PutEvents request size is now 1 MB (1,048,576 bytes) — the widely cited 256 KB figure is superseded and must be treated as misinformation** per Version Absolutism.

The three most critical architecture guardrails for EventBridge EDA are: **(1) always attach a standard Amazon SQS dead-letter queue (DLQ) plus an explicit retry policy to every production target** — retries exhaust silently and permanent errors (missing permissions, deleted target, DNS failure) skip retry entirely, dropping events with no default safety net; **(2) design for at-least-once, unordered, possibly-duplicate delivery** — EventBridge does not guarantee ordering or exactly-once, so every consumer must be idempotent, and archive replay explicitly processes events out of order in one-minute buckets; **(3) never rely on multi-hop forwarding** — EventBridge silently refuses to route an event to a "third hop" (a receiver account/bus forwarding to yet another account/bus), a failure mode invisible except via the DLQ error codes `THIRD_ACCOUNT_HOP_DETECTED` / `THIRD_REGION_HOP_DETECTED`.

---

## Cloud Architecture Glossary

```
Term: Event Bus
Definition: A router that receives events and delivers them to zero or more destinations (targets). A rule is associated with a specific event bus and only evaluates events received by that bus.
Provider Docs Section: eb-event-bus.html
Architect Usage: Use the default bus for AWS-service events (free ingestion); create custom buses to isolate domains/bounded contexts and apply per-bus resource policies and CMK encryption. Limit 100 buses per Region per account.
Common Confusion: Confused with Amazon SNS topics — a bus does content-based routing to many rule/target combinations, whereas an SNS topic fans out one message to subscribers with only attribute-based filtering.
```

```
Term: Default Event Bus
Definition: The auto-provisioned bus in every account/Region that automatically receives events emitted by AWS services and accepts PutEvents calls.
Provider Docs Section: eb-event-bus.html; eb-events.html
Architect Usage: Route AWS-service events (e.g., EC2 state changes, S3 object created) from here. Ingestion of AWS-service events on the default bus is free; you pay only on cross-account delivery.
Common Confusion: Assuming custom application events should also land on the default bus — best practice is a dedicated custom bus per domain for isolation and policy scoping.
```

```
Term: Event Pattern
Definition: A JSON structure attached to a rule that defines which fields and values an incoming event must match. Patterns mirror the structure of the events they match and support comparison operators.
Provider Docs Section: eb-event-patterns.html; eb-create-pattern-operators.html
Architect Usage: Push content-based routing server-side (prefix, suffix, numeric, cidr, wildcard, anything-but, $or, exists) instead of filtering in consumer code. Max event pattern size 2,048 characters.
Common Confusion: Confused with input transformation — a pattern decides IF a target fires; an input transformer decides WHAT payload the target receives.
```

```
Term: Rule
Definition: A configuration on an event bus that matches incoming events either by event pattern or by schedule, and routes matches to up to five targets.
Provider Docs Section: eb-rules.html
Architect Usage: Keep rules narrow (one responsibility). Default 300 rules per bus (100 in af-south-1 / eu-south-1). Managed rules created by AWS services can only be removed with "Force delete".
Common Confusion: Scheduled rules are now a legacy feature — AWS recommends EventBridge Scheduler for time-based invocation instead.
```

```
Term: Target
Definition: A resource or endpoint EventBridge sends an event to when a rule matches. Max five targets per rule.
Provider Docs Section: eb-targets.html
Architect Usage: 30+ supported types incl. AWS Lambda (async), Amazon SQS (standard/FIFO/fair), Amazon SNS, AWS Step Functions (async), Amazon Kinesis Data Streams, Amazon Data Firehose, API Gateway, API Destinations, another event bus, Amazon ECS task.
Common Confusion: Lambda and Step Functions targets are invoked ASYNCHRONOUSLY — do not expect synchronous responses back into the flow.
```

```
Term: Input Transformer
Definition: A mechanism that customizes the text delivered to a target using InputPath-extracted variables substituted into an Input Template (variables referenced as <variable-name>).
Provider Docs Section: eb-transform-target-input.html
Architect Usage: Reshape events for API Destinations/API Gateway/HTTP targets that expect a specific body. Up to 100 variables. Reserved vars: aws.events.rule-arn, aws.events.rule-name, aws.events.event.ingestion-time, aws.events.event, aws.events.event.json.
Common Confusion: CloudWatch Logs and Systems Manager targets do NOT support Input/InputPath within input transformers.
```

```
Term: EventBridge Pipes
Definition: A managed point-to-point integration primitive connecting one source to one target through an optional filter and optional synchronous enrichment step (source → filter → enrichment → target).
Provider Docs Section: eb-pipes.html
Architect Usage: Replace hand-written poller/glue code between a single producer and consumer. Sources: Amazon SQS, Amazon Kinesis Data Streams, Amazon DynamoDB Streams, Amazon MSK, self-managed Apache Kafka, Amazon MQ. Preserves source ordering end-to-end.
Common Confusion: Confused with event buses — Pipes is 1:1 point-to-point; buses are many-to-many. Pipes wildcard filtering is NOT supported (bus rules only).
```

```
Term: Enrichment (Pipes)
Definition: The optional synchronous (REQUEST_RESPONSE) transform step in a Pipe that augments an event before delivery to the target, using an API destination, Amazon API Gateway, AWS Lambda, or AWS Step Functions Express workflow.
Provider Docs Section: pipes-enrichment.html
Architect Usage: Enrich stream/queue records with reference data before the target. Response max 6 MB. Returning an empty response ("", {}, []) suppresses the target — enrichment can act as a filter.
Common Confusion: Only Step Functions EXPRESS workflows are supported (not Standard), because enrichment is synchronous.
```

```
Term: EventBridge Scheduler
Definition: A serverless scheduler that creates, runs, and manages one-time and recurring tasks invoking 270+ AWS services and 6,000+ API operations, with at-least-once delivery.
Provider Docs Section: what-is-scheduler.html
Architect Usage: Use rate(), cron() (6 fields), or at() expressions with per-schedule IANA time zones, flexible time windows, retry policy, and DLQ. Scales to 10,000,000 schedules per Region. Replaces legacy scheduled rules.
Common Confusion: Confused with cron on a server or with scheduled rules — Scheduler adds universal targeting, time zones, flexible windows, and per-schedule retry/DLQ that scheduled rules lack.
```

```
Term: Universal Target Parameter (UTP)
Definition: The EventBridge Scheduler mechanism to invoke any of 6,000+ API operations across 270+ services via an ARN of the form arn:aws:scheduler:::aws-sdk:{service}:{apiAction}.
Provider Docs Section: what-is-scheduler.html
Architect Usage: Schedule actions on services with no templated target (e.g., start an EC2 instance, run a Glue job) without writing Lambda glue.
Common Confusion: Templated targets (SQS, SNS, Lambda, EventBridge) are a convenience subset; UTP covers everything else.
```

```
Term: Schema Registry
Definition: A store that collects and organizes event schemas (OpenAPI 3 and JSONSchema Draft4) into registries: All schemas, AWS event schema registry, Discovered schema registry, and custom registries.
Provider Docs Section: eb-schema-registry.html; eb-schema.html
Architect Usage: Generate typed code bindings (Golang, Java, Python, TypeScript) via console, API, or IDE toolkit to speed consumer development and reduce parsing errors. Registry usage for AWS/custom schemas is free.
Common Confusion: Exporting custom schemas out of the registry is NOT supported; and schema versions change automatically when event shapes change — pin consumers to a version.
```

```
Term: Schema Discovery
Definition: A feature that infers schemas automatically from events flowing on an event bus; each unique schema (including cross-account by default) is added to the Discovered schema registry, with new versions created as event shapes change.
Provider Docs Section: eb-schemas-infer.html
Architect Usage: Turn on temporarily to bootstrap a schema catalog for an existing bus. First 5,000,000 ingested events/month free; $1.00 per million events thereafter (each 8 KB chunk of payload = one billed event). Schema Registry storage and API calls for custom schemas are free.
Common Confusion: Not supported on CMK-encrypted buses (requires an AWS owned key); events larger than 1000 KiB are silently not discovered (no error notification).
```

```
Term: Dead-Letter Queue (DLQ)
Definition: A standard Amazon SQS queue where EventBridge stores events that could not be delivered to a target (or, on CMK buses, that failed encryption/decryption).
Provider Docs Section: eb-rule-dlq.html
Architect Usage: Attach per target for guaranteed capture. FIFO queues are NOT supported; the DLQ must be in the same Region as the rule. Messages carry attributes RULE_ARN, TARGET_ARN, ERROR_CODE, ERROR_MESSAGE, EXHAUSTED_RETRY_CONDITION, RETRY_ATTEMPTS.
Common Confusion: DeadLetterInvocations (a metric) is NOT the same as delivery to a DLQ — it counts suppressed/infinite-loop invocations, whereas InvocationsSentToDlq counts DLQ deliveries.
```

```
Term: Retry Policy
Definition: Per-target configuration governing retriable delivery-failure handling via MaximumRetryAttempts (0–185) and MaximumEventAgeInSeconds (60–86400). Default: retry for 24 hours and up to 185 times with exponential backoff and jitter.
Provider Docs Section: eb-rule-retry-policy.html; API_RetryPolicy.html
Architect Usage: Set both values deliberately per target SLA rather than accepting the 24h/185 default. Retries stop when either limit is reached; then the event is dropped or sent to the DLQ.
Common Confusion: Permanent errors (missing permissions, deleted target, DNS failure) are NOT retried at all — they go straight to the DLQ regardless of retry policy.
```

```
Term: Archive and Replay
Definition: A durable, event-pattern-filtered store of events from a single source bus (Archive) and the ability to resend a time range of those events back to the source bus (Replay).
Provider Docs Section: eb-archive.html
Architect Usage: Use for recovery, reprocessing, and test data. Retention default is indefinite. A managed rule auto-prevents replayed events (carrying a replay-name field) from re-entering the archive.
Common Confusion: Replay is NOT ordered (processes in one-minute buckets), can only target the SOURCE bus, max 10 concurrent replays per account/Region, and replayed events lose their X-Ray trace header.
```

```
Term: Resource-Based Policy (Event Bus)
Definition: A policy attached to an event bus granting or denying principals (accounts, organizations, the events.amazonaws.com service principal) permission to act on the bus — chiefly events:PutEvents.
Provider Docs Section: eb-use-resource-based.html; eb-cross-account.html
Architect Usage: Grant cross-account/cross-org PutEvents with aws:SourceArn / account-ID conditions (confused-deputy protection). Bus policy size limit 10,240 characters.
Common Confusion: EventBridge Pipes does NOT support resource-based policies — restrict Pipes API access via VPC endpoint policies instead.
```

```
Term: API Destination
Definition: An EventBridge target type that invokes an external HTTP endpoint (public or private via PrivateLink/VPC Lattice) using a reusable Connection that stores authorization in AWS Secrets Manager.
Provider Docs Section: eb-targets.html; eb-api-destinations.html
Architect Usage: Integrate SaaS/third-party HTTP APIs without a Lambda proxy; rate-limit per destination (default 300/s). $0.20 per million events. 3,000 API destinations and 3,000 connections per account/Region.
Common Confusion: Confused with API Gateway target — API Destination calls OUT to an external HTTP API; API Gateway target invokes your OWN API in AWS.
```

```
Term: Bus-to-Bus Routing
Definition: A rule whose target is another event bus (same or different account/Region), enabling hierarchical or hub-and-spoke event distribution.
Provider Docs Section: eb-bus-to-bus.html; eb-cross-account.html
Architect Usage: Sender bus uses an IAM role for send permission; receiver bus uses a resource-based policy to accept. Bus-to-bus events are billed as custom events.
Common Confusion: No "third hop" — a receiver bus cannot forward events received from a sender bus on to a third bus; those events are silently not delivered.
```

```
Term: Managed Rule
Definition: An EventBridge rule created and owned by another AWS service in your account to support that service's functionality.
Provider Docs Section: eb-rules.html
Architect Usage: Recognize these in audits; they can only be deleted with the "Force delete" option, and deleting one may break the owning service.
Common Confusion: Confused with AWS managed IAM policies — a managed RULE is a service-created EventBridge rule, unrelated to IAM.
```

```
Term: Idempotency (Consumer)
Definition: The property that processing the same event more than once produces the same result as processing it once — required because EventBridge delivery is at-least-once and can duplicate.
Provider Docs Section: Serverless Applications Lens; saga-choreography.html
Architect Usage: Use an idempotency key (event id or a business key) with a dedupe store (e.g., Amazon DynamoDB conditional writes) in every consumer.
Common Confusion: Assuming EventBridge deduplicates or orders events — it does neither; idempotency is the consumer's responsibility.
```

---

## Architecture Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo or current stable docs) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**Pattern: DLQ + Explicit Retry Policy on Every Production Target** 🟢
- Pillar Alignment: Reliability
- Why: EventBridge retries retriable failures for 24 hours / up to 185 times with exponential backoff and jitter, but "if an event isn't delivered after all retry attempts are exhausted, the event is dropped and EventBridge doesn't continue to process it." Separately, permanent errors (missing permissions, deleted target, invalid address/DNS failure) receive NO retries and go straight to a DLQ if one exists — otherwise they are lost. A DLQ is the only guaranteed capture path. [✓✓ Triangulated | eb-rule-retry-policy.html + eb-rule-dlq.html]
- AWS Services: Amazon EventBridge (rule target), Amazon SQS (standard queue as DLQ)
- Architecture Decision:
  Attach a standard Amazon SQS DLQ (same Region; FIFO not supported) to every target. Set MaximumRetryAttempts (0–185) and MaximumEventAgeInSeconds (60–86400) explicitly per target SLA rather than accepting the 24h/185 default. When configuring via the PutTargets API or for a cross-account DLQ, manually attach the SQS resource-based policy granting events.amazonaws.com sqs:SendMessage with an aws:SourceArn condition scoped to the rule ARN (the console does this automatically).
- Verification:
  `aws events list-targets-by-rule --rule <name> --event-bus-name <bus>` and confirm each target has DeadLetterConfig.Arn and RetryPolicy. Alarm on CloudWatch metric InvocationsFailedToBeSentToDlq (any datapoint = event lost even with a DLQ).
- Trade-offs: Adds an SQS queue per target to operate and drain (redrive via a Lambda consumer); minor cost; requires alarm wiring.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html (accessed 2026-08-28)

**Pattern: Idempotent Consumers for At-Least-Once, Unordered Delivery** 🟢
- Pillar Alignment: Reliability
- Why: EventBridge and EventBridge Scheduler both provide at-least-once delivery and do not guarantee ordering across the fleet; archive replay explicitly processes events out of order in one-minute buckets. Duplicate and reordered delivery is therefore expected, not exceptional. The Serverless Applications Lens and the saga-choreography guidance require participants to be idempotent. [✓✓ Triangulated | what-is-scheduler.html + eb-archive.html]
- AWS Services: AWS Lambda / AWS Step Functions / Amazon ECS (consumers), Amazon DynamoDB (idempotency/dedupe store)
- Architecture Decision:
  Derive an idempotency key from the event id (or a stable business key) and record processed keys in Amazon DynamoDB using a conditional write (attribute_not_exists) with a TTL. Reject/skip already-seen keys. For ordering-sensitive flows, use EventBridge Pipes with an ordered source (Amazon Kinesis/DynamoDB Streams) which preserves source order end-to-end, or carry a sequence/version attribute and discard stale updates.
- Verification:
  Load-test with deliberate duplicate PutEvents and confirm single-effect processing; inspect the DynamoDB dedupe table for one row per business key.
- Trade-offs: Extra DynamoDB read/write per event (latency + cost); idempotency-key design effort; TTL tuning to bound table growth.
- Source: https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html (accessed 2026-08-28)

**Pattern: Scope Cross-Account Ingestion with the `account` Field and Least-Privilege Resource Policies** 🟢
- Pillar Alignment: Security
- Why: When a bus accepts events from an AWS Organization or all accounts, AWS explicitly directs architects to "add account to every EventBridge rule" to prevent triggering on unknown accounts (a `*` in the account field matches nothing, so it is not a wildcard). Since 2023-03-02, all new cross-account event-bus targets must use IAM roles. Broad resource policies otherwise create an unbounded ingestion surface. [✓✓ Triangulated | eb-cross-account.html + eb-use-resource-based.html]
- AWS Services: Amazon EventBridge (event bus resource-based policy, rule), AWS IAM (execution role)
- Architecture Decision:
  On the receiver bus, grant events:PutEvents to specific account IDs or an organization ID via the resource-based policy, guarded with aws:SourceArn. On every rule that consumes cross-account events, pin the source account IDs in the account field (never `*`). Senders attach an IAM role trusted by events.amazonaws.com to forward to the receiver bus ARN.
- Verification:
  `aws events describe-event-bus --name <bus>` and inspect the Policy for scoped principals + conditions; audit rules for an explicit account field.
- Trade-offs: More policy maintenance as accounts are added; senders must manage IAM roles.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html (accessed 2026-08-28)

**Pattern: Server-Side Content Filtering Instead of Consumer-Side Filtering** 🟢
- Pillar Alignment: Cost Optimization / Performance Efficiency
- Why: EventBridge evaluates rich content-based patterns (prefix, suffix, numeric, cidr, wildcard, anything-but, $or, exists) server-side at no extra cost, so unmatched events never invoke — and never bill — a downstream target. In EventBridge Pipes, "you are only charged for events that match the filter," and filtering happens before enrichment. Filtering downstream (in a Lambda that then discards) pays invocation cost for every event. [✓✓ Triangulated | eb-create-pattern-operators.html + eb-pipes-event-filtering.html]
- AWS Services: Amazon EventBridge (rule event pattern), Amazon EventBridge Pipes (FilterCriteria)
- Architecture Decision:
  Push all routing/discard logic into the rule event pattern or Pipe FilterCriteria. Keep patterns within the 2,048-character limit; note wildcard matching is bus-rule-only (max 30 wildcard rules per bus) and $or combinations must stay under 1,000 (InvalidEventPatternException above).
- Verification:
  `aws events test-event-pattern --event-pattern file://pattern.json --event file://sample.json`; monitor MatchedEvents vs Invocations to confirm filtering ratio.
- Trade-offs: Complex patterns can hit the 30-wildcard-rules-per-bus hard cap or the $or 1,000-combination ceiling; pattern logic is less flexible than code.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-pattern-operators.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-event-filtering.html (accessed 2026-08-28)

**Pattern: Prefer EventBridge Scheduler Over Legacy Scheduled Rules for Time-Based Invocation** 🟢
- Pillar Alignment: Operational Excellence
- Why: AWS documentation now labels scheduled event-bus rules a "legacy feature" and recommends EventBridge Scheduler, which adds one-time schedules, per-schedule IANA time zones with automatic DST handling, flexible time windows, built-in retry policy and DLQ, universal targeting of 270+ services, and scale to 10,000,000 schedules per Region. [✓✓ Triangulated | eb-rules.html + what-is-scheduler.html]
- AWS Services: Amazon EventBridge Scheduler (schedule, schedule group), AWS IAM (execution role), Amazon SQS (DLQ)
- Architecture Decision:
  Create schedules with rate()/cron()/at() expressions, set ActionAfterCompletion=DELETE on one-time schedules (completed one-time schedules keep consuming the per-Region quota until deleted), configure a retry policy and a standard-SQS DLQ, and organize schedules into schedule groups (default 500 per Region).
- Verification:
  `aws scheduler get-schedule --name <name> --group-name <group>` and confirm RetryPolicy, DeadLetterConfig, and ActionAfterCompletion; check the 60-second precision (or flexible window) meets the SLA.
- Trade-offs: Target Input payload capped at 256 KB; invocation throttle 1,000 TPS in primary Regions (adjustable); a second service to govern alongside buses.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules.html (accessed 2026-08-28); https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html (accessed 2026-08-28)

**Pattern: Encrypt Sensitive Event Data with a Customer Managed KMS Key (CMK) + DLQ** 🟢
- Pillar Alignment: Security
- Why: EventBridge supports CMK at-rest encryption for event buses (GA 2024-05-14), archives and replay (2025-04), and rule filter patterns and input transformers (2025-09-17), covering event detail, patterns, and target configuration. AWS "strongly recommends" a DLQ on encrypted buses because events that fail encryption/decryption are routed to the DLQ rather than silently lost. [✓✓ Triangulated | eb-encryption-event-bus-cmkey.html + What's New 2024-05]
- AWS Services: Amazon EventBridge (event bus, archive), AWS KMS (customer managed key), Amazon SQS (DLQ)
- Architecture Decision:
  Specify a CMK at bus create/update. Grant the events.amazonaws.com principal kms:DescribeKey, kms:GenerateDataKey, kms:Decrypt in the key policy, constrained by the encryption context "kms:EncryptionContext:aws:events:event-bus:arn":"{bus-arn}" and aws:SourceArn. Attach a DLQ. Note: Schema Discovery is not supported on CMK-encrypted buses (requires an AWS owned key).
- Verification:
  `aws events describe-event-bus --name <bus>` shows KmsKeyIdentifier; monitor EventBusEncryptionFailed (emitted only when non-zero) and CloudTrail KMS events for the encryption context.
- Trade-offs: KMS request cost and key governance overhead; loss of Schema Discovery on the bus; additional key-policy complexity.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-encryption-event-bus-cmkey.html (accessed 2026-08-28); https://aws.amazon.com/about-aws/whats-new/2024/05/amazon-eventbridge-cmk-event-buses/ (accessed 2026-08-28)
  > ⚠️ Source dated 2024-05; verify currency.

### ⚠️ Architectural Decisions

**Decision: EventBridge Bus vs Pipes vs Scheduler vs SNS/SQS/Kinesis for the integration**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Many-to-many routing | Amazon EventBridge event bus + rules | Content-based routing, schema registry, 30+ targets | Ordering; per-event cost on custom bus | Multiple producers fan out to multiple consumers with content-based routing |
  | Point-to-point integration | Amazon EventBridge Pipes | Built-in polling, filter+enrich, order preservation, low $/event | Only 1 source→1 target; no wildcard filter | Wiring one stream/queue (SQS/Kinesis/DynamoDB/MSK/Kafka/MQ) to one target, replacing glue code |
  | Time-based invocation | Amazon EventBridge Scheduler | One-time/recurring, time zones, 270+ targets, huge scale | Not event-triggered; 256 KB input cap | Cron/rate/at scheduling of tasks |
  | Extreme fan-out | Amazon SNS | Millions of endpoints, lowest latency | Only attribute-based filtering | Very high fan-out to many subscribers/endpoints |
  | Ordered high-throughput stream | Amazon Kinesis Data Streams | Ordering per shard, replay window, high throughput | No content routing; shard management | Ordered event streaming / analytics ingestion |

- Cost Profile: Custom bus $1.00/M ingested; Pipes $0.40/M requests (cheapest per event); Scheduler free up to 14,000,000 invocations/month then $1.00/M; AWS-service events free on default bus. SNS/SQS/Kinesis priced separately and often lower per-message for pure transport.
- Scaling Characteristics: Bus PutEvents 10,000 TPS (primary Regions, adjustable); Pipes 3,000 concurrent executions (primary Regions); Scheduler 10,000,000 schedules/Region; SNS/Kinesis scale via their own limits.
- Operational Burden: Bus + rules = low glue but rule sprawl risk; Pipes = lowest glue for 1:1; Scheduler = separate schedule inventory; Kinesis = shard/consumer management.
- Lock-in Assessment: All are AWS-proprietary control planes; event JSON is portable, but rule/pattern/pipe definitions are not. Pipes/Scheduler have partial IaC parity (CDK L2 for Scheduler GA 2025-04).
- Ask The Architect: "Is this a many-to-many routing problem (bus), a single producer→consumer wiring (Pipes), a time-triggered task (Scheduler), or a pure high-fan-out/transport problem (SNS/Kinesis)?"
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html (accessed 2026-08-28); https://aws.amazon.com/eventbridge/pricing/ (accessed 2026-08-28); https://aws.amazon.com/event-driven-architecture/ (accessed 2026-08-28)

**Decision: Choreography vs Orchestration for a multi-service business transaction (Saga)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Choreography | Amazon EventBridge buses + rules + AWS Lambda | Loose coupling, no central SPOF, autonomy | Global timeout/retry control; observability | Few participants; teams own their reactions independently |
  | Orchestration | AWS Step Functions (+ EventBridge triggers) | Central visibility, retries/timeouts, compensations | Central control point/coupling | Many participants; end-to-end monitoring and compensation logic required |

- Cost Profile: Choreography = per-event bus cost + per-Lambda invocation; Orchestration = Step Functions state-transition cost (Express cheaper for high volume) + Lambda.
- Scaling Characteristics: Choreography scales with the bus; Orchestration scales with Step Functions execution limits.
- Operational Burden: Choreography spreads logic across services (harder to trace); Orchestration centralizes logic (easier to reason about, one place to change).
- Lock-in Assessment: Both AWS-proprietary; Step Functions ASL and EventBridge rules are non-portable definitions.
- Ask The Architect: "How many services participate, and do we need centralized compensation/timeout control and end-to-end visibility (orchestration) or maximal decoupling and autonomy (choreography)?"
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-choreography.html (accessed 2026-08-28)

**Decision: Default bus vs multiple custom buses (bus topology)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Single default bus | Amazon EventBridge default event bus | Simplicity; free AWS-service ingestion | Domain isolation; per-domain policy/CMK | Small system; mostly AWS-service events |
  | Custom bus per domain | Amazon EventBridge custom event buses | Bounded-context isolation, per-bus policy + CMK | More buses/rules to manage (100 buses/Region) | Multiple bounded contexts / teams with distinct security postures |
  | Hub-and-spoke (bus-to-bus) | Amazon EventBridge bus-to-bus routing | Central governance/audit point | No third hop; extra custom-event cost | Central account aggregates domain buses |

- Cost Profile: Default-bus AWS-service ingestion is free; custom-bus events $1.00/M; bus-to-bus delivery billed as custom events.
- Scaling Characteristics: 100 event buses per Region per account; 300 rules per bus (100 in af-south-1/eu-south-1).
- Operational Burden: More buses = more IaC and policy surface; hub-and-spoke concentrates governance but must respect the no-third-hop constraint.
- Lock-in Assessment: Topology is AWS-specific; migrating means re-declaring buses/rules/policies.
- Ask The Architect: "Do bounded contexts need isolation (separate buses) and is a central audit/aggregation account required (hub-and-spoke), remembering EventBridge refuses a third hop?"
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-bus-to-bus.html (accessed 2026-08-28)

**Decision: Pipes enrichment compute — Lambda vs Step Functions Express vs API Gateway/API Destination**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Lambda enrichment | AWS Lambda | Arbitrary code, fast cold-path, up to 6 MB response | 15-min pipe execution ceiling shared budget | Custom transform/lookup logic in code |
  | Step Functions Express | AWS Step Functions (Express only) | Multi-step enrichment as a workflow | Standard workflows unsupported (sync only) | Enrichment needs several coordinated calls |
  | API Gateway / API Destination | Amazon API Gateway / API Destination | Call an existing internal or external HTTP API | Network/latency + auth management | Reference data lives behind an HTTP API |

- Cost Profile: Pipes $0.40/M requests plus the enrichment compute cost; enrichment is synchronous so slow enrichers raise per-execution time and cost.
- Scaling Characteristics: Enrichment response max 6 MB; total pipe execution (enrichment + target) max 5 minutes and cannot be increased.
- Operational Burden: Lambda = code to maintain; Step Functions Express = ASL to maintain; API options = manage the endpoint and its auth (Secrets Manager for API Destination).
- Lock-in Assessment: Enrichment target is AWS-specific config; the enricher itself may be portable code (Lambda) or not (Step Functions ASL).
- Ask The Architect: "Is enrichment a single code call (Lambda), a multi-step flow (Step Functions Express), or a call to an existing HTTP API (API Gateway / API Destination) — and can it complete within the 5-minute pipe budget?"
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/pipes-enrichment.html (accessed 2026-08-28)

### 🚫 Anti-Patterns

**Anti-Pattern: No DLQ on production targets (relying on default retry only)**
- Risk Level: CRITICAL
- Why: Reliability — exhausted retries "drop" the event and permanent errors skip retry entirely; without a DLQ these events are unrecoverable and lost silently.
- Blast Radius: Every rule/target without a DLQ; data loss is invisible until a downstream reconciliation gap surfaces.
- ❌ Wrong:
  An Amazon EventBridge rule targeting an AWS Lambda function with no DeadLetterConfig and default retry — when the function is throttled beyond MaximumEventAgeInSeconds or the target is misconfigured (permissions), events vanish.
- ✅ Correct:
  Attach a standard Amazon SQS DLQ to the target, set MaximumRetryAttempts and MaximumEventAgeInSeconds explicitly, and alarm on InvocationsSentToDlq and InvocationsFailedToBeSentToDlq.
- Detection:
  `aws events list-targets-by-rule` shows targets missing DeadLetterConfig; a CloudWatch alarm on FailedInvocations firing with no corresponding DLQ.
- Impact: Data loss
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html (accessed 2026-08-28)

**Anti-Pattern: Recursive / infinite-loop rules**
- Risk Level: HIGH
- Why: Cost / Reliability — a rule whose target action re-emits an event that matches the same rule "fires the rule again, creating an infinite loop," driving runaway invocation cost and throttling.
- Blast Radius: The looping rule and the whole bus (throttling), plus the bill.
- ❌ Wrong:
  A rule matching S3 object-created events whose target re-writes the object's ACL, generating another object event that re-matches the rule — an endless self-triggering loop.
- ✅ Correct:
  Narrow the event pattern to exclude the self-generated event (e.g., filter on a marker attribute or a different detail-type), or route the corrective action to a separate bus/rule that cannot re-match; monitor DeadLetterInvocations (which counts loop-suppressed invocations).
- Detection:
  CloudWatch alarm on abnormal Invocations/TriggeredRules growth; DeadLetterInvocations non-zero; AWS Cost Anomaly Detection on EventBridge.
- Impact: Cost overrun / Availability degradation (throttling)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html (accessed 2026-08-28)

**Anti-Pattern: Relying on multi-hop (third-hop) forwarding across accounts/buses/Regions**
- Risk Level: HIGH
- Why: Reliability — "If a receiver account sets up a rule that sends events received from a sender account on to a third account, these events are not sent to the third account." The same rule applies bus-to-bus. Events silently disappear.
- Blast Radius: Any 3-tier forwarding chain; events are lost at the second hop's onward send.
- ❌ Wrong:
  Account A → Account B's bus → (rule forwards) → Account C's bus. The A-origin events never reach Account C, only surfacing as DLQ code THIRD_ACCOUNT_HOP_DETECTED / THIRD_REGION_HOP_DETECTED.
- ✅ Correct:
  Have Account A publish directly to both Account B and Account C buses (each a single hop), or aggregate at a single hub bus that consumers read from — never chain a received event onward to a third bus.
- Detection:
  Inspect DLQ messages for THIRD_ACCOUNT_HOP_DETECTED / THIRD_REGION_HOP_DETECTED; audit rules whose source and target are both cross-account/cross-bus.
- Impact: Data loss (silent)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html (accessed 2026-08-28)

**Anti-Pattern: Overly permissive event-bus resource policy / `*` in the account field**
- Risk Level: HIGH
- Why: Security — granting events:PutEvents broadly (or on Resource: *) lets untrusted accounts inject events; and using `*` in a rule's account field does NOT act as a wildcard (it matches nothing), so architects who intend "all accounts" leave rules that never scope the source account.
- Blast Radius: The bus and every rule/target downstream; event injection and unexpected triggering.
- ❌ Wrong:
  A bus resource policy allowing events:PutEvents to Principal "*" with no aws:SourceArn/account condition, and rules with `"account": ["*"]`.
- ✅ Correct:
  Scope the resource policy to specific account IDs or an Organization ID with aws:SourceArn, and pin explicit account IDs in every rule's account field; require IAM roles for cross-account targets (mandatory since 2023-03-02).
- Detection:
  `aws events describe-event-bus` policy review for wildcard principals; scan rule patterns for `"account": ["*"]` or a missing account field on cross-account buses.
- Impact: Compliance violation / event injection (integrity)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html (accessed 2026-08-28)

**Anti-Pattern: FIFO SQS queue as a DLQ (or as a required-ordering DLQ)**
- Risk Level: MEDIUM
- Why: Reliability — EventBridge rules, Pipes stream-source DLQs, and Scheduler DLQs all explicitly support standard Amazon SQS queues only; "You can't use a FIFO queue for a DLQ in EventBridge." A FIFO DLQ silently fails to capture.
- Blast Radius: The affected rule/pipe/schedule; failed events are not captured despite an apparent DLQ.
- ❌ Wrong:
  Configuring an Amazon SQS FIFO queue as the DeadLetterConfig target for an EventBridge rule or a Scheduler schedule.
- ✅ Correct:
  Use a standard Amazon SQS queue in the same Region as the rule for the DLQ; if ordering matters for reprocessing, add ordering metadata in the consumer rather than a FIFO DLQ.
- Detection:
  Audit DeadLetterConfig ARNs for `.fifo` suffixes; validate DLQ delivery with a forced-failure test event and confirm messages arrive.
- Impact: Data loss (uncaptured failures)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html (accessed 2026-08-28)

**Anti-Pattern: Enabling CMK on an event bus while still depending on Schema Discovery**
- Risk Level: MEDIUM
- Why: Security/Operational — "Schema discovery does not support" CMK-encrypted buses (requires an AWS owned key), and events >1000 KiB are silently not discovered with no error. Enabling CMK on a bus that relies on discovery silently breaks schema cataloging.
- Blast Radius: Schema catalog for that bus; consumers depending on generated bindings drift out of date.
- ❌ Wrong:
  Turning on a CMK for a bus that has event discovery enabled and expecting the Discovered schema registry to keep updating.
- ✅ Correct:
  Bootstrap schemas with discovery on an AWS-owned-key bus first (or maintain custom schemas), then apply the CMK; or accept CMK and manage schemas explicitly. Attach a DLQ so encryption/decryption-failure events are captured.
- Detection:
  Confirm the bus KmsKeyIdentifier is set while a discoverer is enabled; check the Discovered schema registry for stale versions.
- Impact: Operational degradation (schema drift)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schemas-infer.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-encryption-event-bus-cmkey.html (accessed 2026-08-28)

---

## Cloud-Native Design Patterns

**Pattern: Choreography (Saga via events)**
- Category: Communication / Data consistency
- Problem: Maintain data integrity across a distributed business transaction spanning multiple microservices with separate data stores, where a two-phase commit is impossible (database-per-service).
- Solution on AWS: Each service runs a local transaction and publishes a domain event to a custom Amazon EventBridge bus; downstream services subscribe via rules that invoke AWS Lambda. Failures publish compensating events that trigger compensating transactions (reverse prior steps). Mitigate dual-writes with the transactional outbox pattern; make every participant idempotent.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Coupling | Fully decoupled, no central SPOF | Logic scattered across services |
  | Complexity | Simple with few participants | Grows fast; risk of cyclic dependencies |
  | Control | Service autonomy | Hard to enforce global timeouts/retries |
  | Observability | Independent scaling | Weaker end-to-end visibility than orchestration |

- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-choreography.html (accessed 2026-08-28)

**Pattern: Fan-Out**
- Category: Scalability / Communication
- Problem: Many independent systems must react to a single event without the producer writing per-consumer push code.
- Solution on AWS: Publish one event to Amazon EventBridge; multiple rules (each with up to five targets) route it to independent consumers by content pattern. For very high fan-out to thousands–millions of endpoints, AWS positions Amazon SNS (often used together: EventBridge rule → SNS topic → many subscribers).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Decoupling | Producer unaware of consumers | Per-event cost on custom bus ($1.00/M) |
  | Filtering | Rich content-based routing per consumer | Rule sprawl if unmanaged |
  | Scale | Add consumers without touching producer | Max 5 targets per rule (use SNS/multiple rules beyond that) |

- Source: https://aws.amazon.com/event-driven-architecture/ (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-targets.html (accessed 2026-08-28)

**Pattern: Claim-Check (large-payload offloading via EventBridge Pipes)**
- Category: Data / Communication
- Problem: Events are too large for the 1 MB PutEvents limit or carry sensitive payloads that should not traverse the bus.
- Solution on AWS: Split the message into a lightweight reference ("claim check") plus an external payload stored in Amazon S3. A first EventBridge Pipe's enrichment stores the payload to S3 and forwards only the claim check; a second Pipe retrieves the payload from S3 via the claim check when the consumer needs it. Recommended by AWS for payloads exceeding limits (also: upload to S3 and pass the object URL).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Size/cost | Bus carries only small references | Two-stage architecture complexity |
  | Compliance | Sensitive payload stays in controlled S3 | External-store latency on retrieval |
  | Reliability | Avoids 1 MB hard limit failures | Extra S3 lifecycle/permissions to manage |

- Source: https://aws.amazon.com/blogs/compute/implementing-architectural-patterns-with-amazon-eventbridge-pipes/ (accessed 2026-08-28)
  > ⚠️ Source dated 2023-02; verify currency.

**Pattern: Content-Based Router / Message Filter**
- Category: Communication
- Problem: Heterogeneous events on one bus must reach different consumers, and unwanted events (or PII) must be dropped before downstream processing.
- Solution on AWS: Use Amazon EventBridge rule event patterns (prefix, suffix, numeric, cidr, wildcard, anything-but, $or, exists) to route by content, and EventBridge Pipes FilterCriteria to discard non-matching stream/queue records before enrichment (billed only for matches). Input transformers reshape the retained events for each target.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Efficiency | Unmatched events never invoke/bill a target | Pattern complexity limits (2,048 chars; 30 wildcard rules/bus; $or <1,000 combos) |
  | Decoupling | Routing logic lives in infra, not code | Harder to unit-test than code branches |
  | Compliance | Filter/strip PII before longer-retention stages | Requires disciplined pattern governance |

- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-pattern-operators.html (accessed 2026-08-28); https://aws.amazon.com/blogs/compute/implementing-architectural-patterns-with-amazon-eventbridge-pipes/ (accessed 2026-08-28)

---

## Security Architecture

**Security Domain: Cross-Account / Cross-Region Event Ingestion**
- AWS Services: Amazon EventBridge event bus (resource-based policy), AWS IAM (execution role), AWS Organizations
- Architecture: The receiver/central bus grants events:PutEvents to specific account IDs or an Organization ID via a resource-based policy scoped with aws:SourceArn (confused-deputy protection). Sender rules forward to the receiver bus ARN using an IAM role trusted by events.amazonaws.com (mandatory for cross-account targets created after 2023-03-02). Every consuming rule pins explicit account IDs in the account field. Respect the no-third-hop constraint.
- Verification: `aws events describe-event-bus --name <bus>` to inspect the policy; test with a scoped PutEvents from a remote account and confirm the MatchedEvents metric on the target bus.
- Compliance Alignment: Least-privilege principal scoping and confused-deputy mitigation (Security pillar); per-Region buses support data-residency separation.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-resource-based.html (accessed 2026-08-28)

**Security Domain: Encryption and Key Governance (CMK) + In-Transit**
- AWS Services: Amazon EventBridge (buses, archives, Pipes, connections, API destinations), AWS KMS (customer managed key), AWS Secrets Manager, Amazon SQS (DLQ)
- Architecture: Apply a CMK to buses (GA 2024-05), archives/replay (2025-04), and rule filter patterns/input transformers (2025-09). The key policy grants events.amazonaws.com kms:DescribeKey/GenerateDataKey/Decrypt, bound by the event-bus-ARN encryption context and aws:SourceArn. Encryption in transit requires TLS 1.2 (TLS 1.3 recommended); FIPS 140-3 endpoints available. Events flowing through a Pipe are never stored at rest. Note: event metadata, bus names, rule names, and tags are NOT encrypted at rest; Schema Discovery is unavailable on CMK buses.
- Verification: `aws events describe-event-bus` shows KmsKeyIdentifier; CloudTrail KMS events display the encryption context; monitor EventBusEncryptionFailed.
- Compliance Alignment: Satisfies customer-controlled-key mandates (GDPR, FedRAMP, PCI-DSS key-management controls) — framework reference, not legal advice.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-encryption-event-bus-cmkey.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-data-protection.html (accessed 2026-08-28)

**Security Domain: Private Connectivity / Network Isolation**
- AWS Services: Amazon EventBridge interface VPC endpoints (AWS PrivateLink), VPC endpoint policies, FIPS endpoints
- Architecture: Create interface VPC endpoints — com.amazonaws.{region}.events (buses), com.amazonaws.{region}.pipes and .pipes-data (Pipes control + Kafka/MQ data), com.amazonaws.{region}.schema (Schema Registry) — so PutEvents and Pipes API traffic never traverse the public internet. Apply VPC endpoint resource policies on pipes / pipes-fips to deny specific Pipe APIs or limit APIs to specific Pipe ARNs (Pipes has no resource-based policy, so this is the primary Pipes access control). Use FIPS endpoints where required.
- Verification: Confirm DNS resolves to private IPs; test PutEvents from a VPC with no NAT/IGW; validate the endpoint policy denies unlisted APIs.
- Compliance Alignment: Network isolation for regulated workloads (Security pillar); API-level restriction of Pipes by ARN.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-related-service-vpc.html (accessed 2026-08-28)

---

## Operational Patterns

**Operational Pattern: Archive-and-Replay for Recovery / Reprocessing**
- RTO/RPO: RTO minutes-to-hours (bounded by the replay time-range size, one-minute-interval processing, and the max 10 concurrent replays per account/Region; wait ~10 minutes before replay for archive completeness). RPO near-zero for archived custom/partner events within the retention window (default indefinite); AWS-service event coverage depends on the archive's event pattern.
- AWS Services: Amazon EventBridge Archive, Amazon EventBridge Replay, source Amazon EventBridge bus, target consumers
- Cost Profile: Medium — archive processing $0.10/GB, archive storage $0.023/GB-month, replayed events billed as custom events ($1.00/M). Cost driver is archive volume × retention.
- Automation: Trigger StartReplay from a runbook/Lambda; consumers use the injected replay-name field for idempotency; a managed rule auto-prevents replayed events from re-entering the archive. Replays can be canceled while Starting/Running; EventBridge deletes replays after 90 days.
- Runbook Skeleton:
  1. Identify the incident time window and affected rules.
  2. Confirm archive retention covers the window; wait ≥10 min after the window's end for completeness.
  3. `aws events start-replay --replay-name <name> --event-source-arn <archive-arn> --event-start-time <t0> --event-end-time <t1> --destination Arn=<bus-arn>,FilterArns=<rule-arns>`.
  4. Monitor with `aws events describe-replay` (EventLastReplayedTime); ensure consumers dedupe on replay-name.
  5. Verify downstream reconciliation; cancel if incorrect (while Starting/Running).
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html (accessed 2026-08-28)

**Operational Pattern: Failure Isolation with DLQ + Metric-Driven Alerting**
- RTO/RPO: RTO ~1 minute detection (CloudWatch metric cadence, best-effort delivery) plus fix + DLQ redrive time. RPO zero for events captured in the DLQ; the loss risk is events failing to reach the DLQ (alarm on InvocationsFailedToBeSentToDlq).
- AWS Services: Amazon EventBridge (rule targets), Amazon SQS (DLQ), Amazon CloudWatch (metrics/alarms), Amazon SNS (on-call), AWS Lambda (redrive), AWS X-Ray (root cause)
- Cost Profile: Low — SQS storage of failed events + CloudWatch alarms; cost scales with failure volume.
- Automation: CloudWatch alarms on FailedInvocations, InvocationsSentToDlq, InvocationsFailedToBeSentToDlq, ThrottledRules, DeadLetterInvocations (and EventBusEncryptionFailed for CMK buses) → SNS to on-call; an automated Lambda drains/redrives the DLQ after the underlying fix; X-Ray traces target failures (note the trace header is absent from the DLQ message body but present as an SQS message attribute).
- Runbook Skeleton:
  1. Alarm fires (e.g., InvocationsSentToDlq > 0).
  2. Inspect DLQ messages: read ERROR_CODE, ERROR_MESSAGE, EXHAUSTED_RETRY_CONDITION, TARGET_ARN.
  3. Classify: permission (NO_PERMISSIONS/FAILED_TO_ASSUME_ROLE), missing resource (NO_RESOURCE), throttling, timeout, or target error.
  4. Remediate the target/permission/quota.
  5. Redrive the DLQ (Lambda consumer or SQS start-message-move-task) once healthy.
  6. If InvocationsFailedToBeSentToDlq > 0, fix DLQ permissions/size immediately — those events are lost.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-monitoring.html (accessed 2026-08-28)

---

## Reference Architectures

**Architecture: Saga-Choreography Order Pipeline (event-driven microservices)**
- Context: A distributed order transaction (order → inventory reservation → payment) across independently owned microservices requiring data consistency without two-phase commit.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Ingress | Amazon API Gateway → AWS Lambda | Accept the order, run the local Order transaction |
  | Routing | Amazon EventBridge custom buses (Orders, Inventory, Payment) | Domain-scoped event routing between services |
  | Compute | AWS Lambda (per service) | React to events, run local transactions + compensations |
  | State/dedupe | Amazon DynamoDB | Service data stores + idempotency keys |
  | Reliability | Amazon SQS (DLQ per rule) + Retry Policy | Capture undeliverable events |
  | Recovery | Amazon EventBridge Archive + Replay | Reprocess after incidents |
  | Observability | Amazon CloudWatch (metrics/alarms/logs), AWS X-Ray | Delivery metrics, tracing (PutEvents-origin) |

- Key Decisions: Choreography vs orchestration (few participants → choreography); one custom bus per bounded context; transactional outbox to avoid dual-writes; idempotent consumers keyed on event id; compensating events on failure (revert inventory, cancel order).
- Scaling Path: Start single-account/single-Region; add consumers via new rules (max 5 targets/rule, then SNS fan-out); split high-volume domains onto dedicated buses; migrate to orchestration (AWS Step Functions) if participant count and compensation complexity grow; add cross-account hub-and-spoke (respecting no-third-hop) for organization-wide events.
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-choreography.html (accessed 2026-08-28)

**Architecture: Point-to-Point Streaming Integration with EventBridge Pipes + Claim Check**
- Context: Wire a high-volume stream/queue (Amazon SQS, Amazon Kinesis Data Streams, Amazon DynamoDB Streams, Amazon MSK, or Amazon MQ) to a processing target, with filtering, enrichment, ordering, and large/sensitive payload handling.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Source | Amazon SQS / Kinesis Data Streams / DynamoDB Streams / MSK / Amazon MQ | Event producer with built-in polling by the Pipe |
  | Filter | EventBridge Pipes FilterCriteria | Drop non-matching records before enrichment (billed only for matches) |
  | Enrich | AWS Lambda / Step Functions Express / API Gateway / API Destination | Augment or split payload; store large payload to Amazon S3 (claim check) |
  | Payload store | Amazon S3 | Hold large/sensitive payloads referenced by claim check |
  | Target | AWS Step Functions / AWS Lambda / second event bus | Process the enriched event; second Pipe retrieves payload via claim check |
  | Reliability | Amazon SQS DLQ (stream sources), Retry Policy | Capture failures (max record age 1 min–24 h, 0–185 attempts) |

- Key Decisions: Pipes vs bus (single source→target → Pipes); enrichment compute choice (Lambda vs Step Functions Express vs HTTP); ordering (preserved from ordered sources); claim-check when payloads approach the 1 MB limit or carry PII; stay within the 5-minute pipe execution ceiling and 6 MB enrichment response.
- Scaling Path: Increase source concurrency (DynamoDB/Kinesis ParallelizationFactor × shards; SQS up to 1,250; Kafka up to 1,000 partitions); tune batch size/window; split into multiple Pipes as source/target pairs grow; front with a bus if the integration becomes many-to-many.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html (accessed 2026-08-28); https://aws.amazon.com/blogs/compute/implementing-architectural-patterns-with-amazon-eventbridge-pipes/ (accessed 2026-08-28)
  > ⚠️ Blog source dated 2023-02; verify currency.

---

## Service Equivalence Map

Cross-provider mapping for the messaging/eventing/scheduling service classes covered, to aid architects comparing providers. AWS entries are High Confidence (official docs); cross-provider equivalents are Medium Confidence (functional analogues, not feature-identical).

| Service Class | AWS (2026) | Microsoft Azure | Google Cloud | Oracle Cloud (OCI) |
|---------------|-----------|-----------------|--------------|---------------------|
| Event bus / router (content-based routing) | Amazon EventBridge event bus + rules | Azure Event Grid | Eventarc | OCI Events service |
| Point-to-point integration (source→filter→enrich→target) | Amazon EventBridge Pipes | Azure Event Grid + Logic Apps / Functions | Eventarc + Workflows | OCI Connector Hub |
| Managed scheduler (cron/one-time) | Amazon EventBridge Scheduler | Azure Logic Apps (recurrence) / Azure Scheduler (retired) | Cloud Scheduler | OCI Resource Scheduler |
| Schema registry | Amazon EventBridge Schema Registry | Azure Schema Registry (Event Hubs) | (Pub/Sub schemas) | (N/A native equivalent) |
| Pub/sub topic (high fan-out) | Amazon SNS | Azure Service Bus Topics / Event Grid | Cloud Pub/Sub | OCI Notifications / Streaming |
| Message queue | Amazon SQS | Azure Service Bus Queues / Storage Queues | Cloud Tasks | OCI Queue |
| Event streaming (ordered, replayable) | Amazon Kinesis Data Streams | Azure Event Hubs | Cloud Pub/Sub / Managed Kafka | OCI Streaming |
| Dead-letter queue | Amazon SQS (standard) DLQ | Service Bus / Event Grid dead-lettering | Pub/Sub dead-letter topic | OCI Queue DLQ |

> Cross-provider rows are functional analogues for orientation only; verify feature parity against each provider's current documentation before design decisions. Azure/GCP/OCI comparisons are UNVERIFIED against official AWS sources (AWS does not publish competitor comparisons) — Medium Confidence.

---

## Provider Differentiators

**Differentiator: Rich content-based routing with advanced comparison operators**
- Unique Value: Server-side matching on event content with prefix, suffix, equals-ignore-case, anything-but (+ prefix/suffix/wildcard variants), numeric ranges, cidr (IPv4/IPv6), wildcard, $or (cross-field), and exists — far beyond Amazon SNS attribute filtering and unavailable in SQS/Kinesis.
- Architecture Impact: Routing logic lives in infrastructure, not consumer code; unmatched events never invoke or bill a target.
- When to Leverage: Any many-to-many routing where consumers care about different subsets of event content.
- Caveat: Pattern size 2,048 chars; max 30 wildcard rules per bus (hard); $or combinations must stay under 1,000; wildcard is bus-rule-only (not Pipes).
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-pattern-operators.html (accessed 2026-08-28)

**Differentiator: EventBridge Pipes — managed point-to-point with filter + synchronous enrichment**
- Unique Value: A single managed primitive that polls Amazon SQS/Kinesis/DynamoDB Streams/MSK/Kafka/MQ, filters, synchronously enriches (Lambda/Step Functions Express/API Gateway/API Destination), and delivers — preserving source ordering — replacing bespoke glue/poller code.
- Architecture Impact: Eliminates a class of custom Lambda "pollers"; enrichment can also act as a filter (empty response suppresses the target).
- When to Leverage: Wiring one producer stream/queue to one consumer with transformation/enrichment needs.
- Caveat: 1:1 only; 5-minute execution ceiling (not adjustable); 6 MB enrichment response; only Step Functions Express as enrichment; no resource-based policy (use VPC endpoint policy).
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html (accessed 2026-08-28)

**Differentiator: EventBridge Scheduler — universal targeting at massive scale**
- Unique Value: One-time and recurring schedules invoking 270+ AWS services and 6,000+ API operations via universal target parameters, with per-schedule IANA time zones (automatic DST), flexible time windows, retry policy, DLQ, and scale to 10,000,000 schedules per Region (adjustable to billions).
- Architecture Impact: Replaces cron servers and legacy scheduled rules; schedules become first-class, individually managed resources with built-in reliability controls.
- When to Leverage: Any time-triggered task, especially high-cardinality per-entity schedules (e.g., per-customer reminders).
- Caveat: Target Input payload capped at 256 KB; 60-second precision without a flexible window; not event-triggered.
- Source: https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html (accessed 2026-08-28)

**Differentiator: Schema Registry with discovery and multi-language code bindings**
- Unique Value: Automatic schema discovery from live bus traffic (including cross-account by default), automatic versioning, and generated typed code bindings for Golang, Java, Python, and TypeScript via console, API, or IDE toolkit.
- Architecture Impact: Consumers get typed models, reducing parsing errors and speeding development; a discoverable event catalog across 200+ AWS services (surfaced in the 2025-11 enhanced visual rule builder).
- When to Leverage: Teams building many typed consumers, or documenting an event catalog for an organization.
- Caveat: Exporting custom schemas is unsupported; discovery is billed beyond 5M events/month, unsupported on CMK buses, and silently skips events >1000 KiB.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schema-registry.html (accessed 2026-08-28); https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schema-code-bindings.html (accessed 2026-08-28)

**Differentiator: Native AWS-service and SaaS partner event sources**
- Unique Value: EventBridge ingests events directly from AWS services (free on the default bus) and from SaaS partners via partner event sources onto dedicated buses — a catalog no raw transport primitive (SNS/SQS/Kinesis) provides.
- Architecture Impact: React to AWS control-plane and third-party SaaS events without building integrations; drives event-driven automation and operations.
- When to Leverage: Automating on AWS-service state changes or integrating SaaS providers' events.
- Caveat: Cross-account delivery of AWS-service events is billed ($1.00/M); partner-source setup mechanics vary by provider.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus.html (accessed 2026-08-28); https://aws.amazon.com/event-driven-architecture/ (accessed 2026-08-28)

**Differentiator: Durable Archive and rule-based Replay of routed events**
- Unique Value: A managed, event-pattern-filtered archive of bus events with configurable retention (default indefinite) and replay of a time window back to the source bus, optionally scoped to specific rules — a capability Kinesis (retention only) and SNS/SQS lack for routed events.
- Architecture Impact: Enables recovery, reprocessing, and realistic test-data generation without custom capture infrastructure.
- When to Leverage: Disaster recovery, bug-fix reprocessing, or replaying production traffic into a new consumer.
- Caveat: Replay is unordered (one-minute buckets), source-bus-only, max 10 concurrent per account/Region, and loses the X-Ray trace header.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html (accessed 2026-08-28)

---

## Scenario Coverage

**Standard Case**: Event-driven microservices with fan-out and reliable delivery
- Approach: Publish domain events via PutEvents to a custom Amazon EventBridge bus; route with content-based rules to consumers (AWS Lambda, AWS Step Functions, Amazon SQS). Attach a standard Amazon SQS DLQ and explicit retry policy to every target; make consumers idempotent (Amazon DynamoDB dedupe keys); enable enhanced logging to Amazon CloudWatch Logs; publish the schema to the Schema Registry and generate typed bindings.
- Key Decisions: Custom bus per bounded context; server-side filtering vs consumer filtering; choreography vs orchestration; retry/DLQ tuning per target SLA; idempotency-key strategy.

**Edge Case**: Cross-account, encrypted, large-payload events under compliance constraints
- Approach: Aggregate events into a central bus via cross-account resource-based policies scoped with aws:SourceArn and explicit account fields (single hop only — no third hop). Encrypt with a CMK (bus + archives + filter patterns/input transformers) and attach a DLQ for encryption/decryption failures. For payloads near the 1 MB PutEvents limit or carrying PII, apply the claim-check pattern via EventBridge Pipes with Amazon S3. Use interface VPC endpoints (PrivateLink) and FIPS endpoints for network isolation. Note Schema Discovery is unavailable on CMK buses — maintain custom schemas.
- Approach (handling with AWS services): Amazon EventBridge (cross-account bus, CMK, Pipes, archive), AWS KMS, Amazon S3, Amazon SQS DLQ, AWS PrivateLink, AWS CloudTrail for KMS audit.

**Anti-Pattern Case**: Architect requests a 3-tier cross-account forwarding chain with a FIFO DLQ and no idempotency
- Clarification: Flag three problems before proceeding. (1) EventBridge silently refuses the third hop — ask whether the origin account can publish directly to each destination (single hop) or aggregate at one hub bus. (2) FIFO SQS queues are unsupported as DLQs — confirm a standard SQS DLQ and, if ordering matters, capture ordering metadata in the consumer. (3) At-least-once, unordered delivery means duplicates are expected — require an idempotency-key strategy (DynamoDB conditional writes) before building. Do not implement the multi-hop chain as requested.

---

## Research Iteration Changelog

> Depth = exhaustive; gap-filling loop ran. One row per gap resolved or flagged.

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Metadata / Executive Summary | Event size limit stated as 256 KB in task brief | Corrected to 1 MB (1,048,576 bytes) per current docs; 256 KB flagged as superseded | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html (2026-08-28) |
| 1 | Architecture Guardrails / DLQ | Default retry behavior and permanent-error handling | Added (24h/185, exhausted→drop, permanent errors skip retry) | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html (2026-08-28); eb-rule-dlq.html |
| 1 | Anti-Patterns | Third-hop forwarding failure mode | Added with DLQ error codes THIRD_ACCOUNT_HOP_DETECTED / THIRD_REGION_HOP_DETECTED | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html (2026-08-28) |
| 1 | Security Architecture | CMK GA dates (buses/archives/filter patterns) | Added dated GA milestones (2024-05, 2025-04, 2025-09) | https://aws.amazon.com/about-aws/whats-new/2024/05/amazon-eventbridge-cmk-event-buses/ (2026-08-28) |
| 2 | Cloud-Native Design Patterns | Choreography vs orchestration saga | Added with Prescriptive Guidance citation | https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-choreography.html (2026-08-28) |
| 2 | Provider Differentiators | Pipes / Scheduler / Schema Registry / Archive & Replay | Added 6 differentiators with sources | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html; scheduler what-is; eb-archive.html (2026-08-28) |
| 2 | Operational Patterns | CloudWatch metric names for alerting | Added FailedInvocations, InvocationsSentToDlq, InvocationsFailedToBeSentToDlq, ThrottledRules, DeadLetterInvocations | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-monitoring.html (2026-08-28) |
| 3 | Executive Summary / Differentiators | 2025 feature launches (enhanced logging, visual rule builder, SQS fair queues) | Added dated GA entries | https://aws.amazon.com/about-aws/whats-new/2025/07/amazon-eventbridge-enhanced-logging-improved-observability/ (2026-08-28) |
| 3 | Service Equivalence Map | Cross-provider analogues | Added, marked Medium Confidence / UNVERIFIED for non-AWS | Provider docs (analogues; not AWS-sourced) |
| 4 | Provider Differentiators | Azure Event Grid / GCP Eventarc feature comparison | ⚠️ IRRESOLVABLE — no official AWS source publishes competitor comparisons; out of AWS-only scope | — |
| 4 | Glossary | Standalone GA date of the $or operator | UNVERIFIED — operator confirmed GA in current docs; discrete What's-New date not isolated | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-pattern-operators.html (2026-08-28) |
| 4 | Security Architecture | events:source / events:detail-type / events:creatorAccount condition keys | UNVERIFIED — documented in the Service Authorization Reference (not fetched); resource-policy examples use aws:SourceArn/aws:SourceAccount | https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazoneventbridge.html (not fetched) |
| 4 | Schema Registry | Schema Discovery overage price ($1.00 vs $0.10 per million) | UNVERIFIED — pricing-page fetch returned $1.00/M; older snippets said $0.10/M; confirm per Region | https://aws.amazon.com/eventbridge/pricing/ (2026-08-28) |
| 4 | Scheduler / Retry | Default values for MaximumRetryAttempts / MaximumEventAgeInSeconds on Scheduler | UNVERIFIED — API doc lists ranges (0–185; 60–86400) but not defaults | https://docs.aws.amazon.com/scheduler/latest/APIReference/API_RetryPolicy.html (2026-08-28) |
| 4 | Changelog | Exact date 256 KB→1 MB PutEvents size increase shipped | UNVERIFIED — current value (1 MB) verified; the change-announcement date not located | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html (2026-08-28) |
| 5 | Schema Registry / Glossary | Schema Discovery overage price | ✅ RESOLVED — $1.00/M confirmed from live pricing-page fetch (2026-08-28). $0.10/M is incorrect. Free tier: 5M events/month. Schema Registry (custom schemas + API calls) = free. Glossary updated. | https://aws.amazon.com/eventbridge/pricing/ (2026-08-28) |
| 5 | Glossary | $or operator GA status | ✅ RESOLVED — $or operator is GA: listed in the official comparison table (event bus support: Yes; pipe support: Yes) on the current operators page. No discrete What's-New post date is published on that page; claim status updated to "GA confirmed". | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-pattern-operators.html (2026-08-28) |
| 5 | Scheduler / Retry | Scheduler RetryPolicy valid ranges | ✅ RESOLVED (ranges) / ⚠️ REMAINING (defaults) — API reference confirms MaximumRetryAttempts valid range 0–185 and MaximumEventAgeInSeconds valid range 60–86400; both Required: No. Default values are not published in the API reference. The 24h/185 default documented in the Retry Policy glossary entry applies to EventBridge Rules (not Scheduler). | https://docs.aws.amazon.com/scheduler/latest/APIReference/API_RetryPolicy.html (2026-08-28) |
| 5 | Changelog | PutEvents 1 MB limit re-verification | ✅ VERIFIED — eb-putevents.html (2026-08-28) explicitly states "total request size must be less than 1 MB (1,048,576 bytes)"; a single event may use the full 1 MB if it is the only entry. Change-announcement date from 256 KB remains unlocated. | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents.html (2026-08-28) |
| 5 | Security Architecture | IAM condition keys (Service Authorization Reference) | ⚠️ REMAINING — eb-security-auth.html page did not return full content (model substituted general knowledge). Condition keys events:source, events:detail-type, events:creatorAccount remain documented only by model knowledge; not triangulated from the Service Authorization Reference page itself. | https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazoneventbridge.html (not fetched) |

### Verification commands (expected output)

```bash
grep -E "^## (Executive Summary|Cloud Architecture Glossary|Architecture Guardrails|Cloud-Native Design Patterns|Security Architecture|Operational Patterns|Reference Architectures|Provider Differentiators|Scenario Coverage|Service Equivalence Map)" StoryBeat/docs/research_cloud_AWS_EventBridge_EDA_2026.md
# Expected: all 10 headings appear

grep -E "^### (✅ Mandatory Patterns|⚠️ Architectural Decisions|🚫 Anti-Patterns)" StoryBeat/docs/research_cloud_AWS_EventBridge_EDA_2026.md
# Expected: all 3 subsection headings appear

grep -c "Pillar Alignment:" StoryBeat/docs/research_cloud_AWS_EventBridge_EDA_2026.md
# Expected: 6 (one per Mandatory Pattern)

grep -c "Risk Level:" StoryBeat/docs/research_cloud_AWS_EventBridge_EDA_2026.md
# Expected: 6 (one per Anti-Pattern)

grep "Target_Edition:" StoryBeat/docs/research_cloud_AWS_EventBridge_EDA_2026.md
# Expected: Target_Edition: "AWS EventBridge 2026"
```
