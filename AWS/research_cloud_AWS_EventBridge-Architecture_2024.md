# AWS EventBridge — Event-Driven Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS EventBridge — Event-Driven Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Event-Driven Architecture"
Target_Edition: "AWS EventBridge 2024"
Architecture_Context: "Event-driven applications requiring event routing, filtering, transformation, and delivery across distributed systems — covering event buses, pipes, scheduler, content-based routing, cross-account/cross-region event distribution, schema registry, archive and replay, global endpoints, and SaaS integrations"
Official_Source_URL: "https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to EventBridge feature updates, new event sources, and integration changes"
```

---

## Executive Summary

Amazon EventBridge is AWS's serverless event bus service that enables event-driven application integration at scale. It provides three distinct mechanisms for processing events: **Event Buses** (many-to-many event routing with content-based filtering), **EventBridge Pipes** (point-to-point integrations with enrichment and transformation), and **EventBridge Scheduler** (time-based task invocation with cron/rate expressions and one-time schedules). EventBridge natively integrates with over 200 AWS service event sources, 35+ SaaS partner integrations (Salesforce, Zendesk, Shopify, Auth0, etc.), and supports custom applications via the PutEvents API (up to 10,000 events/second in us-east-1). Unlike SNS/SQS which operate on raw messages, EventBridge operates on structured JSON events with schema awareness — enabling content-based routing via event patterns without consumer-side filtering logic.

The 2024 edition's most architecturally significant advances are: (1) **EventBridge Pipes GA with expanded sources** — point-to-point integrations from DynamoDB Streams, Kinesis Data Streams, SQS, Amazon MSK, and self-managed Apache Kafka to any supported target, with optional filtering, enrichment (Lambda, Step Functions, API Gateway, API destinations), and transformation; (2) **Enhanced event pattern operators** — including `wildcard` matching (`*` prefix/suffix patterns), `equals-ignore-case`, and `$or` operator for complex event filtering logic; (3) **Global Endpoints with automatic failover** — multi-region event routing using Route 53 health checks with RTO/RPO of ~360 seconds; (4) **Customer-managed KMS encryption for event buses** — encrypting events at rest with CMK keys plus dead-letter queues for encryption failures; (5) **EventBridge Scheduler** replacing legacy scheduled rules — offering 10M+ schedules per account, flexible time windows, and universal target support via templated targets.

The three most critical architecture guardrails for EventBridge are: (1) **always configure Dead-Letter Queues (DLQs) on every rule target** — without a DLQ, events that fail delivery after retry exhaustion are permanently lost with no recovery; (2) **design event patterns with maximum specificity** — overly broad patterns (matching all events or missing `source`/`detail-type` filters) create infinite loops, cost explosions, and unintended target invocations; (3) **use separate custom event buses for domain boundaries** — publishing all application events to the default bus mixes them with AWS service events, prevents fine-grained access control, and blocks cross-account distribution patterns.

---

## Cloud Architecture Glossary

```
Term: Event Bus
Definition: A router that receives events and delivers them to zero or more targets based on rules. EventBridge provides three bus types: the default event bus (receives AWS service events automatically), custom event buses (application and SaaS events), and partner event buses (SaaS provider integrations). Each account has one default bus; up to 100 custom buses per account per Region.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus.html
Architect Usage: Use the default bus only for AWS service event routing. Create custom event buses per domain or bounded context (e.g., "orders-bus", "payments-bus") for application events. This enables per-bus access policies, separate archive/replay, and cross-account distribution. Never publish custom application events to the default bus.
Common Confusion: An event bus is NOT a queue — events are not stored for later retrieval. Events that don't match any rule are discarded silently (unless archived). An event bus is also NOT a topic — it doesn't fan out to subscribers; it evaluates rules and routes to targets.

Term: Event
Definition: A JSON object representing a state change or occurrence. All events share a common envelope structure: version, id (UUID), detail-type, source, account, time, region, resources, and detail (the event payload). Events can be up to 256 KB in size. EventBridge assigns the id; publishers provide source, detail-type, and detail.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-events.html
Architect Usage: Design events as immutable facts — they describe what happened, not what to do. Use `source` as a reverse-DNS namespace (e.g., "com.mycompany.orders") and `detail-type` as the event name (e.g., "Order Placed"). The `detail` field contains the event payload. Standardize event schemas across teams via Schema Registry.
Common Confusion: EventBridge events are NOT messages — they represent state changes (something happened), not commands (do something). Events are delivered at-least-once but NOT ordered. The `id` field is system-generated and unique per event delivery — it is NOT a deduplication ID.

Term: Rule
Definition: An association between an event pattern (or schedule) and one or more targets. Rules evaluate events on the bus and route matches to up to 5 targets per rule. A rule belongs to exactly one event bus. Maximum 300 rules per bus (most Regions). Rules can optionally transform events before delivery using input transformers.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules.html
Architect Usage: Create one rule per distinct event-target routing path. Use the most specific event pattern possible to avoid unintended matches. Prefer multiple narrow rules over one broad rule with complex logic. Rules containing wildcards are limited to 30 per bus — use them sparingly.
Common Confusion: A rule with 5 targets invokes ALL 5 targets in parallel when matched — it is NOT round-robin or load-balanced. Rules do NOT guarantee ordering of target invocations. Scheduled rules are legacy — migrate to EventBridge Scheduler for new schedule-based workloads.

Term: Event Pattern
Definition: A JSON structure that defines the filter criteria for matching events on a bus. Event patterns use structural matching — only fields present in the pattern are evaluated; absent fields are ignored. Patterns support exact value matching (arrays), prefix/suffix/wildcard, numeric comparisons, exists/not-exists, and the $or operator. Maximum size: 2,048 characters.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html
Architect Usage: Always match on `source` AND `detail-type` as minimum specificity. Use the EventBridge Sandbox to test patterns before deployment. All values in a pattern field are OR'd (any match); all fields in a pattern are AND'd (all must match). Never use an empty pattern {} in production — it matches everything.
Common Confusion: Event patterns are NOT regex — they use a custom JSON-based DSL. Values must be specified as arrays (e.g., "source": ["aws.ec2"]), not bare strings. Nested field matching in `detail` uses the same structure as the event payload — not dot notation.

Term: Target
Definition: A resource or endpoint that EventBridge invokes when an event matches a rule. Each rule supports up to 5 targets. Targets include Lambda (async), SQS, SNS, Step Functions (async), Kinesis, Firehose, ECS tasks, CodeBuild, CodePipeline, API Gateway, API destinations (HTTP endpoints), CloudWatch Logs, Batch, Redshift Data API, other event buses (cross-account/cross-region), and more.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-targets.html
Architect Usage: EventBridge invokes Lambda and Step Functions asynchronously — the invocation returns immediately. For synchronous processing, use API Gateway as target. Targets require an IAM execution role (except for Lambda, SNS, SQS, and CloudWatch Logs which use resource-based policies). Always configure a DLQ on each target for failed delivery capture.
Common Confusion: EventBridge invokes targets with the FULL event envelope by default — not just the detail. Use Input Transformers or Input Paths to extract and reshape the payload before delivery. A target of "another event bus" is how you implement cross-account or cross-region routing — not cross-bus within the same account (three-hop is blocked).

Term: EventBridge Pipes
Definition: A point-to-point integration resource that connects a single event source to a single target, with optional filtering, enrichment, and transformation steps. Pipes poll the source (unlike event buses which receive pushed events). Supported sources: SQS, DynamoDB Streams, Kinesis Data Streams, Amazon MSK, self-managed Apache Kafka, Amazon MQ (ActiveMQ and RabbitMQ). Maximum 1,000 pipes per account.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html
Architect Usage: Use Pipes for ordered, stream-based processing where the source is a stream/queue and the target is a single downstream service. Pipes maintain ordering within a partition/shard. The enrichment step (Lambda, Step Functions, API Gateway, API destination) augments events before target delivery. Use Pipes + Event Bus together: Pipe sources a stream → sends to a custom event bus → bus fans out to multiple targets.
Common Confusion: Pipes are NOT rules on a bus — they are separate resources with different source models. Pipes POLL sources (pull-based), while buses receive events (push-based). Pipes support exactly ONE source and ONE target — for fan-out, target an event bus from the pipe.

Term: EventBridge Scheduler
Definition: A fully-managed scheduler for creating, running, and managing time-based tasks. Supports cron expressions, rate expressions, and one-time (at) schedules. Offers flexible time windows, retry policies (up to 185 retries), dead-letter queues, and universal target support (any AWS API via templated targets). Supports 10M+ schedules per account per Region.
Provider Docs Section: https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html
Architect Usage: Use Scheduler for ALL new time-based invocations — legacy EventBridge scheduled rules are deprecated in practice. Scheduler supports targets that legacy scheduled rules do not (e.g., any AWS SDK API action). Use flexible time windows for non-time-critical tasks to spread load. Configure DLQ for failed invocations.
Common Confusion: Scheduler is a SEPARATE service (different API, different console section) from EventBridge event buses — but part of the EventBridge product family. Scheduler does NOT publish events to a bus — it directly invokes targets. Do NOT confuse with legacy "scheduled rules" on event buses.

Term: Schema Registry
Definition: A repository for event schemas that EventBridge maintains. The AWS schema registry contains schemas for all AWS service events. You can create custom registries for application events. Schema discovery can automatically infer schemas from events flowing through a bus. Schemas are defined in OpenAPI 3.0 or JSONSchema Draft 4 format.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schema.html
Architect Usage: Enable schema discovery on custom event buses during development to automatically catalog event structures. Generate code bindings (TypeScript, Python, Java, Go) from schemas to ensure type-safe event handling in consumers. Use custom schemas as contracts between producing and consuming teams. Maximum 10 discoverers, 200 discovered schemas, 100 schemas per custom registry per Region.
Common Confusion: Schema discovery adds cost and should be disabled in production once schemas are stabilized. The discovered schema registry is separate from custom registries. Schema discovery observes events on the bus — it does NOT validate or reject events that don't match a schema.

Term: Archive and Replay
Definition: A feature that stores events from an event bus in an archive for later replay. Archives can filter which events to store using event patterns. Retention is configurable (indefinite by default, or N days). Replay re-delivers archived events to the source bus. Maximum 10 concurrent replays per account per Region.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html
Architect Usage: Enable archives on critical event buses for disaster recovery, event sourcing replay, new consumer bootstrapping, and integration testing with production event shapes. Use event pattern filtering on archives to store only relevant events (reduces cost). Replayed events include a `replay-name` metadata field — design consumers for idempotency. Allow 10 minutes after archiving before replaying to ensure all events are captured.
Common Confusion: Archived events are NOT replayed in strict chronological order — they are replayed in one-minute batches based on event time. Replay sends events back to the SAME bus (not arbitrary buses). Archive is NOT a DLQ — it stores ALL matching events regardless of delivery success. Replaying does NOT remove events from the archive.

Term: Global Endpoint
Definition: A managed endpoint that routes custom events across two Regions for Regional fault tolerance. Uses a Route 53 health check to determine which Region (primary or secondary) processes events. When the health check reports unhealthy, events automatically fail over to the secondary Region. Requires identically-named custom event buses in both Regions. Supports event replication (both Regions process all events simultaneously).
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-global-endpoints.html
Architect Usage: Use global endpoints for mission-critical event-driven workloads requiring multi-Region availability. Enable event replication to verify configuration and enable automatic recovery. RTO/RPO is ~360 seconds (max 420s). Global endpoints use Signature Version 4A (SigV4A) — ensure SDK supports AWS CRT library. Publishers use the endpoint ID in PutEvents calls instead of regional endpoints.
Common Confusion: Global endpoints work ONLY with custom events via PutEvents — NOT with AWS service events or partner events. You need identical custom buses and rules in BOTH Regions. Global endpoints do NOT replicate rules, targets, or archives — only events.

Term: API Destination
Definition: An HTTPS endpoint configured as a target for EventBridge rules. API destinations support OAuth, API key, and basic authentication via Connections. Rate limiting is configurable (1–300 invocations/second per destination). Used for integrating with external webhooks, SaaS APIs, and third-party services.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html
Architect Usage: Use API destinations to push events to external systems (Slack, PagerDuty, Datadog, custom webhooks) without Lambda intermediaries. Configure connection authentication once, reuse across multiple API destinations. Set appropriate rate limits to respect third-party API quotas. Maximum 3,000 API destinations and 3,000 connections per account per Region.
Common Confusion: API destinations are NOT the same as API Gateway targets. API destinations call EXTERNAL HTTP endpoints; API Gateway targets invoke your own API Gateway APIs. The rate limit is per-destination — not per-rule or per-bus. Invocations exceeding the rate limit are queued and delivered later (not dropped).

Term: Input Transformer
Definition: A rule-level configuration that reshapes event data before delivery to a target. Consists of two parts: Input Path (extracts values from the event using JSON path expressions) and Input Template (defines the output structure using extracted values and static text). Maximum 100 variables per transformer.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-transform-target-input.html
Architect Usage: Use input transformers to deliver only relevant event fields to targets (reduces payload, improves consumer simplicity). Common use: extract detail fields and format as the target's expected request body. For CloudWatch Logs targets, format as {"timestamp": <time>, "message": <message>}. For API destinations, reshape to match the external API's expected request format.
Common Confusion: Input transformers operate AFTER event pattern matching — they do not affect which events match the rule. Input Path uses JSON path syntax ($.detail.orderId) — not dot notation from the event pattern DSL. Transformed output is what the target receives — the original event is lost to the target unless passed through.

Term: Retry Policy
Definition: Configuration on a rule target that defines how EventBridge retries failed event deliveries. Two parameters: MaximumRetryAttempts (0–185, default 185) and MaximumEventAgeInSeconds (60–86400 seconds / 1 min–24 hours, default 24 hours). Events exceeding either limit are sent to the DLQ (if configured) or discarded.
Provider Docs Section: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html
Architect Usage: Set retry policy based on target criticality. For idempotent targets: maximize retries (185) with 24h age. For time-sensitive events: reduce MaximumEventAgeInSeconds to prevent stale event processing. For non-idempotent targets: reduce MaximumRetryAttempts and rely on DLQ for manual reprocessing. EventBridge uses exponential backoff for retries.
Common Confusion: Retry policy is per-TARGET, not per-rule or per-bus. Some failures bypass retries entirely (permission errors, non-existent resources) and go directly to DLQ. The 24-hour default age means EventBridge retries for up to 24 hours — events are NOT stored indefinitely.
```

---

## Architecture Framework Analysis: AWS Well-Architected — Event-Driven Pillar Alignment

```
Pillar: Reliability
Definition: The ability of a workload to perform its intended function correctly and consistently when it's expected to.
Key Design Principles:
  - Automatically recover from failure (DLQs capture failed deliveries; archive enables replay for recovery)
  - Test recovery procedures (replay archived events; validate DLQ processing runbooks)
  - Scale horizontally to increase aggregate workload availability (EventBridge scales automatically; targets scale independently)
  - Stop guessing capacity (EventBridge handles burst without provisioning; PutEvents scales to 10,000+ TPS)
  - Manage change in automation (IaC for buses, rules, targets, archives, pipes, scheduler)
Applies To Event-Driven Architecture: EventBridge is the primary AWS mechanism for implementing reliable event routing and content-based filtering. DLQs on every target ensure no event loss. Archives enable time-travel replay for recovery. Global Endpoints provide multi-region fault tolerance for mission-critical event flows. At-least-once delivery requires idempotent consumers.
Assessment Questions:
  1. Is every rule target configured with a Dead-Letter Queue (SQS) for failed deliveries?
  2. Are all event consumers designed to be idempotent (safe to process the same event multiple times)?
  3. Are archives enabled on critical event buses for disaster recovery and replay scenarios?
Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html

Pillar: Security
Definition: The ability to protect data, systems, and assets while delivering business value through risk assessments and mitigation strategies.
Key Design Principles:
  - Apply security at all layers (event bus resource policies, IAM execution roles, KMS encryption, VPC endpoints)
  - Enable traceability (CloudTrail for EventBridge API calls, CloudWatch metrics for invocations)
  - Implement least privilege (per-bus resource policies with specific source/account conditions; per-rule IAM roles)
  - Protect data in transit and at rest (TLS for PutEvents; KMS CMK encryption for event bus at rest)
  - Automate security best practices (SCPs, Config rules for bus policy validation)
Applies To Event-Driven Architecture: Every custom event bus must have a restrictive resource-based policy — never allow PutEvents from wildcard principals without conditions. Use KMS customer-managed keys for buses handling sensitive events. IAM roles on rule targets must follow least privilege — specific actions on specific resource ARNs. Cross-account event routing requires explicit resource policies and IAM roles (mandatory since March 2023).
Assessment Questions:
  1. Do all custom event bus resource policies restrict PutEvents to specific accounts/organizations?
  2. Is KMS encryption enabled on event buses handling PII or business-sensitive events?
  3. Do all rule targets use least-privilege IAM execution roles with specific actions and resource ARNs?
Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-security.html

Pillar: Performance Efficiency
Definition: The ability to use computing resources efficiently to meet system requirements and to maintain that efficiency as demand changes and technologies evolve.
Key Design Principles:
  - Use serverless architectures (EventBridge eliminates event routing infrastructure management)
  - Consider mechanical sympathy (PutEvents batch API for up to 10 entries per call; event pattern specificity reduces unnecessary invocations)
  - Democratize advanced technologies (managed content-based routing without custom filtering code)
Applies To Event-Driven Architecture: Use PutEvents batch API (up to 10 events per call) to maximize throughput per API call. Design event patterns with maximum specificity to reduce unnecessary target invocations. Use Input Transformers to send only relevant data to targets (reduces payload processing). For high-throughput streams, use Pipes (polling) rather than publishing individual events via PutEvents.
Assessment Questions:
  1. Are publishers using PutEvents batch API for high-volume scenarios (10 entries per call)?
  2. Are event patterns designed with maximum specificity (source + detail-type at minimum)?
  3. Are Input Transformers used to reduce payload size delivered to targets?
Source: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html

Pillar: Cost Optimization
Definition: The ability to run systems to deliver business value at the lowest price point.
Key Design Principles:
  - Adopt a consumption model (EventBridge charges per event published + per rule matched — $1.00/M custom events, $0 for AWS service events on default bus)
  - Measure overall efficiency (cost per event routed, target invocations per event)
  - Analyze and attribute expenditure (per-bus/per-rule CloudWatch metrics enable cost attribution)
  - Stop spending money on undifferentiated heavy lifting (managed event routing vs self-hosted Kafka/RabbitMQ)
Applies To Event-Driven Architecture: AWS service events on the default bus are free. Custom events cost $1.00/M (first 5M events). Cross-account events are charged to the sender. Archive storage charges apply per GB stored. Use specific event patterns to avoid unnecessary target invocations (each Lambda invocation, Step Functions execution has its own cost). Scheduler is $1.00/M scheduled invocations.
Assessment Questions:
  1. Are event patterns specific enough to prevent unnecessary target invocations?
  2. Are archives configured with appropriate retention periods (not indefinite) to control storage cost?
  3. Is EventBridge Scheduler used instead of Lambda-based cron patterns for time-based tasks?
Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html

Pillar: Operational Excellence
Definition: The ability to support development and run workloads effectively, gain insight into their operations, and continuously improve.
Key Design Principles:
  - Perform operations as code (IaC for buses, rules, pipes, schedulers, archives)
  - Make frequent, small, reversible changes (rule updates, pattern changes, target additions)
  - Anticipate failure (DLQs + CloudWatch alarms on FailedInvocations + archive for replay)
  - Learn from all operational failures (DLQ analysis, CloudWatch metrics, CloudTrail audit)
Applies To Event-Driven Architecture: All EventBridge resources must be IaC-managed (CloudFormation, CDK, Terraform). Enable CloudWatch metrics on all buses — alarm on FailedInvocations, ThrottledRules, and InvocationsFailedToBeSentToDLQ. Use Schema Registry to document event contracts. Enable schema discovery in dev/staging to detect event structure drift.
Assessment Questions:
  1. Are all EventBridge resources (buses, rules, targets, archives, pipes) managed via Infrastructure as Code?
  2. Are CloudWatch alarms configured on FailedInvocations and DLQ metrics for every bus?
  3. Is Schema Registry used to maintain event contracts between producing and consuming teams?
Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html

Pillar: Sustainability
Definition: Minimizing the environmental impact of running cloud workloads.
Key Design Principles:
  - Minimize unnecessary processing (specific event patterns reduce unnecessary target invocations and downstream compute)
  - Use managed services (EventBridge eliminates self-hosted event infrastructure)
  - Maximize utilization (serverless model — zero idle compute for event routing)
Applies To Event-Driven Architecture: Specific event patterns eliminate unnecessary Lambda/Step Functions invocations — reducing compute waste. Input Transformers reduce payload size transmitted to targets — reducing network waste. EventBridge's serverless model has zero idle footprint. Avoid publishing events that no rule matches — dead events waste ingestion resources.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Dead-Letter Queue on Every Rule Target**
- Pillar Alignment: Reliability, Operational Excellence
- Why: Without a DLQ, events that fail delivery after retry exhaustion (default: 185 retries over 24 hours) are permanently lost. Events may fail due to target permission errors, non-existent resources, throttling, or transient failures. DLQs capture these events with error metadata (RULE_ARN, TARGET_ARN, ERROR_CODE, ERROR_MESSAGE, RETRY_ATTEMPTS) enabling diagnosis and reprocessing.
- AWS Services: Amazon EventBridge (rule target DLQ configuration), Amazon SQS (standard queue as DLQ), Amazon CloudWatch (metrics)
- Architecture Decision:
  Every rule target must have a `DeadLetterConfig` with a valid SQS queue ARN. Only standard SQS queues are supported (FIFO queues cannot be EventBridge DLQs). The DLQ must be in the same Region as the rule. Grant the EventBridge service principal `sqs:SendMessage` permission on the DLQ via queue resource policy with `aws:SourceArn` condition scoped to the specific rule ARN. Set DLQ message retention to 14 days (maximum). Configure CloudWatch alarm on `ApproximateNumberOfMessagesVisible > 0`.
- Verification:
  ```bash
  aws events list-targets-by-rule --rule <RULE_NAME> --event-bus-name <BUS_NAME> \
    --query 'Targets[*].{Id:Id,DLQ:DeadLetterConfig.Arn}'
  # Every target must have a non-null DeadLetterConfig.Arn
  ```
- Trade-offs: Adds one SQS queue per target (minor cost — $0.40/M requests). DLQ messages require automated Lambda-driven reprocessing or manual intervention. SQS queue policy must explicitly grant EventBridge access.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html

**Custom Event Buses for Application Events**
- Pillar Alignment: Security, Operational Excellence
- Why: The default event bus receives ALL AWS service events for the account — mixing application events with service events creates security risks (overly broad rules matching unintended events), operational confusion (rules triggering on AWS operational events), and blocks cross-account distribution (you cannot share the default bus). Custom buses enable per-domain access policies, separate archives, independent monitoring, and granular cross-account sharing.
- AWS Services: Amazon EventBridge (custom event buses), AWS IAM (resource-based policies)
- Architecture Decision:
  Create one custom event bus per domain or bounded context (e.g., "orders-events", "payments-events", "inventory-events"). Never publish custom application events to the default bus. Each custom bus should have an explicit resource-based policy that restricts `events:PutEvents` to authorized accounts/principals. Use naming conventions that encode domain and environment (e.g., "prod-orders-events").
- Verification:
  ```bash
  aws events list-event-buses --query 'EventBuses[*].{Name:Name,Policy:Policy}'
  # Custom buses should exist for each application domain
  # Each bus should have a restrictive Policy (not open to all principals)
  ```
- Trade-offs: Multiple buses increase IaC surface area. Cross-bus routing within the same account requires explicit rules with event bus targets. Maximum 100 buses per account per Region (adjustable).
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus.html

**Specific Event Patterns with Source and Detail-Type**
- Pillar Alignment: Security, Cost Optimization, Reliability
- Why: Overly broad event patterns match unintended events — causing cost explosions (unnecessary target invocations), security risks (processing untrusted events), infinite loops (rule matches its own output), and operational noise. The minimum safe pattern specifies `source` AND `detail-type` to constrain matching to a specific event producer and event type.
- AWS Services: Amazon EventBridge (rule event patterns), CloudWatch (NumberOfMatchedEvents metric)
- Architecture Decision:
  Every event pattern MUST include both `"source"` and `"detail-type"` fields at minimum. Add `detail` field filters when additional specificity is required. Never deploy a rule with pattern `{}` (matches everything). For cross-account receiving, add `"account"` field to prevent matching events from unexpected sources. Test all patterns in the EventBridge Sandbox before deployment.
  ```json
  {
    "source": ["com.mycompany.orders"],
    "detail-type": ["Order Placed"],
    "detail": {
      "status": ["CONFIRMED"]
    }
  }
  ```
- Verification:
  ```bash
  aws events describe-rule --name <RULE_NAME> --event-bus-name <BUS_NAME> \
    --query 'EventPattern'
  # Pattern must contain "source" and "detail-type" fields
  # Pattern must NOT be {} or contain only wildcard matches
  ```
- Trade-offs: Very specific patterns require coordination between producers and consumers on schema. Pattern changes require IaC deployment. Maximum pattern size is 2,048 characters — extremely complex patterns may need decomposition into multiple rules.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html

**KMS Encryption for Sensitive Event Buses**
- Pillar Alignment: Security
- Why: Event data flowing through event buses may contain PII, financial data, or business-sensitive payloads. By default, EventBridge encrypts at rest using AWS-owned keys. For regulated workloads, customer-managed KMS keys (CMKs) provide key rotation control, cross-account access control, CloudTrail audit of key usage, and compliance evidence. CMK encryption also enables DLQ configuration for encryption-related failures.
- AWS Services: Amazon EventBridge (event bus encryption), AWS KMS (customer-managed keys), Amazon SQS (encryption failure DLQ)
- Architecture Decision:
  Enable CMK encryption on all event buses handling PII, PHI, financial data, or regulated workloads. Configure an encryption failure DLQ (SQS standard queue) on the bus to capture events that fail encryption/decryption. Grant EventBridge service principal `kms:Decrypt` and `kms:GenerateDataKey` in the KMS key policy. Note: targets consuming encrypted bus events must have access to the KMS key.
- Verification:
  ```bash
  aws events describe-event-bus --name <BUS_NAME> \
    --query '{KmsKeyId:KmsKeyIdentifier,DLQ:DeadLetterConfig}'
  # KmsKeyId should be set for sensitive buses
  ```
- Trade-offs: CMK encryption adds KMS API call costs ($0.03/10,000 requests). Cross-account consumers need KMS key policy grants. Encryption failures are routed to bus-level DLQ — requires monitoring. Some AWS service events cannot be encrypted with CMK.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-encryption.html

**IAM Execution Roles with Least Privilege on Targets**
- Pillar Alignment: Security
- Why: EventBridge assumes an IAM role to invoke targets (except Lambda, SNS, SQS, and CloudWatch Logs which use resource-based policies). Overly permissive roles (wildcard actions or resources) grant EventBridge — and by extension any matched event — access beyond what the specific target needs. Since March 2023, cross-account event bus targets require IAM roles, enforcing Organization SCPs.
- AWS Services: Amazon EventBridge (rule target RoleArn), AWS IAM (execution roles with trust policy for events.amazonaws.com)
- Architecture Decision:
  Create one IAM role per rule (or per target when targets have different permission needs). The trust policy must allow only `events.amazonaws.com` to assume the role. Permission policies must specify exact actions and resource ARNs — never use `*` for action or resource. Use `aws:SourceArn` condition in the trust policy to restrict which rules can assume the role.
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "events.amazonaws.com" },
      "Action": "sts:AssumeRole",
      "Condition": {
        "ArnLike": { "aws:SourceArn": "arn:aws:events:us-east-1:123456789012:rule/orders-bus/*" }
      }
    }]
  }
  ```
- Verification:
  ```bash
  aws events list-targets-by-rule --rule <RULE_NAME> --event-bus-name <BUS_NAME> \
    --query 'Targets[*].RoleArn'
  # Verify role exists and has minimal permissions via:
  aws iam get-role-policy --role-name <ROLE_NAME> --policy-name <POLICY_NAME>
  ```
- Trade-offs: Per-rule roles increase IAM surface area. Role assumption adds minor latency to target invocation. Managing many roles requires naming conventions and IaC automation.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-use-identity-based.html

**Archive Configuration for Critical Event Buses**
- Pillar Alignment: Reliability, Operational Excellence
- Why: Without archives, historical events are irrecoverable. Archives enable disaster recovery (replay events after target failures), new consumer onboarding (bootstrap a new service with historical events), testing (replay production events in staging), and audit (compliance event retention). Archive is the only mechanism for event replay in EventBridge — DLQs only capture failed events, not successful ones.
- AWS Services: Amazon EventBridge (archives and replay), CloudWatch (archive metrics)
- Architecture Decision:
  Enable archives on all business-critical custom event buses. Use event pattern filtering on archives to store only relevant event types (reduces storage cost). Set retention period based on business requirements (90 days for replay/recovery, 365+ for compliance). Monitor archive size and replay progress via CloudWatch. Design consumers for idempotency — replayed events include `replay-name` metadata.
- Verification:
  ```bash
  aws events list-archives --query 'Archives[*].{Name:ArchiveName,Bus:EventSourceArn,State:State,Retention:RetentionDays}'
  # Critical buses should have at least one archive in ENABLED state
  ```
- Trade-offs: Archive storage costs ($0.023/GB/month — same as S3 Standard). Indefinite retention accumulates cost over time. Replay is not instant — events are replayed in one-minute batches. Maximum 10 concurrent replays per account per Region.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html

---

### ⚠️ Architectural Decisions

**Event Bus vs EventBridge Pipes vs Direct Integration**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Event Bus | EventBridge Event Bus | Fan-out, content-based routing, decoupling, multiple consumers | Ordering, exactly-once, low latency | Multiple consumers need the same events; routing logic is complex |
  | EventBridge Pipes | EventBridge Pipes | Ordered processing, enrichment, stream-to-target integration | Fan-out (single target only), flexibility | Point-to-point from stream/queue to single target with enrichment |
  | Direct Integration | Lambda ESM, SQS→Lambda, SNS→SQS | Simplicity, lower latency, native ordering | Routing flexibility, enrichment, cross-account distribution | Simple source-to-consumer with no routing or transformation |

- Cost Profile: Event Bus: $1.00/M custom events + target invocation costs. Pipes: $0.40/M events processed (64KB chunks). Direct integration: only consumer costs.
- Lock-in Assessment: All options are AWS-native. Event Bus patterns are conceptually portable to other event brokers (Azure Event Grid, GCP Eventarc). Pipes are deeply AWS-integrated.
- Architect Instruction: "Ask whether the event flow is one-to-one (Pipes) or one-to-many (Bus), and whether events arrive via stream/queue (Pipes) or API call (Bus)"
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html

**EventBridge vs SNS for Event Distribution**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | EventBridge | Amazon EventBridge | Content-based routing, schema awareness, archive/replay, cross-account, SaaS integration | Raw throughput (vs SNS unlimited), protocol diversity (no SMS/email/push) | Complex routing logic, event-driven architectures, cross-account distribution |
  | SNS Standard | Amazon SNS | Maximum throughput (unlimited TPS), protocol variety (SQS, Lambda, HTTP, email, SMS, push), simplicity | Content-based routing (limited to attribute filtering), no archive/replay, no schema registry | Simple fan-out, notification delivery, high-throughput pub/sub |
  | SNS FIFO | Amazon SNS FIFO | Ordered delivery, deduplication | Throughput (3,000 msg/s max), only SQS FIFO subscribers | Strict ordering requirements with fan-out |

- Cost Profile: EventBridge: $1.00/M custom events. SNS: $0.50/M publishes + $0/delivery to SQS (same region). EventBridge is 2x the per-event cost of SNS for simple fan-out.
- Lock-in Assessment: Both are AWS-native. EventBridge event patterns are more portable (JSON content matching). SNS message filtering is simpler but less powerful.
- Architect Instruction: "Ask whether routing decisions depend on event content (EventBridge) or simple topic subscription (SNS), and whether archive/replay is required"
- Source: https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html

**Single Bus vs Multi-Bus Topology**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Single Custom Bus | One EventBridge custom bus | Simplicity, fewer resources, easier discovery | Access control granularity, blast radius isolation, per-domain archives | Small teams, few event types, single domain |
  | Multi-Bus (per domain) | Multiple custom buses | Security isolation, independent access policies, per-domain archives/monitoring | Cross-domain routing complexity (requires bus-to-bus rules), more IaC | Multiple teams, distinct domains, regulatory boundaries |
  | Multi-Bus (per account) | Custom buses across accounts | Account-level isolation, SCP enforcement, billing separation | Cross-account IAM complexity, event replication cost | Enterprise multi-account strategy (Organizations) |

- Cost Profile: No per-bus cost — only per-event cost. Multi-bus adds cross-bus event forwarding cost ($1.00/M forwarded events).
- Lock-in Assessment: Bus topology is an organizational decision — portable to any event broker that supports namespacing/topics.
- Architect Instruction: "Ask how many teams produce events, whether domains have different security requirements, and whether cross-account distribution is needed"
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus.html

**Global Endpoints vs Cross-Region Rules vs Application-Level Failover**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Global Endpoints | EventBridge Global Endpoints + Route 53 | Automated failover, zero publisher code changes, managed health checks | Only custom events, requires identical buses/rules in both Regions, 360s RTO | Mission-critical event flows requiring automatic Regional failover |
  | Cross-Region Rules | EventBridge rules targeting buses in other Regions | Active-active event processing, both Regions always receive events | Double processing cost, publisher sends to one Region only, manual failover | Active-active architectures where both Regions process all events |
  | Application-Level | Custom failover logic in publisher code | Full control, works with any event type, immediate failover | Complexity, code maintenance, testing burden | Non-standard failover requirements, custom health criteria |

- Cost Profile: Global Endpoints: no additional cost (event replication costs apply if enabled). Cross-Region Rules: $1.00/M forwarded events. Application-Level: development + maintenance cost.
- Lock-in Assessment: Global Endpoints are EventBridge-specific. Application-level failover is portable.
- Architect Instruction: "Ask whether only custom events need multi-region, what the acceptable RTO is, and whether both Regions should always process events"
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-global-endpoints.html

**Scheduler vs Scheduled Rules vs CloudWatch Events (Legacy)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | EventBridge Scheduler | EventBridge Scheduler | Scale (10M+ schedules), universal targets, flexible time windows, retry/DLQ, one-time schedules | Must migrate from legacy rules | ALL new time-based invocations (recommended) |
  | Scheduled Rules (Legacy) | EventBridge scheduled rules on bus | Simplicity for existing deployments | Limited targets, no DLQ, no flexible time windows, max 300 rules/bus shared with event rules | Existing deployments not yet migrated |
  | Cron Lambda | CloudWatch Events + Lambda (self-scheduled) | Full flexibility, custom logic | Operational overhead, cold starts, no managed retry | Complex scheduling logic requiring custom code |

- Cost Profile: Scheduler: $1.00/M invocations (first 14M free). Scheduled Rules: included in bus limits (no separate charge). Cron Lambda: Lambda invocation costs.
- Lock-in Assessment: Scheduler is AWS-specific. Cron expressions are portable.
- Architect Instruction: "Use EventBridge Scheduler for all new schedules. Only keep legacy scheduled rules if migration risk outweighs benefit."
- Source: https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html

---

### 🚫 Anti-Patterns

**Empty or Overly Broad Event Patterns**
- Risk Level: CRITICAL
- Why: A rule with pattern `{}` matches EVERY event on the bus — including AWS service events on the default bus. This causes cost explosions (every event triggers target invocation), potential infinite loops (target produces events that re-match the rule), and security risks (processing untrusted events). Even patterns matching only `source` without `detail-type` are dangerously broad.
- Instead:
  Always specify both `"source"` and `"detail-type"` in event patterns. Add `detail` field filters for further specificity. Use the EventBridge Sandbox to validate pattern match scope before deployment.
- Detection:
  ```bash
  aws events list-rules --event-bus-name <BUS_NAME> \
    --query 'Rules[*].{Name:Name,Pattern:EventPattern}' | \
    jq '.[] | select(.Pattern == "{}" or (.Pattern | fromjson | has("source") | not))'
  ```
- Impact: Cost overrun | Service outage (throttling) | Infinite loop | Security violation
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-patterns-best-practices.html

**Publishing Application Events to the Default Bus**
- Risk Level: HIGH
- Why: The default bus receives all AWS service events. Publishing application events there mixes trusted AWS service events with custom events, makes it impossible to apply domain-specific access policies, prevents cross-account sharing (default bus cannot be shared), and causes rules to potentially match unintended AWS service events. It also blocks independent archive/replay per domain.
- Instead:
  Create custom event buses per domain/bounded context. Publish all application events to custom buses. Reserve the default bus exclusively for AWS service event routing.
- Detection:
  ```bash
  # Check for PutEvents calls to default bus from application code
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=PutEvents \
    --query 'Events[?contains(CloudTrailEvent, `"eventBusName":"default"`)]'
  ```
- Impact: Security violation | Operational confusion | Inability to share events cross-account
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus.html

**Rules Without Dead-Letter Queues**
- Risk Level: HIGH
- Why: Without DLQs, failed event deliveries are silently lost after retry exhaustion. The only indicators are CloudWatch FailedInvocations metrics — but the original events are irrecoverable. This violates the Reliability pillar's requirement for automatic failure recovery. Permission errors, non-existent targets, and throttling all result in permanent event loss.
- Instead:
  Configure `DeadLetterConfig` on every target in every rule. Use standard SQS queues with 14-day retention. Set CloudWatch alarms on DLQ depth (ApproximateNumberOfMessagesVisible > 0). Implement automated or manual DLQ processing pipelines.
- Detection:
  ```bash
  aws events list-targets-by-rule --rule <RULE_NAME> --event-bus-name <BUS_NAME> \
    --query 'Targets[?DeadLetterConfig.Arn==`null`].Id'
  # Any non-empty result indicates targets without DLQs
  ```
- Impact: Data loss | Irrecoverable failures | Compliance violations
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html

**Wildcard Principal in Event Bus Resource Policy**
- Risk Level: CRITICAL
- Why: An event bus resource policy with `"Principal": "*"` and no restrictive conditions allows ANY AWS account to publish events to your bus. This enables event injection (malicious events matching your rules and invoking your targets), denial-of-wallet attacks (flooding your bus with events to incur costs), and data exfiltration (crafting events that trigger targets delivering data externally).
- Instead:
  Always restrict `events:PutEvents` to specific account IDs, Organization IDs (`aws:PrincipalOrgID`), or specific principal ARNs. Use conditions like `aws:SourceAccount`, `aws:SourceArn`, or `aws:PrincipalOrgID` to constrain access.
  ```json
  {
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::111122223333:root" },
    "Action": "events:PutEvents",
    "Resource": "arn:aws:events:us-east-1:444455556666:event-bus/orders-bus",
    "Condition": {
      "StringEquals": { "aws:PrincipalOrgID": "o-example12345" }
    }
  }
  ```
- Detection:
  ```bash
  aws events describe-event-bus --name <BUS_NAME> --query 'Policy' | \
    jq 'fromjson | .Statement[] | select(.Principal == "*" and (.Condition == null))'
  ```
- Impact: Event injection | Denial-of-wallet attack | Data exfiltration | Compliance violation
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus-perms.html

**Infinite Loop Rules (Rule Output Matches Own Input)**
- Risk Level: CRITICAL
- Why: If a rule's target produces an event that matches the same rule's pattern (or another rule on the same bus), it creates an infinite loop. EventBridge processes events recursively without built-in loop detection (beyond the 5-target limit per rule). This results in exponential cost growth and potential service throttling. Common scenario: S3 → EventBridge → Lambda → writes to S3 → EventBridge → Lambda → infinite.
- Instead:
  Design event patterns that cannot match their own target's output. Add discriminating fields (e.g., `"status": ["UNPROCESSED"]`) that the target changes (to `"PROCESSED"`) in its output. Use separate event buses for input and output when both must be events. Review event patterns for potential circular matches during design review.
- Detection:
  Monitor CloudWatch metrics: sudden spike in `Invocations`, `MatchedEvents`, or `TriggeredRules` indicates potential loop. Set CloudWatch alarm on invocation rate exceeding expected baseline by 10x.
- Impact: Cost explosion | Service throttling | Target resource exhaustion | Account suspension
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rules-best-practices.html

**Using Legacy Scheduled Rules for New Workloads**
- Risk Level: MEDIUM
- Why: Legacy scheduled rules share the 300-rule-per-bus quota with event pattern rules, lack DLQ support, lack flexible time windows, support fewer target types, and cannot create one-time schedules. They are effectively deprecated in favor of EventBridge Scheduler which addresses all these limitations with dedicated scalability (10M+ schedules).
- Instead:
  Use EventBridge Scheduler for all new time-based invocations. Migrate existing scheduled rules to Scheduler incrementally. Scheduler supports cron, rate, and one-time schedules with full retry policy, DLQ, and universal target support.
- Detection:
  ```bash
  aws events list-rules --event-bus-name default \
    --query 'Rules[?ScheduleExpression!=`null`].{Name:Name,Schedule:ScheduleExpression}'
  # Any results indicate legacy scheduled rules that should be migrated
  ```
- Impact: Operational limitation | Shared quota exhaustion | Missing failure handling
- Source: https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html

**Not Filtering Events in Archives**
- Risk Level: MEDIUM
- Why: Archives without event pattern filters store ALL events from the bus — including high-volume, low-value operational events. This creates unnecessary storage cost accumulation, makes replay operations slower (more events to process), and may store sensitive events that should not be retained long-term.
- Instead:
  Configure event pattern filters on archives to store only business-significant events. Set appropriate retention periods (not indefinite). Create multiple archives with different retention policies for different event types if needed.
- Detection:
  ```bash
  aws events describe-archive --archive-name <ARCHIVE_NAME> \
    --query '{Pattern:EventPattern,Retention:RetentionDays}'
  # EventPattern should not be null/empty; RetentionDays should not be 0 (indefinite)
  ```
- Impact: Cost overrun | Compliance risk (storing data beyond retention policy) | Slow replays
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html

---

## Cloud-Native Design Patterns

**Event-Driven Fan-Out via Event Bus**
- Category: Communication
- Problem: A single domain event (e.g., "Order Placed") needs to trigger multiple independent downstream processes (send confirmation email, reserve inventory, initiate payment, update analytics) without the producer knowing about or coupling to consumers.
- Solution on AWS:
  Publisher sends event to custom event bus via PutEvents. Multiple rules on the bus match the event based on `source` + `detail-type`. Each rule routes to a different target (Lambda for email, SQS for inventory, Step Functions for payment workflow, Firehose for analytics). Consumers operate independently at their own pace.
- Services Used: EventBridge (custom bus + rules), Lambda, SQS, Step Functions, Firehose
- When to Apply: Multiple independent consumers need the same event; producer-consumer decoupling is required; consumers should be addable/removable without producer changes.
- When NOT to Apply: Single consumer only (use Pipes or direct integration); strict ordering required (use Pipes from Kinesis/DynamoDB stream); high-throughput simple fan-out without content filtering (use SNS).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Coupling | Producers fully decoupled from consumers | Event schema becomes a shared contract |
  | Scalability | Each consumer scales independently | Target throttling requires per-target DLQ handling |
  | Ordering | Parallel processing maximizes throughput | No ordering guarantees between targets |
  | Observability | Per-rule metrics enable targeted monitoring | Distributed tracing requires correlation IDs |

- Complements: Schema Registry (contract management), Archive/Replay (consumer bootstrapping), DLQ (failure recovery)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus.html

**Content-Based Routing**
- Category: Communication
- Problem: Different event instances of the same type require routing to different consumers based on event content (e.g., orders from different regions routed to different fulfillment systems; high-priority events routed to express processing).
- Solution on AWS:
  Publish all events to a single custom bus with discriminating fields in the `detail` payload. Create multiple rules with event patterns matching on `detail` fields (e.g., `"detail": {"region": ["us-east-1"]}` routes to US fulfillment; `"detail": {"priority": ["HIGH"]}` routes to express lane). Each rule targets the appropriate consumer.
- Services Used: EventBridge (custom bus + multiple rules with specific patterns), Lambda/SQS/Step Functions (targets)
- When to Apply: Same event type has multiple processing paths based on content; routing logic should be infrastructure-managed (not application code); new routes should be addable without code changes.
- When NOT to Apply: All events of a type go to the same consumer (no routing needed); routing logic requires complex computation (use Lambda router instead); routing needs stateful decisions (use Step Functions).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Flexibility | Add new routes via IaC without code changes | Event pattern complexity grows with routes |
  | Maintainability | Routing logic visible in infrastructure | Pattern debugging requires EventBridge Sandbox |
  | Performance | Zero-latency content evaluation at bus level | 2,048 char pattern limit constrains complexity |

- Complements: Input Transformer (reshape event per target), Schema Registry (validate routing fields exist)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html

**Stream-to-Service Integration via Pipes**
- Category: Data
- Problem: Events arrive on a streaming source (DynamoDB Streams, Kinesis, SQS, Kafka) and need to be processed by a target service with optional filtering, enrichment (e.g., API lookup), and transformation — maintaining source ordering.
- Solution on AWS:
  Create an EventBridge Pipe with the stream as source. Configure filtering to process only relevant records (e.g., INSERT events from DynamoDB, not REMOVE). Add enrichment step (Lambda function that calls an API to augment the event data). Define target (Step Functions, Lambda, EventBridge bus, API destination). Pipe maintains ordering within DynamoDB partition keys / Kinesis shard IDs.
- Services Used: EventBridge Pipes, DynamoDB Streams/Kinesis/SQS/MSK (source), Lambda/API Gateway/Step Functions (enrichment), any supported target
- When to Apply: Point-to-point stream processing; enrichment needed before target delivery; ordering within partition/shard is required; want to avoid writing Lambda ESM boilerplate for filter/enrich/route.
- When NOT to Apply: Need fan-out to multiple consumers (use Pipe → Event Bus → Rules); need complex stateful processing (use Step Functions directly); need sub-second latency (Pipes add enrichment latency).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Simplicity | No custom Lambda code for filter/enrich/route | Single target limit requires bus for fan-out |
  | Ordering | Maintains source ordering within partition | Cross-partition ordering not guaranteed |
  | Cost | $0.40/M events vs Lambda invocation costs | Enrichment step adds per-invocation cost |

- Complements: Event Bus (fan-out from pipe target), DLQ (failed delivery capture)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html

**Event Sourcing with Archive and Replay**
- Category: Data
- Problem: Need to reconstruct application state from historical events, bootstrap new consumers with historical data, or reprocess events after fixing a bug in consumer logic.
- Solution on AWS:
  Enable archives on the event bus with appropriate event pattern filters and retention. When replay is needed: create a replay specifying the time range and optionally specific rules to target. Replayed events include `replay-name` metadata — consumers detect and handle accordingly (e.g., skip notifications during replay, only rebuild state). Consumers must be idempotent.
- Services Used: EventBridge (archive + replay), SQS/Lambda/Step Functions (idempotent consumers)
- When to Apply: Event-sourced architectures; new consumer onboarding; disaster recovery; bug-fix reprocessing; compliance replay requirements.
- When NOT to Apply: Need real-time ordered event log (use Kinesis); need transaction-level event store (use DynamoDB + custom event store); events contain time-sensitive data that becomes stale (e.g., pricing quotes).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Recovery | Full event history available for replay | Archive storage accumulates cost |
  | Flexibility | Replay to specific rules, specific time ranges | Events not replayed in strict order (1-min batches) |
  | Development | Consumers can be restarted with history | Consumers MUST be idempotent for replay safety |

- Complements: DLQ (capture failures during replay), Schema Registry (validate replayed event compatibility)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html

**Cross-Account Event Hub Pattern**
- Category: Communication
- Problem: In a multi-account AWS Organization, domain events produced in one account need to be consumed by services in other accounts without tight coupling or point-to-point integrations between accounts.
- Solution on AWS:
  Create a "central event hub" custom event bus in a shared-services account. Configure resource-based policy to allow PutEvents from Organization accounts (using `aws:PrincipalOrgID` condition). Each producing account creates rules on their local bus forwarding events to the central hub bus (cross-account target). Consuming accounts either: (a) create rules on the central hub routing to their local buses, or (b) are granted permissions to receive forwarded events. SCPs enforce Organization-level access controls.
- Services Used: EventBridge (custom buses in multiple accounts), IAM (resource policies, execution roles), AWS Organizations (SCPs, OrgID conditions)
- When to Apply: Multi-account enterprise architecture; need centralized event observability; consumer accounts should not be aware of producer accounts; compliance requires centralized audit of event flows.
- When NOT to Apply: Single-account architecture; only 2 accounts need event sharing (direct cross-account rule is simpler); strict latency requirements (cross-account adds ~100ms).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Governance | Centralized event catalog and access control | Central bus is a single point of failure (mitigate with archives) |
  | Decoupling | Producers/consumers unaware of each other | Cross-account IAM complexity |
  | Cost | Single-point monitoring and billing visibility | Event forwarding charges ($1.00/M per hop) |

- Complements: Schema Registry (centralized event catalog), Global Endpoints (multi-region hub), CloudTrail (audit cross-account flows)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html

**Saga Orchestration with EventBridge and Step Functions**
- Category: Resilience
- Problem: A distributed transaction spans multiple services (e.g., place order → reserve inventory → charge payment → ship). Each step can fail, requiring compensating transactions to maintain consistency.
- Solution on AWS:
  Step Functions orchestrates the saga — each step invokes a service (Lambda, ECS task, API). On success, Step Functions emits events to EventBridge for notification/audit. On failure, Step Functions executes compensating transactions (release inventory, refund payment) and emits failure events to EventBridge. EventBridge distributes outcome events to interested consumers (notifications, analytics, monitoring).
- Services Used: Step Functions (orchestrator), EventBridge (event distribution), Lambda (individual saga steps), SQS/DLQ (failure capture)
- When to Apply: Multi-step business processes with compensating transactions; need visibility into transaction progress; failure of one step requires rollback of previous steps.
- When NOT to Apply: Simple two-step transactions (use direct Lambda invocation); all steps are in the same database (use DB transactions); choreography pattern preferred (use EventBridge rules chaining services without orchestrator).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Consistency | Guaranteed compensation on failure | Step Functions adds per-state-transition cost |
  | Visibility | Full execution history in Step Functions | Debugging distributed state across services |
  | Coupling | Services only know their own step | Orchestrator contains workflow logic |

- Complements: DLQ (capture failed compensations), CloudWatch (saga duration/failure metrics)
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-best-practices.html

---

## Security Architecture

**Event Bus Access Control**
- AWS Services: EventBridge (resource-based policies), IAM (identity-based policies), AWS Organizations (SCPs)
- Architecture:
  Resource-based policies on event buses control WHO can publish/receive events. Identity-based policies on publisher IAM roles control WHICH buses they can publish to. SCPs at the Organization level enforce cross-account boundaries. For cross-account event routing (mandatory since March 2023), both the bus resource policy AND the sender's IAM role must allow the action.
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "AllowOrgAccountsPublish",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "events:PutEvents",
      "Resource": "arn:aws:events:us-east-1:ACCOUNT:event-bus/orders-bus",
      "Condition": {
        "StringEquals": { "aws:PrincipalOrgID": "o-org123" }
      }
    }]
  }
  ```
- Compliance Alignment: SOC2 CC6.1 (logical access), PCI-DSS 7.1 (restrict access), HIPAA 164.312(a) (access control)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus-perms.html

**Event Encryption (At-Rest and In-Transit)**
- AWS Services: EventBridge (KMS encryption on bus), AWS KMS (customer-managed keys), SQS (encrypted DLQ for encryption failures)
- Architecture:
  In-transit: All EventBridge API calls use TLS 1.2+ (mandatory). At-rest: Default encryption uses AWS-owned keys. For regulated workloads, configure customer-managed KMS keys on the event bus. When CMK encryption is enabled, EventBridge encrypts events stored transiently during rule evaluation and in archives. Targets consuming encrypted events need `kms:Decrypt` permission on the bus CMK. Configure bus-level DLQ to capture events that fail encryption/decryption.
- Compliance Alignment: SOC2 CC6.7 (encryption), PCI-DSS 3.4 (data at rest), HIPAA 164.312(a)(2)(iv) (encryption)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-encryption.html

**Audit and Monitoring**
- AWS Services: AWS CloudTrail (API audit), Amazon CloudWatch (metrics and alarms), EventBridge (delivery metrics)
- Architecture:
  CloudTrail logs all EventBridge control-plane API calls (CreateRule, PutTargets, PutPermission, etc.) and optionally data-plane calls (PutEvents). CloudWatch metrics per event bus: `Invocations`, `FailedInvocations`, `MatchedEvents`, `TriggeredRules`, `ThrottledRules`, `InvocationsSentToDLQ`, `InvocationsFailedToBeSentToDLQ`. Set alarms on `FailedInvocations > 0`, `ThrottledRules > 0`, and DLQ depth. Enable CloudTrail data events for buses handling sensitive data to audit who published what.
- Compliance Alignment: SOC2 CC7.2 (monitoring), PCI-DSS 10.1 (audit trails), HIPAA 164.312(b) (audit controls)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-logging-monitoring.html

---

## Operational Patterns

**Observability for Event-Driven Architectures**
- RTO/RPO: N/A (monitoring pattern)
- AWS Services: Amazon CloudWatch (Metrics, Logs, Alarms, Dashboards), AWS X-Ray (distributed tracing), EventBridge (native metrics)
- Cost Profile: Low — CloudWatch metrics are included; Logs ingestion $0.50/GB; X-Ray $5.00/M traces sampled.
- Automation:
  Auto-create CloudWatch dashboards per event bus (IaC). Alarm on FailedInvocations, ThrottledRules, DLQ depth. Use X-Ray with Lambda targets for end-to-end trace correlation (pass trace header in event detail). Create composite alarms for multi-bus architectures.
- Runbook Skeleton:
  1. Detection: CloudWatch alarm fires on FailedInvocations > threshold
  2. Triage: Check DLQ messages for ERROR_CODE and TARGET_ARN
  3. Diagnosis: Verify target exists, IAM role permissions, target quotas
  4. Resolution: Fix target issue; replay DLQ messages (Lambda-driven or manual)
  5. Post-mortem: Identify root cause; update alarms/thresholds if needed
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-monitoring.html

**Multi-Region Disaster Recovery with Global Endpoints**
- RTO/RPO: RTO 360 seconds (max 420s) / RPO 360 seconds (events in-flight during failover window)
- AWS Services: EventBridge (Global Endpoints), Amazon Route 53 (health checks), CloudWatch (alarm for health check)
- Cost Profile: Medium — no additional cost for global endpoints; event replication doubles per-event cost for replicated events; Route 53 health check $0.50/month.
- Automation:
  Create CloudWatch alarm monitoring secondary Region health. Route 53 health check monitors the alarm. When alarm transitions to ALARM state, Route 53 fails over PutEvents routing to secondary Region. Event replication (recommended) ensures secondary Region already has all events for consistency verification. Recovery is automatic when health check returns HEALTHY.
- Runbook Skeleton:
  1. Detection: Route 53 health check transitions to unhealthy (CloudWatch alarm fires)
  2. Automatic failover: Events route to secondary Region within 360 seconds
  3. Validation: Verify secondary Region processing events (CloudWatch Invocations metric)
  4. Recovery: Resolve primary Region issue; health check returns healthy; traffic shifts back
  5. Post-mortem: Analyze events lost during failover window; replay from archive if needed
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-global-endpoints.html

**Event Replay for Recovery**
- RTO/RPO: RTO Minutes–Hours (depends on replay volume) / RPO Near-zero (archive captures all events)
- AWS Services: EventBridge (Archive, Replay), CloudWatch (replay progress metrics)
- Cost Profile: Low — archive storage $0.023/GB/month; replay is free (events replayed against PutEvents quota).
- Automation:
  Enable archive on critical buses with event pattern filter. When recovery is needed: create replay with specific time window. Monitor replay progress via `DescribeReplay` API (`EventLastReplayedTime`). Consumers must detect `replay-name` field in replayed events to skip side effects (e.g., don't re-send notifications). Allow 10 minutes after archive write before replay to ensure completeness.
- Runbook Skeleton:
  1. Detection: Consumer failure identified (DLQ depth, missing data in downstream system)
  2. Scope: Determine time window of affected events
  3. Prepare: Ensure consumers handle replay (idempotency check, skip notifications)
  4. Execute: Create replay with time window (optionally target specific rules)
  5. Monitor: Track replay progress; verify downstream systems received events
  6. Post-mortem: Root cause consumer failure; improve DLQ processing automation
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html

---

## Reference Architectures

**Event-Driven Microservices with EventBridge**
- Context: Microservices architecture where services communicate asynchronously via domain events
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Event Routing | EventBridge Custom Bus | Domain event routing with content-based filtering |
  | Event Schema | EventBridge Schema Registry | Event contract management and code generation |
  | Compute | AWS Lambda | Event-driven microservice handlers |
  | Orchestration | AWS Step Functions | Complex multi-step business workflows |
  | Queue Buffer | Amazon SQS | Rate leveling between EventBridge and consumers |
  | State Store | Amazon DynamoDB | Service-local state persistence |
  | Archive | EventBridge Archive | Event history for replay and recovery |
  | DLQ | Amazon SQS | Failed event capture and reprocessing |
  | Monitoring | CloudWatch + X-Ray | Observability and distributed tracing |

- Key Decisions: Bus topology (per-domain vs shared); event schema versioning strategy; sync vs async communication boundaries; error handling (DLQ vs retry vs circuit breaker).
- Scaling Path: Start with single bus → multi-bus per domain → cross-account hub as teams grow. Start with Lambda → add SQS buffer → migrate to containers (ECS/Fargate) for high-throughput consumers.
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/welcome.html

**SaaS Integration Hub**
- Context: Application integrating with multiple SaaS providers (Salesforce, Zendesk, Shopify) via events
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | SaaS Ingestion | EventBridge Partner Event Sources | Receive events from SaaS providers |
  | Custom Ingestion | API Gateway + Lambda | Webhook receiver for SaaS without native EB integration |
  | Event Routing | EventBridge Custom Bus | Route SaaS events to appropriate handlers |
  | Outbound | EventBridge API Destinations | Push events to external SaaS APIs |
  | Auth | EventBridge Connections | OAuth/API key management for API destinations |
  | Transform | EventBridge Input Transformers | Reshape events for target API formats |
  | Retry/DLQ | SQS | Capture failed outbound deliveries |
  | Monitoring | CloudWatch | Track SaaS integration health |

- Key Decisions: Which SaaS partners have native EventBridge integration vs require webhook adapters; rate limiting for outbound API destinations; retry strategy for third-party API failures; credential rotation strategy for Connections.
- Scaling Path: Start with partner event sources → add custom webhook adapters → add bidirectional integrations via API destinations → add event transformation logic → add multi-tenant routing.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-saas.html

---

## Service Equivalence Map

| Category | AWS EventBridge | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----------------|-------------|-------|--------------------|
| **Event Bus / Router** | EventBridge Event Buses | Eventarc | Event Grid | OCI Events |
| **Event Filtering** | Event Patterns (JSON DSL) | Eventarc Filters | Event Grid Filters | OCI Events Rules |
| **Point-to-Point Pipes** | EventBridge Pipes | — (Cloud Functions direct trigger) | — (Service Bus + Functions) | — (Service Connector Hub) |
| **Scheduler** | EventBridge Scheduler | Cloud Scheduler | Logic Apps Recurrence | OCI Resource Scheduler |
| **Schema Registry** | EventBridge Schema Registry | — (manual) | Event Grid Schema Registry | — (manual) |
| **Archive / Replay** | EventBridge Archive & Replay | — (manual via Pub/Sub + Storage) | Event Grid Dead-Letter + Storage | — (manual via Streaming + Object Storage) |
| **Cross-Account** | Event Bus resource policies + IAM | Cross-project Eventarc | Event Grid Domains + RBAC | Cross-compartment OCI Events |
| **Multi-Region** | Global Endpoints | — (manual) | Event Grid Geo DR | — (manual) |
| **SaaS Integration** | Partner Event Sources | — (Eventarc for GCP services) | Event Grid Partner Topics | — (limited) |
| **API Destinations** | EventBridge API Destinations | — (Cloud Functions webhook) | Event Grid Webhook Subscriptions | — (Functions webhook) |

> **⚠️ Important**: EventBridge's unique combination of content-based routing (event patterns), schema registry, archive/replay, global endpoints, and native SaaS integration has no single equivalent in other providers. Azure Event Grid is closest in concept but differs significantly in filtering capabilities and multi-region support.

---

## Provider Differentiators

**EventBridge Event Patterns (Content-Based Routing DSL)**
- Category: Integration
- Unique Value: JSON-based domain-specific language for content-based event filtering that evaluates at the infrastructure level without custom code. Supports exact matching, prefix/suffix/wildcard, numeric comparisons, exists/not-exists, anything-but, and $or operators — all within a declarative JSON structure evaluated at ingestion time.
- Architecture Impact: Eliminates the need for filtering Lambda functions between event source and consumers. Routing decisions are infrastructure-managed and IaC-deployable.
- When to Leverage: Any event-driven architecture where routing decisions depend on event content rather than just event source/type.
- Caveat: Maximum pattern size 2,048 characters. Rules with wildcards limited to 30 per bus. Complex patterns can be difficult to debug (use Sandbox).
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html

**Archive and Replay**
- Category: Data
- Unique Value: Native, managed event archiving with time-range replay directly to the source event bus. No other cloud provider offers built-in event replay at the event router level. Enables event sourcing patterns without custom infrastructure.
- Architecture Impact: Eliminates the need for custom event store + replay infrastructure. Enables safe consumer re-bootstrapping, disaster recovery, and bug-fix reprocessing with a single API call.
- When to Leverage: Event-driven systems requiring replay capability; new consumer onboarding; disaster recovery; integration testing with production event shapes.
- Caveat: Events replayed in 1-minute batches (not strict order). Maximum 10 concurrent replays. Replay targets the source bus only (cannot redirect to a different bus). Archive storage incurs cost.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html

**Global Endpoints (Multi-Region Automatic Failover)**
- Category: Reliability
- Unique Value: Managed multi-region event routing with automatic failover based on Route 53 health checks. No other cloud provider offers built-in multi-region event failover at the event bus level. Publishers use a single endpoint — failover is transparent.
- Architecture Impact: Enables multi-region event-driven architectures without custom failover code or DNS manipulation in publishers. RTO/RPO ~360 seconds.
- When to Leverage: Mission-critical event flows where Regional failure must not stop event processing; global applications requiring event continuity across Regions.
- Caveat: Custom events only (not AWS service events). Requires identical bus/rule setup in both Regions. Requires SigV4A support (AWS CRT library). Limited to 100 endpoints per account per Region.
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-global-endpoints.html

**EventBridge Pipes (Managed Stream Processing)**
- Category: Integration
- Unique Value: Zero-code point-to-point integrations from streaming sources (DynamoDB Streams, Kinesis, SQS, Kafka) to targets with built-in filtering, enrichment, and transformation — maintaining source ordering. Eliminates Lambda ESM boilerplate for filter→enrich→route patterns.
- Architecture Impact: Reduces Lambda functions needed for stream processing. Maintains ordering guarantees from source through to target. Enrichment step enables event augmentation without custom orchestration.
- When to Leverage: Stream-to-service integration where filtering, enrichment, or transformation is needed; replacing Lambda ESM code that only filters/transforms/routes.
- Caveat: Single source, single target per pipe. For fan-out, pipe must target an event bus. Maximum 1,000 pipes per account. Concurrent executions limited (1,000–3,000 depending on Region).
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html

---

## Scenario Coverage

**Standard Case**: Event-driven microservices with domain event routing
- Approach: Custom event bus per domain → rules with specific event patterns (source + detail-type) → Lambda/SQS/Step Functions targets with DLQs → Schema Registry for contracts → Archives for replay capability.
- Key Decisions: Bus topology (per-domain recommended); schema versioning strategy (backward-compatible additions); error handling (DLQ + automated reprocessing vs manual intervention); when to use Pipes vs Bus.

**Edge Case**: Multi-region active-active event processing with eventual consistency
- Approach: Global Endpoints with event replication enabled → identical buses/rules/targets in both Regions → consumers designed for idempotency (deduplication via event ID) → archives in both Regions for independent replay → CloudWatch composite alarms for failover triggers.
- Key Decisions: Accept ~360s RTO/RPO; consumers must handle duplicate events from replication; decide between active-passive (failover only) vs active-active (both Regions always process); database replication strategy must align with event processing strategy.

**Anti-Pattern Case**: Team proposes publishing all events to the default bus with broad pattern matching
- Clarification: Ask: "Why the default bus instead of custom buses?" Default bus receives all AWS service events — mixing with application events prevents security isolation, blocks cross-account sharing, and creates broad-match risks. Require: custom bus per domain, specific patterns (source + detail-type minimum), DLQ on every target, IAM execution roles with least privilege. Refuse: deploying rules with empty patterns {} or patterns missing source/detail-type fields.

---

## Quotas Reference (Key Limits)

| Resource | Default Quota | Adjustable | Notes |
|----------|---------------|------------|-------|
| Event buses per account per Region | 100 | Yes | Includes default + custom + partner |
| Rules per event bus | 300 (most Regions) | Yes | Shared between event pattern and scheduled rules |
| Targets per rule | 5 | No | Hard limit — use multiple rules for more targets |
| PutEvents TPS | 10,000 (us-east-1/us-west-2/eu-west-1) | Yes | 400–2,400 in other Regions |
| PutEvents entries per request | 10 | No | Batch up to 10 events per API call |
| Event size | 256 KB | No | Hard limit per event |
| Event pattern size | 2,048 characters | Yes | Constrains pattern complexity |
| Invocations TPS | 18,750 (us-east-1/us-west-2/eu-west-1) | Yes | Target invocation rate limit |
| API destinations per account | 3,000 | Yes | Per Region |
| API destination invocation rate | 300/second | Yes | Per destination endpoint |
| Connections per account | 3,000 | Yes | Per Region |
| Pipes per account | 1,000 | No (contact support) | Per Region |
| Concurrent pipe executions | 1,000–3,000 | No (contact support) | Region-dependent |
| Archives per account | — | — | No explicit limit documented |
| Concurrent replays | 10 | No | Per account per Region |
| Global endpoints per account | 100 | Yes | Per Region |
| Schema discoverers | 10 | Yes | Per Region |
| Schemas per registry | 100 | Yes | Per Region (except discovered registry: 200) |
| Scheduler schedules per account | 10,000,000+ | Yes | Per Region |
| Scheduler TPS (CreateSchedule) | 5,000 | Yes | Per Region |
| Rules with wildcards per bus | 30 | No | Hard limit |

- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-quota.html
