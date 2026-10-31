# Test Types and Lifecycle: Quarkus JUnit 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Sources are versioned 3.40 guides unless noted.

## Contents

- [Test types](#test-types)
- [Lifecycle](#lifecycle)
- [Conditional execution](#conditional-execution)
- [Continuous testing](#continuous-testing)
- [Coverage](#coverage)
- [Verification commands](#verification-commands)

## Test types

| Type | What it does | Injection | Source |
|---|---|---|---|
| `@QuarkusTest` | JVM test running inside the Quarkus application; test classes are CDI beans | yes | https://quarkus.io/version/3.40/guides/getting-started-testing |
| `@QuarkusIntegrationTest` | black-box test against the built jar, native binary or container; `prod` profile by default (medium confidence) | no | https://quarkus.io/version/3.40/guides/getting-started-testing |
| `@QuarkusMainTest` | command-mode applications; no CDI injection, Panache entities or `@InjectMock` | no | https://quarkus.io/version/3.40/guides/command-mode-reference |
| `@QuarkusMainIntegrationTest` | runs the built jar or native executable of a command-mode app | no | https://quarkus.io/version/3.40/guides/command-mode-reference |

A `@QuarkusIntegrationTest` class can extend a `@QuarkusTest` class to reuse HTTP-only assertions, without `@Inject` (medium confidence, M5: rests on a main-branch example).

## Lifecycle

Quarkus starts once per test run and is restarted only when the next test has a different profile (medium confidence for the profile grouping; see [profiles](./profiles-and-resources.md#test-profiles-medium-confidence)). Hang detection defaults to 10 minutes (`quarkus.test.hang-detection-timeout`). Debug arguments go in `quarkus.test.arg-line`. Source: https://quarkus.io/version/3.40/guides/getting-started-testing

```java
// Quarkus 3.40: @QuarkusTest with REST Assured, injection, transactional rollback
@QuarkusTest
@TestHTTPEndpoint(GreetingResource.class)        // medium confidence, M3
class GreetingResourceTest {
    @Inject GreetingService service;                 // tests are CDI beans

    @Test void hello() {
        given().when().get().then().statusCode(200).body(is("hello"));  // port 8081 by default
    }

    @Test @TestTransaction                           // rolled back at end of test
    void persists() { /* ... */ }
}
```

## Conditional execution

`@EnabledIfConfig` and `@DisabledIfConfig` resolve values through MicroProfile Config. Stacked `@EnabledIfConfig` uses AND logic, stacked `@DisabledIfConfig` uses OR logic. Neither annotation is `@Inherited`. Source: https://quarkus.io/version/3.40/guides/getting-started-testing

## Continuous testing

Source for this section: https://quarkus.io/version/3.40/guides/continuous-testing

- `quarkus.test.continuous-testing` is `paused` (default), `enabled` or `disabled`.
- `quarkus.test.exclude-tags` defaults to `slow` and is ignored when `include-tags` is set.
- `quarkus.test.exclude-pattern` defaults to `.*\.IT[^.]+|.*IT|.*ITCase`.
- `quarkus.test.only-test-application-module=true` disables multi-module support.
- `quarkus.test.flat-class-path` is incompatible with continuous testing.
- The Dev UI is not available in `quarkus:test`.

## Coverage

Source for this section: https://quarkus.io/version/3.40/guides/tests-with-coverage

- Add `io.quarkus:quarkus-jacoco` with test scope. Its automatic configuration works only for `@QuarkusTest`.
- `quarkus.jacoco.data-file` defaults to `target/jacoco-quarkus.exec`.
- `quarkus.jacoco.report-location` defaults to `target/jacoco-report`, but the page also says `target/jacoco-reports` (unverified, I3). Set it explicitly.
- Coverage is not supported in native mode.
- Integration-test coverage needs a jar artifact and `quarkus.package.write-transformed-bytecode-to-build-output=true` (the guide says use with caution).

## Verification commands

Representative commands (page not recorded); adapt to your build.

```bash
./mvnw test                                   # @QuarkusTest via Surefire
./mvnw verify -Dnative                        # @QuarkusIntegrationTest via Failsafe (native)
./mvnw quarkus:test                           # continuous testing without dev mode
./mvnw test -Dquarkus.test.profile.tags=mocked
./mvnw dependency:tree | grep -E "quarkus-junit5|junit-jupiter"
# Expected: no quarkus-junit5 line; junit-jupiter 6.1.3 on Quarkus 3.40.1
```
