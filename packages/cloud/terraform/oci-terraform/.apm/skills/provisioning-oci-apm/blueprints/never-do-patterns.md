# Never Do Patterns — provisioning-oci-apm

7 prohibited patterns. Each shows ❌ wrong + ✅ correct + impact.

---

## 1. Plain-Text APM Data Key Output
**Severity**: CRITICAL — APM domain data integrity compromise

```hcl
# ❌ DON'T — exposed in CI/CD logs, terraform output, state inspect
output "apm_private_key" {
  value = data.oci_apm_data_keys.private_key.data_keys[0].value
}

# ✅ DO — store in Vault, output only the Vault secret OCID
resource "oci_vault_secret" "apm_private_key" {
  # ... (see always-do-patterns.md #4)
}
output "apm_private_key_vault_secret_id" {
  value       = oci_vault_secret.apm_private_key.id
  description = "Vault secret OCID — retrieve value via OCI Vault API from application"
}
```

---

## 2. `is_free_tier` Without `lifecycle.ignore_changes`
**Severity**: CRITICAL — full domain destruction, all child resources cascade-deleted

```hcl
# ❌ DON'T — PR that accidentally flips is_free_tier triggers destroy+create
resource "oci_apm_apm_domain" "main" {
  compartment_id = var.compartment_id
  display_name   = "prod-apm"
  is_free_tier   = false
  # No lifecycle block
}

# ✅ DO — freeze is_free_tier in lifecycle
resource "oci_apm_apm_domain" "main" {
  compartment_id = var.compartment_id
  display_name   = "prod-apm"
  is_free_tier   = false

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [is_free_tier]
  }
}
```

---

## 3. Script Parameter Secrets Hardcoded in `.tf`
**Severity**: HIGH — credentials in `.tfstate` plaintext, version control, CI/CD logs

```hcl
# ❌ DON'T
resource "oci_apm_synthetics_script" "login_flow" {
  parameters {
    param_name  = "password"
    param_value = "SuperSecret123!"  # in state as plaintext
    is_secret   = true               # only masks in OCI console — not in state
  }
}

# ✅ DO — source from sensitive variable injected by CI/CD vault pipeline
variable "login_script_password" {
  type      = string
  sensitive = true
  # Set via TF_VAR_login_script_password from CI/CD vault
}

resource "oci_apm_synthetics_script" "login_flow" {
  parameters {
    param_name  = "password"
    param_value = var.login_script_password
    is_secret   = true
  }
}
```

---

## 4. No `prevent_destroy` on Production APM Domain
**Severity**: CRITICAL — `terraform destroy` permanently deletes APM domain; no soft-delete, no recovery

```hcl
# ❌ DON'T
resource "oci_apm_apm_domain" "main" {
  compartment_id = var.compartment_id
  display_name   = "prod-apm"
  # No lifecycle.prevent_destroy
}

# ✅ DO
resource "oci_apm_apm_domain" "main" {
  compartment_id = var.compartment_id
  display_name   = "prod-apm"

  lifecycle {
    prevent_destroy = true
  }
}
```

---

## 5. Untagged APM Resources
**Severity**: HIGH — cost blindness, OCI governance policy failure, compliance gaps

```hcl
# ❌ DON'T
resource "oci_apm_synthetics_monitor" "api_check" {
  apm_domain_id              = oci_apm_apm_domain.main.id
  display_name               = "API Health Check"
  monitor_type               = "REST"
  repeat_interval_in_seconds = 300
  vantage_points { name = "OraclePublic-us-ashburn-1" }
  # No tags
}

# ✅ DO
locals {
  common_tags = {
    "managed-by"  = "terraform"
    "environment" = var.environment
    "application" = var.application_name
  }
}

resource "oci_apm_synthetics_monitor" "api_check" {
  apm_domain_id              = oci_apm_apm_domain.main.id
  display_name               = "${var.environment}-api-health-check"
  monitor_type               = "REST"
  repeat_interval_in_seconds = 300
  vantage_points { name = "OraclePublic-us-ashburn-1" }

  defined_tags  = var.defined_tags
  freeform_tags = local.common_tags
}
```

---

## 6. Hardcoded OCID in `filter_id` for METRIC_GROUP
**Severity**: MEDIUM — breaks across environments, causes 400 at apply time

```hcl
# ❌ DON'T
resource "oci_apm_config_config" "error_metric" {
  config_type = "METRIC_GROUP"
  filter_id   = "ocid1.apmconfig.oc1..placeholder"  # broken in any other env
  metrics { name = "ErrorRate" }
}

# ✅ DO — reference the span filter resource directly
resource "oci_apm_config_config" "api_error_filter" {
  config_type  = "SPAN_FILTER"
  filter_text  = "kind='SERVER' and http.status_code >= 500"
}

resource "oci_apm_config_config" "error_metric" {
  config_type = "METRIC_GROUP"
  filter_id   = oci_apm_config_config.api_error_filter.id  # real reference
  metrics { name = "ErrorRate" }
}
```

---

## 7. `count = 0` to Disable Monitors (Destroys History)
**Severity**: MEDIUM — monitor history and availability calculations permanently lost

```hcl
# ❌ DON'T — count=0 destroys the monitor resource and its run history
resource "oci_apm_synthetics_monitor" "api_check" {
  count         = var.enable_monitoring ? 1 : 0
  apm_domain_id = oci_apm_apm_domain.main.id
  # ...
}

# ✅ DO — use status to pause without data loss
resource "oci_apm_synthetics_monitor" "api_check" {
  apm_domain_id              = oci_apm_apm_domain.main.id
  display_name               = "API Health Check"
  monitor_type               = "REST"
  repeat_interval_in_seconds = 300
  status                     = var.monitoring_enabled ? "ENABLED" : "DISABLED"
  # ...
}
```
