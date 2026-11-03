# Findings register

Written only by `scripts/state_event.py <slug> finding ...`. One ID per finding (F-001...), kept
across rounds and carried to the next execution while OPEN, REOPENED or DEFERRED. The latest row of
an ID is its status. A finding REOPENED twice is not sent to another fix round: ask the user.

| Timestamp | ID | Status | Severity | Round | Target | Actor | Text |
|---|---|---|---|---|---|---|---|
| 2026-11-01T00:33:37 | F-001 | OPEN | MEDIUM | round-1 | testing-quarkus-cucumber-v8-0 | orchestrator | M1 Java range mis-cited SKILL.md:16, migration-guide.md:42 Max 21 |
| 2026-11-01T00:33:38 | F-002 | OPEN | MEDIUM | round-1 | testing-quarkus-cucumber-v8-0 | orchestrator | M2 Always/Never evidence: SKILL.md:51,59,60 cite wrong page; Never Do :77,:82 put B1 (medium) before B2 |
| 2026-11-01T00:33:39 | F-003 | OPEN | MEDIUM | round-1 | testing-quarkus-cucumber-v8-0 | orchestrator | M3 Failsafe block duplicated with integration skill (runner-patterns.md:55-67, SKILL.md:52-53) |
| 2026-11-01T00:33:39 | F-004 | OPEN | MEDIUM | round-1 | deriving-gherkin-from-openspec-v1-15 | orchestrator | Script: requirement with zero scenarios is gap but exit 0 (check_feature_coverage.py:253-255,307) |
| 2026-11-01T00:33:40 | F-005 | OPEN | MEDIUM | round-1 | quarkus-acceptance-testing | orchestrator | acceptance-test-engineer: coverage command not spelled out (needs --features, --change, --strict); prose-only path/commit limits undisclosed |
| 2026-11-01T00:33:40 | F-006 | OPEN | MEDIUM | round-1 | testing-quarkus-integration-v3-40 | orchestrator | Audit S1: repeats @QuarkusIntegrationTest profile/Failsafe facts from developing-quarkus-junit-v3-40; add boundary line |
| 2026-11-01T00:36:38 | F-001 | FIXED | MEDIUM | round-1 | testing-quarkus-cucumber-v8-0 | orchestrator | fix brief r1 |
| 2026-11-01T00:36:38 | F-002 | FIXED | MEDIUM | round-1 | testing-quarkus-cucumber-v8-0 | orchestrator | fix brief r1 |
| 2026-11-01T00:36:39 | F-003 | FIXED | MEDIUM | round-1 | testing-quarkus-cucumber-v8-0 | orchestrator | fix brief r1 |
| 2026-11-01T00:36:39 | F-004 | FIXED | MEDIUM | round-1 | deriving-gherkin-from-openspec-v1-15 | orchestrator | fix brief r1 |
| 2026-11-01T00:36:40 | F-005 | FIXED | MEDIUM | round-1 | quarkus-acceptance-testing | orchestrator | fix brief r1 |
| 2026-11-01T00:36:40 | F-006 | FIXED | MEDIUM | round-1 | testing-quarkus-integration-v3-40 | orchestrator | fix brief r1 |
| 2026-11-01T00:39:24 | F-007 | OPEN | MEDIUM | round-2 | family | orchestrator | @change-<id> conditional in rules but mandatory in skills (7 files) |
| 2026-11-01T00:39:25 | F-007 | FIXED | MEDIUM | round-2 | family | orchestrator | orchestrator mechanical edit, 8 occurrences |
| 2026-11-01T00:41:30 | F-008 | OPEN | MEDIUM | round-2 | testing-quarkus-cucumber-v8-0 | orchestrator | eval scenario 1 expects @change tag without a change |
| 2026-11-01T00:41:31 | F-008 | FIXED | MEDIUM | round-2 | testing-quarkus-cucumber-v8-0 | orchestrator | orchestrator one-line edit |
