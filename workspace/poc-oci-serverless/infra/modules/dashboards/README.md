# Module: dashboards

Provisions three custom **OCI Management Dashboards** for the `func-rr-rest-proxy`
function via `oci_management_dashboard_management_dashboards_import`. Each dashboard
JSON is a `templatefile` — OCIDs and the custom metric namespace are injected at plan
time and are **never hardcoded** in the committed JSON.

## Dashboards

| Key | File | Source | Purpose |
|-----|------|--------|---------|
| `operations-overview`   | `dashboards/01-operations-overview.json`   | `oci_faas` + `oci_apigateway` MQL | Golden signals: invocations, errors, latency p50/p95/p99, throttles, cold-starts, API GW responses/latency, response count |
| `upstream-dependencies` | `dashboards/02-upstream-dependencies.json` | APM QL (traces) | Downstream latency/errors by span & peer, trace error-rate, top-10 slowest traces, throughput & duration breakdown |
| `route-analytics`       | `dashboards/03-route-analytics.json`       | custom `${metric_namespace}` MQL | Requests/errors/duration by route, status_code, webhook 207, method/env breakdown |

## Usage

```hcl
module "dashboards" {
  source = "../../modules/dashboards"

  compartment_ocid  = var.compartment_ocid
  application_id    = module.app_rest_proxy.application_id
  apm_domain_id     = module.apm.apm_domain_id
  api_deployment_id = module.api_gateway.deployment_id
  metric_namespace  = "rest_proxy_analytics"
  environment       = var.environment
  freeform_tags     = local.tags
}
```

## Inputs

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `compartment_ocid`  | `string`      | —                       | Compartment OCID (validated `ocid1.compartment.`) |
| `application_id`    | `string`      | —                       | rest-proxy Application OCID (validated `ocid1.fnapp.`) — `resourceId` filter for `oci_faas` |
| `apm_domain_id`     | `string`      | —                       | APM Domain OCID (validated `ocid1.apmdomain.`) — `apmDomainId` for APM QL |
| `api_deployment_id` | `string`      | —                       | API Gateway Deployment OCID (validated `ocid1.apideployment.`) — `deploymentId` for `oci_apigateway` |
| `metric_namespace`  | `string`      | `"rest_proxy_analytics"`| Custom metric namespace emitted by the function |
| `environment`       | `string`      | —                       | Environment name (display names / tags) |
| `freeform_tags`     | `map(string)` | `{}`                    | Freeform tags |

## Outputs

| Name | Description |
|------|-------------|
| `dashboard_ids` | Map of dashboard key → `{ display_name, import_id }` |

## IAM Prerequisites

The identity applying this module (deployer user via `SecurityToken`, or a
dynamic group) needs:

```
Allow <subject> to manage management-dashboards in compartment <name>
Allow <subject> to manage management-saved-searches in compartment <name>
Allow <subject> to read metrics in compartment <name>
Allow <subject> to read apm-domains in compartment <name>
```

## ⚠️ Schema caveat — one-time Console export recommended

The `oci_management_dashboard_management_dashboards_import` resource consumes the
**exact** JSON envelope that the OCI Console produces on export. The JSON templates
here follow the documented envelope shape:

```
{ "dashboards": [ { ...dashboard..., "savedSearches": [ { ...widget..., "dataConfig": [...] } ] } ] }
```

with per-widget `row`/`column`/`height`/`width` tiling and `dataConfig` carrying the
MQL / APM QL query. However, OCI does **not** publish a strict public schema for every
`uiConfig` / `dataConfig` viz field, and it validates the payload **server-side at apply**
(not at `terraform plan`). The MQL/APM QL query strings are also validated only at query time.

**Recommended lock-in step:** after the first successful `apply`, export each dashboard
from the OCI Console (Observability → Management Dashboards → Export), and replace the
committed JSON with the exported envelope (re-parameterizing OCIDs/namespace back into
`${...}` template vars). This guarantees the `uiConfig`/`dataConfig` fields match the
current Console schema exactly. Until then, treat the widget viz config as best-effort.

## Lifecycle note

`oci_management_dashboard_management_dashboards_import` has **no Update/Delete lifecycle**
— it is write-once. Changes to the JSON are not detected by `terraform plan`
(`ignore_changes = [import_details]` is set to make this explicit). `override_same_name = true`
lets a re-run overwrite a same-named dashboard. To remove a dashboard, delete it in the
Console (or via API) and remove the map entry.
