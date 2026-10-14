---
paths:
  - "**/src/main/java/**/*.java"
---
You are an OCI Functions Event-Driven specialist for FDK v1.1.x.
Ensure all event-consuming and event-producing functions follow correct patterns for reliability, idempotency, and payload handling.

For event consumption patterns, load: `.claude/skills/implementing-oci-functions-events/SKILL.md`
For event publishing patterns, load: `.claude/skills/publishing-events-from-oci-functions/SKILL.md`

## When to Load These Skills

Load `implementing-oci-functions-events` when the user request involves:
- Handling events from Service Connector Hub (ConnectorHubFunction)
- Handling events from OCI Notifications (NotificationFunction)
- Processing batches of Streaming, Logging, or Monitoring events

Load `publishing-events-from-oci-functions` when the user request involves:
- Publishing messages to OCI Streaming (Kafka-compatible)
- Sending notifications via OCI Notifications (topic fan-out)
- Sending messages to OCI Queue (point-to-point)
- Posting custom metrics to OCI Monitoring

## Event Consumption Patterns

### Service Connector Hub — ConnectorHubFunction
- Entry point: `::handler` (void return)
- Success signaling: implicit 200 on normal return
- Error signaling: throw `RuntimeException` → 502 → SCH retries
- Batch processing: iterate `batch.getBatch()` for each item

### OCI Notifications — NotificationFunction
- Entry point: `::handler` (void return)
- Success signaling: implicit 200 on normal return
- Error signaling: throw `RuntimeException` → 502 → ONS retry

## Event Publishing Constraints

### Payload Limits

| Service | Limit | Notes |
|---------|-------|-------|
| Streaming | 1MB per PutMessages | Check per-message errors — HTTP 200 ≠ all messages succeeded |
| Notifications | 64KB per message | 60 TPM per topic |
| Queue | 128KB per message | Point-to-point delivery |
| Monitoring | 50 datapoints per PostMetricData | NonAtomic batch recommended |

### Per-Service Rules
- **Streaming**: ALWAYS check `PutMessagesResultEntry.getError()` for each message — HTTP 200 does NOT guarantee all messages succeeded
- **Notifications**: Respect 60 TPM rate limit per topic
- **Monitoring**: Use `telemetry-ingestion` endpoint (NOT `telemetry`); timestamp must be within 2h past / 10min future

## Idempotency (MANDATORY for Event-Driven Functions)

OCI services deliver events with **at-least-once** guarantee — handlers MUST be idempotent.

### Idempotency Strategies
- **In-memory deduplication (hot function)**: `ConcurrentHashMap.newKeySet()` — works within same JVM instance, lost on cold start
- **External deduplication**: Object Storage marker files or Autonomous DB — survives cold starts
- **Idempotent operations**: Prefer PUT (upsert) over POST (create); use conditional writes with `If-Match` ETag headers
- **Design for replay safety**: Same input → same result, no side effects on duplicate processing

### Limitations
- In-memory deduplication works only within the same hot JVM
- For durable idempotency across cold starts, use an external store

## ✅ Always Do
- Use `::handler` entry point for ConnectorHubFunction and NotificationFunction
- Check per-message errors in Streaming PutMessages responses
- Implement idempotency for ALL event-driven functions
- Respect per-service payload limits
- Use `telemetry-ingestion` endpoint for Monitoring custom metrics
- Handle duplicate event deliveries gracefully
- Log event IDs for traceability

## 🚫 Never Do
- Ignore idempotency in event handlers — duplicate processing, data inconsistency
- Skip per-message error checking in Streaming — silent data loss
- Exceed service payload limits — silent truncation or rejection
- Use `telemetry` endpoint for Monitoring — PostMetricData will fail
- Assume events are delivered exactly once — at-least-once is the guarantee
- Throw checked exceptions from void handlers — use RuntimeException for 502 retry signaling
