# Unverified Claims and Risks — hashicorp/aws 6.x Secrets Manager

Research date 2026-10-23. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x** is the current stable major (reference 6.69.0, latest 6.70.0 on 2026-10-21).
  Re-verify when starting new work. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **Terraform 1.17.0 is stable since 2026-10-21**; this skill targets `~> 1.16`, not 1.17.
  Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is withdrawn** from GitHub and the Registry; never pin it.
- **The ephemeral `aws_secretsmanager_secret_version` page notes** ephemeral resources "may evolve".
- **v7 is planned** (the 6.0 upgrade guide lists arguments "will be removed in v7.0.0", https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown); when it ships, create a new skill `provisioning-aws-secrets-manager-v7`.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | `force_overwrite_replica_secret` default — not stated | (unverified) — set it explicitly when replicating over an existing secret |
| U2 | `block_public_policy` default — not stated | (unverified) — set `true` explicitly |
| U3 | How to remove a policy managed by `aws_secretsmanager_secret_policy` — not stated (it rejects `"{}"`) | (unverified) |

No I items (no inaccessible sources).

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Do not mix inline `policy` with `aws_secretsmanager_secret_policy` — inferred from the `policy` warning | (medium confidence) |
| M2 | `ignore_changes = [secret_string]` — Terraform meta-argument usage, not in provider docs | (medium confidence) |
| M3 | Data source secret values are persisted in state — inferred from the Terraform docs; provider page silent | (medium confidence) |
| M4 | No resource page for `aws_secretsmanager_secret_replica` found in the provider docs; replication is the `replica` block — absence of evidence | (medium confidence) |
| M5 | The 6.x secret doc lists no rotation arguments (`force_delete_without_recovery` is likewise not an argument) — absence of evidence | (medium confidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG 6.55.0 section only partially visible |
| L2 | No provider `ignore_changes` example exists for these resources |
| L3 | Data sources `aws_secretsmanager_secret_versions`, `aws_secretsmanager_secret_rotation` and `aws_secretsmanager_random_password` not deep-dived |

## Tag to Register Mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First, Replication row — `force_overwrite_replica_secret` default | U1 |
| (unverified) | SKILL.md Ask First, Policy location row — `block_public_policy`; always-do-rotation-policy.md §6 Resource policy | U2 |
| (unverified) | SKILL.md Ask First, Policy location row — removing a policy managed by the policy resource | U3 |
| (medium confidence) | SKILL.md Ask First, Policy location row; always-do-rotation-policy.md §6 Resource policy | M1 |
| (medium confidence, absence of evidence) | SKILL.md Ask First, Replica resource row | M4 |
| (medium confidence, absence of evidence) | SKILL.md Ask First, Rotation arguments row and Immediate deletion row | M5 |
| (medium confidence) | SKILL.md Ask First, Rotation owns the value row | M2 |
| (medium confidence) | always-do-secrets.md §4 Ephemeral and data source reads | M3 |

## Source Bibliography

All fetched 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown — arguments, replica, policy warning
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown — value sources, `secret_string_wo`, `secret_arn`
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown — rotation arguments, `duration`
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_policy.html.markdown — policy resource, `block_public_policy`
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.48.0 to 6.70.0 changes; 6.57.0 withdrawn
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — no Secrets Manager entries
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/secretsmanager_secret_version.html.markdown — data source
8. https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html — AWS best practices
9. https://developer.hashicorp.com/terraform/language/manage-sensitive-data — secrets in state, write-only, ephemeral
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/secretsmanager_secret.html.markdown — secret data source
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/secretsmanager_secret_version.html.markdown — ephemeral resource
12. https://docs.aws.amazon.com/securityhub/latest/userguide/secretsmanager-controls.html — SecretsManager.1 to .5
13. https://releases.hashicorp.com/terraform/ — Terraform 1.16.x and 1.17.0
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — per-resource `region`
15. https://developer.hashicorp.com/terraform/language/expressions/version-constraints — `~>` for root modules
