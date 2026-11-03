# Scores (one row per review report)

Written only by `scripts/state_event.py <slug> score ...`, one row per validate/test/audit report of
the pilot (`--round pilot`) or a P6 round. The latest row of (round, target, kind) wins. The
dashboard and each round's `scoreboard.md` are generated from this file; never write a scoreboard
by hand. Skill and package scores use 0-100 (`100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW`); the audit uses 0-10.

| Timestamp | Round | Target | Kind | Score | HIGH | MEDIUM | LOW | Pass | Total | Actor | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-01T00:11:14 | pilot | testing-quarkus-cucumber-v8-0 | validate | 90 | 0 | 3 | 5 |  |  | orchestrator |  |
| 2026-11-01T00:32:22 | round-1 | acceptance-testing | validate | 9 | 0 | 1 | 2 |  |  | orchestrator |  |
| 2026-11-01T00:32:22 | round-1 | quarkus-acceptance-testing | validate | 8.5 | 0 | 1 | 3 |  |  | orchestrator |  |
| 2026-11-01T00:32:52 | round-1 | package | audit | 8.5 | 0 | 2 | 4 |  |  | orchestrator |  |
| 2026-11-01T00:33:19 | round-1 | testing-quarkus-cucumber-v8-0 | validate | 89 | 0 | 3 | 7 |  |  | orchestrator |  |
| 2026-11-01T00:33:19 | round-1 | testing-quarkus-integration-v3-40 | validate | 98.5 | 0 | 0 | 3 |  |  | orchestrator |  |
| 2026-11-01T00:33:20 | round-1 | deriving-gherkin-from-openspec-v1-15 | validate | 98 | 0 | 0 | 4 |  |  | orchestrator |  |
| 2026-11-01T00:33:37 | round-1 | skills | test | 100 | 0 | 1 | 6 | 23 | 23 | orchestrator |  |
| 2026-11-01T00:38:26 | round-2 | skills | test | 100 | 0 | 0 | 0 | 23 | 23 | orchestrator |  |
| 2026-11-01T00:39:21 | round-2 | testing-quarkus-cucumber-v8-0 | validate | 97 | 0 | 1 | 1 |  |  | orchestrator |  |
| 2026-11-01T00:39:22 | round-2 | testing-quarkus-integration-v3-40 | validate | 99.5 | 0 | 0 | 1 |  |  | orchestrator |  |
| 2026-11-01T00:39:22 | round-2 | deriving-gherkin-from-openspec-v1-15 | validate | 97 | 0 | 1 | 1 |  |  | orchestrator |  |
| 2026-11-01T00:39:23 | round-2 | acceptance-testing | validate | 9 | 0 | 0 | 2 |  |  | orchestrator |  |
| 2026-11-01T00:39:23 | round-2 | quarkus-acceptance-testing | validate | 9 | 0 | 1 | 1 |  |  | orchestrator |  |
| 2026-11-01T00:41:30 | round-2 | package | audit | 9.3 | 0 | 1 | 1 |  |  | orchestrator |  |
| 2026-11-01T00:59:43 | round-1 | package | validate | 85 | 0 | 2 | 5 |  |  | orchestrator | min of acceptance-testing 9.0 and quarkus-acceptance-testing 8.5 (x10) |
| 2026-11-01T00:59:44 | round-2 | package | validate | 90 | 0 | 1 | 3 |  |  | orchestrator | both packages 9/10 (x10) |
