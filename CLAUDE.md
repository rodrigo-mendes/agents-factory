# Agents Factory — CLAUDE.md

AI artifact factory (**Skills, Prompts/Commands, Subagents, Rules**) with an
**anti-hallucination** focus. This repository **produces** artifacts for code agents and **also runs on
Claude Code**: operational prompts are exposed as skills/commands that fork to subagents.

> **Claude Code-first.** The factory documents adoption for **Claude Code** (see `docs/`).
> Config in `.github/` (Copilot) and `.claude/` (Claude Code) coexist — do not delete `.github/`.

## Principles (non-negotiable)

- **Version Absolutism** — 1 skill = 1 version; treat old versions as misinformation.
- **Source Hierarchy** — official doc/registry > official blog > official examples > verified
  community > reject the rest. Reject sources > 12 months old unless they are the current stable.
- **Executable Truth** — every claim links to a dated official source; without a source, mark as "unverified".
- **Workflow P0–P5** — Verify Docs → Analyze → Consult → Propose → Implement → Validate.
- **Three-Tier** — ✅ Always-Do · ⚠️ Ask-First · 🚫 Never-Do (with alternative).
- **Progressive disclosure** — `SKILL.md` lean (< 500 lines) linking blueprints; no giant inline content.

## Naming conventions (kebab-case)

| Artifact | Pattern | Example |
|---|---|---|
| Skill | `gerund-noun` | `researching-technical-frameworks` |
| Command/Prompt | `action-noun` | `cloud-architecture-researcher` |
| Subagent | `domain-role` | `framework-researcher` |
| Rule | `scope-noun` | `skill-frontmatter` |

## Routing — Skill (`/command`) → Subagent → Skills

Operational commands fork (`context: fork`) to a subagent. The 5 subagents live in
[.claude/agents/](.claude/agents/):

| Subagent | Does | Commands it routes |
|---|---|---|
| [framework-researcher](.claude/agents/framework-researcher.md) | anti-hallucination research (uses WebSearch/WebFetch) | `researching-technical-frameworks`, `technical-framework-researcher-terraform`, `cloud-architecture-researcher`, `business-domain-researcher`, `requirements-methodology-researcher`, `architecture-methodology-researcher`, `terraform-engineering-best-practices-researcher` |
| [skill-author](.claude/agents/skill-author.md) | generates SKILL.md / rules | `skill-creator`, `methodologies-skill-generator`, `architecture-approaches-skill-generator`, `terraform-instructions-compiler` |
| [architecture-auditor](.claude/agents/architecture-auditor.md) | audits architecture (consensus = 3 lenses in parallel via Agent tool) | `audit-architecture-scope`/`flow`/`engine`/`consensus` (Copilot target) · `audit-cc-architecture-scope`/`flow`/`engine`/`consensus` (Claude Code target) |
| [quality-validator](.claude/agents/quality-validator.md) | validates quality/adherence | `skill-best-practices-validator`, `instructions-best-practices-validator`, `agent-router-pattern-validator`, `copilot-compatibility-review`, `project-analysis-validator` |
| [skill-evaluator](.claude/agents/skill-evaluator.md) | evaluates skill behavior via LLM-as-judge (runs evaluation-scenarios.md and verifies real responses) | `evaluating-skill-scenarios` |

## How to run (no build step)

Not compiled code — artifacts run **in Claude Code** via `/<command>`:

- Search for a technology: `/researching-technical-frameworks <tech> <version>`
- Create a skill from a research file: `/skill-creator StoryBeat/research_X_v1.md`
- Create a methodology skill (all-in-one): `/methodologies-skill-generator <methodology>`
- Audit a Claude Code project (consensus): `/audit-cc-architecture-consensus <target>`
- Audit a GitHub Copilot project (consensus): `/audit-architecture-consensus <target>`
- Validate skill quality: `/skill-best-practices-validator .claude/skills/`
- Audit full project health: `/project-analysis-validator .claude/`
- Evaluate skill behavior: `/evaluating-skill-scenarios cloud-architecture-researcher`

The 25 commands use `disable-model-invocation: true` (deliberate actions) — accessible via `/name`,
with no auto-listing cost.

## Structure

```
.claude/
├── agents/     ← 5 subagents (framework-researcher, skill-author, architecture-auditor, quality-validator, skill-evaluator)
├── skills/     ← 25 operational commands (fork → subagent)
├── rules/      ← rules by path (paths:) + templates
├── templates/  ← scaffolding: agents/, skills/, rules/, prompts/, reports/
├── MIGRATION.md ← migration history Copilot → Claude Code
├── worktrees/  ← temporary Git worktrees (auto-generated; do not edit)
└── settings.json
docs/
├── capacidades/  ← skills/commands catalog
├── como-usar/    ← operational guides
├── fluxos/       ← flow diagrams
├── manual/       ← subagent reference manual
└── referencia/   ← glossary and conventions
StoryBeat/      ← agent-generated research outputs (untracked)
.github/        ← Copilot config (coexistence; do not delete)
```

## Gotchas

- **Frontmatter conventions** (field names, model values, YAML quoting): see
  [`.claude/rules/skill-frontmatter.md`](.claude/rules/skill-frontmatter.md).
- Do not trust audit counts — verify with `ls`/`wc`/`grep`.
