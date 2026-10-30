# Unit specifying-changes-with-openspec-v1-15

Written only by `scripts/state_event.py unit specifying-changes-with-openspec-v1-15 <STATE>`. Append-only history; the last row is
the current state. Machine: `PLANNED -> RESEARCHED -> AUTHORED -> VERIFIED -> VALIDATED`
(side states `DEFERRED`, `DROPPED`). Going backwards needs `--note` with the reason.

| Timestamp | State | Score | Tokens | Actor | Note |
|---|---|---|---|---|---|
| 2026-10-29T21:06:00 | AUTHORED |  |  | migrate_state | reconstructed; legacy state cell: AUTHORED |
