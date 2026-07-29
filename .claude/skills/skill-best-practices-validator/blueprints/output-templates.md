# Output Templates — skill-best-practices-validator

Copy these structures verbatim when generating validation output. Two artifacts:
the **per-skill review file** and the **consolidated summary**.

## Contents

- [Per-skill review file](#per-skill-review-file)
- [Consolidated summary](#consolidated-summary)

---

## Per-skill review file

Write one per evaluated skill at `.claude/skills/[skill-name]/[skill-name]-best-practices-review.md`:

```markdown
# Best Practices Analysis: [skill-name]

**Date**: [Date]
**File**: `.claude/skills/[skill-name]/SKILL.md`
**Lines**: [N]
**Official Reference**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
**Team Reference**: .claude/skills/authoring-agent-skills/SKILL.md

---

## Summary

- Official criteria met: [X]/8
- Team conventions met: [X]/7
- Critical issues: [N]

---

## Official Criteria (Claude Best Practices)

| Criterion | Status | Notes |
|----------|--------|-------|
| A1. YAML Frontmatter | ✅/❌ | [detail] |
| A2. Conciseness (<500 lines) | ✅/❌ | [detail] |
| A3. Progressive Disclosure | ✅/❌ | [detail] |
| A4. Content (terminology, temporal) | ✅/❌ | [detail] |
| A5. Clear Workflows | ✅/❌ | [detail] |
| A6. File paths | ✅/❌ | [detail] |
| B. Code and Scripts | ✅/❌/N/A | [detail] |
| C. Testing/Evaluation | ✅/❌ | [detail] |

## Team Conventions

| Criterion | Status | Notes |
|----------|--------|-------|
| D1. Naming (gerund, kebab) | ✅/❌ | [detail] |
| D2. Three tiers (✅⚠️🚫) | ✅/❌ | [detail] |
| D3. Version Context | ✅/❌ | [detail] |
| D4. Verification Loop | ✅/❌ | [detail] |
| D5. Anti-patterns with alternatives | ✅/❌ | [detail] |
| D6. Functional links | ✅/❌ | [detail] |
| D7. External resources | ✅/❌ | [detail] |

---

## Recommendations by Priority

### HIGH (Block Functionality)
[List — e.g.: invalid YAML, empty description, body >500 lines]

### MEDIUM (Reduce Quality)
[List — e.g.: inconsistent terminology, broken links, no feedback loops]

### LOW (Optimization)
[List — e.g.: progressive disclosure can improve, naming does not use gerund]

---

## Conclusions
[Summary of issues and strengths]
```

---

## Consolidated summary

After all individual files, write `.claude/skills/skills-best-practices-summary.md`:

```markdown
# Best Practices Summary — Agent Skills

**Date**: [Date]
**Official Reference**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

---

## Executive Summary

- Skills evaluated: [N]
- Meet official criteria: [N] ([X]%)
- Meet team conventions: [N] ([X]%)
- Critical issues: [N]

---

## Compliance Matrix

| Skill | Official (A-C) | Team (D) | Total | Review |
|-------|---------------|------------|-------|--------|
| [skill-1] | [X]/8 | [X]/7 | [X]% | [skill-1-best-practices-review.md](skill-1/skill-1-best-practices-review.md) |
| [skill-2] | [X]/8 | [X]/7 | [X]% | [skill-2-best-practices-review.md](skill-2/skill-2-best-practices-review.md) |
| AVERAGE | [X]/8 | [X]/7 | [X]% | — |

---

## Global Recommendations by Priority

### HIGH (Block Functionality)
[Consolidated list]

### MEDIUM (Reduce Quality)
[Consolidated list]

### LOW (Optimization)
[Consolidated list]
```
