# Audit (consensus: scope, flow, engine applied in sequence) - packages/quality/ - round 2

Score: **9.3/10** (0 HIGH, 1 MEDIUM, 1 LOW). No agents spawned, no plan mode (brief P6-r2-common). Source only (packages/quality/**).

## Round-1 findings
| ID | Status | Evidence |
|---|---|---|
| MEDIUM-S1 IT-fact overlap with junit skill | Resolved | testing-quarkus-integration-v3-40/SKILL.md:40-42 "Scope split: test types, profiles basics: `developing-quarkus-junit-v3-40`..." and :47 "test types and profile basics are in `developing-quarkus-junit-v3-40`" |
| MEDIUM-F1 engineer coverage command implicit | Resolved | acceptance-test-engineer.agent.md:57 full command with `--spec-root ... --features ... [--change <id>] --strict` |
| LOW-F2 reviewer launch path undocumented | Resolved (adequate) | acceptance-testing/README.md:42-43 "launch `acceptance-test-reviewer` with a change id or spec root plus the features directory"; command SKILL.md:32 "which you run" |
| LOW-E2 tag wording mismatch | Resolved | Both rules now say "Tag every scenario (directly or through Rule/Feature inheritance) with `@R<n>` or `@req-<slug>`" (gherkin rule :17, quarkus rule :30) |
| LOW-E3 @change mandatory on spec root | Resolved | gherkin rule :17 "Add `@change-<id>` only when generating from a change delta ... for a spec root no change tag"; same in quarkus rule :30, reviewer :51 ("a delta feature without `@change`"), deriving SKILL.md:58,96, mapping-and-deltas.md:18,25, always-do-patterns.md:20, cucumber SKILL.md:59 + always-do-patterns.md:33, README:21 |
| LOW-E1 Bash allow-list prompt-only | Open, accepted | reviewer.agent.md:34 states the residual risk explicitly |

## Scope (G0-G4)
Layering unchanged and correct: generic `acceptance-testing` <- stack `quarkus-acceptance-testing`; no cycle. Boundary with `quarkus-core` junit skill now explicit. No new leakage.

## Flow (FCC)
`/building-acceptance-tests` (fork -> acceptance-test-engineer) -> 3 skills -> coverage script (exact args) -> mvn verify -> report -> user/caller runs reviewer. Complete, acyclic, no spawning. No new issue.

## Engine (ECC) - @change conditional consistency check
Rules, reviewer, engineer (defers "Tag scenarios per the skills", :91), deriving skill + blueprints, cucumber skill + always-do, README all agree on the conditional `@change-<id>`. The coverage script does not check `@change` (only `--change` selects the delta), so enforcement is via reviewer HIGH, consistent with the rule. One straggler:

- **MEDIUM-N1** `quarkus-acceptance-testing/.apm/skills/testing-quarkus-cucumber-v8-0/blueprints/evaluation-scenarios.md:13` - Scenario 1 query ("Add Cucumber acceptance tests to my Quarkus 3.40 REST app. It exposes POST /items.") names no change, yet Expected says "scenarios tagged `@R<n>` and `@change-<id>`". An LLM-as-judge (skill-evaluator) would penalise the now-correct behaviour of omitting the change tag. Fix: "scenarios tagged `@R<n>` (plus `@change-<id>` on the Feature only for a change delta)", mirroring deriving evaluation-scenarios.md:11 ("when a change id is known").
- **LOW-E1** (carried, accepted) reviewer Bash allow-list is prompt-only; optional PreToolUse hook like static-site-verifier.

Minor note (not scored): steps-and-state.md:98 lists `@change-add-items` as an example tag; it is an example, not a rule - fine.

## Consensus matrix
| Finding | Scope | Flow | Engine | Sev |
|---|---|---|---|---|
| Cucumber eval scenario 1 expects @change without a change | | x | x | MEDIUM |
| Reviewer Bash allow-list prompt-only | | | x | LOW |

## Remediation
1. Edit testing-quarkus-cucumber-v8-0/blueprints/evaluation-scenarios.md:13 to make `@change-<id>` conditional.
2. (Optional) PreToolUse hook for acceptance-test-reviewer Bash.
