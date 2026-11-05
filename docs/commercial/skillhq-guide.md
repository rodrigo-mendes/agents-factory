# SkillHQ guide — from zero to a paid product

Step by step to publish and maintain the bundles on [SkillHQ](https://skillhq.dev/). First, do the
[common preparation](publishing-guide.md) (steps 0 to 2).

Official sources, read on 2026-10-31: [home page](https://skillhq.dev/) (prices, fees,
anti-piracy, refund), [CLI docs](https://skillhq.dev/docs/cli),
[Become a seller](https://skillhq.dev/become-seller). What these pages do not cover is marked
**not documented — confirm with support** (`support@skillhq.dev`).

## Overview

```
A account ─▶ B CLI ─▶ C validate ─▶ D free test ─▶ E Pro (get paid) ─▶ F publish paid
                                                                           │
                       J unpublish ◀─ I protect ◀─ H track ◀─ G update
```

## A. Create the account

1. Go to https://skillhq.dev/ and create the account with GitHub, Google or email.
2. You start on the **Starter** plan: you can already publish, but you cannot yet be paid into a bank account (phase E).

## B. Install and authenticate the CLI

```bash
npm install -g @skill-hq/cli
skillhq auth login          # opens the browser to log in (OAuth)
skillhq auth status         # should show your account
```

To uninstall later: `npm uninstall -g @skill-hq/cli`. To sign out: `skillhq auth logout`.

## C. Validate without publishing

```bash
skillhq validate dist/stripe-for-java/claude
```

The validation checks structure, frontmatter, content quality and duplicates.

| Result | What to do |
|---|---|
| Passed | Go to phase D. Write "validated" in the [results table](publishing-guide.md#4-record-the-free-test-results). |
| Complained about `SKILL.md` at the root | This is the known risk: we export the compiled directory (`.claude/...`). Copy the exact message into the table and stop here: the export script needs another format (for example, one folder per skill). |
| Complained about a duplicate | SkillHQ compares with what already exists (SimHash). Check that the skill was not published before, by you or by someone else. |

## D. Free test publication

```bash
skillhq publish dist/stripe-for-java/claude \
  --price 0 --category development \
  --tags java,stripe,payments \
  --short-description "TEST - do not buy"
```

Then, **install as a buyer** in an empty folder to see what arrives:

```bash
mkdir -p /c/tmp/skillhq-buyer && cd /c/tmp/skillhq-buyer
skillhq install <product-name> --project     # installs into ./.claude/skills/<name>
find .claude -maxdepth 3
```

Write down in the results table whether **skills**, **agents** and **rules** arrived. The documentation only
mentions `.claude/skills/`; agents (`.claude/agents/`) and rules (`.claude/rules/`) may not be copied.

## E. Enable payout (Pro plan)

1. In the dashboard, upgrade to **Pro**.
2. Complete the KYC on Stripe (about 5 minutes): name, address and a photo of an official ID.
3. Connect the bank account. Payments follow the standard Stripe schedule.

**How much you receive:** the page says the seller keeps 85%; the commission is 15% and the Stripe fee
is 1.5% + €0.25 (EU) or 3.25% + €0.25 (outside the EU). The official example (a €10 sale → €8.50 for the
seller, €1.10 for the platform, €0.40 for Stripe) indicates that the Stripe fee comes out of the platform's
share. By that example, a **€29 sale earns €24.65**. Confirm on the first statement.

## F. Publish paid

One command per bundle. Price in euros (minimum €2.00) and one of the 4 categories:
`development`, `productivity`, `security` or `devops`.

```bash
skillhq publish dist/aws-terraform-complete/claude \
  --price 29 --category devops \
  --tags terraform,aws,iac \
  --short-description "26 hashicorp/aws 6.x skills + Terraform engineer and reviewer agents"
```

| Bundle | Suggested category |
|---|---|
| Terraform, CI/CD, observability, cloud | `devops` |
| Java, Quarkus, Stripe, LangChain4j, clean code | `development` |
| reviewers, harness quality | `security` (review) or `development` |
| research, technical book, skill factory | `productivity` |

Suggested prices: [bundle-strategy.md, section 5](bundle-strategy.md#5-pricing-and-version-model).

If `publish` asks for Stripe Connect: do phase E first.

## G. Update

Inside the **same major version** (fixes, new examples):

```bash
python scripts/export-bundle.py aws-terraform-complete --apply
skillhq publish dist/aws-terraform-complete/claude --update --changelog "Fix S3 lifecycle example"
```

The buyer receives it by running `skillhq update` (`skillhq outdated` shows what has an update).

A new major version (e.g., AWS provider 7.x) = a **new product**, with another name. Whoever bought 6.x is not
pushed to 7.x ([version rule](bundle-strategy.md#5-pricing-and-version-model)).

## H. Track sales and refunds

- Sales and payouts: seller dashboard.
- Automatic refund **only if the buyer never downloaded**. After the download, there is no refund; broken
  skills go through manual review.

## I. Protect against copying

- Each download gets a mark (fingerprint) and paraphrased copies are detected by SimHash.
- To request removal of a copy: DMCA process described in the
  [terms of service](https://skillhq.dev/legal/terms) and in the
  [seller agreement](https://skillhq.dev/legal/seller-agreement) (read both before you publish paid).

## J. Unpublish

**Not documented** in the CLI (there is no `unpublish`). Do it through the seller dashboard or ask support.

## Common problems

| Symptom | Likely cause | Fix |
|---|---|---|
| `publish` asks for Stripe Connect | Starter plan | phase E (upgrade to Pro) |
| validation rejected for structure | "compiled directory" format | write down the message and stop (phase C) |
| invalid `--category` | only 4 categories exist | `development`, `productivity`, `security`, `devops` |
| `--short-description` cut off | 200-character limit | shorten it |
| buyer did not receive agents/rules | the CLI installs into `.claude/skills/` | write it down and include copy instructions in `README.md` |

## Checklist per published bundle

- [ ] `export-bundle.py <bundle> --apply` with ✅ (no `BLOCKED.txt`)
- [ ] `skillhq validate` passed
- [ ] price, category, tags and short description checked
- [ ] package `README.md` with version and date
- [ ] record of the publication (date, price, version) in a spreadsheet of your own

## Pending questions for support (ready-made text)

> Hello SkillHQ team. Before publishing paid products I'd like to confirm three points that the docs
> don't cover: (1) is there a native way to sell a bundle of several skills as one product, or should a
> single directory contain several skills? (2) does `skillhq install` also copy Claude Code subagents
> (`.claude/agents/`) and rules (`.claude/rules/`) shipped in the package, or only `.claude/skills/`?
> (3) how can a seller unpublish a product? Thank you.
