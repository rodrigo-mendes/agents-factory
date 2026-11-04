# Audit (consensus: scope, flow, engine applied in sequence) - packages/quality/ - round 1

Score: **8.5/10** (0 HIGH, 2 MEDIUM, 4 LOW). No lens agents spawned; no plan mode (brief P6-r1-common).

## Scope (G0-G4)
- Layering is clean: generic package `acceptance-testing` (knowledge skill + script, `**/*.feature` rule, read-only reviewer) depends on `openspec-core`; stack package `quarkus-acceptance-testing` (2 knowledge skills, 1 fork command, 1 executor, 1 rule) depends on it and on `quarkus-core`. Dependency direction is correct (generic <- stack), no cycle.
- Overlap with `quarkus-core/developing-quarkus-junit-v3-40`: it already covers `@QuarkusIntegrationTest` profile and Surefire/Failsafe split (SKILL.md:51,61,91). `testing-quarkus-integration-v3-40` re-states Failsafe/IT facts. Rule `quarkus-acceptance-tests` routes "Test types, profiles, mocks" to the junit skill, which mitigates it. **MEDIUM-S1**: add an explicit "defer to developing-quarkus-junit-v3-40 for X" boundary line in testing-quarkus-integration-v3-40 SKILL.md, so two skills do not both claim `@QuarkusIntegrationTest` profile facts (drift risk).
- Overlap with `openspec-core`: none harmful; deriving skill reads spec format, does not redefine it (README out-of-scope line 28).

## Flow (FCC)
`/building-acceptance-tests` (context: fork, agent: acceptance-test-engineer, disable-model-invocation) -> engineer loads 3 skills -> runs `check_feature_coverage.py` -> mvn verify -> report -> "caller runs acceptance-test-reviewer". Chain complete and acyclic; engineer never spawns (Never Do), reviewer never spawns.
- **MEDIUM-F1** `quarkus-acceptance-testing/.apm/agents/acceptance-test-engineer.agent.md:52-53` "run ... with the arguments that skill documents" - the agent itself never names `--features`, which is `required=True` (script line 293). The skill documents it (SKILL.md:97), so it works, but the engineer P1 should state the exact command incl. `--change <id> --strict` when input is a change dir, like the reviewer does (reviewer.agent.md:44).
- **LOW-F2** reviewer handoff is user-mediated only ("Next step is acceptance-test-reviewer, which you run", building-acceptance-tests SKILL.md:33) and the reviewer has no `/command`; acceptable (README says orchestrator wiring deferred) but document how to launch it (README line 42 says "launch" without saying via Agent tool / which caller).

## Engine (ECC)
- Frontmatter: command has name/description/argument-hint/context: fork/agent/disable-model-invocation - correct. Knowledge skills have no fork - correct. Agents: tools lists match roles (reviewer no Write/Edit; engineer Edit/Write/Bash), `model: sonnet`.
- Rule globs: `applyTo` comma-list form matches other packages (aws-architect etc.), converted by APM - OK. Both rules match `src/test/resources/features/**` -> both load on feature edits; rules are consistent, low cost.
- Script paths `.claude/skills/deriving-gherkin-from-openspec-v1-15/scripts/...` used consistently in reviewer, rule, README; args match argparse (`--spec-root --change --features --json --strict`).
- **LOW-E1** reviewer Bash restriction is prompt-only (reviewer.agent.md:34 admits it). Consider a PreToolUse hook like static-site-verifier, or accept.
- **LOW-E2** tag placement wording differs: gherkin rule line 17 "Every Rule carries @R<n>", quarkus rule "Tag scenarios @R<n> and @change-<id>". Align wording (tags inherit, so not a defect).
- **LOW-E3** gherkin rule line 17 makes `@change-<id>` mandatory on every Feature, but the command also accepts a spec root (no change). State what tag applies when deriving from a spec root, or make it conditional.
- Non-interactive behaviour: both agents return NEEDS-INPUT/needs-input numbered questions; engineer P0 JVM check matches family rule (17/21). OK.

## Consensus matrix
| Finding | Scope | Flow | Engine | Sev |
|---|---|---|---|---|
| IT-fact overlap with quarkus-core junit | x | | x | MEDIUM |
| Engineer coverage command implicit | | x | x | MEDIUM |
| Reviewer launch path undocumented | | x | | LOW |
| Bash allowlist prompt-only | | | x | LOW |
| Tag wording / @change on spec-root | x | | x | LOW x2 |

## Remediation (priority)
1. Engineer P1: spell out `python .claude/skills/deriving-gherkin-from-openspec-v1-15/scripts/check_feature_coverage.py --spec-root <root> --features <dir> [--change <id> --strict]`.
2. testing-quarkus-integration-v3-40: add boundary line deferring generic @QuarkusIntegrationTest/profile facts to developing-quarkus-junit-v3-40.
3. Gherkin rule: conditional `@change-<id>` (only for change deltas) and align tag wording with the quarkus rule.
4. README acceptance-testing: say the reviewer is launched via the Agent tool by a coordinator or the user.
