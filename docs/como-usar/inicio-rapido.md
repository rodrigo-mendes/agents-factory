# Início Rápido — 3 Passos

Pipeline mínimo de ponta-a-ponta: pesquisar tecnologia → criar skill → validar qualidade.
Tempo estimado: 15-20 minutos. Sem pré-condições além do Claude Code aberto no projecto.

---

## O que vai acontecer

```
Passo 1: /technical-framework-researcher
         → agente pede: tecnologia, versão, URL oficial, parceiros
         → produz: StoryBeat/research_FastAPI_v0.115.md

Passo 2: /skill-creator StoryBeat/research_FastAPI_v0.115.md
         → agente carrega padrões + aplica three-tier
         → produz: .claude/skills/fastapi-async-api/SKILL.md + blueprints/

Passo 3: /skill-best-practices-validator .claude/skills/fastapi-async-api/
         → agente verifica qualidade contra checklist oficial
         → produz: relatório em chat com score + itens de melhoria
```

> **Version Absolutism**: substitua `FastAPI 0.115` por qualquer tecnologia e versão específica.
> O nome da pasta e o ficheiro de pesquisa ajustam-se automaticamente.

---

## Passo 1 — Pesquisar a Tecnologia

```
/technical-framework-researcher
```

O agente vai pedir (interactivamente):

| Campo | Exemplo |
|-------|---------|
| Tecnologia | `FastAPI` |
| Versão | `0.115` |
| URL oficial | `https://fastapi.tiangolo.com/` |
| Parceiros de integração | `Pydantic v2, SQLAlchemy 2.0, pytest` |

**Output produzido**:

```
StoryBeat/research_FastAPI_v0.115.md
```

Secções que o ficheiro contém:
- `## Version_Context` — changelog e breaking changes
- `## Mandatory_Patterns (✅)` — padrões obrigatórios com código validado
- `## Conditional_Patterns (⚠️)` — decisões com trade-offs
- `## Forbidden_Patterns (🚫)` — anti-padrões com alternativas
- `## Source_Bibliography` — todas as fontes com URL + data

> **O que fazer se o agente parar**: se o agente disser "versão não encontrada" ou "não consigo
> confirmar a versão X", forneça o URL oficial exacto da documentação dessa versão.

---

## Passo 2 — Criar a Skill

```
/skill-creator StoryBeat/research_FastAPI_v0.115.md
```

O agente carrega o ficheiro de pesquisa e aplica automaticamente:
- Nome da skill: `fastapi-async-api` (derivado do nome + contexto)
- Estrutura three-tier: Mandatory_Patterns → ✅, Conditional → ⚠️, Forbidden → 🚫
- YAML frontmatter correto (name ≤ 64 chars, description com "Use when...")
- Blueprints com cenários de avaliação

**Output produzido**:

```
.claude/skills/fastapi-async-api/
├── SKILL.md                              ← Base de conhecimento versionada
└── blueprints/
    └── evaluation-scenarios.md           ← 3+ cenários de uso e avaliação
```

Verificação rápida:
```bash
wc -l .claude/skills/fastapi-async-api/SKILL.md   # deve ser ≤ 500
```

---

## Passo 3 — Validar a Skill

```
/skill-best-practices-validator .claude/skills/fastapi-async-api/
```

O agente verifica automaticamente:

| Check | Critério |
|-------|----------|
| Frontmatter `name` | ≤ 64 chars, kebab-case |
| Frontmatter `description` | Inclui "Use when…" |
| Seção ✅ Always Do | Presente com código executável |
| Seção ⚠️ Ask First | Presente com tabela de trade-offs |
| Seção 🚫 Never Do | Presente com alternativa + impacto |
| Tamanho | SKILL.md < 500 linhas |
| Blueprints | `evaluation-scenarios.md` existe com ≥ 3 cenários |
| Version absolutism | Versão única declarada |

**Output**: relatório em chat com score por dimensão e sugestões de melhoria concretas.

---

## Resultados Esperados

Depois dos 3 passos, tem:

- Uma base de conhecimento validada contra fontes oficiais, versionada e pronta para uso por agentes
- Uma skill com guardrails three-tier que qualquer agente pode carregar em P0
- Um relatório de qualidade confirmando que a skill segue os padrões do framework

---

## Próximos Passos

| Quer... | Vá para |
|---------|---------|
| Usar esta skill num agente | [Criando Agentes](criando-agentes.md) |
| Pesquisar outra tecnologia ou domínio | [Pesquisando Tecnologias](pesquisando-tecnologias.md) |
| Ver todos os tipos de researcher | [Catálogo — Pesquisa](../capacidades/prompts-pesquisa.md) |
| Validar o projecto inteiro | [Validando Artefatos](validando-artefatos.md) → Step 3 |
| Ver o pipeline completo com auditoria | [Fluxo de Criação de Projeto](../fluxos/fluxo-criacao-projeto.md) |
| Referência completa com todos os comandos | [Manual de Uso dos Agentes](../manual/README.md) |
