# Conventions

Standards and rules of the Agents Factory.

---

## Workflow P0-P5

Every implementation agent follows these 6 mandatory phases:

| Phase | Name | Action | Failure = |
|:----:|------|------|---------|
| **P0** | Verify Docs | Load mandatory skills and instructions | ❌ Abort |
| **P1** | Analyze | Scan existing code/infrastructure | ❌ Abort |
| **P2** | Consult | Extract ✅⚠️🚫 patterns from skills | ❌ Abort |
| **P3** | Propose | Propose plan and await user approval | ⏸️ Wait |
| **P4** | Implement | Generate code following exact patterns | — |
| **P5** | Validate | Run tools (fmt, compile, lint) | 🔄 Fix |

### Rules

- **Never skip P0**: Without loaded knowledge = guaranteed hallucination
- **Never skip P3**: Implementing without approval is prohibited
- **P5 is mandatory**: Unvalidated code is not delivered
- **Advisory agents**: P4 becomes "Deliver" (delivers designs, not code)

---

## Three-Tier Architecture (✅⚠️🚫)

Every skill organizes guardrails into 3 layers:

### ✅ Always Do (Tier 1)
- **Action**: Auto-execute without asking
- **Requirements**: Complete functional code, specific version, testable
- **Example**: "Always use `lifecycle { prevent_destroy = true }` in stateful resources"

### ⚠️ Ask First (Tier 2)
- **Action**: Present trade-offs and await user decision
- **Requirements**: Trade-off matrix, pros/cons, clear recommendation
- **Example**: "Module monorepo vs. multi-repo? [Pros: X, Cons: Y]. Which do you prefer?"

### 🚫 Never Do (Tier 3)
- **Action**: Automatically block, offer alternative
- **Requirements**: Anti-pattern description, impact, alternative with code
- **Example**: "Never use `terraform destroy` without explicit confirmation. Instead: use targeted destroy with `-target`"

---

## Version Absolutism

| Rule | Description |
|-------|-----------|
| 1 skill = 1 version | `provisioning-oci-functions-terraform-5.x` ≠ `provisioning-oci-functions-terraform-4.x` |
| Never conflict versions | Do not mix patterns from different versions in the same skill |
| Always explicit version | All sample code declares exact version |
| Reject > 12 months | Patterns older than 12 months without validation must be re-researched |
| Separate research | If 2 versions are needed, do 2 separate research files |

---

## Naming Conventions

### Skills
- **Format**: `gerund-noun-specific` (kebab-case)
- **Examples**:
  - ✅ `provisioning-oci-functions`
  - ✅ `researching-technical-frameworks`
  - ✅ `designing-oci-api-gateway`
  - ❌ `helper`, `utils`, `cloud-stuff`
  - ❌ `oci-functions` (missing verb)

### Prompts
- **Format**: `noun-noun-action` or `action-noun` (kebab-case)
- **Examples**:
  - ✅ `cloud-architecture-researcher`
  - ✅ `skill-best-practices-validator`
  - ✅ `agent-router-pattern-validator`

### Agents
- **Format**: `domain-role` (kebab-case)
- **Examples**:
  - ✅ `oci-terraform`
  - ✅ `oci-serverless-architect`
  - ✅ `oci-serverless-stack`

### General rules
- Always kebab-case (lowercase + hyphens)
- Folder name = YAML `name` field
- Maximum 64 characters for `name`
- Without XML tags in the name

---

## YAML Frontmatter

### Required fields (all artifacts)

```yaml
---
name: nome-do-artefato        # ≤64 chars, kebab-case
description: >
  Descrição em terceira pessoa, verbo de ação primeiro.
  Deve incluir "Use when..." para contexto de ativação.
  Máximo 1536 caracteres.
---
```

### Additional fields by type

**Sub-agents** (`.claude/agents/`): use the `tools:` field
```yaml
tools: ['Read', 'Edit', 'Write', 'Bash', 'WebSearch', 'WebFetch']
```

**Skills/Commands** (`.claude/skills/`): use the `allowed-tools:` field
```yaml
allowed-tools: ['Read', 'Edit', 'Write', 'Bash']
```

> **Important distinction**: `tools:` is the correct field for sub-agents; `allowed-tools:` is the correct field for skills and commands. Using the wrong field causes the artifact to be silently ignored.

**Commands** (entry-points):
```yaml
argument-hint: Sugestão de input para o usuário
```

### Rules
- `name`: ≤64 chars, `[a-z0-9-]` only
- `description`: ≤1536 chars, third person, verb first
- Without undocumented custom fields
- Valid YAML (no tabs, correct indentation)

---

## Responsibility Hierarchy

### GitHub Copilot (L0→L4)

| Layer | Artifact | Responsibility | Must not contain |
|:------:|----------|-----------------|-----------------|
| **L0** | `.vscode/settings.json` | Global workspace config | Logic |
| **L1** | `.instructions.md` | Project-wide standards (`applyTo:`) | Long sample code |
| **L2** | `SKILL.md` | Domain knowledge | Routing / orchestration |
| **L3** | `.agent.md` | P0-P5 orchestration | Hardcoded knowledge |
| **L4** | `.prompt.md` | User entry-point | Implementation logic |

### Claude Code (G0→G4)

| Layer | Artifact | Responsibility | Must not contain |
|:------:|----------|-----------------|-----------------|
| **G0** | `CLAUDE.md` | Global manifest — routing table + principles | Domain logic |
| **G1** | `.claude/agents/*.md` | Execution personas with full P0-P5 | Hardcoded knowledge |
| **G2** | `.claude/rules/*.md` | Automatic context by scope (`paths:`) | Extensive code |
| **G3** | `.claude/skills/*/SKILL.md` (`context: fork`) | User entry-points — routes to agent | Implementation logic |
| **G4** | `.claude/skills/*/SKILL.md` (meta-skills) | Knowledge bases — loaded by the agent in P0 | Routing/orchestration |

**Principle**: Each layer delegates downward, never upward.

---

## Blueprints

Every skill can have a `blueprints/` directory with auxiliary content:

```
skill-name/
├── SKILL.md
└── blueprints/
    ├── always-do-patterns.md    ← ✅ expanded patterns with full code
    └── never-do-patterns.md     ← 🚫 anti-patterns with detailed alternatives
```

- Blueprints are loaded by agents during P2 (Consult)
- They serve to keep SKILL.md concise while offering detail when necessary
- Code in blueprints must be functional and testable

---

## Agent Router Pattern

Separation of concerns pattern for agent projects.

### GitHub Copilot chain

```
.prompt.md (entry-point — L4)
  → .agent.md (P0-P5 orchestration — L3)
    → SKILL.md (domain knowledge — L2)
    → .instructions.md (project-wide configuration — L1)
```

### Claude Code chain

```
/comando-skill (context: fork — G3)
  → subagente .claude/agents/*.md (P0-P5 — G1)
    → meta-skill `researching-technical-frameworks` + padrões de autoria integrados ao `skill-creator` (P0 — G4)
    → rules .claude/rules/*.md (injectadas automaticamente por paths: — G2)
    → output (code / report / SKILL.md)
```

**Rules (both systems)**:
- Entry-point never implements — only collects context and routes
- Agent never contains hardcoded knowledge — always loads from skills/meta-skills
- Skill never does routing — only provides three-tier patterns
- Rules/Instructions never contain extensive code — only scope configuration
