# Unit <unit>

Written only by `scripts/state_event.py unit <unit> <STATE>`. Append-only history; the last row is
the current state. Machine: `PLANNED -> RESEARCHED -> AUTHORED -> VERIFIED -> VALIDATED`
(side states `DEFERRED`, `DROPPED`). Going backwards needs `--note` with the reason.

| Timestamp | State | Score | Tokens | Actor | Note |
|---|---|---|---|---|---|
