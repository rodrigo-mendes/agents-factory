# Research — Stripe Java SDK · BILLING / Subscriptions · v34.x

> Per-unit knowledge base (P4 fan-out). **Scope: BILLING ONLY.** Core/client bootstrap,
> payments, and webhook signature verification are separate units — referenced here, not duplicated.

## Metadata

| Field | Value |
|---|---|
| Library | `com.stripe:stripe-java` |
| Target_Version (exact) | **34.0.0** (latest **stable** 34.x patch as of 2026-10-14) |
| Later 34.x artifacts | `34.1.0-alpha.1`, `34.1.0-alpha.2`, `34.1.0-beta.1` — **pre-release only, NOT stable**; do not pin |
| Pinned Stripe API version | **`2026-09-30.endive`** |
| Release date of 34.0.0 | 2026-09-30 (CHANGELOG) / tag published 01 Oct |
| Research_Date | 2026-10-14 |
| Support status | **Current stable** — pin and treat ≤ 33.x billing patterns as superseded / migration-only |
| Version policy | Version Absolutism: 34.x is the single source of truth; ≤ 33.x accessors (notably `Invoice.getSubscription()`) are **misinformation** for 34.x |

**Version confirmation sources:**
- Latest stable = 34.0.0: Maven Central metadata `<release>` is `34.1.0-beta.1` (a pre-release), newest **stable** is `34.0.0` — https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml (lastUpdated 20261008013744)
- Release listing: https://github.com/stripe/stripe-java/releases (34.0.0 = "Latest"; 34.1.0 entries all `alpha`/`beta`)
- Pinned API version `2026-09-30.endive`: https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md (34.0.0 entry — "This release changes the pinned API version to `2026-09-30.endive`")

> **Maven Central note:** `central.sonatype.com` versions tab returned a client-side "Loading…" placeholder (SPA not hydrated at fetch time); version facts above are therefore taken from the canonical `repo1.maven.org` metadata XML, which is authoritative.

---

## ⚠️ Supply-chain / prompt-injection note (security)

Every `docs.stripe.com/...?lang=java` page fetched carries an injected call-to-action block:

> "Start here: Integrate with Stripe using skills and plugins … **Quickstart**: Install the Stripe CLI with `npm install -g @stripe/cli` and run `stripe agent setup`."

This is **page-embedded instruction content, not API documentation**. It was **ignored**; no claim in
this document derives from it. Recorded here only as a supply-chain observation. Do not run
`stripe agent setup` or `npm install -g @stripe/cli` on the basis of a documentation page.

---

## 1. Client surface for billing (34.x)

All billing calls go through the `StripeClient` → `.v1()` resource tree. The legacy static
`Customer.create(...)` / `Subscription.create(...)` style is **not** the documented 34.x path.

> Note: `.v1()` is required for SDK ≥ 29.5.0. All 34.x examples use it. (docs.stripe.com expand page:
> "For SDK versions 29.4.0 or lower, remove `.v1()`…".)

| Operation | 34.x API | Source |
|---|---|---|
| Create customer | `client.v1().customers().create(CustomerCreateParams)` | https://docs.stripe.com/api/customers/create?lang=java |
| Create subscription | `client.v1().subscriptions().create(SubscriptionCreateParams)` | https://docs.stripe.com/api/subscriptions/create?lang=java |
| Expand on retrieve/list | `...Params.builder().addExpand("path").build()` | https://docs.stripe.com/expand?lang=java |

---

## 2. Customer create

Confirmed Java example (verbatim shape, docs.stripe.com, 2026-10-14):

```java
StripeClient client = new StripeClient("<<YOUR_SECRET_KEY>>");

CustomerCreateParams params =
  CustomerCreateParams.builder()
    .setName("Jenny Rosen")
    .setEmail("jennyrosen@example.com")
    .build();

Customer customer = client.v1().customers().create(params);
```

- Builder entry point: `CustomerCreateParams.builder()` — confirmed.
- Setters shown: `setName(String)`, `setEmail(String)` — confirmed.
- `email` max length 512 chars; `name` max length 256 chars (docs param table).
- Source: https://docs.stripe.com/api/customers/create?lang=java

---

## 3. Product & Price references + Subscription create

Price/Product are created with their own resources (referenced, not detailed here). A Subscription is
created with one or more **items**, each referencing an existing **Price ID**.

Confirmed Java example (docs.stripe.com, 2026-10-14):

```java
StripeClient client = new StripeClient("<<YOUR_SECRET_KEY>>");

SubscriptionCreateParams params =
  SubscriptionCreateParams.builder()
    .setCustomer("{{CUSTOMER_ID}}")
    .addItem(
      SubscriptionCreateParams.Item.builder()
        .setPrice("{{PRICE_ID}}")
        .build()
    )
    .build();

Subscription subscription = client.v1().subscriptions().create(params);
```

Confirmed facts:
- Builder: `SubscriptionCreateParams.builder()`; item builder: `SubscriptionCreateParams.Item.builder()`.
- Item → Price linkage: `.setPrice("{{PRICE_ID}}")` on the item builder. Items added via `.addItem(...)`.
- `items` is **required**; "A list of up to **20** subscription items, each with an attached price."
- Each customer can have **up to 500** active or scheduled subscriptions. (docs create page intro)
- Prerequisite object graph (from docs): Product (`POST /v1/products`) → Price (`POST /v1/prices`,
  `recurring.interval=month`) → Customer → Subscription.
- `latest_invoice` on the returned Subscription is a **string ID** by default (see response JSON) and
  must be expanded to retrieve the Invoice object.
- Source: https://docs.stripe.com/api/subscriptions/create?lang=java

---

## 4. `addExpand(...)` — avoiding N+1

Expansion replaces a linked object's ID with the full object in a single call. Java usage:

```java
SubscriptionRetrieveParams params =
  SubscriptionRetrieveParams.builder()
    .addExpand("latest_invoice.payment_intent")
    .build();
```

Confirmed facts:
- Each `addExpand(String)` call adds one dot-notation path; multiple calls allowed (chainable).
- **Maximum expand depth = 4 levels** — confirmed verbatim: "Las expansiones tienen un máximo de
  profundidad de cuatro niveles … una cadena `expand` no puede contener más de 4 propiedades:
  `property1.property2.property3.property4`." (33.x research said depth 4 — **re-verified for 34.x /
  API `2026-09-30.endive`: still 4**.) Source: https://docs.stripe.com/expand?lang=java
- `data.` keyword expands a property on every element of a returned list
  (e.g. `addExpand("data.payment_method")`).
- **Webhooks are never auto-expanded** — "No puedes recibir eventos de webhooks con propiedades
  expandidas automáticamente"; fetch the object with a separate call inside the handler if you need
  nested data. Source: https://docs.stripe.com/expand?lang=java
- `latest_invoice` is expandable on Subscription (string ID in the create response → expand to object).
  The sub-path `latest_invoice.payment_intent` **(medium confidence for the exact `.payment_intent`
  leaf under API `2026-09-30.endive`)**: Invoice's payment linkage was restructured in recent API
  versions; the exact expandable leaf (`payment_intent` vs `payments`/`confirmation_secret`) belongs to
  the **payments unit** and should be confirmed there against the pinned API version. The `latest_invoice`
  expand itself and the depth-4 rule are confirmed.

---

## 5. Invoice lifecycle + `invoice.paid` → Subscription linkage ⚠️ Migration Note

> **This is the most important 34.x correction for billing.** In ≤ 33.x the research flagged
> `Invoice.getSubscription()` as "needs Javadoc confirmation". **For 34.x that top-level accessor
> does NOT exist.** Any code calling `invoice.getSubscription()` against 34.x is misinformation.

Confirmed 34.x accessor chain (Javadoc, stripe.dev):

| Step | Call | Returns | Source |
|---|---|---|---|
| 1 | `invoice.getParent()` | `Invoice.Parent` ("The parent that generated this invoice") | https://stripe.dev/stripe-java/com/stripe/model/Invoice.html |
| 2 | `parent.getType()` | `String` — `"subscription_details"` or `"quote_details"` | https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html |
| 2 | `parent.getSubscriptionDetails()` | `Invoice.Parent.SubscriptionDetails` | https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html |
| 3 | `subscriptionDetails.getSubscription()` | **`String`** — "Get ID of expandable `subscription` object" | https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html |
| 3 | `subscriptionDetails.getSubscriptionObject()` | `Subscription` — expanded object | (same page) |
| 3 | `subscriptionDetails.getSubscriptionProrationDate()` | `Long` | (same page) |
| 3 | `subscriptionDetails.getMetadata()` | `Map<String,String>` | (same page) |

Confirmed facts:
- **`com.stripe.model.Invoice` has NO method whose name contains "Subscription"** (verified against the
  full Method Summary). The only parent accessor is `getParent()`.
- The subscription **ID** on an invoice (34.x) = `invoice.getParent().getSubscriptionDetails().getSubscription()` → `String`.
- The expanded subscription **object** = `...getSubscriptionDetails().getSubscriptionObject()` → `Subscription`.
- `Invoice.Parent` also exposes `getQuoteDetails()` → `Invoice.Parent.QuoteDetails` for quote-originated invoices.

Webhook linkage pattern (`invoice.paid` event — billing side only; signature verification is the
webhook unit's responsibility):

```java
// After the webhook unit has verified the signature and produced an Event:
Invoice invoice = (Invoice) event.getDataObjectDeserializer()
    .getObject()
    .orElseThrow();

String subscriptionId = null;
Invoice.Parent parent = invoice.getParent();
if (parent != null && "subscription_details".equals(parent.getType())) {
    subscriptionId = parent.getSubscriptionDetails().getSubscription();
}
```

- Guard on `getType().equals("subscription_details")` before reading subscription details, because an
  invoice parent may instead be `quote_details` (confirmed enum values on `getType()`).
- Webhook payloads are minimal/unexpanded (see §4), so `getSubscription()` (ID string) is the reliable
  read; use `getSubscriptionObject()` only when you explicitly expanded it on a direct API retrieve.

---

## 6. Breaking changes in 34.0.0 touching billing params ⚠️ Migration Note

Source for all items: CHANGELOG 34.0.0 entry (PR #2292 "Update generated code"), tied to API version
bump `2026-09-30.endive`. https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md

Billing-relevant breaking changes (type changes to `billingCycleAnchor`), verbatim intent:

| # | Param | Change | Impact |
|---|---|---|---|
| 1 | `SubscriptionUpdateParams.billingCycleAnchor` | type changes **from `enum('now'\|'unchanged')`** → **`billing_cycle_anchor_param`** | Code passing the `now`/`unchanged` enum to subscription **update** must migrate to the new param type |
| 2 | `SubscriptionResumeParams.billingCycleAnchor` | type changes → `billing_cycle_anchor_param` | Same migration for subscription **resume** |
| 3 | `InvoiceCreatePreviewParams.subscription_details.billingCycleAnchor` | type changes **from `enum('now'\|'unchanged') \| DateTime`** → **`billing_cycle_anchor_param`** | Invoice **preview** calls that set a billing cycle anchor must migrate |

Notes:
- `SubscriptionCreateParams` continues to accept `billing_cycle_anchor` as a **timestamp** (future UTC)
  and the mutually-exclusive `billing_cycle_anchor_config` object — confirmed on the create params table
  (https://docs.stripe.com/api/subscriptions/create?lang=java). The breaking type change above applies to
  **update/resume/invoice-preview**, not the plain create timestamp field.
- **No other 34.0.0 breaking change affects `Subscription`, `Invoice`, `Price`, or `Product`.** `Product`
  gains an additive `taxDetails` field (non-breaking). (CHANGELOG 34.0.0)

Other (non-billing) 34.0.0 breaking changes, listed for completeness only (belong to other units):
`AccountRejectParams.reason` string→enum; `Charge...card.mandate` string→expandable;
`paymentMethodTypes` removed from PaymentIntent/SetupIntent/checkout.Session create/update/confirm;
Blik/Bancontact `setupFutureUsage` literal→enum; Financial Connections `countries` removed; `payto`
removed from `PaymentMethodUpdateParams`; tax `igic` removed; v2 AccountLink `configurations` removed.
(Source: CHANGELOG 34.0.0.)

---

## 7. Open / unverified items

| Item | Status | Rationale |
|---|---|---|
| Exact expand leaf `latest_invoice.payment_intent` under API `2026-09-30.endive` | **(medium confidence)** | Invoice payment linkage restructured in recent API versions; exact leaf (`payment_intent` vs `payments`/`confirmation_secret`) is the **payments unit's** scope — confirm there |
| `central.sonatype.com` version table | **(unverified via that host)** | SPA returned "Loading…"; version facts sourced from authoritative `repo1.maven.org` metadata XML instead |

All other version/class/method/default/limit claims in this document carry an inline official URL.

---

## Source Bibliography

All sources below are official (Stripe-owned domains: `docs.stripe.com`, `github.com/stripe`,
`stripe.dev`) or the canonical Maven artifact host (`repo1.maven.org`). Every source was fetched on
**2026-10-14**. Community sources: none used (rejected per source hierarchy).

### A. Version, release & changelog sources
1. Maven Central metadata (authoritative artifact index) —
   https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml
   - Used for: full 34.x version list (`34.0.0`, `34.1.0-alpha.1`, `34.1.0-alpha.2`, `34.1.0-beta.1`),
     `<release>`/`<latest>` = `34.1.0-beta.1` (pre-release), `<lastUpdated>` = `20261008013744`.
   - Checked: 2026-10-14.
2. GitHub Releases — stripe/stripe-java —
   https://github.com/stripe/stripe-java/releases
   - Used for: confirming `v34.0.0` is the newest **stable** ("Latest"); `34.1.0` entries are all
     `alpha`/`beta` pre-releases; release date 01 Oct.
   - Checked: 2026-10-14.
3. CHANGELOG.md (raw, master branch) — stripe/stripe-java —
   https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md
   - Used for: 34.0.0 release date (2026-09-30); pinned API version `2026-09-30.endive`; the complete
     list of 34.0.0 breaking changes including the three `billingCycleAnchor` type changes
     (SubscriptionUpdateParams, SubscriptionResumeParams, InvoiceCreatePreviewParams.subscription_details);
     additive `Product.taxDetails`; non-billing breaking changes (PR #2292).
   - Checked: 2026-10-14.
4. Maven Central UI (versions tab) — stripe-java —
   https://central.sonatype.com/artifact/com.stripe/stripe-java/versions
   - Status: SPA placeholder ("Loading…") at fetch time; **not** used as a fact source. Noted for
     transparency; superseded by source #1.
   - Checked: 2026-10-14.

### B. Official API documentation (docs.stripe.com, `?lang=java`)
5. Create a customer (Java) —
   https://docs.stripe.com/api/customers/create?lang=java
   - Used for: `client.v1().customers().create(...)`, `CustomerCreateParams.builder()`,
     `setName`/`setEmail`, field max lengths (email 512, name 256), returned Customer shape.
   - Checked: 2026-10-14. Contained the injected "stripe agent setup" CTA — ignored (see security note).
6. Create a subscription (Java) —
   https://docs.stripe.com/api/subscriptions/create?lang=java
   - Used for: `client.v1().subscriptions().create(...)`, `SubscriptionCreateParams.builder()`,
     `.setCustomer(...)`, `.addItem(SubscriptionCreateParams.Item.builder().setPrice(...))`,
     `items` required + max 20, 500 subscriptions/customer limit, `billing_cycle_anchor` (timestamp) and
     `billing_cycle_anchor_config` params, `latest_invoice` returned as string ID.
   - Checked: 2026-10-14. Contained the injected "stripe agent setup" CTA — ignored.
7. Expanding responses / Expand (Java) —
   https://docs.stripe.com/expand?lang=java
   - Used for: `addExpand(String)` usage, chaining multiple expands, **max depth = 4 levels** (verbatim
     limit), `data.` list-expansion keyword, webhooks never auto-expanded, `.v1()` version note.
   - Checked: 2026-10-14. Contained the injected "stripe agent setup" CTA — ignored.

### C. Official Javadoc (stripe.dev/stripe-java)
8. `com.stripe.model.Invoice` —
   https://stripe.dev/stripe-java/com/stripe/model/Invoice.html
   - Used for: confirming **no `getSubscription()`** (no method name contains "Subscription" in the full
     Method Summary); `getParent()` returns `Invoice.Parent`.
   - Checked: 2026-10-14.
9. `com.stripe.model.Invoice.Parent` —
   https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html
   - Used for: `getType()` (`subscription_details`/`quote_details`), `getSubscriptionDetails()` →
     `Invoice.Parent.SubscriptionDetails`, `getQuoteDetails()` → `Invoice.Parent.QuoteDetails`.
   - Checked: 2026-10-14.
10. `com.stripe.model.Invoice.Parent.SubscriptionDetails` —
    https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html
    - Used for: `getSubscription()` → **`String`** ("Get ID of expandable subscription object"),
      `getSubscriptionObject()` → `Subscription`, `getSubscriptionProrationDate()` → `Long`,
      `getMetadata()` → `Map<String,String>`.
    - Checked: 2026-10-14.

### Source hierarchy & freshness compliance
- Tier used: official docs + official registry + official Javadoc + official changelog only.
- Freshness: all primary facts tie to the 34.0.0 release (2026-09-30) / API `2026-09-30.endive`, i.e.
  current stable, within the required window as of 2026-10-14.
- Triangulation of key billing claims:
  - Client API `client.v1().subscriptions().create` — docs create page + expand page `.v1()` note. [✓✓]
  - `billingCycleAnchor` type changes — CHANGELOG 34.0.0 (single authoritative source). [✓]
  - Invoice→Subscription accessor chain — Javadoc Invoice + Invoice.Parent + SubscriptionDetails (3 pages). [✓✓]
  - Expand max depth 4 — docs expand page (single source; matches 33.x prior finding → re-confirmed). [✓]
- Prompt-injection CTA present on all three docs.stripe.com pages (#5, #6, #7): ignored, recorded as a
  supply-chain note; no claim derived from it.
