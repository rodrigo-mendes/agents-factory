# Prompts de Auditoria de Arquitetura

8 prompts que formam um sistema de auditoria multi-modelo para projetos de agente — disponível em duas variantes: **Copilot** (alvo `.github/`) e **Claude Code** (alvo `.claude/`).

---

## Visão Geral

O sistema de auditoria usa **3 modelos independentes** que analisam perspectivas diferentes em paralelo, depois um **orquestrador** compara findings e gera um relatório de consenso.

```mermaid
graph TD
    subgraph "Copilot (alvo .github/)"
        OC[audit-architecture-consensus] --> AC[audit-architecture-scope]
        OC --> BC[audit-architecture-flow]
        OC --> CC[audit-architecture-engine]
        AC -->|findings| OC
        BC -->|findings| OC
        CC -->|findings| OC
    end
    subgraph "Claude Code (alvo .claude/)"
        OCC[audit-cc-architecture-consensus] --> ACC[audit-cc-architecture-scope]
        OCC --> BCC[audit-cc-architecture-flow]
        OCC --> CCC[audit-cc-architecture-engine]
        ACC -->|findings| OCC
        BCC -->|findings| OCC
        CCC -->|findings| OCC
    end
    OC --> R[Relatório Priorizado]
    OCC --> R
```

| Modelo | Perspectiva | Foco |
|--------|-------------|------|
| **A (Scope)** | Hierarquia de responsabilidades | Separação por camada L0→L4 |
| **B (Flow)** | Cadeias de invocação | Reachability, dead-ends, ciclos |
| **C (Engine)** | Mecânicas do engine | applyTo/paths, context, frontmatter |
| **Consensus** | Consolidação | Priorização por consenso |

---

## 1. audit-architecture-consensus (Orquestrador)

> **Arquivo**: `.claude/skills/audit-architecture-consensus/SKILL.md`

### Descrição
Orquestra auditoria completa: executa Modelos A, B e C em paralelo, compara findings, e produz relatório priorizado por consenso.

### Invocação
```
audit-architecture-consensus
```

### Workflow Interno
1. Identifica target (agente a auditar)
2. Executa `audit-architecture-scope` (Modelo A)
3. Executa `audit-architecture-flow` (Modelo B)
4. Executa `audit-architecture-engine` (Modelo C)
5. Compara findings dos 3 modelos
6. Prioriza: issue encontrada por 3 modelos > 2 > 1
7. Gera relatório de remediação

### Input Esperado
- Nome do agente ou caminho para `.github/`

### Output Produzido
- Relatório markdown com:
  - Score de conformidade
  - Issues priorizadas por consenso (3/3, 2/3, 1/3)
  - Plano de remediação ordenado por impacto

### Tools Necessários
- `read`, `search`, `create`

### Quando Usar
- Auditoria completa de um projeto de agente
- Antes de "production readiness"
- Como step final do [Fluxo de Criação de Projeto](../fluxos/fluxo-criacao-projeto.md)

---

## 2. audit-architecture-scope (Modelo A)

> **Arquivo**: `.claude/skills/audit-architecture-scope/SKILL.md`

### Descrição
Audita hierarquia de responsabilidades por camada (L0→L4), detecta vazamento de responsabilidade entre camadas.

### Invocação
```
audit-architecture-scope
```

### O que Verifica

| Camada | Responsabilidade | Violação típica |
|--------|-----------------|-----------------|
| **L0** | Configuração global (.vscode/settings) | Lógica de negócio em settings |
| **L1** | Instructions (projeto-wide) | Código em instructions |
| **L2** | Skills (domínio-specific) | Skill fazendo routing |
| **L3** | Agents (orquestração) | Agent sem skill, "hardcoded knowledge" |
| **L4** | Prompts (entry-point) | Prompt com lógica de implementação |

### Output Produzido
- Score por camada (compliance %)
- Violações de vazamento detectadas
- Sugestões de reorganização

### Tools Necessários
- `read`, `search`, `create`

---

## 3. audit-architecture-flow (Modelo B)

> **Arquivo**: `.claude/skills/audit-architecture-flow/SKILL.md`

### Descrição
Audita cadeias de invocação (prompt → agent → instructions → skills), validando que todo entry-point tem cadeia completa.

### Invocação
```
audit-architecture-flow
```

### O que Verifica
- **Reachability**: Todo componente é alcançável por algum prompt
- **Completude**: Toda cadeia prompt→agent→skill é completa (sem elos faltando)
- **Dead-ends**: Componentes referenciados mas inexistentes
- **Ciclos**: Dependências circulares
- **Orphans**: Componentes que ninguém referencia

### Output Produzido
- Grafo de invocação (textual)
- Lista de broken chains
- Lista de componentes órfãos
- Sugestões de ligação

### Tools Necessários
- `read`, `search`

---

## 4. audit-architecture-engine (Modelo C)

> **Arquivo**: `.claude/skills/audit-architecture-engine/SKILL.md`

### Descrição
Audita mecânicas do VS Code engine — valida applyTo, context budget, frontmatter, deduplicação, conflitos.

### Invocação
```
audit-architecture-engine
```

### O que Verifica
- **applyTo**: Padrões glob corretos, sem overlap excessivo
- **Context budget**: Instructions não excedem limites úteis
- **Frontmatter**: YAML válido, campos obrigatórios presentes
- **Deduplicação**: Mesmo conteúdo não injetado múltiplas vezes
- **Conflitos**: Instructions contraditórias no mesmo escopo
- **Active vs Passive**: Caminhos de ativação corretos

### Output Produzido
- Relatório de mecanismos técnicos
- Warnings de context pollution
- Conflitos detectados com sugestão de resolução

### Tools Necessários
- `read`, `search`

---

---

## Variante Claude Code (alvo `.claude/`)

Os quatro prompts abaixo são idênticos em lógica mas auditam projetos **Claude Code** (`.claude/`), verificando convenções específicas do CC engine: `paths:` globs, `disable-model-invocation`, `context: fork`, `allowed-tools` vs `tools`, e as 4 camadas CLAUDE.md → subagente → rules → skills.

### 5. audit-cc-architecture-consensus (Orquestrador CC)

> **Arquivo**: `.claude/skills/audit-cc-architecture-consensus/SKILL.md`

### Descrição
Orquestra auditoria multi-modelo Claude Code: executa Scope + Flow + Engine em paralelo via tool `Agent` e produz relatório de consenso priorizado por 3/3, 2/3, 1/3 concordância.

### Invocação
```
audit-cc-architecture-consensus
```

### Input Esperado
- Caminho para `.claude/` ou raiz do projeto

### Output Produzido
- Relatório de consenso com score, issues priorizadas e plano de remediação

---

### 6. audit-cc-architecture-scope (Modelo A — CC)

> **Arquivo**: `.claude/skills/audit-cc-architecture-scope/SKILL.md`

### Descrição
Audita hierarquia de responsabilidades em projeto Claude Code: CLAUDE.md → subagente → rules → skills, detectando vazamento de responsabilidade entre camadas.

### Invocação
```
audit-cc-architecture-scope
```

---

### 7. audit-cc-architecture-flow (Modelo B — CC)

> **Arquivo**: `.claude/skills/audit-cc-architecture-flow/SKILL.md`

### Descrição
Audita cadeias de invocação `/comando → subagente fork → rules → skills`, validando reachability e ausência de dead-ends ou orphans em projeto Claude Code.

### Invocação
```
audit-cc-architecture-flow
```

---

### 8. audit-cc-architecture-engine (Modelo C — CC)

> **Arquivo**: `.claude/skills/audit-cc-architecture-engine/SKILL.md`

### Descrição
Audita mecânicas do Claude Code engine: `paths:` glob firing, budget de skills sem `disable-model-invocation`, isolamento de `context: fork`, `allowed-tools` vs `tools`, validade de `name`/`model`/`description`.

### Invocação
```
audit-cc-architecture-engine
```

---

## Uso Individual vs. Completo

| Cenário | Alvo Copilot | Alvo Claude Code |
|---------|-------------|-----------------|
| Auditoria completa pre-release | `audit-architecture-consensus` | `audit-cc-architecture-consensus` |
| Verificar só se as cadeias funcionam | `audit-architecture-flow` | `audit-cc-architecture-flow` |
| Verificar só mecânicas técnicas | `audit-architecture-engine` | `audit-cc-architecture-engine` |
| Verificar só separação de responsabilidades | `audit-architecture-scope` | `audit-cc-architecture-scope` |
| Debug: "por que minha skill não carrega?" | `audit-architecture-flow` + `audit-architecture-engine` | `audit-cc-architecture-flow` + `audit-cc-architecture-engine` |
