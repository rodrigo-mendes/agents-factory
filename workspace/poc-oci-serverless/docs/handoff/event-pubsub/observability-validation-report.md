---
kind: report
from: "@oci-observability"
to: user
capability: event-pubsub
task: "Close observability validation for the event-driven pub/sub stack (dev)"
status: partial
outcome: distributed-trace PROVEN; live 5-pillar sweep BLOCKED on OCI session re-auth
createdAt: 2026-07-22T20:55:01Z
---

# Observability Validation — event-pubsub (dev)

Scope: read-only + traffic generation. No infra changes. The transaction-path
render fix was already applied/re-imported by main — NOT touched, NOT re-imported.

ENV: profile `poc`, region `sa-saopaulo-1`, auth `security_token`.

## Traffic generated (task 1)

`POST /v1/events` — `jwt_auth_enabled=false` in dev (per deploy-report), so no
Authorization header needed. All 3 returned HTTP 202.

| # | event_type | event_id | transaction_id | HTTP | cold_start |
|---|-----------|----------|----------------|------|-----------|
| 1 | order.created | de80aa1d-5e1a-4077-b112-4cba6cb3d5ee | 718df4d3-e814-4864-b458-b8507a9625b2 | 202 | true |
| 2 | order.created | 093e435d-39ed-4870-853e-be324b709ca3 | 62e90f1b-eece-4dbb-8001-59870b2ca46d | 202 | false |
| 3 | order.created | 1ad59767-1ab3-4ed6-8b35-1d7caa15ee56 | f3f3d38b-2654-4b18-898e-80139e4804cb | 202 | false |

Stream: `event-stream`. events_url:
`https://lopiafgboojvw37sqyoxptl7t4.apigateway.sa-saopaulo-1.oci.customer-oci.com/v1/events`

## Distributed trace — PROVEN (task 2) ✅

Queried APM (`oci apm-traces query query-response run-query`, domain
`ocid1.apmdomain.oc1.sa-saopaulo-1.amaaaaaa543c4nyadklnrazzyaoz5qrrrrg45bapu5hwnd5eyu2h32bkew4q`).
Grouping all spans by TraceId over the traffic window showed EIGHT traces each
carrying producer SERVER + both consumer CONSUMER spans under ONE TraceId.

**Representative TraceId: `f94cb37be4831757ca2f7edbb04c535f`** (producer SERVER span
StartTime 1784752168418 = 20:29:28Z, matches POST #2 / txn 62e90f1b at 20:29:24Z).

| ServiceName | Kind | OperationName |
|---|---|---|
| func-event-producer | **SERVER** | POST /events |
| func-evt-consumer-audit | **CONSUMER** | consume order.created |
| func-evt-consumer-notify | **CONSUMER** | consume order.created |
| func-evt-consumer-notify | CLIENT | NotifyTarget.forward (downstream REST to httpbin) |

Total spans in this trace: **4** (1 producer SERVER + 2 consumer CONSUMER siblings
+ 1 notify CLIENT downstream). The two CONSUMER spans are siblings, re-parented to
the producer's remote W3C context (`trace.traceparent`) → single distributed trace
across the fan-out CONFIRMED. Same shape reproduced across 8 traces in the window
(order.created / order.paid / order.shipped).

Note on TQL attribute names discovered: SpanKind is exposed as **`Kind`** (values
SERVER/CONSUMER/CLIENT); `SpanKind` selected as a column returns null. Filtering by
`transaction.id` as a bare TQL attribute did not resolve (stored under a differently
named tag) — correlation was done by TraceId grouping + StartTime↔POST timestamp,
which is authoritative.

## 5-pillar sweep (task 3)

The OCI CLI session **expired mid-run** (actual token TTL was shorter than the
stated 22:44; `oci session validate` failed right after the APM queries succeeded).
`oci session refresh` cannot renew it — a full `oci session authenticate` requires
interactive browser login, which this agent cannot complete autonomously. The
`validate-observability.sh` sweep and live `check-dashboards.sh` both aborted at
their `require_session` gate.

| Pillar | Result | Decisive line |
|---|---|---|
| logs | NOT RUN (blocked) | check-logs.sh aborted at require_session (session expired). Earlier raw `logging-search` DID return live API-GW records flowing into the log group, so log pipeline is up — but the scripted assertion did not execute. |
| metrics | NOT RUN (blocked) | check-metrics.sh aborted at require_session. |
| traces | PASS (proven directly) | APM ingesting all 3 services (producer=SERVER, audit+notify=CONSUMER) and single-trace correlation proven live above — the stronger check the scripted pillar approximates via IngestedBytes. |
| alarms | NOT RUN (blocked) | check-alarms.sh aborted at require_session. |
| dashboards (render-readiness) | PASS (static) / live cross-check NOT RUN | Static inspection of all 4 source JSONs: every metric widget has widgetTemplate + dataConfig.type=monitoringDataSource + regionName param; every trace widget has widgetTemplate + dataConfig.type=tracesDataSource. transaction-path "Transaction Path (spans)" tile TQL = `show spans ServiceName, OperationName, SpanDuration, SpanKind where ...` — no TraceStatus (fix confirmed in source, untouched). The 4 residual `TraceStatus` refs are all in the separate "Transaction Status / Errors" tile, which correctly uses `show traces ... TraceStatus` (valid on traces). All 4 dashboards imported (import_ids present in terraform output). Live `check-dashboards.sh` (ACTIVE state + ingestion cross-check) did NOT execute due to session expiry. |

## Follow-up required

Re-authenticate the `poc` session, then run the scripted sweep to close the 4
blocked pillars (all evidence points to green — logs flowing, APM ingesting,
dashboards render-clean):

```
oci session authenticate --profile-name poc --region sa-saopaulo-1
OCI_PROFILE=poc OCI_AUTH=security_token OCI_REGION=sa-saopaulo-1 LOOKBACK_MIN=30 \
  bash .claude/skills/validating-oci-observability/scripts/validate-observability.sh --no-smoke
OCI_PROFILE=poc OCI_AUTH=security_token OCI_REGION=sa-saopaulo-1 \
  bash .claude/skills/validating-oci-observability/scripts/check-dashboards.sh
```
(`--no-smoke` because fresh traffic was already generated; regenerate if the window
has aged out.)

Caveat: `lib-common.sh` `FUNCTIONS_META` / fallback OCIDs still describe the OLD
stack (api-handler/facade/rest-proxy), so the scripted `traces` pillar checks APM
config on the wrong apps and `metrics` won't know the audit custom namespace. The
direct APM proof above supersedes the scripted `traces` pillar for this stack.
