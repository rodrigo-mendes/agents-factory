# Unit federating-github-actions-oci

Written only by `scripts/state_event.py unit federating-github-actions-oci <STATE>`. Append-only history; the last row is
the current state. Machine: `PLANNED -> RESEARCHED -> AUTHORED -> VERIFIED -> VALIDATED`
(side states `DEFERRED`, `DROPPED`). Going backwards needs `--note` with the reason.

| Timestamp | State | Score | Tokens | Actor | Note |
|---|---|---|---|---|---|
| 2026-10-30T11:21:32 | RESEARCHED |  | 187112 | orchestrator | 781 lines; Path A consumption unverified; node20 risk |
| 2026-10-30T11:33:43 | AUTHORED |  | 162459 | orchestrator | 10 files |
| 2026-10-30T11:33:44 | VERIFIED |  |  | orchestrator | verify_skill exit 0 |
| 2026-10-30T12:50:44 | VALIDATED | 99.0 |  | orchestrator |  |
