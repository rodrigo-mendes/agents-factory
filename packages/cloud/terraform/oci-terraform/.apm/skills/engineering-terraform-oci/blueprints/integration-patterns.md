# Integration Patterns — Terraform OCI Engineering Best Practices

## Terraform ↔ OCI Object Storage (Backend Setup)

**One-time setup** (before first `terraform init`):

```bash
# Create state bucket with versioning enabled
oci os bucket create \
  --compartment-id $INFRA_COMPARTMENT_OCID \
  --name tf-state-prod \
  --namespace $TENANCY_NAMESPACE

oci os bucket update \
  --bucket-name tf-state-prod \
  --versioning Enabled

# Required IAM policy for CI/CD dynamic group
oci iam policy create \
  --compartment-id $TENANCY_OCID \
  --name "terraform-ci-state-policy" \
  --description "Allow Terraform CI to manage state in Object Storage" \
  --statements '[
    "Allow dynamic-group terraform-ci-dg to manage objects in compartment infra where target.bucket.name='"'"'tf-state-prod'"'"'"
  ]'
```

**Partial config init** (keeps `namespace` out of `.tf` files — avoids tenancy exposure in VCS):
```bash
terraform init \
  -backend-config="namespace=$(oci os ns get --query 'data' --raw-output)" \
  -backend-config="auth=InstancePrincipal" \
  -backend-config="region=us-ashburn-1"
```

**Common issue**: `namespace` attribute rejected inside `backend "oci" {}` HCL block → always pass via `-backend-config` flag.

---

## Terraform ↔ OCI IAM (InstancePrincipal — Credential-Free CI/CD)

**When**: CI runner is an OCI Compute instance or OCI Functions. No API key rotation needed.

```hcl
# provider.tf
provider "oci" {
  region = var.region
  auth   = "InstancePrincipal"
  # No user_ocid, fingerprint, private_key — IAM policies on Dynamic Group control access
}

# backend.tf
terraform {
  backend "oci" {
    bucket = "tf-state-prod"
    key    = "app-one/terraform.tfstate"
    region = "us-ashburn-1"
    # auth = "InstancePrincipal" passed via -backend-config at init
  }
}
```

**OCI setup** (one-time):
1. Create Dynamic Group matching runner OCID: `instance.id = '<RUNNER_OCID>'`
2. Assign policy: `Allow dynamic-group 'terraform-ci-dg' to manage objects in compartment 'infra' where target.bucket.name = 'tf-state-prod'`
3. Add alarm/resource-specific policies as needed per stack

**Credential precedence** (high → low): env vars (`OCI_CLI_AUTH`) → provider block `auth` → `~/.oci/config`

---

## Terraform ↔ GitHub Actions (Plan-on-PR Pipeline)

**Minimal pipeline** (fmt + validate + plan on PR, apply on merge):

```yaml
# .github/workflows/terraform-plan.yml
name: Terraform Plan
on:
  pull_request:
    paths: ['dev/**', 'modules/**']

jobs:
  plan:
    runs-on: ubuntu-latest
    env:
      OCI_CLI_TENANCY:      ${{ secrets.OCI_TENANCY_OCID }}
      OCI_CLI_USER:         ${{ secrets.OCI_USER_OCID }}
      OCI_CLI_FINGERPRINT:  ${{ secrets.OCI_FINGERPRINT }}
      OCI_CLI_KEY_CONTENT:  ${{ secrets.OCI_PRIVATE_KEY }}
      OCI_CLI_REGION:       ${{ vars.OCI_REGION }}
      TF_VAR_compartment_ocid: ${{ secrets.DEV_COMPARTMENT_OCID }}
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.x"
      - run: terraform fmt -check -recursive
        working-directory: dev
      - run: terraform init
        working-directory: dev
      - run: terraform validate
        working-directory: dev
      - run: terraform plan -var-file="terraform.tfvars" -out=tfplan
        working-directory: dev
      - name: Upload plan artifact (CI-restricted, not public)
        uses: actions/upload-artifact@v4
        with:
          name: tfplan-dev
          path: dev/tfplan
          retention-days: 7
```

**Security**: Upload only the raw plan artifact as a restricted CI artifact. Post a sanitized summary (`terraform show -no-color tfplan | grep -E "^(Plan:|  [+~-])"`) as a PR comment — never the full plan output, which may contain sensitive values.

---

## Terraform ↔ `terraform test` (v1.9 Native Testing)

**Unit test** (no infrastructure — `command = plan`):
```hcl
# tests/module.tftest.hcl
variables {
  compartment_ocid = "ocid1.compartment.oc1..test"
  environment      = "dev"
}

run "reject_invalid_environment" {
  command   = plan
  variables { environment = "invalid-env" }
  expect_failures = [var.environment]   # validation block must fire
}

run "validate_resource_naming" {
  command = plan
  assert {
    condition     = oci_objectstorage_bucket.logs.name == "payment-service-dev-logs"
    error_message = "Bucket name must follow <app>-<env>-<purpose> convention"
  }
}
```

**Integration test** (real OCI resources — `command = apply`):
```hcl
run "create_and_verify_bucket" {
  command = apply   # creates real OCI resources; torn down after test run
  assert {
    condition     = oci_objectstorage_bucket.logs.access_type == "NoPublicAccess"
    error_message = "Bucket must not be publicly accessible"
  }
}
```

**Parallel tests** (v1.9 `state_key` — runs in isolation):
```hcl
test {
  parallel = true
}

run "test_networking" {
  command   = apply
  state_key = "net"    # isolated state key → safe to run in parallel
  module    { source = "./modules/networking" }
}

run "test_storage" {
  command   = apply
  state_key = "storage"
  module    { source = "./modules/storage" }
}
```

```bash
terraform test          # run all *.tftest.hcl in tests/ directory
# Expected: All tests passed.
```

---

## Terraform ↔ OCI Vault (Secret Injection)

**Purpose**: Inject passwords/tokens at plan time from OCI Vault; avoids secrets in `.tfvars` files.

```hcl
# Declare secret OCID as a variable (non-sensitive — it's an OCID, not the secret itself)
variable "db_password_secret_ocid" {
  type        = string
  description = "OCID of the OCI Vault secret containing the DB admin password."
  validation {
    condition     = can(regex("^ocid1\\.vaultsecret\\.", var.db_password_secret_ocid))
    error_message = "Must be a valid OCI Vault secret OCID."
  }
}

# Read the secret value at plan/apply time
data "oci_secrets_secretbundle" "db_password" {
  secret_id      = var.db_password_secret_ocid
  version_number = 1
}

resource "oci_database_autonomous_database" "app_db" {
  admin_password = data.oci_secrets_secretbundle.db_password.secret_bundle_content[0].content
  # ...
}
```

**IAM policy required**:
```
Allow dynamic-group 'terraform-ci-dg' to read secret-bundles in compartment 'infra'
  where target.secret.id = '<SECRET_OCID>'
```

**Note**: The secret value is still written to Terraform state in plaintext. Restrict state bucket access via IAM and enable Object Storage server-side encryption (`kms_key_id` on the backend).
