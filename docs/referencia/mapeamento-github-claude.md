# Mapeamento .github/ ↔ .claude/

Tabela de equivalência entre os artefatos do GitHub Copilot (`.github/`) e os do Claude Code (`.claude/`).

O projeto opera em **regime de coexistência**: `.github/` e `.claude/` coexistem no repositório, cada um
servindo seu respectivo runtime. Ambos implementam o mesmo conjunto de capacidades operacionais com
artefatos nativos de cada plataforma.

---

## Prompts Copilot → Skills Claude Code

| # | Prompt Copilot (`.github/prompts/`) | Skill Claude Code (`.claude/skills/`) | Categoria | Status |
|:-:|-------------------------------------|---------------------------------------|-----------|--------|
| 1 | `technical-framework-researcher.prompt.md` | `researching-technical-frameworks/SKILL.md` | Pesquisa | ✅ Equivalente |
| 2 | `technical-framework-researcher-terraform.prompt.md` | `technical-framework-researcher-terraform/SKILL.md` | Pesquisa | ✅ Equivalente |
| 3 | `terraform-engineering-best-practices-researcher.prompt.md` | `terraform-engineering-best-practices-researcher/SKILL.md` | Pesquisa | ✅ Equivalente |
| 4 | `architecture-methodology-researcher.prompt.md` | `architecture-methodology-researcher/SKILL.md` | Pesquisa | ✅ Equivalente |
| 5 | `cloud-architecture-researcher.prompt.md` | `cloud-architecture-researcher/SKILL.md` | Pesquisa | ✅ Equivalente |
| 6 | `business-domain-researcher.prompt.md` | `business-domain-researcher/SKILL.md` | Pesquisa | ✅ Equivalente |
| 7 | `requirements-methodology-researcher.prompt.md` | `requirements-methodology-researcher/SKILL.md` | Pesquisa | ✅ Equivalente |
| 8 | `skill-creator.prompt.md` | `skill-creator/SKILL.md` | Compilação | ✅ Equivalente |
| 9 | `terraform-instructions-compiler.prompt.md` | `terraform-instructions-compiler/SKILL.md` | Compilação | ✅ Equivalente |
| 10 | `archtecture-approches-skill-generator.prompt.md` ⚠️ | `architecture-approaches-skill-generator/SKILL.md` | Compilação | ✅ Equivalente (typo no filename Copilot) |
| 11 | `methodologies-skill-generator.prompt.md` | `methodologies-skill-generator/SKILL.md` | Compilação | ✅ Equivalente |
| 12 | `copilot-compatibility-review.prompt.md` | `copilot-compatibility-review/SKILL.md` | Validação | ✅ Equivalente |
| 13 | `instructions-best-practices-validator.prompt.md` | `instructions-best-practices-validator/SKILL.md` | Validação | ✅ Equivalente |
| 14 | `skill-best-practices-validator.prompt.md` | `skill-best-practices-validator/SKILL.md` | Validação | ✅ Equivalente |
| 15 | `project-quality-improvements.md` ⚠️ | `project-analysis-validator/SKILL.md` | Validação | ⚠️ Renomeado e escopo ampliado no CC |
| 16 | `agent-router-pattern-validator.prompt.md` | `agent-router-pattern-validator/SKILL.md` | Validação | ✅ Equivalente |
| 17 | `audit-architecture-consensus.prompt.md` | `audit-architecture-consensus/SKILL.md` | Auditoria Copilot | ✅ Equivalente |
| 18 | `audit-architecture-scope.prompt.md` | `audit-architecture-scope/SKILL.md` | Auditoria Copilot | ✅ Equivalente |
| 19 | `audit-architecture-flow.prompt.md` | `audit-architecture-flow/SKILL.md` | Auditoria Copilot | ✅ Equivalente |
| 20 | `audit-architecture-engine.prompt.md` | `audit-architecture-engine/SKILL.md` | Auditoria Copilot | ✅ Equivalente |

---

## Capacidades Exclusivas do Claude Code

As seguintes skills existem apenas em `.claude/` — não têm equivalente Copilot porque auditam
especificamente a arquitetura de projetos Claude Code.

| Skill Claude Code | Categoria | Justificativa |
|-------------------|-----------|---------------|
| `audit-cc-architecture-consensus/SKILL.md` | Auditoria CC | Audita `.claude/` — não existe no Copilot |
| `audit-cc-architecture-scope/SKILL.md` | Auditoria CC | Audita `.claude/` — não existe no Copilot |
| `audit-cc-architecture-flow/SKILL.md` | Auditoria CC | Audita `.claude/` — não existe no Copilot |
| `audit-cc-architecture-engine/SKILL.md` | Auditoria CC | Audita `.claude/` — não existe no Copilot |

---

## Meta-Skills (presentes em ambos os sistemas)

| Meta-Skill | Copilot | Claude Code |
|------------|---------|-------------|
| `authoring-agent-skills` | `.github/skills/authoring-agent-skills/SKILL.md` | *(integrado ao `skill-creator`)* |
| `researching-technical-frameworks` | `.github/skills/researching-technical-frameworks/SKILL.md` | `.claude/skills/researching-technical-frameworks/SKILL.md` |

> **Divergência**: No Claude Code, os padrões de autoria do `authoring-agent-skills` foram
> incorporados diretamente ao `skill-creator`, eliminando a indireção. O Copilot mantém as duas
> skills separadas.

---

## Templates (espelho .github/ ↔ .claude/)

| Tipo | Copilot (`.github/templates/`) | Claude Code (`.claude/templates/`) |
|------|-------------------------------|-------------------------------------|
| Agent | `agents/TEMPLATE.AGENT.md` | `agents/TEMPLATE.AGENT.md` |
| Agent | `agents/TEMPLATE.ADVISORY-AGENT.md` | `agents/TEMPLATE.ADVISORY-AGENT.md` |
| Agent | `agents/TEMPLATE.ORCHESTRATOR-AGENT.md` | `agents/TEMPLATE.ORCHESTRATOR-AGENT.md` |
| Prompt | `prompts/TEMPLATE.RESEARCH.prompt.md` | `prompts/TEMPLATE.RESEARCH.prompt.md` |
| Prompt | `prompts/TEMPLATE.GENERATOR.prompt.md` | `prompts/TEMPLATE.GENERATOR.prompt.md` |
| Prompt | `prompts/TEMPLATE.VALIDATION.prompt.md` | `prompts/TEMPLATE.VALIDATION.prompt.md` |
| Prompt | `prompts/TEMPLATE.ENTRY-POINT.prompt.md` | `prompts/TEMPLATE.ENTRY-POINT.prompt.md` |
| Prompt | `prompts/TEMPLATE.FEATURE-ADD.prompt.md` | `prompts/TEMPLATE.FEATURE-ADD.prompt.md` |
| Prompt | `prompts/TEMPLATE.DESIGN.prompt.md` | `prompts/TEMPLATE.DESIGN.prompt.md` |
| Skill | `skills/TEMPLATE.SKILL.md` | `skills/TEMPLATE.SKILL.md` |
| Instrução/Regra | `instructions/TEMPLATE.CONFIG.instructions.md` | `rules/TEMPLATE.CONFIG.md` |
| Instrução/Regra | `instructions/TEMPLATE.STANDARDS.instructions.md` | `rules/TEMPLATE.STANDARDS.md` |
| Instrução/Regra | `instructions/TEMPLATE.SKILLS.instructions.md` | `rules/TEMPLATE.SKILLS.md` |
| Report | `reports/POST_MORTEM_TEMPLATE.md` | `reports/POST_MORTEM_TEMPLATE.md` |

> **Diferença estrutural**: `.github/` usa `instructions/` (formato `.instructions.md`); `.claude/`
> usa `rules/` (formato `.md` simples com campo `paths:` no frontmatter).

---

## Anomalias Conhecidas em .github/

| Arquivo | Problema |
|---------|----------|
| `archtecture-approches-skill-generator.prompt.md` | Typo no filename — falta `i` em `architecture` e `c` em `approaches` |
| `project-quality-improvements.md` | Extensão incorreta — falta `.prompt` antes de `.md`; conteúdo foi renomeado e expandido para `project-analysis-validator` no Claude Code |

---

## Resumo de Contagens

| Sistema | Prompts/Skills operacionais | Meta-skills | Agents | Templates | Rules/Instructions |
|---------|:--:|:--:|:--:|:--:|:--:|
| `.github/` (Copilot) | 20 | 2 | 0 | 15 | 0 |
| `.claude/` (Claude Code) | 24 | 1 | 4 | 14 | 1 |

> `.github/` tem 15 templates (inclui `README.md`); `.claude/` tem 14 (sem README interno).
