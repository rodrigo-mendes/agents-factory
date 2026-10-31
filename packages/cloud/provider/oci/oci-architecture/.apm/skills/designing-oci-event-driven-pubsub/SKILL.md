---
name: designing-oci-event-driven-pubsub
description: "Designs end-to-end event-driven pub/sub architectures on OCI using Functions + Streaming + Service Connector Hub. Use when designing producer/consumer patterns, fan-out topologies, idempotent consumers, consumer variants (REST/DB/event-chain), or distributed tracing through asynchronous streams."
---

## Version Context

**Technology**: OCI Functions (FDK Java v1.1.x, Java 17) + OCI Streaming + OCI Service Connector Hub
**Architecture Domain**: Event-Driven / Pub-Sub
**Target Edition**: OCI Best Practices (verify currency at [OCI Architecture Center](https://docs.oracle.com/en/solutions/))
**Pattern Docs**: `docs/patterns/02-event-driven/` (02, 02a, 02b, 02c)
**Support Status**: Active — handoff evidence at `workspace/poc-oci-serverless/docs/handoff/event-pubsub/`

**Key Architectural Facts**:
- OCI Streaming is Kafka-compatible (TCP 9092/9093 + HTTPS messages endpoint)
- Stream Pool must be **PUBLIC** when SCH is the source — SCH is Oracle-managed and runs OUTSIDE customer VCNs; a private-endpoint-only pool is unreachable (see Always Do Pattern 3 and Never Do Pattern 1)
- SCH invokes Functions targets **synchronously** with a ~30-60 s hard deadline; heavy JVM cold starts (~60 s for a 2.28 GB image) abort every cold delivery until the container is warm
- Distributed tracing CANNOT cross the stream boundary via HTTP headers — the trace context must travel inside the message envelope

⚠️ **CRITICAL — Agent Warning**:
This skill covers architecture decisions only. For Terraform provisioning of Streaming, SCH, and Functions, use `provisioning-oci-event-driven-pubsub` and its cross-referenced provisioning skills. For Java implementation of producer/consumer handlers, use `developing-oci-functions-java` and `implementing-oci-functions-events`.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory architecture patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Consumer variant and topology decisions
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns and failure modes
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Full topology diagrams and variant specs
- **[Evaluations](./evaluations.json)** — Design scenario evaluations
- **[PoC Worked Examples](./blueprints/poc-worked-examples.md)** — Pattern 02 event-driven pub/sub from the reference PoC (fan-out + distributed trace proven live)
- **[Reference Architecture](#reference-architecture)** — Component diagram
- **[Verification Loop](#verification-loop)** — Post-deploy validation commands

---

## Reference Architecture

```
                        ┌──────────────────────────────────────────────────────┐
                        │               OCI Compartment                        │
 External               │  VCN                                                 │
 System ─── HTTPS ───► API Gateway (public subnet)                             │
                        │         │                                            │
                        │         │ (VCN internal)                             │
                        │  ┌──────▼──────────────────────────────────────┐    │
                        │  │  Private Subnet                              │    │
                        │  │  func-event-producer                         │    │
                        │  │  - validates EventRequest                    │    │
                        │  │  - generates event_id (UUID)                 │    │
                        │  │  - key = event_type (partition ordering)     │    │
                        │  │  - value = JSON → Base64                     │    │
                        │  │  - returns 202 Accepted immediately          │    │
                        │  └─────────────┬────────────────────────────────┘   │
                        │                │ stream-push (IAM DG)               │
                        │                ▼                                     │
                        │  OCI Streaming (PUBLIC pool)                         │
                        │  stream: event-stream (3 partitions, 168h)           │
                        │                │                                     │
                        │       ┌────────┴────────┐                           │
                        │       │ SCH Cursor A    │ SCH Cursor B              │
                        │  sch-notify (ACTIVE)  sch-audit (ACTIVE)            │
                        │  (own cursor state)  (own cursor state)             │
                        │       │                 │                           │
                        │  ┌────▼──────────┐ ┌───▼──────────┐               │
                        │  │func-evt-      │ │func-evt-      │               │
                        │  │consumer-notify│ │consumer-audit │               │
                        │  │ REST target   │ │ audit log     │               │
                        │  └───────────────┘ └───────────────┘               │
                        └──────────────────────────────────────────────────────┘
```

**Fan-out**: Two separate `oci_sch_service_connector` resources pointing at the same stream — OCI tracks cursor state independently per connector. Both consumers receive the same message.

---

## Core Design Principles

### 1. Producer: Message Envelope

Every message published to the stream MUST include a standard envelope inside the Base64-encoded JSON payload:

```json
{
  "event_id":       "<UUID>",          // Idempotency key — consumers dedup by this
  "event_type":     "order.created",   // Partition key — routing and ordering
  "payload":        { ... },           // Domain data
  "correlation_id": "<trace-carrier>", // Distributed tracing — see Principle 4
  "timestamp":      "<ISO8601 timestamp>"
}
```

**Partition key = `event_type`**: guarantees ordering within each event type across partitions. `PutMessages` sets `key = event_type`; OCI Streaming routes all messages with the same key to the same partition.

### 2. Consumer: Idempotency by event_id

The SCH delivery guarantee is **at-least-once** — cursors can replay on reactivation (`TRIM_HORIZON`) and any transient error causes retry. Consumers MUST be idempotent:

- Check `event_id` against a dedup store (in-memory map for POC; persistent cache/DB for production)
- Process only if `event_id` is new
- Mark as processed before or atomically with the action (depends on target semantics)

### 3. Fan-Out: N Independent SCH Cursors

True pub/sub fan-out requires **one `oci_sch_service_connector` per consumer** — all pointing at the same `stream_id`. OCI Streaming maintains independent cursor state per connector. This is NOT a single connector routing to multiple functions — that pattern does not exist in SCH. See Never Do Pattern 2.

**Naming convention**: `sch-<purpose>-<env>` (e.g., `sch-event-notify-dev`, `sch-event-audit-dev`)

### 4. Distributed Tracing Through the Stream Boundary

HTTP trace headers (W3C `traceparent`) cannot cross the Streaming boundary because the producer finishes before the consumer starts. The architectural pattern is:

```
Producer:  generate traceId + spanId → embed as correlation_id in envelope
           return 202 with transaction_id (= traceId)

Consumer:  read correlation_id from envelope → create child span
           log traceId + spanId via MDC for log-trace correlation
```

This produces a "broken" trace (no parent-child span link across the stream gap) in APM Trace Explorer unless the consumer explicitly reconstructs the context from `correlation_id`. The MDC traceId in both producer and consumer logs enables manual correlation via `transaction_id`.

### 5. SCH Cold-Start Ceiling Trade-Off

SCH invokes Functions targets synchronously with a platform deadline of ~30-60 s. A heavy JVM image (2.28 GB, 67-jar OTel+Jersey3+OCI-SDK classpath) requires ~60 s of platform container-provisioning + JVM pre-main class-loading BEFORE any application code runs. This creates a hard ceiling:

**Cold delivery → abort (444 Client request aborted) → `ErrorsAtTarget` → retry loop → never succeeds**

Escapes (in order of effort):
1. **Function timeout = 300 s + memory >= 1024 MB**: the ~60 s cold start completes within the deadline; pay-per-use works (confirmed in dev cycle 10)
2. **Provisioned concurrency**: eliminates cold delivery; platform minimum is count=10 (NOT 1), 20 warm containers for 2 consumers = significant cost
3. **GraalVM native image**: ~150 MB, cold start ~2-5 s, well under any SCH deadline; requires native compilation step
4. **Decouple async**: SCH → ONS/Queue (tolerates cold latency) → Function; no direct sync deadline

See Never Do Pattern 3 and Ask First Decision 3 for the full decision matrix.

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns**:
- **Public Stream Pool when SCH is source** — SCH runs outside VCN; private-endpoint pools are unreachable (ErrorsAtSource, MessagesFromSource=0)
- **Standard message envelope** — event_id (idempotency), event_type (partition key), correlation_id (tracing), timestamp (ordering)
- **event_type as partition key** — guarantees ordering per event type; `PutMessages` key field maps to Kafka key
- **Idempotent consumers** — SCH at-least-once delivery; dedup by event_id before acting
- **One SCH per consumer** — each connector holds independent cursor state; do not attempt to fan out from a single connector
- **Function timeout 300 s + memory >= 1024 MB** — minimum viable config for SCH targets using standard JVM images; enables cold starts to complete within the sync deadline
- **Monitor ErrorsAtSource AND ErrorsAtTarget separately** — ErrorsAtSource = source-read failure (pool reachability, IAM stream verbs); ErrorsAtTarget = function invoke failure (auth, cold-start, contract)

### ⚠️ Ask First

For complete decision matrices, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points**:
- **Consumer variant** — REST/DB/event-chain; each has distinct IAM, network, and error-handling requirements
- **Stream pool type** — PUBLIC required for SCH source; PRIVATE acceptable for in-VCN Kafka clients only
- **Cursor strategy** — LATEST (real-time, discard gap) vs TRIM_HORIZON (full replay, requires idempotency)
- **Cold-start mitigation** — timeout+memory (cheapest), provisioned concurrency (costly, min=10), GraalVM native, or async decouple

### 🚫 Never Do

For complete anti-patterns, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns**:
- **Private-endpoint-only pool with SCH as source** — SCH cannot reach in-VCN private endpoints; ErrorsAtSource, zero consumer invocations
- **Single SCH routing to multiple function targets** — SCH has exactly 1 target per connector; fan-out requires N connectors
- **Ignoring the SCH sync deadline with cold JVM** — memory bump and timeout bump do NOT reduce the ~60 s platform cold-provisioning time; explicit mitigation required
- **HTTP headers for trace propagation across stream** — no HTTP transport between producer and consumer; embed correlation_id in envelope
- **Missing fn-function IAM verb** — SCH Functions target requires BOTH `use fn-function` AND `use fn-invocation`; missing fn-function causes fast auth-reject (zero function logs, ErrorsAtTarget, looks like cold start but isn't)

---

## Integration Patterns

For complete topology diagrams, see [Integration Patterns](./blueprints/integration-patterns.md).

**Supported variants** (from pattern docs in `workspace/poc-oci-serverless/docs/patterns/02-event-driven/`):
- **02 Producer** (`02-event-driven-pub-sub.md`) — API Gateway → func-event-producer → Streaming
- **02a REST Consumer** (`02a-event-driven-rest-consumer.md`) — SCH → func-event-consumer-rest → external HTTP
- **02b Database Consumer** (`02b-event-driven-database-consumer.md`) — SCH → func-event-consumer-ords/jdbc → DB
- **02c Event Chain** (`02c-event-driven-event-chain.md`) — SCH → func-event-consumer-chain → another stream/queue/ONS

---

## Verification Loop

Run after every architecture change or deploy. Metrics namespace: `oci_service_connector_hub`.

```bash
# 1. Confirm stream pool is PUBLIC (no private-endpoint-settings)
oci streaming admin stream-pool get \
  --stream-pool-id <POOL_OCID> \
  --query 'data.{"endpoint":"endpoint-fqdn","private-ep":"private-endpoint-settings"}'
# Expected: private-ep = null; endpoint contains "cell-1.streaming.<region>.oci.oraclecloud.com"

# 2. Verify both SCH connectors ACTIVE
oci sch service-connector list \
  --compartment-id <COMP_OCID> \
  --lifecycle-state ACTIVE \
  --query 'data[].{name:"display-name",state:"lifecycle-state"}'
# Expected: sch-event-notify-dev + sch-event-audit-dev = ACTIVE

# 3. Verify SCH ErrorsAtSource = 0 (source reachable)
oci monitoring metric-data summarize-metrics-data \
  --compartment-id <COMP_OCID> \
  --namespace oci_service_connector_hub \
  --query-text 'ErrorsAtSource[5m].sum()' \
  --resolution 5m
# Expected: 0 on all connectors

# 4. Verify SCH FunctionInvocationCount > 0 (consumers firing)
oci monitoring metric-data summarize-metrics-data \
  --compartment-id <COMP_OCID> \
  --namespace oci_service_connector_hub \
  --query-text 'FunctionInvocationCount[5m].sum()' \
  --resolution 5m
# Expected: >= 1 per consumer after a smoke test

# 5. Fan-out proof: same event_id in BOTH consumer logs
oci logging search log-entries \
  --search-query 'search "<LOG_GROUP_OCID>" | source like "%consumer%" | message like "%event_id=<UUID>%" | sort by datetime desc' \
  --time-start <ISO8601> --time-end <ISO8601>
# Expected: 2 matching log entries (audit + notify), same event_id
```

**Troubleshooting**:
- `ErrorsAtSource > 0` → pool is private (recreate as PUBLIC) OR missing `{STREAM_READ, STREAM_CONSUME}` IAM verbs for serviceconnector principal
- `ErrorsAtTarget > 0, zero function logs` → missing `use fn-function` verb (fast auth reject, not cold start)
- `ErrorsAtTarget > 0, function logs show "Received" then 444 abort` → cold-start ceiling; raise memory to 1024 MB + timeout to 300 s; if still failing, add GraalVM native or async decouple
- `FunctionInvocationCount = 0 after smoke` → SCH not yet polling (wait 1-2 poll cycles, ~5-10 min) OR ErrorsAtSource/Target blocking pipeline

---

## Quick Reference

### IAM Verbs Checklist

| Principal | Verb | Resource | Purpose |
|-----------|------|----------|---------|
| Functions DG | `use stream-push` | stream | Producer publishes messages |
| `serviceconnector` | `{STREAM_READ, STREAM_CONSUME}` | stream | SCH reads from stream |
| `serviceconnector` | `use fn-function` | compartment | SCH resolves target function (REQUIRED — missing = fast auth reject) |
| `serviceconnector` | `use fn-invocation` | compartment | SCH invokes target function |
| Functions DG (consumer) | `read secret-bundles` | vault | Fetch API keys / DB creds (02a/02b) |

### func.yaml Minimums for SCH Consumer

```yaml
memory: 1024        # Minimum for cold start to complete within SCH sync deadline
timeout: 300        # Maximum platform timeout; gives cold provision time to finish
```

### Stream Pool Endpoint Types

| Pool Type | `private_endpoint_settings` | Reachable by SCH | Reachable by in-VCN Functions |
|-----------|----------------------------|-----------------|-------------------------------|
| PUBLIC | absent / null | YES | YES (via NAT or Service GW) |
| PRIVATE | present (subnet_id, nsg_ids) | NO | YES (private IP inside VCN) |

---

## Skill Cross-References

| Need | Use Skill |
|------|-----------|
| Terraform: Streaming Pool + Stream | `provisioning-oci-streaming` |
| Terraform: Service Connector Hub | `provisioning-oci-connector-hub` |
| Terraform: full pub/sub stack | `provisioning-oci-event-driven-pubsub` |
| Terraform: IAM for producer/consumer | `provisioning-oci-iam` |
| Java: produce to Streaming from Function | `publishing-events-from-oci-functions` |
| Java: consume ConnectorHub batch | `implementing-oci-functions-events` |
| Architecture: full serverless stack | `architecting-oci-serverless` |
| SCH design decisions | `designing-oci-connector-hub` |
| Stream Pool architecture decisions | `provisioning-oci-streaming` (Ask First section) |

---

## External Resources

- [OCI Streaming Overview](https://docs.oracle.com/en-us/iaas/Content/Streaming/Concepts/streamingoverview.htm) (verified 2026-07-26)
- [OCI Service Connector Hub — Functions Target](https://docs.oracle.com/iaas/Content/connector-hub/create-service-connector-functions-target.htm) (verified 2026-07-26)
- [OCI Service Connector Hub — Streaming Source](https://docs.oracle.com/iaas/Content/connector-hub/create-service-connector-streaming-source.htm) (verified 2026-07-26)
- [OCI Functions — Provisioned Concurrency](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingprovisionedconcurrency.htm) (verified 2026-07-26)
- Pattern Docs (workspace): `workspace/poc-oci-serverless/docs/patterns/02-event-driven/` — 02, 02a, 02b, 02c (verified 2026-07-26)
- Handoff Evidence: `workspace/poc-oci-serverless/docs/handoff/event-pubsub/` — delivery records (verified 2026-07-26)
