# Always Do Patterns — OCI Event-Driven Pub/Sub Architecture

Mandatory patterns for every OCI Streaming + SCH + Functions pub/sub design. Auto-execute without waiting for user confirmation.

---

## Pattern 1 — PUBLIC Stream Pool When SCH Is the Source

**Why**: Service Connector Hub is an Oracle-managed service that runs OUTSIDE customer VCNs. A stream pool configured with only `private_endpoint_settings` exposes a private IP address (e.g., 10.0.1.131) reachable only from inside the customer VCN. SCH has no route to that address. Result: `ErrorsAtSource` increments on every poll cycle, `MessagesFromSource = 0`, and consumers are never invoked — even with correct IAM and SCH wiring.

**Rule**: Use a PUBLIC stream pool (no `private_endpoint_settings` block) whenever SCH is the source. Private pools are only appropriate for in-VCN Kafka clients (producer functions, Kafka-compatible consumers inside the VCN).

```
✅ CORRECT: PUBLIC pool — SCH can reach the Oracle-managed messages endpoint
  Stream Pool endpoint: cell-1.streaming.<region>.oci.oraclecloud.com
  private-endpoint-settings: null

❌ WRONG: PRIVATE pool with SCH as source
  Stream Pool endpoint: <pool-id>.streaming.<region>.oci.oraclecloud.com (in-VCN only)
  private-endpoint-settings: { subnet_id = ..., nsg_ids = [...] }
  → SCH ErrorsAtSource = 1.0/poll, MessagesFromSource = 0, consumers never fire
```

**Evidence**: `docs/handoff/event-pubsub/diagnosis-report-sch-source.md`, `deploy-report.md` cycle 10 (public pool fix unblocked fan-out).

**Note on private pool for producers**: An in-VCN producer function CAN reach a private pool — the producer runs inside the VCN and can hit the private endpoint (add an NSG self-ingress 443 rule for the functions subnet). This does NOT apply to SCH.

---

## Pattern 2 — Standard Message Envelope

**Why**: Without a standard envelope, idempotency dedup, trace correlation, event routing, and ordering guarantees require out-of-band configuration. A consistent schema enables any consumer to operate without producer-specific logic.

Every message published to the stream MUST include:

```json
{
  "event_id":       "550e8400-e29b-41d4-a716-446655440000",
  "event_type":     "order.created",
  "payload":        { "orderId": "ORD-001", "amount": 100.00 },
  "correlation_id": "txn-abc123",
  "timestamp":      "2026-07-22T18:35:33Z"
}
```

| Field | Type | Purpose | Required |
|-------|------|---------|---------|
| `event_id` | UUID string | Idempotency key — consumers dedup by this value | YES |
| `event_type` | string | Partition key + routing — `PutMessages` key field | YES |
| `payload` | object | Domain data | YES |
| `correlation_id` | string | Trace carrier across the stream boundary | Recommended |
| `timestamp` | ISO-8601 | Event ordering and audit | Recommended |

The entire envelope is JSON-serialized and Base64-encoded before being set as the Streaming message value (OCI Streaming requires Base64).

---

## Pattern 3 — event_type as Partition Key

**Why**: OCI Streaming routes messages with the same key to the same partition, guaranteeing ordering within a partition. Using `event_type` as the key ensures all events of the same type (e.g., all "order.created") are processed in order by a given consumer.

```java
// Producer — Java SDK
PutMessagesDetailsEntry entry = PutMessagesDetailsEntry.builder()
    .key(Base64.getEncoder().encode(
           request.getEventType().getBytes(StandardCharsets.UTF_8)))
    .value(Base64.getEncoder().encode(
           objectMapper.writeValueAsBytes(envelope)))
    .build();
```

**Trade-off**: If `event_type` cardinality is very low (e.g., only 2-3 types) and partition count is high, some partitions may receive no messages. Acceptable trade-off for ordering guarantees.

---

## Pattern 4 — Idempotent Consumers

**Why**: SCH delivery is at-least-once. A connector with `cursor_kind = "TRIM_HORIZON"` replays all retained messages on reactivation. A transient SCH error causes a retry on the same message. Without idempotency, duplicate processing corrupts downstream state (duplicate REST calls, duplicate DB writes, double-counted metrics).

**Dedup strategy by consumer variant**:

| Variant | Dedup Store | Check | Action |
|---------|------------|-------|--------|
| 02a REST | In-memory `Set<String>` (POC) / Redis/DB (prod) | `seen.contains(event_id)` | Skip if present; process and add if absent |
| 02b Database | Unique constraint on `event_id` column | Upsert with ON CONFLICT IGNORE | Idempotent by DB constraint |
| 02c Event Chain | Include `event_id` in downstream message | Downstream consumer deduplicates | Chain idempotency |

---

## Pattern 5 — One Service Connector Per Consumer

**Why**: OCI Service Connector Hub has exactly one target per connector resource. Fan-out to N consumers requires N separate `oci_sch_service_connector` resources, all pointing at the same `stream_id`. OCI Streaming maintains independent cursor state per connector — each connector advances its own offset independently, so all consumers receive the same messages.

```
Source (OCI Streaming — same stream_id)
  │
  ├── SCH connector A (cursor state A) → func-evt-consumer-notify
  └── SCH connector B (cursor state B) → func-evt-consumer-audit
```

**Terraform**: Use `for_each` on a `var.connectors` map — one entry per consumer. See `provisioning-oci-event-driven-pubsub` skill.

---

## Pattern 6 — function timeout = 300 s + memory >= 1024 MB for SCH Targets

**Why**: SCH invokes Functions targets synchronously. Standard JVM images (OTel + Jersey3 + OCI SDK) require ~55-60 s of platform container-provisioning + JVM pre-main class-loading before application code runs. With `timeout = 60` (default) or `memory = 256 MB` (~0.17 vCPU), the SCH sync deadline expires during cold-provisioning → `444 Client request aborted` → `ErrorsAtTarget` loop. Memory raises CPU allocation (1024 MB = ~0.67 vCPU), cutting JVM class-load time; timeout 300 s gives cold-provision time to finish.

This does NOT apply to producer functions invoked via API Gateway (which buffers the cold start response).

```yaml
# func.yaml — SCH consumer minimum
memory: 1024    # ~0.67 vCPU; reduces JVM class-load time
timeout: 300    # Maximum; gives cold-provisioning room to complete
```

**Evidence**: `docs/handoff/event-pubsub/diagnosis-report.md` (55 s pre-main gap at 256 MB), `deploy-report.md` cycle 10 (1024 MB + timeout 300 s = fan-out GREEN with pay-per-use).

---

## Pattern 7 — Monitor ErrorsAtSource and ErrorsAtTarget Separately

**Why**: These metrics diagnose different failure modes and are not interchangeable. `ErrorsAtSource` = SCH cannot read the stream (pool reachability, missing STREAM_READ/STREAM_CONSUME verbs). `ErrorsAtTarget` = SCH read succeeded but function invocation failed (missing fn-function/fn-invocation verbs, cold-start timeout, contract mismatch). Treating them as a single "error" metric delays root cause identification.

```bash
# Both queries for per-connector monitoring
oci monitoring metric-data summarize-metrics-data \
  --compartment-id <COMP_OCID> \
  --namespace oci_service_connector_hub \
  --query-text 'ErrorsAtSource[5m].sum()'

oci monitoring metric-data summarize-metrics-data \
  --compartment-id <COMP_OCID> \
  --namespace oci_service_connector_hub \
  --query-text 'ErrorsAtTarget[5m].sum()'

# Both must be 0 for a healthy fan-out pipeline
```
