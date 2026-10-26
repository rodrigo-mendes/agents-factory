# Integration Patterns — managing-terraform-cicd

## Complete Azure DevOps Pipeline Template

Full two-stage pipeline: Validate (PR) → Apply (merge to main). Copy as `azure-pipelines.yml` at repo root.

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

**Why it's mandatory**: Complete pipeline covering validation, plan artifact passing, and staged apply
**Failure if omitted**: Incomplete pipeline missing serialization, credential injection, or plan review gate

---

## PR Trigger Configuration

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

**Source**: [Azure DevOps YAML Pipeline trigger](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/trigger)

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

## Required Variable Group: `oci-terraform-credentials`

| Variable | Type | Description |
|----------|------|-------------|
| `OCI_TENANCY_OCID` | Secret | OCI tenancy OCID |
| `OCI_USER_OCID` | Secret | OCI user OCID |
| `OCI_FINGERPRINT` | Secret | API key fingerprint |
| `OCI_PRIVATE_KEY` | Secret | PEM private key content |
| `OCI_S3_ACCESS_KEY` | Secret | Customer Secret Key — access key |
| `OCI_S3_SECRET_KEY` | Secret | Customer Secret Key — secret key |

**Rules**:
- Use `env:` blocks to inject secrets — never inline in `script:`
- Scope variable groups to specific pipelines when possible
- Mark ALL credential variables as **secret** (lock icon in Library UI)
