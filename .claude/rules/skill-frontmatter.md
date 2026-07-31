---
name: skill-frontmatter
paths:
  - ".claude/skills/**/SKILL.md"
  - ".claude/templates/skills/*.md"
---

# Frontmatter conventions — Skills (`.claude/skills/<n>/SKILL.md`)

## Required fields (all skills)

| Field | Rule |
|---|---|
| `name` | kebab-case; must match the folder name |
| `description` | ≤ 1536 characters; must contain a **"Use when…"** trigger |

## Knowledge skills (auto-invocable)

Only `name` + `description`. No `disable-model-invocation`, no `context`. Claude auto-invokes these when the trigger is matched.

```yaml
---
name: my-knowledge-skill
description: "Explains X patterns for Y. Use when the user asks about X in context Z."
---
```

## Action-command skills (deliberate, via `/name`)

Add four extra fields. All four are required together — omitting any one breaks the routing:

| Field | Rule |
|---|---|
| `argument-hint` | Human-readable hint for the slash-command argument (shown in the UI); required when the skill uses `$ARGUMENTS` |
| `context: fork` | Forks execution to a subagent |
| `agent:` | Name of the subagent to invoke; must match a file in `.claude/agents/` without the `.md` extension |
| `disable-model-invocation: true` | Prevents auto-listing cost; makes the skill accessible only via `/name` |

```yaml
---
name: my-action-command
description: "Creates X from Y. Use when authoring a new X from a research file."
argument-hint: "Path to research file (e.g. StoryBeat/research_X_v1.md)"
context: fork
agent: skill-author
disable-model-invocation: true
---
```

## Optional field

| Field | Rule |
|---|---|
| `allowed-tools:` | Least-privilege tool restriction. Use **`allowed-tools:`** — **not** `tools:` (that field belongs to subagents). |

## Progressive disclosure

Keep `SKILL.md` < 500 lines; link `blueprints/` for large content. Avoid `@file` (eager import) for large files.

## YAML

- Values containing `:` **require quotes** (e.g. `argument-hint: "Scope: new / review"`).
- `name` must match the folder name exactly.

Full reference: [skill-creator](../skills/skill-creator/SKILL.md).
