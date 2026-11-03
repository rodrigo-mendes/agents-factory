# quarkus-acceptance-testing

APM package that turns OpenSpec scenarios into **Cucumber 8.0 acceptance tests** for Quarkus 3.40 LTS
REST applications (black-box, Failsafe, RestAssured, WireMock for external HTTP).

## Contents

| Kind | Name | Role |
|---|---|---|
| Skill | `testing-quarkus-cucumber-v8-0` | Cucumber 8.0.4 on Quarkus 3.40: B1 default runner (Cucumber `Main.run` inside one `@QuarkusIntegrationTest`), B2 `@Suite` runner, steps and state |
| Skill | `testing-quarkus-integration-v3-40` | `@QuarkusIntegrationTest`, Failsafe, Dev Services, RestAssured, WireMock, Testcontainers |
| Agent | `acceptance-test-engineer` | Non-interactive executor: features, step definitions, `AcceptanceIT`, stubs, `verify` |
| Command | `/building-acceptance-tests` | Forks to `acceptance-test-engineer` |
| Rule | `quarkus-acceptance-tests` | Step, IT and feature files in Quarkus projects |

Comes from the `acceptance-testing` package (dependency): skill `deriving-gherkin-from-openspec-v1-15`,
rule `gherkin-feature-authoring`, agent `acceptance-test-reviewer`. From `quarkus-core`:
`developing-quarkus-junit-v3-40`, `developing-quarkus-rest-v3-40`, `developing-quarkus-arc-v3-40`.
The agent loads only the junit skill; rest and arc come transitively for production code.

`acceptance-test-reviewer` has no `/command`: the user or a coordinator launches it with the Agent
tool after the engineer.

## Scope

Quarkus 3.40 LTS REST applications, Cucumber 8.0 as a black-box suite over HTTP, features derived from
OpenSpec requirements and scenarios.

## Out of scope

- `quarkus-cucumber` as the default runner (Ask-First only; see the Cucumber skill).
- Native-image tests.
- JavaScript / Playwright UI tests.
- Wiring into the SaaS orchestrator flow (deferred).

## Usage

```
/building-acceptance-tests openspec/changes/add-greeting ./service mode=features-only
/building-acceptance-tests openspec ./service mode=full
```

After the command, launch `acceptance-test-reviewer` (read-only, no `/command`) with the Agent tool on the result. The agent returns
numbered questions (NEEDS-INPUT) when the spec is incomplete or an Ask-First item is open.

## Versions

| Component | Version |
|---|---|
| Cucumber JVM | 8.0.4 |
| Quarkus | 3.40 LTS |
| quarkus-wiremock | 1.8.1 |
| RestAssured | 6.0.1 |
| Testcontainers | 2.0.5 (medium confidence) |
| JDK | 17 / 21 |

Details and source dates live in the two skills.

## Provenance

- Research under `workspace/software-quality` (family facts and rules).
- Orchestrator spike: Cucumber 8.0.4 inside `@QuarkusIntegrationTest` and the WireMock Dev Service passed
  `mvn verify` on Quarkus 3.40.1, JDK 21, 2026-10-31.
- Approval: recorded 2026-10-31 in `workspace/software-quality/execution-1/state/gates/G1.md` and `G2.md`.

## Maintenance

After editing sources, run `apm install --target claude` and commit sources plus regenerated `.claude/`.
