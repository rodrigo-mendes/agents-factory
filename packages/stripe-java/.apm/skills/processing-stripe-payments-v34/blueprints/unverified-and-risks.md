# Unverified Claims and Risks — stripe-java 34.0.0 (PAYMENTS)

Research date 2026-10-14. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **34.x is the current stable major** as of 2026-10-14; pre-releases `v34.1.0-alpha.1/-alpha.2/-beta.1` exist. Re-verify when starting a new project or after 30 days. Source: https://github.com/stripe/stripe-java/releases (checked 2026-10-14).
- **33.x is superseded** (last: 33.4.2, 2026-09-09). All 33.x payments patterns are treated as misinformation for a 34.x target. Do not apply 33.x guidance to 34.x code.
- Maven Central `<latest>/<release>` = `34.1.0-beta.1` (pre-release); stable GA pin `34.0.0` corroborated by GitHub releases "Latest" marker. Central.sonatype version table did not render at research time — re-verify via https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml if currency matters.
- `2026-09-30.endive` is pinned by default in 34.0.0; future 34.x minor releases may change this default. Audit pinned-version assumptions whenever upgrading minor releases.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Exact calendar year of the `v34.0.0` GitHub release tag (renders as "01 Oct" without year on the releases page) | (unverified) — CHANGELOG header date `2026-09-30` used as authoritative; human verification of calendar year required |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | `.setConfirm(true)` accessor on `PaymentIntentCreateParams` | (medium confidence) — inferred from `confirm` API param; not seen in a rendered 34.x Java snippet or Javadoc page |
| M2 | `.setCustomer("cus_…")` accessor on `PaymentIntentCreateParams` | (medium confidence) — inferred from `customer` API param; not seen in a rendered 34.x Java snippet or Javadoc page |
| M3 | `.setPaymentMethod("pm_…")` accessor on `PaymentIntentCreateParams` | (medium confidence) — inferred from `payment_method` API param; confirmed on `PaymentIntentConfirmParams` sample only, not Create |
| M4 | `.setCaptureMethod(...)` accessor on `PaymentIntentCreateParams` | (medium confidence) — inferred from `capture_method` API param; not seen in a rendered 34.x Java snippet |
| M5 | `.setSetupFutureUsage(...)` accessor on `PaymentIntentCreateParams` | (medium confidence) — inferred from `setup_future_usage` API param; not seen in a rendered 34.x Java snippet |
| M6 | `.setAmountToCapture(...)` accessor on `PaymentIntentCaptureParams` | (medium confidence) — inferred from `amount_to_capture` API param; not seen in a rendered 34.x Java snippet |
| M7 | `.setFinalCapture(...)` accessor on `PaymentIntentCaptureParams` | (medium confidence) — inferred from `final_capture` API param; not seen in a rendered 34.x Java snippet |
| M8 | Maven stable GA patch `34.0.0` is the only stable 34.x release | (medium confidence) — central.sonatype version table did not render; corroborated by GitHub releases "Latest" marker and `maven-metadata.xml` |

## Coverage Limits

| Tag | Item | Status |
|---|---|---|
| L1 | central.sonatype version table for `com.stripe:stripe-java` | (coverage limit) — versions page did not load 2026-10-14 (JS placeholder); stable coordinate corroborated via GitHub Releases + Maven `maven-metadata.xml` |
| L2 | Stripe Javadoc pages for `PaymentIntentCreateParams`, `PaymentIntentCaptureParams` | (coverage limit) — only the top-level Javadoc host `stripe.dev/stripe-java/` was verified to exist; individual param-class pages for accessor names were not individually loaded |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md Version Context — Maven stable pin corroboration | M8 |
| (medium confidence) | SKILL.md Ask-First row — `.setFinalCapture(false)` accessor name | M7 |
| (medium confidence) | SKILL.md Ask-First row — `.setSetupFutureUsage(...)` accessor name | M5 |
| (medium confidence) | SKILL.md Quick Reference row — medium-confidence accessor list | M1, M2, M3, M4, M5, M6, M7 |
| (medium confidence) | always-do-patterns.md §5 — `.setAmountToCapture(...)` inline comment | M6 |
| (medium confidence) | always-do-patterns.md §5 — `.setFinalCapture(false)` inline comment | M7 |
| (medium confidence) | evaluation-scenarios.md Scenario 2 — `.setCaptureMethod(...)` accessor | M4 |
| (medium confidence) | evaluation-scenarios.md Scenario 4 — `.setConfirm(true)`, `.setCustomer(...)`, `.setCaptureMethod(...)` | M1, M2, M4 |
| (unverified) | unverified-and-risks.md Unverified Items — release year of v34.0.0 | U1 |

## Source Bibliography

All sources are official (Stripe-owned or Maven official registry) and were fetched on **2026-10-14**.

1. **PaymentIntent — Create (Java)**
   https://docs.stripe.com/api/payment_intents/create?lang=java
   Used for: `client.v1().paymentIntents().create(...)`, `PaymentIntentCreateParams.builder()`,
   `.setAmount(2000L)`, `.setCurrency("usd")`, `AutomaticPaymentMethods` nested builder,
   `amount` minor-unit semantics and limits, `automatic_payment_methods`, `client_secret` scoping,
   `confirm`/`capture_method`/`setup_future_usage` API params, `allowed_/excluded_payment_method_types` replacement.

2. **PaymentIntent — Confirm (Java)**
   https://docs.stripe.com/api/payment_intents/confirm?lang=java
   Used for: `.setPaymentMethod("pm_card_visa")`, `.setReturnUrl(...)` (verified from sample),
   `client.v1().paymentIntents().confirm(id, params)`, status-transition semantics,
   `confirmation_method` automatic vs manual, confirm upper limit, `client_secret` scoping.

3. **PaymentIntent — Capture (Java)**
   https://docs.stripe.com/api/payment_intents/capture?lang=java
   Used for: `PaymentIntentCaptureParams.builder().build()`,
   `client.v1().paymentIntents().capture(id, params)`, `amount_to_capture`, `final_capture`
   (default `true`/multicapture semantics), 7-day auto-cancel, `requires_capture` status.

4. **PaymentIntent — Cancel (Java)**
   https://docs.stripe.com/api/payment_intents/cancel?lang=java
   Used for: `PaymentIntentCancelParams.builder().build()`,
   `client.v1().paymentIntents().cancel(id, params)`, cancelable statuses,
   `cancellation_reason` values, auto-refund on `requires_capture` cancel.

5. **stripe-java CHANGELOG**
   https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md
   (raw: https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md)
   Used for: 34.0.0 date `2026-09-30`; pinned API version `2026-09-30.endive`;
   ⚠️ breaks: `paymentMethodTypes` removal (PaymentIntentCreate/Confirm/Update + SetupIntent + checkout.Session);
   BLIK `setupFutureUsage` literal→enum; `countries` removal on FC filters.

6. **stripe-java Releases**
   https://github.com/stripe/stripe-java/releases
   Used for: `v34.0.0` "Latest" status; pre-releases `v34.1.0-alpha.1/-alpha.2/-beta.1`;
   last 33.x stable `33.4.2` (2026-09-09).

7. **Maven Central metadata**
   https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml
   Used for: `<latest>/<release>` = `34.1.0-beta.1`; stable `34.0.0` coordinate presence.

8. **central.sonatype — versions**
   https://central.sonatype.com/artifact/com.stripe/stripe-java/versions
   Attempted for independent patch confirmation; version table did not render (JS placeholder)
   — see Coverage Limits L1.

9. **Stripe Docs — Zero-decimal currencies**
   https://docs.stripe.com/currencies#zero-decimal
   Used for: zero-decimal currency minor-unit semantics for the `amount` field.

10. **Idempotent requests (cross-ref)**
    https://docs.stripe.com/api/idempotent_requests
    Cited as cross-reference anchor only; key-length rule and `RequestOptions` mechanics owned by
    `developing-stripe-java-core-v34`.

11. **stripe-java Javadoc**
    https://stripe.dev/stripe-java/
    Referenced as the verification target for medium-confidence accessor names (M1–M7);
    individual param-class pages were not individually loaded — see Coverage Limits L2.
