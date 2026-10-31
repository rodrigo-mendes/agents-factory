---
name: integrating-stripe-quarkus-v3-40
description: "Integrates stripe-java 34.0.0 into Quarkus 3.40 LTS on AWS Lambda: StripeClient producer, secrets, timeouts, webhook raw body and signature, SQS hand-off, dedupe, idempotency keys, tenant mapping. Use when adding Stripe to a Quarkus Lambda. Not for Stripe API semantics or Quarkus 4."
---

# Integrating Stripe (stripe-java 34) in Quarkus 3.40 on AWS Lambda

> Version lock: every claim applies to **stripe-java 34.0.0 inside Quarkus 3.40 LTS (patch 3.40.1.1) on AWS Lambda behind API Gateway** only. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: what changes when stripe-java runs in a Quarkus Lambda (client wiring, time budget, secrets, webhook transport, hand-off, dedupe, idempotency keys, tenant mapping, JVM vs native). It complements, by name only (package stripe-java, not edited here): `developing-stripe-java-core-v34`, `processing-stripe-payments-v34`, `handling-stripe-webhooks-v34`, `managing-stripe-subscriptions-v34`; they own the Stripe API semantics, which this skill does not repeat. Other neighbours, by name only (other packages): `developing-quarkus-amazon-lambda-http-v3-40`, `developing-quarkus-amazon-lambda-v3-40`, `integrating-quarkus-amazon-messaging-v3-40`, `integrating-quarkus-amazon-data-v3-40`, `securing-quarkus-lambda-cognito-v3-40`; agents `stripe-integrator`, `stripe-advisor`. Out of scope: Terraform, Stripe.js, Connect beyond a pointer, Quarkus 4.

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| stripe-java | 34.0.0 is the only stable 34.x; Maven `<release>` points at pre-release 34.1.0-beta.1 (lastUpdated 2026-10-21); 34.0.0 released 2026-10-01 and default `Stripe-Version` 2026-09-30.endive (medium confidence, M13: taken from the neighbour skills `developing-stripe-java-core-v34` and `handling-stripe-webhooks-v34`, not re-fetched) | https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml ; https://github.com/stripe/stripe-java/releases ; https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md |
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 (2026-10-19) | https://quarkus.io/releases |
| HTTP extensions | `quarkus-amazon-lambda-http` (HTTP API, payload 2.0) and `quarkus-amazon-lambda-rest` (REST API): "This technology is considered preview" | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| Quarkiverse amazon-services | 3.23.0 (LTS), built on Quarkus 3.40.0; running it on patch 3.40.1.1 is (medium confidence) | https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom |
| Lambda Java runtimes | `java25`, `java21`, `java17.al2023` (deprecation 2029-06-30) | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html |
| SnapStart | Java 11+ managed runtimes; not OS-only runtimes (so not Quarkus native) | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Pre-releases 34.1.0-alpha.1 to alpha.4 and beta.1 exist; do not let tooling resolve "release". Pin 34.0.0; a 35.x line is a new skill.
- Quarkus 4.0.0 is "Upcoming" with no date; its content is rejected here. The two HTTP extensions stay preview.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Webhook pipeline blueprint](./blueprints/webhook-pipeline.md)
- [Verification Loop](./blueprints/verification-and-production.md#verification-loop)
- [Production readiness](./blueprints/verification-and-production.md#production-readiness)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Source bibliography](./blueprints/source-bibliography.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Build one `StripeClient` per JVM in a CDI producer; never set `Stripe.apiKey`.** The README says the legacy pattern "will be marked as deprecated soon" ([README v34.0.0](https://github.com/stripe/stripe-java/blob/v34.0.0/README.md)). See [patterns](./blueprints/always-do-patterns.md#1-stripeclient-producer).
- **Load `stripe.api-key` and the `whsec_` signing secret from Secrets Manager or SSM.** Stripe: "Never put secret API keys in source code" ([keys best practices](https://docs.stripe.com/keys-best-practices)). See [patterns](./blueprints/always-do-patterns.md#2-secrets-from-secrets-manager-or-ssm).
- **Set connect and read timeouts explicitly.** Builder defaults are 30 000 ms and 80 000 ms ([Stripe.java v34.0.0](https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java)); See Ask First D1 and [patterns](./blueprints/always-do-patterns.md#3-explicit-timeouts).
- **Take the webhook body as `byte[]` and verify `new String(body, UTF_8)`.** Stripe requires "the raw body of the request" ([webhooks](https://docs.stripe.com/webhooks)). See [patterns](./blueprints/always-do-patterns.md#4-raw-body-as-bytes).
- **Take the `Stripe-Signature` header from the request exactly as Stripe sends it and pass it unchanged to `constructEvent`.** The header is one line, `t=...,v1=...,v0=...` ([webhooks](https://docs.stripe.com/webhooks)); See Ask First D9 and [patterns](./blueprints/always-do-patterns.md#5-signature-header).
- **Send the verified event to SQS before returning 2xx.** Background work resumes only "if Lambda reuses the execution environment" ([Lambda runtime environment](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)). See [patterns](./blueprints/always-do-patterns.md#6-sqs-hand-off-before-2xx).
- **Claim each `evt_` id with a DynamoDB conditional put (`attribute_not_exists`).** Stripe: endpoints "might occasionally receive the same event more than once" ([webhooks](https://docs.stripe.com/webhooks)). See [patterns](./blueprints/always-do-patterns.md#7-event-id-dedupe).
- **Use one idempotency key per operation, persist it and reuse it on every attempt.** Stripe: "generate and persist a key for the operation and supply it to every attempt" ([error handling](https://docs.stripe.com/error-low-level?lang=java)). See [patterns](./blueprints/always-do-patterns.md#8-business-idempotency-keys).
- **On the API path, take the tenant from the verified token.** Family rule 6: "Multi-tenant isolation (tenant from token, never from path alone) is a 🚫 when violated". See [never-do patterns](./blueprints/never-do-patterns.md#n6-tenant-from-the-path-alone).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| D1 Timeout and retry values | A: short read timeout, 0 retries. B: moderate timeout, 1 retry. C: move Stripe calls into the SQS worker and keep the defaults. The budget formula is (medium confidence). See [D1](./blueprints/ask-first-decisions.md#d1-timeout-and-retry-values) | "Which API Gateway type (REST or HTTP), Lambda timeout, and can the call be asynchronous?" |
| D2 JVM + SnapStart or native | Native is never a default: stripe-java documents no GraalVM support (medium confidence, absence of evidence) and maintainers marked it "not planned" (2026-06-18). SnapStart supports Java managed runtimes only. See [D2](./blueprints/ask-first-decisions.md#d2-jvm--snapstart-or-native) | "Is native required? If yes, accept that Stripe does not support it and that every Stripe call path needs a native integration test?" |
| D3 DNS cache TTL | Stripe README: 60 s; AWS SnapStart guidance: 0. Both quotes are given in D3; which wins is (unverified), so there is no default. See [D3](./blueprints/ask-first-decisions.md#d3-dns-cache-ttl) | "Is SnapStart on? Which TTL do you want: 60 s (Stripe README) or 0 (AWS SnapStart guidance)?" |
| D4 Secrets and SnapStart | Key and client live in the encrypted snapshot; rotation needs a new published version (medium confidence); priming with a Stripe call is not recommended unless measured; whether `build()` does network I/O is (unverified). See [D4](./blueprints/ask-first-decisions.md#d4-secrets-and-snapstart) | "Is a secret in the KMS-encrypted snapshot acceptable, and is a customer managed key required?" |
| D5 Webhook transport | Public webhook on API Gateway vs Stripe event destination to Amazon EventBridge. See [D5](./blueprints/ask-first-decisions.md#d5-webhook-transport) | "Is a public endpoint acceptable? Are response-dependent event types needed?" |
| D6 Message content, IP allowlist, Connect | Verified payload vs event id on the SQS message (payload size vs 1 MiB is (unverified)); WAF only on REST API; tenant as Customer vs connected account. See [D6 to D8](./blueprints/ask-first-decisions.md#d6-sqs-message-content) | "Snapshot or thin events? Enforce Stripe IPs at the edge? Do tenants receive payouts?" |
| D9 `Stripe-Signature` header parameter (medium confidence, M15 and L2) | The HTTP extension splits header values on "," (medium confidence, M15: handler source read through a summarising tool, see [LambdaHttpHandler](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java)) and a non-collection `@HeaderParam` uses the first value; read from the jakartaee/rest `main` branch javadoc, not the 3.1 tag ([javadoc](https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/HeaderParam.java)). A: `@Context HttpHeaders` with `getHeaderString` (what the patterns use). B: single-valued `@RestHeader String`. I recommend A. See [D9](./blueprints/ask-first-decisions.md#d9-signature-header-parameter) | "Is the signature header ever sent with a comma, or through a proxy that merges headers?" |
| D10 Harm of a request-id idempotency key and of trusting Customer metadata (medium confidence, M5 and M6) | Both harm claims are inferences. A: a key derived from the business operation and an own `stripeCustomerId -> tenantId` table (metadata as a hint). B: request-id key and metadata as the source. For a Stripe webhook, never taking the tenant from payload or Customer metadata alone is this skill's design, not family rule 6. I recommend A. See [D10](./blueprints/ask-first-decisions.md#d10-request-id-key-and-customer-metadata-harm-claims) | "Which business identifier is stable across client retries, and where is the authoritative Customer-to-tenant mapping stored?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Deserialise the webhook into a POJO or `JsonNode` before verification; any other body type "Will be mapped from JSON to that type" ([Quarkus REST guide](https://quarkus.io/version/3.40/guides/rest)) | Take `byte[]` and call `constructEvent` on the exact UTF-8 string ([webhooks](https://docs.stripe.com/webhooks)) |
| Process the event in a background thread after returning 2xx; the work resumes only if Lambda reuses the environment ([Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)) | Complete the SQS send first; on failure return non-2xx so Stripe retries ([webhooks](https://docs.stripe.com/webhooks)) |
| Leave the 30 s / 80 s default timeouts on an API Gateway function; the gateway integration timeout is 29 s for a REST API (raisable for Regional and private APIs; [REST API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html)) and at most 30 s for an HTTP API, not raisable ([HTTP API quotas](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html)) | Set explicit timeouts below the gateway timeout (values: Ask First D1) |
| Use the Lambda or API Gateway request id as the idempotency key; Stripe wants one key per operation reused on every attempt ([error handling](https://docs.stripe.com/error-low-level?lang=java)) | Use a key derived from the business operation (Stripe's example: a shopping cart id), up to 255 characters, no personal data ([error handling](https://docs.stripe.com/error-low-level?lang=java), [idempotent requests](https://docs.stripe.com/api/idempotent_requests)); the composition is in [pattern 8](./blueprints/always-do-patterns.md#8-business-idempotency-keys) |
| Take the tenant from the request path alone; family rule 6: "Multi-tenant isolation (tenant from token, never from path alone) is a 🚫 when violated" | Take the tenant from the verified token; the webhook case is Ask First D10 |
| Set the signature tolerance to 0 or skip verification on a public endpoint; 0 "disables the recency check entirely" ([webhooks](https://docs.stripe.com/webhooks)) | Use the 3-argument `constructEvent` (default tolerance 5 minutes) |
| Use `Stripe.apiKey` or a literal key in code or committed config ([README](https://github.com/stripe/stripe-java/blob/v34.0.0/README.md), [keys](https://docs.stripe.com/keys-best-practices)) | Use the producer and the Secrets Manager or SSM config source |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `DEFAULT_CONNECT_TIMEOUT` | `30 * 1000` ms | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java |
| `DEFAULT_READ_TIMEOUT` | `80 * 1000` ms | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java |
| `StripeClient` `maxNetworkRetries` default | 0 (legacy global is 2) | https://docs.stripe.com/error-low-level?lang=java ; Stripe.java above |
| SDK retry backoff | `Thread.sleep`, base 500 ms doubling to 5 s, jitter 0.75 to 1.0 (medium confidence, M16) | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/HttpClient.java |
| Automatic idempotency key | `UUID.randomUUID()` on a POST without a user key | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/StripeRequest.java |
| Idempotency key limits | up to 255 characters; retained at least 24 hours | https://docs.stripe.com/api/idempotent_requests |
| Signature header and tolerance | `t=...,v1=...,v0=...`; library default tolerance 5 minutes | https://docs.stripe.com/webhooks |
| Stripe delivery retries | live: up to three days with exponential back off; sandbox: three times over a few hours | https://docs.stripe.com/webhooks |
| Manual resend window | Dashboard 15 days, CLI 30 days (EventBridge: no manual resend) | https://docs.stripe.com/webhooks ; https://docs.stripe.com/event-destinations/eventbridge |
| Stripe webhook response timeout | no number published (medium confidence, absence of evidence) | https://support.stripe.com/questions/webhooks-how-to-investigate-and-fix-timed-out ; https://docs.stripe.com/webhooks (neither states one) |
| API Gateway integration timeout | REST 29 s (raisable for Regional and private APIs); HTTP API 30 s maximum, not raisable | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html ; https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html |
| API Gateway to Lambda errors | Lambda rejection 500; function error or bad response 502; no retry of invocations | https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway-errors.html |
| SQS maximum message size | 1,048,576 bytes (1 MiB) | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html |
| Metadata limits | 50 pairs; key 40 characters; value 500 characters | https://docs.stripe.com/metadata |
| Dedupe condition | `attribute_not_exists(<key>)` rejects the second write | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html |
| Event destinations per account | up to 16 | https://docs.stripe.com/webhooks |

## External Resources

All fetched 2026-10-28.

- Stripe webhooks: https://docs.stripe.com/webhooks
- Stripe error handling and retries (Java): https://docs.stripe.com/error-low-level?lang=java
- Stripe keys best practices: https://docs.stripe.com/keys-best-practices
- stripe-java v34.0.0 README: https://github.com/stripe/stripe-java/blob/v34.0.0/README.md
- Quarkus REST guide: https://quarkus.io/version/3.40/guides/rest
- Quarkus AWS Lambda HTTP guide: https://quarkus.io/version/3.40/guides/aws-lambda-http
- AWS Lambda runtime environment: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html
- AWS Lambda SnapStart best practices: https://docs.aws.amazon.com/lambda/latest/dg/snapstart-best-practices.html
- API Gateway quotas: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html (REST) ; https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html (HTTP API)
- Full bibliography: [source bibliography](./blueprints/source-bibliography.md)
