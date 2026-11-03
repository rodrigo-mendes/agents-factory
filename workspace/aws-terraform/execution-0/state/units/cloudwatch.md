# Unit cloudwatch

Written only by `scripts/state_event.py unit cloudwatch <STATE>`. Append-only history; the last row is
the current state. Machine: `PLANNED -> RESEARCHED -> AUTHORED -> VERIFIED -> VALIDATED`
(side states `DEFERRED`, `DROPPED`). Going backwards needs `--note` with the reason.

| Timestamp | State | Score | Tokens | Actor | Note |
|---|---|---|---|---|---|
| 2026-10-29T21:05:47 | VALIDATED |  |  | migrate_state | reconstructed; legacy state cell: VALIDATED (evaluator 4/4, 24/24); fixed undefined `security_alerts` topic + rewo |
