---
name: naming-conventions
description: "Naming pattern enforcement for all .github/ artifacts — agents, prompts, skills, instructions."
applyTo: ".github/{agents/*.agent.md,prompts/*.prompt.md,skills/**,instructions/*.instructions.md}"
---

# Naming Conventions — .github/ Artifacts

All artifact names must be **kebab-case** (lowercase letters, numbers, hyphens only — no spaces,
no underscores, no PascalCase).

## Artifact naming patterns

| Artifact type | Pattern | Rationale |
|---|---|---|
| Skill folder | `gerund-noun` | Action-oriented — describes what the skill *does* |
| Agent file (base name) | `domain-role` | Identity-oriented — describes *who* the agent is |
| Prompt file (base name) | `verb-noun-qualifier` | Action-oriented — describes what the prompt triggers |
| Instruction file (base name) | `scope-noun` | Scope-oriented — describes what the instruction governs |

## ✅ Correct examples

| Type | Correct name | Why |
|---|---|---|
| Skill folder | `researching-technical-frameworks` | gerund + noun |
| Skill folder | `authoring-agent-skills` | gerund + noun |
| Agent | `framework-researcher` | domain + role |
| Agent | `skill-author` | domain + role |
| Prompt | `audit-architecture-scope` | verb-noun-qualifier |
| Prompt | `technical-framework-researcher` | verb-noun-qualifier |
| Instruction | `skill-frontmatter` | scope + noun |
| Instruction | `naming-conventions` | scope + noun |

## ❌ Incorrect examples

| Incorrect | Problem | Correct form |
|---|---|---|
| `ResearchFrameworks` | PascalCase not allowed | `researching-technical-frameworks` |
| `researcher_framework` | underscores not allowed | `framework-researcher` |
| `validate_skill` | underscores not allowed | `skill-best-practices-validator` |
| `SkillAuthor` | PascalCase not allowed | `skill-author` |

## Copilot-specific note

The file extension determines the artifact type — the name alone must disambiguate intent
within each type. Two files with the same base name but different extensions are distinct
artifacts and will be injected by different mechanisms (`applyTo:` vs routing via `agent:`).
Do not create same-name pairs unless they are intentionally related (e.g., a skill SKILL.md
and its corresponding `.prompt.md` entry point may share a base theme but not an identical name).
