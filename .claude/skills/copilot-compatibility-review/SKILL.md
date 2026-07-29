---
name: copilot-compatibility-review
description: Reviews GitHub Copilot assets for compatibility against official documentation and reports gaps. Use when checking Copilot-format assets before or during migration.
argument-hint: "Path to the Copilot assets repository/directory"
context: fork
agent: quality-validator
disable-model-invocation: true
---
# Prompt: GitHub Copilot Compatibility Analysis

## Objective
Generate a comprehensive compatibility analysis of a development copilot's assets against the official GitHub Copilot standards and your team's internal conventions.

## Quick Navigation

- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 scenarios: canonical, edge, misuse
- **[Verification Loop](#verification-loop)** — Self-check before saving the report
- **[External Resources](#external-resources)** — Official documentation from which criteria are derived

---

## Agent Instructions

Act as a GitHub Copilot Ecosystem Architect & Developer. **NEVER respond based on your base knowledge alone**. Always perform web searches in the official Microsoft/GitHub online documentation on GitHub Copilot and industry best practices before evaluating any criterion.

---

## Blueprints & Guardrails

### ✅ Always Do

- **Search official documentation before evaluating** — consult the most recent official GitHub/VS Code documentation before issuing any criterion; field specifications change frequently.
- **Read all assets before writing the report** — read every `.agent.md`, `.instructions.md`, `.prompt.md`, and `SKILL.md` found before issuing findings.
- **Cite the criterion and file in every finding** — each issue must reference the asset type (AGENTS/INSTRUCTIONS/PROMPTS/SKILLS), the exact file, and the affected field or section.
- **Verify referenced files exist** — if an asset references another file (skill, instruction, prompt), confirm the target exists before marking it compliant.
- **Detect and report critical frontmatter issues** — malformed YAML, missing required fields, and invalid values are always HIGH priority.
- **Confirm files found with ls/Glob** — enumerate real assets; never assume which files exist without filesystem inspection.

### ⚠️ Ask First

- **Assets with experimental fields** — if undocumented fields are found in the frontmatter, ask the user whether they are internal/experimental before marking them as violations.
- **Missing README.md** — if there is no `README.md`, confirm with the user whether this is intentional before reporting it as a high-priority gap.
- **Non-standard directory structure** — if assets are in a different directory than expected (e.g., `.github/` vs `.claude/`), ask the user what the canonical layout is before evaluating.
- **Inaccessible internal documentation** — if your team's internal Copilot conventions page is not accessible, confirm with the user how to proceed before skipping that verification.

### 🚫 Never Do

- **Never report a frontmatter issue without citing the field and invalid value** — "incorrect frontmatter" is not actionable. ✅ Cite the exact field (e.g., `name: My Agent` → must be kebab-case) and the value found.
- **Never evaluate based on outdated base knowledge** — GitHub Copilot specifications evolve. ✅ Always search the most recent official documentation before evaluating.
- **Never omit the Action Summary section** — it is the highest-value section for the user. ✅ The priority sections (HIGH/MEDIUM/LOW) are mandatory at the start of the report.
- **Never include corrected code examples in the report** — the goal is to identify problems and reference documentation, not to rewrite the assets. ✅ Identify the problem, cite the criterion, and link the official documentation.
- **Never fail the entire evaluation because an internal documentation URL is inaccessible** — it is an external and optional dependency. ✅ If the URL is not accessible, mark that specific check as "requires internal access" and continue with the rest of the analysis.

---

## Execution Instructions

### Step 1: Search Official Documentation

Search the web for the most recent official documentation on:
1. **GitHub Copilot Custom Agents** — `.agent.md` format with YAML frontmatter
2. **GitHub Copilot Custom Instructions** — `.instructions.md` format with YAML frontmatter
3. **GitHub Copilot Prompt Files** — `.prompt.md` format with YAML frontmatter
4. **GitHub Copilot Agent Skills** — directory structure with `SKILL.md`
5. **Team internal conventions** — see note below

> **Note on internal documentation**:
> If your team has an internal Copilot conventions page, replace this placeholder with your URL:
> `https://<your-team>.atlassian.net/<space>/<page-id>` *(or omit if not applicable)*
> If the URL is not accessible, proceed using the current repository's conventions as the reference and
> mark the "Internal Structure" verification as **requires internal access** in the report.

### Step 2: Analyze Repository Assets

Explore and analyze the following directories and files:
- `.github/agents/*.agent.md`
- `.github/instructions/*.instructions.md`
- `.github/prompts/**/*.prompt.md`
- `.github/skills/**/*.skill.md` or `SKILL.md`
- `README.md`

For each asset type, verify:

#### AGENTS (.agent.md)
- YAML frontmatter delimited with `---`
- `name` field (kebab-case, unique)
- `description` field (for contextual activation)
- Optional fields: `target`, `tools`, `infer`, `metadata`

**Official reference:** https://docs.github.com/en/reference/custom-agents-configuration

#### INSTRUCTIONS (.instructions.md)
- YAML frontmatter delimited with `---`
- `description` field (when to apply)
- `applyTo` field (glob pattern for matching)
- Optional fields: `excludeAgent`

**Official reference:** https://docs.github.com/en/copilot/how-tos/configure-custom-instructions

#### PROMPTS (.prompt.md)
- YAML frontmatter delimited with `---`
- `name` field (kebab-case for slash command)
- `description` field (for autocomplete)
- `agent` field (specific agent)
- Optional fields: `argument-hint`

**Official references:**
- https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files
- https://code.visualstudio.com/docs/copilot/customization/prompt-files

#### SKILLS (SKILL.md in subdirectories)
- Structure: `.github/skills/<skill-name>/SKILL.md`
- YAML frontmatter delimited with `---`
- `name` field (lowercase, hyphens)
- `description` field (for contextual activation)

**Official references:**
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- https://code.visualstudio.com/docs/copilot/customization/agent-skills

#### README.md
- Section listing supported environments or tools
- Values must match official documentation (e.g., Visual Studio Code, Copilot CLI, IntelliJ IDEA)
- Must not contain incorrect or placeholder values

### Step 3: Generate Compatibility Report

Create a file `COPILOT_COMPATIBILITY_REVIEW.md` with the following structure:

```markdown
# Compatibility Analysis

---

## ACTION SUMMARY

### HIGH Priority (Block Functionality)
1. **AGENTS**: [List of critical issues]
2. **INSTRUCTIONS**: [List of critical issues]
3. **PROMPTS**: [List of critical issues]
4. **SKILLS**: [List of critical issues]
5. **README.md**: [List of critical issues]

### MEDIUM Priority (Improve Compatibility)
[List of recommended optional improvements]

### LOW Priority (Organization)
[List of organizational improvements]

---

## README.md

### Current File
- `README.md`

### Issues Detected
[Detailed list of issues]

**Reference:** [Link to official documentation]

---

## AGENTS (.agent.md)

### File
- [List of .agent.md files]

### Issues Detected
[Detailed list of issues including:
1. Missing or incorrect YAML frontmatter
2. Missing required fields
3. Unimplemented optional fields]

**Reference:** [Custom agents configuration - GitHub Docs]

---

## INSTRUCTIONS (.instructions.md)

### Current Files
- [List of .instructions.md files]

### Issues Detected
[Detailed list of issues]

**Reference:** [Configure custom instructions - GitHub Docs]

---

## PROMPTS (.prompt.md)

### Current Files
- [List of .prompt.md files]

### Issues Detected
[Detailed list of issues]

**Expected usage:** `/command-name #file:file.ext`

**Reference:** [Prompt files - GitHub Docs]

---

## SKILLS (.skill.md or SKILL.md in subdirectories)

### Current Files
- [List of .skill.md or SKILL.md files]

### Issues Detected
[Detailed list of issues with emphasis on directory structure]

**Reference:** [About Agent Skills - GitHub Docs]

---
```

### Step 4: Evaluation Criteria

For each asset, identify:
- **CRITICAL ISSUES**: Block copilot functionality (missing frontmatter, incorrect structure)
- **MEDIUM ISSUES**: Reduce compatibility or optional functionality
- **LOW ISSUES**: Organization, metadata, additional documentation

Do NOT include corrected code examples in the report. Only identify problems and reference official documentation.

### Step 5: Output Format

- No emojis
- No "Corrections Required" sections with code examples
- Focus on detected problems and official references
- List of affected files must appear immediately after each section title
- Use subtitles "### Current File(s)" and "### Issues Detected"

---

## Verification Loop

Before saving the report, the validator MUST self-verify:

1. **Asset count** — confirm the number of files listed in each section matches those found with `ls`/`Glob`. If the AGENTS section lists 3 files, all 3 must have been inspected.
2. **Action Summary section mandatory** — verify the HIGH/MEDIUM/LOW priority section exists and is at the start of the report, before the per-asset-type sections.
3. **Findings with official reference** — every listed problem must have at least one reference to official documentation (link to GitHub Docs or VS Code Docs).
4. **Internal documentation check marked correctly** — if the team's internal URL was not accessible, the report must include the "requires internal access" mark in the README section and must not report it as a blocking failure.
5. **No corrected code** — verify the report does not contain code blocks with corrections (only problem identification and references).

---

## External Resources

### Official GitHub Copilot Documentation
- [Custom agents configuration](https://docs.github.com/en/reference/custom-agents-configuration) — `.agent.md` fields
- [Configure custom instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions) — `.instructions.md` fields, `applyTo`
- [Prompt files](https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files) — `.prompt.md` fields
- [About Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) — `SKILL.md` structure
- [Custom instructions library](https://docs.github.com/en/copilot/tutorials/customization-library/custom-instructions) — canonical examples

### Official VS Code Documentation
- [Prompt files (VS Code)](https://code.visualstudio.com/docs/copilot/customization/prompt-files) — fields and behavior
- [Agent skills (VS Code)](https://code.visualstudio.com/docs/copilot/customization/agent-skills) — directory structure and frontmatter

---

**Invocation**:
```
/copilot-compatibility-review
```
or
```
@workspace analyze the compatibility of this copilot using /copilot-compatibility-review
```
