# AdviceWith, Lifecycle Hooks and Route Loading

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Lifecycle hooks

Mapping from the testing guide (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html): `afterAll` to `doAfterAll`, `afterEach`/`afterTestExecution` to `doAfterEach`, `beforeAll` to `doAfterConstruct`, `beforeEach` to `doBeforeEach`. Signatures are from the 3.40.0 source (https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java).

```java
// Camel Quarkus 3.40.x
@QuarkusTest
class OrderRouteTest extends CamelQuarkusTestSupport {

    @Override
    protected void doBeforeEach(QuarkusTestMethodContext ctx) throws Exception {
        AdviceWith.adviceWith(this.context, "orders", r ->
            r.weaveById("toErp").replace().to("mock:erp"));
    }   // non-advised routes auto-start afterwards (3.36+)

    @Test
    void routesOrder() throws Exception {
        MockEndpoint erp = getMockEndpoint("mock:erp");
        erp.expectedMessageCount(1);
        template.sendBody("direct:orders", "{\"id\":1}");
        erp.assertIsSatisfied();
    }   // advice cleaned up before the next method

    @Override
    protected void doAfterAll(QuarkusTestContext ctx) throws Exception { }
}
```

`doAfterConstruct` runs before each test under `@TestInstance(Lifecycle.PER_METHOD)` (3.40.0 javadoc). The `doAfterAll` parameter type `QuarkusTestContext` is taken from the research sample and was not separately confirmed (medium confidence).

## Choosing between doBeforeEach and adviceRoute

| Need | Use | Source |
|---|---|---|
| Same advice for every test method of the class | `AdviceWith.adviceWith(this.context, ...)` in `@BeforeEach`/`doBeforeEach` | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html |
| Different advice per test method | `adviceRoute(routeId, advice)` inside the test | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html |

## Mocking a consumer and an outbound endpoint

```java
// Camel Quarkus 3.40.x
adviceRoute("orders", r -> {
    r.replaceFromWith("direct:in");
    r.weaveById("toErp").replace().to("mock:erp");
});
```

`weaveById` and `weaveByToUri` are documented in the testing guide. `replaceFromWith` is not shown on the 3.40 Camel Quarkus page; it comes from the Camel AdviceWith manual (medium confidence).

## Routes loaded in tests

All application RouteBuilders plus the XML/YAML routes matched by `camel.main.routes-include-pattern` are loaded. Filter them with `quarkus.camel.routes-discovery.include-patterns|exclude-patterns` and `camel.main.routes-include-pattern|routes-exclude-pattern` (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html).

## Overriding createCamelContext (irresolvable)

The 3.40 guide shows overriding `createCamelContext()` with a `super` call, but the 3.40.0 `CamelQuarkusTestSupport` source declares only `camelContextSupplier()` and `bindToRegistry(Registry)`; `AbstractTestSupport` was not read. Do not assert that the override compiles; configure through CDI beans or `@BindToRegistry`, or compile once to check. See the [register](./unverified-and-risks.md#irresolvable-items-do-not-assert).
