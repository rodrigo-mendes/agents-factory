# Agents Factory — CLAUDE.md

Fábrica de artefatos de IA (**Skills, Prompts/Commands, Subagentes, Rules**) com foco
**anti-alucinação**. Este repositório **produz** artefatos para agentes de código e **também roda no
Claude Code**: os prompts operacionais são expostos como skills/comandos que forkam para subagentes.

> **Dual-target.** A fábrica documenta adoção para **Claude Code** (`docs/adocao-claude-code/`) e
> **GitHub Copilot** (`docs/adopcion/`). Config em `.github/` (Copilot) e `.claude/` (Claude Code)
> **coexistem** durante a transição — não apague `.github/`.

## Princípios (não-negociáveis)

- **Version Absolutism** — 1 skill = 1 versão; tratar versões antigas como desinformação.
- **Source Hierarchy** — doc oficial/registry > blog oficial > exemplos oficiais > comunidade
  verificada > rejeitar o resto. Rejeitar fontes > 12 meses salvo se forem a stable atual.
- **Executable Truth** — toda afirmação linka a fonte oficial datada; sem fonte, marcar "unverified".
- **Workflow P0–P5** — Verify Docs → Analyze → Consult → Propose → Implement → Validate.
- **Três Tiers** — ✅ Always-Do · ⚠️ Ask-First · 🚫 Never-Do (com alternativa).
- **Progressive disclosure** — `SKILL.md` enxuto (< 500 linhas) linkando blueprints; nada de inline gigante.

## Convenções de nome (kebab-case)

| Artefato | Padrão | Exemplo |
|---|---|---|
| Skill | `gerund-noun` | `researching-technical-frameworks` |
| Comando/Prompt | `action-noun` | `technical-framework-researcher` |
| Subagente | `domain-role` | `framework-researcher` |
| Rule | `scope-noun` | `skill-frontmatter` |

## Roteamento — Skill (`/comando`) → Subagente → Skills

Os comandos operacionais forkam (`context: fork`) para um subagente. Os 4 subagentes vivem em
[.claude/agents/](.claude/agents/):

| Subagente | Faz | Comandos que roteia |
|---|---|---|
| [framework-researcher](.claude/agents/framework-researcher.md) | pesquisa anti-alucinação (usa WebSearch/WebFetch) | `technical-framework-researcher`(+`-terraform`), `cloud-architecture-researcher`, `business-domain-researcher`, `requirements-methodology-researcher`, `architecture-methodology-researcher`, `terraform-engineering-best-practices-researcher` |
| [skill-author](.claude/agents/skill-author.md) | gera SKILL.md / rules | `skill-creator`, `methodologies-skill-generator`, `architecture-approaches-skill-generator`, `terraform-instructions-compiler` |
| [architecture-auditor](.claude/agents/architecture-auditor.md) | audita arquitetura (consensus = 3 lentes em paralelo via tool Agent) | `audit-architecture-scope`/`flow`/`engine`/`consensus` |
| [quality-validator](.claude/agents/quality-validator.md) | valida qualidade/aderência | `skill-best-practices-validator`, `instructions-best-practices-validator`, `agent-router-pattern-validator`, `copilot-compatibility-review` |

**Meta-skills** (auto-invocáveis, conhecimento base):
[researching-technical-frameworks](.claude/skills/researching-technical-frameworks/SKILL.md) ·
[authoring-agent-skills](.claude/skills/authoring-agent-skills/SKILL.md).

## Como rodar (não há build)

Não é código compilado — os artefatos rodam **no Claude Code** via `/<comando>`:

- Pesquisar tecnologia: `/technical-framework-researcher <tech> <versão>`
- Criar skill: `/skill-creator`
- Auditar arquitetura (consenso): `/audit-architecture-consensus <alvo>`
- Validar qualidade de skills: `/skill-best-practices-validator .claude/skills/`

Os 19 comandos usam `disable-model-invocation: true` (ações deliberadas) — acessíveis por `/nome`,
sem custo de auto-listagem. Só as 2 meta-skills ficam auto-invocáveis.

## Estrutura

```
.claude/
├── agents/     ← 4 subagentes (framework-researcher, skill-author, architecture-auditor, quality-validator)
├── skills/     ← 2 meta-skills + 19 comandos operacionais (fork → subagente)
├── rules/      ← rules por caminho (paths:) + templates
├── templates/  ← scaffolding (variantes Claude Code de agents/skills/rules)
└── settings.json
docs/           ← visão geral, capacidades, fluxos, referência, programas de adoção
StoryBeat/      ← saídas de pesquisa geradas por agentes (untracked)
.github/        ← config Copilot (coexistência; não apagar)
```

## Gotchas

- `tools:` é de subagentes; `allowed-tools:` é de skills/commands. Não trocar.
- Nomes de modelo válidos: `opus`/`sonnet`/`haiku`/`fable`/`inherit` ou IDs (`claude-opus-4-8`).
  Inválidos: versões antigas e sufixos `*plan`.
- YAML: valores com `:` precisam de aspas (ex.: `argument-hint: "Scope: new / review"`).
- Não confie em contagens de auditorias — confirme com `ls`/`wc`/`grep`.
