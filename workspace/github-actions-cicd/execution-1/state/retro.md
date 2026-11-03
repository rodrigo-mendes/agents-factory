# Retro (lessons that change the next batch or the next run)

Written only by `scripts/state_event.py <slug> retro ...`. Kinds:
- `brief`: pasted into every later worker brief of this run (e.g. "3rd time an author stated an
  inferred claim as High").
- `known-failure`: proposed new row for `blueprints/known-failures.md` (applied in a separate change).
- `lesson`: anything else worth reading before the next run of this slug.

| Timestamp | ID | Kind | Target | Actor | Text |
|---|---|---|---|---|---|
| 2026-10-30T10:39:23 | R-001 | known-failure | p3-pilot.md | orchestrator | P3 playbook does not say where the pilot validate report goes; rounds/round-0 trips check_state (needs test+audit). Use execution-N/pilot/. |
| 2026-10-30T11:56:10 | R-002 | lesson | orchestrator | orchestrator | PIPELINE_STATE.md went stale from P3 to P5: render_state.py was not run at P4 done / P5 start. Chain render_state.py into every phase/gate/unit-batch command. |
| 2026-10-30T12:19:49 | R-003 | known-failure | p5-package-assembly.md | orchestrator | Full root apm install in P5 (Windows) deleted 459 committed .claude files and 6 vercel lock entries; scoped sandbox install at deep workspace path hit WinError 3 (MAX_PATH); fixed by scoped_install.py |
| 2026-10-30T12:56:22 | R-004 | lesson | orchestrator | orchestrator | Check every script exit code before chaining state writes: supply-chain was marked VERIFIED on a failing verify, and a fix was launched in the same command that printed BUDGET EXCEEDED |
| 2026-10-30T12:56:23 | R-005 | lesson | p6-quality-loop.md | orchestrator | Cross-skill contracts (block inputs, role/env names, required check) drifted in parallel authoring; fix canonical names as a family rule before fan-out, not after round 1 |
| 2026-10-30T12:56:24 | R-006 | brief | known-failures.md | orchestrator | Proposed known-failure: full root apm install on Windows exit 0 but deleted 459 committed .claude files and dropped vercel lock entries; recovery = git restore deleted .claude from HEAD + merge_lock.p |
| 2026-10-30T13:04:27 | R-007 | known-failure | state_event.py | orchestrator | .run.lock only stores pid/host/start; a second session in the same conversation inherits it and both write the run. Lock should carry a session id and refuse writes from another session |
