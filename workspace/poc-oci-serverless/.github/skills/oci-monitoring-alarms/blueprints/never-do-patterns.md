# 🚫 Never Do Patterns — OCI Monitoring Alarms

---

## Anti-Pattern 1: Hardcoding Credentials for PostMetricData

**Risk**: CRITICAL — credential leak exposes full OCI API access; OCI Audit loses per-resource traceability.

```python
# ❌ WRONG — never hardcode credentials
config = {
    "user": "ocid1.user.oc1..aaaa...",
    "key_content": "-----BEGIN RSA PRIVATE KEY-----\nMIIEow...",  # SECRET IN CODE
    "fingerprint": "aa:bb:cc:...",
    "tenancy": "ocid1.tenancy.oc1..aaaa...",
    "region": "us-ashburn-1"
}
client = oci.monitoring.MonitoringClient(config)
```

```python
# ✅ CORRECT — instance principal (Compute) or resource principal (Functions)
import oci
signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
client = oci.monitoring.MonitoringClient(
    config={},
    service_endpoint="https://telemetry-ingestion.us-ashburn-1.oraclecloud.com",
    signer=signer
)
```

**Detection**:
```bash
grep -r "key_content\|private_key\|api_key\|USER_OCID\|TENANCY_OCID" \
  --include="*.py" --include="*.java" --include="*.go" .
# Any result = credential in code — must be removed
```

---

## Anti-Pattern 2: Default PT1M `pending_duration` on Threshold Alarms

**Risk**: HIGH — single-evaluation FIRING on volatile metrics produces alert fatigue; on-call teams miss genuine incidents.

```hcl
# ❌ WRONG — default PT1M fires on any single metric spike
resource "oci_monitoring_alarm" "cpu_high" {
  query    = "CpuUtilization[1m].mean() > 80"
  severity = "CRITICAL"
  # pending_duration not set — defaults to PT1M
}
```

```hcl
# ✅ CORRECT — sustained condition required before FIRING
resource "oci_monitoring_alarm" "cpu_high" {
  query            = "CpuUtilization[1m].mean() > 80"
  severity         = "CRITICAL"
  pending_duration = "PT5M"   # must persist for 5 minutes
}
```

**Detection**:
```bash
oci monitoring alarm list \
  --compartment-id $COMPARTMENT_OCID \
  --query 'data[?"pending-duration"==`"PT1M"` && "is-enabled"==`true` && severity!=`"INFO"`].{name:"display-name",severity:severity}'
# Any result = alarm needs pending_duration update
```

---

## Anti-Pattern 3: Disabling Alarms for Planned Maintenance

**Risk**: HIGH — `is_enabled = false` stops evaluation; if not re-enabled, creates a silent monitoring gap that survives indefinitely.

```hcl
# ❌ WRONG — disabling stops evaluation; human must remember to re-enable
resource "oci_monitoring_alarm" "cpu_high" {
  is_enabled = false   # "temporary" for maintenance — often forgotten
}
```

```hcl
# ✅ CORRECT — suppression silences notifications; alarm keeps evaluating
resource "oci_monitoring_alarm_suppression" "maintenance" {
  alarm_suppression_target {
    target_type = "ALARM"
    alarm_id    = oci_monitoring_alarm.cpu_high.id
  }
  display_name        = "maintenance-CHG-2026-0551"
  description         = "Scheduled patching window CHG-2026-0551"
  time_suppress_from  = "2026-06-10T02:00:00.000Z"
  time_suppress_until = "2026-06-10T04:00:00.000Z"   # auto-expires
  level               = "ALARM"
}
```

**Detection**:
```bash
oci monitoring alarm list \
  --compartment-id $COMPARTMENT_OCID \
  --query 'data[?"is-enabled"==`false`].{id:id,name:"display-name",updated:"time-updated"}'
# Review each result — confirm intentional disablement vs forgotten post-maintenance state
```

---

## Anti-Pattern 4: Posting Custom Metrics to the Wrong API Endpoint

**Risk**: MEDIUM — `telemetry` endpoint returns HTTP 404 for PostMetricData; metrics are silently dropped; alarms based on custom metrics never fire or fire as absence alerts.

```python
# ❌ WRONG — telemetry endpoint does NOT accept PostMetricData
client = oci.monitoring.MonitoringClient(
    config=config,
    service_endpoint="https://telemetry.us-ashburn-1.oraclecloud.com"   # WRONG for writes
)
```

```python
# ✅ CORRECT — telemetry-ingestion endpoint for PostMetricData ONLY
client = oci.monitoring.MonitoringClient(
    config={},
    service_endpoint="https://telemetry-ingestion.us-ashburn-1.oraclecloud.com",  # CORRECT
    signer=signer
)
```

**Terraform variable pattern**:
```hcl
variable "oci_region" { default = "us-ashburn-1" }

locals {
  telemetry_endpoint           = "https://telemetry.${var.oci_region}.oraclecloud.com"
  telemetry_ingestion_endpoint = "https://telemetry-ingestion.${var.oci_region}.oraclecloud.com"
}
# Use telemetry_ingestion_endpoint for all PostMetricData SDK configuration
```

**Detection**:
```bash
# Endpoint test — should return 401/405, NOT 404
curl -I https://telemetry-ingestion.${OCI_REGION}.oraclecloud.com/20180401/metrics \
  2>/dev/null | grep "HTTP/"
# HTTP/2 404 = wrong endpoint; HTTP/2 401 or 405 = correct endpoint
```

---

## Anti-Pattern 5: Missing `repeat_notification_duration` on CRITICAL Alarms

**Risk**: MEDIUM — default delivers one notification on state transition; a missed page on a P1 burns SLA time silently. FIRING alarm with no re-notification = invisible extended outage.

```hcl
# ❌ WRONG — single notification only; missed page = no follow-up
resource "oci_monitoring_alarm" "p1_alarm" {
  severity = "CRITICAL"
  # repeat_notification_duration not set — fires once on OK→FIRING
}
```

```hcl
# ✅ CORRECT — re-pages every 15 minutes while alarm remains FIRING
resource "oci_monitoring_alarm" "p1_alarm" {
  severity                     = "CRITICAL"
  pending_duration             = "PT3M"
  repeat_notification_duration = "PT15M"   # re-notify if still FIRING after 15 min
}
```

**Detection**:
```bash
oci monitoring alarm list \
  --compartment-id $COMPARTMENT_OCID \
  --query 'data[?severity==`"CRITICAL"` && "repeat-notification-duration"==`null`].{name:"display-name",severity:severity}'
# Any result = CRITICAL alarm without repeat notification
```
