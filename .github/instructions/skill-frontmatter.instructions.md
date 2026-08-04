---
applyTo: ".github/{skills/**,agents/*.agent.md,prompts/*.prompt.md}"
---

# Frontmatter conventions — agents-factory

When creating or editing skills, agents, or prompts in this repository, follow:

## Skills (`.github/skills/<name>/SKILL.md`)

- Frontmatter YAML required: `name` + `description`. The `description` must contain a
  **"Use when…"** trigger, be specific, and be ≤ 1536 characters.
- Tool field is **`tools:`** as a YAML array — `['read', 'search', 'editFiles', 'createFile']`.
- **Progressive disclosure**: keep `SKILL.md` < 500 lines, linking `blueprints/` on demand.

## Agents (`.github/agents/<name>.agent.md`)

- Frontmatter YAML required: `name` + `description` + `tools:` (array).
- `description` must contain a **"Use when…"** trigger (used for automatic invocation routing).
- `tools:` array uses Copilot tool names: `read`, `search`, `editFiles`, `createFile`, `runInTerminal`.
  Apply least-privilege — only grant tools the agent actually needs.
- `name` in kebab-case, matching the filename (without `.agent.md`).

## Prompts (`.github/prompts/<name>.prompt.md`)

- Frontmatter YAML required: `name` + `description` + `argument-hint`.
- Operational prompts that delegate to an agent should reference the agent in their body
  (Copilot has no `context: fork` — delegation is instructional, not mechanical).
- `tools:` array optional; only set when the prompt itself uses specific tools inline.
- Filename must use `.prompt.md` extension (not bare `.md`).

## YAML

- Values containing `:` **must be quoted** (e.g., `argument-hint: "Scope: new / review"`).
- Names in kebab-case; `name` must match the folder name (skills) or filename stem (agents/prompts).
- No duplicate frontmatter fields.
