# Integration Patterns — managing-terraform-state

## OCI Object Storage Remote Backend (Full Configuration)

Complete `backend.tf` for remote state stored in OCI Object Storage via the S3-compatible API.

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

    # Required — OCI Object Storage does not expose AWS-compatible metadata endpoints
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}
```

**Credential injection** (never hardcode in backend config):
```bash
export AWS_ACCESS_KEY_ID="${OCI_S3_ACCESS_KEY}"
export AWS_SECRET_ACCESS_KEY="${OCI_S3_SECRET_KEY}"
terraform init
```

**Source**: [OCI Object Storage S3 Compatibility](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/s3compatibleapi.htm)

---

## State Key Structure (Remote Backend)

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

**Naming convention**: `<project>/<component>/<env>/terraform.tfstate`

---

## Declarative Import Block (v1.11+)

```hcl
# Step 1 — add import block to any .tf file in the environment directory
import {
  to = oci_core_vcn.existing
  id = "ocid1.vcn.oc1.iad.aaa..."
}

# Step 2 — generate resource config (creates generated.tf)
# terraform plan -generate-config-out=generated.tf

# Step 3 — review generated.tf, then apply
# terraform apply
```

**Why declarative over CLI import**: Tracked in code, reproducible, auditable in PR reviews
**Source**: [Terraform Import Configuration Generation](https://developer.hashicorp.com/terraform/language/import)

---

## `moved {}` Block Patterns

```hcl
# Pattern 1 — Rename a resource (no destroy/recreate)
moved {
  from = oci_core_vcn.main_vcn
  to   = oci_core_vcn.this
}

# Pattern 2 — Move resource into a module
moved {
  from = oci_core_vcn.this
  to   = module.networking.oci_core_vcn.this
}

# Pattern 3 — Rename a module
moved {
  from = module.network
  to   = module.networking
}
```

**Why it's mandatory**: Prevents unnecessary destroy/recreate during refactoring
**Source**: [Terraform Refactoring](https://developer.hashicorp.com/terraform/language/moved)

---

## Cross-State Reference Pattern

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

Pass the OCID via `tfvars` or pipeline `TF_VAR_vcn_id` environment variable — never via `terraform_remote_state`.

---

## State Operations Safety Reference

| Operation | Command | Safety Check |
|-----------|---------|--------------|
| **Move resource** | `terraform state mv old new` | Run `terraform plan` after — expect 0 changes |
| **Declarative move** | `moved { from = ...; to = ... }` in `.tf` | Preferred — tracked in code |
| **Import existing** | `import { to = ...; id = "..." }` in `.tf` | Run `terraform plan -generate-config-out=generated.tf` |
| **Remove from state** | `terraform state rm <resource>` | Backup state first |
| **Refresh / drift** | `terraform plan -refresh-only` | Review drift before applying |
| **Replace resource** | `terraform apply -replace=<resource>` | Review plan before applying |

---

## Disaster Recovery Runbook

1. **Before any state operation**:
   ```bash
   terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate
   ```
2. **After state corruption** — restore from backup:
   ```bash
   terraform state push backup-20260101-120000.tfstate
   ```
3. **Remote state** — enable OCI Object Storage versioning on the state bucket so every write is retained
4. **Lock stuck** — identify the lock holder (`terraform force-unlock` shows lock ID and timestamp); verify no process is running before unlocking
