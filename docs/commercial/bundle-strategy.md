# Sales strategy: skill bundles on Agensi and SkillHQ

Working document for publishing this repository's packages as paid products.
Facts about the platforms come from each platform's official documentation, read on **2026-10-31**
(links in the [Sources](#11-sources) section). Where the documentation says nothing, the text marks it **not documented**.
Check the terms again before you publish: both platforms change fast.

## 1. Summary

- **What to sell:** 19 bundles built from the existing packages. Each is a meta-package in
  [`packages/bundles/`](../../packages/bundles/) (only `apm.yml`, no content of its own; one of them also has
  an `export.yml` that cuts what goes on sale).
- **How to package:** `scripts/export-bundle.py` generates the compiled directory for the target (a folder for
  SkillHQ, a zip for Agensi), already without Vercel content and without sensitive data (section 9).
- **Step by step:** [common preparation](publishing-guide.md), [SkillHQ guide](skillhq-guide.md),
  [Agensi guide](agensi-guide.md).
- **Where:** Agensi (one-time purchase or subscription, 70% to the creator) and SkillHQ (one-time purchase,
  85% minus Stripe fee).
- **How to charge:** on Agensi, one listing per major version (one-time purchase) and a "Latest" subscription track
  for the bundles that change fast. On SkillHQ, a one-time purchase with updates inside the
  same major version.
- **Where to start:** 3 bundles and free lead magnets (section 10).

## 2. Before you sell (blockers)

1. **Intellectual property.** Confirm in writing with your employer (and with the client, if applicable)
   that you can sell the content. Both platforms require the content to be yours or
   licensed; Agensi says creators keep ownership and give the platform a license to distribute.
2. **Client content and sensitive data.** A scan with 8 detectors (names, emails, OCIDs,
   OCIR namespace, hosts, AWS accounts, keys, personal paths) found client content and real
   tenancy data in the OCI packages; they were replaced with placeholders on 2026-10-31. The same detector
   runs on every export and **blocks** the bundle if it finds anything (`scripts/export_detectors.py`).
   The skill `integrating-oracle-rms-webhooks` is never exported: it is one client's integration, not a product.
3. **Third-party content.** [`third-party/vercel-frontend`](../../packages/third-party/vercel-frontend/)
   only points to official Vercel repositories. These 20 skills **never** go into a paid package:
   Agensi rejects "repackaged free skills". The `saas-starter-team` bundle pulls this package in
   transitively; the export must remove it, and the listing must name the Vercel repositories as a
   free prerequisite.
4. **Quality.** Run `/skill-best-practices-validator` and `/evaluating-skill-scenarios` on every skill
   in the bundle. The report works as a sales argument ("tested with scenarios").
5. **Security.** The Agensi scan looks for dangerous commands, secrets, environment variable collection,
   network access, obfuscation and prompt injection. Skills that tell the user to run `aws`, `terraform` or
   `oci` must make clear that the commands are the user's and that nothing runs without approval.

## 3. Platform comparison

| | Agensi | SkillHQ |
|---|---|---|
| Payout | 70% per sale; subscription 70% after Stripe fees | 85% (15% commission) + Stripe fee charged separately: 1.5% + €0.25 (EU), 3.25% + €0.25 (outside the EU) |
| Listing fee | not documented | none |
| Price | free; suggests US$5-15 (simple skill) and US$20-50 (complete skill) | minimum €2.00; free €0.00; range quoted as "€2–$50" |
| Upload format | **zip** with `SKILL.md` (`name` + `description` in the frontmatter) + optional scripts, references and assets | **directory** with `SKILL.md` + `README.md`, published by the `skillhq` CLI |
| Review | automatic scan (8 checks) + manual review of 24-48h | automatic validation (structure, frontmatter, quality, duplicate) |
| Delivery to the buyer | the agent loads the skill through the Agensi connector/MCP; nothing is downloaded | `skillhq install` writes to `~/.claude/skills/<name>` (or `./.claude/skills` with `--project`) |
| Updates | one-time purchase gets **free updates**; a new version goes through review before it takes effect | `skillhq publish --update --changelog`; the buyer runs `skillhq update` |
| Subscription | yes: minimum US$5/month, annual discount from 0 to 50% (default: 2 months free), release notes required | not documented |
| Bundles | exist on the creator profile; mechanics and price not documented | not documented |
| Payment | Stripe Connect or Zoneless (USDC); KYC required to get paid | Stripe Connect; Starter publishes without Stripe, Pro (KYC) is paid directly to the bank |
| Anti-piracy | not documented | fingerprint per download, SimHash, DMCA |
| Refund | not documented | automatic if never downloaded; after that, no |
| Agents served | Claude, ChatGPT, Cursor, Codex, Gemini CLI and others through the connector | Claude Code (SKILL.md) and Custom GPTs |

**Practical consequence:** only the SKILL.md files (with `blueprints/`, `assets/`, `scripts/`) are portable.
Subagents (`.claude/agents/`), `/commands` with `context: fork` and rules (`.claude/rules/`) belong to
Claude Code. The Agensi documentation **does not say** whether the MCP delivers anything beyond SKILL.md. Before
you publish a bundle with agents, publish a test skill and confirm what reaches the buyer.

## 4. Bundle catalog

Counts of own content (without the Vercel skills), adding up all the packages the bundle pulls in.
Every bundle includes the 5 rules of `factory-core` (frontmatter and names); they are included in the counts.

### A. For people who create skills (the same audience as the marketplaces)

| Bundle | Direct packages | Skills (commands) | Agents | Rules | Audience |
|---|---|---|---|---|---|
| [`skill-factory-pro`](../../packages/bundles/skill-factory-pro/apm.yml) | factory/agent-package-builder, artifact-authoring, researching-frameworks | 11 (9) | 4 | 5 | people who create skills and agents |
| [`harness-quality-kit`](../../packages/bundles/harness-quality-kit/apm.yml) | harness-quality/auditing, validating, evaluating | 14 (14) | 3 | 5 | people who maintain skills and agents in production |
| [`anti-hallucination-research`](../../packages/bundles/anti-hallucination-research/apm.yml) | factory/researching-frameworks, researching-platform | 20 (20) | 3 | 5 | architects and platform teams |

### B. Cloud

| Bundle | Direct packages | Skills (commands) | Agents | Rules |
|---|---|---|---|---|
| [`aws-terraform-complete`](../../packages/bundles/aws-terraform-complete/apm.yml) | cloud/terraform/terraform | 39 (10) | 8 | 9 |
| [`aws-well-architected-reviewer`](../../packages/bundles/aws-well-architected-reviewer/apm.yml) | cloud/provider/aws/aws-architect | 44 (2) | 4 | 8 |
| [`oci-serverless-complete`](../../packages/bundles/oci-serverless-complete/apm.yml) | oci-functions-java, oci-observability, oci-architecture, oci-terraform | 56 (9) | 8 | 34 |
| [`multi-cloud-terraform`](../../packages/bundles/multi-cloud-terraform/apm.yml) | cloud/terraform/terraform, oci-terraform | 60 (12) | 9 | 17 |
| [`cloud-observability`](../../packages/bundles/cloud-observability/apm.yml) | aws-observability, oci-observability | 82 (3) | 4 | 11 |
| [`architecture-board`](../../packages/bundles/architecture-board/apm.yml) | solution-architecture, aws-architect, oci-architecture | 53 (4) | 8 | 10 |

### C. Java

| Bundle | Direct packages | Skills (commands) | Agents | Rules |
|---|---|---|---|---|
| [`serverless-java-aws`](../../packages/bundles/serverless-java-aws/apm.yml) | java/quarkus/quarkus-aws, cloud/provider/aws/aws-lambda | 88 (2) | 7 | 14 |
| [`camel-quarkus-integration`](../../packages/bundles/camel-quarkus-integration/apm.yml) | java/quarkus/camel-quarkus-integrator | 16 (0) | 1 | 9 |
| [`java-ai-langchain4j`](../../packages/bundles/java-ai-langchain4j/apm.yml) | java/libs/langchain4j, java/quarkus/quarkus-langchain4j | 62 (1) | 5 | 11 |
| [`stripe-for-java`](../../packages/bundles/stripe-for-java/apm.yml) | java/libs/stripe-java | 6 (2) | 2 | 6 |
| [`java-clean-code`](../../packages/bundles/java-clean-code/apm.yml) | java/clean-code/clean-code-quarkus, clean-code-oci | 2 (0) | 0 | 7 |

### D. Delivery and CI/CD

| Bundle | Direct packages | Skills (commands) | Agents | Rules |
|---|---|---|---|---|
| [`github-actions-secure-cicd`](../../packages/bundles/github-actions-secure-cicd/apm.yml) | delivery/github/github-actions-cicd | 12 (1) | 2 | 9 |
| [`spec-driven-delivery`](../../packages/bundles/spec-driven-delivery/apm.yml) | delivery/specs/openspec-github | 7 (2) | 2 | 7 |

### E. Outside IT and flagship

| Bundle | Direct packages | Skills (commands) | Agents | Rules |
|---|---|---|---|---|
| [`technical-book-author`](../../packages/bundles/technical-book-author/apm.yml) | content-generation/book-writing | 10 (10) | 13 | 5 |
| [`saas-starter-team`](../../packages/bundles/saas-starter-team/apm.yml) | saas/aws-saas-serverless-quarkus-react-nextjs | 123 (16) + 20 Vercel | 29 | 23 |

Large bundles through transitivity: `cloud-observability` (82 skills) and `serverless-java-aws` (88)
bring in the 40 `aws-skills` and the 26 `aws-terraform` because the agents depend on them. This is value
for the buyer, but check that the price reflects the size.

### F. Cut at export

| Bundle | Direct packages | What goes on sale |
|---|---|---|
| [`ai-code-review-squad`](../../packages/bundles/ai-code-review-squad/apm.yml) | quarkus-langchain4j, terraform, github-actions-cicd, stripe-java | REVIEW_SQUAD_COUNTS |

The reviewers are in different packages, so the `apm.yml` installs the whole packages and the
[`export.yml`](../../packages/bundles/ai-code-review-squad/export.yml) cuts: only the 5
read-only reviewers (`quarkus-code-reviewer`, `langchain4j-reviewer`, `terraform-code-reviewer`,
`cicd-pipeline-reviewer`, `stripe-advisor`) and the skills and rules they cite go in. `nextjs-code-reviewer` and
`ui-design-reviewer` stay out because they depend on the Vercel skills.

## 5. Pricing and version model

### Version rule

The repository follows "1 skill = 1 version" (skills with the suffix `-v6`, `-v3-40`, `-v1-22`). This still
holds in the sale: **the product may have no version, but the content always does**.

- **Agensi, one-time purchase:** because the buyer gets free updates, each major version becomes a
  **separate listing** ("AWS Terraform 6.x"). Fixes inside 6.x ship as an update; version 7
  becomes another listing. Whoever bought 6.x is not pushed to 7.
- **Agensi, "Latest" subscription:** the track always points to the current stable version. When the major
  version changes, the release note (required) says which version now applies. The price model is fixed
  per skill once published; you can migrate a skill from one-time purchase to subscription, and whoever
  bought before keeps the one-time version.
- **SkillHQ:** one-time purchase only (subscription not documented). Same rule: one listing per major
  version, `--update` only inside it.

### Who goes on subscription and who stays on one-time purchase

| "Latest" subscription on Agensi (changes fast) | One-time purchase (stable) |
|---|---|
| `skill-factory-pro` (changes with Claude Code and the SKILL.md format) | `camel-quarkus-integration` (Quarkus 3.40 LTS) |
| `aws-terraform-complete` (the AWS provider ships versions often) | `stripe-for-java` (stripe-java 34.x) |
| `github-actions-secure-cicd` (supply chain incidents) | `oci-serverless-complete` |
| `harness-quality-kit` | `technical-book-author` |
| `serverless-java-aws`, `java-ai-langchain4j` (quarkus-langchain4j is at CR) | `spec-driven-delivery`, `architecture-board` |

### Suggested price table

A one-time purchase should cost about 3 to 4 months of subscription, so that one does not cannibalize the other.

| Tier | Examples | One-time purchase | Subscription (Agensi) |
|---|---|---|---|
| Free lead magnet | 1 skill from each bundle | €0 | — |
| Single item | one skill or one agent | €3-9 | US$5/month (minimum) |
| Domain bundle | stripe, camel, spec-driven, github-actions, book | €15-25 | US$5-7/month |
| Professional bundle | skill-factory-pro, aws-terraform-complete, multi-cloud, serverless-java-aws | €29-39 | US$9-12/month |
| Flagship | saas-starter-team | €49 (near the ceiling quoted by SkillHQ) | US$15/month |

Suggested free lead magnets (one per bundle, to attract people who later buy the package):
`composing-github-actions-pipelines`, `applying-aws-well-architected`, `rules-compiler`,
`specifying-changes-with-openspec-v1-15`, `developing-quarkus-arc-v3-40`.

## 6. What is uploaded: the compiled directory of the target

The package you sell is what APM generates for the target (today `claude`), already filtered:

```
dist/<bundle>/claude/            ← folder (SkillHQ)
├── README.md                    ← generated: description, version, date, contents, installation
└── .claude/
    ├── skills/<name>/SKILL.md (+ blueprints/, assets/, scripts/)
    ├── agents/<name>.md
    └── rules/<name>.md
dist/<bundle>-claude.zip         ← the same content (Agensi)
```

The buyer copies the `.claude/` folder to the project root. Skills work in other agents that
read `SKILL.md`; agents, `/commands` and rules belong to Claude Code.

**Risk to test before you sell:** both platforms document a `SKILL.md` at the root of the uploaded
package; the compiled directory has the `SKILL.md` files inside `.claude/skills/<name>/`. Publish a small
bundle as free on each platform and see whether the validation accepts it
([results table](publishing-guide.md#4-record-the-free-test-results)).

## 7. Agensi — summary

Account and Creator Mode → payout (Stripe Connect or USDC, with KYC) → zip upload through
**Submit a Skill** → automatic scan + 24-48h review → one-time purchase (free updates for whoever
bought) or subscription (minimum US$5/month, release notes required, fixed model once published).
Full step by step: [agensi-guide.md](agensi-guide.md).

## 8. SkillHQ — summary

Account → CLI (`npm install -g @skill-hq/cli`, `skillhq auth login`) → `skillhq validate` →
`skillhq publish --price --category` → Pro plan (Stripe KYC) to get paid → updates with
`--update --changelog`. Full step by step: [skillhq-guide.md](skillhq-guide.md).

## 9. How to generate the packages in the repository

Each bundle is a meta-package in `packages/bundles/<name>/apm.yml`: it lists only the top-level packages, the rest
comes through transitivity. The bundles do **not** go into the root `apm.yml` (that would be a second path to
packages that are already installed).

```bash
python scripts/export-bundle.py stripe-for-java              # dry run: shows what would go in
python scripts/export-bundle.py stripe-for-java --apply      # writes the folder and the zip to dist/
python scripts/export-bundle.py --all --apply                # all bundles
```

For each bundle, the script:

1. installs only the bundle into a fresh temporary folder on each attempt, with a short path
   (`C:\tmp\ax\<6 letters>`): with long names, the paths inside `apm_modules/` pass the Windows
   260-character limit and the install always fails. Up to 5 attempts (Windows file locks
   are intermittent);
2. runs the 2 post-install scripts in that folder (`--root`);
3. reads from that folder's `apm.lock.yaml` each generated file and the package that owns it;
4. removes the files that do not come from a local package or that come from `third-party/` (Vercel), removes
   `integrating-oracle-rms-webhooks` and applies `export.yml`, if there is one;
5. runs the 8 sensitive-data detectors: if they find anything, the bundle is **blocked** and the list goes to
   `dist/<bundle>/BLOCKED.txt`;
6. writes the folder and the zip (reproducible zip: same input, same sha256).

**`export.yml` (optional, next to `apm.yml`; APM ignores it):**

| Field | Values | Default |
|---|---|---|
| `agents` | list of names, or `all` | `all` |
| `skills` | list of names, `cited` or `all` | `all` |
| `rules` | list of names, `cited` or `all` (the 5 base frontmatter and naming rules always go in) | `all` |
| `include` / `exclude` | paths relative to the target (`skills/x`, `agents/y.md`, `rules/z.md`); accept `*` | — |

`cited` = names written between backticks in the text of the selected agents.

The detectors have their own tests: `python scripts/tests/test_export_detectors.py`. To scan a whole
folder: `python scripts/export_detectors.py packages --skip third-party`.

## 10. Phased launch

1. **Blockers (section 2):** IP, client content, Vercel, validation and scan.
2. **Delivery test:** publish a small bundle as free on each platform and confirm what
   reaches the buyer (only SKILL.md or also agents and rules) — phase D of the guides.
3. **First wave:** `github-actions-secure-cicd` (widest audience), `skill-factory-pro` (same
   audience as the marketplaces) and `aws-terraform-complete`, each with a free lead magnet.
4. **Measure for 4 weeks:** lead magnet downloads, conversion to paid, refunds and canceled
   subscriptions.
5. **Expand:** niche bundles (OCI, Camel, Stripe), then the flagship `saas-starter-team`.
6. **Maintenance:** the repository pipeline produces the updates and the release notes
   (`/researching-technical-frameworks` → `/skill-creator` → `/skill-best-practices-validator` →
   `/evaluating-skill-scenarios`). Reserve time each month for every bundle on subscription.

## 11. Sources

All read on 2026-10-31.

- Agensi, *How to Sell Skills on Agensi* (2026-03-30): https://www.agensi.io/learn/how-to-sell-skills-on-agensi
- Agensi, *Subscription Skills on Agensi* (2026-06-17): https://www.agensi.io/learn/subscription-skills-launch
- Agensi, *Sell*: https://www.agensi.io/sell
- Agensi, *How Agensi Payouts Work*: https://www.agensi.io/learn/how-agensi-payouts-work-stripe-connect
- SkillHQ, home page (prices, fees, anti-piracy, refund): https://skillhq.dev/
- SkillHQ, *CLI docs*: https://skillhq.dev/docs/cli
- SkillHQ, *Become a seller*: https://skillhq.dev/become-seller
- SkillHQ, terms and seller agreement (not read, read before you publish):
  https://skillhq.dev/legal/terms, https://skillhq.dev/legal/seller-agreement
