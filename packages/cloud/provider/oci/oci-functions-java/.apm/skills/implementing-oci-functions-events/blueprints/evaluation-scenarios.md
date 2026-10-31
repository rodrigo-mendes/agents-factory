# Evaluation Scenarios — implementing-oci-functions-events

## Scenario 1: Canonical — API Gateway Typed Handler

```json
{
  "skills": ["implementing-oci-functions-events"],
  "query": "Write a Java function that handles API Gateway POST requests, deserializes the body to an OrderRequest POJO, and returns an OrderResponse with a generated order ID. Use fn-events.",
  "expected_behavior": [
    "Extends APIGatewayFunction<OrderRequest, OrderResponse> (not a raw handler)",
    "Overrides handler(APIGatewayRequestEvent<OrderRequest> event) — NOT handleRequest",
    "Returns APIGatewayResponseEvent<OrderResponse> with statusCode and body",
    "Updates func.yaml cmd to ClassName::handler (not ::handleRequest)",
    "Adds fn-events Maven dependency (com.fnproject.fn:fn-events:1.1.x)",
    "Annotates OrderRequest with @JsonIgnoreProperties(ignoreUnknown = true)",
    "Does NOT manually parse the API Gateway JSON envelope (raw body extraction + JSON.parse)"
  ]
}
```

## Scenario 2: Edge Case — FDK 1.0.x Project Upgrade Required

```json
{
  "skills": ["implementing-oci-functions-events"],
  "query": "I tried to add fn-events to my project but the compiler can't find com.fnproject.events.APIGatewayFunction. My current FDK version is 1.0.186.",
  "expected_behavior": [
    "Identifies root cause: fn-events module does NOT exist in FDK 1.0.x — introduced only in 1.1.x",
    "Requires upgrading FDK from 1.0.186 to 1.1.11 (or latest 1.1.x) — not just adding the fn-events artifact",
    "Updates ALL FDK dependencies in pom.xml to 1.1.11: api, runtime, testing-core, testing-junit4, fn-events, fn-events-testing",
    "Verifies no mixed versions between FDK modules (all must be same 1.1.x version)",
    "Notes that the fn-events-testing artifact is also required for unit tests (APIGatewayTestFeature)",
    "Does NOT suggest adding only fn-events while keeping other FDK dependencies at 1.0.x (version mismatch causes ClassLoader failures)"
  ]
}
```

## Scenario 3: Edge Case — ConnectorHub Batch Partial Failure

```json
{
  "skills": ["implementing-oci-functions-events"],
  "query": "My ConnectorHubFunction processes a batch of LoggingData records. If one record fails processing, should the entire batch fail? What happens to the failed connector invocation?",
  "expected_behavior": [
    "Explains the batch semantics: ConnectorHubFunction.handler receives a ConnectorHubBatch<T> containing all records from one SCH invocation",
    "If handler throws a RuntimeException, the entire batch is marked as failed and SCH retries the batch",
    "Recommends implementing per-record try/catch: log individual failures and continue processing remaining records (partial processing)",
    "Identifies the misuse: fail-fast (throwing on first error) causes repeated SCH retries for a batch with one bad record — healthy records are never processed",
    "For dead-letter handling: write failed records to Object Storage or OCI Streaming within the handler, then complete successfully",
    "Does NOT recommend ignoring errors entirely (silent data loss) or always throwing on any error (retry storms)"
  ]
}
```

## Scenario 4: Edge Case — func.yaml cmd Entry Point Mismatch

```json
{
  "skills": ["implementing-oci-functions-events"],
  "query": "My fn-events function deploys successfully but every invocation returns HTTP 502 immediately. The logs show 'method not found: handleRequest'. What is wrong?",
  "expected_behavior": [
    "Identifies the root cause: func.yaml cmd still points to ::handleRequest after migrating to fn-events (which uses ::handler)",
    "Correct cmd format: com.example.MyFunction::handler",
    "Verifies with: grep 'cmd:' func.yaml",
    "Explains that APIGatewayFunction, ConnectorHubFunction, and NotificationFunction all override handler(), not handleRequest()",
    "Rebuilds and redeploys after the func.yaml fix: mvn clean package + fn deploy --app <app-name>",
    "Does NOT accept the 502 as a code logic issue without first verifying the func.yaml entry point"
  ]
}
```

## Scenario 5: Misuse Case — Raw Manual API Gateway Parsing

```json
{
  "skills": ["implementing-oci-functions-events"],
  "query": "Instead of using APIGatewayFunction, I want to parse the API Gateway JSON envelope manually in handleRequest(InputEvent) to extract the body and query parameters myself. This gives me more control.",
  "expected_behavior": [
    "Flags this as a Never Do anti-pattern: manual API Gateway JSON envelope parsing is brittle and error-prone",
    "The raw envelope structure (requestType, requestContext, isBase64Encoded, etc.) is internal to the API Gateway integration and can change",
    "APIGatewayFunction provides type-safe access to body (auto-deserialized), queryParameters, headers, and pathParameters without manual parsing",
    "Correctly identifies the only valid exception: custom binary protocols or non-JSON bodies where automatic POJO deserialization is not applicable — use InputEvent directly for those",
    "Does NOT implement the raw parsing pattern as the default approach",
    "Offers APIGatewayFunction as the correct typed abstraction for standard HTTP JSON APIs"
  ]
}
```
