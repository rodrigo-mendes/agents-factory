---
kind: report
from: "@oci-functions-java"
to: "@oci-deployer"
refs: diagnosis-report.md
capability: event-pubsub
outcome: success
createdAt: 2026-07-21T23:48:47Z
---

## What changed

Distributed-tracing export bug fixed in the copied `obs/TracingSupport.java` of all three
event pub/sub services. Root cause: the OTel SDK used `BatchSpanProcessor` (async export on a
background thread) — but OCI Functions freeze the container the instant the handler returns, so
the batch export thread never ran and spans never reached OCI APM ("Failed to export spans. The
request could not be executed."). Functions still returned 200, but the distributed trace
(producer -> stream -> both consumers) and the transaction-path dashboard had no data.

Files edited (kept byte-identical except the `package` line):
- `services/func-event-producer/src/main/java/com/brx/functions/event/producer/obs/TracingSupport.java`
- `services/func-evt-consumer-notify/src/main/java/com/brx/functions/event/consumer/notify/obs/TracingSupport.java`
- `services/func-evt-consumer-audit/src/main/java/com/brx/functions/event/consumer/audit/obs/TracingSupport.java`

Changes applied identically to all three:
1. **`BatchSpanProcessor` -> `SimpleSpanProcessor`** — synchronous export on `span.end()` within the
   live invocation (correct serverless pattern). Import swapped
   (`...export.BatchSpanProcessor` -> `...export.SimpleSpanProcessor`); builder call changed
   `.addSpanProcessor(BatchSpanProcessor.builder(exporter).build())` ->
   `.addSpanProcessor(SimpleSpanProcessor.create(exporter))`. The `OtlpHttpSpanExporter` 5s timeout
   is unchanged.
2. **OTel init moved from lazy (first span) into `configure()`** — when APM URL + dataKey are present,
   `configure()` now calls `initOpenTelemetry(...)` directly at cold start (off the request path).
   `ensureInitialized()` is retained as a cheap idempotent guard (double-checked `synchronized`;
   no-op when the tracer is already set) so `startSpan`/`startRootSpan`/`startConsumerSpan` still
   work whether or not init already ran. Building the exporter makes no network call (export is
   deferred to `span.end()`), so this adds no cold-start network latency.
3. **No method signatures changed.** The `injectTraceContext` / `startConsumerSpan` extract/inject
   trace-propagation contract is byte-identical across all three — the distributed trace stays intact.
   Class/field/method Javadoc + inline comments were updated to describe the new eager-init +
   synchronous-export behavior (comment-only; applied identically to all three).

## Resources / OCIDs

Three images rebuilt and pushed at **tag 0.0.2** to `gru.ocir.io/gr2o2hdgzoxw/serverless-app`
(same OCIR repo as the 0.0.1 images). No infra changed — no OCIDs created.

| Image URI | Push digest |
|---|---|
| `gru.ocir.io/gr2o2hdgzoxw/serverless-app/func-event-producer:0.0.2`      | `sha256:a5831318d7508250c75992a2297a088686d56dcc47fb816e8080ae4a82a9f440` |
| `gru.ocir.io/gr2o2hdgzoxw/serverless-app/func-evt-consumer-notify:0.0.2` | `sha256:ca888b71219e234aff3b7dd72f503990ea28463a123f6c1d338132be9f95fd09` |
| `gru.ocir.io/gr2o2hdgzoxw/serverless-app/func-evt-consumer-audit:0.0.2`  | `sha256:89652846b3f4c287f89b6f0b08585d78c6eccac4720bed7cc79f35adf1466bfc` |

Built `linux/amd64` via each service's `build-push.sh 0.0.2`. OCIR `docker login` to `gru.ocir.io`
succeeded on every push (session valid; no auth error). JVM pinned to Corretto 21
(`JAVA_HOME=$(/usr/libexec/java_home -v 21)`) for all Maven/Docker steps.

## Validation

- **Identical-except-package proof** — `diff` between every pair of the three files shows only line 1
  (the `package` declaration) differs. Bodies with line 1 stripped share one md5
  (`8ab1719d25a126bfc4d23bf2d63c0ce7`). No `BatchSpanProcessor` reference remains in `src/main`
  except the Javadoc sentence that explains *why* it is avoided; `SimpleSpanProcessor` present in all three.
- **`mvn -q test`** (Corretto 21, all green):
  - `func-event-producer` -> Tests run: 7, Failures: 0, Errors: 0 — BUILD SUCCESS
  - `func-evt-consumer-notify` -> Tests run: 6, Failures: 0, Errors: 0 — BUILD SUCCESS
  - `func-evt-consumer-audit` -> Tests run: 5, Failures: 0, Errors: 0 — BUILD SUCCESS
  - **18 total, 0 failures.** No test asserted on `BatchSpanProcessor`, so **no test needed updating.**
  - (Audit image build also re-ran `mvn package` tests inside the Dockerfile -> third green confirmation.)
- **`scripts/preflight.sh`** on each service -> all checks pass (Dockerfile CMD present, jersey3 HTTP
  provider present, no credentials in func.yaml, Docker running, initError pattern present).
- **Did NOT run `terraform apply`** (a separate agent owns deploy) and did **not** touch `infra/`.

## Acceptance status

- [x] `SimpleSpanProcessor` swap applied identically to all 3 (diff proof: only package line differs)
- [x] OTel init moved into `configure()`; `ensureInitialized()` kept as idempotent guard; thread-safety preserved
- [x] No method signatures changed; inject/extract propagation contract byte-identical across all 3
- [x] `mvn test` green in all 3 (7 + 6 + 5 = 18, 0 failures)
- [x] `preflight.sh` passes on all 3
- [x] 3 images built + pushed at tag 0.0.2 to the 0.0.1 OCIR repo (digests captured)
- [x] No `terraform apply`, no `infra/` changes

## Next action

Images are ready. Hand off: run `/deploy-function` (`@oci-deployer`) — point the three functions at
their `:0.0.2` images and `terraform apply` (per `diagnosis-report.md`, also bump the two consumers to
`memory_in_mbs = 1024` via `-var`, since tfvars is permission-blocked). Then re-verify fan-out
(`ErrorsAtTarget` stops) and confirm the producer->stream->both-consumers distributed trace + the
transaction-path dashboard now show data in OCI APM. Context: this file + `docs/handoff/event-pubsub/diagnosis-report.md`.

## Open issues / blockers

- The tracing fix removes the *"Failed to export spans"* error and makes spans actually reach APM, but
  it does **not** by itself fix the cold-start-over-SCH-timeout root cause from `diagnosis-report.md`.
  The memory bump (256 -> 1024 MB) for the two consumers is still required at deploy and is out of Java
  scope (Terraform `-var`, owned by @oci-deployer / @oci-terraform).
- With `SimpleSpanProcessor`, `span.end()` now blocks on the OTLP HTTP POST (5s exporter timeout). This
  is intended (spans must flush before the container freezes) and fits the 60s function timeout, but it
  adds up to ~5s per exported span to on-request latency if APM is slow/unreachable — export failures
  are still caught and logged at DEBUG, never breaking the handler.
