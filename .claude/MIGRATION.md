# Migration GitHub Copilot → Claude Code — Notes & Decommission

Status: **`.claude/` created alongside `.github/` (coexistence)**. Copilot remains functional;
decommission is a final phase, executed **only after validation in real use**.

## What was migrated

| Item | Result |
|---|---|
| `CLAUDE.md` (root) | new — principles, conventions, routing table, dual-target |
| Subagents | 4 real ones in `.claude/agents/` (framework-researcher, skill-author, architecture-auditor, quality-validator) |
| Operational prompts | 23 → `.claude/skills/<n>/SKILL.md` (`context: fork` + `agent:` + `disable-model-invocation: true`) |
| Meta-skills | 2 → `.claude/skills/` (wording neutralized) |
| Rules | `skill-frontmatter` (active, `paths:`) + instructions templates → `templates/rules/` |
| Templates/examples | Claude Code variants (tools translated, `applyTo:`→`paths:`, `.agent.md`/`.instructions.md`→`.md`) |
| settings/gitignore | `.claude/settings.json` (permissions) + `.gitignore` (local files, `StoryBeat/`) |

## Improvements applied
1. **4 real subagents** with least-privilege and "Use when…" trigger (did not exist before).
2. **WebSearch/WebFetch** in `framework-researcher` → real anti-hallucination (previously depended on the user pasting docs).
3. **Multi-model audit as native parallel orchestration**: `architecture-auditor` receives the `Agent` tool
   and fires scope/flow/engine in parallel, synthesizing consensus (previously was just text instruction).
4. **`disable-model-invocation: true`** on the 23 commands → auto-listing cost ~zero; only the 2 meta-skills are auto-invocable.
5. **Frontmatter fixed** on ~10 prompts that lacked valid `name`/`description`.

## Phase 2 — cleanup & progressive disclosure (done)
- **Progressive disclosure** applied to the 6 skills > 500 lines (content moved verbatim to `blueprints/`,
  SKILL.md with summary + link at point of use):
  | Skill | Before → after | Blueprints |
  |---|---|---|
  | `technical-framework-researcher-terraform` | 1051 → 434 | 7 |
  | `terraform-engineering-best-practices-researcher` | 766 → 189 | 5 |
  | `cloud-architecture-researcher` | 610 → 198 | 2 |
  | `audit-architecture-scope` | 605 → 336 | 2 |
  | `terraform-instructions-compiler` | 599 → 247 | 2 |
  | `architecture-approaches-skill-generator` | 587 → 309 | 1 |
  All < 500 lines; 0 broken links; frontmatter unchanged.
- **`examples/` removed** from both trees (`.claude/templates/`, `.github/templates/`) — 71% of the tree,
  OCI/Terraform hardcoded. READMEs now point to live artifacts (`.claude/agents/`, `.claude/skills/`).
- **Technology-agnostic banner** added to the 26 `TEMPLATE.*` files (13 in each tree).

## Validation by dogfooding (done)
Ran the factory's own validators/auditor against `.claude/`:
- **architecture-auditor** (scope+flow+engine consensus): **PASS 9.4/10**, 0 P0/P1. All counts confirmed
  (4 subagents, 25 skills, 23 commands, 0 broken `agent:` refs, 0 orphans).
- **quality-validator** (skill-best-practices + agent-router): 0 P0. The 8 P1s pointed to **Copilot residue in the body**
  of the audit/validation skills (runtime instructions reading `.github/agents/*.agent.md`,
  `.github/copilot-instructions.md`, `*.prompt.md`, `.github/instructions/`). **Fixed**: they now point to
  `.claude/agents/*.md`, `CLAUDE.md`, `.claude/skills/*/SKILL.md`, `.claude/rules/` (validators/compiler kept
  dual-target). Also: `skill-author` gained `model: sonnet`; Copilot example links in skill-creator/
  authoring-agent-skills/researching-technical-frameworks fixed to `.claude/rules|skills`.

## Optional follow-ups (non-blocking)
- **Copilot conceptual vocabulary** still present in the audit rubrics (labels "Layer L0–L4", `.agent.md`
  in criterion tables, `report-template.md`) — this is the conceptual model, not runtime paths; rewriting
  to Claude Code vocabulary is doc-only (R1).
- **Typo** `architecture-approaches-skill-generator` → renaming changes the `/...` command name; decide separately.
- **Prompt variables** (`{{VAR}}`, INPUT VARIABLES sections) were preserved; the subagent collects them.
  Where a single argument makes sense, use `$ARGUMENTS`/`$1`.

## Verification already done (structural)
`scratchpad/verify.py`: 4 agents · 21 skills · 1 rule · 0 broken refs · 0 `runSubagent`/`list_dir` ·
`name`=folder in all · `agent:` points to existing subagent · YAML without unquoted `:`.

## Pending functional verification (interactive, in Claude Code)
- `/memory` → confirm that `CLAUDE.md` loads.
- `/technical-framework-researcher <tech> <version>` → runs via `framework-researcher`, uses WebFetch.
- `/skill-creator` → runs via `skill-author`.
- `/audit-architecture-consensus <target>` → fires the 3 subagents in parallel.
- `/skill-best-practices-validator .claude/skills/` → quality report.

## Copilot Decommission (FINAL phase — DO NOT execute now)
Run as its own PR, after the team validates `.claude/` in real use:
1. Remove `.github/prompts/`, `.github/skills/` (and `.github/agents/` if it exists).
2. Adjust `README.md` and `docs/adopcion/` (Copilot program) to reflect Claude-Code-only, or archive them.
3. **Keep** `.github/workflows/` (CI) and anything unrelated to Copilot.
4. Remove the `ask: Write(./.github/**)` line from `.claude/settings.json` (there will be nothing left to protect).
5. Run `scratchpad/verify.py` again and confirm counts.
