---
name: processing-stripe-payments-v34
description: "Implements Stripe Java SDK 34.x PAYMENTS: PaymentIntents create/confirm/capture/cancel, automatic payment methods, amounts in minor units. Use when building or migrating Java payment flows with stripe-java 34.0.0. Not for core/client bootstrap, webhooks, or billing."
---

# Processing Stripe Payments — PaymentIntents (v34)

> Version lock: every claim applies to **stripe-java 34.0.0** only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| stripe-java | 34.0.0 — current stable major; ≤33.x superseded | https://github.com/stripe/stripe-java/releases |
| Pinned Stripe API version | `2026-09-30.endive` (SDK default for `Stripe-Version` header) | https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md |
| Scope | PAYMENTS ONLY — `PaymentIntents` create / confirm / capture / cancel | |
| Client accessor | `client.v1().paymentIntents()` — `StripeClient` owned by `developing-stripe-java-core-v34` | https://docs.stripe.com/api/payment_intents/create?lang=java |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- 34.x is the current stable; 33.x superseded 2026-09-09 (last: 33.4.2). ([source](https://github.com/stripe/stripe-java/releases))
- Pre-releases 34.1.0-alpha.1 / -alpha.2 / -beta.1 exist; do not pin them. ([source](https://github.com/stripe/stripe-java/releases))
- Maven Central `<latest>/<release>` = `34.1.0-beta.1` (pre-release); stable GA pin remains `34.0.0`. (medium confidence — central.sonatype version table did not render at research time)

**Version lock:** this skill locks to the **34.x major line** (suffix `-v34`). A new major (35.x) is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [34.0.0 Breaking Changes (PAYMENTS)](#3400-breaking-changes-payments)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `client.v1().paymentIntents().*` with typed `*Params.builder()` classes** — the legacy static `PaymentIntent.create(...)` style belongs to the older usage model ([create](https://docs.stripe.com/api/payment_intents/create?lang=java), fetched 2026-10-14). See [patterns](./blueprints/always-do-patterns.md#1-service-accessor).
- **Compute `amount` server-side in minor units as `Long`** — `2000L` = $20.00 USD; supports zero-decimal currencies ([create](https://docs.stripe.com/api/payment_intents/create?lang=java), [currencies](https://docs.stripe.com/currencies#zero-decimal), fetched 2026-10-14). See [patterns](./blueprints/always-do-patterns.md#2-amount-in-minor-units).
- **Enable `AutomaticPaymentMethods.setEnabled(true)` and deliver `client_secret` to the client SDK** for payment completion ([create](https://docs.stripe.com/api/payment_intents/create?lang=java), fetched 2026-10-14). See [patterns](./blueprints/always-do-patterns.md#3-automatic-payment-methods-recommended-default).
- **Send an idempotency key on every create/confirm/capture/cancel POST** — the ≤255-char rule and `RequestOptions` mechanics are owned by `developing-stripe-java-core-v34`; cross-reference it, do not re-derive ([Idempotent requests](https://docs.stripe.com/api/idempotent_requests), fetched 2026-10-14).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| `capture_method = manual` | Separate auth/capture; uncaptured intents auto-cancel after **7 days** by default ([capture](https://docs.stripe.com/api/payment_intents/capture?lang=java)) | "Should capture be separate from authorization? Plan a capture job before day 7." |
| `final_capture = false` multicapture | Keeps remaining funds for future partial captures; availability-gated ([capture](https://docs.stripe.com/api/payment_intents/capture?lang=java)); accessor `.setFinalCapture(false)` (medium confidence — verify in 34.0.0 Javadoc) | "Is multicapture enabled on this Stripe account? Verify before use." |
| `setup_future_usage` saved-card flows | Triggers SCA/compliance checks; accessor `.setSetupFutureUsage(...)` (medium confidence — verify in 34.0.0 Javadoc) ([create](https://docs.stripe.com/api/payment_intents/create?lang=java)) | "Does this flow save the card for future use? Confirm SCA compliance and accessor name." |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| `.setPaymentMethodTypes(...)` on `PaymentIntentCreateParams` / `PaymentIntentConfirmParams` — **removed in 34.0.0** ([CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md)) | Use `allowed_payment_method_types` / `excluded_payment_method_types`, or rely on `automatic_payment_methods` |
| BLIK `setupFutureUsage` as a string literal `"none"` in 34.x — **enum only** ([CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md)) | Use the generated enum type; recompile against 34.0.0 |
| Trust a client-supplied `amount` total ([create](https://docs.stripe.com/api/payment_intents/create?lang=java)) | Compute amount server-side from your own product/price catalog |
| Log or expose `client_secret` beyond the single checkout session ([confirm](https://docs.stripe.com/api/payment_intents/confirm?lang=java)) | Scope `client_secret` delivery via TLS to the specific checkout session only |

## Quick Reference

Sources fetched 2026-10-14.

| Aspect | Value | Source |
|---|---|---|
| Create | `client.v1().paymentIntents().create(params)` | https://docs.stripe.com/api/payment_intents/create?lang=java |
| Confirm | `client.v1().paymentIntents().confirm(id, params)` | https://docs.stripe.com/api/payment_intents/confirm?lang=java |
| Capture | `client.v1().paymentIntents().capture(id, params)` | https://docs.stripe.com/api/payment_intents/capture?lang=java |
| Cancel | `client.v1().paymentIntents().cancel(id, params)` | https://docs.stripe.com/api/payment_intents/cancel?lang=java |
| Return type (all) | `com.stripe.model.PaymentIntent` | https://docs.stripe.com/api/payment_intents/create?lang=java |
| Amount type | `Long` in minor units (e.g. `2000L` = $20.00 USD) | https://docs.stripe.com/api/payment_intents/create?lang=java |
| Amount max | 8 digits (`99999999`) | https://docs.stripe.com/api/payment_intents/create?lang=java |
| Auto-cancel (uncaptured) | 7 days after creation (default) | https://docs.stripe.com/api/payment_intents/capture?lang=java |
| Cancelable statuses | `requires_payment_method`, `requires_capture`, `requires_confirmation`, `requires_action`, `processing` | https://docs.stripe.com/api/payment_intents/cancel?lang=java |
| Verified Create accessors | `.setAmount(2000L)`, `.setCurrency("usd")`, `AutomaticPaymentMethods.builder().setEnabled(true)` | https://docs.stripe.com/api/payment_intents/create?lang=java |
| Verified Confirm accessors | `.setPaymentMethod("pm_card_visa")`, `.setReturnUrl(...)` on `PaymentIntentConfirmParams` | https://docs.stripe.com/api/payment_intents/confirm?lang=java |
| Medium-confidence accessors | `.setConfirm(true)`, `.setCustomer(...)`, `.setCaptureMethod(...)`, `.setSetupFutureUsage(...)`, `.setAmountToCapture(...)`, `.setFinalCapture(...)` — verify in Javadoc | https://stripe.dev/stripe-java/ |

## 34.0.0 Breaking Changes (PAYMENTS)

Source: [CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md), fetched 2026-10-14.

| # | Break | Impact | Migration |
|---|---|---|---|
| 1 | **`paymentMethodTypes` removed** on `PaymentIntentCreateParams`, `PaymentIntentConfirmParams` (and `Update`, `SetupIntent*`, `checkout.Session*`) | `.setPaymentMethodTypes(...)` no longer compiles | Use `allowed_payment_method_types` / `excluded_payment_method_types`, or `automatic_payment_methods` |
| 2 | **BLIK `setupFutureUsage` literal→enum** on `PaymentIntent.payment_method_options.blik` and `PaymentIntentConfirmParams…blik.setupFutureUsage` | String literal `"none"` no longer compiles | Use the generated enum type; recompile against 34.0.0 |
| 3 | **`countries` removed** on `financialconnections.Session.filters` | Only affects flows that build Financial Connections sessions (e.g. `us_bank_account`); pure card flows unaffected | Drop `.setCountries(...)` on FC session filters |

Rows 1–2 surface as **compile errors** when upgrading a ≤33.x payments integration to 34.0.0. Audit every `.setPaymentMethodTypes` call site and any BLIK `setupFutureUsage` handling before upgrading.

## External Resources

All fetched 2026-10-14.

- PaymentIntent — Create (Java): https://docs.stripe.com/api/payment_intents/create?lang=java
- PaymentIntent — Confirm (Java): https://docs.stripe.com/api/payment_intents/confirm?lang=java
- PaymentIntent — Capture (Java): https://docs.stripe.com/api/payment_intents/capture?lang=java
- PaymentIntent — Cancel (Java): https://docs.stripe.com/api/payment_intents/cancel?lang=java
- stripe-java CHANGELOG: https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md
- stripe-java Releases: https://github.com/stripe/stripe-java/releases
- Stripe Javadoc (34.x): https://stripe.dev/stripe-java/
- Zero-decimal currencies: https://docs.stripe.com/currencies#zero-decimal
- Idempotent requests (cross-ref): https://docs.stripe.com/api/idempotent_requests
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
