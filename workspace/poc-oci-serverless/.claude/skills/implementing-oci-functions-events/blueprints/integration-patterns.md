## Integration Patterns

### fn-events ↔ OCI API Gateway

**Pattern**: Synchronous HTTP request/response with typed abstractions.

```java
// API Gateway → Function (fn-events v1.1.x)
// func.yaml cmd: com.example.Function::handler
public class Function extends APIGatewayFunction<OrderRequest, OrderResponse> {
    @Override
    public APIGatewayResponseEvent<OrderResponse> handler(
            APIGatewayRequestEvent<OrderRequest> requestEvent) {
        // Query params, headers, method, body — all typed
        return new APIGatewayResponseEvent.Builder<OrderResponse>()
            .statusCode(HttpStatus.SC_OK)
            .body(new OrderResponse())
            .build();
    }
}
```

**Required Configuration**: API Gateway deployment route must point to the function with `type: ORACLE_FUNCTIONS_BACKEND`.

**Source**: [API Gateway + Functions](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingfunctionsbackend.htm)

---

### fn-events ↔ OCI Service Connector Hub (Streaming)

**Pattern**: Async batch processing of Streaming messages with auto base64 decode.

```java
// SCH (Streaming source) → Function (fn-events v1.1.x)
public class StreamProcessorFunction extends ConnectorHubFunction<StreamingData<OrderEvent>> {

    @Override
    public void handler(ConnectorHubBatch<StreamingData<OrderEvent>> batch) {
        for (StreamingData<OrderEvent> stream : batch.getBatch()) {
            OrderEvent event = stream.getValue();    // auto base64 decoded
            String streamName = stream.getStream();
            String partition = stream.getPartition();
            String offset = stream.getOffset();
            process(event);
        }
    }
}
```

**Required Configuration**: Service Connector Hub connector with Streaming source and Functions target.

**Source**: [SCH Streaming Source](https://docs.oracle.com/en-us/iaas/Content/connector-hub/create-service-connector-streaming-source.htm)

---

### fn-events ↔ OCI Notifications

**Pattern**: Async single message processing from topic subscription.

```java
// OCI Notifications → Function (fn-events v1.1.x)
public class NotificationHandler extends NotificationFunction<AlertPayload> {
    @Override
    public void handler(NotificationMessage<AlertPayload> content) {
        AlertPayload payload = content.getBody();
        // Headers available via content.getHeaders()
        process(payload);
    }
}
```

**Required Configuration**: OCI Notification topic with Function subscription.

**Source**: [OCI Notifications](https://docs.oracle.com/en-us/iaas/Content/Notification/Tasks/create-subscription-function.htm)

---

### fn-events ↔ OCI Service Connector Hub (Monitoring)

**Pattern**: Async batch processing of OCI Monitoring metrics.

```java
// SCH (Monitoring source) → Function (fn-events v1.1.x)
public class MetricAlertFunction extends ConnectorHubFunction<MetricData> {

    private double threshold;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        this.threshold = Double.parseDouble(
            ctx.getConfigurationByKey("CPU_THRESHOLD").orElse("90.0"));
    }

    @Override
    public void handler(ConnectorHubBatch<MetricData> batch) {
        for (MetricData metric : batch.getBatch()) {
            if (metric.getDatapoints().stream()
                    .anyMatch(dp -> dp.getValue() > threshold)) {
                sendAlert(metric);
            }
        }
    }
}
```

**Source**: [SCH Monitoring Source](https://docs.oracle.com/en-us/iaas/Content/connector-hub/create-service-connector-monitoring-source.htm)

---

