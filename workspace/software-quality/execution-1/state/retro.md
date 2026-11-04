# Retro (lessons that change the next batch or the next run)

Written only by `scripts/state_event.py <slug> retro ...`. Kinds:
- `brief`: pasted into every later worker brief of this run (e.g. "3rd time an author stated an
  inferred claim as High").
- `known-failure`: proposed new row for `blueprints/known-failures.md` (applied in a separate change).
- `lesson`: anything else worth reading before the next run of this slug.

| Timestamp | ID | Kind | Target | Actor | Text |
|---|---|---|---|---|---|
| 2026-11-01T00:12:48 | R-001 | brief | author | orchestrator | Every Version Context row cites the page that states it (not a neighbour fact); Never Do alternatives must be High confidence (put spike-only patterns second); plugin versions need a URL or (medium co |
| 2026-11-03T12:34:35 | R-002 | known-failure | P8 | orchestrator | Windows LongPathsEnabled=0: apm cannot replace apm_modules/vercel (WinError 145); delete apm_modules with rd /s /q \?\path; agent-browser checkout fails with 'local changes' -> lock not written |
| 2026-11-03T12:34:35 | R-003 | lesson | P6 | orchestrator | Record package scores with target 'package' (0-100), never per package name, or the dashboard counts them as skills |
