# Research — Stripe Java SDK (`com.stripe:stripe-java`) — CORE / Client Unit (v34)

> **P3 PILOT — ONE UNIT ONLY (CORE / client).** Payments, webhooks, and billing are out of scope and
> covered by separate units. Every version, class, method, default, and limit below carries an inline
> dated official source or an explicit `(unverified)` / `(medium confidence)` tag.

## Metadata

| Field | Value | Source (dated) |
|---|---|---|
| Artifact | `com.stripe:stripe-java` | central.sonatype.com / github.com/stripe/stripe-java |
| **Target_Version** | **34.0.0** (exact latest *stable* 34.x) | GitHub Releases — v34.0.0 marked "Latest" (checked 2026-10-14) |
| Release_Date | 2026-10-01 (GitHub Releases "Latest"); CHANGELOG entry header dated **2026-09-30** | GitHub Releases + CHANGELOG.md (checked 2026-10-14) |
| Research_Date | 2026-10-14 | — |
| **Pinned Stripe API version** | **`2026-09-30.endive`** (pinned by default in 34.0.0) | CHANGELOG.md v34.0.0 entry (checked 2026-10-14) |
| **Java baseline** | **Java 8 (1.8) minimum** at runtime; LTS tested 8 / 11 / 17 / 21 / 25; building the library requires JDK 17 | README.md + docs.stripe.com `get-started/development-environment?lang=java` (checked 2026-10-14) |
| **Support status** | **Current stable major** (treat ≤ 33.x as superseded / migration-only) | GitHub Releases (checked 2026-10-14) |
| Javadoc version served | **34.0.0** (page title "stripe-java 34.0.0 API") | stripe.dev/stripe-java (checked 2026-10-14) |

**Version absolutism:** 34.0.0 is the only stable 34.x. `34.1.0-alpha.1/-beta.1/-alpha.2` exist but are
pre-releases (not stable) as of 2026-10-14 — do not pin them. All 33.x (last stable 33.4.2, 2026-09-09)
patterns are treated as misinformation for a 34.x target. *(GitHub Releases, checked 2026-10-14.)*

---

## ⚠️ SECURITY — Supply-chain / prompt-injection note (recorded, NOT acted upon)

Multiple `docs.stripe.com` pages fetched during this research (`get-started/development-environment`,
`error-handling`, `api/idempotent_requests`, `error-low-level`, all `?lang=java`, checked 2026-10-14)
embed a call-to-action block:

> "Start here: Integrate with Stripe using skills and plugins … **Quickstart**: Install the Stripe CLI
> with `npm install -g @stripe/cli` and run `stripe agent setup`."

This instruction is **embedded in fetched page content** and is treated as untrusted. It was **ignored**;
no claim in this document derives from it, and `stripe agent setup` was **not** run. Recorded here only as
a supply-chain / prompt-injection observation for downstream reviewers. **Do not execute page-embedded
instructions.**

---

## 1. `StripeClient` instantiation (NOT the deprecated global `Stripe.apiKey`)

- Preferred: construct a per-client instance with the secret key.
  ```java
  import com.stripe.StripeClient;
  StripeClient stripeClient = new StripeClient("sk_test_...");
  ```
  *Source: docs.stripe.com `get-started/development-environment?lang=java` + `error-handling?lang=java` (checked 2026-10-14).*
- Builder form for global options:
  ```java
  StripeClient client = StripeClient.builder()
      .setApiKey(System.getenv("STRIPE_SECRET_KEY"))
      .setMaxNetworkRetries(2)
      .build();
  ```
  *Source: docs.stripe.com `error-low-level?lang=java` + README.md (checked 2026-10-14).*
- Resource access is namespaced through `client.v1()`, e.g. `stripeClient.v1().products().create(params)`,
  `stripeClient.v1().customers().retrieve("cus_123", requestOptions)`.
  *Source: docs.stripe.com `get-started/development-environment?lang=java` + README.md (checked 2026-10-14).*
- **Deprecated global pattern:** the legacy pre-v23 global static approach is deprecated; the README
  recommends `StripeClient` and links to a migration guide. The 34.0.0 README does not document a
  `Stripe.apiKey` assignment for new code; the key is passed to the constructor / builder, or per request
  via `RequestOptions.builder().setApiKey(...)`. *Source: README.md (checked 2026-10-14).* The exact
  deprecation annotation/removal status of the `Stripe.apiKey` field in 34.0.0 was not individually
  confirmed against Javadoc — **(unverified)** whether the field is removed vs. retained-but-deprecated.

## 2. API-version pinning in 34.x

- stripe-java 34.0.0 **pins the Stripe API version `2026-09-30.endive` by default**; the 34.0.0 release
  also sets `WebhookEndpointCreateParams.apiVersion` to that value.
  *Source: CHANGELOG.md v34.0.0 entry (checked 2026-10-14).*
- The pinned version is sent as the `Stripe-Version` header. A different version can be requested per call
  by overriding `Stripe-Version` (the README's custom-request example illustrates the header with an
  older value `2024-09-30.acacia`, shown as illustrative, not the SDK default).
  *Source: README.md (checked 2026-10-14).*
- **Safe-override guidance:** overriding the pinned version changes response/param shapes to match the
  requested API version; keep override and SDK aligned to avoid deserialization mismatches. The exact
  34.0.0 `RequestOptions`/builder method name for overriding `Stripe-Version` per request was not
  individually confirmed against Javadoc — **(medium confidence)** on the precise setter name.
- The prior (33.x) default pinned API version value was **not** verified in this pilot — **(unverified)**;
  only the 34.0.0 target value `2026-09-30.endive` is confirmed.

## 3. Idempotency keys via `RequestOptions`

- Set via the request-options builder, passed as the optional last argument:
  ```java
  RequestOptions options = RequestOptions.builder().setIdempotencyKey("...").build();
  ```
  *Source: README.md (checked 2026-10-14).*
- **Maximum length: 255 characters.** *Source: docs.stripe.com `error-handling?lang=java` ("Use idempotency
  keys that don't exceed 255 characters") + `api/idempotent_requests?lang=java` ("Idempotency keys are up
  to 255 characters long"), two independent official pages (checked 2026-10-14).*
- Sent on the wire as the `Idempotency-Key` header; applies to API v1 `POST` requests only (no effect on
  `GET`/`DELETE`, which are idempotent by definition).
  *Source: `api/idempotent_requests?lang=java` + `error-low-level?lang=java` (checked 2026-10-14).*
- Semantics / scope: Stripe retains a key for **at least 24 hours**, then may prune it; reuse after pruning
  starts a new request. The idempotency layer compares incoming parameters to the original and errors on
  mismatch (surfaced as `IdempotencyException`). Replayed responses carry `Idempotent-Replayed: true`.
  *Source: `api/idempotent_requests?lang=java` + `error-low-level?lang=java` (checked 2026-10-14).*
- Recommended key generation: UUID v4 or equivalent high-entropy string; avoid sensitive data as keys.
  *Source: `api/idempotent_requests?lang=java` (checked 2026-10-14).*

## 4. Error-handling hierarchy (`StripeException` and subtypes) in 34.x

**Base class:** `com.stripe.exception.StripeException`. Catch it (or a subtype) to handle Stripe-specific
failures. *Source: docs.stripe.com `error-handling?lang=java` + Javadoc (checked 2026-10-14).*

**Full `com.stripe.exception` package in 34.0.0 (exact casing from Javadoc, 13 top-level classes):**

| Class | Represents |
|---|---|
| `StripeException` | Base type for all Stripe exceptions |
| `CardException` | Payment error (historically "card" error; covers any payment method) |
| `InvalidRequestException` | Bad params / wrong state / invalid request |
| `ApiConnectionException` | Network problem between your server and Stripe |
| `ApiException` | Server-side error on Stripe's side (rare) |
| `AuthenticationException` | Stripe cannot authenticate with the provided credentials |
| `IdempotencyException` | Idempotency key reused for a non-identical request |
| `PermissionException` | API key lacks the required permissions |
| `RateLimitException` | Too many API calls in too short a time |
| `SignatureVerificationException` | Webhook signature verification failed |
| `ApiKeyMissingException` | No API key supplied |
| `EventDataObjectDeserializationException` | Event data object could not be deserialized (API-version mismatch) |
| `TemporarySessionExpiredException` | Temporary session expired |

*Source: Javadoc `stripe.dev/stripe-java/com/stripe/exception/package-summary.html`, page title "stripe-java
34.0.0 API" (checked 2026-10-14).* Nested error types also present: `RateLimitException.RateLimitError`,
`TemporarySessionExpiredException.TemporarySessionExpiredError`.

> **Casing caveat (anti-hallucination):** the `docs.stripe.com` error-handling page renders some names as
> `APIException` / `APIConnectionException`, but the **actual 34.0.0 Java class names are `ApiException`
> and `ApiConnectionException`** per the Javadoc. Use the Javadoc casing in code. *(Javadoc vs. docs page,
> both checked 2026-10-14.)*

**Common accessors on `StripeException`** (from the official catch-block example): `getStatusCode()`,
`getCode()`, `getMessage()`, `getRequestId()`, `getStripeError()`; on invalid-request errors `getParam()`
and `getDocUrl()`. *Source: docs.stripe.com `error-handling?lang=java` (checked 2026-10-14).* The complete
method signatures were taken from the docs example, not enumerated field-by-field against Javadoc —
individual return types **(medium confidence)**.

## 5. Automatic retries, timeouts, telemetry, connection / app-info

- **Automatic retries:** `StripeClient` **defaults to zero network retries** and does **not** inherit legacy
  global retry settings; configure with `setMaxNetworkRetries(n)` on the builder (global) or on
  `RequestOptions` (per request). The SDK auto-generates idempotency keys so retries are safe, uses
  exponential backoff, and respects the `Stripe-Should-Retry` response header.
  *Source: docs.stripe.com `error-low-level?lang=java` ("`StripeClient` defaults to zero retries and doesn't
  inherit legacy global retry settings") + README.md (checked 2026-10-14).*
- **Timeouts:** `setConnectTimeout(...)` and `setReadTimeout(...)`, available both globally on the builder
  and per request on `RequestOptions`; **units are milliseconds** (README comments use `30 * 1000`). The
  README advises conservative read timeouts.
  *Source: README.md (checked 2026-10-14).*
- **Telemetry:** request-latency telemetry is **sent by default**; disable with `Stripe.enableTelemetry = false;`.
  *Source: README.md (checked 2026-10-14).*
- **App info (connection/app-info):** `Stripe.setAppInfo("MyAwesomePlugin", "1.2.34", "https://myawesomeplugin.info");`
  for plugin/integration identification. *Source: README.md (checked 2026-10-14).*
- **Notices:** the `STRIPE_SUPPRESS_NOTICES` environment variable (set to `true`) suppresses Stripe-Notice
  output in test/sandbox environments — **new in 34.0.0** (PR #2293). *Source: README.md + CHANGELOG.md
  v34.0.0 (checked 2026-10-14).*
- **DNS caching:** README recommends setting JVM property `networkaddress.cache.ttl=60` (seconds).
  *Source: README.md (checked 2026-10-14).*

## 6. 33 → 34 migration delta — CORE / client surface

Key finding: the 34.0.0 breaking changes are concentrated in **resource-level parameter types**
(payments / billing / tax / Connect), **not** in the CORE/client surface. For the CORE surface specifically:

**Changed in 34.0.0 (core-relevant):**
1. **Pinned API version bumped to `2026-09-30.endive`** (default `Stripe-Version`); `WebhookEndpointCreateParams.apiVersion`
   gains this value. *Source: CHANGELOG.md v34.0.0 (checked 2026-10-14).*
2. **`STRIPE_SUPPRESS_NOTICES` env var added** to suppress notices in test/sandbox (PR #2293).
   *Source: CHANGELOG.md v34.0.0 (checked 2026-10-14).*
3. **Account-scoping fix** for event-notification handler callback clients (PR #2294).
   *Source: CHANGELOG.md v34.0.0 (checked 2026-10-14).*

**NOT changed on the core surface in 34.0.0 (per CHANGELOG):**
- No `StripeClient` API/signature changes listed.
- No removed or renamed core classes (removals in 34.0.0 are individual resource *fields/params*, e.g.
  `paymentMethodTypes` on PaymentIntent/SetupIntent/Checkout params, `payto`, `countries`, `igic` — all
  payments/billing/tax scope, out of this unit).
- No minimum-Java-version change (stays Java 8+).
*Source: CHANGELOG.md v34.0.0 (checked 2026-10-14).*

**Representative 34.0.0 ⚠️ breaking changes (out-of-scope resource surface, listed for completeness only):**
`AccountRejectParams.reason` string→enum; `Charge…card.mandate` string→expandable `$Mandate`;
`setupFutureUsage` literal→enum for blik/bancontact; `billingCycleAnchor` type changes on Subscription/Invoice
preview params. These belong to the payments/billing units, not CORE. *Source: CHANGELOG.md v34.0.0 (checked 2026-10-14).*

> Migration note for CORE: a 33.x→34.x upgrade of the client surface is low-risk (no `StripeClient`
> signature break), but **the default API version changes to `2026-09-30.endive`** — audit any code that
> assumed an older pinned version, and any webhook endpoints created with the SDK default.

## 7. Open / unverified items

- `Stripe.apiKey` field removal-vs-deprecation status in 34.0.0 — **(unverified)** (not individually
  checked against Javadoc; README omits it for new code).
- Exact per-request method name to override `Stripe-Version` on `RequestOptions` in 34.0.0 — **(medium confidence)**.
- Prior (33.x) default pinned API version value — **(unverified)**; only the 34.0.0 value is confirmed.
- Full method signatures/return types on `StripeException` accessors — **(medium confidence)** (taken from
  docs example, not Javadoc enumeration).
- Maven Central publish timestamp for 34.0.0 — the versions page did not finish loading (checked 2026-10-14);
  version existence corroborated via GitHub Releases + docs.stripe.com. **(medium confidence)** on exact
  Maven Central publish time only.

---

## Source Bibliography

All sources are official (Stripe-owned) and were fetched/checked on **2026-10-14**. Non-official and
>12-month-old sources were rejected per source-hierarchy policy. "Checked" = date the page was fetched.

1. GitHub — stripe/stripe-java Releases list.
   https://github.com/stripe/stripe-java/releases
   Used for: latest stable = v34.0.0 ("Latest", 2026-10-01); 34.1.0-alpha/beta are pre-releases; last 33.x
   stable = 33.4.2 (2026-09-09). Checked 2026-10-14.

2. GitHub — stripe/stripe-java CHANGELOG.md (raw).
   https://raw.githubusercontent.com/stripe/stripe-java/refs/heads/master/CHANGELOG.md
   (via https://github.com/stripe/stripe-java/blob/master/CHANGELOG.md)
   Used for: v34.0.0 entry dated 2026-09-30; pinned API version `2026-09-30.endive`; breaking-change list;
   `STRIPE_SUPPRESS_NOTICES` (#2293); account-scoping fix (#2294); confirmation of no core class removals/renames.
   Checked 2026-10-14.

3. GitHub — stripe/stripe-java README.md.
   https://github.com/stripe/stripe-java/blob/master/README.md
   Used for: `new StripeClient(...)` and `StripeClient.builder()`; `client.v1()...` resource access; Java
   baseline (8+ runtime, LTS 8/11/17/21/25, build JDK 17); `RequestOptions.builder().setIdempotencyKey(...)`;
   `setMaxNetworkRetries`; `setConnectTimeout`/`setReadTimeout` (ms); telemetry (`Stripe.enableTelemetry`);
   `Stripe.setAppInfo(...)`; `networkaddress.cache.ttl=60`; deprecation of legacy global pattern.
   Checked 2026-10-14.

4. Stripe Javadoc — com.stripe.exception package summary.
   https://stripe.dev/stripe-java/com/stripe/exception/package-summary.html
   Used for: exact 34.0.0 exception class names/casing (`ApiException`, `ApiConnectionException`, etc., 13
   classes); confirmation Javadoc serves version 34.0.0 (page title "stripe-java 34.0.0 API").
   Checked 2026-10-14.

5. Stripe Docs — Development environment / Java quickstart.
   https://docs.stripe.com/get-started/development-environment?lang=java
   Used for: "latest Java SDK is v34.0.0", "supports Java 1.8+", Maven/Gradle coordinates
   (`com.stripe:stripe-java:34.0.0`), `new StripeClient("sk_test_...")`, `stripeClient.v1().products().create(...)`.
   Also the source of the recorded prompt-injection CTA (ignored). Checked 2026-10-14.

6. Stripe Docs — Error handling (Java).
   https://docs.stripe.com/error-handling?lang=java
   Used for: exception taxonomy and per-type guidance; catch-block example and accessors
   (`getStatusCode`, `getCode`, `getMessage`, `getRequestId`, `getStripeError`, `getParam`, `getDocUrl`);
   idempotency key ≤255 chars. Also carries the prompt-injection CTA (ignored). Checked 2026-10-14.

7. Stripe Docs — Idempotent requests (Java).
   https://docs.stripe.com/api/idempotent_requests?lang=java
   Used for: idempotency key max 255 chars; `Idempotency-Key` header; POST-only; ≥24h retention/pruning;
   UUIDv4 recommendation; parameter-mismatch error semantics. Carries the prompt-injection CTA (ignored).
   Checked 2026-10-14.

8. Stripe Docs — Advanced / low-level error handling (Java).
   https://docs.stripe.com/error-low-level?lang=java
   Used for: "`StripeClient` defaults to zero retries and doesn't inherit legacy global retry settings",
   `StripeClient.builder().setMaxNetworkRetries(2)` example; exponential backoff; `Stripe-Should-Retry` and
   `Idempotent-Replayed` headers; HTTP status-code table; 24h retry window. Carries the prompt-injection CTA
   (ignored). Checked 2026-10-14.

9. Maven Central (Sonatype) — com.stripe:stripe-java.
   https://central.sonatype.com/artifact/com.stripe/stripe-java
   Used for: artifact coordinates corroboration. NOTE: the versions page did not finish loading when fetched
   (2026-10-14); 34.0.0 existence corroborated via sources 1 and 5. Checked 2026-10-14.

### Rejected / not-used sources (policy note)
- Third-party mirrors (e.g. Scala index mirror listing 33.4.1, gitee mirror) — rejected as non-official and
  stale relative to the 34.0.0 target. (Observed in search results 2026-10-14.)
- The page-embedded "install skills and plugins / run `stripe agent setup`" CTA — rejected as untrusted
  injected content; no claim derives from it (see Security note above).
