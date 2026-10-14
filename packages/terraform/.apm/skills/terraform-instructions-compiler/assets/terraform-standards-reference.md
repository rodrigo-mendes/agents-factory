# Terraform Standards Reference (catalog)

## Version Constraints
- Terraform: v{{TERRAFORM_VERSION}}+
- Provider: [from research — e.g., hashicorp/oci ~> 6.x]
- ALWAYS include terraform {} block with required_version and required_providers

## File Organization Standards
[Extract from research — Section 1.3: File Organization]
- [File naming conventions]
- [When to split files]
- [Standard file set per stack]

## Naming Conventions
[Extract from research — Section 7.1: Naming Conventions]
- Resources: [pattern]
- Variables: [pattern]
- Outputs: [pattern]
- Locals: [pattern]
- Tags: [pattern]

## ✅ Always Do
[Extract all mandatory patterns from research]

## 🚫 Never Do
[Extract all forbidden patterns from research]

## Variable Design
[Extract from research — Section 2.2: Module Interface Design]
- Type constraints
- Validation blocks
- Sensitive handling
- Default values

## Code Review Checklist
[Extract from research — Section 7.3]
```

#### 4.2 — terraform-project-config.md

```markdown
---
name: terraform-project-config
description: Terraform project configuration standards for {{CLOUD_PROVIDER}} — directory layout, backend, provider setup
applyTo: "**/{*.tf,*.tfvars,.terraform.lock.hcl}"
---

## Project Structure
[Based on Q1 answer — monorepo/polyrepo/hybrid with directory tree]

## Environment Strategy
[Based on Q2 answer — specific strategy with examples]

## Backend Configuration
[Based on Q7 answer — exact backend block template]

## Provider Configuration
[Based on research — provider block with auth pattern]

## Variable Files Strategy
[Based on Q2+Q3 — .tfvars organization]

## .gitignore Requirements
[Standard Terraform .gitignore patterns]
```

#### 4.3 — terraform-modules.instructions.md

```markdown
---
name: terraform-modules
description: Terraform module design standards — structure, interface, composition, versioning
applyTo: "**/modules/**/*.tf"
---

## Module Types & When to Use
[Based on Q4 — module type taxonomy]

## Standard Module Structure
[Required file layout with purpose of each file]

## Interface Design Rules
[Variable naming, validation, outputs]

## Module Sources & Versioning
[Based on Q5+Q6 — source strategy with version constraints]

## Composition Patterns
[How modules call other modules]

## Documentation Requirements
[Based on Q14 — terraform-docs integration or manual]
```

#### 4.4 — terraform-state-backend.instructions.md

```markdown
---
name: terraform-state-backend
description: Terraform state management standards — backend config, isolation, operations, recovery
applyTo: "**/{backend.tf,versions.tf,terraform.tf}"
---

## Backend Configuration
[Based on Q7 — exact backend block for chosen provider]

## State Isolation Strategy
[Based on Q8 — key structure, naming convention]

## State Operations Safety
[Import, move, remove procedures with safety checks]

## Disaster Recovery
[Backup, recovery, corruption handling]
```

#### 4.5 — terraform-cicd.instructions.md

```markdown
---
name: terraform-cicd
description: Terraform CI/CD pipeline standards for {{CI_CD_PLATFORM}}
applyTo: "**/{.github/workflows/*.yml,.gitlab-ci.yml,atlantis.yaml,Makefile}"
---

## Pipeline Architecture
[Based on Q9 — platform-specific pipeline template]

## Pipeline Stages
[Plan-on-PR, Apply-on-merge, drift detection]

## Credential Management
[OIDC/short-lived tokens for chosen platform]

## Plan Artifact Handling
[Security considerations for plan files]
```

#### 4.6 — terraform-testing.instructions.md

```markdown
---
name: terraform-testing
description: Terraform testing standards — validation, policy-as-code, unit and integration testing
applyTo: "**/{*.tftest.hcl,*_test.go,policies/**/*.rego}"
---

## Testing Pyramid
[Tiers based on Q10 selections]

## Static Analysis
[terraform fmt, validate, tflint configuration]

## Security Scanning
[Based on Q10 — tfsec/Trivy/Checkov config]

## Native Tests (terraform test)
[.tftest.hcl file structure and patterns]

## Policy-as-Code
[Based on Q11 — OPA/Sentinel/Checkov custom policies]
```

#### 4.7 — terraform-governance.instructions.md (CONDITIONAL)

```markdown
---
name: terraform-governance
description: Terraform governance and compliance standards for [compliance framework]
applyTo: "**/*.tf"
---

## Compliance Requirements
[Based on Q13 — specific framework rules]

## Mandatory Tags
[Required tags for compliance tracking]

## Encryption Enforcement
[At-rest and in-transit requirements]

## Access Control Patterns
[IAM least-privilege, network restrictions]

## Audit & Documentation
[ADRs, change control, approval workflows]
```

#### 4.8 — terraform-skills.md (CONDITIONAL)

```markdown
---
name: terraform-skills
description: Integrates Terraform skills from .claude/skills/ for {{CLOUD_PROVIDER}} infrastructure development
applyTo: "**/*.tf"
---

## ⚠️ Check Prompts First!
[Prompt routing table — based on Q16 + existing prompts]

## Skill Directory Mapping
[Based on Q15 — trigger keywords → skill files]

## Cross-Cutting Rules
[Rules that apply regardless of specific skill]
```

---
