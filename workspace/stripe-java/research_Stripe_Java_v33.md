# Research: Stripe Java SDK (`com.stripe:stripe-java`) v33.x

## Metadata

```yaml
system_or_tech_name: Stripe Java SDK (com.stripe:stripe-java)
target_version: 33.4.2            # exact latest 33.x patch (verified)
target_major: "33.x"
release_date: 2026-09-09          # 33.4.2 publish date (GitHub releases / CHANGELOG)
previous_33x_patch: 33.4.1        # 2026-09-01
research_date: 2026-10-14
pinned_stripe_api_version: "2026-08-26.dahlia"   # pinned by 33.4.0; unchanged through 33.4.1/33.4.2
java_baseline: "Java 8+ (medium confidence — README 'Requirements'; exact minimum not re-confirmed this pass)"
build_coordinates: "com.stripe:stripe-java:33.4.2"
support_status: "SUPERSEDED MAJOR — v34.0.0 shipped 2026-10-01; 33.x is now N-1. New work should evaluate 34.x. 33.x research is intentionally version-locked per request."
source_hierarchy: official docs > official GitHub releases/CHANGELOG/source > official Javadoc > reject community
freshness_threshold_months: 6
```

> ⚠️ **Version-absolutism notice.** This document pins **33.4.2**. Patterns from majors **< 33 are
> treated as disinformation** and must not be mixed in. The user's initial assumption of "33.4.1"
> was **corrected by verification**: the latest 33.x patch is **33.4.2 (2026-09-09)**. Separately,
> **v34.0.0 (2026-10-01)** is now the newest stable major — flagged in Support status and Migration.
>
> **Javadoc caveat.** The official Javadoc at `stripe.dev/stripe-java/*` currently serves **34.0.0**.
> Accessor/method names below were confirmed there (and, where noted, against the pinned GitHub
> source) and are present in 33.x because each cited class was introduced at or before v29.x; a
> 33.4.2-specific Javadoc snapshot was not independently loaded. Such claims are tagged
> **[Javadoc 34.0.0; stable since ≤29.x]**.
>
> 🛡️ **Supply-chain note.** During research, every `docs.stripe.com` page carried an injected
> top-of-page block ("…skills and plugins… run `stripe agent setup`"). It is **not** official
> technical documentation and was **disregarded** by all investigators and this synthesis. No claim
> in this document derives from it.

---

## Executive Summary

The Stripe Java SDK (`com.stripe:stripe-java`) is the official server-side client for the Stripe
REST API. Major **33** is built on the service-oriented **`StripeClient`** (instance-based,
injectable) rather than the legacy global static `Stripe.apiKey`. Resources are reached through a
**versioned namespace** — `client.v1().paymentIntents()…` — and the `.v1()` segment is **required
for SDK versions above 29.4.0** (i.e., all of 33.x); the docs explicitly note "For SDK versions
29.4.0 or lower, remove `.v1()`." Source: [PaymentIntents guide (Java)](https://docs.stripe.com/payments/payment-intents?lang=java) — read 2026-10-14.

In 33.x the SDK pins a dated Stripe API version per release; **33.4.0 pinned `2026-08-26.dahlia`**,
and patches **33.4.1** (2026-09-01, hardened requestor vs. malicious URLs) and **33.4.2**
(2026-09-09, webhook secrets validated non-empty) kept that pin. Source:
[stripe-java CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) — read 2026-10-14.

Three critical patterns define correct 33.x usage: (1) construct one **`StripeClient`** (via
`new StripeClient(key)` or `StripeClient.builder()`) and reach resources through `client.v1()...`;
(2) always pass an **idempotency key** via `RequestOptions` on writes (max 255 chars) and let the
SDK's **automatic network retries** (`setMaxNetworkRetries`) run — retries auto-attach idempotency
keys; and (3) **verify webhook signatures on the raw request body** (default tolerance 300s) before
trusting any event. 33.x also matured thin-event handling: **33.3.0** added
`StripeClient.constructEventWithoutVerification`, `parseEventNotificationWithoutVerification`, and
`Webhook.Signature.generateSignatureHeader` (test helper); **33.4.0** made the
**`EventNotificationHandler`** class GA. Source:
[CHANGELOG 33.3.0 / 33.4.0](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) — read 2026-10-14.

> **A material API-model change (verified):** the Invoice→Subscription link is **no longer** a
> top-level `invoice.subscription`. Since v29.0.0 (API `2025-03-31.basil`) it lives under
> `invoice.getParent().getSubscriptionDetails().getSubscription()` — present in all 33.x. Source:
> [Invoice.Parent Javadoc](https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html) +
> [basil changelog](https://docs.stripe.com/changelog/basil/2025-03-31/adds-new-parent-field-to-invoicing-objects.md) — read 2026-10-14.

---

## Architectural Guardrails

### ✅ Mandatory Patterns

**1. Instantiate `StripeClient`; never use global static `Stripe.apiKey`.**
Why: instance scoping enables DI, per-client config, testability; new (incl. v2) endpoints are only
reachable through `StripeClient`.
```java
// Stripe Java 33.4.2
StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
// or, for tuning:
StripeClient tuned = StripeClient.builder()
    .setApiKey(System.getenv("STRIPE_SECRET_KEY"))
    .setMaxNetworkRetries(2)
    .setConnectTimeout(30 * 1000)   // milliseconds
    .setReadTimeout(80 * 1000)      // milliseconds
    .build();
PaymentIntent pi = client.v1().paymentIntents().create(params);
```
Source: [StripeClient Javadoc](https://stripe.dev/stripe-java/com/stripe/StripeClient.html),
[StripeClientBuilder Javadoc](https://stripe.dev/stripe-java/com/stripe/StripeClient.StripeClientBuilder.html),
[README](https://github.com/stripe/stripe-java/blob/master/README.md) — read 2026-10-14. [Javadoc 34.0.0; StripeClient stable since ≤29.x]

**2. Send an idempotency key on every write via `RequestOptions` (max 255 chars).**
Why: makes retries safe. Reusing a key with different params throws `IdempotencyException`.
```java
// Stripe Java 33.4.2
RequestOptions options = RequestOptions.builder()
    .setIdempotencyKey("order-4711-create")   // ≤ 255 chars, request-scoped
    .build();
PaymentIntent pi = client.v1().paymentIntents().create(params, options);
```
Source: [RequestOptions.RequestOptionsBuilder Javadoc](https://stripe.dev/stripe-java/com/stripe/net/RequestOptions.RequestOptionsBuilder.html),
[Error handling (Java)](https://docs.stripe.com/error-handling?lang=java) — read 2026-10-14.

**3. Verify webhook signatures on the raw body before using the event.**
Why: signature verification is the trust boundary; parsed/re-serialized bodies break it. Entry points
(both throw `SignatureVerificationException`; `JsonSyntaxException` on malformed JSON): static
`Webhook.constructEvent(payload, sigHeader, secret[, tolerance[, Clock]])` and instance
`client.constructEvent(payload, sigHeader, secret[, tolerance])`. Default tolerance is
**`Webhook.DEFAULT_TOLERANCE = 300` seconds (5 min)**; passing `0` disables the timestamp check and is
strongly discouraged.
```java
// Stripe Java 33.4.2
try {
    Event event = client.constructEvent(rawPayload, sigHeader, endpointSecret); // or Webhook.constructEvent(...)
} catch (SignatureVerificationException e) {
    return ResponseEntity.badRequest().build(); // reject; do NOT process
}
```
Source: [Webhook Javadoc](https://stripe.dev/stripe-java/com/stripe/net/Webhook.html),
[StripeClient Javadoc](https://stripe.dev/stripe-java/com/stripe/StripeClient.html),
[Webhook.java source — DEFAULT_TOLERANCE=300](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/net/Webhook.java),
[Webhooks quickstart (Java)](https://docs.stripe.com/webhooks/quickstart?lang=java) — read 2026-10-14; non-empty
secret validation added in [CHANGELOG 33.4.2](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) — read 2026-10-14.

**4. Compute monetary amounts server-side in the currency's minor unit (`long`).**
Why: client-supplied amounts are untrusted; USD uses cents (`2000L` = $20.00; USD min `50L` = $0.50,
up to 8 digits).
```java
// Stripe Java 33.4.2
PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(2000L)          // minor units; derive server-side, never from the client
    .setCurrency("usd")        // lowercase ISO 4217
    .setAutomaticPaymentMethods(
        PaymentIntentCreateParams.AutomaticPaymentMethods.builder().setEnabled(true).build())
    .build();
```
Source: [Create a PaymentIntent (Java)](https://docs.stripe.com/api/payment_intents/create?lang=java),
[PaymentIntents guide (Java)](https://docs.stripe.com/payments/payment-intents?lang=java) — read 2026-10-14.

**5. Read the Invoice→Subscription link through `parent`, not a top-level field.**
Why: since v29.0.0 (API `2025-03-31.basil`) `invoice.subscription` was removed.
```java
// Stripe Java 33.4.2 — always check parent.type first
Invoice.Parent parent = invoice.getParent();
if ("subscription_details".equals(parent.getType())) {
    String subId = parent.getSubscriptionDetails().getSubscription();          // raw id
    Subscription sub = parent.getSubscriptionDetails().getSubscriptionObject(); // null unless expanded
}
```
Source: [Invoice.Parent Javadoc](https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html),
[Invoice.Parent.SubscriptionDetails Javadoc](https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html),
[basil changelog](https://docs.stripe.com/changelog/basil/2025-03-31/adds-new-parent-field-to-invoicing-objects.md) — read 2026-10-14. [Javadoc 34.0.0; stable since 29.0.0]

**6. Handle `getDataObjectDeserializer().getObject()` as an `Optional` and guard the API-version mismatch.**
Why: `getObject()` returns `Optional.empty()` when `event.getApiVersion()` differs from the library's
pinned `Stripe.API_VERSION` (common for events fetched via `Event.retrieve/list`). Create the webhook
endpoint with `api_version = Stripe.API_VERSION`, or fall back to
`deserializeUnsafeWith(CompatibilityTransformer)`.
```java
// Stripe Java 33.4.2
Optional<StripeObject> maybe = event.getDataObjectDeserializer().getObject();
StripeObject obj = maybe.orElseGet(() ->
    event.getDataObjectDeserializer().deserializeUnsafe()); // last resort; fields may be lost
```
Source: [EventDataObjectDeserializer Javadoc](https://stripe.dev/stripe-java/com/stripe/model/EventDataObjectDeserializer.html),
[Event Javadoc](https://stripe.dev/stripe-java/com/stripe/model/Event.html) — read 2026-10-14.

### ⚠️ Conditional Patterns

**1. Thin events / `EventNotificationHandler` (v2) vs. classic snapshot `Event` (v1).**
Decision: classic `event.getDataObjectDeserializer().getObject()` snapshot dispatch via a
`switch (event.getType())`, OR the thin **`EventNotificationHandler`** (GA 33.4.0) +
`client.parseEventNotification(payload, sig, secret[, tolerance])` (returns
`com.stripe.model.v2.core.EventNotification`), which re-fetches the current object via `StripeClient`.
Tradeoffs: snapshot = no extra fetch but object reflects the event's API version; thin/re-fetch =
always current but an extra API call. When: choose thin/re-fetch for workflows sensitive to stale
snapshots (webhooks deliver minimal, non-expanded objects, so re-fetch with `expand` if needed).
Source: [CHANGELOG 33.4.0](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md),
[StripeClient Javadoc](https://stripe.dev/stripe-java/com/stripe/StripeClient.html),
[Expand (Java)](https://docs.stripe.com/expand?lang=java) — read 2026-10-14.

**2. Tune automatic network retries / timeouts per workload.**
Decision: set `setMaxNetworkRetries`, `setConnectTimeout`, `setReadTimeout` (all **milliseconds**) on
the client builder, or per-request on `RequestOptions` (boxed `Integer`, null falls back to global).
Tradeoffs: more retries improve resilience to transient network/5xx/409 errors but raise tail
latency; idempotency keys (auto-attached on retries) keep them safe. When: raise for batch/webhook
reactions; keep conservative read timeouts (some endpoints are time-intensive). Source:
[StripeClientBuilder Javadoc](https://stripe.dev/stripe-java/com/stripe/StripeClient.StripeClientBuilder.html),
[RequestOptionsBuilder Javadoc](https://stripe.dev/stripe-java/com/stripe/net/RequestOptions.RequestOptionsBuilder.html) — read 2026-10-14.

**3. `create`-then-`confirm` (two-step) vs. `confirm=true` single-call.**
Decision: create + return `client_secret` to the client for confirmation, OR set `confirm=true` (or
call `client.v1().paymentIntents().confirm(id, params)` server-side with a known payment method for
off-session). Tradeoffs: client-side confirm handles SCA/`next_action` in the browser; server-side
confirm suits saved/off-session methods and may need `confirmation_method=manual` for explicit
re-confirmation after each `next_action`. Source:
[Confirm a PaymentIntent (Java)](https://docs.stripe.com/api/payment_intents/confirm?lang=java) — read 2026-10-14.

### 🚫 Forbidden Patterns

**1. Global static API key configuration.**
❌ Wrong:
```java
Stripe.apiKey = "sk_live_...";                 // legacy global mutable state
PaymentIntent pi = PaymentIntent.create(params);
```
✅ Correct:
```java
StripeClient client = new StripeClient("sk_live_...");
PaymentIntent pi = client.v1().paymentIntents().create(params);
```
Impact: hidden global state, not thread-safe to reconfigure, untestable; v2 endpoints unreachable.
The legacy static path is documented as "will be marked as deprecated soon." Source:
[README](https://github.com/stripe/stripe-java/blob/master/README.md),
[StripeClient Javadoc](https://stripe.dev/stripe-java/com/stripe/StripeClient.html) — read 2026-10-14.

**2. Verifying a webhook against a parsed/re-serialized body (or skipping verification).**
❌ Wrong:
```java
String body = objectMapper.writeValueAsString(parsedJson);   // re-serialized ≠ original bytes
Webhook.constructEvent(body, sigHeader, secret);             // HMAC will not match
```
✅ Correct:
```java
String rawBody = request.body();                             // original bytes (e.g. Spark request.body())
client.constructEvent(rawBody, request.headers("Stripe-Signature"), endpointSecret);
```
Impact: valid events rejected, or (if verification skipped) attacker-forged payloads trigger
fulfillment/access. Middleware that reorders keys or changes whitespace invalidates the HMAC. Source:
[Webhooks quickstart (Java)](https://docs.stripe.com/webhooks/quickstart?lang=java),
[Manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints) — read 2026-10-14.

**3. Trusting a client-supplied amount.**
❌ Wrong:
```java
params = PaymentIntentCreateParams.builder().setAmount(requestFromBrowser.getAmount()).build();
```
✅ Correct:
```java
long amount = pricingService.totalMinorUnits(cartId);  // derived server-side
params = PaymentIntentCreateParams.builder().setAmount(amount).setCurrency("usd").build();
```
Impact: price tampering / under-charging. Source:
[PaymentIntents guide (Java)](https://docs.stripe.com/payments/payment-intents?lang=java) — read 2026-10-14.

**4. Reading `invoice.getSubscription()` (removed since v29.0.0).**
❌ Wrong: `String subId = invoice.getSubscription();` — getter does not exist on 33.x `Invoice`.
✅ Correct: `invoice.getParent().getSubscriptionDetails().getSubscription()` (after checking
`parent.getType().equals("subscription_details")`).
Impact: compile error or, in older mental models, `null` ids and broken reconciliation. Source:
[basil changelog](https://docs.stripe.com/changelog/basil/2025-03-31/adds-new-parent-field-to-invoicing-objects.md),
[Invoice.Parent.SubscriptionDetails Javadoc](https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html) — read 2026-10-14.

---

## Migration Guide

**Within major 33 (API-version pins & notable changes):**
| Release | Date | Pinned Stripe API version | Notable |
|---|---|---|---|
| 33.0.0 | 2026-06-05 | 2026-05-27.dahlia (unchanged) | ⚠️ `tax_rate.tax_details` now expandable |
| 33.1.0 | 2026-06-24 | 2026-06-24.dahlia | ⚠️ removed `storedCredentialUsage`; invoice `customFields/description/footer` added |
| 33.2.0 | 2026-07-29 | 2026-07-29.dahlia | deprecations: `proofOfRegistration`, `dynamicTaxRates` |
| 33.3.0 | 2026-08-10 | (unchanged) | `constructEventWithoutVerification`, `parseEventNotificationWithoutVerification`, `Webhook.Signature.generateSignatureHeader`, `stripe.major_api_version` |
| 33.4.0 | 2026-08-26 | **2026-08-26.dahlia** | `EventNotificationHandler` GA; ⚠️ removed `cryptogram` from `three_d_secure` on PaymentAttemptRecord/PaymentRecord |
| 33.4.1 | 2026-09-01 | (unchanged) | security: hardened requestor vs. malicious URLs |
| 33.4.2 | 2026-09-09 | (unchanged) | security: webhook secrets validated non-empty |

Source: [stripe-java CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) — read 2026-10-14 (high confidence, dated).

**From majors < 33 (treated as disinformation here):**
- Replace global `Stripe.apiKey` + static `Resource.create()` with `StripeClient` + `client.v1()...`.
  The `.v1()` accessor is required for SDK > 29.4.0. Source:
  [PaymentIntents guide (Java)](https://docs.stripe.com/payments/payment-intents?lang=java) — read 2026-10-14.
- ⚠️ **Migration Note (invoice→subscription):** the relationship moved from top-level
  `invoice.subscription` to `invoice.getParent().getSubscriptionDetails().getSubscription()` at
  v29.0.0 / API `2025-03-31.basil`. Source:
  [basil changelog](https://docs.stripe.com/changelog/basil/2025-03-31/adds-new-parent-field-to-invoicing-objects.md) — read 2026-10-14.

**API-version pinning mechanics:** there is **no public `setStripeVersionOverride`** on
`StripeClientBuilder`; the only override is the static, internal-use
`RequestOptions.RequestOptionsBuilder.unsafeSetStripeVersionOverride(...)` (not recommended). The
supported way to pin an API version is to **pin the library version** itself. A `com.stripe.StripeVersion`
constant class was **not found** in the Javadoc **(unverified)**. Source:
[RequestOptionsBuilder Javadoc](https://stripe.dev/stripe-java/com/stripe/net/RequestOptions.RequestOptionsBuilder.html),
[README](https://github.com/stripe/stripe-java/blob/master/README.md) — read 2026-10-14.

**Forward caveat:** **v34.0.0 (2026-10-01)** is the newest stable major. 33.x is a recent, supported
line but now **N-1**; plan a 34.x evaluation. The PaymentIntents API surface showed no breaking
change between 33.x and 34.0.0 in the release notes, but a full 33→34 changelog diff was not fetched
**(unverified)**. Source: [GitHub releases](https://github.com/stripe/stripe-java/releases) — read 2026-10-14.

---

## Implementation Blueprint

```xml
<!-- Maven — Stripe Java 33.4.2 -->
<dependency>
  <groupId>com.stripe</groupId>
  <artifactId>stripe-java</artifactId>
  <version>33.4.2</version>
</dependency>
```
```gradle
// Gradle — Stripe Java 33.4.2
implementation 'com.stripe:stripe-java:33.4.2'
```
Source: [central.sonatype.com — com.stripe:stripe-java](https://central.sonatype.com/artifact/com.stripe/stripe-java) — read 2026-10-14.

**Payments (create → return client_secret → confirm):**
```java
// Stripe Java 33.4.2
StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));

PaymentIntentCreateParams create = PaymentIntentCreateParams.builder()
    .setAmount(2000L).setCurrency("usd")
    .setAutomaticPaymentMethods(
        PaymentIntentCreateParams.AutomaticPaymentMethods.builder().setEnabled(true).build())
    .build();
PaymentIntent pi = client.v1().paymentIntents().create(create,
    RequestOptions.builder().setIdempotencyKey("order-4711").build());

String clientSecret = pi.getClientSecret(); // return to frontend over TLS; never log or put in URLs

// Server-side confirm (e.g. saved/off-session method):
PaymentIntentConfirmParams confirm = PaymentIntentConfirmParams.builder()
    .setPaymentMethod("pm_card_visa").setReturnUrl("https://www.example.com").build();
PaymentIntent confirmed = client.v1().paymentIntents().confirm(pi.getId(), confirm);
```
Source: [Create](https://docs.stripe.com/api/payment_intents/create?lang=java),
[Confirm](https://docs.stripe.com/api/payment_intents/confirm?lang=java),
[PaymentIntents guide](https://docs.stripe.com/payments/payment-intents?lang=java) — read 2026-10-14.

**Billing (customer → price → subscription, with expand):**
```java
// Stripe Java 33.4.2
Customer customer = client.v1().customers().create(
    CustomerCreateParams.builder().setName("Jenny Rosen").setEmail("jenny@example.com").build());

Price price = client.v1().prices().create(PriceCreateParams.builder()
    .setCurrency("usd").setUnitAmount(1000L)
    .setRecurring(PriceCreateParams.Recurring.builder()
        .setInterval(PriceCreateParams.Recurring.Interval.MONTH).build())   // DAY/WEEK/MONTH/YEAR
    .setProductData(PriceCreateParams.ProductData.builder().setName("Gold Plan").build())
    .build());

Subscription sub = client.v1().subscriptions().create(SubscriptionCreateParams.builder()
    .setCustomer(customer.getId())
    .addItem(SubscriptionCreateParams.Item.builder().setPrice(price.getId()).build())
    .addExpand("latest_invoice.payment_intent")   // expand (max depth 4) to avoid N+1
    .build());

Invoice latest = sub.getLatestInvoiceObject();        // populated because expanded
PaymentIntent subPi = latest.getPaymentIntentObject();
```
Source: [Customers create](https://docs.stripe.com/api/customers/create?lang=java),
[Prices create](https://docs.stripe.com/api/prices/create?lang=java),
[Subscriptions create](https://docs.stripe.com/api/subscriptions/create?lang=java),
[Expand](https://docs.stripe.com/expand?lang=java),
[Subscription Javadoc](https://stripe.dev/stripe-java/com/stripe/model/Subscription.html) — read 2026-10-14. [Javadoc 34.0.0; stable since ≤29.x]

**Webhooks (verify → dedupe → dispatch → 2xx):**
```java
// Stripe Java 33.4.2
Event event;
try {
    event = client.constructEvent(request.body(), request.headers("Stripe-Signature"), endpointSecret);
} catch (SignatureVerificationException e) {
    return ResponseEntity.badRequest().build();       // 400 on bad signature
}
if (alreadyProcessed(event.getId())) return ResponseEntity.ok().build(); // dedupe on evt_ id (at-least-once)
Optional<StripeObject> obj = event.getDataObjectDeserializer().getObject();
switch (event.getType()) {
    case "payment_intent.succeeded": /* ... */ break;
    case "invoice.paid":             /* ... */ break;
    case "invoice.payment_failed":   /* ... */ break;
    case "customer.subscription.deleted": /* revoke access */ break;
    default: /* log unhandled */ break;
}
return ResponseEntity.ok().build(); // return 2xx promptly; defer heavy work to a queue
```
Source: [Webhooks quickstart (Java)](https://docs.stripe.com/webhooks/quickstart?lang=java),
[Manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints),
[Billing webhooks](https://docs.stripe.com/billing/subscriptions/webhooks) — read 2026-10-14.

---

## Quality Control

- **Testing:** use test-mode keys and the Stripe CLI (`stripe listen` / `stripe trigger`) to replay
  events; `Webhook.Signature.generateSignatureHeader(payload, secret)` (added 33.3.0) builds signed
  headers for unit tests without the CLI; the `Webhook.constructEvent(..., tolerance, Clock)` overload
  injects a fixed `Clock` for deterministic timestamp tests. Source:
  [CHANGELOG 33.3.0](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md),
  [Webhook Javadoc](https://stripe.dev/stripe-java/com/stripe/net/Webhook.html) — read 2026-10-14.
- **Isolation/mocking:** inject `StripeClient` as a dependency so tests substitute a stub; the
  `new StripeClient(StripeResponseGetter)` constructor supports a custom HTTP client for tests.
  Source: [StripeClient Javadoc](https://stripe.dev/stripe-java/com/stripe/StripeClient.html) — read 2026-10-14.
- **Type safety:** params use typed builders; prefer enums (`Recurring.Interval.MONTH`,
  `SetupFutureUsage.OFF_SESSION`) over string literals. Source:
  [API reference (Java)](https://docs.stripe.com/api?lang=java) — read 2026-10-14.

---

## Production Readiness

- **Error handling:** catch the `StripeException` hierarchy — `CardException`,
  `InvalidRequestException` (`getParam()`, `getDocUrl()`), `AuthenticationException`,
  `ApiConnectionException` (indeterminate — retry with idempotency key), `ApiException` (indeterminate
  — reconcile via webhooks), `PermissionException`, `RateLimitException` (backoff),
  `IdempotencyException`, `SignatureVerificationException`. Base fields: `getStatusCode()`,
  `getCode()`, `getMessage()`, `getRequestId()` (`req_...`). Source:
  [Error handling (Java)](https://docs.stripe.com/error-handling?lang=java) — read 2026-10-14.
- **Retries/timeouts:** `setMaxNetworkRetries` / `setConnectTimeout` / `setReadTimeout` (ms) on the
  builder or per-request; retries auto-attach idempotency keys. Source:
  [StripeClientBuilder Javadoc](https://stripe.dev/stripe-java/com/stripe/StripeClient.StripeClientBuilder.html) — read 2026-10-14.
- **Telemetry:** request-latency telemetry is **enabled by default** and controlled only via the
  **static** field `Stripe.enableTelemetry = false;` — there is **no** per-instance
  `setTelemetry()`/`enableTelemetry()` on `StripeClientBuilder`. 33.1.1 replaced the source hash with
  a Telemetry UUID. Source: [README](https://github.com/stripe/stripe-java/blob/master/README.md),
  [CHANGELOG 33.1.1](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) — read 2026-10-14.
- **Webhooks at scale:** verify signature → respond 2xx fast → process asynchronously; dedupe on
  `event.getId()` (prefix `evt_`); expect at-least-once delivery and minimal (non-expanded) event
  objects — re-fetch with `expand` when you need nested data. Stripe retries failed deliveries for up
  to ~3 days with exponential back-off; optionally restrict inbound to Stripe's published webhook IP
  ranges (defense in depth). Source: [Manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints),
  [Expand (Java)](https://docs.stripe.com/expand?lang=java) — read 2026-10-14.
- **Secrets:** never log `client_secret`, embed it in URLs, or expose it beyond the specific
  customer; require TLS on any page carrying it. Source:
  [PaymentIntents guide (Java)](https://docs.stripe.com/payments/payment-intents?lang=java) — read 2026-10-14.
- **Invoice lifecycle events** (billing): `invoice.created` / `invoice.finalized` / `invoice.paid` /
  `invoice.payment_failed` / `invoice.payment_action_required` / `invoice.upcoming` / `invoice.updated`;
  subscription: `customer.subscription.created|updated|deleted|paused|resumed|trial_will_end`. Source:
  [Billing subscriptions webhooks](https://docs.stripe.com/billing/subscriptions/webhooks) — read 2026-10-14.

---

## Reference Implementations

- Official GitHub repo + examples: https://github.com/stripe/stripe-java — read 2026-10-14
- Official API reference (Java tab): https://docs.stripe.com/api?lang=java — read 2026-10-14
- Official webhooks quickstart (Java): https://docs.stripe.com/webhooks/quickstart?lang=java — read 2026-10-14
- Official billing webhooks guide: https://docs.stripe.com/billing/subscriptions/webhooks — read 2026-10-14

---

## Research Gaps

| # | Gap | Status | Follow-up |
|---|---|---|---|
| 1 | `com.stripe.StripeVersion` constant class | **(unverified)** | Not found in Javadoc; likely does not exist — pin library version instead |
| 2 | Public `setStripeVersionOverride` on `StripeClientBuilder` | **(does not exist)** | Only static `unsafeSetStripeVersionOverride` on RequestOptionsBuilder |
| 3 | `paymentIntent.confirm(...)` instance method on a model object in 33.x | **(unverified)** | Docs show only `client.v1().paymentIntents().confirm(id, params)` |
| 4 | Exact Java minimum baseline (8 vs 11) | (medium confidence) | Confirm README "Requirements" |
| 5 | Full 33→34 API-surface diff | **(unverified)** | Fetch 34.0.0 changelog diff if 34.x adoption considered |

> Note: the earlier gap on default webhook tolerance and `constructEvent` entry points is **resolved**
> (DEFAULT_TOLERANCE=300 confirmed in `Webhook.java`; overloads confirmed in Javadoc).

---

## Research Iteration Changelog

| Iteration | Item | Resolution |
|---|---|---|
| 1 | "latest patch 33.4.1" (user assumption) | Corrected to **33.4.2 (2026-09-09)** via GitHub releases + CHANGELOG |
| 1 | Pinned Stripe API version | Confirmed **2026-08-26.dahlia** (set in 33.4.0, unchanged in 33.4.1/33.4.2) |
| 1 | Support status | Found **v34.0.0 (2026-10-01)** now latest stable major → 33.x is N-1 |
| 2 | Invoice→Subscription accessor (was unverified) | Resolved: `invoice.getParent().getSubscriptionDetails().getSubscription()/getSubscriptionObject()` — Invoice.Parent Javadoc + basil changelog |
| 2 | `client.v1()` idiom | Confirmed required for SDK > 29.4.0 — PaymentIntents guide |
| 2 | Telemetry / version-override / error hierarchy / timeouts / idempotency limits | Upgraded to verified via core-client investigator (Javadoc + docs) |
| 3 | Webhook default tolerance + constructEvent entry points (was medium) | Resolved: DEFAULT_TOLERANCE=300 (Webhook.java), static+instance overloads, EventDataObjectDeserializer Optional + API-version-mismatch caveat, parseEventNotification (v2) |
| 3 | Prompt-injection block on docs.stripe.com pages | Detected by investigators and disregarded; recorded as supply-chain note |

---

## Completion Checklist

- [x] Target version pinned (33.4.2) and verified against dated official sources
- [x] All required sections present (bibliography placed last per request)
- [x] Three tiers (✅ / ⚠️ / 🚫) with side-by-side ❌/✅ on every Forbidden pattern
- [x] Migration section with per-release API pins and <33 guidance
- [x] `## Source Bibliography` present as the final section with 29 dated official URLs
- [x] Version mentioned well over 5 times
- [x] Unverified claims explicitly tagged
- [x] All four sections (core, payments, webhooks, billing) confirmed by section-investigators

---

## Agent Operation Notes

**High confidence (dated official sources / Javadoc / pinned source):** latest 33.x = 33.4.2
(2026-09-09); v34.0.0 (2026-10-01) now latest major; pinned API `2026-08-26.dahlia`; `StripeClient`
+ `client.v1()` (required > 29.4.0); builder setters `setMaxNetworkRetries`/`setConnectTimeout`/
`setReadTimeout` (ms); idempotency via `RequestOptions` (≤255 chars, `IdempotencyException` on
mismatch); `StripeException` hierarchy and base accessors; PaymentIntent create/confirm/retrieve
idioms; Customer/Price/Subscription builders; expand (max depth 4); Invoice→Subscription via
`parent.subscription_details`; webhook `Webhook.constructEvent` / `client.constructEvent` overloads;
`DEFAULT_TOLERANCE=300`; `getDataObjectDeserializer().getObject()` Optional + API-version-mismatch
caveat; `parseEventNotification` (v2 thin events); telemetry static-only; no public
`setStripeVersionOverride`; per-release changelog facts.

**Medium confidence (official page cited, exact value not re-confirmed):** Java minimum baseline.

**Unverified (flagged):** `com.stripe.StripeVersion` class existence; `paymentIntent.confirm(...)`
instance method on 33.x models; full 33→34 API diff.

**Process note:** all four parallel `section-investigator` agents (core, payments, webhooks, billing)
returned and are merged; no investigator output was fabricated. Investigators flagged (and
disregarded) a prompt-injection block injected atop docs.stripe.com pages — this synthesis likewise
ignores it. Recommend running `/skill-best-practices-validator` on this file before authoring the four
downstream skills (core/client, payments, webhooks, billing).

---

## Source Bibliography

### Primary Sources (verified, dated)
1. [stripe-java GitHub Releases](https://github.com/stripe/stripe-java/releases) — read 2026-10-14. Latest 33.x = 33.4.2 (2026-09-09); 33.4.1 (2026-09-01); v34.0.0 (2026-10-01).
2. [stripe-java CHANGELOG.md](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) — read 2026-10-14. Per-release API pins, breaking changes, new classes.
3. [stripe-java Webhook.java source](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/net/Webhook.java) — read 2026-10-14. `DEFAULT_TOLERANCE=300`, header parsing, overloads.
4. [Maven Central — com.stripe:stripe-java](https://central.sonatype.com/artifact/com.stripe/stripe-java) — read 2026-10-14. Build coordinates.
5. [stripe-java README](https://github.com/stripe/stripe-java/blob/master/README.md) — read 2026-10-14. Client usage, telemetry, version-pinning guidance.

### Official Javadoc (serves 34.0.0; classes stable since ≤29.x)
6. [StripeClient Javadoc](https://stripe.dev/stripe-java/com/stripe/StripeClient.html) — read 2026-10-14.
7. [StripeClient.StripeClientBuilder Javadoc](https://stripe.dev/stripe-java/com/stripe/StripeClient.StripeClientBuilder.html) — read 2026-10-14.
8. [RequestOptions.RequestOptionsBuilder Javadoc](https://stripe.dev/stripe-java/com/stripe/net/RequestOptions.RequestOptionsBuilder.html) — read 2026-10-14.
9. [Webhook Javadoc](https://stripe.dev/stripe-java/com/stripe/net/Webhook.html) — read 2026-10-14.
10. [EventDataObjectDeserializer Javadoc](https://stripe.dev/stripe-java/com/stripe/model/EventDataObjectDeserializer.html) — read 2026-10-14.
11. [Event Javadoc](https://stripe.dev/stripe-java/com/stripe/model/Event.html) — read 2026-10-14.
12. [Subscription Javadoc](https://stripe.dev/stripe-java/com/stripe/model/Subscription.html) — read 2026-10-14.
13. [Invoice.Parent Javadoc](https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html) — read 2026-10-14.
14. [Invoice.Parent.SubscriptionDetails Javadoc](https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html) — read 2026-10-14.

### Official Documentation
15. [Stripe API reference (Java)](https://docs.stripe.com/api?lang=java) — read 2026-10-14.
16. [Create a PaymentIntent (Java)](https://docs.stripe.com/api/payment_intents/create?lang=java) — read 2026-10-14.
17. [Confirm a PaymentIntent (Java)](https://docs.stripe.com/api/payment_intents/confirm?lang=java) — read 2026-10-14.
18. [Retrieve a PaymentIntent (Java)](https://docs.stripe.com/api/payment_intents/retrieve?lang=java) — read 2026-10-14.
19. [PaymentIntents guide (Java)](https://docs.stripe.com/payments/payment-intents?lang=java) — read 2026-10-14.
20. [Webhooks quickstart (Java)](https://docs.stripe.com/webhooks/quickstart?lang=java) — read 2026-10-14.
21. [Manage webhook endpoints](https://docs.stripe.com/events/manage-webhook-endpoints) — read 2026-10-14.
22. [Error handling (Java)](https://docs.stripe.com/error-handling?lang=java) — read 2026-10-14.
23. [Customers create (Java)](https://docs.stripe.com/api/customers/create?lang=java) — read 2026-10-14.
24. [Prices create (Java)](https://docs.stripe.com/api/prices/create?lang=java) — read 2026-10-14.
25. [Subscriptions create (Java)](https://docs.stripe.com/api/subscriptions/create?lang=java) — read 2026-10-14.
26. [Expanding responses (Java)](https://docs.stripe.com/expand?lang=java) — read 2026-10-14.
27. [Invoice object (Java)](https://docs.stripe.com/api/invoices/object?lang=java) — read 2026-10-14.
28. [Billing subscriptions webhooks](https://docs.stripe.com/billing/subscriptions/webhooks) — read 2026-10-14.
29. [Basil changelog — parent field on invoicing objects](https://docs.stripe.com/changelog/basil/2025-03-31/adds-new-parent-field-to-invoicing-objects.md) — read 2026-10-14.
