# ✅ Always Do — OCI APM Mandatory Patterns

---

## Pattern 1: One APM Domain Per Environment

Create one APM Domain per environment (dev/staging/prod) in separate OCI compartments. The domain is the IAM boundary, billing unit, and data retention scope.

```hcl
# terraform/apm-domains.tf
resource "oci_apm_apm_domain" "prod" {
  compartment_id = var.prod_compartment_ocid
  display_name   = "prod-${var.app_name}-apm"
  description    = "Production APM domain for ${var.app_name}"
  is_free_tier   = false
  defined_tags = {
    "operations.environment" = "production"
    "operations.app"         = var.app_name
    "cost.cost-center"       = var.cost_center
  }
}

resource "oci_apm_apm_domain" "staging" {
  compartment_id = var.staging_compartment_ocid
  display_name   = "staging-${var.app_name}-apm"
  is_free_tier   = false
}

resource "oci_apm_apm_domain" "dev" {
  compartment_id = var.dev_compartment_ocid
  display_name   = "dev-${var.app_name}-apm"
  is_free_tier   = true  # Always Free sufficient for dev
}
```

**Domain topology**:
```
tenancy
├── compartment: app-prod    → apm-domain: prod-{app}-apm
├── compartment: app-staging → apm-domain: staging-{app}-apm
└── compartment: app-dev     → apm-domain: dev-{app}-apm  (free tier)
```

---

## Pattern 2: Inject TraceId/SpanId into Log Records

Embed the active span's TraceId and SpanId into every application log record. Required for Trace Explorer → OCI Logging cross-signal navigation.

**APM Java Agent (auto-instrumented) — Logback MDC**:
```xml
<!-- logback.xml -->
<appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
  <encoder class="net.logstash.logback.encoder.LogstashEncoder">
    <provider class="net.logstash.logback.composite.loggingevent.LoggingEventPatternJsonProvider">
      <pattern>{"traceId":"%X{traceId}","spanId":"%X{spanId}"}</pattern>
    </provider>
  </encoder>
</appender>
```

**OpenTelemetry SDK (manual)**:
```java
// Inject at request handling boundary (e.g., servlet filter, interceptor)
Span span = Span.current();
SpanContext ctx = span.getSpanContext();
MDC.put("traceId", ctx.getTraceId());
MDC.put("spanId",  ctx.getSpanId());
// Clear MDC in finally block after request completes
```

**Verification TQL query**:
```
show spans where kind='SERVER' limit 5
# Copy a traceId, then search OCI Logging:
# search "..." | where data.traceId = '<trace-id>'
```

---

## Pattern 3: Store Data Keys in OCI Vault

Never hardcode APM Data Keys in source code, container images, or build artifacts. Store Private Data Keys in OCI Vault Secrets and inject at runtime.

```hcl
# terraform/apm-vault.tf
resource "oci_vault_secret" "apm_private_key" {
  compartment_id = var.app_compartment_ocid
  vault_id       = var.vault_ocid
  key_id         = var.master_key_ocid
  secret_name    = "apm-private-data-key-${var.environment}"
  secret_content {
    content_type = "BASE64"
    content      = base64encode(oci_apm_apm_domain.prod.data_upload_endpoint) # placeholder — set actual key post-domain creation
    stage        = "CURRENT"
  }
}
```

**OKE injection via environment variable**:
```yaml
# kubernetes/deployment.yaml
env:
  - name: APM_PRIVATE_DATA_KEY
    valueFrom:
      secretKeyRef:
        name: apm-private-key   # Synced from OCI Vault via External Secrets Operator
        key: value
```

**APM Java Agent config**:
```properties
# apm-agent.properties — reference env var, never hardcode
com.oracle.apm.agent.service.data.upload.endpoint=${APM_DATA_UPLOAD_ENDPOINT}
com.oracle.apm.agent.data.key=${APM_PRIVATE_DATA_KEY}
```

---

## Pattern 4: Tag Spans with service.name, service.version, deployment.environment

These three resource attributes are required for Service Map topology, APDEX scoring, and environment-scoped TQL queries.

**OpenTelemetry SDK (Java)**:
```java
Resource resource = Resource.getDefault()
    .merge(Resource.create(Attributes.of(
        ResourceAttributes.SERVICE_NAME,           "payment-service",
        ResourceAttributes.SERVICE_VERSION,        System.getenv("APP_VERSION"),
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT, System.getenv("ENV")
    )));
SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
    .setResource(resource)
    .build();
```

**Via environment variables (any OTel SDK)**:
```bash
export OTEL_SERVICE_NAME=payment-service
export OTEL_RESOURCE_ATTRIBUTES="service.version=1.4.2,deployment.environment=production"
```

**APM Java Agent**:
```properties
com.oracle.apm.agent.service.name=${SERVICE_NAME}
com.oracle.apm.agent.service.version=${APP_VERSION}
com.oracle.apm.agent.deployment.environment=${ENV}
```

**Verification TQL query**:
```
show spans where kind='SERVER' and attributes["service.name"] IS NULL limit 50
# Expected: 0 rows. Any result = untagged service requiring fix.
```

---

## Pattern 5: Enable Synthetic Monitors ≥7 Days Before Go-Live

At minimum, deploy REST + SCRIPTED_REST monitors on critical endpoints before production launch to establish response time baselines and alert thresholds.

```hcl
# terraform/synthetic-monitors.tf
resource "oci_apm_synthetics_monitor" "api_health" {
  apm_domain_id              = oci_apm_apm_domain.prod.id
  display_name               = "prod-${var.app_name}-api-health"
  monitor_type               = "REST"
  repeat_interval_in_seconds = 60
  status                     = "ENABLED"
  target                     = "https://api.${var.app_domain}/health"
  timeout_in_seconds         = 10

  vantage_points { name = "OraclePublic-us-ashburn-1" }
  vantage_points { name = "OraclePublic-eu-frankfurt-1" }
  vantage_points { name = "OraclePublic-ap-sydney-1" }

  configuration {
    config_type           = "REST_CONFIG"
    verify_response_codes = ["200"]
    is_failure_retried    = false
  }
}

# OCI Monitoring alarm on synthetic failure
resource "oci_monitoring_alarm" "synthetic_failure" {
  compartment_id        = var.prod_compartment_ocid
  display_name          = "synthetic-${var.app_name}-failure"
  metric_compartment_id = var.prod_compartment_ocid
  namespace             = "oracle_apm_synthetics"
  query                 = "ErrorCount[1m].sum() > 1"
  severity              = "CRITICAL"
  destinations          = [var.ops_notification_topic_ocid]
  is_enabled            = true
}
```

**Pre-launch checklist**:
```
☐ REST monitor on /health from 3+ geographic vantage points (1-min interval)
☐ SCRIPTED_REST or SCRIPTED_BROWSER on primary user journey (login flow)
☐ OCI Notifications topic connected to PagerDuty/email
☐ Monitor running ≥7 days in staging before production go-live
☐ Baseline P50/P95 response times documented from staging monitor results
```

---

## Pattern 6: Use Public Key for Browser/RUM, Private Key for Server Agents

Key type selection is a security boundary — never swap them.

| Deployment | Key Type | Reason |
|---|---|---|
| Browser RUM JavaScript agent | `PUBLIC` | Visible in page source; write-only; low exposure risk |
| Mobile app SDK | `PUBLIC` | Embedded in binary; write-only |
| APM Java Agent on Compute/OKE | `PRIVATE` | Server-side; store in Vault |
| OTLP Collector | `PRIVATE` | Server-side pipeline; store in Vault |
| OpenTelemetry SDK (server) | `PRIVATE` | Server-side; inject via env var |

**Browser RUM configuration (correct)**:
```javascript
// Only PUBLIC key here — safe to embed in HTML/JS
window.apmrum = {
  serviceName: 'checkout-frontend',
  webApplication: 'storefront',
  ociDataUploadEndpoint: 'https://{domain-id}.apm-agt.{region}.oci.oraclecloud.com',
  OracleAPMPublicDataKey: 'PUBLIC_KEY_VALUE_HERE',  // ✅ Public key
  sampleRate: 1.0
};
```

---

## Pattern 7: Propagate W3C TraceContext Headers at Every HTTP/gRPC Boundary

All services must propagate `traceparent` and `tracestate` headers. A single hop that drops or regenerates the TraceId fragments the trace permanently.

**OpenTelemetry SDK — configure W3C propagator**:
```java
OpenTelemetrySdk.builder()
    .setPropagators(ContextPropagators.create(
        TextMapPropagator.composite(
            W3CTraceContextPropagator.getInstance(),
            W3CBaggagePropagator.getInstance()
        )))
    .buildAndRegisterGlobal();
```

**OCI API Gateway — verify header passthrough** (check route header transformation rules do not strip `traceparent`):
```bash
oci api-gateway route-table get --route-table-id <ocid> \
  --query 'data.routes[].{"path":path,"headers":"request-policies.header-transformations"}'
# Confirm traceparent is NOT in the "rename" or "remove" transformation lists
```

**OCI Load Balancer — verify header forwarding**:
```bash
oci lb backend-set list --load-balancer-id <ocid> \
  --query 'data[].name' 
# Verify no header filtering rule removes traceparent in listener policies
```
