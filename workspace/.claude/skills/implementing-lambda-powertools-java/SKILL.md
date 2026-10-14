---
name: implementing-lambda-powertools-java
description: "Instruments AWS Lambda Java functions with Lambda Powertools v2 (v2.10.0) following the AWS Well-Architected Serverless Lens. Use when designing, coding, or reviewing Java Lambda handlers that need structured logging, distributed tracing, custom metrics, idempotency, batch processing, or secrets/parameters retrieval."
---

## Function

Specialist in AWS Lambda Powertools for Java v2.10.0 — structured observability, idempotency, batch processing, and configuration management for Java Lambda web application backends on AWS.

## Version Context

**Technology**: AWS Lambda Powertools for Java
**Target version**: v2.10.0
**Release date**: September 2026
**Support status**: Active (v1 reached end-of-life December 12, 2025)

**Key v2 changes from v1**:
- `@Metrics` renamed to `@FlushMetrics`; `namespace` is now required
- `captureError` (boolean) replaced by `captureMode` (enum: `ENVIRONMENT_VAR | RESPONSE | ERROR | BOTH | DISABLED`)
- Logging rebuilt on SLF4J; backend choice: `powertools-logging-log4j` or `powertools-logging-logback`
- MDC replaces `LoggingUtils.appendKey()` for per-invocation context
- Idempotency and Parameters split into provider-specific sub-modules
- `@SqsBatch` removed; `BatchMessageHandlerBuilder` replaces it
- Functional API (no AspectJ) introduced at v2.7.0 with 100% feature parity
- Thread-safe utilities from v2.8.0; Lambda Metadata utility new in v2.10.0
- `dev.aspectj:aspectj-maven-plugin` required (not `org.codehaus.mojo`) for Java 17+

**Deprecated / removed in v2**:
- `@Metrics`, `MetricsUtils.metricsLogger()`, `MetricsLogger`, `putDimensions(DimensionSet)` (v1 API — removed)
- `@SqsBatch` annotation (removed)
- `captureError = false` boolean on `@Tracing` (replaced by `captureMode`)
- `LoggingUtils.appendKey()` (replaced by `MDC.put()`)

⚠️ **CRITICAL — Agent Warning**:
This skill targets v2.10.0. v1 is end-of-life. Reject ALL v1 API patterns. Do not mix v1 annotations or utility classes with v2 dependencies.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier rules (✅⚠️🚫)
- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 7 mandatory patterns with full code examples
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural decision matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 11 anti-patterns with ❌ wrong / ✅ correct examples
- **[Integration Patterns](#integration-patterns)** — Cross-service combinations
- **[Verification Loop](#verification-loop)** — Post-generation validation commands
- **[Quick Reference](#quick-reference)** — Dependencies, limits, key env vars
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test scenarios
- **[External Resources](#external-resources)** — Dated official sources

---

## Blueprints & Guardrails

### ✅ Always Do

Full code examples in [Always Do Patterns](./blueprints/always-do-patterns.md).

- **Structured JSON logging with correlation ID** — Deploy `powertools-logging-log4j:2.10.0` or `powertools-logging-logback:2.10.0`. Annotate every handler with `@Logging(correlationIdPath = CorrelationIdPaths.API_GATEWAY_REST, clearState = true)`. Configure `JsonTemplateLayout` (Log4j2) or `LambdaJsonEncoder` (Logback). Set `POWERTOOLS_SERVICE_NAME`. Unstructured logging (`System.out.println`) is a Well-Architected anti-pattern that breaks CloudWatch Logs Insights field extraction.

- **Active X-Ray tracing with subsegments and annotations** — Set `Tracing: Active` in SAM/CDK for every function. Add `powertools-tracing:2.10.0` as a dependency and aspectLibrary. Annotate handler with `@Tracing`. Wrap external dependency calls in `TracingUtils.withSubsegment("callDynamoDB", ...)`. Grant `xray:PutTraceSegments` and `xray:PutTelemetryRecords` on the execution role.

- **Custom metrics via EMF with cold start capture** — Add `powertools-metrics:2.10.0`. Annotate handler with `@FlushMetrics(namespace = "AppNamespace", service = "booking", captureColdStart = true)`. Emit business metrics via `metrics.addMetric("SuccessfulBooking", 1, MetricUnit.COUNT)`. Set `raiseOnEmptyMetrics = true` in production to catch silent paths that emit no metrics.

- **Idempotency on every mutating API operation** — Add `powertools-idempotency-dynamodb:2.10.0` runtime + `powertools-idempotency-core` as aspectLibrary. Initialize `Idempotency.config().withPersistenceStore(...).configure()` **in the constructor** (mandatory). Annotate POST/PUT/DELETE handlers with `@Idempotent`. Use `withEventKeyJMESPath("powertools_json(body)")` for API Gateway events. Enable DynamoDB TTL on `expiration` attribute.

- **Externalize configuration and secrets via Parameters utility** — Use `powertools-parameters-ssm` for config and `powertools-parameters-secrets` for credentials. Initialize providers in the constructor (SnapStart compatible). Use `withDecryption()` for SecureString. Tune TTL with `withMaxAge()`. Lambda environment variables hold only the parameter name/ARN — never the value itself.

- **Partial batch failure handling for SQS/Kinesis/DynamoDB Streams** — Enable `ReportBatchItemFailures` on the event source mapping. Add `powertools-batch:2.10.0`. Build with `BatchMessageHandlerBuilder.withSqsBatchHandler()`. Use `processBatchInParallel()` with virtual threads (Java 21+) for I/O-bound records. Do **not** use parallel processing on FIFO queues.

- **Initialize Powertools utilities in the constructor for SnapStart** — Place `Idempotency.config()`, `SSMProvider`/`SecretsProvider` construction, and `TracingUtils.init()` in the class constructor. Call `ValidationConfig.get()` in a static initializer to prime schema cache. Set `networkaddress.cache.ttl=0` before logger init. Generate UUIDs, nonces, and random values **inside** `handleRequest()` — never in static initializers.

### ⚠️ Ask First

Full decision matrices in [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Annotation API (AspectJ CTW) vs Functional API** — Ask whether the runtime uses GraalVM native image, Kotlin, or heavy Lombok usage. If yes → use Functional API (v2.7.0+, no AspectJ plugin needed). If standard Maven/Gradle Java 11+ with no GraalVM → Annotation API is ergonomically simpler.

- **Log4j2 backend vs Logback backend** — Ask whether the project already has a Log4j2 or Logback dependency. Do not add both — class-loading conflicts will occur. No cost difference; switching requires only changing the Maven/Gradle dependency and the XML config file.

- **SSM Parameter Store vs Secrets Manager for credentials** — Ask whether the credential requires automated rotation. If yes → Secrets Manager ($0.40/secret/month). If no → SSM Parameter Store SecureString (free tier). Both are abstracted by the Parameters utility.

- **DynamoDB idempotency table — On-Demand vs Provisioned Capacity** — Ask the expected peak requests-per-second for the mutating endpoint. Variable/unpredictable → On-Demand (PAY_PER_REQUEST). High-throughput and predictable → Provisioned + Auto Scaling. Idempotency costs 2 WCU (first call) + 1 WCU + 1 RCU (retry). Max storable response: 400 KB.

### 🚫 Never Do

Full anti-patterns with code in [Never Do Patterns](./blueprints/never-do-patterns.md).

| Anti-Pattern | Risk | Correct Alternative |
|---|---|---|
| `System.out.println()` / unstructured log | CRITICAL — breaks CloudWatch Insights, no correlation IDs | `@Logging` with `JsonTemplateLayout` / `LambdaJsonEncoder` |
| `Tracing: PassThrough` or no X-Ray annotation | HIGH — latency blind spots, no service map | `Tracing: Active` + `@Tracing` + execution role X-Ray grants |
| Secrets/passwords as plaintext Lambda env vars or hardcoded | CRITICAL — data breach, compliance violation | SSM SecureString or Secrets Manager via `powertools-parameters-*` |
| Shared IAM execution role across multiple Lambda functions | HIGH — violates least-privilege, blast radius | One role per function with only required permissions |
| No `@Idempotent` on retryable mutating endpoints (POST/PUT/DELETE) | CRITICAL — duplicate orders, duplicate payments | `@Idempotent` + `DynamoDBPersistenceStore` + `withEventKeyJMESPath()` |
| No DLQ for async Lambda invocations | HIGH — silent event loss after retries exhausted | `DestinationConfig.OnFailure` → SQS DLQ + CloudWatch Alarm on depth |
| API Gateway API Keys as the sole authorization mechanism | CRITICAL — API Keys are not security controls | Cognito User Pools JWT, Lambda Authorizer, or `AWS_IAM` SigV4 |
| `UUID.randomUUID()` in static initializers with SnapStart | HIGH — predictable/colliding IDs across restored environments | Move all entropy generation into `handleRequest()` |
| `org.codehaus.mojo:aspectj-maven-plugin` with Java 17+ | HIGH — build failure or silent annotation no-op | `dev.aspectj:aspectj-maven-plugin:1.14` + matching `aspectjrt` |
| v1 `@Metrics` / `MetricsUtils` / `putDimensions(DimensionSet)` in v2 projects | HIGH — build failure or ClassNotFoundException | `@FlushMetrics` + `MetricUnit` (Powertools) + `addDimension()` |
| `BatchWriteItem` / `PutRecords` without inspecting partial failures | HIGH — silent data loss | Check `getUnprocessedItems()` (DynamoDB) and `getFailedRecordCount()` (Kinesis); use `powertools-batch` for Lambda event sources |

---

## Integration Patterns

Full integration code in [Integration Patterns](./blueprints/integration-patterns.md).

**Core Powertools stack (all handlers)**:
`powertools-logging-log4j` (or `logback`) + `powertools-tracing` + `powertools-metrics` — annotate every handler with `@Logging`, `@Tracing`, and `@FlushMetrics`. All three utilities share `POWERTOOLS_SERVICE_NAME` as a common service dimension.

**Idempotency + Batch (SQS exactly-once processing)**:
`powertools-batch` + `powertools-idempotency-dynamodb` — batch handler calls per-record method annotated with `@Idempotent(@IdempotencyKey)` on the message ID. Requires `ReportBatchItemFailures` on the event source mapping.

**Large Messages + Batch + S3**:
`powertools-large-messages` + `powertools-batch` — `@LargeMessage` on the per-record method (not on `handleRequest`). `deleteS3Object=false` if downstream processing needs the S3 object.

**Parameters + SnapStart**:
`powertools-parameters-ssm` / `powertools-parameters-secrets` — initialize providers in the class constructor so SnapStart snapshots them pre-initialized. Use `withMaxAge()` TTL tuning per parameter sensitivity (credentials: 5s–30s; config: 30s–60s).

**Validation + Idempotency (API Gateway)**:
`powertools-validation` before `@Idempotent` processing. Invalid input returns HTTP 400 (v2 behavior) before hitting idempotency logic, preventing idempotency table pollution with invalid request hashes.

**Common problems**:
- **`@Idempotent` initialized in handler instead of constructor** → `IdempotencyConfigException` at runtime; move `Idempotency.config().configure()` to the constructor.
- **FIFO queue + `processBatchInParallel()`** → `UnsupportedOperationException`; use ordered `processBatch()` for FIFO.
- **Two logging backends on classpath** → class-loading conflicts; use only one of `powertools-logging-log4j` or `powertools-logging-logback`.
- **SnapStart with unique IDs in static fields** → identical IDs across all restored execution environments; generate entropy in handler method.

---

## Verification Loop

Run after every code generation:

### 1. Build / Compile

```bash
mvn package -q
# Expected: BUILD SUCCESS
# Exit code: 0
# If aspectj-maven-plugin fails: verify groupId is dev.aspectj (not org.codehaus.mojo)
```

### 2. Unit Tests

```bash
mvn test -q
# Expected: Tests run: N, Failures: 0, Errors: 0
# Exit code: 0
# Set POWERTOOLS_METRICS_DISABLED=true in test env to suppress EMF stdout
# Set POWERTOOLS_IDEMPOTENCY_DISABLED=true to skip DynamoDB calls in unit tests
```

### 3. Structure Checks

```bash
# Confirm no v1 API usage
grep -r "@Metrics\|MetricsUtils\|putDimensions\|@SqsBatch\|captureError" src/
# Expected: no output

# Confirm no hardcoded secrets
grep -r "password\|secret\|api_key" src/ --include="*.java"
# Expected: no output (or only variable names, not values)

# Confirm no unstructured logging
grep -r "System\.out\.println" src/
# Expected: no output

# Confirm no static entropy generation
grep -r "static.*UUID\.randomUUID\|static.*new Random" src/
# Expected: no output (SnapStart safety)

# Confirm aspectj plugin groupId
grep "aspectj-maven-plugin" -A2 pom.xml | grep "groupId"
# Expected: dev.aspectj
```

### 4. Deployment Smoke Test

```bash
aws lambda invoke --function-name <FunctionName> /tmp/out.json
cat /tmp/out.json
# Expected: well-formed JSON response, no ERROR level log in CloudWatch

# Verify structured JSON log output
aws logs tail /aws/lambda/<FunctionName> --since 5m | head -20
# Expected: each log line is a single-line JSON object with fields: level, service, function_request_id, correlation_id
```

**Troubleshooting**:
- `ClassNotFoundException: software.amazon.lambda.powertools.metrics.Metrics` → v1/v2 mixing; check all `powertools-*` dependencies are `2.x.x`
- `@Tracing` / `@Logging` annotations have no effect at runtime → AspectJ weaving not configured; verify aspectLibrary declarations in `pom.xml`
- `IdempotencyConfigException` → `Idempotency.config().configure()` called in handler, not constructor; move to constructor

---

## Quick Reference

**Maven BOM coordinates (v2.10.0)**:
```xml
<dependency>
  <groupId>software.amazon.lambda</groupId>
  <artifactId>powertools-bom</artifactId>
  <version>2.10.0</version>
  <type>pom</type>
  <scope>import</scope>
</dependency>
```

**Module names**: `powertools-logging-log4j`, `powertools-logging-logback`, `powertools-tracing`, `powertools-metrics`, `powertools-idempotency-dynamodb`, `powertools-idempotency-core`, `powertools-parameters-ssm`, `powertools-parameters-secrets`, `powertools-parameters-appconfig`, `powertools-batch`, `powertools-validation`, `powertools-large-messages`, `powertools-lambda-metadata`

**Key environment variables**:

| Variable | Purpose |
|---|---|
| `POWERTOOLS_SERVICE_NAME` | Service name injected in all logs, traces, and metrics |
| `POWERTOOLS_LOG_LEVEL` | Log level (overridden by `AWS_LAMBDA_LOG_LEVEL` from Lambda config) |
| `POWERTOOLS_METRICS_NAMESPACE` | Default namespace for `@FlushMetrics` |
| `POWERTOOLS_METRICS_DISABLED` | Set `true` in tests to suppress EMF stdout |
| `POWERTOOLS_IDEMPOTENCY_DISABLED` | Set `true` in unit tests to skip DynamoDB idempotency checks |
| `POWERTOOLS_TRACER_CAPTURE_RESPONSE` | `false` for non-production or large-payload handlers |

**Critical limits**:

| Resource | Limit | Scope |
|---|---|---|
| CloudWatch Metrics dimensions | 30 per metric blob (v2; was 9 in v1) | per `@FlushMetrics` invocation |
| DynamoDB idempotency item size | 400 KB max | stored handler response |
| SQS message size (standard) | 256 KB | use `powertools-large-messages` above this |
| SQS batch size | 10,000 messages max | `powertools-batch` |
| `@FlushMetrics` namespace | Required (build error if absent) | v2 enforcement |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/implementing-lambda-powertools-java/
├── SKILL.md                              ← This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             ← ✅ 7 mandatory patterns with full code
    ├── ask-first-decisions.md            ← ⚠️ 4 decision matrices
    ├── never-do-patterns.md              ← 🚫 11 anti-patterns with ❌/✅ code
    ├── integration-patterns.md           ← Cross-service code examples
    └── evaluation-scenarios.md           ← 6 test scenarios for skill-evaluator
```

---

## External Resources

### Official Documentation
- [AWS Lambda Powertools for Java — Latest](https://docs.aws.amazon.com/powertools/java/latest/) — Primary reference (2026-09-01)
- [Powertools Logging v2](https://docs.aws.amazon.com/powertools/java/2.8.0/core/logging/) — SLF4J, MDC, log buffering (2026-09-01)
- [Powertools Idempotency](https://docs.aws.amazon.com/powertools/java/latest/utilities/idempotency/) — DynamoDB persistence store, JMESPath (2026-09-01)
- [Powertools Batch Processing](https://docs.aws.amazon.com/powertools/java/latest/utilities/batch/) — SQS/Kinesis/DynamoDB Streams (2026-09-01)
- [Powertools Parameters](https://docs.aws.amazon.com/powertools/java/latest/utilities/parameters/) — SSM, Secrets Manager, AppConfig (2026-09-01)
- [Powertools Validation](https://docs.aws.amazon.com/powertools/java/latest/utilities/validation/) — JSON Schema, HTTP 400 on API GW failure (2026-09-01)
- [Lambda SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html) — Constructor initialization, DNS cache TTL (2026-09-01)

### Well-Architected Alignment
- [Serverless Lens — Operational Excellence: Logging](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-logging.html) — Structured logging mandate (2026-09-01)
- [Serverless Lens — Operational Excellence: Tracing](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-distributed-tracing.html) — Active X-Ray requirement (2026-09-01)
- [Serverless Lens — Reliability: Failure Management](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html) — Idempotency, DLQ, partial batch (2026-09-01)
- [Serverless Lens — Security: IAM](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html) — Least-privilege roles, secrets management (2026-09-01)

### Supporting Services
- [CloudWatch Embedded Metric Format](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html) — EMF specification (2026-09-01)
