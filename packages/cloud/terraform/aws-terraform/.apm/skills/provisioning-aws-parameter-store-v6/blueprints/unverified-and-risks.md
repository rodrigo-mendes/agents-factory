# Unverified Claims and Risks — hashicorp/aws 6.x Parameter Store

Research date 2026-10-23. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x**: latest 6.70.0, constraint `~> 6.69`, no 7.x released. Re-verify when starting
  new work. Source: https://releases.hashicorp.com/terraform-provider-aws/
- **Terraform 1.17.0 is stable since 2026-10-21** and is not the target (`~> 1.16`). Its changelog lists
  no breaking changes; moving to it is a deliberate re-verification, not part of this skill.
  Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is withdrawn** from GitHub and the Registry. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **v7 is planned** — create `provisioning-aws-parameter-store-v7` when it ships.
- Ephemeral resources are described on the provider page as a new feature whose usage may change.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Minimum Terraform CLI version for ephemeral resources, and the provider version that introduced `ephemeral.aws_ssm_parameter` — not stated on the page | (unverified) — check the Terraform ephemeral-resources docs |
| U3 | Parameter name constraints (length, characters, reserved prefixes) — page fetch returned no content | (unverified) |
| U4 | Whether `GetParametersByPath` needs the bare path ARN besides `path/*`; recursive-deny behavior — page fetch returned no content | (unverified) |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Ephemeral-value semantics (not persisted; ephemeral contexts only) are general Terraform behavior, not restated on the provider page | (medium confidence) |
| M2 | Throttling with many parameters is inferred from the PutParameter 3 TPS quota | (medium confidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG read through ~6.40 in two chunks; the 6.55.0 section boundary was split, so a 6.55.0 SSM entry could be missed |
| L2 | `aws_ssm_default_patch_baseline` / `aws_ssm_patch_baseline` arguments not researched (6.59.0 added a list resource for `aws_ssm_patch_baseline`) |
| L3 | Parameter policies (Expiration, ExpirationNotification, NoChangeNotification): no Terraform argument documented on the resource page; not researched further |
| L4 | Pricing figures not researched |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First, Ephemeral read row — minimum CLI version | U1 |
| (medium confidence) | SKILL.md Ask First, Ephemeral read row — ephemeral semantics | M1 |
| (unverified) | SKILL.md Ask First, Names and path IAM row — name constraints | U3 |
| (unverified) | SKILL.md Ask First, Names and path IAM row — bare path ARN | U4 |
| (medium confidence) | SKILL.md Ask First, Many parameters row — throttling | M2 |
| (unverified) | ask-first-ephemeral.md — minimum Terraform version | U1 |
| (medium confidence) | ask-first-ephemeral.md — ephemeral semantics and replica HCL | M1 |

## Source Bibliography

All fetched 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown — arguments, write-only, tiers, import
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameter.html.markdown — data source
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/ssm_parameter.html.markdown — ephemeral resource, `arn`
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.57.0 withdrawn; 6.58.0/6.59.0 fixes
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — no Parameter Store entries
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameters_by_path.html.markdown — by-path data source
7. https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html — tiers, default tier
8. https://docs.aws.amazon.com/systems-manager/latest/userguide/secure-string-parameter-kms-encryption.html — KMS, encryption context
9. https://docs.aws.amazon.com/general/latest/gr/ssm.html — quotas
10. https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-default-tier.html — Intelligent-Tiering
11. https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html — hierarchies
12. https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html — overview, Secrets Manager comparison
13. https://docs.aws.amazon.com/securityhub/latest/userguide/ssm-controls.html — SSM.1–SSM.7
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — `region`
15. https://developer.hashicorp.com/terraform/language/expressions/version-constraints — `~>` constraints
