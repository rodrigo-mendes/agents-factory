---
name: managing-terraform-cicd
description: "Manages Terraform CI/CD pipelines for Azure DevOps deploying to OCI — plan-on-PR, apply-on-merge, credential management, pipeline security, and serialized execution. Use when setting up or debugging Azure DevOps pipelines that run Terraform against OCI infrastructure."
---

## Version Context

**Technology**: Terraform CI/CD with Azure DevOps
**Target Version**: Terraform v1.11+ / OCI Provider oracle/oci ~> 8.13
**Pipeline Platform**: Azure DevOps YAML Pipelines
**Support Status**: Active

**Key Capabilities**:
- Plan-on-PR / Apply-on-merge workflow with artifact passing
- Multi-environment matrix strategy with serialized execution
- OCI Customer Secret Key credential injection via variable groups
- Pipeline security with branch protection and environment gates

**Critical Constraints**:
- OCI Object Storage does NOT support state locking — serialize all applies with `maxParallel: 1`
- Plan files contain state data — treat as secrets with retention policies
- Never use `-auto-approve` — always apply a reviewed plan file

> **CRITICAL**: OCI has no state locking mechanism (no DynamoDB equivalent). All pipeline jobs MUST use `maxParallel: 1` to prevent concurrent state modifications. Plan files contain sensitive state — never log or expose them.

---

## Quick Navigation

**In this file**: ✅ Always Do · ⚠️ Ask First · 🚫 Never Do · Verification Loop · Quick Reference · External Resources

**Blueprints**:
- [Full Pipeline Template](./blueprints/integration-patterns.md) — Complete YAML + security matrix + variable group
- [Evaluation Scenarios](./blueprints/evaluation-scenarios.md) — Canonical, edge, and misuse test cases

---

## Blueprints & Guardrails

### ✅ Always Do

#### Two-Stage Pipeline: Validate (PR) then Apply (merge)

Separates validation from deployment — all changes are reviewed before applying.

**Stages**:
1. **Validate** (on PR): `fmt -check` → `validate` → `plan` → publish plan artifact
2. **Apply** (on merge to main): download plan artifact → `init` → `apply -input=false tfplan`

See the complete YAML in [blueprints/integration-patterns.md](./blueprints/integration-patterns.md).

**Why it's mandatory**: Prevents unreviewed infrastructure changes from reaching production
**Failure if omitted**: Unreviewed plan applied directly — potential destruction of production resources

#### Serialized Execution with `maxParallel: 1`

```yaml
strategy:
  matrix:
    dev:
      ENVIRONMENT: dev
    staging:
      ENVIRONMENT: staging
    prod:
      ENVIRONMENT: prod
  maxParallel: 1  # Serialize — OCI has no state locking
```

**Why it's mandatory**: OCI Object Storage has no state locking. Concurrent applies corrupt state.
**Failure if omitted**: Race condition corrupts `.tfstate` — resources orphaned or duplicated

#### Non-Interactive Pipeline Flags

```bash
# Always use these flags — prevent interactive prompts and ensure reproducibility
terraform init   -input=false
terraform plan   -var-file=${ENVIRONMENT}.tfvars -out=tfplan -input=false
terraform apply  -input=false tfplan
```

- `-input=false` on `init`, `plan`, and `apply` — prevents pipeline hang waiting for input
- `-out=tfplan` on `plan` — apply the saved plan file, never re-plan without review
- Pin Terraform version via `TerraformInstaller@1` — never use `latest`

#### Credential Injection via Variable Groups

Store all OCI credentials in Azure DevOps **Library → Variable Groups**, marked as **secret**. Inject via `env:` blocks.

```yaml
# ✅ CORRECT — credentials from variable group, injected via env:
- script: terraform plan -var-file=dev.tfvars -out=tfplan -input=false
  env:
    TF_VAR_tenancy_ocid: $(OCI_TENANCY_OCID)
    TF_VAR_private_key: $(OCI_PRIVATE_KEY)
    AWS_ACCESS_KEY_ID: $(OCI_S3_ACCESS_KEY)
    AWS_SECRET_ACCESS_KEY: $(OCI_S3_SECRET_KEY)
```

Required variables: `OCI_TENANCY_OCID`, `OCI_USER_OCID`, `OCI_FINGERPRINT`, `OCI_PRIVATE_KEY`, `OCI_S3_ACCESS_KEY`, `OCI_S3_SECRET_KEY`. Full table in [blueprints/integration-patterns.md](./blueprints/integration-patterns.md).

---

### ⚠️ Ask First

#### Environment Promotion Strategy

**Decision point**: How should changes propagate from dev → staging → prod?

| Option | Safety | Speed | When to choose |
|--------|--------|-------|----------------|
| Sequential gates (manual approval per env) | High | Slow | Production workloads, compliance requirements |
| Auto-promote dev, gate staging+prod | Medium | Medium | Standard development workflow |
| Auto-promote all | Low | Fast | Dev/experimentation environments only |

**Agent behavior**: Before configuring environment gates, ask: "Should staging/prod applies require manual approval, or should all environments auto-apply on merge to main?"

**Decision factors**:
- Compliance or change-management requirements for prod
- Team size (solo vs. multiple engineers merging concurrently)
- Tolerance for rollback vs. risk of unreviewed changes

---

### 🚫 Never Do

#### Hardcoded Credentials in Pipeline YAML

```yaml
# 🚫 WRONG — credentials committed to version control
- script: |
    export TF_VAR_tenancy_ocid="ocid1.tenancy.oc1..aaa..."
    terraform plan
```

```yaml
# ✅ CORRECT — reference variable group secret via env: block
- script: terraform plan -var-file=dev.tfvars -out=tfplan -input=false
  env:
    TF_VAR_tenancy_ocid: $(OCI_TENANCY_OCID)
```

**Why it's prohibited**: Credentials in YAML are committed to version control and exposed in Git history
**Real impact**: API keys in Git history are practically irrevocable — require full key rotation and audit

#### Auto-Approve Without Plan Review

```bash
# 🚫 WRONG — no plan review, changes applied blindly
terraform apply -auto-approve

# ✅ CORRECT — plan saved as artifact, reviewed, then applied
terraform plan -var-file=dev.tfvars -out=tfplan -input=false
terraform apply -input=false tfplan
```

**Why it's prohibited**: Unreviewed changes applied directly — accidental resource deletion, data loss, downtime
**Real impact**: `terraform apply -auto-approve` on a misconfigured change can destroy production resources with no recovery window

---

## Verification Loop

### 1. Pipeline Syntax Validation
```bash
az pipelines validate --yaml-path azure-pipelines.yml
```
**Expected**: Valid YAML syntax | **Exit code**: 0

### 2. Terraform Format Check
```bash
terraform fmt -check -recursive
```
**Expected**: No output (all files formatted) | **Exit code**: 0

### 3. Terraform Validate
```bash
terraform init -backend=false && terraform validate
```
**Expected**: `Success! The configuration is valid.` | **Exit code**: 0

### 4. Plan Dry Run
```bash
cd environments/dev
terraform init -input=false
terraform plan -var-file=dev.tfvars -out=tfplan -input=false
```
**Expected**: Plan summary with adds/changes/destroys | **Exit code**: 0

**Troubleshooting**:
- `Error: Failed to query available provider packages` → Check `terraform init` has network access
- `Error: Variables not allowed` → Verify `env:` block injects `TF_VAR_*` correctly
- Concurrent state modification → Confirm `maxParallel: 1` is set on all Terraform jobs

---

## Quick Reference

**Pipeline rules**:
1. `maxParallel: 1` on all Terraform matrix jobs — OCI lacks state locking
2. `-input=false` on `init`, `plan`, and `apply`
3. `-out=tfplan` on plan; always apply the saved plan file
4. Never `-auto-approve` — always apply a reviewed plan
5. `fmt -check` and `validate` before `plan`
6. `environment:` gates for staging/prod manual approval
7. Pin Terraform version — never use `latest`

---

## External Resources

- [Azure DevOps YAML Schema](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema) — Pipeline syntax reference (verified 2026-07-26)
- [Azure DevOps Variable Groups](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups) — Secret management in Library (verified 2026-07-26)
- [Terraform CLI Commands](https://developer.hashicorp.com/terraform/cli/commands) — init / plan / apply flags (verified 2026-07-26)
- [OCI Customer Secret Keys](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcredentials.htm) — S3-compatible credential setup (verified 2026-07-26)
- [OCI Object Storage S3 Compatibility](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/s3compatibleapi.htm) — Backend endpoint format (verified 2026-07-26)
- [Terraform OCI Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs) — oracle/oci provider reference (verified 2026-07-26)
