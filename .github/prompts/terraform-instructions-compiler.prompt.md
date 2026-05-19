---
description: Interactive compiler that extracts Terraform best practices from research files, interviews the user about project context, and compiles targeted .instructions.md files for GitHub Copilot.
---

# Prompt: Terraform Best Practices → Instructions Compiler

## PURPOSE

This is an **extraction, planning, and generation prompt**. Given a Terraform best practices research file (produced by `terraform-engineering-best-practices-researcher.prompt.md` or equivalent), it:

1. **Interviews** the user about their project context and preferences
2. **Plans** which `.instructions.md` files to generate and their scope
3. **Generates** production-ready `.instructions.md` files following the template standards

The output is **NOT a document for humans to read** — it is a set of **operational instruction files for GitHub Copilot agents**, structured to enforce Terraform best practices during code generation.

---

## INPUT VARIABLES

```yaml
RESEARCH_FILE:          # Path to the Terraform best practices research file
                        # e.g., "agents_arch_doc/terraform/research_Terraform_Engineering_Best_Practices_v1.9.md"
TERRAFORM_VERSION:      # e.g., "1.8", "1.9", "1.10"
CLOUD_PROVIDER:         # e.g., "OCI", "AWS", "Azure", "GCP"
PROJECT_ROOT:           # Where to place .github/instructions/ files
                        # e.g., "." (current workspace) or a target project path
```

---

## Role
Copilot Configuration Architect & Senior Infrastructure Engineer specializing in Terraform IaC standards enforcement through GitHub Copilot custom instructions.

## Context
You have received a Terraform best practices research file. Your mission is to transform this research into actionable `.instructions.md` files that GitHub Copilot will use to enforce standards during Terraform code generation, review, and refactoring.

---

## Execution Workflow

### Phase 1: Load Research & Templates (REQUIRED)

#### Step 1.1: Load Research File

Read the research file at `{{RESEARCH_FILE}}` and extract and classify all findings into:
- ✅ Mandatory patterns → Will become `Always Do` rules in instructions
- ⚠️ Conditional patterns → Will become interview questions for the user
- 🚫 Forbidden patterns → Will become `Never Do` rules in instructions

#### Step 1.2: Load Instruction Templates

Read the three instruction templates from `.github/templates/instructions/`:
- `TEMPLATE.STANDARDS.instructions.md`
- `TEMPLATE.CONFIG.instructions.md`
- `TEMPLATE.SKILLS.instructions.md`

Understand the three template types and their purposes:
- **STANDARDS** → Code quality, naming, structure rules (applies to `*.tf` files)
- **CONFIG** → Project configuration, backend, provider setup (applies to config files)
- **SKILLS** → Skill integration and prompt routing (applies to all Terraform files)

---

### Phase 2: User Interview (REQUIRED)

Before planning instruction files, ask the user these questions to calibrate the output. Present ALL questions at once, grouped by category.

#### 2.1 — Project Structure Questions

```
📁 PROJECT STRUCTURE

Q1: How is your Terraform project organized?
   a) Monorepo — all infrastructure in one repository
   b) Polyrepo — separate repos per service/environment
   c) Hybrid — shared modules repo + deployment repos
   d) Not decided yet — recommend best option for my context

Q2: How do you separate environments (dev/staging/prod)?
   a) Directory per environment (environments/dev/, environments/prod/)
   b) Terraform workspaces
   c) Terragrunt with hierarchy
   d) Separate repos per environment
   e) Not decided yet — recommend based on team size

Q3: How do you organize files within a stack/module?
   a) Single main.tf (small stacks)
   b) Split by purpose (main.tf, variables.tf, outputs.tf, providers.tf)
   c) Split by resource type (network.tf, compute.tf, iam.tf, storage.tf)
   d) Follow whatever the research recommends
```

#### 2.2 — Module Strategy Questions

```
📦 MODULE DESIGN

Q4: What is your module strategy?
   a) Resource modules — thin wrappers (1-3 resources per module)
   b) Infrastructure modules — composed stacks (networking, compute layers)
   c) Both — resource modules composed into infrastructure modules
   d) No modules yet — inline resources only
   e) Not decided — recommend based on project scale

Q5: Where do you source modules from?
   a) Local paths only (./modules/)
   b) Private Git repos with version tags
   c) Terraform Registry (public or private)
   d) Mix of sources
   e) Not decided yet

Q6: How strict is your module versioning?
   a) Exact pinning (version = "1.2.3")
   b) Pessimistic constraint (version = "~> 1.2")
   c) Range constraint (version = ">= 1.0, < 2.0")
   d) No versioning yet
```

#### 2.3 — State & Backend Questions

```
🔒 STATE MANAGEMENT

Q7: What backend do you use for Terraform state?
   a) S3 + DynamoDB (AWS)
   b) OCI Object Storage
   c) Azure Blob Storage
   d) GCS (Google Cloud Storage)
   e) Terraform Cloud / Enterprise
   f) Local state (development only)
   g) Not decided yet — recommend for {{CLOUD_PROVIDER}}

Q8: How do you isolate state files?
   a) One state per environment (dev.tfstate, prod.tfstate)
   b) One state per component × environment
   c) One state per service/domain
   d) Monolithic state (everything in one)
   e) Not decided yet
```

#### 2.4 — CI/CD & Testing Questions

```
🔄 CI/CD & TESTING

Q9: What CI/CD platform do you use for Terraform?
   a) GitHub Actions
   b) GitLab CI
   c) Terraform Cloud / Enterprise
   d) Atlantis
   e) Spacelift / env0
   f) Jenkins
   g) None yet — recommend one
   h) Other: ___

Q10: What testing tools do you use or want to adopt?
   a) terraform validate + terraform fmt only
   b) tflint
   c) tfsec / Trivy
   d) Checkov
   e) OPA / Conftest
   f) terraform test (native)
   g) Terratest (Go)
   h) None yet — recommend a testing stack
   (Select all that apply)

Q11: Do you enforce policy-as-code?
   a) Yes — OPA/Rego
   b) Yes — Sentinel (Terraform Cloud)
   c) Yes — Checkov custom policies
   d) No — but I want to start
   e) No — not needed for now
```

#### 2.5 — Team & Governance Questions

```
👥 TEAM & GOVERNANCE

Q12: What is your team size for Terraform work?
   a) Solo developer
   b) Small team (2-5)
   c) Medium team (5-15)
   d) Large / platform team (15+)

Q13: Do you need compliance enforcement?
   a) Yes — specific standards (SOC2, HIPAA, PCI-DSS, LGPD)
   b) Yes — internal policies only
   c) No — general best practices are enough

Q14: Do you use terraform-docs for module documentation?
   a) Yes — auto-generated README.md
   b) No — manual documentation
   c) No documentation yet — I want to start
```

#### 2.6 — Existing Skills & Integrations

```
🔗 EXISTING ECOSYSTEM

Q15: Do you have existing Terraform skills in .github/skills/?
   a) Yes — I have provider-specific skills (list them)
   b) No — this will be my first Terraform instructions
   c) I have the research file but no skills yet

Q16: Do you want the instructions to route to specialized prompts?
   a) Yes — integrate with existing prompts in .github/prompts/
   b) No — standalone instructions are enough
   c) Yes — but I need to create the prompts first
```

---

### Phase 3: Planning (REQUIRED)

Based on the interview answers, generate a **plan** before creating any files. The plan MUST be presented to the user for approval.

#### 3.1 — Determine Instruction Files to Generate

Evaluate which instruction files are needed based on answers:

| Instruction File | When to Generate | applyTo Pattern |
|---|---|---|
| `terraform-standards.instructions.md` | **Always** — core coding standards | `**/*.tf` |
| `terraform-project-config.instructions.md` | When Q1-Q3 have specific answers | `**/{*.tf,*.tfvars,.terraform.lock.hcl}` |
| `terraform-modules.instructions.md` | When Q4-Q6 indicate module usage | `**/modules/**/*.tf` |
| `terraform-state-backend.instructions.md` | When Q7-Q8 have specific answers | `**/{backend.tf,versions.tf,terraform.tf}` |
| `terraform-cicd.instructions.md` | When Q9-Q11 have specific answers | `**/{.github/workflows/*.yml,.gitlab-ci.yml,atlantis.yaml}` |
| `terraform-testing.instructions.md` | When Q10 selects testing tools | `**/{*.tftest.hcl,*_test.go,policies/**}` |
| `terraform-governance.instructions.md` | When Q13 = compliance needed | `**/*.tf` |
| `terraform-skills.instructions.md` | When Q15-Q16 indicate existing skills | `**/*.tf` |

#### 3.2 — Present Plan to User

Present the plan in this format:

```
📋 INSTRUCTION FILES PLAN

Based on your answers, I will generate the following instruction files:

┌─────────────────────────────────────────────────────────────┐
│ #  │ File                                  │ Scope          │
├─────────────────────────────────────────────────────────────┤
│ 1  │ terraform-standards.instructions.md   │ All .tf files  │
│    │ → Naming, file structure, code quality │                │
├─────────────────────────────────────────────────────────────┤
│ 2  │ terraform-modules.instructions.md     │ modules/**     │
│    │ → Module design, interface, versioning │                │
├─────────────────────────────────────────────────────────────┤
│ ...│ ...                                    │ ...            │
└─────────────────────────────────────────────────────────────┘

Each file will enforce:
  ✅ [N] mandatory patterns
  ⚠️ [N] conditional patterns (resolved by your answers)
  🚫 [N] forbidden patterns

Total files: [N]
Location: {{PROJECT_ROOT}}/.github/instructions/

Proceed with generation? (yes / adjust plan)
```

**Wait for user approval before proceeding to Phase 4.**

---

### Phase 4: Generate Instruction Files

For each planned file, follow the structure below. Use the appropriate template from `.github/templates/instructions/` as the base.

#### 4.1 — terraform-standards.instructions.md (ALWAYS GENERATED)

```markdown
---
name: terraform-standards
description: Terraform v{{TERRAFORM_VERSION}} coding standards for {{CLOUD_PROVIDER}} — naming, structure, code quality, and mandatory patterns
applyTo: "**/*.tf"
---

You are a Terraform Code Quality specialist for {{CLOUD_PROVIDER}} infrastructure. 
Ensure all Terraform code follows v{{TERRAFORM_VERSION}} best practices for production readiness.

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

#### 4.2 — terraform-project-config.instructions.md

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

#### 4.8 — terraform-skills.instructions.md (CONDITIONAL)

```markdown
---
name: terraform-skills
description: Integrates Terraform skills from .github/skills/ for {{CLOUD_PROVIDER}} infrastructure development
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

### Phase 5: Validation (REQUIRED)

After generating all files, validate each instruction file:

#### 5.1 — Structure Validation
- [ ] YAML frontmatter has `name`, `description`, `applyTo`
- [ ] `description` clearly states what the instruction enforces
- [ ] `applyTo` glob pattern is correct and scoped appropriately
- [ ] File is saved to `{{PROJECT_ROOT}}/.github/instructions/`

#### 5.2 — Content Validation
- [ ] All ✅ patterns from research are covered across instruction files
- [ ] All 🚫 patterns from research are covered across instruction files
- [ ] ⚠️ patterns resolved by user answers are included as ✅ in the appropriate file
- [ ] ⚠️ patterns NOT resolved by user are documented with comments for future decision
- [ ] No duplication between instruction files — each concern lives in ONE file
- [ ] Version numbers match {{TERRAFORM_VERSION}} throughout
- [ ] Cloud provider specifics match {{CLOUD_PROVIDER}} throughout

#### 5.3 — Coverage Matrix
Present a final coverage matrix to the user:

```
📊 COVERAGE MATRIX

Research Section                    → Instruction File
─────────────────────────────────────────────────────
1. Project Organization             → terraform-project-config
2. Module Architecture              → terraform-modules
3. Environment Strategy             → terraform-project-config
4. State Management                 → terraform-state-backend
5. CI/CD Pipelines                  → terraform-cicd
6. Testing Strategy                 → terraform-testing
7. Code Quality & Standards         → terraform-standards
8. Advanced Patterns (if needed)    → terraform-governance / terraform-standards
9. Governance & Compliance          → terraform-governance

Mandatory Patterns (✅):  [N] covered / [N] total from research
Forbidden Patterns (🚫):  [N] covered / [N] total from research
Conditional Resolved (⚠️→✅): [N] resolved by interview
Conditional Pending (⚠️):     [N] deferred (user didn't decide)
```

---

## Quality Gates (Final Checklist)

Before delivering output:
- [ ] ✅ Research file was fully loaded and parsed
- [ ] ✅ User interview completed (all 16 questions answered)
- [ ] ✅ Plan was approved by user before generation
- [ ] ✅ All generated files follow template structure from `.github/templates/instructions/`
- [ ] ✅ YAML frontmatter is valid in every file
- [ ] ✅ `applyTo` patterns don't overlap excessively between files
- [ ] ✅ No research patterns left uncovered (coverage matrix is complete)
- [ ] ✅ No hardcoded secrets or credentials in examples
- [ ] ✅ All code examples use {{TERRAFORM_VERSION}} syntax
- [ ] ✅ Cloud provider references match {{CLOUD_PROVIDER}}
- [ ] ✅ Each instruction file is self-contained (can be understood without other files)
- [ ] ✅ Conditional patterns resolved by user are converted to mandatory rules
- [ ] ✅ Files are placed in `{{PROJECT_ROOT}}/.github/instructions/`

---

## Output Priorities
1. 🚨 Security and state safety rules (always in terraform-standards)
2. ✅ Core coding standards (terraform-standards — always generated)
3. 📁 Project structure (terraform-project-config)
4. 📦 Module design (terraform-modules)
5. 🔒 State management (terraform-state-backend)
6. 🔄 CI/CD enforcement (terraform-cicd)
7. 🧪 Testing standards (terraform-testing)
8. 📋 Governance (terraform-governance — conditional)
9. 🔗 Skill routing (terraform-skills — conditional)

---

## Error Handling

### If Research File Is Missing
```
"No research file found at {{RESEARCH_FILE}}.

To generate one, use the prompt:
  /terraform-engineering-best-practices-researcher

With variables:
  TERRAFORM_VERSION: {{TERRAFORM_VERSION}}
  CLOUD_PROVIDER: {{CLOUD_PROVIDER}}

Then re-run this prompt with the generated research file."
```

### If User Skips Questions
For any unanswered question, use the research file's recommended default and add a comment in the generated instruction:
```markdown
<!-- TODO: This pattern was auto-selected from research defaults.
     Review and adjust for your specific context.
     Original question: [Q text] -->
```

### If Templates Are Missing
Generate instruction files using the patterns documented in this prompt directly. The templates are preferred but not required.
