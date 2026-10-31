# P0 Intake

Back to [SKILL.md](../../SKILL.md).

**Inputs:** a brief (frameworks and/or needs), a `research_dir`, or a `resume` directory (see [modes](../modes.md)).

1. Detect the mode; ask if ambiguous.
2. Preflight: `ls .claude/agents` must contain framework-researcher, artifact-author, quality-validator, skill-evaluator, architecture-auditor; `ls .claude/skills` must contain the research worker named in the brief, skill-creator, agent-creator. Missing -> stop with the list; do not improvise.
3. `python3 scripts/state_event.py workspace/<slug> init` (creates `execution-<N>`, `LATEST`, and copies the brief and family templates when absent), then `state_event.py workspace/<slug> lock`, then start the dashboard watcher in the background: `python3 scripts/watch_state.py workspace/<slug>` (re-renders `PIPELINE_STATE.md` every 5 min; exits by itself after the P9 unlock). Fill `PACKAGE_BRIEF.md`. Layout: [state layout](../state-layout.md).
3b. Rehearsal (minute 1, not hour 5): `scripts/snapshot_env.py --write workspace/<slug> --phase P0` (tools, encodings, autocrlf, whether `git init` works in the sandbox) and `scripts/preflight_apm.py --slug <slug>` (another live run, foreign files in `.claude/`, broken root `apm.yml`). A BLOCK is shown to the user now; a missing tool becomes `defer add` for the steps that need it, not a surprise later.
4. Reject early: brief without frameworks or needs; `rounds` not an integer; a slug that collides with an existing package.

**Done when:** `state_event.py ... phase P0 done` succeeded and `render_state.py` shows current phase P1. **Gate:** none.
