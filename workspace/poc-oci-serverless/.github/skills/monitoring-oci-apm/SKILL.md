---
name: monitoring-oci-apm
description: "Instruments, configures, and governs OCI Application Performance Monitoring (APM) for distributed tracing, RUM, synthetic monitoring, and OpenTelemetry integration. Use when deploying observability for OCI-hosted applications, configuring APM domains, instrumenting Java or polyglot services, or managing trace data security and cost governance."
---

## Function
Specialist in full-stack observability with OCI APM — APM Domain provisioning, distributed tracing (OpenTelemetry/proprietary agent), Real User Monitoring, Synthetic Monitoring, TQL queries, IAM guardrails, and cost governance.

## Version Context

**Technology**: Oracle Cloud Infrastructure Application Performance Monitoring (OCI APM)
**Target version**: APM Control Plane API v20200630 / Best Practices 2024
**Release date**: GA — ongoing; LLM Observability is Preview as of 2024
**Support status**: Active

**Important changes in this version**:
- OTLP/HTTP and OTLP/gRPC ingest endpoints are now **production-stable** (previously preview)
- APM Java Agent supports Java 21 LTS including virtual threads (Project Loom)
- Synthetic scripted browser monitors include Vantage Point network diagnostics (traceroute/DNS)
- LLM Observability (GenAI trace capture) introduced as **Preview** — not covered by SLA

**Deprecated**: None in this cycle; v1 APM ingest paths still function but OTLP is the preferred path for new deployments

⚠️ **CRITICAL — Agent Warning**: This skill targets APM Control Plane API v20200630. Do not mix proprietary APM agent patterns with OpenTelemetry SDK patterns without an explicit architectural decision (see Ask First: Agent Strategy).

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 7 mandatory patterns with Terraform and code examples
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural decisions with trade-off matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 6 anti-patterns with correct alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — APM ↔ OCI Logging, Vault, Monitoring, OTel Collector
- **[Verification Loop](#verification-loop)** — CLI/TQL validation commands
- **[Quick Reference](#quick-reference)** — Service limits and critical commands
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with Terraform/code, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **One APM Domain Per Environment** — IAM + billing boundary; dev/staging/prod must be isolated; mixing contaminate IAM access, costs, and TQL dashboards
- **Inject TraceId/SpanId into log records** — Without MDC injection, traces and OCI Logging records are disconnected during incident investigation; destroys cross-signal value
- **Store Data Keys in OCI Vault** — Private Data Key provides write access to APM domain; hardcoded keys enable span flooding (cost attack) and data integrity loss
- **Tag spans with `service.name`, `service.version`, `deployment.environment`** — Without `service.name`, Service Map shows "unknown"; APDEX and service-level alarms cannot be attributed
- **Enable Synthetic Monitors ≥7 days before go-live** — Establishes response time baseline; without it, first production outage has no alert threshold and is discovered via user complaints
- **Use Public Data Key for browser/RUM, Private Key for server-side agents** — Public key is write-only and safe to expose in JavaScript; Private key in client code enables unauthorized telemetry injection
- **Propagate W3C TraceContext headers (`traceparent`, `tracestate`) at every HTTP/gRPC boundary** — Dropped headers fragment traces; cross-service latency attribution becomes impossible

### ⚠️ Ask First

For complete decision matrices with code, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Agent Instrumentation Strategy** — APM Java Agent (deep Oracle DB diagnostics, zero-code) vs. OTel SDK (polyglot, portable, low lock-in) vs. OTLP Collector sidecar (multi-backend, PII scrubbing pipeline)
- **Sampling Strategy** — 100% (dev/low volume) vs. fixed-rate head sampling vs. tail-based via OTLP Collector (required at >1K req/s to control cost while retaining all errors)
- **Vantage Point Selection** — Oracle Public OCI-hosted VPs vs. 50+ non-OCI Oracle VPs vs. Dedicated on-premises VPs (for private/intranet services)
- **Multi-Region APM Domain Strategy** — Single domain (managed SaaS HA) vs. one domain per OCI region vs. OTLP Collector dual-write fanout (zero observability loss)
- **PII Scrubbing Approach** — APM Java Agent `http.request.params.exclude` properties vs. OTLP Collector `redaction` processor (preferred for cross-service enforcement)

### 🚫 Never Do

For complete anti-patterns with ❌ wrong / ✅ correct code, see [Never Do Patterns](./blueprints/never-do-patterns.md).

- **Private Data Key in client-side code or public repositories** — CRITICAL: enables span flooding (cost amplification), trace data corruption, and domain reconnaissance
- **Single APM Domain shared across environments** — Developers get read access to production PII in span attributes; SLA reports contaminated with staging synthetic results
- **Missing `service.name` on spans** — Service Map unavailable; APDEX scoring impossible; service-level alerting broken; increased MTTR
- **100% sampling at >5K req/s without cost controls** — 15 spans/trace × 5K req/s = 270K spans/min; unbounded APM billing with no proportional observability gain
- **No Synthetic Monitors before production go-live** — Zero alerting before user complaints; no geographic availability baseline; SLA reporting impossible from day one
- **APM agent egress without subnet routing (NAT/Service Gateway)** — Private subnet instances cannot reach APM Data Upload Endpoint; spans silently dropped

---

## Integration Patterns

For complete integration code, see [Integration Patterns](./blueprints/integration-patterns.md).

- **APM ↔ OCI Logging** — Inject TraceId/SpanId via MDC into log records; enables Trace Explorer → OCI Logging navigation on `data.traceId`
- **APM ↔ OCI Vault** — Store Private Data Key as Vault Secret; inject via `APM_PRIVATE_DATA_KEY` env var or OKE External Secrets Operator
- **APM ↔ OCI Monitoring** — Synthetic results emit to `oracle_apm_synthetics` namespace; create alarms on `ErrorCount[1m].sum() > 1` for SLO burn-rate alerting
- **APM ↔ OpenTelemetry Collector** — OTLP/HTTP exporter to `https://{domain-id}.apm-agt.{region}.oci.oraclecloud.com/20200101/observations/private`; enables tail sampling and multi-backend fanout

**Common problems**:
- **Fragmented traces across services** → Verify `traceparent`/`tracestate` headers are not stripped by OCI Load Balancer or API Gateway header policies
- **HTTP 401 on span upload** → Confirm correct key type: Public key for browser agents, Private key for server agents; check Vault Secret value rotation
- **`service.name` = "unknown" in Service Map** → Resource attribute not set at SDK init; use `OTEL_SERVICE_NAME` env var or `Resource.create()` with `SERVICE_NAME`

---

## Verification Loop

Execute after each APM configuration change or instrumentation deployment:

### 1. Validate APM Domain Connectivity
```bash
curl -s -o /dev/null -w "%{http_code}" \
  "https://{apm-domain-id}.apm-agt.{region}.oci.oraclecloud.com/20200101/ping" \
  -H "Authorization: dataKey {public-data-key}"
# Expected: 200 | Exit code: 0
# If 401: wrong key type or key value; if 000/curl error: NSG/routing issue
```

### 2. Verify Span Attribute Completeness (TQL)
```
show spans where kind='SERVER' and attributes["service.name"] IS NULL limit 50
# Expected: 0 rows — any result indicates untagged services

show spans where kind='SERVER' and status.code='ERROR' limit 10
# Expected: results include traceId, spanId, service.name attributes populated
```

### 3. Check Synthetic Monitor Status (OCI CLI)
```bash
oci apm-synthetics monitor list --apm-domain-id <ocid> \
  --query 'data[].{name:"display-name",status:status,vps:"vantage-points"}' \
  --output table
# Expected: All critical monitors show status=ENABLED with ≥2 vantage points
```

### 4. Verify Data Keys Are in Vault (Not Hardcoded)
```bash
# Scan application repos for embedded APM keys (run in each app repo)
git log --all -p -- "*.properties" "*.yaml" "*.yml" "*.env" \
  | grep -i "apm.*key\|data.*key\|private.*key" | grep -v "^---"
# Expected: No output — any result requires immediate key rotation + Vault migration
```

**Troubleshooting**:
- `HTTP 000` on ping → NSG egress rule missing TCP/443; or Service Gateway route table misconfigured
- Spans visible in Trace Explorer but Service Map empty → `service.name` resource attribute not propagated; check `OTEL_SERVICE_NAME` env var
- Synthetic monitor `INVALID` status → Script syntax error or target URL unreachable from Vantage Point network

---

## Quick Reference

**Essential OCI CLI commands**:
```bash
# List APM domains with environment tags
oci apm-control-plane apm-domain list --compartment-id <ocid> \
  --query 'data[].{id:id,name:"display-name",freeTier:"is-free-tier",state:"lifecycle-state"}'

# Get Data Upload Endpoint for an APM domain
oci apm-control-plane apm-domain get --apm-domain-id <ocid> \
  --query 'data."data-upload-endpoint"'

# List synthetic monitor failures in last hour
oci apm-synthetics monitor list --apm-domain-id <ocid> --status ENABLED
```

**Critical limits**:

| Resource | Limit | Scope |
|---|---|---|
| Always Free spans | 1,000 events/hour | Per APM Domain |
| Always Free synthetic runs | 10 runs/hour | Per APM Domain |
| Synthetic min interval (paid) | 1 minute | Per monitor |
| Recommended sampling threshold | >1K req/s → tail-based | Per service |
| Data Key rotation | Annually minimum | Per domain |
| Span `service.name` max length | Standard OTel (255 chars) | Per span |

---

## Blueprints Directory Structure

```
.github/skills/monitoring-oci-apm/
├── SKILL.md                              ← This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             ← ✅ 7 mandatory patterns with Terraform/code
    ├── ask-first-decisions.md            ← ⚠️ 5 decision matrices with trade-off tables
    ├── never-do-patterns.md              ← 🚫 6 anti-patterns with ❌/✅ code examples
    └── integration-patterns.md          ← Cross-service integration examples
```

---

## External Resources

### Official Documentation
- [OCI APM Overview](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/application-performance-monitoring.html)
- [APM Control Plane API v20200630](https://docs.oracle.com/en-us/iaas/api/#/en/apm-control-plane/20200630/)
- [APM Java Agent Instrumentation](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/instrument-application-apm-java-agent.html)
- [OpenTelemetry Configuration Guide](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/configure-open-telemetry.html)
- [Synthetic Monitoring](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/synthetic-monitoring.html)
- [Trace Query Language (TQL)](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/trace-query-language.html)

### Security & Best Practices
- [APM Security Guide](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/apm-security.html)
- [APM Domain Operations (key management)](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/apm-domain-operations.html)
- [Log Correlation (TraceId injection)](https://docs.oracle.com/en-us/iaas/application-performance-monitoring/doc/correlate-apm-logs.html)

### Terraform Resources
- [oci_apm_apm_domain](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apm_apm_domain)
- [oci_apm_synthetics_monitor](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apm_synthetics_monitor)
- [oci_apm_config_config (APDEX)](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apm_config_config)
