# Como Usar — Onboarding

## Pré-requisitos

| Requisito | Mínimo |
|-----------|--------|
| Claude Code CLI | claude.ai/code |

## Setup

1. Clone ou adicione este repositório ao seu workspace:
   ```bash
   git clone <repo-url> agents-factory
   ```

2. Abra com Claude Code:
   ```bash
   claude agents-factory
   ```

3. Os comandos ficam disponíveis automaticamente via `/nome-do-comando`

> **Nota**: Os comandos em `.claude/skills/` são carregados automaticamente pelo Claude Code quando o projeto está aberto.

## Primeiro Uso

Escolha um dos cenários abaixo baseado no seu objetivo:

### "Quero pesquisar uma tecnologia"
→ [Pesquisando Tecnologias](pesquisando-tecnologias.md)

```
/technical-framework-researcher
```

### "Quero criar um agente novo"
→ [Criando Agentes](criando-agentes.md)

```
/skill-creator
```

### "Quero criar uma skill"
→ [Criando Skills](criando-skills.md)

```
/skill-creator
```

### "Quero validar o que já tenho"
→ [Validando Artefatos](validando-artefatos.md)

```
/project-analysis-validator .claude/
```

## Conceitos Essenciais

Antes de mergulhar nos guias, entenda estes 4 conceitos:

| Conceito | Resumo | Detalhe |
|----------|--------|---------|
| **Three-Tier** | ✅ Auto-executar / ⚠️ Perguntar / 🚫 Nunca fazer | [Convenções](../referencia/convencoes.md#three-tier) |
| **P0-P5** | 6 fases obrigatórias de execução de agente | [Convenções](../referencia/convencoes.md#workflow-p0-p5) |
| **Version Absolutism** | 1 skill = 1 versão específica | [Convenções](../referencia/convencoes.md#version-absolutism) |
| **Agent Router Pattern** | Prompt → Agent → Skills (separação de concerns) | [Visão Geral](../visao-geral.md) |

## Próximos Passos

| Se você quer... | Leia |
|-----------------|------|
| Entender a arquitetura | [Visão Geral](../visao-geral.md) |
| Ver todas as capacidades | [Catálogo](../capacidades/README.md) |
| Entender fluxos combinados | [Fluxos](../fluxos/README.md) |
| Referência de convenções | [Convenções](../referencia/convencoes.md) |
