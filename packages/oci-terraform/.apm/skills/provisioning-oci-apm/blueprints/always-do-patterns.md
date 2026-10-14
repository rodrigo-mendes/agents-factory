# Always Do Patterns — provisioning-oci-apm

Full code examples for all 9 mandatory patterns. Each pattern is **low-to-medium freedom** (exact HCL required for security and immutability constraints).

---

## 1. OCI Backend + Version Lock

```hcl
terraform {
  required_version = ">= 1.9"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 8.0"
    }
  }

  backend "oci" {
    namespace = var.object_storage_namespace
    bucket    = "tf-state-apm-prod"
    key       = "apm/terraform.tfstate"
    region    = "us-phoenix-1"
  }
}
```
> OCI Object Storage backend has built-in conditional PUT locking — no DynamoDB table needed.

---

## 2. Provider Auth — No Credentials in Code

```hcl
# Production: Instance Principal
provider "oci" {
  region = var.region
  auth   = "InstancePrincipal"  # or "ResourcePrincipal" in Functions/OKE
}

# CI/CD: API Key from env vars only
provider "oci" {
  region       = var.region
  tenancy_ocid = var.tenancy_ocid   # TF_VAR_tenancy_ocid
  user_ocid    = var.user_ocid       # TF_VAR_user_ocid
  fingerprint  = var.fingerprint     # TF_VAR_fingerprint
  private_key  = var.private_key_pem # TF_VAR_private_key_pem (sensitive)
}
```

---

## 3. APM Domain with Lifecycle Guards

```hcl
resource "oci_apm_apm_domain" "main" {
  compartment_id = var.compartment_id
  display_name   = "${var.environment}-apm-domain"
  is_free_tier   = var.is_free_tier  # Explicitly set — immutable after creation

  defined_tags = merge(var.defined_tags, {
    "${var.tag_namespace}.Environment" = var.environment
    "${var.tag_namespace}.ManagedBy"   = "terraform"
  })
  freeform_tags = { "environment" = var.environment, "managed-by" = "terraform" }

  lifecycle {
    prevent_destroy = true                # No soft-delete — permanent loss otherwise
    ignore_changes  = [is_free_tier]      # Immutable; prevent accidental recreation
  }
}

variable "is_free_tier" {
  type    = bool
  default = false

  validation {
    condition     = var.environment != "production" || !var.is_free_tier
    error_message = "Production environments must not use free tier APM domains."
  }
}
```

---

## 4. APM Data Keys → OCI Vault (never plain output)

```hcl
data "oci_apm_data_keys" "private_key" {
  apm_domain_id = oci_apm_apm_domain.main.id
  data_key_type = "PRIVATE"
}

resource "oci_vault_secret" "apm_private_key" {
  compartment_id = var.compartment_id
  vault_id       = var.vault_id
  key_id         = var.kms_key_id
  secret_name    = "${var.environment}-apm-private-data-key"

  secret_content {
    content_type = "BASE64"
    content      = base64encode(data.oci_apm_data_keys.private_key.data_keys[0].value)
  }

  freeform_tags = { "managed-by" = "terraform" }
}

# Safe outputs — OCIDs and endpoints, NOT key values
output "apm_domain_id"              { value = oci_apm_apm_domain.main.id }
output "apm_upload_endpoint"        { value = oci_apm_apm_domain.main.data_upload_endpoint }
output "apm_private_key_secret_id"  { value = oci_vault_secret.apm_private_key.id }
```

---

## 5. SPAN_FILTER Before METRIC_GROUP (Dependency Order)

```hcl
resource "oci_apm_config_config" "api_errors_filter" {
  apm_domain_id = oci_apm_apm_domain.main.id
  config_type   = "SPAN_FILTER"
  display_name  = "API Error Spans"
  filter_text   = "kind='SERVER' and http.status_code >= 500"
  freeform_tags = { "managed-by" = "terraform" }
}

resource "oci_apm_config_config" "api_error_rate_metric" {
  apm_domain_id = oci_apm_apm_domain.main.id
  config_type   = "METRIC_GROUP"
  display_name  = "API Error Rate"
  filter_id     = oci_apm_config_config.api_errors_filter.id  # implicit depends_on
  namespace     = "custom_apm_metrics"

  metrics {
    name = "ErrorRate"
    unit = "count"
  }
  freeform_tags = { "managed-by" = "terraform" }
}
```

---

## 6. Apdex Rules with Explicit Priority

```hcl
resource "oci_apm_config_config" "checkout_apdex" {
  apm_domain_id = oci_apm_apm_domain.main.id
  config_type   = "APDEX"
  display_name  = "Checkout Service SLA"

  rules {
    display_name             = "Checkout - Critical Path"
    filter_text              = "kind='SERVER' and serviceName='checkout-service'"
    is_enabled               = true
    is_apply_to_error_spans  = false
    priority                 = 1
    satisfied_response_time  = 1000   # ≤ 1s = satisfied
    tolerating_response_time = 4000   # ≤ 4s = tolerating; > 4s = frustrated
  }

  rules {
    display_name             = "All Other Services (catch-all)"
    filter_text              = "kind='SERVER'"
    is_enabled               = true
    is_apply_to_error_spans  = false
    priority                 = 100
    satisfied_response_time  = 2000
    tolerating_response_time = 8000
  }

  freeform_tags = { "managed-by" = "terraform" }
}
```

---

## 7. Synthetic Monitor with Interval/Timeout Validation

```hcl
variable "rest_repeat_interval_seconds" {
  type    = number
  default = 300
  validation {
    condition     = var.rest_repeat_interval_seconds >= 60
    error_message = "REST monitor repeat_interval_in_seconds must be >= 60."
  }
}

resource "oci_apm_synthetics_monitor" "api_health" {
  apm_domain_id              = oci_apm_apm_domain.main.id
  display_name               = "${var.environment}-api-health"
  monitor_type               = "REST"
  repeat_interval_in_seconds = var.rest_repeat_interval_seconds
  timeout_in_seconds         = 120   # <= 50% of interval (no retry)
  status                     = "ENABLED"
  is_failure_retried         = false

  vantage_points { name = "OraclePublic-us-ashburn-1" }

  configuration {
    config_type                       = "REST_CONFIG"
    request_method                    = "GET"
    is_certificate_validation_enabled = true
    verify_response_codes             = ["2xx"]
  }

  target        = var.api_health_endpoint
  defined_tags  = var.defined_tags
  freeform_tags = { "managed-by" = "terraform", "environment" = var.environment }
}
```

---

## 8. IAM Policy per APM Sub-Service (Least Privilege)

```hcl
resource "oci_identity_policy" "apm_terraform_provisioner" {
  compartment_id = var.compartment_id
  name           = "${var.environment}-apm-terraform-provisioner"
  description    = "Terraform CI/CD — APM management"

  statements = [
    "Allow group ${var.terraform_group_name} to manage apm-domains in compartment ${var.compartment_name}",
    "Allow group ${var.terraform_group_name} to manage apm-synthetics-monitor in compartment ${var.compartment_name}",
    "Allow group ${var.terraform_group_name} to manage apm-config in compartment ${var.compartment_name}",
    "Allow group ${var.terraform_group_name} to read secret-bundles in compartment ${var.compartment_name}",
    "Allow group ${var.terraform_group_name} to manage vaults in compartment ${var.compartment_name}",
  ]
}

resource "oci_identity_policy" "apm_app_runtime" {
  compartment_id = var.compartment_id
  name           = "${var.environment}-apm-app-runtime"
  description    = "App instance principal — APM read-only data key access"

  statements = [
    "Allow dynamic-group ${var.app_dynamic_group_name} to read apm-domains in compartment ${var.compartment_name}",
    "Allow dynamic-group ${var.app_dynamic_group_name} to read secret-bundles in compartment ${var.compartment_name} where target.secret.name = '${var.environment}-apm-private-data-key'",
  ]
}
```

---

## 9. Variable Validation for OCIDs and Enums

```hcl
variable "compartment_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_id))
    error_message = "compartment_id must start with 'ocid1.compartment.'."
  }
}

variable "apm_domain_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.apmdomain\\.", var.apm_domain_id))
    error_message = "apm_domain_id must start with 'ocid1.apmdomain.'."
  }
}

variable "monitor_type" {
  type = string
  validation {
    condition = contains([
      "BROWSER", "REST", "SCRIPTED_BROWSER", "SCRIPTED_REST",
      "NETWORK", "DNS_SERVER", "DNS_TRACE", "DNSSEC", "FTP", "SQL"
    ], var.monitor_type)
    error_message = "monitor_type must be one of the valid OCI APM Synthetics types."
  }
}

variable "script_content_type" {
  type    = string
  default = "JS"
  validation {
    condition     = contains(["SIDE", "JS", "PLAYWRIGHT_TS"], var.script_content_type)
    error_message = "script_content_type must be SIDE, JS, or PLAYWRIGHT_TS."
  }
}
```
