# Never-Do Patterns — provisioning-aws-cognito-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented reason with its
source (read 2026-10-23), and the correct alternative. One row here = one row in SKILL.md.

| Anti-pattern | Blueprint |
|---|---|
| `username_attributes` together with `alias_attributes` | [never-do-pool-domain](./never-do-pool-domain.md#1-username_attributes-together-with-alias_attributes) |
| Removing `sms_configuration` in place | [never-do-pool-domain](./never-do-pool-domain.md#2-removing-sms_configuration-in-place) |
| `ON`/`OPTIONAL` MFA without a method block | [never-do-pool-domain](./never-do-pool-domain.md#3-mfa-on-or-optional-without-a-method-block) |
| Custom domain certificate outside us-east-1 | [never-do-pool-domain](./never-do-pool-domain.md#4-custom-domain-certificate-outside-us-east-1) |
| Pinning withdrawn provider 6.57.0 | [never-do-pool-domain](./never-do-pool-domain.md#5-pinning-version-6570) |
| `allowed_oauth_flows` without the user-pool-client flag | [never-do-client-oauth](./never-do-client-oauth.md#1-allowed_oauth_flows-without-the-flag) |
| `default_redirect_uri` missing from `callback_urls` | [never-do-client-oauth](./never-do-client-oauth.md#2-default_redirect_uri-missing-from-callback_urls) |
| Legacy auth-flow values combined with `ALLOW_*` | [never-do-client-oauth](./never-do-client-oauth.md#3-legacy-auth-flow-values-combined-with-allow_) |
| `client_credentials` combined with other flows | [never-do-client-oauth](./never-do-client-oauth.md#4-client_credentials-combined-with-other-flows) |
| Non-localhost `http://` callback URLs | [never-do-client-oauth](./never-do-client-oauth.md#5-non-localhost-http-callback-urls) |
