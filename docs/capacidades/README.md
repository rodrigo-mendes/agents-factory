# Catálogo de Capacidades

Todas as capacidades do Agents Factory organizadas por categoria.

## Resumo

| Categoria | Qtd | Propósito |
|-----------|:---:|-----------|
| [Skills](skills.md) | 2 | Meta-skills que definem padrões do framework |
| [Templates](templates.md) | 14 | Scaffolding para criar qualquer artefato |
| [Pesquisa](prompts-pesquisa.md) | 7 | Construir bases de conhecimento validadas |
| [Compilação](prompts-compilacao.md) | 4 | Transformar pesquisa em skills/instructions |
| [Validação](prompts-validacao.md) | 4 | Verificar qualidade de artefatos |
| [Auditoria](prompts-arquitetura.md) | 8 | Auditar arquitetura multi-modelo |
| [Framework](prompts-framework.md) | 1 | Validar projetos de agente |

---

## Tabela Completa

| # | Nome | Tipo | Categoria | Descrição |
|:-:|------|------|-----------|-----------|
| 1 | `authoring-agent-skills` | Skill | Meta | Padrões de criação de skills (three-tier, YAML, blueprints) |
| 2 | `researching-technical-frameworks` | Skill | Meta | Metodologia de pesquisa com version absolutism |
| 3 | `agent-router-pattern-validator` | Prompt | Framework | Análise de conformidade com Agent Router Pattern |
| 4 | `technical-framework-researcher` | Prompt | Pesquisa | Pesquisa tecnologias/frameworks com fontes oficiais |
| 5 | `technical-framework-researcher-terraform` | Prompt | Pesquisa | Pesquisa serviços cloud + Terraform |
| 6 | `terraform-engineering-best-practices-researcher` | Prompt | Pesquisa | Pesquisa práticas de engenharia Terraform |
| 7 | `architecture-methodology-researcher` | Prompt | Pesquisa | Pesquisa metodologias de arquitetura (C4, TOGAF, DDD) |
| 8 | `cloud-architecture-researcher` | Prompt | Pesquisa | Pesquisa frameworks de arquitetura cloud (WAF, CAF) |
| 9 | `business-domain-researcher` | Prompt | Pesquisa | Pesquisa domínios organizacionais e regulatórios |
| 10 | `requirements-methodology-researcher` | Prompt | Pesquisa | Pesquisa frameworks de requisitos (Scrum, SAFe) |
| 11 | `skill-creator` | Prompt | Compilação | Gera SKILL.md a partir de pesquisa |
| 12 | `terraform-instructions-compiler` | Prompt | Compilação | Compila pesquisa Terraform em .instructions.md |
| 13 | `architecture-approaches-skill-generator` | Prompt | Compilação | Gera SKILL.md de metodologia de arquitetura |
| 14 | `methodologies-skill-generator` | Prompt | Compilação | Gera SKILL.md de metodologia de engenharia |
| 15 | `copilot-compatibility-review` | Prompt | Validação | Verifica compatibilidade com docs oficiais do Copilot |
| 16 | `instructions-best-practices-validator` | Prompt | Validação | Valida .instructions.md contra best practices |
| 17 | `skill-best-practices-validator` | Prompt | Validação | Valida SKILL.md contra Claude best practices |
| 18 | `project-analysis-validator` | Prompt | Validação | Análise de qualidade geral do projeto |
| 19 | `audit-architecture-consensus` | Prompt | Auditoria | Orquestra 3 modelos em paralelo + consenso (alvo Copilot) |
| 20 | `audit-architecture-scope` | Prompt | Auditoria | Modelo A: hierarquia de responsabilidades L0→L4 (alvo Copilot) |
| 21 | `audit-architecture-flow` | Prompt | Auditoria | Modelo B: cadeias de invocação prompt→agent→skill (alvo Copilot) |
| 22 | `audit-architecture-engine` | Prompt | Auditoria | Modelo C: mecânicas do VS Code engine (alvo Copilot) |
| 23 | `audit-cc-architecture-consensus` | Prompt | Auditoria | Orquestra 3 modelos em paralelo + consenso (alvo Claude Code) |
| 24 | `audit-cc-architecture-scope` | Prompt | Auditoria | Modelo A: hierarquia de responsabilidades G0→G4 (alvo Claude Code) |
| 25 | `audit-cc-architecture-flow` | Prompt | Auditoria | Modelo B: cadeias de invocação prompt→agent→skill (alvo Claude Code) |
| 26 | `audit-cc-architecture-engine` | Prompt | Auditoria | Modelo C: mecânicas do Claude Code engine (alvo Claude Code) |

---

## Como Escolher

```mermaid
flowchart TD
    START{O que você quer fazer?} --> Q1{Pesquisar algo?}
    START --> Q2{Criar artefato?}
    START --> Q3{Validar qualidade?}
    START --> Q4{Auditar arquitetura?}
    
    Q1 -->|Tecnologia| R1[technical-framework-researcher]
    Q1 -->|Terraform| R2[terraform-engineering-best-practices-researcher]
    Q1 -->|Arquitetura| R3[architecture-methodology-researcher]
    Q1 -->|Cloud| R4[cloud-architecture-researcher]
    Q1 -->|Domínio| R5[business-domain-researcher]
    Q1 -->|Requisitos| R6[requirements-methodology-researcher]
    
    Q2 -->|Skill| C1[skill-creator]
    Q2 -->|Instructions| C2[terraform-instructions-compiler]
    
    Q3 -->|Compatibilidade| V1[copilot-compatibility-review]
    Q3 -->|Instructions| V2[instructions-best-practices-validator]
    Q3 -->|Skills| V3[skill-best-practices-validator]
    Q3 -->|Projeto todo| V4[project-analysis-validator]
    
    Q4 -->|Projeto .claude/ — completa| A1CC[audit-cc-architecture-consensus]
    Q4 -->|Projeto .github/ — completa| A1[audit-architecture-consensus]
    Q4 -->|Lentes individuais| AIND[Ver prompts-arquitetura.md]
```
