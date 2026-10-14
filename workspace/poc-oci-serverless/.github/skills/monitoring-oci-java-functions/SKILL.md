---
name: monitoring-oci-java-functions
description: "Instruments OCI Java Functions with custom metrics and alarms using OCI Monitoring API v20180401, FDK Java 1.1.12, and OCI SDK 3.87.0. Use when adding custom metric ingestion, configuring oci_faas alarms, wiring Terraform monitoring stacks, or troubleshooting silent metric loss in OCI Function deployments."
---

## Function

Specialist in OCI Monitoring integration (custom metrics, alarms, suppressions, Metric Streams) for **OCI Functions — Java** deployments. Covers Resource Principal auth, `PostMetricData`, `oci_faas` built-in metrics, MQL alarm queries, and Terraform monitoring infrastructure.

## Version Context

**Technology**: OCI Functions (FDK Java) + OCI Monitoring API
**FDK Java**: v1.1.12 (released 2026-05-08)
**OCI Java SDK**: v3.87.0 (released 2026-05-20)
**OCI Monitoring API**: v20180401 (stable)
**Support Status**: Active

**Breaking changes in SDK 3.x**:
- Jersey3 HTTP client mandatory: `oci-java-sdk-common-httpclient-jersey3` (replaces Jersey2)
- `MonitoringClient` no longer accepts `String region` in constructor — use `.region(Region.X)` builder method

**Deprecated**: Jersey2 HTTP client (`oci-java-sdk-common-httpclient-jersey`) → use Jersey3 equivalent

⚠️ **CRITICAL — Agent Warning**: This skill targets FDK 1.1.12 / OCI SDK 3.87.0. Reject any patterns using Jersey2, API Key credentials, or per-invocation client construction.

---

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 7 mandatory patterns with full Java + Terraform code
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural decisions with tradeoff matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 anti-patterns with ❌ wrong / ✅ correct code
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Complete Java function + Terraform monitoring stack
- **[Verification Loop](#verification-loop)** — Build, test, metric validation commands
- **[Quick Reference](#quick-reference)** — API limits and critical thresholds

---

## Blueprints & Guardrails

### ✅ Always Do

Full code examples → [Always Do Patterns](./blueprints/always-do-patterns.md)

- **Resource Principal auth for `MonitoringClient`** — Never API Key credentials. Missing Dynamic Group → HTTP 401/404 with no platform indication.
- **`@FnConfiguration` static cold-start init** — Creating client per invocation adds 150–400 ms overhead and risks HTTP 429 on OCI metadata service under concurrency.
- **`PostMetricData` with `BatchAtomicity.NonAtomic` + rejection check** — `Atomic` drops all valid datapoints if one fails. Detached thread posts are silently lost at container freeze.
- **Inject `COMPARTMENT_OCID` and `METRIC_NAMESPACE` via function config** — Hardcoding breaks multi-env promotion; dev metrics contaminate prod series.
- **Service Gateway in VCN for private-subnet functions** — Without it, `telemetry-ingestion.*` DNS resolves to public IP unreachable from private subnet → silent metric loss, no function error.
- **Configure alarms on `oci_faas` built-in metrics** — `FunctionInvocationCount`, `FunctionExecutionDuration`, `FunctionThrottleCount`, `FunctionErrorCount` are emitted with zero application code. Not alarming on them leaves a function operationally blind.
- **Set `pending_duration` ≥ PT2M on production alarms** — Default PT1M fires on cold-start spikes → alert fatigue → on-call desensitization → missed real incidents.

### ⚠️ Ask First

Full decision matrices → [Ask First Decisions](./blueprints/ask-first-decisions.md)

- **Metric namespace strategy** — Per-function / per-application / per-domain. Ask: "Do multiple functions share a business domain dashboard?"
- **Batch vs per-event metric posts** — One `PostMetricDataRequest` per item vs batch at invocation end. Ask: "Does each item need individual timing?"
- **Alarm notification destination** — ONS email / HTTPS webhook / PagerDuty / OCI Streaming / OCI Functions auto-remediation. Ask: "Human response < 5 min or automated remediation?"
- **Alarm suppression strategy** — Manual one-time, recurring iCalendar RRULE, or disable (`is_enabled = false`). Ask: "Planned maintenance — one-time or recurring schedule?"
- **Metric Streams for real-time routing** — OCI Dashboards vs Connector Hub → Streaming (Grafana/Prometheus) vs Object Storage (long-term retention). Ask: "Does the team use Grafana or need > 90-day retention?"

### 🚫 Never Do

Full anti-patterns with alternatives → [Never Do Patterns](./blueprints/never-do-patterns.md)

- **API Key credentials in Docker image** — Private key baked into OCIR image; any developer with pull access gains full tenancy API access (OWASP A07:2021).
- **`MonitoringClient` per invocation** — 150–400 ms per call, `BindException` under load, HTTP 429 on metadata service.
- **Fire-and-forget metric posts** — Detached threads and unawaited `CompletableFuture` race with FDK container freeze → silent dashboard gaps.
- **Flat `custom_metrics` catch-all namespace** — Alarm MQL becomes unmaintainable; metric name collisions across services; `ListMetrics` returns hundreds of unrelated entries.
- **Hardcoded `COMPARTMENT_OCID` or namespace in source** — Dev load contaminates prod metric series; blocks environment promotion without recompilation.
- **`pending_duration = PT1M` (alarm default) on production** — Cold-start spikes trigger CRITICAL pages → alert fatigue → genuine incidents missed.
- **Datapoint timestamps > 2 hours old** — OCI Monitoring silently drops them; `PostMetricData` returns HTTP 200 with `rejectedMetricsData`, not an HTTP error.

---

## Integration Patterns

Full Java + Terraform examples → [Integration Patterns](./blueprints/integration-patterns.md)

- **Java Function ↔ OCI Monitoring** — `OrderProcessorFunction`: static init, batch metrics, rejection check, error swallowing
- **Terraform ↔ OCI Monitoring Stack** — Notification topic, 4 alarms (errors/duration/throttle/custom), maintenance suppression, function config wiring
- **FDK testing ↔ `MonitoringClient` mock** — Constructor-injected `MonitoringClient` for unit-testable functions

**Common problems**:
- **`OciMetadataServiceException` at startup** → Dynamic Group misconfigured or IAM policy missing. Halt deployment.
- **HTTP 429 on `PostMetricData`** → Batch multiple `MetricDataDetails` per request; implement exponential backoff. 50 TPS shared per region.
- **`No data` in `oci_faas` namespace after deploy** → OCI Functions Application logging/metrics not enabled in Application settings.
- **Connection timeout to `telemetry-ingestion.*`** → Service Gateway missing or private route table not configured.

---

## Verification Loop

Execute after each code generation cycle:

### 1. Build Function Image
```bash
fn build
# Expected: Successfully built <image>:<tag>
# Exit code: 0
```

### 2. Unit Tests + Dependency Check
```bash
mvn test
# Expected: BUILD SUCCESS; 0 failures

mvn dependency:tree | grep -E "httpclient|jersey"
# Expected: oci-java-sdk-common-httpclient-jersey3 present; NO jersey2 artifact
```

### 3. Deploy + Metric Smoke Test
```bash
fn deploy --app <app-name>
echo -n '"test-order-001"' | fn invoke <app-name> <function-name>
# Expected: function response (e.g. "confirmed:test-order-001")
# Then in OCI Console → Monitoring → Metrics Explorer:
# Namespace: <METRIC_NAMESPACE>, Metric: <custom metric name>
# Expected: datapoint visible within 1–2 minutes
```

### 4. Terraform Monitoring Stack
```bash
terraform plan -var-file=prod.tfvars
# Expected: 0 errors; alarm resources show correct MQL queries and pending_duration

terraform apply -var-file=prod.tfvars
# Expected: alarms in OK state after successful invocations
```

**Troubleshooting**:
- `oci-java-sdk-common-httpclient-jersey` in dependency tree → remove Jersey2; add `oci-java-sdk-common-httpclient-jersey3`
- `OciMetadataServiceException` → check Dynamic Group rule and IAM policy `use metrics` in compartment
- Alarm MQL shows `No data` → verify function OCID in MQL matches deployed function; confirm `oci_faas` namespace is enabled on Application

---

## Quick Reference

**Critical API limits**:

| Resource | Limit | Scope |
|----------|-------|-------|
| `PostMetricData` rate | 50 TPS | Per `telemetry-ingestion` endpoint, shared tenancy |
| `MetricDataDetails` per request | 50 objects | Per `PostMetricDataRequest` |
| `Datapoint` per `MetricDataDetails` | 50 objects | Per `MetricDataDetails` |
| Datapoint timestamp window | Last 2 hours | Server-side; silently dropped otherwise |
| Metric dimensions per metric | 10 key-value pairs | Per `MetricDataDetails` |
| Alarm evaluation latency | 1–3 minutes | From ingestion to alarm state change |

**Monitoring endpoint families**:
- **Write only**: `https://telemetry-ingestion.{region}.oraclecloud.com` (`PostMetricData`)
- **Read + management**: `https://telemetry.{region}.oraclecloud.com` (queries, alarms, `ListMetrics`)
- Single `MonitoringClient` instance routes to both — no separate client needed.

---

## External Resources

- [OCI Monitoring Overview](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Concepts/monitoringoverview.htm)
- [OCI Monitoring API Reference (v20180401)](https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/)
- [OCI Functions Metrics (oci_faas)](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsmetrics.htm)
- [OCI Functions Resource Principal](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm)
- [OCI Monitoring MQL Reference](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Reference/mql.htm)
- [FDK Java FnConfiguration Guide](https://github.com/fnproject/docs/blob/master/fdks/fdk-java/FunctionConfiguration.md)
- [OCI Java SDK — MonitoringMetricPostExample](https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/MonitoringMetricPostExample.java)
- [Terraform OCI Provider — oci_monitoring_alarm](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/monitoring_alarm)
- [Terraform OCI Provider — oci_monitoring_alarm_suppression](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/monitoring_alarm_suppression)
- [OCI Service Gateway](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/servicegateway.htm)
- [OCI Functions Security Best Practices](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionssecuritybestpractices.htm)
