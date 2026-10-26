---
name: managing-stripe-subscriptions-v34
description: "Manages Stripe billing with stripe-java 34.x: Customers, Prices, Subscriptions, and invoice lifecycle via StripeClient. Use when implementing subscription billing, invoice handling, or migrating ≤33.x billing code to stripe-java 34.x."
---

# Managing Stripe Subscriptions — Billing (stripe-java v34)

> Version lock: every claim applies to **stripe-java 34.0.0** only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| stripe-java | 34.0.0 — current stable major; ≤33.x superseded | https://github.com/stripe/stripe-java/releases |
| Pinned Stripe API version | `2026-09-30.endive` (SDK default for `Stripe-Version` header) | https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md |
| Maven artifact | `com.stripe:stripe-java:34.0.0` | https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- 34.x is the current stable; 33.x superseded 2026-10-01. All ≤33.x billing patterns — notably `Invoice.getSubscription()` — are treated as misinformation for 34.x targets. ([source](https://github.com/stripe/stripe-java/releases))
- Pre-releases 34.1.0-alpha.1 / -alpha.2 / -beta.1 exist; do not pin them. ([source](https://github.com/stripe/stripe-java/releases))
- `2026-09-30.endive` is the 34.0.0 default; future 34.x minor releases may change this.

**Version lock:** this skill locks to the **34.x major line** (suffix `-v34`), tracking 34.x as it evolves (34.0.0 is the reference patch). A new major (35.x) is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [33 to 34 Migration (Billing)](#33-to-34-migration-billing)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `client.v1().customers().create(CustomerCreateParams)` for customer creation** — the legacy static `Customer.create(...)` is not the documented 34.x path ([docs.stripe.com/api/customers/create?lang=java](https://docs.stripe.com/api/customers/create?lang=java), checked 2026-10-14). See [patterns](./blueprints/always-do-patterns.md#1-customer-create).
- **Use `client.v1().subscriptions().create(SubscriptionCreateParams)` with at least one `.addItem(...)` referencing a Price ID** — `items` is required; max 20 per subscription ([docs.stripe.com/api/subscriptions/create?lang=java](https://docs.stripe.com/api/subscriptions/create?lang=java), checked 2026-10-14). See [patterns](./blueprints/always-do-patterns.md#2-subscription-create).
- **Traverse the 34.x Invoice→Subscription chain: `invoice.getParent()` → `.getSubscriptionDetails()` → `.getSubscription()` (String ID) or `.getSubscriptionObject()` (expanded)** — `Invoice` has no top-level `getSubscription()` in 34.x ([stripe.dev/stripe-java/com/stripe/model/Invoice.html](https://stripe.dev/stripe-java/com/stripe/model/Invoice.html), checked 2026-10-14). See [patterns](./blueprints/always-do-patterns.md#3-invoice-to-subscription-accessor-chain-34x).
- **Guard on `"subscription_details".equals(parent.getType())` before calling `getSubscriptionDetails()`** — `Invoice.Parent.getType()` may return `"quote_details"` for quote-originated invoices ([stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html](https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html), checked 2026-10-14). See [patterns](./blueprints/always-do-patterns.md#4-guard-on-parent-type).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Expanding `latest_invoice` | `latest_invoice` is returned as a string ID by default; expand with `.addExpand("latest_invoice")` to get the Invoice object in a single call ([docs.stripe.com/expand?lang=java](https://docs.stripe.com/expand?lang=java)). Max expand depth = 4 levels. | "Does this call need the full Invoice object inline? If yes, add `.addExpand("latest_invoice")` to the params builder." |
| `latest_invoice.payment_intent` expand leaf | The exact expand path under API `2026-09-30.endive` (medium confidence) — Invoice payment linkage was restructured in recent API versions; the exact leaf belongs to the payments unit. | "Confirm the exact payment expand leaf against the pinned API version with the payments unit before using `latest_invoice.payment_intent`." |
| `billing_cycle_anchor` on subscription create | `SubscriptionCreateParams` accepts `billing_cycle_anchor` as a future UTC timestamp and `billing_cycle_anchor_config` object — both unchanged in 34.0.0 ([docs.stripe.com/api/subscriptions/create?lang=java](https://docs.stripe.com/api/subscriptions/create?lang=java)). | "Does this subscription need a custom billing cycle start? Use the timestamp field on create — not the `billing_cycle_anchor_param` type that applies only to update/resume." |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| `invoice.getSubscription()` — this method does NOT exist on `Invoice` in 34.x; the ≤33.x pattern is misinformation for 34.x ([stripe.dev/stripe-java/com/stripe/model/Invoice.html](https://stripe.dev/stripe-java/com/stripe/model/Invoice.html), checked 2026-10-14) | `invoice.getParent().getSubscriptionDetails().getSubscription()` after guarding on `"subscription_details".equals(parent.getType())` |
| Pass the old `billingCycleAnchor` enum (`'now'` / `'unchanged'`) to `SubscriptionUpdateParams` or `SubscriptionResumeParams` — the type changed to `billing_cycle_anchor_param` in 34.0.0 ([CHANGELOG 34.0.0 PR #2292](https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md)) | Migrate to the new `billing_cycle_anchor_param` type for update and resume; the create-params timestamp field is unchanged |
| Create a subscription without any `.addItem(...)` — `items` is required ([docs.stripe.com/api/subscriptions/create?lang=java](https://docs.stripe.com/api/subscriptions/create?lang=java)) | Add at least one item: `.addItem(SubscriptionCreateParams.Item.builder().setPrice("price_...").build())` |
| Expect webhook event data objects to carry expanded linked objects | Webhooks are never auto-expanded ([docs.stripe.com/expand?lang=java](https://docs.stripe.com/expand?lang=java)); use the ID string from the payload and retrieve/expand on a separate direct API call |

## Quick Reference

Sources fetched 2026-10-14.

| Aspect | Value | Source |
|---|---|---|
| Create customer | `client.v1().customers().create(CustomerCreateParams)` | https://docs.stripe.com/api/customers/create?lang=java |
| Create subscription | `client.v1().subscriptions().create(SubscriptionCreateParams)` | https://docs.stripe.com/api/subscriptions/create?lang=java |
| Items required on create | Yes; max 20 items per subscription | https://docs.stripe.com/api/subscriptions/create?lang=java |
| Subscriptions per customer | Max 500 active or scheduled | https://docs.stripe.com/api/subscriptions/create?lang=java |
| Customer email max length | 512 characters | https://docs.stripe.com/api/customers/create?lang=java |
| Customer name max length | 256 characters | https://docs.stripe.com/api/customers/create?lang=java |
| Invoice→Subscription ID (34.x) | `invoice.getParent().getSubscriptionDetails().getSubscription()` → `String` | https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html |
| Invoice→Subscription Object (34.x) | `...getSubscriptionDetails().getSubscriptionObject()` → `Subscription` (when expanded) | https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html |
| `Invoice.getSubscription()` in 34.x | Does NOT exist — ≤33.x pattern; misinformation for 34.x | https://stripe.dev/stripe-java/com/stripe/model/Invoice.html |
| `Invoice.Parent.getType()` values | `"subscription_details"` or `"quote_details"` | https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html |
| Expand max depth | 4 levels | https://docs.stripe.com/expand?lang=java |
| Webhooks auto-expanded | Never | https://docs.stripe.com/expand?lang=java |
| `billingCycleAnchor` type (update/resume/preview) | Changed to `billing_cycle_anchor_param` in 34.0.0 | https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md |
| `billing_cycle_anchor` type (create) | Unchanged — timestamp (future UTC) | https://docs.stripe.com/api/subscriptions/create?lang=java |

## 33 to 34 Migration (Billing)

Breaking changes in 34.0.0 that affect billing code ([CHANGELOG 34.0.0 PR #2292](https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md), checked 2026-10-14):

1. **`Invoice.getSubscription()` removed** — 34.x `Invoice` has no top-level `getSubscription()`. Use the full parent chain: `invoice.getParent()` → `getSubscriptionDetails()` → `getSubscription()` (String ID). Guard on `"subscription_details".equals(parent.getType())`. Cited pages: [Invoice.html](https://stripe.dev/stripe-java/com/stripe/model/Invoice.html), [Invoice.Parent.html](https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html), [Invoice.Parent.SubscriptionDetails.html](https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html).
2. **`SubscriptionUpdateParams.billingCycleAnchor`** — type changed from `enum('now'|'unchanged')` to `billing_cycle_anchor_param`. Migrate accordingly.
3. **`SubscriptionResumeParams.billingCycleAnchor`** — same type change to `billing_cycle_anchor_param`.
4. **`InvoiceCreatePreviewParams.subscription_details.billingCycleAnchor`** — type changed from `enum('now'|'unchanged') | DateTime` to `billing_cycle_anchor_param`.

Note: `SubscriptionCreateParams.billing_cycle_anchor` (timestamp) is **unchanged**. No other 34.0.0 breaking changes affect `Subscription`, `Invoice`, `Price`, or `Product`. (`Product` gains additive `taxDetails` — non-breaking.)

Core upgrade from 33.x to 34.x is **high-risk for billing code** unless all four points above are addressed.

## External Resources

All fetched 2026-10-14.

- Stripe Java SDK releases: https://github.com/stripe/stripe-java/releases
- CHANGELOG.md: https://raw.githubusercontent.com/stripe/stripe-java/master/CHANGELOG.md
- Stripe Docs — Create customer (Java): https://docs.stripe.com/api/customers/create?lang=java
- Stripe Docs — Create subscription (Java): https://docs.stripe.com/api/subscriptions/create?lang=java
- Stripe Docs — Expanding responses (Java): https://docs.stripe.com/expand?lang=java
- Javadoc — Invoice: https://stripe.dev/stripe-java/com/stripe/model/Invoice.html
- Javadoc — Invoice.Parent: https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.html
- Javadoc — Invoice.Parent.SubscriptionDetails: https://stripe.dev/stripe-java/com/stripe/model/Invoice.Parent.SubscriptionDetails.html
- Maven Central metadata (authoritative): https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
