# Always-Do Patterns: camel-quarkus-junit 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). All six patterns are High with versioned evidence except the statements explicitly tagged as medium confidence.

Contents: [1 Test dependency](#1-test-dependency) · [2 Base class and package](#2-base-class-and-package) · [3 One shared CamelContext](#3-one-shared-camelcontext) · [4 Advice in doBeforeEach](#4-advice-in-dobeforeeach) · [5 Per-method adviceRoute](#5-per-method-adviceroute) · [6 Integration tests without injection](#6-integration-tests-without-injection)

## 1. Test dependency

Only `camel-quarkus-junit` is documented in the 3.40 testing guide.

```xml
<!-- Camel Quarkus 3.40.x; version managed by the Camel Quarkus BOM -->
<dependency>
    <groupId>org.apache.camel.quarkus</groupId>
    <artifactId>camel-quarkus-junit</artifactId>
    <scope>test</scope>
</dependency>
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html

## 2. Base class and package

The 3.40.0 source declares `package org.apache.camel.quarkus.test;` and `public class CamelQuarkusTestSupport extends AbstractTestSupport implements QuarkusTestProfile`. The context is injected (`@Inject protected CamelContext context;`).

```java
// Camel Quarkus 3.40.x, JVM mode only
import io.quarkus.test.junit.QuarkusTest;
import org.apache.camel.component.mock.MockEndpoint;
import org.apache.camel.quarkus.test.CamelQuarkusTestSupport;
import org.junit.jupiter.api.Test;

@QuarkusTest
class GreetRouteTest extends CamelQuarkusTestSupport {
    @Test
    void greets() throws Exception {
        MockEndpoint mock = getMockEndpoint("mock:result");
        mock.expectedBodiesReceived("Hello World");
        template.sendBody("direct:start", "World");
        mock.assertIsSatisfied();
    }
}
```

Note: `template` is assigned from `contextManager.template()`; its declaring superclass was not read (medium confidence). The choice between this base class and a plain `@QuarkusTest` is a decision in the Ask First table of [SKILL.md](../SKILL.md).

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java

## 3. One shared CamelContext

The guide says one CamelContext is shared and stays started for the whole suite, that returning a new context "throws an exception", and that you can't call `stop()`/`start()` (the guide's recorded wording; it does not say that stop/start throws). The `camelContextSupplier` javadoc says "Do not create your own CamelContext instance".

```java
// Inspect or configure, never replace
@Inject CamelContext context; // supplied by CamelQuarkusTestSupport

// Clean context needed? Use a profile (restarts the application and the CamelContext; medium confidence, M12)
@QuarkusTest @TestProfile(IsolatedProfile.class)
class IsolatedTest extends CamelQuarkusTestSupport { }
```

Sources: the testing guide and the 3.40.0 source file linked in pattern 2.

## 4. Advice in doBeforeEach

Since 3.36, routes that are not advised start automatically once the method completes, and advice is cleaned up between test methods.

```java
@Override
protected void doBeforeEach(QuarkusTestMethodContext ctx) throws Exception {
    AdviceWith.adviceWith(this.context, "my-kafka-route", route ->
        route.weaveById("kafkaProducer").replace().to("mock:kafka-stub"));
}
```

Hook signature (3.40.0 source): `protected void doBeforeEach(QuarkusTestMethodContext context) throws Exception`. A JUnit `@BeforeEach` method works the same way with the same body (3.36.0 migration guide). More in [AdviceWith and lifecycle](./advice-with-and-lifecycle.md).

Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html

## 5. Per-method adviceRoute

The helper "handles route lifecycle (stop, advice, start) automatically". The javadoc and the guide warn against advising routes from `createRouteBuilder()`.

Signature (3.40.0): `protected void adviceRoute(String routeId, ThrowingConsumer<AdviceWithRouteBuilder, Exception> advice) throws Exception`

```java
@Test
void stubbed() throws Exception {
    adviceRoute("my-route", r -> r.weaveById("kafkaProducer").replace().to("mock:stub"));
    // assertions...
}
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html ; the 3.40.0 source file linked in pattern 2.

## 6. Integration tests without injection

The Camel guide says integration tests cannot `@Inject` beans or override beans, so communication uses the network, filesystem watching or other IPC; the test can extend the JVM test class (medium confidence: the subclassing shape rests on a `main`-branch example). Quarkus 3.40 says integration tests support everything "except injecting into tests". `CamelQuarkusTestSupport` "does not work for native mode tests" (javadoc).

```java
@QuarkusIntegrationTest
class HelloHttpIT extends HelloHttpTest { }   // HelloHttpTest: plain @QuarkusTest, REST Assured only
```

The `timer-log` example in `main` of camel-quarkus-examples uses the same shape (medium confidence, `main` branch; https://github.com/apache/camel-quarkus-examples/blob/main/timer-log/src/test/java/org/acme/timer/log/TimerLogIT.java). See [native testing](./native-testing.md).

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html ; https://quarkus.io/version/3.40/guides/getting-started-testing
