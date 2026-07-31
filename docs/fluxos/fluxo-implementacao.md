# Flow: Implementation

Use existing agents for feature design + implementation.

---

## Diagram

```mermaid
flowchart TD
    START([User requirement]) --> TYPE{Needs<br/>design first?}
    
    TYPE -->|Yes - complex scope| ADV[Advisory Agent<br/>Design + ADRs + Roadmap]
    TYPE -->|No - clear scope| IMPL[Implementation Agent<br/>Generate code]
    
    ADV --> PLAN[Implementation Plan<br/>+ Delegation to agents]
    PLAN --> IMPL
    
    IMPL --> DOMAIN{Domain?}
    
    DOMAIN -->|Single domain| SINGLE[Implementation Agent<br/>P0-P5 with domain skills]
    DOMAIN -->|Cross-domain| ORCH[Orchestrator Agent<br/>P0-P5 multi-skill]
    
    SINGLE --> CODE[Generated Code]
    ORCH --> CODE
    
    CODE --> VALID[P5: Validate<br/>terraform fmt, mvn compile...]
    
    VALID -->|❌ fails| FIX[Fix + re-validate]
    FIX --> VALID
    
    VALID -->|✅ passes| AUDIT{Audit?}
    
    AUDIT -->|Yes — target .claude/| ARC[audit-cc-architecture-consensus]
    AUDIT -->|Yes — target .github/| ARCP[audit-architecture-consensus]
    AUDIT -->|No| DONE([✅ Implemented])
    
    ARC --> DONE
    ARCP --> DONE
```

---

## Implementation Patterns

### Pattern 1: Advisory → Implementation (Design-first)

For complex scopes or when the architecture is not clear.

```mermaid
sequenceDiagram
    participant U as User
    participant ADV as Advisory Agent
    participant IMP as Implementation Agent
    
    U->>ADV: "Design a serverless API"
    ADV->>ADV: P0-P5 (read-only)
    ADV->>U: ADR + Diagram + Delegation Plan
    Note over ADV: "Use @oci-terraform for X"<br/>"Use @oci-functions for Y"
    U->>IMP: "Provision X as per design"
    IMP->>IMP: P0-P5 (with code)
    IMP->>U: Generated + validated code
```

**Real example**: `oci-serverless-architect` (design) → `oci-terraform` (infrastructure)

---

### Pattern 2: Direct Implementation (Single domain)

For clear scopes in a specific domain.

```mermaid
sequenceDiagram
    participant U as User
    participant AG as Implementation Agent
    participant SK as Skills
    
    U->>AG: "Create API Gateway for function X"
    AG->>SK: P0: Load provisioning-oci-api-gateway
    SK->>AG: Patterns (✅⚠️🚫)
    AG->>AG: P1: Scan existing .tf files
    AG->>AG: P2: Extract patterns
    AG->>U: P3: Propose plan
    U->>AG: Approved
    AG->>AG: P4: Generate .tf files
    AG->>AG: P5: terraform fmt + validate
    AG->>U: ✅ Code ready
```

**Real example**: `oci-terraform` with skill `provisioning-oci-api-gateway`

---

### Pattern 3: Orchestrator (Cross-domain)

For implementations involving multiple technical domains with dependencies.

```mermaid
sequenceDiagram
    participant U as User
    participant OR as Orchestrator Agent
    participant SK1 as Java Skills
    participant SK2 as Terraform Skills
    
    U->>OR: "Create function + full infra"
    OR->>SK1: P0: Load developing-oci-functions-java
    OR->>SK2: P0: Load provisioning-oci-*
    OR->>OR: P1: Scan Java + Terraform
    OR->>OR: P2: Extract patterns from both
    OR->>U: P3: Propose cross-domain plan
    Note over OR: Order: Java → TF Function → TF IAM → TF API GW
    U->>OR: Approved
    OR->>OR: P4.1: Generate Java (handler, pom.xml)
    OR->>OR: P4.2: Generate TF (function resource)
    OR->>OR: P4.3: Generate TF (IAM policies)
    OR->>OR: P4.4: Generate TF (API Gateway route)
    OR->>OR: P5: mvn compile + terraform validate
    OR->>U: ✅ Complete stack
```

**Real example**: `oci-serverless-stack` (Java + Terraform)

---

## Dependency Between Patterns

```mermaid
graph TD
    A[Advisory] -->|"delegation plan"| B[Implementation]
    A -->|"delegation plan"| C[Orchestrator]
    B -->|"single domain"| D[Code]
    C -->|"multi domain"| D
```

| If the scope is... | Use |
|-----------------|-----|
| Undefined (needs design) | Advisory → Implementation |
| Clear, one domain | Direct Implementation |
| Clear, multiple domains | Direct Orchestrator |
| Complex, multiple domains | Advisory → Orchestrator |

---

## Capabilities Involved

| Step | Agent Type | Skills Used |
|-------|---------------|-------------------|
| Design | Advisory | Architecture skills (designing-*, architecting-*) |
| Single Implementation | Implementation | Domain skills (provisioning-*, developing-*) |
| Cross Implementation | Orchestrator | Skills from multiple domains |
| Validation | (built-in P5) | — |
| CC Audit | `audit-cc-architecture-consensus` (target `.claude/`) | — |
| Copilot Audit | `audit-architecture-consensus` (target `.github/`) | — |

---

## Execution Order in Cross-Domain

The Orchestrator respects dependencies between domains:

```
Layer 1: Networking    (base — no dependencies)
Layer 2: IAM           (depends on networking for compartments)
Layer 3: Core Service  (depends on IAM for policies)
Layer 4: Integration   (depends on service for OCIDs)
```

Each layer only starts after the previous one is complete and validated.

---

## Final Result

- **Advisory**: ADRs + diagram + delegation plan
- **Implementation**: Generated + validated code (fmt/compile)
- **Orchestrator**: Complete multi-domain stack + cross-domain validated

---

> **Audit reference**: For full details on CC vs Copilot variants, consensus criteria, and individual lenses → [architecture-auditor Manual](../manual/architecture-auditor.md)
