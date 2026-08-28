---
name: terraform-engineering-best-practices-researcher
description: Researches Terraform engineering best practices (project layout, module design, CI/CD, testing, governance) into a source-backed knowledge base. Use when researching Terraform engineering practices for a skill or rules.
argument-hint: "<topic> [depth=exhaustive] [iterations=5] (e.g. module-design depth=deep iterations=3)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# INPUT VARIABLES
- `TERRAFORM_VERSION`: [e.g., "1.8", "1.9", "1.10"]
- `CLOUD_PROVIDER`: [e.g., "AWS", "OCI", "Azure", "GCP", "Multi-Cloud"]
- `TEAM_SIZE`: [e.g., "solo", "small (2-5)", "medium (5-15)", "large (15+)"]
- `PROJECT_SCALE`: [e.g., "single-app", "multi-app", "platform-team", "enterprise"]
- `ENVIRONMENT_COUNT`: [e.g., "dev/prod", "dev/staging/prod", "dev/qa/staging/prod + per-tenant"]
- `TOOLING_PREFERENCES`: [optional — e.g., "Terragrunt", "Terraform Stacks", "Terraform Cloud", "Spacelift", "Atlantis", "GitHub Actions", "GitLab CI"]
- `COMPLIANCE_REQUIREMENTS`: [optional — e.g., "SOC2", "HIPAA", "PCI-DSS", "LGPD", "internal-policy-only"]
- `OFFICIAL_URL_IF_KNOWN`: [optional — e.g., "https://developer.hashicorp.com/terraform"]
- `RESEARCH_DEPTH`: research strategy — `quick` | `standard` | `deep` | `exhaustive` (default: **exhaustive**)
- `MAX_ITERATIONS`: gap-filling loop limit — any positive integer (default: **5**; ignored when depth=quick)

---

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Mandatory patterns, decisions, anti-patterns
- **[Project & Modules](./blueprints/research-scope-project-modules.md)** — Repository layout, module types, interface, composition
- **[Environments & State](./blueprints/research-scope-environments-state.md)** — Isolation, backend, segmentation, recovery
- **[CI/CD & Testing](./blueprints/research-scope-cicd-testing.md)** — Pipeline architecture, test pyramid, native test framework
- **[Quality, Advanced & Governance](./blueprints/research-scope-quality-advanced-governance.md)** — Naming, DRY, multi-account, change control, compliance
- **[Output Template](./blueprints/output-format.md)** — Full research document structure
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 scenarios: canonical, edge case, misuse, anti-pattern trap
- **[Verification Loop](#verification-loop)** — Gap-filling loop and post-research checklist
- **[External Resources](#external-resources)** — Official documentation this skill relies on

---

## Blueprints & Guardrails

### ✅ Always Do — Summary
- Pin Terraform and provider versions
- Use remote state with locking and encryption
- Validate inputs with variable validation blocks
- Run `terraform fmt` and `terraform validate` in CI
- Tag all resources with ownership and environment
- Never commit secrets to version control
- Use `.gitignore` for `.terraform/`, `*.tfstate`, `*.tfvars` with secrets
- Review `terraform plan` before every apply
- Use `prevent_destroy` lifecycle for critical resources
- Document module interfaces (variables, outputs, README)

### ⚠️ Ask First — Summary
- Monorepo vs. polyrepo vs. hybrid
- Workspaces vs. directory-per-env vs. Terragrunt
- Flat vs. layered vs. domain-driven directory structure
- Native `terraform test` vs. terratest
- Terraform Cloud vs. self-hosted CI/CD
- Module granularity (resource-level vs. stack-level)
- Remote state references vs. data sources for cross-stack
- `count` vs. `for_each` for conditional resources
- **Research depth** — if the user does not specify `depth=`, ask whether they need quick validation, standard coverage, deep analysis, or exhaustive research before starting

### 🚫 Never Do — Summary
- Hardcoded credentials in `.tf` files
- Local state in shared/team environments
- Unencrypted state backends
- `terraform apply` without prior `terraform plan` review
- Force-unlock without understanding the lock holder
- Manual resource changes without importing to state
- Branch-per-environment strategy (state divergence risk)
- Committing `.tfstate` files to version control
- Using `terraform taint` (deprecated — use `-replace`)
- Skipping CI/CD validation steps (`--no-verify` equivalents)
- Applying plan files generated from a different code version

> Full details in [Three-Tier Operational Guardrails Summary](#three-tier-operational-guardrails-summary)

---

# Role & Mission

Senior Infrastructure Engineer & AI Safety Architect building a hallucination-proof knowledge base for **Terraform v{{TERRAFORM_VERSION}} engineering best practices** — covering project organization, module design, environment strategy, CI/CD pipelines, testing, governance, and team collaboration patterns for **{{CLOUD_PROVIDER}}** workloads at **{{PROJECT_SCALE}}** scale with **{{TEAM_SIZE}}** team.

## Core Principles
1. **Version Absolutism**: Only patterns valid for Terraform v{{TERRAFORM_VERSION}} — treat older patterns, deprecated features, and sunset commands as misinformation
2. **Source Hierarchy**: HashiCorp Official Docs > Terraform Registry Best Practices > HashiCorp Blog/Learn > Recognized IaC Books (Brikman, Morris) > Verified Community (Terragrunt docs, Cloud Posse) > Reject All Else
3. **Pragmatic Engineering**: Recommend patterns proportional to team size and project scale — avoid over-engineering for small teams, avoid under-engineering for enterprises
4. **Safety First**: Prioritize state integrity, blast radius minimization, and change control over developer velocity
5. **Executable Truth**: Every recommendation must link to verifiable documentation or reproducible project structure
6. **Provider Awareness**: Patterns must account for {{CLOUD_PROVIDER}}-specific constraints (API rate limits, resource quotas, IAM models)

---

# Research Strategy

## Source Priority
1. Official HashiCorp documentation (https://developer.hashicorp.com/terraform)
2. Terraform Registry module design standards
3. HashiCorp Learn tutorials and recommended practices
4. "Terraform: Up & Running" (Yevgeniy Brikman) — latest edition for v{{TERRAFORM_VERSION}} patterns
5. "Infrastructure as Code" (Kief Morris) — patterns and practices
6. Cloud Posse reference architecture (https://github.com/cloudposse)
7. Gruntwork/Terragrunt documentation (if {{TOOLING_PREFERENCES}} includes Terragrunt)
8. Validate via GitHub issues, HashiCorp Discuss, and real-world production postmortems
9. Flag content older than 12 months — Terraform evolves rapidly
10. Conflict resolution: Official Docs → Learn → Books → Community → Reject

## Confidence Tiers
- **High Confidence (Autonomous)**: HashiCorp official recommendations, documented CLI behaviors, Registry module standards
- **Medium Confidence (Verify)**: Community patterns widely adopted (>1000 GitHub stars), book recommendations for current version
- **Low Confidence (Must ask user)**: Organizational governance choices, CI/CD platform selection, team workflow preferences, compliance-specific implementations

---

# Research Scope

## Research Scope §1–2 — Project Organization & Module Design

Repository/module layout, module types, interface definition, and composition patterns. Details in [Project & Modules](./blueprints/research-scope-project-modules.md).
## Research Scope §3–4 — Environment Management & State at Scale

Environment isolation, per-environment variables, backend configuration, state segmentation, and state recovery. Details in [Environments & State](./blueprints/research-scope-environments-state.md).
## Research Scope §5–6 — CI/CD Pipelines & Testing

Pipeline architecture and security, tooling, testing pyramid, native test framework, and policy-as-code. Details in [CI/CD & Testing](./blueprints/research-scope-cicd-testing.md).
## Research Scope §7–9 — Code Quality, Advanced Patterns & Governance

Naming, DRY, code review; multi-account/scale/refactoring; change control, compliance-as-code, and documentation. Details in [Quality, Advanced & Governance](./blueprints/research-scope-quality-advanced-governance.md).
## Three-Tier Operational Guardrails Summary

### ✅ Always Do: Mandatory Patterns
Non-negotiable practices regardless of scale:
- Pin Terraform and provider versions
- Use remote state with locking and encryption
- Validate inputs with variable validation blocks
- Run `terraform fmt` and `terraform validate` in CI
- Tag all resources with ownership and environment
- Never commit secrets to version control
- Use `.gitignore` for `.terraform/`, `*.tfstate`, `*.tfvars` with secrets
- Review `terraform plan` before every apply
- Use `prevent_destroy` lifecycle for critical resources
- Document module interfaces (variables, outputs, README)

### ⚠️ Ask First: Architectural Crossroads
Valid patterns where choice depends on context:
- Monorepo vs. polyrepo vs. hybrid
- Workspaces vs. directory-per-env vs. Terragrunt
- Flat vs. layered vs. domain-driven directory structure
- Native `terraform test` vs. terratest
- Terraform Cloud vs. self-hosted CI/CD
- Module granularity (resource-level vs. stack-level)
- Remote state references vs. data sources for cross-stack
- `count` vs. `for_each` for conditional resources

**Format**:
```
Decision: [What to choose]
Options: [A, B, C]
Tradeoffs:
  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
Agent: "Ask user: [specific decision question]"
Source: [Link]
```

### 🚫 Never Do: Forbidden Patterns
Anti-patterns that cause state corruption, security breaches, or operational failures:
- Hardcoded credentials in `.tf` files
- Local state in shared/team environments
- Unencrypted state backends
- `terraform apply` without prior `terraform plan` review
- Force-unlock without understanding the lock holder
- Manual resource changes without importing to state
- Branch-per-environment strategy (state divergence risk)
- Committing `.tfstate` files to version control
- Using `terraform taint` (deprecated — use `-replace`)
- Skipping CI/CD validation steps (`--no-verify` equivalents)
- Applying plan files generated from a different code version

**Format**:
```
Anti-Pattern: [What NOT to do]
Why: [Security | State corruption | Operational risk]
❌ Wrong:
  [Bad HCL, bad CLI invocation, or bad CI config — concrete artifact, not prose]
✅ Correct:
  [Right HCL, CLI invocation, or CI config with brief explanation]
Impact: [What breaks]
Severity: [CRITICAL | HIGH | MEDIUM]
Source: [Link]
```

> Every Never Do entry **must** include a side-by-side ❌ wrong / ✅ correct example. For
> workflow anti-patterns (e.g., apply without plan, force-unlock misuse), use concrete CLI
> commands or CI YAML snippets rather than prose-only prohibitions.

---

# Output Format

Full template: [Output Template](./blueprints/output-format.md).

> **MANDATORY OUTPUT FORMAT — ASSEMBLY SEQUENCE:**
> 1. Open `./blueprints/output-format.md` and copy the skeleton (all section headings, sub-headings, and placeholder markers) into the output file **before** populating content.
> 2. Populate each section from research findings. Do not deviate from heading names or order.
> 3. The 20 required sections in order — if any is absent, the output is **incomplete**:

| # | Exact heading | Minimum content |
|---|---|---|
| 1 | `## Metadata` | yaml block with all 9 fields |
| 2 | `## Executive Summary` | 3 paragraphs: landscape, key recommendations, critical patterns |
| 3 | `## Project Organization` | repository strategy, directory layout, file conventions |
| 4 | `## Module Architecture` | module types, interface design, composition, versioning |
| 5 | `## Environment Strategy` | isolation patterns, variable management |
| 6 | `## State Management` | backend strategy, isolation, operations |
| 7 | `## CI/CD Pipeline` | pipeline architecture, security, tooling |
| 8 | `## Testing Strategy` | testing pyramid, native tests, policy-as-code |
| 9 | `## Code Quality & Standards` | naming, DRY patterns, code review |
| 10 | `## Advanced Patterns` | multi-account, scale, refactoring *(conditional: enterprise/platform-team only)* |
| 11 | `## Governance & Compliance` | change control, compliance-as-code *(conditional: when COMPLIANCE_REQUIREMENTS specified)* |
| 12 | `## Architectural Guardrails` → `### ✅ Mandatory Patterns` | ≥3 patterns with ❌/✅ code examples |
| 13 | `## Architectural Guardrails` → `### ⚠️ Conditional Patterns` | ≥2 decision matrices |
| 14 | `## Architectural Guardrails` → `### 🚫 Forbidden Patterns` | ≥3 anti-patterns with severity rating + ❌/✅ side-by-side |
| 15 | `## Reference Implementations` | official HashiCorp + community reference architectures with URLs |
| 16 | `## Source Bibliography` | Primary/Books/Community sources with dates |
| 17 | `## Completion Checklist` | all 9 research scope areas + per-team-size calibration |
| 18 | `## Research Gaps` | Gap/Impact/Workaround/Follow-up per unresolved item |
| 19 | `## Agent Operation Notes` | High/Medium/Low Confidence + Scale Sensitivity + Emergency Stop |
| 20 | `## Research Iteration Changelog` | table with Iteration/Section/Item/Action/Source; one row per gap-loop resolution (omit for depth=quick) |

---

# Output Priorities
1. 🚨 State corruption and security anti-patterns
2. ✅ Project organization mandatory patterns
3. ⚠️ Module design and composition decisions
4. 📈 CI/CD and testing automation
5. 🎯 Scale-appropriate governance patterns

## Verification Loop

### Gap-Filling Loop (repeat up to `MAX_ITERATIONS` times, skip when `depth=quick`)

1. Run the checklist below.
2. List every item that fails or is incomplete — these are **gaps**.
3. If gaps exist and iterations remain: research the missing items, fill them in the output, decrement iteration counter, repeat from step 1.
4. If no gaps remain or `MAX_ITERATIONS` is reached: proceed to output.

### Checklist

```
[ ] All 20 required output sections present (see Output Format table above)
[ ] Architectural Guardrails has all 3 subsections: ✅ Mandatory Patterns, ⚠️ Conditional Patterns, 🚫 Forbidden Patterns
[ ] Every 🚫 Forbidden Pattern has ❌ wrong / ✅ correct side-by-side (not prose only)
[ ] Every 🚫 Forbidden Pattern has a severity rating
[ ] Directory structures are complete and consistent (copy-pasteable)
[ ] Module examples follow Registry standards (variables.tf, outputs.tf, main.tf)
[ ] CI/CD pipelines are syntactically valid for {{TOOLING_PREFERENCES}}
[ ] All HCL examples pass `terraform fmt` conventions
[ ] Recommendations calibrated for {{TEAM_SIZE}} and {{PROJECT_SCALE}}
[ ] All sources are dated and version-specific to v{{TERRAFORM_VERSION}}
[ ] Research Iteration Changelog present and complete (skip for depth=quick)
```

```bash
# Confirm domain sections are present
grep -E "^## (Executive Summary|Project Organization|Module Architecture|Environment Strategy|State Management|CI/CD Pipeline|Testing Strategy|Code Quality)" \
  research_Terraform_Engineering_*.md
# Expected: all 8 domain section headers appear

# Confirm Architectural Guardrails subsections are present
grep -E "^### (✅ Mandatory Patterns|⚠️ Conditional Patterns|🚫 Forbidden Patterns)" \
  research_Terraform_Engineering_*.md
# Expected: all 3 subsection headers appear

# Confirm closing sections are present
grep -E "^## (Reference Implementations|Source Bibliography|Completion Checklist|Research Gaps|Agent Operation Notes)" \
  research_Terraform_Engineering_*.md
# Expected: all 5 closing section headers appear

# Confirm every Forbidden Pattern has a correct alternative
grep -c "✅ Correct\|# ✅\|# DO" research_Terraform_Engineering_*.md
# Expected: count equals or exceeds the number of Forbidden Pattern entries

# Confirm version specificity throughout the document
grep -c "v{{TERRAFORM_VERSION}}\|v1\.[0-9]" research_Terraform_Engineering_*.md
# Expected: multiple version references distributed across sections
```

---

## External Resources

### HashiCorp Official Documentation

- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)
- [Terraform CLI Documentation](https://developer.hashicorp.com/terraform/cli)
- [Terraform Best Practices Guide](https://developer.hashicorp.com/terraform/cloud-adopt/best-practices)
- [Terraform Registry — Module Standards](https://developer.hashicorp.com/terraform/registry/modules/publish)
- [Terraform native test framework](https://developer.hashicorp.com/terraform/language/tests)
- [HashiCorp Learn — Terraform](https://developer.hashicorp.com/terraform/tutorials)

### Recognized IaC Books (source tier: community-verified)

- "Terraform: Up & Running" — Yevgeniy Brikman (cite edition matching `{{TERRAFORM_VERSION}}`)
- "Infrastructure as Code" — Kief Morris (patterns and practices reference)

### Community Reference Architectures (source tier: verified community)

- [Cloud Posse reference architecture](https://github.com/cloudposse) — >1 k stars, actively maintained
- [Gruntwork / Terragrunt documentation](https://terragrunt.gruntwork.io/) — when `TOOLING_PREFERENCES` includes Terragrunt

### Static Analysis & Testing Tools

- [tfsec — security scanner](https://github.com/aquasecurity/tfsec)
- [tflint — Terraform linter](https://github.com/terraform-linters/tflint)
- [Checkov — policy-as-code](https://www.checkov.io/)
- [Terratest — Go testing framework](https://terratest.gruntwork.io/)
- [Infracost — cost estimation](https://www.infracost.io/)

### CI/CD Platform Docs (cite when `TOOLING_PREFERENCES` specifies them)

- [Atlantis — Terraform pull request automation](https://www.runatlantis.io/docs/)
- [Spacelift documentation](https://docs.spacelift.io/)
- [Terraform Cloud / HCP Terraform](https://developer.hashicorp.com/terraform/cloud-docs)

### Meta-Skills

- [skill-creator SKILL.md](../skill-creator/SKILL.md) — Three-tier pattern conventions
- [researching-technical-frameworks SKILL.md](../researching-technical-frameworks/SKILL.md) — Anti-hallucination research methodology
