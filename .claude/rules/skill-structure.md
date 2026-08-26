---
name: skill-structure
description: "Structure and completeness rules for SKILL.md files. Enforces 500-line limit, required blueprints, and Quick Navigation requirements."
paths:
  - ".claude/skills/**/SKILL.md"
---

# Skill Structure Rules

## Line limit

**SKILL.md must not exceed 500 lines.**

If the file approaches 500 lines, move detailed content to `blueprints/` subdirectory files and replace with a summary + link. This is the progressive-disclosure principle.

## Required blueprints

Every action-command skill (one with `context: fork`) **must** have a `blueprints/` subdirectory containing at minimum:

| File | Purpose | Required |
|---|---|---|
| `blueprints/evaluation-scenarios.md` | Test scenarios for skill-evaluator | **Always required** |
| `blueprints/always-do-patterns.md` | Full ✅ patterns with code | Recommended when >3 patterns |
| `blueprints/never-do-patterns.md` | Full 🚫 patterns with ❌/✅ examples | Recommended when >3 patterns |

## Quick Navigation requirements

The `## Quick Navigation` section **must** link to:
- `blueprints/evaluation-scenarios.md` (always)
- `#blueprints--guardrails` or the equivalent guardrails section anchor (always)
- Any blueprint files that contain content referenced from the SKILL.md body

## Three-Tier Guardrails placement

The `## Blueprints & Guardrails` section (containing ✅, ⚠️, 🚫 summaries) **must** appear:
- After `## Quick Navigation`
- Before any long sections (Research Scope, Implementation Blueprint, etc.)

This ensures the most actionable content is visible before scrolling.

## ✅ Correct structure

```
## Quick Navigation
- [Blueprints & Guardrails](#blueprints--guardrails)
- [Evaluation Scenarios](./blueprints/evaluation-scenarios.md)
- ...

## Blueprints & Guardrails
### ✅ Always Do
...
### ⚠️ Ask First
...
### 🚫 Never Do
...

## [Long sections below]
```

## 🚫 Never Do

- **Never exceed 500 lines** — split to blueprints
- **Never place guardrails inside a subsection** (e.g., inside `## Research Scope §2`) — they must be top-level
- **Never omit `evaluation-scenarios.md`** from action-command skills
