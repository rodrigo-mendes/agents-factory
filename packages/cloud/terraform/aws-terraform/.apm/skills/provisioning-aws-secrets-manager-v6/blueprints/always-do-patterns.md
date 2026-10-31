# Always-Do Patterns — provisioning-aws-secrets-manager-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) | [always-do-secrets](./always-do-secrets.md#1-terraform-block) |
| 2 | Secret with KMS key, recovery window, replica, tags | [always-do-secrets](./always-do-secrets.md#2-secret) |
| 3 | Secret version with a write-only value | [always-do-secrets](./always-do-secrets.md#3-secret-version-with-a-write-only-value) |
| 4 | Ephemeral and data source reads | [always-do-secrets](./always-do-secrets.md#4-ephemeral-and-data-source-reads) |
| 5 | Rotation with `aws_secretsmanager_secret_rotation` | [always-do-rotation-policy](./always-do-rotation-policy.md#5-rotation) |
| 6 | Resource policy with `block_public_policy` | [always-do-rotation-policy](./always-do-rotation-policy.md#6-resource-policy) |
