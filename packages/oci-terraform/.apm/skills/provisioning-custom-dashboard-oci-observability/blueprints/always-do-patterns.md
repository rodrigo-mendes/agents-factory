# ✅ Always Do Patterns — provisioning-oci-observability

Full HCL examples for all 9 mandatory patterns. See [SKILL.md](../SKILL.md) for summaries.

---

## 1. Terraform Configuration Block with Provider Version Constraint

```hcl
terraform {
  required_version = ">= 1.9"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 8.0"
    }
  }

  backend "s3" {
    bucket                      = "my-org-terraform-state"
    key                         = "prod/observability/terraform.tfstate"
    region                      = "us-ashburn-1"
    endpoint                    = "https://<namespace>.compat.objectstorage.us-ashburn-1.oraclecloud.com"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    force_path_style            = true
  }
  # No native state locking on OCI Object Storage S3 backend.
  # Use HCP Terraform or OCI Resource Manager for team environments.
}
```

---

## 2. OCI Provider Authentication

```hcl
# Production: Instance Principal (OCI DevOps, OKE, Functions)
provider "oci" {
  region = var.region
  auth   = "InstancePrincipal"
}

# CI/CD pipeline (GitHub Actions + OCI OIDC):
provider "oci" {
  region = var.region
  auth   = "SecurityToken"
}

# Development only (local workstation):
provider "oci" {
  region           = var.region
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  # NEVER: private_key = "<raw PEM content>"
}
```

---

## 3. APM Domain with Log Group Integration

```hcl
resource "oci_logging_log_group" "apm_log_group" {
  compartment_id = var.compartment_ocid
  display_name   = "apm-${var.environment}-log-group"
  description    = "Log group for APM domain trace correlation"
  freeform_tags  = { Environment = var.environment, ManagedBy = "terraform" }
  lifecycle { ignore_changes = [defined_tags] }
}

resource "oci_apm_apm_domain" "main" {
  compartment_id = var.compartment_ocid
  display_name   = "apm-${var.environment}"
  is_free_tier   = var.apm_is_free_tier
  log_group_id   = oci_logging_log_group.apm_log_group.id  # Required for trace-log correlation
  freeform_tags  = { Environment = var.environment, ManagedBy = "terraform" }
}

data "oci_apm_data_keys" "private_key" {
  apm_domain_id = oci_apm_apm_domain.main.id
  data_key_type = "PRIVATE"
}

output "apm_private_data_key" {
  value       = data.oci_apm_data_keys.private_key.data_keys[0].value
  sensitive   = true  # MANDATORY: masks from plan/apply output and logs
  description = "APM private data key — store in OCI Vault, never in app config directly"
}

output "apm_endpoint" {
  value       = oci_apm_apm_domain.main.data_upload_endpoint
  description = "APM domain data upload endpoint for SDK configuration"
}
```

---

## 4. APM Config — Span Filter, Apdex, Metric Group

```hcl
resource "oci_apm_config_config" "server_span_filter" {
  apm_domain_id = oci_apm_apm_domain.main.id
  config_type   = "SPAN_FILTER"
  display_name  = "server-consumer-spans"
  filter_text   = "kind='SERVER' or kind='CONSUMER'"
  freeform_tags = { ManagedBy = "terraform" }
}

resource "oci_apm_config_config" "api_apdex" {
  apm_domain_id = oci_apm_apm_domain.main.id
  config_type   = "APDEX"
  display_name  = "api-apdex-rules"

  rules {
    display_name             = "fast-endpoints"
    filter_text              = "kind='SERVER' and operationName LIKE '/api/v1/%'"
    is_apply_to_error_spans  = true
    is_enabled               = true
    priority                 = 1
    satisfied_response_time  = 500   # ms
    tolerating_response_time = 2000  # ms
  }
}

resource "oci_apm_config_config" "error_metric_group" {
  apm_domain_id = oci_apm_apm_domain.main.id
  config_type   = "METRIC_GROUP"
  display_name  = "api-error-rate-metrics"
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
```

---

## 5. Logging — Log Group and Log with Explicit Retention

```hcl
resource "oci_logging_log_group" "app_log_group" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.app_name}-${var.environment}-logs"
  freeform_tags  = { Application = var.app_name, ManagedBy = "terraform" }
  lifecycle { ignore_changes = [defined_tags] }
}

resource "oci_logging_log" "app_custom_log" {
  display_name       = "${var.app_name}-custom"
  log_group_id       = oci_logging_log_group.app_log_group.id
  log_type           = "CUSTOM"
  retention_duration = var.log_retention_days  # 30 | 60 | 90 | 180 — always explicit
}

resource "oci_logging_log" "function_log" {
  display_name       = "${var.app_name}-function-invocation"
  log_group_id       = oci_logging_log_group.app_log_group.id
  log_type           = "SERVICE"
  retention_duration = var.log_retention_days

  configuration {
    source {
      category    = "invoke"
      resource    = var.function_ocid
      service     = "functions"
      source_type = "OCISERVICE"
    }
    compartment_id = var.compartment_ocid
  }
}
```

---

## 6. Monitoring Alarm with ONS Topic and pending_duration

```hcl
resource "oci_ons_notification_topic" "ops_alerts" {
  compartment_id = var.compartment_ocid
  name           = "${var.environment}-ops-alerts"
}

resource "oci_monitoring_alarm" "apm_error_rate" {
  compartment_id        = var.compartment_ocid
  display_name          = "${var.environment}-apm-high-error-rate"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oracle_apm_rum"
  query                 = "ErrorRate[5m].mean() > 5"
  severity              = "WARNING"
  destinations          = [oci_ons_notification_topic.ops_alerts.id]
  pending_duration      = "PT5M"                # Required: prevents flapping
  repeat_notification_duration = "PT2H"         # Prevents alert spam
  message_format        = "ONS_OPTIMIZED"
  notification_version  = "1.X"

  overrides {                                   # Multi-severity escalation (v8.x)
    query            = "ErrorRate[5m].mean() > 20"
    severity         = "CRITICAL"
    pending_duration = "PT2M"
    rule_name        = "critical-threshold"
    body             = "CRITICAL: Error rate >20% in ${var.environment}"
  }
}
```

---

## 7. Management Dashboard Saved Search (CRUD)

```hcl
resource "oci_management_dashboard_management_saved_search" "apm_error_trend" {
  compartment_id      = var.compartment_ocid
  display_name        = "${var.app_name}-APM Error Trend"
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

  ui_config = jsonencode({
    vizType          = "lineChart"
    defaultDataSource = "errorRate"
    isRefreshEnabled = true
  })

  # Use Terraform reference — never hardcode OCID
  data_config = jsonencode([{
    name       = "errorRate"
    type       = "apmDataSource"
    parameters = { apmDomainId = oci_apm_apm_domain.main.id }
  }])
}
```

---

## 8. Management Dashboard Bulk Import (Write-Once)

```hcl
# Export from source environment (for version control)
data "oci_management_dashboard_management_dashboards_export" "existing" {
  export_dashboard_id = var.export_dashboard_id_encoded  # URL-encoded JSON
}

# Import to target — file must be tracked in source control
resource "oci_management_dashboard_management_dashboards_import" "apm_suite" {
  import_details_file                    = "${path.module}/dashboards/apm-suite.json"
  override_dashboard_compartment_ocid    = var.compartment_ocid
  override_saved_search_compartment_ocid = var.compartment_ocid
  override_same_name                     = true
  # WARNING: No Read/Update/Delete lifecycle — changes to JSON not detected by terraform plan
}
```

---

## 9. Variable Validation for OCI-Specific Enum Values

```hcl
variable "log_retention_days" {
  type    = number
  default = 30
  validation {
    condition     = contains([30, 60, 90, 180], var.log_retention_days)
    error_message = "retention_duration must be one of: 30, 60, 90, 180"
  }
}

variable "alarm_severity" {
  type    = string
  default = "WARNING"
  validation {
    condition     = contains(["CRITICAL", "ERROR", "WARNING", "INFO"], var.alarm_severity)
    error_message = "Alarm severity must be CRITICAL, ERROR, WARNING, or INFO"
  }
}

variable "compartment_ocid" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "Must be a valid OCI compartment OCID starting with ocid1.compartment."
  }
}
```

---

## Import envelope — confirmed RENDER-VALID schema (`oci_management_dashboard_management_dashboards_import`)

Confirmed live 2026-07-07 (3 dashboards for `func-rr-rest-proxy`) and cross-checked against Oracle's official sample (`oracle-quickstart/oci-management-agent/sample-dashboards`). Two levels of validity:

- **Import-valid** (passes the apply HTTP 400 checks): structural fields — `tiles[]`+`savedSearches[]` nested per dashboard, `featuresConfig`, valid `providerId`.
- **Render-valid** (Console actually draws the widget): each **savedSearch** MUST carry `widgetTemplate` + `widgetVM` + a rich `uiConfig.chartInfo.jetConfig` + a `dataConfig` of `type:"monitoringDataSource"`. A minimal `{"vizType":"lineChart"}` uiConfig with `dataConfig:[{type:"MQL",query}]` **imports fine but the Console fails with "Dashboard service had an internal error while adding widget."**

### Metric (MQL) widget — the shape the Console renders

```json
{
  "dashboards": [
    {
      "dashboardId": "ocid1.custommanagementdashboard.oc1..my-ops",
      "displayName": "Ops Overview",
      "compartmentId": "${compartment_ocid}",
      "isOobDashboard": false, "isShowInHome": false,
      "providerId": "management-dashboard", "providerName": "Management Dashboard", "providerVersion": "3.0.0",
      "isShowDescription": true, "screenImage": "", "nls": {},
      "type": "normal",
      "metadataVersion": "2.0",
      "uiConfig": { "isFilteringEnabled": false, "isTimeRangeEnabled": true, "isRefreshEnabled": true },
      "dataConfig": [],
      "featuresConfig": { "crossService": { "shared": false } },
      "parametersConfig": [
        { "savedSearchId": "OOBSS-management-dashboard-compartment-filter", "displayName": "Compartment",
          "width": 3, "state": "DEFAULT", "name": "compartmentId", "localStorageKey": "compartmentId",
          "parametersMap": { "isStoreInLocalStorage": false, "isActiveCompartment": "true" } },
        { "name": "time", "displayName": "Time", "src": "$(context.time)" }
      ],
      "drilldownConfig": [],
      "tiles": [
        { "displayName": "Invocations", "savedSearchId": "ocid1.custommanagementsavedsearch.oc1..ops-invocations",
          "row": 0, "column": 0, "height": 4, "width": 6,
          "nls": {}, "uiConfig": {}, "dataConfig": [], "state": "DEFAULT", "drilldownConfig": [],
          "parametersMap": { "compartmentId": "$(dashboard.params.compartmentId)", "time": "$(dashboard.params.time)" } }
      ],
      "savedSearches": [
        {
          "id": "ocid1.custommanagementsavedsearch.oc1..ops-invocations",
          "displayName": "Invocations",
          "providerId": "management-dashboard", "providerName": "Management Dashboard", "providerVersion": "3.0.0",
          "compartmentId": "${compartment_ocid}", "isOobSavedSearch": false,
          "description": "FunctionInvocationCount per 1m", "nls": {},
          "type": "WIDGET_SHOW_IN_DASHBOARD", "metadataVersion": "2.0", "screenImage": "",
          "widgetTemplate": "visualizations/chartWidgetTemplate.html",
          "widgetVM": "visualizations/chartWidget",
          "parametersConfig": [], "drilldownConfig": [],
          "featuresConfig": { "crossService": { "shared": false } },
          "uiConfig": {
            "vizType": "chart",
            "chartInfo": {
              "jetConfig": { "type": "lineWithArea", "timeAxisType": "enabled",
                "xAxis": { "viewportMin": "$(params.time.start)", "viewportMax": "$(params.time.end)" },
                "yAxis": { "title": "" }, "dataCursor": "on" },
              "value": "aggregatedDatapoints.value", "group": "aggregatedDatapoints.timestamp",
              "colorBy": "_allDimensionConglomerate", "series": "_allDimensionConglomerate" },
            "defaultDataSource": "Invocations"
          },
          "dataConfig": [
            { "name": "Invocations", "type": "monitoringDataSource",
              "parameters": {
                "compartmentId": "$(params.compartmentId)",
                "startTime": "$(params.time.start)", "endTime": "$(params.time.end)",
                "regionName": "$(params.regionName)",
                "namespace": "oci_faas",
                "mql": "FunctionInvocationCount[1m]{applicationId=\"${application_id}\"}.sum()" } }
          ]
        }
      ]
    }
  ]
}
```

**Key render fields (each omission = silent Console "adding widget" error, NOT an apply error):**
- Dashboard `type: "normal"` (not `"DASHBOARD"`); dashboard `uiConfig` with `isTimeRangeEnabled/isRefreshEnabled`; dashboard `parametersConfig` wiring `compartmentId` (OOB compartment-filter saved search) + `time`.
- SavedSearch `widgetTemplate: "visualizations/chartWidgetTemplate.html"` + `widgetVM: "visualizations/chartWidget"`.
- SavedSearch `uiConfig.vizType: "chart"` with `chartInfo.jetConfig` (`type`: `lineWithArea|bar|pie|area`), `value: "aggregatedDatapoints.value"`, `group: "aggregatedDatapoints.timestamp"`.
- SavedSearch `dataConfig[].type: "monitoringDataSource"` with `parameters.mql` (the MQL string), `namespace`, and `$(params.*)` for compartmentId/time/regionName. NOT `{type:"MQL",query}`.
- Tiles reference the saved search by `savedSearchId` and pass `parametersMap` from `$(dashboard.params.*)`; tiles keep `uiConfig:{}`/`dataConfig:[]` (inherit from the saved search).

> **RENDER GOTCHA — a metric widget imports but shows NO DATA if `regionName` is undeclared.** Confirmed live 2026-07-07 (captured from Console `{JSON}`, Data source = Monitoring). The `dataConfig.parameters` reference `$(params.regionName)` AND `$(params.time.start)`/`$(params.time.end)` — so the **savedSearch MUST declare its own `parametersConfig`** with the three params, or they resolve to empty and the query silently returns nothing (widget draws blank even though the metric has data):
> ```json
> "parametersConfig": [
>   {"name":"time","required":true,"editUi":{"inputType":"savedSearch","filterTile":{"filterId":"OOBSS-management-dashboard-time-selector-filter","parametersMap":{"maxDurationDays":89}}}},
>   {"name":"compartmentId","required":true,"defaultFilterIds":["OOBSS-management-dashboard-compartment-filter"],"valueFormat":{"type":"object"},"editUi":{"inputType":"compartmentSelect"}},
>   {"name":"regionName","required":false,"defaultFilterIds":["OOBSS-management-dashboard-region-filter"],"valueFormat":{"type":"string"},"editUi":{"inputType":"savedSearch","filterTile":{"filterId":"OOBSS-management-dashboard-region-filter","parametersMap":{"selectionMode":"single"}}}}
> ]
> ```
> Also add `"maxDataPoints": "useIntervalExact"` to `dataConfig.parameters`, add the region filter to the **dashboard** `parametersConfig` (`{savedSearchId:"OOBSS-management-dashboard-region-filter", name:"regionName", localStorageKey:"regionName", parametersMap:{isStoreInLocalStorage:true}}`), and pass `regionName` in each tile `parametersMap`. Without the region param the dashboard imports clean and even passes the "adding widget" check, but every metric tile is empty.

### APM trace (TQL) widget — confirmed `tracesDataSource` shape

Confirmed live 2026-07-07 (captured from the Console `{JSON}` editor: Dashboards → Create query-based widget → Data source = **Traces**). Same `widgetTemplate`/`widgetVM` as metrics, but a **different dataConfig type/params** plus an `apmDomain` param.

- **savedSearch.dataConfig**: `type: "tracesDataSource"`, query goes in `parameters.apmQuery` (NOT `mql`), time via `$(params.startTime)`/`$(params.endTime)` (NOT `time.start`), plus `apmDomain: "$(params.apmDomain)"`, `maxDesiredDataPoints: 320`, `dimensionFilters: "$(params.flex)"`, `simplifyDataSource: true`.
- **savedSearch.parametersConfig**: `[{name:"time", defaultFilterIds:["OOBSS-management-dashboard-time-selector-filter"]}, {name:"apmDomain", defaultFilterIds:["OOBSS-APM-domain-filter"]}, {name:"flex"}]`.
- **dashboard.parametersConfig** adds the APM domain filter `{savedSearchId:"OOBSS-APM-domain-filter", name:"apmDomain", localStorageKey:"apmDomain", parametersMap:{isStoreInLocalStorage:true, compartmentId:"$(dashboard.params.compartmentId)"}}` alongside compartment + time filters. **dashboard.featuresConfig**: `{crossService:{shared:true}, serviceTypes:["APM"]}`. Tile `parametersMap`: `{compartmentId, time, apmDomain}`. The domain is picked at runtime via the OOB filter (defaults to the single domain) — the query does NOT hardcode an apmDomainId.

```json
"dataConfig": [{
  "name": "traceData", "type": "tracesDataSource",
  "parameters": {
    "compartmentId": "$(params.compartmentId)",
    "startTime": "$(params.startTime)", "endTime": "$(params.endTime)",
    "apmDomain": "$(params.apmDomain)",
    "maxDesiredDataPoints": 320, "dimensionFilters": "$(params.flex)",
    "apmQuery": "show spans avg(SpanDuration) as \"Latency\" where ServiceName = 'my-svc' and SpanKind = 'CLIENT' group by OperationName",
    "simplifyDataSource": true }
}]
```

`vizType:"table"` + `tableInfo.cols` is the safest render for any TQL; chart jetConfig for traces differs from metrics — capture from the Console `{JSON}` if you need bar/line. **TQL syntax**: attributes are PascalCase built-ins; aggregates need `as "alias"`; `group by` comes AFTER `where`; no `percentage()` function.

> **`show spans` vs `show traces` attributes are NOT interchangeable (confirmed live 2026-07-07).** A `show spans` query that selects a trace-level attribute errors — e.g. `TraceStatus` in a spans tile fails with `attribute TraceStatus ... not found ... Character 63`. Pick the built-ins for the level you query:
> - **`show spans` (span level)**: `ServiceName`, `OperationName`, `SpanDuration`, `SpanKind`, `SpanStatus`, `SpanErrorCount` + tag names bare/unquoted (`peer.service`, `http.status_code`). Filter span errors with `SpanErrorCount > 0`.
> - **`show traces` (trace level)**: `TraceId`, `OperationName`, `TraceDuration`, `TraceStatus`, `TraceErrorSpans`. Filter trace errors with `TraceStatus = 'ERROR'`.
>
> `TraceStatus` and `TraceDuration` exist ONLY on `show traces` — never in a `show spans` tile.

Working references (applied live): metric widgets → `infra/modules/dashboards/dashboards/01-operations-overview.json`, `03-route-analytics.json`; trace widgets → `02-upstream-dependencies.json`.

### Cleanup gotcha (write-once + overrideSameName)

Destroying the `..._import` resource does NOT reliably delete the imported dashboard/saved-searches — they linger ACTIVE. A re-import with `override_same_name = true` then fails `401 NotAuthenticated / RelatedResourceNotAuthorizedOrNotFound (Cannot find Resource <ocid>)` because it tries to update stale same-named resources. Fix: delete the orphans by OCID first (`oci management-dashboard dashboard delete` + `saved-search delete --force`), then re-apply.
