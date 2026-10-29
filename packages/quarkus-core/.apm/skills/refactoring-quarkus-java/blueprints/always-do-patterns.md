# Always-do patterns

Back to [SKILL.md](../SKILL.md). Quarkus statements apply to Quarkus 3.40.x. The first six patterns are Quarkus facts with a source URL. The last three (green baseline, test coupling, one smell at a time) are the general method stated as team practice (register U1, no page read): team practice, outside the Always Do tier.

## Contents

- [Scope for an extracted collaborator](#scope-for-an-extracted-collaborator)
- [Markers travel with a moved bean](#markers-travel-with-a-moved-bean)
- [Resource signature keeps its thread model](#resource-signature-keeps-its-thread-model)
- [Validation stays on the resource parameter](#validation-stays-on-the-resource-parameter)
- [Lambda handler name stays in sync](#lambda-handler-name-stays-in-sync)
- [Index a new module](#index-a-new-module)
- [Green baseline](#green-baseline) (method)
- [Test coupling](#test-coupling) (method)
- [One smell at a time](#one-smell-at-a-time) (method)

## Scope for an extracted collaborator

A class that other beans receive through `@Inject` needs a bean-defining annotation; discovery runs in annotated mode ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). The CDI guide recommends `@ApplicationScoped` ([CDI guide](https://quarkus.io/version/3.40/guides/cdi)).

```java
// extracted from OrderResource; injected by the resource
@ApplicationScoped
public class OrderMapper {
    public OrderDto toDto(Order o) { return new OrderDto(o.id(), o.total()); }
}
```

A helper created with `new` inside one class is not a bean and needs no annotation.

## Markers travel with a moved bean

When a bean moves to another class or package, take every marker with it. Unremovable roots are `@Unremovable`, `quarkus.arc.unremovable-types`, `UnremovableBeanBuildItem`, `@Named` beans and beans with an observer method ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). Build-time conditions (`@IfBuildProfile`, `@IfBuildProperty`) are evaluated at build time ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)), so keep them on the same bean.

```java
@ApplicationScoped
@Unremovable                        // io.quarkus.arc.Unremovable
@Identifier("orderMapper")          // io.smallrye.common.annotation.Identifier
public class OrderMapper { }        // keep both after the move
```

A bean qualified only with `@Identifier` is a decision, not a rule: see the Ask First row in [SKILL.md](../SKILL.md).

## Resource signature keeps its thread model

Quarkus REST picks the thread from the method signature ([REST guide](https://quarkus.io/version/3.40/guides/rest)). Extract the body, not the signature.

```java
// before: blocking signature, worker thread
@GET @Path("/{id}")
public Order get(@RestPath String id) { /* 40 lines */ }

// after: same signature kind; the body delegates
@GET @Path("/{id}")
public Order get(@RestPath String id) { return orders.find(id); }
```

## Validation stays on the resource parameter

With `quarkus-hibernate-validator`, constraint failures on REST endpoint parameters return a bad request with a violations report; violations in service methods give 5xx unless `ConstraintViolationException` is mapped ([validation guide](https://quarkus.io/version/3.40/guides/validation)).

```java
@POST
public Response create(@Valid @NotNull Order order) { return orders.create(order); } // keep the constraints here
```

## Lambda handler name stays in sync

The Lambda handler is `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest`; the user handler is selected by `quarkus.lambda.handler`, a CDI name ([AWS Lambda guide](https://quarkus.io/guides/aws-lambda)). When splitting a handler, the class that keeps the CDI name stays the entry point and delegates.

```java
// illustrative handler shape (medium confidence, M6); only the CDI-name rule is from the guide
@Named("orderEvents")                              // CDI name
public class OrderEventsHandler implements RequestHandler<SQSEvent, Void> {
    @Inject OrderEventProcessor processor;         // new collaborator
    public Void handleRequest(SQSEvent e, Context c) { processor.process(e); return null; }
}
```

```properties
quarkus.lambda.handler=orderEvents
```

Scope of the example (medium confidence, M6): the whole snippet (`RequestHandler<SQSEvent, Void>`, the `@Named` handler bean, the collaborator) is illustrative and was not read from a page. Use it only to see that the name and the property move together; take the handler type and event types from your project.

## Index a new module

Beans in another Maven module are discovered only if that module has `beans.xml`, `META-INF/jandex.idx`, or the application sets `quarkus.index-dependency.<name>.group-id` and `.artifact-id` ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)).

```properties
quarkus.index-dependency.orders-core.group-id=com.acme
quarkus.index-dependency.orders-core.artifact-id=orders-core
```

See [package taxonomy](./package-taxonomy.md#moving-classes-between-packages-and-modules).

---

## Method patterns (team practice, unverified U1; outside the Always Do tier)

### Green baseline

Run the whole suite and require exit code 0 before the first edit. A red baseline makes it impossible to tell regressions from earlier failures. If it is red, fix the tests first; never comment them out.

```bash
# representative command, adapt to your build tool
./mvnw test
```

See the [JUnit skill](../../developing-quarkus-junit-v3-40/SKILL.md) for test artifacts.

### Test coupling

Before extracting, list what the tests depend on. These names must keep working, or the test moves with the logic:

- `@InjectMock` and `@InjectSpy` fields name a bean type and require a normal scope (medium confidence, L1; [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)).
- `@TestHTTPEndpoint(OrderResource.class)` binds a test to a resource class (medium confidence, L1; [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)).
- `QuarkusMock.installMockForType(mock, Type.class)` names a bean type (medium confidence, L1; [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)).
- Package-private constructors or methods called directly by unit tests.

### One smell at a time

Pick the single largest smell (long method, repeated scaffolding, magic-string classification, mixed concerns). Extract it, recompile, run the suite, then pick the next. Never batch several extractions into one unverified step. Steps in the [recipe](./refactor-recipe.md#steps).
