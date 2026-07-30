# Evaluation Checklist — Project Analysis Validator

Full rubric for dimensions P1–P7. Each item grades as ✅ Pass / ⚠️ Warn / 🚫 Fail.

---

## P1 — Directory Structure

| Check | Pass | Warn | Fail |
|-------|------|------|------|
| `.claude/agents/` exists | present | — | absent |
| `.claude/skills/` exists | present | — | absent |
| `.claude/rules/` exists | present | — | absent |
| `CLAUDE.md` at project root | present | — | absent |
| `.claude/templates/` | present | absent | — |
| `.claude/settings.json` | present | absent | — |
| No unexpected top-level dirs in `.claude/` | clean | unknown dirs | — |

**Fail threshold:** any of the first 4 items absent → P1 = 🚫

---

## P2 — CLAUDE.md Accuracy

| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Agent count matches `ls .claude/agents/*.md` | exact | ±1 | >±1 or not stated |
| Skill count matches `find .claude/skills -name SKILL.md \| wc -l` | exact | — | any discrepancy |
| Routing table covers all `context: fork` skills | all covered | 1–2 missing | ≥3 missing |
| No routing table row references a non-existent skill | all resolve | — | any broken ref |
| Structure section lists all real dirs in `.claude/` | complete | 1 dir missing | ≥2 missing |
| Command counts in table match skill count per agent | exact | — | any mismatch |

**Fail threshold:** skill count discrepancy OR broken routing row → P2 = 🚫

---

## P3 — Frontmatter Correctness

### Agents (`.claude/agents/*.md`)

| Field | Required | Valid values |
|-------|----------|-------------|
| `name` | Yes | kebab-case, ≤ 64 chars, matches filename |
| `description` | Yes | non-empty, "Use when…" trigger present, ≤ 1536 chars |
| `tools` | Yes | comma-separated list from allowed tool names |
| `model` | Optional | `opus`, `sonnet`, `haiku`, `fable`, `inherit`, or versioned ID |

Grading:
- ✅ Pass — all required fields present and valid for every agent
- ⚠️ Warn — 1 agent has optional field issues or soft limit violations
- 🚫 Fail — any agent missing `name`, `description`, or `tools`; or uses `allowed-tools:` instead of `tools:`

### Skills (`.claude/skills/*/SKILL.md`)

| Field | Required | Valid values |
|-------|----------|-------------|
| `name` | Yes | kebab-case, matches folder name |
| `description` | Yes | non-empty, "Use when…" trigger, ≤ 1536 chars |
| `context` | Command skills | must be `fork` |
| `agent` | Command skills | must match an existing agent name |
| `disable-model-invocation` | Command skills | must be `true` |
| `allowed-tools` | Optional | use `allowed-tools:`, never `tools:` |

Grading:
- ✅ Pass — all required fields present and valid
- ⚠️ Warn — non-critical issues (missing `argument-hint`, description lacks trigger)
- 🚫 Fail — `name` mismatch, missing required field for command skill, `tools:` used instead of `allowed-tools:`

---

## P4 — Router Consistency

| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Every `context: fork` skill has `agent:` | all present | — | any missing |
| Every `agent: X` resolves to `.claude/agents/X.md` | all resolve | — | any broken |
| Every `disable-model-invocation: true` has `context: fork` | all paired | — | any unpaired |
| Agent description mentions routed commands | all listed | some missing | — |
| No orphan `context: fork` without agent target | clean | — | any orphan |

**Fail threshold:** any broken `agent:` reference or orphan `context: fork` → P4 = 🚫

---

## P5 — Naming Conventions

| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Skill folder names are kebab-case | all kebab | — | any violation |
| Agent file basenames are kebab-case | all kebab | — | any violation |
| Skill `name:` field = folder name | all match | — | any mismatch |
| Agent `name:` field = file basename (no `.md`) | all match | — | any mismatch |
| Skill names use gerund-noun pattern (preferred) | all/most | some not | — |
| Agent names use domain-role pattern (preferred) | all/most | some not | — |
| No uppercase, no underscores, no spaces in names | clean | — | any violation |

**Fail threshold:** name/folder mismatch for any artifact → P5 = 🚫 (others are ⚠️ Warn)

---

## P6 — Progressive Disclosure

| Check | Pass | Warn | Fail |
|-------|------|------|------|
| All SKILL.md files ≤ 500 lines | all ≤ 500 | 1–2 > 500 | ≥3 > 500 |
| Skills > 300 lines have a `blueprints/` dir | all do | 1 missing | ≥2 missing |
| No eager `@file` imports for large files (> 100 lines) | none | — | any present |
| Blueprint filenames are descriptive | all descriptive | — | — |

**Fail threshold:** P6 does not auto-fail; ≥3 overlong skills without blueprints = 🚫

---

## P7 — Rule Coverage

| Check | Pass | Warn | Fail |
|-------|------|------|------|
| `.claude/rules/` contains ≥ 1 file | ≥ 1 file | — | 0 files |
| A rule file covers frontmatter conventions | present | — | absent |
| Rule files reference active skills/agents they govern | linked | some missing | — |
| Rule file last modified ≤ 12 months ago (git log) | recent | 6–12 months | > 12 months |

**Fail threshold:** 0 rule files → P7 = 🚫

---

## Severity Mapping

| Grade | Threshold | Recommended action |
|-------|-----------|-------------------|
| ✅ Pass | 0 issues | No action required |
| ⚠️ Warn | ≥ 1 soft issue | Fix before next major release |
| 🚫 Fail | ≥ 1 hard issue | Block ship / fix immediately |

Overall project grade = lowest single-dimension grade.
