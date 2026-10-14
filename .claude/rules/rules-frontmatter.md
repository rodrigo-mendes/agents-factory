---
name: rules-frontmatter
description: "Frontmatter schema for rules/instructions files (.claude/rules/*.md). Use when creating or editing a rule definition."
paths:
  - ".claude/rules/*.md"
  - ".claude/skills/rules-compiler/assets/*.md"
---

# Frontmatter conventions — Rules (`.claude/rules/<n>.md`)

## Required fields

| Field | Rule |
|---|---|
| `name` | kebab-case; unique across all rules in `.claude/rules/` |
| `paths` | YAML list of glob patterns; drives automatic context injection when Claude Code opens a matching file |

## Optional fields

| Field | Rule |
|---|---|
| `description` | Brief summary of what this rule covers. Optional per this schema, but every rule in `.claude/rules/` currently has one — treat it as recommended, not skippable. |

## Minimal example

```yaml
---
name: my-rule
paths:
  - ".claude/some/path/**/*.md"
---
```

## With description

```yaml
---
name: my-rule
description: "Standards for X — naming, structure, and mandatory patterns."
paths:
  - "**/*.ts"
  - "**/*.tsx"
---
```

## Critical distinctions

- `paths:` is exclusive to rules — agents and skills do not have this field.
- Rules have **no** `tools:`, `model:`, `context:`, `agent:`, or `disable-model-invocation` fields.
- `description` is optional per this schema; every rule under `.claude/rules/` has one today.
- The glob patterns in `paths:` follow ripgrep/glob conventions relative to the workspace root.

## YAML

- Values containing `:` require quotes.
- `name` must be kebab-case and unique.
