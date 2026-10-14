# Never Do Patterns — OCI Logging (Terraform oracle/oci ~> 8.15)

## Anti-Pattern 1: Omitting `retention_duration` (Severity: CRITICAL)

```hcl
# ❌ DON'T — silently defaults to 30 days
resource "oci_logging_log" "app_log" {
  display_name = "app-logs"
  log_group_id = oci_logging_log_group.app.id
  log_type     = "CUSTOM"
  is_enabled   = true
  # retention_duration not set
}
```

```hcl
# ✅ DO — always set explicitly
resource "oci_logging_log" "app_log" {
  display_name       = "app-logs"
  log_group_id       = oci_logging_log_group.app.id
  log_type           = "CUSTOM"
  is_enabled         = true
  retention_duration = var.log_retention_days  # validated: 30|60|90|120|150|180
}
```

**Impact**: `data loss` — data permanently deleted at 30 days; cannot be recovered; extending retention after expiry has no retroactive effect.

---

## Anti-Pattern 2: Hardcoded Credentials in Provider Block (Severity: CRITICAL)

```hcl
# ❌ DON'T — inline OCIDs and key path
provider "oci" {
  tenancy_ocid     = "ocid1.tenancy.oc1..aaaaaaaaXXXXXXXXXXXX"
  user_ocid        = "ocid1.user.oc1..aaaaaaaaXXXXXXXXXXXX"
  fingerprint      = "12:34:56:78:9a:bc:de:f0:12:34:56:78:9a:bc:de:f0"
  private_key_path = "/home/user/.oci/oci_api_key.pem"
  region           = "us-ashburn-1"
}
```

```hcl
# ✅ DO — Instance Principal (production)
provider "oci" {
  auth   = "InstancePrincipal"
  region = var.region
}

# ✅ DO — API Key via config file (local dev / CI)
provider "oci" {
  auth             = "ApiKey"
  config_file_path = "~/.oci/config"
  profile          = var.oci_profile
  region           = var.region
}
```

**Impact**: `security breach` — audit identity exposed in code; private key path breaks in CI/CD; static references in version control history.

---

## Anti-Pattern 3: `is_enabled = false` Without Explicit Variable (Severity: HIGH)

```hcl
# ❌ DON'T — hardcoded false, no visibility
resource "oci_logging_log" "app_log" {
  is_enabled         = false
  retention_duration = 90
  # ...
}
```

```hcl
# ✅ DO — gate behind a named variable
variable "logging_enabled" {
  type        = bool
  description = "Enable log collection. Set false only for maintenance windows."
  default     = true
}

resource "oci_logging_log" "app_log" {
  is_enabled         = var.logging_enabled
  retention_duration = var.log_retention_days
  # ...
}
```

**Impact**: `unmanaged drift` — log ingestion stops silently; no alarm; monitoring gap is invisible until you investigate a missing log query.

---

## Anti-Pattern 4: Mixing Compliance and Application Logs in One Log Group (Severity: HIGH)

```hcl
# ❌ DON'T — all log types in one group
resource "oci_logging_log_group" "all_logs" {
  compartment_id = var.compartment_id
  display_name   = "all-logs"
}

resource "oci_logging_log" "audit" {
  log_group_id = oci_logging_log_group.all_logs.id
  log_type     = "SERVICE"
  # OCI Audit log...
}

resource "oci_logging_log" "app" {
  log_group_id = oci_logging_log_group.all_logs.id
  log_type     = "CUSTOM"
}
```

```hcl
# ✅ DO — one log group per concern domain
resource "oci_logging_log_group" "audit_logs" { ... }  # compliance access only
resource "oci_logging_log_group" "app_logs"   { ... }  # app team access
resource "oci_logging_log_group" "infra_logs" { ... }  # infra team access
```

**Impact**: `security breach` — IAM policies must grant app team members access to audit logs; Connector Hub cannot apply differential routing or retention per log type.

---

## Anti-Pattern 5: Hardcoded Instance OCIDs in `group_association.group_list` (Severity: HIGH)

```hcl
# ❌ DON'T — hardcoded instance OCID
resource "oci_logging_unified_agent_configuration" "app" {
  group_association {
    group_list = ["ocid1.instance.oc1.iad.AAAAAAAAXXXXXXXX"]
  }
}
```

```hcl
# ✅ DO — dynamic group OCID
resource "oci_logging_unified_agent_configuration" "app" {
  group_association {
    group_list = [oci_identity_dynamic_group.log_agents.id]
  }
}
```

**Impact**: `unmanaged drift` — replaced instances (auto-scaling, blue/green) silently lose log collection; new instance OCID is not in the list until Terraform is re-applied manually.

---

## Anti-Pattern 6: No `prevent_destroy` on Production Log Groups (Severity: CRITICAL)

```hcl
# ❌ DON'T — log group deletable by terraform destroy
resource "oci_logging_log_group" "prod_logs" {
  compartment_id = var.compartment_id
  display_name   = "prod-app-logs"
  # No lifecycle block
}
```

```hcl
# ✅ DO — protect production log groups
resource "oci_logging_log_group" "prod_logs" {
  compartment_id = var.compartment_id
  display_name   = "prod-app-logs"
  freeform_tags  = local.common_tags

  lifecycle {
    prevent_destroy = true
  }
}
```

**Impact**: `data loss` — `terraform destroy` or accidental module removal permanently deletes all child Log objects and buffered log data; Connector Hub source references become invalid.

---

## Anti-Pattern 7: UMA Configuration Without IAM Policy (Severity: HIGH)

```hcl
# ❌ DON'T — UMA config created but no IAM policy
resource "oci_logging_unified_agent_configuration" "app" {
  group_association {
    group_list = [oci_identity_dynamic_group.log_agents.id]
  }
  # No oci_identity_policy resource
}
```

```hcl
# ✅ DO — always pair with IAM policy + depends_on
resource "oci_identity_policy" "log_agents" {
  compartment_id = var.compartment_id
  name           = "${var.app_name}-log-agent-policy"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.log_agents.name} to use log-content in compartment id ${var.compartment_id}",
    "Allow dynamic-group ${oci_identity_dynamic_group.log_agents.name} to read log-groups in compartment id ${var.compartment_id}"
  ]
}

resource "oci_logging_unified_agent_configuration" "app" {
  # ...
  depends_on = [oci_identity_policy.log_agents]
}
```

**Impact**: `unmanaged drift` — the UMA agent starts on instances but silently fails all log writes; no error surfaces in `terraform plan` or `terraform apply`; only discoverable by querying the log endpoint and finding zero records.
