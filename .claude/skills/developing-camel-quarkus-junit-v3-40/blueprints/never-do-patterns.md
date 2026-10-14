# Never-Do Patterns: camel-quarkus-junit 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). All seven items are High with versioned evidence.

Contents: [1 junit5](#1-camel-quarkus-junit5-and-junit5-imports-severity-high) · [2 startRouteDefinitions](#2-startroutedefinitions-after-advicewith-severity-moderate) · [3 CamelContext](#3-replacing-stopping-or-starting-the-camelcontext-severity-high) · [4 wildcards](#4-wildcard-weave-patterns-severity-moderate) · [5 createRouteBuilder](#5-advising-routes-from-createroutebuilder-severity-moderate) · [6 integration tests](#6-inject-or-camelquarkustestsupport-in-quarkusintegrationtest-severity-high) · [7 isUseAdviceWith](#7-isuseadvicewith-severity-moderate)

## 1. camel-quarkus-junit5 and junit5 imports (severity: high)

Renamed in 3.31. The 3.40.0 `junit5` artifact is a stub marked "Deprecated" whose only dependency is `camel-quarkus-junit`.

```xml
<!-- ❌ WRONG -->
<artifactId>camel-quarkus-junit5</artifactId>  <!-- import org.apache.camel.test.junit5.* -->
<!-- ✅ CORRECT -->
<artifactId>camel-quarkus-junit</artifactId><scope>test</scope> <!-- org.apache.camel.test.junit6.* -->
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html ; https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom

## 2. startRouteDefinitions() after AdviceWith (severity: moderate)

Since 3.36, routes that are not advised start automatically.

```java
// ❌ WRONG (3.35 idiom)
AdviceWith.adviceWith(context, "my-route", r -> ...);
startRouteDefinitions();
// ✅ CORRECT
AdviceWith.adviceWith(this.context, "my-route", r -> ...); // routes auto-start after @BeforeEach
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html

## 3. Replacing, stopping or starting the CamelContext (severity: high)

There is one application-scoped context; the guide says returning a new one throws an exception and that you can't call `stop()`/`start()` (its recorded wording; it does not say stop/start throws).

```java
// ❌ WRONG
context.stop(); context.start();
// or: return new DefaultCamelContext();
// ✅ CORRECT: inspect or configure the injected context, never replace it
```

A clean context is a separate decision: see the Ask First row "State isolation" in [SKILL.md](../SKILL.md).

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html

## 4. Wildcard weave patterns (severity: moderate)

The guide warns that a pattern like `weaveByToUri("kafka:*")` matches every matching endpoint.

```java
// ❌ WRONG
route.weaveByToUri("kafka:*").replace().to("mock:x");
// ✅ CORRECT
route.weaveById("kafkaProducer").replace().to("mock:x");
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html

## 5. Advising routes from createRouteBuilder() (severity: moderate)

The guide says this "can behave unpredictably"; the `adviceRoute` javadoc says the same.

```java
// ❌ WRONG
@Override protected RoutesBuilder createRouteBuilder() { /* route "t" */ }
// then: adviceRoute("t", ...)
// ✅ CORRECT: advise a route defined in src/main (application RouteBuilder);
// use createRouteBuilder only for test-only routes
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java

## 6. @Inject or CamelQuarkusTestSupport in @QuarkusIntegrationTest (severity: high)

Integration tests cannot inject or override beans; the base class does not work in native mode.

```java
// ❌ WRONG
@QuarkusIntegrationTest
class RouteIT extends CamelQuarkusTestSupport { @Inject ProducerTemplate t; }
// ✅ CORRECT
@QuarkusIntegrationTest
class RouteIT {   // no @Inject, no CamelQuarkusTestSupport: network only
    @Test void ok() { io.restassured.RestAssured.given().when().get("/orders").then().statusCode(200); }
}
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://quarkus.io/version/3.40/guides/getting-started-testing

## 7. isUseAdviceWith() (severity: moderate)

`@Deprecated(since = "3.15.0")` in the 3.40.0 source; the javadoc says to advise in `doBeforeEach`.

```java
// ❌ WRONG
@Override public boolean isUseAdviceWith() { return true; }
// ✅ CORRECT
@Override protected void doBeforeEach(QuarkusTestMethodContext ctx) throws Exception { AdviceWith.adviceWith(this.context, "r", b -> ...); }
```

Source: https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java
