# Correlation Recipe

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. The recipe only combines what the three pillar skills state; the combined code body is illustrative (medium confidence, M5 in the register). Nothing here says a trace id is written into a log line: no pillar skill states it (U9 in the register).

## Contents

- [Key set](#key-set)
- [Combined handler sketch (X-Ray path)](#combined-handler-sketch-x-ray-path)
- [OpenTelemetry path](#opentelemetry-path)
- [How to join the pillars](#how-to-join-the-pillars)
- [What the recipe does not claim](#what-the-recipe-does-not-claim)

## Key set

| Key | Log | Trace | Metric | Source skills |
|---|---|---|---|---|
| Request id (spelling per pillar, stated once in the [SKILL.md Quick Reference](../SKILL.md#quick-reference)): MDC `AWSRequestId`, trace metadata `AWSRequestId`, EMF `requestId` | MDC `AWSRequestId` | X-Ray metadata `AWSRequestId` or span attribute (metadata by default) | EMF root property `requestId` | [logging](../../logging-quarkus-lambda-v3-40/blueprints/mdc-and-request-id.md), [tracing A7, A8](../../tracing-quarkus-lambda-v3-40/blueprints/always-do-patterns.md), [monitoring](../../monitoring-quarkus-lambda-v3-40/blueprints/always-do-patterns.md#7-bounded-dimensions) |
| `tenantId` | MDC | annotation (indexed) | dimension, root property or proxy (Ask First 3) | same |

## Combined handler sketch (X-Ray path)

```java
// Quarkus 3.40.1.1 - illustrative (medium confidence). Decisions taken: X-Ray SDK, hand-written EMF,
// tenant option C (bounded TenantTier dimension + tenantId property).
// Init: nothing for logging; X-Ray TracingInterceptor on SDK clients per tracing A5.
// Usage: per invocation, MDC put -> subsegment -> work -> EMF line -> cleanup in finally.
@Named("orders")
public class OrdersLambda implements RequestHandler<OrderEvent, OrderResult> {

    @Override
    public OrderResult handleRequest(OrderEvent event, Context context) {
        String requestId = context.getAwsRequestId();
        String tenantId = tenantFromVerifiedToken(event);          // family rule 6
        MDC.put("AWSRequestId", requestId);                        // logging: put yourself in JVM mode
        MDC.put("tenantId", tenantId);
        Subsegment sub = AWSXRay.beginSubsegment("order-processing");   // tracing F6: not the function segment
        try {
            sub.putAnnotation("tenantId", tenantId);               // tracing A7: indexed, valid key
            sub.putMetadata("AWSRequestId", requestId);            // everything else is metadata
            Log.info("order received");
            OrderResult result = process(event);
            Log.info("order processed");
            System.out.println(emfLine(requestId, tenantId, tierOf(tenantId), 1));  // monitoring: raw line, before return
            return result;
        } catch (RuntimeException e) {
            sub.addException(e);
            Log.error("order failed", e);
            throw e;
        } finally {
            AWSXRay.endSubsegment();
            MDC.remove("tenantId");                                // logging: clear what you put
            MDC.remove("AWSRequestId");
        }
    }
}
```

`emfLine(...)` builds one JSON object on one line per [EMF implementation](../../monitoring-quarkus-lambda-v3-40/blueprints/emf-implementation.md): `Namespace` not starting with `AWS/`, dimension `TenantTier` (bounded), `tenantId` and `requestId` as root properties, timestamp in epoch milliseconds.

## OpenTelemetry path

Replace the subsegment lines by a span attribute plus the `aws.xray.annotations` list ([tracing A8](../../tracing-quarkus-lambda-v3-40/blueprints/always-do-patterns.md#a8-otel-annotations)) and set `quarkus.otel.simple=true` ([A9](../../tracing-quarkus-lambda-v3-40/blueprints/always-do-patterns.md#a9-simple-span-processor)). No export route to X-Ray was found documented; it needs a PoC (Ask First 1, medium confidence, absence of evidence, M7). The log and metric lines are unchanged.

## How to join the pillars

1. Start from a trace in the X-Ray console filtered by annotation `tenantId` (filter expressions use indexed annotations, see [tracing A7](../../tracing-quarkus-lambda-v3-40/blueprints/always-do-patterns.md#a7-x-ray-annotations)).
2. Take the `AWSRequestId` from the trace metadata (the EMF line carries the same value as `requestId`) and query the function's log group on `mdc.AWSRequestId` (Logs Insights dot notation, medium confidence; queries in the [logging verification loop](../../logging-quarkus-lambda-v3-40/blueprints/verification-loop.md#logs-insights-queries)). Query both spellings `AWSRequestId` and `AWSrequestId` when Lambda-generated lines are involved (unverified, U2 in the register).
3. Join the metric by the tenant representation chosen in Ask First 3: option A dimension (per-tenant graph), option B `stats ... by tenantId` in Logs Insights ([monitoring D2](../../monitoring-quarkus-lambda-v3-40/blueprints/ask-first-decisions.md#d2-tenant-as-dimension-or-in-the-log)), option C proxy dimension then drill down in the logs.

Logs Insights field discovery works only in the Standard log class and extracts at most 200 fields from a JSON log ([logging Quick Reference](../../logging-quarkus-lambda-v3-40/SKILL.md#quick-reference)).

## What the recipe does not claim

- No trace id inside the log line (U9).
- No local proof of the JVM MDC path: dev and test go through the poll loop (medium confidence, [logging](../../logging-quarkus-lambda-v3-40/blueprints/mdc-and-request-id.md#per-mode-behaviour)).
- No trace id assertion in local tests: whether the mock event server sends `Lambda-Runtime-Trace-Id` is (unverified, U8 in the register).
- With an HTTP API there is no API Gateway node and the trace starts at the Lambda segment ([API Gateway HTTP API vs REST API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)).
