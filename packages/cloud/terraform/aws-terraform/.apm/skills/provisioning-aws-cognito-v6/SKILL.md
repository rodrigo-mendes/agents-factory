---
name: provisioning-aws-cognito-v6
description: "Cognito Terraform (aws 6.x): user pools, app clients, domains, identity pools. Use when writing HCL for Cognito sign-in. Not for API Gateway, ACM, SES, Lambda, IAM, Route 53."
---

# Provisioning AWS Cognito with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = the 6.x major line of hashicorp/aws (reference patch 6.69.0 / 6.70.0) + **Terraform ~> 1.16**.
> A new major (v7) is a new skill. Sources read **2026-10-23** unless stated. Claims tagged (unverified) or
> (medium confidence) were not fully confirmed against an official page.

## Version Context

| Item | Value | Source (read 2026-10-23) |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"`; newest 1.16.x is 1.16.7 (2026-10-23) | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest 6.70.0 (2026-10-23); this skill uses `version = "~> 6.69"` | https://releases.hashicorp.com/terraform-provider-aws/ |
| Withdrawn | 6.57.0 was withdrawn from GitHub and the Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Region | Regional resources accept optional `region`; changing it forces replacement; import with `id@region` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown |
| Identity-based import | `identity` block requires Terraform >= 1.12.0 | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown |
| Root vs module constraints | Root modules use `~>`; reusable modules set only a minimum (`>=`) | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable (2026-10-21) but is not the target of this skill; re-verify when starting new work.
  https://releases.hashicorp.com/terraform/ (2026-10-23); https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (2026-10-23)
- 6.57.0 is withdrawn; v7 is planned and no 7.x release exists. A v7 skill must be new.
  https://releases.hashicorp.com/terraform-provider-aws/ (2026-10-23)

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Always-do pool: [terraform block, user pool, MFA, email, schema](./blueprints/always-do-pool.md)
- Always-do client/domain: [app client, custom domain, identity pool](./blueprints/always-do-client-domain.md)
- Never-do pool/domain: [attributes, SMS removal, MFA, certificate Region, withdrawn version](./blueprints/never-do-pool-domain.md)
- Never-do client/OAuth: [OAuth flags, redirect URI, auth flows, http callbacks](./blueprints/never-do-client-oauth.md)
- Hubs: [always-do-patterns](./blueprints/always-do-patterns.md) · [never-do-patterns](./blueprints/never-do-patterns.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [5.x → 6.x Migration](#5x--6x-migration-cognito) · [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Constrain root modules with `~>`; this skill's targets are `~> 1.16` (CLI) and `~> 6.69` (aws).**
  See [pool §1](./blueprints/always-do-pool.md#1-terraform-block-and-region).
  https://developer.hashicorp.com/terraform/language/expressions/version-constraints
- **Set the optional `region` argument only to target another Region; Cognito resources document it.**
  See [pool §1](./blueprints/always-do-pool.md#1-terraform-block-and-region).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown
- **Choose either `username_attributes` or `alias_attributes` on a user pool — the two conflict.**
  See [pool §2](./blueprints/always-do-pool.md#2-user-pool-sign-in-mfa-recovery-and-email).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown
- **With `mfa_configuration = "ON"` or `"OPTIONAL"`, set at least one of `email_mfa_configuration`, `sms_configuration`, `software_token_mfa_configuration`.**
  See [pool §2](./blueprints/always-do-pool.md#2-user-pool-sign-in-mfa-recovery-and-email).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown
- **Give `email_mfa_configuration` an `email_configuration` block.**
  See [pool §2](./blueprints/always-do-pool.md#2-user-pool-sign-in-mfa-recovery-and-email).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown
- **Set `email_sending_account = "DEVELOPER"` and `source_arn` whenever `from_email_address` is set.**
  See [pool §2](./blueprints/always-do-pool.md#2-user-pool-sign-in-mfa-recovery-and-email).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown
- **Treat `schema` as add-only — attributes can be added, but not modified or removed.**
  See [pool §3](./blueprints/always-do-pool.md#3-schema-password-policy-and-deletion-protection).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown
- **`deletion_protection` takes `ACTIVE` or `INACTIVE` (default `INACTIVE`); deactivate it before deleting the pool.**
  See [pool §3](./blueprints/always-do-pool.md#3-schema-password-policy-and-deletion-protection).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown
- **Set `allowed_oauth_flows_user_pool_client = true` before `allowed_oauth_flows`/`allowed_oauth_scopes`/URLs on a client.**
  See [client §4](./blueprints/always-do-client-domain.md#4-user-pool-client-oauth).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_client.html.markdown
- **Keep `default_redirect_uri` inside `callback_urls`.**
  See [client §4](./blueprints/always-do-client-domain.md#4-user-pool-client-oauth).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_client.html.markdown
- **Use an ISSUED ACM certificate in us-east-1 as `certificate_arn` for a custom domain.**
  See [domain §5](./blueprints/always-do-client-domain.md#5-user-pool-domain-prefix-and-custom).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_domain.html.markdown
- **Set `ambiguous_role_resolution` on every `role_mapping` of type `Token` or `Rules`.**
  See [identity §6](./blueprints/always-do-client-domain.md#6-identity-pool-and-roles-attachment).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_identity_pool_roles_attachment.html.markdown
- **Create a domain on the pool before `aws_cognito_user_pool_ui_customization`.**
  See [domain §5](./blueprints/always-do-client-domain.md#5-user-pool-domain-prefix-and-custom).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_ui_customization.html.markdown

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Plan tier and threat protection | `user_pool_tier` is `LITE`, `ESSENTIALS` or `PLUS`; threat protection (including adaptive authentication) is a Plus-plan feature ([AWS](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-threat-protection.html)). `user_pool_add_ons.advanced_security_mode` (`OFF`/`AUDIT`/`ENFORCED`) is still documented ([provider](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown)); AWS recommends audit mode for at least 2 weeks before full-function. Pricing not covered. | "Which tier, and audit or enforced threat protection?" |
| Sign-in identifiers | AWS: "After you create a user pool, you can't change this setting." ([AWS](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html)). Whether the provider forces replacement is not stated on its page (unverified). | "Email, phone, or alias sign-in — confirmed final for this pool?" |
| MFA mode | `OFF` (default), `ON`, `OPTIONAL` ([provider](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown)). Security Hub Cognito.5 applies to password-only pools ([page](https://docs.aws.amazon.com/securityhub/latest/userguide/cognito-controls.html)); whether `OPTIONAL` passes it is (unverified). | "Is MFA required (`ON`) or optional?" |
| Email MFA recovery entries | Page: `email_mfa_configuration` "requires at least 2 `account_recovery_setting` entries"; the page's example uses one `account_recovery_setting` block with two `recovery_mechanism` blocks. The two readings differ (medium confidence) — see [pool §2](./blueprints/always-do-pool.md#2-user-pool-sign-in-mfa-recovery-and-email). ([provider](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown)) | "Use the page's example shape?" |
| Deletion protection | `ACTIVE` blocks deletion; Security Hub Cognito.6 checks that deletion protection is enabled ([page](https://docs.aws.amazon.com/securityhub/latest/userguide/cognito-controls.html)). | "Set `deletion_protection = \"ACTIVE\"`?" |
| Email sender | `COGNITO_DEFAULT` or `DEVELOPER` (SES) ([provider](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown)); SES identity belongs to provisioning-aws-ses-v6. | "Built-in sender or SES?" |
| Lambda triggers | `lambda_config` accepts trigger ARNs ([provider](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown)); the invoke permission (`cognito-idp.amazonaws.com`) is (unverified) — see provisioning-aws-lambda-v6. | "Which triggers, and who owns the Lambda?" |
| Client secret | `generate_secret`; AWS: for server-side/M2M clients, `client_credentials` requires one ([AWS](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html)). Whether the provider marks `client_secret` sensitive is (unverified) — mark outputs `sensitive = true`. | "Is this a confidential client?" |
| Token revocation | AWS activates revocation by default on new clients ([AWS](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html)); the provider default for `enable_token_revocation` is not stated (medium confidence). | "Set `enable_token_revocation` explicitly?" |
| Schema diffs | `lifecycle { ignore_changes = [schema] }` is a common mitigation, not documented on the provider page (medium confidence). | "Accept `ignore_changes` on `schema`?" |
| Identity pool guests | Security Hub Cognito.2: identity pools should not allow unauthenticated identities ([page](https://docs.aws.amazon.com/securityhub/latest/userguide/cognito-controls.html)). | "Is `allow_unauthenticated_identities = true` needed?" |
| API Gateway authorizer | Authorizer arguments are deferred to provisioning-aws-api-gateway-v6 (unverified). | "Which authorizer type consumes this pool?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `username_attributes` and `alias_attributes` together — they conflict. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown)) | Set only one of the two |
| Remove `sms_configuration` expecting an in-place update — "the SMS configuration cannot be removed without recreating the Cognito User Pool". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown)) | Plan to recreate the pool; the page says to use `taint` to force recreation |
| Set `mfa_configuration` to `ON`/`OPTIONAL` with no MFA method block. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown)) | Add `email_mfa_configuration`, `sms_configuration` or `software_token_mfa_configuration` |
| Use a certificate outside us-east-1 for a custom domain — AWS: it fronts a CloudFront distribution. ([source](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html)) | Use an ISSUED ACM certificate in us-east-1 |
| Set `allowed_oauth_flows` without `allowed_oauth_flows_user_pool_client = true`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_client.html.markdown)) | Set the flag to `true` first |
| Point `default_redirect_uri` at a URL absent from `callback_urls`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_client.html.markdown)) | List the URI in `callback_urls` |
| Combine legacy `explicit_auth_flows` values (`ADMIN_NO_SRP_AUTH`, `CUSTOM_AUTH_FLOW_ONLY`, `USER_PASSWORD_AUTH`) with `ALLOW_*` values. ([source](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html)) | Use either the legacy values or the `ALLOW_*` values in one client, not both |
| Combine `client_credentials` with other `allowed_oauth_flows` — it must be the only flow. ([source](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html)) | Set `allowed_oauth_flows = ["client_credentials"]` on that client |
| Use `http://` callback URLs other than `http://localhost`, `http://127.0.0.1`, `http://[::1]` — HTTPS is required otherwise. ([source](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html)) | Use HTTPS callback URLs |
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` |

## Quick Reference

Sources read 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| Pool required argument | `name`; import ID = pool ID (e.g. `us-west-2_abc123`, example) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown |
| Client required / import | `name`, `user_pool_id`; import `<user_pool_id>/<client_id>` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_client.html.markdown |
| Domain required / import | `domain`, `user_pool_id`; import = the domain value | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_domain.html.markdown |
| `managed_login_version` | `1` = classic hosted UI, `2` = managed login | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_domain.html.markdown |
| Domain exports for DNS | `cloudfront_distribution`, `cloudfront_distribution_zone_id` (Route 53 alias; `evaluate_target_health = false`) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_domain.html.markdown |
| Custom domain prerequisites | Parent domain must resolve via an A record (SOA alone fails); public hosted zone only; propagation about 60 s (Route 53), up to 1 h for a certificate change | https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html |
| Token validity | Access/ID 5 min–1 day, refresh 60 min–10 years; units via `token_validity_units` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_client.html.markdown |
| Security Hub Cognito.1–6 | All Medium: threat protection full-function (1), no unauthenticated identity pools (2), password policy (3), threat protection custom auth (4), MFA (5), deletion protection (6) | https://docs.aws.amazon.com/securityhub/latest/userguide/cognito-controls.html |
| Cognito.3 | Page: min length 8, four character classes, temporary password validity <= 7 days (default) | https://docs.aws.amazon.com/securityhub/latest/userguide/cognito-controls.html |
| Cognito.1/4 levers | `user_pool_tier = "PLUS"` + `advanced_security_mode = "ENFORCED"`; `custom_auth_mode = "ENFORCED"` (medium confidence, inference) | https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-threat-protection.html |

### Other resources

Each row: provider page `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/<resource-name-without-aws_>.html.markdown`.

| Resource | Required / key notes | Import ID |
|---|---|---|
| `aws_cognito_resource_server` | `identifier`, `name`, `user_pool_id`; `scope { scope_name, scope_description }`; exports `scope_identifiers` | `<user_pool_id>\|<identifier>` |
| `aws_cognito_user_group` | `name`, `user_pool_id`; optional `description`, `precedence`, `role_arn` | `<user_pool_id>/<name>` |
| `aws_cognito_identity_provider` | `user_pool_id`, `provider_name`, `provider_type`; `provider_details`, `attribute_mapping`, `idp_identifiers` | `<user_pool_id>:<provider_name>` |
| `aws_cognito_identity_pool` | `identity_pool_name`, `allow_unauthenticated_identities`; `cognito_identity_providers`, `supported_login_providers` | `region:GUID` |
| `aws_cognito_identity_pool_roles_attachment` | `identity_pool_id`, `roles` (`authenticated`/`unauthenticated`); `role_mapping` | identity pool ID |
| `aws_cognito_user_pool_ui_customization` | `user_pool_id` + `css` or `image_file`; page: "the user pool must have a domain associated with it" | `<user_pool_id>,<client_id>` |
| `aws_cognito_managed_user_pool_client` | `user_pool_id` + `name_pattern` or `name_prefix`; adopts a client created by another AWS service, "does not create or delete" it | `<user_pool_id>/<client_id>` |

## 5.x → 6.x Migration (Cognito)

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown (2026-10-23)

- **`aws_cognito_user_in_group`**: "For the `id`, use a comma-delimited string concatenating `user_pool_id`, `group_name`, and `username`." This is the only Cognito change in 6.0.0.
- No other `aws_cognito_*` entries in the 6.0 guide or in the CHANGELOG from 6.48.0 to 6.70.0 (medium confidence, absence of evidence).
- Upgrade path (guide wording): "Before upgrading to version `6.0.0`, first upgrade to the latest available `5.x` version of the provider."
  Run a plan that completes "without errors or unexpected changes", then update version constraints to allow the `6.x` series
  (this skill uses `~> 6.69`) and run `terraform init -upgrade` "to download the new version".
- v7 is planned: the guide says "`s3_us_east_1_regional_endpoint` will be removed in `v7.0.0`"; no 7.x release exists.

## External Resources

- Provider releases: https://releases.hashicorp.com/terraform-provider-aws/
- Provider CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- AWS Cognito — custom domain: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html
- AWS Cognito — threat protection: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-threat-protection.html
- AWS Cognito — security best practices: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html
- Security Hub Cognito controls: https://docs.aws.amazon.com/securityhub/latest/userguide/cognito-controls.html
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
