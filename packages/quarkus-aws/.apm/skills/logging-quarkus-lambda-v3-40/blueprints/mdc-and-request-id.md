# MDC and Request Id per Mode

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. The per-mode facts below were read from Quarkus source at tag 3.40.1.1, not from a guide (medium confidence, M2 in the register).

## Contents

- [Per-mode behaviour](#per-mode-behaviour)
- [Handler pattern](#handler-pattern)
- [HTTP extension variant](#http-extension-variant)
- [Two MDC classes](#two-mdc-classes)
- [Key spelling](#key-spelling)
- [Queries](#queries)

## Per-mode behaviour

| Mode | Who puts `AWSRequestId` into MDC | Evidence |
|---|---|---|
| Native (OS-only runtime) | the Quarkus poll loop; removed in `finally` | `AmazonLambdaProcessor` starts the poll loop `onlyIf = NativeBuild.class`; `AbstractLambdaPollLoop` calls `MDC.put("AWSRequestId", requestId)` and `MDC.remove("AWSRequestId")` ([poll loop](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java), [processor](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/deployment/src/main/java/io/quarkus/amazon/lambda/deployment/AmazonLambdaProcessor.java)) (medium confidence) |
| Dev and test (mock event server) | the same poll loop | same sources (medium confidence) |
| JVM on a managed Java runtime | nobody: `QuarkusStreamHandler.handleRequest` to `AmazonLambdaRecorder.handle` has no MDC code, so the handler must | [QuarkusStreamHandler](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/runtime/src/main/java/io/quarkus/amazon/lambda/runtime/QuarkusStreamHandler.java), [AmazonLambdaRecorder](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AmazonLambdaRecorder.java) (medium confidence, absence of MDC code) |

Consequences:

- Put the id yourself in JVM mode and clear it in `finally`. The poll loop's own `finally` removes only `AWSRequestId`, so keys you add (`tenantId`) are yours to clear.
- Do not rely on a test that passes through the mock event server to prove the JVM path: dev and test go through the poll loop (medium confidence).
- The poll loop does not read `AWS_LAMBDA_LOG_LEVEL` or `AWS_LAMBDA_LOG_FORMAT` (medium confidence). Whether any other Quarkus 3.40 component does is (unverified); Lambda `LoggingConfig` alone does not change Quarkus levels or format.
- `AWS_LAMBDA_LOG_GROUP_NAME` and `AWS_LAMBDA_LOG_STREAM_NAME` are not available under SnapStart ([AWS env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)); the MDC id is the stable correlation key.

## Handler pattern

Illustrative body (medium confidence); class shapes follow the Lambda guide. The tenant comes from the verified token (family rule 6).

```java
// Quarkus 3.40.1.1 - Init: nothing to initialise for logging
// Usage: per invocation, MDC put -> log -> MDC remove in finally
@Named("orders")
public class OrdersLambda implements RequestHandler<OrderEvent, OrderResult> {
    @Override
    public OrderResult handleRequest(OrderEvent event, Context context) {
        MDC.put("AWSRequestId", context.getAwsRequestId());
        MDC.put("tenantId", tenantFromVerifiedToken(event));
        try {
            Log.info("order received");
            OrderResult r = process(event);
            Log.info("order processed");
            return r;
        } catch (RuntimeException e) {
            Log.error("order failed", e);      // exception-output-type=detailed by default
            throw e;
        } finally {
            MDC.remove("tenantId");
            MDC.remove("AWSRequestId");
        }
    }
}
```

AWS's Java sample shows `Context` carrying `awsRequestId`, "the unique request id of the invocation" ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)).

## HTTP extension variant

With `quarkus-amazon-lambda-http` (preview, "This technology is considered preview", [guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) and Quarkus REST, the Lambda `Context` is injectable with `@Context` in Jakarta REST resources, or `@Inject` elsewhere ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). See `developing-quarkus-amazon-lambda-http-v3-40`. Whether a Jakarta REST filter is a better place for the put and remove is not covered by any page read (medium confidence, design choice).

```java
// Quarkus 3.40.1.1 - quarkus-amazon-lambda-http + quarkus-rest (illustrative, medium confidence)
@Path("/orders")
public class OrdersResource {
    @POST
    public Response create(@Context com.amazonaws.services.lambda.runtime.Context lambda, Order o) {
        MDC.put("AWSRequestId", lambda.getAwsRequestId());
        try { Log.info("create order"); return Response.ok().build(); }
        finally { MDC.remove("AWSRequestId"); }
    }
}
```

## Two MDC classes

- The 3.40 guide's MDC examples use `org.jboss.logmanager.MDC` ([logging guide](https://quarkus.io/version/3.40/guides/logging)).
- The Quarkus Lambda poll loop uses `org.jboss.logging.MDC` ([poll loop](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java)).
- Whether both write to the same store is (unverified). Default to the guide's class and check that one JSON line carries `mdc` before shipping; the follow-up is the jboss-logging `LoggerProvider` for JBoss LogManager.
- The JSON output carries MDC under `"mdc"` ([logging guide](https://quarkus.io/version/3.40/guides/logging)); `quarkus.log.console.json.mdc.flat-fields=true` moves entries to the root (default `false`).

## Key spelling

Lambda's own Java JSON objects carry the request id as `AWSrequestId` ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)); the AWS log4j2 example and the Quarkus poll loop use `AWSRequestId`. Whether Logs Insights field names are case sensitive is (unverified). For queries that span Lambda-generated and Quarkus-generated lines, query both spellings or standardise on the MDC key.

## Queries

Logs Insights field discovery works only in the Standard log class, extracts at most 200 fields from a JSON log, and uses dot notation for nested JSON ([discovered fields](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html)). Queries on `mdc.<key>` against Quarkus output are an inference (medium confidence); the query text is in the [Verification Loop](./verification-loop.md#logs-insights-queries).
