---
Full_Name: "Stripe Java SDK (com.stripe:stripe-java)"
Target_Version: "33.x (latest patch confirmed: 33.1.1)"
Release_Date: "33.0.0 → 2026-06-05 (out-of-band major) · 33.1.0 → 2026-06-24 · 33.1.1 (latest 33.x) → 2026-07-15"
Support_Status: "Current stable major line as of Research_Date (2026-07-23). Actively maintained. 32.x and earlier are superseded and treated here as disinformation per version-absolutism."
Primary_Docs: "https://docs.stripe.com/api?lang=java · https://docs.stripe.com/webhooks?lang=java · https://docs.stripe.com/error-handling?lang=java"
Official_Repo: "https://github.com/stripe/stripe-java"
Research_Date: "2026-07-23"
Domain_Complexity: "Complex (security-critical payments; PCI-adjacent; webhook trust boundary)"
Pinned_Stripe_API_Version: "33.1.x pins 2026-06-24.dahlia · 33.0.0 pins 2026-05-27.dahlia"
Java_Baseline: "LTS JDKs — Java 8 (1.8), 11, 17, 21, 25 (per 33.x README, checked 2026-07-23)"
---

# Stripe Java SDK **33.x** — Version-Absolute Research Knowledge Base

> **VERSION LOCK:** This document describes **stripe-java 33.x** ONLY (latest confirmed patch **33.1.1**,
> released **2026-07-15**, pinning Stripe API version **`2026-06-24.dahlia`**; the initial **33.0.0
> (2026-06-05)** pins **`2026-05-27.dahlia`**). Patterns from **32.x and earlier are treated as
> disinformation** and must not be mixed in. This is a **fresh 33.x research task** — it does NOT reuse
> claims from the superseded 29.x knowledge base. Where a fact could not be confirmed against an official,
> dated source, it is explicitly flagged **unverified**.

---

## 1. Executive Summary

**stripe-java 33.x** is the official Java client library (Maven coordinates `com.stripe:stripe-java`) for the
Stripe REST API. The 33.x major line begins at **33.0.0 (2026-06-05)** — an **out-of-band major** that,
per the official release notes, "doesn't change the pinned API version; it still uses `2026-05-27.dahlia`"
and exists solely "to update a field type that changed": PR #2234 made **`tax_rate.tax_details` expandable**.
The release notes state plainly: *"If you're not using `tax_details`, this is a no-op release."* The latest
patch confirmed from the official CHANGELOG is **33.1.1 (2026-07-15)**, and the **33.1.x** line pins the
Stripe API version **`2026-06-24.dahlia`**. Both `dahlia` API versions are the current 2026 series
(successor to the earlier `clover` and `basil` series). Teams on 32.x or earlier MUST read the Migration
Guide (Section 3), which is a **multi-major jump** with several breaking changes.

The **defining architectural pattern** in 33.x is the **service-based `StripeClient` with the `v1()`
namespace**: you instantiate `StripeClient client = new StripeClient(apiKey)` once and call typed services
through `client.v1().customers().create(params)` using **typed parameter builders**
(`CustomerCreateParams.builder()...build()`). Per the 33.x README (checked 2026-07-23), the **legacy static
resource pattern** (`Customer.create(...)`) "is still available to use but **will be marked as deprecated
soon**" — so new 33.x code MUST use `StripeClient` + `v1()`. Note the cumulative history: the flat
top-level service accessors were **deprecated in 31.0.0** in favor of `v1()`, event handling was overhauled
into strongly-typed `EventNotification` classes in **30.0.0**, and **32.0.0** re-parented
`RateLimitException` under `StripeException` (no longer `ApiException`), renamed `parseThinEvent` →
`parseEventNotification`, moved V2 decimal fields from `String` to `BigDecimal`, and changed the module name
from `stripe.java` to `com.stripe`.

Because payments are **security-critical**, this knowledge base is rated **Complex**. The three highest-risk
surfaces are unchanged in 33.x: (1) **webhook signature verification** (the server-side trust boundary — an
unverified webhook is attacker-controlled input; 33.x uses `client.constructEvent(payload, sigHeader,
endpointSecret)` throwing `SignatureVerificationException`), (2) **idempotency keys** on all state-changing
retries (to prevent double charges, via `RequestOptions.builder().setIdempotencyKey(...)`), and (3)
**secret-key handling** (never in source; env / secret-manager only). Every guardrail below targets
**stripe-java 33.x** with the pinned API version **`2026-06-24.dahlia`**.

---

## 2. Architectural Guardrails

### ✅ Mandatory Patterns (Complex tier — 9 patterns)

**A1 — Instantiate `StripeClient` once; reuse it (33.x service pattern).**
```java
// stripe-java 33.x — service-based client (preferred; NOT the legacy static pattern)
import com.stripe.StripeClient;

StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
// Reuse `client` across the app: it owns the HTTP client / connection pool.
```
Source: [stripe-java README — recommended usage](https://github.com/stripe/stripe-java) (checked 2026-07-23).

**A2 — Use typed parameter builders through the `v1()` namespace, never raw maps.**
```java
// stripe-java 33.x — v1() namespace + typed builders
CustomerCreateParams params = CustomerCreateParams.builder()
    .setEmail("jane@example.com")
    .setDescription("KB demo customer (stripe-java 33.x)")
    .build();
Customer customer = client.v1().customers().create(params);
```
Builders give compile-time safety against field-name typos. The `v1()` namespace is the non-deprecated
accessor (flat top-level accessors were deprecated in 31.0.0).
Source: [stripe-java README](https://github.com/stripe/stripe-java) (2026-07-23).

**A3 — Idempotency keys on every state-changing call (retry-safe).**
```java
// stripe-java 33.x — stable key per LOGICAL operation, NOT per attempt
RequestOptions opts = RequestOptions.builder()
    .setIdempotencyKey(orderId + ":create-pi")  // deterministic per order, reused on retry
    .build();
PaymentIntent pi = client.v1().paymentIntents().create(piParams, opts);
```
Source: [stripe-java README — RequestOptions idempotency](https://github.com/stripe/stripe-java) (2026-07-23);
[Stripe idempotency docs](https://docs.stripe.com/api/idempotent_requests) (2026-07-23).

**A4 — Verify webhook signatures before trusting any payload (trust boundary).**
```java
// stripe-java 33.x — instance method on StripeClient (delegates to Webhook.constructEvent)
Event event = client.constructEvent(payload, sigHeader, endpointSecret);
// Throws SignatureVerificationException if the payload is not genuinely from Stripe.
```
The underlying static overloads confirmed in `Webhook.java` (checked 2026-07-23) are:
`constructEvent(String payload, String sigHeader, String secret)`,
`constructEvent(..., long tolerance)`, and `constructEvent(..., long tolerance, Clock clock)` — all
returning `Event` and declaring `throws SignatureVerificationException`. Default timestamp tolerance
`DEFAULT_TOLERANCE = 300` seconds (5 minutes).
Source: [Stripe Webhooks docs — Java](https://docs.stripe.com/webhooks?lang=java) (2026-07-23);
[stripe-java `Webhook.java`](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/net/Webhook.java) (2026-07-23).

**A5 — Catch the `StripeException` hierarchy by subtype (most specific first).**
Subclasses confirmed for 33.x from the official error-handling docs (checked 2026-07-23): `CardException`,
`InvalidRequestException`, `ApiConnectionException`, `ApiException`, `AuthenticationException`,
`IdempotencyException`, `PermissionException`, `RateLimitException`, `SignatureVerificationException`.
As of the 32.0.0 breaking change (carried into 33.x), **`RateLimitException` extends `StripeException`
directly** (no longer `ApiException`).
```java
// stripe-java 33.x — catch specific subtypes before the base StripeException
try {
    PaymentIntent paymentIntent = client.v1().paymentIntents().create(params);
} catch (CardException e) {
    // Card declined / payment error — surface e.getCode() / e.getDeclineCode() to caller
    log.warn("Payment error: {}", e.getMessage());
} catch (RateLimitException e) {
    // Back off and retry with jitter
    log.warn("Rate limited; backing off");
} catch (InvalidRequestException e) {
    // Programming/config error — invalid params. Do NOT retry blindly.
    log.error("Invalid request (id={})", e.getRequestId());
} catch (StripeException e) {
    // Auth / connection / API / idempotency errors
    log.error("Stripe error: status={} code={} reqId={}", e.getStatusCode(), e.getCode(), e.getRequestId());
}
```
Source: [Stripe error handling — Java](https://docs.stripe.com/error-handling?lang=java) (2026-07-23);
[stripe-java CHANGELOG — 32.0.0 RateLimitException reparent](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) (2026-07-23).

**A6 — Pin the Stripe API version explicitly; let the SDK major own the default.**
The 33.1.x major pins **`2026-06-24.dahlia`** (33.0.0 pins `2026-05-27.dahlia`) — the SDK sets this by
default. For deterministic behavior across environments, set it explicitly via `RequestOptions` or a
per-request `StripeVersion` override so an SDK bump never silently changes wire behavior.
```java
// stripe-java 33.x — explicit API version override (defense-in-depth)
RequestOptions opts = RequestOptions.builder()
    .setStripeVersionOverride("2026-06-24.dahlia")   // match the SDK-pinned dahlia version
    .build();
```
Source: [stripe-java CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) (2026-07-23);
[Stripe API versioning](https://docs.stripe.com/api/versioning) (2026-07-23).
> ⚠️ `setStripeVersionOverride` method name is **unverified** against 33.x Javadoc (see Agent Notes); the
> pinned version string `2026-06-24.dahlia` IS verified.

**A7 — Read the secret key from the environment / secret manager, never from source.**
```java
// stripe-java 33.x — key from env; sk_live_* keys must never be committed
String apiKey = System.getenv("STRIPE_SECRET_KEY");
if (apiKey == null || apiKey.isBlank()) {
    throw new IllegalStateException("STRIPE_SECRET_KEY not set");
}
StripeClient client = new StripeClient(apiKey);
```
Source: [Stripe API keys / security](https://docs.stripe.com/keys) (2026-07-23).

**A8 — Use expandable fields to avoid N+1 round trips (33.x expand API).**
```java
// stripe-java 33.x — expand nested objects in a single request
PaymentIntentRetrieveParams params = PaymentIntentRetrieveParams.builder()
    .addExpand("customer")
    .addExpand("latest_charge")
    .build();
PaymentIntent pi = client.v1().paymentIntents().retrieve(piId, params, null);
```
Note: 33.0.0 specifically made **`tax_rate.tax_details` expandable** (PR #2234) — if you read
`tax_details`, its type changed and must be expanded/updated when upgrading.
Source: [Stripe expanding responses](https://docs.stripe.com/expand) (2026-07-23);
[stripe-java v33.0.0 release notes](https://github.com/stripe/stripe-java/releases/tag/v33.0.0) (2026-07-23).

**A9 — Use amounts in the smallest currency unit (integer minor units) computed server-side.**
Stripe amounts are integers in the smallest currency unit (e.g., cents). Compute the amount on the server
from your own catalog/price data — never from a client-supplied number.
```java
// stripe-java 33.x — 2000 = $20.00 USD (minor units), derived server-side
PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(2000L)
    .setCurrency("usd")
    .build();
```
Source: [Stripe amounts / currencies](https://docs.stripe.com/currencies#zero-decimal) (2026-07-23).

---

### ⚠️ Conditional Patterns (tradeoff matrices)

**C1 — Synchronous vs. asynchronous calls.**

| Option | Latency model | Best when | Cost |
|---|---|---|---|
| Synchronous (default `client.v1()...`) | Blocks calling thread | Request/response web handlers, simple flows | Ties up a thread per in-flight call |
| Async (wrap in your own executor / reactive layer) | Non-blocking | High-throughput, many concurrent Stripe calls | You own thread-pool sizing + backpressure |

33.x ships synchronous service methods; async is achieved by wrapping calls in your application's executor.
> ⚠️ Whether 33.x exposes first-class async service methods is **unverified** — treat as sync-only.

**C2 — `StripeClient` instance vs. deprecated static resource pattern.**

| Option | Status in 33.x | Use when |
|---|---|---|
| `client.v1().customers().create(...)` | ✅ Recommended, non-deprecated | All new 33.x code |
| `Customer.create(...)` (static, global key) | ⚠️ "will be marked as deprecated soon" (README) | Only legacy code mid-migration |

Source: [stripe-java README](https://github.com/stripe/stripe-java) (2026-07-23).

**C3 — PaymentIntent automatic vs. manual confirmation.**

| Option | Flow | Best when | Tradeoff |
|---|---|---|---|
| Automatic confirmation (`automatic_payment_methods`) | Stripe manages next actions client-side | Standard checkout, PaymentElement | Less server control |
| Manual confirmation (`confirm=true` server-side) | Server drives confirmation | MOTO, saved-method off-session | You must handle `requires_action` / SCA |

Source: [Stripe PaymentIntents lifecycle](https://docs.stripe.com/payments/paymentintents/lifecycle) (2026-07-23).

**C4 — Webhook idempotency storage backend.**

| Option | Dedup key | Best when | Tradeoff |
|---|---|---|---|
| Relational unique index on `event.id` | Strong, transactional | Already have a DB | Extra write per event |
| Redis SETNX with TTL | Fast, ephemeral | High volume, tolerant of TTL window | Not durable past TTL |
| No storage (rely on handler idempotency) | — | Handlers are naturally idempotent | Risky for side-effecting handlers |

Stripe may deliver an event more than once; dedup on `event.getId()`.
Source: [Stripe webhooks best practices](https://docs.stripe.com/webhooks#handle-duplicate-events) (2026-07-23).

**C5 — Pagination: auto-pagination vs. manual page cursors.**

| Option | Ergonomics | Best when | Tradeoff |
|---|---|---|---|
| `.autoPagingIterable()` | Simple `for` loop over all results | Batch jobs, exports | Unbounded fetches; watch memory/time |
| Manual `starting_after` cursor | Explicit page control | UI pagination, bounded pages | More code |

Source: [Stripe pagination](https://docs.stripe.com/api/pagination) (2026-07-23).

**C6 — Network retry policy: SDK auto-retries vs. application-level retries.**

| Option | Where retries happen | Best when | Tradeoff |
|---|---|---|---|
| SDK `setMaxNetworkRetries(n)` (default 2) | Inside the client, idempotent-safe | Transient network errors | Bounded; SDK adds idempotency key automatically |
| App-level retry loop | Your code | Business-level retry semantics | MUST pass a stable idempotency key yourself |

Default `maxNetworkRetries` is **2** in 33.x.
Source: [stripe-java `Stripe.java` defaults](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/Stripe.java) (2026-07-23).

---

### 🚫 Forbidden Patterns (each with ✅ 33.x alternative)

**F1 — Hardcoded secret keys.**
```java
// 🚫 NEVER — key committed to source (leak = full account compromise)
StripeClient client = new StripeClient("sk_live_51Hxxxxxxxxxxxxxxxx");

// ✅ 33.x — read from env / secret manager
StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
```
Source: [Stripe API keys](https://docs.stripe.com/keys#safe-keys) (2026-07-23).

**F2 — Skipping webhook signature verification.**
```java
// 🚫 NEVER — trusting raw body = accepting attacker-forged events
Event event = ApiResource.GSON.fromJson(payload, Event.class);

// ✅ 33.x — verify signature; only then trust the event
Event event = client.constructEvent(payload, sigHeader, endpointSecret); // throws SignatureVerificationException
```
Source: [Stripe webhook signatures](https://docs.stripe.com/webhooks/signature) (2026-07-23).

**F3 — No idempotency key on retried state-changing calls.**
```java
// 🚫 NEVER — a network retry can create a SECOND charge
PaymentIntent pi = client.v1().paymentIntents().create(params);

// ✅ 33.x — stable idempotency key makes retries safe
RequestOptions opts = RequestOptions.builder().setIdempotencyKey(orderId + ":create-pi").build();
PaymentIntent pi = client.v1().paymentIntents().create(params, opts);
```
Source: [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests) (2026-07-23).

**F4 — Catching generic `Exception` instead of `StripeException` subtypes.**
```java
// 🚫 NEVER — swallows card declines, rate limits, and bugs identically
try { client.v1().paymentIntents().create(params); }
catch (Exception e) { log.error("failed", e); }

// ✅ 33.x — branch on subtype (see A5): CardException, RateLimitException, InvalidRequestException, StripeException
```
Source: [Stripe error handling — Java](https://docs.stripe.com/error-handling?lang=java) (2026-07-23).

**F5 — Trusting a client-supplied amount.**
```java
// 🚫 NEVER — attacker sends amount=1 for a $500 order
long amount = Long.parseLong(request.queryParams("amount"));

// ✅ 33.x — compute amount server-side from your own price/catalog data (minor units)
long amount = order.totalMinorUnits(); // authoritative, server-derived
PaymentIntentCreateParams p = PaymentIntentCreateParams.builder().setAmount(amount).setCurrency("usd").build();
```
Source: [Stripe integration security](https://docs.stripe.com/security/guide) (2026-07-23).

**F6 — Mixing SDK majors / conflicting API versions on one classpath.**
```xml
<!-- 🚫 NEVER — two stripe-java majors resolve to one jar; behavior is undefined -->
<!-- 32.x transitive + 33.x direct on the same classpath -->

<!-- ✅ 33.x — one and only one stripe-java version; run `mvn dependency:tree` to confirm -->
<dependency>
  <groupId>com.stripe</groupId>
  <artifactId>stripe-java</artifactId>
  <version>33.1.1</version>
</dependency>
```
Source: [stripe-java releases](https://github.com/stripe/stripe-java/releases) (2026-07-23).

**F7 — New code on the deprecated static resource pattern.**
```java
// 🚫 AVOID in 33.x — static pattern is "will be marked as deprecated soon"
Stripe.apiKey = System.getenv("STRIPE_SECRET_KEY");
Customer c = Customer.create(paramsMap);

// ✅ 33.x — service-based client + v1() namespace + typed builders
StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
Customer c = client.v1().customers().create(CustomerCreateParams.builder().setEmail("x@y.com").build());
```
Source: [stripe-java README](https://github.com/stripe/stripe-java) (2026-07-23).

---

## 3. Migration Guide

### 3a. 32.x → 33.x breaking changes (from the official CHANGELOG, 2026-07-23)

**33.0.0 is an out-of-band major with a single behavioral change:**
- **`tax_rate.tax_details` is now expandable** (PR #2234). Its type changed slightly. If you do NOT use
  `tax_details`, 33.0.0 is a **no-op** vs. the prior release. The pinned API version is unchanged at
  `2026-05-27.dahlia` for 33.0.0.

**Step-by-step upgrade path (32.x → 33.1.1):**
1. Bump the dependency to `33.1.1` (Maven/Gradle) — see Section 5.
2. Run `mvn dependency:tree` and confirm exactly one `com.stripe:stripe-java:33.1.1` (no lingering 32.x).
3. `grep` your codebase for `tax_details` usage. If present, update to read it as an expandable field
   (add `.addExpand("tax_details")` where you read it and adjust the accessor type).
4. Recompile (`mvn -q -DskipTests compile`). If you avoid `tax_details`, expect zero source changes.
5. Note that 33.1.x pins **`2026-06-24.dahlia`** (33.0.0 pinned `2026-05-27.dahlia`); review that API
   changelog diff if you rely on API-version-sensitive fields.
6. Re-run webhook tests with the Stripe CLI (Section 5).

### 3b. Cumulative note for a 29.x → 33.x jump (multi-major — read all)

A team leaping from 29.x must absorb the breaking changes across 30, 31, 32, and 33 (CHANGELOG, 2026-07-23):

- **30.0.0** (`2025-09-30.clover`): event handling overhauled into strongly-typed `EventNotification`
  classes; event resources moved from `v2` to `v2.core`; new `StripeContext` object; throws
  `ApiKeyMissingException` instead of `IllegalArgumentException`; V2 query params `Integer`→`Long`.
- **31.0.0** (`2025-11-17.clover`): V2 array serialization switched to indexed format
  (`?include[0]=foo`); V2 delete ops return `V2DeletedObject`; query params `Integer`→`Long`;
  **flat top-level service accessors deprecated in favor of `v1()`**.
- **32.0.0** (`2026-03-25.dahlia`): removed `RequestOptions.getApiKey()` (→ `getAuthenticator()`);
  V2 decimal fields `String`→`BigDecimal`; **`RateLimitException` now extends `StripeException`**
  (was `ApiException`); `parseThinEvent` renamed **`parseEventNotification`**; module name
  `stripe.java` → `com.stripe`.
- **33.0.0 / 33.1.x** (`2026-05-27.dahlia` / `2026-06-24.dahlia`): `tax_rate.tax_details` expandable.

> Because this is a multi-major jump, budget time to migrate off the static pattern (A1/A2/F7), adopt
> `v1()` everywhere, and rewrite exception handling around the 32.0.0 `RateLimitException` reparenting.

Source: [stripe-java CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) (2026-07-23);
[stripe-java releases](https://github.com/stripe/stripe-java/releases) (2026-07-23).

---

## 4. Implementation Blueprint (all 33.x-tagged)

### 4a. Create a PaymentIntent
```java
// stripe-java 33.x — create a PaymentIntent with idempotency + server-derived amount
import com.stripe.StripeClient;
import com.stripe.model.PaymentIntent;
import com.stripe.net.RequestOptions;
import com.stripe.param.PaymentIntentCreateParams;

public PaymentIntent createIntent(String orderId, long amountMinorUnits) throws Exception {
    StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY")); // A7

    PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
        .setAmount(amountMinorUnits)          // A9 — integer minor units, server-derived
        .setCurrency("usd")
        .setAutomaticPaymentMethods(          // C3 — automatic confirmation flow
            PaymentIntentCreateParams.AutomaticPaymentMethods.builder().setEnabled(true).build())
        .build();

    RequestOptions opts = RequestOptions.builder()
        .setIdempotencyKey(orderId + ":create-pi")   // A3 — stable per logical op
        .build();

    return client.v1().paymentIntents().create(params, opts); // A1/A2 — StripeClient + v1()
}
```
Source: [Stripe PaymentIntents API — Java](https://docs.stripe.com/api/payment_intents/create?lang=java) (2026-07-23).

### 4b. Create a Customer + Subscription (Billing)
```java
// stripe-java 33.x — create a Customer then subscribe them to an existing Price
import com.stripe.StripeClient;
import com.stripe.model.Customer;
import com.stripe.model.Subscription;
import com.stripe.param.CustomerCreateParams;
import com.stripe.param.SubscriptionCreateParams;

public Subscription subscribe(String email, String priceId) throws Exception {
    StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));

    // 1) Customer
    Customer customer = client.v1().customers().create(
        CustomerCreateParams.builder()
            .setEmail(email)
            .setDescription("stripe-java 33.x subscriber")
            .build());

    // 2) Subscription referencing a pre-created Price (Product+Price live in your Stripe dashboard/API)
    SubscriptionCreateParams subParams = SubscriptionCreateParams.builder()
        .setCustomer(customer.getId())
        .addItem(SubscriptionCreateParams.Item.builder().setPrice(priceId).build())
        .addExpand("latest_invoice.payment_intent")   // A8 — expand to avoid N+1
        .build();

    return client.v1().subscriptions().create(subParams);
}
```
Source: [Stripe Subscriptions API — Java](https://docs.stripe.com/api/subscriptions/create?lang=java) (2026-07-23);
[Stripe Prices API](https://docs.stripe.com/api/prices?lang=java) (2026-07-23).

### 4c. Webhook endpoint with signature verification (payment_intent.succeeded + invoice.paid)
```java
// stripe-java 33.x — Spark-style handler; verify signature THEN dispatch
import com.stripe.StripeClient;
import com.stripe.exception.SignatureVerificationException;
import com.stripe.model.Event;
import com.stripe.model.StripeObject;
import com.stripe.model.PaymentIntent;
import com.stripe.model.Invoice;

public String handleWebhook(String payload, String sigHeader) {
    StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
    String endpointSecret = System.getenv("STRIPE_WEBHOOK_SECRET"); // whsec_...

    Event event;
    try {
        // A4 — signature verification (throws on forged/expired payloads; tolerance 300s)
        event = client.constructEvent(payload, sigHeader, endpointSecret);
    } catch (SignatureVerificationException e) {
        return respond(400, "Invalid signature"); // F2 — reject unverified input
    }

    // C4 — idempotency: dedup on event.getId() before side effects
    if (alreadyProcessed(event.getId())) {
        return respond(200, "duplicate ignored");
    }

    StripeObject obj = event.getDataObjectDeserializer().getObject().orElse(null);
    switch (event.getType()) {
        case "payment_intent.succeeded": {
            PaymentIntent pi = (PaymentIntent) obj;
            fulfillOrder(pi.getId());
            break;
        }
        case "invoice.paid": {
            Invoice invoice = (Invoice) obj;
            activateSubscriptionPeriod(invoice.getSubscription());
            break;
        }
        default:
            // Log unhandled types; still return 200 so Stripe stops retrying
            log.info("Unhandled 33.x event type: {}", event.getType());
    }
    markProcessed(event.getId());
    return respond(200, "ok");
}
```
Source: [Stripe webhooks — Java](https://docs.stripe.com/webhooks?lang=java) (2026-07-23);
[Stripe handle payment events](https://docs.stripe.com/webhooks/handling-payment-events) (2026-07-23).

> Note: the official webhooks page demonstrates `payment_intent.succeeded` and `payment_method.attached`;
> the `invoice.paid` case and `getSubscription()` accessor are standard Billing patterns — verify the exact
> `Invoice` accessor name against 33.x Javadoc for your build (see Agent Notes).

---

## 5. Quality Control (verification commands + expected output)

### 5a. Maven dependency (must show 33.x)
```xml
<dependency>
  <groupId>com.stripe</groupId>
  <artifactId>stripe-java</artifactId>
  <version>33.1.1</version>
</dependency>
```
### 5b. Gradle dependency
```groovy
implementation "com.stripe:stripe-java:33.1.1"
```
Source: [stripe-java README](https://github.com/stripe/stripe-java) (2026-07-23);
[Maven Central com.stripe:stripe-java](https://central.sonatype.com/artifact/com.stripe/stripe-java) (2026-07-23).

### 5c. `mvn dependency:tree` — expected output (excerpt)
```text
$ mvn dependency:tree | grep stripe
[INFO] +- com.stripe:stripe-java:jar:33.1.1:compile
# Expected: exactly ONE stripe-java line, resolving to 33.1.1. Any 32.x line = mixed majors (F6) → fix.
```

### 5d. Compile check
```text
$ mvn -q -DskipTests compile
# Expected: BUILD SUCCESS with no "cannot find symbol" errors for StripeClient / v1() / *CreateParams.
# A "cannot find symbol: method v1()" error means a pre-31.x jar leaked onto the classpath.
```

### 5e. Stripe CLI local webhook test
```text
$ stripe listen --forward-to localhost:4242/webhook
> Ready! You are using Stripe API Version [2026-06-24.dahlia]. Your webhook signing secret is whsec_xxx (^C to quit)

$ stripe trigger payment_intent.succeeded
Setting up fixture for: payment_intent
Trigger succeeded! Check dashboard for event details.

# In the listen terminal you should see:
2026-07-23 10:00:00  --> payment_intent.succeeded [evt_1Nxxxx]
2026-07-23 10:00:00 <--  [200] POST http://localhost:4242/webhook [evt_1Nxxxx]

$ stripe trigger invoice.paid
Trigger succeeded! Check dashboard for event details.
# listen terminal:
2026-07-23 10:01:00  --> invoice.paid [evt_1Nyyyy]
2026-07-23 10:01:00 <--  [200] POST http://localhost:4242/webhook [evt_1Nyyyy]
```
A `[400]` response means signature verification failed — confirm your framework passes the **raw** body
(A4/F2) and `STRIPE_WEBHOOK_SECRET` matches the `whsec_` printed by `stripe listen`.
Source: [Stripe CLI docs](https://docs.stripe.com/stripe-cli) (2026-07-23);
[Stripe CLI trigger](https://docs.stripe.com/cli/trigger) (2026-07-23).

---

## 6. Production Readiness

- **Timeouts (33.x defaults, from `Stripe.java`, 2026-07-23):** connect timeout `DEFAULT_CONNECT_TIMEOUT =
  30000` ms (30 s); read timeout `DEFAULT_READ_TIMEOUT = 80000` ms (80 s). Tune per SLA via
  `RequestOptions.builder().setConnectTimeout(...).setReadTimeout(...)`.
  Source: [stripe-java `Stripe.java`](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/Stripe.java) (2026-07-23).
- **Max network retries (default 2):** the SDK auto-retries idempotent/transient failures up to 2 times and
  automatically attaches an idempotency key to retried requests. Raise via `setMaxNetworkRetries(n)` for
  flaky networks; keep app-level retries idempotent (C6/F3).
  Source: same `Stripe.java` (2026-07-23).
- **Rate limits:** Stripe enforces per-account request-rate limits; handle `RateLimitException` (A5) with
  exponential backoff + jitter. Live mode limits differ from test mode.
  Source: [Stripe rate limits](https://docs.stripe.com/rate-limits) (2026-07-23).
- **Monitoring:** log `getRequestId()` on every `StripeException` for Stripe support correlation; alert on
  spikes in `CardException` decline codes and any `AuthenticationException` (key rotation/leak signal);
  monitor webhook endpoint 2xx rate and Stripe's automatic-retry/backoff for failing endpoints.
  Source: [Stripe request IDs / logs](https://docs.stripe.com/dashboard/basics#logs) (2026-07-23).
- **Security hardening (PCI + keys):** use **restricted API keys** scoped to only the resources a service
  needs; never let raw PAN touch your server (use Stripe.js / Elements / PaymentElement to keep card data
  out of PCI scope — SAQ A); rotate keys on suspected leak; store `whsec_` and `sk_` in a secret manager.
  Source: [Stripe restricted keys](https://docs.stripe.com/keys#limit-access) (2026-07-23);
  [Stripe PCI compliance](https://docs.stripe.com/security/guide#validating-pci-compliance) (2026-07-23).

---

## 7. Source Bibliography (all dated 2026-07-23 unless noted)

### Primary — Official Stripe docs
- [Stripe API reference (Java)](https://docs.stripe.com/api?lang=java) — checked 2026-07-23
- [Stripe Webhooks (Java)](https://docs.stripe.com/webhooks?lang=java) — checked 2026-07-23
- [Stripe webhook signatures](https://docs.stripe.com/webhooks/signature) — checked 2026-07-23
- [Stripe error handling (Java)](https://docs.stripe.com/error-handling?lang=java) — checked 2026-07-23
- [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests) — checked 2026-07-23
- [Stripe PaymentIntents create (Java)](https://docs.stripe.com/api/payment_intents/create?lang=java) — checked 2026-07-23
- [Stripe Subscriptions create (Java)](https://docs.stripe.com/api/subscriptions/create?lang=java) — checked 2026-07-23
- [Stripe Prices API](https://docs.stripe.com/api/prices?lang=java) — checked 2026-07-23
- [Stripe expand](https://docs.stripe.com/expand) — checked 2026-07-23
- [Stripe pagination](https://docs.stripe.com/api/pagination) — checked 2026-07-23
- [Stripe rate limits](https://docs.stripe.com/rate-limits) — checked 2026-07-23
- [Stripe API keys / restricted keys](https://docs.stripe.com/keys) — checked 2026-07-23
- [Stripe security guide / PCI](https://docs.stripe.com/security/guide) — checked 2026-07-23
- [Stripe CLI](https://docs.stripe.com/stripe-cli) · [trigger](https://docs.stripe.com/cli/trigger) — checked 2026-07-23

### Primary — Official GitHub (stripe/stripe-java)
- [stripe-java README](https://github.com/stripe/stripe-java) — checked 2026-07-23 (Java baseline, deps, StripeClient/v1(), idempotency, RequestOptions)
- [stripe-java CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) — checked 2026-07-23 (33.1.1/33.1.0/33.0.0 dates + pinned API versions; 30–32 breaking changes)
- [stripe-java Releases](https://github.com/stripe/stripe-java/releases) — checked 2026-07-23
- [v33.0.0 release notes](https://github.com/stripe/stripe-java/releases/tag/v33.0.0) — released 2026-06-05/06; checked 2026-07-23 (out-of-band major, tax_details expandable, pins 2026-05-27.dahlia)
- [`Stripe.java`](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/Stripe.java) — checked 2026-07-23 (VERSION=33.1.1; DEFAULT_CONNECT_TIMEOUT=30000; DEFAULT_READ_TIMEOUT=80000; maxNetworkRetries default 2)
- [`Webhook.java`](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/net/Webhook.java) — checked 2026-07-23 (constructEvent overloads; DEFAULT_TOLERANCE=300)

### Registry
- [Maven Central — com.stripe:stripe-java](https://central.sonatype.com/artifact/com.stripe/stripe-java) — checked 2026-07-23

---

## 8. Agent Operation Notes

### Confirmed facts (High confidence — official, dated sources)
- **Latest 33.x patch = 33.1.1 (2026-07-15)**; also 33.1.0 (2026-06-24), 33.0.0 (2026-06-05). *(CHANGELOG + README VERSION="33.1.1")*
- **Pinned API version:** 33.1.x → `2026-06-24.dahlia`; 33.0.0 → `2026-05-27.dahlia`. *(CHANGELOG + v33.0.0 release notes)*
- **Java baseline:** LTS JDKs 8/11/17/21/**25** supported in 33.x. *(README)*
- **StripeClient + `v1()` + typed builders** is the recommended 33.x pattern; **static resource pattern is
  NOT yet deprecated but "will be marked as deprecated soon"** (README wording verbatim). *(README)*
- **Webhook:** `client.constructEvent(payload, sigHeader, endpointSecret)` → `Event`, throws
  `SignatureVerificationException`; static overloads + `DEFAULT_TOLERANCE=300`. *(docs + Webhook.java)*
- **Idempotency:** `RequestOptions.builder().setIdempotencyKey(...)`. *(README)*
- **Exception hierarchy (33.x):** CardException, InvalidRequestException, ApiConnectionException,
  ApiException, AuthenticationException, IdempotencyException, PermissionException, RateLimitException,
  SignatureVerificationException — all under `StripeException`; **RateLimitException reparented under
  StripeException in 32.0.0** (carried into 33.x). *(error-handling docs + CHANGELOG)*
- **Defaults:** connect 30 s, read 80 s, maxNetworkRetries 2. *(Stripe.java)*
- **32→33 breaking change:** `tax_rate.tax_details` expandable (33.0.0, PR #2234). *(v33.0.0 notes)*
- **Cumulative 29→33 breaking changes** across 30/31/32/33. *(CHANGELOG)*

### Unverified items (flagged — could not confirm against a dated official source)
1. **`RequestOptions.setStripeVersionOverride("...")` method name** (A6) — the *pinned version string*
   `2026-06-24.dahlia` is verified, but the exact 33.x setter/method name for a per-request API-version
   override was not confirmed against 33.x Javadoc. Verify before use.
2. **First-class async service methods in 33.x** (C1) — treated as sync-only; async support unverified.
3. **`Invoice.getSubscription()` accessor name** in 4c — Billing pattern is standard, but the exact 33.x
   Javadoc accessor (field could be nested/expandable under dahlia) was not directly confirmed.
4. **`invoice.paid` handling** shown by extrapolation — the official webhooks page demonstrates
   `payment_intent.succeeded` + `payment_method.attached`; `invoice.paid` dispatch is standard but not on
   the fetched page.
5. **Exact `2026-06-24.dahlia` / `2026-05-27.dahlia` per-field API changelog diffs** — the version *names
   and pins* are verified from the CHANGELOG; the granular API-changelog page for dahlia was not fetched.

### Recommendation
Run `/skill-best-practices-validator` on this output, and confirm items 1–5 against the 33.1.1 Javadoc
(`javadoc.io/doc/com.stripe/stripe-java/33.1.1`) before authoring a downstream skill.
