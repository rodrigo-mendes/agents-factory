# Unverified Claims and Risks — hashicorp/aws 6.x KMS

Research date 2026-10-14. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-14 (reference 6.69.0). Re-verify when
  starting new work or after 30 days. Source: https://github.com/hashicorp/terraform-provider-aws/releases
- **Terraform 1.16.6** is the current stable CLI. **1.17.0-rc2** exists — do not target it.
  Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is permanently withdrawn** from GitHub and the Registry. Any constraint resolving to it
  fails `terraform init`.
- **v7 is planned** — upgrade guide already documents items "removed in v7.0.0". When v7 ships,
  create a new skill `provisioning-aws-kms-v7`.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | `key_usage = "KEY_AGREEMENT"` — the KMS API accepts it (NIST ECC / SM2) but it is not listed in the provider's `key_usage` enum | (unverified) — treat as unsupported in Terraform until confirmed |
| U2 | Exact error name returned when enabling rotation on asymmetric/HMAC keys | (unverified) — the restriction itself is confirmed; do not name the exception in code or docs |
| U3 | FIPS 140-3 Level 3 HSM claim (from legacy research) was not fetched in this unit | (unverified) — do not reproduce |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Which `aws_kms_key` arguments force replacement — AWS API makes `KeySpec`, `KeyUsage`, `Origin`, `MultiRegion` immutable, but the provider page has no forces-new markers for them | (medium confidence) — treat as likely forces-new; confirm before applying changes to existing keys |
| M2 | Full 14-value `operations` list for `aws_kms_grant` — the research paraphrased from WebFetch; only a partial list is confirmed | (medium confidence) — re-read the raw resource page before using the full list in a validation rule |
| M3 | Verbatim wording of provider NOTE blocks — WebFetch paraphrases; substance confirmed on raw markdown | (medium confidence) — use source URLs to verify exact wording before quoting in policy or runbooks |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG was read in 100k-character chunks; 6.54.0 was only partly visible at the chunk boundary. No KMS entries appeared in either chunk. |
| L2 | Raw `main` branch docs may run slightly ahead of 6.69.0 (same caveat as the pilot). |
| L3 | Out of scope and not researched: `aws_kms_custom_key_store`, `aws_kms_ciphertext`, `data.aws_kms_secrets`, `data.aws_kms_alias`, `data.aws_kms_public_key`, and ephemeral KMS resources. |
| L4 | Terraform `lifecycle.prevent_destroy` semantics were not re-fetched in this unit; they are core Terraform language features. |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | always-do-key-basics.md §2 — immutability note | M1 |
| (unverified) | never-do-usage.md §1 — exact API error name for asymmetric rotation | U2 |
| (medium confidence) | always-do-key-policy.md §5 — full grant operations list | M2 |
| (medium confidence) | always-do-key-basics.md §2 — immutability of KeySpec/KeyUsage/Origin/MultiRegion | M1 |

## Source Bibliography

All fetched 2026-10-14. Numbers match the original research bibliography.

1. https://releases.hashicorp.com/terraform/ — Terraform 1.16.6 stable; 1.17.0-rc2 pre-release
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — aws_kms_secret removed in 6.0; region added to all resources
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.57.0 withdrawn; no KMS entries 6.48–6.69
4. https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html — KMS.1/2/3/4/5 controls
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown — arguments, defaults, rotation, policy note
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key_policy.html.markdown — bypass_policy_lockout_safety_check; destroy behaviour
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_alias.html.markdown — name/name_prefix; import
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_grant.html.markdown — operations; retire_on_delete; plain-text state warning
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_replica_key.html.markdown — primary_key_arn; rotation on primary only
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_external_key.html.markdown — key_spec; key material plain-text state
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/kms_key.html.markdown — data source; exports customer_master_key_spec and key_spec
12. https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html — root principal; admin/user action sets; kms:RotateKeyOnDemand
13. https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html — least privilege; Resource "*" only for CreateKey/GenerateRandom/ListAliases/ListKeys
14. https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html — symmetric-only auto-rotation; 365-day AWS default; on-demand for EXTERNAL; pending-deletion keys not rotated
15. https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html — waiting period 7–30 days; irreversible; disable instead of delete
16. https://docs.aws.amazon.com/kms/latest/developerguide/kms-alias.html — alias behaviour; uniqueness per account/Region
17. https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateKey.html — CustomerMasterKeySpec deprecated in favour of KeySpec; bypass_policy_lockout_safety_check; immutability
18. https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateAlias.html — pattern `alias/[a-zA-Z0-9/_-]+`; alias/aws/ reserved; 1–256 chars
19. https://docs.aws.amazon.com/kms/latest/developerguide/least-privilege.html — kms:ViaService; kms:EncryptionContext; aws:SourceArn
20. Shared version and region facts: the Terraform and provider pages cited inline, read 2026-10-23.
