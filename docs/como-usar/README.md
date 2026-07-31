# How to Use — Onboarding

## Prerequisites

| Requirement | Minimum |
|-----------|--------|
| Claude Code CLI | [claude.ai/code](https://claude.ai/code) |
| Git | Any recent version |

## Setup

1. Clone or add this repository to your workspace:
   ```bash
   git clone <repo-url> agents-factory
   ```

2. Open with Claude Code:
   ```bash
   claude agents-factory
   ```

3. Commands become available automatically via `/command-name`

> **Note**: Commands in `.claude/skills/` are automatically loaded by Claude Code when the project is open.

## Quick Start (5 minutes)

> Want to see the complete pipeline in a single read? → [Quick Start](inicio-rapido.md)

## First Use

Choose one of the scenarios below based on your goal:

### "I want to research a technology"
→ [Researching Technologies](pesquisando-tecnologias.md)

```
/researching-technical-frameworks
```

### "I want to create a skill"
→ [Creating Skills](criando-skills.md)

```
/skill-creator StoryBeat/research_<Tech>_v<Version>.md
```

### "I want to create a full agent"
→ [Creating Agents](criando-agentes.md)

There is no single command — the process involves researching technologies, creating skills, and then
manually creating the agent definition files from the templates in
`.claude/templates/`.

### "I want to validate what I already have"
→ [Validating Artifacts](validando-artefatos.md)

```
/project-analysis-validator .claude/
```

## Essential Concepts

Before diving into the guides, understand these 4 concepts:

| Concept | Summary | Detail |
|----------|--------|---------|
| **Three-Tier** | ✅ Self-execute / ⚠️ Ask first / 🚫 Never do | [Conventions](../referencia/convencoes.md#three-tier) |
| **P0-P5** | 6 mandatory agent execution phases | [Conventions](../referencia/convencoes.md#workflow-p0-p5) |
| **Version Absolutism** | 1 skill = 1 specific version | [Conventions](../referencia/convencoes.md#version-absolutism) |
| **Agent Router Pattern** | Prompt → Agent → Skills (separation of concerns) | [Overview](../visao-geral.md) |

## Next Steps

| If you want to... | Read |
|-----------------|------|
| Understand the architecture | [Overview](../visao-geral.md) |
| See all capabilities | [Catalog](../capacidades/README.md) |
| Invocation examples for each command | [Agent Usage Manual](../manual/README.md) |
| Understand combined flows | [Flows](../fluxos/README.md) |
| Reference for conventions and terms | [Conventions](../referencia/convencoes.md) · [Glossary](../referencia/glossario.md) |
