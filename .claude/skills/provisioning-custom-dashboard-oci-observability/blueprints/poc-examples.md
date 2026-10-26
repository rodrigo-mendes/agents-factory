# Worked Examples — provisioning-custom-dashboard-oci-observability

Source: `workspace/poc-oci-serverless/infra/modules/dashboards/`

---

## Worked example (from the reference PoC)

### OCI Management Dashboard bulk import — `infra/modules/dashboards/main.tf`

The PoC provisions 4 custom dashboards via `oci_management_dashboard_management_dashboards_import`.
OCIDs and namespace values are injected through `templatefile` — never hardcoded in the JSON
payload. The resource has no Update/Delete lifecycle, so changes to the JSON are not detected by
`terraform plan` after initial creation.

```hcl
# from infra/modules/dashboards/main.tf

locals {
  # All dynamic values injected via templatefile — zero hardcoded OCIDs in JSON
  template_vars = {
    compartment_ocid  = var.compartment_ocid
    application_id    = var.application_id
    apm_domain_id     = var.apm_domain_id
    api_deployment_id = var.api_deployment_id
    metric_namespace  = var.metric_namespace
    environment       = var.environment
    # Event pub/sub dashboards
    producer_function_id    = var.producer_function_id
    notify_function_id      = var.notify_function_id
    audit_function_id       = var.audit_function_id
    events_metric_namespace = var.events_metric_namespace
  }

  dashboards = {
    "operations-overview"   = { file = "01-operations-overview.json",   display_name = "REST Proxy — Operations Overview (${var.environment})" }
    "upstream-dependencies" = { file = "02-upstream-dependencies.json", display_name = "REST Proxy — Upstream Dependencies (${var.environment})" }
    "route-analytics"       = { file = "03-route-analytics.json",       display_name = "REST Proxy — Route Analytics (${var.environment})" }
    "transaction-path"      = { file = "04-transaction-path.json",      display_name = "Events — Transaction Path (${var.environment})" }
  }
}

resource "oci_management_dashboard_management_dashboards_import" "this" {
  for_each = local.dashboards

  import_details = templatefile(
    "${path.module}/dashboards/${each.value.file}",
    local.template_vars
  )

  override_dashboard_compartment_ocid    = var.compartment_ocid
  override_saved_search_compartment_ocid = var.compartment_ocid
  override_same_name                     = true   # Forces overwrite if same display_name exists

  lifecycle {
    ignore_changes = [import_details]   # Resource has no read; drift is invisible after creation
  }
}
```

**Key patterns from this example:**
- `templatefile(...)` replaces every OCID/namespace placeholder in the dashboard JSON — never hardcode identifiers in the JSON files.
- `override_same_name = true` ensures re-running `terraform apply` after a JSON change overwrites the existing dashboard instead of failing with a duplicate-name error.
- `ignore_changes = [import_details]` is required because the resource has no read API — Terraform cannot detect drift, so any post-creation change to the JSON must be applied via `terraform taint` or `terraform apply -replace`.
- `for_each` over a stable map (string keys) ensures that adding a new dashboard does not affect existing ones.
- `override_*_compartment_ocid` fields correct the compartment when importing dashboards originally exported from a different compartment.
