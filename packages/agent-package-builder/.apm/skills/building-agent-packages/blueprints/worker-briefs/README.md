# Worker briefs

Back to [SKILL.md](../../SKILL.md). Prompt templates the orchestrator sends to the existing subagents. Fill `<...>`; never drop the "Hard constraints" block.

**Why not slash commands:** worker skills (`researching-*`, `skill-creator`, validators) have `context: fork` + `disable-model-invocation: true`; the model cannot invoke them. Launch the subagent (`framework-researcher`, `artifact-author`, `quality-validator`, `skill-evaluator`, `architecture-auditor`) with the Agent tool and tell it to follow that worker's `SKILL.md` as its spec.

## Hard constraints (paste in every brief)

- Do NOT spawn any agent, section-investigator or background task; fetch pages yourself.
- Do NOT enter plan mode and do not wait for a P3 gate: the user approved this scope in this session (see Approval line); it is not a new approval and you must not treat it as one from yourself.
- Write only the files named under "Output". Report the paths and anything you could not verify.
- Apply `<workspace>/_family_facts.md` and `_family_rules.md` as given; do not edit them.
- Lessons from earlier batches (retro `brief` rows): <paste them verbatim, or "none yet">.
- Do not edit shared files (root `apm.yml`, lock, `CLAUDE.md`, `docs/`, other packages); return a request instead.

## Approval line (exact form)

`The user approved <scope> on <date> (verbatim: "<quote>"); recorded in <workspace>/execution-<N>/state/gates/<G>.md. This is a relay, not a new approval.`

If a worker still refuses: stop and ask the user again. Never reword the line to sound stronger.

Briefs: [researcher](researcher.md) · [skill-author-hybrid](skill-author-hybrid.md) · [package-author](package-author.md) · [validator](validator.md) · [fix-cycle](fix-cycle.md)
