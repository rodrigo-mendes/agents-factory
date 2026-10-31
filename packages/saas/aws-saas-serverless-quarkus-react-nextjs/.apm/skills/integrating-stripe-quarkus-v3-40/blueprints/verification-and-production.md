# Verification and Production Readiness

Back to [SKILL.md](../SKILL.md). stripe-java 34.0.0, Quarkus 3.40.1.1. Fetched 2026-10-28. Commands are representative: adapt them to the environment; none was executed during research. Code is illustrative and was not compiled (medium confidence).

## Contents

- [Verification Loop](#verification-loop)
- [Mocking](#mocking)
- [Gateway integration](#gateway-integration)
- [Production readiness](#production-readiness)

## Verification Loop

```bash
# 1. Version pin
mvn -q dependency:tree -Dincludes=com.stripe:stripe-java
# Expected: com.stripe:stripe-java:jar:34.0.0
# 2. No legacy global key; review every default client
grep -rn "Stripe.apiKey" src/main/java && echo "FORBIDDEN (N8)"
grep -rn "new StripeClient(" src/main/java && echo "check defaults 30 s / 80 s (N4)"
# Expected: no output from the first grep
# 3. Webhook resource takes byte[] and joins the header
grep -rn '@RestHeader("Stripe-Signature") String' src/main/java && echo "review (Ask First D9)"
grep -rn 'getHeaderString("Stripe-Signature")' src/main/java
# Expected: 1 match
# 4. Local end-to-end with the Stripe CLI (dev-mode mock event server listens on 8080)
stripe listen --forward-to localhost:8080/stripe/webhook   # prints a whsec_ value for the dev profile
stripe trigger payment_intent.succeeded
# Expected: 200 in the Quarkus dev log and one SQS message
# 5. SnapStart version state: both the setting and the version state
aws lambda get-function-configuration --function-name billing:live --query '{SnapStart: SnapStart, State: State}'
# Expected: SnapStart.OptimizationStatus On AND State Active (a version still being optimised is not ready)
```

Whether the dev-mode mock event server takes the same comma-split path as production is not documented (unverified); keep the signature test below.

## Mocking

Stripe signature = HMAC-SHA256(secret, `t` + "." + payload), header `t=<t>,v1=<hex>` ([webhooks](https://docs.stripe.com/webhooks)). Test with `quarkus-junit` and RestAssured against the mock event server; `quarkus-test-amazon-lambda` was removed in Quarkus 3.31 ([migration guide](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)).

```java
String payload = "{\"id\":\"evt_test_1\",\"object\":\"event\",\"type\":\"payment_intent.succeeded\",\"data\":{\"object\":{}}}";
long t = java.time.Instant.now().getEpochSecond();
String v1 = hmacSha256Hex("whsec_test", t + "." + payload);       // test helper using javax.crypto.Mac "HmacSHA256"
given().contentType("application/json").header("Stripe-Signature", "t=" + t + ",v1=" + v1)
       .body(payload)
   .when().post("/stripe/webhook")
   .then().statusCode(200);        // proves the byte[] body and the joined header survive the HTTP handler
// Negative: the same request with changed whitespace in the payload -> 400
// Replace SqsClient with a test @Alternative or @InjectMock (normal scope needed); no real Stripe call
```

An API-version mismatch between the test JSON and the SDK pin empties `getObject()` (internal skill `handling-stripe-webhooks-v34`): assert on `event.getId()` and `getType()` only.

## Gateway integration

| Gateway | Quarkus extension | Body to the resource | `Stripe-Signature` |
|---|---|---|---|
| HTTP API (payload 2.0) | `quarkus-amazon-lambda-http` | base64-decoded when `isBase64Encoded`, else UTF-8 copy | split on "," by the handler (medium confidence, M15), so use `getHeaderString`; payload 2.0 combines duplicate headers with commas and lowercases names ([HTTP API Lambda integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html)) |
| REST API (proxy) | `quarkus-amazon-lambda-rest` | same rule; with binary media types configured the request arrives base64-encoded ([payload encodings](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-payload-encodings-workflow.html)) | `multiValueHeaders` copied as-is; a single comma-bearing value stays one value ([proxy integrations](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html)) |

Stripe's "Body Mapping Template" advice targets non-proxy integrations, not this path (contradiction C1). The binary-media-type requirement of the REST extension belongs to `developing-quarkus-amazon-lambda-http-v3-40`.

## Production readiness

- Performance: init work (Secrets Manager fetch, client build) moves into the snapshot with SnapStart; SDK retries block the thread with `Thread.sleep` ([HttpClient.java](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/HttpClient.java)). Spikes "during the beginning of the month when all subscriptions renew" are why Stripe wants a queue ([webhooks](https://docs.stripe.com/webhooks)). Lambda provisions one environment per concurrent request (1,000 default account concurrency) ([concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html)); capping the consumer protects Stripe rate limits (medium confidence).
- Scalability: up to 16 event destinations; subscribe only to required event types ("Listening for extra events (or all events)… we don't recommend it") ([webhooks](https://docs.stripe.com/webhooks)).
- Monitoring: alarm on webhook 4xx and 5xx at the gateway and on SQS age of oldest message; log request id, tenant id and `evt_` id, no personal data and no keys (family rule 7; [keys](https://docs.stripe.com/keys-best-practices): do not expose key variables in diagnostics). The Workbench "Event deliveries" tab shows per-attempt status ([webhooks](https://docs.stripe.com/webhooks)).
- Security checklist:
  - [ ] restricted API key per function from Secrets Manager; rotate periodically ([keys](https://docs.stripe.com/keys-best-practices))
  - [ ] webhook secret rolled periodically; rotation window handling: Ask First D4
  - [ ] HTTPS only, TLS v1.2 or v1.3 ([webhooks](https://docs.stripe.com/webhooks)); IP allowlist where the gateway allows it (D7)
  - [ ] snapshot KMS key choice (D4)
  - [ ] no Stripe call and no key or ID generation in `beforeCheckpoint`
  - [ ] tenant resolved per [pattern 9](./always-do-patterns.md#9-tenant-lookup)
