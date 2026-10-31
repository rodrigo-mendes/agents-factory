# Metrics (cost estimated vs actual)

Written only by `scripts/state_event.py <slug> metric ...`. The P3 pilot writes the estimate per
unit and for the whole run; every stage writes its actual. `check_state.py` compares the actual sum
with `token_budget` of `PACKAGE_BRIEF.md`.

| Timestamp | Scope | Kind | Tokens | Minutes | Actor | Note |
|---|---|---|---|---|---|---|
