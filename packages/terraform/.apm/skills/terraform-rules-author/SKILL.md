---
name: terraform-rules-author
description: >
  Non-interactive compiler that takes a Terraform research file and target project context,
  then generates scoped Terraform rules/instruction files without an interactive interview.
  Use when a research file already exists and all context (Terraform version, cloud provider,
  target project path, platform) is known upfront — for example in a pipeline or batch
  authoring session. For the guided interactive interview path, use
  /terraform-instructions-compiler instead.
argument-hint: "<research-file-path> <project-root> [platform: claude-code|copilot]"
context: fork
agent: terraform-rules-author
disable-model-invocation: true
---

# Authoring Terraform Rules (non-interactive)

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier rules for this skill
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 scenarios: canonical, edge case, misuse rejection
- **[Agent](../../../.apm/agents/terraform-rules-author.agent.md)** — `terraform-rules-author` executor
- **[Standards Catalog](../terraform-instructions-compiler/assets/terraform-standards-reference.md)** — Terraform pattern catalog
- **[Interactive alternative](../terraform-instructions-compiler/SKILL.md)** — `terraform-instructions-compiler` (with interview)

## Blueprints & Guardrails

### ✅ Always Do

- **Supply all five required inputs** — `RESEARCH_FILE`, `TERRAFORM_VERSION`, `CLOUD_PROVIDER`,
  `PROJECT_ROOT`, `TARGET_PLATFORM`. The agent returns numbered questions and stops if any are
  missing; the generation never starts partially.
- **Point to an existing research file** — run `/terraform-engineering-best-practices-researcher`
  first if the file does not yet exist.
- **Specify `TARGET_PLATFORM` explicitly** — `claude-code` (output to `.claude/rules/`) or
  `copilot` (output to `.github/instructions/`). Never leave it ambiguous.

### ⚠️ Ask First

- **More than 5 instruction files would be generated** — the agent will list the planned files
  and ask for confirmation before proceeding. Review the plan before approving.
- **Conflicting version in research vs `TERRAFORM_VERSION`** — the agent flags version mismatches
  and waits for clarification; confirm which version to target.

### 🚫 Never Do

- **Do not skip the research file** — this skill is a compiler, not a generator. Without a
  research file there is no authoritative source for Terraform patterns.
  Alternative: run `/terraform-engineering-best-practices-researcher` first.
- **Do not use this skill for HCL authoring or Terraform execution** — it produces rules files
  only, not IaC code. A Terraform executor skill does not yet exist in this package.
- **Do not pass a stale research file** — files older than the active Terraform version should
  be re-researched. Source-date the research file and verify it targets the correct version.

## Usage

Pass inputs as arguments or inline in the message:

```
/terraform-rules-author \
  RESEARCH_FILE=workspace/research_terraform_v1.9.md \
  TERRAFORM_VERSION=1.9 \
  CLOUD_PROVIDER=OCI \
  PROJECT_ROOT=. \
  TARGET_PLATFORM=claude-code
```

Or by natural-language description:

> "Using `workspace/research_terraform_v1.9.md`, generate Claude Code rules for my OCI project
> at `/projects/infra` targeting Terraform 1.9."

## Output

- One mandatory `terraform-standards.md` file.
- Zero or more additional scoped instruction files (modules, state, CI/CD, testing, governance)
  based on the research file contents.
- A coverage matrix showing how each research section maps to an output file.
- A DONE / NEEDS-INPUT / PARTIAL status report.

## Related Skills

| Skill | When to use |
|---|---|
| `terraform-instructions-compiler` | Interactive interview — guided, confirms plan before generating |
| `terraform-engineering-best-practices-researcher` | Produce the research file this skill consumes |
| `technical-framework-researcher-terraform` | Research a specific Terraform topic or version |
