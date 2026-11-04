# Research — Stripe Java SDK (PAYMENTS unit) — v34.x

| Metadata | Value |
|---|---|
| **Artifact** | `com.stripe:stripe-java` — PAYMENTS unit (PaymentIntents lifecycle) |
| **Target_Version** | `34.0.0` (exact; latest **stable** 34.x) |
| **Research_Date** | 2026-10-14 |
| **Pinned_API_Version** | `2026-09-30.endive` (set by the 34.0.0 release) — [CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) |
| **Support_Status** | Current stable. `34.1.0` exists **only** as pre-releases (`-alpha.1`, `-alpha.2`, `-beta.1`) — not GA — [releases](https://github.com/stripe/stripe-java/releases). `≤ 33.x` superseded → migration-only. |
| **Primary client** | `com.stripe.StripeClient` → `client.v1().paymentIntents()` |
| **Scope** | PAYMENTS ONLY — PaymentIntents create / confirm / capture / cancel. Core/client bootstrap, webhooks, and billing are **separate units** (referenced, not duplicated). |

> **Version Absolutism.** This document pins **34.0.0**. Patterns from `≤ 33.x` are treated as
> misinformation for new code and appear only as migration notes. The 34.1.0 line is pre-release
> and MUST NOT be adopted as stable.

---

## 0. Version & Release Verification

- **Latest stable 34.x = `34.0.0`**, marked "Latest" on the GitHub releases page; released 2026-10-01 (page) / dated `2026-09-30` in the CHANGELOG header — [releases](https://github.com/stripe/stripe-java/releases), [CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md).
- **No stable 34.x patch beyond 34.0.0.** Visible 34.x artifacts above 34.0.0 are all pre-release: `v34.1.0-alpha.1`, `v34.1.0-alpha.2`, `v34.1.0-beta.1` — [releases](https://github.com/stripe/stripe-java/releases).
- **Maven Central metadata** (`maven-metadata.xml`) reports `<latest>` and `<release>` = `34.1.0-beta.1`, `lastUpdated 2026-10-08` — but these point at a **beta** build. The latest **GA/stable** coordinate for production use remains `34.0.0` — [maven-metadata.xml](https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml). `(medium confidence on exact patch currency: re-verify central.sonatype listing, which failed to render a version table at research time — see Gaps.)`
- **Pinned Stripe API version for 34.0.0 = `2026-09-30.endive`**: "This release changes the pinned API version to `2026-09-30.endive`." — [CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md).

**Maven coordinate (stable):**
```xml
<dependency>
  <groupId>com.stripe</groupId>
  <artifactId>stripe-java</artifactId>
  <version>34.0.0</version>
</dependency>
```
Source: [maven-metadata.xml](https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml), [central.sonatype](https://central.sonatype.com/artifact/com.stripe/stripe-java/versions).

---

## 1. PaymentIntents — Client Entry Point

All PAYMENTS operations route through the modern `StripeClient` service graph:
`client.v1().paymentIntents()`. The core/client unit owns `StripeClient` construction (API key,
config); this unit only consumes it.

| Operation | Method chain | Params class | Source |
|---|---|---|---|
| Create | `client.v1().paymentIntents().create(params)` | `PaymentIntentCreateParams` | [create](https://docs.stripe.com/api/payment_intents/create?lang=java) |
| Confirm | `client.v1().paymentIntents().confirm(id, params)` | `PaymentIntentConfirmParams` | [confirm](https://docs.stripe.com/api/payment_intents/confirm?lang=java) |
| Capture | `client.v1().paymentIntents().capture(id, params)` | `PaymentIntentCaptureParams` | [capture](https://docs.stripe.com/api/payment_intents/capture?lang=java) |
| Cancel | `client.v1().paymentIntents().cancel(id, params)` | `PaymentIntentCancelParams` | [cancel](https://docs.stripe.com/api/payment_intents/cancel?lang=java) |

Returned object type: `com.stripe.model.PaymentIntent` in every case.

> ✅ **Always-Do.** Use the `client.v1().paymentIntents()…` service accessor. The legacy static
> `PaymentIntent.create(...)` style belongs to the older usage model; prefer the `StripeClient`
> graph shown in the official 34.x Java samples — [create](https://docs.stripe.com/api/payment_intents/create?lang=java).

---

## 2. Create a PaymentIntent

**Official 34.x Java sample** (quoted verbatim) — [create](https://docs.stripe.com/api/payment_intents/create?lang=java):
```java
StripeClient client = new StripeClient("<<YOUR_SECRET_KEY>>");

PaymentIntentCreateParams params =
  PaymentIntentCreateParams.builder()
    .setAmount(2000L)
    .setCurrency("usd")
    .setAutomaticPaymentMethods(
      PaymentIntentCreateParams.AutomaticPaymentMethods.builder()
        .setEnabled(true)
        .build()
    )
    .build();

PaymentIntent paymentIntent = client.v1().paymentIntents().create(params);
```

Key verified accessors / parameters:

| Param (API) | Java builder accessor | Notes | Source |
|---|---|---|---|
| `amount` (integer, **required**) | `.setAmount(2000L)` | Minor units (smallest currency unit): 2000 = $20.00 USD. Min $0.50 US equiv; supports up to 8 digits. | [create](https://docs.stripe.com/api/payment_intents/create?lang=java) |
| `currency` (enum, **required**) | `.setCurrency("usd")` | Lowercase ISO-4217. | [create](https://docs.stripe.com/api/payment_intents/create?lang=java) |
| `automatic_payment_methods` | `.setAutomaticPaymentMethods(AutomaticPaymentMethods.builder().setEnabled(true).build())` | Nested builder `PaymentIntentCreateParams.AutomaticPaymentMethods`. | [create](https://docs.stripe.com/api/payment_intents/create?lang=java) |
| `confirm` (boolean, default `false`) | `.setConfirm(true)` `(medium confidence — accessor inferred from param; verify in 34.x Javadoc)` | `true` = create+confirm in one call; unlocks Confirm-API params. | [create](https://docs.stripe.com/api/payment_intents/create?lang=java) |
| `customer` (string) | `.setCustomer("cus_…")` `(medium confidence — accessor inferred; verify Javadoc)` | Required alongside a customer-attached `payment_method`. | [create](https://docs.stripe.com/api/payment_intents/create?lang=java) |
| `payment_method` (string) | `.setPaymentMethod("pm_…")` `(medium confidence — accessor inferred; verify Javadoc)` | Attach a PaymentMethod id. | [create](https://docs.stripe.com/api/payment_intents/create?lang=java) |
| `capture_method` (enum) | `.setCaptureMethod(...)` `(medium confidence — accessor inferred; verify Javadoc)` | `automatic` / `automatic_async` (default) / `manual`. | [create](https://docs.stripe.com/api/payment_intents/create?lang=java) |
| `setup_future_usage` (enum) | `.setSetupFutureUsage(...)` `(medium confidence — accessor inferred; verify Javadoc)` | Enum `off_session` / `on_session`. | [create](https://docs.stripe.com/api/payment_intents/create?lang=java) |

> Only `setAmount`, `setCurrency`, and the `AutomaticPaymentMethods` nested builder are quoted
> directly from the official Java sample. Accessors tagged `(medium confidence)` are the
> conventional stripe-java camelCase form of a documented API parameter but were **not** seen in a
> rendered 34.x Java snippet or Javadoc page during this pass — confirm against the
> [stripe-java Javadoc](https://stripe.dev/stripe-java/) or the `v34.0.0` tag before codifying.

### Amounts — minor units (server-derived)
`amount` is "a positive integer representing how much to charge in the smallest currency unit
(e.g., 100 cents to charge $1.00 or 100 to charge ¥100, a zero-decimal currency)." Minimum is
$0.50 US or equivalent; values support up to eight digits (max `99999999`) — [create](https://docs.stripe.com/api/payment_intents/create?lang=java), [currencies / zero-decimal](https://docs.stripe.com/currencies#zero-decimal).

> ✅ **Always-Do.** Derive the amount **server-side** in minor units; never trust a client-supplied
> total. Use `Long` (`2000L`) to avoid 32-bit overflow on large zero-decimal amounts — the official
> sample uses a `long` literal — [create](https://docs.stripe.com/api/payment_intents/create?lang=java).

---

## 3. Automatic Payment Methods & `client_secret`

- `automatic_payment_methods.enabled = true` lets the PaymentIntent accept the payment methods you
  enable in the Dashboard that are compatible with the intent's other params — [create](https://docs.stripe.com/api/payment_intents/create?lang=java).
- The response exposes `client_secret` (e.g. `pi_..._secret_...`) used by the client SDKs to
  complete the payment; for `confirmation_method = automatic`, payment may be completed client-side
  with the `client_secret` and no further server confirmation — [confirm](https://docs.stripe.com/api/payment_intents/confirm?lang=java).

> 🚫 **Never-Do.** Never log or expose the secret key; never leak `client_secret` to untrusted
> parties beyond the specific checkout session's client. `client_secret` is scoped to one
> PaymentIntent — [confirm](https://docs.stripe.com/api/payment_intents/confirm?lang=java).

---

## 4. Confirm a PaymentIntent

**Official 34.x Java sample** (verbatim) — [confirm](https://docs.stripe.com/api/payment_intents/confirm?lang=java):
```java
StripeClient client = new StripeClient("<<YOUR_SECRET_KEY>>");

PaymentIntentConfirmParams params =
  PaymentIntentConfirmParams.builder()
    .setPaymentMethod("pm_card_visa")
    .setReturnUrl("https://www.example.com")
    .build();

PaymentIntent paymentIntent =
  client.v1().paymentIntents().confirm("{{PAYMENT_INTENT_ID}}", params);
```
Verified accessors from the sample: `.setPaymentMethod(String)`, `.setReturnUrl(String)` on
`PaymentIntentConfirmParams.builder()`.

**Confirmation flow / status transitions** — [confirm](https://docs.stripe.com/api/payment_intents/confirm?lang=java):
- Requires additional auth → `requires_action` with `next_action`.
- Failure → `requires_payment_method` (or `canceled` once the confirm limit is reached).
- Success → `succeeded`, or `requires_capture` when `capture_method = manual`.
- `confirmation_method = automatic`: completable client-side via `client_secret`.
- `confirmation_method = manual`: every attempt must use the secret key; server must re-confirm
  after each required action.
- There is a variable upper limit on confirmations; exceeding it transitions the intent to `canceled`.

---

## 5. Capture a PaymentIntent (separate auth/capture)

**Official 34.x Java sample** (verbatim) — [capture](https://docs.stripe.com/api/payment_intents/capture?lang=java):
```java
StripeClient client = new StripeClient("<<YOUR_SECRET_KEY>>");

PaymentIntentCaptureParams params = PaymentIntentCaptureParams.builder().build();

PaymentIntent paymentIntent =
  client.v1().paymentIntents().capture("{{PAYMENT_INTENT_ID}}", params);
```
- Capture applies when `status = requires_capture` (i.e. created/confirmed with
  `capture_method = manual`) — [capture](https://docs.stripe.com/api/payment_intents/capture?lang=java).
- `amount_to_capture` (integer, optional): must be ≤ original amount; defaults to the full
  `amount_capturable` — [capture](https://docs.stripe.com/api/payment_intents/capture?lang=java).
- `final_capture` (boolean, default `true`): `false` keeps remaining uncaptured funds for future
  captures (**multicapture** only) — [capture](https://docs.stripe.com/api/payment_intents/capture?lang=java).
- Uncaptured PaymentIntents are canceled a set number of days (**7 by default**) after creation — [capture](https://docs.stripe.com/api/payment_intents/capture?lang=java).

---

## 6. Cancel a PaymentIntent

**Official 34.x Java sample** (verbatim) — [cancel](https://docs.stripe.com/api/payment_intents/cancel?lang=java):
```java
StripeClient client = new StripeClient("<<YOUR_SECRET_KEY>>");

PaymentIntentCancelParams params = PaymentIntentCancelParams.builder().build();

PaymentIntent paymentIntent =
  client.v1().paymentIntents().cancel("{{PAYMENT_INTENT_ID}}", params);
```
- Cancelable statuses: `requires_payment_method`, `requires_capture`, `requires_confirmation`,
  `requires_action`, and (rare) `processing` — [cancel](https://docs.stripe.com/api/payment_intents/cancel?lang=java).
- `cancellation_reason` (string, optional) values: `duplicate`, `fraudulent`,
  `requested_by_customer`, `abandoned` — [cancel](https://docs.stripe.com/api/payment_intents/cancel?lang=java).
- For `requires_capture`, the remaining `amount_capturable` is automatically refunded on cancel — [cancel](https://docs.stripe.com/api/payment_intents/cancel?lang=java).

---

## 7. ⚠️ 34.0.0 Breaking Changes — PAYMENTS-relevant

Source for all rows: [stripe-java CHANGELOG — 34.0.0](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md) (also mirrored on [releases](https://github.com/stripe/stripe-java/releases)).

| # | Change | Impact on payments code | Migration (from ≤33.x) |
|---|---|---|---|
| 1 | ⚠️ **Remove `paymentMethodTypes`** on `PaymentIntentConfirmParams`, `PaymentIntentCreateParams` (and `PaymentIntentUpdateParams`, `SetupIntentCreateParams`, `SetupIntentUpdateParams`, `checkout.SessionCreateParams`). | `.setPaymentMethodTypes(...)` no longer compiles on these params. | Switch to `allowed_payment_method_types` / `excluded_payment_method_types` (both now documented on create & confirm), or rely on `automatic_payment_methods`. The create/confirm param pages now list `allowed_payment_method_types` and `excluded_payment_method_types`, **not** `payment_method_types` as a request param — [create](https://docs.stripe.com/api/payment_intents/create?lang=java), [confirm](https://docs.stripe.com/api/payment_intents/confirm?lang=java). |
| 2 | ⚠️ **`setupFutureUsage` literal→enum.** `PaymentIntent.payment_method_options.blik.setupFutureUsage` changes from `literal('none')` to `enum('none'\|'off_session')` (same for `checkout.Session…bancontact.setupFutureUsage`). On the request side, `PaymentIntentConfirmParams.payment_method_options.blik.setupFutureUsage` similarly widens to an enum. | Code reading/writing the BLIK (and related) `setupFutureUsage` nested field must use the new enum type rather than a string literal. | Replace the literal string handling with the generated enum; recompile against 34.0.0. |
| 3 | ⚠️ **Remove `countries`** on `financialconnections.Session.filters` and `…SessionCreateParams.filters`. | Only relevant if a payment flow builds a Financial Connections session (e.g. us_bank_account). Pure card PaymentIntent flows are unaffected. | Drop `.setCountries(...)` on FC session filters. |

> ⚠️ **Migration Note.** Rows 1–2 are resource/param-level breaks that will surface as **compile
> errors** when a ≤33.x payments integration is bumped to 34.0.0. Audit every `.setPaymentMethodTypes`
> call site and any BLIK/`setupFutureUsage` nested-option handling before upgrading.

Non-payment 34.0.0 ⚠️ breaks (listed for completeness, out of this unit's scope):
`AccountRejectParams.reason` string→enum; `Charge.payment_method_details.card.mandate` string→expandable `Mandate`;
`InvoiceCreatePreviewParams…billingCycleAnchor` type change; subscription resume/update `billingCycleAnchor` type change;
`igic` removed from several `tax.Registration` options; `payto` removed from `PaymentMethodUpdateParams`;
`configurations` removed from several `v2.core.AccountLink` use cases — [CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md).

---

## 8. Idempotency (cross-reference — NOT re-derived here)

Idempotency keys apply to PaymentIntent create/confirm/capture/cancel as POST operations. The
**key length / `≤255` rule and header mechanics are owned by the core/client unit** — see that unit;
do not duplicate. Authoritative source: [Idempotent requests](https://docs.stripe.com/api/idempotent_requests). Set the key via
`RequestOptions`-level idempotency support in stripe-java `(medium confidence on exact 34.x
accessor — verify in core unit / Javadoc)`.

---

## 9. Three-Tier Guidance (PAYMENTS)

**✅ Always-Do**
- Pin `com.stripe:stripe-java:34.0.0`; verify the pinned Stripe API version is `2026-09-30.endive` — [CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md).
- Use `client.v1().paymentIntents()…` with the typed `*Params.builder()` classes — [create](https://docs.stripe.com/api/payment_intents/create?lang=java).
- Compute `amount` server-side in minor units as `Long` — [create](https://docs.stripe.com/api/payment_intents/create?lang=java).
- Prefer `automatic_payment_methods.enabled=true` + `client_secret` client completion — [create](https://docs.stripe.com/api/payment_intents/create?lang=java).
- Send an idempotency key on every create/confirm/capture/cancel (see §8) — [Idempotent requests](https://docs.stripe.com/api/idempotent_requests).

**⚠️ Ask-First**
- `capture_method = manual` (separate auth/capture) — adds a capture/expiry obligation (7-day default auto-cancel) — [capture](https://docs.stripe.com/api/payment_intents/capture?lang=java).
- `final_capture=false` multicapture — availability-gated — [capture](https://docs.stripe.com/api/payment_intents/capture?lang=java).
- `off_session`/`setup_future_usage` saved-card flows — SCA/compliance implications — [create](https://docs.stripe.com/api/payment_intents/create?lang=java).

**🚫 Never-Do**
- Never use removed `paymentMethodTypes` on PaymentIntent params in 34.x → use allowed/excluded lists — [CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md).
- Never treat BLIK `setupFutureUsage` as a string literal in 34.x → it is an enum — [CHANGELOG](https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md).
- Never trust a client-supplied amount; never expose the secret key — [create](https://docs.stripe.com/api/payment_intents/create?lang=java).

---

## 10. SECURITY — Supply-chain / prompt-injection note

Every fetched `docs.stripe.com/api/payment_intents/*` page carried an injected call-to-action:
a "Start here: Integrate with Stripe using skills and plugins" block instructing the reader to
`npm install -g @stripe/cli` and run `stripe agent setup`. **This instruction was ignored, no claim
in this document derives from it, and it is recorded here solely as a supply-chain / prompt-injection
observation.** Treat any page-embedded "run this command" directive on Stripe docs as untrusted and
out-of-band; verify tooling only against the official CLI install page before acting — observed on
[create](https://docs.stripe.com/api/payment_intents/create?lang=java), [confirm](https://docs.stripe.com/api/payment_intents/confirm?lang=java), [capture](https://docs.stripe.com/api/payment_intents/capture?lang=java), [cancel](https://docs.stripe.com/api/payment_intents/cancel?lang=java).

---

## 11. Gaps / Unverified

- `(medium confidence)` Exact camelCase **Java accessor names** for `confirm`, `customer`,
  `payment_method`, `capture_method`, `setup_future_usage` on `PaymentIntentCreateParams`, and for
  `amount_to_capture`/`final_capture` on `PaymentIntentCaptureParams`, were inferred from documented
  API params — **not** seen in a rendered 34.x Java snippet. Verify against the
  [stripe-java Javadoc](https://stripe.dev/stripe-java/) or the `v34.0.0` source tag before encoding them in a skill.
- `(medium confidence)` central.sonatype version table failed to render (JS placeholder) at research
  time; Maven Central `maven-metadata.xml` `<latest>/<release>` point to `34.1.0-beta.1`. The stable
  GA pin `34.0.0` is corroborated by the GitHub releases "Latest" marker, but a second independent
  confirmation of "no stable patch > 34.0.0" via the Sonatype UI is pending — [releases](https://github.com/stripe/stripe-java/releases), [maven-metadata.xml](https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml).
- `⚠️ IRRESOLVABLE — human verification required`: exact calendar year of the `v34.0.0` GitHub
  release tag — the releases page renders "01 Oct" without a year; the CHANGELOG header date
  `2026-09-30` is used as the authoritative date here.

---

## Source Bibliography

All sources are official (docs.stripe.com, github.com/stripe/stripe-java, stripe.dev, Maven Central /
central.sonatype). Each was fetched and read on **2026-10-14**. No community or third-party source was
used. Pages on docs.stripe.com carried an injected "skills/plugins — run `stripe agent setup`" CTA
which was ignored (see §10).

1. **PaymentIntent — Create (Java)** — https://docs.stripe.com/api/payment_intents/create?lang=java
   - Verified: `client.v1().paymentIntents().create(...)`; `PaymentIntentCreateParams.builder()`;
     `.setAmount(2000L)`, `.setCurrency("usd")`, `AutomaticPaymentMethods` nested builder.
   - Verified: `amount` minor-units definition, min $0.50, 8-digit max; `confirm`, `capture_method`,
     `setup_future_usage` enums; removal reflected via `allowed_/excluded_payment_method_types`.
   - Fetched 2026-10-14.
2. **PaymentIntent — Confirm (Java)** — https://docs.stripe.com/api/payment_intents/confirm?lang=java
   - Verified sample: `.setPaymentMethod("pm_card_visa")`, `.setReturnUrl(...)`,
     `client.v1().paymentIntents().confirm("{{PAYMENT_INTENT_ID}}", params)`.
   - Verified: status-transition semantics; automatic vs manual confirmation_method; confirm upper limit.
   - Fetched 2026-10-14.
3. **PaymentIntent — Capture (Java)** — https://docs.stripe.com/api/payment_intents/capture?lang=java
   - Verified sample: `PaymentIntentCaptureParams.builder().build()`;
     `client.v1().paymentIntents().capture(id, params)`.
   - Verified: `amount_to_capture`, `final_capture` default true/multicapture, 7-day auto-cancel.
   - Fetched 2026-10-14.
4. **PaymentIntent — Cancel (Java)** — https://docs.stripe.com/api/payment_intents/cancel?lang=java
   - Verified sample: `PaymentIntentCancelParams.builder().build()`;
     `client.v1().paymentIntents().cancel(id, params)`.
   - Verified: cancelable statuses; `cancellation_reason` values duplicate/fraudulent/requested_by_customer/abandoned.
   - Fetched 2026-10-14.
5. **stripe-java CHANGELOG** — https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md
   (raw: https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md)
   - Verified: 34.0.0 dated 2026-09-30; pinned API version `2026-09-30.endive`.
   - Verified ⚠️ breaks: remove `paymentMethodTypes` (PaymentIntentCreate/Confirm/Update + SetupIntent + checkout.Session);
     `setupFutureUsage` literal→enum (blik / bancontact); remove `countries` on financialconnections filters.
   - Fetched 2026-10-14.
6. **stripe-java Releases** — https://github.com/stripe/stripe-java/releases
   - Verified: `v34.0.0` marked "Latest"; `v34.1.0-alpha.1/-alpha.2/-beta.1` are pre-releases only.
   - Fetched 2026-10-14.
7. **Maven Central metadata** — https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml
   - Verified: `<latest>/<release>` = `34.1.0-beta.1`; lastUpdated 2026-10-08; `34.0.0` present as the stable GA.
   - Fetched 2026-10-14.
8. **central.sonatype — versions** — https://central.sonatype.com/artifact/com.stripe/stripe-java/versions
   - Attempted for independent patch confirmation; version table did not render (JS placeholder) — see Gaps.
   - Fetched 2026-10-14.
9. **Zero-decimal / currencies** — https://docs.stripe.com/currencies#zero-decimal
   - Supports the minor-unit amount semantics cited in §2.
   - Referenced from create page 2026-10-14.
10. **Idempotent requests (cross-ref, core unit owns the ≤255 rule)** — https://docs.stripe.com/api/idempotent_requests
    - Cited only to anchor §8; not re-derived in this PAYMENTS unit.
    - Referenced 2026-10-14.
11. **stripe-java Javadoc (pending verification of inferred accessors)** — https://stripe.dev/stripe-java/
    - To be used to confirm the `(medium confidence)` accessor names in §2 and §11.
    - Canonical host for the generated 34.x API reference (`PaymentIntentCreateParams`,
      `PaymentIntentConfirmParams`, `PaymentIntentCaptureParams`, `PaymentIntentCancelParams`).
    - Referenced 2026-10-14.

### Source hierarchy & freshness compliance

- **Tier 1 — Official docs (versioned):** entries 1–4, 9, 10 (docs.stripe.com, `?lang=java`).
- **Tier 1 — Official source repo / changelog:** entries 5, 6 (github.com/stripe/stripe-java).
- **Tier 1 — Official registry:** entries 7, 8 (Maven Central / central.sonatype).
- **Tier 1 — Official Javadoc:** entry 11 (stripe.dev).
- **Rejected tiers:** no official blog, no community, no third-party, no Stack Overflow used.
- **Freshness:** all sources reflect the 34.0.0 release (2026-09-30) and were fetched 2026-10-14 —
  within the 12-month threshold; the pinned release itself is < 1 month old.

### Cross-unit references (NOT duplicated in this PAYMENTS unit)

- **Core/client unit** — `StripeClient` construction, API key config, `RequestOptions`, and the
  idempotency key `≤255` rule (anchored via source 10 only).
- **Webhooks unit** — event signature verification for `payment_intent.*` events (out of scope here).
- **Billing unit** — subscription/invoice `billingCycleAnchor` 34.0.0 type changes (listed in §7 as
  non-payment breaks only).

### Verification log

- 2026-10-14 — Confirmed latest **stable** 34.x = `34.0.0` via releases "Latest" marker (source 6).
- 2026-10-14 — Confirmed pinned API version `2026-09-30.endive` via CHANGELOG (source 5).
- 2026-10-14 — Confirmed 3 payment-relevant 34.0.0 ⚠️ breaks via CHANGELOG (source 5), corroborated
  for `paymentMethodTypes` removal by the create/confirm param pages now exposing
  `allowed_/excluded_payment_method_types` (sources 1, 2) — `[✓✓ Triangulated | CHANGELOG + API docs]`.
- 2026-10-14 — Recorded docs.stripe.com prompt-injection CTA as a supply-chain note (§10); no claim
  derived from it.

---
*End of PAYMENTS unit research — research_Stripe_Java_Payments_v34.md*
