# Evaluation Scenarios — developing-oci-functions-java

## Scenario 1: Canonical — New Function with OCI SDK Client

```json
{
  "skills": ["developing-oci-functions-java"],
  "query": "Write a Java function that reads a JSON request containing an objectName, retrieves that object from OCI Object Storage, and returns its content as a string. Use best practices.",
  "expected_behavior": [
    "Declares ObjectStorageClient as an instance field (not a local variable in the handler)",
    "Initializes ObjectStorageClient in @FnConfiguration using ResourcePrincipalAuthenticationDetailsProvider — not API keys",
    "Accepts a typed POJO (e.g., ObjectRequest with objectName field) as handler parameter — not raw String",
    "Reads object via client.getObject() in the handler method, not in @FnConfiguration",
    "Logs to System.err (not System.out) for structured JSON logging",
    "Sets cmd in func.yaml as ClassName::methodName",
    "Does NOT initialize the SDK client inside the handler method (hot function anti-pattern)"
  ]
}
```

## Scenario 2: Edge Case — FDK 1.0.x to 1.1.x Migration

```json
{
  "skills": ["developing-oci-functions-java"],
  "query": "My function currently extends nothing and has a handleRequest(InputEvent input, OutputEvent.Emitter emitter) signature. I want to upgrade to FDK 1.1.11 and use the APIGatewayFunction typed abstraction. What must change?",
  "expected_behavior": [
    "Identifies that fn-events module is required — add fn-events and fn-events-testing Maven dependencies (not available in 1.0.x)",
    "Changes class to extend APIGatewayFunction<RequestType, ResponseType>",
    "Renames method from handleRequest to handler with the correct APIGatewayRequestEvent<Req> parameter",
    "Updates func.yaml cmd to reference ::handler (not ::handleRequest)",
    "Notes that return type changes to APIGatewayResponseEvent<ResponseType>",
    "Warns that mixing raw FDK handlers with fn-events abstract classes in the same function causes ClassLoader conflicts",
    "Does NOT keep the old handleRequest signature alongside the new handler — they cannot coexist"
  ]
}
```

## Scenario 3: Edge Case — Cold Start Optimization

```json
{
  "skills": ["developing-oci-functions-java"],
  "query": "My Java function has a 12-second cold start. It initializes three OCI SDK clients and fetches two Vault secrets on every invocation. How do I fix this?",
  "expected_behavior": [
    "Moves all OCI SDK client initialization (ObjectStorageClient, SecretsClient, etc.) to @FnConfiguration — runs once per container lifetime",
    "Fetches Vault secrets in @FnConfiguration and caches them as instance fields — secrets rarely change",
    "Notes that @FnConfiguration runs ONCE in the hot function model; subsequent warm invocations skip it entirely",
    "Estimates that moving SDK init from handler to @FnConfiguration reduces per-invocation overhead from 10-100x (cold start) to near-zero (warm)",
    "Recommends provisioned concurrency if sub-second cold start is required (ask-first decision)",
    "Does NOT suggest lazy init inside the handler as a solution (still pays init cost on first call per container)"
  ]
}
```

## Scenario 4: Edge Case — initError and Startup Failure Diagnosis

```json
{
  "skills": ["developing-oci-functions-java"],
  "query": "My function returns HTTP 502 immediately on every invocation with no useful error in OCI Logging. How do I diagnose an initError?",
  "expected_behavior": [
    "Identifies HTTP 502 with no handler log output as a signature of initError (FDK fails before handler is reached)",
    "Checks OCI Function application logs for FDK startup error messages (class loading, func.yaml cmd resolution)",
    "Verifies func.yaml cmd format: must be fully-qualified ClassName::methodName — a wrong method name is a common initError cause",
    "Checks that all dependency JARs are present in the Docker image (dependency:copy-dependencies Maven step)",
    "Checks @FnConfiguration for exceptions thrown during initialization (e.g., Vault secret not found, NullPointerException)",
    "Runs local docker test: fn start + fn invoke to reproduce and see container stderr output",
    "Does NOT assume the function logic is wrong without first ruling out initError"
  ]
}
```

## Scenario 5: Misuse Case — Mutable Shared State Between Invocations

```json
{
  "skills": ["developing-oci-functions-java"],
  "query": "I want to accumulate a running count of processed items across function invocations using a static counter field, then flush to a database every 100 items.",
  "expected_behavior": [
    "Flags this as a CRITICAL Never Do: mutable shared state between invocations is a hot function anti-pattern",
    "Explains that state leaks between different callers' requests since OCI Functions reuses the JVM for hot invocations",
    "Notes that state is also lost when the container is recycled (cold start), making the count unreliable",
    "Proposes stateless alternatives: use OCI Streaming (per-event processing) or an external counter (OCI Object Storage, database, or Redis) accessed within the handler",
    "For batching, recommends OCI Connector Hub (batches at the infrastructure layer, not in function state)",
    "Does NOT implement the static counter pattern even with synchronization (synchronized block does not fix cross-request leakage in serverless)"
  ]
}
```
