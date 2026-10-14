---
name: logging-oci-java-functions
description: "Configures and troubleshoots structured logging for OCI Java Functions: Java framework selection (SLF4J/Logback/Log4j2), stdout capture via OCI Log resources, programmatic log ingestion via LoggingIngestionClient, MDC lifecycle, log retention, and Connector Hub pipelines. Use when setting up logging in OCI Java Functions, selecting a Java logging framework, enabling OCI Logging, routing audit logs to separate Log Groups, or forwarding logs to OCI Logging Analytics."
---

## Function
Specialist in the **logging pillar** of OCI Java Functions observability — covering Java logging framework setup (SLF4J, Logback, Log4j2), structured JSON stdout output, OCI Logging resource provisioning, programmatic `LoggingIngestionClient.putLogs()` batching, log retention strategy, and Connector Hub → Logging Analytics pipelines.

> **Scope boundary**: This skill handles log framework wiring, log routing, and log storage only.
> - Custom metrics + alarms → [`monitoring-oci-java-functions`]
> - Full observability overview (metrics + tracing) → [`observing-oci-java-functions`]
> - Resource Principal IAM setup → [`observing-oci-java-functions`] — Always Do: Resource Principal Auth

## Version Context

**Technology**: OCI Functions + OCI Logging + OCI Logging Analytics + OCI Connector Hub
**FDK Java**: 1.1.12 (May 2026) | **OCI Java SDK BOM**: 3.87.0 (May 2026)
**SLF4J**: 2.0.16 | **Logback**: 1.5.18 | **logstash-logback-encoder**: 8.0
**Log4j2** (when used): 2.24.3 minimum — **never < 2.17.1** (Log4Shell CVE-2021-44228)
**Java Runtime**: Java 11 (OCI-managed) / Java 17–21 (custom Docker image)
**Support Status**: Active

**Breaking Changes (FDK 1.0.x → 1.1.x)**:
- JUnit 5: replace `testing-junit4` with `testing-junit5:1.1.12`
- Logback 1.5.x requires SLF4J 2.x API — do not mix with Logback 1.4.x or SLF4J 1.7.x

⚠️ **Version Lock**: Targets FDK 1.1.12 / OCI SDK 3.87.0. Mix of SDK module versions causes `NoClassDefFoundError` at cold-start — always import via BOM.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 7 mandatory logging patterns with full code
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural decisions with trade-off matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 6 anti-patterns with security impact and correct alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Full Maven POM, logback.xml, lifecycle blueprint
- **[Verification Loop](#verification-loop)** — Build, test, and log output validation commands
- **[Quick Reference](#quick-reference)** — Critical limits and essential Maven coordinates
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with full code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **Enable OCI Logging Log Resource on Function Application** — Provision `oci_logging_log` with `source_type = "OCISERVICE"` and `category = "invoke"`; stdout/stderr are **silently discarded** without this — no error is surfaced anywhere
- **Structured JSON Logging to stdout** — Use SLF4J + Logback + `logstash-logback-encoder:8.0`; unstructured `println` blocks OCI Logging Analytics field extraction and MQL alarm queries
- **MDC Cleanup on Every Invocation** — Call `MDC.clear()` in `finally`; the FDK reuses the same JVM thread across warm invocations — stale context fields silently corrupt log correlation
- **JUL-to-SLF4J Bridge** — Install `SLF4JBridgeHandler` once in `@FnConfiguration`; without it, OCI SDK internal JUL messages bypass Logback and print unstructured text to stderr
- **Resource Principal for LoggingIngestionClient** — Use `ResourcePrincipalAuthenticationDetailsProvider`; no API key files in Docker image (see [`observing-oci-java-functions`] for full IAM setup)
- **PutLogs — Synchronous Batch Before Return** — Collect `LogEntry` objects during invocation; call `putLogs()` once before handler returns; background threads lose data when FDK freezes the container post-return
- **Log-Level via Function Environment Variable** — Externalize log level via `ctx.getConfigurationByKey("LOG_LEVEL")`; hardcoded levels require Docker image rebuild to change

### ⚠️ Ask First

For complete decision matrices with option-level code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Java Logging Framework** — JUL (zero deps, custom JSON formatter needed) vs. SLF4J+Logback (standard, best JSON) vs. SLF4J+Log4j2 (heavier, CVE history); ask: existing dep? cold-start SLA?
- **Log Delivery Strategy** — stdout capture only (zero code) vs. SDK PutLogs (audit trail, custom retention) vs. Connector Hub → Log Analytics (ML anomaly, >180d retention); ask: retention need? audit compliance tier?
- **PutLogs Batching Strategy** — per-event (many API calls, risky) vs. batch at invocation end (one call, recommended) vs. periodic flush (long-running functions only); ask: log entry frequency per invocation?
- **Log Group Organization** — single shared group vs. separate operational + audit groups (different retention, scoped IAM read access); ask: PCI/SOC2/HIPAA compliance? developer access to audit logs?

### 🚫 Never Do

For complete anti-patterns with ❌ wrong and ✅ correct code, see [Never Do Patterns](./blueprints/never-do-patterns.md).

- **No OCI Log Resource on Function Application** — stdout silently discarded; zero visibility in OCI Console despite correct function code
- **Log4j2 < 2.17.1** — Log4Shell CVE-2021-44228 (CVSS 10.0) RCE via JNDI lookup; OCI Functions processes untrusted external input — critical exposure
- **Log PII or Credentials to stdout** — OCI Logging is searchable and forwardable to SIEM; GDPR Article 5(1)(f) breach + OWASP A09 credential exposure
- **MDC Not Cleared Between Warm Invocations** — Stale `orderId`/`userId` fields in subsequent invocation logs; silent cross-invocation context leak
- **Unstructured System.out.println** — Single-string `data` field in OCI Logging; no severity filtering, no field extraction, no alarm capability
- **Fire-and-Forget Thread for PutLogs** — FDK container may freeze before thread completes; audit log entries silently dropped; compliance violation

---

## Integration Patterns

For complete code examples including full Maven POM, `logback.xml`, and lifecycle blueprint, see [Integration Patterns](./blueprints/integration-patterns.md).

- **OCI Functions ↔ OCI Logging (stdout)** — `oci_logging_log` Terraform + Logback `LogstashEncoder`; zero additional SDK dependency beyond FDK
- **OCI Functions ↔ OCI Logging (SDK write)** — `oci-java-sdk-loggingingestion` + `LoggingIngestionClient.putLogs()`; Resource Principal; batched at invocation end
- **OCI Functions ↔ OCI Logging Analytics** — Connector Hub `oci_sch_service_connector` from Log Group → LA Log Group; no function code change required

**Common problems**:
- **No logs in OCI Console** → OCI Log resource not provisioned or not associated with Function App
- **Unstructured log lines** → Missing `logstash-logback-encoder`; `logback.xml` not on classpath
- **PutLogs connection timeout in VPC** → Service Gateway for "OCI Services" not attached to the function subnet
- **OCI SDK JUL noise in stderr** → JUL→SLF4J bridge not installed (Pattern 4)

---

## Verification Loop

The agent MUST execute after each code generation:

### 1. Build
```bash
mvn package -DskipTests
# Expected: BUILD SUCCESS; target/*.jar created
# Exit code: 0
```

### 2. Security — Check Log4j2 transitive deps
```bash
mvn dependency:tree | grep log4j
# Expected: no output, OR lines showing 2.24.x only
# Any version < 2.17.1 → STOP, block deployment, add explicit override
```

### 3. Unit Tests
```bash
mvn test
# Expected: BUILD SUCCESS, all tests pass
# Exit code: 0
```

### 4. Local Smoke + JSON Log Validation
```bash
fn start &
fn deploy --app test-app --local
echo -n '"test-order-001"' | fn invoke test-app order-processor 2>&1 \
  | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line.startswith('{'):
        obj = json.loads(line)
        assert 'timestamp' in obj, 'Missing timestamp'
        assert 'level'     in obj, 'Missing level'
        assert 'message'   in obj, 'Missing message'
        print('JSON log valid:', obj.get('message'))
"
# Expected: at least 2 'JSON log valid:' lines
```

### 5. OWASP Dependency Check (CI gate)
```bash
mvn org.owasp:dependency-check-maven:check
# Expected: BUILD SUCCESS, no CRITICAL/HIGH CVEs
```

**Troubleshooting**:
- `No logs in OCI Console` → OCI Log resource not provisioned or not linked to Function App
- `ClassNotFoundException: LogstashEncoder` → `logstash-logback-encoder` missing from `pom.xml`
- `OciMetadataServiceException` on LoggingIngestionClient init → IAM Dynamic Group misconfigured; STOP, do not retry in loop
- `Connection timed out` on `putLogs` in VPC → Service Gateway missing for "OCI Services" on the function subnet

---

## Quick Reference

**Essential Maven coordinates**:
```xml
<slf4j.version>2.0.16</slf4j.version>
<logback.version>1.5.18</logback.version>
<logstash.encoder.version>8.0</logstash.encoder.version>
<oci.sdk.version>3.87.0</oci.sdk.version>
<!-- Required modules: oci-java-sdk-loggingingestion, oci-java-sdk-common-httpclient-jersey3 -->
```

**Critical limits**:

| Resource | Limit | Scope |
|----------|-------|-------|
| OCI Log retention | 30–180 days max | Per Log resource |
| PutLogs request size | 10 MB max | Per API call |
| LogEntry per batch | 300 max | Per `PutLogsDetails` |
| Log Group write throughput | ~10 MB/s | Per Log Group |
| Log4j2 minimum safe version | 2.17.1 | CVE-2021-44228 |

---

## External Resources

### Official Documentation
- [OCI Functions Logging](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionslogging.htm)
- [OCI Logging Ingestion API](https://docs.oracle.com/en-us/iaas/api/#/en/logging-dataplane/20200831/)
- [OCI Connector Hub](https://docs.oracle.com/en-us/iaas/Content/connector-hub/home.htm)
- [OCI Logging Analytics](https://docs.oracle.com/en-us/iaas/logging-analytics/home.htm)
- [FDK Java — FunctionConfiguration Guide](https://github.com/fnproject/docs/blob/master/fdks/fdk-java/FunctionConfiguration.md)

### Logging Frameworks
- [SLF4J Manual](https://www.slf4j.org/manual.html)
- [Logback Configuration](https://logback.qos.ch/manual/configuration.html)
- [SLF4J JUL Bridge](https://www.slf4j.org/legacy.html#jul-to-slf4j)
- [logstash-logback-encoder](https://github.com/logfellow/logstash-logback-encoder)

### Security & Best Practices
- [Log4j2 Security Advisories — CVE-2021-44228](https://logging.apache.org/log4j/2.x/security.html)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [SLF4J MDC Manual](https://logback.qos.ch/manual/mdc.html)
