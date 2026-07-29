---
name: skill-creator
description: Guides generation of an Agent Skill using the authoring-agent-skills standard. Use when creating a new skill from validated research.
argument-hint: "Path to research file (e.g. StoryBeat/research_FastAPI_v0.115.md)"
context: fork
agent: skill-author
disable-model-invocation: true
---
# PROMPT: Skill Generator for Programming Agents

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier rules for this skill's own operation
- **[Critical Requirements](#critical-requirements)** — Three-tier + Essential Sections mandates for generated output
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 scenarios: canonical, edge, misuse
- **[Quality Gates](#quality-gates-final-checklist)** — Final checklist before delivering output
- **[Verification Loop](#verification-loop)** — Post-generation self-check commands
- **[External Resources](#external-resources)** — Reference links

---

## Blueprints & Guardrails

### ✅ Always Do

- **Load `authoring-agent-skills` before generating** — Read `.claude/skills/authoring-agent-skills/SKILL.md` as Step 1. It is the authoritative reference for naming rules, three-tier structure, and quality checklist.
- **Verify the research file exists before proceeding** — If `$ARGUMENTS` is missing or unreadable, stop and display the error message. Do not generate from memory.
- **Start from `TEMPLATE.SKILL.md`** — Use `.claude/templates/skills/TEMPLATE.SKILL.md` as the scaffold. Populate every section placeholder; never invent new sections or skip existing ones.
- **Create `blueprints/evaluation-scenarios.md`** — Generate at least 3 evaluation scenarios and save them as part of the output. This is always required, not optional.
- **Stay under 500 lines** — Monitor line count during generation; if approaching 500, extract the largest content block to `blueprints/` before writing further inline content.

### ⚠️ Ask First

- **Skill approaching 500 lines during generation** — Pause and confirm with user which section(s) to extract to `blueprints/` before exceeding the limit.
- **Domain complexity unclear** — If the research file lacks a `Domain_Complexity` field and complexity is genuinely ambiguous, ask the user before deciding tier counts (Foundational vs. Standard vs. Complex).
- **No research file, user wants to generate from conversation** — Ask whether to run a researcher skill first or proceed with the user's provided specification.

### 🚫 Never Do

| ❌ Incorrect | ✅ Correct |
|---|---|
| Generate a SKILL.md without reading a research file | Run `/technical-framework-researcher` or an equivalent first; pass the output as `$ARGUMENTS` |
| Skip creating `blueprints/evaluation-scenarios.md` | Always produce at least 3 scenarios — this is a mandatory artifact, not optional |
| Use absolute or Windows-style paths in the generated SKILL.md | Use relative paths only (`./blueprints/file.md`, `../../rules/skill-frontmatter.md`) |
| Duplicate large documentation blocks inline | Move blocks > 30 lines to `blueprints/` and link from SKILL.md |

---

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
Skill Author

## Context
You have received technical documentation in the research file provided as `$ARGUMENTS`. Derive the technology name, target version, and skill name from the research file path and its frontmatter (by convention: `research_<TechName>_<Version>.md`). Your mission is to transform this research into a production-grade Claude Code Agent Skill following the [official Claude best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) and the team conventions in **authoring-agent-skills**.

**Input**: Research file at `$ARGUMENTS`
**Output**: Complete `SKILL.md` saved at `.claude/skills/<skill-name>/SKILL.md`

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
- [ ] YAML frontmatter rules (name: max 64 chars, lowercase/numbers/hyphens; description: third-person, max 1536 chars)
- [ ] Three-level structure (✅⚠️🚫) — team convention
- [ ] Progressive disclosure patterns
- [ ] Quality checklist (official + team)

### Step 2: Process Research File
Load `$ARGUMENTS` and map:
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
Create at least 3 evaluation scenarios to test the skill. Derive `<skill-name>` from the research file metadata (folder name = YAML `name`).

```json
{
  "skills": ["<skill-name>"],
  "query": "[representative task]",
  "expected_behavior": ["[specific expected outcome 1]", "[specific expected outcome 2]"]
}
```

Save scenarios as `.claude/skills/<skill-name>/blueprints/evaluation-scenarios.md`. Add a Quick Navigation link in SKILL.md: `[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)`.

---

## Critical Requirements

### 1. Follow authoring-agent-skills Standards
All skills MUST follow the patterns documented in [authoring-agent-skills](../../skills/authoring-agent-skills/SKILL.md). Key points:

- **Naming**: `lowercase-kebab-case`, gerund form preferred (folder = YAML name)
- **Name constraints**: max 64 chars, lowercase letters/numbers/hyphens only, no reserved words (`anthropic`, `claude`)
- **File**: Exactly `.claude/skills/<skill-name>/SKILL.md` (derive `<skill-name>` from research file)
- **YAML `description`**: third-person, max 1536 chars. Format: `"[Action verb] [what] with [Tech]. Use when [trigger]."`

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

| ❌ Don't | ✅ Do instead |
|---|---|
| Duplicate large documentation blocks inline | Move to `blueprints/` and link from SKILL.md |
| Use absolute or Windows-style paths | Use relative paths: `./blueprints/file.md`, `../../rules/file.md` |
| Link to files that don't exist yet | Create the target file first, then add the link |
| Include time-sensitive information (release dates, "new in v1.x") | Move to a `## Version Context` section with explicit version lock |

---

## Output Structure

The output is a complete `SKILL.md` file ready to save at `.claude/skills/<skill-name>/SKILL.md` (derive `<skill-name>` from the research file path and frontmatter).

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
- [ ] All three tiers (✅⚠️🚫) populated with research data — no tier may be empty
- [ ] Every 🚫 Never Do item has an inline ✅ correct alternative (not just "don't do X")
- [ ] Version Context section present
- [ ] Anti-patterns have correct alternatives in code
- [ ] Code examples are copy-paste executable
- [ ] No absolute paths (only relative or URLs)
- [ ] All links tested (no 404s)
- [ ] `## External Resources` section present with at least one dated official link
- [ ] Research bibliography linked under External Resources

**Evaluation**:
- [ ] At least 3 evaluation scenarios created and saved as `blueprints/evaluation-scenarios.md`
- [ ] Quick Navigation in SKILL.md links to `./blueprints/evaluation-scenarios.md`
- [ ] Scenarios cover: canonical use, edge case, and misuse/anti-pattern trap

---

## Verification Loop

After generating the SKILL.md and evaluation scenarios, run these checks:

```bash
# 1. Line count must stay under 500
wc -l ".claude/skills/<skill-name>/SKILL.md"
# Expected: ≤ 500

# 2. All three tiers present
grep -c "### ✅ Always Do\|### ⚠️ Ask First\|### 🚫 Never Do" ".claude/skills/<skill-name>/SKILL.md"
# Expected: 3

# 3. Evaluation scenarios created
test -f ".claude/skills/<skill-name>/blueprints/evaluation-scenarios.md" && echo "OK" || echo "MISSING"
# Expected: OK

# 4. All blueprint links resolve
grep -oE '\./blueprints/[^)]+' ".claude/skills/<skill-name>/SKILL.md" | while read f; do
  [ -f ".claude/skills/<skill-name>/$f" ] && echo "OK: $f" || echo "MISSING: $f"
done
# Expected: all OK

# 5. No absolute paths
grep -nE "(C:\\\\|/Users/|/home/)" ".claude/skills/<skill-name>/SKILL.md"
# Expected: no output
```

> Replace `<skill-name>` with the actual skill folder name derived from the research file.

---

## Expected Input Format

The `$ARGUMENTS` file (research file path) should be the output of the research protocol containing:

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
2. **SECOND**: Read the research file at `$ARGUMENTS` thoroughly; derive `<skill-name>`, tech name, and version from its path and frontmatter
3. **THIRD**: Map the sections of the research to the skill structure (consider degrees of freedom for each pattern)
4. **FOURTH**: Apply authoring-agent-skills rules (official + team conventions)
5. **FIFTH**: Generate concise, production-ready `SKILL.md` at `.claude/skills/<skill-name>/SKILL.md` (under 500 lines)
6. **SIXTH**: Create 3 evaluation scenarios; save as `.claude/skills/<skill-name>/blueprints/evaluation-scenarios.md`; add Quick Navigation link in SKILL.md
7. **SEVENTH**: Perform self-verification against the quality checklist

**Final Output** (two mandatory artifacts):
- `.claude/skills/<skill-name>/SKILL.md`
- `.claude/skills/<skill-name>/blueprints/evaluation-scenarios.md`

---

## Invocation Example

**Command (via `/skill-creator`):**
```
/skill-creator StoryBeat/research_FastAPI_v0.104.1.md
```

The agent derives from the path: tech = `FastAPI`, version = `0.104.1`, skill name = `fastapi-async-api`.

**Expected output** (two artifacts):
- `.claude/skills/fastapi-async-api/SKILL.md`
- `.claude/skills/fastapi-async-api/blueprints/evaluation-scenarios.md`

---

## External Resources

### Claude Code Skill Authoring
- [Claude Code — Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — Anthropic official (current)
- [authoring-agent-skills SKILL.md](../../skills/authoring-agent-skills/SKILL.md) — House conventions: three-tier architecture, progressive disclosure, quality checklist
- [TEMPLATE.SKILL.md](../../templates/skills/TEMPLATE.SKILL.md) — Canonical scaffold for generated SKILL.md files
- [skill-frontmatter rules](../../rules/skill-frontmatter.md) — YAML frontmatter requirements (name, description, allowed-tools, context, agent)

### Research Input Standard
- [researching-technical-frameworks SKILL.md](../researching-technical-frameworks/SKILL.md) — Research protocol that produces the `$ARGUMENTS` input file
