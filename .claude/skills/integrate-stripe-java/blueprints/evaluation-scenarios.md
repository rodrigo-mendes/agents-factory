# Evaluation Scenarios — integrate-stripe-java

These scenarios test the `stripe-integrator` executor agent invoked via `integrate-stripe-java`.
Run with `/evaluating-skill-scenarios integrate-stripe-java`.

---

## Scenario 1 — PaymentIntent Create with Idempotency (Canonical)

**Input**: "Implement a REST endpoint POST /payments that creates a PaymentIntent for $20.00 USD
with automatic payment methods enabled. Use a UUID v4 idempotency key. Target project:
./payments-api. Maven wrapper present. Unit tests: yes."

**Expected behavior**:
1. Agent loads `developing-stripe-java-core-v34` first (StripeClient construction, idempotency).
2. Loads `processing-stripe-payments-v34` for PaymentIntent create parameters.
3. Loads family rules; confirms R01 (idempotency key), R05 (no global Stripe.apiKey), R06 (no
   client_secret logging).
4. Generates a Java class with:
   - `StripeClient` instantiated via constructor (not `Stripe.apiKey` global).
   - `PaymentIntentCreateParams` using `setAmount(2000L)`, `setCurrency("usd")`, `AutomaticPaymentMethods`.
   - `RequestOptions` with a UUID v4 idempotency key passed to every `.create()` call.
   - A unit test verifying the params builder values.
5. Runs `./mvnw clean compile` and `./mvnw test`; reports results.
6. Report includes R01–R07 checklist with PASS/N/A per rule.

**Pass criteria**:
- `Stripe.apiKey` does not appear in any generated file (R05).
- Idempotency key present on `.create()` call (R01).
- Amount is `2000L` as `Long`, not a float or string (skill pattern).
- `client_secret` is not logged (R06).
- Verification commands are run and results reported.
- All `(medium confidence)` accessors (e.g. `.setConfirm(true)`) are flagged if used.

---

## Scenario 2 — Missing Requirement → Returns Questions (Non-Interactive Contract)

**Input**: "Add a Stripe webhook endpoint."

**Expected behavior**:
1. Agent identifies the requirement is underspecified: no project path, no information on which
   event types to handle, no async processor details, no dedup store specified.
2. At Step 1, agent stops and returns numbered questions. Example questions:
   1. What is the target project path?
   2. Which Stripe event types should this endpoint handle (e.g., `payment_intent.succeeded`,
      `invoice.payment_failed`)?
   3. Where should processed event IDs be persisted for deduplication (DB table, Redis, in-memory)?
   4. Should processing be synchronous (simple handler) or asynchronous (queue-based)?
   5. Is the endpoint using Spring MVC, Quarkus, or plain servlet? (Affects raw-body capture.)
3. No code is generated.

**Pass criteria**:
- Returns numbered questions without producing any code.
- Does not invent defaults for async processor or dedup store.
- At least 3 questions returned, all concrete.

---

## Scenario 3 — Webhook Handler with Signature-First and Deduplication

**Input**: "Implement a Spring Boot webhook endpoint at POST /webhooks/stripe that: (1) verifies
the Stripe-Signature header before any logic, (2) dedupes on event ID using a processed_events
table (Spring Data JPA), (3) returns 200 OK immediately, (4) publishes the event to an
application event queue for async processing. Target: ./billing-service, Maven wrapper, tests: yes."

**Expected behavior**:
1. Agent loads `developing-stripe-java-core-v34` and `handling-stripe-webhooks-v34`.
2. Loads family rules R02 (signature first), R03 (dedupe + 2xx), R06 (no whsec logging).
3. Generates a Spring `@RestController` with:
   - `@RequestBody String rawBody` to capture unparsed UTF-8 body (raw-body rule from webhooks skill).
   - `client.constructEvent(rawBody, sigHeader, whsec)` as the first statement (R02).
   - Dedupe check against `ProcessedEventRepository` before any processing (R03).
   - Return `ResponseEntity.ok().build()` before async publish (R03).
   - `ApplicationEventPublisher.publishEvent(...)` for async processing.
4. Runs `./mvnw clean compile` and `./mvnw test`.
5. R02 and R03 marked PASS in the checklist.

**Pass criteria**:
- Signature verification call is the first non-trivial statement in the handler (R02 — PASS).
- Dedupe on `event.getId()` present before any business logic (R03 — PASS).
- 200 OK returned before async processing (R03 — PASS).
- Raw body captured as `String` without JSON re-parsing (webhooks skill always-do).
- `whsec` is not logged (R06 — PASS).

---

## Scenario 4 — 33.x to 34.x Migration: Invoice Subscription Accessor

**Input**: "We have existing code calling `invoice.getSubscription()` in our 33.x integration.
Migrate this to stripe-java 34.x. Project: ./legacy-billing, plain mvn (no wrapper)."

**Expected behavior**:
1. Agent loads `developing-stripe-java-core-v34` and `managing-stripe-subscriptions-v34`.
2. Loads family rules; identifies R07 (33.x pattern superseded).
3. Greps the project for `getSubscription()` calls on Invoice objects.
4. Replaces with `invoice.getParent().getSubscriptionDetails().getSubscription()`, guarded by
   `"subscription_details".equals(parent.getType())` check.
5. Also checks for `.setPaymentMethodTypes(...)` (R07, payments skill) and
   `SubscriptionUpdateParams.billingCycleAnchor` enum usage (R07, subscriptions skill).
6. Runs `mvn clean compile`; fixes any remaining compile errors.
7. Reports: R07 PASS (all ≤33.x patterns removed), files changed.

**Pass criteria**:
- No `invoice.getSubscription()` remains in any Java file after the migration.
- Guard `"subscription_details".equals(parent.getType())` is present before `getSubscriptionDetails()`.
- All R07-listed patterns are checked (not just the Invoice one).
- Compile verification is run with `mvn clean compile` (no wrapper), result reported.
- `(medium confidence)` items from `managing-stripe-subscriptions-v34` are flagged.
