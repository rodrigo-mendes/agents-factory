# 🚫 Never Do Patterns — OCI Logging

## Anti-Pattern 1: Default 30-Day Retention on Production Logs

**Risk**: CRITICAL — Compliance violation, irreversible data loss

❌ **Wrong** — omitting `retention_duration` silently accepts 30-day default:
```hcl
resource "oci_logging_log" "api_log" {
  display_name = "api-service-access"
  log_group_id = oci_logging_log_group.app.id
  log_type     = "CUSTOM"
  is_enabled   = true
  # retention_duration not set → silently defaults to 30 days
}
```

✅ **Correct** — always explicit at creation time:
```hcl
resource "oci_logging_log" "api_log" {
  display_name       = "api-service-access"
  log_group_id       = oci_logging_log_group.app.id
  log_type           = "CUSTOM"
  is_enabled         = true
  retention_duration = 90  # Set at creation — retroactive increase cannot recover deleted data
}
```

**Detection:**
```bash
oci logging log list --log-group-id <log-group-ocid> \
  --query 'data[?"retention-duration"==`30`].{id:id,name:"display-name"}'
```

**Impact**: Compliance audit failure; no log evidence for events older than 30 days; permanent data loss.

---

## Anti-Pattern 2: `NONE` Parser in Production UMA

**Risk**: HIGH — Operational blind spot, logs become unsearchable blobs

❌ **Wrong**:
```hcl
parser {
  parser_type = "NONE"  # Raw string — no field extraction
}
```

✅ **Correct** — minimum viable structured parsing:
```hcl
# Option A: App emits JSON
parser {
  parser_type = "JSON"
}

# Option B: Fixed-format text — extract at least timestamp and level
parser {
  parser_type = "REGEXP"
  expression  = "^(?P<timestamp>\\d{4}-\\d{2}-\\d{2}T[\\d:.]+Z?) (?P<level>[A-Z]+) (?P<message>.*)$"
}

# Option C: Start with NONE in dev, but convert before prod promotion
# Add a Terraform lifecycle check or CI gate to block NONE in prod environments
```

**Impact**: Zero field-level searchability in Log Explorer; Connector Hub logRule filters cannot match fields; log-derived metrics impossible; root cause analysis requires raw string grep.

---

## Anti-Pattern 3: Single Log Group for All Log Types

**Risk**: HIGH — IAM scope collapse, selective routing impossible

❌ **Wrong**:
```hcl
# One log group containing app logs, VCN flow logs, and DB audit
resource "oci_logging_log_group" "everything" {
  display_name = "all-logs"  # Developers reading app logs can also read VCN flow + DB audit
}
```

✅ **Correct** — domain-separated log groups:
```hcl
resource "oci_logging_log_group" "app_logs"      { display_name = "app-service-logs" ... }
resource "oci_logging_log_group" "infra_logs"    { display_name = "infra-platform-logs" ... }
resource "oci_logging_log_group" "security_logs" { display_name = "security-audit-logs" ... }
```

**Detection:**
```bash
# Find log groups with mixed log types (both CUSTOM and SERVICE)
oci logging log list --log-group-id <ocid> \
  --query 'data[].{"type":"log-type","name":"display-name"}'
# Red flag: results contain both log-type=CUSTOM and log-type=SERVICE
```

**Impact**: Unauthorized access to sensitive log data; IAM grant to app developers inadvertently exposes VCN flow logs and database audit events; Connector Hub cannot selectively route by domain.

---

## Anti-Pattern 4: Enable High-Volume Service Logs Without Archival Pipeline

**Risk**: HIGH — Permanent compliance data loss, unexpected cost

❌ **Wrong**:
```hcl
# Log enabled with no Connector Hub connector pre-deployed
resource "oci_logging_log" "vcn_flow" {
  log_type           = "SERVICE"
  is_enabled         = true
  retention_duration = 180  # 180-day max, but no archival → data gap after 180 days
  # No depends_on archival connector
}
```

✅ **Correct** — archival pipeline first, log second:
```hcl
resource "oci_sch_service_connector" "vcn_archiver" { ... }  # Connector first

resource "oci_logging_log" "vcn_flow" {
  depends_on = [oci_sch_service_connector.vcn_archiver]  # Log AFTER archival confirmed
  log_type   = "SERVICE"
  is_enabled = true
  retention_duration = 180
}
```

**Impact**: All log data from log-enable date to archival-pipeline-deploy date is permanently lost. Compliance audit cannot produce evidence for that gap period. Retroactive recovery is impossible.

---

## Anti-Pattern 5: VCN Flow Logs at `all` Category on Every Subnet

**Risk**: MEDIUM — Cost overrun, pipeline saturation

❌ **Wrong**:
```hcl
# Applying "all" category to every subnet — accepted + rejected traffic = massive volume
configuration {
  source {
    category = "all"     # Millions of events/day on busy subnets
    resource = oci_core_subnet.app_subnet.id
    service  = "flowlogs"
    ...
  }
}
```

✅ **Correct** — risk-based category selection:
```hcl
# App/internal subnets: rejected traffic only (security events without accepted-traffic noise)
configuration {
  source {
    category = "reject"  # Security events only
    resource = oci_core_subnet.app_subnet.id
    service  = "flowlogs"
    ...
  }
}

# Perimeter / internet-facing subnets: all traffic (forensics-grade, justified cost)
configuration {
  source {
    category = "all"     # Only for perimeter — document compliance justification
    resource = oci_core_subnet.perimeter_subnet.id
    service  = "flowlogs"
    ...
  }
}
```

**Detection:**
```bash
oci logging log list --log-group-id <log-group-ocid> \
  --query 'data[?configuration.source.category==`all` && configuration.source.service==`flowlogs`].{id:id,resource:"configuration.source.resource"}'
# Review each result — confirm it is a perimeter/compliance-required subnet
```

**Impact**: Ingestion cost overrun; Object Storage archival becomes unwieldy (billions of records); downstream Connector Hub pipelines saturated; OCI Logging ingestion throttling risk.

---

## Anti-Pattern 6: UMA Configuration Targeting Individual Instance OCIDs

**Risk**: HIGH — Log collection gaps on every instance replacement

❌ **Wrong**:
```hcl
group_association {
  group_list = [
    "ocid1.instance.oc1.sa-saopaulo-1.xxxxx",  # Hardcoded instance OCIDs
    "ocid1.instance.oc1.sa-saopaulo-1.yyyyy"   # Break on every auto-scale event
  ]
}
```

✅ **Correct** — dynamic group with compartment-matching rule:
```hcl
# Dynamic group (tenancy-level resource)
resource "oci_identity_dynamic_group" "app_instances" {
  compartment_id = var.tenancy_ocid
  name           = "prod-app-instances"
  matching_rule  = "ALL {instance.compartment.id = '${var.app_compartment_ocid}'}"
}

resource "oci_logging_unified_agent_configuration" "collector" {
  group_association {
    group_list = [oci_identity_dynamic_group.app_instances.id]  # OCID of the dynamic group
  }
  ...
}
```

**Impact**: Every auto-scaling event, rolling deployment, or instance pool replacement creates a log collection gap. New instances are not enrolled until the UMA config is manually updated — silent data loss until discovered.
