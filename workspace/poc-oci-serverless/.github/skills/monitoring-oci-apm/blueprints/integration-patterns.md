# Integration Patterns — OCI APM

---

## APM ↔ OCI Logging

**Purpose**: Cross-signal correlation — navigate from a span in Trace Explorer to the correlated OCI Logging record using TraceId.

**Compatibility**:
- OCI APM: APM Control Plane API v20200630+
- OCI Logging: unified monitoring agent or OCI Functions log output
- Java: Logback + logstash-logback-encoder; Log4j2 supported via `ThreadContext`

**Logback setup** (logstash JSON encoder):
```xml
<!-- pom.xml dependency -->
<dependency>
  <groupId>net.logstash.logback</groupId>
  <artifactId>logstash-logback-encoder</artifactId>
  <version>7.4</version>
</dependency>

<!-- logback.xml — inject TraceId/SpanId from MDC into JSON log -->
<appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
  <encoder class="net.logstash.logback.encoder.LogstashEncoder">
    <provider class="net.logstash.logback.composite.loggingevent.MdcJsonProvider"/>
  </encoder>
</appender>
```

**OTel SDK — MDC injection**:
```java
// Servlet filter / Spring interceptor — inject once per request
Span activeSpan = Span.current();
SpanContext ctx = activeSpan.getSpanContext();
if (ctx.isValid()) {
    MDC.put("traceId", ctx.getTraceId());
    MDC.put("spanId",  ctx.getSpanId());
}
// Clear in finally block after request handling
```

**OCI Logging search after injection**:
```bash
oci logging-search search-logs \
  --search-query 'search "ocid1.loggroup.../ocid1.log..." | where data.traceId="<trace-id-from-apm>"' \
  --time-start "2024-05-25T10:00:00Z" \
  --time-end "2024-05-25T11:00:00Z"
```

**Common issues**:
- MDC empty in log records → verify active span exists before MDC.put; W3C propagation must reach the service
- `data.traceId` not indexed in OCI Logging → ensure log schema uses structured JSON; plain text logs cannot be searched by field

---

## APM ↔ OCI Vault

**Purpose**: Secure storage and runtime injection of APM Private Data Keys without hardcoding.

**Setup**:
```bash
# Store Private Data Key in Vault after APM Domain creation
PRIVATE_KEY=$(oci apm-control-plane data-keys list \
  --apm-domain-id <ocid> \
  --query 'data[?name==`auto_generated_private_datakey`].value | [0]' \
  --raw-output)

oci vault secret create-base64 \
  --compartment-id <compartment-ocid> \
  --vault-id <vault-ocid> \
  --key-id <master-key-ocid> \
  --secret-name "apm-private-key-prod" \
  --secret-content-content "$(echo -n "$PRIVATE_KEY" | base64)"
```

**OKE — External Secrets Operator** (sync Vault Secret → Kubernetes Secret):
```yaml
# ExternalSecret manifest
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: apm-private-key
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: oci-vault-store
    kind: SecretStore
  target:
    name: apm-private-key
  data:
    - secretKey: value
      remoteRef:
        key: apm-private-key-prod  # Vault Secret name
```

**Pod reference**:
```yaml
env:
  - name: APM_PRIVATE_DATA_KEY
    valueFrom:
      secretKeyRef:
        name: apm-private-key
        key: value
```

**Key rotation**:
```bash
# Rotate APM Data Keys annually (or on suspected exposure)
oci apm-control-plane apm-domain generate-data-keys \
  --apm-domain-id <ocid> \
  --generate-data-keys-details '[{"name":"auto_generated_private_datakey","dataKeyType":"PRIVATE"}]'
# After rotation: update Vault Secret value → pods restart picks up new key automatically
```

---

## APM ↔ OCI Monitoring

**Purpose**: Use synthetic monitor results and APM custom metrics to drive SLO alarms with OCI Monitoring native alerting.

**Namespaces**:
| Namespace | Metrics |
|---|---|
| `oracle_apm_synthetics` | `ErrorCount`, `ResponseTime`, `AvailabilityRate` per monitor |
| `oracle_apm` | `SpanCount`, `ErrorCount` per service (when APM emits to Monitoring) |

**SLO burn-rate alarm**:
```hcl
resource "oci_monitoring_alarm" "api_availability" {
  compartment_id        = var.prod_compartment_ocid
  display_name          = "api-availability-slo-burn"
  metric_compartment_id = var.prod_compartment_ocid
  namespace             = "oracle_apm_synthetics"
  # Alert if 2+ failures in any 1-min window across all monitors in domain
  query                 = "ErrorCount[1m]{apmDomainId = \"${oci_apm_apm_domain.prod.id}\"}.sum() > 1"
  severity              = "CRITICAL"
  destinations          = [oci_ons_notification_topic.pagerduty.id]
  is_enabled            = true
  message_format        = "ONS_OPTIMIZED"
  repeat_notification_duration = "PT5M"  # Re-alarm every 5 min while firing
}
```

**APDEX alarm** (via APM Config + OCI Monitoring metric export):
```hcl
resource "oci_apm_config_config" "checkout_apdex" {
  apm_domain_id = oci_apm_apm_domain.prod.id
  config_type   = "APDEX"
  display_name  = "checkout-api-apdex"
  filter_text   = "kind = 'SERVER' AND attributes[\"service.name\"] = 'checkout-api'"
  rules {
    filter_text              = "kind = 'SERVER'"
    is_apply_to_error_spans  = true
    is_enabled               = true
    satisfied_response_time  = 200    # T = 200ms
    tolerating_response_time = 800    # 4T = 800ms
    priority                 = 1
  }
}
```

---

## APM ↔ OpenTelemetry Collector

**Purpose**: Decouple application instrumentation from APM endpoint; enable tail-based sampling, PII scrubbing, and multi-backend export.

**OKE DaemonSet deployment** (recommended over sidecar — 1 Collector per node):
```yaml
# otel-collector-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: otel-collector
  namespace: observability
spec:
  selector:
    matchLabels:
      app: otel-collector
  template:
    spec:
      containers:
        - name: otel-collector
          image: otel/opentelemetry-collector-contrib:0.100.0
          resources:
            requests: { cpu: "200m", memory: "256Mi" }
            limits:   { cpu: "1000m", memory: "512Mi" }
          volumeMounts:
            - name: otel-config
              mountPath: /etc/otel
          env:
            - name: APM_PRIVATE_DATA_KEY
              valueFrom:
                secretKeyRef:
                  name: apm-private-key
                  key: value
      volumes:
        - name: otel-config
          configMap:
            name: otel-collector-config
```

**Full Collector config with tail sampling + APM export**:
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: "0.0.0.0:4317" }
      http: { endpoint: "0.0.0.0:4318" }

processors:
  memory_limiter:
    check_interval: 1s
    limit_percentage: 75
    spike_limit_percentage: 15
  batch:
    send_batch_size: 1000
    timeout: 10s
  tail_sampling:
    decision_wait: 30s
    num_traces: 50000
    policies:
      - name: errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow-traces
        type: latency
        latency: { threshold_ms: 2000 }
      - name: probabilistic-ok
        type: probabilistic
        probabilistic: { sampling_percentage: 5 }

exporters:
  otlphttp/apm:
    endpoint: "https://{domain-id}.apm-agt.{region}.oci.oraclecloud.com/20200101/observations/private"
    headers:
      Authorization: "dataKey ${APM_PRIVATE_DATA_KEY}"
    retry_on_failure:
      enabled: true
      initial_interval: 5s
      max_interval: 30s
      max_elapsed_time: 300s

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, tail_sampling, batch]
      exporters: [otlphttp/apm]
```

**Application OTLP SDK config** (point to DaemonSet node IP):
```bash
# Use Kubernetes Downward API to get node IP
export OTEL_EXPORTER_OTLP_ENDPOINT="http://$(cat /etc/pod-info/node-ip):4317"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
```

**Sizing**: 1 vCPU + 512MB RAM per Collector pod handles ~10K spans/sec; horizontal scale beyond that.
