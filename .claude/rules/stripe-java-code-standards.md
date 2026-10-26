---
name: stripe-java-code-standards
description: "Stripe Java 34.x code standards for Java source and Maven POM files: idempotency, webhook trust boundary, secret handling, version alignment, and 33.x→34.x migration. Use when editing or reviewing Stripe Java integration code."
paths:
  - "**/*.java"
  - "**/pom.xml"
---

# Stripe Java Code Standards (stripe-java 34.x)

Technical facts live in the four knowledge skills under
`packages/stripe-java/.apm/skills/`. This rule states what to check and where to look; it does
not duplicate skill bodies. Tags `(unverified)` and `(medium confidence)` from a skill apply here
too. Family rules source: `workspace/stripe-java/_family_rules_v34.md` (R01–R07).

---

## Always

- **R01 — Idempotency key on every mutating POST.** Every call to `.create()`, `.confirm()`,
  `.capture()`, `.cancel()`, or any other POST operation must pass a `RequestOptions` with a UUID
  v4 idempotency key (≤ 255 chars). Skill: `developing-stripe-java-core-v34`.

- **R02 — Verify webhook signature BEFORE any side effect.** `client.constructEvent(raw, sig,
  secret)` or `client.parseEventNotification(...)` must be the first statement in every webhook
  handler method, before any DB write, queue publish, or external call.
  Skill: `handling-stripe-webhooks-v34`.

- **R03 — Dedupe webhook events on `event.getId()`; return 2xx before async processing.**
  Check the processed-event store before executing business logic. Return `200 OK` (or equivalent)
  immediately; process asynchronously. Skill: `handling-stripe-webhooks-v34`.

- **R04 — Pin and align Stripe-Version.** Do not override `Stripe-Version` per-request without
  explicit justification. Webhook endpoint `api_versions` must match SDK default
  (`2026-09-30.endive` for stripe-java 34.0.0). Skill: `developing-stripe-java-core-v34`,
  `handling-stripe-webhooks-v34`.

- **R05 — No `Stripe.apiKey` global assignment.** Use `new StripeClient("sk_...")` or
  `StripeClient.builder().setApiKey(...).build()`. Skill: `developing-stripe-java-core-v34`.

- **R06 — No secret keys or card data in logs.** API keys (`sk_live_…`, `sk_test_…`), webhook
  secrets (`whsec_…`), `client_secret` values, and card/PAN data must not appear in any log
  statement at any level. Skill: `developing-stripe-java-core-v34`, `processing-stripe-payments-v34`,
  `handling-stripe-webhooks-v34`.

- **R07 — No ≤33.x patterns.** The following are superseded and must not appear in code
  targeting 34.x:
  - `invoice.getSubscription()` — use the `getParent().getSubscriptionDetails().getSubscription()` chain.
  - `.setPaymentMethodTypes(...)` on `PaymentIntentCreateParams` — use `automatic_payment_methods`.
  - `Stripe.apiKey = ...` global — use `StripeClient` (also R05).
  - `SubscriptionUpdateParams.billingCycleAnchor` enum `'now'`/`'unchanged'` — use `billing_cycle_anchor_param`.
  Skill: all four skills, each carrying a "33 to 34 Migration" section.

- **Raw body for webhooks.** Capture the webhook request body as raw UTF-8 `String` before any
  JSON framework parses it. In Spring use `@RequestBody String rawBody`. Any re-serialization
  breaks HMAC signature verification. Skill: `handling-stripe-webhooks-v34`.

- **Amount in minor units as `Long`.** Payment amounts must be `Long` values in minor units
  (e.g. `2000L` = $20.00 USD). Never accept a client-supplied amount total directly.
  Skill: `processing-stripe-payments-v34`.

- **`pom.xml` version pin.** The declared `stripe-java` version must be `34.0.0` (or a current
  34.x GA; never a pre-release `-alpha` or `-beta`). Skill: `developing-stripe-java-core-v34`.

---

## Ask First

- **Retry count (`setMaxNetworkRetries`).** Default is 0 retries on `StripeClient`. Increasing
  retries requires idempotency keys on all retried calls (R01). Skill: `developing-stripe-java-core-v34`.

- **`capture_method = manual`.** Uncaptured PaymentIntents auto-cancel after 7 days.
  Skill: `processing-stripe-payments-v34`.

- **`deserializeUnsafe()` on webhook event objects.** Forces deserialization across API-version
  mismatch; may lose fields. Skill: `handling-stripe-webhooks-v34`.

- **Anything a loaded skill marks as an Ask-First decision.** Do not resolve skill-level
  Ask-First items without consulting the relevant agent or skill first.

---

## Never

- `Stripe.apiKey = "sk_..."` anywhere in production code (R05).
- Log any value named `apiKey`, `secretKey`, `whsec`, `clientSecret`, or that matches `sk_live_`/`sk_test_` patterns (R06).
- Call `invoice.getSubscription()` — it does not exist in stripe-java 34.x (R07).
- Call `.setPaymentMethodTypes(...)` on `PaymentIntentCreateParams` or `PaymentIntentConfirmParams` — removed in 34.0.0 (R07).
- Trust a client-supplied payment amount; compute server-side in minor units (R07 scope + `processing-stripe-payments-v34` Never-Do).
- Use any `-alpha` or `-beta` stripe-java version in production `pom.xml` (`developing-stripe-java-core-v34`).
- Use `EventNotificationHandler` as a class name — the Java class is `com.stripe.StripeEventNotificationHandler` (`handling-stripe-webhooks-v34`).
- Act on a webhook payload before signature verification completes (R02).

---

## Verify

- Grep for `Stripe\.apiKey\s*=` — any match is R05 violation.
- Grep for `getSubscription()` on Invoice objects — any match is R07 violation.
- Grep for `setPaymentMethodTypes` — any match is R07 violation.
- Grep for log statements containing `clientSecret`, `whsec`, `sk_live_`, `sk_test_` — any match is R06 violation.
- Run `mvn clean compile` (or `./mvnw clean compile`) after any change. Fix compile errors before claiming success.
