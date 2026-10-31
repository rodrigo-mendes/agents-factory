# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Fetched 2026-10-28. Each item lists options and tradeoffs; the user decides. No option here is a default.

## Contents

- [D1. Timeout and retry values](#d1-timeout-and-retry-values)
- [D2. JVM + SnapStart or native](#d2-jvm--snapstart-or-native)
- [D3. DNS cache TTL](#d3-dns-cache-ttl)
- [D4. Secrets and SnapStart](#d4-secrets-and-snapstart)
- [D5. Webhook transport](#d5-webhook-transport)
- [D6. SQS message content](#d6-sqs-message-content)
- [D7. Inbound IP allowlist and gateway type](#d7-inbound-ip-allowlist-and-gateway-type)
- [D8. Customers or Connect](#d8-customers-or-connect)
- [D9. Signature header parameter](#d9-signature-header-parameter)
- [D10. Request id key and Customer metadata harm claims](#d10-request-id-key-and-customer-metadata-harm-claims)

## D1. Timeout and retry values

The numbers are a design choice and the budget formula `(1 + retries) x (connect + read) + backoff` is (medium confidence). Inputs: defaults 30 s / 80 s, `StripeClient` retries 0, backoff 0.5 to 5 s (medium confidence, M16) ([Stripe.java](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java), [HttpClient.java](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/HttpClient.java)); gateway timeout 29 s REST, raisable for Regional and private APIs ([REST API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html)), and 30 s HTTP API maximum, not raisable ([HTTP API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html)). The README: a short timeout "increases the likelihood of a problem within our servers" ([README](https://github.com/stripe/stripe-java/blob/v34.0.0/README.md)).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A short read timeout, 0 retries | fits the gateway budget easily | an unknown outcome must be reconciled ([error handling](https://docs.stripe.com/error-low-level?lang=java)) | synchronous PaymentIntent create for a UI |
| B moderate timeout, 1 retry | absorbs one transient error | `Thread.sleep` backoff consumes the budget | low-latency retrieve or update |
| C Stripe calls inside the SQS worker, defaults kept | Stripe's "conservative read timeouts" | asynchronous UX (client polls or waits for the webhook) | subscription and billing back-office work |

Ask: "Which API Gateway type, which Lambda timeout, and can the call be asynchronous? Then compute the budget." The SQS worker is bounded by the Lambda timeout and the SQS visibility timeout (internal skill `integrating-quarkus-amazon-messaging-v3-40`).

## D2. JVM + SnapStart or native

Native is never a default (family rule 3). stripe-java documents no GraalVM support (medium confidence, absence of evidence; [README](https://github.com/stripe/stripe-java/blob/v34.0.0/README.md)); maintainers wrote "We have not looked into supporting GraalVM" (2024-11-04) and marked it "not planned" (2026-06-18) ([issue 1905](https://github.com/stripe/stripe-java/issues/1905)); a 2021 Quarkus native build failed because Gson could not instantiate `com.stripe.model.Event` ([issue 1199](https://github.com/stripe/stripe-java/issues/1199)); a community report (not Stripe; medium confidence, issue thread read as a tool summary, L1) of a silent native failure on nested `TaxIdListParams.Owner` is dated 2026-09-30 ([issue 1905](https://github.com/stripe/stripe-java/issues/1905)). SnapStart supports Java managed runtimes, not OS-only runtimes ([SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)).

| Option | Optimizes | Sacrifices |
|---|---|---|
| A JVM + SnapStart | no Stripe-specific build configuration | key and client in the snapshot (D4); DNS conflict (D3) |
| B native | lowest memory and start time | no Stripe support; hand-maintained reflection registration; failures can be silent; no SnapStart |

Ask: "Is native required? If yes, require `@QuarkusIntegrationTest` coverage of every Stripe call path." Whether the registration workaround is complete is (medium confidence).

## D3. DNS cache TTL

Contradiction C2. Stripe README: set `networkaddress.cache.ttl` "to 60 seconds" because "default JVM configurations can have their DNS cache TTL set to forever" ([README](https://github.com/stripe/stripe-java/blob/v34.0.0/README.md)). AWS SnapStart: "Avoid using Java DNS cache", set it to 0; "Lambda Event Functions already cache DNS responses" ([SnapStart best practices](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-best-practices.html)); a cached lookup can cause "connection timeouts when the function resumes from a snapshot". Which value wins is (unverified); no page read settles it, so this skill gives no default.

| Option | Optimizes | Sacrifices |
|---|---|---|
| A 60 s | Stripe's stated reason (IPs not guaranteed static) | possible timeouts after a snapshot restore |
| B 0 | AWS SnapStart guidance; Lambda's managed DNS caching still applies | more lookups |

Ask: "Is SnapStart on? Which TTL do you choose, 60 s (Stripe README) or 0 (AWS SnapStart guidance)?" Present both quotes above and wait for the answer; do not pick one on the user's behalf.

## D4. Secrets and SnapStart

A client built at init lives in the snapshot with the key, encrypted with an AWS managed key by default or a customer managed KMS key ([snapstart-security](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-security.html)). AWS: "The state of connections… isn't guaranteed" after restore, and only AWS SDK connections automatically resume in most cases, so stripe-java must re-establish its own; re-establish connections in the handler or an after-restore hook; dummy invocations must not start "business transactions" ([best practices](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-best-practices.html)). Whether `StripeClient.build()` performs network I/O is assumed none and was not verified (unverified).

| Option | Optimizes | Sacrifices |
|---|---|---|
| A build at init, no Stripe call before the snapshot | class loading out of the invoke path | key in the snapshot |
| B prime with a Stripe call in `beforeCheckpoint` | warmer TLS and classes | connection state not guaranteed; avoid unless measured; GET only if at all |
| C build lazily on first invocation | key never in the snapshot | first-request latency |

Rotation: the Secrets Manager config source loads once at startup and the snapshot freezes the value, so a rotation needs a new published version (medium confidence). Stripe can delay old webhook-secret expiry "for up to 24 hours" and signs once per active secret ([webhooks](https://docs.stripe.com/webhooks)); updating Secrets Manager and publishing a new version inside that window is (medium confidence). Do not generate keys or IDs in `beforeCheckpoint`; SDK idempotency UUIDs are generated per request ([StripeRequest.java](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/StripeRequest.java)); retry jitter uses `ThreadLocalRandom` and its restored state could repeat across environments, low impact (medium confidence).

Ask: "Is a secret in the KMS-encrypted snapshot acceptable, and is a customer managed key required?"

## D5. Webhook transport

| Option | Optimizes | Sacrifices |
|---|---|---|
| A public webhook, API Gateway to Quarkus to SQS | full control; supports `issuing_authorization.request` and Checkout redirect behaviour; manual resend (Dashboard 15 days, CLI 30 days) | you own raw body, header, signature, 2xx latency |
| B Stripe event destination to Amazon EventBridge | no public endpoint; "verification isn't needed" for cloud providers; targets include Lambda, SQS, SNS, Step Functions | partner event source must be associated "within 7 days" or the destination is disabled; "You can't manually resend events to Amazon EventBridge through Stripe"; payload wrapped in `detail`; not supported by event notification handlers on the public-preview channel |

Sources: [EventBridge destination](https://docs.stripe.com/event-destinations/eventbridge), [webhooks](https://docs.stripe.com/webhooks), [manage webhook endpoints](https://docs.stripe.com/webhooks/event-notification-handlers?lang=java). The fit to this architecture is (medium confidence). Ask: "Is a public endpoint acceptable, and are response-dependent event types needed?"

## D6. SQS message content

Option A: the verified payload; the consumer needs no Stripe call, bounded by the SQS 1 MiB limit ([SQS quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html)) and by the event size, which Stripe does not state on the pages read (unverified). Option B: `evt_` id and type, or a thin event; the consumer calls the Stripe API for the latest state, matching the Thin payload Stripe recommends for new destinations ([webhooks](https://docs.stripe.com/webhooks)); thin events use `parseEventNotification` (skill `handling-stripe-webhooks-v34`). Ask: "Snapshot or thin events? Can payloads exceed 1 MiB?" (then an S3 reference, owned by the messaging skill).

## D7. Inbound IP allowlist and gateway type

Stripe: use IP allowlisting and signature verification, "Use both of these protections" ([webhooks](https://docs.stripe.com/webhooks)). AWS WAF attaches to REST API only; HTTP API has none ([API Gateway comparison](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)). Infrastructure code is out of scope (`provisioning-aws-api-gateway-v6`). Ask: "Must the Stripe IP list be enforced at the edge? If yes, REST API."

## D8. Customers or Connect

Option A: one platform account, tenant to Customer. Option B: tenant as connected account; `withStripeContext` "is useful for creating thread-safe clients with different contexts" ([StripeClient.java](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/StripeClient.java)) and event destinations choose `@self` or `@accounts` ([webhooks](https://docs.stripe.com/webhooks)). Connect is out of scope beyond this pointer. Ask: "Do tenants receive payouts, or only pay you?"

## D9. Signature header parameter

The High rule (take the header as Stripe sends it) is Always Do 5; the claims below are medium or unverified.

**Signature header (medium confidence, M15 and L2).** The 3.40.1.1 HTTP handler splits header values on "," and the REST handler copies `multiValueHeaders` as-is ([HTTP handler](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java), [REST handler](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java)). For a non-collection `@HeaderParam` "the first value (lexically) of the parameter is used"; `getHeaderString` joins values "separated by a ',' character" (javadoc read on the `main` branch: [HeaderParam](https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/HeaderParam.java), [HttpHeaders](https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/core/HttpHeaders.java)). The Stripe header is `t=...,v1=...,v0=...` on one line ([webhooks](https://docs.stripe.com/webhooks)). That a single-valued `@RestHeader String` then sees only `t=...` and fails verification on every delivery is an inference that was not tested (unverified), as is whether the dev-mode mock event server takes the same split path.

| Option | Optimizes | Sacrifices |
|---|---|---|
| A `@Context HttpHeaders` and `getHeaderString("Stripe-Signature")` | gets the comma-joined value, the same code for both extensions | an extra parameter type in the resource method |
| B single-valued `@RestHeader String` | shortest signature | on the HTTP extension may see only the first value (unverified) |

Recommendation: A. Ask: "Is the signature header ever sent with a comma, or through a proxy that merges headers?" Keep the signature test in the Verification Loop either way.

## D10. Request id key and Customer metadata harm claims

Both harm claims below are inferences.

**Request id as idempotency key (medium confidence, M5).** Stripe wants one key per operation, reused on every attempt (a High statement, Never Do row 4). That a client retry arrives as a new invocation with a new request id, so the key creates a second operation and double charges, is an inference. Options: A a key derived from the business operation (Stripe's example derives it from a shopping cart id; the tenant + operation + business id composition `t:<tenant>:checkout:<orderId>` is this skill's own design, see [pattern 8](./always-do-patterns.md#8-business-idempotency-keys)); B request-id key. Recommendation: A. Ask: "Which business identifier is stable across client retries?"

**Customer metadata as tenant source (medium confidence, M6).** Family rule 6 is "Multi-tenant isolation (tenant from token, never from path alone) is a 🚫 when violated" (Never Do covers the path case). For a Stripe webhook this skill's own design goes further: the tenant is never taken from payload or Customer metadata alone. That metadata can be edited by anyone holding a key or Dashboard access, and so grants a plan across tenants if wrong, is an inference (medium confidence, M6). Options: A own table `stripeCustomerId -> tenantId`, metadata as a hint with an alert on mismatch; B metadata as the source (harm as above, medium confidence, M6). Recommendation: A. Ask: "Where is the authoritative Customer-to-tenant mapping stored?"
