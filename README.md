# Agents Factory

Framework sistemático para criação de **Skills, Prompts e Agentes** — com suporte a **Claude Code** (`.claude/`) e **GitHub Copilot** (`.github/`) em coexistência — focado em prevenir alucinações de IA através de pesquisa validada, versionamento rigoroso e padrões de qualidade.

## O que é

O Agents Factory é uma fábrica de artefatos de IA que oferece:

- **2 Meta-Skills** — Padrões de criação de skills e pesquisa de tecnologias
- **24 Skills Operacionais** (Claude Code) / **20 Prompts** (Copilot) — Pesquisa, compilação, validação e auditoria
- **14 Templates** — Scaffolding para qualquer tipo de artefato
- **4 Fluxos Combinados** — Pipelines de ponta-a-ponta

## Início Rápido

### Claude Code (recomendado)

```
/technical-framework-researcher
```
> Pesquisa a tecnologia com version absolutism, produzindo uma base de conhecimento livre de alucinações.

```
/project-analysis-validator
```
> Análise estrutural e de qualidade de projetos de agente com recomendações priorizadas.

```
/audit-cc-architecture-consensus
```
> Auditoria multi-modelo de projetos Claude Code com relatório de consenso priorizado.

### GitHub Copilot

```
@workspace /technical-framework-researcher
```

```
@workspace /project-analysis-validator
```

## Estrutura do Repositório

```
.claude/                    ← Claude Code (runtime principal)
├── agents/                 ← 4 subagentes (framework-researcher, skill-author, architecture-auditor, quality-validator)
├── skills/                 ← 26 skills (2 meta + 24 operacionais com context: fork)
├── rules/                  ← 1 rule de frontmatter
├── templates/              ← 14 templates (agents/, prompts/, rules/, skills/, reports/)
└── settings.json

.github/                    ← GitHub Copilot (coexistência; não remover)
├── skills/                 ← 2 meta-skills
├── prompts/                ← 20 prompts operacionais
└── templates/              ← 15 templates (agents/, instructions/, prompts/, skills/, reports/)
```

## Documentação

| Seção | Descrição |
|-------|-----------|
| [Visão Geral](docs/visao-geral.md) | Arquitetura do framework com diagramas |
| [Catálogo de Capacidades](docs/capacidades/README.md) | Todas as capacidades listadas e categorizadas |
| [Como Usar](docs/como-usar/README.md) | Guias passo-a-passo por jornada |
| [Fluxos Combinados](docs/fluxos/README.md) | Pipelines de ponta-a-ponta com diagramas |
| [Mapeamento .github/ ↔ .claude/](docs/referencia/mapeamento-github-claude.md) | Equivalência entre artefatos Copilot e Claude Code |
| [Referência](docs/referencia/convencoes.md) | Convenções, padrões e glossário |

## Pré-requisitos

**Claude Code (recomendado):**
- Claude Code CLI instalado
- Este repositório clonado

**GitHub Copilot (coexistência):**
- VS Code com GitHub Copilot Chat ativo
- Extensão GitHub Copilot Chat (≥ 0.20)
- Este repositório clonado ou adicionado como workspace

## Princípios

| Princípio | Descrição |
|-----------|-----------|
| **Version Absolutism** | Uma skill = uma versão. Nunca misturar versões. |
| **Three-Tier (✅⚠️🚫)** | Padrões obrigatórios, decisões do usuário, anti-padrões |
| **P0-P5 Workflow** | Todo agente segue: Verify → Analyze → Consult → Propose → Implement → Validate |
| **Anti-Alucinação** | Toda informação validada contra documentação oficial |
