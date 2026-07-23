---
name: terraform-instructions-compiler
description: Interactive compiler that extracts Terraform best practices from a research file, interviews the user, and compiles targeted rules/instruction files. Use when turning Terraform research into scoped rules.
context: fork
agent: skill-author
disable-model-invocation: true
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
PROJECT_ROOT:           # Where to place output files
TARGET_PLATFORM:        # claude-code -> .claude/rules/*.md | copilot -> .github/instructions/*.instructions.md
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

Read the three instruction templates from `.claude/templates/instructions/`:
- `TEMPLATE.STANDARDS.md`
- `TEMPLATE.CONFIG.md`
- `TEMPLATE.SKILLS.md`

Understand the three template types and their purposes:
- **STANDARDS** → Code quality, naming, structure rules (applies to `*.tf` files)
- **CONFIG** → Project configuration, backend, provider setup (applies to config files)
- **SKILLS** → Skill integration and prompt routing (applies to all Terraform files)

---

### Phase 2: User Interview (REQUIRED)

Roteiro completo de entrevista (perguntas por área: estrutura, ambientes, backend, módulos, CI/CD, testes, compliance) para coletar o contexto do projeto. Perguntas em [Interview Questions](./blueprints/interview-questions.md).
### Phase 3: Planning (REQUIRED)

Based on the interview answers, generate a **plan** before creating any files. The plan MUST be presented to the user for approval.

#### 3.1 — Determine Instruction Files to Generate

Evaluate which instruction files are needed based on answers:

| Instruction File | When to Generate | applyTo Pattern |
|---|---|---|
| `terraform-standards.md` | **Always** — core coding standards | `**/*.tf` |
| `terraform-project-config.md` | When Q1-Q3 have specific answers | `**/{*.tf,*.tfvars,.terraform.lock.hcl}` |
| `terraform-modules.instructions.md` | When Q4-Q6 indicate module usage | `**/modules/**/*.tf` |
| `terraform-state-backend.instructions.md` | When Q7-Q8 have specific answers | `**/{backend.tf,versions.tf,terraform.tf}` |
| `terraform-cicd.instructions.md` | When Q9-Q11 have specific answers | `**/{.github/workflows/*.yml,.gitlab-ci.yml,atlantis.yaml}` |
| `terraform-testing.instructions.md` | When Q10 selects testing tools | `**/{*.tftest.hcl,*_test.go,policies/**}` |
| `terraform-governance.instructions.md` | When Q13 = compliance needed | `**/*.tf` |
| `terraform-skills.md` | When Q15-Q16 indicate existing skills | `**/*.tf` |

#### 3.2 — Present Plan to User

Present the plan in this format:

```
📋 INSTRUCTION FILES PLAN

Based on your answers, I will generate the following instruction files:

┌─────────────────────────────────────────────────────────────┐
│ #  │ File                                  │ Scope          │
├─────────────────────────────────────────────────────────────┤
│ 1  │ terraform-standards.md   │ All .tf files  │
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
Location: {{PROJECT_ROOT}}/.claude/rules/ (Claude Code) or {{PROJECT_ROOT}}/.github/instructions/ (Copilot)

Proceed with generation? (yes / adjust plan)
```

**Wait for user approval before proceeding to Phase 4.**

---

### Phase 4: Generate Instruction Files

For each planned file, follow the structure below. Use the appropriate template from `.claude/templates/instructions/` as the base.

#### 4.1 — terraform-standards.md (ALWAYS GENERATED)

```markdown
---
name: terraform-standards
description: Terraform v{{TERRAFORM_VERSION}} coding standards for {{CLOUD_PROVIDER}} — naming, structure, code quality, and mandatory patterns
applyTo: "**/*.tf"
---

You are a Terraform Code Quality specialist for {{CLOUD_PROVIDER}} infrastructure. 
Ensure all Terraform code follows v{{TERRAFORM_VERSION}} best practices for production readiness.

## Terraform Standards Reference

Catálogo de padrões que o compilador aplica: version constraints, organização de arquivos, naming, ✅/🚫, variáveis, módulos, state, pipelines, testes, segurança/compliance, tags e roteamento de skills. Referência completa em [Standards Reference](./blueprints/terraform-standards-reference.md).
### Phase 5: Validation (REQUIRED)

After generating all files, validate each instruction file:

#### 5.1 — Structure Validation
- [ ] YAML frontmatter has `name`, `description`, `applyTo`
- [ ] `description` clearly states what the instruction enforces
- [ ] `applyTo` glob pattern is correct and scoped appropriately
- [ ] File is saved to `{{PROJECT_ROOT}}/.claude/rules/` (Claude Code) or `.github/instructions/` (Copilot)

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
- [ ] ✅ All generated files follow template structure from `.claude/templates/instructions/`
- [ ] ✅ YAML frontmatter is valid in every file
- [ ] ✅ `applyTo` patterns don't overlap excessively between files
- [ ] ✅ No research patterns left uncovered (coverage matrix is complete)
- [ ] ✅ No hardcoded secrets or credentials in examples
- [ ] ✅ All code examples use {{TERRAFORM_VERSION}} syntax
- [ ] ✅ Cloud provider references match {{CLOUD_PROVIDER}}
- [ ] ✅ Each instruction file is self-contained (can be understood without other files)
- [ ] ✅ Conditional patterns resolved by user are converted to mandatory rules
- [ ] ✅ Files are placed in `{{PROJECT_ROOT}}/.claude/rules/` (Claude Code) or `.github/instructions/` (Copilot)

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
