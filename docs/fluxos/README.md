# Fluxos Combinados

Pipelines de ponta-a-ponta que combinam múltiplas capacidades complementares.

---

## Mapa Geral

```mermaid
flowchart TD
    START{Qual é o objetivo?} --> Q1[Criar projeto de agente novo]
    START --> Q2[Construir base de conhecimento]
    START --> Q3[Validar qualidade]
    START --> Q4[Implementar com agente existente]

    Q1 --> F1[Fluxo de Criação de Projeto]
    Q2 --> F2[Fluxo de Base de Conhecimento]
    Q3 --> F3[Fluxo de Qualidade]
    Q4 --> F4[Fluxo de Implementação]

    click F1 "fluxo-criacao-projeto.md"
    click F2 "fluxo-base-conhecimento.md"
    click F3 "fluxo-qualidade.md"
    click F4 "fluxo-implementacao.md"
```

---

## Os 4 Fluxos

### 1. [Fluxo de Criação de Projeto](fluxo-criacao-projeto.md)

**Objetivo**: Criar um projeto de agente production-ready do zero.

```mermaid
graph LR
    A[researching-technical-frameworks] --> B[skill-creator] --> C[agent-router-pattern-validator] --> D[audit-architecture-consensus] --> E[✅ Produção]
```

**Capacidades envolvidas**: 1 de framework + 4 de auditoria + pesquisa + compilação

---

### 2. [Fluxo de Base de Conhecimento](fluxo-base-conhecimento.md)

**Objetivo**: Pesquisar tecnologia e transformar em skill/instruction operacional.

```mermaid
graph LR
    A[Researcher] --> B[Compiler/Generator] --> C[Validator] --> D[✅ Skill/Instruction]
```

**Capacidades envolvidas**: 7 de pesquisa + 4 de compilação + 2 de validação

---

### 3. [Fluxo de Qualidade](fluxo-qualidade.md)

**Objetivo**: Verificar e melhorar qualidade de artefatos existentes.

```mermaid
graph LR
    A[compatibility-review] --> B[instructions/skill-validator] --> C[project-analysis] --> D[✅ Qualidade]
```

**Capacidades envolvidas**: 4 de validação + (opcional) 5 de auditoria

---

### 4. [Fluxo de Implementação](fluxo-implementacao.md)

**Objetivo**: Usar agentes existentes para design + implementação.

```mermaid
graph LR
    A[Advisory Agent<br/>Design] --> B[Implementation Agent<br/>Código] --> C[Audit<br/>Validação]
```

**Capacidades envolvidas**: Agents (Advisory → Implementation) + Auditoria

---

## Quando Usar Qual Fluxo

| Situação | Fluxo |
|----------|-------|
| Começando domínio novo de automação | Criação de Projeto |
| Aprendendo tecnologia nova | Base de Conhecimento |
| Revisão de qualidade periódica | Qualidade |
| Projeto de agente já existe, quer usar | Implementação |
| Tudo do zero (tecnologia nova + agente) | Base de Conhecimento → Criação de Projeto |

---

## Composição entre Fluxos

Os fluxos se complementam. Cenário completo "do zero até produção":

```mermaid
graph TD
    subgraph "Fase 1: Conhecimento"
        R[Researcher] --> C[Compiler]
        C --> V1[Skill Validator]
    end

    subgraph "Fase 2: Projeto"
        RP[agent-router-pattern-validator]
    end

    subgraph "Fase 3: Qualidade"
        PV[project-analysis-validator] --> AU[audit-architecture-consensus]
    end

    V1 -->|skills prontas| RP
    RP --> PV
    AU --> PROD[✅ Production Ready]
```
