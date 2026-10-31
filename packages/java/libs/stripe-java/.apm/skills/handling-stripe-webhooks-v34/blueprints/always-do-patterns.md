# Always-Do Patterns — stripe-java 34.0.0 (WEBHOOKS)

Sources fetched 2026-10-14.

## 1. Signature Verification

Instance method (preferred in 34.x); static `Webhook.constructEvent` adds a 5-arg `Clock` overload for tests.

```java
// Instance — 3-arg, DEFAULT_TOLERANCE = 300 s
// Source: https://stripe.dev/stripe-java/com/stripe/StripeClient.html
Event event = client.constructEvent(rawBody, sigHeader, webhookSecret);

// Static — 3-arg (same DEFAULT_TOLERANCE)
// Source: https://stripe.dev/stripe-java/com/stripe/net/Webhook.html
Event event = Webhook.constructEvent(rawBody, sigHeader, webhookSecret);

// Static — 4-arg (custom tolerance seconds)
Event event = Webhook.constructEvent(rawBody, sigHeader, webhookSecret, 600L);

// Static — 5-arg (injectable Clock for unit tests)
// Source: https://raw.githubusercontent.com/stripe/stripe-java/v34.0.0/src/main/java/com/stripe/net/Webhook.java
Event event = Webhook.constructEvent(rawBody, sigHeader, webhookSecret, 300L, Clock.fixed(...));

// Catch on failure — map to HTTP 400
// Source: https://docs.stripe.com/webhooks/event-notification-handlers?lang=java
try { event = client.constructEvent(rawBody, sigHeader, webhookSecret); }
catch (SignatureVerificationException e) { return ResponseEntity.status(400).body("Invalid sig"); }

// Thin events (v2) — use parseEventNotification instead
// Source: https://stripe.dev/stripe-java/com/stripe/StripeClient.html
EventNotification notif = client.parseEventNotification(rawBody, sigHeader, webhookSecret);
```

Note: `StripeClient.constructEvent` exposes only 3-arg and 4-arg (no `Clock`); 5-arg is static-only.

## 2. Raw Body

Pass the raw UTF-8 bytes — any JSON middleware that re-serializes breaks HMAC verification.

```java
// Spring Boot — @RequestBody String, NOT a DTO
// Source: https://docs.stripe.com/webhooks/event-notification-handlers?lang=java
@PostMapping("/webhook")
public ResponseEntity<String> webhook(
        @RequestBody String rawBody,
        @RequestHeader("Stripe-Signature") String sig) { ... }

// AWS Lambda — capture rawBody via body-mapping template before auto-parsing.
```

## 3. 2xx and Async

Return `200` immediately; hand work to an async queue.

```java
// Source: https://docs.stripe.com/webhooks/event-notification-handlers?lang=java
Event event = client.constructEvent(rawBody, sig, webhookSecret);
asyncQueue.dispatch(event);        // enqueue BEFORE returning
return ResponseEntity.ok("");      // 200 stops Stripe retries
```

Rules: `2xx` = OK; `3xx` = failure; `4xx`/`5xx` = failure; retries up to 3 days; TLS 1.2+ required.

## 4. Deduplication

Dedupe on `event.getId()` (`evt_…`); supplement with `data.object` id + `event.type` for rare dual events.

```java
// Source: https://docs.stripe.com/webhooks/event-notification-handlers?lang=java
if (seen.contains(event.getId())) return ResponseEntity.ok("dup");
seen.add(event.getId());

// For StripeEventNotificationHandler — dedupe in preHandle
handler.preHandle((notif, cl) -> {
    if (seen.contains(notif.getId())) return false; // false = skip without error
    seen.add(notif.getId()); return true;
});
```

## 5. Deserialization

`getObject()` returns `Optional<StripeObject>` — **empty** when `Event.getApiVersion()` ≠ `Stripe.API_VERSION`.
Always check presence; pin your webhook endpoint to `2026-09-30.endive` as the permanent fix.

```java
// Source: https://stripe.dev/stripe-java/com/stripe/model/EventDataObjectDeserializer.html
EventDataObjectDeserializer d = event.getDataObjectDeserializer();
d.getObject().ifPresent(obj -> { /* cast and process */ });

// Mismatch handling:
if (d.getObject().isEmpty()) {
    String raw = d.getRawJson(); // inspect or use deserializeUnsafe() with known risk
}
```

## 6. Event Notification Handler

Use `com.stripe.StripeEventNotificationHandler` (not `EventNotificationHandler` — that class does not exist).
Created via `client.notificationHandler(secret, fallback)` (GA Java since v33.4.0; fix #2294 in 34.0.0).

```java
// Source: https://stripe.dev/stripe-java/com/stripe/StripeEventNotificationHandler.html
// Source: https://docs.stripe.com/webhooks/event-notification-handlers?lang=java
StripeEventNotificationHandler handler =
    client.notificationHandler(WEBHOOK_SECRET, (notif, cl, details) -> { /* fallback */ });

handler
    .onV1ChargeSucceeded((notif, cl) -> { /* cl scoped to event account — #2294 fix */ })
    .onV1PaymentIntentSucceeded((notif, cl) -> { /* ... */ });

// Verifying endpoint:
try { handler.handle(rawBody, sig); return ResponseEntity.ok(""); }
catch (SignatureVerificationException e) { return ResponseEntity.status(400).body("bad sig"); }

// Pre-authenticated (EventBridge/Event Grid only — no sig check):
StripeEventNotificationHandlerWithoutVerification h2 =
    client.notificationHandlerWithoutVerification((notif, cl, details) -> { /* fallback */ });
// Source: https://docs.stripe.com/webhooks/event-notification-handlers?lang=java
```
