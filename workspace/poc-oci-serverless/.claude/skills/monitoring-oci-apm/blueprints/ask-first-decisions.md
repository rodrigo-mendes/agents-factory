# ⚠️ Ask First — OCI APM Architectural Decisions

Before implementing, present these options with trade-offs and wait for the team's decision.

---

## Decision 1: Agent Instrumentation Strategy

**Ask**: "Does this workload run Oracle Database with SQL performance diagnostics requirements, or does the team require multi-cloud/multi-backend observability portability?"

| Option | Best When | Sacrifices | Lock-in |
|---|---|---|---|
| **APM Java Agent** (`-javaagent`) | All-Java/. NET stack + Oracle DB; brownfield apps (no code changes allowed) | Java/.NET only; Oracle-specific config; larger JVM start time | High — proprietary SQL capture, config format |
| **OTel SDK (manual)** | Polyglot services (Go, Python, Node.js, Ruby); teams with OTel expertise | Code instrumentation required; no deep Oracle DB SQL capture | Low — change OTLP exporter endpoint to switch backends |
| **OTLP Collector sidecar/DaemonSet** | Kubernetes (OKE); orgs standardizing on OTel; PII scrubbing pipeline needed | Additional HA infrastructure component; network hop | None — Collector is vendor-neutral |
| **APM Browser Agent (JS)** | Any web app requiring frontend RUM | Browser-only; CSP configuration required | Medium — proprietary JS snippet |

**APM Java Agent** — JVM startup config:
```bash
java -javaagent:/opt/apm-agent/oracle-apm-agent.jar \
     -Dcom.oracle.apm.agent.service.name=payment-service \
     -jar app.jar
```

**OTel SDK + OTLP to APM** — exporter config:
```java
OtlpHttpSpanExporter exporter = OtlpHttpSpanExporter.builder()
    // OtlpHttpSpanExporter requires the FULL path including /v1/traces (it does not append it automatically).
    // Posting OTLP to /observations/private → rejection MISSING_DATA_FORMAT (metric oci_apm/PayloadRejections).
    .setEndpoint("https://{domain-id}.apm-agt.{region}.oci.oraclecloud.com/20200101/opentelemetry/private/v1/traces")
    .addHeader("Authorization", "dataKey " + System.getenv("APM_PRIVATE_DATA_KEY"))
    .build();
```

**OTLP Collector** — minimal config:
```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: "0.0.0.0:4317" }
      http: { endpoint: "0.0.0.0:4318" }
exporters:
  otlphttp/apm:
    endpoint: "https://{domain-id}.apm-agt.{region}.oci.oraclecloud.com/20200101/opentelemetry/private"
    headers:
      Authorization: "dataKey ${APM_PRIVATE_DATA_KEY}"
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [otlphttp/apm]
```

---

## Decision 2: Sampling Strategy

**Ask**: "What is the peak request rate, and must all errors be captured or is a statistical sample of errors acceptable?"

| Option | Use When | Cost | Error Coverage |
|---|---|---|---|
| **100% (no sampling)** | <1K req/s; dev/staging | Linear with traffic | 100% |
| **Fixed-rate head sampling** (e.g., 10%) | Known traffic; cost-controlled; non-critical services | ~10% of full cost | ~10% of errors lost |
| **Tail-based (OTLP Collector)** | >1K req/s production; compliance requires all errors | Errors: ~100%; OK traces: ~1–5% | 100% errors retained |

**Rule of thumb**: >5K req/s requires tail-based sampling to maintain predictable APM costs.

**Tail-based sampling — OTLP Collector processor**:
```yaml
processors:
  tail_sampling:
    decision_wait: 30s        # Buffer spans for 30s before sampling decision
    num_traces: 50000          # Max traces in memory buffer
    policies:
      - name: errors-policy
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow-traces
        type: latency
        latency: { threshold_ms: 2000 }
      - name: probabilistic-ok
        type: probabilistic
        probabilistic: { sampling_percentage: 5 }  # 5% of healthy traces
```

**Fixed-rate via OTel SDK**:
```java
SdkTracerProvider.builder()
    .setSampler(Sampler.parentBased(Sampler.traceIdRatioBased(0.10))) // 10% sampling
    .build();
```

---

## Decision 3: Vantage Point Selection for Synthetic Monitors

**Ask**: "Are the monitored endpoints accessible from the public internet, or are they private/intranet services? What geographic regions represent the primary user base?"

| Option | Use When | Setup |
|---|---|---|
| **Oracle Public VPs (OCI-hosted)** | OCI-deployed services; test OCI backbone path | None — select from console |
| **Oracle Public VPs (non-OCI: AWS, Azure, GCP, colo)** | Global CDN-backed apps; cross-cloud latency measurement | None — 50+ locations available |
| **Dedicated On-Premises VP** | Private/intranet services; VPN-only endpoints; regulated no-external-probe environments | Deploy VP agent container in private network |

**Dedicated Vantage Point Terraform**:
```hcl
resource "oci_apm_synthetics_dedicated_vantage_point" "internal" {
  apm_domain_id  = oci_apm_apm_domain.prod.id
  display_name   = "internal-vpc-vantage-point"
  dvp_stack_details {
    dvp_stack_type    = "ORACLE_RM_STACK"
    dvp_stack_id      = var.resource_manager_stack_ocid
    dvp_version       = "latest"
  }
  region = var.region
  status = "ENABLED"
}
```

**Coverage matrix recommendation**:
```
Monitor Type      | Target                       | Interval | Vantage Points
REST              | /health (primary API)         | 1 min    | 3+ regions
REST              | /health (each dependency)     | 5 min    | 1 region
SCRIPTED_REST     | Login → profile flow          | 5 min    | 2 regions
SCRIPTED_BROWSER  | Login → cart → checkout flow  | 15 min   | 2 regions
REST              | TLS certificate expiry check  | 1 day    | 1 region (alert <30 days)
```

---

## Decision 4: Multi-Region APM Domain Strategy

**Ask**: "Is this a multi-region deployment? What is the maximum acceptable observability gap during an OCI regional event?"

| Option | RTO | RPO | Cost | Complexity |
|---|---|---|---|---|
| **Single-Region APM** | 0 (SaaS managed) | Span loss during region outage | $ | Low |
| **One domain per OCI region** | 0 per region | Zero — local agents report locally | $$ | Medium |
| **OTLP Collector dual-write fanout** | 0 | Zero — spans written to 2 domains | $$$ | High |

**Dual-write OTLP Collector config** (for zero observability loss):
```yaml
exporters:
  otlphttp/primary:
    endpoint: "https://{primary-domain}.apm-agt.us-ashburn-1.oci.oraclecloud.com/20200101/opentelemetry/private"
    headers: { Authorization: "dataKey ${APM_KEY_PRIMARY}" }
  otlphttp/secondary:
    endpoint: "https://{secondary-domain}.apm-agt.eu-frankfurt-1.oci.oraclecloud.com/20200101/opentelemetry/private"
    headers: { Authorization: "dataKey ${APM_KEY_SECONDARY}" }
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [otlphttp/primary, otlphttp/secondary]
```

**Cost note**: Dual-write doubles span ingestion costs. Apply conservative sampling (errors-only) on the secondary domain to reduce cost while maintaining DR coverage.

---

## Decision 5: PII Scrubbing Approach

**Ask**: "What PII may appear in span attributes (URL parameters, HTTP headers, SQL bind variables)? What is the regulatory obligation (GDPR, PCI-DSS, HIPAA)?"

| Option | Use When | Enforcement |
|---|---|---|
| **APM Java Agent exclude properties** | Java-only stack; simple parameter/header exclusion | Per-agent config; can be inconsistent across services |
| **OTLP Collector `redaction` processor** | Polyglot or multi-service; compliance-driven; consistent enforcement | Central pipeline; applies to all services forwarding to Collector |

**APM Java Agent** (parameter exclusion):
```properties
# apm-agent.properties
com.oracle.apm.agent.tracer.http.request.params.exclude=password,token,apikey,ssn,credit_card
com.oracle.apm.agent.tracer.http.request.headers.exclude=Authorization,Cookie,X-API-Key
com.oracle.apm.agent.tracer.jdbc.bind.vars.capture=false  # Disable SQL bind var capture
```

**OTLP Collector** `redaction` processor (preferred for multi-service):
```yaml
processors:
  redaction:
    allow_all_keys: true
    blocked_values:
      - "4[0-9]{12}(?:[0-9]{3})?"         # Visa card pattern
      - "[0-9]{3}-[0-9]{2}-[0-9]{4}"       # SSN pattern
    summary: debug
  attributes/remove_headers:
    actions:
      - key: http.request.header.authorization
        action: delete
      - key: http.request.header.cookie
        action: delete
```

**Verification TQL**:
```
show spans where attributes["http.url"] LIKE "%password=%" 
  OR attributes["http.request.header.authorization"] IS NOT NULL
limit 10
# Expected: 0 results after scrubbing rules are applied
```

**Critical**: APM Datastore does not support span-level deletion after ingestion. Scrubbing must occur before the Data Upload Endpoint receives the span.
