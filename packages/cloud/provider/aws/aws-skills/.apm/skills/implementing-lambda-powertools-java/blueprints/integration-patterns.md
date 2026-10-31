# Integration Patterns — Lambda Powertools for Java v2.10.0

Cross-service combinations summarised in SKILL.md. Official sources accessed 2026-09-01.
Source research: `workspace/docs/research_cloud_AWS_LambdaPowertools_Java_2026.md`.

---

## 1. Core observability stack (all handlers)

Modules: `powertools-logging-log4j` (or `-logback`) + `powertools-tracing` + `powertools-metrics`.

```java
@Logging(correlationIdPath = CorrelationIdPaths.API_GATEWAY_REST, clearState = true)
@Tracing
@FlushMetrics(namespace = "App", service = "booking", captureColdStart = true)
public Object handleRequest(...) { ... }
```

- All three share `POWERTOOLS_SERVICE_NAME` as the service dimension.
- X-Ray Service Map shows the dependency graph; Logs Insights correlates by `function_request_id` and `correlation_id`.
- Add CloudWatch alarms on error rate and p99 latency metrics.
- Cost note: high-volume functions need log sampling (`samplingRate=0.1` in the research) to control ingestion cost.

Sources: [Serverless Lens: logging](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-logging.html); [Serverless Lens: tracing](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-distributed-tracing.html)

---

## 2. Idempotent transactional API (API Gateway)

- API Gateway REST API to a Lambda entry point annotated `@Idempotent` (`powertools-idempotency-dynamodb`).
- Multi-step flows: Step Functions Express workflows (saga); one Lambda per step; one idempotency table per mutating step; SQS DLQ for async compensation.
- Trade-off: 2 WCU on first call, 1 WCU + 1 RCU on retry; about 1-5 ms added per invocation (research estimate).
- Validation first: `powertools-validation` runs before `@Idempotent`, so invalid input returns HTTP 400 before touching the idempotency table (no pollution with invalid request hashes).

Sources: [failure-management](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html); [Powertools Idempotency](https://docs.aws.amazon.com/powertools/java/latest/utilities/idempotency/); [Powertools Validation](https://docs.aws.amazon.com/powertools/java/latest/utilities/validation/)

---

## 3. Batch + idempotency (SQS, effectively once per record)

- SQS standard queue with `ReportBatchItemFailures`; handler built with `BatchMessageHandlerBuilder.withSqsBatchHandler()`.
- Per-record method annotated `@Idempotent` with `@IdempotencyKey` on the message ID parameter; separate idempotency table; DLQ on the queue.
- Parallel processing (virtual threads, Java 21+) only for I/O-bound standard queues; never FIFO.
- `@SqsBatch` is removed in v2.

Sources: [Powertools Batch](https://docs.aws.amazon.com/powertools/java/latest/utilities/batch/); [Powertools Idempotency](https://docs.aws.amazon.com/powertools/java/latest/utilities/idempotency/)

---

## 4. Large messages + batch + S3

- Producer offloads payloads above 256 KB to S3 with `amazon-sqs-java-extended-client-lib` (1.1.0+ or 2.0.0+) or `amazon-sns-java-extended-client-lib` (2.0.0+).
- Consumer: `powertools-large-messages:2.10.0` with `@LargeMessage` on the **per-record** method, not on `handleRequest`.
- `@LargeMessage(deleteS3Object=false)` if downstream processing needs the S3 object.
- IAM: `s3:GetObject` and `s3:DeleteObject`. Adds about 5-20 ms per large message (research estimate).

Source: [Powertools Large Messages](https://docs.aws.amazon.com/powertools/java/latest/utilities/large_messages/)

---

## 5. Parameters + SnapStart / AppConfig feature flags

- Providers (`SSMProvider`, `SecretsProvider`) built in the constructor so SnapStart snapshots them pre-initialized.
- TTL by sensitivity via `withMaxAge()`: credentials 5-30 s, config 30-60 s.
- Feature flags: `powertools-parameters-appconfig:2.10.0` with `withMaxAge(30, ChronoUnit.SECONDS)`; AppConfig deployment strategy controls rollout, with rollback on a CloudWatch alarm.
- Cache miss costs about 10 ms against AppConfig (research estimate).

Source: [Powertools Parameters](https://docs.aws.amazon.com/powertools/java/latest/utilities/parameters/)

---

## Common problems

- `IdempotencyConfigException` -> `Idempotency.config().configure()` was called in the handler; move it to the constructor.
- `UnsupportedOperationException` from `processBatchInParallel()` -> FIFO queue; use ordered `processBatch()`.
- Class-loading conflicts -> two logging backends on the classpath; keep one.
- Identical IDs across restored environments -> entropy generated in static fields; move into the handler method.
- `ClassNotFoundException` for `...powertools.metrics.Metrics` -> v1/v2 mixing; all `powertools-*` must be 2.x.x.
