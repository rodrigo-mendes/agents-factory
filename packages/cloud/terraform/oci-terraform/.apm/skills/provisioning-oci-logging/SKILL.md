---
name: provisioning-oci-logging
description: "Provisions OCI Logging resources (Log Groups, Log objects, Unified Monitoring Agent configurations) using Terraform oracle/oci ~> 8.15 (Terraform >= 1.9). Use when writing Terraform HCL for OCI log group creation, service/custom log configuration, UMA log collection from compute/OKE, log retention policies, or log archival pipelines on Oracle Cloud Infrastructure."
---

## Version Context

**Technology**: Terraform OCI Provider (`oracle/oci`)
**Target version**: `~> 8.15` (8.15.0 — released 2026-05-20)
**Terraform version**: `>= 1.9`
**OCI Logging API**: `v20200531` (stable)
**Support status**: Active

**Important changes in 8.x**:
- `CUSTOM_PLUGIN` source type added — arbitrary Fluentd plugin configuration for non-built-in sources
- `OPENMETRICS` parser type added — scrape Prometheus endpoints and emit to OCI Monitoring via UMA
- `MONITORING` configuration_type supported — turns UMA into a Kubernetes metric scraper for OCI Monitoring
- `group_list` in `group_association` now accepts dynamic group OCIDs directly (string-interpolated compartment conditions removed)

**Deprecated**: None in 8.x.

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform OCI Provider `~> 8.15` / `v20200531` Logging API.
Reject patterns from provider `7.x` or earlier. `group_list` values must be dynamic group OCIDs — not hardcoded instance OCIDs or compartment match strings.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 9 mandatory patterns with Terraform HCL
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural crossroads with tradeoff matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 anti-patterns with ❌ wrong / ✅ correct examples
- **[Integration Patterns](./blueprints/integration-patterns.md)** — IAM, Connector Hub, Object Storage, OKE
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases
- **[Verification Loop](#verification-loop)** — Terraform and OCI CLI validation commands
- **[Quick Reference](#quick-reference)** — Critical limits and key values at a glance
- **[External Resources](#external-resources)** — Official OCI documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with Terraform HCL examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (all 9 required — this domain is Complex tier):
- **Terraform provider constraint `~> 8.15` + version lock** — Pin provider to `oracle/oci ~> 8.15`; declare `terraform >= 1.9`; prevents silent breaking changes from a future v9.x release.
- **Provider authentication via Instance Principal or API Key profile** — Never hardcode `tenancy_ocid`, `user_ocid`, `fingerprint`, or `private_key_path` inline; use `auth = "InstancePrincipal"` in production or `config_file_path = "~/.oci/config"` for local dev.
- **Dedicated Log Group per access control boundary** — One log group per IAM domain (app, infra, audit); mixing streams in a single group forces overly broad IAM policies and prevents selective Connector Hub routing.
- **Explicit `retention_duration` and `is_enabled = true` on every Log object** — Default retention is 30 days and data is permanently deleted; `is_enabled = false` silently stops ingestion with no alarm; both must be explicitly set at creation.
- **Variable validation for `retention_duration`** — Constrain to `[30, 60, 90, 120, 150, 180]` at plan time; invalid values cause apply-time API errors without early feedback.
- **UMA configuration with dynamic group + IAM policy trio** — Always create `oci_identity_dynamic_group` + `oci_identity_policy` + `oci_logging_unified_agent_configuration` together; UMA silently fails to write logs without the IAM policy; new instances auto-inherit via dynamic group — no Terraform re-apply required.
- **`lifecycle { prevent_destroy = true }` on production Log Groups** — Log Group deletion permanently destroys all child logs and in-flight data; `prevent_destroy` forces explicit lifecycle override before any deletion.
- **Output definitions for cross-stack OCID dependencies** — Log Group and Log OCIDs are required by Connector Hub, API Gateway, and Load Balancer resources; expose via outputs for remote state consumption.
- **Mandatory `freeform_tags` via `locals`** — OCI Logging resources have no native tag enforcement; enforce `managed_by`, `environment`, `app`, `cost_center` via `local.common_tags` applied to every resource.

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points** (ask before implementing):
- **LOGGING vs. MONITORING `configuration_type`** — `LOGGING` for log file collection; `MONITORING` for Kubernetes pod metric scraping; a single UMA config resource cannot mix both — create two separate resources if needed.
- **Per-environment Log Groups vs. shared Log Group** — Per-env groups required for regulated workloads, separate team IAM, or distinct Connector Hub routing; OCI quota is 50 log groups/compartment (soft limit).
- **State backend: local vs. OCI Object Storage vs. ORM** — ORM preferred for OCI-first teams (built-in locking, IAM, audit); OCI Object Storage HTTP backend viable but has no native state locking.
- **Parser type for UMA sources** — JSON for modern structured logs; CRI for OKE containers (`is_merge_cri_fields = true` required); GROK/MULTILINE for legacy formats; ask about log format before choosing.
- **`count` vs. `for_each` for multiple logs** — Always use `for_each` with stable map keys; `count`-index reordering causes resource recreation and permanent log data loss.

### 🚫 Never Do

For complete anti-patterns with side-by-side code, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns**:
- **Omitting `retention_duration`** — CRITICAL: silently defaults to 30 days; data is permanently deleted and unrecoverable; cannot be extended retroactively after expiry.
- **Hardcoded credentials or OCIDs in provider block** — CRITICAL: exposes audit identity and breaks CI/CD; use Instance Principal or `~/.oci/config` profile.
- **`is_enabled = false` without an explicit variable** — HIGH: silently stops log ingestion with no alarm or error; always gate behind a named boolean variable with `default = true`.
- **Mixing compliance and application logs in one Log Group** — HIGH: forces overly broad IAM policies; prevents differential retention and targeted Connector Hub routing.
- **Hardcoded instance OCIDs in `group_association.group_list`** — HIGH: replaced instances silently lose log collection; use dynamic group OCID so new instances inherit automatically.
- **No `prevent_destroy` on production Log Groups** — CRITICAL: `terraform destroy` or accidental module removal permanently deletes all log history; add `lifecycle { prevent_destroy = true }`.
- **UMA configuration without IAM policy** — HIGH: agent starts but silently fails to write logs; no Terraform-visible error at plan or apply.

---

## Integration Patterns

For complete integration code with IAM, Connector Hub, Object Storage, and OKE examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Supported integrations**:
- **OCI Logging ↔ IAM (Dynamic Groups + Policies)** — Every UMA configuration requires a dynamic group + IAM policy pair; dynamic groups always live in the tenancy compartment, not child compartments.
- **OCI Logging ↔ OCI Connector Hub** — Service Connector sources a Log Group and routes to Object Storage, Functions, or Notifications; SCH requires `request.principal.type='serviceconnector'` IAM policy or shows INACTIVE with no clear error.
- **OCI Logging ↔ OCI Object Storage** — Long-term retention beyond 180-day OCI Logging limit; pair with lifecycle policy (`INFREQUENT_ACCESS` at 30 days, `DELETE` at compliance horizon); configure Connector Hub **before** log data exceeds the OCI Logging retention window — it does not retroactively export.
- **OCI Logging ↔ OCI Compute / OKE (UMA)** — UMA is pre-installed on OCI Compute images; polls for config every 30 seconds; OKE requires `parser_type = "CRI"` with `is_merge_cri_fields = true` for `/var/log/pods/**/*.log`.

**Common problems**:
- **Problem**: Connector Hub shows INACTIVE state → **Solution**: Add IAM policy `Allow any-user to manage objects ... where request.principal.type='serviceconnector'`; SCH does not surface the IAM denial as an error.
- **Problem**: UMA agent collects no logs after instance replacement → **Solution**: Verify `group_list` uses a dynamic group OCID (not a hardcoded instance OCID); confirm the dynamic group `matching_rule` uses `instance.compartment.id`, not the compartment display name.
- **Problem**: Log data disappears unexpectedly → **Solution**: Check `retention_duration` on the Log object; if not set explicitly, it defaulted to 30 days and data aged out; cannot be recovered.

---

## Verification Loop

Run after every Terraform apply or OCI Logging configuration change:

### 1. Terraform Validation
```bash
terraform fmt -recursive -check=true
# Expected: Exit 0 — no formatting changes needed

terraform validate
# Expected: "Success! The configuration is valid."
```

### 2. Plan Review
```bash
terraform plan -out=tfplan -lock=false
# Expected: Plan shows oci_logging_* resources, no unexpected DESTROY actions
# Exit code: 0
```

### 3. State and Output Verification
```bash
terraform state list | grep oci_logging
# Expected: oci_logging_log_group.*, oci_logging_log.*, oci_logging_unified_agent_configuration.*

terraform output app_log_group_id
# Expected: ocid1.loggroup.oc1.*
```

### 4. OCI CLI Log Health Check
```bash
oci logging log list \
  --log-group-id <log_group_ocid> \
  --query 'data[].{"name":"display-name","enabled":"is-enabled","retention":"retention-duration","state":"lifecycle-state"}'
# Expected: All logs show "enabled": true, "state": "ACTIVE"

oci logging unified-agent-configuration list \
  --compartment-id <compartment_ocid> \
  --query 'data[].{"name":"display-name","state":"configuration-state","enabled":"is-enabled"}'
# Expected: UMA configs show configurationState "SUCCEEDED"
```

**Troubleshooting**:
- `retention-duration: 30` on production log → Recreate log with correct `retention_duration`; cannot be recovered retroactively.
- UMA `configurationState: "FAILED"` → Check IAM policy exists for dynamic group; verify `matching_rule` uses `instance.compartment.id`.
- Log object `state: "INACTIVE"` → Check `is_enabled = true`; verify source service (LB, API GW) has logging enabled referencing this log OCID.
- Connector Hub `lifecycleState: "INACTIVE"` → Add SCH IAM policy with `request.principal.type='serviceconnector'`.

---

## Quick Reference

**Essential Terraform commands**:
```bash
terraform init -upgrade    # Ensure oracle/oci ~> 8.15 downloaded
terraform fmt -recursive   # Format HCL
terraform validate         # Schema + syntax check
terraform plan -out=tfplan # Dry run
terraform apply tfplan     # Apply from plan
terraform state list       # List managed resources
```

**Import commands**:
```bash
terraform import oci_logging_log_group.app_logs "<group_ocid>"
terraform import "oci_logging_log.service[\"lb-access\"]" "logGroupId/<group_ocid>/logId/<log_ocid>"
terraform import oci_logging_unified_agent_configuration.app "<config_ocid>"
```

**Critical limits**:

| Resource | Default Limit | Scope | Action |
|---|---|---|---|
| Log Groups | 50 | Per compartment | Request increase via OCI Support |
| Logs per Log Group | 100 | Per log group | Request increase |
| Retention duration | 30–180 days | Per Log object | >180 days requires Connector Hub → Object Storage |
| UMA config poll | 30 seconds | Per instance | Config changes apply without restart |

---

## External Resources

### Official Documentation
- [OCI Logging Overview](https://docs.oracle.com/iaas/Content/Logging/Concepts/loggingoverview.htm) (verified 2026-07-26)
- [OCI Logging Management API v20200531](https://docs.oracle.com/iaas/api/#/en/logging-management/20200531/) (verified 2026-07-26)
- [OCI Unified Monitoring Agent](https://docs.oracle.com/iaas/Content/Logging/Concepts/agentconcepts.htm) (verified 2026-07-26)

### Terraform Registry
- [oci_logging_log_group](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/logging_log_group) (verified 2026-07-26)
- [oci_logging_log](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/logging_log) (verified 2026-07-26)
- [oci_logging_unified_agent_configuration](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/logging_unified_agent_configuration) (verified 2026-07-26)
- [OCI Provider Registry (oracle/oci)](https://registry.terraform.io/providers/oracle/oci/latest) (verified 2026-07-26)

### Security & IAM
- [OCI IAM Policies for Logging](https://docs.oracle.com/iaas/Content/Logging/Task/managinglogs.htm) (verified 2026-07-26)
- [OCI Resource Tags](https://docs.cloud.oracle.com/iaas/Content/General/Concepts/resourcetags.htm) (verified 2026-07-26)

### Reference Implementation
- [Official OCI Logging Terraform Examples](https://github.com/oracle/terraform-provider-oci/tree/master/examples/logging) (verified 2026-07-26)
