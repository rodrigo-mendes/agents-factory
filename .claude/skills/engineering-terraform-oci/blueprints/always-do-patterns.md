# ✅ Always Do — Terraform OCI Engineering Best Practices

## 1. Pin Terraform + Provider Versions

**Freedom**: Low — exact syntax; mismatches break pipelines silently

```hcl
# terraform.tf — in every root module and shared module
terraform {
  required_version = "~> 1.9"   # allow 1.9.x patch updates, block 2.x

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 8.15"       # allow 8.x, block 9.0
    }
  }
}
```

**Why**: Unpinned versions pull breaking changes on `terraform init -upgrade`. `~> 1.9` allows only patch updates.

---

## 2. OCI Object Storage Backend (Remote State with Locking)

**Freedom**: Low — exact configuration; never local backend in team environments

```hcl
# backend.tf (dev environment)
terraform {
  backend "oci" {
    bucket = "tf-state-dev"
    key    = "app-one/terraform.tfstate"
    region = "us-ashburn-1"
    # KMS encryption for production:
    # kms_key_id = "ocid1.key.oc1.iad.xxxxxxxxxxxxx"
    # namespace passed via: terraform init -backend-config="namespace=<tenancy-ns>"
    # auth = "InstancePrincipal"  # for CI/CD on OCI Compute
  }
}
```

**Locking**: Built-in via `If-None-Match: *` header on Object Storage — no DynamoDB equivalent needed.

**Per-environment separation** (required):
```
tf-state-dev bucket  → dev/  directory state files
tf-state-prod bucket → prod/ directory state files (separate bucket, not just separate key)
```

**Required IAM policy** for CI/CD dynamic group:
```
Allow dynamic-group 'terraform-ci-dg' to manage objects in compartment 'infra'
  where target.bucket.name = 'tf-state-dev'
```

---

## 3. Enable State Bucket Versioning

**Freedom**: Low — one-time setup per bucket; enables recovery from state corruption

```bash
# Run once during initial environment setup
oci os bucket update \
  --bucket-name tf-state-prod \
  --versioning Enabled
# Expected: HTTP 200 | "versioning": "Enabled"

# Verify
oci os bucket get --bucket-name tf-state-prod \
  --query 'data.versioning'
# Expected: "Enabled"
```

**State recovery** (when corruption occurs):
```bash
# Pull current state before surgery
terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate

# Restore a previous version via OCI CLI
oci os object get \
  --bucket-name tf-state-prod \
  --name app-one/terraform.tfstate \
  --version-id <VERSION_ID> \
  --file terraform.tfstate.restored
terraform state push terraform.tfstate.restored
```

---

## 4. Validate All Module Inputs with `validation {}` Blocks

**Freedom**: Medium — pattern is fixed; exact regex/condition varies by variable type

```hcl
# variables.tf — order: type → description → default → sensitive → validation
variable "environment" {
  type        = string
  description = "Deployment environment. Determines resource sizing and policies."
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "compartment_ocid" {
  type        = string
  description = "OCID of the OCI compartment where resources will be provisioned."
  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid must be a valid OCI compartment OCID (ocid1.compartment.*)."
  }
}

variable "db_admin_password" {
  type        = string
  description = "Admin password for the Autonomous Database. Must be 12-30 chars."
  sensitive   = true
  validation {
    condition     = length(var.db_admin_password) >= 12 && length(var.db_admin_password) <= 30
    error_message = "db_admin_password must be between 12 and 30 characters."
  }
}
```

**Why**: Validation fires at `terraform plan` — before any OCI API calls — catching misconfiguration early with clear messages.

---

## 5. `prevent_destroy = true` on Critical Resources

**Freedom**: Low — exact lifecycle block; omit only for ephemeral/test resources

```hcl
resource "oci_database_autonomous_database" "app_db" {
  # ... required fields ...
  lifecycle {
    prevent_destroy = true   # terraform destroy fails with error in prod
    ignore_changes  = [freeform_tags]  # allow out-of-band tag updates without recreation
  }
}

resource "oci_core_vcn" "prod_network" {
  # ...
  lifecycle {
    prevent_destroy = true
  }
}
```

**Apply to**: databases, prod VCNs, prod state buckets, OCI Functions application resources.
**Omit for**: dev/test resources, ephemeral compute instances, module examples.

---

## 6. `common_tags` Locals on Every Resource

**Freedom**: Medium — structure is fixed; tag key names are org-specific

```hcl
# locals.tf — centralized tag composition
locals {
  common_tags = {
    Environment = var.environment        # "dev" | "prod"
    Application = var.app_name           # "payment-service"
    ManagedBy   = "Terraform"
    Repository  = "github.com/org/repo"  # traceability
  }
}

# Apply to every resource
resource "oci_objectstorage_bucket" "logs" {
  name          = "${var.app_name}-${var.environment}-logs"
  freeform_tags = local.common_tags
}

resource "oci_objectstorage_bucket" "backups" {
  name          = "${var.app_name}-${var.environment}-backups"
  freeform_tags = local.common_tags
}
```

**Why**: Untagged resources cannot be attributed in OCI Cost Analysis. Governance policies retroactively flag untagged resources.

---

## 7. Enforce `.gitignore`

**Freedom**: Low — exact file content; prevents credential and state exposure

```gitignore
# .gitignore (repo root) — never commit these
.terraform/
*.tfstate
*.tfstate.*
.terraform.tfstate.lock.info
*.tfplan
override.tf
override.tf.json
*_override.tf
*_override.tf.json
secrets.auto.tfvars
*.pem
*.key
.terraformrc
terraform.rc
```

**Non-sensitive `.tfvars`** (safe to commit):
```
# dev/terraform.tfvars — commit this (no secrets)
environment  = "dev"
app_name     = "payment-service"
shape        = "VM.Standard.E3.Flex"
ocpu_count   = 1
```

**Never commit**: files containing passwords, private keys, or secret OCIDs.

---

## 8. Run `fmt -check` + `validate` in CI on Every PR

**Freedom**: Low — exact commands; blocks broken configs before plan

```bash
# Required CI gate — must all exit 0 before plan stage runs
terraform fmt -check -recursive    # fails if any file is not canonical format
terraform init -backend=false       # init without backend (validates provider schema)
terraform validate                  # checks types, required args, resource references
```

**Auto-fix locally** before pushing:
```bash
terraform fmt -recursive  # rewrites files in-place to canonical format
```

**Why**: These three commands together catch: formatting inconsistencies, type errors, missing required arguments, invalid resource references — all before any OCI API calls are made.
