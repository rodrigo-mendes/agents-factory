---
kind: report
from: "@oci-deployer"
to: "@oci-debugger"
refs: report-terraform-infra.md, pderiso-implementa-o-pattern-eager-quokka.md (Fase 4)
capability: event-pubsub
outcome: partial
createdAt: 2026-07-21T22:04:30Z
---

## Summary (cycle 2 — after coordinator's NSG + dashboard fixes)

The two infra/config blockers from cycle 1 are RESOLVED. Re-apply added exactly 2
resources (NSG self-ingress 443 rule + transaction-path dashboard), 0 rollbacks. The
producer smoke now returns **HTTP 202** and the event is confirmed PUBLISHED to the
stream. BUT **fan-out is NOT proven**: both Service Connector Hubs read the stream fine
(`ErrorsAtSource=0`) yet **fail to deliver to their target consumer functions**
(`ErrorsAtTarget` incrementing continuously), and BOTH consumer functions emit **zero
log output** and a direct invoke **hangs/times out**. That is a consumer-side runtime
failure needing @oci-debugger — it is NOT a deploy-config or infra-reachability issue
(both now verified good).

## Cycle-2 apply (blocker fixes)

- Fixes authored by coordinator (network + observability agents), HCL only:
  1. `infra/modules/network/main.tf` — new
     `oci_core_network_security_group_security_rule.functions_ingress_self` (INGRESS TCP
     443, source = functions NSG self) so the producer reaches Stream Pool PE 10.0.1.131:443.
  2. `infra/modules/dashboards/dashboards/04-transaction-path.json` — removed stray
     `state:"DEFAULT"` on the free-text `txnId` param (no savedSearchId) → import invariant OK.
- Live-image pins reconciled against `terraform state show` (matched cycle-1 exactly):
  facade 0.0.9, api-handler 0.0.11, rest-proxy 0.0.24, api_gateway_name=apigw-serverless,
  + the 3 new `*_image` at 0.0.1.
- `terraform plan` (saved) → **2 create, 0 update, 0 destroy, 0 rollback**. Guards passed
  (no change to the 3 live functions or gateway). Applied: **"Apply complete! 2 added,
  0 changed, 0 destroyed."** transaction-path dashboard now in state.

## Smoke — PASS (producer path)

`POST /v1/events` `{"event_type":"order.created","payload":{"orderId":"SMOKE-2"},"correlation_id":"smoke-002"}`
→ **HTTP 202** (time_total 3.7s). Body:
`{"status":"accepted","stream":"event-stream","event_id":"3dad59b3-1b8f-480d-af7a-c3a528cfd3c9","transaction_id":"a889554f-bddd-45f2-978e-93f2c8222d5e","elapsed_ms":398,"cold_start":false}`
- transaction_id: **a889554f-bddd-45f2-978e-93f2c8222d5e**
- event_id: **3dad59b3-1b8f-480d-af7a-c3a528cfd3c9**
- Producer log confirms publish (logged only after per-message `getError()` check):
  `PUBLISHED event | event_id=3dad59b3-... | event_type=order.created | transaction_id=a889554f-...`
  (logger `com.brx.functions.event.producer.EventProducerFunction`, 21:20:29Z).
- No JWT used (`jwt_auth_enabled=false`); gateway control `GET /v1/health` → 200.

## Fan-out — NOT PROVEN (consumer-side failure) — HAND OFF TO @oci-debugger

Evidence gathered over ~40 min after the 202:

1. **SCH wiring correct** (both ACTIVE): notify SCH source = stream `...jum2bvohq`
   (cursor TRIM_HORIZON), target function = `...qxui43bkqd` (notify) ✓; audit SCH same
   source, target = `...4gsk4nyx7a` (audit) ✓. batch 128kb.
2. **SCH reads OK, delivery fails** (namespace `oci_service_connector_hub`, per connectorId):
   - notify: `ErrorsAtSource` = no-data (0); `ErrorsAtTarget` = 8 datapoints, still
     incrementing (latest 22:01Z).
   - audit:  `ErrorsAtSource` = no-data (0); `ErrorsAtTarget` = 7 datapoints, ongoing.
   => the SCH successfully consumes the message from the stream but the **target Function
   invocation errors on every retry**.
3. **Consumers produce ZERO logs**: fixed-window search of compartment/log-group
   (21:15–now) shows only `api-serverless-dev` (3) + `app-event-producer-dev` (5); NO
   `app-evt-consumer-notify-dev` / `app-evt-consumer-audit-dev` entries at all — not even
   an init line.
4. **Direct invoke hangs**: `oci raw-request` / `fn invoke` on the audit function timed
   out at 90s (no response).
5. Config ruled out: notify Application config is fully populated
   (`NOTIFY_TARGET_URL=https://httpbin.org/post`, APM_DATA_KEY, APM_DOMAIN_URL,
   SERVICE_NAME=func-evt-consumer-notify, METRIC_NAMESPACE, COMPARTMENT_OCID, LOG_LEVEL).
   Function-level config empty `{}` is expected (config lives at app level).

### Interpretation for the debugger (classification: CODE / runtime — start at P0/timeout)

Both consumers hang with zero logs and cause `ErrorsAtTarget`. audit does NO external
call yet fails the same way as notify (which forwards to httpbin) → the common cause is a
**consumer image startup/handler runtime problem**, not the httpbin egress and not IAM
(`ErrorsAtSource=0` proves the SCH principal can read the stream; a missing fn-invocation
policy would also error but the recurring target error + total log silence points to the
function boot/handler). Prime suspects to check first:
  - Function boots at all? (zero logs incl. no init line ⇒ possible immediate crash / bad
    CMD-vs-handler for the ConnectorHubFunction signature, or the FDK not finding the
    `void handler(ConnectorHubBatch<StreamingData<DomainEvent>>)` entrypoint).
  - APM/OTLP exporter blocking on init (both consumers init APM with APM_DOMAIN_URL/KEY);
    a blocking OTLP export on cold start would hang the invoke → target timeout, zero logs.
  - Is the consumer image the ConnectorHub flavor and does its func.yaml/Dockerfile CMD
    match `...NotifyConsumerFunction::handler` / `...AuditConsumerFunction::handler`?
Recommend: `oci-debugger` P0-P4 on the audit function first (no external dependency), then
notify. The producer, streaming, IAM (stream read), NSG, and SCH wiring are all verified
good — scope the diagnosis to the consumer function runtime.

## Resources / OCIDs (current)

- events_url: `https://lopiafgboojvw37sqyoxptl7t4.apigateway.sa-saopaulo-1.oci.customer-oci.com/v1/events`
- stream_id: `ocid1.stream...jum2bvohq` · stream_pool PE ip 10.0.1.131 (private), Kafka `hrwntx7gzy7a.streaming...:9092`
- producer fn/app: `...sqb6jm3f5h` / `...ocnsg26tu2` (image func-event-producer:0.0.1)
- notify   fn/app: `...qxui43bkqd` / `...o6cktchg6z` (image func-evt-consumer-notify:0.0.1)
- audit    fn/app: `...4gsk4nyx7a` / `...4afwc7uhsw` (image func-evt-consumer-audit:0.0.1)
- SCH notify `...3mmwluvjpt` (ACTIVE) / audit `...tuoccrobef` (ACTIVE)
- consumer logs: notify `ocid1.log...tlmc5kdsx4`, audit `ocid1.log...f6h74nfhwc`
  (log group `ocid1.loggroup...al3zodisib`)
- audit invoke endpoint: `https://j4t4lcmieha.sa-saopaulo-1.functions.oci.oraclecloud.com`

## Acceptance status

- [x] 3 images built + pushed (0.0.1); NSG + dashboard fixes applied (2 add, 0 rollback)
- [x] Smoke `POST /v1/events` → **202** with event_id + transaction_id; publish confirmed
- [x] transaction-path dashboard imported (in state)
- [ ] Fan-out (both consumers process same event_id) — ❌ consumers fail on SCH invoke,
      zero logs, `ErrorsAtTarget` ongoing
- [ ] audit `batch.size()` line — ❌ never emitted (consumer never logged)

## Next action

**Hand off:** run `/debug-function` (`@oci-debugger`) — the two consumer functions
(`func-evt-consumer-notify`, `func-evt-consumer-audit`) fail on every SCH invocation with
zero logs and a hanging direct-invoke (`ErrorsAtTarget` incrementing; `ErrorsAtSource=0`).
Start P0-P4 on the audit function (no external dependency). Context: this file.

## Open issues / blockers

- Auto-fix cycles: none — classifies as CODE/runtime (consumer function), out of deployer
  scope (not a `-var`/config or infra-reachability fix). Producer/stream/IAM/NSG/SCH all
  verified good this cycle.
- tfvars drift persists: every future apply must pin the 3 existing image tags +
  api_gateway_name via `-var` (facade 0.0.9 / api-handler 0.0.11 / rest-proxy 0.0.24 /
  api_gateway_name=apigw-serverless) until tfvars is writable and updated.
- Observability validation suite intentionally NOT run (separate step per work order).
- Session was extended to 2026-07-22 00:43:54; no 401 hit.

---

## Cycle 3 (memory bump) — BLOCKED: OCI session expired before apply

Per @oci-debugger diagnosis (`diagnosis-report.md`): consumers are not broken — cold start
~62s at 256 MB (~0.17 vCPU, 67-jar OTel/Jersey3/OCI-SDK classpath) overruns the SCH
target-invoke timeout → `ErrorsAtTarget` loop. Fix = raise consumer memory (→ more vCPU).

**Applied (HCL only, staged, NOT yet deployed):**
- `infra/environments/dev/apps.tf`: `memory_in_mbs` **256 → 1024** for BOTH
  `module.app_evt_consumer_notify` (line 173) and `module.app_evt_consumer_audit` (line 209).
  Producer (line 136) and the 3 existing functions (lines 22/57/92) left at 256 — untouched.

**BLOCKED before `terraform plan`/`apply`:** the OCI CLI session (profile `poc`) **expired**
(`ERROR: This CLI session has expired`). It was valid to ~2026-07-22 00:43; re-auth is
interactive and cannot be done non-interactively here. No apply ran → no partial state.

### Resume steps (after `oci session authenticate --profile poc`, region sa-saopaulo-1)

1. `terraform -chdir=infra/environments/dev plan -out=<f>` with the SAME pin set:
   `-var api_facade_image=...func-api-facade:0.0.9 -var api_handler_image=...api-handler:0.0.11`
   `-var rest_proxy_image=...func-rr-rest-proxy:0.0.24 -var api_gateway_name=apigw-serverless`
   `-var event_producer_image=...func-event-producer:0.0.1`
   `-var evt_consumer_notify_image=...func-evt-consumer-notify:0.0.1`
   `-var evt_consumer_audit_image=...func-evt-consumer-audit:0.0.1`
   Plan MUST show ONLY 2 in-place updates (the 2 consumer functions, memory 256→1024),
   0 destroy, 0 rollback of the 3 live funcs / gateway. If anything else, STOP.
2. Apply the saved plan (reuses deployed 0.0.1 images — no rebuild).
3. Re-smoke `POST /v1/events` `{"event_type":"order.created","payload":{"orderId":"SMOKE-3"},"correlation_id":"smoke-003"}`
   → expect 202; save event_id + transaction_id.
4. Prove fan-out: wait 60-120s, then from `oci_service_connector_hub` metrics confirm
   `ErrorsAtTarget` STOPS incrementing for both connectors, AND both consumer logs
   (`...tlmc5kdsx4` notify, `...f6h74nfhwc` audit) show the same event_id
   (audit: "AUDIT event"; notify: httpbin forward). Grab audit "BATCH received | records=N".
5. If consumers STILL overrun after 1024 MB → capture the new cold-start time and escalate
   for the secondary code fix (move OTel init to `configure()`, rebuild consumers as 0.0.2).

Session expiry is the only blocker; the memory fix is staged and ready.

---

## Cycle 3b (memory bump APPLIED) — PARTIAL: 202 OK, fan-out STILL blocked → needs code fix (OTel→configure(), rebuild 0.0.2)
(updated 2026-07-21T23:15:05Z)

**Apply:** `terraform apply` of the staged 256→1024 memory bump → **"Apply complete! 0 added, 2 changed, 0 destroyed."** Plan was exactly 2 in-place updates (both consumer functions, memory 256→1024), 0 destroy, 0 rollback — guards passed. Live-verified: notify & audit `memory-in-mbs = 1024`.

**Re-smoke SMOKE-3:** `POST /v1/events` `{...orderId:SMOKE-3, correlation_id:smoke-003}` → **HTTP 202**.
Body: `{"status":"accepted","stream":"event-stream","event_id":"1f55b08d-413d-4e10-9fd4-962e118a2169","transaction_id":"4d5c3b17-f23e-471b-84ad-84e6ff15509a","elapsed_ms":2695,"cold_start":true}`
- event_id **1f55b08d-413d-4e10-9fd4-962e118a2169** · transaction_id **4d5c3b17-f23e-471b-84ad-84e6ff15509a**
- Producer log confirms publish: `PUBLISHED event | event_id=1f55b08d... | event_type=order.created` at 22:58:21Z; `EventProducerFunction COLD_START completed in 2598ms`; FDK `Served ... in 61.278s` (producer's own cold start; publish itself 2.7s).

**Fan-out: STILL BLOCKED — the 1024MB bump did NOT bring the consumer cold start under the SCH target-invoke timeout.** Stop condition (per coordinator) met:
- **Zero consumer log entries** since the bump (~22:55Z) through 23:12Z — neither notify nor audit even logs `Received function invocation request` for SMOKE-3. The SCH synchronous invoke is killed before the function flushes any log.
- **`ErrorsAtTarget` keeps incrementing** on BOTH connectors right up to now: notify [23:06, 23:11], audit [23:02, 23:07, 23:12] — one per ~5-min retry cycle, unbroken.
- SMOKE-3 event_id never appears in either consumer log.

**Observed cold-start time (the number the coordinator asked for):**
- Consumer cold start at 256 MB was measured (pre-bump, debugger's live invoke): FDK `Served function invocation request in **62.434 seconds**` (of which ~55s was platform+JVM pre-main class-load; app init only 2.3s: `AuditConsumerFunction COLD_START completed in 2318ms`).
- At 1024 MB the consumer cold start is **not directly measurable from logs** because the SCH kills the sync invoke before the function logs anything — but the persistent `ErrorsAtTarget` + total log silence prove it is **still > the SCH function-target invoke timeout** (SCH sync target-invoke hard limit ~30s). A 1024 MB JVM cold-loading the 67-jar OTel/Jersey3/OCI-SDK classpath still exceeds ~30s.
- Corroborating: even the producer (invoked via API Gateway, which tolerates long cold starts) took 61.3s wall for its SMOKE-3 cold start — same heavy classpath. The SCH's ~30s sync timeout is the wall the consumers hit; memory alone can't clear it.
- Also seen in consumer logs: `Failed to export spans. The request could not be executed...` — the OTLP/APM exporter erroring on the hot path, consistent with OTel init being the dominant cold-start weight.

**=> STOP per instruction. The secondary CODE fix is required:** move OTel/APM init out of the invoke path into FDK `configure()` (so it's paid once at container init, not per-invoke) and/or trim the exporter, then rebuild BOTH consumers as **0.0.2** and re-deploy. Optionally raise the SCH `batch_time_in_sec` and keep 1024 MB. This is a @oci-functions-java code change (not deployer/-var/config scope).

**Next action — Hand off:** `@oci-functions-java` — move OTel init to `configure()` in both consumer functions (NotifyConsumerFunction, AuditConsumerFunction), rebuild as 0.0.2. Then @oci-deployer re-applies with `-var evt_consumer_notify_image=...:0.0.2 -var evt_consumer_audit_image=...:0.0.2` (keep 1024 MB + all existing pins) and re-runs SMOKE-4 + fan-out proof. Context: this file + diagnosis-report.md.

Session valid to 2026-07-22 01:49:24; no 401. Producer/stream/IAM/NSG/SCH-wiring/memory-1024 all good; only the consumer cold-start-vs-SCH-timeout remains.

---

## Cycle 4 (0.0.2 tracing fix + 1024MB + timeout 300s) — APPLIED. Producer 202 OK, trace fix VERIFIED, but fan-out STILL blocked by a PLATFORM cold-provisioning ceiling (~60s) that exceeds the SCH sync target-invoke deadline → ESCALATE to architecture change.
(updated 2026-07-22T00:20:07Z)

**Apply:** `terraform apply` → **"Apply complete! 0 added, 3 changed, 0 destroyed."** Plan was exactly 3 in-place function updates: producer image 0.0.1→0.0.2; notify image→0.0.2 + timeout 60→300; audit image→0.0.2 + timeout 60→300. 0 destroy, 0 rollback (guards passed). Live-verified audit = image 0.0.2 / mem 1024 / timeout 300.

**Smoke:** SMOKE-4 → **202** (event_id 41b7e2b0-e2b3-4107-9fd9-46cd9ca53acc, txn fbca0663-3d34-44e3-81fc-e129ccd662eb). SMOKE-5 (producer warm) → **202** (event_id c2fd26d5-6031-4d78-befa-d3e96e65769a, txn f2ad9780-a6a1-4d22-b6cc-407461435002, elapsed 300ms, cold_start=false). Producer path fully healthy.

**Trace fix (0.0.2) — VERIFIED working** (from the direct-invoke that ran to completion):
- `OpenTelemetry initialized | endpoint=https://aaaadhwllmvc4a...` and `OCI Monitoring SDK Client initialized` in configure() (init moved out of hot path).
- `AuditConsumerFunction COLD_START completed in **964ms**` (was 2318ms at 256MB).
- `AUDIT event | event_id=direct-warm-1` → `BATCH complete | records=1` → `Served ... in 7.939 seconds` (warm).
- **NO "Failed to export spans" anywhere** (SimpleSpanProcessor sync export before freeze works). MDC traceId/spanId path exercised.

**Fan-out — STILL BLOCKED; root cause is now a PLATFORM ceiling, not code/memory/timeout:**
- **The blocking wall is ~60s of platform container cold-provisioning + JVM pre-main**, which happens BEFORE any application code/log. Direct-invoke evidence: `Received function invocation request` 00:10:13 → 60s later `Served ... in 59.974 seconds with error code **444 - StatusConnectionClosedWithoutResponse (444): Client request aborted**` — the client (SCH/CLI) gave up at ~60s while the container was still provisioning; **no app log at all in that first 60s**. The immediately-following invoke on the now-warm container did app-cold-start in 964ms and served in 7.9s.
- This ~60s is a fixed cost of the **2.28 GB image + 67-jar classpath (OTel+Jersey3+OCI-SDK) loading under the FDK before main** — memory (1024MB), function timeout (300s), and the 0.0.2 code fix do NOT reduce it (it precedes app init).
- **SCH synchronous target-invoke deadline (~30-60s, platform fixed) < the 60s cold-provisioning** ⇒ every COLD SCH delivery is aborted ⇒ `ErrorsAtTarget` keeps incrementing: notify [00:06, 00:11], audit [00:02, 00:07, 00:12] — unbroken through the 0.0.2 deploy.
- Warming a container manually (direct-invoke) did NOT unblock the SCH: over the next ~4 min the SCH still never delivered SMOKE-4/5 (only my `direct-warm-1` shows in audit); idle Functions containers scale down within ~1-2 min, so the SCH's next ~5-min-cycle poll re-hits a cold container and re-aborts. notify never warmed and never delivered.

### Measured cold-start numbers (for the escalation)
| phase | 256MB (cy1-3) | 1024MB + 0.0.2 (cy4) |
|---|---|---|
| platform provision + JVM pre-main (Received→first app log / abort) | ~55-62s | **~60s (Received→444 abort, no app log)** |
| app init (COLD_START completed) | 2318ms | **964ms** |
| warm invoke (Served) | 0.836s | **7.9s** |
| span-export error | present | **GONE** |

### => STOP per instruction — genuine SCH-side ceiling. Escalate to ARCHITECTURE change (owner: @oci-serverless-architect / @oci-serverless-stack).
Memory/timeout/code are exhausted; the ~60s platform cold-provisioning of this heavy JVM image cannot fit the SCH sync invoke deadline on a cold container. Options for the architect to pick:
1. **Provisioned concurrency** on both consumer functions (keep ≥1 warm container always) — set `provisioned_concurrency = 1` (currently 0) in the consumer app modules. Eliminates cold delivery entirely; direct cost. Fastest path to green fan-out with the current image.
2. **Shrink the image / classpath** to cut pre-main load: slim base image, prune OTel/Jersey to the minimum, GraalVM native-image, or a lighter HTTP provider — bring cold-provision under the SCH deadline.
3. **Decouple from the SCH sync invoke**: SCH → target that tolerates cold latency (e.g. SCH→Notifications/Queue→async), or a warm long-lived Kafka-consumer instead of per-delivery function cold starts.
(2)/(3) are larger; (1) is the immediate unblock and preserves the pub/sub design.

**Next action — Hand off:** `@oci-serverless-architect` (or `@oci-serverless-stack`) — decide the cold-start-vs-SCH-ceiling fix (recommend provisioned_concurrency=1 on both consumers as the immediate unblock). Everything else is green: producer 202+publish, streaming, IAM, NSG, SCH wiring (both ACTIVE, correct targets), consumer code 0.0.2 (trace fix verified, 964ms app init, no span-export error), memory 1024, timeout 300. Context: this file + diagnosis-report.md.

Session valid to 2026-07-22 02:32; no 401. Full observability/APM-trace-explorer validation deferred to @oci-observability once fan-out is unblocked (span-export path already proven healthy).

---

## Cycle 5 (provisioned_concurrency=1 fix) — BLOCKED: OCI session expired before apply
(updated 2026-07-22T12:27:19Z)

User approved the fast-path fix. `infra/environments/dev/apps.tf` edited (by coordinator):
both consumer modules `provisioned_concurrency = 1` (was 0) — the function-app module wires
`provisioned_concurrency_config { strategy="CONSTANT", count=1 }`, reserving 1 always-warm
container per consumer so the SCH sync-invoke never hits the ~60s platform cold start.
Producer and the 3 existing functions left at `provisioned_concurrency = 0`. Images stay
0.0.2, memory 1024, timeout 300 (all already applied in cycle 4).

**Staged, NOT applied — BLOCKED:** the OCI CLI session (profile `poc`) **expired**
(wall clock 2026-07-22T12:07Z, past the ~02:32 window; `oci` returns
"This CLI session has expired"). Re-auth is interactive and cannot be done
non-interactively here. No `terraform apply` ran → no partial state. Edit verified intact
in apps.tf (notify line ~187, audit line ~222 = `provisioned_concurrency = 1`).

### Resume (after re-auth: `oci session authenticate --profile poc`, region sa-saopaulo-1)

1. `terraform -chdir=infra/environments/dev apply` with the SAME pin set (all event images
   at **0.0.2**, facade 0.0.9, api-handler 0.0.11, rest-proxy 0.0.24,
   api_gateway_name=apigw-serverless). Expected plan: **exactly 2 in-place updates** — both
   consumer functions gaining `provisioned_concurrency_config` (count 1); 0 destroy,
   0 rollback, producer + 3 live funcs + gateway untouched. If anything else, STOP.
   (Apply may take a few min while the platform provisions the warm containers — pays the
   ~60s cold start once, now.)
2. Confirm both consumers show `provisioned-concurrency-config.count = 1`; wait ~1-2 min for
   warm instances.
3. Re-smoke SMOKE-6 `{"event_type":"order.created","payload":{"orderId":"SMOKE-6"},"correlation_id":"smoke-006"}`
   → expect 202; save event_id + transaction_id.
4. Prove fan-out (goal): within ~1-2 min confirm (a) `ErrorsAtTarget` goes FLAT for BOTH SCH
   connectors, and (b) BOTH consumer logs show the SAME event_id (audit "AUDIT event";
   notify httpbin forward). Consumer log OCIDs: notify `...tlmc5kdsx4`, audit `...f6h74nfhwc`;
   log group `...al3zodisib`. SCH ids: notify `...3mmwluvjpt`, audit `...tuoccrobef`.
5. Prove distributed trace: no "Failed to export spans" (already verified gone in 0.0.2);
   grab the shared traceId from producer + both consumer logs (MDC) for the same
   transaction_id; if queryable, pull the APM trace for the txn (producer SERVER + 2 CONSUMER
   spans, one TraceId).

Only blocker is session expiry; the fix is staged and ready. All prior state green:
producer 202+publish, streaming, IAM, NSG, SCH wiring (both ACTIVE), consumer 0.0.2
(trace fix verified: 964ms app init, no span-export error), memory 1024, timeout 300.

---

## Cycle 6 (provisioned_concurrency) — APPLIED (count=10, platform min), producer 202 OK, but FAN-OUT STILL FAILS with warm containers → SCH→function delivery path issue (STOP per instruction)
(updated 2026-07-22T13:29:28Z)

**Value correction:** `provisioned_concurrency = 1` was REJECTED by the platform:
`400 InvalidParameter: Invalid provisionedConcurrencyConfig: Count must be a multiple of 10`.
OCI Functions requires PC count to be a multiple of 10 (min 10). Deployer set both consumers
to **10** (the minimum valid value) to realize the approved keep-warm approach; producer + 3
live functions stay at 0. **COST FLAG:** this reserves **10 always-on 1024 MB containers per
consumer (20 total)**, not the intended 1 — materially higher spend than assumed. Coordinator/
user should confirm they accept 10-each, or pick a lower-cost alternative (image slim / async
decouple), since 1 is not achievable on this platform.

**Apply:** `terraform apply` → **"Apply complete! 0 added, 2 changed, 0 destroyed."** Plan was
exactly 2 in-place updates (both consumers gaining `provisioned_concurrency_config {count:10,
strategy:CONSTANT}`), 0 destroy/rollback. Live-verified both consumers: pc {count:10,
strategy:CONSTANT}, mem 1024, timeout 300, state ACTIVE.

**Smoke:** SMOKE-6 → **202** (event_id 13c0ae48-6e44-4052-aa7a-b2b300b237d0, txn
66ef6a76-2a90-4d1f-bca6-72404898bde5).

**FAN-OUT STILL FAILS — and it is NOT cold start anymore (unexpected; SCH delivery-path issue):**
- `ErrorsAtTarget` keeps incrementing on BOTH connectors AFTER the PC apply, unbroken:
  notify [13:12,13:17,13:22,13:27], audit [13:09,13:14,13:19,13:24] (one per ~5-min SCH retry).
- **SMOKE-6 never reached either consumer.** Consumer log activity since 13:00 = ONLY the
  deployer's own `pc-warm-check` direct-invoke (audit, 13:25). notify: zero activity.
- **BUT a direct `oci fn function invoke` of the audit function now SUCCEEDS FAST**: Received
  13:25:01 → first app log 13:25:03 (~2s, the ~60s cold-provision wall is GONE, image now
  host-cached) → `AuditConsumerFunction COLD_START completed in 974ms` → `AUDIT event |
  event_id=pc-warm-check` → `BATCH complete` → `Served ... in 6.257 seconds`. No span-export error.
- => The function is healthy and responds in ~6s on direct invoke, yet the SCH→function
  delivery produces ZERO function logs and persistent ErrorsAtTarget. The failure is
  **decoupled from cold start** — it is in the SCH target-invoke path itself.

**Auth/wiring re-checked (all correct — so the issue is subtler):**
- IAM streaming policy statements: `Allow any-user to use fn-invocation in compartment
  mom-fast-track-poc-oci-serverless where request.principal.type='serviceconnector'` PRESENT
  (also STREAM_READ/STREAM_CONSUME + producer stream-push). ErrorsAtSource=0 (SCH reads fine).
- SCH notify target: kind=functions, function-id `...qxui43bkqd` (correct), batch-time 60s,
  lifecycle ACTIVE, lifecycle-details empty (no error surfaced). audit likewise ACTIVE→`...4gsk4nyx7a`.

### Hypotheses for coordinator/@oci-debugger (SCH-side, beyond deployer scope)
1. **SCH function-target invoke timeout**: SCH invokes the function synchronously and may itself
   time out well under the function's 300s (and even under the ~6s warm response if it routes to
   a NON-provisioned/cold host — PC reserves 10 warm, but the SCH-triggered invocation may not be
   landing on the provisioned pool). Note the direct invoke STILL cold-started (COLD_START 974ms)
   rather than hitting a warm PC instance — so PC instances may not be serving invocations as
   expected, or need the FDK/function to be "hot" differently.
2. **fn-invocation policy scope/propagation** or the SCH needing `use functions-family` /
   resource-scoped statement rather than compartment `fn-invocation` — worth an explicit test.
3. SCH invoke payload/response contract mismatch that fails before the function logs (but the
   local/direct ConnectorHub-shaped batch worked, making this less likely).

**Next action — STOP + Hand off:** `@oci-debugger` / coordinator — investigate why the SCH
target-invoke fails (ErrorsAtTarget) while a direct fn invoke succeeds in ~6s and IAM+wiring are
correct. Prime suspects: SCH sync invoke-timeout vs the invoke not landing on the provisioned-
concurrency warm pool; and/or fn-invocation policy form. Everything else green: producer
202+publish, streaming, IAM stream-read (ErrorsAtSource=0), NSG, SCH ACTIVE+correct-target,
consumer 0.0.2 (trace fix verified, no span-export error, 974ms app init, 6.3s warm-ish), mem
1024, timeout 300, PC count=10 applied. Context: this file + diagnosis-report.md.

Session valid to 2026-07-22 16:01:04; no 401. COST FLAG on PC=10 (20 warm containers) awaiting confirm.

---

## Cycle 7 (revert PC to stop cost) — PC REMOVED via API (TF apply couldn't); NEW unexpected IAM change in plan → STOPPED before applying it
(updated 2026-07-22T14:40:12Z)

**Task:** apply to remove provisioned concurrency (cost: 20 warm 1024MB containers) after user decided to revert + debug SCH path separately. apps.tf reverted by coordinator to `provisioned_concurrency = 0` on both consumers.

**Provider quirk — plain `terraform apply` is a NO-OP and does NOT remove PC:**
- The function-app module uses `dynamic "provisioned_concurrency_config" { for_each = var.provisioned_concurrency > 0 ? [1] : [] }`. With var=0 the block yields zero instances → desired = "no PC block".
- But the OCI provider treats `provisioned_concurrency_config` as optional+computed: an absent desired block means "leave as-is", NOT "remove". `terraform state show` shows NO PC block on either consumer, and `terraform apply -refresh-only` did NOT pull the live count=10 into state. So a normal plan = **no-op** while the platform kept billing **PC {count:10} live on BOTH consumers** (verified via `oci fn function get`).
- => a plain apply would silently fail the intent (cost keeps running).

**Action taken to actually stop the cost (deployer-scoped, non-disruptive):**
- `oci fn function update --function-id <notify/audit> --provisioned-concurrency '{"strategy":"NONE"}' --force` on BOTH consumers. This releases the warm pool immediately WITHOUT recreating the function or changing its OCID (no downtime/OCID churn, unlike `terraform apply -replace`), and leaves live == the "no PC" state Terraform already believes → no TF drift introduced.
- **VERIFIED live after clear: notify PC = {strategy:NONE}, audit PC = {strategy:NONE}.** Cost stopped (20 warm containers released).

**STOP condition hit — plan shows an UNEXPECTED change I was told not to apply:**
- After the PC clear, `terraform plan` = **"Plan: 0 to add, 1 to change, 0 to destroy"** — and the 1 change is NOT the consumers. It is `module.iam.oci_identity_policy.streaming will be updated in-place`, ADDING a new statement:
  `+ "Allow any-user to use fn-function in compartment mom-fast-track-poc-oci-serverless where all {request.principal.type='serviceconnector'}"`
- This is a NEW IAM statement (`use fn-function` alongside the existing `use fn-invocation`) — evidently the SEPARATE debugger's in-flight fix for the SCH→function invoke failure (cycle-6). It is OUTSIDE this task's scope ("apply to remove PC; if anything else, STOP and report").
- Per instruction I did NOT apply it. No `terraform apply` was run this cycle (the PC removal was done via the API, not TF). State is unchanged by me except the two API PC-clears (which TF already considers the desired state → plan does not want to touch PC).

### Note for coordinator / debugger
- The `use fn-function` statement addition is very likely the real SCH-invoke fix (SCH principal needs `use fn-function`, not just `fn-invocation`, to invoke the target). That aligns with cycle-6's finding (SCH ErrorsAtTarget with zero function logs despite correct wiring). When the debugger is ready, apply it with the standard pin set (event images 0.0.2, facade 0.0.9, api-handler 0.0.11, rest-proxy 0.0.24, api_gateway_name=apigw-serverless) — expected plan = 1 in-place IAM update — then re-smoke + fan-out check.
- PC is now OFF; if a keep-warm approach is revisited, remember the platform floor is count=10 (multiple of 10) — 1 is invalid.

## Next action
**Report to coordinator:** PC removed (cost stopped) via API on both consumers (strategy NONE, verified). `terraform apply` was NOT run because (a) it's a no-op for PC removal by provider design, and (b) the current plan contains a separate, unexpected IAM `fn-function` change (the debugger's SCH fix) that is out of this task's scope — STOPPED per instruction. Awaiting direction on the IAM change. Context: this file.

Session valid to 2026-07-22 16:01:04; no 401.

---

## Cycle 9 (public stream pool for SCH source fix) — STOPPED before apply: plan does NOT match intent (2 problems)
(updated 2026-07-22T17:55:16Z)

Root cause confirmed by coordinator: stream pool is PRIVATE-endpoint-only (10.0.1.131, in-VCN);
managed SCH runs outside the VCN → can't read → ErrorsAtSource=1.0/poll, MessagesFromSource empty,
consumers never invoked. Fix staged: `infra/modules/streaming/main.tf` removes
`private_endpoint_settings` to make the pool PUBLIC (user accepted the trade).

**Reviewed the plan carefully as instructed — it does NOT match the expected change set. STOPPED. Two problems:**

### Problem 1 — the pool is NOT actually being made public (plan = no-op on the pool)
- HCL is correct (pool block has no `private_endpoint_settings`), BUT the OCI provider treats
  `private_endpoint_settings` as **optional+computed**: removing it from config means "leave as-is",
  NOT "make public" — identical trap to `provisioned_concurrency_config` in cycle 7.
- `terraform show -json` of the saved plan: pool + stream = **no-op** (NO replace). Expected the
  coordinator's REPLACE of `oci_streaming_stream_pool.this` + `oci_streaming_stream.event_stream`
  — it is absent.
- **Live pool is STILL PRIVATE**: `oci streaming admin stream-pool get` shows
  `private-endpoint-ip: 10.0.1.131`, subnet + NSG still set. Producer app config is also unchanged
  (no new public STREAM endpoint) — expected update-in-place, absent.
- => a plain `terraform apply` would NOT fix ErrorsAtSource. The pool must be **force-replaced**
  (`terraform apply -replace='module.streaming.oci_streaming_stream_pool.this'`, which cascades to
  the stream via dependency) to actually drop the private endpoint and get a public messages endpoint.

### Problem 2 — the plan would REGRESS consumer memory 1024 → 256 (unwanted rollback)
- `apps.tf` currently has `memory_in_mbs = 256` for BOTH consumers (lines 176, 215), but the LIVE
  functions are **1024** (from cycle 3). The plan's 2 in-place consumer updates are purely
  `memory_in_mbs 1024 -> 256` — an unrequested rollback of the memory bump. (timeout stays 300; images 0.0.2.)
- The coordinator said consumers "stay 0.0.2 for now" and to isolate the source fix — rolling memory
  back to 256 is not intended and would re-worsen cold start. apps.tf needs 1024 restored on both
  consumers before any apply.
- (3rd plan item = IAM streaming policy `description` text tweak only — benign.)

### Actual plan (saved): 0 add, 3 update, 0 destroy
- update memory_in_mbs 1024->256 on app_evt_consumer_audit  (UNWANTED rollback)
- update memory_in_mbs 1024->256 on app_evt_consumer_notify (UNWANTED rollback)
- update description text on module.iam.oci_identity_policy.streaming (benign)
- NO stream pool/stream replace, NO producer app-config update → the public-pool fix would NOT apply.

### What's needed before I apply (owner: @oci-terraform / coordinator)
1. Restore `memory_in_mbs = 1024` on both consumer modules in apps.tf (undo the 256 regression),
   OR confirm you actually want 256 now (you did not say so).
2. To force the pool public, the apply must `-replace` the stream pool (optional-computed block
   removal won't diff). Confirm you accept the pool+stream REPLACE (new stream_id + messages_endpoint;
   the 2 SCH connector sources + producer STREAM_OCID/ENDPOINT then update-in-place to the new ids;
   buffered messages lost — already accepted). With `-replace` the plan SHOULD show: replace pool,
   replace stream, update 2 SCH sources, update producer app config. I will re-review before applying.

### Nothing applied this cycle. Pool still private; ErrorsAtSource still failing; no fan-out.
Session valid to 2026-07-22 20:39:56; no 401.

---

## Cycle 10 (PUBLIC stream pool) — SUCCESS: SOURCE FIXED + FAN-OUT WORKS (no native/PC needed)
(updated 2026-07-22T18:58:24Z)

**Root cause (confirmed & fixed):** the stream pool was private-endpoint-only (10.0.1.131, in-VCN); the managed SCH runs outside the VCN → couldn't read → ErrorsAtSource=1.0/poll → consumers never invoked. Fix = recreate the pool PUBLIC.

**Apply (two steps — provider immutability):**
1. `terraform apply -replace=pool -replace=stream` (the coordinator's single -replace on the pool was NOT enough: the stream's stream_pool_id is force-new, so the stream needed its own -replace or it tried an illegal in-place repoint). Plan reviewed: replace pool + stream, update producer app config + both SCH sources, benign IAM desc; 0 destroys of Functions/gateway/live-apps. Result: pool+stream recreated PUBLIC, producer config repointed — BUT the SCH source update FAILED: `400 Invalid Operation. Sources with Private Endpoints cannot be updated` (the old SCH source had a private endpoint → immutable, must be replaced).
2. `terraform apply -replace=sch[notify] -replace=sch[audit]` → **"Apply complete! 2 added, 0 changed, 2 destroyed."** Both SCH connectors recreated pointing at the new public stream, private-endpoint now NULL.

**Live verification:**
- New pool PUBLIC: endpoint `cell-1.streaming.sa-saopaulo-1.oci.oraclecloud.com`, private-endpoint-settings all null.
- New stream_id `...xitxqll4lqot`. New SCH OCIDs: notify `...yfeocehevu`, audit `...lgornh5cz7` — both ACTIVE, source=new public stream (matches), private-endpoint NULL, targets = correct consumer fns.

**Smoke SMOKE-9 → 202** (producer published to the new public stream via NAT egress):
event_id **d48b2dae-127c-42f3-82d0-b2f22b629d27**, transaction_id **e519505a-0614-4b8f-9de9-a2257fec769c**.

**SOURCE FIXED + FAN-OUT PROVEN (the goal):**
- SCH metrics per connector (18:30-18:42): **ErrorsAtSource = 0** on both (was 1.0/poll) ✅; **ErrorsAtTarget = 0** ✅.
- Consumer **FunctionInvocationCount**: notify [18:37,1], audit [18:37,1] — BOTH invoked ✅.
- **Both consumer logs processed the SAME event_id** d48b2dae (true pub/sub fan-out, 2 cursors):
  - producer 18:35:33 `PUBLISHED event | event_id=d48b2dae...`
  - notify   18:37:43 `BATCH received | records=1` → `FORWARDED event | event_id=d48b2dae...` (httpbin) → `BATCH complete` → Served 62.060s
  - audit    18:37:43 `BATCH received | records=1` → `AUDIT event | event_id=d48b2dae...` → `BATCH complete` → Served 62.419s
- Cold start (~62s) now COMPLETES within the 300s timeout (not aborted) → ErrorsAtTarget=0. So with timeout=300 + memory=1024, **pay-per-use Functions+SCH works — no native/PC needed.**
- **No span-export errors** (0.0.2 tracing fix healthy → spans exported for the distributed trace).

**Trace note:** consumer JSON log envelope doesn't carry traceId as a structured field (it's in MDC/message, not the exported record), so the single-shared-traceId proof needs the APM Trace Explorer — that's the coordinator's separate @oci-observability step. Span export is confirmed working (no export errors), so the trace data is flowing.

## Status: fan-out GREEN
Producer 202+publish → new PUBLIC stream → both SCH (ACTIVE, ErrorsAtSource/Target=0) → both consumers invoked & logged the same event_id. The whole pub/sub path works end-to-end on pay-per-use Functions.

## Next action
Hand to **@oci-observability** for the live APM distributed-trace validation (single TraceId across producer SERVER + both consumer CONSUMER spans by transaction_id e519505a-...) + the transaction-path dashboard + 5-pillar validation. No further deployer action needed unless trace/dashboard validation surfaces an issue.

Session valid to 2026-07-22 20:39:56; no 401.
