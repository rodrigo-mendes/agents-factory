---
kind: report
from: "@oci-debugger"
to: "@oci-deployer"
refs: deploy-report.md, report-terraform-infra.md
capability: event-pubsub
outcome: success
createdAt: 2026-07-21T22:43:51Z
---

## What changed

- Diagnosis only — @oci-debugger never edits code. No files touched.
- Local diagnostic containers created and removed (fnlocal-audit*, cleaned up).

## Root cause

The consumer functions are **NOT broken** — they return HTTP 200 and log correctly.
The failure is **cold-start latency exceeding the Service Connector Hub target-invoke
timeout**. Each SCH delivery hits a cold container; the cold start takes ~62s end-to-end
(measured live: FDK "Served function invocation request in 62.434 seconds"). The SCH gives
up before the cold start finishes -> records `ErrorsAtTarget` -> retries -> triggers another
cold start -> permanent failure loop. The "zero logs / hang" the deployer saw was the
observation window / client timeout (90s) closing before the ~62s invocation flushed.

Dominant cost: **~55s between "Received function invocation request" and the first user
log** — platform container provisioning + JVM pre-main class-loading of the large classpath
(OpenTelemetry SDK + Jersey3 + OCI SDK + logback = 67 dependency jars) on a
**256 MB memory allocation (~0.17 vCPU)** under `-XX:+UseSerialGC`. The application init
itself is only 2.3s and the handler ~5.4s — both healthy.

Why the producer (same image build, same subnet/NSG/IAM) works but the consumers don't:
the producer is invoked synchronously via API Gateway, which absorbs the first cold start
and steady traffic keeps it warm; the SCH consumers get a cold container on nearly every
bursty delivery and the cold start overruns the SCH invoke timeout.

**Audit and notify share the identical root cause** — same 256 MB sizing, same heavy OTel
classpath, same cold-start profile. httpbin egress (notify) is a red herring; audit has no
egress and fails identically.

## Evidence

- **Live direct invoke of audit returned 200** (not a hang): headers
  `Fn-Fdk-Version: fdk-java/1.1.11`, `Fn-Fdk-Runtime: java/OpenJDK 17`, empty body (correct
  for void ConnectorHubFunction). Cold call ~82s wall; warm call ~17s.
- **Live OCI Logging timeline for the invoke** (log `...f6h74nfhwc`), event_id=live-diag-1:
  - 22:35:08.913  Received function invocation request
  - 22:36:03.644  JUL-to-SLF4J bridge installed     <- 54.7s gap (platform+JVM pre-main)
  - 22:36:05.466  AuditConsumerFunction COLD_START completed in 2318ms
  - 22:36:05.940  BATCH received | records=1
  - 22:36:06.445  AUDIT event | event_id=live-diag-1 ...
  - 22:36:11.330  BATCH complete | records=1
  - 22:36:11.347  Served function invocation request in **62.434 seconds**
- **Local docker run of the exact deployed image (`func-evt-consumer-audit:0.0.1`)** with the
  real app config (COMPARTMENT_OCID + APM_DOMAIN_URL + APM_DATA_KEY): returns 200, full logs,
  MonitoringClient + OTLP paths exercised; warm invoke 66ms. RP-provider failure in
  configure() degrades fast (caught) — never blocks. => image/code/CMD/manifest/logback all good.
- **Ruled out (all verified good, identical to working producer):**
  - CMD/func.yaml cmd match; `::handler`; handler signature `void handler(ConnectorHubBatch<T>)`
    matches fn-events 1.1.11 abstract method (javap-confirmed).
  - logback.xml packaged at jar root -> ConsoleAppender to stdout (not the zero-logs cause).
  - pom.xml has fn-events + oci-java-sdk-common-httpclient-jersey3 (HTTP provider present).
  - IAM: `policy-streaming-serverless-dev` has
    `Allow any-user to use fn-invocation ... where request.principal.type='serviceconnector'` (present).
  - Network: functions NSG egress 0.0.0.0/0 all; route table has NAT (internet) + Service
    Gateway (OCI services). Producer and both consumers share the SAME subnet + SAME NSG.
- Image size 2.28 GB (uncompressed) — dominated by the fnproject base JDK layers; app jars
  are 16 MB (67 jars). The bloat that matters for cold start is the **number/weight of
  classpath jars to load under low CPU**, not the OCIR pull.

## Exact fix

Primary lever — cut cold start under the SCH timeout. Apply BOTH:

1. **Increase consumer memory 256 -> 1024 MB** (raises CPU from ~0.17 to ~0.67 vCPU, which is
   the single biggest cold-start reducer for a JVM loading a heavy classpath). Terraform var
   for both `func-evt-consumer-audit` and `func-evt-consumer-notify`:
   - `infra/.../functions` `memory_in_mbs = 1024` (from 256) — set via the per-function
     `var.functions` entry / `-var` used at apply (tfvars is permission-blocked; pin via `-var`).

2. **Move OTel SDK init off the request path.** In
   `services/func-evt-consumer-{audit,notify}/src/main/java/.../obs/TracingSupport.java`,
   `initOpenTelemetry(...)` is currently triggered lazily by `ensureInitialized()` on the FIRST
   span (inside the handler), adding ~0.5-6s to the first invocation and re-running on every
   cold container. Move it into `configure(RuntimeContext, String)` (cold-start) so the first
   SCH invocation isn't charged for exporter setup, OR keep lazy but only if memory bump alone
   doesn't get the p99 cold start comfortably under the SCH timeout. (Owner: @oci-functions-java.)

Secondary (optional, if cold start must go lower):
- Trim the classpath: the tracing path pulls the full OTel SDK + OTLP + okhttp sender. If APM
  is not essential for the audit consumer, gating OTel behind config already exists — but the
  jars still load. Consider a slimmer exporter or shading to fewer jars.
- Confirm/raise the SCH target-invoke timeout if it is configurable on the connector; but the
  durable fix is reducing cold start, not lengthening the timeout.

## Classification

**config** (memory sizing via Terraform `-var`) + **code** (move OTel init to cold-start).
NOT infra-network, NOT IAM, NOT a broken image.

## Next action

Hand off: run `/deploy-function` (`@oci-deployer`) to re-apply the two consumer functions with
`memory_in_mbs = 1024` (pinned via `-var`, tfvars is permission-blocked) and, after
@oci-functions-java moves OTel init to `configure()`, rebuild + redeploy 0.0.2 for both
audit and notify. Then re-verify fan-out (`ErrorsAtTarget` stops, both consumers log the same
event_id). Context: this file.

## Open issues / blockers

- Session was valid to 2026-07-22 00:43; all live OCI calls completed before expiry. No 401.
- The 55s pre-main gap is partly platform container-provisioning latency (outside our control);
  the memory bump + OTel-init move target the JVM/class-load portion, which is the part that
  pushes total over the SCH timeout. If p99 still overruns after 1024 MB, escalate to 2048 MB.
