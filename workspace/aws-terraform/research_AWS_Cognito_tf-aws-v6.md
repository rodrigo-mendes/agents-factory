# Research — AWS Cognito with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `cognito`, P4 fan-out, flat — no sub-agents).
> Regional service: every in-scope resource documents the optional `region` argument (F5); none is in the F14 global list.
> Registry pages render JS-only (F12); upstream raw markdown on `main` is the resource-doc source.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_Cognito_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL). Claims found wrong are listed in §9.
> Every URL below was read 2026-10-23; numbers in [brackets] refer to the Source Bibliography.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"`; newest 1.16.x = 1.16.7 | F1 |
| Terraform 1.17.0 | Stable, NOT the target | F2 |
| hashicorp/aws | latest 6.70.0; constraint `version = "~> 6.69"`; no 7.x | F3, F18 |
| Withdrawn | 6.57.0 — never pin | F4 |
| Region | Regional resources take optional `region`; changing it forces replacement; import `id@region` | F5 |
| Identity-based import | `identity` block needs Terraform >= 1.12.0 | F11 |
| Upgrade path 5.x → 6.0 | latest 5.x first, clean plan, `init -upgrade` | F17 |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

## 2. Provider 6.x changes for Cognito

- **6.0.0 upgrade guide** [12]: the only Cognito item is `aws_cognito_user_in_group` — "For the `id`, use a comma-delimited string concatenating `user_pool_id`, `group_name`, and `username`." No arguments removed/renamed for any other `aws_cognito_*` resource (F13).
- **CHANGELOG 6.48.0 → 6.70.0** [11]: no `aws_cognito_*` entries found in 6.70.0 (2026-10-21) down to 6.48.0 (2026-06-03). Section boundary around 6.55.0 (2026-07-15) was split across two reads (M1).
- Feature arguments `user_pool_tier`, `sign_in_policy`, `web_authn_configuration`, `refresh_token_rotation`, `email_mfa_configuration` are all documented on current resource pages [1][2]; the release that introduced each was not located in the 6.48–6.70 range (pre-6.48) (L2).

## 3. `aws_cognito_user_pool` [1]

Required: `name`. Import ID: user pool ID, e.g. `us-west-2_abc123` (import block or `terraform import`).
Exported: `arn`, `creation_date`, `custom_domain`, `domain`, `endpoint`, `estimated_number_of_users`, `id`, `last_modified_date`, `tags_all`.

**Sign-in identifiers**
- `username_attributes` (`email`, `phone_number`) **conflicts with** `alias_attributes` (`phone_number`, `email`, `preferred_username`) [1].
- Immutability: AWS — "After you create a user pool, you can't change this setting." [14]. The provider page does not state forces-new for either argument (U1) — treat as a create-time decision.
- `auto_verified_attributes`: `email`, `phone_number` [1]. AWS recommends auto-verification when email/phone are aliases [14].
- `username_configuration.case_sensitive` appears in the legacy example; not re-checked on [1] (U2).

**password_policy** — `minimum_length`, `require_lowercase|numbers|symbols|uppercase`, `temporary_password_validity_days`, `password_history_size` (0–24, 0 = not enforced; requires advanced security features active) [1]. Page lists no defaults (U3). Security Hub Cognito.3 checks length >= 8, all four character classes, temp validity <= 7 days by default [13].

**MFA**
- `mfa_configuration`: `OFF` (default), `ON`, `OPTIONAL`. `ON`/`OPTIONAL` require at least one of `email_mfa_configuration`, `sms_configuration`, `software_token_mfa_configuration` [1].
- `software_token_mfa_configuration { enabled = true }` effective only with `ON`/`OPTIONAL`; to disable without `sms_configuration`, set `OFF` **and** remove the block [1].
- `email_mfa_configuration` (`message` must contain `{####}`, `subject`) requires >= 2 `account_recovery_setting` entries and an `email_configuration` block [1].
- `sms_configuration` (`external_id`, `sns_caller_arn` required; `sns_region`). WARNING: "Due to Cognito API restrictions, the SMS configuration cannot be removed without recreating the Cognito User Pool." Drift detection is disabled for this block; use `taint` to force recreation [1].

**account_recovery_setting** — `recovery_mechanism { name, priority }`; `name` ∈ `verified_email`, `verified_phone_number`, `admin_only`; priority 1 = highest [1].

**email_configuration** — `email_sending_account`: `COGNITO_DEFAULT` (built-in) or `DEVELOPER` (SES). `DEVELOPER` is required if `from_email_address` is set; `source_arn` (SES verified identity ARN) required with `DEVELOPER`. Also `configuration_set`, `reply_to_email_address` [1].

**schema** (repeatable) — `name`, `attribute_data_type` (`Boolean|Number|String|DateTime`) required; `number_attribute_constraints` / `string_attribute_constraints` required for Number/String and "prevent resource recreation" when set; optional `developer_only_attribute`, `mutable`, `required`. "Attributes can be added, but not modified or removed." Max 50 [1]. AWS: custom attributes "are permanent" — cannot rename, delete, or change type/mutability/length; required-ness cannot be switched after creation [14].
- `lifecycle { ignore_changes = [schema] }` is a common mitigation for schema perpetual diffs; not documented on [1] (M2).

**lambda_config** — `create_auth_challenge`, `custom_message`, `define_auth_challenge`, `post_authentication`, `post_confirmation`, `pre_authentication`, `pre_sign_up`, `pre_token_generation` (legacy), `user_migration`, `verify_auth_challenge_response`; `pre_token_generation_config { lambda_arn, lambda_version = V1_0|V2_0|V3_0 }` (ARN must match `pre_token_generation` if both set); `custom_email_sender` / `custom_sms_sender` { `lambda_arn`, `lambda_version = "V1_0"` }; `kms_key_id` for custom sender encryption [1]. Lambda invoke permission (`aws_lambda_permission`, principal `cognito-idp.amazonaws.com`) is required by the Lambda trigger model (U4 — not re-verified this unit; see Lambda unit).

**Other**
- `deletion_protection`: `ACTIVE` | `INACTIVE` (default); deactivate before deleting [1].
- `user_pool_tier`: `LITE` | `ESSENTIALS` | `PLUS` [1]. Threat protection is a Plus-plan feature [16]; `ALLOW_USER_AUTH` requires Essentials or higher [15].
- `sign_in_policy.allowed_first_auth_factors`: `PASSWORD`, `EMAIL_OTP`, `SMS_OTP`, `WEB_AUTHN` [1].
- `web_authn_configuration { relying_party_id, user_verification = required|preferred }` [1].
- `user_pool_add_ons { advanced_security_mode = OFF|AUDIT|ENFORCED; advanced_security_additional_flows { custom_auth_mode = AUDIT|ENFORCED (default AUDIT) } }` — still documented [1]; the AWS API still enables threat protection via `UserPoolAddOns.AdvancedSecurityMode` on a Plus pool [16].
- `admin_create_user_config { allow_admin_create_user_only; invite_message_template { email_message, email_subject, sms_message } }` (messages need `{username}` and `{####}`) [1].
- `verification_message_template`: `default_email_option` `CONFIRM_WITH_CODE` (default) | `CONFIRM_WITH_LINK`; `email_message` (`{####}`), `email_message_by_link` (`{##Click Here##}`), `email_subject(_by_link)`, `sms_message`; conflict with top-level `email_verification_message`/`email_verification_subject`/`sms_verification_message` [1].
- `user_attribute_update_settings.attributes_require_verification_before_update` (`email`, `phone_number`) — each value must also be in `auto_verified_attributes` [1].
- `tags` supported (exported `tags_all`) [1].

## 4. `aws_cognito_user_pool_client` [2]

Required: `name`, `user_pool_id`. Import: `<user_pool_id>/<client_id>`. Exported: `id`, `client_secret` (sensitivity not stated, U5). No NOTE/WARNING blocks; page points to `aws_cognito_managed_user_pool_client` for service-created clients.

- `generate_secret` (bool); forces-new not stated on [2] (U6). AWS: secrets are auto-generated, for server-side/M2M clients; `client_credentials` requires a secret [15][18].
- `explicit_auth_flows`: `ALLOW_USER_AUTH`, `ALLOW_USER_SRP_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH`, `ALLOW_USER_PASSWORD_AUTH`, `ALLOW_ADMIN_USER_PASSWORD_AUTH`, `ALLOW_CUSTOM_AUTH`, plus legacy `ADMIN_NO_SRP_AUTH`, `CUSTOM_AUTH_FLOW_ONLY`, `USER_PASSWORD_AUTH` [2]. AWS: legacy values cannot be combined with `ALLOW_*`; unset = `ALLOW_REFRESH_TOKEN_AUTH`, `ALLOW_USER_SRP_AUTH`, `ALLOW_CUSTOM_AUTH` [15].
- OAuth: `allowed_oauth_flows_user_pool_client = true` must be set before `allowed_oauth_flows` (`code|implicit|client_credentials`), `allowed_oauth_scopes` (`phone|email|openid|profile|aws.cognito.signin.user.admin` + resource-server scopes), `callback_urls`, `logout_urls`; `default_redirect_uri` must be in `callback_urls` [2]. AWS: HTTPS required except `http://localhost`, `http://127.0.0.1`, `http://[::1]` (testing); `client_credentials` must be the only flow when used [15].
- `supported_identity_providers`: `COGNITO`, `Facebook`, `Google`, `SignInWithApple`, `LoginWithAmazon` or SAML/OIDC provider names (`aws_cognito_identity_provider.provider_name`) [2][15]. Removing `COGNITO` does not block SDK auth — only WAF does [15].
- Token validity: access/id 5 min–1 day (default unit hours), refresh 60 min–10 years (default unit days); `token_validity_units { access_token, id_token, refresh_token }` ∈ seconds|minutes|hours|days [2]. AWS defaults: access/id 1 h, refresh 30 days [15].
- `auth_session_validity`: 3–15 min, default 3 [2].
- `prevent_user_existence_errors`: values `LEGACY|ENABLED`, API default `LEGACY` [15] (provider page lists no values).
- `enable_token_revocation`: AWS activates it by default on new clients [15]; provider-side default not stated (M3).
- `refresh_token_rotation { feature = ENABLED|DISABLED; retry_grace_period_seconds = 0..60 }` [2]; rotation requires `GetTokensFromRefreshToken` [15].
- `enable_propagate_additional_user_context_data` — only on clients with a secret [15].
- `read_attributes` / `write_attributes`: unset write = write to all standard attributes; remove authorization-relevant attributes from every client's write list [14][15].
- `analytics_configuration` (`application_arn` xor `application_id` + `external_id`/`role_arn`, `user_data_shared`) [2].

## 5. `aws_cognito_user_pool_domain` [3]

Required: `domain`, `user_pool_id`. Optional: `certificate_arn`, `managed_login_version` (`1` classic hosted UI, `2` managed login), `region`.
- Prefix domain: `domain = "auth"` (prefix only). Custom domain: FQDN + `certificate_arn` of an **ISSUED ACM cert in us-east-1** [3]; AWS: us-east-1 regardless of pool Region because it fronts a CloudFront distribution [17]. Provision the cert via a `us-east-1` provider alias or `region = "us-east-1"` on `aws_acm_certificate` (F5; medium confidence for the per-resource form, same reasoning as F16).
- AWS prerequisites [17]: parent domain must resolve via an **A record** (SOA alone fails); public hosted zone only; managed login v2 requires min TLS `TLS_V1_2_2021`; certificate replacement takes up to 1 hour; `/.well-known/openid-configuration` served only on the custom domain. `SecurityPolicy` (min TLS) exists in the API; a matching provider argument was not seen on [3] (U7).
- Exported: `aws_account_id`, `cloudfront_distribution`, `cloudfront_distribution_arn`, `cloudfront_distribution_zone_id`, `s3_bucket`, `version`. Route 53 alias: `name = cloudfront_distribution`, `zone_id = cloudfront_distribution_zone_id`, `evaluate_target_health = false` [3].
- Import: the domain value, e.g. `auth.example.org` [3].

## 6. Other in-scope resources

| Resource | Required | Key notes | Import ID |
|---|---|---|---|
| `aws_cognito_resource_server` [7] | `identifier`, `name`, `user_pool_id` | `scope { scope_name, scope_description }`; exported `scope_identifiers` = `identifier/scope_name` | `<user_pool_id>\|<identifier>` |
| `aws_cognito_user_group` [8] | `name`, `user_pool_id` | `description`, `precedence`, `role_arn` | `<user_pool_id>/<name>` |
| `aws_cognito_identity_provider` [6] | `user_pool_id`, `provider_name`, `provider_type` | `provider_details` (map, e.g. Google `client_id`/`client_secret`/`authorize_scopes`), `attribute_mapping`, `idp_identifiers`; valid types only via API link | `<user_pool_id>:<provider_name>` |
| `aws_cognito_identity_pool` [4] | `identity_pool_name`, `allow_unauthenticated_identities` | `allow_classic_flow` (default false), `cognito_identity_providers { client_id, provider_name, server_side_token_check }`, `supported_login_providers`, `openid_connect_provider_arns`, `saml_provider_arns`, `developer_provider_name` | `region:GUID` |
| `aws_cognito_identity_pool_roles_attachment` [5] | `identity_pool_id`, `roles` (`authenticated`/`unauthenticated` → role ARN) | `role_mapping { identity_provider, type = Token\|Rules, ambiguous_role_resolution (required for Token/Rules), mapping_rule { claim, match_type, role_arn, value } x<=25 }` | identity pool ID |
| `aws_cognito_user_pool_ui_customization` [9] | `user_pool_id` + one of `css`/`image_file` | `client_id` default `ALL`; `image_file` base64, no drift detection; NOTE: "the user pool must have a domain associated with it" | `<user_pool_id>,<client_id>` |
| `aws_cognito_managed_user_pool_client` [10] | `user_pool_id` + `name_pattern` or `name_prefix` (exactly one match) | Adopts a client created by another AWS service (e.g. OpenSearch); "does not create or delete this resource" | `<user_pool_id>/<client_id>` |

Note: the `aws_cognito_user_pool_ui_customization` (classic hosted UI) vs managed-login branding (`managed_login_version = 2`) choice — branding resource not in scope (L3).

## 7. AWS guidance

**Security Hub CSPM Cognito controls** [13] (all Medium, change-triggered):

| ID | Title | Resource | Terraform lever |
|---|---|---|---|
| Cognito.1 | Threat protection, full-function enforcement, standard auth (`SecurityMode` default `ENFORCED`) | UserPool | `user_pool_tier = "PLUS"` + `user_pool_add_ons.advanced_security_mode = "ENFORCED"` |
| Cognito.2 | Identity pools should not allow unauthenticated identities | IdentityPool | `allow_unauthenticated_identities = false` |
| Cognito.3 | Strong password policy (min 8, 4 classes, temp <= 7 days) | UserPool | `password_policy` |
| Cognito.4 | Threat protection full-function for custom auth | UserPool | `advanced_security_additional_flows.custom_auth_mode = "ENFORCED"` |
| Cognito.5 | MFA enabled for password-only sign-in pools (N/A for federated/passwordless) | UserPool | `mfa_configuration = "ON"` (or OPTIONAL — whether OPTIONAL passes is U8) |
| Cognito.6 | Deletion protection enabled | UserPool | `deletion_protection = "ACTIVE"` |

Mapping of Cognito.1/4 to provider arguments is inference from [1][16] (M4).

**Best practices** [16][18]:
- Run threat protection in audit mode >= 2 weeks before full-function [16]; it doesn't cover federated sign-in or M2M, and doesn't rate-limit — add an AWS WAF web ACL [16][18].
- Client secrets only for confidential/server-side and M2M clients; store in Secrets Manager; never in public clients [18].
- Prefer WebAuthn passkeys; otherwise SRP + MFA [18]. PKCE with fresh verifier per request [18].
- `prevent_user_existence_errors = "ENABLED"`, `allow_admin_create_user_only` / `admin_only` recovery to limit public sign-up abuse [18].
- Revoke refresh tokens on sign-out; minimum scopes; least-privilege IAM (only user pool / identity pool resource granularity — permissions span all app clients) [18].
- Use `sub` as the stable user identifier, never sign-in attributes [14].

**API Gateway cross-reference only**: REST `aws_api_gateway_authorizer` (type `COGNITO_USER_POOLS`) and HTTP API `aws_apigatewayv2_authorizer` (type `JWT`, issuer `https://cognito-idp.<region>.amazonaws.com/<pool_id>`, audience = client ID) — not verified in this unit; defer to the API Gateway unit (U9).

## 8. Unverified / medium-confidence / limits

- U1 Forces-new for `username_attributes`/`alias_attributes` not stated on [1]; AWS says immutable [14].
- U2 `username_configuration.case_sensitive` not re-read.
- U3 `password_policy` defaults not on provider page.
- U4 Lambda permission requirement (cross-ref Lambda unit).
- U5 `client_secret` sensitivity marking not stated on [2] — still mark outputs `sensitive = true`.
- U6 `generate_secret` forces-new not stated.
- U7 Custom-domain min-TLS (`SecurityPolicy`) provider argument not seen.
- U8 Whether Cognito.5 passes with `OPTIONAL`.
- U9 API Gateway authorizer details.
- M1 CHANGELOG 6.55.0 section read across a chunk boundary.
- M2 `ignore_changes = [schema]` pattern — not provider-documented.
- M3 Provider default for `enable_token_revocation` (API default = enabled).
- M4 Security Hub ↔ argument mapping for Cognito.1/4.
- L1 Pricing/MAU tiers not researched (legacy pricing table unverified).
- L2 Introduction version of tier/passkey/rotation arguments not located (pre-6.48).
- L3 `aws_cognito_managed_login_branding`, `aws_cognito_log_delivery_configuration`, `aws_cognito_user`, `aws_cognito_user_in_group`, risk configuration, data sources out of scope.
- L4 Cognito user pool replication / multi-Region not covered.

## 9. Legacy checklist claims found wrong

1. "`user_pool_tier` replaces `user_pool_add_ons.advanced_security_mode` in v6.x … remove the old block" — wrong: both documented [1]; AWS still enables threat protection through `AdvancedSecurityMode` on a Plus pool [16]; no 6.0 upgrade-guide entry [12].
2. Tier table "ESSENTIALS: + adaptive authentication" — wrong: threat protection (incl. adaptive auth) is Plus [16].
3. "Cognito resources are not regional by default" — wrong: regional, optional `region` (F5, [1]).
4. `enable_token_revocation` "defaults to false" — contradicts AWS (new clients activate it by default) [15].
5. Custom domain "~45 min propagation" — not supported: AWS cites ~60 s Route 53 propagation and up to 1 h for certificate change [17].
6. `required_version = ">= 1.7"`, `~> 6.0`, S3 backend `dynamodb_table` — superseded (F1, F3, F7).

## 10. Security note

No prompt-injection or instruction-like text was observed in any fetched page.

## Source Bibliography

All read 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_client.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_domain.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_identity_pool.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_identity_pool_roles_attachment.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_identity_provider.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_resource_server.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_group.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_user_pool_ui_customization.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cognito_managed_user_pool_client.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
13. https://docs.aws.amazon.com/securityhub/latest/userguide/cognito-controls.html
14. https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html
15. https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolClient.html
16. https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pool-settings-threat-protection.html
17. https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html
18. https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html
19. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown (via F5/F19)
