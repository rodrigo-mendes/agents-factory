# Research: stripe-java 34.x inside Quarkus 3.40 LTS on AWS Lambda behind API Gateway

Unit U7 of the quarkus-aws-saas family. Future skill: `integrating-stripe-quarkus-v3-40` (package `quarkus-aws-saas`).
Source item: "Stripe payments inside Quarkus on Lambda".
Family facts applied as given: `workspace/quarkus-aws-saas/_family_facts_v3.40.md` (cited FF<n> = line number of the fact row in that file, e.g. FF8 = Quarkus 3.40 LTS row), `workspace/_family_facts_v3.40.md`.
Family rules applied as given: `workspace/quarkus-aws-saas/_family_rules_v3.40.md` (rules 5, 6, 9-12 in particular; cited R<n> = rule number), plus the inherited policy files.

All pages were read on **2026-10-28** with the WebFetch tool. Quoted sentences were returned verbatim by the tool (verbatim quotes are capped at about 125 characters, so longer passages are paraphrased without quotes). Every `[Sn]` tag resolves to one URL in the [Source Bibliography](#source-bibliography). Internal sources (`[In]`) are the existing stripe-java skills and the sibling research files in this folder; they are cited as internal and were not re-verified unless a `[Sn]` sits next to them. Pages read only in part, summarised by the tool, or that returned 404 are listed as coverage limits (L-ids) in [Research Gaps](#research-gaps). IDs A1-A9 / Q1-Q8 / F1-F7 below are this document's own Always / Conditional / Forbidden patterns (not family facts).

Scope boundary. Covered here: (1) wiring one `StripeClient` per JVM in Quarkus CDI, timeouts and retries against the Lambda / API Gateway budget, the API key and webhook secret from Secrets Manager/SSM, SnapStart effects; (2) webhooks on `quarkus-amazon-lambda-http` / `-rest`: raw body, base64, `Stripe-Signature` header access, tolerance, fast 2xx + SQS hand-off, event-id dedupe, Stripe delivery retries; (3) idempotency-key derivation for outbound POSTs in a Lambda; (4) multi-tenant mapping tenant <-> Stripe Customer; (5) native image status. Referenced by name and NOT repeated: Stripe API semantics and SDK basics (`developing-stripe-java-core-v34` [I1], `handling-stripe-webhooks-v34` [I2], `processing-stripe-payments-v34`, `managing-stripe-subscriptions-v34`), Lambda packaging and SnapStart mechanics (U1 [I4]), HTTP extension mapping (U2 [I5]), Cognito/tenant-from-token (U3), DynamoDB (U4 [I6]), SQS and config sources (U5 [I7]), Terraform, Stripe.js, Quarkus 4.

## Contents

- [Metadata](#metadata)
- [Executive Summary](#executive-summary)
- [Architectural Guardrails](#architectural-guardrails): [Mandatory](#-mandatory-patterns), [Conditional](#️-conditional-patterns), [Forbidden](#-forbidden-patterns)
- [Migration Guide](#migration-guide)
- [Implementation Blueprint](#implementation-blueprint)
- [Quality Control](#quality-control)
- [Production Readiness](#production-readiness)
- [Reference Implementations](#reference-implementations)
- [Source Bibliography](#source-bibliography)
- [Research Gaps](#research-gaps)
- [Research Iteration Changelog](#research-iteration-changelog)
- [Completion Checklist](#completion-checklist)
- [Agent Operation Notes](#agent-operation-notes)
- [Contradictions Report](#contradictions-report)

---

## Metadata

```yaml
Full_Name: stripe-java (com.stripe:stripe-java) 34.x used from a Quarkus 3.40 LTS AWS Lambda (io.quarkus:quarkus-amazon-lambda-http / quarkus-amazon-lambda-rest 3.40.1.1) behind Amazon API Gateway (HTTP API payload 2.0 or REST API proxy)
Target_Version: stripe-java 34.0.0 (only stable 34.x on Maven Central; SDK default Stripe-Version 2026-09-30.endive per [I1]) + Quarkus 3.40.1.1 + Quarkiverse amazon-services 3.23.0
Release_Date: stripe-java 34.0.0 = 2026-10-01 per [I1] (not re-fetched); Quarkus 3.40 = 2026-09-30, 3.40.1.1 = 2026-10-19 (FF8)
Support_Status: stripe-java 34.x current stable major [I1]; Maven <release> tag points at 34.1.0-beta.1 (pre-release, do not pin) [S16]; Quarkus 3.40 LTS until 2027-09-30 (FF8); quarkus-amazon-lambda-http/-rest are "preview" (FF25)
Primary_Docs: https://docs.stripe.com/webhooks ; https://docs.stripe.com/error-low-level?lang=java ; https://quarkus.io/version/3.40/guides/rest
Official_Repo: https://github.com/stripe/stripe-java (tag v34.0.0) ; https://github.com/quarkusio/quarkus (tag 3.40.1.1)
Research_Date: 2026-10-28
Domain_Complexity: Complex (payments, secrets, signature verification, multi-tenant isolation, two serverless runtimes)
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 7          # Always-Do patterns with 2+ independent sources (A1, A3, A4, A5 inputs, A6, A7, A8)
Unverified_Count: 9            # U1-U9 in Research Gaps
Irresolvable_Count: 3          # G1 numeric webhook timeout, G2 StripeClient thread-safety statement, G3 HTTP API request base64 rule
Research_Quality_Score: 84%    # (~75 claims - 9 unverified - 3 irresolvable) / 75; medium-confidence items counted as verified-with-tag
Deviations_from_agent_workflow: "Caller forbade sub-agents, background tasks and plan mode (scope approved by the user 2026-10-28, relayed via workspace/quarkus-aws-saas/PIPELINE_STATE.md#approvals); all pages fetched directly; file written directly instead of via research-synthesizer. No Stripe or AWS call was executed; no code was compiled."
```

---

## Executive Summary

stripe-java 34.0.0 is a plain Java library: `StripeClient` is built once (constructor or builder), talks HTTPS through a default `HttpURLConnectionClient`, and verifies webhooks with `constructEvent` / `parseEventNotification` [S12][S15][I1][I2]. Running it inside a Quarkus 3.40 Lambda adds four constraints the existing Stripe skills do not cover: (a) **time budget** — the builder defaults are `DEFAULT_CONNECT_TIMEOUT = 30 * 1000` and `DEFAULT_READ_TIMEOUT = 80 * 1000` ms [S11][S12], while the API Gateway integration timeout is 29 s (REST) / 30 s (HTTP API, not raisable) [I8], so the defaults must be lowered on any request path; (b) **raw body and header transport** — Stripe requires "the raw body of the request" [S1]; the Quarkus HTTP and REST handlers base64-decode the body when `isBase64Encoded` is set and otherwise copy it as UTF-8 [S21][S22], so a `byte[]` entity ("The entire request body, not decoded" [S20]) gives the exact bytes; but the HTTP-extension handler **splits every header value on commas** (only `access-control-request-headers` is exempt) [S21], and `Stripe-Signature` is `t=...,v1=...,v0=...` [S1], so the header must be re-joined (`HttpHeaders.getHeaderString` joins values "separated by a ',' character" [S32]); (c) **Lambda lifecycle** — Lambda freezes the environment after the response and background work "resume[s] if Lambda reuses the execution environment" only [S28], so "respond 2xx fast, process asynchronously" [S1] means *hand off to SQS before returning*, not a background thread; (d) **SnapStart** — a `StripeClient` built at init lives in the encrypted snapshot together with the API key [S27], connection state is not guaranteed after restore for non-AWS-SDK clients [S26], and the Stripe README's DNS-TTL advice (60 s) conflicts with AWS's SnapStart advice (disable the Java DNS cache, TTL 0) [S9][S26].

What is specific to these versions: stripe-java 34.0.0 auto-adds an `Idempotency-Key` (`UUID.randomUUID()`) to every POST that has no user key [S14] and retries (only if `maxNetworkRetries` > 0; StripeClient default 0 [S5][S12]) on connect/socket timeouts, `Stripe-Should-Retry: true`, 409 and 5xx with 500 ms-5 s jittered `Thread.sleep` [S13]. Stripe now recommends **Thin** events for new destinations [S1] and offers Amazon EventBridge as a destination that needs no signature verification [S2][S7]. stripe-java documents **no GraalVM native support**; maintainers marked it "not planned" on 2026-06-18 (issue #1905) [S17], and a 2021 Quarkus native report failed on Gson reflection of `com.stripe.model.Event` [S18] — so JVM (+ SnapStart) is the conservative path and native is Ask-First (R3).

Three critical patterns: (1) one `@Singleton` `StripeClient` producer with explicit connect/read timeouts and a retry count sized so that `(1 + retries) x (connect + read) + backoff` stays under the API Gateway timeout and the Lambda timeout (Q2); (2) the webhook resource takes `byte[]` + `HttpHeaders.getHeaderString("Stripe-Signature")`, verifies, sends the verified event to SQS, returns 2xx; the SQS consumer dedupes on the `evt_` id with a DynamoDB conditional put (`attribute_not_exists`) [S30][I2]; (3) the tenant is resolved from *our* mapping table keyed by the Stripe Customer id, never from webhook metadata alone (R6). Domain tier **Complex**: security-critical (secret key, HMAC), multi-service (API Gateway, Lambda, Secrets Manager, SQS, DynamoDB, Stripe), multi-tenant.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source, inference, or community-only evidence) | 🔴 Low (verify before use)

### ✅ Mandatory Patterns

**A1. One `StripeClient` per JVM, produced by CDI, never `Stripe.apiKey`**
> Confidence: 🟢 High | [✓✓ Triangulated | stripe-java README v34.0.0 (2026-10-28) + StripeClient.java v34.0.0 (2026-10-28) + Lambda execution-environment page (2026-10-28)]
- Why: README shows `new StripeClient("sk_test_...")` and says the legacy pattern "is still available to use but will be marked as deprecated soon" and "new API endpoints will only be accessible in the StripeClient" [S9]. `Stripe.apiKey` is still `public static volatile String apiKey;` with no `@Deprecated` in 34.0.0 [S11] — the existing core skill already forbids it [I1]. Lambda reuses the environment and "Objects declared outside of the function's handler method remain initialized" [S28]; an execution environment "is busy and cannot process other requests" while handling one [S29], so one client per environment is enough. Stripe documents no thread-safety guarantee for `StripeClient` itself; the only statement is that `withStripeContext` "is useful for creating thread-safe clients with different contexts" "without reinitializing HTTP connections" [S12] (see G2). Scope: `@Singleton` has no client proxy and is "slightly faster" but is not mockable with `@InjectMock` without `@MockitoConfig(convertScopes = true)` [I3]; `@ApplicationScoped` would need a proxy of `StripeClient` (ArC `transform-unproxyable-classes=true` by default [I3]) — choose per test strategy.
- Code:
  ```java
  // Quarkus 3.40.1.1 + stripe-java 34.0.0 — one client per JVM (Lambda execution environment)
  import com.stripe.StripeClient;
  import jakarta.enterprise.inject.Produces;
  import jakarta.inject.Singleton;
  import org.eclipse.microprofile.config.inject.ConfigProperty;

  @Singleton
  public class StripeClientProducer {
      @Produces
      @Singleton
      StripeClient stripeClient(@ConfigProperty(name = "stripe.api-key") String apiKey,
                                @ConfigProperty(name = "stripe.connect-timeout-ms") int connectMs,
                                @ConfigProperty(name = "stripe.read-timeout-ms") int readMs,
                                @ConfigProperty(name = "stripe.max-network-retries") int retries) {
          return StripeClient.builder()
                  .setApiKey(apiKey)              // value from Secrets Manager/SSM config source (A3)
                  .setConnectTimeout(connectMs)   // ms; builder default Stripe.DEFAULT_CONNECT_TIMEOUT = 30 000
                  .setReadTimeout(readMs)         // ms; builder default Stripe.DEFAULT_READ_TIMEOUT = 80 000
                  .setMaxNetworkRetries(retries)  // StripeClient default 0
                  .build();
      }
  }
  ```
- Source: https://github.com/stripe/stripe-java/blob/v34.0.0/README.md (2026-10-28); https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/StripeClient.java (2026-10-28); https://stripe.dev/stripe-java/com/stripe/StripeClient.StripeClientBuilder.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html (2026-10-28); [I3] `developing-quarkus-arc-v3-40` scopes.

**A2. Set connect/read timeouts and retries explicitly so the worst case fits the API Gateway and Lambda timeouts**
> Confidence: 🟢 High for every input number | [✓✓ Triangulated | Stripe.java + StripeClient.java + HttpClient.java v34.0.0 (2026-10-28) + error-low-level (2026-10-28) + D2 research]; the budget formula itself is an inference (🟡)
- Why: builder fields default to `Stripe.DEFAULT_CONNECT_TIMEOUT` / `DEFAULT_READ_TIMEOUT` [S12] = `30 * 1000` / `80 * 1000` ms [S11]; "StripeClient defaults to zero retries and doesn't inherit legacy global retry settings" [S5] (the legacy global is `maxNetworkRetries = 2` [S11]). Retries sleep with `Thread.sleep`, base 500 ms doubling to max 5 s, jitter 0.75-1.0 [S13]. API Gateway integration timeout: REST 50 ms-29 s (raisable for Regional/private), HTTP API 30 s max; a timed-out integration returns 504 [I8]. The Invoke phase is limited by the function timeout [S28]. The README warns "Please take care to set conservative read timeouts" because "a short timeout increases the likelihood of a problem within our servers" [S9] — hence the actual values are Ask-First (Q2).
- Code:
  ```properties
  # application.properties — Quarkus 3.40.1.1, request path behind API Gateway (example values, see Q2)
  # worst case ~ (1 + retries) x (connect + read) + backoff <= 29 s (REST) / 30 s (HTTP API) and <= Lambda timeout
  stripe.connect-timeout-ms=3000
  stripe.read-timeout-ms=20000
  stripe.max-network-retries=0
  # SQS consumer function (no API Gateway in front): bounded by the Lambda timeout / SQS visibility timeout (U5)
  %sqs-worker.stripe.read-timeout-ms=80000
  %sqs-worker.stripe.max-network-retries=2
  ```
- Source: https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java (2026-10-28); https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/HttpClient.java (2026-10-28); https://docs.stripe.com/error-low-level?lang=java (2026-10-28); [I8] research_AWS_LambdaDebug_2026-10.md (API Gateway timeouts).

**A3. Load the secret key and the `whsec_` signing secret from Secrets Manager or SSM, never from code or committed config**
> Confidence: 🟢 High | [✓✓ Triangulated | Stripe keys best practices (2026-10-28) + Quarkiverse Secrets Manager config source via U5 + family rule R5]
- Why: Stripe: "Never put secret API keys in source code"; "Use your platform’s secrets management tools (such as a secrets vault)"; it lists "AWS Secrets Manager: Integrates with IAM and supports automatic rotation" and says to "Use restricted API keys with limited permissions instead of unrestricted secret API keys" [S3]. The webhook secret is unique per endpoint and differs between test and live keys [S1]. Mechanism (not repeated here): Quarkiverse 3.23.0 `quarkus.secretsmanager.config.secrets."<property>"=<secret-name>`; values are "loaded once at startup (the config source does not poll for updates)" [I7 A10/Q1]. Family rule R5.
- Code:
  ```properties
  # Quarkiverse amazon-services 3.23.0 config source (mechanism: U5 research A10)
  quarkus.secretsmanager.config.enabled=true
  quarkus.secretsmanager.config.secrets."stripe.api-key"=prod/stripe/restricted-key
  quarkus.secretsmanager.config.secrets."stripe.webhook-secret"=prod/stripe/whsec-payments-endpoint
  ```
- Source: https://docs.stripe.com/keys-best-practices (2026-10-28); https://docs.stripe.com/webhooks (2026-10-28); [I7] research_Quarkus_AmazonMessaging_v3.40.md A10, Q1.

**A4. Read the webhook body as `byte[]` and pass `new String(bytes, UTF_8)` to verification**
> Confidence: 🟢 High | [✓✓ Triangulated | Stripe webhooks (2026-10-28) + Quarkus REST 3.40 guide (2026-10-28) + Quarkus HTTP/REST handler source 3.40.1.1 (2026-10-28)]
- Why: "Stripe requires the raw body of the request to perform signature verification… Any manipulation to the raw body of the request causes the verification to fail" [S1]; "The request body must be the exact UTF-8 string Stripe sent" [S2]; Stripe's own Java example does `new String(requestBody.readAllBytes(), StandardCharsets.UTF_8)` [S2]. Quarkus REST: `byte[]` = "The entire request body, not decoded"; `String` = "The entire request body, decoded"; any other type "Will be mapped from JSON to that type" [S20] (a POJO is re-serialised JSON and fails verification). The Lambda handlers build the body as `Base64.getDecoder().decode(body)` when `isBase64Encoded` is true, else `Unpooled.copiedBuffer(body, StandardCharsets.UTF_8)` (HTTP and REST extensions alike) [S21][S22]; both paths yield the original bytes for a UTF-8 JSON payload.
- Code: see [Implementation Blueprint](#implementation-blueprint) step 3.
- Source: https://docs.stripe.com/webhooks (2026-10-28); https://docs.stripe.com/webhooks/event-notification-handlers?lang=java (2026-10-28, served as "Manage webhook endpoints"); https://quarkus.io/version/3.40/guides/rest (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java (2026-10-28).

**A5. Read `Stripe-Signature` with `HttpHeaders.getHeaderString(...)` (comma-joined), not a single-valued `@RestHeader String`**
> Confidence: 🟢 High for each input (header format, handler split, JAX-RS semantics) | [✓✓ Triangulated | Stripe webhooks (2026-10-28) + lambda-http LambdaHttpHandler 3.40.1.1 (2026-10-28) + Jakarta REST HeaderParam/HttpHeaders javadoc (2026-10-28)]; the end-to-end failure is an inference not tested (🟡, U1)
- Why: the header "contains a timestamp and one or more signatures" — `t=…,v1=…,v0=…`, "a real Stripe-Signature header is on a single line" [S1]. The `quarkus-amazon-lambda-http` 3.40.1.1 handler adds each `header.getValue().split(",")` piece as a separate header value unless the name is `access-control-request-headers` [S21]. Jakarta REST: for a non-collection parameter with multiple values "the first value (lexically) of the parameter is used" [S31], while `getHeaderString` joins values "separated by a ',' character" [S32]. So `@RestHeader("Stripe-Signature") String` would likely see only `t=…` and verification would fail; `getHeaderString` reconstructs the original string. The REST extension copies `multiValueHeaders` as-is [S22], and API Gateway REST keeps a single comma-bearing header as one value (`"header3": ["value1,value2"]`) [S24], so the problem is specific to the HTTP extension — use the same code for both.
- Code:
  ```java
  // ✅ works for quarkus-amazon-lambda-http AND -rest 3.40.1.1
  String sig = headers.getHeaderString("Stripe-Signature");   // @Context jakarta.ws.rs.core.HttpHeaders headers
  // ❌ @RestHeader("Stripe-Signature") String sig  -> first split piece only on lambda-http (inference, U1)
  ```
- Source: https://docs.stripe.com/webhooks (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java (2026-10-28); https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/HeaderParam.java (2026-10-28); https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/core/HttpHeaders.java (2026-10-28).

**A6. Verify, then hand the event to SQS, then return 2xx — all inside the invocation**
> Confidence: 🟢 High | [✓✓ Triangulated | Stripe webhooks (2026-10-28) + Lambda execution-environment page (2026-10-28) + Stripe manage-webhook-endpoints (2026-10-28)]
- Why: endpoints must "Quickly return a successful status code (2xx) before any complex logic that might cause a timeout" and "process incoming events with an asynchronous queue" [S1]; a "(Timed out) ERR" means "The destination server took too long to respond" [S1]. In Lambda, background work that "did not complete when the function ended" resumes only "if Lambda reuses the execution environment" — "Make sure that any background processes or callbacks in your code are complete before the code exits" [S28]. Therefore the queue write must complete before the 2xx; if it fails, return non-2xx so Stripe retries ("for up to three days with an exponential back off in live mode"; sandbox "three times over the course of a few hours") [S1]. A 3xx counts as a failure [S1]. Stripe publishes no numeric response timeout (G1).
- Code: Blueprint step 3 (`sqs.sendMessage(...)` before `Response.ok()`).
- Source: https://docs.stripe.com/webhooks (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html (2026-10-28); SQS client: [I7].

**A7. Dedupe on the event id with a DynamoDB conditional put in the consumer**
> Confidence: 🟢 High | [✓✓ Triangulated | Stripe webhooks + manage-webhook-endpoints (2026-10-28) + DynamoDB conditional put (2026-10-28) + U5 A7]; TTL length is an inference (🟡)
- Why: "Webhook endpoints might occasionally receive the same event more than once… logging the event IDs you’ve processed"; for dual Event objects "use the ID of the object in data.object along with the event.type"; "Don’t use created to determine event order or whether you’ve already processed an event" [S1]. Stripe's recovery guidance uses `is_processing_or_processed` / `mark_as_processing` / `mark_as_processed` and says to skip already-processed events and return 200 [S2]. SQS-triggered Lambdas are at-least-once too [I7 A7], so dedupe in the consumer even if the ingress also checks. DynamoDB: `attribute_not_exists(Id)` "is true only when no item with that Id value already exists… DynamoDB rejects the write"; error message "The conditional request failed" [S30]. Retention: automatic retries span 3 days, Dashboard resend works 15 days, CLI resend 30 days [S1] → keep dedupe items ≥ 30 days (inference 🟡).
- Code: Blueprint step 4.
- Source: https://docs.stripe.com/webhooks (2026-10-28); https://docs.stripe.com/webhooks/event-notification-handlers?lang=java (2026-10-28); https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html (2026-10-28); [I6] U4 for the table/client.

**A8. Derive the idempotency key from the business operation, persist it, and reuse it on every attempt; never from the Lambda/API Gateway request id**
> Confidence: 🟢 High | [✓✓ Triangulated | error-low-level (2026-10-28) + idempotent_requests (2026-10-28) + StripeRequest.java v34.0.0 (2026-10-28)]; the request-id argument is an inference (🟡)
- Why: "If your application retries across separate SDK calls or process restarts, generate and persist a key for the operation and supply it to every attempt"; strategies: "UUID v4" or "Derive the key from a user-attached object, like the ID of a shopping cart" [S5]. Keys are "up to 255 characters"; "Avoid using sensitive data (for example, email addresses or personal identifiers)"; incoming parameters are compared with the original; keys retained at least 24 h [S4]. stripe-java 34.0.0 already sets `Idempotency-Key = UUID.randomUUID()` on a POST without a user key [S14], and its own retries resend the same request object [S13] — so the SDK protects only its internal retries. A client retry through API Gateway is a new invocation with a new request id, and API Gateway does not retry Lambda invocations (FF38), so a request-id key adds nothing over the SDK default (inference 🟡). For SQS-driven calls, base the key on the Stripe event id or the business key so redeliveries reuse it.
- Code:
  ```java
  // stripe-java 34.0.0 — key = tenant + operation + business id (<= 255 chars, no PII)
  String key = "t:" + tenantId + ":checkout:" + orderId;          // or a validated client-supplied Idempotency-Key
  RequestOptions opts = RequestOptions.builder().setIdempotencyKey(key).build();
  PaymentIntent pi = stripe.v1().paymentIntents().create(params, opts);  // params must be identical on every retry
  ```
- Source: https://docs.stripe.com/error-low-level?lang=java (2026-10-28); https://docs.stripe.com/api/idempotent_requests (2026-10-28); https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/StripeRequest.java (2026-10-28); family fact FF38.

**A9. Resolve the tenant from our own mapping keyed by Stripe ids; put the tenant id in Customer metadata only as a reconciliation hint**
> Confidence: 🟢 High for the Stripe facts | [✓✓ Triangulated | Stripe metadata (2026-10-28) + error-low-level (2026-10-28) + family rule R6]; the "never trust metadata alone" rationale is a family decision plus inference (🟡)
- Why: metadata lets you "store your user’s unique identifier from your system on a Stripe Customer"; limits "50 total key-value pairs", key "40 character limit", value "500 character limit"; "Never store sensitive information… to metadata" [S6]. Events carry "the corresponding object and any metadata the object contains" [S6]; metadata does not copy automatically to related objects except listed one-time snapshots (PaymentIntent→Charge, Subscription→Invoice `parent.subscription_details.metadata`, …) [S6]. Stripe recommends to "include a local identifier in its metadata so you can match an object received through a webhook to your local records" [S5]. Metadata is writable by any holder of a secret key or Dashboard access (inference), so per R6 the authoritative tenant comes from our table (`stripeCustomerId → tenantId`, U4), and on the API path from the token (U3), never from the body/path.
- Code: Blueprint step 5.
- Source: https://docs.stripe.com/metadata (2026-10-28); https://docs.stripe.com/error-low-level?lang=java (2026-10-28); family rule R6 (`_family_rules_v3.40.md`).

### ⚠️ Conditional Patterns

**Q1. Webhook transport: API Gateway + Quarkus endpoint vs Stripe → Amazon EventBridge destination**
> Confidence: 🟢 High (Stripe pages) / 🟡 Medium (fit to this architecture)
- Options: (A) public HTTPS webhook on API Gateway → Quarkus Lambda → SQS (this research); (B) Stripe event destination to Amazon EventBridge → rule → SQS/Lambda.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A webhook | full control; supports `issuing_authorization.request` and Checkout redirect behaviour [S7]; manual resend in Dashboard (15 d) / CLI (30 d) [S1] | you own raw body, header, signature, 2xx latency, IP allowlist (A4-A6) | most SaaS integrations |
  | B EventBridge | no public endpoint; "verification isn’t needed" for cloud providers [S2]; targets incl. Lambda, SQS, SNS, Step Functions [S7] | partner event source must be associated "within 7 days" or the destination is disabled; "You can’t manually resend events to Amazon EventBridge through Stripe"; create an archive to replay; payload wrapped in `detail` [S7]; event notification handlers don't support EventBridge on the public-preview channel [S2] | AWS-native pipelines, no inbound internet |

- Agent: "Ask whether a public webhook endpoint is acceptable and whether any response-dependent event types (issuing authorization, Checkout redirect) are needed."
- Source: https://docs.stripe.com/event-destinations/eventbridge (2026-10-28); https://docs.stripe.com/webhooks/event-notification-handlers?lang=java (2026-10-28).

**Q2. Timeout and retry values on the request path**
> Confidence: 🟡 Medium (numbers are a design choice)
- Options: (A) short read timeout, 0 retries, rely on the caller's idempotent retry; (B) moderate read timeout, 1 retry; (C) move Stripe calls off the request path into the SQS worker and keep the defaults (80 s read) with retries.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | fits 29/30 s easily | README: a short timeout "increases the likelihood of a problem within our servers" [S9]; an unknown outcome must be reconciled [S5] | synchronous PaymentIntent create for a UI |
  | B | absorbs one transient error | `Thread.sleep` backoff 0.5-5 s consumes the budget [S13] | low-latency calls (retrieve/update) |
  | C | Stripe's "conservative read timeouts" [S9] | asynchronous UX (client polls or waits for the webhook) | subscription/billing back-office work |

- Agent: "Ask the API Gateway type (29 s REST / 30 s HTTP), the Lambda timeout, and whether the call can be asynchronous; then compute (1+retries)x(connect+read)+backoff."
- Source: https://github.com/stripe/stripe-java/blob/v34.0.0/README.md (2026-10-28); https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/HttpClient.java (2026-10-28); [I8].

**Q3. JVM + SnapStart vs native image (R3)**
> Confidence: 🟢 High (status facts) / 🟡 Medium (workaround completeness)
- Options: (A) JVM managed runtime + SnapStart; (B) Quarkus native with hand-maintained reflection registration of stripe-java classes.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A JVM+SnapStart | no Stripe-specific build config; SnapStart supports Java managed runtimes (FF16) | snapshot holds key + client (Q4); DNS-TTL conflict (Q5, C2) | default, conservative |
  | B native | lowest memory/start time | stripe-java: no GraalVM docs (README silent [S9]); maintainers: "We have not looked into supporting GraalVM" (2024-11-04) and status "not planned" (2026-06-18) [S17]; Gson failed to instantiate `com.stripe.model.Event` in a native build (2021) [S18]; a community (not Stripe) report of a silent native failure where nested `TaxIdListParams.Owner` was ignored (2026-09-30) [S17] | only with full reflection registration + native integration tests of every Stripe call path |

- Agent: "Ask whether native is required; if yes, warn that Stripe does not support it and that failures can be silent (community report), and require @QuarkusIntegrationTest coverage of every Stripe call."
- Source: https://github.com/stripe/stripe-java/issues/1905 (2026-10-28); https://github.com/stripe/stripe-java/issues/1199 (2026-10-28); https://github.com/stripe/stripe-java/blob/v34.0.0/README.md (2026-10-28).

**Q4. SnapStart: where to build the `StripeClient` and whether to prime**
> Confidence: 🟡 Medium
- Options: (A) build at init (eager startup or first injection), no Stripe network call before the snapshot; (B) prime with a Stripe call in `beforeCheckpoint`; (C) build lazily in the first invocation.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | class loading out of the invoke path ("preload dependencies and initialize resources… in your initialization code") [S26] | key in the snapshot (encrypted with an AWS managed key by default or a customer managed KMS key [S27]) | default |
  | B | warmer TLS/classes | "The state of connections… isn't guaranteed" after restore; "re-establish your network connections… in the function handler" or an after-restore hook [S26]; only AWS SDK connections "In most cases… automatically resume" — stripe-java is not an AWS SDK; dummy invocations must not have side effects such as "initiating business transactions" [S26] | avoid unless measured; GET-only if at all |
  | C | key never in the snapshot | first-request latency | strict "no secret in snapshot" policy |

- Agent: "Ask whether a secret in the (KMS-encrypted) snapshot is acceptable and whether a customer managed key is required."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart-best-practices.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/snapstart-security.html (2026-10-28); U1 [I4] A6/A7 for CRaC hooks.

**Q5. DNS cache TTL under SnapStart (source conflict C2)**
> Confidence: 🟢 High for each quote; which one wins is (unverified)
- Options: (A) Stripe README: set `networkaddress.cache.ttl` "to 60 seconds" because "default JVM configurations can have their DNS cache TTL set to forever" and Stripe IPs are not guaranteed static [S9]; (B) AWS SnapStart: "Avoid using Java DNS cache", set `networkaddress.cache.ttl` to 0; "Lambda Event Functions already cache DNS responses" [S26].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A 60 s | Stripe's stated reason | possible "connection timeouts when the function resumes from a snapshot" [S26] | JVM without SnapStart |
  | B 0 | AWS SnapStart guidance; Lambda's managed DNS caching still applies [S26] | more lookups (served by Lambda's cache) | SnapStart enabled |

- Agent: "If SnapStart is on, present both quotes and recommend B (AWS is the authority for the snapshot behaviour); otherwise A."
- Source: https://github.com/stripe/stripe-java/blob/v34.0.0/README.md (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/snapstart-best-practices.html (2026-10-28).

**Q6. What to put on the SQS message: the verified payload vs the event id only**
> Confidence: 🟡 Medium
- Options: (A) the verified raw payload (snapshot event) — the consumer needs no Stripe call; (B) `evt_` id + type (or a thin event) — the consumer fetches the object ("retrieve the API resource from the Stripe API to access the latest" [S1]).
- Tradeoffs: A is bounded by the SQS 1 MiB message limit (FF32) and by the event size, which Stripe does not state on the pages read (U6); B costs a Stripe GET per message and matches the thin-event model Stripe recommends for new integrations [S1]. Thin events use `parseEventNotification` instead of `constructEvent` [I2].
- Agent: "Ask snapshot vs thin event destination; for snapshot, ask whether payloads can exceed 1 MiB (then S3 + reference, U5)."
- Source: https://docs.stripe.com/webhooks (2026-10-28); FF32; [I2].

**Q7. Inbound IP allowlist and gateway type**
> Confidence: 🟢 High (Stripe recommendation, API Gateway split) / 🟡 Medium (fit)
- Options: (A) REST API with AWS WAF / resource policy limiting the webhook route to Stripe IPs; (B) HTTP API (no WAF at the API, FF35) with signature verification only.
- Tradeoffs: Stripe says "Use both of these protections" — IP allowlisting and signature verification [S1]; WAF is REST-only (FF35). IaC defers to `provisioning-aws-api-gateway-v6` (R4).
- Agent: "Ask whether the Stripe IP allowlist (docs.stripe.com/ips) must be enforced at the edge; if yes, REST API."
- Source: https://docs.stripe.com/webhooks (2026-10-28); FF35.

**Q8. Tenants as Stripe Customers on one account vs Stripe Connect accounts**
> Confidence: 🟡 Medium (Connect is out of scope beyond this pointer)
- Options: (A) one platform account, tenant ↔ Customer (A9); (B) tenant = connected account with per-request account/context — `StripeClient.withStripeContext` "is useful for creating thread-safe clients with different contexts" [S12]; event destinations choose `@self` vs `@accounts` [S1].
- Agent: "Ask whether tenants receive payouts (Connect) or only pay you (Customers)."
- Source: https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/StripeClient.java (2026-10-28); https://docs.stripe.com/webhooks (2026-10-28).

### 🚫 Forbidden Patterns

**F1. Deserialising the webhook into a POJO or `JsonNode` before verification**
> Severity: Critical
> Confidence: 🟢 High
- Why: any body type other than the listed raw types "Will be mapped from JSON to that type" [S20]; "Any manipulation to the raw body of the request causes the verification to fail" [S1].
- Impact: `No signatures found matching the expected signature for payload` [S2]; legitimate events rejected (retried up to 3 days, then lost).
- ❌ Wrong:
  ```java
  @POST @Path("/stripe/webhook")
  public Response receive(StripeEventDto event, @RestHeader("Stripe-Signature") String sig) { ... }
  ```
- ✅ Correct:
  ```java
  @POST @Path("/stripe/webhook")
  public Response receive(byte[] body, @Context HttpHeaders headers) throws SignatureVerificationException {
      Event e = stripe.constructEvent(new String(body, StandardCharsets.UTF_8),
                                      headers.getHeaderString("Stripe-Signature"), webhookSecret);
      ...
  }
  ```
- Source: https://quarkus.io/version/3.40/guides/rest (2026-10-28); https://docs.stripe.com/webhooks (2026-10-28).

**F2. Taking `Stripe-Signature` as a single-valued header parameter on `quarkus-amazon-lambda-http`**
> Severity: High
> Confidence: 🟢 High for the inputs; the failure outcome is 🟡 (U1, not tested)
- Why: the 3.40.1.1 HTTP handler splits header values on "," [S21]; Jakarta REST picks "the first value" for non-collection parameters [S31].
- Impact: verification fails on every delivery although the body is correct.
- ❌ Wrong:
  ```java
  public Response receive(byte[] body, @RestHeader("Stripe-Signature") String sig)
  ```
- ✅ Correct:
  ```java
  public Response receive(byte[] body, @Context HttpHeaders headers) {
      String sig = headers.getHeaderString("Stripe-Signature");  // values joined with ','
  ```
- Source: https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java (2026-10-28); https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/core/HttpHeaders.java (2026-10-28).

**F3. Processing in a background thread after returning 2xx**
> Severity: High
> Confidence: 🟢 High
- Why: "Background processes or callbacks that were initiated by your Lambda function and did not complete when the function ended resume if Lambda reuses the execution environment" [S28].
- Impact: events acknowledged to Stripe (no retry) but never processed.
- ❌ Wrong:
  ```java
  executor.submit(() -> fulfil(event));   // Lambda freezes after the response
  return Response.ok().build();
  ```
- ✅ Correct:
  ```java
  sqs.sendMessage(b -> b.queueUrl(queueUrl).messageBody(payload));  // completes before returning
  return Response.ok().build();                                       // on send failure: 5xx so Stripe retries
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html (2026-10-28); https://docs.stripe.com/webhooks (2026-10-28).

**F4. Leaving stripe-java default timeouts on an API-Gateway-fronted function**
> Severity: High
> Confidence: 🟢 High
- Why: defaults 30 s connect / 80 s read [S11] exceed the 29 s / 30 s integration timeout [I8].
- Impact: the client gets 504 while the Stripe POST may still succeed (outcome unknown → reconcile [S5]).
- ❌ Wrong:
  ```java
  return new StripeClient(apiKey);   // 30 000 / 80 000 ms defaults
  ```
- ✅ Correct:
  ```java
  return StripeClient.builder().setApiKey(apiKey)
          .setConnectTimeout(3_000).setReadTimeout(20_000).setMaxNetworkRetries(0).build();  // values per Q2
  ```
- Source: https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java (2026-10-28); [I8].

**F5. Using the Lambda or API Gateway request id as the Stripe idempotency key**
> Severity: High
> Confidence: 🟢 High for the Stripe rules; the request-id behaviour is an inference 🟡
- Why: Stripe wants a key that identifies a single operation and is reused on every attempt [S5]; a user's retry arrives as a new invocation with a new id (FF38: API Gateway does not retry Lambda invocations), so it creates a second operation.
- Impact: double charges on client retry.
- ❌ Wrong:
  ```java
  RequestOptions.builder().setIdempotencyKey(lambdaContext.getAwsRequestId()).build();
  ```
- ✅ Correct:
  ```java
  RequestOptions.builder().setIdempotencyKey("t:" + tenantId + ":checkout:" + orderId).build();
  ```
- Source: https://docs.stripe.com/error-low-level?lang=java (2026-10-28); FF38.

**F6. Taking the tenant from webhook metadata (or from the request body) without a lookup**
> Severity: Critical
> Confidence: 🟢 High (family rule R6) / 🟡 rationale
- Why: R6 (tenant from token / own mapping, never from path or payload alone); metadata is free-form key-value data [S6].
- Impact: cross-tenant entitlement grant if metadata is wrong or edited.
- ❌ Wrong:
  ```java
  String tenantId = customer.getMetadata().get("tenant_id");
  grantPlan(tenantId, sub);
  ```
- ✅ Correct:
  ```java
  String tenantId = tenantMapping.findTenantByStripeCustomer(sub.getCustomer())   // our table (U4)
          .orElseThrow(() -> new UnknownCustomerException(sub.getCustomer()));
  if (!tenantId.equals(customer.getMetadata().get("tenant_id"))) alertMismatch(tenantId, sub);  // hint only
  grantPlan(tenantId, sub);
  ```
- Source: `_family_rules_v3.40.md` R6; https://docs.stripe.com/metadata (2026-10-28).

**F7. Signature tolerance 0, or skipping verification on a public endpoint**
> Severity: High
> Confidence: 🟢 High
- Why: "Our libraries have a default tolerance of 5 minutes"; "Don’t use a tolerance value of 0. Using a tolerance value of 0 disables the recency check entirely"; use NTP [S1]. `DEFAULT_TOLERANCE = 300` s in 34.0.0 [I2]. `*WithoutVerification` constructors are for cloud-provider transports only [S2][I2].
- Impact: replay attacks or forged events.
- ❌ Wrong:
  ```java
  stripe.constructEvent(payload, sig, secret, 0);
  ```
- ✅ Correct:
  ```java
  stripe.constructEvent(payload, sig, secret);   // DEFAULT_TOLERANCE 300 s
  ```
- Source: https://docs.stripe.com/webhooks (2026-10-28); [I2].

---

## Migration Guide

> Confidence: 🟢 High | Sources: stripe-java CHANGELOG via [I1]/[I2] (2026-10-14, not re-fetched, L5) + Maven metadata [S16] (2026-10-28) + Stripe webhooks page [S1] (2026-10-28)

**Breaking changes relevant to this integration** (SDK-level changes are owned by [I1]/[I2]):
- stripe-java 34.0.0 pins `2026-09-30.endive`; a webhook endpoint whose API version differs leaves `getObject()` empty [I2]. Snapshot destinations select an API version at creation [S1].
- Pre-releases since the [I1] research: 34.1.0-alpha.3, alpha.4 and beta.1 now exist; Maven `<release>` = `34.1.0-beta.1` (lastUpdated 2026-10-21) [S16] — do not let tooling resolve "release"; pin `34.0.0`.
- Stripe's docs now recommend the **Thin** payload for new destinations [S1]; existing snapshot code keeps working.
- Quarkus side: no Stripe-specific change; `quarkus.snapstart.enable` → `quarkus.snapstart.enabled` (FF22); `quarkus-amazon-lambda-http/-rest` remain preview (FF25).

**Upgrade Steps**:
1. Pin `com.stripe:stripe-java:34.0.0` explicitly (no version ranges).
2. Replace any `Stripe.apiKey = …` with the A1 producer.
3. Replace `@RestHeader String` signature params with `HttpHeaders.getHeaderString` (A5) and POJO webhook bodies with `byte[]` (A4).
4. Set explicit timeouts/retries (A2, Q2).
5. Move secrets to the Secrets Manager config source (A3); publish a new SnapStart version after rotation (U5).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| stripe-java | 34.0.0 | 34.x stable | 35.x = new skill [I1] |
| Java | 17 (Quarkiverse source/target, FF17) | 25 | stripe-java supports LTS 8/11/17/21/25 [S10]; Lambda java17/21/25 runtimes (FF15) |
| Quarkus | 3.40.1.1 | 3.40.x | FF8 |
| Quarkiverse amazon-services | 3.23.0 | 3.23.x | FF17 |
| GraalVM native | — | — | not supported by Stripe (Q3) |

---

## Implementation Blueprint

> Confidence: 🟢 High for each API used (cited per step) | the assembled example was not compiled (🟡)

**Lifecycle**:
```text
Init (or SnapStart snapshot): Secrets Manager config source loads stripe.api-key + stripe.webhook-secret once [I7]
  -> @Singleton StripeClient built with explicit timeouts (A1, A2); no Stripe network call (Q4)
Restore (SnapStart): after-restore hook only if you re-create clients/state (U1 research A6/A7) [I4]
Invoke (API path):   tenant from token (U3) -> mapping table (U4) -> stripe.v1()...create(params, RequestOptions(key)) (A8)
Invoke (webhook):    byte[] body + getHeaderString -> constructEvent -> SQS send -> 2xx (A4-A6)
Invoke (SQS worker): conditional put evt_ id -> process -> mark processed (A7, A9)
```

**Step 1 — dependencies** (versions per FF17 and [I1]):
```xml
<!-- Quarkus 3.40.1.1 platform BOM + Quarkiverse 3.23.0 BOM assumed (U1/U4/U5) -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-amazon-lambda-http</artifactId></dependency>
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest</artifactId></dependency>
<dependency><groupId>io.quarkiverse.amazonservices</groupId><artifactId>quarkus-amazon-secretsmanager</artifactId></dependency>
<dependency><groupId>io.quarkiverse.amazonservices</groupId><artifactId>quarkus-amazon-sqs</artifactId></dependency>
<dependency><groupId>io.quarkiverse.amazonservices</groupId><artifactId>quarkus-amazon-dynamodb</artifactId></dependency>
<dependency><groupId>com.stripe</groupId><artifactId>stripe-java</artifactId><version>34.0.0</version></dependency>
<!-- SQS/DynamoDB need an explicit HTTP client artifact (FF28, U5 A2); the Secrets Manager/SSM POMs carry url-connection-client [I7] -->
```

**Step 2 — client producer**: A1 code.

**Step 3 — webhook resource** (Quarkus REST on lambda-http/-rest 3.40.1.1; stripe-java 34.0.0):
```java
package org.acme.billing;

import com.stripe.StripeClient;
import com.stripe.exception.SignatureVerificationException;
import com.stripe.model.Event;
import jakarta.inject.Inject;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.HttpHeaders;
import jakarta.ws.rs.core.Response;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.MessageAttributeValue;

@Path("/stripe/webhook")
public class StripeWebhookResource {

    @Inject StripeClient stripe;
    @Inject SqsClient sqs;                                                   // Quarkiverse 3.23.0 (U5)
    @ConfigProperty(name = "stripe.webhook-secret") String webhookSecret;    // whsec_ from Secrets Manager (A3)
    @ConfigProperty(name = "billing.stripe-events-queue-url") String queueUrl;

    @POST
    public Response receive(byte[] body, @Context HttpHeaders headers) {     // byte[] = "not decoded" [S20]
        String payload = new String(body, StandardCharsets.UTF_8);           // Stripe's own Java pattern [S2]
        String sig = headers.getHeaderString("Stripe-Signature");            // re-joins split values [S21][S32]
        final Event event;
        try {
            event = stripe.constructEvent(payload, sig, webhookSecret);      // 3-arg, DEFAULT_TOLERANCE 300 s [I2]
        } catch (SignatureVerificationException e) {
            return Response.status(400).build();                             // Stripe examples answer 400 [S1]
        }
        // Hand-off BEFORE returning: Lambda freezes after the response [S28]
        sqs.sendMessage(b -> b.queueUrl(queueUrl)
                .messageBody(payload)                                        // or the event id only (Q6)
                .messageAttributes(Map.of("eventId", MessageAttributeValue.builder()
                        .dataType("String").stringValue(event.getId()).build())));
        return Response.ok().build();   // an SQS exception propagates -> 5xx -> Stripe retries [S1]
    }
}
```
Notes: the response has no body, so the base64-on-non-text-Content-Type response rule (U2 C5/G1, [I5]) does not matter here. The exception type `constructEvent` throws for a non-JSON body is not stated on the pages read (U8).

**Step 4 — SQS consumer with dedupe** (AWS SDK v2 via Quarkiverse 3.23.0; table design per U4):
```java
// claim the event id once; a failed condition = duplicate -> skip (and let SQS delete the message)
boolean claim(String eventId, long ttlEpochSeconds) {
    try {
        dynamo.putItem(b -> b.tableName(dedupeTable)
                .item(Map.of("pk", AttributeValue.fromS("stripe#" + eventId),
                             "status", AttributeValue.fromS("PROCESSING"),
                             "ttl", AttributeValue.fromN(Long.toString(ttlEpochSeconds))))   // >= 30 days (A7)
                .conditionExpression("attribute_not_exists(pk)"));                         // [S30]
        return true;
    } catch (ConditionalCheckFailedException dup) {   // SDK exception class name (medium confidence, U9)
        return false;
    }
}
// after success: update status=PROCESSED; on failure: delete the claim (or let a lease expire) so a redelivery can retry
```
Mirrors Stripe's `mark_as_processing` / `mark_as_processed` flow [S2].

**Step 5 — tenant mapping on customer creation and in the consumer** (A9):
```java
// API path: tenantId comes from the verified token (U3), never from the body
CustomerCreateParams p = CustomerCreateParams.builder()
        .putMetadata("tenant_id", tenantId)              // key <= 40 chars, value <= 500 chars, no sensitive data [S6]
        .build();
Customer c = stripe.v1().customers().create(p,
        RequestOptions.builder().setIdempotencyKey("t:" + tenantId + ":customer").build());   // one Customer per tenant
tenantMapping.put(tenantId, c.getId());                  // DynamoDB, both directions (U4)

// Consumer: resolve the tenant from OUR table using the Stripe customer id carried by the object
String tenant = tenantMapping.findTenantByStripeCustomer(stripeCustomerId).orElseThrow();
```
Method names follow the `client.v1().<resource>().create(params, options)` pattern of [I1]; exact param-class/builder names per resource belong to `processing-stripe-payments-v34` / `managing-stripe-subscriptions-v34` (`putMetadata` builder name: medium confidence).

**Integration**: stripe-java 34.0.0 ↔ API Gateway

| Gateway | Quarkus extension | Body to resource | `Stripe-Signature` | Note |
|---|---|---|---|---|
| HTTP API (payload 2.0) | `quarkus-amazon-lambda-http` | base64-decoded if `isBase64Encoded`, else UTF-8 copy [S21] | split on "," by the handler → use `getHeaderString` [S21][S32]; payload 2.0 combines duplicate headers with commas and lowercases names [S23] | when HTTP API sets `isBase64Encoded` for JSON is not documented (G3) |
| REST API (proxy) | `quarkus-amazon-lambda-rest` | same rule [S22]; with `BinaryMediaTypes */*` (required, U2 A4) the request is treated as binary and arrives base64-encoded (U2; content-type tables [S25]) | `multiValueHeaders` copied as-is [S22]; a single comma-bearing value stays one value [S24] | Stripe's "Body Mapping Template" advice targets non-proxy integrations, not this path (C1) |

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
# 1. Version pins
mvn -q dependency:tree -Dincludes=com.stripe:stripe-java     # Expected: com.stripe:stripe-java:jar:34.0.0
# 2. No legacy global key / no default client on request paths
grep -rn "Stripe.apiKey" src/main/java && echo "FORBIDDEN (A1)"
grep -rn "new StripeClient(" src/main/java && echo "check: defaults 30s/80s (F4)"
# 3. Webhook resource takes byte[] and joins the header
grep -rn '@RestHeader("Stripe-Signature") String' src/main/java && echo "FORBIDDEN (F2)"
grep -rn 'getHeaderString("Stripe-Signature")' src/main/java     # Expected: 1 match
# 4. Local end-to-end with the Stripe CLI (dev-mode mock event server on 8080, FF14)
stripe listen --forward-to localhost:8080/stripe/webhook          # prints a whsec_... for the dev profile [S1]
stripe trigger payment_intent.succeeded                           # Expected: 200 in the Quarkus dev log, 1 SQS message
# 5. SnapStart version state (FF33)
aws lambda get-function-configuration --function-name billing:live --query 'SnapStart'   # Expected: OptimizationStatus On
```
Whether the dev-mode mock event server takes the same comma-split path as production is not documented (U1): keep the test below.

**Mocking**:
```java
// Quarkus 3.40 test (JUnit 5 + RestAssured against the mock event server, U6) — signature computed locally
// Stripe signature = HMAC-SHA256(secret, t + "." + payload), header "t=<t>,v1=<hex>" [S1]
String payload = "{\"id\":\"evt_test_1\",\"object\":\"event\",\"type\":\"payment_intent.succeeded\",\"data\":{\"object\":{}}}";
long t = java.time.Instant.now().getEpochSecond();
String v1 = hmacSha256Hex("whsec_test", t + "." + payload);       // test helper (javax.crypto.Mac "HmacSHA256")
given().contentType("application/json").header("Stripe-Signature", "t=" + t + ",v1=" + v1)
       .body(payload)
   .when().post("/stripe/webhook")
   .then().statusCode(200);                 // proves A4 + A5 survive the HTTP handler's comma split
// Negative: same request with the payload re-serialised (whitespace changed) -> 400
// SqsClient replaced by a test @Alternative or @InjectMock (normal scope needed, [I3]); no real Stripe call
```
An API-version mismatch between the test JSON and `Stripe.API_VERSION` empties `getObject()` [I2] — assert on `event.getId()` / `getType()` only.

---

## Production Readiness

- **Performance**: init work (Secrets Manager fetch, client build) moves into the snapshot with SnapStart (FF16, [S26]); Stripe retries block the thread with `Thread.sleep` (0.5-5 s) [S13]. Webhook spikes ("during the beginning of the month when all subscriptions renew") are why Stripe wants a queue [S1]; Lambda provisions one environment per concurrent request (1,000 default account concurrency; 1,000 environments every 10 s per function) [S29] — cap the consumer with reserved concurrency to protect Stripe rate limits (429 → backoff [S5]) (inference 🟡).
- **Scalability**: up to 16 event destinations [S1]; subscribe only to required event types ("Listening for extra events (or all events)… we don’t recommend it") [S1].
- **Monitoring**: alarm on webhook 4xx/5xx at the gateway and on SQS age of oldest message (U5); log `requestId`, `tenantId`, `evt_` id — no PII, no keys (R7; [S3]: don't expose key variables on error pages or diagnostics); the Workbench "Event deliveries" tab shows per-attempt status [S1]; the `v2.core.health.event_generation_failure.resolved` event (public preview) reports events Stripe failed to generate [S2].
- **Security**:
  - [ ] restricted API key per function, from Secrets Manager [S3]; rotate periodically [S3]
  - [ ] webhook secret rolled periodically; Stripe can delay old-secret expiry "for up to 24 hours" and signs once per active secret [S1] — update Secrets Manager and publish a new SnapStart version inside that window (U5, medium confidence)
  - [ ] HTTPS only, TLS v1.2/v1.3 [S1]; IP allowlist where the gateway allows it (Q7)
  - [ ] snapshot KMS key choice (Q4) [S27]
  - [ ] no Stripe call and no key/ID generation in `beforeCheckpoint` (uniqueness, U1 A6 [I4]); SDK idempotency UUIDs are generated per request at call time [S14]; retry jitter uses `ThreadLocalRandom` [S13], whose restored state could repeat across environments — low impact (jitter only), (medium confidence)
  - [ ] tenant resolved per A9 / F6

---

## Reference Implementations

- Stripe Java webhook handler (`readAllBytes` + UTF-8, `handler.handle(body, sig)`): https://docs.stripe.com/webhooks/event-notification-handlers?lang=java (2026-10-28) [S2]
- Stripe manual verification algorithm (`t` + "." + payload, HMAC-SHA256, constant-time compare, ignore non-`v1` schemes): https://docs.stripe.com/webhooks (2026-10-28) [S1]
- Stripe Java retry configuration example: https://docs.stripe.com/error-low-level?lang=java (2026-10-28) [S5]
- Stripe blog on Secrets Manager rotation of Stripe keys (linked from [S3], not read — L6): https://stripe.dev/blog/securing-stripe-api-keys-aws-automatic-rotation
- Quarkus HTTP mapping source at 3.40.1.1: [S21], [S22]
- Community (not authoritative, reported only, not endorsed by Stripe or Quarkus): `romixch/stripe-java-graalvm` and an unpolished `quarkiverse-stripe` extension (issue #1199 [S18]); `@RegisterForReflection` workaround (issue #1905 [S17]).

---

## Source Bibliography

**Primary** (all read 2026-10-28):

| ID | URL | Coverage | Used for |
|---|---|---|---|
| S1 | https://docs.stripe.com/webhooks (read via `.md?locale=en-US`) | full page (a first fetch returned the Spanish page, discarded) | raw body, header format, tolerance, 2xx, async, retries, ordering, dedupe, secret roll, IP allowlist, 16 destinations, Thin recommended |
| S2 | https://docs.stripe.com/webhooks/event-notification-handlers?lang=java | full; URL now serves "Manage webhook endpoints" | Java readAllBytes/UTF-8 example, exact UTF-8 body, Body Mapping Template note, processing/processed flow, handler preview banner, health event |
| S3 | https://docs.stripe.com/keys-best-practices | full | secrets vault, AWS Secrets Manager, restricted keys, rotation, env-var exposure |
| S4 | https://docs.stripe.com/api/idempotent_requests | full | V4 UUID, 255 chars, no sensitive data, 24 h, parameter comparison, POST only |
| S5 | https://docs.stripe.com/error-low-level?lang=java | full | StripeClient zero retries, persist key across attempts, cart-id-derived key, 409 handling, 500 indeterminate, metadata local identifier |
| S6 | https://docs.stripe.com/metadata | full | limits, sensitive data, events carry metadata, copy exceptions |
| S7 | https://docs.stripe.com/event-destinations/eventbridge | full | EventBridge destination, 7-day association, no manual resend, archive, `detail` envelope |
| S8 | https://support.stripe.com/questions/webhooks-how-to-investigate-and-fix-timed-out | full, no page date | no numeric timeout (G1) |
| S9 | https://github.com/stripe/stripe-java/blob/v34.0.0/README.md | tool summary + short quotes | legacy pattern status, timeout advice, DNS TTL 60, ProGuard, no GraalVM section |
| S10 | https://github.com/stripe/stripe-java/blob/master/README.md | tool summary | Maven snippet 34.0.0, JDK LTS list, telemetry |
| S11 | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/Stripe.java | targeted lines | DEFAULT_CONNECT/READ_TIMEOUT, VERSION 34.0.0, legacy retries 2, apiKey not @Deprecated |
| S12 | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/StripeClient.java | whole file (tool) | builder defaults, constructEvent signatures, withStripeContext wording |
| S13 | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/HttpClient.java | targeted | retry conditions, delays, Thread.sleep, ThreadLocalRandom jitter |
| S14 | https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/StripeRequest.java | targeted | automatic Idempotency-Key UUID on POST |
| S15 | https://stripe.dev/stripe-java/com/stripe/StripeClient.StripeClientBuilder.html | full (Javadoc 34.0.0) | setter names, default HttpURLConnectionClient |
| S16 | https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml | full | 34.x versions, release tag = 34.1.0-beta.1 |
| S17 | https://github.com/stripe/stripe-java/issues/1905 | tool summary of body + comments | GraalVM "not planned" (maintainer, 2026-06-18); community reports |
| S18 | https://github.com/stripe/stripe-java/issues/1199 | tool summary | Quarkus native Gson failure (2021), maintainer replies |
| S19 | https://github.com/stripe/stripe-java/issues?q=graalvm | listing | issue states |
| S20 | https://quarkus.io/version/3.40/guides/rest | chars 0-100000 and 100000-167085 in two windows (tool summaries) | body types, @RestHeader, HttpHeaders contextual object, execution model |
| S21 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java | targeted | base64 decode, UTF-8 copy, comma split |
| S22 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java | targeted | same body rule, multiValueHeaders copy |
| S23 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html | full | payload 2.0 fields, duplicate headers comma-joined, lowercased names |
| S24 | https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html | full | "maps the entire client request", multiValueHeaders example |
| S25 | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-payload-encodings-workflow.html | full | REST content-type conversion tables |
| S26 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-best-practices.html | full | init preload, networking, DNS cache, dummy-invocation side effects |
| S27 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-security.html | full | snapshot KMS encryption |
| S28 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html | full | freeze, background work, reuse, init/restore limits |
| S29 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html | full | one request per environment, concurrency quotas |
| S30 | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html | full | conditional put |
| S31 | https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/HeaderParam.java | javadoc (main branch, not the 3.1 tag, L2) | first value for non-collection types |
| S32 | https://raw.githubusercontent.com/jakartaee/rest/main/jaxrs-api/src/main/java/jakarta/ws/rs/core/HttpHeaders.java | javadoc (main branch, L2) | getHeaderString joins with ',' |

**Internal** (cited as internal, not re-verified here):
- I1 `packages/stripe-java/.apm/skills/developing-stripe-java-core-v34/SKILL.md` (research 2026-10-14)
- I2 `packages/stripe-java/.apm/skills/handling-stripe-webhooks-v34/SKILL.md` + `blueprints/always-do-patterns.md`
- I3 `packages/quarkus-core/.apm/skills/developing-quarkus-arc-v3-40/` (SKILL.md, scopes-and-injection)
- I4 `workspace/quarkus-aws-saas/research_Quarkus_AmazonLambda_v3.40.md` (U1: SnapStart A5-A7)
- I5 `workspace/quarkus-aws-saas/research_Quarkus_AmazonLambdaHTTP_v3.40.md` (U2: mapping, A4, C5, G1)
- I6 `workspace/quarkus-aws-saas/research_Quarkus_AmazonData_v3.40.md` (U4: DynamoDB, tenant isolation)
- I7 `workspace/quarkus-aws-saas/research_Quarkus_AmazonMessaging_v3.40.md` (U5: Secrets Manager/SSM config source, SQS, A7, A10, Q1)
- I8 `workspace/quarkus-aws-saas/research_AWS_LambdaDebug_2026-10.md` (D2: API Gateway timeouts 29 s / 30 s, 504)
- FF<n> rows of `_family_facts_v3.40.md` (by line number); R<n> items of `_family_rules_v3.40.md`

**Validation** (searches, 2026-10-28): WebSearch "stripe-java StripeClient thread safe share instance" (no official statement); "github stripe/stripe-java issue GraalVM native-image reflection" (no Stripe hit; led to S19); "docs.stripe.com webhook endpoint response timeout seconds" (only third-party numbers, rejected per source hierarchy; led to S8); "Jakarta RESTful Web Services spec first value (lexically)" (led to S31).

---

## Research Gaps

> Every gap that survives all gap-loop iterations also appears as an IRRESOLVABLE row in the changelog.

```
Gap: G1 — Stripe publishes no numeric webhook response timeout (S1, S2, S8 checked; third-party "20 s" figures rejected)
Impact: cannot size the webhook Lambda budget against Stripe's cutoff
Workaround: keep the webhook path to verify + one SQS send; watch "(Timed out) ERR" deliveries in Workbench
Follow-up: docs.stripe.com/webhooks after 34.x minor releases; Stripe support
§7-ref: Iteration 2 — IRRESOLVABLE

Gap: G2 — no Stripe statement that a StripeClient instance is thread-safe (README, Javadoc, source checked; only the withStripeContext wording)
Impact: low on default Lambda (one request per environment, S29); relevant for Lambda Managed Instances (concurrent invocations, S28) and non-Lambda reuse
Workaround: one client per JVM is Stripe's documented usage; do not share mutable RequestOptions builders between threads
Follow-up: stripe-java GitHub discussions/issues
§7-ref: Iteration 1 — IRRESOLVABLE

Gap: G3 — when API Gateway HTTP API sets isBase64Encoded=true for a JSON POST is not documented (carried from U2 item U2)
Impact: none for correctness (Quarkus decodes both paths, S21) — only for debugging
Workaround: byte[] entity (A4)
Follow-up: AWS HTTP API payload docs
§7-ref: Iteration 3 — IRRESOLVABLE
```

Unverified / medium items (tagged in the text):
- U1 (unverified) End-to-end effect of the lambda-http comma split on `@RestHeader String` in Quarkus REST (inference from S21 + S31; the Quarkus REST guide does not describe multi-value handling for `@RestHeader String`); also whether the dev-mode mock event server takes the same split path. Test in Quality Control.
- U2 = G2. U3 = G3.
- U4 (unverified) Whether building a `StripeClient` performs any network I/O (assumed none; `build()` only creates a `LiveStripeResponseGetter` [S12], whose internals were not read).
- U5 (medium confidence) Secret rotation under SnapStart requires publishing a new version, because the Secrets Manager config source loads once at startup [I7] and the snapshot freezes the value.
- U6 (unverified) Maximum Stripe event payload size vs the SQS 1 MiB limit.
- U7 (unverified) Lambda host clock synchronisation (NTP) relative to the 300 s tolerance — no AWS page read states it.
- U8 (unverified) Exception type thrown by `constructEvent` for a malformed (non-JSON) body.
- U9 (medium confidence) AWS SDK v2 exception class `ConditionalCheckFailedException` for the failed condition (S30 states the message only).
- Coverage limits: L1 S9, S10, S17, S18, S20 are tool summaries with short verbatim quotes; L2 S31/S32 read from the jakartaee/rest main branch, not the 3.1 tag used by Quarkus 3.40 (search reports identical wording across versions — medium confidence); L3 HTTP 404 for `github.com/stripe/stripe-java/tree/v34.0.0/src/main/resources` (absence of `META-INF/native-image` not confirmed), `jakarta.ee/specifications/restful-ws/3.1/jakarta-restful-ws-spec-3.1`, `jakarta.ee/specifications/platform/11/apidocs/jakarta/ws/rs/headerparam`; L4 `code.yawk.at` DNS failure; L5 stripe-java CHANGELOG not re-fetched (34.0.0 facts via [I1]/[I2]); L6 stripe.dev rotation blog not read.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | A1 / G2 | StripeClient thread safety | Searched README, Javadoc, source; only `withStripeContext` wording found | S12 (2026-10-28) |
| 1 | G2 | Thread-safety statement | ⚠️ IRRESOLVABLE — no official page states it | — |
| 1 | Q3 | GraalVM native support | Resolved: maintainer status "not planned" (2026-06-18); README silent | S17, S9 (2026-10-28) |
| 1 | A2 | Builder default timeouts | Resolved: 30 000 / 80 000 ms; StripeClient retries 0 | S11, S12, S5 (2026-10-28) |
| 1 | A8 | SDK automatic idempotency key | Resolved: UUID on POST without a user key | S14 (2026-10-28) |
| 2 | A5 | Header split vs JAX-RS single value | Resolved inputs: handler split + "first value" + getHeaderString join | S21, S31, S32 (2026-10-28) |
| 2 | G1 | Numeric webhook timeout | ⚠️ IRRESOLVABLE — Stripe docs and support page give no number; third-party values rejected | S1, S8 |
| 2 | C1 | Body Mapping Template advice vs proxy integration | Resolved: proxy "maps the entire client request"; template advice targets non-proxy | S2, S24 (2026-10-28) |
| 3 | G3 | HTTP API request base64 rule | ⚠️ IRRESOLVABLE — S23 shows the field, no rule (same as U2 item U2) | — |
| 3 | Q1 | EventBridge destination limits | Added | S7 (2026-10-28) |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (wiring, timeouts/retries, secrets, SnapStart, raw body, base64, header, tolerance, 2xx + SQS, dedupe, delivery retries, idempotency keys, multi-tenant, native)
- [x] Pattern counts driven by domain needs (9 Always / 8 Conditional / 7 Forbidden)
- [x] Every anti-pattern has an alternative (✅ alternatives name High options only; medium ones point to Q-items, R9)
- [x] All CLI commands marked representative
- [x] Integration examples complete (producer, webhook resource, consumer dedupe, tenant mapping) — not compiled
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example (A1 producer, Blueprint step 3) — 🟡 not compiled
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated or their single-source parts downgraded (A2 formula, A7 TTL, A8 request-id part, A9 rationale marked 🟡)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in the changelog

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1, A3, A4, A6, A7 (dedupe mechanism), F1, F3, F4, F7; builder defaults; Stripe retry/delivery numbers; Quarkus body-type table.
- **Medium Confidence (validate with user)**: A2 timeout formula and values (Q2); A5 failure outcome (U1) — keep `getHeaderString` regardless; A8 request-id reasoning; A9 metadata rationale; dedupe TTL ≥ 30 days; SnapStart rotation (U5); jitter-state note.
- **Low Confidence (must ask human)**: native image (Q3); G1-G3; Connect (Q8).
- **Edge Cases (pause)**: stripe-java 34.1.0 pre-releases exist (do not pin); `quarkus-amazon-lambda-http/-rest` are preview (FF25).
- **Emergency Stop**: none triggered (all primary facts come from official Stripe, AWS, Quarkus or Jakarta pages, or source at a tag).

---

## Contradictions Report

| ID | Statement A | Statement B | Handling |
|---|---|---|---|
| C1 | [I2] `handling-stripe-webhooks-v34` and [S2]: on AWS API Gateway + Lambda, capture `rawBody` with a **Body Mapping Template** | Quarkus `quarkus-amazon-lambda-http/-rest` use Lambda **proxy** integrations, where API Gateway "maps the entire client request to the input event" [S24] and Quarkus passes the decoded body to the resource [S21][S22] | Not a factual conflict, but the existing skill's Lambda advice does not apply to Quarkus proxy integrations; the new skill must say so and use A4. Report to the stripe-java package owner. |
| C2 | Stripe README: set `networkaddress.cache.ttl` to `60` [S9] (also in [I1] Quick Reference) | AWS SnapStart: avoid the Java DNS cache, set it to `0` [S26] | Ask-First Q5; cite both. |
| C3 | [S2] banner: "Event notification handlers are available in public preview" | Same page's version table and [I2]: Java GA since `v33.4.0` | Stripe page is internally inconsistent; keep [I2]'s GA statement and note the banner. Also: the `event-notification-handlers?lang=java` URL cited by [I2] now serves the "Manage webhook endpoints" page. |
| C4 | [I1] Version Context lists pre-releases 34.1.0-alpha.1 / -beta.1 / -alpha.2 | Maven metadata (lastUpdated 2026-10-21) lists alpha.1-alpha.4 and beta.1; `<release>` = 34.1.0-beta.1 [S16] | Update only; 34.0.0 is still the only stable. |
| C5 | StripeClientBuilder `build()` Javadoc: "Constructs a StripeResponseGetterOptions" | Code returns `new StripeClient(...)` [S12] | Cosmetic; no action. |

No family fact was contradicted by a page read for this unit.
