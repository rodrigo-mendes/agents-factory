---
name: integrating-stripe-payments-java
description: "Integrates Stripe payments into Java applications using stripe-java 33.x. Use when implementing PaymentIntents, Subscriptions, or Webhook endpoints with the Stripe Java SDK on Java 8/11/17/21/25."
---

## Function

Specialist in security-critical Stripe payment integration for **stripe-java 33.x** (latest patch 33.1.1), pinning Stripe API version `2026-06-24.dahlia`, targeting Java LTS runtimes 8, 11, 17, 21, and 25.

---

## Version Context

**Technology**: Stripe Java SDK (`com.stripe:stripe-java`)
**Target version**: 33.x (latest confirmed patch: **33.1.1**, released 2026-07-15)
**Pinned Stripe API**: `2026-06-24.dahlia` (33.1.x line); `2026-05-27.dahlia` (33.0.0 only)
> **Unverified**: granular per-field diffs between `2026-05-27.dahlia` and `2026-06-24.dahlia` were not verified. Version strings/pins are confirmed from the CHANGELOG; if your code depends on dahlia-specific field behavior, check the [Stripe API changelog](https://docs.stripe.com/changelog) before relying on it.
**Release dates**: 33.0.0 → 2026-06-05 · 33.1.0 → 2026-06-24 · 33.1.1 → 2026-07-15
**Support status**: Current stable major line (as of 2026-07-23). Actively maintained.
**Java baseline**: LTS JDKs — 8 (1.8), 11, 17, 21, 25

**Important changes reaching 33.x**:
- **33.0.0**: `tax_rate.tax_details` made expandable (out-of-band major; no-op if you do not use `tax_details`)
- **32.0.0** (carried into 33.x): `RateLimitException` reparented — now extends `StripeException` directly, no longer `ApiException`; `parseThinEvent` renamed `parseEventNotification`; module name changed from `stripe.java` to `com.stripe`
- **31.0.0**: flat top-level service accessors deprecated in favor of `v1()` namespace
- **30.0.0**: event handling overhauled into strongly-typed `EventNotification` classes

**Deprecated in 33.x**:
- Static resource pattern (`Customer.create(...)`, `Stripe.apiKey = ...`) — README states "will be marked as deprecated soon". Use `StripeClient` + `v1()` for all new code.

Source: [stripe-java README](https://github.com/stripe/stripe-java) · [CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) (checked 2026-07-23)

**CRITICAL — Version Lock**:
This skill targets **stripe-java 33.x** ONLY (latest patch **33.1.1**).
Patterns from **32.x and earlier are treated as disinformation** — do not mix them in.
Verify every code path against the `v1()` namespace and typed builders.

---

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Full 33.x code: StripeClient, typed builders, idempotency, webhook verification, exception handling, API pinning, secret key, expandable fields, server-side amounts
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Decision matrices: sync vs async, StripeClient vs static, PaymentIntent confirmation mode, webhook dedup storage, pagination, retry policy
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with ✅ 33.x corrected side-by-side
- **[Integration Examples](./blueprints/integration-examples.md)** — PaymentIntent lifecycle, Customer + Subscription (Billing), webhook endpoint for `payment_intent.succeeded` + `invoice.paid`
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 concrete scenarios: PaymentIntent creation, Customer+Subscription, webhook signature verification, anti-pattern trap (F2+F5)
- **[Verification Loop](#verification-loop)** — Maven/Gradle coords, `mvn dependency:tree`, Stripe CLI `stripe listen` / `stripe trigger`
- **[Quick Reference](#quick-reference)** — Essential coords, limits, and commands

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with full 33.x-tagged code, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns (Complex tier — 9 patterns)**:

- **A1 — Instantiate `StripeClient` once; reuse it** — `new StripeClient(System.getenv("STRIPE_SECRET_KEY"))`. The client owns the HTTP pool. Instantiating per-request is wasteful; the static global pattern is pre-deprecated.
- **A2 — Use typed parameter builders through `v1()` namespace** — `client.v1().customers().create(CustomerCreateParams.builder()...build())`. Compile-time safety; `v1()` is the non-deprecated accessor (flat accessors deprecated in 31.0.0).
- **A3 — Idempotency key on every state-changing call** — `RequestOptions.builder().setIdempotencyKey(orderId + ":create-pi")`. Stable per logical operation (not per attempt). Prevents duplicate charges on retry.
- **A4 — Verify webhook signatures before trusting any payload** — `client.constructEvent(payload, sigHeader, endpointSecret)` throws `SignatureVerificationException` on forged/expired payloads. Default tolerance: 300 s. Unverified webhook = attacker-controlled input.
- **A5 — Catch `StripeException` hierarchy by subtype, most specific first** — Order: `CardException` → `RateLimitException` → `InvalidRequestException` → `StripeException`. Note: `RateLimitException` extends `StripeException` directly (not `ApiException`) since 32.0.0.
- **A6 — Pin the Stripe API version explicitly** — 33.1.x pins `2026-06-24.dahlia` by default; consider an explicit override via `RequestOptions` for defense-in-depth across environments. *Note: exact setter method name `setStripeVersionOverride` is unverified against 33.x Javadoc — verify before use.*
- **A7 — Read secret key from environment / secret manager only** — `System.getenv("STRIPE_SECRET_KEY")`. Guard against null/blank at startup. Never commit `sk_live_*` or `sk_test_*` to source.
- **A8 — Use expandable fields to avoid N+1 round trips** — `addExpand("customer")` / `addExpand("latest_charge")` on retrieve/list params. 33.0.0 specifically made `tax_rate.tax_details` expandable (PR #2234).
- **A9 — Compute amounts server-side in integer minor units** — Stripe amounts are integers (e.g., 2000 = $20.00 USD). Derive from your own catalog; never accept a client-supplied amount.

### ⚠️ Ask First

For complete decision matrices with tradeoff tables, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points (6 architectural crossroads)**:

- **C1 — Sync vs async calls** — 33.x ships synchronous service methods; async is achieved by wrapping in your own executor/reactive layer. Whether 33.x exposes first-class async methods is **unverified** — treat as sync-only until confirmed.
- **C2 — `StripeClient` instance vs deprecated static pattern** — `client.v1()...` is recommended for all new 33.x code; `Customer.create(...)` only for legacy code mid-migration.
- **C3 — PaymentIntent automatic vs manual confirmation** — Automatic (`automatic_payment_methods`) for standard checkout / PaymentElement; manual (`confirm=true`) for MOTO / saved-method off-session (requires handling `requires_action` / SCA).
- **C4 — Webhook idempotency storage backend** — Relational unique index on `event.id` (strong, transactional) vs Redis SETNX with TTL (fast, ephemeral) vs no storage (only if handlers are naturally idempotent). Stripe may deliver events more than once.
- **C5 — Pagination: auto-pagination vs manual cursors** — `.autoPagingIterable()` for batch/export jobs (watch unbounded fetches); manual `starting_after` cursor for UI pagination / bounded pages.
- **C6 — SDK auto-retries vs application-level retries** — SDK default `maxNetworkRetries = 2`; SDK auto-attaches idempotency keys on retries. App-level retries require you to supply a stable idempotency key manually.

### 🚫 Never Do

For complete anti-patterns with wrong ❌ / correct ✅ code side-by-side, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns (7 anti-patterns, each with ✅ alternative)**:

- **F1 — Hardcode secret keys in source** — `new StripeClient("sk_live_51H...")` leaks the key on commit/log. **✅ Use `System.getenv("STRIPE_SECRET_KEY")`.**
- **F2 — Skip webhook signature verification** — `ApiResource.GSON.fromJson(payload, Event.class)` trusts attacker-forged input. **✅ Use `client.constructEvent(payload, sigHeader, endpointSecret)`.**
- **F3 — Retry state-changing calls without an idempotency key** — a network retry creates a second charge. **✅ Pass `RequestOptions` with a stable `setIdempotencyKey`.**
- **F4 — Catch generic `Exception` instead of `StripeException` subtypes** — swallows card declines, rate limits, and programming errors identically. **✅ Branch on `CardException`, `RateLimitException`, `InvalidRequestException`, `StripeException`.**
- **F5 — Trust a client-supplied amount** — attacker sends `amount=1` for a $500 order. **✅ Compute amount server-side from your own catalog in integer minor units.**
- **F6 — Mix SDK majors on the same classpath** — 32.x transitive + 33.x direct = undefined behavior. **✅ One version only; run `mvn dependency:tree | grep stripe` to confirm.**
- **F7 — Write new code on the deprecated static resource pattern** — `Stripe.apiKey = ...` + `Customer.create(map)` is pre-deprecated. **✅ Use `StripeClient` + `v1()` + typed builders.**

---

## Integration Patterns

For complete integration code examples, see [Integration Examples](./blueprints/integration-examples.md).

**Summary of integrations**:
- **stripe-java 33.x ↔ PaymentIntents** — One-time charge lifecycle: create with idempotency key, server-derived amount, automatic confirmation; handle `CardException`; confirm via client-side PaymentElement or server-side `confirm=true`.
- **stripe-java 33.x ↔ Billing / Subscriptions** — Create `Customer`, then `Subscription` referencing a pre-built `Price`; expand `latest_invoice.payment_intent` to avoid N+1; handle `invoice.paid` webhook to activate subscription periods.
- **stripe-java 33.x ↔ Webhooks** — Verify `Stripe-Signature` header via `client.constructEvent()`; dedup on `event.getId()`; dispatch `payment_intent.succeeded` and `invoice.paid`; return HTTP 200 for all processed and unhandled events.

**Common problems**:
- **Problem**: Webhook returns `400` on `stripe trigger` → **Solution**: Confirm the framework passes the **raw** body bytes (not parsed JSON) and `STRIPE_WEBHOOK_SECRET` matches the `whsec_` printed by `stripe listen`.
- **Problem**: `cannot find symbol: method v1()` at compile time → **Solution**: A pre-31.x `stripe-java` jar is on the classpath. Run `mvn dependency:tree` and exclude/upgrade the stale transitive.
- **Problem**: Double charges on retry → **Solution**: Add `RequestOptions` with a stable `setIdempotencyKey` derived from your order/operation ID (A3/F3).

---

## Verification Loop

The agent MUST execute these steps after every code generation involving stripe-java 33.x.

### 1. Dependency — confirm stripe-java 33.x in pom.xml / build.gradle

**Maven** (`pom.xml`):
```xml
<dependency>
  <groupId>com.stripe</groupId>
  <artifactId>stripe-java</artifactId>
  <version>33.1.1</version>
</dependency>
```

**Gradle** (`build.gradle`):
```groovy
implementation "com.stripe:stripe-java:33.1.1"
```

Source: [stripe-java README](https://github.com/stripe/stripe-java) · [Maven Central](https://central.sonatype.com/artifact/com.stripe/stripe-java) (2026-07-23)

### 2. Dependency tree — no mixed majors (F6)

```bash
mvn dependency:tree | grep stripe
```
Expected (exactly one line):
```
[INFO] +- com.stripe:stripe-java:jar:33.1.1:compile
```
Any `32.x` line = mixed majors → exclude the stale transitive and re-run.

### 3. Compile check

```bash
mvn -q -DskipTests compile
```
Expected: `BUILD SUCCESS` with no `cannot find symbol` errors.
A `cannot find symbol: method v1()` error means a pre-31.x jar is on the classpath.

### 4. Local webhook test (Stripe CLI)

```bash
stripe listen --forward-to localhost:4242/webhook
# Expected banner includes: Stripe API Version [2026-06-24.dahlia]
# Note the whsec_... value → set as STRIPE_WEBHOOK_SECRET

stripe trigger payment_intent.succeeded
# listen terminal: --> payment_intent.succeeded [evt_xxx]
#                  <-- [200] POST http://localhost:4242/webhook [evt_xxx]

stripe trigger invoice.paid
# listen terminal: --> invoice.paid [evt_yyy]
#                  <-- [200] POST http://localhost:4242/webhook [evt_yyy]
```

A `[400]` response = signature verification failure (check raw body + correct `whsec_`).

Source: [Stripe CLI](https://docs.stripe.com/stripe-cli) · [stripe trigger](https://docs.stripe.com/cli/trigger) (2026-07-23)

**Troubleshooting**:
- `[400]` on webhook → framework is passing parsed JSON instead of raw body; also confirm `STRIPE_WEBHOOK_SECRET = whsec_...` printed by `stripe listen`
- `cannot find symbol: method v1()` → stale 30.x or earlier jar on classpath; run `mvn dependency:tree`
- `RateLimitException` not caught → likely catching the pre-32.0.0 pattern where it was under `ApiException`; update catch block to extend `StripeException` directly (A5)
- Double charge in test → missing idempotency key on retry path (A3/F3)

---

## Quick Reference

**Dependency coords (stripe-java 33.x)**:
```
com.stripe:stripe-java:33.1.1
Pinned Stripe API: 2026-06-24.dahlia (33.1.x) / 2026-05-27.dahlia (33.0.0)
Java: 8 / 11 / 17 / 21 / 25 (LTS)
```

**Essential build commands**:
```bash
mvn dependency:tree | grep stripe   # verify single 33.x entry
mvn -q -DskipTests compile          # compile check
stripe listen --forward-to localhost:4242/webhook
stripe trigger payment_intent.succeeded
stripe trigger invoice.paid
```

**Critical limits and defaults** (stripe-java 33.x):

| Resource | Limit / Default | Source |
|---|---|---|
| Connect timeout | 30 000 ms (30 s) | `Stripe.java` DEFAULT_CONNECT_TIMEOUT |
| Read timeout | 80 000 ms (80 s) | `Stripe.java` DEFAULT_READ_TIMEOUT |
| SDK auto-retries | 2 (default) | `Stripe.java` maxNetworkRetries |
| Webhook timestamp tolerance | 300 s (5 min) | `Webhook.java` DEFAULT_TOLERANCE |
| Amount unit | Integer minor units | Stripe currencies docs |

Source: [`Stripe.java`](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/Stripe.java) · [`Webhook.java`](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/net/Webhook.java) (checked 2026-07-23)

---

## Blueprints Directory Structure

```
.claude/skills/integrating-stripe-payments-java/
├── SKILL.md                        <- This file (summary + guardrails, <500 lines)
└── blueprints/
    ├── always-do-patterns.md       <- ✅ Full 33.x code for all 9 mandatory patterns
    ├── ask-first-decisions.md      <- ⚠️ Tradeoff matrices for 6 decision points
    ├── never-do-patterns.md        <- 🚫 7 anti-patterns with wrong/correct code side-by-side
    ├── integration-examples.md     <- PaymentIntent, Customer+Subscription, Webhook endpoint
    └── evaluation-scenarios.md     <- 4 evaluation scenarios (PaymentIntent, Subscription, Webhook, anti-pattern trap)
```

---

## External Resources

### Official Stripe Documentation (all checked 2026-07-23)
- [Stripe API reference (Java)](https://docs.stripe.com/api?lang=java)
- [Stripe Webhooks (Java)](https://docs.stripe.com/webhooks?lang=java)
- [Stripe webhook signatures](https://docs.stripe.com/webhooks/signature)
- [Stripe error handling (Java)](https://docs.stripe.com/error-handling?lang=java)
- [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- [Stripe PaymentIntents create (Java)](https://docs.stripe.com/api/payment_intents/create?lang=java)
- [Stripe PaymentIntents lifecycle](https://docs.stripe.com/payments/paymentintents/lifecycle)
- [Stripe Subscriptions create (Java)](https://docs.stripe.com/api/subscriptions/create?lang=java)
- [Stripe Prices API](https://docs.stripe.com/api/prices?lang=java)
- [Stripe expand](https://docs.stripe.com/expand)
- [Stripe pagination](https://docs.stripe.com/api/pagination)
- [Stripe rate limits](https://docs.stripe.com/rate-limits)
- [Stripe API versioning](https://docs.stripe.com/api/versioning)
- [Stripe API keys / restricted keys](https://docs.stripe.com/keys)
- [Stripe security guide / PCI compliance](https://docs.stripe.com/security/guide)
- [Stripe CLI](https://docs.stripe.com/stripe-cli) · [stripe trigger](https://docs.stripe.com/cli/trigger)

### Official GitHub (stripe/stripe-java, all checked 2026-07-23)
- [stripe-java README](https://github.com/stripe/stripe-java)
- [stripe-java CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md)
- [stripe-java releases](https://github.com/stripe/stripe-java/releases)
- [v33.0.0 release notes](https://github.com/stripe/stripe-java/releases/tag/v33.0.0)
- [`Stripe.java` (defaults)](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/Stripe.java)
- [`Webhook.java` (constructEvent overloads)](https://github.com/stripe/stripe-java/blob/master/src/main/java/com/stripe/net/Webhook.java)

### Registry
- [Maven Central — com.stripe:stripe-java](https://central.sonatype.com/artifact/com.stripe/stripe-java)

### Security & Compliance
- [Stripe restricted API keys](https://docs.stripe.com/keys#limit-access)
- [Stripe PCI compliance](https://docs.stripe.com/security/guide#validating-pci-compliance)
- [Stripe integration security](https://docs.stripe.com/security/guide)
