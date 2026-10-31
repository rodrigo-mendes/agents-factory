# Unverified Claims and Risks — hashicorp/aws 6.x SES

Sources dated 2026-10-23 (Terraform 1.17.0 CHANGELOG: 2026-10-22). See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **Terraform 1.17.0** is stable since 2026-10-21; this skill targets `~> 1.16` (newest 1.16.x is 1.16.7, 2026-10-23). Re-verify when starting new work. Source: https://releases.hashicorp.com/terraform/
- **hashicorp/aws 6.70.0** (2026-10-23) is the latest; reference patches 6.69.0 / 6.70.0. Source: https://releases.hashicorp.com/terraform-provider-aws/
- **6.57.0 is withdrawn** from GitHub and the Registry; a constraint that resolves to it is a risk.
- **v7 is planned** — the 6.0 guide says "`s3_us_east_1_regional_endpoint` will be removed in `v7.0.0`"; no 7.x release exists. When v7 ships, create `provisioning-aws-ses-v7`.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | No documented v2 verification-wait resource; Terraform behaviour with `verification_status = PENDING` beyond exporting the attribute | (unverified) — ask how downstream resources should wait |
| U2 | How to obtain the Easy DKIM CNAME value suffix in HCL (the identity page exports `tokens` only) | (unverified) — ask first |
| U3 | One identity managed by both `aws_ses_*` and `aws_sesv2_*` | (unverified) — unconfirmed; ask first |
| U4 | Several destination blocks in one `event_destination` | (unverified) — one block shown |
| U5 | Allowed `default_subscription_status` values besides `OPT_IN` | (unverified) |
| U6 | Destroy behaviour of `aws_sesv2_account_suppression_attributes` and `aws_sesv2_account_vdm_attributes` | (unverified) |
| U7 | Whether a provider resource exists for leaving the sandbox (production access); AWS documents console and CLI | (unverified) |
| U8 | Numeric bounce/complaint thresholds | (unverified) |
| U9 | List-vs-set indexing of `dkim_signing_attributes[0].tokens` and `delivery_options[0].tls_policy` in HCL | (unverified) — tagged once per blueprint header |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M4 | CHANGELOG SES entries: 6.51.0 deletion-detection fix for `aws_ses_domain_mail_from`; 6.62.0 `aws_sesv2_multi_region_endpoint` | (medium confidence) |
| M5 | `PENDING` is a documented `verification_status` value; whether creation returns before verification completes is not documented | (medium confidence) |
| M2 | The 6.0 upgrade guide has no SES entries; CHANGELOG 6.48.0–6.70.0 has no SES breaking changes | (medium confidence, absence of evidence) |
| M6 | That `delivery_options { tls_policy }` is the argument Security Hub SES.3 checks is not stated by either page | (medium confidence) |
| M3 | A fixed Easy DKIM CNAME suffix `<token>.dkim.amazonses.com` is likely outdated; AWS documents a Region/identity-specific suffix | (medium confidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | Not covered: `aws_sesv2_email_identity_feedback_attributes`, templates, receipt rules, classic event destinations, data sources |
| L2 | CHANGELOG coverage of SES entries (6.48.0–6.70.0) may be incomplete; 6.51.0 (2026-06-17) and 6.62.0 entries are tagged (medium confidence) |
| L3 | `aws_sesv2_multi_region_endpoint` (new in 6.62.0, 2026-08-26) and global identities are not covered |
| — | The resource is `aws_sesv2_account_vdm_attributes`; the name `aws_sesv2_account_vdm_options` is not documented |
| — | Resource pages cited are the provider documentation on the `main` branch and may run slightly ahead of 6.70.0 |
| — | The `behavior_on_mx_failure` page confirms the classic default `UseDefaultValue` and v2 values `USE_DEFAULT_VALUE` / `REJECT_MESSAGE`; v2 states no default |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | always-do-identity-dns.md header; never-do-ses-config.md header; always-do-sending-config.md §4 — list-vs-set indexing | U9 |
| (medium confidence) | SKILL.md ⚠️ Ask First — Waiting for verification; always-do-identity-dns.md §2 | M5 |
| (medium confidence) | SKILL.md 5.x → 6.x Migration (SES), 6.51.0 and 6.62.0 bullets | M4 |
| (unverified) | SKILL.md ⚠️ Ask First — Waiting for verification; always-do-identity-dns.md §2 | U1 |
| (unverified) | SKILL.md ⚠️ Ask First — DKIM CNAME value; always-do-identity-dns.md §2 | U2 |
| (medium confidence) | SKILL.md ⚠️ Ask First — DKIM CNAME value (fixed suffix likely outdated) | M3 |
| (medium confidence) | SKILL.md Quick Reference — Configuration set TLS argument | M6 |
| (unverified) | SKILL.md ⚠️ Ask First — Both families on one identity; SKILL.md Classic aws_ses family; always-do-classic-family.md §9 | U3 |
| (unverified) | SKILL.md ⚠️ Ask First — Event destination shape; always-do-sending-config.md §5 | U4 |
| (unverified) | SKILL.md ⚠️ Ask First — Contact-list topics; always-do-sending-config.md §6 | U5 |
| (unverified) | SKILL.md ⚠️ Ask First — Account-level resources; always-do-sending-config.md §7 | U6 |
| (unverified) | SKILL.md ⚠️ Ask First — Sandbox and production access | U7 |
| (unverified) | SKILL.md ⚠️ Ask First — Bounce/complaint thresholds | U8 |
| (unverified) | SKILL.md Classic aws_ses family (v2 verification equivalent) | U1 |
| (medium confidence, absence of evidence) | SKILL.md 5.x → 6.x Migration (SES), 6.0 guide and CHANGELOG lines | M2 |

## Source Bibliography

All dated 2026-10-23 unless noted.

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
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_domain_mail_from.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_domain_identity_verification.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
16. https://docs.aws.amazon.com/securityhub/latest/userguide/ses-controls.html
17. https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html
18. https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html
19. https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html
20. https://docs.aws.amazon.com/ses/latest/dg/mail-from.html
21. https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html
22. https://docs.aws.amazon.com/ses/latest/dg/best-practices.html
23. https://docs.aws.amazon.com/ses/latest/dg/tips-and-best-practices.html
24. https://releases.hashicorp.com/terraform/ and https://raw.githubusercontent.com/hashicorp/terraform/v1.16/CHANGELOG.md
25. https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (2026-10-23)
26. https://releases.hashicorp.com/terraform-provider-aws/
27. https://developer.hashicorp.com/terraform/language/backend/s3
28. https://developer.hashicorp.com/terraform/language/expressions/version-constraints
29. https://developer.hashicorp.com/terraform/language/tests and https://developer.hashicorp.com/terraform/language/tests/mocking
