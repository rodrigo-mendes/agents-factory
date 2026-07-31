# Agente: skill-author

> **Modelo:** `sonnet` | **Tools:** Read, Grep, Glob, Write, Edit
> **Papel:** Skill & Instructions Author — converte pesquisa validada em artefatos operacionais (SKILL.md e rules/instructions) prontos para uso por agentes.

**O que faz:** Lê um documento de pesquisa gerado por `framework-researcher`, aplica os padrões de autoria integrados ao `skill-creator` (three-tier, progressive disclosure, YAML correto) e produz um ou mais arquivos de skill ou instrução.

**O que NÃO faz:** Pesquisar tecnologias na web, auditar arquitetura, validar qualidade de artefatos existentes.

**Pré-condição universal:** O documento de pesquisa (`research_<Tech>_v<Version>.md`) deve existir e ter fontes datadas. Sem research file, o agente para e instrui a rodar um researcher primeiro.

---

## /skill-creator

> **Agente:** `skill-author` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use após ter um `research_<Tech>_v<Version>.md` de qualquer researcher e querer transformá-lo em uma SKILL.md operacional para Claude Code.

**Palavras-gatilho:** "criar skill de FastAPI", "gerar SKILL.md para Redis", "compilar pesquisa em skill", "transformar research em skill".

### Pré-condições

- Arquivo de pesquisa deve existir: `research_<TechName>_v<Version>.md`
- O arquivo deve conter Source Bibliography com fontes datadas
- Se o arquivo não existir → rodar `/researching-technical-frameworks` primeiro

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Caminho para o research file | ✅ | `StoryBeat/research_FastAPI_v0.115.md` |

### Exemplo de Chamada

```
/skill-creator StoryBeat/research_FastAPI_v0.115.md
```

O agente vai derivar automaticamente do arquivo:
- Nome da skill: `fastapi-async-api` (kebab-case, gerund preferido)
- Versão: `0.115`
- Seções Three-Tier: Mandatory_Patterns → ✅, Conditional_Patterns → ⚠️, Forbidden_Patterns → 🚫

### Workflow Interno (7 passos)

1. Aplica padrões integrados de autoria do `skill-creator` (baseline de qualidade)
2. Lê o research file em `$ARGUMENTS`
3. Mapeia seções da pesquisa para estrutura da skill
4. Aplica regras de frontmatter (name ≤ 64 chars, description com "Use when…")
5. Gera `SKILL.md` com corpo ≤ 500 linhas
6. Cria 3 cenários de avaliação em blueprints
7. Auto-verifica contra checklist de qualidade

### Output Produzido

```
.claude/skills/fastapi-async-api/
├── SKILL.md
└── blueprints/
    └── evaluation-scenarios.md
```

**Estrutura do `SKILL.md` gerado:**
```yaml
---
name: fastapi-async-api
description: >-
  Implements FastAPI 0.115 async endpoints following official patterns.
  Use when building REST APIs with FastAPI, Pydantic v2, and async SQLAlchemy.
allowed-tools: Read, Edit, Write, Bash
---
```

Corpo: Version Context, ✅ Always Do (com código executável), ⚠️ Ask First (com tabela de trade-offs), 🚫 Never Do (com alternativa inline), Verification Loop, External Resources.

### Verificação Pós-Geração

```bash
wc -l .claude/skills/fastapi-async-api/SKILL.md
# Esperado: ≤ 500

grep -c "### ✅\|### ⚠️\|### 🚫" .claude/skills/fastapi-async-api/SKILL.md
# Esperado: 3

test -f .claude/skills/fastapi-async-api/blueprints/evaluation-scenarios.md && echo "OK" || echo "MISSING"

grep -nE "(C:\\\\|/Users/|/home/)" .claude/skills/fastapi-async-api/SKILL.md
# Esperado: nenhuma saída (sem caminhos absolutos)
```

### Próximos Passos

- Validar qualidade → `/skill-best-practices-validator .claude/skills/fastapi-async-api/`
- Verificar saúde geral → `/project-analysis-validator .claude/`

### Nunca Fazer

- Invocar sem um research file — sem base de pesquisa, o agente para
- Pular a criação de `blueprints/evaluation-scenarios.md` — é obrigatório
- Colocar caminhos absolutos ou Windows-style no SKILL.md gerado
- Misturar conteúdo de versões diferentes no mesmo SKILL.md

---

## /methodologies-skill-generator

> **Agente:** `skill-author` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use quando quiser criar uma skill de uma **metodologia de engenharia ou processo** (Scrum, SAFe, Kanban, BPM, DORA, Team Topologies) **sem ter um research file prévio** — este comando pesquisa e gera a skill em um único pipeline.

**Palavras-gatilho:** "criar skill de Scrum", "skill SAFe 6", "metodologia de Kanban em skill", "gerar skill de DORA Metrics".

> **Diferença do `/skill-creator`:** Este faz pesquisa + geração em um único passo (tudo-em-um). O `/skill-creator` apenas gera a partir de um research file que já existe.

### Pré-condições

Nenhuma — pesquisa e geração são feitas internamente.

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Metodologia | ✅ | `Scrum`, `SAFe`, `Kanban`, `BPM`, `DORA` |
| Edição / versão | ✅ | `Scrum Guide 2020`, `SAFe 6.0` |
| Contexto de engenharia | Opcional | `squad de produto SaaS, 2 semanas sprint` |
| URL oficial | Opcional | `https://scrumguides.org/` |

### Exemplo de Chamada

```
/methodologies-skill-generator Scrum
```

O agente vai perguntar:
```
Edição: Scrum Guide 2020
Contexto: squad de produto com 8 pessoas, sprints de 2 semanas
```

### Pipeline Interno (5 fases)

1. **Classificação:** identifica o tipo de metodologia e complexidade
2. **Pesquisa autoritativa:** WebSearch/WebFetch em fontes oficiais com version absolutism
3. **Geração do SKILL.md:** aplica three-tier, YAML correto, blueprints
4. **Auto-validação:** verifica checklist de qualidade
5. **Output:** salva skill e confirma para o usuário

### Output Produzido

```
.claude/skills/scrum-sprint-practices/
├── SKILL.md
└── blueprints/
    └── evaluation-scenarios.md
```

### Próximos Passos

- `/skill-best-practices-validator .claude/skills/scrum-sprint-practices/`

---

## /architecture-approaches-skill-generator

> **Agente:** `skill-author` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use quando quiser criar uma skill de uma **metodologia ou notação de arquitetura de software** (C4, DDD, TOGAF, ADR, UML, ArchiMate, Event-Driven) **sem ter um research file prévio**.

**Palavras-gatilho:** "criar skill de C4 Model", "skill para DDD", "gerar skill de ADR", "skill para TOGAF 10", "notação de arquitetura em skill".

> **Diferença do `/skill-creator`:** Pipeline tudo-em-um (pesquisa + gera). Use `/skill-creator` se já tiver um `research_<Metodologia>.md` pronto de `/architecture-methodology-researcher`.

### Pré-condições

Nenhuma — pesquisa e geração são feitas internamente.

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Metodologia / notação | ✅ | `C4 Model`, `DDD`, `TOGAF`, `ADR`, `UML 2.5` |
| Edição / versão | ✅ | `C4 v4`, `TOGAF 10`, `UML 2.5` |
| Contexto de arquitetura | Opcional | `microserviços, plataforma de pagamentos` |
| URL oficial | Opcional | `https://c4model.com/` |

### Exemplo de Chamada

```
/architecture-approaches-skill-generator C4 Model
```

O agente vai perguntar:
```
Edição: v4 (2024)
Contexto: plataforma de e-commerce com 15 serviços
Nível de abstração: System Context + Container
```

### Mapeamento Pesquisa → Three-Tier

| Seção da Pesquisa | Tier da Skill |
|-------------------|---------------|
| Padrões obrigatórios | ✅ Always Do |
| Decisões arquiteturais | ⚠️ Ask First |
| Anti-padrões | 🚫 Never Do |

### Output Produzido

```
.claude/skills/c4-model-architecture/
├── SKILL.md
└── blueprints/
    └── evaluation-scenarios.md
```

---

## /terraform-instructions-compiler

> **Agente:** `skill-author` | **Contexto:** fork | **Modelo invocation:** desabilitado

### Quando Usar

Use após `/terraform-engineering-best-practices-researcher` para compilar a pesquisa em **arquivos `.instructions.md`** (regras de escopo) que o Copilot injeta automaticamente nos contextos corretos.

**Palavras-gatilho:** "compilar regras Terraform", "gerar instructions de Terraform", "criar .instructions.md de IaC", "compiler Terraform para projeto".

> **Diferença de `/skill-creator`:** Produz `.instructions.md` (não `SKILL.md`). Instructions são injetadas automaticamente por escopo de arquivo; skills são chamadas explicitamente. Use para definir padrões de projeto, não capacidades de geração.

### Pré-condições

- Research file deve existir: `research_Terraform_Engineering_Best_Practices_v<Version>.md`
- Gerado por `/terraform-engineering-best-practices-researcher`

### Inputs

| Campo | Obrigatório | Exemplo |
|-------|:-----------:|---------|
| Research file | ✅ | `StoryBeat/research_Terraform_Engineering_Best_Practices_v1.9.md` |
| Versão Terraform | Derivada do arquivo | `1.9` |
| Cloud Provider | Derivada do arquivo | `AWS` |
| Root do projeto | Opcional | `.github/instructions/` |

### Exemplo de Chamada

```
/terraform-instructions-compiler StoryBeat/research_Terraform_Engineering_Best_Practices_v1.9.md
```

### Pipeline Interno (4 fases)

1. **Lê** o research file e templates de referência:
   - `TEMPLATE.STANDARDS.instructions.md`
   - `TEMPLATE.CONFIG.instructions.md`
   - `TEMPLATE.SKILLS.instructions.md`
2. **Entrevista interativa** (até 16 perguntas): quais aspectos incluir, contexto do projeto
3. **Plano de geração**: define quais arquivos criar
4. **Geração**: salva os `.instructions.md` categorizados

### Output Produzido

```
.github/instructions/
├── terraform-config.instructions.md      ← setup de backend, providers, versions
├── terraform-standards.instructions.md   ← naming, estrutura de módulos, tags
└── terraform-skills.instructions.md      ← keywords → routing table de skills
```

Cada arquivo tem campo `applyTo:` correto:
- `terraform-config` → `applyTo: "**/*.tf"`
- `terraform-standards` → `applyTo: "**/*.tf, **/modules/**"`
- `terraform-skills` → `applyTo: "**/*.tf"`

### Verificação Pós-Geração

```bash
ls .github/instructions/terraform-*.instructions.md
grep "applyTo:" .github/instructions/terraform-*.instructions.md
```

### Próximos Passos

- Validar qualidade das instructions → `/instructions-best-practices-validator .github/instructions/`

---

## Princípios do Agente

**Progressive Disclosure** — SKILL.md fica abaixo de 500 linhas. Conteúdo extenso vai para `blueprints/` linkados.

**Three-Tier obrigatório** — nenhum tier pode estar vazio. Todo ✅ tem código executável. Todo 🚫 tem alternativa inline com impacto.

**Frontmatter válido:**
- `name`: ≤ 64 chars, kebab-case, sem palavras reservadas (`anthropic`, `claude`)
- `description`: terceira pessoa, inclui "Use when…", ≤ 1536 chars
- Skills usam `allowed-tools:`; agentes usam `tools:` — nunca trocar

---

*Ver [README do manual](README.md) para navegação geral.*
