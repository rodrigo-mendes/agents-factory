---
name: developing-stripe-java-core-v34
description: "Implements Stripe Java SDK 34.x CORE/client: StripeClient, API-version pinning, idempotency keys, error handling, retries and timeouts. Use when building or migrating Java code with stripe-java 34.0.0. Not for payments, webhooks, or billing."
---

# Developing with Stripe Java SDK — CORE / Client (v34)

> Version lock: every claim applies to **stripe-java 34.0.0** only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| stripe-java | 34.0.0 — current stable major; ≤33.x superseded | https://github.com/stripe/stripe-java/releases |
| Pinned Stripe API version | `2026-09-30.endive` (SDK default for `Stripe-Version` header) | https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md |
| Java runtime | Java 8 minimum; LTS tested: 8 / 11 / 17 / 21 / 25 | https://github.com/stripe/stripe-java/blob/master/README.md |
| Maven artifact | `com.stripe:stripe-java:34.0.0` | https://docs.stripe.com/get-started/development-environment?lang=java |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- 34.x is the current stable; 33.x superseded 2026-10-01 (last: 33.4.2, 2026-09-09). ([source](https://github.com/stripe/stripe-java/releases))
- Pre-releases 34.1.0-alpha.1 / -beta.1 / -alpha.2 exist; do not pin them. ([source](https://github.com/stripe/stripe-java/releases))
- `2026-09-30.endive` is the 34.0.0 default; future 34.x minor releases may change this.

**Version lock:** this skill locks to the **34.x major line** (suffix `-v34`), not a single minor —
it tracks 34.x as it evolves (34.0.0 is the reference patch). A new major (35.x) is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Construct `StripeClient` via the constructor or builder** — the pre-v23 `Stripe.apiKey` global is not documented for new code ([README.md](https://github.com/stripe/stripe-java/blob/master/README.md), checked 2026-10-14). See [patterns](./blueprints/always-do-patterns.md#1-stripeclient-instantiation).
- **Pass `RequestOptions` with an idempotency key (≤ 255 chars) on every mutating POST call** ([docs.stripe.com/api/idempotent_requests?lang=java](https://docs.stripe.com/api/idempotent_requests?lang=java), checked 2026-10-14). See [patterns](./blueprints/always-do-patterns.md#2-idempotency-keys).
- **Catch `StripeException` (or a named subtype) around every API call** ([docs.stripe.com/error-handling?lang=java](https://docs.stripe.com/error-handling?lang=java), checked 2026-10-14). See [patterns](./blueprints/always-do-patterns.md#3-error-handling).
- **Use Javadoc casing for exception names: `ApiException` and `ApiConnectionException`** — docs.stripe.com prose mis-renders them as `APIException`/`APIConnectionException`; Javadoc is authoritative ([stripe.dev/stripe-java exception package](https://stripe.dev/stripe-java/com/stripe/exception/package-summary.html), checked 2026-10-14).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Retry count | Default is 0 retries; `setMaxNetworkRetries(n)` on builder (global) or `RequestOptions` (per request) ([docs.stripe.com/error-low-level?lang=java](https://docs.stripe.com/error-low-level?lang=java)); SDK auto-generates idempotency keys for retries. | "Should transient failures be retried? If yes, set `setMaxNetworkRetries(2)` or higher." |
| API-version override | Default pins `2026-09-30.endive`; per-request override via `RequestOptions` possible (setter name — (medium confidence); keep override and SDK aligned to avoid deserialization mismatch). | "Does this call need a different Stripe API version? Confirm the exact setter name against the 34.0.0 Javadoc first." |
| Telemetry | Request-latency telemetry sent by default; disable with `Stripe.enableTelemetry = false` ([README.md](https://github.com/stripe/stripe-java/blob/master/README.md)). | "Is Stripe telemetry acceptable for this deployment?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| `Stripe.apiKey = "sk_..."` global assignment (pre-v23 pattern, not documented for new code; [README.md](https://github.com/stripe/stripe-java/blob/master/README.md)) — removal-vs-deprecation status: see [unverified-and-risks.md](./blueprints/unverified-and-risks.md) U1 | `new StripeClient("sk_test_...")` or `StripeClient.builder().setApiKey(...).build()` |
| Idempotency keys > 255 chars ([docs.stripe.com/api/idempotent_requests?lang=java](https://docs.stripe.com/api/idempotent_requests?lang=java)) | UUID v4 (36 chars — well within the limit) |
| Override `Stripe-Version` without verifying SDK model compatibility | Rely on SDK default `2026-09-30.endive`; if you override, test response shapes against SDK models |
| Use `APIException` / `APIConnectionException` from docs.stripe.com prose in code ([stripe.dev Javadoc](https://stripe.dev/stripe-java/com/stripe/exception/package-summary.html)) | Use `ApiException` / `ApiConnectionException` |

## Quick Reference

Sources fetched 2026-10-14.

| Aspect | Value | Source |
|---|---|---|
| StripeClient constructor | `new StripeClient("sk_test_...")` | https://docs.stripe.com/get-started/development-environment?lang=java |
| Builder entry-point | `StripeClient.builder().setApiKey(...).setMaxNetworkRetries(2).build()` | https://docs.stripe.com/error-low-level?lang=java |
| Resource access namespace | `client.v1().products().create(params)` | https://github.com/stripe/stripe-java/blob/master/README.md |
| Idempotency key max | 255 characters | https://docs.stripe.com/api/idempotent_requests?lang=java |
| Idempotency key retention | At least 24 hours before possible pruning | https://docs.stripe.com/api/idempotent_requests?lang=java |
| Default network retries | 0 (StripeClient; does not inherit legacy global setting) | https://docs.stripe.com/error-low-level?lang=java |
| Timeout units | Milliseconds (`setConnectTimeout`, `setReadTimeout`) | https://github.com/stripe/stripe-java/blob/master/README.md |
| DNS cache TTL | JVM property `networkaddress.cache.ttl=60` (seconds) | https://github.com/stripe/stripe-java/blob/master/README.md |
| `STRIPE_SUPPRESS_NOTICES` | Set to `true` to suppress notices in test/sandbox (new in 34.0.0) | https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md |

## 33 to 34 Migration (Core)

Breaking changes in 34.0.0 are concentrated in resource-level parameter types (payments/billing/tax), **not** the CORE/client surface ([CHANGELOG.md](https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md), checked 2026-10-14):

- **Pinned API version changed to `2026-09-30.endive`** — audit code that assumed an older SDK default, and webhook endpoints created with the SDK default.
- `STRIPE_SUPPRESS_NOTICES` env var added for test/sandbox use.
- No `StripeClient` API/signature changes; no core class removals; Java minimum stays Java 8+.

Core upgrade from 33.x to 34.x is **low-risk** provided you audit API-version dependencies.

## External Resources

All fetched 2026-10-14.

- Stripe Java SDK releases: https://github.com/stripe/stripe-java/releases
- README.md: https://github.com/stripe/stripe-java/blob/master/README.md
- CHANGELOG.md: https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md
- Javadoc (34.0.0): https://stripe.dev/stripe-java/com/stripe/exception/package-summary.html
- Stripe Docs — Dev environment (Java): https://docs.stripe.com/get-started/development-environment?lang=java
- Stripe Docs — Error handling (Java): https://docs.stripe.com/error-handling?lang=java
- Stripe Docs — Idempotent requests (Java): https://docs.stripe.com/api/idempotent_requests?lang=java
- Stripe Docs — Low-level error handling (Java): https://docs.stripe.com/error-low-level?lang=java
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
