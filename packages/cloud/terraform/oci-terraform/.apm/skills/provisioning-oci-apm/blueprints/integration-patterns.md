# Integration Patterns — provisioning-oci-apm

Full integration HCL for all 6 integration partners.

---

## Terraform ↔ OCI IAM

**Pattern**: Group + policy per APM sub-service; never `manage all-resources`.

```hcl
resource "oci_identity_policy" "apm_full" {
  compartment_id = var.compartment_id
  name           = "apm-terraform-full-${var.environment}"
  description    = "Full APM management for Terraform CI/CD"

  statements = [
    "Allow group id ${var.terraform_group_id} to manage apm-domains in compartment id ${var.compartment_id}",
    "Allow group id ${var.terraform_group_id} to manage apm-synthetics-monitor in compartment id ${var.compartment_id}",
    "Allow group id ${var.terraform_group_id} to manage apm-config in compartment id ${var.compartment_id}",
  ]
}
```

**Common issue**: IAM policy propagation delay ~15–30s; if Terraform apply fails immediately after policy creation, add a `time_sleep` resource or retry.

**Source**: [OCI IAM Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_policy)

---

## Terraform ↔ OCI Vault

**Pattern**: Write APM private data key to Vault; use `ignore_changes = [secret_content]` to prevent Terraform from overwriting out-of-band rotations.

```hcl
resource "oci_vault_secret" "apm_data_key" {
  compartment_id = var.compartment_id
  vault_id       = var.vault_id
  key_id         = var.kms_key_id
  secret_name    = "${var.environment}/apm/private-data-key"

  secret_content {
    content_type = "BASE64"
    content      = base64encode(data.oci_apm_data_keys.private.data_keys[0].value)
    stage        = "CURRENT"
  }

  freeform_tags = { "managed-by" = "terraform" }

  lifecycle {
    ignore_changes = [secret_content]  # Prevent rotation conflicts
  }
}
```

**Key rotation** (outside Terraform):
```bash
oci apm-control-plane apm-domain generate-data-keys \
  --apm-domain-id <domain_ocid> \
  --generate-data-keys-details '[{"name":"auto_x","dataKeyType":"PRIVATE"}]'

oci vault secret update-base64 \
  --secret-id <vault_secret_ocid> \
  --secret-content-content "$(echo -n '<new_key>' | base64)"
```

**Source**: [oci_vault_secret](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/vault_secret)

---

## Terraform ↔ OCI Monitoring

**Pattern**: APM METRIC_GROUP publishes custom metrics to a namespace; `oci_monitoring_alarm` queries that namespace. Metric data appears 2–5 min after first span ingestion.

```hcl
resource "oci_monitoring_alarm" "apm_error_rate_high" {
  compartment_id        = var.compartment_id
  display_name          = "${var.environment}-apm-error-rate-high"
  is_enabled            = true
  metric_compartment_id = var.compartment_id
  namespace             = "custom_apm_metrics"   # Must match METRIC_GROUP namespace
  query                 = "HttpErrorRate[5m].mean() > 5"
  severity              = "CRITICAL"
  pending_duration      = "PT3M"
  destinations          = [var.ons_topic_id]
  body                  = "APM error rate exceeded 5% in ${var.environment}."

  depends_on = [oci_apm_config_config.error_rate_metric]
}
```

**Source**: [oci_monitoring_alarm](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/monitoring_alarm)

---

## Terraform ↔ OCI Notifications (ONS)

**Pattern**: Topic + subscription for alert delivery.

```hcl
resource "oci_ons_notification_topic" "apm_alerts" {
  compartment_id = var.compartment_id
  name           = "${var.environment}-apm-alerts"
  freeform_tags  = { "managed-by" = "terraform" }
}

resource "oci_ons_subscription" "apm_email_alert" {
  compartment_id = var.compartment_id
  topic_id       = oci_ons_notification_topic.apm_alerts.id
  endpoint       = var.alert_email
  protocol       = "EMAIL"
  freeform_tags  = { "managed-by" = "terraform" }
}
```

**Known gap**: APM Synthetics monitors do not have a direct OCI Notifications binding via Terraform as of oracle/oci v8.x. Use an OCI Monitoring alarm on the Synthetics availability metric namespace as workaround. Email subscriptions remain in `PENDING` state until manually confirmed from inbox.

**Source**: [oci_ons_notification_topic](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/ons_notification_topic)

---

## Terraform ↔ OCI Streaming (for Dedicated Vantage Points)

**Pattern**: DVP requires an OCI Streaming stream for control-plane communication. Pre-provision RM stack before creating DVP.

```hcl
resource "oci_streaming_stream" "dvp_stream" {
  compartment_id     = var.compartment_id
  name               = "${var.environment}-dvp-stream"
  partitions         = 1
  retention_in_hours = 24
  freeform_tags      = { "managed-by" = "terraform" }
}

resource "oci_apm_synthetics_dedicated_vantage_point" "internal_dvp" {
  apm_domain_id = oci_apm_apm_domain.main.id
  display_name  = "${var.environment}-internal-dvp"   # IMMUTABLE — changing forces recreation
  region        = var.region
  status        = "ENABLED"

  dvp_stack_details {
    dvp_stack_id   = var.resource_manager_stack_id   # Pre-created RM stack
    dvp_stack_type = "ORACLE_RM_STACK"
    dvp_stream_id  = oci_streaming_stream.dvp_stream.id
    dvp_version    = "1.0"
  }

  freeform_tags = { "managed-by" = "terraform" }
  depends_on    = [oci_streaming_stream.dvp_stream]
}
```

**Source**: [oci_apm_synthetics_dedicated_vantage_point](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apm_synthetics_dedicated_vantage_point)

---

## Terraform ↔ OCI Logging (Service Connector Hub)

**Pattern**: Route APM metric data to OCI Logging Analytics for long-term retention and SIEM integration.

```hcl
resource "oci_sch_service_connector" "apm_to_logging" {
  compartment_id = var.compartment_id
  display_name   = "${var.environment}-apm-metrics-to-logging"
  state          = "ACTIVE"

  source {
    kind = "monitoring"
    monitoring_sources {
      compartment_id = var.compartment_id
      namespace_details {
        kind = "selected"
        namespaces {
          namespace = "custom_apm_metrics"
          metrics { kind = "all" }
        }
      }
    }
  }

  target {
    kind                  = "loggingAnalytics"
    log_group_id          = var.log_group_id
    log_source_identifier = "APMMetrics"
  }

  freeform_tags = { "managed-by" = "terraform" }
}
```

**Source**: [oci_sch_service_connector](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/sch_service_connector)

---

## Import Commands (Existing Resources)

```bash
terraform import oci_apm_apm_domain.main <apm_domain_ocid>

terraform import oci_apm_synthetics_monitor.api_health \
  "monitors/<monitor_ocid>/apmDomainId/<domain_ocid>"

terraform import oci_apm_config_config.api_errors_filter \
  "configs/<config_ocid>/apmDomainId/<domain_ocid>"

terraform import oci_apm_synthetics_script.login_flow \
  "scripts/<script_ocid>/apmDomainId/<domain_ocid>"
```
