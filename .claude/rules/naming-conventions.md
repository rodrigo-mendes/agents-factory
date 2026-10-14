---
name: naming-conventions
description: "Naming convention rules for skills, agents, and rules in this factory. Use when creating or renaming any artifact."
paths:
  - ".claude/skills/**/SKILL.md"
  - ".claude/agents/*.md"
  - ".claude/rules/*.md"
---

# Naming Conventions — agents-factory

## Artifact naming patterns (kebab-case, all artifacts)

Both skill kinds live under `.claude/skills/<name>/SKILL.md` — the frontmatter shape decides
which pattern applies (see [skill-frontmatter.md](./skill-frontmatter.md)), not a separate folder.

| Artifact type | Pattern | Rationale |
|---|---|---|
| Skill folder — **knowledge skill** (no `context: fork`, auto-invocable) | `gerund-noun` | Action-oriented — describes what the skill *teaches/does* (e.g., `researching-technical-frameworks`, `auditing-architecture`) |
| Skill folder — **action-command skill** (`context: fork` + `disable-model-invocation: true`, routes to a subagent) | `action-noun` or `domain-role` | Deliberate-invocation commands follow the same pattern as the subagent/domain they front (e.g., `skill-creator`, `skill-best-practices-validator`, `audit-architecture-scope`) |
| Agent file | `domain-role` | Identity-oriented — describes *who* the agent is (e.g., `framework-researcher`, `artifact-author`) |
| Rule file | `scope-noun` | Scope-oriented — describes *what* the rule governs (e.g., `skill-frontmatter`, `naming-conventions`) |

## ✅ Correct examples

| Type | Correct name | Why |
|---|---|---|
| Knowledge skill | `researching-technical-frameworks` | gerund (`researching`) + noun (`technical-frameworks`) |
| Knowledge skill | `auditing-architecture` | gerund (`auditing`) + noun (`architecture`) |
| Action-command skill | `skill-creator` | domain (`skill`) + role (`creator`) — mirrors its subagent naming, not gerund-noun |
| Action-command skill | `skill-best-practices-validator` | domain (`skill-best-practices`) + role (`validator`) |
| Agent | `framework-researcher` | domain (`framework`) + role (`researcher`) |
| Agent | `artifact-author` | domain (`artifact`) + role (`author`) |
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
