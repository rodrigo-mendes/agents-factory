---
name: managing-terraform-cicd
description: Manages Terraform CI/CD pipelines for Azure DevOps deploying to OCI — plan-on-PR, apply-on-merge, credential management, pipeline security, and serialized execution.
---

## Version Context

**Technology**: Terraform CI/CD with Azure DevOps
**Target Version**: Terraform v1.11+ / OCI Provider oracle/oci ~> 8.13
**Pipeline Platform**: Azure DevOps (YAML Pipelines)
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

⚠️ **CRITICAL — Agent Warning**:
OCI has no state locking mechanism (no DynamoDB equivalent). All pipeline jobs MUST be serialized with `maxParallel: 1` to prevent concurrent state modifications. Plan files contain sensitive state — never log or expose them.

## Quick Navigation

- **[Always Do Patterns](#-always-do)** — Mandatory pipeline patterns
- **[Ask First Decisions](#️-ask-first)** — Pipeline architecture decisions
- **[Never Do Patterns](#-never-do)** — Pipeline anti-patterns
- **[Verification Loop](#verification-loop)** — Pipeline validation commands
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance

---

## Blueprints & Guardrails

### ✅ Always Do

#### Two-Stage Pipeline Architecture
**Why it's mandatory**: Separates validation (PR) from deployment (merge) to ensure all changes are reviewed before applying.

```yaml
trigger:
  branches:
    include:
      - main
  paths:
    include:
      - environments/*
      - modules/*

pr:
  branches:
    include:
      - main
  paths:
    include:
      - environments/*
      - modules/*
```

**Stages**:
1. **Validate** (on PR): `fmt -check` → `validate` → `plan` → publish plan artifact
2. **Apply** (on merge to main): download plan artifact → `init` → `apply`

**Failure if omitted**: Unreviewed infrastructure changes applied to production
**Source**: [Azure DevOps YAML Pipeline](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema)

#### Complete Pipeline Template

```yaml
# azure-pipelines.yml
variables:
  - group: oci-terraform-credentials  # Variable group with OCI secrets
  - name: TF_VERSION
    value: '1.11.0'
  - name: OCI_REGION
    value: 'us-ashburn-1'

stages:
  - stage: Validate
    displayName: 'Terraform Validate & Plan'
    jobs:
      - job: Plan
        pool:
          vmImage: 'ubuntu-latest'
        strategy:
          matrix:
            dev:
              ENVIRONMENT: dev
            staging:
              ENVIRONMENT: staging
            prod:
              ENVIRONMENT: prod
          maxParallel: 1  # Serialize — OCI has no state locking
        steps:
          - task: TerraformInstaller@1
            displayName: 'Install Terraform'
            inputs:
              terraformVersion: $(TF_VERSION)

          - script: |
              cd environments/$(ENVIRONMENT)
              terraform init -input=false
            displayName: 'Terraform Init'
            env:
              AWS_ACCESS_KEY_ID: $(OCI_S3_ACCESS_KEY)
              AWS_SECRET_ACCESS_KEY: $(OCI_S3_SECRET_KEY)

          - script: terraform fmt -check -recursive
            displayName: 'Format Check'

          - script: |
              cd environments/$(ENVIRONMENT)
              terraform validate
            displayName: 'Validate'

          - script: |
              cd environments/$(ENVIRONMENT)
              terraform plan \
                -var-file=$(ENVIRONMENT).tfvars \
                -out=tfplan \
                -input=false
            displayName: 'Plan'
            env:
              AWS_ACCESS_KEY_ID: $(OCI_S3_ACCESS_KEY)
              AWS_SECRET_ACCESS_KEY: $(OCI_S3_SECRET_KEY)
              TF_VAR_tenancy_ocid: $(OCI_TENANCY_OCID)
              TF_VAR_user_ocid: $(OCI_USER_OCID)
              TF_VAR_fingerprint: $(OCI_FINGERPRINT)
              TF_VAR_private_key: $(OCI_PRIVATE_KEY)
              TF_VAR_region: $(OCI_REGION)

          - publish: environments/$(ENVIRONMENT)/tfplan
            artifact: tfplan-$(ENVIRONMENT)

  - stage: Apply
    displayName: 'Terraform Apply'
    dependsOn: Validate
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: ApplyDev
        displayName: 'Apply Dev'
        environment: dev
        pool:
          vmImage: 'ubuntu-latest'
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                - download: current
                  artifact: tfplan-dev
                - script: |
                    cd environments/dev
                    terraform init -input=false
                    cp $(Pipeline.Workspace)/tfplan-dev/tfplan .
                    terraform apply -input=false tfplan
                  env:
                    AWS_ACCESS_KEY_ID: $(OCI_S3_ACCESS_KEY)
                    AWS_SECRET_ACCESS_KEY: $(OCI_S3_SECRET_KEY)
                    TF_VAR_tenancy_ocid: $(OCI_TENANCY_OCID)
                    TF_VAR_user_ocid: $(OCI_USER_OCID)
                    TF_VAR_fingerprint: $(OCI_FINGERPRINT)
                    TF_VAR_private_key: $(OCI_PRIVATE_KEY)
                    TF_VAR_region: $(OCI_REGION)
```

**Why it's mandatory**: Complete pipeline covering validation, plan artifact, and apply stages
**Failure if omitted**: Incomplete pipeline missing stages, credential injection, or serialization

#### Credential Management via Variable Groups

Store all OCI credentials in Azure DevOps **variable groups** (Library), marked as **secret**.

**Required Variable Group: `oci-terraform-credentials`**

| Variable | Type | Description |
|----------|------|-------------|
| `OCI_TENANCY_OCID` | Secret | OCI tenancy OCID |
| `OCI_USER_OCID` | Secret | OCI user OCID |
| `OCI_FINGERPRINT` | Secret | API key fingerprint |
| `OCI_PRIVATE_KEY` | Secret | PEM private key content |
| `OCI_S3_ACCESS_KEY` | Secret | Customer Secret Key — access key |
| `OCI_S3_SECRET_KEY` | Secret | Customer Secret Key — secret key |

**Rules**:
- Use `env:` blocks to inject secrets — never `script` inline
- Scope variable groups to specific pipelines when possible
- Mark ALL credential variables as **secret** (lock icon)

#### Pipeline Flags

```bash
# Always use these flags to prevent interactive prompts and ensure reproducibility
terraform init -input=false
terraform plan -var-file=dev.tfvars -out=tfplan -input=false
terraform apply -input=false tfplan
```

- Always use `-input=false` on `init`, `plan`, and `apply`
- Always use `-out=tfplan` on `plan` and apply the saved plan file
- Pin Terraform version via `TerraformInstaller@1` — never use `latest`

---

### ⚠️ Ask First

#### Environment Promotion Strategy
**Decision point**: How should changes propagate from dev → staging → prod?

| Option | Safety | Speed | When to choose |
|--------|--------|-------|----------------|
| Sequential gates (manual approval per env) | High | Slow | Production workloads, compliance requirements |
| Auto-promote dev, gate staging+prod | Medium | Medium | Standard development workflow |
| Auto-promote all (dev only) | Low | Fast | Development/experimentation only |

**Agent behavior**: "Before configuring environment gates, ask: 'Should staging/prod applies require manual approval, or should all environments auto-apply on merge?'"

---

### 🚫 Never Do

#### Hardcoded Credentials
```yaml
# 🚫 INCORRECT — credentials in pipeline YAML
- script: |
    export TF_VAR_tenancy_ocid="ocid1.tenancy.oc1..aaa..."
    terraform plan
```

```yaml
# ✅ CORRECT — credentials from variable group
- script: terraform plan -var-file=dev.tfvars -out=tfplan -input=false
  env:
    TF_VAR_tenancy_ocid: $(OCI_TENANCY_OCID)
```

**Why it's prohibited**: Credentials in YAML are committed to version control — security breach
**Real impact**: API keys exposed in Git history, impossible to fully revoke

#### Auto-Approve in Production
```bash
# 🚫 INCORRECT — no plan review
terraform apply -auto-approve

# ✅ CORRECT — apply a reviewed plan file
terraform plan -out=tfplan
terraform apply tfplan
```

**Why it's prohibited**: Unreviewed changes applied directly — potential destruction of resources
**Real impact**: Accidental resource deletion, data loss, downtime

---

## Pipeline Security Matrix

| Concern | Mitigation |
|---------|------------|
| **Credential storage** | Azure DevOps variable groups marked as secret |
| **Plan file sensitivity** | Plan files contain state — treat as secrets, use artifacts with retention |
| **State access** | OCI Customer Secret Keys scoped to a service user with minimal IAM policies |
| **PR plan output** | Sanitize plan output — mask OCIDs and sensitive values |
| **Branch protection** | Require PR reviews, status checks passing, no direct push to main |
| **Apply serialization** | `maxParallel: 1` — OCI has no state locking, serialize applies |

---

## Verification Loop

### 1. Pipeline Syntax Validation
```bash
# Validate YAML syntax (Azure DevOps CLI)
az pipelines validate --yaml-path azure-pipelines.yml
```
**Expected output**: Valid YAML syntax
**Exit code**: 0

### 2. Terraform Format Check
```bash
terraform fmt -check -recursive
```
**Expected output**: No output (all files formatted)
**Exit code**: 0

### 3. Terraform Validate
```bash
terraform init -backend=false && terraform validate
```
**Expected output**: `Success! The configuration is valid.`
**Exit code**: 0

### 4. Plan Dry Run
```bash
cd environments/dev
terraform init -input=false
terraform plan -var-file=dev.tfvars -out=tfplan -input=false
```
**Expected output**: Plan summary with adds/changes/destroys
**Exit code**: 0

**Troubleshooting**:
- `Error: Failed to query available provider packages` → Check `terraform init` has network access
- `Error: Variables not allowed` → Check `env:` block injects `TF_VAR_*` correctly
- Concurrent state modification → Verify `maxParallel: 1` is set on all Terraform jobs

---

## Quick Reference

**Pipeline rules**:
1. Always use `-input=false` on `init`, `plan`, and `apply`
2. Always use `-out=tfplan` and apply the saved plan file
3. Never use `-auto-approve` — always apply a reviewed plan
4. Always run `fmt -check` and `validate` before `plan`
5. Use `maxParallel: 1` — OCI lacks state locking
6. Use `environment:` gates for staging/prod manual approval
7. Pin Terraform version — never use `latest`

**External Resources**:
- [Azure DevOps YAML Schema](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema)
- [Terraform CLI Commands](https://developer.hashicorp.com/terraform/cli/commands)
- [OCI Customer Secret Keys](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcredentials.htm)
