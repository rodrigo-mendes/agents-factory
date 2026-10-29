# Findings register

Written only by `scripts/state_event.py <slug> finding ...`. One ID per finding (F-001...), kept
across rounds and carried to the next execution while OPEN, REOPENED or DEFERRED. The latest row of
an ID is its status. A finding REOPENED twice is not sent to another fix round: ask the user.

| Timestamp | ID | Status | Severity | Round | Target | Actor | Text |
|---|---|---|---|---|---|---|---|
