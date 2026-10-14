---
name: engineering-terraform-oci
description: "Structures, configures, and governs Terraform v1.9 + oracle/oci ~> 8.x projects for OCI workloads. Use when designing project layout, module architecture, state management, CI/CD pipelines, or testing strategy for OCI infrastructure."
---

## Version Context

**Technology**: Terraform + oracle/oci Provider
**Target version**: Terraform v1.9 / oracle/oci ~> 8.15
**Research validated**: 2026-05-25
**Support status**: Active

**Important changes in this version**:
- `terraform test` parallel execution + `state_key` isolation added (v1.9)
- Declarative `import {}` block production-stable (v1.5+)
- `moved {}` block for safe refactoring without destroy/recreate
- OCI Object Storage backend (`backend "oci"`) natively supported — no DynamoDB equivalent

**Deprecated**:
- `terraform taint` — **removed**; use `terraform apply -replace="<address>"` instead
- Branch-per-environment — replaced by directory-per-environment

⚠️ **CRITICAL — Agent Warning**: This skill targets Terraform v1.9 + oracle/oci ~> 8.x. Do not apply patterns from Terraform < 1.5 or provider < 8.0.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Version pinning, OCI backend, lifecycle rules, tagging, validation
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Repo strategy, env isolation, module granularity, CI/CD tooling
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — State, secrets, apply safety, deprecated commands
- **[Integration Patterns](./blueprints/integration-patterns.md)** — OCI backend IAM, GitHub Actions, `terraform test`, OCI Vault
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 5 scenarios: module skeleton, backend init failure, state lock, moved block refactor, API key misuse
- **[Verification Loop](#verification-loop)** — fmt → validate → plan → apply gates
- **[Quick Reference](#quick-reference)** — Essential commands and limits

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **Pin Terraform + provider versions** — `required_version = "~> 1.9"` + `version = "~> 8.15"` in every root module; prevents silent breaking upgrades
- **OCI Object Storage backend** — never local backend for team environments; built-in locking via `If-None-Match: *`, no DynamoDB needed
- **Enable state bucket versioning** — `oci os bucket update --versioning Enabled`; enables recovery from state corruption
- **Validate all module inputs** — `validation {}` blocks on every variable; catches errors at `plan` time before any API calls
- **`prevent_destroy = true` on critical resources** — databases, prod VCNs, state buckets; blocks accidental `terraform destroy`
- **`common_tags` locals on every resource** — `Environment`, `Application`, `ManagedBy = "Terraform"`; required for OCI Cost Analysis attribution
- **Enforce `.gitignore`** — `*.tfstate`, `.terraform/`, `secrets.auto.tfvars`, `*.tfplan`; prevents credential and state exposure
- **`fmt -check` + `validate` in CI on every PR** — static gate; catches syntax and type errors before plan is allowed

### ⚠️ Ask First

For complete decision matrices, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Repository strategy** — Monorepo vs hybrid (shared modules + per-app repo) vs polyrepo; ask: "How many OCI apps share infrastructure patterns?"
- **Environment isolation** — Directory-per-environment vs workspaces vs Terragrunt; ask: "Do dev and prod have significantly different resource configs?"
- **Module granularity** — Infrastructure module vs thin wrapper vs single root; ask: "Do multiple apps follow the same infrastructure shape?"
- **Cross-stack references** — `terraform_remote_state` vs OCI provider data sources vs OCI Vault; ask: "Do non-Terraform tools also need the shared values?"
- **CI/CD tooling** — GitHub Actions vs Atlantis vs HCP Terraform; ask: "Is the CI runner hosted on OCI Compute (enabling InstancePrincipal)?"

### 🚫 Never Do

For complete anti-patterns with ❌/✅ examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

- **Hardcode OCI API keys in `.tf` files** — CRITICAL: credential exposure; use InstancePrincipal/env vars instead
- **Local backend for team environments** — CRITICAL: no locking → state corruption from concurrent applies
- **Commit `*.tfstate` to VCS** — CRITICAL: state contains secrets; use remote OCI backend
- **Apply without reviewing `terraform plan`** — CRITICAL: silent destructive changes reach production
- **`force-unlock` without confirming no active run** — HIGH: breaks safety net; verify lock holder first
- **`terraform taint`** — HIGH: removed in v1.x; use `terraform apply -replace="<address>"`
- **Branch-per-environment** — HIGH: state diverges; merges become destructive
- **Apply a stale plan file** — HIGH: regenerate plan immediately before every apply

---

## Integration Patterns

For complete code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

- **Terraform ↔ OCI Object Storage (Backend)** — `backend "oci" {}` partial config via `-backend-config`; IAM dynamic group policy required
- **Terraform ↔ OCI IAM (InstancePrincipal)** — credential-free CI/CD for OCI Compute runners; no API key rotation
- **Terraform ↔ GitHub Actions** — `hashicorp/setup-terraform@v3`; plan artifact uploaded for review; sanitized summary in PR comment
- **Terraform ↔ `terraform test`** — unit tests with `command = plan`, integration with `command = apply`; parallel isolation via `state_key`
- **Terraform ↔ OCI Vault** — `oci_secrets_secretbundle` data source for passwords/tokens; keeps secrets out of `.tfvars`

**Common problems**:
- `namespace` rejected in `backend "oci"` block → pass via `terraform init -backend-config="namespace=<value>"`
- `terraform taint` command not found → use `terraform apply -replace="<resource_address>"`
- Concurrent apply state lock stuck → verify no active CI run, then `terraform force-unlock <LOCK_ID>`

---

## Verification Loop

Run after every code generation cycle:

### 1. Format & Validate
```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
# Expected: "Success! The configuration is valid." | Exit code: 0
```

### 2. Static Security Analysis
```bash
checkov -d . --framework terraform --quiet
tflint --chdir=. --recursive
# Expected: passed checks > failed | Exit code: 0
```

### 3. Plan Review
```bash
terraform init
terraform plan -out=tfplan -lock=true -lock-timeout=60s
terraform show -no-color tfplan | grep -E "^(Plan:|  [+~-])"
# Expected: no "will be destroyed" or "forces replacement" surprises
```

### 4. State Validation (post-apply)
```bash
terraform state list
# Expected: resource count matches intent; all resources listed
```

**Troubleshooting**:
- `fmt -check` fails → run `terraform fmt -recursive` to auto-fix, then re-run check
- `validate` fails on unknown provider schema → run `terraform init -upgrade`
- Plan shows unexpected destroy → check `forces replacement` annotations; use `moved {}` block instead of rename

---

## Quick Reference

**Essential commands**:
```bash
terraform init -backend-config="namespace=<tenancy-ns>"  # partial config
terraform fmt -recursive && terraform validate
terraform plan -out=tfplan -var-file="terraform.tfvars"
terraform apply tfplan
terraform apply -replace="oci_core_instance.web"          # replaces taint
terraform state pull > backup-$(date +%Y%m%d).tfstate     # before state surgery
terraform test                                             # run *.tftest.hcl
```

**Critical decisions at a glance**:

| Concern | Recommended | Never |
|---------|-------------|-------|
| State backend | OCI Object Storage | Local backend for teams |
| Env isolation | Directory-per-environment | Shared state across envs |
| Module type | Infrastructure module (multi-resource) | Thin single-resource wrapper |
| Secrets in CI | InstancePrincipal / env vars | API keys in `.tf` files |
| Env config | `.tfvars` per environment | `terraform workspace` for config-different envs |
| Destroy protection | `lifecycle { prevent_destroy = true }` | No lifecycle on critical resources |

---

## Blueprints Directory Structure

```
.claude/skills/engineering-terraform-oci/
├── SKILL.md                         ← This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md        ← 8 mandatory patterns with code
    ├── ask-first-decisions.md       ← 5 decision matrices with tradeoff tables
    ├── never-do-patterns.md         ← 8 anti-patterns with ❌/✅ examples
    └── integration-patterns.md     ← OCI backend, GitHub Actions, terraform test, Vault
```

---

## External Resources

### Official Documentation
- [Terraform OCI Backend](https://developer.hashicorp.com/terraform/language/backend/oci) (verified 2026-07-26)
- [Terraform Style Guide](https://developer.hashicorp.com/terraform/language/style) (verified 2026-07-26)
- [Terraform Test Framework](https://developer.hashicorp.com/terraform/language/tests) (verified 2026-07-26)
- [Module Development](https://developer.hashicorp.com/terraform/language/modules/develop) (verified 2026-07-26)
- [import block](https://developer.hashicorp.com/terraform/language/import) (verified 2026-07-26)
- [moved block](https://developer.hashicorp.com/terraform/language/moved) (verified 2026-07-26)
- [oracle/oci Provider Registry](https://registry.terraform.io/providers/oracle/oci/latest/docs) (verified 2026-07-26)

### Security & Tooling
- [TFLint OCI ruleset](https://github.com/terraform-linters/tflint-ruleset-oci) (verified 2026-07-26)
- [Checkov OCI rules](https://www.checkov.io/5.Policy%20Index/terraform.html) (verified 2026-07-26)
- [Atlantis PR automation](https://www.runatlantis.io/docs) (verified 2026-07-26)
- [GitHub .gitignore for Terraform](https://github.com/github/gitignore/blob/main/Terraform.gitignore) (verified 2026-07-26)
