# Evaluation Scenarios — testing-oci-functions-java

## Scenario 1: Unit Test for POJO Handler

```json
{
  "skills": ["testing-oci-functions-java"],
  "query": "Write a unit test for my OrderFunction that takes an OrderRequest POJO and returns OrderResponse. The function uses @FnConfiguration to read BUCKET_NAME config.",
  "expected_behavior": [
    "Uses FnTestingRule with @Rule annotation",
    "Calls testing.setConfig('BUCKET_NAME', ...) before enqueue",
    "Sets content-type: application/json header on the event",
    "Asserts result via testing.getOnlyResult()",
    "Does NOT initialize real OCI SDK clients"
  ]
}
```

## Scenario 2: API Gateway Function Test

```json
{
  "skills": ["testing-oci-functions-java"],
  "query": "Write tests for my UserApiFunction that extends APIGatewayFunction<UserRequest, UserResponse>. I need to test GET with query params and POST with body.",
  "expected_behavior": [
    "Uses APIGatewayTestFeature.createDefault(fn)",
    "Mocks APIGatewayRequestEvent with Mockito",
    "Sets method, body, queryParameters on mock event",
    "Uses apiGw.givenEvent(event).enqueue() pattern",
    "Asserts response status code and typed body via apiGw.getResult()",
    "Does NOT manually construct API Gateway JSON envelope"
  ]
}
```

## Scenario 3: Function with OCI Object Storage Integration

```json
{
  "skills": ["testing-oci-functions-java"],
  "query": "My FileProcessorFunction reads from Object Storage and writes results back. How do I test it without real OCI access?",
  "expected_behavior": [
    "Creates MockOciClients class with static ObjectStorageClient field",
    "Uses testing.addSharedClass(MockOciClients.class) — NOT the function class",
    "Mocks getObject and putObject with Mockito when/thenReturn",
    "Function uses Class.forName pattern in @FnConfiguration for mock detection",
    "Tests verify mock interactions with verify()",
    "Includes BmcException error path test (404, 429)"
  ]
}
```

## Scenario 4: Hot Function State Leak Detection

```json
{
  "skills": ["testing-oci-functions-java"],
  "query": "I suspect my function has a state leak between invocations. How do I write a test to catch it?",
  "expected_behavior": [
    "Enqueues multiple events (3+) in single test",
    "Calls testing.thenRun() once after all enqueues",
    "Uses testing.getResults() to check all results independently",
    "Verifies no state accumulation between invocations",
    "May use .enqueue(10) shorthand for repeated invocations"
  ]
}
```

## Scenario 5: ConnectorHub/SCH Function Test

```json
{
  "skills": ["testing-oci-functions-java"],
  "query": "Write a test for my LogProcessor that extends ConnectorHubFunction<LoggingData>. It has a void handler.",
  "expected_behavior": [
    "Uses FnTestingRule with JSON batch payload",
    "Sets content-type: application/json",
    "For success: asserts result status 200 (implicit success for void handler)",
    "For failure: documents that RuntimeException produces 502 status",
    "Does NOT use APIGatewayTestFeature for SCH functions"
  ]
}
```
