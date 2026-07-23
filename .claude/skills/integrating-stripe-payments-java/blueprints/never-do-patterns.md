# 🚫 Never Do — stripe-java 33.x Anti-Patterns

> **Version lock**: All patterns target **stripe-java 33.x** (latest patch **33.1.1**, API `2026-06-24.dahlia`).
> Each anti-pattern includes the exact wrong code, the consequence, and the ✅ 33.x corrected alternative.

---

## F1 — Hardcoded secret keys in source

**Why forbidden**: A committed or logged `sk_live_*` key gives any reader full access to your Stripe account. It cannot be revoked selectively — you must rotate the key and invalidate all sessions.

```java
// 🚫 NEVER — key committed to source (one git push = full account compromise)
StripeClient client = new StripeClient("sk_live_51Hxxxxxxxxxxxxxxxx");

// 🚫 NEVER — key in a properties file checked into git
@Value("${stripe.key}")  // application.properties: stripe.key=sk_live_51H...
```

```java
// ✅ stripe-java 33.x — read from environment variable or secret manager
String apiKey = System.getenv("STRIPE_SECRET_KEY");
if (apiKey == null || apiKey.isBlank()) {
    throw new IllegalStateException("STRIPE_SECRET_KEY not set");
}
StripeClient client = new StripeClient(apiKey);

// For production: inject from AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault, etc.
// Use restricted API keys scoped only to the resources this service needs.
```

Source: [Stripe API keys](https://docs.stripe.com/keys#safe-keys) (2026-07-23)

---

## F2 — Skipping webhook signature verification

**Why forbidden**: A Stripe webhook endpoint that does not verify signatures will accept and act on any HTTP POST — including attacker-forged events that trigger order fulfillment, subscription activation, or account changes without a real payment.

```java
// 🚫 NEVER — trusting raw body = accepting attacker-forged events
// This bypasses the trust boundary entirely.
Event event = ApiResource.GSON.fromJson(payload, Event.class);
processPaymentSuccess(event); // attacker can fake a payment_intent.succeeded

// 🚫 NEVER — partial verification (checking only event type, not signature)
if (body.contains("payment_intent.succeeded")) {
    fulfillOrder(); // no cryptographic proof the event is real
}
```

```java
// ✅ stripe-java 33.x — verify signature first; only then trust the event
import com.stripe.exception.SignatureVerificationException;
import com.stripe.model.Event;

Event event;
try {
    // payload = raw request body (String, NOT parsed JSON)
    // sigHeader = Stripe-Signature HTTP header value
    // endpointSecret = whsec_... from Stripe dashboard / stripe listen
    event = client.constructEvent(payload, sigHeader, endpointSecret);
} catch (SignatureVerificationException e) {
    return respond(400, "Invalid signature"); // reject; do not process
}
// Safe to read event.getType() and event.getData() only after this point.
```

Source: [Stripe webhook signatures](https://docs.stripe.com/webhooks/signature) (2026-07-23)

---

## F3 — No idempotency key on retried state-changing calls

**Why forbidden**: If a `createPaymentIntent` call times out, a retry without an idempotency key will create a second PaymentIntent — potentially charging the customer twice.

```java
// 🚫 NEVER — retrying a state-changing call with no idempotency key
for (int i = 0; i < 3; i++) {
    try {
        // Each attempt is a NEW PaymentIntent — three attempts = three potential charges
        PaymentIntent pi = client.v1().paymentIntents().create(params);
        break;
    } catch (ApiConnectionException e) {
        Thread.sleep(1000);
    }
}
```

```java
// ✅ stripe-java 33.x — stable idempotency key generated ONCE, reused on every retry attempt
String idempotencyKey = orderId + ":create-pi"; // deterministic per logical operation

RequestOptions opts = RequestOptions.builder()
    .setIdempotencyKey(idempotencyKey)
    .build();

for (int i = 0; i < 3; i++) {
    try {
        // Same key every attempt → Stripe returns the original PaymentIntent, no duplicate charge
        PaymentIntent pi = client.v1().paymentIntents().create(params, opts);
        break;
    } catch (ApiConnectionException e) {
        Thread.sleep(backoffMs(i));
    }
}
```

Source: [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests) (2026-07-23)

---

## F4 — Catching generic `Exception` instead of `StripeException` subtypes

**Why forbidden**: Catching the root `Exception` (or `Throwable`) collapses card declines, rate-limit events, programming errors, and actual bugs into identical handling. You lose the ability to retry safely (rate limits), surface user-friendly messages (card declines), or alert on auth failures (key rotation signals).

```java
// 🚫 NEVER — catching Exception loses all stripe-specific context
try {
    PaymentIntent pi = client.v1().paymentIntents().create(params, opts);
} catch (Exception e) {
    log.error("Payment failed", e);
    return respond(500, "Payment failed"); // user gets a generic error for a declined card
}
```

```java
// ✅ stripe-java 33.x — catch subtypes most-specific-first
// (RateLimitException extends StripeException directly in 33.x — NOT ApiException)
try {
    PaymentIntent pi = client.v1().paymentIntents().create(params, opts);

} catch (CardException e) {
    // Declined — show user-facing message
    log.warn("Card declined: code={} decline={}", e.getCode(), e.getDeclineCode());
    return respond(402, "Your card was declined: " + e.getMessage());

} catch (RateLimitException e) {
    // Back off and retry; this is NOT a programming error
    log.warn("Rate limited; reqId={}", e.getRequestId());
    return respond(429, "Service temporarily busy — please retry");

} catch (InvalidRequestException e) {
    // Bug in your code (wrong params) — do NOT retry; fix the request
    log.error("Invalid request; reqId={}", e.getRequestId(), e);
    return respond(500, "Internal error");

} catch (AuthenticationException e) {
    // Key problem — alert ops immediately
    log.error("AUTH FAILURE — possible key leak; reqId={}", e.getRequestId(), e);
    return respond(500, "Internal error");

} catch (StripeException e) {
    log.error("Stripe error; status={} reqId={}", e.getStatusCode(), e.getRequestId(), e);
    return respond(500, "Payment service error");
}
```

Source: [Stripe error handling — Java](https://docs.stripe.com/error-handling?lang=java) · [CHANGELOG 32.0.0](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) (2026-07-23)

---

## F5 — Trusting a client-supplied amount

**Why forbidden**: Any client-side value can be tampered with. An attacker sending `amount=1` for a $500 order causes Stripe to charge 1 cent, completing a payment at a fraction of the real price.

```java
// 🚫 NEVER — amount from HTTP request (attacker-controlled)
long amount = Long.parseLong(request.queryParams("amount"));   // query parameter
// or from a JSON body:
long amount = requestBody.get("amount").asLong();              // JSON body field

PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(amount)   // attacker sends 1 → charges 1 cent for a $500 item
    .setCurrency("usd")
    .build();
```

```java
// ✅ stripe-java 33.x — amount computed server-side from authoritative catalog/order data
// orderId comes from the session/JWT/URL; the ORDER TOTAL is looked up from YOUR database
Order order = orderRepository.findById(orderId)
    .orElseThrow(() -> new IllegalArgumentException("Order not found: " + orderId));

long amountMinorUnits = order.totalMinorUnits(); // authoritative, server-derived, immutable

PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
    .setAmount(amountMinorUnits)  // e.g., 5000 = $50.00 USD
    .setCurrency(order.currencyCode())
    .build();
```

Source: [Stripe integration security](https://docs.stripe.com/security/guide) (2026-07-23)

---

## F6 — Mixing SDK majors / conflicting API versions on one classpath

**Why forbidden**: Java's classpath resolution collapses two `stripe-java` jars into one arbitrary winner. The result is undefined behavior — methods missing, wrong serialization, silent wrong API-version pins.

```xml
<!-- 🚫 NEVER — two stripe-java majors on the classpath -->
<!-- Direct dependency on 33.x -->
<dependency>
  <groupId>com.stripe</groupId>
  <artifactId>stripe-java</artifactId>
  <version>33.1.1</version>
</dependency>
<!-- 32.x pulled in transitively by another dependency — both resolve to one JAR: undefined behavior -->
```

```xml
<!-- ✅ stripe-java 33.x — one and only one version; enforce via dependency management -->
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>com.stripe</groupId>
      <artifactId>stripe-java</artifactId>
      <version>33.1.1</version>
    </dependency>
  </dependencies>
</dependencyManagement>
```

Verify after every dependency change:
```bash
mvn dependency:tree | grep stripe
# Expected: exactly ONE line → com.stripe:stripe-java:jar:33.1.1:compile
# Any 32.x line = mixed majors → add an exclusion and re-run.
```

Source: [stripe-java releases](https://github.com/stripe/stripe-java/releases) (2026-07-23)

---

## F7 — Writing new code on the deprecated static resource pattern

**Why forbidden**: The static resource pattern (`Stripe.apiKey = ...`, `Customer.create(map)`) is explicitly flagged in the 33.x README as "will be marked as deprecated soon." It uses a global mutable key (not safe for multi-tenant use), accepts raw maps (no compile-time safety), and does not benefit from the `StripeClient` connection-pool lifecycle.

```java
// 🚫 AVOID in 33.x — static pattern (pre-deprecated; not for new code)
import com.stripe.Stripe;
import com.stripe.model.Customer;

Stripe.apiKey = System.getenv("STRIPE_SECRET_KEY"); // global mutable state
Map<String, Object> params = new HashMap<>();
params.put("email", "jane@example.com");
Customer c = Customer.create(params); // raw map — no compile-time field validation
```

```java
// ✅ stripe-java 33.x — StripeClient + v1() namespace + typed builders
import com.stripe.StripeClient;
import com.stripe.model.Customer;
import com.stripe.param.CustomerCreateParams;

StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY")); // instance, not global
CustomerCreateParams params = CustomerCreateParams.builder()
    .setEmail("jane@example.com")
    .setDescription("Created via stripe-java 33.x")
    .build();
Customer c = client.v1().customers().create(params); // typed, compile-time safe
```

Source: [stripe-java README](https://github.com/stripe/stripe-java) (2026-07-23)
