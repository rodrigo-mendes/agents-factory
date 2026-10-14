---
name: provisioning-oci-apm
description: "Provisions and configures OCI APM resources with Terraform oracle/oci v8.0+. Use when creating APM domains, synthetic monitors, Apdex rules, span filters, metric groups, vantage points, or managing APM data key security with Terraform on OCI."
---

## Version Context

**Technology**: Terraform + OCI Provider (oracle/oci)
**Target version**: oracle/oci ~> 8.0 (latest 8.15.0) / Terraform >= 1.9
**Release date**: 2026-05-20
**Support status**: Active

**Important changes in v8.x**:
- `config_type = "MACS_APM_EXTENSION"` added to `oci_apm_config_config`
- `content_type = "PLAYWRIGHT_TS"` added to `oci_apm_synthetics_script`
- `oci_apm_synthetics_on_premise_vantage_point_worker` resource added

**Deprecated**: None

⚠️ **CRITICAL — Agent Warning**:
This skill targets oracle/oci ~> 8.0 / Terraform >= 1.9. Reject patterns from oracle/oci < 5.0.
`is_free_tier` on `oci_apm_apm_domain` is **immutable** — changing it forces domain recreation.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory HCL with full examples
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architecture decisions with tradeoff matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with ❌/✅ alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — IAM, Vault, Monitoring, ONS, Streaming, Logging
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases
- **[Verification Loop](#verification-loop)** — Terraform validation commands
- **[Quick Reference](#quick-reference)** — Limits and critical constraints
- **[External Resources](#external-resources)** — Official documentation

---

## Blueprints & Guardrails

### ✅ Always Do

Full code examples → [Always Do Patterns](./blueprints/always-do-patterns.md)

**Domain**: Complex — 9 mandatory patterns apply:

1. **OCI Backend + Version Lock** — Pin `oracle/oci ~> 8.0`, use OCI Object Storage backend; no local state in shared infrastructure.
2. **Instance Principal auth (no credentials in code)** — Use `auth = "InstancePrincipal"` in production; for CI/CD use env vars (`TF_VAR_*`), never `.tf` literal values.
3. **APM Domain with `lifecycle.prevent_destroy`** — Always set `is_free_tier` explicitly, `prevent_destroy = true`, and `ignore_changes = [is_free_tier]` in production.
4. **Data Keys → OCI Vault** — Pipe private data keys to `oci_vault_secret`; mark any output containing key values `sensitive = true`. Never output raw key values.
5. **SPAN_FILTER before METRIC_GROUP** — Reference span filter OCID directly in `filter_id`; this creates implicit dependency. Never use placeholder OCIDs.
6. **Apdex rules with explicit priority** — Set `priority`, `satisfied_response_time`, and `tolerating_response_time` on every rule; include a catch-all rule at high priority number.
7. **Synthetic monitor interval/timeout validation** — Validate `repeat_interval_in_seconds >= 60` (REST) or `>= 300` (others) via `variable` validation block before plan.
8. **IAM policies per sub-service** — Separate `manage apm-domains` / `manage apm-synthetics-monitor` / `manage apm-config` statements; never grant tenancy-wide `manage all-resources`.
9. **Variable type constraints for all OCIDs and enums** — Use `can(regex("^ocid1\\."))` validation and `contains([...])` for enum inputs.

### ⚠️ Ask First

Full decision matrices → [Ask First Decisions](./blueprints/ask-first-decisions.md)

**6 architectural crossroads — always confirm before proceeding**:

1. **Free Tier vs Paid Domain** — `is_free_tier` is immutable. Confirm environment type and cost approval before setting.
2. **Vantage Point Type** — Public (internet), Dedicated (VCN-private, requires RM stack + Streaming), or On-Premise (behind firewall). Confirm endpoint visibility.
3. **Inline vs Script-Based Monitor** — Simple URL check (REST/BROWSER) vs multi-step script (SCRIPTED_REST/SCRIPTED_BROWSER/PLAYWRIGHT_TS).
4. **Multi-Environment Domain Strategy** — Separate domain per env vs shared domain; compliance and isolation requirements drive this.
5. **State Isolation Strategy** — Terraform workspaces vs directory-per-environment; APM domain recreation risk favors directory isolation.
6. **Apdex Granularity** — Global catch-all vs per-service vs per-operation rules; depends on SLA differentiation between services.

### 🚫 Never Do

Full anti-patterns with alternatives → [Never Do Patterns](./blueprints/never-do-patterns.md)

**7 prohibited patterns**:

1. **Plain-text APM data key output** — `CRITICAL`: exposes bearer token in CI/CD logs and state inspect.
2. **`is_free_tier` without `lifecycle.ignore_changes`** — `CRITICAL`: accidental change destroys domain + all child resources.
3. **Script parameter secrets hardcoded in `.tf`** — `HIGH`: credentials land in `.tfstate` in plaintext.
4. **No `prevent_destroy` on production APM domain** — `CRITICAL`: `terraform destroy` permanently deletes all APM data; no soft-delete.
5. **Untagged APM resources** — `HIGH`: blocks cost attribution, OCI governance policy enforcement.
6. **`filter_id` with hardcoded OCID in METRIC_GROUP** — `MEDIUM`: breaks across environments; causes 400 at apply time.
7. **`count = 0` to disable monitors** — `MEDIUM`: destroys monitor history; use `status = "DISABLED"` instead.

---

## Integration Patterns

Full integration code → [Integration Patterns](./blueprints/integration-patterns.md)

- **Terraform ↔ OCI IAM** — Group + policy per sub-service; 15–30s propagation delay after apply.
- **Terraform ↔ OCI Vault** — Write private data key as `oci_vault_secret`; use `ignore_changes = [secret_content]` to avoid rotation conflicts.
- **Terraform ↔ OCI Monitoring** — APM METRIC_GROUP publishes to a custom namespace; `oci_monitoring_alarm` queries that namespace.
- **Terraform ↔ OCI Notifications (ONS)** — Topic + subscription for alerts; email requires manual confirmation; APM Synthetics alert binding not yet a TF resource — use Monitoring alarm as workaround.
- **Terraform ↔ OCI Streaming** — Required for Dedicated Vantage Points (DVP); `dvp_stream_id` wired to `oci_apm_synthetics_dedicated_vantage_point`.
- **Terraform ↔ OCI Logging** — Service Connector Hub routes APM metrics to Logging Analytics for long-term retention.

**Common problems**:
- **`400 InvalidParameter` on METRIC_GROUP apply** → `filter_id` references non-existent SPAN_FILTER; check creation order.
- **IAM policy not effective immediately after apply** → Wait 30s; IAM propagation is async.
- **APM domain plan shows "must be replaced"** → `is_free_tier` changed; add `lifecycle.ignore_changes = [is_free_tier]` and revert the value.

---

## Verification Loop

Run after every code generation:

### 1. Format
```bash
terraform fmt -recursive -check=true
# Expected: exit 0, no output
# Fix: terraform fmt -recursive
```

### 2. Validate
```bash
terraform validate
# Expected: "Success! The configuration is valid." | Exit: 0
```

### 3. Security Scan
```bash
tfsec . --exclude-results-below-severity HIGH
checkov -d . --framework terraform --compact
# Expected: 0 HIGH/CRITICAL findings from tfsec; Checkov passed > failed
```

### 4. Plan (explicit var file)
```bash
terraform plan -var-file="terraform.tfvars" -out=apm.tfplan
terraform show apm.tfplan | grep "must be replaced"
# Expected: no "must be replaced" lines — especially for oci_apm_apm_domain
```

### 5. State Verify (post-apply)
```bash
terraform state list | grep apm
terraform state show oci_apm_apm_domain.main | grep -E "(state|data_upload)"
# Expected: state = "ACTIVE"
```

**Troubleshooting**:
- `Error: is_free_tier is immutable` → Domain must be recreated; confirm with user before proceeding.
- `Error: repeat_interval_in_seconds must be >= 60` → Increase interval in variable or `.tfvars`.
- `Error 404 on filter_id` → SPAN_FILTER resource not yet applied; verify dependency reference is direct (not hardcoded OCID).

---

## Quick Reference

**Essential commands**:
```bash
terraform init -upgrade        # Init + upgrade to latest ~> 8.x patch
terraform fmt -recursive       # Format all .tf files
terraform validate             # Syntax + schema check
terraform plan -out=apm.tfplan # Plan to file
terraform apply apm.tfplan     # Apply from plan file only
```

**Critical limits**:

| Resource | Constraint | Notes |
|----------|-----------|-------|
| REST monitor interval | >= 60s | API validation error if violated |
| All other monitor types interval | >= 300s | BROWSER, SCRIPTED_*, NETWORK, DNS, FTP, SQL |
| Monitor timeout | ≤ 50% of interval (no retry) / ≤ 30% (retry) | |
| Synthetic monitors per domain | 100 (soft limit) | Request increase via support |
| Vantage points per monitor | 50 | |
| Script size (JS/PLAYWRIGHT_TS) | 64 KB | SIDE scripts: 1 MB |
| Config items per domain | 1000 | Span filters + metric groups + Apdex combined |
| Free tier domains per tenancy | 1 | Hard limit |

**Immutable properties** (changing = resource recreation):
- `oci_apm_apm_domain`: `is_free_tier`
- `oci_apm_synthetics_monitor`: `monitor_type`
- `oci_apm_synthetics_dedicated_vantage_point`: `display_name`
- `oci_apm_config_config`: `config_type`

---

## External Resources

- [OCI Provider Registry v8.x](https://registry.terraform.io/providers/oracle/oci/latest) (verified 2026-07-26)
- [oci_apm_apm_domain resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apm_apm_domain) (verified 2026-07-26)
- [oci_apm_config_config resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apm_config_config) (verified 2026-07-26)
- [oci_apm_synthetics_monitor resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apm_synthetics_monitor) (verified 2026-07-26)
- [oci_apm_synthetics_script resource](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apm_synthetics_script) (verified 2026-07-26)
- [oci_apm_data_keys data source](https://registry.terraform.io/providers/oracle/oci/latest/docs/data-sources/apm_data_keys) (verified 2026-07-26)
- [OCI Backend for Terraform](https://developer.hashicorp.com/terraform/language/backend/oci) (verified 2026-07-26)
- [OCI Provider Authentication Guide](https://registry.terraform.io/providers/oracle/oci/latest/docs/guides/authentication) (verified 2026-07-26)
- [OCI APM Overview](https://docs.oracle.com/iaas/Content/ApplicationPerformanceMonitoring/Concepts/apmconceptsoverview.htm) (verified 2026-07-26)
- [OCI Provider Changelog](https://github.com/oracle/terraform-provider-oci/blob/master/CHANGELOG.md) (verified 2026-07-26)
- [tfsec](https://github.com/aquasecurity/tfsec) | [Checkov OCI rules](https://www.checkov.io/) (verified 2026-07-26)
