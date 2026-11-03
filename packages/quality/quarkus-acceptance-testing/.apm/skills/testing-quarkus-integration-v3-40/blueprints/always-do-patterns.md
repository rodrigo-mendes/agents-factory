# Always-do patterns

Back to [SKILL.md](../SKILL.md). All sources read 2026-11-01. Pom and run modes: [Failsafe and run modes](./failsafe-and-run-modes.md); stubs: [stubbing and containers](./stubbing-and-containers.md); HTTP and data: [RestAssured and data](./restassured-and-data.md).

## Naming and reuse

- Name IT classes `*IT` and annotate them `@QuarkusIntegrationTest`.
- Reuse a `@QuarkusTest` class by extension, so one set of assertions runs in-process and against the packaged artifact:

```java
@QuarkusIntegrationTest
class GreetingResourceIT extends GreetingResourceTest { }
```

- Continuous testing excludes `.*IT` by default (`quarkus.test.exclude-pattern`).
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing; https://quarkus.io/version/3.40/guides/maven-tooling; https://quarkus.io/version/3.40/guides/all-config.

## Black-box only

- The artifact runs in its own process: no bean injection, no `@InjectMock`. The only injectable types are `DevServicesContext` and, with quarkus-wiremock, `WireMock` (family fact F6).
- Assert on status, headers and body over HTTP. Test types and mocks live in `developing-quarkus-junit-v3-40`.
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing.

## Configuration reaches the app

The launched app uses the `prod` profile and ignores test-scope `application.properties`. Three channels exist:

```java
public class ExternalApiResource implements QuarkusTestResourceLifecycleManager {
    private WireMockServer server;
    @Override public Map<String, String> start() {
        server = new WireMockServer(WireMockConfiguration.options().dynamicPort());
        server.start();
        return Map.of("quarkus.rest-client.orders-api.url", server.baseUrl());
    }
    @Override public void stop() { if (server != null) server.stop(); }
}
```

- Test resource `start()` return map (above).
- `quarkus.test.arg-line` for JVM or app arguments, `quarkus.test.env.*` for environment variables.
- Dev Services, which publish their connection settings automatically.
- Activate a resource with `@QuarkusTestResource(ExternalApiResource.class)`; scope rules are in `developing-quarkus-junit-v3-40`.
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing; https://quarkus.io/version/3.40/guides/rest-client ("Using a Mock HTTP Server for tests").

## Profile for ITs

- Default is `prod`. Override with `-Dquarkus.test.integration-test-profile=it`.
- `%it.` keys must sit in `src/main/resources/application.properties`, because that is the file packaged.
- Native tests always use `prod`.
- Source: https://quarkus.io/version/3.40/guides/getting-started-testing; https://quarkus.io/version/3.40/guides/all-config; https://quarkus.io/version/3.40/guides/maven-tooling.

## BOM-managed versions

- Import `io.quarkus.platform:quarkus-bom` 3.40.x and declare `rest-assured`, `quarkus-junit` and `testcontainers-*` without `<version>`.
- quarkus-wiremock is not in the BOM: pin `1.8.1` explicitly for `quarkus-wiremock` and `quarkus-wiremock-test`.
- Source: https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/pom.xml; https://docs.quarkiverse.io/quarkus-wiremock/dev/index.html.

## Verify the run

- A green build with zero ITs is not evidence: count `<testcase` entries in `target/failsafe-reports` after `mvn verify`.
- Check no IT injects beans: `grep -rn "@Inject" src/test/java --include=*IT.java` (unverified).
