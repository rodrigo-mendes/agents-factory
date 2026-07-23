---
name: skill-creator
description: Guides generation of an Agent Skill using the authoring-agent-skills standard. Use when creating a new skill from validated research.
context: fork
agent: skill-author
disable-model-invocation: true
---
# PROMPT: Skill Generator for Programming Agents

## How This Prompt Works with authoring-agent-skills

This is an **orchestration prompt** for agents. It guides you through the workflow of:
1. Loading the `authoring-agent-skills` SKILL.md (the technical standard)
2. Reading a research file (input)
3. Applying the standard to create a new SKILL.md (output)

### Key References
- **Technical Standard**: [authoring-agent-skills SKILL.md](../../skills/authoring-agent-skills/SKILL.md)
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
Copilot Configuration Architect

## Context
You have received technical documentation for **{{SYSTEM_OR_TECH_NAME}} v{{TARGET_VERSION}}**. Your mission is to transform this research into a production-grade GitHub Copilot Agent Skill following the [official Claude best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) and the team conventions in **authoring-agent-skills**.

**Input**: Research file in {{FILE_RESULT}}
**Output**: Complete `SKILL.md` ready for `.claude/skills/{{SKILL_NAME}}/`

### Key Principle: Conciseness
The context window is a shared resource. For every piece of content, ask:
- "Does Claude really need this explanation?"
- "Can I assume Claude knows this?"
- "Does this paragraph justify its token cost?"

**Keep SKILL.md body under 500 lines.** Use progressive disclosure (separate files) when approaching this limit.

---

## Execution Workflow

### Step 1: Load Authoring Skill (REQUIRED)

Read `.claude/skills/authoring-agent-skills/SKILL.md` before proceeding.

**Check that you have loaded**:
- [ ] Core principles (conciseness, degrees of freedom)
- [ ] YAML frontmatter rules (name: max 64 chars, lowercase/numbers/hyphens; description: third-person, max 1024 chars)
- [ ] Three-level structure (✅⚠️🚫) — team convention
- [ ] Progressive disclosure patterns
- [ ] Quality checklist (official + team)

### Step 2: Process Research File
Load {{FILE_RESULT}} and map:
- "Mandatory Patterns" → ✅ Always Do
- "Conditional Patterns" → ⚠️ Ask First  
- "Forbidden Patterns" → 🚫 Never Do
- "Verification Commands" → Verification Loop
- "Source Bibliography" → External Resources

**Domain Complexity Assessment**: Check if the research file includes a `Domain_Complexity` field in its metadata. If present, use it to validate that pattern counts align with the appropriate tier:
- **Foundational** (3-4 / 2-3 / 2-3): Single-concern, wrapper, orchestrator
- **Standard** (5-6 / 3-4 / 4-5): Multi-concern integration
- **Complex** (7-9 / 4-6 / 5-7): Security-critical, multi-layer

If not present, assess complexity from the research content itself. Include every pattern the domain requires — never pad to reach a count, never omit to fit under a cap.

For each pattern, determine the appropriate **degree of freedom**:
- **High freedom** (text instructions): multiple valid approaches, context-dependent
- **Medium freedom** (pseudocode/templates): preferred pattern exists, some variation OK
- **Low freedom** (exact scripts): fragile operations, consistency critical

### Step 3: Generate SKILL.md
Apply the authoring-agent-skills standards (see [File Structure](../../skills/authoring-agent-skills/SKILL.md#file-structure--three-tier-architecture)) to create the file.

### Step 4: Create Evaluation Scenarios
Create at least 3 evaluation scenarios to test the skill:
```json
{
  "skills": ["{{SKILL_NAME}}"],
  "query": "[representative task]",
  "expected_behavior": ["[specific expected outcome 1]", "[specific expected outcome 2]"]
}
```

---

## Critical Requirements

### 1. Follow authoring-agent-skills Standards
All skills MUST follow the patterns documented in [authoring-agent-skills](../../skills/authoring-agent-skills/SKILL.md). Key points:

- **Naming**: `lowercase-kebab-case`, gerund form preferred (folder = YAML name)
- **Name constraints**: max 64 chars, lowercase letters/numbers/hyphens only, no reserved words (`anthropic`, `claude`)
- **File**: Exactly `.claude/skills/{{SKILL_NAME}}/SKILL.md`
- **YAML `description`**: third-person, max 1024 chars. Format: `"[Action verb] [what] with [Tech]. Use when [trigger]."`

### 2. Three-Level Architecture (✅⚠️🚫)
See [Three-Tier Architecture](../../skills/authoring-agent-skills/SKILL.md#file-structure--three-tier-architecture) in authoring-agent-skills for complete details.

**Quick mapping from research**:
- "Mandatory Patterns" → ✅ Always Do (concise examples with code — include all patterns the domain requires)
- "Conditional Patterns" → ⚠️ Ask First (decisions with tradeoff matrix — include all decision points)
- "Forbidden Patterns" → 🚫 Never Do (anti-patterns with correct alternatives — include all anti-patterns discovered)

### 3. Essential Sections (Team Conventions)
- **Version Context**: Technology, target version, release date, support status, breaking changes
- **Verification Loop**: Adapted to the technology (lint, tests, health checks)
- **Integration Patterns**: For each technology partner
- **External Resources**: Links to official documentation

### 4. Progressive Disclosure & Context Efficiency
- Keep SKILL.md under 500 lines — split into `blueprints/` files when approaching this limit
- Use relative links: `[Skill Frontmatter Rule](../../rules/skill-frontmatter.md)`
- Link to official external documentation
- Keep file references one level deep from SKILL.md
- Use forward slashes in all paths

🚫 **Don't**:
- Duplicate large blocks of documentation
- Use absolute paths or Windows-style paths
- Link to non-existent files
- Include time-sensitive information (use "old patterns" section)

---

## Output Structure

The output is a complete `SKILL.md` file ready to save at `.claude/skills/{{SKILL_NAME}}/SKILL.md`.

**How to produce it**:
1. Start from the canonical scaffold: [TEMPLATE.SKILL.md](../../templates/skills/TEMPLATE.SKILL.md) — it defines every required section with placeholders. Do not invent sections or omit existing ones.
2. Populate each section following the conventions in [authoring-agent-skills/SKILL.md](../../skills/authoring-agent-skills/SKILL.md): naming rules, three-tier guardrails (✅⚠️🚫), version lock, degrees of freedom. That skill is the authoritative reference for *how* to write each section.
3. Replace all `[placeholder]` values with content derived from the research file mapping (Step 2 above).
4. Apply progressive disclosure: if the file approaches 500 lines, move large code examples to `blueprints/*.md` and link from SKILL.md.

> The template defines **what** to include. The skill defines **how** to write it. This prompt defines **when and in what order**.

---

## Quality Gates (Final Checklist)

Before generating output, verify against the [Quality Checklist](../../skills/authoring-agent-skills/SKILL.md#quality-checklist) in authoring-agent-skills:

**Core Quality (Official)**:
- [ ] Description is third-person, specific, includes what + when
- [ ] SKILL.md body under 500 lines
- [ ] No time-sensitive information
- [ ] Consistent terminology throughout
- [ ] File references one level deep
- [ ] No Windows-style paths

**Team Conventions**:
- [ ] YAML `name` = folder name = kebab-case (gerund preferred)
- [ ] All three levels (✅⚠️🚫) populated with research data
- [ ] Version Context section present
- [ ] Anti-patterns have correct alternatives in code
- [ ] Code examples are copy-paste executable
- [ ] No absolute paths (only relative or URLs)
- [ ] All links tested (no 404s)
- [ ] Research bibliography linked as external resources

**Evaluation**:
- [ ] At least 3 evaluation scenarios created

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

1. **FIRST**: Load `.claude/skills/authoring-agent-skills/SKILL.md`
2. **SECOND**: Read the research file in {{FILE_RESULT}} thoroughly
3. **THIRD**: Map the sections of the research to the skill structure (consider degrees of freedom for each pattern)
4. **FOURTH**: Apply authoring-agent-skills rules (official + team conventions)
5. **FIFTH**: Generate concise, production-ready SKILL.md (under 500 lines)
6. **SIXTH**: Create 3 evaluation scenarios
7. **SEVENTH**: Perform self-verification against the quality checklist

**Final Output**: Complete file ready to save in `.claude/skills/{{SKILL_NAME}}/SKILL.md`

---

## Invocation Example

**Context variables:**
- `SYSTEM_OR_TECH_NAME` = "FastAPI"
- `TARGET_VERSION` = "0.104.1"
- `FILE_RESULT` = "./research_fastapi_v0.104.1.md"
- `SKILL_NAME` = "fastapi-async-api"

**Command:** "Using authoring-agent-skills, generate a skill for `fastapi-async-api` based on `./research_fastapi_v0.104.1.md`"

**Expected output**: Complete and functional `.claude/skills/fastapi-async-api/SKILL.md`.
