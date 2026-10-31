# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). stripe-java 34.0.0, Quarkus 3.40.1.1, Quarkiverse amazon-services 3.23.0. Fetched 2026-10-28. All code is illustrative: it was not compiled or run (medium confidence).

## Contents

- [1. StripeClient producer](#1-stripeclient-producer)
- [2. Secrets from Secrets Manager or SSM](#2-secrets-from-secrets-manager-or-ssm)
- [3. Explicit timeouts](#3-explicit-timeouts)
- [4. Raw body as bytes](#4-raw-body-as-bytes)
- [5. Signature header](#5-signature-header)
- [6. SQS hand-off before 2xx](#6-sqs-hand-off-before-2xx)
- [7. Event-id dedupe](#7-event-id-dedupe)
- [8. Business idempotency keys](#8-business-idempotency-keys)
- [9. Tenant lookup](#9-tenant-lookup)

## 1. StripeClient producer

The README shows `new StripeClient("sk_test_...")`; the legacy pattern "is still available to use but will be marked as deprecated soon" and "new API endpoints will only be accessible in the StripeClient" ([README](https://github.com/stripe/stripe-java/blob/v34.0.0/README.md)). In Lambda "Objects declared outside of the function's handler method remain initialized" ([runtime environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)) and an environment handles one request at a time ([concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html)), so one client per environment is enough. Stripe states no thread-safety guarantee for `StripeClient`; the only wording is that `withStripeContext` "is useful for creating thread-safe clients with different contexts" (medium confidence, absence of evidence). Do not share mutable `RequestOptions` builders between threads.

Scope choice: `@Singleton` has no client proxy but cannot be mocked with `@InjectMock` unless `@MockitoConfig(convertScopes = true)`; `@ApplicationScoped` needs a proxy of `StripeClient` (neighbour skill `developing-quarkus-arc-v3-40`, which cites the [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing) and the [CDI guide](https://quarkus.io/version/3.40/guides/cdi); medium confidence, L5: pages cited by the neighbour skill, not re-fetched).

```java
// Quarkus 3.40.1.1 + stripe-java 34.0.0 (illustrative, medium confidence)
@Singleton
public class StripeClientProducer {
    @Produces
    @Singleton
    StripeClient stripeClient(@ConfigProperty(name = "stripe.api-key") String apiKey,
                              @ConfigProperty(name = "stripe.connect-timeout-ms") int connectMs,
                              @ConfigProperty(name = "stripe.read-timeout-ms") int readMs,
                              @ConfigProperty(name = "stripe.max-network-retries") int retries) {
        return StripeClient.builder().setApiKey(apiKey)
                .setConnectTimeout(connectMs).setReadTimeout(readMs)
                .setMaxNetworkRetries(retries).build();
    }
}
```

## 2. Secrets from Secrets Manager or SSM

Stripe: "Never put secret API keys in source code"; "Use your platform's secrets management tools (such as a secrets vault)"; it lists "AWS Secrets Manager: Integrates with IAM and supports automatic rotation" and says to "Use restricted API keys with limited permissions instead of unrestricted secret API keys" ([keys best practices](https://docs.stripe.com/keys-best-practices)). The webhook secret is unique per endpoint and differs between test and live keys ([webhooks](https://docs.stripe.com/webhooks)). The Quarkiverse config source loads values "once at startup (the config source does not poll for updates)" ([Quarkiverse Secrets Manager page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html), as cited by the neighbour skill `integrating-quarkus-amazon-messaging-v3-40`, not re-fetched here; medium confidence, L5); rotation consequences: [D4](./ask-first-decisions.md#d4-secrets-and-snapstart).

```properties
# Quarkiverse amazon-services 3.23.0 config source (mechanism owned by the messaging skill)
quarkus.secretsmanager.config.enabled=true
quarkus.secretsmanager.config.secrets."stripe.api-key"=prod/stripe/restricted-key
quarkus.secretsmanager.config.secrets."stripe.webhook-secret"=prod/stripe/whsec-payments-endpoint
```

## 3. Explicit timeouts

Builder fields default to `Stripe.DEFAULT_CONNECT_TIMEOUT` (`30 * 1000`) and `DEFAULT_READ_TIMEOUT` (`80 * 1000`) ms ([Stripe.java](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java)). "StripeClient defaults to zero retries and doesn't inherit legacy global retry settings" ([error handling](https://docs.stripe.com/error-low-level?lang=java)); the legacy global is `maxNetworkRetries = 2`. Retries sleep with `Thread.sleep`, base 500 ms doubling to 5 s, jitter 0.75 to 1.0 (medium confidence, M16: HttpClient.java was read only in a targeted way through a summarising tool, no verbatim quote recorded) ([HttpClient.java](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/HttpClient.java)). API Gateway integration timeout: REST 29 s (raisable for Regional and private APIs, [REST API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html)), HTTP API 30 s maximum, not raisable ([HTTP API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html)). The README warns "Please take care to set conservative read timeouts" ([README](https://github.com/stripe/stripe-java/blob/v34.0.0/README.md)).

Budget check (medium confidence): `(1 + retries) x (connect + read) + backoff` must stay below the gateway timeout and the Lambda timeout. The numbers are Ask First [D1](./ask-first-decisions.md#d1-timeout-and-retry-values); keep them in configuration, never inline.

```properties
# application.properties - placeholders, fill from the D1 answer
stripe.connect-timeout-ms=<ms>
stripe.read-timeout-ms=<ms>
stripe.max-network-retries=<count>
```

## 4. Raw body as bytes

"Stripe requires the raw body of the request to perform signature verification… Any manipulation to the raw body of the request causes the verification to fail" ([webhooks](https://docs.stripe.com/webhooks)); Stripe's Java example reads `requestBody.readAllBytes()` as UTF-8 ([manage webhook endpoints](https://docs.stripe.com/webhooks/event-notification-handlers?lang=java)). Quarkus REST maps `byte[]` to "The entire request body, not decoded" and any unlisted type "Will be mapped from JSON to that type" ([guide](https://quarkus.io/version/3.40/guides/rest)). The 3.40.1.1 handlers use `Base64.getDecoder().decode(body)` when `isBase64Encoded` is true, else a UTF-8 copy, in both the [HTTP](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java) and the [REST](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java) extension. When the HTTP API sets `isBase64Encoded` for a JSON POST is not documented (medium confidence, absence of evidence); both paths yield the original bytes.

Both extensions use Lambda proxy integrations, so the "Body Mapping Template" advice of the existing webhooks skill does not apply (contradiction C1 in the [register](./unverified-and-risks.md#contradictions)).

```java
public Response receive(byte[] body, @Context HttpHeaders headers) {
    String payload = new String(body, StandardCharsets.UTF_8);   // verify this exact string
```

## 5. Signature header

The header "contains a timestamp and one or more signatures", as `t=...,v1=...,v0=...` on a single line ([webhooks](https://docs.stripe.com/webhooks)). The HTTP handler adds each `header.getValue().split(",")` piece as a separate value unless the name is `access-control-request-headers`; the REST handler copies `multiValueHeaders` as-is (medium confidence, M15: handler source read through a summarising tool; [HTTP handler](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java), [REST handler](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java)). For a non-collection `@HeaderParam` with several values "the first value (lexically) of the parameter is used", while `getHeaderString` joins values "separated by a ',' character" (medium confidence, L2: both javadocs were read on the `main` branch, not the 3.1 tag Quarkus 3.40 uses; the quotes are recorded here; [HeaderParam](https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/HeaderParam.java), [HttpHeaders](https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/core/HttpHeaders.java)). A single-valued `@RestHeader String` is the alternative weighed in Ask First [D9](./ask-first-decisions.md#d9-signature-header-parameter), where the untested end-to-end effect is tagged (unverified). Use the same code for both extensions.

```java
String sig = headers.getHeaderString("Stripe-Signature");   // @Context jakarta.ws.rs.core.HttpHeaders
Event event = stripe.constructEvent(payload, sig, webhookSecret);  // 3-argument form, default tolerance
```

## 6. SQS hand-off before 2xx

Stripe: "Quickly return a successful status code (2xx) before any complex logic that might cause a timeout" and "process incoming events with an asynchronous queue"; a 3xx counts as a failure ([webhooks](https://docs.stripe.com/webhooks)). In Lambda, background work that "did not complete when the function ended" resumes only "if Lambda reuses the execution environment" ([runtime environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)). So the queue write finishes inside the invocation. If it fails, let the error end as a 5xx: Stripe retries live-mode deliveries "for up to three days with an exponential back off" ([webhooks](https://docs.stripe.com/webhooks)). Stripe publishes no numeric response timeout (medium confidence, absence of evidence); keep the path to verify plus one send.

```java
sqs.sendMessage(b -> b.queueUrl(queueUrl).messageBody(payload));   // completes before returning
return Response.ok().build();
```

## 7. Event-id dedupe

Stripe: "Webhook endpoints might occasionally receive the same event more than once… logging the event IDs you've processed"; do not use `created` "to determine event order or whether you've already processed an event" ([webhooks](https://docs.stripe.com/webhooks)). DynamoDB: `attribute_not_exists` "is true only when no item with that Id value already exists"; the failed write reads "The conditional request failed" ([condition expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)). SQS-triggered Lambdas are also at-least-once ([Lambda with SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html), as cited by the neighbour skill `integrating-quarkus-amazon-messaging-v3-40`, not re-fetched here; medium confidence, L5), so dedupe in the consumer. Keep items at least 30 days: retries span 3 days, Dashboard resend 15 days, CLI resend 30 days ([webhooks](https://docs.stripe.com/webhooks)); the retention length is an inference (medium confidence). The SDK exception class name below is (medium confidence). Table design belongs to `integrating-quarkus-amazon-data-v3-40`.

```java
boolean claim(String eventId, long ttlEpochSeconds) {
    try {
        dynamo.putItem(b -> b.tableName(dedupeTable)
            .item(Map.of("pk", AttributeValue.fromS("stripe#" + eventId),
                         "status", AttributeValue.fromS("PROCESSING"),
                         "ttl", AttributeValue.fromN(Long.toString(ttlEpochSeconds))))
            .conditionExpression("attribute_not_exists(pk)"));
        return true;
    } catch (ConditionalCheckFailedException duplicate) { return false; }   // skip, let SQS delete
}
```

## 8. Business idempotency keys

"If your application retries across separate SDK calls or process restarts, generate and persist a key for the operation and supply it to every attempt"; strategies are "UUID v4" or "Derive the key from a user-attached object, like the ID of a shopping cart" ([error handling](https://docs.stripe.com/error-low-level?lang=java)). Keys are "up to 255 characters", "Avoid using sensitive data", incoming parameters are compared with the original ([idempotent requests](https://docs.stripe.com/api/idempotent_requests)). stripe-java 34.0.0 sets a random UUID on a POST without a user key, and its internal retries resend the same request ([StripeRequest.java](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/StripeRequest.java)), so the SDK protects only its own retries. A client retry through API Gateway is a new invocation with a new request id and API Gateway does not retry Lambda invocations ([API Gateway errors](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html)); that a request-id key therefore adds nothing is an inference (medium confidence). For SQS-driven calls base the key on the event id or the business key.

```java
// derived business key: the composition is this skill's design (Stripe's example: a cart id)
String key = "t:" + tenantId + ":checkout:" + orderId;     // <= 255 chars, no personal data
RequestOptions opts = RequestOptions.builder().setIdempotencyKey(key).build();
PaymentIntent pi = stripe.v1().paymentIntents().create(params, opts);  // identical params on every retry
```

## 9. Tenant lookup

Metadata lets you "store your user's unique identifier from your system on a Stripe Customer"; limits are 50 pairs, 40-character keys, 500-character values; "Never store sensitive information" there ([metadata](https://docs.stripe.com/metadata)). This is the recommendation of Ask First D10, not an Always Do. For a Stripe webhook this skill's own design (not family rule 6, which covers the path case) is that the authoritative record is `stripeCustomerId -> tenantId` in your table and metadata is a reconciliation hint (Ask First D10). Metadata being writable by any holder of a secret key or Dashboard access is an inference (medium confidence). Full flow: [webhook pipeline](./webhook-pipeline.md#tenant-mapping).

```java
String tenantId = tenantMapping.findTenantByStripeCustomer(customerId).orElseThrow();
```
