# 🚫 Never Do Patterns — provisioning-oci-observability

Anti-patterns with correct alternatives for all 7 forbidden patterns. See [SKILL.md](../SKILL.md) for summaries.

---

## 1. APM Data Key Hardcoded in HCL

**Impact**: CRITICAL — Trace injection, APM domain abuse, application topology exposure

```hcl
# ❌ NEVER DO
resource "oci_functions_function" "app" {
  # ...
  environment = {
    APM_PRIVATE_DATA_KEY = "DataKey_ABCDEFGHIJKLMNOP1234567890"  # credential in plaintext
  }
}
```

```hcl
# ✅ DO — Store key in Vault; reference by OCID
resource "oci_vault_secret" "apm_private_key" {
  compartment_id = var.compartment_ocid
  vault_id       = var.vault_ocid
  key_id         = var.kms_key_ocid
  secret_name    = "apm-${var.environment}-private-data-key"

  secret_content {
    content_type = "BASE64"
    content      = base64encode(data.oci_apm_data_keys.private_key.data_keys[0].value)
  }

  lifecycle {
    ignore_changes = [secret_content]  # Prevent rotation override
  }
}

# Application receives the secret OCID, retrieves value at runtime
locals {
  function_env = {
    APM_DATA_KEY_SECRET_OCID = oci_vault_secret.apm_private_key.id
    APM_ENDPOINT             = oci_apm_apm_domain.main.data_upload_endpoint
  }
}
```

---

## 2. Dashboard JSON Inline in `import_details` Variable

**Impact**: HIGH — Unreviewed dashboard changes, no audit trail in version control

```hcl
# ❌ NEVER DO
resource "oci_management_dashboard_management_dashboards_import" "bad" {
  import_details = var.some_inline_json  # complex JSON blob in tfvars — unreviewed in PRs
}
```

```hcl
# ✅ DO — tracked JSON file in source control
resource "oci_management_dashboard_management_dashboards_import" "good" {
  import_details_file = "${path.module}/dashboards/apm-observability.json"
  # dashboards/apm-observability.json is committed to git and diff-visible in PRs
}
# Validate JSON pre-commit: jq . dashboards/apm-observability.json
```

---

## 3. Log Resource Without Explicit `retention_duration`

**Impact**: HIGH — Silent compliance failure, unexpected log deletion

```hcl
# ❌ NEVER DO
resource "oci_logging_log" "bad" {
  display_name = "app-log"
  log_group_id = oci_logging_log_group.main.id
  log_type     = "CUSTOM"
  # No retention_duration — silently defaults to 30 days
  # May violate 90-day PCI DSS or 180-day SOC2 audit requirements
}
```

```hcl
# ✅ DO — always set explicitly with validated variable
variable "log_retention_days" {
  type    = number
  default = 30
  validation {
    condition     = contains([30, 60, 90, 180], var.log_retention_days)
    error_message = "retention_duration must be 30, 60, 90, or 180"
  }
}

resource "oci_logging_log" "good" {
  display_name       = "app-log"
  log_group_id       = oci_logging_log_group.main.id
  log_type           = "CUSTOM"
  retention_duration = var.log_retention_days  # explicit, validated, compliance-aligned
}
```

---

## 4. Monitoring Alarm Without `pending_duration`

**Impact**: MEDIUM — Alert fatigue, on-call burnout, missed real incidents

```hcl
# ❌ NEVER DO
resource "oci_monitoring_alarm" "bad" {
  namespace        = "oci_computeagent"
  query            = "CpuUtilization[1m].mean() > 80"  # fires on every 1-minute spike
  severity         = "WARNING"
  destinations     = [oci_ons_notification_topic.alerts.id]
  # No pending_duration — alerts fire immediately, causing noise flood
}
```

```hcl
# ✅ DO — sustained condition before firing; throttle repeats
resource "oci_monitoring_alarm" "good" {
  namespace                    = "oci_computeagent"
  query                        = "CpuUtilization[5m].mean() > 80"  # 5m window, not 1m
  severity                     = "WARNING"
  destinations                 = [oci_ons_notification_topic.alerts.id]
  pending_duration             = "PT5M"   # condition must persist 5 minutes
  repeat_notification_duration = "PT2H"  # suppress repeat notifications for 2h
}
```

---

## 5. API Key Authentication in CI/CD Pipelines

**Impact**: CRITICAL — OCI API keys never expire; leaked key = full tenancy compromise

```hcl
# ❌ NEVER DO
provider "oci" {
  tenancy_ocid     = "ocid1.tenancy.oc1..aaaa..."
  user_ocid        = "ocid1.user.oc1..aaaa..."
  fingerprint      = "aa:bb:cc:dd:..."
  private_key      = file("~/.oci/oci_api_key.pem")  # key content embedded — never do this
}
```

```hcl
# ✅ DO — credential-free authentication
# On OCI compute (DevOps build runner, OKE pod, Functions):
provider "oci" {
  region = var.region
  auth   = "InstancePrincipal"
}

# In GitHub Actions with OCI Workload Identity OIDC plugin:
provider "oci" {
  region = var.region
  auth   = "SecurityToken"
}

# Dev workstation only (never in CI/CD):
provider "oci" {
  region           = var.region
  private_key_path = var.private_key_path  # path to file — never inline content
}
```

---

## 6. APM Domain Without IAM Policy for Data Upload

**Impact**: HIGH — APM instrumentation silently fails; HTTP 403 on data upload, no traces

```hcl
# ❌ NEVER DO
resource "oci_apm_apm_domain" "main" {
  compartment_id = var.compartment_ocid
  display_name   = "apm-prod"
  # No IAM policy → applications receive 403 on every trace upload
  # No observable error in Terraform — fails silently at runtime
}
```

```hcl
# ✅ DO — IAM dynamic group + policy for application workloads
resource "oci_identity_dynamic_group" "app_workloads" {
  compartment_id = var.tenancy_ocid
  name           = "${var.environment}-app-workloads"
  description    = "Dynamic group for compute resources running APM-instrumented apps"
  matching_rule  = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"
}

resource "oci_identity_policy" "apm_data_upload" {
  compartment_id = var.tenancy_ocid
  name           = "${var.environment}-apm-data-upload-policy"
  description    = "Allows application workloads to write traces to APM domain"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.app_workloads.name} to use apm-domains in compartment id ${var.compartment_ocid}",
  ]
}
```

---

## 7. Hardcoded OCIDs in Saved Search `data_config` JSON

**Impact**: MEDIUM — Dashboard portability failure across environments, manual OCID updates required

```hcl
# ❌ NEVER DO
resource "oci_management_dashboard_management_saved_search" "bad" {
  # ...
  data_config = jsonencode([{
    name = "traces"
    type = "apmDataSource"
    parameters = {
      apmDomainId = "ocid1.apmdomain.oc1..aaaaXXXXXXXXXXXX"  # hardcoded — breaks in other envs
    }
  }])
}
```

```hcl
# ✅ DO — reference Terraform resource attribute
resource "oci_management_dashboard_management_saved_search" "good" {
  # ...
  data_config = jsonencode([{
    name = "traces"
    type = "apmDataSource"
    parameters = {
      apmDomainId = oci_apm_apm_domain.main.id  # resolved at apply time per environment
    }
  }])
}
```

---

## Import-envelope anti-patterns (confirmed live 2026-07-07)

These all pass `terraform plan`/`validate` and fail only at apply with HTTP 400 — validation is server-side.

### ❌ Dashboard object without both `tiles[]` and `savedSearches[]`
```json
// WRONG — savedSearches nested but no tiles → 400 "field: Tiles ... not-nil list"
{ "dashboards": [ { "displayName": "...", "savedSearches": [ /* widgets */ ] } ] }
// WRONG — moved savedSearches to top level → 400 "field: SavedSearches ... not-nil list"
{ "dashboards": [ { "tiles": [ ... ] } ], "savedSearches": [ ... ] }
```
```json
// RIGHT — BOTH nested inside each dashboard
{ "dashboards": [ { "tiles": [ { "savedSearchId": "...", "row":0,"column":0,"height":4,"width":6, ... } ],
                    "savedSearches": [ { "id": "...", ... } ] } ] }
```

### ❌ Empty `featuresConfig` / invalid `providerId`
```json
"featuresConfig": {},                 // 400 "must contain property crossService" then "...shared"
"providerId": "oci-monitoring"        // 400 "Invalid providerId"
```
```json
"featuresConfig": { "crossService": { "shared": false } },
"providerId": "management-dashboard"  // valid: opsi|APM|log-analytics|management-dashboard|management-agent|dbm|appmgmt
```

### ❌ `resourceId` filter in `oci_faas` widget queries (silent empty widget)
```json
// WRONG — resourceId is the FUNCTION (fnfunc) OCID; filtering by the App OCID matches nothing
"query": "FunctionInvocationCount[1m]{resourceId=\"${application_id}\"}.sum()"
```
```json
// RIGHT — applicationId is the Application (fnapp) OCID; functionId does NOT exist as a dimension
"query": "FunctionInvocationCount[1m]{applicationId=\"${application_id}\"}.sum()"
```

### ❌ Relying on the functions dynamic-group to import dashboards
The import runs as the identity executing Terraform (user `SecurityToken` / Instance Principal), NOT the workload dynamic group. Grant the **deployer's** IAM group `manage management-dashboards` + `manage management-saved-searches` in the compartment — otherwise apply fails authz.
