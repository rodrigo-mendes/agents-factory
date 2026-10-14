# Unverified Claims and Risks — stripe-java 34.0.0 (BILLING)

Research date 2026-10-14. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **34.x is the current stable major** as of 2026-10-14; the SDK moves fast (GitHub Releases shows
  alpha/beta pre-releases for 34.1.0 as of research date). Re-verify when starting a new project
  or after 30 days. Source: https://github.com/stripe/stripe-java/releases (checked 2026-10-14).
- **33.x is superseded** (last: 33.4.2, 2026-09-09). All ≤33.x billing patterns — especially
  `Invoice.getSubscription()` — are treated as misinformation for a 34.x target. Do not apply
  33.x guidance to 34.x code.
- `2026-09-30.endive` is pinned by default in 34.0.0; future 34.x minor releases may change this
  default. Audit pinned-version assumptions whenever upgrading minor releases.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | `central.sonatype.com` version table for stripe-java 34.0.0 | (unverified via that host) — SPA returned "Loading…"; version facts sourced from authoritative `repo1.maven.org` metadata XML instead |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Exact expand leaf `latest_invoice.payment_intent` under API `2026-09-30.endive` | (medium confidence) — Invoice payment linkage was restructured in recent API versions; the exact leaf (`payment_intent` vs `payments`/`confirmation_secret`) belongs to the **payments unit** — confirm there before use |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md Ask-First row — `latest_invoice.payment_intent` expand leaf | M1 |
| (medium confidence) | blueprints/never-do-patterns.md §4 — payment expand leaf note | M1 |
| (unverified via that host) | This file — version table via central.sonatype.com | U1 |

## Source Bibliography

All sources are official (Stripe-owned or canonical Maven host) and were fetched on **2026-10-14**.

1. **Maven Central metadata (authoritative artifact index)**
   https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml
   Used for: full 34.x version list; `<release>` = `34.1.0-beta.1` (pre-release); newest stable = `34.0.0`;
   `<lastUpdated>` = `20261008013744`.

2. **GitHub Releases — stripe/stripe-java**
   https://github.com/stripe/stripe-java/releases
   Used for: confirming `v34.0.0` is "Latest"; `34.1.0` entries are alpha/beta only; 33.4.2 is last 33.x stable.

3. **CHANGELOG.md (raw, master branch) — stripe/stripe-java**
   https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md
   Used for: 34.0.0 pinned API version `2026-09-30.endive`; the three `billingCycleAnchor` type changes
   (PR #2292: `SubscriptionUpdateParams`, `SubscriptionResumeParams`,
   `InvoiceCreatePreviewParams.subscription_details`); additive `Product.taxDetails`; non-billing breaking changes.

4. **Maven Central UI (versions tab) — stripe-java**
   https://central.sonatype.com/artifact/com.stripe/stripe-java/versions
   Status: SPA placeholder ("Loading…") at fetch time; not used as a fact source. Superseded by source #1.

5. **Stripe Docs — Create a customer (Java)**
   https://docs.stripe.com/api/customers/create?lang=java
   Used for: `client.v1().customers().create(...)`, `CustomerCreateParams.builder()`,
   `setName`/`setEmail`, field max lengths (email 512, name 256), returned Customer shape.

6. **Stripe Docs — Create a subscription (Java)**
   https://docs.stripe.com/api/subscriptions/create?lang=java
   Used for: `client.v1().subscriptions().create(...)`, `SubscriptionCreateParams.builder()`,
   `.setCustomer(...)`, `.addItem(SubscriptionCreateParams.Item.builder().setPrice(...))`,
   `items` required + max 20, 500 subscriptions/customer limit, `billing_cycle_anchor` (timestamp)
   and `billing_cycle_anchor_config` params unchanged on create, `latest_invoice` as string ID.

7. **Stripe Docs — Expanding responses (Java)**
   https://docs.stripe.com/expand?lang=java
   Used for: `addExpand(String)` usage, max depth 4 levels (verbatim), `data.` list-expansion keyword,
   webhooks never auto-expanded, `.v1()` version note.

8. **Javadoc — com.stripe.model.Invoice**
   https://stripe.dev/stripe-java/com/stripe/model/Invoice.html
   Used for: confirming no `getSubscription()` in 34.x (no method name containing "Subscription" in
   the full Method Summary); `getParent()` → `Invoice.Parent`.

9. **Javadoc — com.stripe.model.Invoice.Parent**
   https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html
   Used for: `getType()` returning `"subscription_details"` or `"quote_details"`;
   `getSubscriptionDetails()` → `Invoice.Parent.SubscriptionDetails`;
   `getQuoteDetails()` → `Invoice.Parent.QuoteDetails`.

10. **Javadoc — com.stripe.model.Invoice.Parent.SubscriptionDetails**
    https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html
    Used for: `getSubscription()` → `String` ("Get ID of expandable subscription object");
    `getSubscriptionObject()` → `Subscription`; `getSubscriptionProrationDate()` → `Long`;
    `getMetadata()` → `Map<String,String>`.
