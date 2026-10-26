# 🚫 Never Do — OCI APM Anti-Patterns

---

## Anti-Pattern 1: Private Data Key in Client-Side Code or Public Repositories

**Risk**: CRITICAL — cost amplification attack, trace data corruption, domain reconnaissance

❌ **Wrong**:
```javascript
// Browser RUM config — NEVER use Private key in browser code
window.apmrum = {
  OracleAPMPublicDataKey: 'PRIVATE_KEY_abc123xyz456...',  // ❌ Private key exposed in page source
  ociDataUploadEndpoint: 'https://{domain-id}.apm-agt.region.oci.oraclecloud.com'
};
```

```properties
# Dockerfile or committed properties file
# ❌ Key hardcoded and visible in git history / container layers
apm.private.data.key=abc123xyz456...
```

✅ **Correct**:
```javascript
// Browser: Public key only — write-only, safe to expose
window.apmrum = {
  OracleAPMPublicDataKey: 'PUBLIC_KEY_value_here',  // ✅ Public key
};
```

```bash
# Server agents: inject Private key from OCI Vault at runtime
export APM_PRIVATE_DATA_KEY=$(oci secrets secret-bundle get \
  --secret-id <vault-secret-ocid> --query 'data."secret-bundle-content".content' --raw-output \
  | base64 --decode)
# Reference in apm-agent.properties: com.oracle.apm.agent.data.key=${APM_PRIVATE_DATA_KEY}
```

**Detection**:
```bash
git log --all -p | grep -E "[A-Za-z0-9+/]{40,}" | grep -i "apm.*key\|private.*key\|data.*key"
```

---

## Anti-Pattern 2: Single APM Domain Shared Across Environments

**Risk**: HIGH — production PII accessible to dev team; SLA reports contaminated; cost attribution broken

❌ **Wrong**:
```hcl
# One domain for everything — wrong
resource "oci_apm_apm_domain" "shared" {
  compartment_id = var.shared_compartment_ocid
  display_name   = "all-environments-apm"  # ❌ dev + staging + prod mixed
}
```

```
# Attempting to filter in TQL queries instead of domain isolation:
show spans where attributes["deployment.environment"]='production'  # ❌ prone to missed filters; developers see all env data by default
```

✅ **Correct**:
```hcl
# Separate domains per environment in separate compartments
resource "oci_apm_apm_domain" "prod"    { compartment_id = var.prod_compartment_ocid ... }
resource "oci_apm_apm_domain" "staging" { compartment_id = var.staging_compartment_ocid ... }
resource "oci_apm_apm_domain" "dev"     { compartment_id = var.dev_compartment_ocid; is_free_tier = true ... }
```

**Impact of shared domain**: Developer with Trace Explorer `use` permission on the shared domain can query ALL traces — including production spans with `userId`, `orderId`, `email` attributes. IAM compartment isolation is the correct boundary.

---

## Anti-Pattern 3: Missing `service.name` on Spans

**Risk**: HIGH — Service Map unavailable; APDEX scoring impossible; service-level alerting broken

❌ **Wrong**:
```java
// No resource attributes set — spans appear as "unknown" in Service Map
SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
    .addSpanProcessor(BatchSpanProcessor.builder(exporter).build())
    .build();  // ❌ No resource with service.name
```

```yaml
# OTel Collector sending to APM without service name in resource
# Result: all services appear as a single "unknown" node in topology
```

✅ **Correct**:
```java
Resource resource = Resource.getDefault()
    .merge(Resource.create(Attributes.of(
        ResourceAttributes.SERVICE_NAME,           "payment-service",
        ResourceAttributes.SERVICE_VERSION,        System.getenv("APP_VERSION"),
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT, System.getenv("ENV")
    )));
SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
    .setResource(resource)
    .addSpanProcessor(BatchSpanProcessor.builder(exporter).build())
    .build();
```

```bash
# Simplest fix — environment variable (all OTel SDK languages)
export OTEL_SERVICE_NAME=payment-service
```

**Detection TQL**:
```
show spans where attributes["service.name"] IS NULL and kind='SERVER' limit 100
```

---

## Anti-Pattern 4: 100% Sampling at >5K req/s Without Cost Controls

**Risk**: MEDIUM — unbounded APM billing; no proportional observability gain; possible throttling

❌ **Wrong**:
```yaml
# No sampling config — all spans ingested by default
exporters:
  otlphttp/apm:
    endpoint: "https://{domain-id}.apm-agt.{region}.oci.oraclecloud.com/..."
# At 5K req/s × 15 spans/trace = 4.5M spans/hour = 75K events/minute  ❌ unbounded cost
```

✅ **Correct** (tail-based for production):
```yaml
processors:
  tail_sampling:
    decision_wait: 30s
    policies:
      - name: errors              # Retain 100% of error traces
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow-traces         # Retain all traces >2s
        type: latency
        latency: { threshold_ms: 2000 }
      - name: probabilistic-ok   # 5% sample of healthy fast traces
        type: probabilistic
        probabilistic: { sampling_percentage: 5 }
```

**Cost formula**: `total_requests/hour × avg_spans_per_trace = APM events/hour`
- >5K req/s production → tail-based required
- Set OCI Budget alert at 120% of APM baseline spend

---

## Anti-Pattern 5: No Synthetic Monitors Before Production Go-Live

**Risk**: HIGH — zero alerting; first outage discovered via user complaints; no SLA baseline

❌ **Wrong**:
```
# Launch checklist missing:
☐ Synthetic monitors — SKIPPED ("we'll add them after launch")
# Result: production outage at 02:00 → detected by user tickets at 09:00 (7-hour MTTR)
```

✅ **Correct**:
```bash
# Verify monitors exist and are ENABLED before go-live (run in CI pipeline or runbook)
MONITOR_COUNT=$(oci apm-synthetics monitor list \
  --apm-domain-id "${APM_DOMAIN_OCID}" \
  --status ENABLED \
  --query 'length(data)' \
  --raw-output)

if [ "$MONITOR_COUNT" -lt 2 ]; then
  echo "ERROR: Fewer than 2 synthetic monitors enabled. Go-live blocked."
  exit 1
fi
```

**Minimum pre-launch monitors**:
```
☐ REST monitor on /health endpoint from 3+ vantage points (1-min interval)
☐ SCRIPTED_REST or SCRIPTED_BROWSER covering primary user journey
☐ OCI Monitoring alarm → OCI Notifications topic connected and tested
☐ Monitors running ≥7 days before go-live to establish response time baseline
```

---

## Anti-Pattern 6: APM Agent Egress Without Proper Subnet Routing

**Risk**: HIGH — spans silently dropped; no error in application logs; tracing appears broken

❌ **Wrong**:
```
# Compute instance in private subnet with no NAT or Service Gateway route
# APM agent attempts to reach: {domain-id}.apm-agt.{region}.oci.oraclecloud.com
# Result: TCP timeout → spans buffered then dropped; no 4xx/5xx logged
```

✅ **Correct — Service Gateway** (recommended for OCI workloads):
```hcl
# terraform/networking.tf
resource "oci_core_service_gateway" "sgw" {
  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_ocid
  display_name   = "service-gateway"
  services {
    service_id = data.oci_core_services.all_services.services[0].id  # "All {region} Services in Oracle Services Network"
  }
}

resource "oci_core_route_table" "private_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_ocid
  route_rules {
    network_entity_id = oci_core_service_gateway.sgw.id
    destination       = "all-iad-services-in-oracle-services-network"
    destination_type  = "SERVICE_CIDR_BLOCK"
  }
}
```

**NSG egress rule** (minimum scope — TCP/443 to OCI Services network, not 0.0.0.0/0):
```hcl
resource "oci_core_network_security_group_security_rule" "apm_egress" {
  network_security_group_id = var.app_nsg_ocid
  direction                 = "EGRESS"
  protocol                  = "6"  # TCP
  destination               = "all-iad-services-in-oracle-services-network"
  destination_type          = "SERVICE_CIDR_BLOCK"
  tcp_options { destination_port_range { min = 443; max = 443 } }
}
```

**Connectivity test from compute instance**:
```bash
curl -s -o /dev/null -w "%{http_code}" \
  "https://{domain-id}.apm-agt.{region}.oci.oraclecloud.com/20200101/ping" \
  -H "Authorization: dataKey {public-data-key}"
# Expected: 200. If 000 → routing issue. If 401 → key issue.
```
