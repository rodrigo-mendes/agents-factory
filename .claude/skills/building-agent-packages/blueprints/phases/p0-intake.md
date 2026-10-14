# P0 Intake

Back to [SKILL.md](../../SKILL.md).

**Inputs:** a brief (frameworks and/or needs), a `research_dir`, or a `resume` directory (see [modes](../modes.md)).

1. Detect the mode; ask if ambiguous.
2. Preflight: `ls .claude/agents` must contain framework-researcher, artifact-author, quality-validator, skill-evaluator, architecture-auditor; `ls .claude/skills` must contain the research worker named in the brief, skill-creator, agent-creator. Missing -> stop with the list; do not improvise.
3. Create `workspace/<slug>/`, copy `assets/PACKAGE_BRIEF.template.md` and `assets/PIPELINE_STATE.template.md`, fill them.
4. Reject early: brief without frameworks or needs; `rounds` not an integer; a slug that collides with an existing package.

**Done when:** state file exists with `current_phase: P1`. **Gate:** none.
