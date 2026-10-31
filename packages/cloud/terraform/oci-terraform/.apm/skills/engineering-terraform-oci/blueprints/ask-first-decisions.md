# ⚠️ Ask First — Terraform OCI Engineering Best Practices

## Decision 1: Repository Strategy

**Agent**: Ask: "How many OCI applications does the team manage, and do they share infrastructure patterns?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Hybrid** (recommended) | Shared modules versioned independently; per-app blast radius | Module version bumps required per consumer | 2–5 apps, small team (2–5 engineers) |
| Monorepo | Single VCS, cross-app visibility | Noisy CI; everyone can touch everything | 1–2 apps, tiny team |
| Polyrepo | Full isolation | Hard to share modules; no cross-app visibility | Large teams, security-sensitive separation |

**Hybrid structure** (recommended for multi-app / small team):
```
terraform-oci-modules/        # shared modules registry (Git tags = versions)
  └── modules/
      ├── networking/
      ├── compute/
      └── object-storage/

oci-app-one-infra/            # per-app deployment repo
  ├── modules/                # app-specific local modules
  ├── dev/
  │   ├── terraform.tf
  │   ├── backend.tf
  │   ├── main.tf
  │   └── terraform.tfvars
  └── prod/
      ├── terraform.tf
      ├── backend.tf
      ├── main.tf
      └── terraform.tfvars
```

**Module versioning** (Git ref pinning):
```hcl
module "networking" {
  # Production: exact tag
  source = "git::https://github.com/org/terraform-oci-modules.git//modules/networking?ref=v1.2.0"
}
```

---

## Decision 2: Environment Isolation Strategy

**Agent**: Ask: "Do dev and prod have significantly different resource configurations (shapes, counts, features enabled)?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Directory-per-env** (recommended) | Full state isolation; blast radius = 1 env × 1 app | Some code duplication | Different configs per env — most cases |
| `terraform workspace` | Single codebase | Same state structure across envs; workspace-specific backends need care | Truly identical infra across envs |
| Terragrunt | DRY + isolation + workspace-like structure | Learning curve; extra tool | 3+ environments or 5+ apps |

**Directory-per-env structure** (recommended):
```
oci-app-one-infra/
├── dev/
│   ├── backend.tf        # bucket = "tf-state-dev", key = "app-one/terraform.tfstate"
│   └── terraform.tfvars  # environment = "dev", shape = "VM.Standard.E3.Flex", ocpu = 1
└── prod/
    ├── backend.tf        # bucket = "tf-state-prod", key = "app-one/terraform.tfstate"
    └── terraform.tfvars  # environment = "prod", shape = "VM.Standard.E4.Flex", ocpu = 4
```

**State isolation**: Each directory has its own backend → separate OCI Object Storage object → zero blast radius between environments.

---

## Decision 3: Module Granularity

**Agent**: Ask: "Do multiple applications follow the same infrastructure shape?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Infrastructure module** (recommended) | Multi-resource logical unit; reusable abstraction | Initial design time | 2+ apps sharing same stack shape |
| Thin resource wrapper | Claimed reusability | No abstraction value; pure indirection | **Never** — use resources directly |
| Single root module | Simplicity | No reusability | Single throwaway environment |

**Infrastructure module** (recommended) — composes multiple resources:
```hcl
# modules/app-stack/main.tf
resource "oci_core_vcn" "app" { ... }
resource "oci_core_subnet" "app" { ... }
resource "oci_functions_function" "app" { ... }
resource "oci_objectstorage_bucket" "app" { ... }
# Outputs: vcn_id, subnet_id, function_id

# Consuming in dev/main.tf:
module "app_stack" {
  source           = "../modules/app-stack"
  environment      = "dev"
  compartment_ocid = var.compartment_ocid
  app_name         = "payment-service"
}
```

**Thin wrapper anti-pattern** — do NOT create a module that wraps a single resource:
```hcl
# ❌ modules/vcn/main.tf — no abstraction value, just indirection
resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_id
  cidr_block     = var.cidr_block
  display_name   = var.display_name
}
# Use oci_core_vcn directly in main.tf instead
```

---

## Decision 4: Cross-Stack Reference Mechanism

**Agent**: Ask: "Do non-Terraform tools (scripts, apps) also need access to the shared values?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **OCI provider data sources** (recommended) | Loose coupling; non-TF consumers work | Resource must be discoverable by name/tag | Networking IDs, shared infra (recommended) |
| `terraform_remote_state` | Explicit Terraform outputs | Exposes full state to consumer; tight coupling | Small teams, all stacks under same control |
| OCI Vault parameters | Cross-tool, secure, auditable | Requires OCI Vault setup | Sensitive values across stacks and tools |

**Preferred** — provider data source (loose coupling):
```hcl
data "oci_core_vcns" "shared_vcn" {
  compartment_id = var.compartment_ocid
  display_name   = "shared-vcn-${var.environment}"
}

resource "oci_core_subnet" "app" {
  vcn_id         = data.oci_core_vcns.shared_vcn.virtual_networks[0].id
  compartment_id = var.compartment_ocid
  # ...
}
```

**Acceptable** — `terraform_remote_state` (when teams control both stacks):
```hcl
data "terraform_remote_state" "networking" {
  backend = "oci"
  config = {
    bucket    = "tf-state-${var.environment}"
    namespace = var.oci_namespace
    key       = "shared-networking/terraform.tfstate"
    region    = var.region
  }
}

resource "oci_core_instance" "app" {
  subnet_id = data.terraform_remote_state.networking.outputs.app_subnet_id
}
```

---

## Decision 5: CI/CD Tooling

**Agent**: Ask: "Is the CI runner hosted on OCI Compute? Does the team need a Terraform-native PR review UI?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **GitHub Actions** (recommended) | Native OIDC; easy setup; matrix builds | No built-in plan approval UI | Teams already on GitHub |
| Atlantis | Native plan-on-PR + apply-on-comment UX; repo-level config | Must host the Atlantis server | Terraform-native UX at zero SaaS cost |
| HCP Terraform | Fully managed (state + runs + policy); Sentinel | Cost ($20+/user/month for Plus) | Teams wanting turnkey solution |

**Pipeline stage order** (all tools):
```
fmt -check → validate → plan (on PR) → manual review → apply (on merge/approval)
```

**InstancePrincipal for Atlantis on OCI Compute** (no API key storage):
```hcl
provider "oci" {
  region = var.region
  auth   = "InstancePrincipal"
}
terraform {
  backend "oci" {
    auth = "InstancePrincipal"
    # ...
  }
}
```

---

## Decision 6: Removing or Changing optional+computed OCI Attributes

**Agent**: Ask: "Are you trying to remove or change a resource attribute that was previously set, using only `terraform apply`? Check whether the attribute is optional+computed in the OCI provider — if so, a plain apply is a no-op."

The OCI Terraform provider marks several resource attributes as **optional+computed**: when these attributes are absent from the HCL configuration, the provider interprets the absence as "leave the live value as-is" rather than "set to null/default". This makes plain `terraform apply` a **silent no-op** for the intended change.

**Known optional+computed traps in OCI serverless patterns**:

| Resource | Attribute | Effect of removing from HCL |
|----------|-----------|------------------------------|
| `oci_streaming_stream_pool` | `private_endpoint_settings` | NO-OP — pool remains private; ErrorsAtSource persists if SCH is source |
| `oci_functions_function` | `provisioned_concurrency_config` | NO-OP — PC containers keep running; cost continues |

**Correct approach — use `-replace` (Terraform) or CLI (OCI)**:

```bash
# Option A: force-replace via terraform (destroys + recreates resource)
# Use when resource recreation is acceptable (e.g., POC, pool switch to public)
terraform apply -replace='module.streaming.oci_streaming_stream_pool.this'
# → Review the cascading plan: stream, SCH connectors, producer config all update

# Option B: OCI CLI direct update (no resource recreation, no Terraform drift)
# Use for provisioned_concurrency on Functions (avoids function OCID change)
oci fn function update \
  --function-id <OCID> \
  --provisioned-concurrency '{"strategy":"NONE"}' \
  --force
# Then verify: oci fn function get --function-id <OCID> --query 'data."provisioned-concurrency-config"'
# terraform plan afterward should show no diff (TF already considers live state correct)
```

**Evidence**: `docs/handoff/event-pubsub/deploy-report.md` cycle 7 (provisioned_concurrency no-op confirmed; PC removed via CLI), cycle 9 (private_endpoint_settings no-op confirmed; pool recreated via -replace).
