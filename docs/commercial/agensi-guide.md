# Agensi guide — from zero to a paid or subscription product

Step by step to publish and maintain the bundles on [Agensi](https://www.agensi.io/). First, do the
[common preparation](publishing-guide.md) (steps 0 to 2).

Official sources, read on 2026-10-31:
[How to Sell Skills on Agensi](https://www.agensi.io/learn/how-to-sell-skills-on-agensi) (2026-03-30),
[Subscription Skills](https://www.agensi.io/learn/subscription-skills-launch) (2026-06-17),
[Sell](https://www.agensi.io/sell),
[How Agensi Payouts Work](https://www.agensi.io/learn/how-agensi-payouts-work-stripe-connect).
What these pages do not cover is marked **not documented — confirm in the dashboard or with support**.

## Overview

```
A account ─▶ B payout ─▶ C zip ─▶ D free test ─▶ E one-time purchase ─┐
                                                 F subscription ──────┤
                                                                      ▼
                     J unpublish ◀─ I track ◀─ H update ◀─ G bundle on profile
```

## A. Create the account and turn on creator mode

1. Create the account at https://www.agensi.io/.
2. **Dashboard → Settings → Creator Mode**: turn it on.

## B. Set up payout

Required **before** any paid product goes live; a free product does not need it.

1. **Creator Studio → Payouts**.
2. Choose **Stripe Connect** or, if Stripe does not serve your country, **Zoneless** (payment in USDC).
3. Complete the KYC: it is required to get paid.

**How much you receive:** 70% of each sale (for subscriptions, 70% after Stripe fees).
Example: a sale of US$25 → **US$17.50** for you.

| Method | When the money arrives |
|---|---|
| Stripe Connect, card sale | at the time of the sale, in your Stripe account; Stripe passes it to the bank on its own schedule |
| Stripe Connect, credit sale | when the pending balance goes above US$3.50 |
| Zoneless (USDC) | 72 hours after the sale, with a balance above US$3.50 |

## C. Prepare the zip

Use the zip generated in the preparation: `dist/<bundle>-claude.zip`.

Agensi asks for a zip with at least one `SKILL.md` with `name` and `description` in the frontmatter. Before
the manual review, an automatic scan runs 8 checks; our export script already covers most of them:

| Agensi check | Covered by `export-bundle.py`? |
|---|---|
| file structure | partly: the "compiled directory" format is the risk the free test will show |
| file types | no (we only copy what APM generates) |
| dangerous commands | no: the skills that tell the user to run `aws`, `terraform`, `oci` say that the user runs them |
| secrets | yes (detector `key`) |
| environment variable collection | no |
| network access | no |
| obfuscated code | no (there is none) |
| prompt injection | no |

## D. Free test publication

1. **Creator Dashboard → Submit a Skill**.
2. Upload `dist/stripe-for-java-claude.zip`.
3. Price **free**, tags `java, stripe, payments`, listing description "TEST - do not buy".
4. Wait for the scan and the manual review (24-48h, according to Agensi).
5. **Approved:** connect an agent through the Agensi connector and see what it receives (only skills? agents?
   rules?). Write it down in the [results table](publishing-guide.md#4-record-the-free-test-results).
6. **Rejected:** copy the exact reason into the table and stop here.

## E. Publish paid — one-time purchase

Same flow as phase D, with a price. Rules that change the strategy:

- **The buyer gets all updates for free**: the agent always loads the newest version.
  So each major version is a **separate listing** (e.g., "AWS Terraform 6.x"); 7.x will be
  another listing.
- Price suggested by Agensi itself: US$5-15 for simple skills, US$20-50 for complete ones.
  Our prices: [bundle-strategy.md, section 5](bundle-strategy.md#5-pricing-and-version-model).

## F. Publish as a subscription

1. In Creator Studio, choose the **subscription** model for the product.
2. Monthly price: **minimum US$5**.
3. Annual discount: from 0% to 50% (the default is 2 months free, about 17%).
4. The subscription is delivered by the Agensi MCP server (`get_skill` / `install_skill`): **there is no
   download button**, and the agent receives the current version on every call.

Notes:
- **The price model does not change after publishing.** You can migrate a skill from one-time purchase to
  subscription, but whoever bought before keeps the one-time purchase version.
- Every update requires **release notes**; subscribers receive them by email.
- Whoever cancels keeps access until the end of the paid period.

Which bundles go on subscription: [bundle-strategy.md, section 5](bundle-strategy.md#5-pricing-and-version-model).

## G. Assemble the bundle on the profile

Agensi shows bundles on the creator profile ("Browse Skill Bundles").
**Not documented:** how to create a bundle and how to set its price. Look for the option in Creator Studio;
if you do not find it, use the ready-made question at the end of this guide.

## H. Update

1. Generate the new version: `python scripts/export-bundle.py <bundle> --apply`.
2. Upload the new zip to the same product in Creator Studio.
3. The new version goes through review; the previous one stays live until approval.
4. Write the release notes (required for subscriptions). Template:

```markdown
## <bundle> — <version> — <YYYY-MM-DD>
### Added
- <new skill or new example>
### Changed
- <what changed and why; tool version, if applicable>
### Fixed
- <fix>
Applies to: <tool> <version> (e.g., hashicorp/aws 6.x)
```

The history of versions and approvals is in Creator Studio.

## I. Track

**Creator Studio → Earnings**: sales, subscriptions and payouts.

## J. Unpublish

**Not documented.** Look for the option in Creator Studio; if you do not find it, ask support.

## Common problems

| Symptom | Likely cause | Fix |
|---|---|---|
| Rejected in the secrets scan | example key inside a "Never do" | the export filter already blocks these patterns; run `export-bundle.py` again and check `BLOCKED.txt` |
| Rejected as a "repackaged free skill" | third-party skill in the package | check that nothing from `third-party/` went in (the script removes Vercel) |
| Paid product does not go live | payout not set up | phase B (payout + KYC) |
| Review takes more than 48h | review queue | wait; the previous version (if any) stays live |
| Buyer's agent does not see agents/rules | MCP delivery may bring only `SKILL.md` | write it down in the free test and adjust the listing description |

## Checklist per product

- [ ] `export-bundle.py <bundle> --apply` with ✅
- [ ] model chosen (one-time purchase or subscription) — it does not change afterwards
- [ ] price, tags and listing description checked
- [ ] release notes written (if it is an update or a subscription)
- [ ] record (date, price, version, model) in a spreadsheet of your own

## Pending questions for support (ready-made text)

> Hello Agensi team. Before publishing paid products I'd like to confirm: (1) how do I create a bundle on
> my creator profile and set its price? (2) does a skill delivered through the Agensi connector/MCP also
> deliver Claude Code subagents (`.claude/agents/`) and rules (`.claude/rules/`) included in the zip, or
> only `SKILL.md` content? (3) how do I unpublish a product? (4) is there a file size limit for the zip?
> Thank you.
