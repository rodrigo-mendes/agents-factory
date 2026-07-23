# Integration Examples — stripe-java 33.x

> **Version lock**: All examples target **stripe-java 33.x** (latest patch **33.1.1**, API `2026-06-24.dahlia`).
> Comments reference the guardrail codes (A1–A9, C1–C6, F1–F7) defined in SKILL.md.

---

## Example 1 — Create a PaymentIntent (one-time charge)

Full lifecycle: server creates PaymentIntent with idempotency key and server-derived amount, client completes payment via Stripe.js / PaymentElement, server handles `payment_intent.succeeded` webhook.

```java
// stripe-java 33.x — PaymentIntent create (one-time charge)
import com.stripe.StripeClient;
import com.stripe.exception.CardException;
import com.stripe.exception.RateLimitException;
import com.stripe.exception.InvalidRequestException;
import com.stripe.exception.StripeException;
import com.stripe.model.PaymentIntent;
import com.stripe.net.RequestOptions;
import com.stripe.param.PaymentIntentCreateParams;

public class PaymentService {

    private final StripeClient client; // A1 — injected singleton

    public PaymentService() {
        String apiKey = System.getenv("STRIPE_SECRET_KEY"); // A7 — from env
        if (apiKey == null || apiKey.isBlank()) {
            throw new IllegalStateException("STRIPE_SECRET_KEY not set");
        }
        this.client = new StripeClient(apiKey); // A1 — instantiate once
    }

    /**
     * Creates a PaymentIntent for a given order.
     * The client secret returned must be passed to Stripe.js / PaymentElement to complete payment.
     * stripe-java 33.x — API 2026-06-24.dahlia
     */
    public String createPaymentIntent(String orderId, long amountMinorUnits, String currency)
            throws StripeException {

        // A9 — amount must be server-derived (passed in from authoritative catalog, not from client)
        // A2 — typed builder; v1() namespace
        PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
            .setAmount(amountMinorUnits)           // e.g., 5000 = $50.00 USD
            .setCurrency(currency)                 // e.g., "usd"
            .setAutomaticPaymentMethods(           // C3 — automatic confirmation for standard checkout
                PaymentIntentCreateParams.AutomaticPaymentMethods.builder()
                    .setEnabled(true)
                    .build())
            .build();

        // A3 — idempotency key: stable per logical operation, not per HTTP attempt
        RequestOptions opts = RequestOptions.builder()
            .setIdempotencyKey(orderId + ":create-pi")
            .build();

        try {
            PaymentIntent pi = client.v1().paymentIntents().create(params, opts); // A1/A2
            return pi.getClientSecret(); // return to client for Stripe.js

        } catch (CardException e) {
            // A5 — card declined; surface to user
            throw e;
        } catch (RateLimitException e) {
            // A5 — back off; caller should retry with the same idempotency key
            throw e;
        } catch (InvalidRequestException | StripeException e) {
            // A5 — programming error or Stripe service error
            throw e;
        }
    }
}
```

Source: [Stripe PaymentIntents create (Java)](https://docs.stripe.com/api/payment_intents/create?lang=java) · [Stripe PaymentIntents lifecycle](https://docs.stripe.com/payments/paymentintents/lifecycle) (2026-07-23)

---

## Example 2 — Create a Customer + Subscription (Billing)

Creates a `Customer`, then subscribes them to an existing `Price`. The `Price` must already exist in your Stripe dashboard or have been created via the Prices API — this example references a pre-created `priceId`.

```java
// stripe-java 33.x — Customer + Subscription (Billing)
import com.stripe.StripeClient;
import com.stripe.exception.StripeException;
import com.stripe.model.Customer;
import com.stripe.model.Subscription;
import com.stripe.net.RequestOptions;
import com.stripe.param.CustomerCreateParams;
import com.stripe.param.SubscriptionCreateParams;

public class BillingService {

    private final StripeClient client; // A1 — injected singleton

    /**
     * Creates a Stripe Customer and immediately subscribes them to the given Price.
     * Returns the Subscription with latest_invoice.payment_intent expanded (A8).
     * stripe-java 33.x — API 2026-06-24.dahlia
     */
    public Subscription subscribe(String tenantId, String email, String priceId)
            throws StripeException {

        // Step 1 — Create a Customer (A2 — typed builder, v1() namespace)
        CustomerCreateParams customerParams = CustomerCreateParams.builder()
            .setEmail(email)
            .setDescription("stripe-java 33.x subscriber — tenant:" + tenantId)
            .build();

        RequestOptions customerOpts = RequestOptions.builder()
            .setIdempotencyKey(tenantId + ":create-customer") // A3 — idempotent
            .build();

        Customer customer = client.v1().customers().create(customerParams, customerOpts);

        // Step 2 — Subscribe to the Price (Product+Price already exist in Stripe)
        SubscriptionCreateParams subParams = SubscriptionCreateParams.builder()
            .setCustomer(customer.getId())
            .addItem(SubscriptionCreateParams.Item.builder()
                .setPrice(priceId) // references a pre-created Price (e.g., price_H2345...)
                .build())
            .addExpand("latest_invoice.payment_intent") // A8 — avoid N+1; get PI in one call
            .build();

        RequestOptions subOpts = RequestOptions.builder()
            .setIdempotencyKey(tenantId + ":create-sub:" + priceId) // A3 — idempotent
            .build();

        return client.v1().subscriptions().create(subParams, subOpts);
        // subscription.getLatestInvoice() is now expanded (due to addExpand above)
    }
}
```

> **Unverified note (KB item 3)**: The exact accessor name for the expanded `latest_invoice` on a `Subscription` object (e.g., `getLatestInvoice()` returning an `Invoice` vs. a String ID) was not confirmed against the 33.1.1 Javadoc. The pattern of expanding `latest_invoice.payment_intent` is standard Stripe Billing; verify the accessor chain against `javadoc.io/doc/com.stripe/stripe-java/33.1.1` before using in production.

Source: [Stripe Subscriptions create (Java)](https://docs.stripe.com/api/subscriptions/create?lang=java) · [Stripe Prices API](https://docs.stripe.com/api/prices?lang=java) · [Stripe expand](https://docs.stripe.com/expand) (2026-07-23)

---

## Example 3 — Webhook endpoint with signature verification

Handles `payment_intent.succeeded` and `invoice.paid` events. Verifies the signature (A4), deduplicates on `event.getId()` (C4), dispatches by type, and always returns HTTP 200 for processed and unhandled events (so Stripe stops retrying).

```java
// stripe-java 33.x — Webhook endpoint (Spark-style handler; adapt to your framework)
import com.stripe.StripeClient;
import com.stripe.exception.SignatureVerificationException;
import com.stripe.model.Event;
import com.stripe.model.Invoice;
import com.stripe.model.PaymentIntent;
import com.stripe.model.StripeObject;

public class WebhookHandler {

    private final StripeClient client;         // A1 — injected singleton
    private final String endpointSecret;       // A7 — whsec_... from env

    public WebhookHandler() {
        this.client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
        this.endpointSecret = System.getenv("STRIPE_WEBHOOK_SECRET"); // whsec_...
    }

    /**
     * Main webhook dispatcher.
     * IMPORTANT: `payload` MUST be the raw request body as a String — do NOT parse to JSON first.
     * `sigHeader` is the value of the Stripe-Signature HTTP header.
     * stripe-java 33.x — API 2026-06-24.dahlia
     */
    public WebhookResponse handle(String payload, String sigHeader) {
        // A4 — verify signature; throws SignatureVerificationException on forgery/expiry (>300s)
        Event event;
        try {
            event = client.constructEvent(payload, sigHeader, endpointSecret);
        } catch (SignatureVerificationException e) {
            // F2 — reject unverified payload; never process without a valid signature
            return WebhookResponse.error(400, "Invalid Stripe signature");
        }

        // C4 — idempotency: check before executing any side effects
        if (isAlreadyProcessed(event.getId())) {
            return WebhookResponse.ok("duplicate ignored"); // 200 → Stripe stops retrying
        }

        // Deserialize the event data object
        StripeObject stripeObject = event.getDataObjectDeserializer()
            .getObject()
            .orElse(null);

        switch (event.getType()) {
            case "payment_intent.succeeded": {
                PaymentIntent pi = (PaymentIntent) stripeObject;
                if (pi != null) {
                    fulfillOrder(pi.getId());
                }
                break;
            }
            case "invoice.paid": {
                // Note (KB item 4, unverified): invoice.paid dispatch is standard Billing practice;
                // the official webhooks page demonstrates payment_intent.succeeded +
                // payment_method.attached but not invoice.paid. Verify against 33.x Javadoc.
                Invoice invoice = (Invoice) stripeObject;
                if (invoice != null) {
                    // Note (KB item 3, unverified): exact accessor name getSubscription()
                    // on Invoice was not confirmed against 33.1.1 Javadoc.
                    activateSubscriptionPeriod(invoice.getSubscription());
                }
                break;
            }
            default:
                // Log unhandled types but return 200 — Stripe retries on non-2xx indefinitely
                log.info("Unhandled stripe-java 33.x event type: {}", event.getType());
        }

        markProcessed(event.getId()); // C4 — persist after side effects (within same transaction)
        return WebhookResponse.ok("ok");
    }

    // ---------- infrastructure stubs (implement with your DB/cache) ----------
    private boolean isAlreadyProcessed(String eventId) { /* DB or Redis SETNX check */ return false; }
    private void markProcessed(String eventId) { /* DB insert with unique constraint on event_id */ }
    private void fulfillOrder(String paymentIntentId) { /* your order fulfillment logic */ }
    private void activateSubscriptionPeriod(String subscriptionId) { /* your billing logic */ }
}
```

> **Unverified notes carried from KB**:
> - **KB item 3**: `Invoice.getSubscription()` accessor name — standard Billing pattern, not confirmed against 33.1.1 Javadoc. Verify before deploying.
> - **KB item 4**: `invoice.paid` dispatch shown by extrapolation from standard Stripe Billing; the official fetched webhooks page demonstrated `payment_intent.succeeded` and `payment_method.attached`. The event type itself is a documented Stripe event; dispatch is standard practice.

**Framework-specific notes**:
- **Spring Boot**: annotate the endpoint with `@RequestMapping(consumes = MediaType.TEXT_PLAIN_VALUE)` and inject `HttpServletRequest`; read the raw body with `request.getReader()` and pass as `String` — do NOT use `@RequestBody` with a parsed type.
- **Quarkus / Jakarta**: use `@Context HttpServletRequest` and read `request.getInputStream()` into a `String`.
- **Spark Java** (as in the KB example): `request.body()` gives the raw string; pass `request.headers("Stripe-Signature")` as `sigHeader`.

Source: [Stripe webhooks — Java](https://docs.stripe.com/webhooks?lang=java) · [Stripe handle payment events](https://docs.stripe.com/webhooks/handling-payment-events) · [Stripe webhook signatures](https://docs.stripe.com/webhooks/signature) (2026-07-23)

---

## Production Readiness Checklist

Before going live with stripe-java 33.x integrations:

| Item | Check | Source |
|---|---|---|
| Single stripe-java 33.1.1 on classpath | `mvn dependency:tree \| grep stripe` shows exactly one entry | [Maven Central](https://central.sonatype.com/artifact/com.stripe/stripe-java) |
| Secret key from env / secret manager | No `sk_live_*` in source or config files | [Stripe keys](https://docs.stripe.com/keys) |
| Webhook signature verified on every request | `client.constructEvent(payload, sigHeader, endpointSecret)` in place | [Stripe webhooks](https://docs.stripe.com/webhooks/signature) |
| Idempotency keys on all state-changing calls | `RequestOptions.setIdempotencyKey(...)` on create/update calls | [Stripe idempotency](https://docs.stripe.com/api/idempotent_requests) |
| Amounts server-derived (not client-supplied) | Amount sourced from your catalog/DB, not from request params | [Stripe security guide](https://docs.stripe.com/security/guide) |
| Exception handling by StripeException subtype | `CardException`, `RateLimitException`, etc. caught separately | [Stripe error handling](https://docs.stripe.com/error-handling?lang=java) |
| Webhook dedup storage in place | Unique index or Redis SETNX on `event.getId()` | [Stripe duplicate events](https://docs.stripe.com/webhooks#handle-duplicate-events) |
| Restricted API keys (least-privilege) | Per-service keys scoped to required resources only | [Stripe restricted keys](https://docs.stripe.com/keys#limit-access) |
| `whsec_` secret in secret manager | Not hardcoded; rotated on suspected leak | [Stripe security guide](https://docs.stripe.com/security/guide) |
| Stripe CLI webhook tested locally | `stripe listen` + `stripe trigger` returned `[200]` for all handled event types | [Stripe CLI](https://docs.stripe.com/stripe-cli) |
| Connect timeout / read timeout tuned | Defaults: 30 s connect, 80 s read (adjust per SLA if needed) | [`Stripe.java`](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/Stripe.java) |
| `getRequestId()` logged on every StripeException | For Stripe support correlation; alert on `AuthenticationException` | [Stripe request IDs](https://docs.stripe.com/dashboard/basics#logs) |
