# Research — Amazon SES with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `ses`, flat fan-out, single researcher, no sub-agents).
> Registry pages render JS-only (F12); upstream raw markdown from `hashicorp/terraform-provider-aws` (`main`) is the authority for resource docs.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_SES_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL).
> Family split: **SES v2 (`aws_sesv2_*`) is the primary family.** Classic `aws_ses_*` resources are covered only in §9, only for what their pages say. Do not mix the two families for the same identity in one design unless you have read both pages (no provider page documents a cross-family conflict — see U3).

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"`; 1.16.7 newest 1.16.x | F1, F19 |
| Terraform 1.17.0 | stable, not the target | F2 |
| hashicorp/aws | latest 6.70.0; constraint `~> 6.69`; no 7.x | F3, F18 |
| Withdrawn | 6.57.0 — never pin | F4 |
| Region | SES is **regional**: every `aws_sesv2_*` / `aws_ses_*` page read documents optional `region` (defaults to provider region); changing forces replacement; import `id@region` | F5; resource pages [1]–[10] |
| Global? | SES is not in the F14 global list | F14 |
| Identity per Region | "To send email from the same domain or email address in more than one AWS Region, you must create and verify a separate identity for each Region." Up to 10,000 identities per Region | [16] |
| Sandbox per Region | "The sandbox status for your account is unique per each AWS Region." | [15] |

Constraint block: identical to the pilot (`required_version = "~> 1.16"`, `aws ~> 6.69`) — F1, F3, F6.

## 2. Provider 6.x changes for SES

- **6.0.0 upgrade guide (F13):** the guide contains **no** mention of SES, `aws_ses*` or `aws_sesv2*` — no removed/renamed SES arguments [11].
- **CHANGELOG 6.48.0 → 6.70.0** (SES-filtered) [12]:
  - 6.51.0 (2026-06-17): "resource/aws_ses_domain_mail_from: Correctly detect resources deleted outside of Terraform when refreshing state" (#48387) — classic family.
  - 6.62.0 (2026-08-26): New Resource `aws_sesv2_multi_region_endpoint` (#49660) — out of scope here, page not read (L3).
  - No other SES entries in 6.48.0–6.70.0 (6.55.0 straddled two fetch windows; no SES entry seen in either part — medium confidence, M1).
- No SES breaking changes in the 6.x line found.

## 3. `aws_sesv2_email_identity` [1]

- **Required:** `email_identity` — an email address **or** a domain. `identity_type` (exported) is `EMAIL_ADDRESS` or `DOMAIN`.
- **Optional:** `configuration_set_name` (default config set for this identity; a config set named in the send request takes precedence — also stated by AWS [16]); `dkim_signing_attributes`; `region`; `tags`.
- `dkim_signing_attributes` (domain identities):
  - Easy DKIM: `next_signing_key_length` = `RSA_1024_BIT` | `RSA_2048_BIT`; the page says it can be changed at most once per day. AWS: Easy DKIM default is 2048-bit; "You can't switch to a different key length more than once in a 24 hour period (unless it's the first downgrade to 1024 in that period)" and you can't switch to the length already configured [14].
  - BYODKIM: `domain_signing_private_key` (Sensitive; 1024- or 2048-bit RSA, base64; delete first/last PEM lines and line breaks) + `domain_signing_selector` [1][16].
  - Exported: `current_signing_key_length`, `last_key_generation_timestamp`, `signing_attributes_origin` (`AWS_SES` = Easy DKIM, `EXTERNAL` = BYODKIM), `status`, `tokens` (Easy DKIM: strings for CNAME records; BYODKIM: the selector).
- **Exported:** `arn`, `identity_type`, `tags_all`, `verification_status` (`PENDING` | `SUCCESS` | `FAILED` | `TEMPORARY_FAILURE` | `NOT_STARTED`), `verified_for_sending_status`.
- **Import:** `email_identity` value, e.g. `example.com`.
- **Timeouts:** none documented. The page documents **no waiter for verification** — creation returns with the identity possibly `PENDING`; Terraform behaviour beyond exporting status is not documented (U1).
- AWS migration warning: switching BYODKIM → Easy DKIM, SES "will not use BYODKIM to sign your emails while Easy DKIM is being set up"; emails may go unsigned until DNS is confirmed — use an intermediary subdomain or downtime [14].

### DKIM DNS records (Easy DKIM) — as AWS states
- Three CNAME records [16]. Name form `<token>._domainkey.<domain>` (correct: `abc123._domainkey.domain.com`; incorrect: `_abc123._domainkey.domain.com`) [16].
- Value: "the DKIM token followed by a hosted zone domain (for example, `token.dkim.us-west-2.amazonses.com`). The hosted zone portion varies by AWS Region and identity", retrievable as `SigningHostedZone` in the CreateEmailIdentity/GetEmailIdentity API response [16]. The `aws_sesv2_email_identity` page does **not** export a `SigningHostedZone` attribute [1] — the value suffix to use in `aws_route53_record` is therefore not documented by the provider (U2).
- DNS propagation "can take up to 72 hours"; once SES detects all records, DKIM shows Successful and identity Verified [16].
- Email address identity: verification link from no-reply-aws@amazon.com; link expires after 24 hours [16]. Email addresses are case-sensitive; domains are not [16].
- Inherited verification: an address on a verified domain is limited to "straightforward email sending"; using it with configuration sets, delegate-sending policy authorizations or overrides requires verifying it explicitly as an email identity [16].

## 4. `aws_sesv2_email_identity_mail_from_attributes` [2]

- **Required:** `email_identity` (verified identity). **Optional:** `mail_from_domain` (required when `behavior_on_mx_failure = "REJECT_MESSAGE"`), `behavior_on_mx_failure` (`USE_DEFAULT_VALUE` | `REJECT_MESSAGE`; **no default stated on the page**), `region`. No exported attributes. Import: `email_identity`.
- AWS requirements [17]:
  - MAIL FROM domain must be a subdomain of the parent domain of a verified identity; shouldn't be a subdomain you send from or receive email on.
  - Records: `MX 10 feedback-smtp.<region>.amazonses.com` and TXT `"v=spf1 include:amazonses.com ~all"` on the MAIL FROM subdomain.
  - "you must publish exactly one MX record … If the MAIL FROM domain has multiple MX records, the custom MAIL FROM setup with Amazon SES will fail."
  - States: Pending (72 h detection, fallback used) → Success | TemporaryFailure (72 h) → Failed (restart setup required).
  - Reject message → `MailFromDomainNotVerified` error on send; Use default → `amazonses.com` subdomain.

## 5. `aws_sesv2_configuration_set` [3]

- **Required:** `configuration_set_name`. **Optional blocks:** `delivery_options`, `reputation_options`, `sending_options`, `suppression_options`, `tracking_options`, `vdm_options`; plus `region`, `tags`.
- `delivery_options`: `max_delivery_seconds` (300–50400), `sending_pool_name`, `tls_policy` (`REQUIRE` | `OPTIONAL`).
- `reputation_options.reputation_metrics_enabled` (bool); exported `reputation_options.last_fresh_start`.
- `sending_options.sending_enabled` (bool).
- `suppression_options.suppressed_reasons`: `BOUNCE`, `COMPLAINT`.
- `tracking_options`: `custom_redirect_domain` (required inside block), `https_policy` (`REQUIRE` | `REQUIRE_OPEN_ONLY` | `OPTIONAL`).
- `vdm_options`: `dashboard_options.engagement_metrics`, `guardian_options.optimized_shared_delivery` (`ENABLED` | `DISABLED`).
- No defaults stated except `region`. Exported `arn`. Import: `configuration_set_name`.
- **Security Hub SES.3** fails unless `tls_policy = "REQUIRE"` (§12).

## 6. `aws_sesv2_configuration_set_event_destination` [4]

- **Required:** `configuration_set_name`, `event_destination_name`, `event_destination` block. Optional `region`.
- `event_destination.enabled` — **default `false`** (set `true` explicitly).
- `matching_event_types` (required): `SEND`, `REJECT`, `BOUNCE`, `COMPLAINT`, `DELIVERY`, `OPEN`, `CLICK`, `RENDERING_FAILURE`, `DELIVERY_DELAY`, `SUBSCRIPTION`.
- Destinations: `cloud_watch_destination.dimension_configuration` (`default_dimension_value`, `dimension_name`, `dimension_value_source` = `MESSAGE_TAG` | `EMAIL_HEADER` | `LINK_TAG`); `event_bridge_destination.event_bus_arn` ("Only the default bus is supported."); `kinesis_firehose_destination` (`delivery_stream_arn`, `iam_role_arn`); `pinpoint_destination.application_arn`; `sns_destination.topic_arn`.
- `id` / import: `configuration_set_name|event_destination_name`.
- Mutual exclusivity of destination blocks within one `event_destination` is not stated on the page (U4).

## 7. `aws_sesv2_dedicated_ip_pool` [5]

- **Required:** `pool_name`. **Optional:** `scaling_mode` (`STANDARD` | `MANAGED`; when omitted the AWS API defaults to standard), `region`, `tags`. Exported `arn`. Import: `pool_name`. No timeouts documented.
- Link to configuration set via `delivery_options.sending_pool_name` [3].

## 8. Contact lists and account-level resources

- `aws_sesv2_contact_list` [6]: required `contact_list_name`; optional `description`, `topic` blocks (`topic_name`, `display_name`, `default_subscription_status` required; `description` optional; example uses `OPT_IN`, other values not listed — U5), `region`, `tags`. Exported `arn`, `created_timestamp`, `last_updated_timestamp`. Import: `contact_list_name`. Tag it — SES.1 (§12).
- `aws_sesv2_account_vdm_attributes` [7] (**note:** the brief's name `aws_sesv2_account_vdm_options` does not exist; the documented resource is `_attributes`): required `vdm_enabled` (`ENABLED` | `DISABLED`); optional `dashboard_attributes.engagement_metrics`, `guardian_attributes.optimized_shared_delivery`, `region`. Import ID literal `ses-account-vdm-attributes`.
- `aws_sesv2_account_suppression_attributes` [8]: required `suppressed_reasons` (`COMPLAINT`, `BOUNCE`); optional `region`. Import: AWS account ID. Destroy behaviour not documented (U6).
- `aws_sesv2_email_identity_policy` [9] (sending authorization, v2): required `email_identity`, `policy_name`, `policy` (JSON); optional `region`. Import `email_identity|policy_name`. Example uses `aws_sesv2_email_identity.example.arn` as `Resource`.
- Sandbox in sandbox mode: "For sending authorization, neither you nor the delegate sender can send email to non-verified email addresses." [15]

## 9. Classic family `aws_ses_*` — only what the pages say

- `aws_ses_identity_policy` [10]: `identity` (name or ARN), `name`, `policy` (suggests `aws_iam_policy_document`), `region`. Import `identity|name` (e.g. `'example.com|example'`).
- `aws_ses_domain_mail_from` [18]: `behavior_on_mx_failure` "Defaults to `UseDefaultValue`" (classic casing — v2 uses `USE_DEFAULT_VALUE`); MX required for validation, TXT may be needed for SPF; import by `domain`. 6.51.0 fixed out-of-band deletion detection [12].
- `aws_ses_domain_identity_verification` [19]: "does not represent a real-world entity in AWS"; waits for verification; `create` timeout default **45 minutes**; changing/deleting it alone has no immediate AWS effect. **No sesv2 equivalent page was found/read** (U1).
- Classic and v2 casing/value sets differ (e.g. `UseDefaultValue` vs `USE_DEFAULT_VALUE`) — do not copy values across families.

## 10. Sandbox vs production access

- Restrictions in sandbox: send only to verified addresses/domains or the mailbox simulator; 200 messages / 24 h; 1 message/second; account-level suppression bulk actions/API disabled [15].
- Request methods documented: **console** and **AWS CLI** `aws sesv2 put-account-details --production-access-enabled --mail-type TRANSACTIONAL|MARKETING --website-url … --additional-contact-email-addresses … --contact-language EN|JA` [15]. AWS Support responds within 96 hours.
- Terraform: none of the provider pages read documents a resource for production access. AWS does not say "cannot be requested via Terraform"; the claim "not possible in Terraform" is therefore **unverified** (U7). Treat as an out-of-band, per-Region step.

## 11. DMARC / SPF / DKIM DNS guidance (AWS wording only) [20]

- DMARC TXT name `_dmarc.<domain>`, example value `"v=DMARC1;p=quarantine;rua=mailto:my_dmarc_report@example.com"`.
- Roll out gradually: `p=none` (monitor) → `p=quarantine` → `p=reject`, sub-domains first, then top-level.
- SPF alignment needs a custom MAIL FROM domain and a non-strict SPF policy (`aspf=s` must not be set). DKIM alignment: DKIM domain must match From domain (relaxed alignment if sending from a subdomain). AWS: "both SPF and DKIM are necessary for DMARC to have the best chance".

## 12. AWS guidance — Security Hub controls [13] and best practices

| ID | Title | Severity | Resource | Terraform lever |
|---|---|---|---|---|
| SES.1 | SES contact lists should be tagged | Low | `AWS::SES::ContactList` | `aws_sesv2_contact_list.tags` (param `requiredTagKeys`) |
| SES.2 | SES configuration sets should be tagged | Low | `AWS::SES::ConfigurationSet` | `aws_sesv2_configuration_set.tags` |
| SES.3 | SES configuration sets should have TLS enabled for sending emails | Medium | `AWS::SES::ConfigurationSet` | `delivery_options { tls_policy = "REQUIRE" }` (Config rule `ses-sending-tls-required`) |

SES.3 rationale: "By default, Amazon SES uses opportunistic TLS"; with REQUIRE, messages are delivered only over TLS [13]. Controls "may not be available in all AWS Regions" [13].

Best practices [21][22]: use subdomains per mail type (e.g. `marketing.` vs `orders.`) because they "develop their own reputations"; authenticate with SPF and sign with DKIM; double opt-in; avoid `no-reply@` From/Reply-to; validate collected addresses; comply with anti-spam law. Numeric bounce/complaint thresholds were not on these pages (U8).

## 13. Unverified / medium-confidence items and limits

- **U1** No documented sesv2 waiter for identity verification; Terraform behaviour when `verification_status = PENDING` beyond attribute export is undocumented (unverified).
- **U2** Exact CNAME value suffix for Easy DKIM in Terraform: AWS says it is the region/identity-specific `SigningHostedZone`; the provider page exports only `tokens` (unverified how to obtain it in HCL).
- **U3** No provider page documents conflicts between managing one identity with both `aws_ses_*` and `aws_sesv2_*` (unverified).
- **U4** Whether multiple destination blocks may coexist in one `event_destination` (unverified).
- **U5** Allowed values of `default_subscription_status` besides `OPT_IN` (unverified).
- **U6** Destroy behaviour of `aws_sesv2_account_suppression_attributes` / `_vdm_attributes` (unverified).
- **U7** "Production access cannot be requested via Terraform" — no official statement; only absence of a resource (unverified).
- **U8** Bounce/complaint rate thresholds (not on pages read; unverified).
- **M1** 6.55.0 SES-free (page split across two fetch windows) — medium confidence.
- **L1** Not read: `aws_sesv2_email_identity_feedback_attributes`, templates, receipt rules, classic event destinations, data sources.
- **L2** CHANGELOG reviewed via fetch-model summaries, not line-by-line.
- **L3** `aws_sesv2_multi_region_endpoint` (6.62.0) and DEED/global identities not researched.

### Legacy-file claims found wrong or unsupported
- Legacy builds Easy DKIM CNAME values as `<token>.dkim.amazonses.com`; AWS now states the hosted-zone suffix "varies by AWS Region and identity" (e.g. `token.dkim.us-west-2.amazonses.com`) [16] — **likely wrong / outdated** (medium confidence).
- "`behavior_on_mx_failure` default **changed** to UseDefaultValue": the page states the default is `UseDefaultValue` but nothing about a change — "changed" is unsupported.
- Legacy covers only classic `aws_ses_*`; v2 is the family with configuration-set TLS, VDM and suppression options needed for SES.3.
- Legacy cites registry.terraform.io pages (JS-only, F12) as sources.

## 14. Security note

None — no instruction-like or prompt-injection text was observed in any fetched page.

## Source Bibliography

All read 2026-10-23.
1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity_mail_from_attributes.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set_event_destination.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_dedicated_ip_pool.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_contact_list.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_account_vdm_attributes.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_account_suppression_attributes.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity_policy.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_identity_policy.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
13. https://docs.aws.amazon.com/securityhub/latest/userguide/ses-controls.html
14. https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html
15. https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html
16. https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html
17. https://docs.aws.amazon.com/ses/latest/dg/mail-from.html
18. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_domain_mail_from.html.markdown
19. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_domain_identity_verification.html.markdown
20. https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html
21. https://docs.aws.amazon.com/ses/latest/dg/best-practices.html
22. https://docs.aws.amazon.com/ses/latest/dg/tips-and-best-practices.html
