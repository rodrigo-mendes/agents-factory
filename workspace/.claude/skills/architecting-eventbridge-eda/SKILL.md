---
name: architecting-eventbridge-eda
description: "Designs and implements AWS EventBridge event-driven architectures covering event buses, Pipes, Scheduler, and Schema Registry. Use when building EDA patterns on AWS with EventBridge as the routing backbone — fan-out, choreography sagas, point-to-point integrations, or time-triggered workloads."
---

## Function

Specialist in AWS EventBridge Event-Driven Architecture (EDA): content-based routing, fan-out, saga choreography, point-to-point stream integration (EventBridge Pipes), time-based invocation (EventBridge Scheduler), schema governance, and reliability patterns for AWS serverless workloads.

## Version Context

**Technology/Framework**: Amazon EventBridge
**Target edition**: AWS EventBridge 2026
**Research date**: 2026-08-28
**Support status**: Active

**Important changes (2024–2026)**:
- CMK at-rest encryption: event buses (GA 2024-05), archives/replay (2025-04), filter patterns and input transformers (2025-09-17)
- Enhanced logging to CloudWatch Logs, S3, and Data Firehose (GA 2025-07)
- SQS fair-queue targets and enhanced visual rule builder across 200+ service event catalog (2025-11)
- PutEvents request size is now **1 MB (1,048,576 bytes)** — the widely cited 256 KB figure is superseded misinformation
- `$or` cross-field filter operator GA; combined `anything-but` with prefix/suffix/wildcard (2024-05)

**Deprecated**: Scheduled event-bus rules — AWS labels these a "legacy feature"; use EventBridge Scheduler for all new time-based workloads.

**Key primitives**:

| Primitive | Purpose | Max Scale |
|-----------|---------|-----------|
| Event Bus + Rules | Many-to-many content-based routing | 100 buses/Region, 300 rules/bus, 10,000 TPS |
| EventBridge Pipes | 1:1 source→filter→enrich→target | 3,000 concurrent executions |
| EventBridge Scheduler | Time-triggered, 270+ targets, 6,000+ API ops | 10,000,000 schedules/Region |
| Schema Registry | Discovery, versioning, typed code bindings | 5M events/month free discovery tier |

⚠️ **CRITICAL — Agent Warning**:
This skill targets AWS EventBridge 2026. Reject the 256 KB PutEvents limit (superseded by 1 MB). Do not recommend scheduled rules for new time-based workloads. Lambda and Step Functions bus targets are invoked ASYNCHRONOUSLY — never design for synchronous return from a bus target.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 patterns (read first)
- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 6 mandatory patterns with verification commands
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural decision matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 6 anti-patterns with ❌/✅ examples
- **[Integration Patterns](#integration-patterns)** — Cross-service integration summary
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 5 test cases
- **[Verification Loop](#verification-loop)** — CLI validation commands
- **[Quick Reference](#quick-reference)** — Limits, costs, and essential commands
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For full patterns with code examples and verification commands see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **Attach a standard SQS DLQ and explicit retry policy to every production target** — Exhausted retries drop events silently. Permanent errors (missing permissions, deleted target, DNS failure) skip retry entirely and go straight to the DLQ — or are lost if no DLQ exists. Set `MaximumRetryAttempts` (0–185) and `MaximumEventAgeInSeconds` (60–86400) explicitly; never rely on the 24h/185 default. FIFO queues are NOT supported as DLQs. Alarm on `InvocationsFailedToBeSentToDlq` (any non-zero = event lost even with a DLQ).

- **Design every consumer to be idempotent** — EventBridge is at-least-once and unordered across the fleet; archive replay processes in one-minute buckets (out of order). Use an idempotency key (event id or stable business key) with a DynamoDB conditional write (`attribute_not_exists`) and a TTL. For ordering-sensitive flows use EventBridge Pipes with an ordered source (Kinesis/DynamoDB Streams), which preserves source order end-to-end.

- **Scope cross-account ingestion: pin explicit account IDs in every rule's `account` field** — A `"*"` in the `account` field matches nothing; it is not a wildcard. Grant `events:PutEvents` on the receiver bus only to specific account IDs or an Org ID, guarded with `aws:SourceArn` (confused-deputy protection). Cross-account targets created after 2023-03-02 require an IAM role.

- **Push all routing and discard logic server-side into rule event patterns or Pipe FilterCriteria** — EventBridge evaluates patterns (prefix, suffix, numeric, cidr, wildcard, anything-but, $or, exists) at no extra cost; unmatched events never invoke or bill a downstream target. Keep patterns within 2,048 characters; max 30 wildcard rules per bus (hard limit); $or combinations under 1,000.

- **Use EventBridge Scheduler (not scheduled rules) for all new time-based invocations** — Scheduler adds one-time schedules, per-schedule IANA time zones with automatic DST, flexible time windows, per-schedule retry policy and DLQ, and universal targeting of 270+ services. Set `ActionAfterCompletion=DELETE` on one-time schedules; completed schedules consume the per-Region quota until deleted.

- **Encrypt sensitive event buses with a CMK and always pair with a DLQ** — CMK coverage is now complete: buses (2024-05), archives/replay (2025-04), filter patterns and input transformers (2025-09-17). Attach a DLQ on every CMK bus — encryption/decryption failures route to the DLQ, not silently dropped. Note: Schema Discovery is unsupported on CMK buses (requires an AWS-owned key).

### ⚠️ Ask First

For full decision matrices with trade-off tables see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Which EventBridge primitive fits this integration?** — Ask: "Is this many-to-many content routing (event bus + rules), a single producer→consumer wiring with filter/enrich (Pipes), a time-triggered task (Scheduler), high-fan-out to endpoints (SNS), or an ordered high-throughput stream (Kinesis)?" Confirm before designing. Cost anchors: custom bus $1.00/M; Pipes $0.40/M; Scheduler free up to 14M/month.

- **Choreography or orchestration for a multi-service saga?** — Ask: "How many participants and do we need centralized compensation, timeout control, and end-to-end visibility (Step Functions orchestration) or maximal decoupling and autonomy (EventBridge choreography)?" A small number of independently owned services favors choreography; many participants or complex compensating transactions favor orchestration.

- **Single default bus or custom buses per bounded context?** — Ask: "Do domains need isolation (separate security posture, CMK, resource policy per domain) and is a central audit account needed (hub-and-spoke)?" Remind: no third hop — a receiver bus cannot forward received events onward to a third bus. Max 100 buses per Region.

- **Which Pipes enrichment compute?** — Ask: "Is enrichment a single code call (Lambda), a multi-step flow (Step Functions Express only — Standard not supported), or a call to an existing HTTP API (API Gateway / API Destination)? Can it finish within the 5-minute pipe execution ceiling?" Enrichment response max 6 MB; an empty response suppresses the target (acts as a filter).

### 🚫 Never Do

For anti-patterns with full ❌/✅ code examples see [Never Do Patterns](./blueprints/never-do-patterns.md).

| Anti-Pattern | Risk | Alternative |
|---|---|---|
| Production target with no DLQ | CRITICAL — events lost silently on retry exhaustion or on any permanent error | Standard SQS DLQ (same Region) + alarm on `InvocationsFailedToBeSentToDlq` |
| Recursive/infinite-loop rules | HIGH — runaway cost and bus throttling | Narrow pattern to exclude self-generated events; monitor `DeadLetterInvocations` |
| Three-hop cross-account/bus forwarding chain | HIGH — events silently dropped (`THIRD_ACCOUNT_HOP_DETECTED`) | Origin publishes directly to each destination (single hop); or consumers read from hub bus |
| `"account": ["*"]` in a rule or overly broad bus resource policy | HIGH — `*` matches nothing; broad policy enables event injection | Explicit account IDs in the rule; scope bus policy to specific principals with `aws:SourceArn` |
| FIFO SQS queue as a DLQ | MEDIUM — failures uncaptured despite an apparent DLQ | Standard SQS queue only; encode ordering metadata in the consumer |
| CMK bus with Schema Discovery still enabled | MEDIUM — discovery silently stops updating schemas | Bootstrap schema catalog first on AWS-owned-key bus, then apply CMK; or manage schemas explicitly |

---

## Integration Patterns

For full code examples see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **EventBridge ↔ AWS Lambda / Step Functions** — Async invocation; attach DLQ + retry policy per target. Lambda receives the full event JSON envelope; Step Functions starts an execution asynchronously (Standard or Express).
- **EventBridge ↔ Amazon SQS (fan-out buffer)** — Route bus events to SQS for consumer groups; SQS fair queues (2025-11) supported as a target type. Use standard queues for DLQs; FIFO queues are target-only (not DLQ).
- **EventBridge Pipes ↔ Kinesis/DynamoDB Streams** — Preserves shard ordering end-to-end; tune `ParallelizationFactor` for throughput. Wildcard FilterCriteria not supported in Pipes (bus rules only).
- **EventBridge Scheduler ↔ Universal Targets** — ARN pattern `arn:aws:scheduler:::aws-sdk:{service}:{apiAction}` invokes any of 6,000+ API operations without Lambda glue.
- **EventBridge ↔ API Destinations** — Calls external HTTP APIs; credentials in Secrets Manager; default rate limit 300/s; $0.20/M events; use PrivateLink for private HTTP targets.

**Common problems**:
- **`THIRD_ACCOUNT_HOP_DETECTED` in DLQ** → Hub bus forwarding to a third account/bus. Redesign as direct publish from origin to each destination.
- **`InvocationsFailedToBeSentToDlq` > 0** → DLQ permissions misconfigured or FIFO queue used. Fix: grant `events.amazonaws.com` `sqs:SendMessage` with `aws:SourceArn` scoped to the rule ARN; use a standard queue.
- **Schema Discovery not updating** → CMK enabled on the bus. Discovery requires an AWS-owned key; manage schemas explicitly.
- **Pipe not delivering to target** → Enrichment returned empty body (`""`, `{}`, `[]`), which suppresses the target. Confirm enrichment returns a non-empty payload when target invocation is desired.

---

## Verification Loop

Run after every EventBridge configuration change:

### 1. Validate targets have DLQ and retry policy
```bash
aws events list-targets-by-rule \
  --rule <rule-name> \
  --event-bus-name <bus-name> \
  --query 'Targets[*].{Id:Id, DLQ:DeadLetterConfig.Arn, Retry:RetryPolicy}'
# Expected: every target shows a non-null DLQ Arn and an explicit RetryPolicy object
```

### 2. Test an event pattern
```bash
aws events test-event-pattern \
  --event-pattern file://pattern.json \
  --event file://sample-event.json
# Expected: {"Result": true}
```

### 3. Inspect bus resource policy for cross-account scope
```bash
aws events describe-event-bus --name <bus-name> --query 'Policy'
# Expected: policy scoped to specific account IDs or Org ID with aws:SourceArn; no Principal "*"
```

### 4. Verify Scheduler schedule configuration
```bash
aws scheduler get-schedule \
  --name <schedule-name> \
  --group-name <group-name> \
  --query '{RetryPolicy:RetryPolicy, DLQ:DeadLetterConfig.Arn, ActionAfterCompletion:ActionAfterCompletion}'
# Expected: RetryPolicy and DLQ present; one-time schedules show ActionAfterCompletion=DELETE
```

### 5. Check CMK encryption status on bus
```bash
aws events describe-event-bus --name <bus-name> --query 'KmsKeyIdentifier'
# Expected: CMK ARN if encryption required; null otherwise
```

**Troubleshooting**:
- `NO_PERMISSIONS` in DLQ → Target IAM role missing or bus resource policy too restrictive; inspect `ERROR_MESSAGE` attribute on the DLQ message.
- `THIRD_ACCOUNT_HOP_DETECTED` → Redesign forwarding topology; remove the intermediate forwarding rule.
- `InvalidEventPatternException` → Pattern exceeds 2,048 chars, >1,000 `$or` combinations, or >30 wildcard rules on the bus.

---

## Quick Reference

**Essential commands**:
```bash
# Send a test event
aws events put-events --entries '[{"Source":"com.example.orders","DetailType":"OrderPlaced","Detail":"{\"orderId\":\"123\"}","EventBusName":"my-bus"}]'

# List all rules on a bus
aws events list-rules --event-bus-name <bus-name>

# Test a rule event pattern
aws events test-event-pattern --event-pattern file://pattern.json --event file://event.json

# Start archive replay
aws events start-replay \
  --replay-name <name> \
  --event-source-arn <archive-arn> \
  --event-start-time <t0> \
  --event-end-time <t1> \
  --destination Arn=<bus-arn>,FilterArns=<rule-arns>
```

**Critical limits**:

| Resource | Limit | Notes |
|---|---|---|
| PutEvents request size | 1 MB (1,048,576 bytes) | 256 KB is superseded misinformation |
| Event buses per Region | 100 | Soft limit; adjustable |
| Rules per event bus | 300 (100 in af-south-1/eu-south-1) | Managed rules count toward this |
| Targets per rule | 5 | Use SNS or multiple rules for higher fan-out |
| Event pattern size | 2,048 characters | Hard limit |
| Wildcard rules per bus | 30 | Hard; wildcard is bus-rule-only (not Pipes) |
| Scheduler schedules/Region | 10,000,000 | Adjustable to billions |
| Scheduler target input | 256 KB | Hard limit |
| Pipes enrichment response | 6 MB | Hard limit |
| Pipes execution ceiling | 5 minutes | Not adjustable |
| Concurrent replays/account | 10 per Region | Not adjustable |
| MaximumRetryAttempts (rules) | 0–185 | Default: 185 |
| MaximumEventAgeInSeconds (rules) | 60–86400 | Default: 86400 (24 h) |

**Cost anchors**:
- Custom bus events: $1.00/M
- Pipes: $0.40/M requests
- Scheduler: free first 14M invocations/month, then $1.00/M
- Default-bus AWS-service events: free
- Archive processing: $0.10/GB; storage: $0.023/GB-month
- API Destinations: $0.20/M events
- Schema Discovery: free first 5M events/month, then $1.00/M

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-eventbridge-eda/
├── SKILL.md                          <- This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md         <- 6 mandatory patterns with full verification commands
    ├── ask-first-decisions.md        <- 4 architectural decision matrices with option tables
    ├── never-do-patterns.md          <- 6 anti-patterns with wrong/correct code examples
    └── evaluation-scenarios.md       <- 5 test scenarios for skill evaluation
```

---

## External Resources

### Official Documentation (accessed 2026-08-28)
- [Amazon EventBridge User Guide](https://docs.aws.amazon.com/eventbridge/latest/userguide/) — Primary reference
- [EventBridge DLQ](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-dlq.html) — Dead-letter queue setup and error codes
- [EventBridge Retry Policy](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html) — Retry semantics; permanent-error handling
- [EventBridge Cross-Account Routing](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-cross-account.html) — Cross-account setup and no-third-hop constraint
- [EventBridge Event Patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-pattern-operators.html) — Comparison operators reference
- [EventBridge Pipes](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html) — Point-to-point integration primitive
- [Pipes Enrichment](https://docs.aws.amazon.com/eventbridge/latest/userguide/pipes-enrichment.html) — Enrichment compute options and limits
- [EventBridge Scheduler](https://docs.aws.amazon.com/scheduler/latest/UserGuide/what-is-scheduler.html) — Universal scheduler reference
- [EventBridge CMK Encryption](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-encryption-event-bus-cmkey.html) — At-rest encryption with customer managed keys
- [EventBridge Schema Registry](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schema-registry.html) — Schema discovery and code bindings
- [EventBridge Archive and Replay](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html) — Recovery and reprocessing
- [EventBridge Monitoring Metrics](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-monitoring.html) — CloudWatch metrics and alarms

### Architecture Patterns
- [Saga Choreography (AWS Prescriptive Guidance)](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-choreography.html) — Distributed saga design (accessed 2026-08-28)
- [EventBridge Pricing](https://aws.amazon.com/eventbridge/pricing/) — Current cost model (accessed 2026-08-28)
- [AWS Event-Driven Architecture](https://aws.amazon.com/event-driven-architecture/) — Reference landing page (accessed 2026-08-28)
