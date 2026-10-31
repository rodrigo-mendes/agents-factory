# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). stripe-java 34.0.0, Quarkus 3.40.1.1. Fetched 2026-10-28. Code is illustrative and was not compiled (medium confidence). Every Never Do rests on High claims only; every alternative names only options that are confirmed. Open choices and harm claims of medium or unverified confidence live in an [Ask First](./ask-first-decisions.md) item (D9, D10). Ids follow the research numbering; N2 is not used.

## Contents

- [N1. POJO body before verification](#n1-pojo-body-before-verification)
- [N3. Background thread after 2xx](#n3-background-thread-after-2xx)
- [N4. Default timeouts behind API Gateway](#n4-default-timeouts-behind-api-gateway)
- [N5. Request id as idempotency key](#n5-request-id-as-idempotency-key)
- [N6. Tenant from the path alone](#n6-tenant-from-the-path-alone)
- [N7. Tolerance 0 or no verification](#n7-tolerance-0-or-no-verification)
- [N8. Legacy global key or literal key](#n8-legacy-global-key-or-literal-key)

## N1. POJO body before verification

Any body type other than the listed raw types "Will be mapped from JSON to that type" ([Quarkus REST guide](https://quarkus.io/version/3.40/guides/rest)); "Any manipulation to the raw body of the request causes the verification to fail" ([webhooks](https://docs.stripe.com/webhooks)). Impact: `No signatures found matching the expected signature for payload` ([manage webhook endpoints](https://docs.stripe.com/webhooks/event-notification-handlers?lang=java)); real events are rejected and retried for up to 3 days, then lost.

```java
// ❌ WRONG
@POST @Path("/stripe/webhook")
public Response receive(StripeEventDto event, @RestHeader("Stripe-Signature") String sig) { ... }
// ✅ CORRECT
@POST @Path("/stripe/webhook")
public Response receive(byte[] body, @Context HttpHeaders headers) throws SignatureVerificationException {
    Event e = stripe.constructEvent(new String(body, StandardCharsets.UTF_8),
                                    headers.getHeaderString("Stripe-Signature"), webhookSecret);
```

## N3. Background thread after 2xx

"Background processes or callbacks that were initiated by your Lambda function and did not complete when the function ended resume if Lambda reuses the execution environment" ([runtime environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)). Impact: events acknowledged to Stripe (no retry) but never processed.

```java
// ❌ WRONG
executor.submit(() -> fulfil(event));      // Lambda freezes after the response
return Response.ok().build();
// ✅ CORRECT
sqs.sendMessage(b -> b.queueUrl(queueUrl).messageBody(payload));   // completes first
return Response.ok().build();                                       // send failure -> 5xx -> Stripe retries
```

## N4. Default timeouts behind API Gateway

Defaults are 30 s connect and 80 s read ([Stripe.java](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java)); the gateway integration timeout is 29 s for a REST API, raisable for Regional and private APIs ([REST API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html)), and at most 30 s for an HTTP API, not raisable ([HTTP API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html)). Impact: the client gets 504 while the Stripe POST may still succeed, so the outcome is unknown and must be reconciled ([error handling](https://docs.stripe.com/error-low-level?lang=java)). The numbers below are examples only; the real values are Ask First [D1](./ask-first-decisions.md#d1-timeout-and-retry-values) and the budget formula is (medium confidence).

```java
// ❌ WRONG
return new StripeClient(apiKey);        // 30 000 / 80 000 ms
// ✅ CORRECT
return StripeClient.builder().setApiKey(apiKey)
        .setConnectTimeout(connectMs).setReadTimeout(readMs).setMaxNetworkRetries(retries).build();
```

## N5. Request id as idempotency key

Stripe wants a key that identifies one operation and is reused on every attempt ([error handling](https://docs.stripe.com/error-low-level?lang=java)); a per-invocation id is not such a key. The concrete harm claim is unconfirmed: Ask First [D10](./ask-first-decisions.md#d10-request-id-key-and-customer-metadata-harm-claims). Stripe's own example derives the key from a user-attached object such as a shopping cart id; the composition used below is this skill's design ([pattern 8](./always-do-patterns.md#8-business-idempotency-keys)).

```java
// ❌ WRONG
RequestOptions.builder().setIdempotencyKey(lambdaContext.getAwsRequestId()).build();
// ✅ CORRECT (derived business key; the composition is this skill's design, pattern 8)
RequestOptions.builder().setIdempotencyKey("t:" + tenantId + ":checkout:" + orderId).build();
```

## N6. Tenant from the path alone

Family rule 6: "Multi-tenant isolation (tenant from token, never from path alone) is a 🚫 when violated". The webhook case is Ask First [D10](./ask-first-decisions.md#d10-request-id-key-and-customer-metadata-harm-claims); no claim is made here.

```java
// ❌ WRONG
String tenantId = uriInfo.getPathParameters().getFirst("tenantId");
// ✅ CORRECT (placeholder helper: the tenant comes from the verified token)
String tenantId = tenantFromVerifiedToken(securityIdentity);
```

## N7. Tolerance 0 or no verification

"Our libraries have a default tolerance of 5 minutes"; "Don't use a tolerance value of 0. Using a tolerance value of 0 disables the recency check entirely"; use NTP ([webhooks](https://docs.stripe.com/webhooks)). Whether the Lambda host clock is synchronised is not stated on any page read (unverified). The `*WithoutVerification` constructors are for cloud-provider transports only ([manage webhook endpoints](https://docs.stripe.com/webhooks/event-notification-handlers?lang=java)). Impact: replay or forged events.

```java
// ❌ WRONG
stripe.constructEvent(payload, sig, secret, 0);
// ✅ CORRECT
stripe.constructEvent(payload, sig, secret);     // default tolerance 300 s
```

## N8. Legacy global key or literal key

`Stripe.apiKey` is still `public static volatile String apiKey;` in 34.0.0 and "will be marked as deprecated soon" ([README](https://github.com/stripe/stripe-java/blob/v34.0.0/README.md), [Stripe.java](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java)); "Never put secret API keys in source code" ([keys](https://docs.stripe.com/keys-best-practices)). Impact: a global shared key, no per-client timeouts, key leaked through the repository.

```java
// ❌ WRONG
Stripe.apiKey = "sk_live_...";
// ✅ CORRECT
@Inject StripeClient stripe;      // producer reads stripe.api-key from the Secrets Manager config source
```
