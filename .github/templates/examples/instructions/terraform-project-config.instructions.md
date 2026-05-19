---
name: terraform-project-config
description: Terraform v1.11 project configuration standards for OCI — monorepo layout, directory-per-environment, provider setup, and .gitignore
applyTo: "**/{*.tf,*.tfvars,.terraform.lock.hcl}"
---

You are a Terraform Project Configuration specialist for OCI.
Ensure Terraform projects follow the monorepo layout with directory-per-environment isolation for a solo developer workflow.

For complete HCL patterns and provider configuration examples, load the relevant provisioning skill from `.github/skills/provisioning-oci-*/SKILL.md`.

## When to Load Skills

Load provisioning skills when generating environment configuration or module calls. See `terraform-skills.instructions.md` for the skill routing table.

## Project Structure — Monorepo with Local Modules

```
project-infra/
├── modules/                       # Shared local modules
│   ├── networking/
│   ├── compute/
│   ├── functions/
│   ├── api-gateway/
│   └── iam/
├── environments/
│   ├── dev/
│   │   ├── main.tf               # Calls shared modules
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── terraform.tf          # Version constraints
│   │   ├── providers.tf          # Provider config
│   │   ├── locals.tf             # Environment-specific locals
│   │   └── dev.tfvars
│   ├── staging/
│   └── prod/
├── tests/
│   ├── networking.tftest.hcl
│   └── compute.tftest.hcl
├── .gitignore
└── README.md
```

## Environment Strategy — Directory-per-Environment

Each environment has its own directory with independent state and configuration:
- Natural state isolation per environment
- Independent blast radius per environment
- No risk of applying to the wrong workspace

### Apply Workflow
Navigate to the environment directory, then init → plan → apply with the environment's `.tfvars` file.

## File Organization — Split by Resource Type

When a stack exceeds ~200 lines or ~10 resources, split `main.tf` into:
- `network.tf`, `compute.tf`, `iam.tf`, `storage.tf`, `functions.tf`, `api_gateway.tf`

Always keep these files separate regardless of stack size:
- `variables.tf`, `outputs.tf`, `terraform.tf`, `providers.tf`, `locals.tf`

## Provider Configuration Rules

### OCI Provider — API Key Auth (Solo Developer)
- Credentials via environment variables (`TF_VAR_tenancy_ocid`, etc.) or OCI CLI config file (`~/.oci/config`)
- NEVER hardcode credentials in `.tf` files

### Multi-Region (Provider Aliases)
- Use `alias` attribute for multi-region deployments
- Pass aliased providers to modules via `providers = { oci = oci.phoenix }`

## Variable Files Strategy
- `.tfvars` files contain environment-specific values only
- Never put secrets in `.tfvars` files
- Use `TF_VAR_*` environment variables for sensitive values

## .gitignore Requirements

Every Terraform project MUST have a `.gitignore` covering:
- `.terraform/` directory
- `*.tfstate` and `*.tfstate.*` files
- `*.tfplan` files
- `.terraform.tfstate.lock.info`
- `crash.log` and `crash.*.log`
- `override.tf` and `*_override.tf` files
- `*.tfvars` (with `!*.tfvars.example` exception)
- `.terraformrc` and `terraform.rc`

## OCI Compartment Strategy

Use OCI's compartment hierarchy for blast radius isolation:
- Top-level: `workloads` compartment under tenancy
- Per-project: `<project-name>` under workloads
- Per-environment: `dev`, `staging`, `prod` under project
- Use `for_each = toset(["dev", "staging", "prod"])` for environment compartments
