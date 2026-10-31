# Stripe Java Family Rules — v34

> Shipped with `integrate-stripe-java` (copied 2026-10-29 from the factory provenance file `workspace/stripe-java/_family_rules_v34.md`, which now
> points here). This copy is the one stripe-integrator, stripe-advisor and review-stripe-integration read; edit it here, not in `workspace/`.

Cross-cutting policies that span two or more of the four stripe-java v34 knowledge skills.
Rules are numbered and testable. Every rule cites the skill(s) from which the policy is derived.

Skills in scope: `developing-stripe-java-core-v34`, `processing-stripe-payments-v34`,
`handling-stripe-webhooks-v34`, `managing-stripe-subscriptions-v34`.

Research date: **2026-10-14**. Version lock: stripe-java 34.0.0 / Stripe API `2026-09-30.endive`.

---

## Rules

### R01 — Idempotency key on every mutating POST

**Policy:** Every POST call (PaymentIntent create/confirm/capture/cancel, Customer create,
Subscription create, any other mutating operation) must pass a `RequestOptions` with an
idempotency key (≤ 255 chars): one key per logical operation, business-derived when possible,
persisted and reused on every retry of that operation; a UUID v4 only when no business key exists
(aligned 2026-10-29 with integrating-stripe-quarkus-v3-40 and the stripe agents).

**Test:** Grep for `.create(`, `.confirm(`, `.capture(`, `.cancel(` without a matching
`RequestOptions` argument on the same or preceding lines.

**Skills:** `developing-stripe-java-core-v34` (idempotency mechanics), `processing-stripe-payments-v34`
(PaymentIntent calls), `managing-stripe-subscriptions-v34` (Customer/Subscription calls).

---

### R02 — Verify webhook signature BEFORE any side effect

**Policy:** `client.constructEvent(raw, sigHeader, whsec)` or
`client.parseEventNotification(raw, sigHeader, whsec)` must be called before any database write,
queue publish, or external API call triggered by an incoming webhook payload.

**Test:** Webhook handler methods must not contain business logic (DB writes, queue publishes)
before the signature verification call. The verification call must appear as the first non-trivial
statement in the handler method or be delegated to a `StripeEventNotificationHandler` that
verifies on `handle(body, sig)`.

**Skills:** `handling-stripe-webhooks-v34` (primary), `processing-stripe-payments-v34` (webhook
events for PaymentIntent status transitions).

---

### R03 — Dedupe webhook events on event ID and return 2xx

**Policy:** Every webhook must be deduplicated on `event.getId()` (the `evt_…` key) before
processing, in the handler or in the consumer it durably hands off to. The HTTP response must be 2xx
once the event is verified and handed off (process asynchronously). Returning non-2xx
or letting the request time out causes Stripe to retry for up to 3 days.

**Test:** Webhook endpoints must: (a) check the processed-event store (in the handler or its consumer) before executing business logic;
(b) return `200 OK` (or equivalent 2xx) regardless of async processing outcome.

**Skills:** `handling-stripe-webhooks-v34` (primary — deduplication and async response patterns).

---

### R04 — Pin and align Stripe-Version across SDK and webhook endpoints

**Policy:** The stripe-java 34.0.0 SDK default is `2026-09-30.endive`. Webhook endpoint
`api_versions` must match the SDK version to prevent deserialization mismatches.
Do not override `Stripe-Version` per-request without verifying SDK model compatibility.

**Test:** Webhook endpoints registered in the Stripe Dashboard must declare
`api_versions: ["2026-09-30.endive"]` (or whatever version the SDK default is pinned to).
Per-request `Stripe-Version` overrides in code are an Ask-First item per `developing-stripe-java-core-v34`.

**Skills:** `developing-stripe-java-core-v34` (API-version pinning), `handling-stripe-webhooks-v34`
(endpoint api_versions, deserialization footgun).

---

### R05 — Never use the deprecated global `Stripe.apiKey`

**Policy:** `Stripe.apiKey = "sk_..."` (the pre-v23 global assignment pattern) must not appear
in any production code. Instantiate `StripeClient` via constructor or builder.

**Test:** Grep for `Stripe\.apiKey\s*=` — any match is a violation.

**Skills:** `developing-stripe-java-core-v34` (primary — StripeClient patterns and the removal
status of the global field, tagged as an unverified U1 item in that skill).

---

### R06 — Never log secret keys or full card data

**Policy:** API secret keys (`sk_live_…`, `sk_test_…`), webhook signing secrets (`whsec_…`),
`client_secret` values, and any card/PAN data must not appear in application logs at any level.

**Test:** Log statements must not interpolate variables named `apiKey`, `secretKey`, `whsec`,
`clientSecret`, `cardNumber`, or similar; log masking must be applied.

**Skills:** `developing-stripe-java-core-v34` (API key handling), `processing-stripe-payments-v34`
(`client_secret` scoping — Never Do: log or expose `client_secret`), `handling-stripe-webhooks-v34`
(webhook secret handling).

---

### R07 — Treat ≤33.x patterns as superseded; do not mix versions

**Policy:** Any pattern from stripe-java ≤33.x is treated as misinformation when targeting 34.x.
Specifically prohibited:
- `invoice.getSubscription()` → use `invoice.getParent().getSubscriptionDetails().getSubscription()`
- `.setPaymentMethodTypes(...)` on PaymentIntentCreateParams → use `automatic_payment_methods`
- `Stripe.apiKey` global → use `StripeClient`
- `SubscriptionUpdateParams.billingCycleAnchor` enum `'now'/'unchanged'` → use `billing_cycle_anchor_param`

**Test:** Grep for the listed ≤33.x call patterns. Any match in code targeting 34.x is a violation.

**Skills:** `developing-stripe-java-core-v34`, `processing-stripe-payments-v34`,
`managing-stripe-subscriptions-v34`, `handling-stripe-webhooks-v34` — all four skills carry
"33 to 34 Migration" sections identifying the specific superseded patterns.
