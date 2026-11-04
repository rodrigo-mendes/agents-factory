# Unit deriving-gherkin-from-openspec-v1-15

Written only by `scripts/state_event.py unit deriving-gherkin-from-openspec-v1-15 <STATE>`. Append-only history; the last row is
the current state. Machine: `PLANNED -> RESEARCHED -> AUTHORED -> VERIFIED -> VALIDATED`
(side states `DEFERRED`, `DROPPED`). Going backwards needs `--note` with the reason.

| Timestamp | State | Score | Tokens | Actor | Note |
|---|---|---|---|---|---|
| 2026-10-31T23:13:22 | PLANNED |  |  | orchestrator |  |
| 2026-11-01T00:17:39 | RESEARCHED |  |  | orchestrator |  |
| 2026-11-01T00:18:05 | RESEARCHED |  | 135333 | orchestrator | tokens |
| 2026-11-01T00:24:36 | VERIFIED |  | 150834 | orchestrator | 10 unittests OK; --strict tested with gherkin-official 42.0.1 |
| 2026-11-01T00:39:27 | VALIDATED | 97 |  | orchestrator |  |
