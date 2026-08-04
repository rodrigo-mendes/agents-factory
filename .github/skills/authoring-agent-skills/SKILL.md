---
name: authoring-agent-skills
description: Creates, documents, and refines GitHub Copilot Agent Skills (SKILL.md) following official Claude best practices and team conventions. Use when authoring or improving agent skills.
---

## Quick Navigation

- **[Core Principles](#core-principles)** — Conciseness, degrees of freedom, progressive disclosure (Official)
- **[YAML Frontmatter](#yaml-frontmatter)** — Name and description rules (Official)
- **[File Structure & Three-Tier Architecture](#file-structure--three-tier-architecture)** — ✅⚠️🚫 patterns, Version Context, Verification Loop (Team Convention)
- **[Progressive Disclosure](#progressive-disclosure)** — How to organize multi-file skills (Official)
- **[Workflows & Feedback Loops](#workflows--feedback-loops)** — Sequential steps and validation loops (Official)
- **[Content Guidelines](#content-guidelines)** — Terminology, templates, anti-patterns to avoid (Official)
- **[Evaluation & Iteration](#evaluation--iteration)** — Testing and improving skills (Official)
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Test cases to verify skill correctness
- **[Quality Checklist](#quality-checklist)** — Validation before sharing
- **[Template](#skill-template)** — Copy-paste starting point
- **[Common Mistakes](#common-mistakes-vs-correct-usage)** — What to avoid

**Reference**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

---

## Core Principles

These principles come from the [official Claude Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

### Conciseness is Key

The context window is a shared resource. Only add context Claude doesn't already have. Challenge each piece of content:
- "Does Claude really need this explanation?"
- "Can I assume Claude knows this?"
- "Does this paragraph justify its token cost?"

**Keep SKILL.md body under 500 lines.** Split into separate files when approaching this limit.

### Degrees of Freedom

Match the level of specificity to the task's fragility:

| Freedom Level | Use When | Example |
|---|---|---|
| **High** (text instructions) | Multiple approaches valid, context-dependent | Code review guidelines |
| **Medium** (pseudocode/templates) | Preferred pattern exists, some variation OK | Report generation template |
| **Low** (exact scripts) | Operations are fragile, consistency critical | Database migration commands |

### Test with Multiple Models

Skills act as additions to models — effectiveness depends on the underlying model. What works for Opus might need more detail for Haiku. Aim for instructions that work across all target models.

---

## YAML Frontmatter

### Official Rules (from Claude docs)

**`name`** (required):
- Maximum 64 characters
- Only lowercase letters, numbers, and hyphens
- No XML tags, no reserved words (`anthropic`, `claude`)

**`description`** (required):
- Maximum 1024 characters, non-empty, no XML tags
- Write in **third person** (not "I can help" or "You can use")
- Include BOTH what the skill does AND when to use it

### Naming Convention

Prefer **gerund form** (verb + -ing) for skill names:
- ✅ `processing-pdfs`, `analyzing-spreadsheets`, `provisioning-oci-functions`
- ✅ Acceptable: noun phrases (`pdf-processing`) or action-oriented (`process-pdfs`)
- ❌ Avoid: vague (`helper`, `utils`), overly generic (`documents`, `data`), reserved words

**Folder name = YAML `name` field = kebab-case**

### Description Format

```yaml
---
name: verbing-tech-specific-task
description: "[Action verb] [what] with [Tech] v[X.Y]+. Use when [trigger context]."
---
```

**Good**: `"Builds async REST APIs with FastAPI v0.100+. Use when creating high-performance Python APIs."`
**Bad**: `"Helps with FastAPI"`, `"I can help you process Excel files"`, `"Processes data"`

---

## File Structure & Three-Tier Architecture

> **Team Convention**: The three-tier architecture (✅⚠️🚫) is this team's pattern for organizing guardrails within skills. It is not from the official Claude docs but has proven effective across 19+ skills.

For complete rules and examples, see [Three-Tier Architecture](./blueprints/three-tier-architecture.md).

**Summary**:
- **File naming**: `SKILL.md` (main), `blueprints/*.md` for auxiliary content
- **Always Do (Tier 1)**: Mandatory patterns — auto-execute with full code examples
- **Ask First (Tier 2)**: Architectural crossroads — present options with trade-offs, wait for user decision
- **Never Do (Tier 3)**: Anti-patterns — show wrong code + correct alternative + impact


### Version Lock (Team Convention)

> Include this section when the skill is version-specific.

```markdown
## Version Context

**Technology**: [Official Name]
**Target Version**: v[X.Y.Z]
**Release Date**: [DD/MM/YYYY]
**Support Status**: [Active LTS / Maintenance / EOL on DATE]

**Breaking Changes in this version**:
- [Change 1 and impact]

**Deprecations**:
- [Feature X] → use [Alternative Z]

⚠️ **Version Lock**: This skill targets v[X.Y.Z]. Do not mix patterns from other versions.
```
### Verification Loop (Team Convention)

> Include when the skill involves code generation. Adapt commands to the technology.

```markdown
## Verification Loop

### 1. Lint & Format
```bash
[exact command]
```
**Expected**: [output] | **Exit code**: 0

### 2. Tests
```bash
[exact command]
```
**Expected**: [output] | **Exit code**: 0

### 3. Integration/Health Check (if applicable)
```bash
[exact command]
```
**Expected**: [output]

**Troubleshooting**:
- Error X → Solution Y
```

### Integration Patterns (If Applicable)

```markdown
## Integration Patterns

### [Tech A] ↔ [Tech B]

**Official Library**: `[name]==X.Y.Z`
**Compatibility**: 
- [Tech A]: vX.Y+
- [Tech B]: vA.B+

**Installation**:
```bash
pip install [name]==X.Y.Z
# or
poetry add [name]@X.Y.Z
```

**Integration Pattern**:
```[language]
# Complete functional setup
[code with imports, config, usage, cleanup]
```

**Required Configuration**:
```[config format]
[minimum config file]
```

**Common Issues**:
- **Issue**: [Common problem]
  **Cause**: [Root cause]
  **Solution**: [Fix with code]
  
**Performance Tips**:
- [Tip 1 with benchmark if available]
- [Tip 2]

**Source**: [Official link]
```

---

## Progressive Disclosure

SKILL.md is an overview that points Claude to detailed materials as needed — like a table of contents. Claude loads additional files only when relevant.

### Patterns (Official)

**Pattern 1 — High-level guide with references**: SKILL.md contains quick-start instructions, links to separate files for advanced features, API reference, and examples.

**Pattern 2 — Domain-specific organization**: For skills with multiple domains, organize by domain so Claude only loads what's relevant (e.g., `reference/finance.md`, `reference/sales.md`).

**Pattern 3 — Conditional details**: Show basic content inline, link to advanced content (e.g., "For tracked changes: See [REDLINING.md](REDLINING.md)").

### Rules

- **Keep references one level deep** from SKILL.md — avoid deeply nested file chains
- **Name files descriptively**: `form_validation_rules.md`, not `doc2.md`
- **Add TOC** for reference files longer than 100 lines
- **Use forward slashes** in all file paths (`reference/guide.md`, not `reference\guide.md`)
- **Extract to blueprints/** when: skill >500 lines, >3 large code examples (>50 lines each), or multiple complex integration patterns

### Context Efficiency

**Link, don't duplicate**:
```markdown
See [Java Code Standards](../../instructions/java-functions-standards.instructions.md) for naming conventions and code quality rules.
```

**For large examples** (>50 lines): create `blueprints/[name].py` and reference from SKILL.md.

**Never**:
- ❌ Copy large blocks of external documentation
- ❌ Use absolute paths (`C:\Users\...` or `/home/user/...`)
- ❌ Link to non-existent files
- ❌ Include deprecated information without marking it as "old patterns"

---

## Workflows & Feedback Loops

### Use Workflows for Complex Tasks (Official)

Break complex operations into clear, sequential steps. For particularly complex workflows, provide a checklist:

```markdown
## Workflow: [Task Name]

Task Progress:
- [ ] Step 1: [Action] (run [script/command])
- [ ] Step 2: [Action]
- [ ] Step 3: Validate (run [validator])
- [ ] Step 4: [Action]
- [ ] Step 5: Verify output

If validation fails at Step 3, return to Step 2.
```

### Implement Feedback Loops (Official)

The pattern **run validator → fix errors → repeat** greatly improves output quality:

```markdown
1. Make changes
2. Validate: `[validation command]`
3. If validation fails → fix issues → go to step 2
4. Only proceed when validation passes
```

---

## Content Guidelines

### Avoid Time-Sensitive Information (Official)

Don't include dates that will become outdated. Use an "old patterns" section instead:

```markdown
## Current method
Use the v2 API endpoint.

<details>
<summary>Legacy v1 API (deprecated)</summary>
The v1 API is no longer supported.
</details>
```

### Use Consistent Terminology (Official)

Choose one term and use it throughout: always "API endpoint" (not mixing "URL", "route", "path").

### Avoid Offering Too Many Options (Official)

Don't present multiple approaches unless necessary. Provide a default with an escape hatch:

```markdown
Use pdfplumber for text extraction.
For scanned PDFs requiring OCR, use pdf2image with pytesseract instead.
```

---

## Evaluation & Iteration

For complete evaluation-driven development guidance, see [Evaluation & Iteration](./blueprints/evaluation-iteration.md).

**Summary** (from official Claude docs):
1. **Build evaluations BEFORE writing extensive documentation** — identify real gaps first
2. **Create at least 3 evaluation scenarios** that test those gaps
3. **Iterate with Claude A/B pattern** — one Claude instance refines the skill, another tests it
4. **Observe how Claude navigates** — watch for unexpected exploration paths, missed connections, overreliance on certain sections
5. **Gather team feedback** — does the skill activate when expected? What's missing?

---

## Quality Checklist

Based on the [official checklist](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#checklist-for-effective-skills) plus team conventions.

### Core Quality (Official)

- [ ] Description is specific, includes key terms, and states both what and when
- [ ] Description is in third person (not "I can help" or "You can use")
- [ ] SKILL.md body is under 500 lines
- [ ] Additional details are in separate files (progressive disclosure)
- [ ] No time-sensitive information (or in "old patterns" section)
- [ ] Consistent terminology throughout
- [ ] Examples are concrete, not abstract
- [ ] File references are one level deep from SKILL.md
- [ ] Workflows have clear sequential steps
- [ ] No Windows-style paths (all forward slashes)

### Code and Scripts (Official)

- [ ] Scripts solve problems rather than punt to Claude
- [ ] Error handling is explicit and helpful
- [ ] No "voodoo constants" (all values documented/justified)
- [ ] Required packages listed in instructions
- [ ] Validation/verification steps for critical operations
- [ ] Feedback loops included for quality-critical tasks

### Testing (Official)

- [ ] At least 3 evaluation scenarios created
- [ ] Tested with real usage scenarios
- [ ] Team feedback incorporated (if applicable)

### Team Conventions

- [ ] YAML `name` = folder name = kebab-case (gerund form preferred)
- [ ] Three-tier guardrails (✅⚠️🚫) present and populated
- [ ] Version Context section included (if version-specific)
- [ ] Verification Loop commands present and tested
- [ ] Anti-patterns show wrong code + correct alternative side by side
- [ ] All links tested, no 404s
- [ ] Only relative paths or full URLs (no absolute local paths)
- [ ] Code blocks have correct language tags

---

## Integration with Search Protocol

### Expected Input
Search file containing:

```yaml
Metadata:
  Full_Name: [string]
  Target_Version: [string]
  Release_Date: [date]
  Support_Status: [string]

Architectural_Guardrails:
  Mandatory_Patterns: [list with code]
  Conditional_Patterns: [list with tradeoffs]
  Forbidden_Patterns: [list with alternatives]

Implementation_Blueprint:
  Lifecycle: [code]
  Integrations: [list of examples]

Quality_Control:
  Verification_Commands: [bash scripts]
  Expected_Outputs: [strings]

Source_Bibliography:
  Primary: [URLs]
  DeepLinks: [organized URLs]
```

### Transformation (Direct Mapping)

```
Search → Skill

Mandatory_Patterns       → ✅ Always Do
Conditional_Patterns     → ⚠️ Ask First  
Forbidden_Patterns       → 🚫 Never Do
Verification_Commands    → Verification Loop
Source_Bibliography      → External Resources
Metadata.Target_Version  → Version Context
```
---

## Skill Template

Use the canonical scaffold at [TEMPLATE.SKILL.md](../../templates/skills/TEMPLATE.SKILL.md) as your starting point — it contains every required section with placeholders ready to fill.

**Sections the template provides**:
- Frontmatter (`name`, `description`) — follows the naming and description rules above
- `## Function` — one-line role declaration
- `## Version Context` — version lock block
- `## Quick Navigation` — TOC linking all sections
- `## Blueprints & Guardrails` — ✅ Always Do / ⚠️ Ask First / 🚫 Never Do with Domain Complexity Tiers
- `## Integration Patterns` — cross-service summaries
- `## Verification Loop` — build / test / health-check commands
- `## Quick Reference` — essential commands and critical limits table
- `## Blueprints Directory Structure` — when to use `blueprints/` vs inline
- `## External Resources` — official docs, security, migration links

> Populate each section following the conventions documented in this file (naming, three-tier guardrails, version lock, degrees of freedom).

### Common Mistakes vs. Correct Usage

| Aspect | ❌ Incorrect | ✅ Correct |
|---------|-----------|------------|
| **Description** | `"Helps with FastAPI"` | `"Builds async REST APIs with FastAPI v0.100+. Use when creating high-performance Python APIs."` |
| **Description POV** | `"I can help you process files"` | `"Processes Excel files and generates reports. Use when analyzing spreadsheets."` |
| **Code** | `app = FastAPI()` | `# ✅ Lifespan context (required v0.100+)`<br>`app = FastAPI(lifespan=ctx)` |
| **Anti-pattern** | `"Don't use sync"` | Side-by-side code:<br>`# 🚫 WRONG: time.sleep()`<br>`# ✅ CORRECT: await asyncio.sleep()` |
| **Paths** | `scripts\helper.py` | `scripts/helper.py` |
| **Options** | `"Use pypdf, or pdfplumber, or PyMuPDF, or..."` | `"Use pdfplumber. For OCR, use pdf2image instead."` |

---

## External Resources

- [Official: Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — Primary reference
- [Official: Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — Architecture and structure
- [Three-Tier Architecture (Team)](./blueprints/three-tier-architecture.md) — ✅⚠️🚫 framework with examples
- [Evaluation & Iteration (Official)](./blueprints/evaluation-iteration.md) — Testing and improving skills
| **Links** | Generic link | Direct deep link:<br>`fastapi.com/async#technical` |
| **Version** | Not mentioned | Mentioned 5x:<br>- Frontmatter<br>- Version Context<br>- Code comments<br>- Anti-patterns<br>- Final warning |
---

## References
- [GitHub Copilot Agent Skills Documentation](https://docs.github.com/en/copilot/building-copilot-extensions/building-a-copilot-agent-for-your-copilot-extension/about-agent-skills)