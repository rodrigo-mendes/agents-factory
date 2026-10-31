# Always-Do Patterns — provisioning-aws-cognito-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL and cites its official source (read 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and the optional `region` argument | [always-do-pool](./always-do-pool.md#1-terraform-block-and-region) |
| 2 | User pool sign-in identifiers, MFA, account recovery, SES email | [always-do-pool](./always-do-pool.md#2-user-pool-sign-in-mfa-recovery-and-email) |
| 3 | Schema (add-only), password policy, deletion protection | [always-do-pool](./always-do-pool.md#3-schema-password-policy-and-deletion-protection) |
| 4 | App client with OAuth flags, redirect URIs and auth flows | [always-do-client-domain](./always-do-client-domain.md#4-user-pool-client-oauth) |
| 5 | Prefix and custom domain (ACM certificate in us-east-1, Route 53 alias) | [always-do-client-domain](./always-do-client-domain.md#5-user-pool-domain-prefix-and-custom) |
| 6 | Identity pool and roles attachment (`ambiguous_role_resolution`) | [always-do-client-domain](./always-do-client-domain.md#6-identity-pool-and-roles-attachment) |
