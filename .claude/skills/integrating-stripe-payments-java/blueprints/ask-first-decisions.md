# ⚠️ Ask First — stripe-java 33.x Decision Matrices

> **Version lock**: All patterns target **stripe-java 33.x** (latest patch **33.1.1**, API `2026-06-24.dahlia`).
> Present the tradeoff table and wait for a decision before generating code.

---

## C1 — Synchronous vs. asynchronous calls

**Context**: stripe-java 33.x ships synchronous service methods. Async behavior is achieved by wrapping calls in your application's own executor or reactive framework.

> **Unverified**: Whether stripe-java 33.x exposes first-class async service methods (e.g., `CompletableFuture`-returning variants) was not confirmed against an official dated source. Treat as sync-only until confirmed against the 33.1.1 Javadoc at `javadoc.io/doc/com.stripe/stripe-java/33.1.1`. See KB Section 8, item 2.

| Option | Latency model | Best when | Cost |
|---|---|---|---|
| Synchronous (default `client.v1()...`) | Blocks calling thread | Request/response web handlers, simple flows, low concurrency | Ties up one thread per in-flight Stripe call |
| Async via executor (wrap sync calls) | Non-blocking at application level | High-throughput, many concurrent Stripe calls, reactive stacks | You own thread-pool sizing, back-pressure, and error propagation |

**Ask**: "How many concurrent Stripe API calls do you expect at peak, and are you running a reactive framework (e.g., WebFlux, Vert.x)?"

```java
// stripe-java 33.x — wrapping sync call in a CompletableFuture executor (ask-first pattern)
CompletableFuture<PaymentIntent> future = CompletableFuture.supplyAsync(() -> {
    try {
        return client.v1().paymentIntents().create(params, opts);
    } catch (StripeException e) {
        throw new RuntimeException(e); // handle in exceptionally()
    }
}, stripeExecutor); // dedicated thread pool sized to your concurrency budget
```

---

## C2 — `StripeClient` instance vs. deprecated static resource pattern

**Context**: 33.x README states the static pattern (`Customer.create(...)`, `Stripe.apiKey = ...`) "is still available to use but will be marked as deprecated soon." New code MUST use `StripeClient` + `v1()`.

| Option | Status in 33.x | Use when |
|---|---|---|
| `client.v1().customers().create(params)` | Recommended, non-deprecated | All new 33.x code |
| `Customer.create(paramsMap)` (static, global key) | Pre-deprecated ("will be marked soon") | Only legacy code in the middle of a migration — not for new features |

**Ask**: "Is this a new integration, or are you migrating an existing codebase that uses the static pattern?"

For new code, always go with `StripeClient`. For migration, apply `StripeClient` + `v1()` module-by-module; do not add new static-pattern calls.

Source: [stripe-java README](https://github.com/stripe/stripe-java) (2026-07-23)

---

## C3 — PaymentIntent automatic vs. manual confirmation

**Context**: Stripe supports two PaymentIntent confirmation modes with distinct SCA/authentication implications.

| Option | Flow | Best when | Tradeoff |
|---|---|---|---|
| Automatic confirmation (`automatic_payment_methods: {enabled: true}`) | Stripe manages next actions client-side via PaymentElement | Standard checkout, PaymentElement UI, broad payment method support | Less server control; client must handle `requires_action` redirects |
| Manual confirmation (`confirm: true` server-side) | Server drives the confirmation step | MOTO (mail order / telephone order), saved-method off-session charges, platform flows | You must explicitly handle `requires_action` state and SCA challenges |

**Ask**: "Is this a customer-initiated checkout flow with a UI (PaymentElement), or a server-initiated charge against a saved payment method?"

```java
// stripe-java 33.x — automatic confirmation (C3 — standard checkout)
PaymentIntentCreateParams autoParams = PaymentIntentCreateParams.builder()
    .setAmount(amountMinorUnits)
    .setCurrency("usd")
    .setAutomaticPaymentMethods(
        PaymentIntentCreateParams.AutomaticPaymentMethods.builder().setEnabled(true).build())
    .build();
PaymentIntent pi = client.v1().paymentIntents().create(autoParams, opts);
// Client-side: use pi.getClientSecret() with Stripe.js / PaymentElement to complete the payment.

// stripe-java 33.x — manual confirmation (C3 — server-initiated off-session)
PaymentIntentCreateParams manualParams = PaymentIntentCreateParams.builder()
    .setAmount(amountMinorUnits)
    .setCurrency("usd")
    .setPaymentMethod(savedPaymentMethodId)
    .setCustomer(customerId)
    .setConfirm(true)
    .setOffSession(true)
    .build();
// Must handle status == "requires_action" for SCA.
```

Source: [Stripe PaymentIntents lifecycle](https://docs.stripe.com/payments/paymentintents/lifecycle) (2026-07-23)

---

## C4 — Webhook idempotency storage backend

**Context**: Stripe may deliver an event more than once. Your handler must dedup on `event.getId()` before executing any side effects (fulfill order, activate subscription, send email). The storage backend choice depends on your infrastructure and durability requirements.

| Option | Dedup key | Best when | Tradeoff |
|---|---|---|---|
| Relational DB unique index on `event_id` | Strong, transactional, durable | Already have a relational DB; side effects are DB writes | Extra write per event; slightly higher latency |
| Redis `SETNX event_id EX <ttl>` | Fast, low-latency, ephemeral | High event volume; acceptable to reprocess after TTL expires | Not durable past TTL; reprocessing possible for very old events |
| No dedup storage (rely on handler idempotency) | — | Side effects are naturally idempotent (e.g., pure upserts) | Risky for any handler with non-idempotent side effects (email sends, charges) |

**Ask**: "Are your webhook handlers idempotent? Do you have a DB or Redis available? What is the acceptable window for duplicate event protection?"

```java
// stripe-java 33.x — webhook dedup pattern (relational DB example)
// Called BEFORE executing any side effects:
if (eventRepository.existsByStripeEventId(event.getId())) {
    return respond(200, "duplicate ignored"); // Stripe stops retrying on 2xx
}
// ... execute side effects ...
eventRepository.markProcessed(event.getId()); // unique constraint prevents race conditions
```

Source: [Stripe webhooks best practices — handle duplicate events](https://docs.stripe.com/webhooks#handle-duplicate-events) (2026-07-23)

---

## C5 — Pagination: auto-pagination vs. manual page cursors

**Context**: stripe-java 33.x supports both iteration patterns for list endpoints.

| Option | Ergonomics | Best when | Tradeoff |
|---|---|---|---|
| `.autoPagingIterable()` | Simple `for-each` loop; SDK handles `starting_after` cursors | Batch jobs, exports, full-dataset scans | Unbounded fetches; watch memory usage and rate limits for large datasets |
| Manual `starting_after` cursor | Explicit control over page size and iteration | UI pagination, bounded result sets, streaming large datasets | More code; you manage cursor state |

**Ask**: "Is this a batch export (full scan) or a paginated UI listing with a bounded page size?"

```java
// stripe-java 33.x — auto-pagination (batch export, use carefully for large datasets)
CustomerListParams listParams = CustomerListParams.builder().setLimit(100L).build();
for (Customer c : client.v1().customers().list(listParams).autoPagingIterable()) {
    processCustomer(c); // SDK auto-fetches next pages; watch Stripe rate limits
}

// stripe-java 33.x — manual cursor pagination (bounded UI listing)
CustomerListParams page1Params = CustomerListParams.builder().setLimit(25L).build();
CustomerCollection page1 = client.v1().customers().list(page1Params);
// To fetch next page:
if (page1.getHasMore()) {
    String lastId = page1.getData().get(page1.getData().size() - 1).getId();
    CustomerListParams page2Params = CustomerListParams.builder()
        .setLimit(25L)
        .setStartingAfter(lastId)
        .build();
    CustomerCollection page2 = client.v1().customers().list(page2Params);
}
```

Source: [Stripe pagination](https://docs.stripe.com/api/pagination) (2026-07-23)

---

## C6 — SDK auto-retries vs. application-level retries

**Context**: stripe-java 33.x includes built-in retry logic. Layering application-level retries on top requires careful idempotency key management to avoid double charges.

| Option | Where retries happen | Default | Best when | Tradeoff |
|---|---|---|---|---|
| SDK `setMaxNetworkRetries(n)` | Inside the client, before returning to caller | 2 retries | Transient network errors; you want minimal retry code | Bounded retries; SDK automatically attaches idempotency key on retried requests |
| App-level retry loop | Your code, outside the SDK call | N/A | Business-level semantics (e.g., retry only CardException after delay) | You MUST pass a stable idempotency key yourself on every attempt |

Default `maxNetworkRetries` is **2** in stripe-java 33.x.

**Ask**: "Do you need business-level retry semantics (e.g., retry declined cards after user updates payment method), or is basic network-error retry sufficient?"

```java
// stripe-java 33.x — SDK-level retries (simple; SDK handles idempotency on retry)
// Configure once at startup:
StripeClient client = new StripeClient(System.getenv("STRIPE_SECRET_KEY"));
// SDK default maxNetworkRetries=2 is usually sufficient for transient network errors.
// To tune: use StripeClientBuilder if the API exposes it, or set Stripe.setMaxNetworkRetries(n)
// (confirm against 33.x API — builder-based config preferred over static setters).

// stripe-java 33.x — app-level retry (MUST use stable idempotency key)
String idempotencyKey = orderId + ":create-pi-" + UUID.randomUUID(); // generate ONCE, reuse on retry
for (int attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    try {
        RequestOptions opts = RequestOptions.builder()
            .setIdempotencyKey(idempotencyKey) // same key every attempt
            .build();
        return client.v1().paymentIntents().create(params, opts);
    } catch (RateLimitException e) {
        Thread.sleep(backoffMs(attempt)); // exponential backoff + jitter
    }
}
```

Source: [`Stripe.java` defaults](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/Stripe.java) · [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests) (2026-07-23)
