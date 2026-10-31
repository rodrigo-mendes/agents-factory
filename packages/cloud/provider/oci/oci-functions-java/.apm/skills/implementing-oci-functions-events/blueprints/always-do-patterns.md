### ✅ Always Do

**fn-events Maven Dependencies**: The fn-events module is separate from the FDK core. It must be explicitly declared in `pom.xml` with version aligned to the FDK.

```xml
<!-- ✅ CORRECT: fn-events v1.1.11 dependencies (must match FDK version) -->
<properties>
    <fdk.version>1.1.11</fdk.version>
</properties>

<dependencies>
    <!-- Runtime: typed event abstractions -->
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>fn-events</artifactId>
        <version>${fdk.version}</version>
    </dependency>

    <!-- Test: event-specific test features -->
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>fn-events-testing</artifactId>
        <version>${fdk.version}</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

**Why it is mandatory**: fn-events is an optional module — without explicit dependency, abstract classes like `APIGatewayFunction` are not on the classpath.
**Failure if omitted**: `ClassNotFoundException` at runtime.
**Source**: [fn-events README](https://github.com/fnproject/fdk-java/blob/master/fn-events/README.md)

---

**func.yaml Entry Point — `::handler`**: When using fn-events abstract classes, the `cmd` in `func.yaml` must point to the `handler` method, not `handleRequest`.

```yaml
# ✅ CORRECT: func.yaml for fn-events v1.1.x abstract class
schema_version: 20180708
name: api-gateway-fn
version: 0.0.1
runtime: java
build_image: fnproject/fn-java-fdk-build:jdk17-latest
run_image: fnproject/fn-java-fdk:jre17-latest
cmd: com.example.Function::handler
memory: 256
timeout: 30
```

**Why it is mandatory**: The abstract classes (`APIGatewayFunction`, `ConnectorHubFunction`, `NotificationFunction`) define `handler()` as the entry point — not `handleRequest`.
**Failure if omitted**: Function invocation fails silently or routes to wrong method.
**Source**: [API Gateway Example](https://github.com/fnproject/fdk-java/blob/master/examples/apigateway-event/README.md)

---

**APIGatewayFunction for Typed HTTP Request/Response**: When a function is an API Gateway backend, extend `APIGatewayFunction<Req, Res>` for type-safe request/response with access to query params, headers, HTTP method, and status code control.

```java
// ✅ CORRECT: Typed API Gateway function (fn-events v1.1.x)
import com.fnproject.events.APIGatewayFunction;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.Headers;
import com.fnproject.fn.api.RuntimeContext;
import org.apache.http.HttpStatus;
import java.util.Optional;

public class OrderFunction extends APIGatewayFunction<OrderRequest, OrderResponse> {

    private OrderService orderService;

    // @FnConfiguration works with fn-events abstract classes
    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        String dbUrl = ctx.getConfigurationByKey("DB_URL").orElseThrow();
        this.orderService = new OrderService(dbUrl);
    }

    @Override
    public APIGatewayResponseEvent<OrderResponse> handler(
            APIGatewayRequestEvent<OrderRequest> requestEvent) {

        String method = requestEvent.getMethod();
        Optional<String> orderId = requestEvent.getQueryParameters().get("id");
        OrderRequest body = requestEvent.getBody(); // type-safe deserialization

        try {
            OrderResponse response;
            int statusCode;

            switch (method) {
                case "GET":
                    response = orderService.getOrder(orderId.orElseThrow());
                    statusCode = HttpStatus.SC_OK;
                    break;
                case "POST":
                    response = orderService.createOrder(body);
                    statusCode = HttpStatus.SC_CREATED;
                    break;
                default:
                    response = new OrderResponse("Method not allowed");
                    statusCode = HttpStatus.SC_METHOD_NOT_ALLOWED;
            }

            return new APIGatewayResponseEvent.Builder<OrderResponse>()
                .statusCode(statusCode)
                .headers(Headers.emptyHeaders()
                    .addHeader("Content-Type", "application/json"))
                .body(response)
                .build();

        } catch (NotFoundException e) {
            return new APIGatewayResponseEvent.Builder<OrderResponse>()
                .statusCode(HttpStatus.SC_NOT_FOUND)
                .body(new OrderResponse(e.getMessage()))
                .build();
        }
        // Unexpected exceptions → RuntimeException → 502
    }
}
```

**Why it is mandatory**: `APIGatewayFunction` encapsulates parsing, validation, and serialization of the API Gateway JSON envelope with type safety. Manual parsing is brittle and undocumented.
**Failure if omitted**: Fragile code that breaks when gateway envelope format changes; no type safety; no query param parsing.
**Source**: [API Gateway Example](https://github.com/fnproject/fdk-java/blob/master/examples/apigateway-event/README.md)

---

**ConnectorHubFunction for Batch Processing**: Service Connector Hub sends events in batches. `ConnectorHubFunction<T>` receives `ConnectorHubBatch<T>` with a typed list of events. The handler is `void` — success is implicit 200, failure is via `RuntimeException` (502 → SCH retry).

```java
// ✅ CORRECT: ConnectorHub batch processing (fn-events v1.1.x)
import com.fnproject.events.ConnectorHubFunction;
import com.fnproject.events.input.ConnectorHubBatch;
import com.fnproject.events.input.sch.LoggingData;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;

public class LogProcessorFunction extends ConnectorHubFunction<LoggingData> {

    private LogService logService;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        this.logService = new LogService(ctx);
    }

    @Override
    public void handler(ConnectorHubBatch<LoggingData> batch) {
        // ✅ MUST iterate all items — ignoring items = silent data loss
        for (LoggingData log : batch.getBatch()) {
            logService.processLog(log);
        }
        // implicit 200 on success
        // throw RuntimeException for 502 + SCH retry
    }
}
```

**Why it is mandatory**: SCH configures batch size in Batch Settings. Every item in the batch must be processed.
**Failure if omitted**: Silent data loss if batch items are skipped; compile error if handler returns a value.
**Source**: [Connector Hub Logging Example](https://github.com/fnproject/fdk-java/blob/master/examples/connectorhub-logging/README.md)

---

**Error Signaling via RuntimeException**: `ConnectorHubFunction` and `NotificationFunction` have `void` handlers. The only way to signal failure is `throw RuntimeException`, which results in HTTP 502. SCH applies automatic retry policy.

```java
// ✅ CORRECT: Error signaling in void handlers (fn-events v1.1.x)
@Override
public void handler(ConnectorHubBatch<LoggingData> batch) {
    try {
        for (LoggingData log : batch.getBatch()) {
            processLog(log);
        }
    } catch (Exception e) {
        // 502 triggers SCH retry policy
        throw new RuntimeException("Failed to process batch", e);
    }
}
```

**Why it is mandatory**: void handlers have no return channel. RuntimeException → 502 is the only mechanism for SCH/Notifications to detect failure and retry.
**Failure if omitted**: Errors are swallowed silently; SCH assumes success (200) and does not retry.
**Source**: [SCH Retry Policy](https://docs.oracle.com/en-us/iaas/Content/connector-hub/overview.htm#deactivate)

---

**Test Features for Each Event Type**: Each event type has a corresponding test feature that integrates with `FnTestingRule`.

```java
// ✅ CORRECT: Test setup with fn-events-testing v1.1.x
import com.fnproject.events.testing.APIGatewayTestFeature;
import com.fnproject.events.testing.ConnectorHubTestFeature;
import com.fnproject.events.testing.NotificationTestFeature;
import com.fnproject.fn.testing.FnTestingRule;
import org.junit.Rule;
import org.junit.Test;

public class FunctionTest {
    @Rule
    public FnTestingRule fn = FnTestingRule.createDefault();

    // Use the feature matching your function type:
    private final APIGatewayTestFeature apiGw = APIGatewayTestFeature.createDefault(fn);
    // OR
    private final ConnectorHubTestFeature sch = ConnectorHubTestFeature.createDefault(fn);
    // OR
    private final NotificationTestFeature notif = NotificationTestFeature.createDefault(fn);

    @Test
    public void testApiGatewayFunction() {
        fn.setConfig("DB_URL", "jdbc:h2:mem:test");

        // Build and enqueue a typed event
        apiGw.givenEvent(mockRequestEvent).enqueue();
        fn.thenRun(OrderFunction.class, "handler");

        // Extract typed result
        APIGatewayResponseEvent<OrderResponse> response = apiGw.getResult(OrderResponse.class);
        assertEquals(Integer.valueOf(201), response.getStatus());
    }
}
```

**Why it is mandatory**: Test features provide the correct event envelope structure. Without them, tests must manually construct internal JSON envelopes.
**Failure if omitted**: Tests don't match runtime behavior; false positives.
**Source**: [fn-events-testing module](https://github.com/fnproject/fdk-java/tree/master/fn-events-testing)

---

