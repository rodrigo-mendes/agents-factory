---
name: instructions-best-practices-validator
description: Analyzes instruction/rule files for quality and adherence to official (GitHub/VS Code) best practices and team conventions. Use when validating instruction or .claude/rules files.
argument-hint: "Directory of instructions/rules to validate"
context: fork
agent: quality-validator
disable-model-invocation: true
---
# Prompt: Custom Instructions Best Practices Validator

## Objective
Generate a quality and best-practices adherence analysis of `.instructions.md` files based on:
- **Official GitHub**: https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot
- **Official VS Code**: https://code.visualstudio.com/docs/copilot/customization/custom-instructions
- **Examples Library**: https://docs.github.com/en/copilot/tutorials/customization-library/custom-instructions
- **Team conventions**: established in `.claude/rules/` (Claude Code) or `.github/instructions/` (Copilot) of the current repository

## Quick Navigation

- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 scenarios: canonical, edge, misuse
- **[Verification Loop](#verification-loop)** — Self-check before saving the report
- **[External Resources](#external-resources)** — Official documentation from which criteria are derived

---

## Agent Instructions

Act as a Custom Instructions Quality Specialist. Evaluate each `.instructions.md` against the official GitHub/VS Code criteria and team conventions.

---

## Blueprints & Guardrails

### ✅ Always Do

- **Read at least 3 existing instruction files as style references** before issuing any findings — establish the team conventions baseline.
- **Confirm `applyTo` exists in every file** — its absence is the most critical issue; without it, instructions are never applied automatically.
- **Cite the exact criterion and file in every finding** — each issue must reference the criterion (A1, B2, E3, etc.) and the affected filename.
- **Analyze overlaps and gaps in `applyTo` patterns** — pattern coverage analysis is a mandatory section of the report.
- **Differentiate official criteria (A-D) from team conventions (E)** in separate tables — enables correct prioritization.
- **Confirm referenced files exist** — if an `.instructions.md` references another file or skill, verify the target exists.

### ⚠️ Ask First

- **Global `applyTo: "**"` pattern** — if an excessively broad pattern is detected, ask whether it is intentional (e.g., global project instructions) before marking it as a violation.
- **Mixed-language instructions** — if the repository has instructions in multiple languages, ask what the canonical language is before evaluating consistency.
- **Files with >300 lines** — when a file exceeds 300 lines, ask whether the user wants only the diagnosis or also a split proposal.
- **Conflicts between files with the same `applyTo`** — before marking as a violation, ask whether the conflicting instructions are intentional (e.g., one overrides the other by load order).

### 🚫 Never Do

- **Never omit the `applyTo` analysis** — it is the most critical field; a file without `applyTo` never activates automatically. ✅ Always verify presence, glob validity, and pattern specificity.
- **Never mark a rule as good just because it exists** — quality requires that it include the reasoning ("Use X because Y"). ✅ Verify that each rule explains WHY it exists.
- **Never report a violation without citing the file and section** — produces unactionable output. ✅ Name the exact file (e.g., `terraform-standards.instructions.md`) and the section or line.
- **Never ignore conflicts between files** — conflicting instructions with the same `applyTo` produce non-deterministic behavior. ✅ List every conflicting pair with their patterns and the rules that contradict each other.
- **Never generate the report without the "applyTo Patterns Analysis" section** — overlaps and gaps are as important as per-file findings. ✅ The pattern analysis section is mandatory.

---

## Execution Instructions

### Step 1: Load Reference Criteria

Read the following before evaluating:
1. `.claude/rules/` (Claude Code) or `.github/instructions/` (Copilot) — list all existing files to understand team conventions
2. At least 3 existing `.instructions.md` files as style reference

### Step 2: Discover and Analyze Instructions

Explore `.claude/rules/*.md` (Claude Code) or `.github/instructions/*.instructions.md` (Copilot) and evaluate each file against the criteria below.

---

## Evaluation Criteria

### A. YAML Frontmatter (Official — GitHub + VS Code)

**A1. `name` field**
- Present and descriptive
- Kebab-case (lowercase, hyphens)
- Maximum 64 characters
- Matches the filename (without `.instructions.md` extension)

**A2. `description` field**
- Present and not empty
- Maximum 1536 characters
- Describes WHAT it does AND WHEN it activates
- Third person (not "I help" or "You can")
- Specific enough for semantic matching

**A3. `applyTo` field**
- Present (if absent, instructions are NEVER applied automatically)
- Valid glob pattern with forward slashes only
- Path relative to workspace root
- Specific (does not use `**` unless intentionally global)
- Multiple patterns comma-separated when applicable

**A4. `excludeAgent` field (optional)**
- If present, valid value: `"code-review"` or `"cloud-agent"`

### B. Content and Structure (Official — VS Code Best Practices)

**B1. Conciseness**
- Short, self-contained instructions
- Each instruction is a simple, clear statement
- No unnecessary explanations of concepts Copilot already knows
- Focused on non-obvious rules (not repeating what linters/formatters already do)

**B2. Reasoning included**
- Rules include WHY the convention exists
- The AI makes better decisions in edge cases when it understands the reason
- Correct example: "Use `date-fns` instead of `moment.js` because moment.js is deprecated and increases bundle size"
- Incorrect example: "Use `date-fns`" (without justification)

**B3. Concrete examples**
- Preferred patterns shown with concrete code
- Patterns to avoid shown with concrete code
- Not abstract — always with real examples

**B4. Natural language in Markdown**
- Clean Markdown format
- No XML tags or proprietary formats
- Whitespace between instructions for readability

**B5. Default + Escape Hatch**
- Provides a clear default for common decisions
- States when it is valid to deviate from the default
- Does not offer too many options without a recommendation

### C. Paths and References (Official)

**C1. Forward slashes only**
- `src/main/java/**/*.java` ✅
- `src\main\java\**\*.java` ❌

**C2. Relative paths or full URLs**
- `./blueprints/pattern.md` ✅
- `https://docs.example.com/guide` ✅
- `C:\Users\dev\project\file.md` ❌
- `/home/user/project/file.md` ❌

**C3. References to other files**
- Markdown links to reference workspace files
- Verifiable links (existing targets)
- Maximum one level of depth from the instruction file

### D. Scope and Granularity (Official — GitHub)

**D1. Single Responsibility**
- Each file covers ONE coherent topic/domain
- Does not mix unrelated concerns
- Filename reflects its exact scope

**D2. `applyTo` granularity**
- Pattern not too broad (avoid `**/*` without reason)
- Pattern not too restrictive (covers all relevant files)
- Consistent with other files in the same domain

**D3. No conflicts between files**
- Does not contradict other `.instructions.md` in the same repository
- If multiple files apply to the same glob, they do not generate conflicting instructions

### E. Team Conventions

**E1. Consistent naming**
- Format: `{domain}-{sub-domain}.instructions.md`
- Examples: `java-functions-fdk`, `terraform-standards`, `java-functions-error-handling`
- Grouping pattern by technology + concern

**E2. Role Statement**
- First line of body defines the agent role: "You are a [Role] specialist..."
- Specific to the file's domain

**E3. Version Context section (if applicable)**
- Technology versions explicit
- Clear version constraints (e.g., "FDK v1.1.x", "Terraform v1.11+")

**E4. Code as instruction**
- Code blocks with correct + incorrect pattern
- Comments in code: `// ✅ CORRECT:` and `// 🚫 WRONG:`
- Correct language tag in code fences

**E5. Skill Integration (if routing file)**
- Complete keyword → skill mapping table
- All referenced skill paths exist
- Integration workflow documented

**E6. Functional links**
- Valid cross-references to other instructions/skills
- External links to official documentation
- No 404s

---

### Step 3: Generate Validation Report

Create a file `INSTRUCTIONS_BEST_PRACTICES_REVIEW.md` with the following structure:

```markdown
# Custom Instructions Best Practices Analysis

**Date**: [Date]
**Official GitHub Reference**: https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot
**Official VS Code Reference**: https://code.visualstudio.com/docs/copilot/customization/custom-instructions
**Team Reference**: .github/instructions/

---

## Executive Summary

- Instructions evaluated: [N]
- Meet official criteria: [N] ([X]%)
- Meet team conventions: [N] ([X]%)
- Critical issues: [N]

---

## Per-File Evaluation

### Instruction: [filename]
**File**: `.github/instructions/[name].instructions.md`
**Lines**: [N]
**applyTo**: `[pattern]`

#### Official Criteria (GitHub + VS Code)
| Criterion | Status | Notes |
|----------|--------|-------|
| A1. name (kebab-case, max 64) | ✅/❌ | [detail] |
| A2. description (clear, third person) | ✅/❌ | [detail] |
| A3. applyTo (valid glob, specific) | ✅/❌ | [detail] |
| A4. excludeAgent (if present) | ✅/❌/N/A | [detail] |
| B1. Conciseness | ✅/❌ | [detail] |
| B2. Reasoning included | ✅/❌ | [detail] |
| B3. Concrete examples | ✅/❌ | [detail] |
| B4. Clean Markdown | ✅/❌ | [detail] |
| B5. Default + Escape Hatch | ✅/❌ | [detail] |
| C. Paths and references | ✅/❌ | [detail] |
| D1. Single Responsibility | ✅/❌ | [detail] |
| D2. applyTo granularity | ✅/❌ | [detail] |
| D3. No conflicts | ✅/❌ | [detail] |

#### Team Conventions
| Criterion | Status | Notes |
|----------|--------|-------|
| E1. Consistent naming | ✅/❌ | [detail] |
| E2. Role Statement | ✅/❌ | [detail] |
| E3. Version Context | ✅/❌ | [detail] |
| E4. Code as instruction | ✅/❌ | [detail] |
| E5. Skill Integration | ✅/❌/N/A | [detail] |
| E6. Functional links | ✅/❌ | [detail] |

**Key Findings**: [Summary of issues and strengths]

---

## Compliance Matrix

| Instruction | Official (A-D) | Team (E) | Total |
|-------------|---------------|------------|-------|
| [instruction-1] | [X]/13 | [X]/6 | [X]% |
| [instruction-2] | [X]/13 | [X]/6 | [X]% |
| AVERAGE | [X]/13 | [X]/6 | [X]% |

---

## applyTo Patterns Analysis

### Pattern Coverage
| Pattern | Files using it | Overlaps |
|---------|-----------------|----------|
| `**/*.tf` | terraform-*.instructions.md | [list of overlaps] |
| `**/src/main/java/**/*.java` | java-functions-*.instructions.md | [list of overlaps] |

### Conflicts Detected
[List of instructions applying to the same glob with potentially conflicting rules]

### Gaps Detected
[File types with no coverage by any instruction]

---

## Recommendations by Priority

### HIGH (Block Functionality)
[List — e.g.: missing applyTo, empty description, malformed YAML]

### MEDIUM (Reduce Quality)
[List — e.g.: no reasoning in rules, abstract examples, inconsistent naming]

### LOW (Optimization)
[List — e.g.: conciseness improvable, generic role statement]

---

## Conclusions
[General summary and next actions]
```

---

## Anti-Pattern Detection

The validator must detect and report:

1. **Missing `applyTo`** — the file is NEVER applied automatically (manual attachment only)
2. **Overly broad `applyTo`** — `"**"` or `"**/*"` without clear justification
3. **Vague description** — "Helps with code" → correct to a specific description with trigger
4. **First-person description** — "I help you with..." → third person
5. **Windows-style paths** — `src\main\java` → `src/main/java`
6. **Absolute paths** — `/home/user/...` or `C:\Users\...` → relative paths
7. **Monolithic file** — a single `.instructions.md` with >300 lines covering multiple concerns → split
8. **Rules without justification** — "Use X" without explaining why → add reasoning
9. **Only abstract rules without examples** — "Follow best practices" → concrete code
10. **Conflict between files** — two instructions with the same `applyTo` giving contradictory guidance
11. **Name does not match filename** — `name: foo` in file `bar.instructions.md`
12. **Invalid glob patterns** — backslashes, absolute paths, incorrect syntax
13. **Temporal information without marking** — "The new API (released 2024)" → mark as version context
14. **Referenced skills that don't exist** — link to `.claude/skills/X/SKILL.md` where X does not exist

---

## Verification Loop

Before saving the report, the validator MUST self-verify:

1. **File count** — confirm the number of files evaluated in the Compliance Matrix matches those found with `ls`/`Glob` in the target directory.
2. **Mandatory applyTo section** — verify the "applyTo Patterns Analysis" section is present with three subsections: Coverage, Conflicts, Gaps.
3. **Findings with cited criterion** — every item in "Recommendations by Priority" must reference at least one criterion (A3, B2, E1, etc.) and a specific file.
4. **Referenced links** — if the report links to skills or instruction files, verify the paths exist before including them.
5. **Complete tables** — each evaluated file must have exactly 13 rows of official criteria (A1-A4, B1-B5, C, D1-D3) and 6 rows of team conventions (E1-E6).

---

## Output Format

- Technical and objective language
- Focus on specific problems, not generalizations
- Clearly differentiate: **official** criteria (from GitHub/VS Code docs) vs **team conventions**
- Analysis of `applyTo` patterns as a special section (overlaps, gaps, conflicts)
- Compliance matrix for quick visualization
- Concrete and prioritized actions

---

## External Resources

### Official GitHub Copilot Documentation
- [Adding repository custom instructions for GitHub Copilot](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot) — primary source for criteria A-D
- [Configure custom instructions (GitHub how-to)](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions) — `applyTo`, `excludeAgent` fields and examples
- [Custom instructions library](https://docs.github.com/en/copilot/tutorials/customization-library/custom-instructions) — canonical examples by domain

### Official VS Code Documentation
- [Custom instructions (VS Code)](https://code.visualstudio.com/docs/copilot/customization/custom-instructions) — best practices for conciseness, reasoning, and scope

### Team Conventions
- [skill-frontmatter rules](./../../rules/skill-frontmatter.md) — frontmatter rules for `.claude/rules/` and `.claude/agents/`
- [authoring-agent-skills SKILL.md](./../authoring-agent-skills/SKILL.md) — skills ecosystem context

---

**Suggested invocation**:
```
Analyze the .instructions.md files in this repository using the best practices validator.
```

**Expected output**: `INSTRUCTIONS_BEST_PRACTICES_REVIEW.md` with complete analysis and prioritized recommendations.
