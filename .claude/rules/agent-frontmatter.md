---
name: agent-frontmatter
description: "Frontmatter schema for subagent files (.claude/agents/*.md). Use when creating or editing a subagent definition."
paths:
  - ".claude/agents/*.md"
  - ".claude/templates/agents/*.md"
---

# Frontmatter conventions — Subagents (`.claude/agents/<n>.md`)

## Required fields

| Field | Rule |
|---|---|
| `name` | kebab-case; must match the filename without extension |
| `description` | ≤ 1536 characters; must contain a **"Use when…"** trigger — this is the only field used for automatic delegation routing |
| `tools` | comma-separated list; least-privilege (only what the agent actually needs) |

## Optional fields

| Field | Rule |
|---|---|
| `model` | `opus`, `sonnet`, `haiku`, `fable`, or a full model ID (e.g. `claude-opus-5`). Omit to inherit from parent. ❌ Never old versions, never `*plan` suffixes. |

## Critical distinction

- Agents use **`tools:`** — not `allowed-tools:` (that field belongs to skills/commands).
- `model:` is exclusive to agents; rules and skills do not use this field.
- Templates omit `model:` — choose it explicitly when instantiating a real agent.

## Description style

Use the `>` block scalar for multi-sentence descriptions:

```yaml
name: my-researcher
description: >
  Domain Researcher — builds hallucination-proof knowledge bases from official docs.
  Use when researching a technology to produce a SKILL-ready knowledge base
  (e.g. "research FastAPI 0.115", "research OCI best practices").
tools: Read, Grep, Glob, WebSearch, WebFetch, Write
model: opus
```

## YAML

- Values containing `:` require quotes.
- `name` must match the filename without the `.md` extension.
