# Never Do Patterns — OCI Service Connector Hub

Each anti-pattern shows ❌ what not to do and ✅ the correct alternative with real impact statements.

---

## Anti-Pattern 1 — Connector Without Pre-Existing IAM Policies

**Risk Level**: CRITICAL
**Impact**: Connector enters FAILED lifecycle state on activation and **silently drops all pipeline data**. No retry, no buffer, no recovery for the missed period. FAILED connectors emit no OCI Monitoring metrics — data loss is invisible until downstream systems report missing data.

```hcl
# ❌ WRONG: connector created before IAM policy — will immediately enter FAILED state
resource "oci_sch_service_connector" "log_archive" {
  compartment_id = var.compartment_ocid
  display_name   = "log-archive"
  source { ... }
  target { ... }
}

resource "oci_identity_policy" "connector_policy" {
  # Created after connector — too late
}
```

```hcl
# ✅ CORRECT: policy created first, connector depends on it
resource "oci_identity_policy" "connector_policy" {
  compartment_id = var.compartment_ocid
  name           = "connector-hub-policy"
  statements = [
    "allow service serviceconnectors to read log-content in compartment ${var.source_compartment_name}",
    "allow service serviceconnectors to manage objects in compartment ${var.target_compartment_name} where target.bucket.name = '${var.bucket_name}'",
  ]
}

resource "oci_sch_service_connector" "log_archive" {
  depends_on     = [oci_identity_policy.connector_policy]
  compartment_id = var.compartment_ocid
  display_name   = "log-archive"
  source { ... }
  target { ... }
}
```

**Detection**:
```bash
oci sch service-connector list --compartment-id <OCID> --lifecycle-state FAILED \
  --query 'data[].{id:id,name:"display-name",details:"lifecycle-details"}'
```

---

## Anti-Pattern 2 — Logging Source Without Log Group Scoping in Production

**Risk Level**: HIGH
**Impact**: Ingests ALL compartment logs including `_Audit` events. Operators with access to the Object Storage target gain unintended access to audit data. Cost overrun from unbounded log volume. Audit events contaminate application log pipelines.

```hcl
# ❌ WRONG: compartment-level source with no log group scoping
source {
  kind = "logging"
  log_sources {
    compartment_id = var.compartment_ocid
    # log_group_id omitted = ALL logs in compartment
  }
}
```

```hcl
# ✅ CORRECT: always scope to log group (minimum)
source {
  kind = "logging"
  log_sources {
    compartment_id = var.compartment_ocid
    log_group_id   = oci_logging_log_group.app_logs.id
  }
}

# ✅ CORRECT: audit-only connector (separate resource, uses _Audit sentinel)
source {
  kind = "logging"
  log_sources {
    compartment_id = var.tenancy_ocid
    log_group_id   = "_Audit"
  }
}
```

---

## Anti-Pattern 3 — No Error Monitoring on Connector Lifecycle State

**Risk Level**: HIGH
**Impact**: A connector that transitions to FAILED state produces no visible signal. Downstream systems (log archives, SIEM feeds, custom metrics) silently receive no data until operators discover the issue days later — creating compliance audit gaps and SLA breaches.

```hcl
# ❌ WRONG: connector deployed with no associated alarm
resource "oci_sch_service_connector" "log_archive" {
  # ...
}
# No oci_monitoring_alarm resource anywhere
```

```hcl
# ✅ CORRECT: deploy error alarm alongside every production connector
resource "oci_monitoring_alarm" "connector_error" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.connector_display_name}-error-alarm"
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_service_connector_hub"
  query                 = "ErrorCount[1m].sum() > 0"
  severity              = "CRITICAL"
  destinations          = [oci_ons_notification_topic.ops_alerts.id]
  is_enabled            = true
}

# Complementary: alarm on absence of data throughput (detects silent FAILED state)
resource "oci_monitoring_alarm" "connector_no_throughput" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.connector_display_name}-no-throughput-alarm"
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_service_connector_hub"
  query                 = "BytesTransferred[5m].sum() == 0"
  severity              = "WARNING"
  destinations          = [oci_ons_notification_topic.ops_alerts.id]
  is_enabled            = true
}
```

---

## Anti-Pattern 4 — Overly Broad IAM Policy for Connector Service Principal

**Risk Level**: HIGH
**Impact**: Grants the connector hub service principal blast radius far beyond the pipeline's needs. A misconfigured or malicious connector modification could read/write unintended resources, causing unauthorized data access or data corruption.

```hcl
# ❌ WRONG: unrestricted wildcard grant
resource "oci_identity_policy" "connector_policy" {
  statements = [
    "allow service serviceconnectors to manage all-resources in tenancy"  # Grants everything
  ]
}
```

```hcl
# ✅ CORRECT: minimum required verbs with resource-level where conditions
resource "oci_identity_policy" "connector_policy" {
  statements = [
    # Read ONLY from source log content — not manage, not use
    "allow service serviceconnectors to read log-content in compartment ${var.source_compartment_name}",
    # Write ONLY to the specific named bucket — not all objects in the compartment
    "allow service serviceconnectors to manage objects in compartment ${var.target_compartment_name} where target.bucket.name = '${var.bucket_name}'",
  ]
}
```

**IAM verb reference per source/target combination**:
- Logging source → `read log-content`
- Streaming source → `use stream-pull` on the specific stream
- Object Storage target → `manage objects` with `where target.bucket.name = '<name>'`
- Functions target → BOTH `use fn-function` AND `use fn-invocation` (fn-function is REQUIRED so the serviceconnector principal can resolve the function; omitting it denies every SCH invoke at authorization with ZERO function logs and rising ErrorsAtTarget — per official OCI docs a Functions target needs both verbs)
- ONS target → `use ons-topics` on the specific topic
- Monitoring target → `use metrics`
- Logging Analytics target → `use log-analytics`

---

## Anti-Pattern 5 — Connector Loop: Logging Source + Logging Target in Same Compartment

**Risk Level**: CRITICAL
**Impact**: Target log group activity events re-trigger the source, creating exponential log amplification. Can escalate to tenancy-level cost explosion and OCI Logging throttling that causes data loss **across all logging in the tenancy** — not just this connector.

```hcl
# ❌ CRITICAL WRONG: source and target are both Logging in the same compartment
resource "oci_sch_service_connector" "loop_danger" {
  source {
    kind = "logging"
    log_sources {
      compartment_id = var.compartment_ocid
      log_group_id   = oci_logging_log_group.app_logs.id
    }
  }
  target {
    kind          = "logging"
    log_group_id  = oci_logging_log_group.aggregated_logs.id  # Same compartment — LOOP RISK
    log_source_identifier = "connector-output"
  }
}
```

```hcl
# ✅ CORRECT: cross-compartment Logging target (source in app compartment, target in observability compartment)
# OR use Object Storage / Logging Analytics targets instead of re-ingesting into OCI Logging
resource "oci_sch_service_connector" "safe_aggregation" {
  source {
    kind = "logging"
    log_sources {
      compartment_id = var.app_compartment_ocid      # app compartment
      log_group_id   = oci_logging_log_group.app_logs.id
    }
  }
  target {
    kind                  = "logging"
    log_group_id          = oci_logging_log_group.central_logs.id  # observability compartment — no active connectors sourcing from it
    log_source_identifier = "app-aggregated"
  }
}
```

**Detection**:
```bash
oci sch service-connector list --compartment-id <OCID> \
  --query 'data[?source.kind==`logging` && target.kind==`logging`].{id:id,name:"display-name"}'
```

---

## Anti-Pattern 6 — Function Task Without Batch Size Tuning

**Risk Level**: MEDIUM
**Impact**: Default batch parameters cause either thousands of tiny cold-start invocations per hour (cost overrun) or batches that wait the maximum time before invoking (unacceptable pipeline latency). Cold starts on OCI Functions add 200–500 ms of overhead per invocation.

```hcl
# ❌ WRONG: function task with no batch tuning (uses framework defaults — often sub-optimal)
tasks {
  kind        = "function"
  function_id = oci_functions_function.transformer.id
  # No batch_size_in_kbs or batch_time_in_sec configured
}
```

```hcl
# ✅ CORRECT: tune based on throughput and latency requirements
# For cost-optimized (batch more, invoke less):
tasks {
  kind              = "function"
  function_id       = oci_functions_function.transformer.id
  batch_size_in_kbs = 5000  # Accumulate up to 5 MB before invoking (max: 6000 KB)
  batch_time_in_sec = 120   # Max wait 2 minutes (max: 600 sec)
}

# For latency-sensitive (invoke faster, smaller batches):
tasks {
  kind              = "function"
  function_id       = oci_functions_function.transformer.id
  batch_size_in_kbs = 500   # Smaller batch = more invocations, lower latency
  batch_time_in_sec = 10    # Invoke within 10 seconds regardless of size
}
```

**Monitoring**: Track invocation frequency via OCI Monitoring `oci_faas` namespace — `FunctionInvocationCount` spikes with small payload sizes indicate under-tuned batching.

---

## Anti-Pattern 7 — Using the Deprecated `lifecyle_details` Attribute (Typo)

**Risk Level**: MEDIUM
**Impact**: The `lifecyle_details` attribute (missing 'c' in lifecycle) was removed after January 27, 2026. Any Terraform configuration referencing it will fail on oracle/oci >= 8.x provider builds with a "An argument named lifecyle_details is not expected here" error.

```hcl
# ❌ WRONG: deprecated typo attribute — removed after January 27, 2026
output "connector_lifecycle" {
  value = oci_sch_service_connector.example.lifecyle_details  # typo — removed
}
```

```hcl
# ✅ CORRECT: use the correctly spelled attribute
output "connector_lifecycle_details" {
  value       = oci_sch_service_connector.example.lifecycle_details
  description = "Detail message — check for IAM errors if state is FAILED"
}
```

**Detection**:
```bash
grep -r "lifecyle_details" .
# Expected: no matches — any match is a bug
```

**Note**: `lifecycle_details` (correct spelling) is a computed attribute — you can reference it in outputs and `terraform plan` to diagnose FAILED connectors without triggering replacement.
