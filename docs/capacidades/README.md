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
| [Auditoria](prompts-arquitetura.md) | 5 | Auditar arquitetura multi-modelo |
| [Framework](prompts-framework.md) | 2 | Criar e validar projetos de agente |

---

## Tabela Completa

| # | Nome | Tipo | Categoria | Descrição |
|:-:|------|------|-----------|-----------|
| 1 | `authoring-agent-skills` | Skill | Meta | Padrões de criação de skills (three-tier, YAML, blueprints) |
| 2 | `researching-technical-frameworks` | Skill | Meta | Metodologia de pesquisa com version absolutism |
| 3 | `agent-bootstrap` | Prompt | Framework | Wizard interativo que gera projeto completo de agente |
| 4 | `agent-router-pattern-validator` | Prompt | Framework | Análise de conformidade com Agent Router Pattern |
| 5 | `technical-framework-researcher` | Prompt | Pesquisa | Pesquisa tecnologias/frameworks com fontes oficiais |
| 6 | `technical-framework-researcher-terraform` | Prompt | Pesquisa | Pesquisa serviços cloud + Terraform |
| 7 | `terraform-engineering-best-practices-researcher` | Prompt | Pesquisa | Pesquisa práticas de engenharia Terraform |
| 8 | `architecture-methodology-researcher` | Prompt | Pesquisa | Pesquisa metodologias de arquitetura (C4, TOGAF, DDD) |
| 9 | `cloud-architecture-researcher` | Prompt | Pesquisa | Pesquisa frameworks de arquitetura cloud (WAF, CAF) |
| 10 | `business-domain-researcher` | Prompt | Pesquisa | Pesquisa domínios organizacionais e regulatórios |
| 11 | `requirements-methodology-researcher` | Prompt | Pesquisa | Pesquisa frameworks de requisitos (Scrum, SAFe) |
| 12 | `skill-creator` | Prompt | Compilação | Gera SKILL.md a partir de pesquisa |
| 13 | `terraform-instructions-compiler` | Prompt | Compilação | Compila pesquisa Terraform em .instructions.md |
| 14 | `architecture-approaches-skill-generator` | Prompt | Compilação | Gera SKILL.md de metodologia de arquitetura |
| 15 | `methodologies-skill-generator` | Prompt | Compilação | Gera SKILL.md de metodologia de engenharia |
| 16 | `copilot-compatibility-review` | Prompt | Validação | Verifica compatibilidade com docs oficiais do Copilot |
| 17 | `instructions-best-practices-validator` | Prompt | Validação | Valida .instructions.md contra best practices |
| 18 | `skill-best-practices-validator` | Prompt | Validação | Valida SKILL.md contra Claude best practices |
| 19 | `project-analysis-validator` | Prompt | Validação | Análise de qualidade geral do projeto |
| 20 | `audit-architecture-consensus` | Prompt | Auditoria | Orquestra 3 modelos em paralelo + consenso |
| 21 | `audit-architecture-scope` | Prompt | Auditoria | Modelo A: hierarquia de responsabilidades L0→L4 |
| 22 | `audit-architecture-flow` | Prompt | Auditoria | Modelo B: cadeias de invocação prompt→agent→skill |
| 23 | `audit-architecture-engine` | Prompt | Auditoria | Modelo C: mecânicas do VS Code engine |

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
    Q2 -->|Agente completo| C3[agent-bootstrap]
    
    Q3 -->|Compatibilidade| V1[copilot-compatibility-review]
    Q3 -->|Instructions| V2[instructions-best-practices-validator]
    Q3 -->|Skills| V3[skill-best-practices-validator]
    Q3 -->|Projeto todo| V4[project-analysis-validator]
    
    Q4 -->|Auditoria completa| A1[audit-architecture-consensus]
    Q4 -->|Só escopo| A2[audit-architecture-scope]
    Q4 -->|Só fluxo| A3[audit-architecture-flow]
    Q4 -->|Só engine| A4[audit-architecture-engine]
```
