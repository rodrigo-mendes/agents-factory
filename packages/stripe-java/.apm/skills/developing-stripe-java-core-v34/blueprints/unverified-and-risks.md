# Unverified Claims and Risks — stripe-java 34.0.0 (CORE)

Research date 2026-10-14. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **34.x is the current stable major** as of 2026-10-14; the SDK moves fast (GitHub Releases shows
  alpha/beta pre-releases for 34.1.0 as of research date). Re-verify when starting a new project
  or after 30 days. Source: https://github.com/stripe/stripe-java/releases (checked 2026-10-14).
- **33.x is superseded** (last: 33.4.2, 2026-09-09). All 33.x patterns are treated as misinformation
  for a 34.x target. Do not apply 33.x guidance to 34.x code.
- `2026-09-30.endive` is pinned by default in 34.0.0; future 34.x minor releases may change this
  default. Audit pinned-version assumptions whenever upgrading minor releases.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | `Stripe.apiKey` field removal vs. retention-but-deprecated in 34.0.0 | (unverified) — not individually checked against 34.0.0 Javadoc; README omits it for new code |
| U2 | Prior 33.x default pinned API version value | (unverified) — only the 34.0.0 value `2026-09-30.endive` was confirmed |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Exact `RequestOptions` setter name for per-request `Stripe-Version` override in 34.0.0 | (medium confidence) — README illustrates the header but does not name the 34.0.0 setter method |
| M2 | Return types of `StripeException` accessors (`getStatusCode()`, etc.) | (medium confidence) — from docs example code, not enumerated against Javadoc |

## Coverage Limits

| Tag | Item | Status |
|---|---|---|
| L1 | Maven Central publish timestamp for 34.0.0 | (coverage limit) — versions page did not load 2026-10-14; existence corroborated via GitHub Releases + docs.stripe.com |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Never-Do row — `Stripe.apiKey` removal-vs-deprecation status | U1 |
| (unverified) | never-do-patterns.md §1 — `Stripe.apiKey` field status | U1 |
| (medium confidence) | SKILL.md Ask-First row — per-request `Stripe-Version` setter name | M1 |
| (medium confidence) | never-do-patterns.md §4 — `Stripe-Version` setter name | M1 |
| (medium confidence) | always-do-patterns.md — `StripeException` accessor return types | M2 |

## Source Bibliography

All sources are official (Stripe-owned) and were fetched on **2026-10-14**.

1. **GitHub — stripe/stripe-java Releases**
   https://github.com/stripe/stripe-java/releases
   Used for: v34.0.0 "Latest" status, pre-release list, last 33.x stable 33.4.2.

2. **GitHub — stripe/stripe-java CHANGELOG.md**
   https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md
   Used for: pinned API version `2026-09-30.endive`, breaking-change list, `STRIPE_SUPPRESS_NOTICES` (#2293),
   account-scoping fix (#2294), no core class removals/renames.

3. **GitHub — stripe/stripe-java README.md**
   https://github.com/stripe/stripe-java/blob/master/README.md
   Used for: StripeClient constructor and builder; `client.v1()` namespace; Java baseline (8+ runtime,
   LTS 8/11/17/21/25, build JDK 17); `RequestOptions`; `setMaxNetworkRetries`; timeouts (ms);
   telemetry (`Stripe.enableTelemetry`); `Stripe.setAppInfo`; `networkaddress.cache.ttl=60`.

4. **Stripe Javadoc — com.stripe.exception package summary**
   https://stripe.dev/stripe-java/com/stripe/exception/package-summary.html
   Used for: exact 34.0.0 exception class names/casing (13 classes including `ApiException`/`ApiConnectionException`).

5. **Stripe Docs — Development environment / Java quickstart**
   https://docs.stripe.com/get-started/development-environment?lang=java
   Used for: `com.stripe:stripe-java:34.0.0`, `new StripeClient(...)`, `stripeClient.v1()`.

6. **Stripe Docs — Error handling (Java)**
   https://docs.stripe.com/error-handling?lang=java
   Used for: exception taxonomy, catch-block example, accessors, idempotency key 255 chars.

7. **Stripe Docs — Idempotent requests (Java)**
   https://docs.stripe.com/api/idempotent_requests?lang=java
   Used for: idempotency key max 255 chars, `Idempotency-Key` header, POST-only, 24h retention,
   UUID v4 recommendation, `IdempotencyException` on param mismatch.

8. **Stripe Docs — Advanced / low-level error handling (Java)**
   https://docs.stripe.com/error-low-level?lang=java
   Used for: StripeClient defaults to zero retries, `setMaxNetworkRetries(2)` builder example,
   exponential backoff, `Stripe-Should-Retry`, `Idempotent-Replayed: true`.

9. **Maven Central (Sonatype) — com.stripe:stripe-java**
   https://central.sonatype.com/artifact/com.stripe/stripe-java
   Used for: artifact coordinates corroboration only. (M3: versions page did not load; existence
   corroborated via sources 1 and 5.)
