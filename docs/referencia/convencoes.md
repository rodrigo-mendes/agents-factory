# Convenções

Padrões e regras do Agents Factory.

---

## Workflow P0-P5

Todo agente de implementação segue estas 6 fases obrigatórias:

| Fase | Nome | Ação | Falha = |
|:----:|------|------|---------|
| **P0** | Verify Docs | Carregar skills e instructions obrigatórias | ❌ Abortar |
| **P1** | Analyze | Escanear código/infra existente | ❌ Abortar |
| **P2** | Consult | Extrair padrões ✅⚠️🚫 das skills | ❌ Abortar |
| **P3** | Propose | Propor plano e aguardar aprovação do usuário | ⏸️ Aguardar |
| **P4** | Implement | Gerar código seguindo padrões exatos | — |
| **P5** | Validate | Executar ferramentas (fmt, compile, lint) | 🔄 Corrigir |

### Regras

- **Nunca pular P0**: Sem conhecimento carregado = alucinação garantida
- **Nunca pular P3**: Implementar sem aprovação é proibido
- **P5 é obrigatório**: Código não validado não é entregue
- **Advisory agents**: P4 vira "Deliver" (entrega designs, não código)

---

## Three-Tier Architecture (✅⚠️🚫)

Toda skill organiza guardrails em 3 camadas:

### ✅ Always Do (Tier 1)
- **Ação**: Auto-executar sem perguntar
- **Requisitos**: Código funcional completo, versão específica, testável
- **Exemplo**: "Sempre usar `lifecycle { prevent_destroy = true }` em recursos stateful"

### ⚠️ Ask First (Tier 2)
- **Ação**: Apresentar trade-offs e aguardar decisão do usuário
- **Requisitos**: Trade-off matrix, prós/contras, recomendação clara
- **Exemplo**: "Module monorepo vs. multi-repo? [Prós: X, Contras: Y]. Qual prefere?"

### 🚫 Never Do (Tier 3)
- **Ação**: Bloquear automaticamente, oferecer alternativa
- **Requisitos**: Descrição do anti-padrão, impacto, alternativa com código
- **Exemplo**: "Nunca usar `terraform destroy` sem confirmação explícita. Ao invés: usar targeted destroy com `-target`"

---

## Version Absolutism

| Regra | Descrição |
|-------|-----------|
| 1 skill = 1 versão | `provisioning-oci-functions-terraform-5.x` ≠ `provisioning-oci-functions-terraform-4.x` |
| Nunca conflitar versões | Não misturar padrões de versões diferentes na mesma skill |
| Versão explícita sempre | Todo código de exemplo declara versão exata |
| Rejeitar > 12 meses | Padrões com mais de 12 meses sem validação devem ser re-pesquisados |
| Separar pesquisas | Se precisa de 2 versões, fazer 2 pesquisas separadas |

---

## Naming Conventions

### Skills
- **Formato**: `gerund-noun-specific` (kebab-case)
- **Exemplos**:
  - ✅ `provisioning-oci-functions`
  - ✅ `researching-technical-frameworks`
  - ✅ `designing-oci-api-gateway`
  - ❌ `helper`, `utils`, `cloud-stuff`
  - ❌ `oci-functions` (falta verbo)

### Prompts
- **Formato**: `noun-noun-action` ou `action-noun` (kebab-case)
- **Exemplos**:
  - ✅ `technical-framework-researcher`
  - ✅ `skill-best-practices-validator`
  - ✅ `agent-router-pattern-validator`

### Agents
- **Formato**: `domain-role` (kebab-case)
- **Exemplos**:
  - ✅ `oci-terraform`
  - ✅ `oci-serverless-architect`
  - ✅ `oci-serverless-stack`

### Regras gerais
- Sempre kebab-case (minúsculas + hifens)
- Folder name = YAML `name` field
- Máximo 64 caracteres para `name`
- Sem XML tags no nome

---

## YAML Frontmatter

### Campos obrigatórios (todos os artefatos)

```yaml
---
name: nome-do-artefato        # ≤64 chars, kebab-case
description: >
  Descrição em terceira pessoa, verbo de ação primeiro.
  Deve incluir "Use when..." para contexto de ativação.
  Máximo 1536 caracteres.
---
```

### Campos adicionais por tipo

**Subagentes** (`.claude/agents/`): usam o campo `tools:`
```yaml
tools: ['Read', 'Edit', 'Write', 'Bash', 'WebSearch', 'WebFetch']
```

**Skills/Comandos** (`.claude/skills/`): usam o campo `allowed-tools:`
```yaml
allowed-tools: ['Read', 'Edit', 'Write', 'Bash']
```

> **Distinção importante**: `tools:` é o campo correto para subagentes; `allowed-tools:` é o campo correto para skills e comandos. Usar o campo errado faz o artefato ser ignorado silenciosamente.

**Comandos** (entry-points):
```yaml
argument-hint: Sugestão de input para o usuário
```

### Regras
- `name`: ≤64 chars, `[a-z0-9-]` apenas
- `description`: ≤1536 chars, terceira pessoa, verbo primeiro
- Sem campos customizados não documentados
- YAML válido (sem tabs, indentação correta)

---

## Hierarquia de Responsabilidades

### GitHub Copilot (L0→L4)

| Camada | Artefato | Responsabilidade | Não deve conter |
|:------:|----------|-----------------|-----------------|
| **L0** | `.vscode/settings.json` | Config global do workspace | Lógica |
| **L1** | `.instructions.md` | Padrões project-wide (`applyTo:`) | Código de exemplo longo |
| **L2** | `SKILL.md` | Conhecimento de domínio | Routing / orchestration |
| **L3** | `.agent.md` | Orquestração P0-P5 | Knowledge hardcoded |
| **L4** | `.prompt.md` | Entry-point do usuário | Lógica de implementação |

### Claude Code (G0→G4)

| Camada | Artefato | Responsabilidade | Não deve conter |
|:------:|----------|-----------------|-----------------|
| **G0** | `CLAUDE.md` | Manifesto global — routing table + princípios | Lógica de domínio |
| **G1** | `.claude/agents/*.md` | Personas de execução com P0-P5 completo | Knowledge hardcoded |
| **G2** | `.claude/rules/*.md` | Contexto automático por scope (`paths:`) | Código extenso |
| **G3** | `.claude/skills/*/SKILL.md` (`context: fork`) | Entry-points de utilizador — roteia para agente | Lógica de implementação |
| **G4** | `.claude/skills/*/SKILL.md` (meta-skills) | Bases de conhecimento — carregadas pelo agente em P0 | Routing/orchestration |

**Princípio**: Cada camada delega para baixo, nunca para cima.

---

## Blueprints

Toda skill pode ter um diretório `blueprints/` com conteúdo auxiliar:

```
skill-name/
├── SKILL.md
└── blueprints/
    ├── always-do-patterns.md    ← Padrões ✅ expandidos com código completo
    └── never-do-patterns.md     ← Anti-padrões 🚫 com alternativas detalhadas
```

- Blueprints são carregados por agentes durante P2 (Consult)
- Servem para manter a SKILL.md concisa enquanto oferece detalhe quando necessário
- Código nos blueprints deve ser funcional e testável

---

## Agent Router Pattern

Padrão de separação de concerns para projetos de agente.

### Cadeia GitHub Copilot

```
.prompt.md (entry-point — L4)
  → .agent.md (orquestração P0-P5 — L3)
    → SKILL.md (conhecimento de domínio — L2)
    → .instructions.md (configuração project-wide — L1)
```

### Cadeia Claude Code

```
/comando-skill (context: fork — G3)
  → subagente .claude/agents/*.md (P0-P5 — G1)
    → meta-skills authoring-agent-skills + researching-technical-frameworks (P0 — G4)
    → rules .claude/rules/*.md (injectadas automaticamente por paths: — G2)
    → output (código / relatório / SKILL.md)
```

**Regras (ambos os sistemas)**:
- Entry-point nunca implementa — só coleta contexto e roteia
- Agente nunca contém knowledge hardcoded — sempre carrega de skills/meta-skills
- Skill nunca faz routing — só fornece padrões three-tier
- Rules/Instructions nunca contêm código extenso — só configuração de escopo
