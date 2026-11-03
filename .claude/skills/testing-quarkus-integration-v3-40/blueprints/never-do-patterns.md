# Never-do patterns

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-01: [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing), [rest-client guide](https://quarkus.io/version/3.40/guides/rest-client), [Testcontainers releases](https://github.com/testcontainers/testcontainers-java/releases), [pom.xml 3.40.1](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/pom.xml).

## Injection into an IT

Impact: null fields or a startup error, because the app is another process.

```java
// ❌ Wrong
@QuarkusIntegrationTest
class OrdersIT { @Inject OrderService service; }
```

✅ Instead: assert through HTTP with RestAssured; stub dependencies with WireMock or a test resource.

## IT configuration in test resources

```properties
# ❌ Wrong: src/test/resources/application.properties is not read by the launched app
quarkus.rest-client.orders-api.url=http://localhost:8089
```

✅ Instead: return the value from `QuarkusTestResourceLifecycleManager.start()` (see [always-do](./always-do-patterns.md#configuration-reaches-the-app)).

Second option, spike-proven only (medium confidence): a `${quarkus.wiremock.devservices.port}` expression in main `application.properties`, see [stubbing](./stubbing-and-containers.md#url-wiring-for-the-launched-app).

## Surefire running ITs

Impact: ITs run before `package`, so there is no artifact to launch, or they run twice.
✅ Instead: Surefire for `@QuarkusTest`, Failsafe for `*IT` with goals `integration-test` and `verify`.

## Real external services

The rest-client guide shows a WireMock catch-all proxy to the real API "for demonstration only"; copying it makes the suite flaky and can change real data.
✅ Instead: explicit stubs only; an unmatched request returns 404 from WireMock.

## Testcontainers 1.x

```java
// ❌ Wrong: 1.x coordinates and JUnit 4 rule
// org.testcontainers:postgresql  +  @ClassRule PostgreSQLContainer
```

✅ Instead: `org.testcontainers:testcontainers-postgresql`, version from the Quarkus BOM, started in a test resource.

## Version overrides

```xml
<!-- ❌ Wrong: overrides the BOM-managed 6.0.1 -->
<artifactId>rest-assured</artifactId><version>6.3.0</version>
```

✅ Instead: no `<version>`. RestAssured 6.3.0 exists upstream but Quarkus 3.40 manages 6.0.1 (family rule 8). Also no explicit `junit-jupiter`, `byte-buddy` or `mockito-inline`.

## Sharing state through method order

Tests of one Failsafe run share the app and its database; `quarkus.test.class-orderer` orders classes only.
✅ Instead: unique keys per test, see [test data isolation](./restassured-and-data.md#test-data-isolation).
