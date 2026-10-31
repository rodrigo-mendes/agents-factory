# Worked Examples — provisioning-oci-apm

Source: `workspace/poc-oci-serverless/infra/modules/apm/` and `infra/modules/observability/`

---

## Worked example (from the reference PoC)

### APM Domain — `infra/modules/apm/main.tf`

The PoC provisions a free-tier APM domain and exposes the private data key for function
instrumentation. The `is_free_tier` attribute has a known drift issue (OCI normalizes it
server-side), so it is ignored in lifecycle.

```hcl
# from infra/modules/apm/main.tf

resource "oci_apm_apm_domain" "this" {
  compartment_id = var.compartment_ocid
  display_name   = "apm-${var.project_name}-${var.environment}"
  description    = "APM Domain for serverless functions (${var.project_name}-${var.environment})"
  is_free_tier   = true

  freeform_tags = var.tags

  lifecycle {
    ignore_changes = [is_free_tier]   # OCI normalizes this attribute server-side
  }
}

data "oci_apm_data_keys" "private" {
  apm_domain_id = oci_apm_apm_domain.this.id
  data_key_type = "PRIVATE"
}
```

### OCI Logging + Monitoring Alarms — `infra/modules/observability/main.tf` (excerpt)

```hcl
# from infra/modules/observability/main.tf

resource "oci_logging_log_group" "this" {
  count          = var.enable_logging ? 1 : 0
  compartment_id = var.compartment_ocid
  display_name   = "lg-${var.project_name}-${var.environment}"
  description    = "Log group for serverless infrastructure"
  freeform_tags  = var.tags
}

# Service log for each Functions Application (for_each over app map)
resource "oci_logging_log" "functions_invoke" {
  for_each     = var.enable_logging ? local.apps : {}
  display_name = "log-functions-invoke-${each.key}-${var.environment}"
  log_group_id = oci_logging_log_group.this[0].id
  log_type     = "SERVICE"
  is_enabled   = true
  configuration {
    compartment_id = var.compartment_ocid
    source {
      category    = "invoke"
      resource    = each.value   # application_id
      service     = "functions"
      source_type = "OCISERVICE"
    }
  }
  freeform_tags = var.tags
}

# Alarm example: Function error count
resource "oci_monitoring_alarm" "function_errors" {
  for_each              = var.enable_monitoring_alarms ? local.apps : {}
  compartment_id        = var.compartment_ocid
  display_name          = "alarm-fn-errors-${each.key}-${var.project_name}-${var.environment}"
  is_enabled            = true
  metric_compartment_id = var.compartment_ocid
  namespace             = "oci_faas"
  severity              = "CRITICAL"
  query                 = "FunctionErrorCount[5m]{applicationId = \"${each.value}\"}.sum() > 0"
  body                  = "Function invocation errors in application ${each.key}"
  message_format        = "ONS_OPTIMIZED"
  pending_duration      = "PT5M"
  repeat_notification_duration = "PT15M"
  is_notifications_per_metric_dimension_enabled = false
  destinations = [oci_ons_notification_topic.alerts[0].id]
  freeform_tags = var.tags
}
```

**Key patterns from this example:**
- APM domain uses `ignore_changes = [is_free_tier]` — mandatory to prevent perpetual drift.
- Logging uses `for_each` over a `local.apps` map (application_id values) so new applications add logs without duplicating the log group.
- Alarm queries use `{applicationId = \"${each.value}\"}` to scope per-application — avoids noisy cross-application alerts.
- `ONS_OPTIMIZED` message format is required for alarm-to-email delivery via ONS subscriptions.
