# Capabilities Catalog

All Agents Factory capabilities organized by category.

## Summary

| Category | Count | Purpose |
|-----------|:---:|-----------|
| [Skills](skills.md) | 1 | Research skill with version absolutism; authoring patterns integrated into `skill-creator` |
| [Templates](templates.md) | 14 | Scaffolding to create any artifact |
| [Research](prompts-pesquisa.md) | 7 | Build validated knowledge bases |
| [Compilation](prompts-compilacao.md) | 4 | Transform research into skills/instructions |
| [Validation](prompts-validacao.md) | 4 | Verify artifact quality |
| [Auditing](prompts-arquitetura.md) | 8 | Multi-model architecture auditing |
| [Framework](prompts-framework.md) | 1 | Validate agent projects |
| [Evaluation](prompts-avaliacao.md) | 1 | Test skill behavior via LLM-as-judge |

---

## Full Table

| # | Name | Type | Category | Description |
|:-:|------|------|-----------|-----------|
| 1 | `researching-technical-frameworks` | Skill | Research | Researches technologies/frameworks with version absolutism |
| 2 | `agent-router-pattern-validator` | Prompt | Framework | Agent Router Pattern compliance analysis |
| 3 | `technical-framework-researcher-terraform` | Prompt | Research | Researches cloud services + Terraform |
| 4 | `terraform-engineering-best-practices-researcher` | Prompt | Research | Researches Terraform engineering practices |
| 5 | `architecture-methodology-researcher` | Prompt | Research | Researches architecture methodologies (C4, TOGAF, DDD) |
| 6 | `cloud-architecture-researcher` | Prompt | Research | Researches cloud architecture frameworks (WAF, CAF) |
| 7 | `business-domain-researcher` | Prompt | Research | Researches organizational and regulatory domains |
| 8 | `requirements-methodology-researcher` | Prompt | Research | Researches requirements frameworks (Scrum, SAFe) |
| 9 | `skill-creator` | Prompt | Compilation | Generates SKILL.md from research; incorporates authoring patterns (three-tier, YAML, blueprints) |
| 10 | `terraform-instructions-compiler` | Prompt | Compilation | Compiles Terraform research into .instructions.md |
| 11 | `architecture-approaches-skill-generator` | Prompt | Compilation | Generates SKILL.md for architecture methodology |
| 12 | `methodologies-skill-generator` | Prompt | Compilation | Generates SKILL.md for engineering methodology |
| 13 | `copilot-compatibility-review` | Prompt | Validation | Verifies compatibility with official Copilot docs |
| 14 | `instructions-best-practices-validator` | Prompt | Validation | Validates .instructions.md against best practices |
| 15 | `skill-best-practices-validator` | Prompt | Validation | Validates SKILL.md against Claude best practices |
| 16 | `project-analysis-validator` | Prompt | Validation | Overall project quality analysis |
| 17 | `audit-architecture-consensus` | Prompt | Auditing | Orchestrates 3 models in parallel + consensus (Copilot target) |
| 18 | `audit-architecture-scope` | Prompt | Auditing | Model A: responsibility hierarchy L0→L4 (Copilot target) |
| 19 | `audit-architecture-flow` | Prompt | Auditing | Model B: invocation chains prompt→agent→skill (Copilot target) |
| 20 | `audit-architecture-engine` | Prompt | Auditing | Model C: VS Code engine mechanics (Copilot target) |
| 21 | `audit-cc-architecture-consensus` | Prompt | Auditing | Orchestrates 3 models in parallel + consensus (Claude Code target) |
| 22 | `audit-cc-architecture-scope` | Prompt | Auditing | Model A: responsibility hierarchy G0→G4 (Claude Code target) |
| 23 | `audit-cc-architecture-flow` | Prompt | Auditing | Model B: invocation chains prompt→agent→skill (Claude Code target) |
| 24 | `audit-cc-architecture-engine` | Prompt | Auditing | Model C: Claude Code engine mechanics (Claude Code target) |
| 25 | `evaluating-skill-scenarios` | Prompt | Evaluation | Executes LLM-as-judge scenarios and judges skill behavior |

---

## How to Choose

```mermaid
flowchart TD
    START{What do you want to do?} --> Q1{Research something?}
    START --> Q2{Create an artifact?}
    START --> Q3{Validate quality?}
    START --> Q4{Audit architecture?}
    
    Q1 -->|Technology| R1[researching-technical-frameworks]
    Q1 -->|Terraform| R2[terraform-engineering-best-practices-researcher]
    Q1 -->|Architecture| R3[architecture-methodology-researcher]
    Q1 -->|Cloud| R4[cloud-architecture-researcher]
    Q1 -->|Domain| R5[business-domain-researcher]
    Q1 -->|Requirements| R6[requirements-methodology-researcher]
    
    Q2 -->|Skill| C1[skill-creator]
    Q2 -->|Instructions| C2[terraform-instructions-compiler]
    
    Q3 -->|Compatibility| V1[copilot-compatibility-review]
    Q3 -->|Instructions| V2[instructions-best-practices-validator]
    Q3 -->|Skills| V3[skill-best-practices-validator]
    Q3 -->|Whole project| V4[project-analysis-validator]
    
    Q4 -->|.claude/ project — full| A1CC[audit-cc-architecture-consensus]
    Q4 -->|.github/ project — full| A1[audit-architecture-consensus]
    Q4 -->|Individual lenses| AIND[See prompts-arquitetura.md]
```
