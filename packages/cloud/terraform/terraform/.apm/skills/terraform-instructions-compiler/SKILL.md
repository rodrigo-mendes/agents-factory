---
name: terraform-instructions-compiler
description: Interactive compiler that extracts Terraform best practices from a research file, interviews the user, and compiles targeted rules/instruction files. Use when turning Terraform research into scoped rules.
argument-hint: "<research-file-path> (e.g. workspace/research_terraform_v1.5.md)"
context: fork
agent: artifact-author
disable-model-invocation: true
---
# Prompt: Terraform Best Practices → Instructions Compiler

## PURPOSE

This is an **extraction, planning, and generation prompt**. Given a Terraform best practices
research file (produced by `terraform-engineering-best-practices-researcher` or equivalent), it:

1. **Interviews** the user about their project context and preferences
2. **Plans** which instruction files to generate and their scope
3. **Generates** production-ready instruction files following the template standards

The output is **NOT a document for humans to read** — it is a set of operational instruction
files that enforce Terraform best practices during code generation, for whichever agent runtime
consumes them (Claude Code rules or Copilot instructions — see `TARGET_PLATFORM` below).

This skill is a **domain compiler**: it supplies Terraform-specific data (the file matrix below,
the pattern catalog, the interview script) to the generic 5-phase engine in
[`../rules-compiler/SKILL.md`](../rules-compiler/SKILL.md). It follows
[domain-compiler-contract.md](../rules-compiler/blueprints/domain-compiler-contract.md). Adding a
new domain (Kubernetes, AWS, …) means writing a sibling skill under this same contract — not
extending this one.

---

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier rules for this compiler's own operation
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 scenarios: canonical path, edge case, misuse rejection, anti-pattern trap
- **[Interview Questions](./blueprints/interview-questions.md)** — Full interview script (Phase 2)
- **[Standards Reference](./assets/terraform-standards-reference.md)** — Terraform pattern catalog (Phase 4)
- **[Generic Engine](../rules-compiler/SKILL.md)** — the 5-phase workflow this skill follows
- **[Verification Loop](#verification-loop)** — Post-generation self-check
- **[External Resources](#external-resources)** — Reference links

---

## Blueprints & Guardrails

These rules govern this compiler's own operation (not the instruction files it generates).

### ✅ Always Do

- **Load the research file first** — Read `{{RESEARCH_FILE}}` completely before starting the interview. Classify all findings into ✅/⚠️/🚫 before presenting interview questions (see [rules-compiler Phase 1](../rules-compiler/SKILL.md#phase-1--load-research--templates)). A missing or unread research file must trigger the error-handling path, not a silent default.
- **Present the plan before generating** — After the interview, produce the full file plan and wait for explicit user approval before writing any instruction file. Never generate files speculatively.
- **Always generate `terraform-standards.md`** — This file is mandatory regardless of interview answers. It is the foundation for all other instruction files.
- **Produce the coverage matrix** — After generating all files, present the Phase 5 coverage matrix showing which research patterns map to which instruction files and how many remain pending.
- **Load the 3 generic templates from `rules-compiler`** — [`../rules-compiler/assets/`](../rules-compiler/assets/) holds `TEMPLATE.STANDARDS.md`, `TEMPLATE.CONFIG.md`, `TEMPLATE.SKILLS.md`; match each generated file to STANDARDS, CONFIG, or SKILLS as appropriate. Never copy these templates locally.
- **Validate each generated file** — Run [rules-compiler Phase 5](../rules-compiler/SKILL.md#phase-5--validation) for every file before delivering. Flag every failure; do not skip silently.
- **Place files by `TARGET_PLATFORM`** — `{{PROJECT_ROOT}}/.claude/rules/` for Claude Code (`paths:` frontmatter), `{{PROJECT_ROOT}}/.github/instructions/` for Copilot (`applyTo:` frontmatter). `TARGET_PLATFORM` only ever changes the output's format — never which template or which pattern catalog is used.
- **Scope `applyTo`/`paths` patterns precisely** — Never use `**/*` as the sole glob; each instruction file must target a specific file pattern relevant to its concern.

### ⚠️ Ask First

- **Number of instruction files** — When interview answers imply more than 5 instruction files, ask the user to confirm scope before proceeding. More files = more maintenance surface.
- **Overlapping patterns** — When two planned instruction files share a significant overlap in their glob patterns (e.g., both target `**/*.tf`), ask whether to merge them or document the precedence order explicitly.
- **Conditional patterns unresolved by interview** — When a ⚠️ conditional pattern from research was not resolved by the user's answers, ask whether to defer it with a `<!-- TODO -->` comment or to resolve it with the research default. Do not silently choose.
- **`TARGET_PLATFORM` mismatch** — When the user's project has both `.claude/` and `.github/` directories, ask which platform is the target before placing files.

### 🚫 Never Do

- **Never generate files without user approval of the plan** — Phase 3 plan must be approved before any file is written. ✅ Present the plan table and wait for "yes" or "adjust plan".
- **Never use `**/*` as the sole glob** — Overly broad patterns apply the instruction to unrelated files, causing noise. ✅ Use the specific patterns from the Phase 3 table (e.g., `**/*.tf`, `**/modules/**/*.tf`).
- **Never include secrets or credentials in code examples** — Even example values must use placeholder variables. ✅ Use `var.secret_value` or `TF_VAR_*` references in all examples.
- **Never mix Terraform version syntax** — Do not use `terraform 0.x` syntax in an instruction targeting `{{TERRAFORM_VERSION}} 1.x`. ✅ Every code example must use `{{TERRAFORM_VERSION}}` syntax only.
- **Never duplicate constraints across instruction files** — Each rule lives in exactly one file. ✅ If a rule appears in `terraform-standards.md`, it must not be repeated in `terraform-modules.instructions.md`.
- **Never skip the coverage matrix** — Deliver it even if all patterns are covered. ✅ The matrix is the user's receipt that research was fully consumed.
- **Never generate files if the research file is missing** — Display the error-handling message and stop. ✅ Prompt the user to run `/terraform-engineering-best-practices-researcher` first.

---

## INPUT VARIABLES

```yaml
RESEARCH_FILE:          # Path to the Terraform best practices research file
                        # e.g., "agents_arch_doc/terraform/research_Terraform_Engineering_Best_Practices_v1.9.md"
TERRAFORM_VERSION:      # e.g., "1.8", "1.9", "1.10"
CLOUD_PROVIDER:         # e.g., "OCI", "AWS", "Azure", "GCP"
PROJECT_ROOT:           # Where to place output files
TARGET_PLATFORM:        # claude-code -> .claude/rules/*.md (paths:) | copilot -> .github/instructions/*.instructions.md (applyTo:)
                        # e.g., "." (current workspace) or a target project path
```

---

## Role

Senior Infrastructure Engineer specializing in Terraform IaC standards enforcement. This skill's
identity is the **domain** (Terraform), not the runtime — it produces standards enforcement
content equally usable by a Claude Code rule or a Copilot instruction file; `TARGET_PLATFORM`
only selects the output dialect (see [rules-compiler Phase 4](../rules-compiler/SKILL.md#phase-4--generate)).

## Context

You have received a Terraform best practices research file. Your mission is to transform this
research into actionable instruction files that enforce standards during Terraform code
generation, review, and refactoring — regardless of which agent runtime will read them.

---

## Execution Workflow

This skill follows the generic engine in
[`../rules-compiler/SKILL.md`](../rules-compiler/SKILL.md). What's below is what's specific to
Terraform: the file matrix (Phase 3) and the pattern catalog reference (Phase 4). For the
mechanics that don't change per domain, see the engine's own phase sections.

### Phase 1: Load Research & Templates

Follow [rules-compiler Phase 1](../rules-compiler/SKILL.md#phase-1--load-research--templates).
Load the 3 generic templates from [`../rules-compiler/assets/`](../rules-compiler/assets/):
`TEMPLATE.STANDARDS.md`, `TEMPLATE.CONFIG.md`, `TEMPLATE.SKILLS.md`.

### Phase 2: User Interview (REQUIRED)

Full interview script (questions by area: structure, environments, backend, modules, CI/CD,
testing, compliance) is in [Interview Questions](./blueprints/interview-questions.md).

---

### Phase 3: Planning (REQUIRED)

Based on the interview answers, generate a **plan** before creating any files. The plan MUST be
presented to the user for approval — see [rules-compiler Phase 3](../rules-compiler/SKILL.md#phase-3--planning).

#### 3.1 — Determine Instruction Files to Generate (Terraform-specific matrix)

| Instruction File | When to Generate | Target Pattern |
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

> **MANDATORY OUTPUT FORMAT:** Always produce the final deliverable using the exact structure below. Never skip, reorder, or abbreviate any section.

Present the plan in this format:

```
INSTRUCTION FILES PLAN

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
  [N] mandatory patterns
  [N] conditional patterns (resolved by your answers)
  [N] forbidden patterns

Total files: [N]
Location: {{PROJECT_ROOT}}/.claude/rules/ (Claude Code) or {{PROJECT_ROOT}}/.github/instructions/ (Copilot)

Proceed with generation? (yes / adjust plan)
```

**Wait for user approval before proceeding to Phase 4.**

---

### Phase 4: Generate Instruction Files

Follow [rules-compiler Phase 4](../rules-compiler/SKILL.md#phase-4--generate). For each planned
file, pick the matching generic template (STANDARDS / CONFIG / SKILLS) and fill it with Terraform
data.

#### 4.1 — terraform-standards.md (ALWAYS GENERATED)

The `terraform-standards.md` file enforces Terraform v`{{TERRAFORM_VERSION}}` coding standards
for `{{CLOUD_PROVIDER}}`: version constraints, file organization, naming conventions, mandatory
and forbidden patterns, variable/output rules, module patterns, state management, CI/CD gates,
testing standards, security/compliance, tagging, and skill routing.

Pattern catalog reference: [Standards Reference](./assets/terraform-standards-reference.md)

---

### Phase 5: Validation (REQUIRED)

Follow [rules-compiler Phase 5](../rules-compiler/SKILL.md#phase-5--validation). Terraform-specific
additions to that checklist:

- [ ] Version numbers match `{{TERRAFORM_VERSION}}` throughout
- [ ] Cloud provider specifics match `{{CLOUD_PROVIDER}}` throughout

#### 5.3 — Coverage Matrix

> **MANDATORY OUTPUT FORMAT:** Always produce the final deliverable using the exact structure below. Never skip, reorder, or abbreviate any section.

Present a final coverage matrix to the user:

```
COVERAGE MATRIX

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

## Verification Loop

After generating all instruction files, the agent MUST verify:

```
[ ] terraform-standards.md was generated (always required)
[ ] Each generated file has valid frontmatter (name, description, paths:/applyTo:)
[ ] No glob is "**/*" without a more specific qualifier
[ ] No secrets or credential literals appear in any code example
[ ] All code examples use {{TERRAFORM_VERSION}} syntax (not 0.x patterns)
[ ] Coverage matrix delivered and shows 0 uncovered ✅ mandatory patterns
[ ] Coverage matrix delivered and shows 0 uncovered 🚫 forbidden patterns
[ ] Files placed in correct location for {{TARGET_PLATFORM}}
[ ] User approval of plan was received before Phase 4 execution
```

---

## Quality Gates (Final Checklist)

Before delivering output:
- [ ] Research file was fully loaded and parsed
- [ ] User interview completed (all applicable questions answered)
- [ ] Plan was approved by user before generation
- [ ] All generated files follow the generic templates in `../rules-compiler/assets/`
- [ ] Frontmatter is valid in every file
- [ ] Patterns don't overlap excessively between files
- [ ] No research patterns left uncovered (coverage matrix is complete)
- [ ] No hardcoded secrets or credentials in examples
- [ ] All code examples use `{{TERRAFORM_VERSION}}` syntax
- [ ] Cloud provider references match `{{CLOUD_PROVIDER}}`
- [ ] Each instruction file is self-contained (can be understood without other files)
- [ ] Conditional patterns resolved by user are converted to mandatory rules
- [ ] Files are placed in `{{PROJECT_ROOT}}/.claude/rules/` (Claude Code) or `.github/instructions/` (Copilot)

---

## Output Priorities
1. Security and state safety rules (always in terraform-standards)
2. Core coding standards (terraform-standards — always generated)
3. Project structure (terraform-project-config)
4. Module design (terraform-modules)
5. State management (terraform-state-backend)
6. CI/CD enforcement (terraform-cicd)
7. Testing standards (terraform-testing)
8. Governance (terraform-governance — conditional)
9. Skill routing (terraform-skills — conditional)

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

### If the Generic Templates Are Missing
Generate instruction files using the patterns documented in this prompt directly. The templates
in `../rules-compiler/assets/` are preferred but not required.

---

## External Resources

### Terraform Official Documentation
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language) — HashiCorp (current)
- [Terraform Registry](https://registry.terraform.io) — Provider and module registry
- [Terraform CLI Reference](https://developer.hashicorp.com/terraform/cli) — HashiCorp
- [Terraform Best Practices](https://developer.hashicorp.com/terraform/cloud-docs/recommended-practices) — HashiCorp recommended practices

### Generic Engine & Templates
- [rules-compiler](../rules-compiler/SKILL.md) — the 5-phase engine this skill follows
- [domain-compiler-contract.md](../rules-compiler/blueprints/domain-compiler-contract.md) — what a domain compiler must supply
- [skill-frontmatter rules](../../rules/skill-frontmatter.md) — YAML frontmatter requirements

### Research Generator
- Run `/terraform-engineering-best-practices-researcher` to generate the research file input
