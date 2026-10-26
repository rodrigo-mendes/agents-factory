# Never Do Patterns — OCI Event-Driven Pub/Sub Architecture

Each anti-pattern shows what NOT to do and the correct alternative. Patterns are ordered by severity.

---

## Anti-Pattern 1 — Private-Endpoint-Only Stream Pool with SCH as Source

**Risk Level**: CRITICAL
**Impact**: SCH is an Oracle-managed service that runs OUTSIDE customer VCNs. A pool with only `private_endpoint_settings` exposes a private IP (e.g., 10.0.1.131) reachable only from inside the VCN. SCH has no route to it. Result: `ErrorsAtSource` increments on every ~5-min poll cycle, `MessagesFromSource = 0`, `FunctionInvocationCount = 0` — consumers are never invoked. This failure is silent until an operator queries SCH metrics; the pipeline looks "ACTIVE" in the console.

```
❌ WRONG: private pool + SCH source
  oci_streaming_stream_pool.this {
    private_endpoint_settings { subnet_id = ..., nsg_ids = [...] }
  }
  + oci_sch_service_connector with source { kind = "streaming" }
  → SCH ErrorsAtSource=1.0/poll, MessagesFromSource=0, consumers never fire

✅ CORRECT: public pool + SCH source
  oci_streaming_stream_pool.this {
    # No private_endpoint_settings block → public endpoint
    kafka_settings { auto_create_topics_enable = false }
  }
  + oci_sch_service_connector with source { kind = "streaming" }
  → SCH reads fine (ErrorsAtSource=0), consumers invoked
```

**Important nuance**: A producer function inside the VCN CAN read/write a private pool (it has network access via NSG). But SCH cannot. This means "private pool for security" and "SCH fan-out" are mutually exclusive choices — not complementary.

**Fix if already deployed**: `private_endpoint_settings` is immutable. A plain `terraform apply` with the block removed is a NO-OP (provider treats it as optional+computed — "leave as-is"). The pool must be force-replaced: `terraform apply -replace='module.streaming.oci_streaming_stream_pool.this'`. This destroys/recreates the pool AND the stream (data loss, new OCIDs). All references (producer config, SCH source configs, IAM) must be updated.

**Evidence**: `docs/handoff/event-pubsub/diagnosis-report-sch-source.md`, `deploy-report.md` cycle 9 (no-op trap) and cycle 10 (public pool fix → fan-out GREEN).

---

## Anti-Pattern 2 — Single SCH Routing to Multiple Functions

**Risk Level**: HIGH
**Impact**: Service Connector Hub has exactly one `target` block per `oci_sch_service_connector` resource. There is no multi-target or routing DSL. Attempting to fan out to two functions from a single connector either fails at apply time or only reaches the single configured target, silently dropping all deliveries to the second consumer.

```
❌ WRONG: one connector, two "targets" (schema violation)
  resource "oci_sch_service_connector" "fanout" {
    source { kind = "streaming" ... }
    target { kind = "functions"; function_id = consumer_a }  # Only first target honored
    target { kind = "functions"; function_id = consumer_b }  # Schema violation
  }

✅ CORRECT: N connectors, same source, independent targets
  resource "oci_sch_service_connector" "notify" {
    source { kind = "streaming"; stream_id = var.stream_id }
    target { kind = "functions"; function_id = consumer_notify }
  }

  resource "oci_sch_service_connector" "audit" {
    source { kind = "streaming"; stream_id = var.stream_id }
    target { kind = "functions"; function_id = consumer_audit }
  }
  # OCI tracks cursor state per connector → both receive the same messages
```

**Evidence**: `infra/modules/service-connector/main.tf` (for_each pattern), `deploy-report.md` cycle 10 (same event_id in both consumer logs proving independent fan-out).

---

## Anti-Pattern 3 — Ignoring the SCH Sync Deadline with Standard JVM Cold Start

**Risk Level**: HIGH
**Impact**: SCH invokes Functions targets synchronously. Standard JVM images (OTel + Jersey3 + OCI SDK, 67+ dependency jars) require ~55-60 s of platform container-provisioning + JVM pre-main class-loading before any application code runs. The SCH sync target-invoke deadline is ~30-60 s. At 256 MB (~0.17 vCPU), every cold delivery aborts with `444 Client request aborted` → `ErrorsAtTarget` → retry → new cold start → permanent loop. Memory bump (256 → 1024 MB) and function timeout bump (60 → 300 s) do NOT eliminate the ~60 s pre-main gap; they only give it room to complete. Without explicit mitigation, every cold SCH delivery fails.

```
❌ WRONG: default memory + timeout on SCH consumer (cold start exceeds deadline)
  func.yaml:
    memory: 256     # ~0.17 vCPU → JVM class-load slow
    timeout: 60     # SCH abort before cold start finishes → ErrorsAtTarget loop

✅ CORRECT: raise memory + timeout so cold start completes within deadline
  func.yaml:
    memory: 1024    # ~0.67 vCPU → faster class-load; cold start ~60s still, but COMPLETES
    timeout: 300    # Maximum; gives platform provisioning time to finish

✅ ALSO CORRECT (if cold delivery must be zero): GraalVM native image
  # Native binary: ~150 MB, cold start ~2-5 s — well under any SCH deadline
  # Requires native compilation in CI/CD; no JVM; OCI SDK native config required

✅ ALSO CORRECT (if runtime config is not enough): async decouple
  # SCH → target that buffers (ONS/Queue) → Function invoked asynchronously
  # No sync deadline; Function wakes on its own schedule
```

**Measured data** (from `diagnosis-report.md`):

| Phase | 256 MB | 1024 MB + code fix |
|-------|--------|-------------------|
| Platform provision + JVM pre-main | ~55-62 s | ~60 s (immovable) |
| App init (COLD_START completed) | 2318 ms | 964 ms |
| Warm invoke | 0.8 s | 7.9 s |
| SCH delivery result | ABORT (444) | SUCCESS |

Note: the ~60 s pre-main gap is platform container provisioning + JVM class-loading under the FDK before `main()`. It is NOT reducible by app-init optimization (moving OTel to `configure()` reduces app-init from 2.3 s to 0.96 s, but leaves the pre-main gap unchanged). The memory bump to 1024 MB makes the gap complete within timeout=300 s; it does not shrink the gap.

---

## Anti-Pattern 4 — HTTP Headers for Trace Propagation Across the Stream Boundary

**Risk Level**: MEDIUM
**Impact**: The producer function completes and returns 202 before any consumer is invoked. There is no live HTTP connection between producer and consumer — no `traceparent` header can be forwarded. Adding HTTP trace headers to the Streaming message value has no effect. The APM Trace Explorer shows a broken trace (no parent-child span link across the stream gap).

```
❌ WRONG: trying to propagate trace via HTTP headers across the stream
  // Producer code — placing HTTP headers in the Streaming message key/value
  Map<String, String> carrier = new HashMap<>();
  openTelemetry.getPropagators().getTextMapPropagator().inject(context, carrier, setter);
  // carrier contents (traceparent, tracestate) are LOST — SCH does not forward them
  // The consumer has no HTTP context to extract them from

✅ CORRECT: embed trace context inside the message envelope
  // Producer: embed correlation_id (= traceId or transaction_id) in envelope JSON
  DomainEvent envelope = DomainEvent.builder()
      .eventId(UUID.randomUUID().toString())
      .correlationId(transactionId)  // = producer traceId
      .build();
  // Consumer: read correlation_id → create child span with this as parent context
  Span span = tracer.spanBuilder("consumer.process")
      .setParent(Context.current().with(
          Span.wrap(SpanContext.createFromRemoteParent(
              traceId, spanId, TraceFlags.getSampled(), TraceState.getDefault()))))
      .startSpan();
  // Consumer: log MDC traceId for log-trace correlation
  MDC.put("traceId", traceId); MDC.put("spanId", spanId);
```

**Consequence**: The APM Trace Explorer will show two separate traces (one for producer, one for each consumer) linked only by the `correlation_id` / `transaction_id` field in logs. Manual correlation via log search is required for the cross-stream gap.

---

## Anti-Pattern 5 — Missing fn-function IAM Verb for SCH Functions Target

**Risk Level**: CRITICAL
**Impact**: SCH requires TWO IAM verbs to invoke a Functions target: `use fn-function` (resolve/GetFunction) and `use fn-invocation` (invoke). Missing `fn-function` causes a fast authorization rejection BEFORE the Functions invoke pipeline — zero function logs (not even `Received function invocation request`), `ErrorsAtTarget` incrementing every poll cycle, no `LatencyAtTarget` metric. This looks exactly like a cold-start abort (similar ErrorsAtTarget pattern) but the signature is different: cold-start shows `Received` then 60 s then 444; missing fn-function shows NOTHING.

```
❌ WRONG: only fn-invocation (SCH cannot resolve the target function)
  "Allow any-user to use fn-invocation in compartment X
    where request.principal.type='serviceconnector'"
  → ErrorsAtTarget every poll, zero function logs — fast auth reject

✅ CORRECT: both fn-function AND fn-invocation
  "Allow any-user to use fn-function   in compartment X
    where all {request.principal.type='serviceconnector'}"
  "Allow any-user to use fn-invocation in compartment X
    where all {request.principal.type='serviceconnector'}"
  → SCH resolves function, invokes it; function logs appear
```

**Diagnostic signature**:
- `ErrorsAtTarget > 0` AND `FunctionInvocationCount = 0` AND ZERO function log entries (not even `Received`) → missing `fn-function`
- `ErrorsAtTarget > 0` AND `FunctionInvocationCount = 0` AND function logs show `Received` then 60 s then 444 → cold-start ceiling (Pattern 3 above)

**Evidence**: `docs/handoff/event-pubsub/diagnosis-report-sch-auth.md` (fast auth reject, fn-function fix), `infra/modules/iam/main.tf` lines 92-93.
