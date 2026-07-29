---
name: skill-best-practices-validator
description: Analyzes Agent Skills for quality and adherence to official Claude best practices and team conventions. Use when validating .claude/skills before shipping.
argument-hint: "Directory of skills to validate (e.g. .claude/skills/)"
context: fork
agent: quality-validator
disable-model-invocation: true
---
# Prompt: Agent Skills Best Practices Validator

## Objective
Generate a quality and best-practices adherence analysis of Agent Skills based on:
- **Official**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **Team**: `.claude/skills/authoring-agent-skills/SKILL.md`

## Quick Navigation

- **[Output Templates](./blueprints/output-templates.md)** — individual review + consolidated summary templates
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 scenarios: canonical, edge, misuse
- **[Execution Instructions](#execution-instructions)** — 3-step workflow
- **[Evaluation Criteria](#evaluation-criteria)** — A1–A6, B, C (official) + D1–D7 (team)
- **[Anti-Pattern Detection](#anti-pattern-detection)** — 11 detection rules
- **[Verification Loop](#verification-loop)** — Self-validation before saving
- **[External Resources](#external-resources)** — Official documentation from which criteria derive

---

## Agent Instructions

Act as an Agent Skills Quality Specialist. Evaluate each skill against the official Claude criteria
and the team conventions documented in `authoring-agent-skills`.

---

## Blueprints & Guardrails

### ✅ Always Do

- **Read reference files before evaluating** — read `.claude/skills/authoring-agent-skills/SKILL.md`
  and `.claude/skills/authoring-agent-skills/blueprints/three-tier-architecture.md` before emitting
  any criterion.
- **Confirm counts with real filesystem inspection** — use `ls`/`Glob` to enumerate the SKILL.md
  files present; never rely on self-reported counts or assume which files exist.
- **Cite the exact criterion in each finding** — every issue must reference the criterion (A1, B2,
  D3, etc.) and the location (filename + section).
- **Generate an individual file per evaluated skill** — at
  `.claude/skills/[skill-name]/[skill-name]-best-practices-review.md`.
- **Generate the consolidated summary at the end** — `.claude/skills/skills-best-practices-summary.md`
  with the comparative matrix of all skills.
- **Count real lines in SKILL.md** — use file reading to confirm the line count; do not estimate
  visually.

### ⚠️ Ask First

- **Third-party or legacy skills** — if the evaluated skill is marked as third-party or has
  "legacy" notices, ask the user whether to apply team criteria D1-D7 or only the official A-C
  criteria.
- **Skills without version context** — if SKILL.md does not declare a version, ask whether the
  skill is intentionally version-agnostic or if the context is missing.
- **Custom directory** — if the `$ARGUMENTS` argument points to a non-standard path, confirm before
  proceeding.
- **Skills with > 500 lines** — when SKILL.md exceeds 500 lines, ask whether the user wants only
  the diagnosis or also a proposed extraction to `blueprints/`.

### 🚫 Never Do

- **Never report a violation without citing criterion + location** — produces unactionable output.
  ✅ Always name the criterion (e.g. "A1 — description max 1536 chars") and the line or section
  where it occurs.
- **Never assume a skill meets a criterion without reading the file** — if the file was not read,
  do not assign a status. ✅ Read the complete file before evaluating; report "file not read" if
  inaccessible.
- **Never mix official criteria with team conventions in the same cell** — makes prioritization
  harder. ✅ Keep the A-C (official) and D (team) tables separate as in the template.
- **Never omit the "Recommendations by Priority" section** — it is the most actionable section.
  ✅ Always include it with HIGH / MEDIUM / LOW classification.
- **Never generate only the consolidated summary without individual files** — summary without detail
  does not allow correction. ✅ Generate both: individual file + summary.

#### Finding: incorrect vs. correct (side by side)

The format of each finding is the validator's primary output. Contrast:

```markdown
<!-- 🚫 INCORRECT — unactionable: no criterion, no location -->
- The description is too long and should be shortened.
- Some guardrails are missing.
```

```markdown
<!-- ✅ CORRECT — criterion + location + action -->
- **A1** (SKILL.md, frontmatter `description`, line 3): 1710 chars > limit 1536.
  Rewrite with "Use when…" trigger ≤ 1536.
- **D2** (SKILL.md, `## Blueprints & Guardrails`): `### ⚠️ Ask First` tier is missing.
  Add the tier with populated items.
```

---

## Execution Instructions

### Step 1: Load Reference Criteria

Read the following files before evaluating:
1. `.claude/skills/authoring-agent-skills/SKILL.md` — Team standard
2. `.claude/skills/authoring-agent-skills/blueprints/three-tier-architecture.md` — Three-tier architecture

### Step 2: Discover and Analyze Skills

Explore `.claude/skills/*/SKILL.md` (or the directory indicated in `$ARGUMENTS`) and evaluate each
skill against the criteria below.

---

## Evaluation Criteria

### A. Core Quality (Official — from Claude Best Practices)

**A1. YAML Frontmatter**
- `name`: max 64 chars, only lowercase/numbers/hyphens, no XML tags, no reserved words
  (`anthropic`, `claude`)
- `description`: non-empty, max 1536 chars, no XML tags
- Description in **third person** (not "I can help" or "You can use")
- Includes WHAT it does AND WHEN to use it

**A2. Conciseness**
- SKILL.md body under 500 lines
- Only adds context Claude does not already have
- No unnecessary explanations

**A3. Structure and Progressive Disclosure**
- Additional details in separate files (when needed)
- File references: maximum one level deep from SKILL.md
- Reference files >100 lines include a table of contents
- Descriptive file names (`form_validation_rules.md`, not `doc2.md`)

**A4. Content**
- No time-sensitive information (or in an "old patterns" section)
- Consistent terminology (do not mix "API endpoint", "URL", "route")
- Concrete examples, not abstract ones
- Do not offer too many options — provide a default + escape hatch

**A5. Workflows**
- Complex operations have clear sequential steps
- Feedback loops present for critical tasks (run → validate → fix → repeat)

**A6. File Paths**
- Forward slashes only (`scripts/helper.py`, not `scripts\helper.py`)
- Only relative paths or full URLs (never `C:\Users\...` or `/home/user/...`)

### B. Code and Scripts (Official)

**B1. Scripts solve problems** — do not delegate to the agent what a script can resolve
**B2. Explicit error handling** — scripts do not fail silently
**B3. No "magic constants"** — all values documented/justified
**B4. Listed dependencies** — required packages documented
**B5. Validation** — verification steps for critical operations

### C. Testing (Official)

**C1.** At least 3 evaluation scenarios created
**C2.** Tested with real usage scenarios
**C3.** Team feedback incorporated (if applicable)

### D. Team Conventions

**D1. Naming**: YAML `name` = folder name = kebab-case (gerund form preferred)
**D2. Three tiers**: ✅ Always Do, ⚠️ Ask First, 🚫 Never Do — all present and populated
**D3. Version Context**: Section included (if the skill is version-specific)
**D4. Verification Loop**: Commands present and tested
**D5. Anti-patterns**: Incorrect code + correct alternative side by side
**D6. Links**: All functional, no 404s
**D7. External resources**: Links to official documentation

---

### Step 3: Generate Validation Files

Generate **two artifacts** following the exact templates in
**[blueprints/output-templates.md](./blueprints/output-templates.md)**:

1. **One individual file per skill** —
   `.claude/skills/[skill-name]/[skill-name]-best-practices-review.md`
   (header + Summary + official table A1–A6/B/C + team table D1–D7 + Recommendations by Priority
   + Conclusions).
2. **The consolidated summary** — `.claude/skills/skills-best-practices-summary.md`
   (Executive Summary + Compliance Matrix with one row per skill + AVERAGE row + Global
   Recommendations).

Copy the blueprint structures verbatim; do not improvise the format.

---

## Anti-Pattern Detection

The validator must detect and report:

1. **SKILL.md exceeds 500 lines** — Recommend extracting content to `blueprints/`
2. **Vague or first-person description** — "Helps with docs" or "I can process files" → Correct to
   third person with trigger
3. **description exceeds 1536 chars** — Truncate and rewrite with "Use when..." trigger
4. **Windows-style paths** — `scripts\helper.py` → `scripts/helper.py`
5. **Deep nested references** — SKILL.md → A.md → B.md → C.md → Flatten to one level
6. **Too many options without a default** — "Use pypdf, or pdfplumber, or PyMuPDF" → Provide
   default
7. **Time-sensitive information** — absolute dates ("if before <month> <year>...") or
   "edition <year>" → Use "old patterns" section or anchor to version ("before upgrading to v2...")
8. **Incomplete guardrails** (team) — Only ✅ Always Do, missing ⚠️ or 🚫 → Flag as incomplete
9. **Anti-patterns without alternative** (team) — 🚫 without ✅ correct code → Flag as critical
10. **Magic constants** — `TIMEOUT = 47` without explanation → Document reason
11. **Scripts that delegate to the agent** — Script that simply fails and leaves the agent to
    resolve → Handle errors explicitly

---

## Verification Loop

Before saving the output files, the validator MUST run these commands and confirm the expected
output. Replace `<skills-dir>` with the validated directory (e.g. `.claude/skills`).

```bash
# 1. Skill count: number of review files must equal number of SKILL.md
find <skills-dir> -name SKILL.md | wc -l
find <skills-dir> -name '*-best-practices-review.md' | wc -l   # → same number
# 2. Summary exists and lists all skills
test -f <skills-dir>/skills-best-practices-summary.md && echo OK
# 3. Each skill has its review file (lists those MISSING — empty output = OK)
for f in <skills-dir>/*/SKILL.md; do d=$(dirname "$f"); s=$(basename "$d"); \
  test -f "$d/$s-best-practices-review.md" || echo "MISSING: $s"; done
# 4. Each review cites criteria (0 = failure: review without A#/B/C/D# references)
for r in <skills-dir>/*/*-best-practices-review.md; do \
  grep -qE '\b([A-D][0-9]?|B|C)\.' "$r" || echo "NO-CRITERIA: $r"; done
```

Content checklist (manual verification before saving):

- [ ] **Criteria covered** — each skill's table has exactly 8 official rows (A1–A6, B, C) and 7
  team rows (D1–D7).
- [ ] **Complete matrix** — the number of rows in the consolidated matrix == output of command 1.
- [ ] **Actionable findings** — each item in "Recommendations by Priority" references ≥1 criterion
  (A1, D2, etc.) + location.

All commands must exit with code `0` and no `MISSING:` / `NO-CRITERIA:` lines before saving.

---

## Output Format

- Technical and objective language
- Focus on specific problems, not generalizations
- Clearly differentiate: **official** criteria (from Claude docs) vs **team conventions**
- Compliance matrix for quick visualization
- Concrete and prioritized actions

---

## External Resources

### Official Claude Documentation
- [Claude Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — primary source of A-C criteria
- [Claude Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills) — skill definition and valid frontmatter

### Team Conventions
- [authoring-agent-skills SKILL.md](./../authoring-agent-skills/SKILL.md) — team standard (D criteria)
- [authoring-agent-skills — three-tier-architecture](./../authoring-agent-skills/blueprints/three-tier-architecture.md) — three-tier architecture
- [skill-frontmatter rules](./../../rules/skill-frontmatter.md) — frontmatter limits (description max 1536 chars, `allowed-tools` vs `tools`, etc.)

---

**Suggested invocation**:
```
Analyze the skills in this repository using the best practices validator.
```

**Expected output**: A `.claude/skills/[skill-name]/[skill-name]-best-practices-review.md` file per
skill + `.claude/skills/skills-best-practices-summary.md` with the consolidated comparative matrix.
