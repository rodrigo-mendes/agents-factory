# Metrics (cost estimated vs actual)

Written only by `scripts/state_event.py <slug> metric ...`. The P3 pilot writes the estimate per
unit and for the whole run; every stage writes its actual. `check_state.py` compares the actual sum
with `token_budget` of `PACKAGE_BRIEF.md`.

| Timestamp | Scope | Kind | Tokens | Minutes | Actor | Note |
|---|---|---|---|---|---|---|
| 2026-10-31T23:41:29 | pilot-research | actual | 137238 | 4 | orchestrator |  |
| 2026-11-01T00:09:09 | pilot-author | actual | 153552 | 3 | orchestrator |  |
| 2026-11-01T00:11:14 | pilot-validate | actual | 100000 |  | orchestrator | approx |
| 2026-11-01T00:11:15 | run | estimate | 3300000 |  | orchestrator | pilot 0.4M + U2/U3 0.8M + P5 0.4M + P6 3 rounds ~1.2M + fixes 0.5M |
| 2026-11-01T00:18:05 | P4-research | actual | 270302 | 5 | orchestrator |  |
| 2026-11-01T00:22:17 | testing-quarkus-integration-v3-40 | actual | 131361 | 3 | orchestrator |  |
| 2026-11-01T00:24:36 | deriving-gherkin-from-openspec-v1-15 | actual | 150834 | 5 | orchestrator |  |
| 2026-11-01T00:30:09 | P5 | actual | 216779 | 3 | orchestrator |  |
| 2026-11-01T00:36:41 | round-1 | actual | 1004000 |  | orchestrator | 4 reviewers ~520k + 4 fixes ~385k |
| 2026-11-01T00:39:27 | round-2 | actual | 268879 |  | orchestrator |  |
| 2026-11-01T00:41:32 | round-2-audit | actual | 118006 |  | orchestrator |  |
