# Package brief — software-quality

```yaml
slug: software-quality
language: en
frameworks:
  - Cucumber JVM 8.0            # pilot researches both paths: Cucumber 8 engine (black-box) vs Quarkiverse quarkus-cucumber 1.3.0
  - Quarkus 3.40                # integration testing (@QuarkusIntegrationTest, Dev Services, Failsafe)
  - quarkus-wiremock 1.8        # WireMock 3.13 for external HTTP in tests
  - Gherkin (cucumber/gherkin 42) + OpenSpec 1.15
needs:
  - Generate Gherkin .feature files from OpenSpec specs/changes for acceptance tests, with traceability
  - Implement the features with Cucumber on Quarkus 3.40
  - Integration tests on Quarkus (IT artifact, Dev Services, WireMock, Testcontainers 2)
  - Gherkin authoring rules for **/*.feature
legacy_source: none
deliverables: [skills, agent, rules, readme, command]
agent_kind: executor            # acceptance-test-engineer (executor) + acceptance-test-reviewer (read-only)
packages:
  - packages/quality/acceptance-testing          # generic: U3, gherkin rule, reviewer
  - packages/quality/quarkus-acceptance-testing  # U1, U2, engineer, command, quarkus rule
out_of_scope:
  - wiring into the SaaS orchestrator flow (coordinating-quarkus-aws-handoffs) -> own run
  - Cucumber for JS/Next.js, Playwright, native-image tests
research_worker: researching-technical-frameworks
research_depth: exhaustive      # user request 2026-10-31; no section-investigators, no plan mode (builder constraint)
rounds: 3
max_rounds: 5
token_budget: 4500000            # G2 2026-11-01
```
