---
name: [domain]-best-practices-validator
description: 'Generates quality analysis and best practices adherence report for [ARTIFACT TYPE] based on [REFERENCE STANDARD]'
argument-hint: '[directory or file pattern to validate]'
---

# Prompt: [ARTIFACT TYPE] Best Practices Validator

## Objective
Generate a quality analysis and best practices adherence report for [ARTIFACT TYPE] based on:
- **Official**: [URL to official best practices / standard reference]
- **Team**: [path to team conventions file, e.g., `.github/skills/[skill-name]/SKILL.md`]

## Role
[ARTIFACT TYPE] Quality Specialist. Evaluate each [artifact] against official criteria and team conventions.

---

## Execution Workflow

### Step 1: Load Reference Criteria

Read the following files before evaluating:
1. `[path-to-team-conventions]` — Team standard
2. `[path-to-supporting-reference]` — Supporting patterns/architecture reference

### Step 2: Discover and Analyze [ARTIFACTS]

Explore `[discovery-pattern]` (e.g., `.github/skills/*/SKILL.md`) and evaluate each artifact against the criteria below.

---

## Evaluation Criteria

The criteria categories below (A through D) are quality dimensions, not pattern counts. A skill with 3 Always Do patterns and a skill with 9 Always Do patterns are both evaluated against the same criteria — what matters is whether each pattern meets the quality bar, not how many there are.

When evaluating, adapt the depth of assessment to the skill's domain complexity tier (Foundational / Standard / Complex). Complex skills have more patterns and integrations, so evaluation naturally covers more ground.

### A. [OFFICIAL STANDARD NAME] (from [source])

**A1. [Criterion Name]**
- [Sub-requirement 1]
- [Sub-requirement 2]
- [Sub-requirement 3]

**A2. [Criterion Name]**
- [Sub-requirement 1]
- [Sub-requirement 2]

**A3. [Criterion Name]**
- [Sub-requirement 1]
- [Sub-requirement 2]
- [Sub-requirement 3]

**A4. [Criterion Name]**
- [Sub-requirement 1]
- [Sub-requirement 2]

**A5. [Criterion Name]**
- [Sub-requirement 1]
- [Sub-requirement 2]

**A6. [Criterion Name]**
- [Sub-requirement 1]
- [Sub-requirement 2]

### B. [SECONDARY CATEGORY] (from [source])

**B1.** [Criterion description]
**B2.** [Criterion description]
**B3.** [Criterion description]
**B4.** [Criterion description]
**B5.** [Criterion description]

### C. [TERTIARY CATEGORY] (from [source])

**C1.** [Criterion description]
**C2.** [Criterion description]
**C3.** [Criterion description]

### D. Team Conventions

**D1. [Convention Name]**: [description]
**D2. [Convention Name]**: [description]
**D3. [Convention Name]**: [description]
**D4. [Convention Name]**: [description]
**D5. [Convention Name]**: [description]
**D6. [Convention Name]**: [description]
**D7. [Convention Name]**: [description]

---

### Step 3: Generate Validation Report

Create a file `[REPORT_FILENAME].md` with the following structure:

```markdown
# [ARTIFACT TYPE] Best Practices Analysis

**Date**: [Date]
**Official Reference**: [URL]
**Team Reference**: [path]

---

## Executive Summary

- Artifacts evaluated: [N]
- Meet official criteria: [N] ([X]%)
- Meet team conventions: [N] ([X]%)
- Critical issues: [N]

---

## Per-Artifact Evaluation

### Artifact: [name]
**File**: `[path]`
**Lines**: [N]

#### Official Criteria ([SOURCE])
| Criterion | Status | Notes |
|-----------|--------|-------|
| A1. [Name] | ✅/❌ | [detail] |
| A2. [Name] | ✅/❌ | [detail] |
| A3. [Name] | ✅/❌ | [detail] |
| A4. [Name] | ✅/❌ | [detail] |
| A5. [Name] | ✅/❌ | [detail] |
| A6. [Name] | ✅/❌ | [detail] |
| B. [Category] | ✅/❌/N/A | [detail] |
| C. [Category] | ✅/❌ | [detail] |

#### Team Conventions
| Criterion | Status | Notes |
|-----------|--------|-------|
| D1. [Name] | ✅/❌ | [detail] |
| D2. [Name] | ✅/❌ | [detail] |
| D3. [Name] | ✅/❌ | [detail] |
| D4. [Name] | ✅/❌ | [detail] |
| D5. [Name] | ✅/❌ | [detail] |
| D6. [Name] | ✅/❌ | [detail] |
| D7. [Name] | ✅/❌ | [detail] |

**Key findings**: [Summary of issues and strengths]

---

## Compliance Matrix

| Artifact | Official (A-C) | Team (D) | Total |
|----------|----------------|----------|-------|
| [artifact-1] | [X]/[MAX] | [X]/[MAX] | [X]% |
| [artifact-2] | [X]/[MAX] | [X]/[MAX] | [X]% |
| AVERAGE | [X]/[MAX] | [X]/[MAX] | [X]% |

---

## Recommendations by Priority

### HIGH (Block Functionality)
[List — e.g., invalid YAML, empty description, exceeds size limits]

### MEDIUM (Reduce Quality)
[List — e.g., inconsistent terminology, broken links, missing feedback loops]

### LOW (Optimization)
[List — e.g., progressive disclosure can improve, naming not following convention]

---

## Conclusions
[General summary and next actions]
```

---

## Anti-Pattern Detection

The validator must detect and report:

1. **[Anti-pattern 1]** — [detection criteria] → [recommendation]
2. **[Anti-pattern 2]** — [detection criteria] → [recommendation]
3. **[Anti-pattern 3]** — [detection criteria] → [recommendation]
4. **[Anti-pattern 4]** — [detection criteria] → [recommendation]
5. **[Anti-pattern 5]** — [detection criteria] → [recommendation]
6. **[Anti-pattern 6]** — [detection criteria] → [recommendation]
7. **[Anti-pattern 7]** — [detection criteria] → [recommendation]
8. **[Anti-pattern 8]** — [detection criteria] → [recommendation]
9. **[Anti-pattern 9]** — [detection criteria] → [recommendation]
10. **[Anti-pattern 10]** — [detection criteria] → [recommendation]

---

## Output Format

- Technical and objective language
- Focus on specific problems, not generalizations
- Clearly differentiate: **official** criteria vs **team** conventions
- Compliance matrix for quick visualization
- Concrete and prioritized actions

---

**Suggested invocation**:
```
Analyze the [artifacts] in this repository using the [domain] best practices validator.
```

**Expected output**: `[REPORT_FILENAME].md` with complete analysis and prioritized recommendations.
