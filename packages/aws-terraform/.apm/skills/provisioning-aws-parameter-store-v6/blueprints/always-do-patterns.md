# Always-Do Patterns — provisioning-aws-parameter-store-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL and cites its official
source (fetched 2026-10-23). Example values are marked `# example`. The ephemeral read is an
Ask First option and lives in [ask-first-ephemeral](./ask-first-ephemeral.md).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-version-constraints) |
| 2 | Hierarchical names and `insecure_value` for non-secret values | [always-do-foundation](./always-do-foundation.md#2-hierarchical-names-and-non-secret-values) |
| 3 | Import by identity | [always-do-foundation](./always-do-foundation.md#3-import) |
| 4 | SecureString with `value_wo` and a customer managed key | [always-do-secrets](./always-do-secrets.md#4-securestring-with-value_wo-and-a-cmk) |
