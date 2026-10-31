# ⚠️ Ask First Decisions — provisioning-oci-observability

Decision matrices for all 4 architectural crossroads. See [SKILL.md](../SKILL.md) for summaries.

---

## 1. Dashboard Import (Write-Once) vs. Saved Search CRUD

**Agent question**: "Are these dashboards being migrated from an existing OCI environment or Console export, or built from scratch in Terraform?"

| Option | Optimizes | Sacrifices | State Behavior |
|--------|-----------|------------|----------------|
| `oci_management_dashboard_management_dashboards_import` | Full layout, OOB dashboards, complex multi-tile | No Update/Delete, no drift detection | Persists after `destroy` |
| `oci_management_dashboard_management_saved_search` | CRUD lifecycle, per-tile version control | No layout control; tiles are independent | Full managed lifecycle |
| **Hybrid** | Tiles in TF + imported layout | Complexity, two resource types | Mixed |

**Decision factors**:
- Migrating from Console or another env → use **import** resource + `import_details_file`
- Building new dashboards in Terraform → use **saved_search** CRUD
- Need per-tile change tracking in PRs → use **saved_search** CRUD
- Provisioning Oracle OOB dashboards at scale → use **import**

```hcl
# Option A: Import (write-once, file-based)
resource "oci_management_dashboard_management_dashboards_import" "apm_suite" {
  import_details_file                    = "${path.module}/dashboards/apm-suite.json"
  override_dashboard_compartment_ocid    = var.compartment_ocid
  override_saved_search_compartment_ocid = var.compartment_ocid
  override_same_name                     = true
}

# Option B: Saved Search CRUD (fully managed)
resource "oci_management_dashboard_management_saved_search" "tile" {
  compartment_id      = var.compartment_ocid
  display_name        = "My Tile"
  provider_id         = "apm"
  provider_name       = "Application Performance Monitoring"
  provider_version    = "3.0"
  metadata_version    = "2.0"
  type                = "SEARCH_SHOW_IN_DASHBOARD"
  is_oob_saved_search = false
  nls                 = jsonencode({})
  ui_config           = jsonencode({ vizType = "lineChart" })
  data_config         = jsonencode([{
    name       = "data"
    type       = "apmDataSource"
    parameters = { apmDomainId = oci_apm_apm_domain.main.id }
  }])
  drilldown_config  = jsonencode([])
  parameters_config = jsonencode([])
  screen_image      = ""
  widget_template   = "visualizations/chartWidgetTemplate.html"
  widget_vm         = "visualizations/chartWidget"
}
```

---

## 2. APM Free Tier vs. Paid APM Domain

**Agent question**: "Is this a production environment with SLA requirements, or dev/POC?"

| Option | Spans/hr | Retention | Apdex Analytics | Cost |
|--------|----------|-----------|-----------------|------|
| `is_free_tier = true` | 1,000 | 7 days | ❌ | Free |
| `is_free_tier = false` | 500,000+ | 30 days | ✅ | Pay-per-span |

**Decision factors**:
- Dev / POC / learning → `is_free_tier = true`
- Any production or SLA-tracked environment → `is_free_tier = false`
- Apdex scoring required → `is_free_tier = false`
- Trace analytics dashboards required → `is_free_tier = false`

```hcl
# Option A: Free tier (dev/staging only)
resource "oci_apm_apm_domain" "dev" {
  compartment_id = var.compartment_ocid
  display_name   = "apm-dev"
  is_free_tier   = true
  log_group_id   = oci_logging_log_group.apm_log_group.id
}

# Option B: Production (paid, full analytics)
resource "oci_apm_apm_domain" "prod" {
  compartment_id = var.compartment_ocid
  display_name   = "apm-prod"
  is_free_tier   = false  # 500K spans/hr, 30-day retention, Apdex enabled
  log_group_id   = oci_logging_log_group.apm_log_group.id
}

# Pattern: environment-driven selection
resource "oci_apm_apm_domain" "main" {
  compartment_id = var.compartment_ocid
  display_name   = "apm-${var.environment}"
  is_free_tier   = var.environment != "prod"  # Free for dev/staging, paid for prod
  log_group_id   = oci_logging_log_group.apm_log_group.id
}
```

---

## 3. Per-Service vs. Shared Log Groups

**Agent question**: "Do different services have separate retention requirements or team-level IAM access separation?"

| Option | Optimizes | Sacrifices | IAM Complexity |
|--------|-----------|------------|----------------|
| Per-service log groups | Isolation, per-service retention, fine-grained IAM | More resources, more connector hub rules | High (1 policy set per service) |
| Shared log group | Simplicity, fewer resources | All-or-nothing IAM, single retention | Low |

**Decision factors**:
- Different teams own different services → **per-service**
- Different retention per compliance domain (90 days for auth logs, 30 for debug) → **per-service**
- Small team, uniform retention → **shared**
- Services have different data classification (PII vs. non-PII) → **per-service**

```hcl
# Option A: Per-service log groups
resource "oci_logging_log_group" "api_logs" {
  compartment_id = var.compartment_ocid
  display_name   = "api-${var.environment}-logs"
  lifecycle { ignore_changes = [defined_tags] }
}

resource "oci_logging_log_group" "auth_logs" {
  compartment_id = var.compartment_ocid
  display_name   = "auth-${var.environment}-logs"
  lifecycle { ignore_changes = [defined_tags] }
}

# Option B: Shared log group
resource "oci_logging_log_group" "app_logs" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.app_name}-${var.environment}-logs"
  lifecycle { ignore_changes = [defined_tags] }
}
```

---

## 4. Alarm Namespace Selection

**Agent question**: "What signal needs alerting — RUM browser traces, synthetic monitors, compute host metrics, or custom APM metric groups from METRIC_GROUP config?"

| Namespace | Signal Type | Example MQL |
|-----------|-------------|-------------|
| `oracle_apm_rum` | RUM error rate, page load | `ErrorRate[5m].mean() > 5` |
| `oracle_apm_synthetics` | Synthetic monitor pass/fail | `isFailure[5m].sum() > 0` |
| `oci_computeagent` | Host CPU, memory, disk | `CpuUtilization[5m].mean() > 80` |
| `oracle_oci_functions` | Function errors, duration | `FunctionInvocationErrors[5m].sum() > 10` |
| Custom (METRIC_GROUP) | Span-derived metrics | `ErrorSpanCount[5m].sum() > 100` |

```hcl
# Option A: RUM error rate alarm
resource "oci_monitoring_alarm" "rum_errors" {
  namespace = "oracle_apm_rum"
  query     = "ErrorRate[5m].mean() > 5"
  # ...
}

# Option B: Synthetic monitor failure alarm
resource "oci_monitoring_alarm" "synthetic_down" {
  namespace = "oracle_apm_synthetics"
  query     = "isFailure[5m].sum() > 0"
  severity  = "CRITICAL"
  # ...
}

# Option C: Custom metric group alarm (from oci_apm_config_config METRIC_GROUP)
resource "oci_monitoring_alarm" "custom_error_count" {
  namespace = "oracle_apm_custom"  # Namespace set in METRIC_GROUP config
  query     = "ErrorSpanCount[5m].sum() > 100"
  # ...
}
```

---

## `providerId` by data source (import / saved search)

Pick `providerId` per what the widget queries — wrong value is rejected at apply. Valid set: `opsi | APM | log-analytics | management-dashboard | management-agent | dbm | appmgmt`.

| Widget data source | `providerId` | dataConfig `type` |
|---|---|---|
| OCI Monitoring metrics (MQL) — `oci_faas`, `oci_apigateway`, custom namespace | `management-dashboard` | `MQL` |
| APM traces / spans (APM QL) | `APM` | APM data source |
| Log Analytics saved search | `log-analytics` | LA data source |

Ask: "Is this widget a metric (MQL → `management-dashboard`), a trace (APM QL → `APM`), or a log query (`log-analytics`)?" Never use `monitoring`/`oci-monitoring` — not valid.
