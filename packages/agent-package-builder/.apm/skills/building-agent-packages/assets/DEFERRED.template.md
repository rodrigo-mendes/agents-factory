# Deferred items

Written only by `scripts/state_event.py <slug> defer ...`. Anything left for later (a unit waiting
for a final release, a G3 leftover, a step moved to another run) gets an owner and a resume trigger.
Carried to the next execution while OPEN or RESUMED.

| Timestamp | ID | Status | Owner | Trigger | Actor | Text |
|---|---|---|---|---|---|---|
