# Worked Examples (from the reference PoC)

These examples are extracted from `workspace/poc-oci-serverless/` — a validated, deployed PoC
(Pattern 02 delivered and validated in dev 2026-07-22; fan-out + distributed trace proven live).
Source: `workspace/poc-oci-serverless/docs/patterns/02-event-driven/02-event-driven-pub-sub.md`.

---

## End-to-end architecture (Pattern 02 — delivered)

```
External System
  │ HTTPS POST /v1/events
  ▼
API Gateway (public subnet)
  │ ORACLE_FUNCTIONS_BACKEND
  ▼
func-event-producer (private subnet)
  │ StreamClient.putMessages()  — key = event_type, value = JSON→Base64
  ▼
OCI Streaming (PUBLIC stream pool — SCH requirement)
  │ Service Connector Hub poll (continuous)
  ▼
Service Connector Hub (Oracle-managed, outside VCN)
  │ Invokes Function targets synchronously (~30–60 s hard deadline)
  ├─► func-evt-consumer-notify  (REST forward to external system)
  └─► func-evt-consumer-audit   (log + custom metric)
```

**Fan-out proven**: same `event_id` UUID appears in both consumer logs from one producer message.
**Trace continuity proven**: single `traceparent` travels inside the message envelope — the producer
embeds it in the JSON payload, consumers extract and continue the span.

---

## Critical constraint: Stream Pool must be PUBLIC

**Source**: `docs/patterns/02-event-driven/02-event-driven-pub-sub.md` (lessons learned section)

```hcl
# infra/modules/streaming/main.tf — PoC pattern
resource "oci_streaming_stream_pool" "this" {
  compartment_id = var.compartment_ocid
  name           = "${var.project_name}-${var.environment}-pool"

  # ⚠️ NO private_endpoint_settings block here.
  # SCH is Oracle-managed and runs OUTSIDE the customer VCN.
  # A private-endpoint-only pool is unreachable by SCH — deliveries fail silently.
  # Only use private endpoint if your consumer is in-VCN (Kafka-protocol consumer in a Function).

  kafka_settings {
    auto_create_topics_enable = false
    num_partitions            = var.default_partitions
    log_retention_hours       = var.retention_hours
  }
}
```

This is the most common failure mode in SCH-based event architectures on OCI. Always verify stream
pool type before provisioning SCH.

---

## Producer func.yaml (from `services/func-event-producer/`)

```yaml
# func.yaml — func-event-producer
schema_version: 20180708
name: func-event-producer
version: 0.0.1
runtime: java
build_image: fnproject/fn-java-fdk-build:jdk17-latest
run_image: fnproject/fn-java-fdk:jre17-latest
cmd: com.brx.functions.eventproducer.EventProducerFunction::handler
memory: 256
timeout: 60
config:
  ENVIRONMENT: dev
  STREAM_OCID: ocid1.stream.oc1...         # Non-sensitive — OCID only, not a credential
  STREAM_ENDPOINT: https://cell-1.streaming.sa-saopaulo-1.oci.oraclecloud.com
```

**Memory 256 MB, timeout 60 s** — sufficient for a fast publish (SDK call completes in <500 ms
for a small JSON payload). The consumer functions need more aggressive sizing due to the SCH
synchronous deadline (use 512 MB / 120 s for JVM-heavy consumers).

---

## Distributed trace: crossing the async boundary

The trace context CANNOT travel via HTTP headers through OCI Streaming (the stream is not an HTTP
transport). The PoC embeds `traceparent` inside the event envelope JSON:

```json
// Producer publishes this JSON → Base64 as the stream message value
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "STORE_CREATED",
  "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "payload": { ... }
}
```

Consumer extracts `traceparent` and passes it to the OTel SDK to continue the trace:
- Use `W3CTraceContextPropagator.getInstance().extract(Context.current(), envelope, getter)`.
- The resulting trace shows producer span → stream boundary → consumer span as a linked chain in
  APM (not a child span — the async boundary creates a new root span linked to the producer trace).

> **Lesson from the PoC**: `SimpleSpanProcessor` is mandatory in FaaS — `BatchSpanProcessor` buffers
> spans and they are lost when the container terminates between invocations. See the Always-Do
> patterns for the observability stack configuration.

---

## IAM policies required (from the PoC delivery)

```hcl
# Producer: push to stream
"Allow dynamic-group fn-event-producer-dg to use stream-push in compartment <name>"

# SCH: read from stream and invoke consumer function
"Allow service serviceconnector to read streams in compartment <name>"
"Allow service serviceconnector to use fn-function in compartment <name>"
"Allow service serviceconnector to use fn-invocation in compartment <name>"

# Consumer: emit custom metrics and write logs
"Allow dynamic-group fn-consumer-dg to use metrics in compartment <name>"
"Allow dynamic-group fn-consumer-dg to use log-content in compartment <name>"
```

Missing the `serviceconnector` policies is the second most common failure mode — SCH silently
drops events when it cannot invoke the target Function.
