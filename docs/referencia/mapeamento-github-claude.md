# Mapping .github/ ↔ .claude/

Equivalence table between GitHub Copilot (`.github/`) artifacts and Claude Code (`.claude/`) artifacts.

The project operates in a **coexistence mode**: `.github/` and `.claude/` coexist in the repository, each
serving its respective runtime. Both implement the same set of operational capabilities with
each platform's native artifacts.

---

## Copilot Prompts → Claude Code Skills

| # | Copilot Prompt (`.github/prompts/`) | Claude Code Skill (`.claude/skills/`) | Category | Status |
|:-:|-------------------------------------|---------------------------------------|-----------|--------|
| 1 | `technical-framework-researcher.prompt.md` | `researching-technical-frameworks/SKILL.md` | Research | ✅ Equivalent |
| 2 | `technical-framework-researcher-terraform.prompt.md` | `technical-framework-researcher-terraform/SKILL.md` | Research | ✅ Equivalent |
| 3 | `terraform-engineering-best-practices-researcher.prompt.md` | `terraform-engineering-best-practices-researcher/SKILL.md` | Research | ✅ Equivalent |
| 4 | `architecture-methodology-researcher.prompt.md` | `architecture-methodology-researcher/SKILL.md` | Research | ✅ Equivalent |
| 5 | `cloud-architecture-researcher.prompt.md` | `cloud-architecture-researcher/SKILL.md` | Research | ✅ Equivalent |
| 6 | `business-domain-researcher.prompt.md` | `business-domain-researcher/SKILL.md` | Research | ✅ Equivalent |
| 7 | `requirements-methodology-researcher.prompt.md` | `requirements-methodology-researcher/SKILL.md` | Research | ✅ Equivalent |
| 8 | `skill-creator.prompt.md` | `skill-creator/SKILL.md` | Compilation | ✅ Equivalent |
| 9 | `terraform-instructions-compiler.prompt.md` | `terraform-instructions-compiler/SKILL.md` | Compilation | ✅ Equivalent |
| 10 | `archtecture-approches-skill-generator.prompt.md` ⚠️ | `architecture-approaches-skill-generator/SKILL.md` | Compilation | ✅ Equivalent (typo no filename Copilot) |
| 11 | `methodologies-skill-generator.prompt.md` | `methodologies-skill-generator/SKILL.md` | Compilation | ✅ Equivalent |
| 12 | `copilot-compatibility-review.prompt.md` | `copilot-compatibility-review/SKILL.md` | Validation | ✅ Equivalent |
| 13 | `instructions-best-practices-validator.prompt.md` | `instructions-best-practices-validator/SKILL.md` | Validation | ✅ Equivalent |
| 14 | `skill-best-practices-validator.prompt.md` | `skill-best-practices-validator/SKILL.md` | Validation | ✅ Equivalent |
| 15 | `project-quality-improvements.md` ⚠️ | `project-analysis-validator/SKILL.md` | Validation | ⚠️ Renamed and scope expanded in CC |
| 16 | `agent-router-pattern-validator.prompt.md` | `agent-router-pattern-validator/SKILL.md` | Validation | ✅ Equivalent |
| 17 | `audit-architecture-consensus.prompt.md` | `audit-architecture-consensus/SKILL.md` | Copilot Audit | ✅ Equivalent |
| 18 | `audit-architecture-scope.prompt.md` | `audit-architecture-scope/SKILL.md` | Copilot Audit | ✅ Equivalent |
| 19 | `audit-architecture-flow.prompt.md` | `audit-architecture-flow/SKILL.md` | Copilot Audit | ✅ Equivalent |
| 20 | `audit-architecture-engine.prompt.md` | `audit-architecture-engine/SKILL.md` | Copilot Audit | ✅ Equivalent |

---

## Claude Code-Exclusive Capabilities

The following skills exist only in `.claude/` — they have no Copilot equivalent because they specifically audit Claude Code project architecture.

| Claude Code Skill | Category | Justification |
|-------------------|-----------|---------------|
| `audit-cc-architecture-consensus/SKILL.md` | CC Audit | Audits `.claude/` — does not exist in Copilot |
| `audit-cc-architecture-scope/SKILL.md` | CC Audit | Audits `.claude/` — does not exist in Copilot |
| `audit-cc-architecture-flow/SKILL.md` | CC Audit | Audits `.claude/` — does not exist in Copilot |
| `audit-cc-architecture-engine/SKILL.md` | CC Audit | Audits `.claude/` — does not exist in Copilot |
| `evaluating-skill-scenarios/SKILL.md` | Evaluation | LLM-as-judge for skills — Claude Code-specific pattern |

---

## Meta-Skills (present in both systems)

| Meta-Skill | Copilot | Claude Code |
|------------|---------|-------------|
| `authoring-agent-skills` | `.github/skills/authoring-agent-skills/SKILL.md` | *(integrated into `skill-creator`)* |
| `researching-technical-frameworks` | `.github/skills/researching-technical-frameworks/SKILL.md` | `.claude/skills/researching-technical-frameworks/SKILL.md` |

> **Divergence**: In Claude Code, the authoring standards from `authoring-agent-skills` were
> incorporated directly into `skill-creator`, eliminating the indirection. Copilot keeps the two
> skills separate.

---

## Templates (mirror .github/ ↔ .claude/)

| Type | Copilot (`.github/templates/`) | Claude Code (`.claude/templates/`) |
|------|-------------------------------|-------------------------------------|
| Agent | `agents/TEMPLATE.AGENT.md` | `agents/TEMPLATE.AGENT.md` |
| Agent | `agents/TEMPLATE.ADVISORY-AGENT.md` | `agents/TEMPLATE.ADVISORY-AGENT.md` |
| Agent | `agents/TEMPLATE.ORCHESTRATOR-AGENT.md` | `agents/TEMPLATE.ORCHESTRATOR-AGENT.md` |
| Prompt | `prompts/TEMPLATE.RESEARCH.prompt.md` | `prompts/TEMPLATE.RESEARCH.prompt.md` |
| Prompt | `prompts/TEMPLATE.GENERATOR.prompt.md` | `prompts/TEMPLATE.GENERATOR.prompt.md` |
| Prompt | `prompts/TEMPLATE.VALIDATION.prompt.md` | `prompts/TEMPLATE.VALIDATION.prompt.md` |
| Prompt | `prompts/TEMPLATE.ENTRY-POINT.prompt.md` | `prompts/TEMPLATE.ENTRY-POINT.prompt.md` |
| Prompt | `prompts/TEMPLATE.FEATURE-ADD.prompt.md` | `prompts/TEMPLATE.FEATURE-ADD.prompt.md` |
| Prompt | `prompts/TEMPLATE.DESIGN.prompt.md` | `prompts/TEMPLATE.DESIGN.prompt.md` |
| Skill | `skills/TEMPLATE.SKILL.md` | `skills/TEMPLATE.SKILL.md` |
| Instruction/Rule | `instructions/TEMPLATE.CONFIG.instructions.md` | `rules/TEMPLATE.CONFIG.md` |
| Instruction/Rule | `instructions/TEMPLATE.STANDARDS.instructions.md` | `rules/TEMPLATE.STANDARDS.md` |
| Instruction/Rule | `instructions/TEMPLATE.SKILLS.instructions.md` | `rules/TEMPLATE.SKILLS.md` |
| Report | `reports/POST_MORTEM_TEMPLATE.md` | `reports/POST_MORTEM_TEMPLATE.md` |

> **Structural difference**: `.github/` uses `instructions/` (`.instructions.md` format); `.claude/`
> uses `rules/` (simple `.md` format with `paths:` field in frontmatter).

---

## Known Anomalies in .github/

| File | Issue |
|---------|----------|
| `archtecture-approches-skill-generator.prompt.md` | Typo in filename — missing `i` in `architecture` and `c` in `approaches` |
| `project-quality-improvements.md` | Incorrect extension — missing `.prompt` before `.md`; content was renamed and expanded to `project-analysis-validator` in Claude Code |

---

## Count Summary

| System | Operational Prompts/Skills | Meta-skills | Agents | Templates | Rules/Instructions |
|---------|:--:|:--:|:--:|:--:|:--:|
| `.github/` (Copilot) | 20 | 2 | 0 | 15 | 0 |
| `.claude/` (Claude Code) | 25 | 1 | 5 | 14 | 1 |

> `.github/` has 15 templates (includes `README.md`); `.claude/` has 14 (without internal README).
