# Before / after examples

Back to [SKILL.md](../SKILL.md). Illustrative shapes of one order flow. The AWS client code (`SqsClient` calls, the `OrderQueue` wrapper) and the resource body are illustrative, not read from a page (medium confidence, M6); the Quarkus rules they demonstrate carry their own sources. Neutral package names: [taxonomy](./package-taxonomy.md).

## Contents

- [Example 1: fat resource to thin resource plus service](#example-1-fat-resource-to-thin-resource-plus-service)
- [Example 2: AWS client wrapper with the same log text and failure mapping](#example-2-aws-client-wrapper-with-the-same-log-text-and-failure-mapping)
- [Example 3: duplicated scaffolding to one helper](#example-3-duplicated-scaffolding-to-one-helper)
- [What stayed identical in all three](#what-stayed-identical-in-all-three)

## Example 1: fat resource to thin resource plus service

Before: one 60-line method validates, maps, calls the queue and builds the error response.

```java
@Path("/orders")
public class OrderResource {
    @Inject SqsClient sqs;
    @ConfigProperty(name = "orders.queue-url") String queueUrl;

    @POST
    public RestResponse<OrderDto> create(@Valid @NotNull Order order) {
        // 1. map
        OrderDto dto = new OrderDto(order.id(), order.total());
        // 2. send
        try {
            sqs.sendMessage(r -> r.queueUrl(queueUrl).messageBody(dto.toJson()));
        } catch (RuntimeException e) {
            LOG.errorf("enqueue failed for %s: %s", order.id(), e.getMessage());
            return RestResponse.status(Status.BAD_GATEWAY, null);
        }
        return RestResponse.status(Status.CREATED, dto);
    }
}
```

After: the resource keeps the blocking signature, the `@Valid` parameter and the status codes; the steps move to collaborators.

```java
@Path("/orders")
public class OrderResource {
    @Inject CreateOrderFlow createOrder;                     // handler/

    @POST
    public RestResponse<OrderDto> create(@Valid @NotNull Order order) {
        return createOrder.run(order);
    }
}

@ApplicationScoped                                           // injected: needs a scope
public class CreateOrderFlow {
    @Inject OrderMapper mapper;                              // transform/
    @Inject OrderQueue queue;                                // client/

    public RestResponse<OrderDto> run(Order order) {
        OrderDto dto = mapper.toDto(order);
        return queue.enqueue(order.id(), dto)
                ? RestResponse.status(Status.CREATED, dto)
                : RestResponse.status(Status.BAD_GATEWAY, null);   // same status as before
    }
}
```

Unchanged on purpose: blocking return type ([REST guide](https://quarkus.io/version/3.40/guides/rest)), `@Valid` on the parameter ([validation guide](https://quarkus.io/version/3.40/guides/validation)), the 201 and 502 codes. Injection members are package-private, not private (medium confidence, M1).

## Example 2: AWS client wrapper with the same log text and failure mapping

```java
@ApplicationScoped
public class OrderQueue {                                    // client/
    private static final Logger LOG = Logger.getLogger(OrderQueue.class);
    @Inject SqsClient sqs;
    @ConfigProperty(name = "orders.queue-url") String queueUrl;

    public boolean enqueue(String orderId, OrderDto dto) {
        try {
            sqs.sendMessage(r -> r.queueUrl(queueUrl).messageBody(dto.toJson()));
            return true;
        } catch (RuntimeException e) {
            LOG.errorf("enqueue failed for %s: %s", orderId, e.getMessage());   // text copied verbatim
            return false;
        }
    }
}
```

Checks for this step: the log text and level equal the original; the exception is still caught at the same point; `OrderQueue` has a scope because `CreateOrderFlow` injects it ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)); a test that used `@InjectMock SqsClient` still targets the same bean type.

## Example 3: duplicated scaffolding to one helper

Before: two methods repeat "log, call, wrap". After: one private method; each caller passes its own text so messages stay identical.

```java
private <T> T traced(String name, Supplier<T> call) {
    LOG.debugf("start %s", name);
    try { return call.get(); }
    finally { LOG.debugf("end %s", name); }
}
```

If the original logged at `info`, the helper logs at `info`; matching level and text is part of parity (see [recipe](./refactor-recipe.md#dry-with-exception-parity)).

## What stayed identical in all three

| Item | Where verified |
|---|---|
| Status codes 201 and 502 | resource test via REST Assured |
| `@Valid` on the endpoint parameter | a test posting an invalid body expects 400 |
| Log texts and levels | diff of the strings |
| Side-effect order: map, then send | read the flow |
| CDI names, scopes, markers | diff of annotations |
