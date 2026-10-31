# Always-Do Patterns — Lambda Powertools for Java v2.10.0

Full detail for the 7 mandatory patterns summarised in SKILL.md.
Source research: `workspace/docs/research_cloud_AWS_LambdaPowertools_Java_2026.md`. Official sources accessed 2026-09-01.

---

## M1 — Structured JSON logging with correlation ID

**Pillar**: Operational Excellence. The Serverless Lens classifies unstructured logging as an anti-pattern.

- Dependency: `powertools-logging-log4j` or `powertools-logging-logback` (2.10.0). Never both.
- Layout: `JsonTemplateLayout` with `LambdaJsonLayout.json` (Log4j2) or `LambdaJsonEncoder` (Logback).
- Set `POWERTOOLS_SERVICE_NAME` on every function.
- Per-invocation context: `MDC.put()`; per-call context: `StructuredArguments.entry()`.

```java
@Logging(correlationIdPath = CorrelationIdPaths.API_GATEWAY_REST, clearState = true)
public APIGatewayProxyResponseEvent handleRequest(APIGatewayProxyRequestEvent in, Context ctx) { ... }
```

Records include timestamp, level, service, cold_start, function_request_id, function_name, function_arn, xray_trace_id, correlation_id.

```
fields @timestamp, level, service, function_request_id, correlation_id, message
| filter level = "ERROR" | sort @timestamp desc | limit 50
```

Sources: [Serverless Lens: logging](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-logging.html); [Powertools Logging](https://docs.aws.amazon.com/powertools/java/2.8.0/core/logging/)

---

## M2 — Active X-Ray tracing with subsegments and annotations

**Pillar**: Operational Excellence.

- `Tracing: Active` in SAM/CDK on every function.
- Add `powertools-tracing:2.10.0` as dependency and as `aspectLibrary`.
- `@Tracing` auto-creates indexed annotations `ColdStart` (Boolean) and `Service` (String).
- Wrap dependency calls: `TracingUtils.withSubsegment("callDynamoDB", ...)`.
- Non-production: `POWERTOOLS_TRACER_CAPTURE_RESPONSE=false` and `POWERTOOLS_TRACER_CAPTURE_ERROR=false` to reduce payload.
- Execution role: `xray:PutTraceSegments`, `xray:PutTelemetryRecords`.
- Verify: X-Ray Service Map shows downstream nodes; filter traces with `Annotation.ColdStart = true`.

Source: [Serverless Lens: tracing](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-distributed-tracing.html)

---

## M3 — Custom metrics via EMF with cold start capture

**Pillar**: Operational Excellence. EMF avoids synchronous `PutMetricData` calls.

```java
@FlushMetrics(namespace = "AppNamespace", service = "booking", captureColdStart = true)
public Object handleRequest(...) {
  metrics.addMetric("SuccessfulBooking", 1, MetricUnit.COUNT);
}
```

- `MetricResolution.HIGH` for 1-second granularity metrics.
- `POWERTOOLS_METRICS_NAMESPACE` sets the default namespace.
- `raiseOnEmptyMetrics = true` in production to catch code paths that emit nothing.
- Tests: `POWERTOOLS_METRICS_DISABLED=true`, then assert EMF JSON on captured stdout.

Source: [CloudWatch EMF specification](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html)

---

## M4 — Idempotency on every mutating API operation

**Pillar**: Reliability. API Gateway clients and SQS can invoke the same handler repeatedly.

- Runtime dependency `powertools-idempotency-dynamodb:2.10.0`; `powertools-idempotency-core` as `aspectLibrary`.
- Configure **in the constructor** (not in the handler).

```java
public OrderHandler() {
  Idempotency.config().withPersistenceStore(
    DynamoDBPersistenceStore.builder().withTableName(System.getenv("TABLE_NAME")).build()
  ).configure();
}
```

- `@Idempotent` on the handler or mutating method; `withEventKeyJMESPath("powertools_json(body)")` for API Gateway events.
- In batch processing, `@Idempotent` goes on the per-record method with `@IdempotencyKey` on the unique field.
- Separate PAY_PER_REQUEST table, partition key `id` (String); DynamoDB TTL on `expiration`, at least the client retry window (default 3600 s).
- Verify: same request twice inside the TTL returns an identical response, no side effects re-run.

Sources: [Serverless Lens: failure management](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html); [Powertools Idempotency](https://docs.aws.amazon.com/powertools/java/latest/utilities/idempotency/)

---

## M5 — Externalize configuration and secrets via Parameters

**Pillar**: Security. Default cache TTL is 5 s, avoiding per-invocation API calls.

- Modules: `powertools-parameters-ssm` (config), `powertools-parameters-secrets` (credentials), `powertools-parameters-appconfig` (feature flags).
- Initialize providers in the constructor (SnapStart-compatible).

```java
ssmProvider.withDecryption().get("/myapp/db/password");
ssmProvider.withMaxAge(1, ChronoUnit.MINUTES).withTransformation(Transformer.json).get("/myapp/config", MyConfig.class);
```

- Execution role: `ssm:GetParameter`, `ssm:GetParametersByPath`, `kms:Decrypt` (SecureString), `secretsmanager:GetSecretValue`. No `ssm:*` / `secretsmanager:*` wildcards.
- Environment variables hold only the parameter name/ARN.

Sources: [Powertools Parameters](https://docs.aws.amazon.com/powertools/java/latest/utilities/parameters/); [Serverless Lens: IAM](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html)

---

## M6 — Partial batch failure handling

**Pillar**: Reliability. Without it one bad record requeues the whole batch.

- Enable `ReportBatchItemFailures` on the SQS / Kinesis / DynamoDB Streams event source mapping.
- Add `powertools-batch:2.10.0`.

```java
BatchMessageHandlerBuilder.withSqsBatchHandler()
  .withSuccessHandler(...).withFailureHandler(...)
  .buildWithMessageHandler(fn, Model.class);
handler.processBatch(event, context);                       // ordered
handler.processBatchInParallel(event, context, executor);   // I/O-bound, virtual threads on Java 21+
```

- Never parallel-process FIFO queues.
- Attach a DLQ to the SQS queue for records that exhaust retries.
- Verify: a malformed record is the only ID in `batchItemFailures`.

Source: [Powertools Batch](https://docs.aws.amazon.com/powertools/java/latest/utilities/batch/)

---

## M7 — Initialize in the constructor for SnapStart

**Pillar**: Performance Efficiency. SnapStart snapshots the environment after the constructor runs.

- Constructor: `Idempotency.config()...configure()`, `SSMProvider` / `SecretsProvider`, `TracingUtils.init()`.
- Static initializer: `ValidationConfig.get()` to prime the schema cache.
- Set `networkaddress.cache.ttl=0` before logger initialization (DNS staleness after restore).
- Generate UUIDs, tokens, nonces inside `handleRequest()`, never in static initializers.
- SnapStart is not usable with Provisioned Concurrency, EFS, or ephemeral storage above 512 MB.

Sources: [Lambda SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html); [Powertools for Java](https://docs.aws.amazon.com/powertools/java/latest/)
