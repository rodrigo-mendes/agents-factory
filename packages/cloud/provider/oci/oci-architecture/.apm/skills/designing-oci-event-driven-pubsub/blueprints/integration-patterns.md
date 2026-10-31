# Integration Patterns — OCI Event-Driven Pub/Sub Architecture

Complete topology diagrams and variant specifications for the pub/sub pattern family.

---

## Pattern 1 — Full Fan-Out Stack (Producer + 2 Consumers)

**Delivered in dev** (cycle 10, 2026-07-22). Status: GREEN.

```
Internet
   │
   │ HTTPS POST /v1/events
   ▼
API Gateway (public subnet)
   │ VCN-internal route
   ▼
func-event-producer (private subnet, 256 MB, 60 s)
   │ Resource Principal → stream-push IAM
   │ PutMessages (key=event_type, value=JSON→Base64)
   ▼
OCI Streaming — event-stream (PUBLIC pool, 3 partitions, 168h retention)
   │
   ├───────────────────┐
   │                   │
SCH: sch-event-notify   SCH: sch-event-audit
(cursor TRIM_HORIZON)   (cursor TRIM_HORIZON)
   │ batch 128KB/60s    │ batch 128KB/60s
   ▼                    ▼
func-evt-consumer-notify  func-evt-consumer-audit
(1024 MB, 300 s)          (1024 MB, 300 s)
   │                         │
   │ HTTP POST (httpbin)      │ OCI Logging (audit record)
   ▼                         ▼
External REST API          Audit log
```

**IAM policy set** (all in one policy resource):
```
# Producer function → stream
Allow dynamic-group dg-functions-dev to use stream-push in compartment X

# SCH source (stream read)
Allow any-user to {STREAM_READ, STREAM_CONSUME} in compartment X
  where all {request.principal.type='serviceconnector'}

# SCH target (function invoke) — BOTH verbs required
Allow any-user to use fn-function   in compartment X
  where all {request.principal.type='serviceconnector'}
Allow any-user to use fn-invocation in compartment X
  where all {request.principal.type='serviceconnector'}
```

**Event flow timing** (cycle 10 measured):
- Producer → stream publish: ~400 ms (warm)
- Stream → SCH poll → consumer invoked: ~2 min (SCH polls every ~5 min; first delivery within one poll cycle)
- Consumer cold-start-to-completion: ~62 s (platform provision + class-load + handler)
- Consumer warm invoke: ~6-8 s

---

## Pattern 2 — REST Consumer Variant (02a)

**Use when**: Event should trigger a call to an external HTTP/REST API (partner notification, ERP webhook, third-party integration).

```
OCI Streaming → sch-event-notify → func-event-consumer-rest
                                        │
                                        ├── Read event_id → check dedup
                                        ├── Fetch API key from Vault (Resource Principal)
                                        ├── HttpClient.POST(target_url, payload)
                                        └── Log success/failure with event_id
```

**Additional IAM** (beyond base set):
```
Allow dynamic-group dg-functions-consumers-dev to read secret-bundles in compartment X
  where target.secret.name = 'api-key-notify'
```

**Additional infrastructure**: NAT Gateway (for HTTPS egress to external URL), OCI Vault secret for API key.

**Error handling**:
- 5xx from target → log and return failure to SCH (SCH retries on next poll)
- 4xx from target → log and skip (no retry — bad request is not recoverable)
- Network timeout → log and return failure

---

## Pattern 3 — Database Consumer Variant (02b)

**Use when**: Event should be persisted to a relational database (audit record, event sourcing projection, read model).

```
OCI Streaming → sch-event-audit-db → func-event-consumer-ords
                                          │
                                          ├── Deserialize DomainEvent
                                          ├── UPSERT via ORDS REST API
                                          │   ON CONFLICT (event_id) DO NOTHING
                                          └── Log result with event_id
```

**Additional infrastructure**: ORDS endpoint (Autonomous DB), Service Gateway (OCI services network path for ORDS).

**Idempotency**: DB-level unique constraint on `event_id` column. Upsert pattern handles replay without application-layer dedup.

---

## Pattern 4 — Event Chain Variant (02c)

**Use when**: The consumer needs to produce events for a downstream pipeline (enrichment, transformation, domain boundary crossing).

```
OCI Streaming (source)
   → sch-event-chain
   → func-event-consumer-chain
        │
        ├── Deserialize DomainEvent
        ├── Enrich / transform payload
        └── PutMessages → OCI Streaming (downstream stream) OR ONS topic
```

**Additional IAM**:
```
Allow dynamic-group dg-functions-consumers-dev to use stream-push in compartment X
  # If chaining to another stream
Allow dynamic-group dg-functions-consumers-dev to use ons-topics in compartment X
  # If publishing to ONS
```

**Chain depth**: Keep event chains shallow (2-3 hops maximum). Deep chains multiply cold-start risk and make distributed trace correlation harder.

---

## Pattern 5 — Distributed Trace Path Across the Stream Boundary

**Architecture constraint**: There is no live HTTP transport between producer and consumer. Trace context must travel inside the message envelope.

```
Producer (SERVER span):
  traceId = "abc123"
  spanId  = "prod001"
  └── embeds correlation_id = "txn-abc123" in DomainEvent envelope
  └── returns 202 with transaction_id = "txn-abc123"

  [OCI Streaming — async gap, no HTTP transport]

Consumer A (CONSUMER span):
  reads correlation_id = "txn-abc123" from envelope
  creates child span with traceId = "abc123" (reconstructed from correlation_id)
  MDC: traceId=abc123, spanId=cons_a_001
  logs: "AUDIT event | event_id=uuid | traceId=abc123"

Consumer B (CONSUMER span):
  reads correlation_id = "txn-abc123" from envelope
  creates child span with traceId = "abc123" (reconstructed)
  MDC: traceId=abc123, spanId=cons_b_001
  logs: "FORWARDED event | event_id=uuid | traceId=abc123"
```

**APM result**: Three separate spans (1 SERVER + 2 CONSUMER) linked by `traceId` = `abc123`. APM Trace Explorer may show them as a single trace if the OTLP exporter correctly sets the remote parent context; otherwise they appear as correlated separate traces discoverable by `transaction_id` search.

**Cross-reference**: Pattern docs at `docs/patterns/02-event-driven/02-event-driven-pub-sub.md` (section 2 on producer Java spec).
