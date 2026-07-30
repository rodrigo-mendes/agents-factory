# Prompts de Validação

4 prompts dedicados a verificar qualidade e conformidade de artefatos do framework.

Todos seguem o padrão do `TEMPLATE.VALIDATION.prompt.md`.

---

## Visão Geral

| Prompt | Valida | Contra | Output |
|--------|--------|--------|--------|
| `copilot-compatibility-review` | Qualquer artefato Copilot | Docs oficiais GitHub + convenções ECI | Relatório de compatibilidade |
| `instructions-best-practices-validator` | `.instructions.md` | Docs GitHub/VS Code + convenções time | Análise de qualidade |
| `skill-best-practices-validator` | `SKILL.md` | Claude best practices + `authoring-agent-skills` | Análise de qualidade |
| `project-analysis-validator` | Projeto inteiro | Quality framework + three-tier | Score + roadmap |

---

## 1. copilot-compatibility-review

> **Arquivo**: `.claude/skills/copilot-compatibility-review/SKILL.md`

### Descrição
Verifica compatibilidade de artefatos GitHub Copilot (`.agent.md`, `.instructions.md`, `.prompt.md`, `SKILL.md`) contra documentação oficial.

### Invocação
```
copilot-compatibility-review
```

### O que Verifica
- YAML frontmatter correto (campos, limites de caracteres)
- Compatibilidade com engine do VS Code
- Uso correto de `applyTo`, `tools`, `agent`
- Aderência a limites documentados

### Input Esperado
- Caminho para repositório/pasta com artefatos Copilot

### Output Produzido
- Relatório markdown com violações categorizadas por severidade

### Dependências
- Nenhuma skill (auto-contido)

### Quando Usar
- Primeiro check após criar qualquer artefato novo
- Antes de commit/PR de artefatos Copilot
- Como step 1 do [Fluxo de Qualidade](../fluxos/fluxo-qualidade.md)

---

## 2. instructions-best-practices-validator

> **Arquivo**: `.claude/skills/instructions-best-practices-validator/SKILL.md`

### Descrição
Valida arquivos `.instructions.md` contra best practices oficiais de GitHub/VS Code e convenções do time.

### Invocação
```
instructions-best-practices-validator
```

### O que Verifica
- Estrutura do arquivo (seções obrigatórias)
- Clareza e concisão das instruções
- Ausência de contradições
- Aderência a padrões de naming
- Escopo adequado (não muito amplo, não muito restrito)

### Input Esperado
- Caminho para diretório contendo `.instructions.md`

### Output Produzido
- Análise de qualidade com sugestões de melhoria priorizadas

### Dependências
- Nenhuma skill (valida contra docs oficiais internamente)

### Quando Usar
- Após `terraform-instructions-compiler` gerar instructions
- Ao revisar instructions existentes
- Como step 2 do [Fluxo de Qualidade](../fluxos/fluxo-qualidade.md)

---

## 3. skill-best-practices-validator

> **Arquivo**: `.claude/skills/skill-best-practices-validator/SKILL.md`

### Descrição
Valida `SKILL.md` contra Claude best practices oficiais e o padrão definido em `authoring-agent-skills`.

### Invocação
```
skill-best-practices-validator
```

### O que Verifica
- Three-tier correto (✅⚠️🚫 — presença e conteúdo)
- YAML frontmatter (name ≤64 chars, description ≤1024 chars)
- Version absolutism (uma versão por skill)
- Blueprints presentes e completos
- Código de exemplo em todos os ✅ Always Do
- Alternativas em todos os 🚫 Never Do
- Progressive disclosure (informação em camadas)

### Input Esperado
- Caminho para diretório de skills

### Output Produzido
- Análise de qualidade com score e itens de melhoria

### Dependências
- Skill: `authoring-agent-skills` (baseline de validação)

### Quando Usar
- Após `skill-creator` ou generators produzirem SKILL.md
- Ao revisar skills existentes
- Como step 3 do [Fluxo de Qualidade](../fluxos/fluxo-qualidade.md)

---

## 4. project-analysis-validator

> **Arquivo**: `.claude/skills/project-analysis-validator/SKILL.md`

### Descrição
Análise holística de projetos de agente Claude Code (`.claude/`) e GitHub Copilot (`.github/`) — detecta drift de CLAUDE.md, frontmatter inválido, routing quebrado e componentes órfãos. Emite score e roadmap de remediação priorizados.

### Invocação
```
project-analysis-validator
```

### O que Verifica
- Completude do projeto (todos os artefatos necessários presentes)
- Consistência entre artefatos (agent referencia skills que existem, etc.)
- Qualidade geral (sem dead-ends, sem referências quebradas)
- Aderência ao Agent Router Pattern
- Cobertura de skills (domínio coberto adequadamente)

### Input Esperado
- Caminho para diretório do projeto de agente

### Output Produzido
- Score de qualidade (0-100)
- Roadmap de melhorias priorizado
- Quick wins identificados

### Dependências
- Nenhuma skill (análise holística)

### Quando Usar
- Validação final antes de "produção"
- Review periódica de projetos existentes
- Como step 4 (final) do [Fluxo de Qualidade](../fluxos/fluxo-qualidade.md)

---

## Pipeline de Validação Recomendado

```mermaid
graph LR
    A[copilot-compatibility-review] -->|compatível| B[instructions-best-practices-validator]
    A -->|compatível| C[skill-best-practices-validator]
    B --> D[project-analysis-validator]
    C --> D
```

Executar nesta ordem garante: primeiro compatibilidade técnica, depois qualidade de conteúdo, por fim consistência holística.

Ver: [Fluxo de Qualidade](../fluxos/fluxo-qualidade.md) para detalhes completos.
