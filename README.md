# Agents Factory

Framework sistemático para criação de **Skills, Prompts e Agentes** para GitHub Copilot, com foco em prevenir alucinações de IA através de pesquisa validada, versionamento rigoroso e padrões de qualidade.

## O que é

O Agents Factory é uma fábrica de artefatos para GitHub Copilot que oferece:

- **2 Meta-Skills** — Padrões de criação de skills e pesquisa de tecnologias
- **21 Prompts Operacionais** — Pesquisa, compilação, validação e auditoria
- **14 Templates** — Scaffolding para qualquer tipo de artefato
- **4 Fluxos Combinados** — Pipelines de ponta-a-ponta

## Início Rápido

### Cenário 1: Pesquisar uma tecnologia nova

```
@workspace /technical-framework-researcher
```
> Pesquisa a tecnologia com version absolutism, produzindo uma base de conhecimento livre de alucinações.

### Cenário 2: Criar um agente completo do zero

```
@workspace /agent-bootstrap
```
> Wizard interativo que gera projeto completo: agent + instructions + prompts + skills.

### Cenário 3: Validar qualidade de um projeto existente

```
@workspace /project-analysis-validator
```
> Análise de qualidade com recomendações de melhoria priorizadas.

## Estrutura do Repositório

```
.github/
├── skills/          ← 2 meta-skills (padrões do framework)
├── prompts/         ← 21 prompts operacionais
└── templates/       ← 14 templates + exemplos reais
    ├── agents/      ← 3 templates de agentes (Implementation, Advisory, Orchestrator)
    ├── prompts/     ← 6 templates de prompts
    ├── skills/      ← 1 template de skill
    ├── instructions/← 3 templates de instructions
    ├── reports/     ← 1 template de relatório
    └── examples/    ← Implementações reais de referência
```

## Documentação

| Seção | Descrição |
|-------|-----------|
| [Visão Geral](docs/visao-geral.md) | Arquitetura do framework com diagramas |
| [Catálogo de Capacidades](docs/capacidades/README.md) | Todas as capacidades listadas e categorizadas |
| [Como Usar](docs/como-usar/README.md) | Guias passo-a-passo por jornada |
| [Fluxos Combinados](docs/fluxos/README.md) | Pipelines de ponta-a-ponta com diagramas |
| [Referência](docs/referencia/convencoes.md) | Convenções, padrões e glossário |

## Pré-requisitos

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
