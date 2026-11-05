# Frontmatter cheatsheet

The header at the top of a skill, subagent or rule file decides how it behaves. This page puts the
three side by side. The full rules are in `.claude/rules/skill-frontmatter.md`,
`agent-frontmatter.md` and `rules-frontmatter.md`.

## At a glance

| Field | Skill | Subagent | Rule |
|---|---|---|---|
| `name` | required, matches the folder | required, matches the file name | required, unique |
| `description` | required, at most 1536 characters, with a "Use when" trigger | required, at most 1536 characters, with a "Use when" trigger | optional but recommended |
| `tools` | no | required, comma-separated, least privilege | no |
| `allowed-tools` | optional | no | no |
| `model` | no | optional (`opus`, `sonnet`, `haiku`, `fable` or a full ID) | no |
| `paths` | no | no | required, list of globs |
| `argument-hint` | commands only | no | no |
| `context: fork` | commands only | no | no |
| `agent` | commands only | no | no |
| `disable-model-invocation` | commands only | no | no |

Use `tools:` in agents and `allowed-tools:` in skills. Never mix them.

## A knowledge skill

Loaded automatically when your request matches the description.

```yaml
---
name: my-knowledge-skill
description: "Explains X patterns for Y. Use when the user asks about X in context Z."
---
```

## A command

Started with `/name`. The four extra fields come together.

```yaml
---
name: my-action-command
description: "Creates X from Y. Use when authoring a new X from a research file."
argument-hint: "Path to research file (e.g. workspace/research_X_v1.md)"
context: fork
agent: artifact-author
disable-model-invocation: true
---
```

`context: fork` and `disable-model-invocation: true` always go together:

| If you set | You must also set | What goes wrong otherwise |
|---|---|---|
| `context: fork` only | `disable-model-invocation: true` | The skill is listed in every session and costs tokens each time. |
| `disable-model-invocation: true` only | `context: fork` | The skill does nothing when you run `/name`. |

`agent:` must match a file in `.claude/agents/` without the `.md` extension.

An inline orchestrator has neither `context: fork` nor `agent:`. See
[Agent architecture](../agents/architecture.md).

## A subagent

```yaml
---
name: my-researcher
description: >
  Domain Researcher — builds knowledge bases from official docs.
  Use when researching a technology (e.g. "research FastAPI 0.115").
tools: Read, Grep, Glob, WebSearch, WebFetch, Write
model: opus
---
```

Use the `>` block for multi-sentence descriptions. Quote any value that contains a colon. Do not use
old model versions or `*plan` suffixes.

## A rule

```yaml
---
name: my-rule
description: "Standards for X — naming, structure and mandatory patterns."
paths:
  - "**/*.ts"
  - "**/*.tsx"
---
```

The rule joins the context when Claude works on a file that matches one of the globs.

## Structure rules for skills

- `SKILL.md` stays under 500 lines. Move long content to `blueprints/` and link it.
- Every command needs `blueprints/evaluation-scenarios.md`.
- `## Quick Navigation` links to the evaluation scenarios and to the guardrails section.
- `## Blueprints & Guardrails` (✅ ⚠️ 🚫) comes right after Quick Navigation, before long sections.

## Related

- [Conventions](conventions.md): naming and the workflow.
- [Glossary](glossary.md).
