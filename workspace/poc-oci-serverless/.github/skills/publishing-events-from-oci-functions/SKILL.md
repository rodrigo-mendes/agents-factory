---
name: publishing-events-from-oci-functions
description: Publishes events and messages from OCI Functions (Java) to OCI Streaming, Notifications, Queue, Monitoring, and Logging using OCI Java SDK v3.x+. Use when sending events from Functions to OCI platform services.
---

## Version Context

**Technology**: OCI Java SDK — Event Publishing from OCI Functions
**Target Version**: OCI Java SDK v3.36+ (project baseline) / v3.86.1 (latest)
**Runtime**: Java 11+ (project targets Java 17)
**Platform**: OCI Functions (Oracle Cloud Infrastructure)
**Release Date**: 2024-ongoing (SDK 3.86.1 released 2026-05-06)
**Support Status**: Active — General Availability
**License**: UPL 1.0 / Apache 2.0 (dual license)

**Supported Target Services**:
- OCI Streaming (Kafka-compatible event streaming) — API v20180418
- OCI Notifications / ONS (pub/sub fan-out) — API v20181201
- OCI Queue (pull-based messaging) — API v20210201
- OCI Monitoring (custom metrics) — API v20180401
- OCI Logging Ingestion (structured logs) — API v20200831

**Key Constraints in This Version**:
- Resource Principal is the **only** acceptable auth method for Functions
- Streaming `PutMessages` total payload ≤ 1MB per request
- Notifications rate limit: 60 TPM (transactions per minute) per topic
- Queue message size limit: 128KB per message
- Monitoring timestamps must be within 2h past / 10min future
- Streaming values must be `byte[]` (base64 encoded)

⚠️ **CRITICAL — Agent Warning**:
This skill is version-specific to OCI Java SDK v3.x+.
Never use API keys or config files in OCI Functions containers — Resource Principal only.
Never use the `telemetry` endpoint for `PostMetricData` — use `telemetry-ingestion`.
Always check per-message errors in Streaming `PutMessagesResult` — HTTP 200 does NOT mean all messages succeeded.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Cross-service integration examples
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Resource Principal + Client init in `@FnConfiguration`** — SDK clients involve TLS/auth. Per-invocation init wastes 100-500ms
- **Streaming: check per-message errors in `putMessages` response** — HTTP 200 doesn't guarantee all messages succeeded. Silent data loss
- **Notifications: use `publishMessage` with proper topic OCID** — Validated delivery to all subscribers
- **Queue: `putMessages` with JSON serialization** — Batch support with per-message error checking
- **Monitoring: `postMetricData` with correct endpoint** — Use `telemetry-ingestion` not `telemetry`
- **Logging: structured JSON via `putLogs`** — Log type, source, subject for filtering

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **Event Transport Selection** — Streaming (ordered, partitioned), Notifications (fan-out), Queue (FIFO/dedup), Monitoring (metrics)
- **Streaming Message Key Strategy** — Determines partition placement and ordering guarantees
- **Monitoring Batch Atomicity** — Controls partial failure behavior for metric batches

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **Creating OCI SDK Clients in handler** — Connection pool exhaustion, 100-500ms overhead per call
- **Wrong Monitoring endpoint (`telemetry` vs `telemetry-ingestion`)** — Silent 404, metrics never recorded
- **Ignoring per-message errors in Streaming** — HTTP 200 with partial failures → silent data loss
- **Exceeding Streaming 1MB batch limit** — Request rejected, all messages in batch lost
- **Hardcoding service endpoints** — Breaks across regions. Use SDK defaults or config
- **Publishing metrics with stale timestamps** — Rejected by Monitoring service (>2h staleness)

---

## Integration Patterns

For complete integration code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Summary of integrations**:
- **OCI Functions ↔ Streaming** — Kafka-compatible event publishing with partition keys
- **OCI Functions ↔ Notifications (ONS)** — Fan-out messaging to email/PagerDuty/webhook subscribers
- **OCI Functions ↔ Queue** — FIFO message delivery with deduplication
- **OCI Functions ↔ Monitoring** — Custom metric publishing for business KPIs
- **OCI Functions ↔ Logging** — Structured log ingestion for audit trails
## Verification Loop

The agent MUST execute after each code generation:

### 1. Dependency Resolution
```bash
mvn dependency:resolve
```
**Expected output**: All `oci-java-sdk-*` artifacts resolved
**Exit code**: 0

### 2. Build
```bash
mvn clean package -DskipTests
# Exit code: 0 (success) | 1 (compilation/test failure)
```
**Expected output**: `BUILD SUCCESS`
**Exit code**: 0

### 3. Unit Tests
```bash
mvn clean test
# Exit code: 0 (all tests passed) | 1 (test failure)
```
**Expected output**: `Tests run: N, Failures: 0, Errors: 0`
**Exit code**: 0

### 4. Function Config Verification
```bash
fn inspect function <app-name> <fn-name>
# Exit code: 0 (success) | 1 (not found)
```
**Expected output**: Config shows `STREAM_ENDPOINT`, `TOPIC_OCID`, `MONITORING_ENDPOINT`, etc.

### 5. IAM Policy Verification
```bash
oci iam policy list --compartment-id <compartment>
# Exit code: 0 (success) | 1 (auth/network error)
```
**Expected output**: Policies granting dynamic-group access to `stream-push`, `ons-topics`, `queues`, `metrics`, `log-content`

### 6. Smoke Test (Function Invoke)
```bash
echo '{"action":"publish","message":"test"}' | fn invoke <app> <fn>
# Exit code: 0 (success) | 1 (invocation error)
```
**Expected output**: `{"status":200,"message":"published"}`

**Troubleshooting**:
- `BmcException 401` → IAM policy missing or dynamic group misconfigured
- `BmcException 404` → Wrong endpoint (check `telemetry-ingestion` vs `telemetry`)
- `BmcException 429` → Rate limit exceeded (throttle or aggregate messages)
- `HTTP 400 on PutMessages` → Total payload exceeds 1MB limit
- Metrics not appearing in dashboard → Check timestamp is within 2h past / 10min future

---

## Quick Reference

**SDK Module Compatibility**:

| SDK Module | Artifact ID | Min SDK Version | API Version | Endpoint Type |
|------------|-------------|-----------------|-------------|---------------|
| Streaming | `oci-java-sdk-streaming` | 2.0+ | 20180418 | Stream `messages_endpoint` |
| Notifications | `oci-java-sdk-ons` | 2.0+ | 20181201 | Topic `apiEndpoint` |
| Queue | `oci-java-sdk-queue` | 3.0+ | 20210201 | Regional (auto) |
| Monitoring | `oci-java-sdk-monitoring` | 2.0+ | 20180401 | `telemetry-ingestion` |
| Logging | `oci-java-sdk-loggingingestion` | 2.0+ | 20200831 | Regional (auto) |

**Service Rate Limits & Payload Constraints**:

| Service | Rate Limit | Max Payload | Key Constraint |
|---------|-----------|-------------|----------------|
| Streaming | Per-partition throttle | 1MB total per `PutMessages` | Values must be `byte[]` |
| Notifications | 60 TPM per topic | 64KB per message | Fan-out is async |
| Queue | 5000 msgs/sec per queue | 128KB per message | Pull-based |
| Monitoring | 50 TPS per tenancy | 50 metric streams/request | Max 20 dimensions |
| Logging | Varies | Per entry limits | Separate from query endpoint |

**Essential IAM Policies**:
```
allow dynamic-group <dg> to use stream-push in compartment <comp>
allow dynamic-group <dg> to use ons-topics in compartment <comp>
allow dynamic-group <dg> to use queues in compartment <comp>
allow dynamic-group <dg> to use metrics in compartment <comp>
allow dynamic-group <dg> to use log-content in compartment <comp>
```

**Performance Baseline**:

| Service Call | Latency | Impact on Function |
|-------------|---------|-------------------|
| Streaming `putMessages` | ~5–20ms | Low overhead per batch |
| Notifications `publishMessage` | ~10–50ms | Moderate |
| Queue `putMessages` | ~5–20ms | Low overhead |
| Monitoring `postMetricData` | ~10–30ms | Low overhead |
| Logging `putLogs` | ~5–20ms | Low overhead |

---

## Security Hardening Checklist

- [ ] Resource Principal only — never API keys or config files in containers
- [ ] IAM policies scoped to minimum verbs (`stream-push`, not `manage streams`)
- [ ] IAM policies scoped to specific compartment (not tenancy)
- [ ] Dynamic Group matching rule specific to this function/app
- [ ] Endpoints from configuration (not hardcoded)
- [ ] No sensitive data in Streaming message keys (visible in admin APIs)
- [ ] Notification message bodies sanitized (no credentials or PII without masking)
- [ ] Custom log content validated (no secrets in log entries)
- [ ] Metric dimensions don't contain PII or secrets
- [ ] Function timeout accounts for outbound call latency

---

## External Resources

### Official Documentation
- [OCI Java SDK Repository](https://github.com/oracle/oci-java-sdk) — v3.86.1
- [OCI Streaming API Reference](https://docs.oracle.com/en-us/iaas/api/#/en/streaming/20180418/)
- [OCI Notifications API Reference](https://docs.oracle.com/en-us/iaas/api/#/en/notification/20181201/)
- [OCI Queue API Reference](https://docs.oracle.com/en-us/iaas/api/#/en/queue/20210201/)
- [OCI Monitoring API Reference](https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/)
- [OCI Logging Ingestion API Reference](https://docs.oracle.com/en-us/iaas/api/#/en/logging-dataplane/20200831/)

### SDK Examples
- [StreamsExample.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/StreamsExample.java)
- [NotificationExample.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/NotificationExample.java)
- [MonitoringMetricPostExample.java](https://github.com/oracle/oci-java-sdk/blob/master/bmc-examples/src/main/java/MonitoringMetricPostExample.java)
- [Queue Module Source](https://github.com/oracle/oci-java-sdk/tree/master/bmc-queue)

### Terraform Resources (Infrastructure Provisioning)
- [oci_streaming_stream](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream)
- [oci_ons_notification_topic](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/ons_notification_topic)
- [oci_queue_queue](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/queue_queue)
- [oci_logging_log](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/logging_log)

### Monitoring & Limits
- [Publishing Custom Metrics Guide](https://docs.oracle.com/iaas/Content/Monitoring/Tasks/publishingcustommetrics.htm)
- [Notification TPM Limits](https://docs.oracle.com/iaas/Content/Notification/Concepts/notificationoverview.htm#limits-pub-msg)
