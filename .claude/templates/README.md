# Templates Directory

Templates for creating new agents, skills, prompts, and rules. Each template is a parameterized blueprint — replace `[PLACEHOLDER]` variables with your specific values.

> **Claude Code variants.** These templates were adapted for the Claude Code format. Mapping
> from GitHub Copilot:
>
> | Copilot | Claude Code | Key Difference |
> |---|---|---|
> | `agents/*.agent.md` (`tools: ['read','search',...]`) | `agents/*.md` (`tools: Read, Grep, Glob, ...`) | subagent; tool names translated; add "Use when…" and optional `model:` |
> | `instructions/*.instructions.md` (`applyTo:`) | `rules/*.md` (`paths:`) | on-demand path-based loading |
> | `prompts/*.prompt.md` (`agent:`) | `skills/<n>/SKILL.md` (`context: fork` + `agent:`) | `/name` command runs inside the subagent; add `disable-model-invocation: true` |
> | `skills/*/SKILL.md` | `skills/*/SKILL.md` | same; see frontmatter options in `skills/TEMPLATE.SKILL.md` |
>
> The **prompt** templates below remain as content-structure references — when generating the
> final artifact for Claude Code, package it as `skills/<n>/SKILL.md` with the frontmatter above.

## Decision Tree: Which Template Do I Use?

```
What are you creating?
│
├─ An AGENT (.agent.md)
│  ├─ Generates code/files directly? → TEMPLATE.AGENT.md (Implementation Agent)
│  ├─ Advisory only (ADRs, diagrams)? → TEMPLATE.ADVISORY-AGENT.md
│  └─ Coordinates multiple domains?   → TEMPLATE.ORCHESTRATOR-AGENT.md
│
├─ A PROMPT (.prompt.md)
│  ├─ Guides user to implement a feature?       → TEMPLATE.FEATURE-ADD.prompt.md
│  ├─ Designs/reviews architecture (advisory)?  → TEMPLATE.DESIGN.prompt.md
│  ├─ Researches a technology/framework?        → TEMPLATE.RESEARCH.prompt.md
│  ├─ Validates artifacts against standards?    → TEMPLATE.VALIDATION.prompt.md
│  ├─ Compiles research into operational files?  → TEMPLATE.GENERATOR.prompt.md  (formerly COMPILER)
│  ├─ Scaffolds an entire agent project?         → *(not implemented — use templates manually)*
│  └─ Collects context and routes to an agent?   → TEMPLATE.ENTRY-POINT.prompt.md
│
├─ A SKILL (SKILL.md)
│  └─ Always → TEMPLATE.SKILL.md
│
└─ An INSTRUCTION (.instructions.md)
   ├─ Project config, structure, dependencies? → TEMPLATE.CONFIG.md
   ├─ Code standards, patterns, conventions?   → TEMPLATE.STANDARDS.md
   └─ Skill/prompt routing & integration?      → TEMPLATE.SKILLS.md
```

---

## Template Inventory

### Agents (`templates/agents/`)

| Template | Pattern | Tools | Use When |
|----------|---------|-------|----------|
| `TEMPLATE.AGENT.md` | Implementation (P0-P5) | read, editFiles, createFile, runInTerminal, search | Creating an agent that generates code/files |
| `TEMPLATE.ADVISORY-AGENT.md` | Advisory (P0-P5) | read, search | Creating an agent that only recommends (no edits) |
| `TEMPLATE.ORCHESTRATOR-AGENT.md` | Orchestrator (P0-P5) | read, editFiles, createFile, runInTerminal, search | Creating an agent that coordinates across domains |

### Prompts (`templates/prompts/`)

| Template | Category | Skill Loading | Use When |
|----------|----------|---------------|----------|
| `TEMPLATE.FEATURE-ADD.prompt.md` | Feature implementation | Yes (mandatory + conditional) | Guiding implementation of a specific capability |
| `TEMPLATE.DESIGN.prompt.md` | Architecture design | Single design skill | Collecting context for advisory agent to produce ADRs/diagrams |
| `TEMPLATE.RESEARCH.prompt.md` | Knowledge building | No (IS the source) | Researching a technology to build knowledge base |
| `TEMPLATE.VALIDATION.prompt.md` | Quality assessment | Reference only | Validating artifacts against standards |
| `TEMPLATE.GENERATOR.prompt.md` | Research-to-instructions compiler | No (uses templates) | Compiling research into operational .instructions.md files via interactive interview |
| `TEMPLATE.ENTRY-POINT.prompt.md` | Agent routing | No (delegated) | Collecting context and routing to an agent |

### Skills (`templates/skills/`)

| Template | Use When |
|----------|----------|
| `TEMPLATE.SKILL.md` | Documenting versioned technology patterns with ✅/⚠️/🚫 guardrails |

### Instructions (`templates/rules/`)

| Template | applyTo Pattern | Use When |
|----------|-----------------|----------|
| `TEMPLATE.CONFIG.md` | Config/project files | Enforcing project setup, dependencies, structure |
| `TEMPLATE.STANDARDS.md` | Source code files | Enforcing coding standards, patterns, conventions |
| `TEMPLATE.SKILLS.md` | All domain files | Routing requests to skills and prompts |

---

## Key Variables (Shared Across Templates)

| Variable | Description | Example |
|----------|-------------|---------|
| `[agent-name]` | Agent identifier (kebab-case) | `oci-terraform` |
| `[LANGUAGE]` | Programming language | `Java`, `Python` |
| `[FRAMEWORK]` | Technology framework | `FDK v1.1.x`, `Terraform` |
| `[SPECIALTY]` | Domain expertise area | `OCI Infrastructure Provisioner` |
| `[VERSION]` | Target version | `1.11`, `17`, `3.x` |
| `[skill-name]` | Skill directory name (kebab-case) | `provisioning-oci-functions` |
| `[prefix]` | Instruction file prefix | `terraform`, `java-functions` |

---

## Conventions

1. **Language**: All templates in English
2. **YAML frontmatter**: Minimal — `name`, `description`, `tools` (agents); `description`, `agent`, `argument-hint` (prompts)
3. **Guardrail tiers**: ✅ Always Do, ⚠️ Ask First, 🚫 Never Do — used consistently across skills and instructions
4. **Workflow**: Implementation and orchestrator agents use P0-P5 (Verify → Analyze → Consult → Propose → Implement → Validate)
5. **Single source of truth**: Prompts reference skills; they don't duplicate code examples
6. **Blueprints**: Skills use `blueprints/` subdirectory for detailed code examples beyond inline patterns

---

## Live Examples (no more `examples/`)

This factory is **technology-agnostic** — we do not maintain concrete example implementations inside
`templates/`. To see real artifacts as reference, look at the **live artifacts** in this repo:

- **Subagents** — `.claude/agents/` (e.g., `framework-researcher.md`, `architecture-auditor.md`)
- **Skills / commands** — `.claude/skills/` (e.g., `researching-technical-frameworks/`, `audit-architecture-scope/`)
- **Rules** — `.claude/rules/` (e.g., `skill-frontmatter.md`)

These are the source of truth and evolve with the repo — use them as models, and the `TEMPLATE.*` files above as blank scaffolding.
