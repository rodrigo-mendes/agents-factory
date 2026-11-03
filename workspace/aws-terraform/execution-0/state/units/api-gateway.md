# Unit api-gateway

Written only by `scripts/state_event.py unit api-gateway <STATE>`. Append-only history; the last row is
the current state. Machine: `PLANNED -> RESEARCHED -> AUTHORED -> VERIFIED -> VALIDATED`
(side states `DEFERRED`, `DROPPED`). Going backwards needs `--note` with the reason.

| Timestamp | State | Score | Tokens | Actor | Note |
|---|---|---|---|---|---|
| 2026-10-29T21:05:47 | VALIDATED |  |  | migrate_state | reconstructed; legacy state cell: VALIDATED round 2 (0 wrong facts; N-H1 date chain + N-M1/M2 + LOW fixed; L-9 API |
