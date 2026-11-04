# Unit testing-quarkus-cucumber-v8-0

Written only by `scripts/state_event.py unit testing-quarkus-cucumber-v8-0 <STATE>`. Append-only history; the last row is
the current state. Machine: `PLANNED -> RESEARCHED -> AUTHORED -> VERIFIED -> VALIDATED`
(side states `DEFERRED`, `DROPPED`). Going backwards needs `--note` with the reason.

| Timestamp | State | Score | Tokens | Actor | Note |
|---|---|---|---|---|---|
| 2026-10-31T23:13:21 | PLANNED |  |  | orchestrator |  |
| 2026-10-31T23:41:29 | RESEARCHED |  | 137238 | orchestrator |  |
| 2026-11-01T00:09:09 | VERIFIED |  | 153552 | orchestrator |  |
| 2026-11-01T00:39:26 | VALIDATED | 97 |  | orchestrator |  |
