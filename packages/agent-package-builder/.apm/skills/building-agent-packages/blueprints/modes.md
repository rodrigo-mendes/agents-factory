# Entry modes and state inspection

Back to [SKILL.md](../SKILL.md). One skill, three entries, same phases.

| Mode | Input | Enters at |
|---|---|---|
| `new` | brief with frameworks and/or needs | P0 |
| `from-research` | `research_dir=<dir>` | INSPECT -> P2 -> G1 -> P3/P4 (authoring only) |
| `resume` | `resume=<dir>` | first unfinished step |

Detect by input type; if unclear, ask. Splitting into separate skills is not worth it unless a mode grows more than ~3 exclusive steps.

## INSPECT (with or without PIPELINE_STATE.md)

Run `python3 scripts/inspect_workspace.py <workspace_dir> [--packages packages]`. It is read-only and reports, from disk: research files (COMPLETE/PARTIAL), family files, skills (OK/INCOMPLETE/CORRUPT/UNCHECKED), validation rounds, recorded phase. The disk always wins over the state file.

Then add git: `git log --oneline -15` and `git status --short` to see what is committed or pending.

| Unit finding | Meaning | Action |
|---|---|---|
| research COMPLETE, skill OK | done | keep |
| research COMPLETE, skill missing/INCOMPLETE | authoring pending/interrupted | re-author that unit only |
| research PARTIAL | interrupted research | discard and redo the research |
| skill dir without SKILL.md | CORRUPT | delete the folder content and redo |
| state says ready, disk says no | the state lied | disk wins; log the discrepancy |

Write the reconstructed state to `PIPELINE_STATE.md` with `reconstructed: true`; approvals not recorded there are asked again.

## from-research

1. INSPECT the dir. Research older than 12 months (factory source rule) or PARTIAL is listed as "redo research", not authored.
2. Propose units, names, mapping research -> skill, package layout, gaps. Missing family facts are derived from the research and verified against official pages.
3. **G1** before generating anything. Then P3 pilot (G2 is lighter: format and cost) and P4 in authoring-only batches.

## resume

Show the table "recorded x real x action", name the interruption point (e.g. "P4, batch 2, units X and Y"), ask for a short confirmation, continue from the first unfinished step. A half-written file is discarded and redone, never patched. Mechanically verified work is never redone.
