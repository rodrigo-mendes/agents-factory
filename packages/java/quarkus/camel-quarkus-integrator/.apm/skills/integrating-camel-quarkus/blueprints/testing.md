# Testing Blueprint

Back to [SKILL.md](../SKILL.md). Shared workflow, structure skill and boundaries live there; this file holds only the testing specialty.

## Contents

- [Specializations](#specializations)
- [Required Skills](#required-skills)
- [What to Ask](#what-to-ask)
- [Ask First Decisions](#ask-first-decisions)
- [Team Conventions](#team-conventions)
- [Quality Standards](#quality-standards)

Two kinds of rules appear below. Anything under **Specializations**, **Required Skills** and **Quality Standards** follows the installed skills. Anything under [Team Conventions](#team-conventions) is (team convention): an internal choice, not official documentation, and it must never override the skills.

## Specializations

1. **Route tests**: `@QuarkusTest` extending `CamelQuarkusTestSupport`, `MockEndpoint`, AdviceWith, `adviceRoute`.
2. **Component and CDI tests**: `@QuarkusTest` with injection, `@InjectMock` on normal-scoped beans.
3. **REST endpoint tests**: REST Assured on `@QuarkusTest`, no Camel base class needed.
4. **Packaged/native tests**: `@QuarkusIntegrationTest` without injection.
5. **File-output tests**: wait for asynchronous file results, then assert on content.
6. **Model/POJO tests**: plain JUnit Jupiter without Quarkus or Camel (for example JAXB model checks).

## Required Skills

| Need | Skill |
|---|---|
| Always | `developing-camel-quarkus-junit-v3-40` (test artifact `camel-quarkus-junit`, AdviceWith, lifecycle hooks) |
| Always | `developing-quarkus-junit-v3-40` (`quarkus-junit`, profiles, test resources, `@InjectMock`) |
| Always | `structuring-camel-quarkus-projects` (test paths and class names) |
| Mocking CDI beans | `developing-quarkus-arc-v3-40`, `developing-camel-quarkus-bean-v3-40` |
| File-output tests | `developing-camel-quarkus-file-v3-40` |
| Log assertions | `developing-camel-quarkus-log-v3-40` (asserting log text is unverified; prefer `mock:` assertions) |

## What to Ask

- Test levels wanted: unit, route, integration against the packaged artifact, performance.
- Which external systems must be replaced (outbound HTTP, files, beans).
- Whether tests must also run against a native build (decides the base class).

## Ask First Decisions

| Decision | Options | Source |
|---|---|---|
| Base class | `CamelQuarkusTestSupport` (JVM only) vs plain `@QuarkusTest` (reusable as integration-test base) (medium confidence) | Ask First in the Camel junit skill |
| State isolation | Shared context vs `@TestProfile` (each profile costs a restart) (medium confidence) | Ask First in both junit skills |
| Mocking strategy | `@InjectMock`, `@Alternative`, `QuarkusMock`, or `MockEndpoint` | Ask First in the Quarkus junit skill; for route collaborators prefer `MockEndpoint`/AdviceWith |
| Performance and load testing | No installed skill covers it; ask whether to proceed without | User |

## Team Conventions

Labelled (team convention). Review items marked FLAGGED with the team before relying on them.

### One test class per route (team convention)

Explicit exception to the structure skill, which names one `[ClassName]Test` per RouteBuilder class; this refines it per `routeId`. A `RouteBuilder` with several `routeId`s gets one test class per route plus one for its error handler (for example `ProcessOrderRouteTest`). FLAGGED: combined with a dedicated `@TestProfile` per class (below), every class restarts Quarkus; the Quarkus junit skill says each profile costs one restart (medium confidence). Use shared profiles for routes that do not conflict.

### When to extend `CamelQuarkusTestSupport` (team convention)

- Extend it when the test uses `MockEndpoint`, `ProducerTemplate`, AdviceWith or the `CamelContext`.
- Do not extend it when the test only uses REST Assured, a POJO, or injected application beans.
- Hybrid (REST Assured plus AdviceWith) when the route starts at `rest()` and its sub-routes must be mocked: call the endpoint with REST Assured and advise the outbound steps.
- FLAGGED: do not restart routes with `getRouteController().startRoute(...)` after advice. Since 3.36 non-advised routes start automatically (Camel junit skill); any REST DSL consumer "merge" behavior is not documented there.

### Choosing how to advise (team convention)

| Route kind | Trigger | Advise by |
|---|---|---|
| `from("direct:x")` | `template.sendBody("direct:x", ...)` | `weaveById("<stepId>")` (give outbound steps ids) |
| `rest().post().to("direct:x")` | REST Assured | `weaveById`; `weaveByToUri` for a fixed URI |
| `toD(...)` with a dynamic URI | as its `from` | FLAGGED: `weaveByType(ToDynamicDefinition.class)` is not documented (the skills document only `weaveById` and `weaveByToUri`): confirm it compiles and works, or give the `toD` an id and use `weaveById` |

Never use wildcard patterns such as `weaveByToUri("kafka:*")` (Camel junit skill, Never Do).

### Test profile isolation (team convention)

When two classes advise the same routes and conflict, give each its own profile: a class implementing `QuarkusTestProfile` that returns `getConfigOverrides()` (Quarkus junit skill), referenced with `@TestProfile`.

- Limit loaded routes with `quarkus.camel.routes-discovery.include-patterns` (Camel junit skill, Quick Reference).
- Provide dummy values for every `@ConfigProperty` the included routes read.
- Use `quarkus.http.test-port=0` for random ports when REST routes load; the default is 8081.
- FLAGGED: do not set `camel.quarkus.test.use-advice-with=true` (the skills never mention it; `isUseAdviceWith()` is deprecated, so advise in `doBeforeEach`/`@BeforeEach`).
- FLAGGED (unverified): a separate `application-<profile>.properties` file per profile. The skills document `getConfigOverrides()` only.

### Advice and mock lifecycle (team convention)

- FLAGGED: do not apply AdviceWith once in `@BeforeAll` with `@TestInstance(PER_CLASS)`. The Camel junit skill says advice is cleaned up between test methods since 3.36, so a once-per-class advice would be undone. Advise in `@BeforeEach`/`doBeforeEach` for class-wide advice, or `adviceRoute(routeId, ...)` per method.
- Reset mock endpoints before and after each test to keep tests independent (team convention; not stated by the skills, harmless).

### File-output tests (team convention)

- Wait for output with Awaitility, then check the file name pattern and content (XML).
- Write test output under `target/test-output/` and clean it up after the test.
- The skills only mention Awaitility in `main`-branch examples (medium confidence); add the dependency explicitly.

### Test documentation (team convention)

- Javadoc on each test class: what is tested and the scenarios covered. English. Name the skills used by name (no file paths).
- Class annotations: `@QuarkusTest` when Quarkus is needed, `@Tag("unit|integration|rest|smoke|file-integration")`.
- Method annotations: `@Test`, `@DisplayName("...")` in English. FLAGGED: tests must not depend on order; use `@TestMethodOrder` with `@Order(N)` only for readable grouping, never for state.
- Group related tests under comment headers (constructor, validation, error handling).

## Quality Standards

### ✅ Always Do

- **Depend on `camel-quarkus-junit` at test scope** and extend `org.apache.camel.quarkus.test.CamelQuarkusTestSupport` for Camel route tests.
- **Mock outbound steps with `MockEndpoint`/AdviceWith**, and clean up test data and files.
- **Keep `@QuarkusIntegrationTest` classes free of `@Inject` and bean overrides.**
- **Test happy path, error path and edge cases** for each route.

### ⚠️ Ask First

- **Test levels** and whether native tests are required.
- **Profile strategy**: shared vs per-class (restart cost).
- **Test data** scenarios to cover.

### 🚫 Never Do

- **Never use `camel-quarkus-junit5` or `org.apache.camel.test.junit5`.** Instead: `camel-quarkus-junit`, `org.apache.camel.test.junit6` imports.
- **Never call `startRouteDefinitions()` after AdviceWith or override `isUseAdviceWith()`.** Instead: rely on auto-start.
- **Never stop, start or replace the CamelContext in a test.** Instead: a distinct `@TestProfile`.
- **Never hardcode test data that must vary, or leave external dependencies unmocked.** Instead: fixtures and mocks.
