---
name: project-analysis-validator
description: >
  Validates an entire agent project for structural integrity, CLAUDE.md accuracy, router
  consistency, frontmatter correctness, and naming conventions across all artifacts. Use when
  auditing the health of a complete Claude Code agent project before a release, after a migration,
  or when docs/implementation drift is suspected (e.g. "/project-analysis-validator .claude/").
argument-hint: "Root directory of the agent project to validate (e.g. .claude/)"
context: fork
agent: quality-validator
disable-model-invocation: true
---
# Prompt: Agent Project Analysis Validator

## Objective

Produce a structural and consistency audit of an entire Claude Code agent project. The validator
covers seven dimensions (P1–P7) and emits one consolidated report with graded findings.

## Quick Navigation

- **[Evaluation Checklist](./blueprints/evaluation-checklist.md)** — full dimension rubric P1–P7
  with pass/warn/fail criteria
- **[Execution Instructions](#execution-instructions)** — 4-step workflow
- **[Dimensions Summary](#dimensions-summary)** — P1–P7 overview
- **[Anti-Pattern Detection](#anti-pattern-detection)** — 9 detection rules
- **[Verification Loop](#verification-loop)** — self-validation commands
- **[Output Format](#output-format)** — report structure

---

## Agent Instructions

Act as an Agent Project Audit Specialist. Validate the project rooted at `$ARGUMENTS` (default:
`.claude/`) across all seven dimensions. Read every agent file and a representative sample of
SKILL.md files to confirm facts; never rely on counts from memory.

---

## Blueprints & Guardrails

### ✅ Always Do

- **Confirm file counts with real filesystem inspection** — use `Glob`/`Grep`/`ls` to enumerate;
  never trust self-reported counts.
- **Read CLAUDE.md fully** before evaluating P2 (accuracy) — you need the claimed counts and
  routing table.
- **Read all agent files** (`.claude/agents/*.md`) — required for P3 (frontmatter) and P4 (router).
- **Cite dimension + evidence for every finding** — e.g. "P4 — skill `foo` has `context: fork`
  but `agent: bar-agent` has no matching file in `.claude/agents/`."
- **Generate the consolidated report** at `.claude/project-analysis-report.md`.
- **Grade each dimension** — ✅ Pass / ⚠️ Warn / 🚫 Fail — with counts of issues per dimension.

### ⚠️ Ask First

- **Non-standard project layout** — if the root dir does not contain `agents/`, `skills/`, or
  `rules/`, ask the user to confirm the project layout before continuing.
- **Worktrees or partial clones** — if `.claude/worktrees/` is present or only a subset of the
  project is available, ask whether to include or exclude worktree artifacts from the audit.
- **Large projects (> 50 skills)** — offer a targeted audit (specific subdir) or full sweep.

### 🚫 Never Do

- **Never report a dimension as Pass without reading the relevant files** — ✅ read the file, then
  grade.
- **Never rewrite or edit any audited file** — this is a read-only validator. ✅ Report findings
  and suggest fixes; leave editing to the user or `--fix` mode if explicitly requested.
- **Never count skills from CLAUDE.md claims alone** — ✅ always use `Glob` to enumerate
  `.claude/skills/*/SKILL.md`.

#### Finding: incorrect vs. correct

```markdown
<!-- 🚫 INCORRECT — no dimension, no evidence -->
- The routing table in CLAUDE.md is outdated.

<!-- ✅ CORRECT — dimension + exact evidence -->
- **P2** (CLAUDE.md, "Roteamento" table): claims `quality-validator` routes 4 commands; actual
  `.claude/skills/` has 5 skills with `agent: quality-validator` — `project-analysis-validator`
  is missing from the table.
```

---

## Execution Instructions

### Step 1: Enumerate Artifacts

```bash
# Agents
ls .claude/agents/*.md
# Skills
find .claude/skills -name SKILL.md | wc -l
# Rules
ls .claude/rules/
# Key docs
ls CLAUDE.md docs/ 2>/dev/null
```

### Step 2: Load Reference Files

Read the following before grading:
1. `CLAUDE.md` — project manifest (counts, routing table, structure section)
2. All `.claude/agents/*.md` — frontmatter + routing description
3. `.claude/rules/skill-frontmatter.md` — active frontmatter conventions

### Step 3: Evaluate All Seven Dimensions

See **[blueprints/evaluation-checklist.md](./blueprints/evaluation-checklist.md)** for the full
rubric. Summary:

| Dim | Focus | Key check |
|-----|-------|-----------|
| P1 | Structure | Required dirs present |
| P2 | CLAUDE.md accuracy | Counts + routing table match disk |
| P3 | Frontmatter | All required fields, valid values |
| P4 | Router consistency | Every `context: fork` skill has a valid agent |
| P5 | Naming conventions | kebab-case, name field = folder/file name |
| P6 | Progressive disclosure | SKILL.md < 500 lines, blueprints used for extras |
| P7 | Rule coverage | ≥ 1 rule file documents project conventions |

### Step 4: Generate Report

Save the consolidated report to `.claude/project-analysis-report.md` following the
[Output Format](#output-format).

---

## Dimensions Summary

**P1 — Directory Structure**
Required dirs: `.claude/agents/`, `.claude/skills/`, `.claude/rules/`. CLAUDE.md present at
project root. Warn for: no `templates/`, unexpected top-level dirs.

**P2 — CLAUDE.md Accuracy**
Counts (skills, agents, commands) claimed in CLAUDE.md match `Glob`/`ls` output. Routing table
covers all skills with `context: fork`. Structure section lists all real dirs.

**P3 — Frontmatter Correctness**
Agents: `name`, `description`, `tools`, optional `model` (valid value). Skills: `name`,
`description` (≤ 1536 chars, "Use when…" trigger). Command skills: `context: fork`, `agent:`,
`disable-model-invocation: true`. Field `allowed-tools:` on skills, `tools:` on agents.

**P4 — Router Consistency**
Every skill with `context: fork` must declare `agent:` matching an existing
`.claude/agents/<name>.md`. Every `disable-model-invocation: true` skill must also have
`context: fork`. The agent's description must mention the routed command(s).

**P5 — Naming Conventions**
Skill folder name = SKILL.md `name:` field. Agent file basename = agent `name:` field. All names
kebab-case only (no underscores, no spaces, no uppercase). Prefer gerund-noun for skills, role for
agents (per CLAUDE.md conventions).

**P6 — Progressive Disclosure**
Each SKILL.md must be < 500 lines. Content exceeding that threshold should live in
`blueprints/*.md` linked from SKILL.md. Warn when blueprints are missing but SKILL.md is > 300
lines.

**P7 — Rule Coverage**
At least one `.claude/rules/*.md` file covers frontmatter conventions. Warn when no rule file
exists or when the rule file is more than 12 months old (last commit).

---

## Anti-Pattern Detection

1. **Orphan `context: fork`** — skill has `context: fork` but no `agent:` field.
2. **Broken agent reference** — `agent: foo` but `.claude/agents/foo.md` does not exist.
3. **Missing `disable-model-invocation`** — command skill (`context: fork`) lacks the flag,
   allowing accidental auto-invocation.
4. **`tools:` on a skill** — skills must use `allowed-tools:`, not `tools:`.
5. **`allowed-tools:` on an agent** — agents must use `tools:`, not `allowed-tools:`.
6. **Name/folder mismatch** — `name: foo-bar` in `.claude/skills/foo_bar/SKILL.md`.
7. **Overlong SKILL.md without blueprints** — SKILL.md > 500 lines with no `blueprints/` dir.
8. **Dead doc reference** — CLAUDE.md routing table lists a command that has no matching skill
   folder in `.claude/skills/`.
9. **CLAUDE.md count drift** — CLAUDE.md states N skills/agents but disk has a different count.

---

## Verification Loop

Before saving the report, run these commands and confirm expected output:

```bash
# 1. Skill count (disk vs CLAUDE.md claim)
find .claude/skills -name SKILL.md | wc -l

# 2. Agent count
ls .claude/agents/*.md | wc -l

# 3. All context:fork skills have an agent: field
grep -rl "context: fork" .claude/skills | xargs grep -L "^agent:" | sed 's/^/MISSING agent: /'

# 4. All agent: values resolve to real files
grep -r "^agent:" .claude/skills --include=SKILL.md -h | \
  awk '{print ".claude/agents/"$2".md"}' | sort -u | \
  while read f; do test -f "$f" || echo "BROKEN: $f"; done

# 5. Report file exists
test -f .claude/project-analysis-report.md && echo "Report OK"
```

Content checklist (manual before saving):
- [ ] All 7 dimensions graded (✅ / ⚠️ / 🚫)
- [ ] Every 🚫 / ⚠️ finding cites dimension + location + fix
- [ ] Commands 3 and 4 above show no output (clean = OK)

---

## Output Format

Report saved to `.claude/project-analysis-report.md`:

```markdown
# Agent Project Analysis Report
**Date:** <ISO date>  **Target:** <argument>  **Validator:** project-analysis-validator

## Executive Summary
<2–3 sentences: overall health, critical blockers count, improvement areas>

## Dimension Results

| Dim | Name | Grade | Issues |
|-----|------|-------|--------|
| P1  | Structure | ✅/⚠️/🚫 | N |
| P2  | CLAUDE.md accuracy | ... | N |
| P3  | Frontmatter | ... | N |
| P4  | Router consistency | ... | N |
| P5  | Naming | ... | N |
| P6  | Progressive disclosure | ... | N |
| P7  | Rule coverage | ... | N |

## Findings by Dimension

### P1 — Structure
...

### P2 — CLAUDE.md Accuracy
...

[one section per dimension]

## Recommendations by Priority

### 🚫 Critical (blocking)
...

### ⚠️ Important (improve soon)
...

### ℹ️ Low (nice to fix)
...
```

---

## External Resources

- [Claude Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills) — frontmatter fields and validation rules
- [Claude Subagents](https://platform.claude.com/docs/en/agents-and-tools/claude-code-subagents) — agent conventions
- [authoring-agent-skills SKILL.md](./../authoring-agent-skills/SKILL.md) — team standard
- [skill-frontmatter rules](./../../rules/skill-frontmatter.md) — active frontmatter conventions

---

**Suggested invocation**:
```
/project-analysis-validator .claude/
```

**Expected output**: `.claude/project-analysis-report.md` with graded findings per dimension.
