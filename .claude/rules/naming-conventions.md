---
name: naming-conventions
description: "Naming convention rules for skills, agents, and rules in this factory. Use when creating or renaming any artifact."
paths:
  - ".claude/skills/*/"
  - ".claude/agents/*.md"
  - ".claude/rules/*.md"
---

# Naming Conventions — agents-factory

## Artifact naming patterns (kebab-case, all artifacts)

| Artifact type | Pattern | Rationale |
|---|---|---|
| Skill folder | `gerund-noun` | Action-oriented — describes what the skill *does* (e.g., `researching-technical-frameworks`, `auditing-architecture`) |
| Agent file | `domain-role` | Identity-oriented — describes *who* the agent is (e.g., `framework-researcher`, `skill-author`) |
| Rule file | `scope-noun` | Scope-oriented — describes *what* the rule governs (e.g., `skill-frontmatter`, `naming-conventions`) |

## ✅ Correct examples

| Type | Correct name | Why |
|---|---|---|
| Skill | `researching-technical-frameworks` | gerund (`researching`) + noun (`technical-frameworks`) |
| Skill | `auditing-architecture` | gerund (`auditing`) + noun (`architecture`) |
| Agent | `framework-researcher` | domain (`framework`) + role (`researcher`) |
| Agent | `skill-author` | domain (`skill`) + role (`author`) |
| Rule | `skill-frontmatter` | scope (`skill`) + noun (`frontmatter`) |
| Rule | `naming-conventions` | scope (`naming`) + noun (`conventions`) |

## ❌ Incorrect examples

| Incorrect | Problem | Correct form |
|---|---|---|
| `technical-framework-researcher` | Skill names must start with a gerund, not a noun | `researching-technical-frameworks` |
| `researcher-framework` | Agent name should be `domain-role`, not `role-domain` | `framework-researcher` |
| `conventions-naming` | Rule name should be `scope-noun`, not `noun-scope` | `naming-conventions` |
| `MyNewSkill` | PascalCase not allowed — use kebab-case | `my-new-skill` |

## Enforcement

- Skill folder names are validated by `skill-frontmatter.md` (name must match folder)
- Agent file names are validated by `agent-frontmatter.md` (name must match filename without extension)
- This rule adds the *pattern* requirement on top of the kebab-case requirement
