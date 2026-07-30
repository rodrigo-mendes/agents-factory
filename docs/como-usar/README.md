# Como Usar — Onboarding

## Pré-requisitos

| Requisito | Mínimo |
|-----------|--------|
| Claude Code CLI | [claude.ai/code](https://claude.ai/code) |
| Git | Qualquer versão recente |

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

## Início Rápido (5 minutos)

> Quer ver o pipeline completo numa única leitura? → [Início Rápido](inicio-rapido.md)

## Primeiro Uso

Escolha um dos cenários abaixo baseado no seu objetivo:

### "Quero pesquisar uma tecnologia"
→ [Pesquisando Tecnologias](pesquisando-tecnologias.md)

```
/technical-framework-researcher
```

### "Quero criar uma skill"
→ [Criando Skills](criando-skills.md)

```
/skill-creator StoryBeat/research_<Tech>_v<Version>.md
```

### "Quero criar um agente completo"
→ [Criando Agentes](criando-agentes.md)

Não há um único comando — o processo envolve pesquisar tecnologias, criar skills e depois
criar manualmente os ficheiros de definição do agente a partir dos templates em
`.claude/templates/`.

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
| Exemplos de chamadas para cada comando | [Manual de Uso dos Agentes](../manual/README.md) |
| Entender fluxos combinados | [Fluxos](../fluxos/README.md) |
| Referência de convenções e termos | [Convenções](../referencia/convencoes.md) · [Glossário](../referencia/glossario.md) |
