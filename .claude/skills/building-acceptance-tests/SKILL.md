---
name: building-acceptance-tests
description: "Routes a closed OpenSpec spec and a Quarkus 3.40 project to the acceptance-test-engineer agent. Use when Gherkin features and Cucumber 8.0 acceptance tests must be derived from a spec and implemented in a Quarkus project (e.g. features only, or the full suite)."
argument-hint: "<change-dir|spec-root> <project-dir> [mode=features-only|full]"
context: fork
agent: acceptance-test-engineer
disable-model-invocation: true
---

# Building Acceptance Tests

## Function

Routes a spec location and a Quarkus project directory to the `acceptance-test-engineer` agent. The
agent derives features from the spec, then (in `full` mode) writes step definitions, the
acceptance IT and stubs, and runs the build. It states no technical facts of its own; they come
from the installed skills.

## How to phrase the request

The agent is non-interactive. Supply all of the following or it returns NEEDS-INPUT questions:

1. **Spec**: an `openspec/changes/<id>` directory or the spec root.
2. **Project dir**: the Quarkus project (Maven).
3. **Mode**: `features-only` or `full` (default `full`).
4. **Decisions** the skills treat as Ask First, if they matter (runner choice, Testcontainers vs Dev Services, parallel scenarios).
5. **External HTTP dependencies** the scenarios touch, so they can be stubbed.

## What the agent will and will not do

**Will:** derive or update features and check coverage with the skill script; add test
dependencies; write steps, the IT and WireMock stubs; run `verify`; report files, coverage, Maven
result, spec impact and open questions. Next step is `acceptance-test-reviewer`, which you run.

**Will not:** edit the spec; change production behaviour beyond what a scenario requires (it
asks); commit, push or deploy; spawn agents; call real external services; work on non-Quarkus
projects.

## Usage examples

```
/building-acceptance-tests openspec/changes/add-greeting ./service mode=features-only
/building-acceptance-tests openspec ./service mode=full
/building-acceptance-tests openspec/changes/add-greeting ./service
```

## Evaluation Scenarios

See [./blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
