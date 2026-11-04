# Unit secrets-manager

Written only by `scripts/state_event.py unit secrets-manager <STATE>`. Append-only history; the last row is
the current state. Machine: `PLANNED -> RESEARCHED -> AUTHORED -> VERIFIED -> VALIDATED`
(side states `DEFERRED`, `DROPPED`). Going backwards needs `--note` with the reason.

| Timestamp | State | Score | Tokens | Actor | Note |
|---|---|---|---|---|---|
| 2026-10-29T21:05:47 | VALIDATED |  |  | migrate_state | reconstructed; legacy state cell: VALIDATED round 2 (0 HIGH; N1–N4 MED fixed by orchestrator; LOW incl. L-1 exampl |
