# Scores (one row per review report)

Written only by `scripts/state_event.py <slug> score ...`, one row per validate/test/audit report of
the pilot (`--round pilot`) or a P6 round. The latest row of (round, target, kind) wins. The
dashboard and each round's `scoreboard.md` are generated from this file; never write a scoreboard
by hand. Skill and package scores use 0-100 (`100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW`); the audit uses 0-10.

| Timestamp | Round | Target | Kind | Score | HIGH | MEDIUM | LOW | Pass | Total | Actor | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|
