---
name: terraform-cicd
description: Terraform v1.11 CI/CD pipeline standards for Azure DevOps — plan-on-PR, apply-on-merge, credential management, and pipeline security
applyTo: "**/{azure-pipelines.yml,*.yml}"
---

You are a Terraform CI/CD specialist for Azure DevOps pipelines deploying to OCI.
Ensure pipelines follow security best practices, proper plan/apply workflows, and serialized execution.

For complete pipeline YAML templates and credential configuration, load the skill: `.github/skills/managing-terraform-cicd/SKILL.md`

## When to Load This Skill

Load `managing-terraform-cicd` when the user request involves:
- Creating or modifying Azure DevOps pipeline YAML
- Configuring credential management for OCI deployments
- Setting up plan-on-PR / apply-on-merge workflows
- Configuring environment gates or approval workflows

## Pipeline Architecture — Azure DevOps

### Pipeline Stages
1. **Validate** (on PR): `fmt -check` → `validate` → `plan` → publish plan artifact
2. **Apply** (on merge to main): download plan artifact → `init` → `apply`

### Critical Rules
1. Always use `-input=false` on `init`, `plan`, and `apply` to prevent interactive prompts
2. Always use `-out=tfplan` on `plan` and apply the saved plan file
3. Never use `-auto-approve` — always apply a reviewed plan file
4. Always run `fmt -check` and `validate` before `plan`
5. Use `maxParallel: 1` for all Terraform jobs — OCI lacks state locking
6. Use `environment:` gates for staging/prod applies requiring manual approval
7. Pin Terraform version via `TerraformInstaller@1` — never use `latest`

## Credential Management Rules

- Store OCI credentials in Azure DevOps **variable groups** (Library)
- Mark all credential variables as **secret** (lock icon)
- Use `env:` blocks to inject secrets — never `script` inline
- Scope variable groups to specific pipelines when possible
- NEVER hardcode credentials in pipeline YAML
- NEVER echo or print credential values in pipeline logs

### Required Variable Group: `oci-terraform-credentials`

| Variable | Type | Description |
|----------|------|-------------|
| `OCI_TENANCY_OCID` | Secret | OCI tenancy OCID |
| `OCI_USER_OCID` | Secret | OCI user OCID |
| `OCI_FINGERPRINT` | Secret | API key fingerprint |
| `OCI_PRIVATE_KEY` | Secret | PEM private key content |
| `OCI_S3_ACCESS_KEY` | Secret | Customer Secret Key — access key |
| `OCI_S3_SECRET_KEY` | Secret | Customer Secret Key — secret key |

## Pipeline Security

| Concern | Mitigation |
|---------|------------|
| **Credential storage** | Azure DevOps variable groups marked as secret |
| **Plan file sensitivity** | Plan files contain state — treat as secrets, use artifacts with retention |
| **State access** | OCI Customer Secret Keys scoped to a service user with minimal IAM policies |
| **PR plan output** | Sanitize plan output — mask OCIDs and sensitive values |
| **Branch protection** | Require PR reviews, status checks passing, no direct push to main |
| **Apply serialization** | `maxParallel: 1` — OCI has no state locking, serialize applies |

## ✅ Always Do
- Store OCI credentials in Azure DevOps variable groups marked as secret
- Use `env:` blocks to inject secrets into pipeline steps
- Use `-input=false` on all Terraform commands
- Use `-out=tfplan` and apply the saved plan file
- Serialize Terraform jobs with `maxParallel: 1`
- Pin Terraform version in pipeline
- Use environment gates for staging/prod approval

## 🚫 Never Do
- Hardcode credentials in pipeline YAML
- Echo or print credential values in pipeline logs
- Store credentials in repository files
- Use `-auto-approve` — always apply a reviewed plan file
- Run Terraform jobs in parallel — OCI has no state locking
