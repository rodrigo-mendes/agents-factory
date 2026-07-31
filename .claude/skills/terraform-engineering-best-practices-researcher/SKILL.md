---
name: terraform-engineering-best-practices-researcher
description: Researches Terraform engineering best practices (project layout, module design, CI/CD, testing, governance) into a source-backed knowledge base. Use when researching Terraform engineering practices for a skill or rules.
argument-hint: "<topic> (e.g. module-design, CI/CD, testing)"
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

---

## Quick Navigation

- **[Project & Modules](./blueprints/research-scope-project-modules.md)** — Repository layout, module types, interface, composition
- **[Environments & State](./blueprints/research-scope-environments-state.md)** — Isolation, backend, segmentation, recovery
- **[CI/CD & Testing](./blueprints/research-scope-cicd-testing.md)** — Pipeline architecture, test pyramid, native test framework
- **[Quality, Advanced & Governance](./blueprints/research-scope-quality-advanced-governance.md)** — Naming, DRY, multi-account, change control, compliance
- **[Output Template](./blueprints/output-format.md)** — Full research document structure
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 scenarios: canonical, edge case, misuse, anti-pattern trap
- **[External Resources](#external-resources)** — Official documentation this skill relies on

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
# Three-Tier Operational Guardrails Summary

## ✅ Always Do: Mandatory Patterns
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

## ⚠️ Ask First: Architectural Crossroads
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

## 🚫 Never Do: Forbidden Patterns
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

Output template (Metadata, Executive Summary, per-area sections, and Architectural Guardrails). Full structure in [Output Template](./blueprints/output-format.md).
## Reference Implementations
- [Official HashiCorp examples with URLs]
- [Community reference architectures (Cloud Posse, Gruntwork)]
- [Book recommendations with edition/chapter references]

## Source Bibliography
**Primary**: [Official docs, HashiCorp Learn, Registry with URLs and dates]
**Books**: [Title, Author, Edition, relevant chapters]
**Community**: [GitHub repos, blog posts with star counts and dates]
**All Deep-Links**: [Complete organized list]

## Completion Checklist
- [ ] All 9 research scope areas addressed
- [ ] 3+ code examples for mandatory patterns
- [ ] Every anti-pattern has a safe alternative
- [ ] Directory structure examples are complete and copy-pasteable
- [ ] Module examples include variables.tf, outputs.tf, main.tf
- [ ] CI/CD pipeline examples match {{TOOLING_PREFERENCES}}
- [ ] Testing examples use v{{TERRAFORM_VERSION}} features
- [ ] Sources dated and linked
- [ ] Recommendations calibrated for {{TEAM_SIZE}} and {{PROJECT_SCALE}}

## Research Gaps
```
Gap: [What's missing or uncertain]
Impact: [Effect on recommendations]
Workaround: [Temporary guidance]
Follow-up: [Where to verify]
```

## Agent Operation Notes
- **High Confidence**: [Patterns that can be applied without asking — official best practices]
- **Medium Confidence**: [Patterns that should be validated — community-adopted but not officially blessed]
- **Low Confidence**: [Patterns that must ask user — organizational, compliance, or preference-dependent]
- **Scale Sensitivity**: [Patterns that change based on team size / project scale]
- **Emergency Stop**: [When to halt — state corruption risk, security exposure, compliance violation]

---

# Output Priorities
1. 🚨 State corruption and security anti-patterns
2. ✅ Project organization mandatory patterns
3. ⚠️ Module design and composition decisions
4. 📈 CI/CD and testing automation
5. 🎯 Scale-appropriate governance patterns

## Verification Loop

Before finalizing:
1. Directory structures are complete and consistent
2. Module examples follow Registry standards
3. CI/CD pipelines are syntactically valid
4. All HCL examples pass `terraform fmt` conventions
5. Every Never Do entry has ❌ wrong / ✅ correct side-by-side (not prose only)
6. Anti-patterns include severity ratings
7. Recommendations are proportional to `{{TEAM_SIZE}}` and `{{PROJECT_SCALE}}`
8. All sources are dated and version-specific to v`{{TERRAFORM_VERSION}}`

```bash
# Confirm mandatory output sections are present
grep -E "^## (Mandatory_Patterns|Conditional_Patterns|Forbidden_Patterns|Agent_Operation_Notes|Source_Bibliography)" \
  research_Terraform_Engineering_*.md
# Expected: section headers appear in the research output file

# Confirm every Never-Do entry has a correct alternative
grep -c "✅ Correct" research_Terraform_Engineering_*.md
# Expected: count equals or exceeds the number of anti-pattern entries

# Confirm version specificity throughout the document
grep -c "v{{TERRAFORM_VERSION}}\|v1\.[0-9]" research_Terraform_Engineering_*.md
# Expected: multiple version references distributed across sections, not only in the header
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
