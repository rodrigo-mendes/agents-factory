---
name: managing-terraform-state
description: "Manages Terraform state lifecycle for OCI — local and remote backends, state isolation, declarative import/moved blocks, operations safety, and disaster recovery. Use when configuring Terraform backends, migrating state, importing existing OCI resources, or recovering from state corruption."
---

## Version Context

**Technology**: Terraform State Management for OCI
**Target Version**: Terraform v1.11+ / OCI Provider oracle/oci ~> 8.13
**Backend**: Local (dev default) / OCI Object Storage via S3-compatible API (team/CI recommended)
**Support Status**: Active

**Key Capabilities (v1.11+)**:
- Declarative `import {}` blocks with `-generate-config-out` for auditable imports
- Declarative `moved {}` blocks for safe refactoring without destroy/recreate
- `terraform plan -refresh-only` for drift detection without applying changes
- `terraform apply -replace=<resource>` (replaces deprecated `taint`)

**Critical Constraints**:
- OCI Object Storage does NOT support state locking (no DynamoDB equivalent)
- `.tfstate` files contain ALL resource attributes including sensitive values — never commit to VCS
- State operations (`state mv`, `state rm`) are irreversible without backups

> **CRITICAL**: Always back up state before any operation: `terraform state pull > backup.tfstate`. State files contain sensitive data — never commit to version control, never share unencrypted. OCI Object Storage lacks native locking — serialize all applies in CI/CD.

---

## Quick Navigation

**In this file**: ✅ Always Do · ⚠️ Ask First · 🚫 Never Do · Verification Loop · Quick Reference · External Resources

**Blueprints**:
- [Full Backend Config + Patterns](./blueprints/integration-patterns.md) — Complete HCL + state ops reference + disaster recovery
- [Evaluation Scenarios](./blueprints/evaluation-scenarios.md) — Canonical, edge, and misuse test cases

---

## Blueprints & Guardrails

### ✅ Always Do

#### State Isolation — Per Environment via Directory

Each environment has its own state file via directory isolation:

```
environments/
├── dev/
│   └── terraform.tfstate
├── staging/
│   └── terraform.tfstate
└── prod/
    └── terraform.tfstate
```

**Why it's mandatory**: Prevents accidental cross-environment resource modification
**Failure if omitted**: `terraform apply` in the wrong directory destroys production resources

#### OCI Object Storage Remote Backend

Use the S3-compatible backend for team and CI/CD workflows. Full `backend.tf` with all required `skip_*` flags in [blueprints/integration-patterns.md](./blueprints/integration-patterns.md).

**Key config snippet**:
```hcl
terraform {
  backend "s3" {
    bucket   = "terraform-state-bucket"
    key      = "project-alpha/dev/terraform.tfstate"
    region   = "us-ashburn-1"
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

**Why it's mandatory**: Team collaboration requires shared state with credential isolation
**Source**: [OCI Object Storage S3 Compatibility](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/s3compatibleapi.htm)

#### Declarative Import (v1.11+)

```hcl
# Step 1 — declare in any .tf file
import {
  to = oci_core_vcn.existing
  id = "ocid1.vcn.oc1.iad.aaa..."
}

# Step 2 — generate resource config
# terraform plan -generate-config-out=generated.tf
```

**Why it's mandatory**: Declarative imports are tracked in code and auditable in PR reviews — unlike CLI `terraform import`
**Failure if omitted**: Ad-hoc CLI imports leave no audit trail and cannot be reproduced

#### Refactoring with `moved {}` Blocks

```hcl
# Rename a resource without destroying it
moved {
  from = oci_core_vcn.main_vcn
  to   = oci_core_vcn.this
}

# Move a resource into a module
moved {
  from = oci_core_vcn.this
  to   = module.networking.oci_core_vcn.this
}
```

Additional patterns (module rename, verification) in [blueprints/integration-patterns.md](./blueprints/integration-patterns.md).

**Why it's mandatory**: `moved {}` blocks prevent unnecessary destroy/recreate during refactoring
**Failure if omitted**: Resource rename without `moved {}` destroys and recreates the resource — causes downtime

#### Cross-State References via Data Sources

```hcl
# ✅ CORRECT — explicit dependency injection via variable
variable "vcn_id" {
  type        = string
  description = "OCID of the VCN from the networking stack"
}

data "oci_core_vcn" "existing" {
  vcn_id = var.vcn_id
}
```

Pass `vcn_id` via `tfvars` or `TF_VAR_vcn_id` in CI/CD — never via `terraform_remote_state`.

---

### ⚠️ Ask First

#### Backend Migration: Local to Remote

**Decision point**: When to migrate from local state to OCI Object Storage backend?

| Signal | Action | Risk |
|--------|--------|------|
| Solo developer, simple project | Keep local state | Low — backup manually |
| Team collaboration needed | Migrate to remote | Medium — requires credential setup |
| CI/CD pipeline deployment | Migrate to remote | Required — pipeline needs shared state |
| 50+ resources per stack | Consider stack splitting | Medium — split by component |

**Agent behavior**: Before configuring a remote backend, ask: "Is this a solo workflow or does a team need shared state access? Does CI/CD need to apply changes?"

#### State Splitting Strategy

**Decision point**: When should a state file be split?

| Stack Size | Strategy | State Key Pattern |
|-----------|----------|-------------------|
| < 50 resources | Single state per environment | `project/env/terraform.tfstate` |
| 50–200 resources | Split by layer (network, compute, IAM) | `project/env/networking.tfstate` |
| 200+ resources | Split by service domain | `project/env/service-a.tfstate` |

**Agent behavior**: Before splitting state, ask: "How many resources are in the current state? What are the natural domain boundaries?"

**Decision factors**:
- Team size and ownership boundaries
- Blast radius of a state corruption event
- Inter-stack dependency complexity

---

### 🚫 Never Do

#### Using `terraform_remote_state` for Cross-Stack Dependencies

```hcl
# 🚫 WRONG — exposes ALL outputs, tight coupling between stacks
data "terraform_remote_state" "networking" {
  backend = "local"
  config  = { path = "../networking/terraform.tfstate" }
}
```

```hcl
# ✅ CORRECT — explicit variable injection, loose coupling
variable "vcn_id" {
  type        = string
  description = "OCID of the VCN from the networking stack"
}

data "oci_core_vcn" "existing" {
  vcn_id = var.vcn_id
}
```

**Why it's prohibited**: `terraform_remote_state` exposes ALL outputs — output changes in one stack can silently break all dependent stacks
**Real impact**: Renaming an output in the networking stack causes a plan error in every dependent stack simultaneously

#### Committing `.tfstate` to Version Control

```gitignore
# ✅ Add to .gitignore — always
*.tfstate
*.tfstate.*
.terraform.tfstate.lock.info
```

**Why it's prohibited**: State files contain ALL resource attributes including passwords, private keys, and endpoints
**Real impact**: Credentials exposed in Git history are practically irrevocable — require full key rotation and security audit

#### Force-Unlock Without Investigation

```bash
# 🚫 WRONG — force-unlocking blindly on any lock error
terraform force-unlock <LOCK_ID>

# ✅ RIGHT — investigate the lock holder first, unlock only when proven stale
# 1. Read the lock error: it prints Who / Created / ID
#    Lock Info: ID: <LOCK_ID>, Who: user@host, Created: 2026-07-26T14:00:00Z
# 2. Confirm no CI/CD job or teammate is mid-apply (check pipeline runs)
# 3. Only if the holder is confirmed dead/stale:
terraform force-unlock <LOCK_ID>
```

**Why it's prohibited**: Another process may be actively modifying state
**Real impact**: Premature unlock allows concurrent state modification — resources orphaned, duplicated, or corrupted
**Correct approach**: Identify the lock holder (timestamp in error), verify no CI/CD job is running, then unlock

---

## Verification Loop

### 1. State Health Check
```bash
terraform state list | wc -l
```
**Expected**: Number of managed resources | **Exit code**: 0

### 2. Drift Detection
```bash
terraform plan -refresh-only
```
**Expected**: `No changes` or list of drifted resources | **Exit code**: 0 (no drift) or 2 (drift detected — not an error)

### 3. State Backup Before Operation
```bash
terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate
```
**Expected**: JSON state file written to disk | **Exit code**: 0

### 4. Post-Operation Validation
```bash
terraform plan
```
**Expected**: `No changes` after state move/import operations | **Exit code**: 0

**Troubleshooting**:
- `Error: Backend initialization required` → Run `terraform init`
- `Error: State lock` → Check for running processes; never `force-unlock` blindly
- `Error: Resource not found` in state → Resource deleted outside Terraform; run `terraform plan -refresh-only`

---

## Quick Reference

```bash
# Backup state (always first)
terraform state pull > backup.tfstate

# List managed resources
terraform state list

# Detect drift without applying
terraform plan -refresh-only

# Generate config for declarative import (v1.11+)
terraform plan -generate-config-out=generated.tf

# Safe replace (replaces deprecated taint)
terraform apply -replace=oci_core_vcn.main
```

---

## External Resources

- [Terraform State Management](https://developer.hashicorp.com/terraform/language/state) — State concepts and backends (verified 2026-07-26)
- [Terraform Backend S3](https://developer.hashicorp.com/terraform/language/backend/s3) — S3-compatible backend configuration (verified 2026-07-26)
- [Import Configuration Generation](https://developer.hashicorp.com/terraform/language/import) — Declarative import blocks (verified 2026-07-26)
- [Terraform Refactoring (moved)](https://developer.hashicorp.com/terraform/language/moved) — moved {} block reference (verified 2026-07-26)
- [OCI Object Storage S3 Compatibility](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/s3compatibleapi.htm) — Backend endpoint format and credentials (verified 2026-07-26)
- [Terraform OCI Provider Data Sources](https://registry.terraform.io/providers/oracle/oci/latest/docs) — OCI data source reference (verified 2026-07-26)
