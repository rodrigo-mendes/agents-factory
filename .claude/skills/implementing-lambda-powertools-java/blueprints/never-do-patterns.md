# Never-Do Patterns — Lambda Powertools for Java v2.10.0

Eleven anti-patterns from SKILL.md with wrong / correct / detection.
Source research: `workspace/docs/research_cloud_AWS_LambdaPowertools_Java_2026.md`. Official sources accessed 2026-09-01.
Serverless Lens base URL: `https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/`

---

## A1 — Unstructured logging (CRITICAL)

- ❌ `System.out.println("Processing order: " + orderId);` or a plain-text pattern-layout appender.
- ✅ `powertools-logging-log4j|logback:2.10.0` + `@Logging(correlationIdPath = CorrelationIdPaths.API_GATEWAY_REST)`; JSON layout.
- Detect: `grep -r "System.out.println" src/`; Logs Insights `fields @message | filter not ispresent(level)`.
- Source: [opex-logging](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-logging.html)

## A2 — No active X-Ray tracing (HIGH)

- ❌ SAM `Tracing: PassThrough` or omitted; role lacks X-Ray permissions; no `@Tracing`.
- ✅ `Tracing: Active`, `powertools-tracing`, `@Tracing`, `xray:PutTraceSegments` + `xray:PutTelemetryRecords`.
- Detect: AWS Config `lambda-function-tracing-enabled`; `aws lambda get-function-configuration --function-name <name> --query TracingConfig`.
- Source: [opex-distributed-tracing](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-distributed-tracing.html)

## A3 — Plaintext secrets in code or env vars (CRITICAL)

- ❌ `DB_PASSWORD=mysecretpassword` in the SAM template; `private static final String API_KEY = "sk-..."`.
- ✅ Secrets Manager / SSM SecureString via `powertools-parameters-secrets|ssm`; env var holds only the name/ARN.

```java
secretsProvider.get("/myapp/db-creds", MyCredentials.class);
```

- Detect: `git grep -r "password\|secret\|api_key" src/`; Security Hub finding Lambda.2 as cited in the research.
- Source: [identity-and-access-management](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html)

## A4 — Shared IAM execution role across functions (HIGH)

- ❌ One `LambdaExecutionRole` with `dynamodb:*` and `s3:*` on every function.
- ✅ One role per function with only the permissions it needs (SAM per-function `Policies`, CDK `Function.addToRolePolicy()`).
- Detect: IAM Access Analyzer; AWS Config `iam-policy-no-statements-with-admin-access`.
- Source: [identity-and-access-management](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html)

## A5 — No `@Idempotent` on retryable mutations (CRITICAL)

- ❌ `POST /orders` calls `dynamoDB.putItem(newOrder)` with no key check; a client retry creates a duplicate.
- ✅ `@Idempotent` + `DynamoDBPersistenceStore` with `withEventKeyJMESPath("powertools_json(body)")`; `withPayloadValidationJMESPath("amount")` detects tampered retries; TTL at least the client retry window.
- Detect: review every POST/PUT/DELETE handler; load-test duplicates inside the TTL.
- Source: [failure-management](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html)

## A6 — No DLQ for async invocations (HIGH)

- ❌ S3 notification to Lambda with `MaximumRetryAttempts: 2` and no `OnFailure` destination.
- ✅ `DestinationConfig.OnFailure` to SQS (or SNS); explicit retry/record-age settings; alarm on DLQ depth.
- Detect: `aws lambda get-function-event-invoke-config --function-name <name>`; AWS Config `lambda-dlq-check`.
- Source: [failure-management](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html)

## A7 — API Gateway API keys as authorization (CRITICAL)

- ❌ `ApiKeyRequired: true` as the only control on a financial endpoint; key shipped to mobile clients.
- ✅ Cognito User Pools JWT or Lambda Authorizer for users; `AWS_IAM` SigV4 for services; AWS WAF for rate limiting and managed rules.
- Detect: Method Request shows Authorization = NONE with API Key Required = true.
- Source: [identity-and-access-management](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html)

## A8 — Unique IDs in static initializers with SnapStart (HIGH)

All restored environments share the snapshot, so static values collide.

- ❌ `private static final String REQUEST_ID = UUID.randomUUID().toString();`
- ✅ Generate UUIDs, nonces and random seeds inside `handleRequest()`.
- Detect: `grep -r "static.*UUID\|static.*Random" src/`.
- Source: [Lambda SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)

## A9 — `org.codehaus.mojo:aspectj-maven-plugin` on Java 17+ (HIGH)

Build fails or weaving silently does nothing, so annotations have no effect.

- ❌

```xml
<groupId>org.codehaus.mojo</groupId><artifactId>aspectj-maven-plugin</artifactId>
```

- ✅ `dev.aspectj:aspectj-maven-plugin:1.14` with matching `aspectjrt` (JDK 11-17 -> 1.9.20.1+, 21 -> 1.9.21+, 25 -> 1.9.25+).
- Detect: `mvn dependency:tree | grep aspectj`; check the plugin groupId.
- Source: [Powertools for Java](https://docs.aws.amazon.com/powertools/java/latest/)

## A10 — v1 `@Metrics` / `MetricsUtils` in v2 projects (HIGH)

v1 reached end-of-life on 2025-12-12; the v1 API is removed in v2.

- ❌ `@Metrics(namespace = "App")` with `MetricsUtils.metricsLogger().putMetric("Bookings", 1, Unit.COUNT)`.
- ✅ `@FlushMetrics(namespace = "App", captureColdStart = true)` with `metrics.addMetric("Bookings", 1, MetricUnit.COUNT)`; get the instance from `MetricsFactory.getMetricsInstance()`; `addDimension()` not `putDimensions(DimensionSet)`.
- Detect: `grep -r "@Metrics\|MetricsUtils\|putMetric\|putDimensions" src/` (any match is v1).
- Source: [Powertools for Java](https://docs.aws.amazon.com/powertools/java/latest/)

## A11 — Ignoring partial failures in BatchWriteItem / PutRecords (HIGH)

`BatchWriteItem` returns success even if only one record is ingested.

- ❌ `dynamoDB.batchWriteItem(request)` without checking `getUnprocessedItems()`; `putRecords` without `getFailedRecordCount()`.
- ✅ Retry `UnprocessedItems` and failed Kinesis records; use `powertools-batch` for Lambda event-source batches.
- Detect: `grep -r "batchWriteItem\|putRecords" src/` and review each call site.
- Source: [failure-management](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html)
