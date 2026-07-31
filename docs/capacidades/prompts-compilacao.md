# Compilation Prompts

4 prompts that transform research documents into operational artifacts (SKILL.md or .instructions.md).

All follow the `TEMPLATE.GENERATOR.prompt.md` pattern.

---

## Overview

| Prompt | Input | Output | Domain |
|--------|-------|--------|---------|
| `skill-creator` | Any research | SKILL.md | Generic |
| `terraform-instructions-compiler` | Terraform research | .instructions.md (multiple) | Terraform |
| `architecture-approaches-skill-generator` | Architecture research | SKILL.md | Architecture |
| `methodologies-skill-generator` | Methodology research | SKILL.md | Methodologies |

---

## 1. skill-creator

> **File**: `.claude/skills/skill-creator/SKILL.md`

### Description
Orchestrates the generation of a SKILL.md from any research document, applying the authoring patterns integrated into `skill-creator`.

### Invocation
```
skill-creator
```

### Internal Workflow
1. Applies integrated authoring patterns (three-tier, YAML, blueprints)
2. Reads the provided research document
3. Applies three-tier architecture (✅⚠️🚫)
4. Generates SKILL.md with correct YAML frontmatter
5. Creates `blueprints/` with always-do and never-do patterns

### Expected Input
- Path to research document (output from any researcher)

### Produced Output
```
skill-name/
├── SKILL.md
└── blueprints/
    ├── always-do-patterns.md
    └── never-do-patterns.md
```

### Dependencies
- Authoring patterns integrated into `skill-creator`
- Template: `TEMPLATE.SKILL.md` (implicit reference)

### Complements
- All 7 research prompts (receives their output)
- `skill-best-practices-validator` (validates the output)

---

## 2. terraform-instructions-compiler

> **File**: `.claude/skills/terraform-instructions-compiler/SKILL.md`

### Description
Interactive compiler that extracts best practices from Terraform research and generates multiple categorized .instructions.md files.

### Invocation
```
terraform-instructions-compiler
```

### Internal Workflow
1. **Phase 1.1**: Reads Terraform research document
2. **Phase 1.2**: Loads reference templates:
   - `TEMPLATE.STANDARDS.instructions.md` (L54)
   - `TEMPLATE.CONFIG.instructions.md` (L55)
   - `TEMPLATE.SKILLS.instructions.md` (L56)
3. **Phase 2**: Interactive interview (which aspects to include)
4. **Phase 3**: Planning (which files to generate)
5. **Phase 4**: Generation of .instructions.md files

### Expected Input
- Research document from `terraform-engineering-best-practices-researcher` or `technical-framework-researcher-terraform`

### Produced Output

> **Target runtime determines the output path:**
> - `terraform-config.instructions.md` (GitHub Copilot) → `.github/instructions/`
> - `terraform-config.md` (Claude Code) → `.claude/rules/`
>
> The compiler asks for the target runtime during the Phase 2 interactive interview.

```
# Copilot example (default)
.github/instructions/
├── terraform-config.instructions.md      ← Setup, backend, providers
├── terraform-standards.instructions.md   ← Naming, modules, structure
└── terraform-skills.instructions.md      ← Keyword → skill routing table

# Claude Code equivalent
.claude/rules/
├── terraform-config.md
├── terraform-standards.md
└── terraform-skills.md
```

### Dependencies
- Templates: `TEMPLATE.CONFIG.instructions.md`, `TEMPLATE.STANDARDS.instructions.md`, `TEMPLATE.SKILLS.instructions.md` (**explicit reference**)

### Complements
- `terraform-engineering-best-practices-researcher` (main input)
- `technical-framework-researcher-terraform` (alternative input)
- `instructions-best-practices-validator` (validates output)

---

## 3. architecture-approaches-skill-generator

> **File**: `.claude/skills/architecture-approaches-skill-generator/SKILL.md`

### Description
Generates SKILL.md from architecture methodology research, applying the three-tier pattern with a focus on architectural decisions.

### Invocation
```
architecture-approaches-skill-generator
```

### Internal Workflow
1. Applies integrated authoring patterns (three-tier, YAML, blueprints)
2. Reads architecture methodology research
3. Identifies architectural decisions → maps to ⚠️ Ask First
4. Identifies mandatory patterns → maps to ✅ Always Do
5. Identifies anti-patterns → maps to 🚫 Never Do
6. Generates versioned SKILL.md

### Expected Input
- Research document from `architecture-methodology-researcher`

### Produced Output
- `SKILL.md` with architectural decisions structured in three-tier

### Dependencies
- Authoring patterns integrated into `skill-creator`

### Complements
- `architecture-methodology-researcher` (input)
- `skill-best-practices-validator` (validates output)

---

## 4. methodologies-skill-generator

> **File**: `.claude/skills/methodologies-skill-generator/SKILL.md`

### Description
Generates SKILL.md from engineering/requirements methodology research, structuring practices in three-tier.

### Invocation
```
methodologies-skill-generator
```

### Internal Workflow
1. Applies integrated authoring patterns (three-tier, YAML, blueprints)
2. Reads methodology research
3. Structures mandatory, optional, and prohibited practices
4. Generates SKILL.md with application examples

### Expected Input
- Research document from `requirements-methodology-researcher`

### Produced Output
- `SKILL.md` with methodology practices in three-tier

### Dependencies
- Authoring patterns integrated into `skill-creator`

### Complements
- `requirements-methodology-researcher` (input)
- `skill-best-practices-validator` (validates output)

---

## Compatibility Matrix: Researcher → Compiler

| Researcher | Recommended Compiler |
|-----------|---------------------|
| `researching-technical-frameworks` | `skill-creator` |
| `technical-framework-researcher-terraform` | `terraform-instructions-compiler` |
| `terraform-engineering-best-practices-researcher` | `terraform-instructions-compiler` |
| `architecture-methodology-researcher` | `architecture-approaches-skill-generator` |
| `cloud-architecture-researcher` | `skill-creator` |
| `business-domain-researcher` | `skill-creator` |
| `requirements-methodology-researcher` | `methodologies-skill-generator` |
