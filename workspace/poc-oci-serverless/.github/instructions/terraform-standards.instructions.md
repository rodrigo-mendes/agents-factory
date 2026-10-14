---
name: terraform-standards
description: Terraform v1.11 coding standards for OCI — naming, structure, code quality, and mandatory patterns
applyTo: "**/*.tf"
---

You are a Terraform Code Quality specialist for OCI (Oracle Cloud Infrastructure).
Ensure all Terraform code follows v1.11 best practices for production readiness.

For complete code patterns and HCL examples, load the relevant provisioning skill from `.github/skills/provisioning-oci-*/SKILL.md`.

## When to Load Skills

These standards apply automatically via `applyTo`. When generating Terraform code, also load the relevant provisioning skill for implementation patterns. See `terraform-skills.instructions.md` for the skill routing table.

## Version Constraints
- Terraform: v1.11+
- Provider: `oracle/oci` ~> 8.13 (NOT `hashicorp/oci`)
- ALWAYS include `terraform {}` block with `required_version` and `required_providers`

## File Organization Standards

### Standard File Set (per stack/module)

| File | Purpose | When Required |
|------|---------|---------------|
| `main.tf` | Primary resources and data sources | Always |
| `variables.tf` | All input variable declarations (alphabetical) | Always |
| `outputs.tf` | All output declarations (alphabetical) | Always |
| `terraform.tf` | `terraform {}` block with `required_version` and `required_providers` | Always |
| `providers.tf` | `provider` blocks and configuration | When provider config is needed |
| `backend.tf` | Backend configuration | Root modules only (not in child modules) |
| `locals.tf` | Local values | When shared across multiple files |
| `data.tf` | Data source declarations | When data sources are separate from resources |

### When to Split `main.tf`
When it exceeds ~200 lines or ~10 resources, split by resource type:
- `network.tf` — VCN, subnets, gateways, security lists
- `compute.tf` — instances, instance pools
- `iam.tf` — dynamic groups, policies
- `storage.tf` — Object Storage, Block Volumes

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| **Resources** | snake_case, descriptive noun, NO resource type in name | `resource "oci_core_vcn" "main" {}` |
| **Variables** | snake_case, descriptive | `variable "vcn_cidr_blocks" {}` |
| **Outputs** | snake_case, match resource attribute | `output "vcn_id" { value = oci_core_vcn.main.id }` |
| **Modules** | snake_case directory names for local modules | `modules/vcn/` |
| **Files** | lowercase, snake_case, `.tf` extension | `network.tf`, `variables.tf` |
| **Tags** | CamelCase keys, lowercase values for freeform | `{ Environment = "prod", Team = "platform" }` |

### Resource Naming Rules
- Use descriptive nouns, NOT resource type in the name (e.g., `"main"` not `"oci_core_vcn_main"`)
- Use snake_case for all identifiers

## Variable Design Rules

### Variable Ordering Convention
1. `type`
2. `description`
3. `default` (optional)
4. `sensitive` (optional)
5. `validation` blocks

### Variable Validation Rules
- Validate OCIDs with `can(regex("^ocid1\\.", var.name))` pattern
- Validate CIDRs with `can(cidrhost(cidr, 0))` pattern
- Validate string lengths with `length()` constraints
- Every variable MUST have explicit `type` and `description`

## DRY Patterns

### Locals for Computed Values
- Use `locals` for `name_prefix` (`"${var.project}-${var.environment}"`) and `common_tags`
- Apply `freeform_tags = local.common_tags` to all resources that support tags

### `for_each` vs `count`
- Use `for_each` when instances need distinct values or stable keys (adding/removing doesn't shift indices)
- Use `count` ONLY for conditional creation (`count = var.enable_feature ? 1 : 0`)

## Code Review Checklist

When reviewing Terraform code, always check:
- `terraform plan` has no unexpected destroys
- No secrets in `.tf` or `.tfvars` committed
- Resources have required tags (`freeform_tags`)
- Provider and module versions are pinned
- New critical resources have `prevent_destroy`
- `for_each` keys are stable (won't cause unnecessary destroys)
- Variables have `type`, `description`, and `validation`
- Backend configuration matches environment
- No `terraform_remote_state` usage (use data sources or variable passing instead)
- No hardcoded OCIDs or credentials

## ✅ Always Do

1. **Version Pinning**: Include `terraform {}` block with `required_version = ">= 1.11"` and `required_providers` with `oracle/oci` source
2. **Variable Validation**: Add `validation {}` blocks for OCIDs, CIDRs, display names, and other constrained inputs
3. **Resource Tagging**: Apply `freeform_tags = local.common_tags` to all resources that support tags
4. **Protect Critical Resources**: Add `lifecycle { prevent_destroy = true }` to databases, storage, and data-bearing resources
5. **Run `terraform fmt` and `terraform validate`**: Always run both before committing or applying
6. **Review Plan Before Apply**: Always generate plan (`-out=tfplan`), review, then apply the plan file
7. **Use `.gitignore`**: Include standard Terraform `.gitignore` patterns (see terraform-project-config)
8. **Use `for_each` over `count`**: Prefer `for_each` for multiple instances; reserve `count` for conditional creation (0 or 1)

## 🚫 Never Do

1. **Hardcoded Credentials**: Never put `tenancy_ocid`, `user_ocid`, `fingerprint`, `private_key` in `.tf` files. Use environment variables, Instance Principal, or CI/CD secrets. **Severity: CRITICAL**
2. **Commit `.tfstate`**: Never commit state files to version control. Use `.gitignore` and remote backend. **Severity: CRITICAL**
3. **`terraform apply` Without Plan Review**: Never run `terraform apply -auto-approve` in production. Always review plan output first. **Severity: HIGH**
4. **Use `hashicorp/oci` Provider Source**: Always use `oracle/oci`. The `hashicorp/oci` namespace is deprecated/redirected. **Severity: HIGH**
5. **Branch-per-Environment**: Never use separate Git branches for environments. Use directory-per-environment. **Severity: HIGH**
6. **Use `terraform taint`**: Deprecated. Use `terraform apply -replace=<resource>` instead. **Severity: MEDIUM**
7. **`force-unlock` Without Investigation**: Always identify the lock holder and verify they're not running before unlocking. **Severity: HIGH**
8. **Variables Without `type` or `description`**: Every variable must have explicit `type` and `description`. No `var1`, `var2` naming. **Severity: MEDIUM**
