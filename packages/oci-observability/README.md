# oci-observability

APM package — OCI Observability domain knowledge for OCI serverless workloads.

Part of the **OCI family** (`factory-core` + `oci-core` dependencies). Migrated from `poc-oci-serverless`.

## What this package provides

One agent (`oci-observability`) and 10 skills covering all five observability pillars:

| Pillar | Skills |
|---|---|
| APM & distributed tracing | `monitoring-oci-apm`, `monitoring-oci-apm-dashboards` |
| Logging | `designing-oci-logging`, `logging-oci-java-functions` |
| Monitoring alarms | `configuring-oci-monitoring-alarms`, `monitoring-oci-java-functions` |
| Connector Hub | `designing-oci-connector-hub` |
| Full function observability | `observing-oci-java-functions` |
| Live validation | `validating-oci-observability` (10 bundled scripts) |
| Routing command | `observe-oci-workload` → `oci-observability` agent |

## Entry point

```
/observe-oci-workload <capability-slug> [pillar: apm|logging|alarms|connector-hub|dashboards|all]
```

The `oci-observability` agent follows a P0–P5 workflow: verify handoff records → analyze existing
infra → consult loaded skills → propose (wait for approval) → implement → validate.

## Skills index

| Skill | Type | Purpose |
|---|---|---|
| `observe-oci-workload` | action-command | Routes to `oci-observability` agent |
| `monitoring-oci-apm` | knowledge | APM domains, distributed tracing, OTel SDK patterns |
| `monitoring-oci-apm-dashboards` | knowledge | APM Management Dashboard design, widgets, APM QL |
| `designing-oci-logging` | knowledge | Logging architecture, log strategy, retention |
| `designing-oci-connector-hub` | knowledge | Connector Hub data pipeline architecture |
| `configuring-oci-monitoring-alarms` | knowledge | Monitoring alarms, suppressions, custom metric ingestion |
| `monitoring-oci-java-functions` | knowledge | Custom metrics via PostMetricData + oci_faas alarms |
| `logging-oci-java-functions` | knowledge | Structured logging for OCI Java Functions |
| `observing-oci-java-functions` | knowledge | All 3 pillars (logs + metrics + traces) at function level |
| `validating-oci-observability` | knowledge | Live 5-pillar validation via OCI CLI + 10 bundled scripts |

## Key gotchas (live-validated)

- **`MonitoringClient` ingestion endpoint**: `setEndpoint("https://telemetry-ingestion.<region>.oraclecloud.com")` is mandatory — omitting it causes `PostMetricData` to fail **silently** (custom namespace stays empty).
- **`SimpleSpanProcessor` over `BatchSpanProcessor`**: OCI Functions freeze on handler return; background export threads never run. Use `SimpleSpanProcessor` for synchronous span export.
- **OTLP endpoint**: `/20200101/opentelemetry/private/v1/traces` — not `/observations/private` (which causes `PayloadRejections > 0`).
- **`oci_faas` alarm dimensions**: valid values are `applicationId` (Application OCID) or `resourceId` (Function OCID). **`functionId` does not exist** — alarms using it never fire.
- **Dashboard render**: `monitoringDataSource` widgets must declare the `regionName` parameter or widgets render blank. Source of truth: Console `{JSON}` editor, not hand-authored JSON.
- **Dashboard import**: `terraform destroy` does NOT delete imported dashboards/saved-searches. Delete by OCID before re-import or hit `401 RelatedResourceNotAuthorizedOrNotFound`.

## PoC reference code

Java worked examples from `libs/obs-commons/` (path-cited) are embedded in:
- `monitoring-oci-apm/blueprints/always-do-patterns.md` — `TracingSupport.java` (eager init + SimpleSpanProcessor)
- `observing-oci-java-functions/blueprints/integration-patterns.md` — `ObservabilityHelper.java` + `TracingSupport.java`
- `logging-oci-java-functions/blueprints/always-do-patterns.md` — `LoggingBridge.java` + `ObservabilityHelper.java`
- `monitoring-oci-java-functions/blueprints/always-do-patterns.md` — `MetricsPublisher.java`

## Validation scripts

`validating-oci-observability/scripts/` contains 10 Python 3 scripts (standard library only, no `jq`; offline tests: `python scripts/tests/run_tests.py`):

| Script | Purpose |
|---|---|
| `validate-observability.py` | Orchestrator — 4-pillar post-deploy gate |
| `generate-dashboard-traffic.py` | Dashboard precondition — generates load before `check-dashboards.py` |
| `check-logs.py` | Logs pillar |
| `check-metrics.py` | Metrics pillar |
| `check-traces.py` | APM traces pillar |
| `check-alarms.py` | Alarms + notification pillar |
| `check-dashboards.py` | Dashboard render-readiness (5th pillar) |
| `trigger-alarm-test.py` | End-to-end alarm→FIRING→email proof |
| `smoke-invoke.py` | Traffic generator |
| `deploy-and-validate.py` | Full runbook (build + push + apply + validate) |
| `lib_common.py` | Shared config module (imported by the others — do not execute directly) |

All scripts are parametrized via environment variables. No hardcoded OCIDs, tenancy IDs, or profile names.

## Dependencies

```yaml
dependencies:
  apm:
    - path: ../factory-core
    - path: ../oci-core
```
