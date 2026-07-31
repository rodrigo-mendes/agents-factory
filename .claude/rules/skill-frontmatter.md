---
name: skill-frontmatter
paths:
  - ".claude/skills/**/SKILL.md"
  - ".claude/agents/*.md"
  - ".claude/rules/*.md"
  - ".claude/templates/**/*.md"
---

# Convenções de frontmatter (fábrica de artefatos)

Ao criar ou editar skills/subagentes neste repositório, siga:

## Skills (`.claude/skills/<n>/SKILL.md`)
- Frontmatter YAML obrigatório: `name` + `description`. A `description` deve conter um gatilho
  **"Use when…"**, ser específica e ter ≤ 1536 caracteres.
- Campo de ferramentas é **`allowed-tools:`** (skills/commands) — **não** `tools:`.
- Comandos de **ação deliberada** (researchers, generators, validators, auditors): adicionar
  `context: fork`, `agent: <subagente>` e `disable-model-invocation: true` (acessíveis por `/nome`,
  sem custo de auto-listagem). Skills de **conhecimento** ficam auto-invocáveis (sem `disable-...`).
- **Progressive disclosure**: manter o `SKILL.md` < 500 linhas, linkando `blueprints/` sob demanda.
  Evitar `@arquivo` (import eager) para conteúdo grande.

## Subagentes (`.claude/agents/<n>.md`)
- Campo de ferramentas é **`tools:`** (subagentes) — **não** `allowed-tools:`. Least-privilege.
- `description` com **"Use when…"** (único campo usado para delegação automática).
- `model:` opcional — `opus`/`sonnet`/`haiku`/`fable`/`inherit` ou IDs (`claude-opus-4-8`).
  ❌ Nunca versões antigas nem sufixos `*plan`.

## YAML
- Valores contendo `:` **precisam de aspas** (ex.: `argument-hint: "Scope: new / review"`).
- Nomes em kebab-case; `name` deve casar com o nome da pasta (skills) / arquivo (agents).

Referência completa: [skill-creator](../skills/skill-creator/SKILL.md).
