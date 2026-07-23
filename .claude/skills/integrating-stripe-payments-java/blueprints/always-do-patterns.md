# ✅ Always Do — stripe-java 33.x Mandatory Patterns

> **Version lock**: All patterns target **stripe-java 33.x** (latest patch **33.1.1**, API `2026-06-24.dahlia`).
> Patterns from 32.x and earlier are disinformation — do not apply them.

---

## A1 — Instantiate `StripeClient` once; reuse it

The `StripeClient` owns the underlying HTTP client and connection pool. Instantiate once (e.g., as a Spring bean, singleton, or application-scoped field) and reuse across the application lifetime.

```java
// stripe-java 33.x — service-based client (preferred; NOT the legacy static pattern)
import com.stripe.StripeClient;

// ✅ Instantiate once per application lifecycle
StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));

// Reuse client.v1().<service>().<method>() throughout the application.
// Creating a new StripeClient per request wastes connections and adds overhead.
```

Source: [stripe-java README — recommended usage](https://github.com/stripe/stripe-java) (checked 2026-07-23)

---

## A2 — Use typed parameter builders through the `v1()` namespace

Never use raw `Map<String, Object>` params or the flat top-level accessors (deprecated since 31.0.0). Typed builders provide compile-time safety against field-name typos.

```java
// stripe-java 33.x — v1() namespace + typed builders
import com.stripe.StripeClient;
import com.stripe.model.Customer;
import com.stripe.param.CustomerCreateParams;

CustomerCreateParams params = CustomerCreateParams.builder()
    .setEmail("jane@example.com")
    .setDescription("KB demo customer (stripe-java 33.x)")
    .build();

Customer customer = client.v1().customers().create(params);
// `v1()` is the non-deprecated namespace; flat accessors were deprecated in 31.0.0.
```

Source: [stripe-java README](https://github.com/stripe/stripe-java) (2026-07-23)

---

## A3 — Idempotency key on every state-changing call

Use a key that is stable per **logical operation** (not per attempt). On retry, the same key causes Stripe to return the original response rather than executing the operation again — preventing duplicate charges.

```java
// stripe-java 33.x — stable idempotency key per logical operation
import com.stripe.net.RequestOptions;
import com.stripe.param.PaymentIntentCreateParams;
import com.stripe.model.PaymentIntent;

PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(2000L)          // A9 — integer minor units, server-derived
    .setCurrency("usd")
    .build();

RequestOptions opts = RequestOptions.builder()
    .setIdempotencyKey(orderId + ":create-pi")  // deterministic per order, reused on retry
    .build();

PaymentIntent pi = client.v1().paymentIntents().create(params, opts);
// Retrying with the same orderId+":create-pi" key returns the original PaymentIntent — no double charge.
```

Source: [stripe-java README — RequestOptions idempotency](https://github.com/stripe/stripe-java) · [Stripe idempotency docs](https://docs.stripe.com/api/idempotent_requests) (2026-07-23)

---

## A4 — Verify webhook signatures before trusting any payload

An unverified webhook is attacker-controlled input. Always call `client.constructEvent()` before reading any field from the payload. The method throws `SignatureVerificationException` if the signature is invalid or the timestamp is outside the tolerance window (default 300 seconds).

```java
// stripe-java 33.x — signature verification (trust boundary)
import com.stripe.StripeClient;
import com.stripe.exception.SignatureVerificationException;
import com.stripe.model.Event;

// Inject client and endpointSecret from env at startup (A7)
String endpointSecret = System.getenv("STRIPE_WEBHOOK_SECRET"); // whsec_...

Event event;
try {
    // payload = raw request body as String (must NOT be parsed/re-serialized first)
    // sigHeader = value of the Stripe-Signature HTTP header
    event = client.constructEvent(payload, sigHeader, endpointSecret);
} catch (SignatureVerificationException e) {
    // Reject forged or expired (>300 s) payloads
    return respond(400, "Invalid signature");
}
// Only here can you trust event.getType() and event.getData()
```

Confirmed `Webhook.java` overloads (stripe-java 33.x, checked 2026-07-23):
- `constructEvent(String payload, String sigHeader, String secret)` → `Event`
- `constructEvent(..., long tolerance)` → `Event`
- `constructEvent(..., long tolerance, Clock clock)` → `Event`
All declare `throws SignatureVerificationException`.

Source: [Stripe Webhooks docs — Java](https://docs.stripe.com/webhooks?lang=java) · [stripe-java `Webhook.java`](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/net/Webhook.java) (2026-07-23)

---

## A5 — Catch the `StripeException` hierarchy by subtype (most specific first)

**Important 33.x hierarchy note**: `RateLimitException` extends `StripeException` directly (not `ApiException`) since the 32.0.0 breaking change, carried into 33.x. Place the most specific subtypes before the base `StripeException` catch.

```java
// stripe-java 33.x — exception handling by subtype
import com.stripe.exception.*;

try {
    PaymentIntent pi = client.v1().paymentIntents().create(params, opts);

} catch (CardException e) {
    // Card declined / payment failure — surface to user
    // e.getCode(): machine-readable code (e.g., "card_declined")
    // e.getDeclineCode(): decline reason (e.g., "insufficient_funds")
    log.warn("Payment error code={} decline={} msg={}",
        e.getCode(), e.getDeclineCode(), e.getMessage());

} catch (RateLimitException e) {
    // Too many requests — back off with exponential jitter, then retry
    // NOTE: extends StripeException directly in 33.x (NOT ApiException)
    log.warn("Rate limited by Stripe; reqId={}", e.getRequestId());

} catch (InvalidRequestException e) {
    // Programming / config error — bad params, wrong resource ID
    // Do NOT retry blindly; fix the request
    log.error("Invalid Stripe request; reqId={} msg={}", e.getRequestId(), e.getMessage());

} catch (ApiConnectionException e) {
    // Network failure — safe to retry with idempotency key
    log.error("Network error reaching Stripe; reqId={}", e.getRequestId());

} catch (AuthenticationException e) {
    // Invalid API key — alert ops; possible key leak or rotation needed
    log.error("Stripe authentication failure; reqId={}", e.getRequestId());

} catch (StripeException e) {
    // Fallback: ApiException, IdempotencyException, PermissionException, etc.
    log.error("Stripe error; status={} code={} reqId={}",
        e.getStatusCode(), e.getCode(), e.getRequestId());
    // Always log getRequestId() for Stripe support correlation
}
```

Confirmed exception subtypes for 33.x: `CardException`, `InvalidRequestException`, `ApiConnectionException`, `ApiException`, `AuthenticationException`, `IdempotencyException`, `PermissionException`, `RateLimitException`, `SignatureVerificationException`.

Source: [Stripe error handling — Java](https://docs.stripe.com/error-handling?lang=java) · [stripe-java CHANGELOG — 32.0.0 RateLimitException reparent](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) (2026-07-23)

---

## A6 — Pin the Stripe API version explicitly

stripe-java 33.1.x pins `2026-06-24.dahlia` by default. For defense-in-depth, override per-request so an accidental SDK bump never silently changes wire behavior.

```java
// stripe-java 33.x — explicit API version override (defense-in-depth)
RequestOptions opts = RequestOptions.builder()
    // Pinned version string is VERIFIED; exact method name setStripeVersionOverride is UNVERIFIED
    // against 33.x Javadoc — confirm against javadoc.io/doc/com.stripe/stripe-java/33.1.1 before use.
    .setStripeVersionOverride("2026-06-24.dahlia")
    .build();
```

> **Unverified**: The method name `setStripeVersionOverride` (A6) was not confirmed against 33.x Javadoc.
> The pinned version string `2026-06-24.dahlia` IS verified. Check the 33.1.1 Javadoc before committing
> this call. See KB Section 8, item 1.

Source: [stripe-java CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) · [Stripe API versioning](https://docs.stripe.com/api/versioning) (2026-07-23)

---

## A7 — Read the secret key from the environment / secret manager only

```java
// stripe-java 33.x — key from env; never from source, config files committed to git, or logs
import com.stripe.StripeClient;

String apiKey = System.getenv("STRIPE_SECRET_KEY");
if (apiKey == null || apiKey.isBlank()) {
    throw new IllegalStateException(
        "STRIPE_SECRET_KEY not set — set it via environment variable or a secret manager");
}
StripeClient client = new StripeClient(apiKey);

// For production: use a secret manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault).
// Use sk_test_* for test mode, sk_live_* for production — never swap modes in code logic.
// Use restricted API keys scoped to only the resources a service needs.
```

Source: [Stripe API keys / security](https://docs.stripe.com/keys) · [Stripe restricted keys](https://docs.stripe.com/keys#limit-access) (2026-07-23)

---

## A8 — Use expandable fields to avoid N+1 round trips

Expandable fields let you retrieve nested objects in a single API call rather than separate fetches.

```java
// stripe-java 33.x — expand nested objects in a single request
import com.stripe.param.PaymentIntentRetrieveParams;
import com.stripe.model.PaymentIntent;

PaymentIntentRetrieveParams params = PaymentIntentRetrieveParams.builder()
    .addExpand("customer")
    .addExpand("latest_charge")
    .build();

PaymentIntent pi = client.v1().paymentIntents().retrieve(piId, params, null);
// pi.getCustomer() and pi.getLatestCharge() are now populated — no extra API calls.
```

**33.x-specific**: 33.0.0 (PR #2234) made `tax_rate.tax_details` expandable. If you read `tax_details`:
```java
// stripe-java 33.x — expand tax_details (new in 33.0.0)
TaxRateRetrieveParams taxParams = TaxRateRetrieveParams.builder()
    .addExpand("tax_details")
    .build();
TaxRate taxRate = client.v1().taxRates().retrieve(taxRateId, taxParams, null);
```

Source: [Stripe expanding responses](https://docs.stripe.com/expand) · [v33.0.0 release notes](https://github.com/stripe/stripe-java/releases/tag/v33.0.0) (2026-07-23)

---

## A9 — Compute amounts server-side in integer minor units

Stripe amounts are integers in the smallest currency unit (cents for USD, yen for JPY, etc.). Always derive the amount from your own authoritative catalog on the server — never from a client-supplied parameter.

```java
// stripe-java 33.x — 2000 = $20.00 USD (minor units), derived server-side
import com.stripe.param.PaymentIntentCreateParams;

// ✅ Authoritative amount from your own order/catalog model
long amountMinorUnits = order.totalMinorUnits(); // e.g., 2000 for $20.00 USD

PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(amountMinorUnits)
    .setCurrency("usd")
    .setAutomaticPaymentMethods(
        PaymentIntentCreateParams.AutomaticPaymentMethods.builder()
            .setEnabled(true)
            .build())
    .build();

// Zero-decimal currencies (JPY, KRW, etc.) — the integer IS the full unit:
// .setAmount(1500L).setCurrency("jpy") → ¥1500
```

Source: [Stripe amounts / currencies](https://docs.stripe.com/currencies#zero-decimal) (2026-07-23)
