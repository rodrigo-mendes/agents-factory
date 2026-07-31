---
name: skill-creator
description: "Creates Agent Skills (SKILL.md) from a research_[TECH]_v[VERSION].md file following official Claude best practices and team conventions. Use when authoring a new skill from a completed research file produced by a researcher skill (e.g. /researching-technical-frameworks). For all-in-one research + skill, use /methodologies-skill-generator or /architecture-approaches-skill-generator instead."
argument-hint: "Path to research file (e.g. StoryBeat/research_FastAPI_v0.115.md)"
context: fork
agent: skill-author
disable-model-invocation: true
---

# PROMPT: Skill Generator for Programming Agents

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Operational three-tier rules for this skill
- **[Authoring Standards](#authoring-standards)** — Core principles, YAML rules, quality checklist
- **[Execution Workflow](#execution-workflow)** — 6-step generation process
- **[Quality Gates](#quality-gates-final-checklist)** — Final checklist before delivering output
- **[Verification Loop](#verification-loop)** — Post-generation self-check commands
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases (generator + authoring standards)
- **[External Resources](#external-resources)** — Reference links

**Reference**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

---

## Blueprints & Guardrails

### ✅ Always Do

- **Verify the research file exists before proceeding** — If `$ARGUMENTS` is missing or unreadable, stop and report the error. Do not generate from memory.
- **Start from `TEMPLATE.SKILL.md`** — Use `.claude/templates/skills/TEMPLATE.SKILL.md` as the scaffold. Populate every section placeholder; never invent new sections or skip existing ones.
- **Create `blueprints/evaluation-scenarios.md`** — Generate at least 3 evaluation scenarios and save them as part of the output. Always required, not optional.
- **Stay under 500 lines** — Monitor line count; if approaching 500, extract the largest content block to `blueprints/` before writing further inline content.
- **Apply authoring standards** — Use the [Authoring Standards](#authoring-standards) below as the authoritative reference for naming, three-tier structure, and quality checklist.

### ⚠️ Ask First

- **Skill approaching 500 lines during generation** — Pause and confirm with user which section(s) to extract to `blueprints/` before exceeding the limit.
- **Domain complexity unclear** — If the research file lacks a `Domain_Complexity` field and complexity is genuinely ambiguous, ask the user before deciding tier counts (Foundational vs. Standard vs. Complex).
- **No research file, user wants to generate from conversation** — Ask whether to run a researcher skill first or proceed with the user's provided specification.

### 🚫 Never Do

| ❌ Incorrect | ✅ Correct |
|---|---|
| Generate a SKILL.md without reading a research file | Run `/researching-technical-frameworks` or equivalent first; pass the output as `$ARGUMENTS` |
| Skip creating `blueprints/evaluation-scenarios.md` | Always produce at least 3 scenarios — mandatory artifact, not optional |
| Use absolute or Windows-style paths in the generated SKILL.md | Use relative paths only (`./blueprints/file.md`, `../../rules/skill-frontmatter.md`) |
| Duplicate large documentation blocks inline | Move blocks > 30 lines to `blueprints/` and link from SKILL.md |
| Author from an unverified/opinion source without flagging | Mark output as `UNVERIFIED`; offer to run `/researching-technical-frameworks` first |

---

## Authoring Standards

> Authoritative reference for naming rules, three-tier structure, and quality checklist. Detailed examples in [Three-Tier Architecture](./blueprints/three-tier-architecture.md) and [Evaluation & Iteration](./blueprints/evaluation-iteration.md).

### Core Principles

The context window is a shared resource. Challenge every piece of content: "Does Claude really need this?" · "Can I assume Claude knows this?" · "Does this justify its token cost?"

**Keep SKILL.md body under 500 lines.** Use progressive disclosure (linked `blueprints/*.md`) for everything else.

**Degrees of freedom** — match specificity to fragility:

| Freedom | Use When | Example |
|---|---|---|
| **High** (text instructions) | Multiple valid approaches | Code review guidelines |
| **Medium** (pseudocode/templates) | Preferred pattern exists | Report generation template |
| **Low** (exact scripts) | Fragile, consistency critical | Database migration commands |

**Test with multiple models** — what works for Opus may need more detail for Haiku.

### YAML Frontmatter

**`name`**: max 64 chars, lowercase/numbers/hyphens only, no reserved words (`anthropic`, `claude`). Prefer gerund form: `processing-pdfs`, `provisioning-oci-functions`. Folder name = YAML `name` = kebab-case.

**`description`**: max 1536 chars, third-person (not "I can help"), includes what + when.
```yaml
description: "[Action verb] [what] with [Tech] v[X.Y]+. Use when [trigger context]."
```
✅ `"Builds async REST APIs with FastAPI v0.100+. Use when creating high-performance Python APIs."`
❌ `"Helps with FastAPI"` · `"I can help you process Excel files"` · `"Useful for building APIs"`

### Three-Tier Architecture

> **Team Convention** — see [Three-Tier Architecture](./blueprints/three-tier-architecture.md) for complete rules, required structure, and code examples.

- **✅ Always Do**: Mandatory patterns — auto-execute, full code examples, at least 2 per skill
- **⚠️ Ask First**: Architectural crossroads — options table + tradeoff matrix, wait for user decision
- **🚫 Never Do**: Anti-patterns — wrong code + correct alternative side-by-side, real-world impact

Include `## Version Context` (version-specific skills) and `## Verification Loop` (code-generating skills).

### Progressive Disclosure

- Extract to `blueprints/` when: SKILL.md > 500 lines, > 3 large examples (> 50 lines each)
- Keep references one level deep from SKILL.md; name files descriptively
- Use forward slashes in all paths; never absolute paths, never dangling links

### Content Guidelines

- **Time-sensitive info** → use `## Version Context` with explicit version lock instead
- **Consistent terminology** → choose one term throughout ("API endpoint", not mixing "URL"/"route"/"path")
- **Offer one default** → `"Use pdfplumber. For OCR, use pdf2image instead."` — not a list of equals

### Quality Checklist

**Core (Official)**:
- [ ] Description: third-person, specific, includes what + when, ≤ 1536 chars
- [ ] SKILL.md body < 500 lines; details in linked `blueprints/` files
- [ ] No time-sensitive info (or in `## Version Context`); consistent terminology
- [ ] File references one level deep; all forward slashes; no Windows-style paths

**Team Conventions**:
- [ ] YAML `name` = folder name = kebab-case (gerund preferred)
- [ ] All three tiers (✅⚠️🚫) populated; every 🚫 item has inline ✅ alternative
- [ ] Version Context section present (if version-specific)
- [ ] Verification Loop commands present, executable, with expected output
- [ ] `## External Resources` with at least one dated official link
- [ ] At least 3 evaluation scenarios in `blueprints/evaluation-scenarios.md`, linked from Quick Navigation

### Skill Template

Start from [TEMPLATE.SKILL.md](../../templates/skills/TEMPLATE.SKILL.md). Sections provided: Frontmatter, `## Function`, `## Version Context`, `## Quick Navigation`, `## Blueprints & Guardrails` (✅⚠️🚫), `## Integration Patterns`, `## Verification Loop`, `## Quick Reference`, `## Blueprints Directory Structure`, `## External Resources`.

### Common Mistakes

| Aspect | ❌ Incorrect | ✅ Correct |
|---|---|---|
| Description | `"Helps with FastAPI"` | `"Builds async REST APIs with FastAPI v0.100+. Use when…"` |
| POV | `"I can help you process files"` | `"Processes Excel files and generates reports. Use when…"` |
| Anti-pattern | `"Don't use sync"` | Side-by-side: `# 🚫 WRONG` + `# ✅ CORRECT` |
| Paths | `scripts\helper.py` | `scripts/helper.py` |
| Options | `"Use pypdf, or pdfplumber, or PyMuPDF"` | `"Use pdfplumber. For OCR, use pdf2image instead."` |

### Research → Skill Mapping

```
Mandatory_Patterns     → ✅ Always Do
Conditional_Patterns   → ⚠️ Ask First
Forbidden_Patterns     → 🚫 Never Do
Verification_Commands  → ## Verification Loop
Mocking_Protocol       → Verification Loop → "### 2. Unit Tests"
Source_Bibliography    → ## External Resources
Metadata.Target_Version → ## Version Context
```

---

## Context

You have received technical documentation in the research file at `$ARGUMENTS`. Derive technology name, target version, and skill name from the file path and frontmatter (convention: `research_<TechName>_<Version>.md`). Transform this research into a production-grade Claude Code Agent Skill following the [official Claude best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) and the [Authoring Standards](#authoring-standards) above.

**Input**: Research file at `$ARGUMENTS`
**Output**: `.claude/skills/<skill-name>/SKILL.md` + `./blueprints/evaluation-scenarios.md`

---

## Execution Workflow

### Step 1: Process Research File

Load `$ARGUMENTS` and map sections using [Research → Skill Mapping](#research--skill-mapping).

**Domain Complexity Assessment**: Check for `Domain_Complexity` in metadata. Use to validate pattern counts:
- **Foundational** (3-4 / 2-3 / 2-3): Single-concern, wrapper, orchestrator
- **Standard** (5-6 / 3-4 / 4-5): Multi-concern integration
- **Complex** (7-9 / 4-6 / 5-7): Security-critical, multi-layer

If absent, assess from content. Never pad to reach a count; never omit to fit a cap. For each pattern, determine degree of freedom: High / Medium / Low.

### Step 2: Generate SKILL.md

1. Start from [TEMPLATE.SKILL.md](../../templates/skills/TEMPLATE.SKILL.md)
2. Populate every section following [Authoring Standards](#authoring-standards)
3. Replace all `[placeholder]` values with research-derived content
4. Apply progressive disclosure: move content > 30 lines to `blueprints/` if approaching 500 lines

Output: `.claude/skills/<skill-name>/SKILL.md`

### Step 3: Create Evaluation Scenarios

Generate at least 3 scenarios (canonical, edge, misuse). Derive `<skill-name>` from the research file metadata.

```json
{
  "skills": ["<skill-name>"],
  "query": "[representative task]",
  "expected_behavior": ["[outcome 1]", "[outcome 2]"]
}
```

Save as `.claude/skills/<skill-name>/blueprints/evaluation-scenarios.md`. Add Quick Navigation link in SKILL.md.

### Step 4: Quality Gate Self-Check

Verify all [Quality Checklist](#quality-checklist) items pass before proceeding.

### Step 5: Verification Loop

Run all checks in [Verification Loop](#verification-loop) below.

### Step 6: Deliver Artifacts

Confirm two mandatory artifacts exist:
- `.claude/skills/<skill-name>/SKILL.md`
- `.claude/skills/<skill-name>/blueprints/evaluation-scenarios.md`

---

## Quality Gates (Final Checklist)

Verify all [Quality Checklist](#quality-checklist) items pass, plus:

- [ ] At least 3 evaluation scenarios in `blueprints/evaluation-scenarios.md`
- [ ] Quick Navigation in SKILL.md links to `./blueprints/evaluation-scenarios.md`
- [ ] Scenarios cover: canonical use, edge case, and misuse/anti-pattern trap

---

## Verification Loop

```bash
# 1. Line count ≤ 500
wc -l ".claude/skills/<skill-name>/SKILL.md"

# 2. Frontmatter required fields present
grep -E "^name:|^description:" ".claude/skills/<skill-name>/SKILL.md" | head -5

# 3. All three tiers present
grep -c "### ✅ Always Do\|### ⚠️ Ask First\|### 🚫 Never Do" ".claude/skills/<skill-name>/SKILL.md"
# Expected: 3

# 4. Evaluation scenarios created
test -f ".claude/skills/<skill-name>/blueprints/evaluation-scenarios.md" && echo "OK" || echo "MISSING"

# 5. All blueprint links resolve
grep -oE '\./blueprints/[^)]+' ".claude/skills/<skill-name>/SKILL.md" | while read f; do
  [ -f ".claude/skills/<skill-name>/$f" ] && echo "OK: $f" || echo "MISSING: $f"
done

# 6. No absolute paths
grep -nE "(C:\\\\|/Users/|/home/|/root/)" ".claude/skills/<skill-name>/SKILL.md"
# Expected: no output
```

> Replace `<skill-name>` with the actual skill folder name derived from the research file.

---

## Expected Input Format

```yaml
Metadata:
  - Full_Name, Target_Version, Release_Date, Primary_Docs

Architectural Guardrails:
  - ✅ Mandatory Patterns (with code)
  - ⚠️ Conditional Patterns (with tradeoff matrix)
  - 🚫 Forbidden Patterns (with alternatives)

Implementation Blueprint:
  - Connection/Session Lifecycle, Integration Examples

Quality Control:
  - Verification Commands (bash), Mocking Protocol

Production Readiness:
  - Performance Baseline, Monitoring Checklist

Source Bibliography:
  - Primary Sources (URLs with dates), Organized Deep Links
```

---

## Invocation Example

```
/skill-creator StoryBeat/research_FastAPI_v0.104.1.md
```

Derived: tech = `FastAPI`, version = `0.104.1`, skill name = `fastapi-async-api`.

Output:
- `.claude/skills/fastapi-async-api/SKILL.md`
- `.claude/skills/fastapi-async-api/blueprints/evaluation-scenarios.md`

---

## External Resources

- [Official: Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — Primary reference
- [Official: Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — Architecture and structure
- [Three-Tier Architecture (Team)](./blueprints/three-tier-architecture.md) — ✅⚠️🚫 framework with examples
- [Evaluation & Iteration (Official)](./blueprints/evaluation-iteration.md) — Testing and improving skills
- [Evaluation Scenarios (Team)](./blueprints/evaluation-scenarios.md) — 6 test cases
- [TEMPLATE.SKILL.md](../../templates/skills/TEMPLATE.SKILL.md) — Canonical scaffold
- [skill-frontmatter rules](../../rules/skill-frontmatter.md) — YAML frontmatter requirements
- [researching-technical-frameworks](../researching-technical-frameworks/SKILL.md) — Research protocol producing `$ARGUMENTS`
