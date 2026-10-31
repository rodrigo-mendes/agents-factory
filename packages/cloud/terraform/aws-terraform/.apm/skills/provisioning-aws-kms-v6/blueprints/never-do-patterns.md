# Never-Do Patterns — provisioning-aws-kms-v6

Index of the never-do blueprints, split by topic. Each entry has a WRONG block, the documented
reason with its source (fetched 2026-10-14), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `policy` in `aws_kms_key` AND `aws_kms_key_policy` on the same key | [never-do-policy](./never-do-policy.md#1-mixing-policy-mechanisms) |
| Omitting root-account principal from a key policy | [never-do-policy](./never-do-policy.md#2-omitting-root-account-principal) |
| `bypass_policy_lockout_safety_check = true` used routinely | [never-do-policy](./never-do-policy.md#3-bypass-policy-lockout-safety-check) |
| `kms:Decrypt` / `kms:ReEncryptFrom` on `"Resource": "*"` in IAM policies (KMS.1/KMS.2) | [never-do-policy](./never-do-policy.md#4-wildcard-resource-in-iam-decrypt-policies) |
| `enable_key_rotation = true` on asymmetric or HMAC keys | [never-do-usage](./never-do-usage.md#1-rotation-on-asymmetric-or-hmac-keys) |
| Alias name starting with `alias/aws/` (reserved for AWS managed keys) | [never-do-usage](./never-do-usage.md#2-aliasaws-prefix) |
| `data "aws_kms_secret"` data source (removed in hashicorp/aws 6.0) | [never-do-usage](./never-do-usage.md#3-aws_kms_secret-data-source-removed-in-60) |
| `rotation_period_in_days` set without `enable_key_rotation = true` | [never-do-usage](./never-do-usage.md#4-rotation_period_in_days-without-enable_key_rotation) |
