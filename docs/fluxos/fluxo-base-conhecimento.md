# Fluxo: Base de Conhecimento

Pesquisar uma tecnologia/metodologia e transformar em artefato operacional (SKILL.md ou .instructions.md).

---

## Diagrama

```mermaid
flowchart TD
    START([Início]) --> CHOOSE{Que tipo de<br/>conhecimento?}
    
    CHOOSE -->|Tecnologia/Framework| R1[technical-framework-researcher]
    CHOOSE -->|Terraform + Cloud| R2[technical-framework-researcher-terraform]
    CHOOSE -->|Práticas Terraform| R3[terraform-engineering-best-practices-researcher]
    CHOOSE -->|Arquitetura| R4[architecture-methodology-researcher]
    CHOOSE -->|Cloud Framework| R5[cloud-architecture-researcher]
    CHOOSE -->|Domínio Negócio| R6[business-domain-researcher]
    CHOOSE -->|Requisitos/Agile| R7[requirements-methodology-researcher]
    
    R1 --> DOC[Documento de Pesquisa]
    R2 --> DOC
    R3 --> DOC
    R4 --> DOC
    R5 --> DOC
    R6 --> DOC
    R7 --> DOC
    
    DOC --> COMPILE{Compilar para<br/>qual formato?}
    
    COMPILE -->|SKILL.md genérico ou serviço cloud| C1[skill-creator]
    COMPILE -->|SKILL.md arquitetura| C2[architecture-approaches-skill-generator]
    COMPILE -->|SKILL.md metodologia| C3[methodologies-skill-generator]
    COMPILE -->|.instructions.md Terraform| C4[terraform-instructions-compiler]
    
    C1 --> ART[Artefato Gerado]
    C2 --> ART
    C3 --> ART
    C4 --> ART
    
    ART --> VALID[skill-best-practices-validator<br/>ou instructions-best-practices-validator]
    
    VALID -->|issues| IMPROVE[Melhorar]
    IMPROVE --> VALID
    
    VALID -->|✅ aprovado| DONE([✅ Artefato Pronto])
```

---

## Etapas Detalhadas

### Etapa 1: Pesquisa

**Escolha o researcher baseado no domínio:**

| Se você precisa de... | Use |
|----------------------|-----|
| Padrões de FastAPI v0.100 | `technical-framework-researcher` |
| Resources Terraform do OCI Functions | `technical-framework-researcher-terraform` |
| Estrutura de projeto Terraform | `terraform-engineering-best-practices-researcher` |
| Padrões C4 Model ou DDD | `architecture-methodology-researcher` |
| AWS Well-Architected | `cloud-architecture-researcher` |
| Processos de compliance financeira | `business-domain-researcher` |
| Práticas SAFe ou Shape Up | `requirements-methodology-researcher` |

**Input**: Tecnologia + versão + contexto
**Output**: Documento markdown de pesquisa validada

> ⚠️ Regra: sempre fornecer versão específica. Sem versão = sem pesquisa.

---

### Etapa 2: Compilação

**Escolha o compiler baseado no output desejado:**

| Pesquisa de... | Compiler | Output |
|---------------|----------|--------|
| Tecnologia genérica | `skill-creator` | `SKILL.md` + `blueprints/` |
| Serviço cloud + Terraform (`technical-framework-researcher-terraform`) | `skill-creator` | `SKILL.md` de provisionamento |
| Arquitetura (C4, DDD) | `architecture-approaches-skill-generator` | `SKILL.md` |
| Metodologia (Scrum, SAFe) | `methodologies-skill-generator` | `SKILL.md` |
| Práticas Terraform (`terraform-engineering-best-practices-researcher`) | `terraform-instructions-compiler` | Múltiplos `.instructions.md` |

**Input**: Documento de pesquisa (output da Etapa 1)
**Output**: Artefato operacional estruturado em three-tier

---

### Etapa 3: Validação

| Se gerou... | Valide com |
|------------|-----------|
| SKILL.md | `skill-best-practices-validator` |
| .instructions.md | `instructions-best-practices-validator` |

**Input**: Artefato gerado (output da Etapa 2)
**Output**: Relatório de qualidade + sugestões de melhoria

---

## Variantes do Fluxo

### Variante A: Skill de tecnologia
```
technical-framework-researcher → skill-creator → skill-best-practices-validator
```

### Variante B: Instructions Terraform
```
terraform-engineering-best-practices-researcher → terraform-instructions-compiler → instructions-best-practices-validator
```

### Variante C: Skill de arquitetura
```
architecture-methodology-researcher → architecture-approaches-skill-generator → skill-best-practices-validator
```

### Variante D: Skill de metodologia
```
requirements-methodology-researcher → methodologies-skill-generator → skill-best-practices-validator
```

---

## Capacidades Envolvidas

| Etapa | Capacidades | Qtd |
|-------|------------|:---:|
| Pesquisa | 7 researchers | 7 |
| Compilação | 4 compilers/generators | 4 |
| Validação | 2 validators | 2 |
| **Total** | | **13** |

---

## Inputs e Outputs entre Etapas

```mermaid
graph LR
    subgraph "Etapa 1"
        R[Researcher]
    end
    subgraph "Etapa 2"
        C[Compiler]
    end
    subgraph "Etapa 3"
        V[Validator]
    end
    
    R -->|"Markdown de pesquisa<br/>(padrões + código + versão)"| C
    C -->|"SKILL.md ou .instructions.md<br/>(three-tier structured)"| V
    V -->|"Relatório de qualidade<br/>(score + melhorias)"| DONE[✅]
```

---

## Resultado Final

- **SKILL.md**: Base de conhecimento versionada pronta para ser carregada por agentes
- **OU .instructions.md**: Configuração de projeto pronta para ser injetada automaticamente

## Próximos Passos

Após ter skills prontas:
- Usá-las em um agente existente → [Fluxo de Implementação](fluxo-implementacao.md)
- Criar um agente novo que use essas skills → [Fluxo de Criação de Projeto](fluxo-criacao-projeto.md)
