---
name: observing-oci-java-functions
description: "Instruments OCI Java Functions with structured logging, custom metrics, and distributed tracing using OCI Logging, OCI Monitoring, and OCI APM. Use when building observable serverless Java workloads on OCI, adding custom metrics or structured logs to existing functions, or choosing a distributed tracing strategy for multi-service function chains."
---

## Version Context

**Technology**: OCI Functions + OCI Logging + OCI Monitoring + OCI APM
**FDK Java**: 1.1.12 (May 2026)
**OCI Java SDK BOM**: 3.87.0 (May 2026)
**APM Java Agent Tracer**: 1.17.1.2 (Jun 2025)
**OpenTelemetry Java Agent**: 2.28.1 (May 2026)
**Java Runtime**: Java 11 (OCI-managed) / Java 17–21 (custom Docker image)
**Support Status**: Active

**Breaking Changes (FDK 1.0.x → 1.1.x)**:
- JUnit 5: replace `testing-junit4` with `testing-junit5:1.1.12`
- `fn-events` library: replaces manual JSON parsing for Connector Hub / API Gateway events

⚠️ **Version Lock**: Targets FDK 1.1.12 / OCI SDK 3.87.0. Mix of SDK module versions causes `NoClassDefFoundError` at cold-start — always import via BOM.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 7 mandatory observability patterns with full code
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural decisions with trade-off matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 6 anti-patterns with correct alternatives and impact
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Full lifecycle blueprint, Dockerfile, Maven POM
- **[Verification Loop](#verification-loop)** — Build, test, invoke, and observability validation
- **[Quick Reference](#quick-reference)** — Critical limits and essential commands
- **[External Resources](#external-resources)** — Official documentation links
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with full code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **Resource Principal Auth** — Use `ResourcePrincipalAuthenticationDetailsProvider` exclusively; bundling API key PEM files in Docker images is a critical security vulnerability — any OCIR reader can extract the key
- **Static Block SDK Init** — Initialize all SDK clients (`MonitoringClient`, `LoggingClient`) in `@FnConfiguration` or a `static {}` block; per-invocation creation adds 150–400 ms and can exhaust ephemeral TCP ports
- **Structured JSON Logging** — Write `{"timestamp":"..","level":"..","message":".."}` to stdout; unstructured `println` blocks OCI Logging Analytics field extraction and alarm MQL queries on log content
- **Enable OCI Logging on Function Application** — Configure `oci_logging_log` Terraform resource with `source_type = "OCISERVICE"` for the Functions application; stdout is silently discarded without this — no error is surfaced
- **PostMetricData for Business KPIs** — Post custom metrics synchronously inside `handleRequest`; fire-and-forget background threads lose data when the FDK freezes the container after return
- **OCI SDK BOM** — Declare `oci-java-sdk-bom:3.87.0` in `<dependencyManagement>`; omitting the BOM causes `NoClassDefFoundError` / `ClassCastException` at cold-start across 80+ SDK modules
- **Config via Function Environment Variables** — Store all OCIDs, metric namespaces, and APM keys in the function `config` block (func.yaml / Terraform); hardcoding topology couples code to deployment environment and exposes infrastructure details

### ⚠️ Ask First

For complete decision matrices with option-level code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Distributed Tracing Strategy** — OCI APM Java Agent (rich auto-instrumentation, Oracle lock-in) vs. OpenTelemetry Agent v2.28.1 (portable, CNCF, +120–200 ms cold start) vs. Manual APM Tracer SDK (minimal overhead, programmatic) vs. None (oci_faas metrics only); ask cold-start SLA and vendor portability requirements before recommending
- **Log Delivery Method** — stdout capture (zero code, automatic) vs. `LoggingClient` SDK push (audit trail, custom retention) vs. OCI Logging Analytics via Connector Hub (ML anomaly, > 30d retention); ask retention period and PII requirements
- **APM Data Key Type** — Private key (server-side, read+write spans) vs. Public key (browser/mobile write-only); wrong choice causes silent trace upload failure — server-side functions always require Private key
- **Java Runtime Version** — Java 11 managed (zero Dockerfile overhead) vs. Java 17 custom image (records, sealed classes) vs. Java 21 custom image (virtual threads, GraalVM native-image); ask feature needs and cold-start targets

### 🚫 Never Do

For complete anti-patterns with ❌ wrong and ✅ correct code, see [Never Do Patterns](./blueprints/never-do-patterns.md).

- **Hardcode OCI credentials in source or Docker image** — Any OCIR reader extracts the private key; grants unrestricted OCI API access; use Resource Principal (zero credentials in image)
- **Create SDK clients per invocation** — Resource Principal metadata HTTP call + connection pool setup on every warm invocation adds 150–400 ms and causes `java.net.BindException` under load
- **Fire-and-forget threads for observability writes** — FDK container freeze after `handleRequest` return races with thread execution; metric and log data silently lost
- **Log all config variables, including secret keys** — OCI Logging is searchable and forwardable to SIEM; exposing `APM_PRIVATE_DATA_KEY` in logs = OWASP A02 Cryptographic Failure, enables unauthorized trace writes
- **Post N individual metrics in a loop near timeout** — Last `PostMetricData` calls are killed mid-flight by the function timeout; results in partial metric series and phantom dashboard gaps
- **Use APM Public Data Key for server-side spans** — Public key is write-only and targets browser endpoints; server span uploads fail silently; APM Trace Explorer remains empty

---

## Integration Patterns

For complete code examples including full Maven POM, Dockerfile, and lifecycle blueprint, see [Integration Patterns](./blueprints/integration-patterns.md).

- **OCI Functions ↔ OCI Monitoring** — `oci-java-sdk-monitoring` + `PostMetricDataRequest`; Resource Principal auth; batch with `BatchAtomicity.NonAtomic`; max 50 `MetricDataDetails` per request
- **OCI Functions ↔ OCI Logging (stdout)** — `oci_logging_log` Terraform resource with `source_type = "OCISERVICE"`; structured JSON via `System.out.println`; zero SDK dependency
- **OCI Functions ↔ OCI APM (OpenTelemetry)** — OpenTelemetry Java agent JAR in multi-stage Dockerfile; `OTEL_EXPORTER_OTLP_ENDPOINT` pointing to `apm-collector.<region>.oci.oraclecloud.com`; Private Data Key in `Authorization` header
- **OCI Functions ↔ OCI APM (native tracer)** — `apm-java-agent-tracer:1.17.1.2` Maven dependency; programmatic `Tracer.spanBuilder` API; no JVM agent, minimal cold-start impact

**Common Problems**:
- **`OciMetadataServiceException` at cold-start** → IAM Dynamic Group missing or function OCID not in scope — halt and verify policy (**Emergency Stop**)
- **APM Trace Explorer empty after deploy** → Wrong `APM_PRIVATE_DATA_KEY` or incorrect OTLP endpoint URL — retrieve endpoint from OCI Console → APM Domain Details
- **`PostMetricData` calls fail from private subnet** → Service Gateway required for OCI API calls; Internet Gateway is insufficient
- **Metrics present but dashboards show gaps** → Function timeout hit before final `PostMetricDataRequest`; add elapsed-time guard (leave 5s buffer)

---

## Verification Loop

### 1. Build
```bash
fn build
# Expected: Successfully built <image>:<tag>  |  Exit code: 0
```

### 2. Unit Tests
```bash
mvn test
# Expected: BUILD SUCCESS, all @Test pass  |  Exit code: 0
```

### 3. Local Integration
```bash
fn start
fn deploy --app test-app --local
echo -n '"order-001"' | fn invoke test-app <function-name>
# Expected: function response value  |  Exit code: 0
```

### 4. OCI Observability Validation
```bash
fn invoke <oci-app> <function-name> --content '"order-001"'
# Then verify in OCI Console within ~30s:
# → Logging: search for {"message":"Function invoked"} structured JSON
# → Monitoring → Metrics Explorer → Namespace: <METRIC_NAMESPACE>
# → APM → Trace Explorer (if tracing enabled)
```

**Troubleshooting**:
- `OciMetadataServiceException` → Dynamic Group / policy misconfigured — **halt and notify human**
- `HTTP 429` on `postMetricData` sustained > 2 min → quota exhausted — **stop metric posts, notify human**
- No logs in OCI Logging → `oci_logging_log` not configured or `is_enabled = false`
- Spans not in APM → verify `APM_PRIVATE_DATA_KEY` and OTLP endpoint format (retrieve from Console, not docs)

---

## Quick Reference

**Essential commands**:
```bash
fn init --runtime java21 --trigger http <function-name>   # scaffold project
fn build                                                   # build Docker image
mvn test                                                   # run unit tests
fn deploy --app <app-name>                                 # deploy to OCI
fn invoke <app> <function-name>                            # invoke in OCI
```

**Critical limits**:

| Resource | Limit | Notes |
|----------|-------|-------|
| Function timeout | 30s default / 300s max | Leave 5s buffer for observability writes |
| Concurrent executions | 60 / function / region | Increase via Service Request |
| `PostMetricData` batch size | 50 `MetricDataDetails`, 50 datapoints each | Batch, never loop N calls |
| Custom metric ingestion | 100 MB/min per namespace | Monitor under high load |
| Memory minimum | 128 MB | Use 256 MB with SDK + observability libs |
| `MonitoringClient` connection pool | 50 connections (default) | Safe for most concurrency |

**High Confidence** (execute without asking):
- Resource Principal auth setup, `@FnConfiguration` static SDK init, structured JSON stdout, `PostMetricData` with `BatchAtomicity.NonAtomic`, FDK JUnit 5 test scaffolding

**Low Confidence** (must confirm with human):
- APM Private Data Key value, Compartment OCID for target environment, IAM Dynamic Group name and existing policies

**Emergency Stop** (halt, notify human immediately):
- `ResourcePrincipalAuthenticationDetailsProvider` throws `OciMetadataServiceException`
- `PostMetricData` returns sustained `HTTP 429`
- APM spans appear in wrong APM domain

---

## External Resources

- [OCI Functions Documentation](https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm) (verified 2026-07-26)
- [FDK Java GitHub — v1.1.12](https://github.com/fnproject/fdk-java) (verified 2026-07-26)
- [FDK Java FnConfiguration Guide](https://github.com/fnproject/docs/blob/master/fdks/fdk-java/FunctionConfiguration.md) (verified 2026-07-26)
- [OCI Java SDK GitHub — v3.87.0](https://github.com/oracle/oci-java-sdk) (verified 2026-07-26)
- [OCI Java SDK — MonitoringMetricPostExample](https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/MonitoringMetricPostExample.java) (verified 2026-07-26)
- [OCI APM Documentation](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/apm-overview.html) (verified 2026-07-26)
- [OCI APM — Build Tracer with Maven](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/build-apm-tracer-maven-project.html) (verified 2026-07-26)
- [OCI Logging Documentation](https://docs.oracle.com/en-us/iaas/Content/Logging/home.htm) (verified 2026-07-26)
- [OCI Monitoring — PostMetricData](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Concepts/monitoringoverview.htm) (verified 2026-07-26)
- [OCI Functions Security Best Practices](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionssecuritybestpractices.htm) (verified 2026-07-26)
- [OCI Functions Resource Principal](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm) (verified 2026-07-26)
- [OCI Functions Custom Images](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscustomimages.htm) (verified 2026-07-26)
- [OpenTelemetry Java Instrumentation — v2.28.1](https://github.com/open-telemetry/opentelemetry-java-instrumentation) (verified 2026-07-26)

---

## Related Skills

**Scope of this skill:** all 3 observability pillars at the function level (structured logging + custom metrics + distributed tracing). Entry point for function observability.

- `monitoring-oci-java-functions` — deep dive into custom metrics via PostMetricData.
- `monitoring-oci-apm` — deep dive into APM domains and distributed tracing.
- `logging-oci-java-functions` — deep dive into structured logging and Java logging frameworks.
- `configuring-oci-monitoring-alarms` — alarms over the emitted metrics.
- Live validation: `validating-oci-observability`.
