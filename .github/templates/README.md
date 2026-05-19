# Templates Directory

Templates for creating new agents, skills, prompts, and instructions. Each template is a parameterized blueprint — replace `[PLACEHOLDER]` variables with your specific values.

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
│  ├─ Compiles research into operational files?  → TEMPLATE.COMPILER.prompt.md
│  ├─ Scaffolds an entire agent project?         → TEMPLATE.SCAFFOLDING.prompt.md
│  └─ Collects context and routes to an agent?   → TEMPLATE.ENTRY-POINT.prompt.md
│
├─ A SKILL (SKILL.md)
│  └─ Always → TEMPLATE.SKILL.md
│
└─ An INSTRUCTION (.instructions.md)
   ├─ Project config, structure, dependencies? → TEMPLATE.CONFIG.instructions.md
   ├─ Code standards, patterns, conventions?   → TEMPLATE.STANDARDS.instructions.md
   └─ Skill/prompt routing & integration?      → TEMPLATE.SKILLS.instructions.md
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
| `TEMPLATE.COMPILER.prompt.md` | Research-to-instructions compiler | No (uses templates) | Compiling research into operational .instructions.md files via interactive interview |
| `TEMPLATE.SCAFFOLDING.prompt.md` | Project scaffolding | No (self-contained) | Scaffolding an entire agent project (agent + instructions + prompts + skills) |
| `TEMPLATE.ENTRY-POINT.prompt.md` | Agent routing | No (delegated) | Collecting context and routing to an agent |

### Skills (`templates/skills/`)

| Template | Use When |
|----------|----------|
| `TEMPLATE.SKILL.md` | Documenting versioned technology patterns with ✅/⚠️/🚫 guardrails |

### Instructions (`templates/instructions/`)

| Template | applyTo Pattern | Use When |
|----------|-----------------|----------|
| `TEMPLATE.CONFIG.instructions.md` | Config/project files | Enforcing project setup, dependencies, structure |
| `TEMPLATE.STANDARDS.instructions.md` | Source code files | Enforcing coding standards, patterns, conventions |
| `TEMPLATE.SKILLS.instructions.md` | All domain files | Routing requests to skills and prompts |

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

## Examples (Existing Implementations)

All examples live in `templates/examples/` so the templates directory is self-contained.

| Template | Example (in `templates/examples/`) |
|----------|------------------------------------|
| Implementation Agent | `examples/agents/oci-terraform.agent.md` |
| Advisory Agent | `examples/agents/oci-serverless-architect.agent.md` |
| Orchestrator Agent | `examples/agents/oci-serverless-stack.agent.md` |
| Feature-Add Prompt | `examples/prompts/add-oci-function.prompt.md` |
| Design Prompt | `examples/prompts/design-api-gateway.prompt.md` |
| Research Prompt | `examples/prompts/technical-framework-researcher.prompt.md` |
| Validation Prompt | `examples/prompts/skill-best-practices-validator.prompt.md` |
| Compiler Prompt | `examples/prompts/terraform-instructions-compiler.prompt.md` |
| Scaffolding Prompt | `examples/prompts/agent-bootstrap.prompt.md` |
| Entry-Point Prompt | `examples/prompts/oci-terraform.prompt.md` |
| Skill (with blueprints) | `examples/skills/provisioning-oci-functions/` |
| CONFIG Instruction | `examples/instructions/terraform-project-config.instructions.md` |
| STANDARDS Instruction | `examples/instructions/terraform-standards.instructions.md` |
| SKILLS Instruction | `examples/instructions/terraform-skills.instructions.md` |

---

## Examples Directory (`templates/examples/`)

Local copies of representative implementations for each template type, organized by artifact:

```
templates/examples/
├── agents/
│   ├── oci-terraform.agent.md              (Implementation)
│   ├── oci-serverless-architect.agent.md   (Advisory)
│   └── oci-serverless-stack.agent.md       (Orchestrator)
├── prompts/
│   ├── add-oci-function.prompt.md          (Feature-Add)
│   ├── design-api-gateway.prompt.md        (Design)
│   ├── technical-framework-researcher.prompt.md (Research)
│   ├── skill-best-practices-validator.prompt.md (Validation)
│   ├── terraform-instructions-compiler.prompt.md (Compiler)
│   ├── agent-bootstrap.prompt.md           (Scaffolding)
│   └── oci-terraform.prompt.md             (Entry-Point)
├── instructions/
│   ├── terraform-project-config.instructions.md  (CONFIG)
│   ├── terraform-standards.instructions.md       (STANDARDS)
│   └── terraform-skills.instructions.md          (SKILLS)
└── skills/
    └── provisioning-oci-functions/          (Skill with blueprints)
        ├── SKILL.md
        └── blueprints/
            ├── always-do-patterns.md
            ├── ask-first-decisions.md
            ├── integration-patterns.md
            └── never-do-patterns.md
```

> **Note**: These are point-in-time snapshots. The authoritative versions live in `.github/agents/`, `.github/prompts/`, `.github/instructions/`, and `.github/skills/`.
