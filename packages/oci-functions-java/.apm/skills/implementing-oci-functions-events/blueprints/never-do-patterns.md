### 🚫 Never Do

**Anti-Pattern**: Using raw `handleRequest` for API Gateway backend

```java
// 🚫 WRONG: Manual parsing of API Gateway envelope (fragile, undocumented)
public class Function {
    public String handleRequest(String rawJson) {
        JsonNode root = mapper.readTree(rawJson);
        String body = root.get("body").asText();
        String method = root.get("httpMethod").asText();
        return "{\"statusCode\": 200, \"body\": \"ok\"}";
    }
}

// ✅ CORRECT: Use APIGatewayFunction abstraction (fn-events v1.1.x)
public class Function extends APIGatewayFunction<RequestDto, ResponseDto> {
    @Override
    public APIGatewayResponseEvent<ResponseDto> handler(
            APIGatewayRequestEvent<RequestDto> requestEvent) {
        RequestDto body = requestEvent.getBody();       // type-safe
        String method = requestEvent.getMethod();        // structured access
        return new APIGatewayResponseEvent.Builder<ResponseDto>()
            .statusCode(200)
            .body(new ResponseDto("ok"))
            .build();
    }
}
```

**Why it is prohibited**: The API Gateway JSON envelope is an internal structure that can change between versions. Manual parsing is brittle and lacks type safety.
**Actual impact**: Code breaks when gateway envelope format changes; no query param parsing; no status code control.
**Source**: [API Gateway Example](https://github.com/fnproject/fdk-java/blob/master/examples/apigateway-event/README.md)

---

**Anti-Pattern**: Manual base64 decode for Streaming events

```java
// 🚫 WRONG: Double decoding — StreamingData already decodes base64 (fn-events v1.1.x)
@Override
public void handler(ConnectorHubBatch<StreamingData<String>> batch) {
    for (StreamingData<String> stream : batch.getBatch()) {
        // getValue() already returns decoded value!
        String value = new String(Base64.getDecoder().decode(stream.getValue()));
    }
}

// ✅ CORRECT: Value is already decoded by StreamingData<T>
@Override
public void handler(ConnectorHubBatch<StreamingData<Employee>> batch) {
    for (StreamingData<Employee> stream : batch.getBatch()) {
        Employee value = stream.getValue(); // already decoded from base64
        process(value);
    }
}
```

**Why it is prohibited**: `StreamingData<T>` automatically decodes base64 and deserializes to the generic type. Manual decoding corrupts data (double decode).
**Actual impact**: Corrupted data, `IllegalArgumentException` on non-base64 decoded content.
**Source**: [Connector Hub Streaming Example](https://github.com/fnproject/fdk-java/blob/master/examples/connectorhub-streaming/README.md)

---

**Anti-Pattern**: Ignoring batch semantics in ConnectorHubFunction

```java
// 🚫 WRONG: Processing only first item — rest of batch silently lost
@Override
public void handler(ConnectorHubBatch<LoggingData> batch) {
    LoggingData first = batch.getBatch().get(0); // ignores rest of batch!
    processLog(first);
}

// ✅ CORRECT: Iterate all items in batch
@Override
public void handler(ConnectorHubBatch<LoggingData> batch) {
    for (LoggingData log : batch.getBatch()) {
        processLog(log);
    }
}
```

**Why it is prohibited**: SCH configures batch size in Batch Settings. Ignoring items in the batch causes silent data loss — events are acknowledged but never processed.
**Actual impact**: Silent data loss at scale. Events permanently lost (SCH considers them delivered).
**Source**: [Connector Hub Logging Example](https://github.com/fnproject/fdk-java/blob/master/examples/connectorhub-logging/README.md)

---

**Anti-Pattern**: Returning values from void handlers

```java
// 🚫 WRONG: ConnectorHubFunction.handler() must be void — COMPILE ERROR
public class Function extends ConnectorHubFunction<LoggingData> {
    @Override
    public String handler(ConnectorHubBatch<LoggingData> batch) {
        return "processed"; // DOES NOT COMPILE
    }
}

// ✅ CORRECT: Void handler, signal errors via RuntimeException
public class Function extends ConnectorHubFunction<LoggingData> {
    @Override
    public void handler(ConnectorHubBatch<LoggingData> batch) {
        for (LoggingData log : batch.getBatch()) {
            processLog(log);
        }
        // success = implicit 200
    }
}
```

**Why it is prohibited**: `ConnectorHubFunction.handler()` and `NotificationFunction.handler()` are defined as `void`. There is no consumer expecting a response.
**Actual impact**: Compilation error — project won't build.
**Source**: [Connector Hub Logging Example](https://github.com/fnproject/fdk-java/blob/master/examples/connectorhub-logging/README.md)

---

**Anti-Pattern**: Mixing fn-events abstractions with raw FDK handlers

```java
// 🚫 WRONG: Extending APIGatewayFunction but also declaring handleRequest
public class Function extends APIGatewayFunction<Req, Res> {
    // This won't be called — APIGatewayFunction uses handler() method
    public String handleRequest(String input) {
        return "this is dead code";
    }

    @Override
    public APIGatewayResponseEvent<Res> handler(APIGatewayRequestEvent<Req> req) {
        // This is the actual entry point
    }
}

// ✅ CORRECT: Use ONLY the handler method defined by the abstract class
public class Function extends APIGatewayFunction<Req, Res> {
    @Override
    public APIGatewayResponseEvent<Res> handler(APIGatewayRequestEvent<Req> req) {
        return new APIGatewayResponseEvent.Builder<Res>()
            .statusCode(200)
            .body(processRequest(req.getBody()))
            .build();
    }
}
```

**Why it is prohibited**: The abstract classes define the contract. Extra `handleRequest` methods are ignored and cause confusion. `func.yaml` must point to `handler`, not `handleRequest`.
**Actual impact**: Dead code confusion; func.yaml misconfiguration leads to invocation failures.
**Source**: [API Gateway Example](https://github.com/fnproject/fdk-java/blob/master/examples/apigateway-event/README.md)

---

**Anti-Pattern**: Sending non-JSON Queue messages

```java
// 🚫 WRONG: Plain string without JSON encoding
queueClient.putMessage("plain text message"); // NOT valid JSON

// ✅ CORRECT: Valid JSON string (quoted) or structured JSON
queueClient.putMessage("\"plain text message\""); // quoted = valid JSON string
queueClient.putMessage("{\"name\": \"John\", \"id\": 123}"); // structured JSON
```

**Why it is prohibited**: Connector Hub forwards messages directly to the Function. Messages must be valid JSON for Jackson deserialization to work.
**Actual impact**: Function fails with `JsonParseException` at runtime.
**Source**: [Connector Hub Queue Example](https://github.com/fnproject/fdk-java/tree/master/examples/connectorhub-queue)

---

