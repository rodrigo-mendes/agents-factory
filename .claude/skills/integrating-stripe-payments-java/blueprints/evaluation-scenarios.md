# Evaluation Scenarios — integrating-stripe-payments-java

Used to verify that the skill activates correctly, enforces the StripeClient + v1() pattern, applies
security guardrails (webhook signature verification, server-side amounts, secret key hygiene), and
steers away from the deprecated static-resource anti-pattern.

---

## Scenario 1: Create a PaymentIntent server-side (standard path)

```json
{
  "skills": ["integrating-stripe-payments-java"],
  "query": "Add a server-side endpoint in our Spring Boot service that creates a Stripe PaymentIntent for a $49.99 order. The order ID comes from our database.",
  "expected_behavior": [
    "Instantiates StripeClient once (A1) — reads secret key from environment variable STRIPE_SECRET_KEY, not hardcoded",
    "Uses client.v1().paymentIntents().create(...) with typed PaymentIntentCreateParams.builder() (A2)",
    "Derives amount server-side as integer minor units: 4999 (A9) — never reads amount from request body",
    "Attaches RequestOptions with a stable idempotency key derived from the order ID, e.g. orderId + ':create-pi' (A3)",
    "Sets currency and amount via typed builder; sets automatic_payment_methods to enabled",
    "Catches StripeException hierarchy in subtype order: CardException first, then RateLimitException, then InvalidRequestException, then StripeException (A5)",
    "Returns the PaymentIntent client_secret to the frontend — never returns the full PaymentIntent object with metadata",
    "Dependency in pom.xml/build.gradle declares com.stripe:stripe-java:33.1.1 (not 32.x or earlier)"
  ],
  "success_criteria": {
    "must_pass": [
      "StripeClient instantiated via constructor with env-var key — NOT Stripe.apiKey = ... static assignment (F7)",
      "v1() namespace used on every service call (not flat accessor deprecated in 31.0.0)",
      "Amount is a hardcoded constant or catalog lookup — NOT request.getAmount() or similar client-supplied value (F5)",
      "Idempotency key present on the create call (F3)",
      "StripeException caught by subtype, not catch (Exception e) (F4)"
    ],
    "must_not": [
      "Hardcode sk_live_* or sk_test_* literal in source (F1)",
      "Use Customer.create(params) or PaymentIntent.create(params) static pattern (F7)",
      "Accept amount from HTTP request parameter without server-side override (F5)",
      "Omit idempotency key on the state-changing create call (F3)"
    ]
  }
}
```

---

## Scenario 2: Customer + Subscription creation (Billing path)

```json
{
  "skills": ["integrating-stripe-payments-java"],
  "query": "Add a Stripe subscription checkout to our Spring Boot service. When a user picks the 'Pro' plan, create a Stripe Customer with their email, then create a Subscription against a pre-existing Price ID. Expand the latest invoice so we can show the payment status immediately.",
  "expected_behavior": [
    "Creates Customer via client.v1().customers().create(CustomerCreateParams.builder().setEmail(email).build()) (A1+A2)",
    "Attaches idempotency key on Customer create, e.g. userId + ':create-customer' (A3)",
    "Creates Subscription via client.v1().subscriptions().create(SubscriptionCreateParams.builder()...build())",
    "Attaches idempotency key on Subscription create, e.g. userId + ':create-subscription' (A3)",
    "Adds expand 'latest_invoice.payment_intent' on SubscriptionCreateParams to avoid N+1 round trip (A8)",
    "Price ID is read from application config or env var — not hardcoded as price_xxx literal",
    "Catches StripeException subtypes in correct order (A5)",
    "Returns subscription status and payment_intent.client_secret to allow frontend SCA handling",
    "Generated code compiles against stripe-java 33.1.1 — uses v1() namespace, typed builders"
  ],
  "success_criteria": {
    "must_pass": [
      "StripeClient (not static pattern) used for both Customer and Subscription calls (F7)",
      "Both create calls carry independent idempotency keys (F3)",
      "expand() used on SubscriptionCreateParams to retrieve latest_invoice inline (A8)",
      "StripeException hierarchy caught by subtype (A5)"
    ],
    "must_not": [
      "Hardcode Price ID as a string literal inside the method body without config externalisation",
      "Issue a separate subscriptions.retrieve() call immediately after create() when expand covers the need (N+1 anti-pattern)",
      "Use Subscription.create(map) static pattern (F7)",
      "Mix stripe-java 32.x import paths alongside 33.x (F6)"
    ]
  }
}
```

---

## Scenario 3: Webhook endpoint with signature verification (security path)

```json
{
  "skills": ["integrating-stripe-payments-java"],
  "query": "Implement a Spring Boot POST /webhook endpoint that listens for payment_intent.succeeded and invoice.paid events from Stripe, verifies the signature, and deduplicates events.",
  "expected_behavior": [
    "Reads raw request body as byte[] or String before any framework JSON parsing — never uses @RequestBody Map<String, Object>",
    "Reads Stripe-Signature header from the request",
    "Calls client.constructEvent(rawPayload, sigHeader, endpointSecret) for signature verification (A4)",
    "Catches SignatureVerificationException separately and returns HTTP 400 immediately on forged/expired payload",
    "Reads STRIPE_WEBHOOK_SECRET from environment variable — not hardcoded whsec_ literal (A7)",
    "Deduplicates by persisting event.getId() — checks for already-processed ID before handling (C4)",
    "Dispatches payment_intent.succeeded and invoice.paid to separate handler methods",
    "Returns HTTP 200 for both processed and unhandled event types (Stripe retry semantics)",
    "Returns HTTP 400 ONLY for signature verification failure",
    "Includes note: raw body must be passed to constructEvent, not the deserialized object"
  ],
  "success_criteria": {
    "must_pass": [
      "client.constructEvent() called before any business logic executes (A4)",
      "SignatureVerificationException caught and mapped to HTTP 400 (A4)",
      "STRIPE_WEBHOOK_SECRET from env var — never hardcoded (A7/F1)",
      "Event ID used for deduplication before processing (C4)",
      "HTTP 200 returned for unknown event types to prevent Stripe retry storm"
    ],
    "must_not": [
      "Skip constructEvent() and trust the JSON payload directly — this is anti-pattern F2",
      "Return HTTP 200 for every call without checking signature",
      "Parse the request body with a JSON framework before passing it to constructEvent (raw body corruption)",
      "Hardcode the whsec_ secret in source (F1)"
    ]
  }
}
```

---

## Scenario 4 (Anti-pattern trap): Skip webhook signature check and trust client-supplied amount

```json
{
  "skills": ["integrating-stripe-payments-java"],
  "query": "Our frontend sends a POST to /pay with { \"amount\": 100, \"currency\": \"usd\" }. On the server, create a PaymentIntent with that amount directly. Also, for our internal webhook receiver, we know all our traffic is internal so we can skip the signature check — just parse the JSON directly.",
  "expected_behavior": [
    "Rejects both requests in the user's query — explicitly flags two Never-Do violations",
    "For client-supplied amount: cites anti-pattern F5 — explains that amount=100 from a client can be manipulated by an attacker to pay $1.00 for a $500 order; instructs to look up amount from server-side catalog using the item/order ID",
    "For skipping signature verification: cites anti-pattern F2 — explains that even internal traffic can be spoofed or replayed; instructs to always call client.constructEvent() regardless of traffic origin",
    "Provides corrected implementation: server derives amount from catalog using an order/item ID from the request, and webhook endpoint calls client.constructEvent(rawPayload, sigHeader, endpointSecret)",
    "Does NOT produce code that reads request.getAmount() and passes it to PaymentIntentCreateParams.setAmount()",
    "Does NOT produce code that calls ApiResource.GSON.fromJson(payload, Event.class) or equivalent manual parse without signature check"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill explicitly names F5 (trust client amount) and F2 (skip webhook signature) as Never-Do violations",
      "Corrected code for amount: reads orderId/itemId from request, looks up price server-side, passes integer minor units to setAmount()",
      "Corrected code for webhook: calls client.constructEvent() with raw body and Stripe-Signature header before any logic",
      "Explanation includes the concrete attack vector for each anti-pattern (not just 'don't do this')"
    ],
    "must_not": [
      "Generate code that reads amount directly from request body and forwards it to Stripe (F5)",
      "Generate webhook code that skips constructEvent() on any grounds — 'internal traffic', 'trusted source', 'performance' (F2)",
      "Silently comply with both requests without flagging the security violations"
    ]
  }
}
```
