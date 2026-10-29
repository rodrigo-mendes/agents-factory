# Profiles, Test Resources, Dev Services and Ports: Quarkus JUnit 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Source unless noted: https://quarkus.io/version/3.40/guides/getting-started-testing

## Contents

- [Test profiles (medium confidence)](#test-profiles-medium-confidence)
- [Separate unit and integration executions (medium confidence)](#separate-unit-and-integration-executions-medium-confidence)
- [Finding the test URL (medium confidence)](#finding-the-test-url-medium-confidence)
- [Test resources (medium confidence)](#test-resources-medium-confidence)
- [Dev Services vs explicit resources](#dev-services-vs-explicit-resources)
- [Test port](#test-port)

## Test profiles (medium confidence)

Single source: the versioned guide. It says: "If a test has a different profile to the previously run test then Quarkus will be shut down and started". The Quarkus orderer groups tests that need the same application instance. `quarkus.test.profile.tags` selects profiles in CI. Each distinct profile or resource set costs one full application restart.

```java
// Quarkus 3.40
public class MockedProfile implements QuarkusTestProfile {
    @Override public Map<String, String> getConfigOverrides() { return Map.of("greeting.prefix", "test"); }
    @Override public Set<Class<?>> getEnabledAlternatives() { return Set.of(FakeClock.class); }
    @Override public Set<String> tags() { return Set.of("mocked"); }
}
@QuarkusTest @TestProfile(MockedProfile.class)
class MockedTest { /* ... */ }
```

## Separate unit and integration executions (medium confidence)

Single source. The guide says `@QuarkusTest` and `@QuarkusIntegrationTest` should not run in the same execution and recommends splitting them on the `io.quarkus.test.junit.QuarkusTest` tag. `@QuarkusIntegrationTest` runs the packaged artifact in the `prod` profile by default (change with `quarkus.test.integration-test-profile`) and does not support injection.

## Finding the test URL (medium confidence)

The 3.40 guide documents `@TestHTTPResource` (URI, URL or String) and `@TestHTTPEndpoint`. The 3.31 migration guide names `ConfigProvider`/`SmallRyeConfig` and the injectable `io.quarkus.vertx.http.HttpServer` instead of reading system properties; it does not name `@TestHTTPResource`/`@TestHTTPEndpoint`. The research rates the pair medium (M3) because the two sources make different claims. Sources: the testing guide ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31

```java
@TestHTTPEndpoint(GreetingResource.class)
@TestHTTPResource
URL url;
```

## Test resources (medium confidence)

- `@QuarkusTestResource` is global unless `restrictToAnnotatedClass = true`; `parallel = true` starts resources concurrently.
- `@WithTestResource(scope = MATCHING_RESOURCES (default) | RESTRICTED_TO_CLASS | GLOBAL)` groups tests by resource set.
- The 3.40 page does not call `@QuarkusTestResource` deprecated (absence of evidence).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `@QuarkusTestResource` (global) | single startup | leaks into all tests | one shared DB or broker |
| `@WithTestResource` `MATCHING_RESOURCES` | isolation plus reuse by group | more restarts | mixed resource needs |
| `RESTRICTED_TO_CLASS` | strict isolation | restart per class | destructive resources |

```java
public class PostgresResource implements QuarkusTestResourceLifecycleManager {
    @Override public Map<String, String> start() { /* start container */ return Map.of("quarkus.datasource.jdbc.url", "..."); }
    @Override public void stop() { }
}
@QuarkusTest @WithTestResource(value = PostgresResource.class) // scope defaults to MATCHING_RESOURCES
class RepoTest { }
```

JUnit parallel test execution with `@QuarkusTest` is not documented on the 3.40 page (unverified, I1).

## Dev Services vs explicit resources

Source: https://quarkus.io/version/3.40/guides/dev-services (first 100k characters read; coverage limit L2, medium confidence beyond that) ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html (precedence of `start()` values)

- Dev Services are automatic in dev and test for unconfigured services, need a container runtime, are disabled when connection config such as a JDBC URL is set, and are disabled globally with `quarkus.devservices.enabled=false`.
- Values returned from a manager's `start()` have higher precedence than `application.properties` (Camel testing guide; for Camel route tests use `developing-camel-quarkus-junit-v3-40`).
- Container sharing applies only in dev mode. Dev Services live in deployment modules and do not affect production.
- Objects implementing `io.quarkus.test.common.DevServicesContext.ContextAware` can be injected with the Dev Services context, which exposes the container network id.
- Whether Dev Services restart or are reused when the application restarts on a profile change is unverified (U1); the page only says they are reused while their configuration is unchanged.

## Test port

Default `quarkus.http.test-port` is 8081 with `quarkus.http.test-ssl-port` alongside; `0` picks a random port. `quarkus.http.test-timeout` (REST Assured) defaults to 30s. Use `0` when parallel CI agents share a host.
