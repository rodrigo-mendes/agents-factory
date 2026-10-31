---
name: [verbing-tech-task]
description: "[Action verb] [what] with [Tech] v[X.Y]+. Use when [trigger context]."
---

> ⚙️ **Technology-agnostic template.** Replace ALL `[PLACEHOLDERS]`. Names in `e.g.`/`[e.g., ...]` are illustrative examples only — they are not standards or defaults of this factory.

## Function
Specialist in [SPECIALTY] for [TECHNOLOGY/FRAMEWORK] v[VERSION]

## Version Context

**Technology/Framework**: [TECHNOLOGY NAME]
**Target version**: v[VERSION]
**Release date**: [DATE]
**Support status**: Active

**Important changes in this version**:
- [Change 1]
- [Change 2]
- [Change 3]

**Deprecated**: [None or list deprecated features]

⚠️ **CRITICAL — Agent Warning**:
This skill is specific to version v[VERSION].
Reject ANY patterns from versions <[VERSION].
Do not mix patterns from previous versions with v[VERSION].

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory patterns with code examples
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Cross-service integration examples
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns** (include all patterns the domain requires — see [Domain Complexity Tiers](#domain-complexity-tiers)):
- **[Mandatory Pattern 1]** — [1-2 line description of what to do and consequence if omitted]
- **[Mandatory Pattern 2]** — [1-2 line description]
- **[...]** — [Add as many patterns as the domain demands]

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points** (include all architectural crossroads):
- **[Decision Point 1]** — [Options summary: Option A vs Option B]
- **[Decision Point 2]** — [Options summary]
- **[...]** — [Add as many decision points as the domain presents]

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns** (include all anti-patterns discovered):
- **[Anti-pattern 1]** — [Why prohibited. Consequence]
- **[Anti-pattern 2]** — [Why prohibited. Consequence]
- **[...]** — [Add as many anti-patterns as the domain has]

---

## Integration Patterns

For complete integration code examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Summary of integrations**:
- **[TECHNOLOGY] ↔ [RELATED TECH 1]** — [Brief description of integration pattern]
- **[TECHNOLOGY] ↔ [RELATED TECH 2]** — [Brief description]
- **[TECHNOLOGY] ↔ [RELATED TECH 3]** — [Brief description]

**Common problems**:
- **Problem**: [Description] → **Solution**: [Fix]
- **Problem**: [Description] → **Solution**: [Fix]

---

## Verification Loop

The agent MUST execute after each code generation:

### 1. Build / Compile
```
[build command]
# Expected: [success message]
# Exit code: 0
```

### 2. Unit Tests
```
[test command]
# Expected: [success message, test count]
# Exit code: 0
```

### 3. Smoke Test / Health Check
```
[smoke test command]
# Expected: [success output]
# Exit code: 0
```

**Troubleshooting**:
- [Error 1] → [Solution]
- [Error 2] → [Solution]
- [Error 3] → [Solution]

---

## Quick Reference

**Essential commands**:
```
[install/setup command]
[build command]
[test command]
[run command]
```

**Critical limits**:

| Resource | Limit | Scope |
|----------|-------|-------|
| [Resource 1] | [Limit] | [Scope] |
| [Resource 2] | [Limit] | [Scope] |
| [Resource 3] | [Limit] | [Scope] |

---

## Blueprints Directory Structure

```
.claude/skills/[skill-name]/
├── SKILL.md                              ← This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             ← ✅ Mandatory patterns with full code examples
    ├── ask-first-decisions.md            ← ⚠️ Decision matrices with option code examples
    ├── never-do-patterns.md              ← 🚫 Anti-patterns with ❌ wrong / ✅ correct examples
    ├── integration-patterns.md           ← Cross-service integration examples
    └── [domain-specific].md              ← Additional files as needed
```

**When to use blueprints/** (recommended):
- Code examples exceed 30 lines
- Multiple variations of a pattern exist
- Integration examples need full context (imports, config, test)
- Skill file would exceed ~300 lines without delegation

**When to keep inline** (simple skills):
- All patterns fit comfortably in SKILL.md summary (no scrolling fatigue)
- Code examples are short (<15 lines each)
- Single technology with no integrations

### Domain Complexity Tiers

Pattern counts should be driven by domain needs, not template minimums:

| Tier | Always Do | Ask First | Never Do | When |
|------|-----------|-----------|----------|------|
| **Foundational** | 3-4 | 2-3 | 2-3 | Single integration, wrapper/orchestrator |
| **Standard** | 5-6 | 3-4 | 4-5 | Multi-concern, moderate config surface |
| **Complex** | 7-9 | 4-6 | 5-7 | Security-critical, multi-layer, compliance |

**Quality rule**: Include every pattern the domain requires. Never pad to reach a count; never omit to fit under a cap.

---

## External Resources

### Official Documentation
- [Link to main documentation]
- [Link to API reference]
- [Link to changelog/release notes]

### Security & Best Practices
- [Link to security guide]
- [Link to best practices]
- [Link to migration guide]

---

## Claude Code — frontmatter options

Skills in Claude Code accept fields beyond `name`/`description`. Choose based on type:

| Field | When to use |
|---|---|
| `allowed-tools:` | Restrict the skill's tools (least-privilege). Do **not** use `tools:` (that is for subagents). |
| `argument-hint: "..."` | The skill receives argument(s) via `/name <arg>` (accessible in the body as `$ARGUMENTS`/`$1`). Quote values containing `:`. |
| `context: fork` | Run the skill in an isolated subagent (long-running flows). Combine with `agent:`. |
| `agent: <subagent>` | Route execution to a subagent from `.claude/agents/` (mirrors the `agent:` field from Copilot). |
| `disable-model-invocation: true` | Deliberate action: only runs via `/name`, excluded from auto-listing (cost ~zero). Knowledge skills **omit** this field to remain auto-invocable. |

**Knowledge skill** (auto-invocable): only `name` + `description` (with "Use when…").
**Action command** (researcher/generator/validator/auditor):
`name` + `description` + `argument-hint` + `context: fork` + `agent:` + `disable-model-invocation: true`.
