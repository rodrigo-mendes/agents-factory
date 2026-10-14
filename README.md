# Agents Factory

Framework sistemático para criação de **Skills, Subagentes e Rules** em **Claude Code**
(`.claude/`, única fonte de verdade) — focado em prevenir alucinações de IA através de pesquisa
validada, versionamento rigoroso e padrões de qualidade. O espelho GitHub Copilot (`.github/`)
pré-migração foi retirado (ver `.claude/MIGRATION.md`); `audit-architecture-*` e
`copilot-compatibility-review` continuam a existir como ferramentas genéricas para auditar
*outros* projetos que tenham `.github/`.

## O que é

O Agents Factory é uma fábrica de artefatos de IA que oferece:

- **78 Skills** (Claude Code) — 51 comandos (`/nome`) e 27 skills de conhecimento (auto-invocáveis). Pesquisa, autoria de skills/agentes/rules, compilação, validação e auditoria — inclui a **família platform-software** (15: orquestradora + 14 irmãs para Kafka, Redis, MongoDB, Postgres…), o **pipeline de livros técnicos** (pacote `book-writing`: 10 comandos + 13 agentes, saída em `Books/`) e os pacotes **Camel Quarkus** (`camel-quarkus-skills`: 13 skills versionadas para Camel Quarkus 3.40 LTS; `camel-quarkus-integrator`: orquestradora `integrating-camel-quarkus`, skill de estrutura, subagente e 3 rules — veja [packages/camel-quarkus-integrator/README.md](packages/camel-quarkus-integrator/README.md))
- **Ficheiros de `assets/`** nas skills que os possuem (`skill-creator`, `agent-creator`, `rules-compiler`, `terraform-instructions-compiler`, `structuring-camel-quarkus-projects` e as skills vindas do `microsoft/apm`) — não existe mais `.claude/templates/`
- **4 Fluxos Combinados** — Pipelines de ponta-a-ponta

## Início Rápido

### Claude Code (recomendado)

```
/researching-technical-frameworks
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

## Estrutura do Repositório

```
.claude/                    ← Claude Code (única fonte de verdade — não há .github/)
├── agents/                 ← 21 subagentes: 5 roteadores (framework-researcher, artifact-author, architecture-auditor, quality-validator, skill-evaluator) + 2 helpers de pesquisa (research-synthesizer, section-investigator) + 13 do pipeline de livros (book-writing) + camel-quarkus-integrator
├── skills/                 ← 78 skills; incl. a família platform-software (15), 15 skills Camel Quarkus e as skills com assets/ próprio
│                              (skill-creator, agent-creator, rules-compiler, terraform-instructions-compiler, structuring-camel-quarkus-projects, …)
├── rules/                  ← 8 rules: 5 da fábrica (agent/rules/skill-frontmatter, naming-conventions, skill-structure) + 3 do Camel Quarkus
└── settings.json
```

## Documentação

| Seção | Descrição |
|-------|-----------|
| [Visão Geral](docs/visao-geral.md) | Arquitetura do framework com diagramas |
| [Catálogo de Capacidades](docs/capacidades/README.md) | Todas as capacidades listadas e categorizadas |
| [Família Platform Software](docs/manual/platform-software-family.md) | 15 comandos para pesquisar plataformas auto-hospedadas (Kafka, Redis, Mongo…) |
| [Como Usar](docs/como-usar/README.md) | Guias passo-a-passo por jornada |
| [Fluxos Combinados](docs/fluxos/README.md) | Pipelines de ponta-a-ponta com diagramas |
| [Referência](docs/referencia/convencoes.md) | Convenções, padrões e glossário |

## Pré-requisitos

- Claude Code CLI instalado
- Este repositório clonado

## Princípios

| Princípio | Descrição |
|-----------|-----------|
| **Version Absolutism** | Uma skill = uma versão. Nunca misturar versões. |
| **Three-Tier (✅⚠️🚫)** | Padrões obrigatórios, decisões do usuário, anti-padrões |
| **P0-P5 Workflow** | Todo agente segue: Verify → Analyze → Consult → Propose → Implement → Validate |
| **Anti-Alucinação** | Toda informação validada contra documentação oficial |
