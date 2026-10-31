# Native and Packaged Integration Tests

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Rules from the docs

| Rule | Source |
|---|---|
| Integration tests cannot `@Inject` or override beans; communicate via network, filesystem watching or other IPC; the test may extend the JVM test class (medium confidence: subclassing rests on a `main`-branch example) | https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html |
| `CamelQuarkusTestSupport` "does not work for native mode tests" (javadoc) | https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java |
| Integration tests run with the `prod` profile by default (`quarkus.test.integration-test-profile`) and ignore `src/test/resources/application.properties` (medium confidence: unversioned or partly read evidence, see the register) | https://quarkus.io/version/3.40/guides/getting-started-testing |
| Failsafe runs `integration-test` and `verify` with `native.image.path=${project.build.directory}/${project.build.finalName}-runner`; set the surefire version explicitly because "the default version does not support JUnit" | https://quarkus.io/version/3.40/guides/getting-started-testing |

The Quarkus page was read for characters 0 to 100000 of 108136 (coverage limit); statements from its unread tail are medium confidence.

## Reusing a JVM test as an integration test

```java
// HTTP-only base: no CamelQuarkusTestSupport, no @Inject
@QuarkusTest
class HelloHttpTest {
    @Test
    void hello() {
        io.restassured.RestAssured.given().when().get("/hello").then().statusCode(200);
    }
}

@io.quarkus.test.junit.QuarkusIntegrationTest
class HelloHttpIT extends HelloHttpTest { }
```

The `timer-log` example in the `main` branch of camel-quarkus-examples follows this shape: `TimerLogTest` (`@QuarkusTest`, Awaitility on `target/quarkus.log`) and `TimerLogIT extends TimerLogTest` (medium confidence, `main` branch, not a 3.40.x tag; https://github.com/apache/camel-quarkus-examples/blob/main/timer-log/src/test/java/org/acme/timer/log/TimerLogIT.java).

## Commands (representative, adapt to your environment)

```bash
mvn verify                 # @QuarkusTest (JVM)
mvn verify -Dnative        # @QuarkusIntegrationTest through maven-failsafe-plugin
# Expected: BUILD SUCCESS
```

Native builder: GraalVM 25.0.4.1 per https://camel.apache.org/camel-quarkus/latest/.

## Security

Test resources should hand credentials to the application through the config map returned by `start()` instead of committing them to `application.properties` (the research states this as practice; no official page recorded, medium confidence).
