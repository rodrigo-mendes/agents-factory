# Unverified Claims and Risks — hashicorp/aws 6.x Cognito

Sources read 2026-10-23 (Terraform 1.17.0 CHANGELOG read 2026-10-22). See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current major**: latest 6.70.0 (2026-10-21); this skill uses `~> 6.69`. Re-verify when
  starting new work. Source: https://releases.hashicorp.com/terraform-provider-aws/
- **Terraform 1.17.0 is stable (2026-10-21)** and is not the target of this skill (target `~> 1.16`; newest 1.16.x is
  1.16.7, 2026-10-22). Re-verify before moving. Sources: https://releases.hashicorp.com/terraform/ ,
  https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md
- **6.57.0 is withdrawn** from GitHub and the Registry; never pin it.
- **v7 is planned**: the 6.0 upgrade guide says "`s3_us_east_1_regional_endpoint` will be removed in `v7.0.0`"; no 7.x
  release exists. When v7 ships, create a new skill `provisioning-aws-cognito-v7`.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Whether changing `username_attributes`/`alias_attributes` forces replacement — not stated on the provider page | (unverified) — SKILL.md quotes the AWS sentence instead |
| U2 | `username_configuration.case_sensitive` — not checked against the current provider page | (unverified) — not used in this skill |
| U3 | `password_policy` defaults — the provider page lists none | (unverified) — set the arguments explicitly |
| U4 | Lambda invoke permission requirement for triggers (`cognito-idp.amazonaws.com`) | (unverified) — see provisioning-aws-lambda-v6 |
| U5 | Whether the provider marks `client_secret` sensitive | (unverified) — mark outputs `sensitive = true` |
| U6 | Whether `generate_secret` forces replacement — not stated | (unverified) |
| U7 | Provider argument for the custom-domain minimum TLS policy — not seen on the page | (unverified) |
| U8 | Whether Security Hub Cognito.5 passes with `mfa_configuration = "OPTIONAL"` | (unverified) |
| U9 | API Gateway authorizer arguments for a Cognito pool | (unverified) — see provisioning-aws-api-gateway-v6 |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | CHANGELOG 6.48.0–6.70.0 lists no `aws_cognito_*` entries; part of the 6.55.0 section was not read (coverage limit) | (medium confidence, absence of evidence) |
| M6 | `email_mfa_configuration` recovery entries: page wording "at least 2 `account_recovery_setting` entries" vs its example of one block with two `recovery_mechanism` blocks | (medium confidence) — neither reading asserted |
| M2 | `lifecycle { ignore_changes = [schema] }` as a schema-diff mitigation — not provider-documented | (medium confidence) |
| M3 | Provider default of `enable_token_revocation` — AWS enables revocation by default on new clients | (medium confidence) |
| M4 | Mapping of Security Hub Cognito.1/4 to `user_pool_tier` + `advanced_security_mode` / `custom_auth_mode` | (medium confidence) — inference |
| M5 | `region = "us-east-1"` on `aws_acm_certificate` as an alternative to a provider alias | (medium confidence) — inference from the enhanced-region guide |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | Pricing and MAU tiers not covered |
| L2 | Release in which `user_pool_tier`, `sign_in_policy`, `web_authn_configuration`, `refresh_token_rotation`, `email_mfa_configuration` were introduced not located (before 6.48.0) |
| L3 | `aws_cognito_managed_login_branding`, `aws_cognito_log_delivery_configuration`, `aws_cognito_user`, `aws_cognito_user_in_group`, risk configuration and data sources not covered |
| L4 | User pool replication / multi-Region not covered |

## Tag to register mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First — Sign-in identifiers (provider replacement behavior) | U1 |
| (unverified) | SKILL.md Ask First — MFA mode (Cognito.5 with OPTIONAL) | U8 |
| (unverified) | SKILL.md Ask First — Lambda triggers (invoke permission) | U4 |
| (unverified) | SKILL.md Ask First — Client secret (sensitivity marking) | U5 |
| (unverified) | SKILL.md Ask First — API Gateway authorizer | U9 |
| (medium confidence) | SKILL.md Ask First — Token revocation | M3 |
| (medium confidence) | SKILL.md Ask First — Schema diffs | M2 |
| (medium confidence, inference) | SKILL.md Quick Reference — Cognito.1/4 levers | M4 |
| (medium confidence, absence of evidence) | SKILL.md 5.x → 6.x Migration — no other `aws_cognito_*` entries | M1 |
| (medium confidence) | always-do-client-domain.md §5 — provider alias and `region` on `aws_acm_certificate` | M5 |
| (medium confidence) | SKILL.md Ask First — Email MFA recovery entries; always-do-pool.md §2 | M6 |

## Source Bibliography

All read 2026-10-23 (provider docs base: `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/`).

1. `r/cognito_user_pool.html.markdown`
2. `r/cognito_user_pool_client.html.markdown`
3. `r/cognito_user_pool_domain.html.markdown`
4. `r/cognito_identity_pool.html.markdown`
5. `r/cognito_identity_pool_roles_attachment.html.markdown`
6. `r/cognito_identity_provider.html.markdown`
7. `r/cognito_resource_server.html.markdown`
8. `r/cognito_user_group.html.markdown`
9. `r/cognito_user_pool_ui_customization.html.markdown`
10. `r/cognito_managed_user_pool_client.html.markdown`
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.57.0 withdrawn; no Cognito entries 6.48–6.70
12. `guides/version-6-upgrade.html.markdown` — `aws_cognito_user_in_group` import ID; upgrade path; v7 note
13. `guides/enhanced-region-support.html.markdown` — optional `region`
14. https://docs.aws.amazon.com/securityhub/latest/userguide/cognito-controls.html
15. https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html
16. https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html
17. https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-threat-protection.html
18. https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html
19. https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html
20. https://releases.hashicorp.com/terraform/ ; https://releases.hashicorp.com/terraform-provider-aws/
21. https://developer.hashicorp.com/terraform/language/expressions/version-constraints
