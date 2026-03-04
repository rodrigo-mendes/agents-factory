---
description: Orchestration prompt to guide agents in generating GitHub Copilot Skills using the skill-author-specialist technical standard
---

# PROMPT: Skill Generator for Programming Agents

## How This Prompt Works with skill-author-specialist

This is an **orchestration prompt** for agents. It guides you through the workflow of:
1. Loading the `skill-author-specialist` SKILL.md (the technical standard)
2. Reading a research file (input)
3. Applying the standard to create a new SKILL.md (output)

### Key References
- **Technical Standard**: [skill-author-specialist SKILL.md](../../skills/skill-author-specialist/SKILL.md)
  - Contains all architectural patterns (✅⚠️🚫)
  - Provides real code examples
  - Includes quality checklist
  
- **This Prompt Adds**:
  - Workflow orchestration
  - Agent step-by-step instructions
  - Generation-specific validation
  - Examples and templates

---

## Role
Copilot Configuration Architect & Senior Python Developer

## Context
You have received technical documentation for the search protocol for **{{SYSTEM_OR_TECH_NAME}} v{{TARGET_VERSION}}**. Your mission is to transform this research into a production-grade GitHub Copilot Agent Skill following the guidelines in **skill-author-specialist**.

**Input**: Research file in {{FILE_RESULT}}
**Output**: Complete `SKILL.md` ready for `.github/skills/{{SKILL_NAME}}/`

---

## Execution Workflow

### Step 1: Load Authoring Skill (REQUIRED)
```bash
# Read the skill before proceeding
cat .github/skills/skill-author-specialist/SKILL.md
```

**Check that you have loaded**:
- [ ] Naming rules (lowercase-kebab-case)
- [ ] Three-level structure (✅⚠️🚫)
- [ ] YAML frontmatter format
- [ ] Executable verification patterns

### Step 2: Process Research File
Load {{FILE_RESULT}} and map:
- "Mandatory Patterns" → ✅ Always Do
- "Conditional Patterns" → ⚠️ Ask First  
- "Forbidden Patterns" → 🚫 Never Do
- "Verification Commands" → Verification Loop
- "Source Bibliography" → External Resources

### Step 3: Generate SKILL.md
Apply the skill-author-specialist standards (see [File Structure & Nomenclature](../../skills/skill-author-specialist/SKILL.md#file-structure--nomenclature-non-negotiable)) to create the file.

---

## Critical Requirements

### 1. Follow skill-author-specialist Standards
All skills MUST follow the patterns documented in [skill-author-specialist](../../skills/skill-author-specialist/SKILL.md). Key points:

- **Naming**: `lowercase-kebab-case` (folder = YAML name = kebab-case)
- **File**: Exactly `.github/skills/{{SKILL_NAME}}/SKILL.md`
- **YAML**: `description` MUST start with "Use this when the user needs to..."

### 2. Three-Level Architecture (✅⚠️🚫)
See [Three-Tier Architecture](../../skills/skill-author-specialist/SKILL.md#three-tier-architecture-framework-core) in skill-author-specialist for complete details.

**Quick mapping from research**:
- "Mandatory Patterns" → ✅ Always Do (2-4 examples with code)
- "Conditional Patterns" → ⚠️ Ask First (1-3 decisions with tradeoff matrix)
- "Forbidden Patterns" → 🚫 Never Do (2-4 anti-patterns with alternatives)

### 3. Essential Sections
See [Essential Sections](../../skills/skill-author-specialist/SKILL.md#essential-sections) in skill-author-specialist for complete templates and examples:

- **Version Context**: Technology, target version, release date, support status, breaking changes
- **Verification Loop**: Lint, type check, tests, health check, security scan
- **Integration Patterns**: For each technology partner
- **Quick Reference**: Most used commands and patterns
- **External Resources**: Links to official documentation and security guides

### 4. Verification Loop
### 4. Context Efficiency
See [Context Efficiency Rules](../../skills/skill-author-specialist/SKILL.md#context-efficiency-rules) in skill-author-specialist:

✅ **Do**:
- Use relative links: `[Global Patterns](../../copilot-instructions.md)`
- Link to official external documentation
- Create `blueprints/[name].py` if >3 large examples

🚫 **Don't**:
- Duplicate large blocks of documentation
- Use absolute paths
- Link to non-existent files

---

## Output Structure

See the complete [Template de Skill Bem-Estruturada](../../skills/skill-author-specialist/SKILL.md#template-de-skill-bem-estruturada) in skill-author-specialist.

**Quick Summary**:
```markdown
---
name: {{SKILL_NAME}}
description: Use this when the user needs to [specific action] with {{SYSTEM_OR_TECH_NAME}} v{{TARGET_VERSION}}
---

## Role
[Specific technical title]

## Version Context
[Target version, release date, support status]

---

## Blueprints & Guardrails

### ✅ Always Do
[Required patterns from research]

### ⚠️ Ask First
[Architectural decisions]

### 🚫 Never Do
[Anti-patterns with alternatives]

---

## Integration Patterns
[Partner technology integrations]

---

## Verification Loop
[Testing commands]

---

## External Resources
[Links to official docs]
```

---

## Quality Gates (Final Checklist)

Before generating output, verify against the [Quality Checklist](../../skills/skill-author-specialist/SKILL.md#quality-checklist) in skill-author-specialist:

- [ ] ✅ Skill-author-specialist has been loaded and read
- [ ] ✅ YAML `name` = folder name = kebab-case
- [ ] ✅ Description begins with "Use this when the user needs to..."
- [ ] ✅ All three levels (✅⚠️🚫) populated with research data
- [ ] ✅ Minimum of 2 code examples per level
- [ ] ✅ All CLI commands from research included
- [ ] ✅ Version {{TARGET_VERSION}} explicitly mentioned 3+ times
- [ ] ✅ No absolute paths (only relative or URLs)
- [ ] ✅ All links tested (no 404s)
- [ ] ✅ Anti-patterns have correct alternatives in code
- [ ] ✅ Code examples are copy-paste executable
- [ ] ✅ Research bibliography linked as external resources

---

## Expected Input Format

The {{FILE_RESULT}} file should be the output of the research protocol containing:

```yaml
Metadata:
  - Full_Name
  - Target_Version
  - Release_Date
  - Primary_Docs

Architectural Guardrails:
  - ✅ Mandatory Patterns (with code)
  - ⚠️ Conditional Patterns (with tradeoff matrix)
  - 🚫 Forbidden Patterns (with alternatives)

Implementation Blueprint:
  - Connection/Session Lifecycle
  - Integration Examples

Quality Control:
  - Verification Commands (bash)
  - Mocking Protocol

Production Readiness:
  - Performance Baseline
  - Monitoring Checklist

Source Bibliography:
  - Primary Sources (URLs with dates)
  - Organized Deep Links
```

---

## Instructions for the Agent

1. **FIRST**: Load `.github/skills/skill-author-specialist/SKILL.md`
2. **SECOND**: Read the research file in {{FILE_RESULT}} thoroughly
3. **THIRD**: Map the sections of the research to the skill structure
4. **FOURTH**: Apply all skill-author-specialist rules
5. **FIFTH**: Generate complete and production-ready SKILL.md
6. **SIXTH**: Perform self-verification against the checklist

**Final Output**: Complete file ready to save in `.github/skills/{{SKILL_NAME}}/SKILL.md`

---

## Invocation Example

```bash
# Context
SYSTEM_OR_TECH_NAME="FastAPI"
TARGET_VERSION="0.104.1"
FILE_RESULT="./research_fastapi_v0.104.1.md"
SKILL_NAME="fastapi-async-api"

# Command
"Using skill-author-specialist, generate a skill for $SKILL_NAME based on $FILE_RESULT"
```

**Expected output**: Complete and functional `.github/skills/fastapi-async-api/SKILL.md`.