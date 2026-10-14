---
name: managing-terraform-state
description: Manages Terraform state lifecycle for OCI — local and remote backends, state isolation, declarative import/moved blocks, operations safety, and disaster recovery.
---

## Version Context

**Technology**: Terraform State Management for OCI
**Target Version**: Terraform v1.11+ / OCI Provider oracle/oci ~> 8.13
**Backend**: Local (current) / OCI Object Storage via S3-compatible API (future)
**Support Status**: Active

**Key Capabilities (v1.11)**:
- Declarative `import {}` blocks with `-generate-config-out`
- Declarative `moved {}` blocks for safe refactoring without destroy
- `terraform plan -refresh-only` for drift detection
- `terraform apply -replace=<resource>` (replaces deprecated `taint`)

**Critical Constraints**:
- OCI Object Storage does NOT support state locking (no DynamoDB equivalent)
- `.tfstate` files contain ALL resource attributes including sensitive values — never commit to VCS
- State operations (`state mv`, `state rm`) are irreversible without backups

⚠️ **CRITICAL — Agent Warning**:
Always back up state before any state operation: `terraform state pull > backup.tfstate`. State files contain sensitive data — never commit to version control, never share unencrypted. OCI Object Storage lacks native state locking — serialize all applies in CI/CD.

## Quick Navigation

- **[Always Do Patterns](#-always-do)** — Mandatory state management patterns
- **[Ask First Decisions](#️-ask-first)** — Backend and isolation decisions
- **[Never Do Patterns](#-never-do)** — State anti-patterns
- **[Verification Loop](#verification-loop)** — State operation validation
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance

---

## Blueprints & Guardrails

### ✅ Always Do

#### State Isolation — Per Environment via Directory

Each environment has its own state file via directory isolation:

```
environments/
├── dev/
│   └── terraform.tfstate         # Isolated dev state
├── staging/
│   └── terraform.tfstate         # Isolated staging state
└── prod/
    └── terraform.tfstate         # Isolated prod state
```

**Why it's mandatory**: Prevents accidental cross-environment resource modification
**Failure if omitted**: `terraform apply` in wrong directory destroys production resources

#### OCI Object Storage Remote Backend (Future)

```hcl
# environments/dev/backend.tf

terraform {
  backend "s3" {
    bucket = "terraform-state-bucket"
    key    = "project-alpha/dev/terraform.tfstate"
    region = "us-ashburn-1"

    endpoints = {
      s3 = "https://<namespace>.compat.objectstorage.us-ashburn-1.oraclecloud.com"
    }

    skip_region_validation      = true
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}
```

**Credential injection** (never hardcode):
```bash
export AWS_ACCESS_KEY_ID="${OCI_S3_ACCESS_KEY}"
export AWS_SECRET_ACCESS_KEY="${OCI_S3_SECRET_KEY}"
terraform init
```

**Why it's mandatory**: Team collaboration requires shared state with credential isolation
**Source**: [OCI Object Storage S3 Compatibility](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/s3compatibleapi.htm)

#### Declarative Import (v1.11)

```hcl
import {
  to = oci_core_vcn.existing
  id = "ocid1.vcn.oc1.iad.aaa..."
}

# Generate resource configuration:
# terraform plan -generate-config-out=generated.tf
```

**Why it's mandatory**: Declarative imports are tracked in code (auditable), unlike CLI `terraform import`
**Failure if omitted**: Ad-hoc CLI imports leave no audit trail and can't be reproduced

#### Refactoring with `moved {}` Blocks

```hcl
# Renaming a resource without destroying it
moved {
  from = oci_core_vcn.main_vcn
  to   = oci_core_vcn.this
}

# Moving a resource into a module
moved {
  from = oci_core_vcn.this
  to   = module.networking.oci_core_vcn.this
}

# Renaming a module
moved {
  from = module.network
  to   = module.networking
}
```

**Why it's mandatory**: `moved {}` blocks prevent unnecessary destroy/recreate during refactoring
**Failure if omitted**: Resource rename via manual state operations risks data loss and downtime

#### Cross-State References via Data Sources

```hcl
# ✅ CORRECT — use OCI data sources
data "oci_core_vcn" "existing" {
  vcn_id = var.vcn_id  # passed as variable
}
```

**Why it's mandatory**: Data sources are loosely coupled and don't expose all state outputs
**Source**: [OCI Terraform Provider Data Sources](https://registry.terraform.io/providers/oracle/oci/latest/docs)

---

### ⚠️ Ask First

#### Backend Migration: Local → Remote
**Decision point**: When to migrate from local state to OCI Object Storage backend?

| Signal | Action | Risk |
|--------|--------|------|
| Solo developer, simple project | Keep local state | Low — backup manually |
| Team collaboration needed | Migrate to remote | Medium — requires credential setup |
| CI/CD pipeline deployment | Migrate to remote | Required — pipeline needs shared state |
| 50+ resources per stack | Consider stack splitting | Medium — split by component |

**Agent behavior**: "Before configuring a remote backend, ask: 'Is this a solo workflow or does a team need shared state access? Does CI/CD need to apply changes?'"

#### State Splitting Strategy
**Decision point**: When should a state file be split into multiple states?

| Stack Size | Strategy | State Key Pattern |
|-----------|----------|-------------------|
| < 50 resources | Single state per environment | `project/env/terraform.tfstate` |
| 50-200 resources | Split by layer (network, compute, IAM) | `project/env/networking.tfstate` |
| 200+ resources | Split by service domain | `project/env/service-a.tfstate` |

**Agent behavior**: "Before splitting state, ask: 'How many resources are in the current state? What are the natural domain boundaries?'"

---

### 🚫 Never Do

#### Using `terraform_remote_state`

```hcl
# 🚫 INCORRECT — exposes ALL outputs, creates tight coupling
data "terraform_remote_state" "networking" {
  backend = "local"
  config  = { path = "../networking/terraform.tfstate" }
}
```

```hcl
# ✅ CORRECT — explicit dependency injection via variables
variable "vcn_id" {
  type        = string
  description = "OCID of the VCN from the networking stack"
}

data "oci_core_vcn" "existing" {
  vcn_id = var.vcn_id
}
```

**Why it's prohibited**: `terraform_remote_state` exposes ALL outputs, creating tight coupling between stacks
**Real impact**: Changes in one stack's outputs can break dependent stacks unexpectedly

#### Committing `.tfstate` to Version Control

**Why it's prohibited**: State files contain ALL resource attributes including sensitive values (passwords, keys, endpoints)
**Real impact**: Credentials exposed in Git history — impossible to fully revoke
**Mitigation**: Add to `.gitignore`:
```gitignore
*.tfstate
*.tfstate.*
.terraform.tfstate.lock.info
```

#### Force-Unlock Without Investigation

**Why it's prohibited**: Another process may be actively modifying state
**Real impact**: Concurrent state modification causes corruption — resources orphaned or duplicated
**Correct approach**: Identify the lock holder and verify they're not running before unlocking

---

## State Operations Safety

| Operation | Command | Safety Check |
|-----------|---------|--------------|
| **Move resource** | `terraform state mv old new` | Run `terraform plan` first — expect 0 changes after move |
| **Declarative move** | `moved { from = ...; to = ... }` in `.tf` file | Preferred over CLI — tracked in code |
| **Import existing** | `import { to = ...; id = "..." }` in `.tf` file | Run `terraform plan -generate-config-out=generated.tf` |
| **Remove from state** | `terraform state rm <resource>` | Backup state first: `terraform state pull > backup.tfstate` |
| **Refresh** | `terraform plan -refresh-only` | Review drift before applying |
| **Replace** | `terraform apply -replace=<resource>` | Review plan before applying |

---

## Disaster Recovery

1. **Before any state operation**: `terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate`
2. **After state corruption**: Restore from backup with `terraform state push backup.tfstate`
3. **For remote state**: Enable OCI Object Storage versioning on the state bucket
4. **Never `force-unlock` without investigation**: Identify the lock holder and verify they're not running

---

## Verification Loop

### 1. State Health Check
```bash
terraform state list | wc -l
```
**Expected output**: Number of managed resources
**Exit code**: 0

### 2. Drift Detection
```bash
terraform plan -refresh-only
```
**Expected output**: `No changes` or list of drifted resources
**Exit code**: 0 (no drift) or 2 (drift detected)

### 3. State Backup Before Operation
```bash
terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate
```
**Expected output**: JSON state file written to disk
**Exit code**: 0

### 4. Post-Operation Validation
```bash
terraform plan
```
**Expected output**: `No changes` after state move/import operations
**Exit code**: 0

**Troubleshooting**:
- `Error: Backend initialization required` → Run `terraform init`
- `Error: State lock` → Check if another process is running; never `force-unlock` blindly
- `Error: Resource not found` in state → Resource may have been deleted outside Terraform; `terraform plan -refresh-only`

---

## Quick Reference

**Essential commands**:
```bash
# Backup state
terraform state pull > backup.tfstate

# List managed resources
terraform state list

# Detect drift
terraform plan -refresh-only

# Import existing resource (v1.11 declarative)
# Add import {} block, then:
terraform plan -generate-config-out=generated.tf

# Safe replace (replaces deprecated taint)
terraform apply -replace=oci_core_vcn.main
```

**State key structure** (remote backend):
```
terraform-state-bucket/
├── project-alpha/
│   ├── dev/terraform.tfstate
│   ├── staging/terraform.tfstate
│   └── prod/terraform.tfstate
└── shared-networking/
    ├── dev/terraform.tfstate
    └── prod/terraform.tfstate
```

**External Resources**:
- [Terraform State Management](https://developer.hashicorp.com/terraform/language/state)
- [Import Configuration Generation](https://developer.hashicorp.com/terraform/language/import)
- [OCI Object Storage S3 Compatibility](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/s3compatibleapi.htm)
