# Package taxonomy and thin entry points

Back to [SKILL.md](../SKILL.md). The shape uses neutral names. It is a team convention, not a Quarkus requirement; the Quarkus-specific hazards are in the last section and carry sources.

## Layout

| Package | Holds | Example |
|---|---|---|
| (root) | The entry class: REST resource or Lambda handler. Never inside a sub-package | `OrderResource`, `OrderEventsHandler` |
| `web/` | Response building and error to HTTP mapping | `ErrorMapper`, `ResponseFactory` |
| `handler/` | One class per use-case flow, called by the entry class | `CreateOrderFlow`, `ProcessOrderEvent` |
| `client/` | External I/O wrappers (AWS SDK clients, REST clients), retry and failure wrapping isolated here | `OrderQueue`, `PartnerGateway` |
| `transform/` | Mapping and marshalling (JSON, model, DTO) | `OrderMapper` |
| `obs/` | Observability (logging helper, metrics, tracing support) | `TracedCall` |

`handler/` means a use-case flow, not the Lambda handler class. The Lambda handler and the REST resource stay at the package root and delegate.

## Thin entry points

An entry class does four things only: read the request or event, validate at the boundary, call one flow, build the response. Business logic lives in collaborators.

```java
@Path("/orders")
public class OrderResource {
    @Inject CreateOrderFlow createOrder;                       // handler/

    @POST
    public RestResponse<OrderDto> create(@Valid @NotNull Order order) {
        return RestResponse.status(Status.CREATED, createOrder.run(order));
    }
}
```

The same shape applies to a Lambda handler: the class that owns the CDI name parses the event and calls a processor in `handler/` (see [patterns](./always-do-patterns.md#lambda-handler-name-stays-in-sync)).

## Test layout

Mirror the main packages in `src/test`. Move a unit test to the class that now owns the logic; keep one test on the entry class that proves the end-to-end behaviour did not change.

## Moving classes between packages and modules

- **Same module:** moving a class to another package keeps discovery; the class still needs its scope ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). Update `@TestHTTPEndpoint`, `@InjectMock` and `quarkus.lambda.handler` references that name the class or its CDI name ([AWS Lambda guide](https://quarkus.io/guides/aws-lambda)).
- **Another module:** needs `beans.xml`, `META-INF/jandex.idx` or `quarkus.index-dependency.<name>.*`, otherwise its beans are not discovered ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). Splitting a module is an Ask First decision.
- **Package-private members:** an `@Inject` field or a method in `handler/` that was package-private to the old class may no longer be reachable after the move; widen only as needed. Package-private rather than private injection members is recommended for native builds (medium confidence, M1).
- **Tests of the moved class:** `@InjectMock` needs a normal-scoped bean ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing)); a new collaborator that tests will mock gets `@ApplicationScoped`.
- **Camel projects:** a route builder keeps its scope rule: `@ApplicationScoped` only when it uses `@Inject` or `@ConfigProperty` ([Camel Quarkus CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)). See the [ArC skill](../../developing-quarkus-arc-v3-40/SKILL.md).
