# Fluxo: Implementação

Usar agentes existentes para design + implementação de funcionalidades.

---

## Diagrama

```mermaid
flowchart TD
    START([Requisito do usuário]) --> TYPE{Precisa de<br/>design primeiro?}
    
    TYPE -->|Sim - escopo complexo| ADV[Advisory Agent<br/>Design + ADRs + Roadmap]
    TYPE -->|Não - escopo claro| IMPL[Implementation Agent<br/>Gerar código]
    
    ADV --> PLAN[Plano de Implementação<br/>+ Delegação para agents]
    PLAN --> IMPL
    
    IMPL --> DOMAIN{Domínio?}
    
    DOMAIN -->|Single domain| SINGLE[Implementation Agent<br/>P0-P5 com skills do domínio]
    DOMAIN -->|Cross-domain| ORCH[Orchestrator Agent<br/>P0-P5 multi-skill]
    
    SINGLE --> CODE[Código Gerado]
    ORCH --> CODE
    
    CODE --> VALID[P5: Validate<br/>terraform fmt, mvn compile...]
    
    VALID -->|❌ falha| FIX[Corrigir + re-validar]
    FIX --> VALID
    
    VALID -->|✅ passa| AUDIT{Auditar?}
    
    AUDIT -->|Sim| ARC[audit-architecture-consensus]
    AUDIT -->|Não| DONE([✅ Implementado])
    
    ARC --> DONE
```

---

## Padrões de Implementação

### Padrão 1: Advisory → Implementation (Design-first)

Para escopos complexos ou quando a arquitetura não está clara.

```mermaid
sequenceDiagram
    participant U as Usuário
    participant ADV as Advisory Agent
    participant IMP as Implementation Agent
    
    U->>ADV: "Design a serverless API"
    ADV->>ADV: P0-P5 (read-only)
    ADV->>U: ADR + Diagrama + Delegation Plan
    Note over ADV: "Use @oci-terraform para X"<br/>"Use @oci-functions para Y"
    U->>IMP: "Provisionar X conforme design"
    IMP->>IMP: P0-P5 (com código)
    IMP->>U: Código gerado + validado
```

**Exemplo real**: `oci-serverless-architect` (design) → `oci-terraform` (infraestrutura)

---

### Padrão 2: Implementation Direto (Single domain)

Para escopos claros em um domínio específico.

```mermaid
sequenceDiagram
    participant U as Usuário
    participant AG as Implementation Agent
    participant SK as Skills
    
    U->>AG: "Criar API Gateway para function X"
    AG->>SK: P0: Load provisioning-oci-api-gateway
    SK->>AG: Patterns (✅⚠️🚫)
    AG->>AG: P1: Scan existing .tf files
    AG->>AG: P2: Extract patterns
    AG->>U: P3: Propose plan
    U->>AG: Aprovado
    AG->>AG: P4: Generate .tf files
    AG->>AG: P5: terraform fmt + validate
    AG->>U: ✅ Código pronto
```

**Exemplo real**: `oci-terraform` com skill `provisioning-oci-api-gateway`

---

### Padrão 3: Orchestrator (Cross-domain)

Para implementações que envolvem múltiplos domínios técnicos com dependências.

```mermaid
sequenceDiagram
    participant U as Usuário
    participant OR as Orchestrator Agent
    participant SK1 as Java Skills
    participant SK2 as Terraform Skills
    
    U->>OR: "Criar function + infra completa"
    OR->>SK1: P0: Load developing-oci-functions-java
    OR->>SK2: P0: Load provisioning-oci-*
    OR->>OR: P1: Scan Java + Terraform
    OR->>OR: P2: Extract patterns de ambos
    OR->>U: P3: Propose cross-domain plan
    Note over OR: Ordem: Java → TF Function → TF IAM → TF API GW
    U->>OR: Aprovado
    OR->>OR: P4.1: Gerar Java (handler, pom.xml)
    OR->>OR: P4.2: Gerar TF (function resource)
    OR->>OR: P4.3: Gerar TF (IAM policies)
    OR->>OR: P4.4: Gerar TF (API Gateway route)
    OR->>OR: P5: mvn compile + terraform validate
    OR->>U: ✅ Stack completa
```

**Exemplo real**: `oci-serverless-stack` (Java + Terraform)

---

## Dependência entre Padrões

```mermaid
graph TD
    A[Advisory] -->|"delegation plan"| B[Implementation]
    A -->|"delegation plan"| C[Orchestrator]
    B -->|"single domain"| D[Código]
    C -->|"multi domain"| D
```

| Se o escopo é... | Use |
|-----------------|-----|
| Indefinido (precisa de design) | Advisory → Implementation |
| Claro, um domínio | Implementation direto |
| Claro, múltiplos domínios | Orchestrator direto |
| Complexo, múltiplos domínios | Advisory → Orchestrator |

---

## Capacidades Envolvidas

| Etapa | Tipo de Agente | Skills Consumidas |
|-------|---------------|-------------------|
| Design | Advisory | Skills de arquitetura (designing-*, architecting-*) |
| Implementação single | Implementation | Skills do domínio (provisioning-*, developing-*) |
| Implementação cross | Orchestrator | Skills de múltiplos domínios |
| Validação | (built-in P5) | — |
| Auditoria | audit-architecture-consensus | — |

---

## Ordem de Execução em Cross-Domain

O Orchestrator respeita dependências entre domínios:

```
Layer 1: Networking    (base — sem dependências)
Layer 2: IAM           (depende de networking para compartments)
Layer 3: Core Service  (depende de IAM para policies)
Layer 4: Integration   (depende de service para OCIDs)
```

Cada layer só inicia após a anterior estar completa e validada.

---

## Resultado Final

- **Advisory**: ADRs + diagrama + plano de delegação
- **Implementation**: Código gerado + validado (fmt/compile)
- **Orchestrator**: Stack multi-domínio completa + validada cross-domain
