---
name: provisioning-aws-ses-v6
description: "SES Terraform (aws 6.x): SESv2 identities, DKIM, MAIL FROM, configuration sets, event destinations, pools. Use when writing HCL for SES. Not for SNS, Route 53, IAM, EventBridge."
---

# Provisioning Amazon SES with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = the **hashicorp/aws 6.x** major line (reference patch 6.69.0 / 6.70.0) +
> **Terraform ~> 1.16** only. Sources dated 2026-10-23 (Terraform 1.17.0 CHANGELOG: 2026-10-22).
> Claims tagged (unverified) or (medium confidence) are not confirmed by an official page.
> Main family: SES v2 (`aws_sesv2_*`). The classic `aws_ses_*` resources have their own section; never mix their arguments or values.

## Version Context

| Item | Value | Source (dated 2026-10-23) |
|---|---|---|
| Terraform CLI | **1.16.7** (2026-10-23) is the newest 1.16.x; constraint `~> 1.16` | https://releases.hashicorp.com/terraform/ |
| Terraform 1.17.0 | Stable since 2026-10-21; not the target of this skill | https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (2026-10-23) |
| hashicorp/aws | **6.70.0** (2026-10-23) is the latest; reference patches 6.69.0 / 6.70.0 | https://releases.hashicorp.com/terraform-provider-aws/ |
| Provider constraint | This skill uses `~> 6.69` (root modules); reusable modules set only a minimum (`>=`) | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| 6.57.0 | Withdrawn from GitHub and the Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| aws v7 | Planned (6.0 upgrade guide); no 7.x release exists (provider releases page) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown ; https://releases.hashicorp.com/terraform-provider-aws/ |
| Region | SES resources document an optional `region` (default = provider Region); changing it forces replacement | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable (2026-10-21); this skill still targets `~> 1.16`. Re-verify when starting new work.
- 6.57.0 is withdrawn; a constraint that resolves to it is a risk.
- v7 is planned (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown; no 7.x release per https://releases.hashicorp.com/terraform-provider-aws/); a new major is a new skill (`provisioning-aws-ses-v7`).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Classic aws_ses family](#classic-aws_ses-family-separate)
- [5.x → 6.x Migration (SES)](#5x--6x-migration-ses)
- Identity and DNS patterns: [terraform block, identity, DKIM, MAIL FROM](./blueprints/always-do-identity-dns.md)
- Sending patterns: [configuration set, events, pool, contact list, account level, test](./blueprints/always-do-sending-config.md)
- Classic family: [aws_ses identity policy and notes](./blueprints/always-do-classic-family.md)
- Never-do SES configuration: [MAIL FROM, DKIM, event bus](./blueprints/never-do-ses-config.md)
- Never-do provider/migration: [withdrawn version, deprecated backend](./blueprints/never-do-provider-migration.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- Use `~>` version constraints in root modules. https://developer.hashicorp.com/terraform/language/expressions/version-constraints
  See [identity-dns §1](./blueprints/always-do-identity-dns.md#1-terraform-block-and-s3-backend).
- Use `use_lockfile = true` on the S3 backend. https://developer.hashicorp.com/terraform/language/backend/s3
  See [identity-dns §1](./blueprints/always-do-identity-dns.md#1-terraform-block-and-s3-backend).
- Create and verify a separate identity in every Region you send from. https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html
  See [identity-dns §2](./blueprints/always-do-identity-dns.md#2-domain-identity-and-easy-dkim).
- Name each Easy DKIM CNAME record `<token>._domainkey.<domain>`. https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html
  See [identity-dns §2](./blueprints/always-do-identity-dns.md#2-domain-identity-and-easy-dkim).
- Use a subdomain of the verified identity's parent domain as the custom MAIL FROM domain. https://docs.aws.amazon.com/ses/latest/dg/mail-from.html
  See [identity-dns §3](./blueprints/always-do-identity-dns.md#3-custom-mail-from).
- Set `delivery_options { tls_policy = "REQUIRE" }` on every configuration set. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set.html.markdown
  See [sending §4](./blueprints/always-do-sending-config.md#4-configuration-set).
- Security Hub SES.3 (medium severity) checks that configuration sets have TLS enabled for sending emails. https://docs.aws.amazon.com/securityhub/latest/userguide/ses-controls.html
  See [sending §4](./blueprints/always-do-sending-config.md#4-configuration-set).
- Tag every configuration set; Security Hub SES.2 (low severity) checks tagging. https://docs.aws.amazon.com/securityhub/latest/userguide/ses-controls.html
  See [sending §4](./blueprints/always-do-sending-config.md#4-configuration-set).
- Tag every contact list; Security Hub SES.1 (low severity) checks tagging. https://docs.aws.amazon.com/securityhub/latest/userguide/ses-controls.html
  See [sending §6](./blueprints/always-do-sending-config.md#6-dedicated-ip-pool-contact-list-and-identity-policy).
- Set `enabled = true` on every event destination; the default is `false`. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set_event_destination.html.markdown
  See [sending §5](./blueprints/always-do-sending-config.md#5-event-destination).
- Run `terraform test` with `mock_provider "aws"` and `command = plan`. https://developer.hashicorp.com/terraform/language/tests/mocking
  See [sending §8](./blueprints/always-do-sending-config.md#8-terraform-test).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| DKIM method | Easy DKIM (`next_signing_key_length` `RSA_1024_BIT` or `RSA_2048_BIT`; AWS default is 2048-bit) or BYODKIM (`domain_signing_private_key` + `domain_signing_selector`). Switching BYODKIM to Easy DKIM: SES "will not use BYODKIM to sign your emails while Easy DKIM is being set up" ([source](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html)) | "Easy DKIM or BYODKIM? If migrating from BYODKIM, is unsigned mail acceptable until DNS is confirmed?" |
| DKIM key length changes | The provider page says `next_signing_key_length` can be changed at most once per day ([provider page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity.html.markdown)). AWS: "You can't switch to a different key length more than once in a 24 hour period (unless it's the first downgrade to 1024 in that period)" ([AWS page](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html)). | "When was the key length last changed? Plan at most one change per 24 hours (AWS exception: the first downgrade to 1024)." |
| DKIM CNAME value | AWS documents the value as the token followed by a hosted-zone domain that "varies by AWS Region and identity" (`SigningHostedZone` in the API response). The identity page exports `tokens` only. How to obtain the suffix in HCL is (unverified) ([identity page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity.html.markdown)). A fixed `<token>.dkim.amazonses.com` suffix is likely outdated (medium confidence). ([source](https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html)) | "How will the DKIM CNAME values be produced (outside Terraform, or another source)?" |
| Waiting for verification | The identity page documents no waiter and no timeouts and lists `PENDING` among the `verification_status` values; whether creation returns before verification completes is (medium confidence). Terraform behaviour beyond exporting status is (unverified). DNS detection "can take up to 72 hours" ([identities page](https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html); [provider page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity.html.markdown)). | "Should downstream resources wait for verification, and how?" |
| Both families on one identity | No provider page documents conflicts between `aws_ses_*` and `aws_sesv2_*` for one identity; behaviour is unconfirmed (unverified) ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity.html.markdown)). | "Is the identity already managed with `aws_ses_*`? Mixing families on one identity is unconfirmed — how should it be handled?" |
| Event destination shape | Types: CloudWatch, EventBridge (default bus only), Firehose, Pinpoint, SNS. Whether several destination blocks may coexist in one `event_destination` is (unverified) ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set_event_destination.html.markdown)). | "Which destination type, and one `event_destination` per type?" |
| Dedicated IP pool | `aws_sesv2_dedicated_ip_pool` (`scaling_mode` `STANDARD` or `MANAGED`) is linked to a configuration set through `delivery_options.sending_pool_name` ([pool page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_dedicated_ip_pool.html.markdown); [configuration set page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set.html.markdown)). | "Is a dedicated IP pool needed, and which scaling mode?" |
| Contact-list topics | `default_subscription_status` is required; the page example uses `OPT_IN`; other allowed values are (unverified) ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_contact_list.html.markdown)). | "What default subscription status should each topic use?" |
| Account-level resources | `aws_sesv2_account_suppression_attributes` (`suppressed_reasons`) and `aws_sesv2_account_vdm_attributes` (`vdm_enabled` `ENABLED` or `DISABLED`) are account-level resources; their destroy behaviour is (unverified) ([suppression page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_account_suppression_attributes.html.markdown); [VDM page](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_account_vdm_attributes.html.markdown)). | "Is this account-level setting owned by this configuration, and what should destroy do?" |
| Sandbox and production access | The sandbox status "is unique per each AWS Region"; AWS documents the console and `aws sesv2 put-account-details` for requesting production access. Whether Terraform has a provider resource for it is (unverified). ([source](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html)) | "Is production access already granted in each target Region?" |
| Bounce/complaint thresholds | Numeric thresholds are not stated on the AWS pages cited here (unverified) ([source](https://docs.aws.amazon.com/ses/latest/dg/best-practices.html)). | "Which bounce/complaint targets should alarms use?" |
| MAIL FROM failure behaviour | `USE_DEFAULT_VALUE` falls back to an `amazonses.com` subdomain; `REJECT_MESSAGE` makes sends fail with `MailFromDomainNotVerified` ([source](https://docs.aws.amazon.com/ses/latest/dg/mail-from.html)). | "Reject or fall back when the MX record fails?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `behavior_on_mx_failure = "REJECT_MESSAGE"` without `mail_from_domain` — the page says `mail_from_domain` is required in that case. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity_mail_from_attributes.html.markdown)) | Set `mail_from_domain` whenever `REJECT_MESSAGE` is used |
| Publish several MX records on the MAIL FROM domain — "the custom MAIL FROM setup with Amazon SES will fail". ([source](https://docs.aws.amazon.com/ses/latest/dg/mail-from.html)) | Publish exactly one MX record on the MAIL FROM domain |
| Name a DKIM CNAME `_<token>._domainkey.<domain>` — AWS labels the leading underscore incorrect. ([source](https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html)) | `<token>._domainkey.<domain>` |
| Point `event_bridge_destination.event_bus_arn` at a custom bus — "Only the default bus is supported." ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set_event_destination.html.markdown)) | Use the ARN of the default event bus |
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` or any non-withdrawn patch |
| Use `dynamodb_table` in the S3 backend — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |

## Quick Reference

Sources dated 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Provider / CLI constraint | `~> 6.69` / `~> 1.16` (this skill) | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| S3 locking | `use_lockfile = true`; `dynamodb_table` deprecated | https://developer.hashicorp.com/terraform/language/backend/s3 |
| Identity input | `email_identity` = email address or domain; `identity_type` exported (`EMAIL_ADDRESS` or `DOMAIN`) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity.html.markdown |
| Identities per Region | "To send email from the same domain or email address in more than one AWS Region, you must create and verify a separate identity for each Region." | https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html |
| Easy DKIM key length | `RSA_1024_BIT` or `RSA_2048_BIT` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity.html.markdown |
| MAIL FROM records | `MX 10 feedback-smtp.<region>.amazonses.com` and TXT `"v=spf1 include:amazonses.com ~all"` | https://docs.aws.amazon.com/ses/latest/dg/mail-from.html |
| v2 MX failure values | `USE_DEFAULT_VALUE` or `REJECT_MESSAGE` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity_mail_from_attributes.html.markdown |
| Delivery TLS | `tls_policy` `REQUIRE` or `OPTIONAL`; `max_delivery_seconds` 300–50400 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set.html.markdown |
| Event destination default | `enabled` defaults to `false` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set_event_destination.html.markdown |
| Event import ID | `configuration_set_name\|event_destination_name` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set_event_destination.html.markdown |
| Pool scaling | `scaling_mode` `STANDARD` or `MANAGED` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_dedicated_ip_pool.html.markdown |
| Account VDM import ID | literal `ses-account-vdm-attributes` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_account_vdm_attributes.html.markdown |
| Security Hub SES.1 / SES.2 | Contact lists / configuration sets should be tagged (low severity) | https://docs.aws.amazon.com/securityhub/latest/userguide/ses-controls.html |
| Security Hub SES.3 | Configuration sets should have TLS enabled (medium severity) | https://docs.aws.amazon.com/securityhub/latest/userguide/ses-controls.html |
| Configuration set TLS argument | `delivery_options { tls_policy }` on the configuration set; that this is the argument SES.3 checks is (medium confidence) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set.html.markdown |
| DMARC TXT | Name `_dmarc.<domain>`; AWS rollout `p=none` then `p=quarantine` then `p=reject` | https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html |

## Classic aws_ses family (separate)

Only what the pages state. Do not copy arguments or value casing between families
(v2 `USE_DEFAULT_VALUE` vs classic `UseDefaultValue`). Details: [classic blueprint](./blueprints/always-do-classic-family.md).

- `aws_ses_identity_policy`: `identity` (name or ARN), `name`, `policy`, optional `region`; import `identity|name`. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_identity_policy.html.markdown
- `aws_ses_domain_mail_from`: `behavior_on_mx_failure` "Defaults to `UseDefaultValue`"; import by `domain`. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_domain_mail_from.html.markdown
- `aws_ses_domain_identity_verification` "does not represent a real-world entity in AWS"; `create` timeout default 45 minutes. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_domain_identity_verification.html.markdown
- A v2 equivalent of the verification resource is (unverified); see Ask First.

## 5.x → 6.x Migration (SES)

Upgrade path, in the wording of the 6.0 upgrade guide
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-23):

- "Before upgrading to version `6.0.0`, first upgrade to the latest available `5.x` version of the provider."
- Get a plan that completes "without errors or unexpected changes".
- "update [version constraints] to allow the `6.x` series" (this skill uses `~> 6.69`).
- Run `terraform init -upgrade` "to download the new version".
- The 6.0 guide has no SES entries (medium confidence, absence of evidence).
- CHANGELOG 6.48.0–6.70.0: no SES breaking changes (medium confidence, absence of evidence).
- 6.51.0 fixed deletion detection for classic `aws_ses_domain_mail_from` (medium confidence). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- 6.62.0 added `aws_sesv2_multi_region_endpoint` (medium confidence; coverage note only, not covered here). https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- v7 is planned: "`s3_us_east_1_regional_endpoint` will be removed in `v7.0.0`" (6.0 upgrade guide); no 7.x release exists (https://releases.hashicorp.com/terraform-provider-aws/).

## External Resources

All dated 2026-10-23.

- Terraform releases: https://releases.hashicorp.com/terraform/
- Provider releases: https://releases.hashicorp.com/terraform-provider-aws/
- Provider CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- Enhanced Region support: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
- SES identities: https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html
- SES custom MAIL FROM: https://docs.aws.amazon.com/ses/latest/dg/mail-from.html
- SES Easy DKIM: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html
- SES production access: https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html
- Security Hub SES controls: https://docs.aws.amazon.com/securityhub/latest/userguide/ses-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
