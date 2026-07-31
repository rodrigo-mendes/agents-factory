# Combined Flows

End-to-end pipelines that combine multiple complementary capabilities.

---

## General Map

```mermaid
flowchart TD
    START{What is the objective?} --> Q1[Create new agent project]
    START --> Q2[Build knowledge base]
    START --> Q3[Validate quality]
    START --> Q4[Implement with existing agent]

    Q1 --> F1[Project Creation Flow]
    Q2 --> F2[Knowledge Base Flow]
    Q3 --> F3[Quality Flow]
    Q4 --> F4[Implementation Flow]

    click F1 "fluxo-criacao-projeto.md"
    click F2 "fluxo-base-conhecimento.md"
    click F3 "fluxo-qualidade.md"
    click F4 "fluxo-implementacao.md"
```

---

## The 4 Flows

### 1. [Project Creation Flow](fluxo-criacao-projeto.md)

**Objective**: Create a production-ready agent project from scratch.

```mermaid
graph LR
    A[researching-technical-frameworks] --> B[skill-creator] --> C[agent-router-pattern-validator] --> D[audit-architecture-consensus] --> E[✅ Production]
```

**Capabilities involved**: 1 framework + 4 audit + research + compilation

---

### 2. [Knowledge Base Flow](fluxo-base-conhecimento.md)

**Objective**: Research a technology and transform it into an operational skill/instruction.

```mermaid
graph LR
    A[Researcher] --> B[Compiler/Generator] --> C[Validator] --> D[✅ Skill/Instruction]
```

**Capabilities involved**: 7 research + 4 compilation + 2 validation

---

### 3. [Quality Flow](fluxo-qualidade.md)

**Objective**: Verify and improve the quality of existing artifacts.

```mermaid
graph LR
    A[compatibility-review] --> B[instructions/skill-validator] --> C[project-analysis] --> D[✅ Quality]
```

**Capabilities involved**: 4 validation + (optional) 5 audit

---

### 4. [Implementation Flow](fluxo-implementacao.md)

**Objective**: Use existing agents for design + implementation.

```mermaid
graph LR
    A[Advisory Agent<br/>Design] --> B[Implementation Agent<br/>Code] --> C[Audit<br/>Validation]
```

**Capabilities involved**: Agents (Advisory → Implementation) + Audit

---

## When to Use Which Flow

| Situation | Flow |
|----------|-------|
| Starting a new automation domain | Project Creation |
| Learning a new technology | Knowledge Base |
| Periodic quality review | Quality |
| Agent project already exists, want to use it | Implementation |
| Everything from scratch (new technology + agent) | Knowledge Base → Project Creation |

---

## Flow Composition

The flows complement each other. Complete scenario "from scratch to production":

```mermaid
graph TD
    subgraph "Phase 1: Knowledge"
        R[Researcher] --> C[Compiler]
        C --> V1[Skill Validator]
    end

    subgraph "Phase 2: Project"
        RP[agent-router-pattern-validator]
    end

    subgraph "Phase 3: Quality"
        PV[project-analysis-validator] --> AU[audit-architecture-consensus]
    end

    V1 -->|ready skills| RP
    RP --> PV
    AU --> PROD[✅ Production Ready]
```
