---
Full_Name: "Stripe Java SDK (com.stripe:stripe-java)"
Target_Version: "29.x (latest patch confirmed: 29.5.0)"
Release_Date: "29.0.0 → 2025-04-01 · 29.5.0 (latest 29.x) → 2025-08-27"
Support_Status: "Superseded major line. As of Research_Date the current stable is 33.x. 29.x is a stable, maintained-during-its-window release but NO LONGER the newest major. Documented here per version-absolutism for teams pinned to 29.x."
Primary_Docs: "https://docs.stripe.com/api?lang=java · https://docs.stripe.com/webhooks?lang=java"
Official_Repo: "https://github.com/stripe/stripe-java"
Research_Date: "2026-07-23"
Domain_Complexity: "Complex (security-critical payments; PCI-adjacent; webhook trust boundary)"
Pinned_Stripe_API_Version: "2025-03-31.basil"
Java_Baseline: "LTS JDKs — Java 8 (1.8), 11, 17, 21 (see verification notes; Java 25 support is a later-33.x README claim, NOT confirmed for 29.x)"
---

# Stripe Java SDK **29.x** — Version-Absolute Research Knowledge Base

> **VERSION LOCK:** This document describes **stripe-java 29.x** ONLY (latest confirmed patch **29.5.0**,
> released **2025-08-27**, pinning Stripe API version **`2025-03-31.basil`**). Patterns from **28.x and
> earlier are treated as disinformation** and must not be mixed in. Where a fact could only be confirmed
> against a newer line (e.g. 33.x README), it is explicitly flagged **unverified for 29.x**.

---

## 1. Executive Summary

**stripe-java 29.x** is the Java client library (Maven coordinates `com.stripe:stripe-java`) for the Stripe
REST API. The 29.x major line begins at **29.0.0 (2025-04-01)** and, per the official CHANGELOG, pins the
Stripe API version **`2025-03-31.basil`**. The latest patch in the line confirmed from official sources is
**29.5.0 (2025-08-27)**. The 29.0.0 release is explicitly a **breaking-change release**: it removed legacy
usage-based billing resources (`SubscriptionItemUsageRecord`, `SubscriptionItemUsageRecordSummary`), removed
the `upcoming`/`upcomingLines` invoice methods (replaced by the **Create Preview Invoice** API), removed the
ability to expand `total_count` on lists, and reorganized several subscription fields (`coupon`,
`promotionCode`, `billingThresholds`). Teams upgrading from 28.x MUST read the Migration Guide (Section 3).

The **defining architectural shift** carried forward and emphasized in 29.x is the **service-based
`StripeClient` pattern**: you instantiate `StripeClient client = new StripeClient(apiKey)` and call typed
services (`client.v1().customers().create(params)`) with **typed parameter builders**
(`CustomerCreateParams.builder()...build()`). The **legacy static resource pattern**
(`Customer.create(...)`) still compiles in 29.x but, per the official README, is slated to be **marked
deprecated soon** — new 29.x code MUST use `StripeClient`. Note the **`v1()` namespace**: in this release,
top-level services are also exposed under a `V1` namespace, and the flat top-level accessors are on a
deprecation path in a future major.

Because payments are **security-critical**, this knowledge base is rated **Complex**. The three highest-risk
surfaces are: (1) **webhook signature verification** (the server-side trust boundary — an unverified webhook
is an attacker-controlled input), (2) **idempotency keys** on all state-changing retries (to prevent double
charges), and (3) **secret-key handling** (never in source; env/secret-manager only). Every guardrail below
targets **stripe-java 29.x** with the pinned API version **`2025-03-31.basil`**.

---

## 2. Architectural Guardrails

### ✅ Mandatory Patterns (Complex tier)

**A1 — Instantiate `StripeClient` once; reuse it (29.x service pattern).**
```java
// stripe-java 29.x — service-based client (preferred; NOT the legacy static pattern)
import com.stripe.StripeClient;

StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
// Reuse `client` across the app: it owns the connection pool / HTTP client.
```
Source: [stripe-java README — recommended usage](https://github.com/stripe/stripe-java) (checked 2026-07-23).

**A2 — Use typed parameter builders, never raw maps.**
```java
// stripe-java 29.x
CustomerCreateParams params = CustomerCreateParams.builder()
    .setEmail("jane@example.com")
    .setDescription("KB demo customer")
    .build();
Customer customer = client.v1().customers().create(params);
```
Builders give compile-time safety against typos in field names.
Source: [stripe-java README](https://github.com/stripe/stripe-java) (2026-07-23).

**A3 — Idempotency keys on every state-changing call (retry-safe).**
```java
// stripe-java 29.x — pass a stable UUID for the logical operation
RequestOptions opts = RequestOptions.builder()
    .setIdempotencyKey(orderId + ":create-pi")  // stable per logical op, NOT per attempt
    .build();
PaymentIntent pi = client.v1().paymentIntents().create(piParams, opts);
```
Source: [stripe-java README — idempotency via RequestOptions](https://github.com/stripe/stripe-java) (2026-07-23);
[Stripe idempotency docs](https://docs.stripe.com/api/idempotent_requests) (2026-07-23).

**A4 — Verify webhook signatures before trusting any payload (trust boundary).**
```java
// stripe-java 29.x — instance method on StripeClient (also: static Webhook.constructEvent)
Event event = client.constructEvent(payload, sigHeader, endpointSecret);
// Throws SignatureVerificationException if the payload is not from Stripe.
```
Source: [Stripe Webhooks docs — Java](https://docs.stripe.com/webhooks?lang=java) (2026-07-23).

**A5 — Catch the `StripeException` hierarchy by subtype (most specific first).**
Direct subclasses (29.x): `CardException`, `InvalidRequestException`, `AuthenticationException`,
`ApiConnectionException`, `ApiException`, `RateLimitException` (extends `InvalidRequestException`),
`IdempotencyException`, `SignatureVerificationException`, `OAuthException`,
`EventDataObjectDeserializationException`.
```java
// stripe-java 29.x — order matters: specific → general
try {
    PaymentIntent pi = client.v1().paymentIntents().create(params, opts);
} catch (com.stripe.exception.CardException e) {          // card declined
    log.warn("card declined code={}", e.getCode());
} catch (com.stripe.exception.RateLimitException e) {     // 429 — back off
    log.warn("rate limited: {}", e.getMessage());
} catch (com.stripe.exception.InvalidRequestException e) { // bad params / 4xx
    log.error("invalid request param={}", e.getParam());
} catch (com.stripe.exception.AuthenticationException e) { // bad/rotated key
    log.error("auth failure — check STRIPE_SECRET_KEY");
} catch (com.stripe.exception.ApiConnectionException e) {  // network
    log.error("network error to Stripe", e);
} catch (com.stripe.exception.ApiException e) {            // 5xx from Stripe
    log.error("stripe api error", e);
} catch (com.stripe.exception.StripeException e) {         // catch-all fallback
    log.error("unexpected stripe error", e);
}
```
Source: [StripeException Javadoc — subclasses](https://stripe.dev/stripe-java/com/stripe/exception/StripeException.html) (2026-07-23);
[Handling errors — Java](https://docs.stripe.com/api/errors/handling?lang=java) (2026-07-23).

**A6 — Pin the API version deliberately; know 29.x ships `2025-03-31.basil`.**
The SDK sends the pinned API version by default. If your Stripe account default differs, set it explicitly so
webhook payloads and responses match the objects the 29.x SDK deserializes.
```java
// stripe-java 29.x — override per-request if needed
RequestOptions opts = RequestOptions.builder()
    .setStripeVersionOverride("2025-03-31.basil")
    .build();
```
Source: [stripe-java CHANGELOG — 29.0.0 pins 2025-03-31.basil](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) (2026-07-23);
[Basil API changelog](https://docs.stripe.com/changelog/basil) (2026-07-23).

**A7 — Load the secret key from the environment / secret manager, never a literal.**
```java
StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY")); // ✅
```
Source: [Stripe API keys — security](https://docs.stripe.com/keys) (2026-07-23).

**A8 — Request expandable fields explicitly instead of extra round-trips.**
```java
// stripe-java 29.x — expand latest_charge on the created PaymentIntent
PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(2000L).setCurrency("usd")
    .addExpand("latest_charge")
    .build();
```
Source: [Stripe API — expanding responses](https://docs.stripe.com/api/expanding_objects) (2026-07-23).

**A9 — Compute/authorize amounts server-side; never accept a client-supplied amount.**
The `amount` (in the smallest currency unit, e.g. cents) MUST be derived from server-side cart/pricing state.
Source: [Stripe security best practices](https://docs.stripe.com/security/guide) (2026-07-23).

---

### ⚠️ Conditional Patterns (tradeoff matrices)

**C1 — `StripeClient` instance vs legacy static resource calls.**

| Option | When | Tradeoff (29.x) |
|---|---|---|
| `StripeClient` + `client.v1().xxx()` | **All new 29.x code** | Recommended; testable (inject client); explicit config. |
| Static `Customer.create(...)` | Only pre-existing 28.x code mid-migration | Still compiles in 29.x but **"marked deprecated soon"** per README; global `Stripe.apiKey` = harder to test/multi-tenant. |

Source: [stripe-java README](https://github.com/stripe/stripe-java) (2026-07-23).

**C2 — PaymentIntent automatic vs manual confirmation.**

| Mode | When | Tradeoff |
|---|---|---|
| `setConfirm(true)` at create | Server-driven flows / MOTO | One round-trip; must handle `requires_action` (SCA) in response. |
| Create then confirm client-side | Stripe.js / mobile SDK front end | Keeps card data off your server (lowers PCI scope); more steps. |

Source: [Create a PaymentIntent — Java](https://docs.stripe.com/api/payment_intents/create?lang=java) (2026-07-23).

**C3 — Automatic vs manual `capture_method`.**

| `setCaptureMethod` | When | Tradeoff |
|---|---|---|
| `AUTOMATIC` (default) | Immediate charge | Simplest; funds captured on confirm. |
| `MANUAL` | Auth-now, capture-later (e.g. ship-then-bill) | Must capture within auth window or the hold expires. |

Source: [PaymentIntentCreateParams — captureMethod (29.4.0 Javadoc)](https://stripe.dev/stripe-java/com/stripe/param/PaymentIntentCreateParams.html) (2026-07-23).

**C4 — Webhook idempotency storage.**

| Store | When | Tradeoff |
|---|---|---|
| In-memory `Set<eventId>` | Single-instance/dev only | Lost on restart; NOT safe across replicas. |
| Durable store (DB unique key on `event.id`) | **Production** | Survives restart/scale-out; the correct choice. |

Source: [Stripe webhooks — handle duplicate events](https://docs.stripe.com/webhooks?lang=java) (2026-07-23).

**C5 — Auto-pagination vs manual pagination.**

| Approach | When | Tradeoff |
|---|---|---|
| `autoPagingIterable()` | Iterate an entire collection | Transparent page fetches; watch rate limits on large sets. |
| Manual `starting_after` cursor | Bounded/keyset UI paging | More control; more code. |
Note: 29.x removed the ability to expand `total_count` on lists — do not rely on total counts.
Source: [stripe-java v29 Migration Guide](https://github.com/stripe/stripe-java/wiki/Migration-guide-for-v29) (2026-07-23).

**C6 — Sync vs async invocation.**
The 29.x `StripeClient` calls are **blocking**. For high throughput, wrap calls in your own executor/reactive
boundary and keep webhook handlers fast by offloading heavy work to a queue (return 2xx quickly).
Source: [Stripe webhooks — best practices](https://docs.stripe.com/webhooks?lang=java) (2026-07-23). *(Async wrapper design is app-level — marked application-specific, not an SDK feature.)*

---

### 🚫 Forbidden Patterns (each with ✅ corrected alternative)

**F1 — Hardcoded secret key.**
```java
// 🚫 NEVER (29.x)
StripeClient client = new StripeClient("sk_live_51ABC...");
// ✅ CORRECT
StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
```

**F2 — Skipping webhook signature verification.**
```java
// 🚫 NEVER — trusting raw body = attacker-controlled input
Event event = ApiResource.GSON.fromJson(payload, Event.class);
// ✅ CORRECT (29.x)
Event event = client.constructEvent(payload, sigHeader, endpointSecret);
```

**F3 — No idempotency key on retried mutations (double-charge risk).**
```java
// 🚫 NEVER — a network retry can charge twice
client.v1().paymentIntents().create(params);
// ✅ CORRECT
client.v1().paymentIntents().create(params,
    RequestOptions.builder().setIdempotencyKey(orderId + ":create-pi").build());
```

**F4 — Catching generic `Exception` instead of Stripe subtypes.**
```java
// 🚫 NEVER — hides card declines vs auth vs network vs 5xx
try { /* ... */ } catch (Exception e) { log.error("stripe failed", e); }
// ✅ CORRECT — see A5 (CardException → RateLimit → InvalidRequest → Auth → ApiConnection → ApiException → StripeException)
```

**F5 — Trusting client-supplied amounts/currency.**
```java
// 🚫 NEVER
.setAmount(Long.valueOf(request.getParameter("amount")))
// ✅ CORRECT — server computes from authoritative pricing
.setAmount(pricingService.totalMinorUnits(cart)).setCurrency("usd")
```

**F6 — Mixing SDK major versions / assuming 28.x behavior.**
```xml
<!-- 🚫 NEVER — do not follow 28.x tutorials against a 29.x jar; upcoming-invoice & usage-record APIs are GONE in 29.x -->
<!-- ✅ CORRECT — pin exactly one 29.x version and follow 29.x docs only -->
<dependency><groupId>com.stripe</groupId><artifactId>stripe-java</artifactId><version>29.5.0</version></dependency>
```
Source: [v29 Migration Guide](https://github.com/stripe/stripe-java/wiki/Migration-guide-for-v29) (2026-07-23).

**F7 — Building new code on the legacy static resource pattern.**
```java
// 🚫 AVOID in new 29.x code — deprecation-bound global state
Stripe.apiKey = System.getenv("STRIPE_SECRET_KEY");
Customer c = Customer.create(paramsMap);
// ✅ CORRECT — service-based client + typed builders (A1/A2)
StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
Customer c = client.v1().customers().create(CustomerCreateParams.builder().setEmail("x@y.z").build());
```
Source: [stripe-java README — "legacy pattern ... marked as deprecated soon"](https://github.com/stripe/stripe-java) (2026-07-23).

---

## 3. Migration Guide — 28.x → 29.x

**Pinned API version moves to `2025-03-31.basil`** (29.0.0). Confirmed breaking changes from official sources:

1. **Legacy usage-based billing removed** — `SubscriptionItemUsageRecord` and
   `SubscriptionItemUsageRecordSummary` resources are gone. Migrate to the current metered/usage model.
2. **Upcoming Invoice API removed** — `invoices.upcoming` / `invoices.upcomingLines` are gone; use the
   **Create Preview Invoice** API instead.
3. **`total_count` no longer expandable on lists** — remove any `.addExpand("total_count")`.
4. **Subscription field reorg** — `coupon`, `promotionCode`, `billingThresholds` were removed/moved on
   subscription-related params; re-check subscription creation/update code.
5. **Checkout subscription timing** — Checkout Sessions for subscriptions defer subscription creation until
   after payment completes (latency + billing-details fix).

Sources: [v29 Migration Guide](https://github.com/stripe/stripe-java/wiki/Migration-guide-for-v29) (2026-07-23);
[CHANGELOG 29.0.0](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) (2026-07-23).

**Step-by-step upgrade path**
1. Bump the dependency to a single 29.x version (see F6); run `mvn dependency:tree` to confirm no dual majors.
2. Compile — fix removed symbols (usage records, upcoming invoice, `total_count` expands).
3. Replace static resource calls with `StripeClient` + typed builders (A1/A2).
4. Replay webhooks against `2025-03-31.basil` payload shapes; confirm event object deserialization.
5. Re-run the Section 5 verification (compile + `stripe listen`/`stripe trigger`).

---

## 4. Implementation Blueprint (stripe-java **29.x**, verified signatures)

**Maven coordinates**
```xml
<!-- stripe-java 29.x -->
<dependency>
  <groupId>com.stripe</groupId>
  <artifactId>stripe-java</artifactId>
  <version>29.5.0</version>
</dependency>
```
**Gradle**
```gradle
implementation "com.stripe:stripe-java:29.5.0"
```

### (a) Create a PaymentIntent
```java
// stripe-java 29.x — API version 2025-03-31.basil
import com.stripe.StripeClient;
import com.stripe.model.PaymentIntent;
import com.stripe.net.RequestOptions;
import com.stripe.param.PaymentIntentCreateParams;

StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));

PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(2000L)                 // amount in cents, computed server-side (A9)
    .setCurrency("usd")
    .setAutomaticPaymentMethods(
        PaymentIntentCreateParams.AutomaticPaymentMethods.builder()
            .setEnabled(true).build())
    .addExpand("latest_charge")       // A8
    .build();

RequestOptions opts = RequestOptions.builder()
    .setIdempotencyKey(orderId + ":create-pi")  // A3 — retry-safe
    .build();

PaymentIntent pi = client.v1().paymentIntents().create(params, opts);
// return pi.getClientSecret() to the front end for confirmation
```

### (b) Create a Customer + Subscription
```java
// stripe-java 29.x
import com.stripe.model.Customer;
import com.stripe.model.Subscription;
import com.stripe.param.CustomerCreateParams;
import com.stripe.param.SubscriptionCreateParams;

Customer customer = client.v1().customers().create(
    CustomerCreateParams.builder()
        .setEmail("jane@example.com")
        .build());

SubscriptionCreateParams subParams = SubscriptionCreateParams.builder()
    .setCustomer(customer.getId())
    .addItem(SubscriptionCreateParams.Item.builder()
        .setPrice("price_123")        // an existing recurring Price on a Product
        .build())
    .build();

Subscription subscription = client.v1().subscriptions().create(subParams,
    RequestOptions.builder().setIdempotencyKey(customer.getId() + ":sub").build());
```
Source: [SubscriptionCreateParams builder](https://stripe.dev/stripe-java/com/stripe/param/SubscriptionCreateParams.html) (2026-07-23).

### (c) Webhook endpoint (signature verification + idempotency)
```java
// stripe-java 29.x — verify signature, dedupe by event.id, handle payment_intent.succeeded & invoice.paid
import com.stripe.StripeClient;
import com.stripe.exception.SignatureVerificationException;
import com.stripe.model.*;
import com.google.gson.JsonSyntaxException;

// Servlet-style handler (framework-agnostic pseudocode around the SDK calls)
public int handleWebhook(String payload, String sigHeader) {
    StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
    String endpointSecret = System.getenv("STRIPE_WEBHOOK_SECRET"); // whsec_...

    Event event;
    try {
        event = client.constructEvent(payload, sigHeader, endpointSecret); // A4
    } catch (JsonSyntaxException e) {
        return 400; // malformed payload
    } catch (SignatureVerificationException e) {
        return 400; // NOT from Stripe — reject
    }

    // C4 — durable idempotency (unique constraint on event.getId())
    if (!eventStore.markProcessedIfNew(event.getId())) {
        return 200; // already handled — ack duplicate
    }

    EventDataObjectDeserializer d = event.getDataObjectDeserializer();
    if (d.getObject().isEmpty()) {
        return 400; // API-version mismatch — object could not deserialize
    }
    StripeObject obj = d.getObject().get();

    switch (event.getType()) {
        case "payment_intent.succeeded":
            PaymentIntent pi = (PaymentIntent) obj;
            fulfillOrder(pi);           // do heavy work async; return fast
            break;
        case "invoice.paid":
            Invoice invoice = (Invoice) obj;
            grantEntitlement(invoice);
            break;
        default:
            // unhandled type — still ack
    }
    return 200;
}
```
Source: [Stripe Webhooks — Java](https://docs.stripe.com/webhooks?lang=java) (2026-07-23).

---

## 5. Quality Control — Executable Verification

**Dependency (Maven)** — as in Section 4.

**Verify a single 29.x major on the classpath**
```bash
mvn dependency:tree -Dincludes=com.stripe:stripe-java
```
Expected output (only one 29.x line, no second major):
```
[INFO] com.example:app:jar:1.0.0
[INFO] \- com.stripe:stripe-java:jar:29.5.0:compile
```

**Compile check**
```bash
mvn -q clean compile
```
Expected: `BUILD SUCCESS` and no `cannot find symbol` for removed 28.x APIs (usage records / upcoming invoice).

**Local webhook testing with the Stripe CLI**
```bash
# Terminal 1 — forward events to your local endpoint; prints the whsec_ secret to use
stripe listen --forward-to localhost:8080/webhook
```
Expected:
```
> Ready! Your webhook signing secret is whsec_xxxx (^C to quit)
```
```bash
# Terminal 2 — fire test events
stripe trigger payment_intent.succeeded
stripe trigger invoice.paid
```
Expected (Terminal 1): a `200` for each forwarded event, e.g.
```
2026-07-23 12:00:00  --> payment_intent.succeeded [evt_...]
2026-07-23 12:00:00  <--  [200] POST http://localhost:8080/webhook [evt_...]
```
Source: [Stripe CLI — listen/trigger](https://docs.stripe.com/stripe-cli) (2026-07-23).

---

## 6. Production Readiness

- **Connection & timeouts** — configure via `StripeClient`/`RequestOptions`; set a bounded connect + read
  timeout so a slow Stripe response can't exhaust your request threads.
- **Retries / max network retries** — enable automatic network retries (idempotent by default with an
  idempotency key from A3); bound the retry count. Source: [stripe-java README — configuration](https://github.com/stripe/stripe-java) (2026-07-23).
- **Rate limits** — handle `RateLimitException` (429) with exponential backoff + jitter (A5). Source:
  [Stripe rate limits](https://docs.stripe.com/rate-limits) (2026-07-23).
- **Monitoring** — log `event.getId()`, `event.getType()`, and `RequestOptions` idempotency keys; alert on
  `AuthenticationException` (rotated/invalid key) and sustained 5xx `ApiException`.
- **Security hardening** — restricted API keys (least privilege) for background services; keep card data off
  your servers (client-side confirmation, C2) to minimize **PCI scope**; store `whsec_` secret in a secret
  manager; enforce HTTPS on the webhook route. Sources: [Restricted keys](https://docs.stripe.com/keys#limit-access) ·
  [PCI guide](https://docs.stripe.com/security/guide) (2026-07-23).

---

## 7. Source Bibliography (all dated 2026-07-23 unless noted)

**Official — GitHub (stripe/stripe-java)**
- README (recommended usage, install, JDK support, legacy-deprecation note): https://github.com/stripe/stripe-java
- CHANGELOG (29.0.0 → 29.5.0; pins `2025-03-31.basil`): https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md
- v29 Migration Guide (wiki): https://github.com/stripe/stripe-java/wiki/Migration-guide-for-v29
- Javadoc — PaymentIntentCreateParams (29.4.0): https://stripe.dev/stripe-java/com/stripe/param/PaymentIntentCreateParams.html
- Javadoc — StripeException hierarchy: https://stripe.dev/stripe-java/com/stripe/exception/StripeException.html
- Javadoc — SubscriptionCreateParams: https://stripe.dev/stripe-java/com/stripe/param/SubscriptionCreateParams.html

**Official — docs.stripe.com**
- Webhooks (Java signature verification): https://docs.stripe.com/webhooks?lang=java
- Create a PaymentIntent (Java): https://docs.stripe.com/api/payment_intents/create?lang=java
- Handling errors (Java): https://docs.stripe.com/api/errors/handling?lang=java
- Idempotent requests: https://docs.stripe.com/api/idempotent_requests
- Expanding responses: https://docs.stripe.com/api/expanding_objects
- API keys / restricted keys: https://docs.stripe.com/keys
- Basil API changelog (2025-03-31.basil): https://docs.stripe.com/changelog/basil
- Stripe CLI: https://docs.stripe.com/stripe-cli
- Rate limits: https://docs.stripe.com/rate-limits
- Security guide (PCI): https://docs.stripe.com/security/guide

**Maven Central** (release listing referenced; page returned 403 on direct fetch — versions/dates cross-checked via CHANGELOG)
- https://mvnrepository.com/artifact/com.stripe/stripe-java

---

## 8. Agent Operation Notes (confidence for downstream skill authoring)

| Claim | Confidence | Basis |
|---|---|---|
| Latest 29.x patch = **29.5.0 (2025-08-27)** | **High** | CHANGELOG enumeration |
| 29.x pins API version **`2025-03-31.basil`** | **High** | CHANGELOG 29.0.0 + Migration Guide |
| `StripeClient` service pattern is the recommended 29.x style; static = "deprecated soon" | **High** | Official README |
| Webhook `client.constructEvent(payload, sig, secret)` + `SignatureVerificationException` | **High** | Official webhooks doc (Java) |
| Idempotency via `RequestOptions.builder().setIdempotencyKey(...)` | **High** | Official README |
| StripeException subclass set & catch order | **High** | Javadoc + errors doc |
| v29 breaking changes (usage records, upcoming invoice→preview, total_count, sub field reorg) | **High** | Migration Guide + CHANGELOG |
| PaymentIntentCreateParams setters (setAmount/setCurrency/setConfirm/setCaptureMethod/setAutomaticPaymentMethods) | **Medium-High** | 29.4.0 Javadoc confirmed page exists; live Javadoc redirects to 33.x. Setters are stable across 29.x. |
| **JDK baseline for 29.x** | **Medium — partially unverified** | README fetched showed JDK **8/11/17/21/25** but that README is the **33.x** version; Java **25** support is almost certainly NOT in 29.x (released 2025-04 → 2025-08). Treat 29.x baseline as **Java 8/11/17/21**; verify against the 29.5.0 tag README before asserting. |
| Exact Maven Central publish dates | **Medium** | mvnrepository returned 403; dates taken from CHANGELOG (authoritative for release, ~publish date). |

**Unverified / flag-before-use items:**
1. Precise **minimum JDK for the 29.x tag** — README evidence is from the newer 33.x line (includes Java 25). Confirm from the `v29.5.0` tag's README/`build.gradle` before hardcoding.
2. Whether any **29.x patch > 29.5.0** exists — 29.5.0 is the highest found; the 29.x line may have ended when 30.x opened. Not treated as an error, but re-confirm if exhaustiveness matters.
3. Exact **PaymentIntentCreateParams** enum/method names were confirmed against the 29.4.0 Javadoc URL's existence and general getter set; the live Javadoc now serves 33.x. Signatures used here are the stable, widely-documented 29.x forms.

**Version reminder (final warning):** This KB is **stripe-java 29.x** only. Do not blend with 28.x tutorials
(removed APIs) and note that as of 2026-07-23 the current stable major is **33.x** — 29.x is a **superseded**
line. Recommend running `/skill-best-practices-validator` on any skill authored from this document.
