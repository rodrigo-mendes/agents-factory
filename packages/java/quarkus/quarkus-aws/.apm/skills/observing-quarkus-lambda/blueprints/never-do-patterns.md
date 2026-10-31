# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Each item is carried from a pillar skill; illustrative code is medium confidence (M5 in the register). The per-mode MDC request id is (medium confidence), so it lives in Ask First 6, not here.

## Contents

- [N1. Unbounded dimension](#n1-unbounded-dimension)
- [N2. PII in any pillar](#n2-pii-in-any-pillar)
- [N3. EMF through the logger](#n3-emf-through-the-logger)
- [N4. Invalid annotation key](#n4-invalid-annotation-key)
- [N5. Default tracing stack](#n5-default-tracing-stack)
- [N6. Double-loading skills](#n6-double-loading-skills)

## N1. Unbounded dimension

Source: [monitoring never-do](../../monitoring-quarkus-lambda-v3-40/blueprints/never-do-patterns.md).

```java
// 🚫 WRONG: every request id and tenant becomes its own billed metric
"Dimensions": [["requestId", "tenantId"]]
```

```java
// ✅ CORRECT: bounded proxy dimension, identifiers as root properties
"Dimensions": [["Service", "TenantTier"]]   // plus root "requestId" and "tenantId" properties
```

Impact: every unique dimension combination is a separate custom metric ([EMF spec](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html)). An unbounded `TenantId` dimension needs an ADR (Ask First 3).

## N2. PII in any pillar

Sources: [logging never-do](../../logging-quarkus-lambda-v3-40/blueprints/never-do-patterns.md), [tracing F4](../../tracing-quarkus-lambda-v3-40/blueprints/never-do-patterns.md#f4-pii-in-trace-data).

```java
// 🚫 WRONG
MDC.put("tenantId", user.getEmail());
sub.putAnnotation("tenantId", user.getEmail());
Log.info(System.getenv().toString());
```

```java
// ✅ CORRECT: opaque, bounded identifier; keep quarkus.otel.traces.eusp.enabled=false
MDC.put("tenantId", tenantFromVerifiedToken(event));
```

Impact: Lambda sets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN` in the environment; End User attributes are PII.

## N3. EMF through the logger

Source: [monitoring never-do](../../monitoring-quarkus-lambda-v3-40/blueprints/never-do-patterns.md).

```java
// 🚫 WRONG: the default console format prefixes timestamp and level (High); JSON logging also wraps the text (medium confidence, M8)
Log.info(emfJson);
```

```java
// ✅ CORRECT: one raw line
System.out.println(emfJson);
```

## N4. Invalid annotation key

Source: [tracing F5](../../tracing-quarkus-lambda-v3-40/blueprints/never-do-patterns.md#f5-invalid-annotation-keys). How the SDK treats invalid keys is (unverified, U10 in the register).

```java
// 🚫 WRONG
sub.putAnnotation("tenant_id", tenantId);
// ✅ CORRECT
sub.putAnnotation("tenantId", tenantId);
```

## N5. Default tracing stack

Source: [tracing C1](../../tracing-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#c1-x-ray-sdk-or-opentelemetry). Neither the X-Ray SDK nor OpenTelemetry is a default; the reasons are in [Ask First 1](./ask-first-decisions.md#1-tracing-stack). Wrong: pick a tracing stack without asking. Correct: ask, record the ADR, prove one route in a PoC.

## N6. Double-loading skills

Wrong: load this umbrella and `logging-quarkus-lambda-v3-40` for a logging-only question. Correct: the pillar skill alone for one pillar; the umbrella for a task that spans pillars.
