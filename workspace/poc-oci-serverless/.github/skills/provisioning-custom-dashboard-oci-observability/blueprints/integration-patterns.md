# Integration Patterns — provisioning-oci-observability

Full HCL for cross-service integrations. See [SKILL.md](../SKILL.md) for summaries.

---

## APM Domain ↔ OCI Vault (Secure Key Distribution)

```hcl
# Step 1: Create APM domain
resource "oci_apm_apm_domain" "main" {
  compartment_id = var.compartment_ocid
  display_name   = "apm-${var.environment}"
  is_free_tier   = false
  log_group_id   = oci_logging_log_group.apm_log_group.id
}

# Step 2: Retrieve private data key (sensitive)
data "oci_apm_data_keys" "private_key" {
  apm_domain_id = oci_apm_apm_domain.main.id
  data_key_type = "PRIVATE"
}

# Step 3: Store in Vault — application retrieves at runtime by OCID
resource "oci_vault_secret" "apm_key" {
  compartment_id = var.compartment_ocid
  vault_id       = var.vault_ocid
  key_id         = var.kms_key_ocid
  secret_name    = "apm-${var.environment}-private-data-key"

  secret_content {
    content_type = "BASE64"
    content      = base64encode(data.oci_apm_data_keys.private_key.data_keys[0].value)
  }

  lifecycle {
    ignore_changes = [secret_content]
  }
}

output "apm_key_secret_ocid" {
  value       = oci_vault_secret.apm_key.id
  description = "Secret OCID for OCI Functions/OKE to retrieve APM data key at runtime"
}
```

---

## OCI Logging ↔ Log Analytics (via Service Connector Hub)

Required to enable Log Analytics widget type in Management Dashboards.

```hcl
resource "oci_logging_log_group" "app_logs" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.app_name}-${var.environment}-logs"
  lifecycle { ignore_changes = [defined_tags] }
}

resource "oci_logging_log" "app_log" {
  display_name       = "${var.app_name}-custom"
  log_group_id       = oci_logging_log_group.app_logs.id
  log_type           = "CUSTOM"
  retention_duration = var.log_retention_days
}

resource "oci_sch_service_connector" "logs_to_log_analytics" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.environment}-logs-to-log-analytics"
  state          = "ACTIVE"

  source {
    kind = "logging"
    log_sources {
      compartment_id = var.compartment_ocid
      log_group_id   = oci_logging_log_group.app_logs.id
      log_id         = oci_logging_log.app_log.id
    }
  }

  target {
    kind                  = "loggingAnalytics"
    log_group_id          = var.log_analytics_log_group_ocid   # Log Analytics group OCID (not Logging)
    log_source_identifier = var.log_analytics_source_name      # e.g., "OCI Logging Generic"
  }

  depends_on = [oci_logging_log.app_log]  # Target must exist before connector starts

  freeform_tags = { ManagedBy = "terraform" }
}
```

**Gotcha**: `log_group_id` in the `target` block is a Log Analytics (Logging Analytics service) group OCID — different service from `oci_logging_log_group`. Log Analytics groups are not managed by the same resource type.

---

## APM Config ↔ OCI Monitoring Alarms (Custom Metrics)

Bridge from trace data to alertable metrics.

```hcl
# Step 1: METRIC_GROUP maps span attributes to custom namespace
resource "oci_apm_config_config" "error_metrics" {
  apm_domain_id = oci_apm_apm_domain.main.id
  config_type   = "METRIC_GROUP"
  display_name  = "api-error-metrics"
  filter_text   = "kind='SERVER'"

  dimensions {
    name         = "serviceName"
    value_source = "tags[\"service.name\"]"
  }

  metrics {
    name         = "ErrorSpanCount"
    unit         = "count"
    value_source = "errorSpanCount"
  }
}

# Step 2: Alarm queries the custom namespace produced by METRIC_GROUP
resource "oci_ons_notification_topic" "alerts" {
  compartment_id = var.compartment_ocid
  name           = "${var.environment}-alerts"
}

resource "oci_monitoring_alarm" "apm_errors" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.environment}-apm-error-count"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oracle_apm_custom"  # namespace from METRIC_GROUP (verify in OCI Console)
  query                 = "ErrorSpanCount[5m].sum() > 100"
  severity              = "WARNING"
  destinations          = [oci_ons_notification_topic.alerts.id]
  pending_duration      = "PT5M"
  repeat_notification_duration = "PT2H"
}
```

---

## Management Dashboards ↔ All Observability Sources

Full stack: APM traces + OCI Logging + Monitoring metrics → unified dashboard.

```hcl
# Tile 1: APM error rate (from APM domain)
resource "oci_management_dashboard_management_saved_search" "apm_tile" {
  compartment_id      = var.compartment_ocid
  display_name        = "${var.app_name} — APM Error Rate"
  provider_id         = "apm"
  provider_name       = "Application Performance Monitoring"
  provider_version    = "3.0"
  metadata_version    = "2.0"
  type                = "SEARCH_SHOW_IN_DASHBOARD"
  is_oob_saved_search = false
  nls                 = jsonencode({})
  drilldown_config    = jsonencode([])
  parameters_config   = jsonencode([])
  screen_image        = ""
  widget_template     = "visualizations/chartWidgetTemplate.html"
  widget_vm           = "visualizations/chartWidget"
  ui_config           = jsonencode({ vizType = "lineChart", defaultDataSource = "errors" })
  data_config         = jsonencode([{
    name       = "errors"
    type       = "apmDataSource"
    parameters = { apmDomainId = oci_apm_apm_domain.main.id }
  }])
}

# Tile 2: Log Analytics query (requires Service Connector Hub routing)
resource "oci_management_dashboard_management_saved_search" "log_tile" {
  compartment_id      = var.compartment_ocid
  display_name        = "${var.app_name} — Error Logs"
  provider_id         = "log-analytics"
  provider_name       = "Log Analytics"
  provider_version    = "2.0"
  metadata_version    = "2.0"
  type                = "SEARCH_SHOW_IN_DASHBOARD"
  is_oob_saved_search = false
  nls                 = jsonencode({})
  drilldown_config    = jsonencode([])
  parameters_config   = jsonencode([])
  screen_image        = ""
  widget_template     = "visualizations/chartWidgetTemplate.html"
  widget_vm           = "visualizations/chartWidget"
  ui_config           = jsonencode({ vizType = "table" })
  data_config         = jsonencode([{
    name = "logs"
    type = "logAnalyticsDataSource"
    parameters = {
      compartmentId = var.compartment_ocid
      savedSearchId = var.log_analytics_saved_search_id  # pre-existing Log Analytics saved search
    }
  }])
}

# Full dashboard import combining saved searches
resource "oci_management_dashboard_management_dashboards_import" "observability_suite" {
  import_details_file                    = "${path.module}/dashboards/observability-suite.json"
  override_dashboard_compartment_ocid    = var.compartment_ocid
  override_saved_search_compartment_ocid = var.compartment_ocid
  override_same_name                     = true

  depends_on = [
    oci_management_dashboard_management_saved_search.apm_tile,
    oci_management_dashboard_management_saved_search.log_tile,
  ]
}
```

---

## Module Composition — Complete Observability Stack

```hcl
# root/main.tf
module "apm" {
  source           = "./modules/apm-domain"
  compartment_ocid = var.compartment_ocid
  environment      = var.environment
  app_name         = var.app_name
  is_free_tier     = var.environment != "prod"
}

module "logging" {
  source                     = "./modules/observability-logging"
  compartment_ocid           = var.compartment_ocid
  environment                = var.environment
  app_name                   = var.app_name
  log_retention_days         = var.log_retention_days
  log_analytics_log_group_id = var.log_analytics_log_group_id
  depends_on                 = [module.apm]
}

module "alarms" {
  source           = "./modules/observability-alarms"
  compartment_ocid = var.compartment_ocid
  environment      = var.environment
  depends_on       = [module.apm]
}

module "dashboards" {
  source           = "./modules/management-dashboards"
  compartment_ocid = var.compartment_ocid
  environment      = var.environment
  app_name         = var.app_name
  apm_domain_id    = module.apm.apm_domain_id
  log_group_id     = module.logging.log_group_id
  depends_on       = [module.apm, module.logging]
}
```
