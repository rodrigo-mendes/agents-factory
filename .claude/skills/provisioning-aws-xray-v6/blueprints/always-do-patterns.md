# Always-Do Patterns — provisioning-aws-xray-v6

Index of the always-do blueprints, split by topic. Each pattern cites its official source
(read 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-s3-backend) |
| 2 | Encryption config (`NONE` default encryption, `KMS` with `key_id`) | [always-do-foundation](./always-do-foundation.md#2-encryption-config) |
| 3 | Sampling rule with all Required arguments, priority 1–9999, `fixed_rate` 0–1 | [always-do-sampling-groups](./always-do-sampling-groups.md#3-sampling-rule) |
| 4 | Group with `insights_configuration`, name limits, identity import | [always-do-sampling-groups](./always-do-sampling-groups.md#4-group) |
| 5 | Tracing in other services (cross-references) and IAM actions | [always-do-cross-service](./always-do-cross-service.md#5-tracing-in-other-services-and-iam) |
