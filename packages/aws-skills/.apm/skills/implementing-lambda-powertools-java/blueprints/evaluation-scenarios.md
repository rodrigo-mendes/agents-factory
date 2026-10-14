# Evaluation Scenarios — implementing-lambda-powertools-java

Skill under test: `implementing-lambda-powertools-java`
Version context: AWS Lambda Powertools for Java v2.10.0

---

## Scenario 1 — Canonical: Full Observability Triad on a REST API Handler

```json
{
  "skills": ["implementing-lambda-powertools-java"],
  "query": "I'm building a Java 21 Lambda function for a booking API endpoint (POST /bookings). It uses API Gateway REST API. Add structured logging, X-Ray tracing, and custom metrics to the handler class.",
  "expected_behavior": [
    "Adds powertools-logging-log4j:2.10.0 (or logback) + powertools-tracing:2.10.0 + powertools-metrics:2.10.0 dependencies",
    "Annotates handler with @Logging(correlationIdPath = CorrelationIdPaths.API_GATEWAY_REST, clearState = true)",
    "Annotates handler with @Tracing",
    "Annotates handler with @FlushMetrics(namespace = 'AppNamespace', service = 'booking', captureColdStart = true)",
    "Configures dev.aspectj:aspectj-maven-plugin with all three modules as aspectLibraries (NOT org.codehaus.mojo)",
    "Sets POWERTOOLS_SERVICE_NAME environment variable instruction",
    "Does NOT use System.out.println or unstructured logging",
    "Emits at least one business metric via metrics.addMetric() using MetricUnit (not Unit)",
    "Does NOT use v1 @Metrics annotation or MetricsUtils"
  ]
}
```

---

## Scenario 2 — Canonical: Idempotent Payment Handler with DynamoDB

```json
{
  "skills": ["implementing-lambda-powertools-java"],
  "query": "My POST /payments Lambda handler must be idempotent because API Gateway clients retry on timeout. The event is an API Gateway REST event with a JSON body containing paymentId and amount. Show me how to configure Powertools Idempotency.",
  "expected_behavior": [
    "Adds powertools-idempotency-dynamodb:2.10.0 runtime dependency and powertools-idempotency-core as aspectLibrary",
    "Initializes Idempotency.config().withPersistenceStore(DynamoDBPersistenceStore.builder()...) in the class CONSTRUCTOR (not in handleRequest)",
    "Annotates handler with @Idempotent",
    "Uses withEventKeyJMESPath(\"powertools_json(body)\") to extract idempotency key from request body",
    "Instructs enabling DynamoDB TTL on the 'expiration' attribute with TTL >= client retry window",
    "Specifies PAY_PER_REQUEST capacity mode for the idempotency DynamoDB table",
    "Does NOT initialize Idempotency.config() inside handleRequest() method",
    "Does NOT use a shared idempotency table across multiple Lambda functions (one per mutating endpoint)"
  ]
}
```

---

## Scenario 3 — Canonical: SQS Batch Processing with Partial Failure Handling

```json
{
  "skills": ["implementing-lambda-powertools-java"],
  "query": "I have an SQS-triggered Lambda that processes a batch of order records. If one record fails, I don't want the entire batch requeued. Show me the correct powertools-batch setup for Java 21.",
  "expected_behavior": [
    "Instructs enabling ReportBatchItemFailures on the SQS event source mapping in SAM/CDK",
    "Adds powertools-batch:2.10.0 dependency",
    "Uses BatchMessageHandlerBuilder.withSqsBatchHandler() — does NOT use removed @SqsBatch annotation",
    "Calls processBatch(event, context) for standard processing",
    "Shows processBatchInParallel(event, context, Executors.newVirtualThreadPerTaskExecutor()) for I/O-bound records (Java 21)",
    "Warns against using parallel processing on FIFO queues (UnsupportedOperationException)",
    "Recommends attaching a DLQ to the SQS queue for records that exhaust retries"
  ]
}
```

---

## Scenario 4 — Edge Case: SnapStart Compatibility Audit

```json
{
  "skills": ["implementing-lambda-powertools-java"],
  "query": "I'm enabling SnapStart on our Java 21 Lambda functions. What do I need to change in my Powertools initialization code to make everything SnapStart-compatible?",
  "expected_behavior": [
    "Identifies that Powertools utility initialization must be in the class constructor, not in handleRequest()",
    "Calls out that Idempotency.config().configure() must be in the constructor",
    "Calls out that Parameters providers (SSMProvider, SecretsProvider) must be instantiated in the constructor",
    "Calls out TracingUtils.init() in the constructor for tracing priming",
    "Calls out ValidationConfig.get() in a static initializer for schema cache priming",
    "CRITICAL: warns that UUID.randomUUID(), new Random(), nonces, and any unique IDs must be generated inside handleRequest() — NOT in static initializers or constructors",
    "Mentions setting networkaddress.cache.ttl=0 to prevent stale DNS after snapshot restore",
    "Clarifies SnapStart is only available on published function versions/aliases, NOT on $LATEST"
  ]
}
```

---

## Scenario 5 — Edge Case: Functional API for GraalVM Native Image Build

```json
{
  "skills": ["implementing-lambda-powertools-java"],
  "query": "We're building a Lambda function with GraalVM native image compilation. We want to use Powertools Logging and Metrics but can't use the AspectJ annotation API. What's the alternative?",
  "expected_behavior": [
    "Identifies the Functional API (available from v2.7.0+) as the correct choice for GraalVM native",
    "Explains that the Functional API wraps handler logic programmatically without requiring AspectJ compile-time weaving",
    "Confirms 100% feature parity between Functional API and Annotation API as of v2.7.0",
    "Does NOT instruct adding dev.aspectj:aspectj-maven-plugin for the Functional API approach",
    "Mentions Functional API is also preferred for Kotlin and Lombok-heavy codebases",
    "Does NOT suggest runtime weaving (AspectJ LTW) or Spring AOP as alternatives"
  ]
}
```

---

## Scenario 6 — Misuse / Anti-Pattern Trap: v1 to v2 Migration Pitfalls

```json
{
  "skills": ["implementing-lambda-powertools-java"],
  "query": "I'm migrating our Lambda functions from Powertools v1 to v2. Our current code uses @Metrics(namespace='App'), MetricsUtils.metricsLogger().putMetric('Orders', 1, Unit.COUNT), and captureError=false on @Tracing. What needs to change?",
  "expected_behavior": [
    "Replaces @Metrics with @FlushMetrics; flags that namespace is now required on the annotation",
    "Replaces MetricsUtils.metricsLogger().putMetric() with MetricsFactory.getMetricsInstance().addMetric()",
    "Replaces Unit.COUNT (EMF) with MetricUnit.COUNT (Powertools)",
    "Replaces captureError=false boolean with captureMode=CaptureMode.DISABLED enum value",
    "Warns that @SqsBatch is removed — migrate to BatchMessageHandlerBuilder",
    "Warns that LoggingUtils.appendKey() is removed — use MDC.put() instead",
    "Warns that v1 reached end-of-life December 12, 2025 — all v1 dependencies must be upgraded to 2.10.0",
    "Does NOT suggest using both v1 and v2 dependencies simultaneously",
    "Reminds to switch org.codehaus.mojo:aspectj-maven-plugin to dev.aspectj:aspectj-maven-plugin:1.14 for Java 17+"
  ]
}
```
