# Always-Do Patterns — provisioning-aws-kms-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-14).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-key-basics](./always-do-key-basics.md#1-terraform-block-and-s3-backend) |
| 2 | `aws_kms_key` — symmetric, `enable_key_rotation`, 30-day deletion window, `lifecycle { prevent_destroy }` | [always-do-key-basics](./always-do-key-basics.md#2-aws_kms_key) |
| 3 | `aws_kms_alias` — `alias/` prefix, `name` vs `name_prefix` | [always-do-key-basics](./always-do-key-basics.md#3-aws_kms_alias) |
| 4 | Key policy — root-account principal, admin/user separation of duties | [always-do-key-policy](./always-do-key-policy.md#4-key-policy-and-separation-of-duties) |
| 5 | `aws_kms_grant` — grantee principal, operations, `retire_on_delete` | [always-do-key-policy](./always-do-key-policy.md#5-aws_kms_grant) |
