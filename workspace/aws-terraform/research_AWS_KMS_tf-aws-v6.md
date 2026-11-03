# Research — AWS KMS with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-14**. Status: **COMPLETE** (unit `kms`, P4 fan-out, flat — no sub-agents).
> Resource docs come from the upstream raw markdown in `hashicorp/terraform-provider-aws` (`main`), because Registry pages render JS-only (F12).
> Coverage reference only (not a source): `workspace/terraform/research_AWS_KMS_aws-v6.x.md` (6.47.0, Terraform 1.7, EOL). Its errors are listed in §9.
> Shared facts are cited by ID from `workspace/aws-terraform/_family_facts_v6.md` (F1–F13) and were not re-researched.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | 1.16.6, target `required_version = "~> 1.16"` (F1); 1.17.0-rc2 is a pre-release, do not target (F2) | F1, F2 |
| hashicorp/aws | 6.69.0, target `version = "~> 6.69"`; no 7.x (F3); never pin 6.57.0 (F4) | F3, F4 |
| Per-resource `region` | Every KMS resource and the `aws_kms_key` data source accept optional `region`. Changing it forces replacement. Import uses `id@region` (F5) | F5; [5]–[11] |
| Identity import | `aws_kms_key` and `aws_kms_alias` document an `identity` import block, which needs Terraform ≥ 1.12.0 (F11). Terraform 1.16 meets this | [5], [7], F11 |
| AWS API naming | `CustomerMasterKeySpec` is **deprecated** in the KMS API in favour of `KeySpec`. "The KeySpec and CustomerMasterKeySpec parameters work the same way. Only the names differ." | [17] |
| Provider naming | `aws_kms_key` exposes only `customer_master_key_spec`, with no `key_spec` argument. `aws_kms_external_key` uses `key_spec`. The `aws_kms_key` data source exports both | [5], [10], [11] |

Root-module constraint block (F1, F3, F6):

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

## 2. Provider 6.x changes for KMS

**6.0.0 breaking changes** (upgrade guide, F13, [2]):
- The only KMS item is the data source `aws_kms_secret`: "The functionality for this data source was removed in v2.0.0 and the data source will be removed in a future version." Do not use it. Use `aws_kms_secrets` instead (not researched in this unit, see L3).
- The guide lists **no** removed or renamed arguments for `aws_kms_key`, `aws_kms_key_policy`, `aws_kms_alias`, `aws_kms_grant`, `aws_kms_replica_key`, `aws_kms_external_key` or `data.aws_kms_key`.
- `region` was added to every resource in 6.0 (F5).

**CHANGELOG 6.48.0 → 6.69.0** ([3], read in two chunks: 6.69.0→6.54.0 and 6.53.0→6.40.0):
- **No entries** for `resource/aws_kms_*`, `data-source/aws_kms_*`, `list-resource/aws_kms_*`, `ephemeral/aws_kms_*` or `action/aws_kms*`. There are no breaking changes, features, enhancements or bug fixes for the in-scope KMS resources.
- Entries that only mention KMS arguments on other services (FYI, out of scope):
  - 6.51.0: `aws_dms_s3_endpoint` — `kms_key_arn` is deprecated in favour of `server_side_encryption_kms_key_id`, and a perpetual-diff fix (#48441).
  - 6.63.0: `aws_synthetics_canary` adds `kms_key_arn` (#49406).
- 6.57.0 was withdrawn (F4).
- 6.54.0 falls on the chunk boundary and was only partly visible (L1).

## 3. aws_kms_key

Source: [5] (2026-10-14).

- **Required:** none.
- **Optional arguments and defaults:**
  - `description`.
  - `key_usage`: `ENCRYPT_DECRYPT` (default) | `SIGN_VERIFY` | `GENERATE_VERIFY_MAC`.
  - `customer_master_key_spec`: default `SYMMETRIC_DEFAULT`. Other values: `RSA_2048`, `RSA_3072`, `RSA_4096`, `HMAC_224`, `HMAC_256`, `HMAC_384`, `HMAC_512`, `ECC_NIST_P256`, `ECC_NIST_P384`, `ECC_NIST_P521`, `ECC_SECG_P256K1`, `ML_DSA_44`, `ML_DSA_65`, `ML_DSA_87`, `SM2` (China Regions only), `ECC_NIST_EDWARDS25519`.
  - `custom_key_store_id`, `xks_key_id`.
  - `policy`: key policy JSON. The docs suggest building it with `aws_iam_policy_document`.
  - `bypass_policy_lockout_safety_check`: default `false`. The docs say "Do not set this value to true indiscriminately".
  - `deletion_window_in_days`: 7–30, default `30`. For a multi-Region primary that has replicas, the waiting period starts when the last replica is deleted.
  - `is_enabled`: default `true`.
  - `enable_key_rotation`: default `false`. It "must be enabled if `rotation_period_in_days` is set".
  - `rotation_period_in_days`: 90–2560 inclusive. **The provider docs state no default.** AWS KMS uses 365 when it is omitted on enable [14].
  - `multi_region`: default `false`.
  - `tags`, `region`.
- **KEY_AGREEMENT gap:** the KMS API accepts `KeyUsage = KEY_AGREEMENT` (NIST ECC / SM2) [17], but the provider's `key_usage` list does not include it [5]. Treat it as unsupported in Terraform unless verified (U1).
- **NOTE (do not mix):** "KMS Key Policy can be configured in either the standalone resource `aws_kms_key_policy` or with the parameter `policy` in this resource. Configuring with both will cause inconsistencies and may overwrite configuration."
- **NOTE (default policy):** "If a key policy is not specified, AWS gives the KMS key a default key policy". That policy gives the owning account's principals unlimited access to all KMS operations.
- **Immutability (AWS API):** `KeySpec`, `KeyUsage`, `Origin` and `MultiRegion` "can't [be] change[d] after the KMS key is created" [17]. Whether the provider plans a *replacement* or an error for each of these arguments is not stated on the resource page (M1).
- **Custom key stores:** only symmetric (`SYMMETRIC_DEFAULT` / `ENCRYPT_DECRYPT`), single-Region keys are allowed. There are no multi-Region keys in a custom key store [17].
- **Attributes:** `arn`, `key_id`, `tags_all`.
- **Timeouts:** only `create`, default `2m`. A custom timeout shorter than the internal default is ignored and the longer value is used.
- **Import:**
  - Identity (Terraform ≥ 1.12): `identity = { id = "<key-id>" }`, with optional `account_id` and `region`.
  - Import block with `id = "<key-id>"`.
  - CLI: `terraform import aws_kms_key.a <key-id>`.
- **Destroy behaviour:** destroying the resource schedules deletion after `deletion_window_in_days`. During the waiting period the key is "Pending deletion": it cannot be used and is not rotated [15]. Pair the key with `lifecycle { prevent_destroy = true }` for production. This is a Terraform core meta-argument, not checked in this unit (L4).

## 4. aws_kms_key_policy

Source: [6].

- **Required:** `key_id`, `policy` (valid JSON; `aws_iam_policy_document` recommended). **Optional:** `bypass_policy_lockout_safety_check` (default `false`), `region`.
- **Destroy:** "If no key policy is specified, or this resource is destroyed, AWS applies a default key policy." That default gives all principals in the owning account unlimited access to all KMS operations, so access control falls back to IAM policies and grants.
  - Destroying this resource therefore **widens** access. It does **not** lock the key out.
  - If `bypass_policy_lockout_safety_check` is set and the resource is destroyed, a warning is shown and the resource is removed from state.
- **Do-not-mix:** the warning is documented on the `aws_kms_key` page (§3), not on this page. Rule: set `policy` on `aws_kms_key` **or** use `aws_kms_key_policy`, never both.
- **Import:** by key ID (`terraform import aws_kms_key_policy.a 1234abcd-…`). No identity import is documented. No timeouts section.

## 5. aws_kms_alias

Sources: [7], [16], [18].

- **Required:** `target_key_id` (key ID or ARN). **Optional:** `name` or `name_prefix` (they conflict; both must start with `alias/`), `region`.
- **Attributes:** `arn`, `target_key_arn`.
- **AWS naming rules** (CreateAlias):
  - 1–256 characters, pattern `^alias/[a-zA-Z0-9/_-]+$`.
  - "The alias name cannot begin with `alias/aws/`. The `alias/aws/` prefix is reserved for AWS managed keys." The error is `InvalidAliasNameException`.
  - The provider page does **not** mention the reserved prefix. The rule comes from the AWS API.
- **AWS behaviour:**
  - An alias is unique per account and Region and points to one key at a time.
  - A key can have many aliases.
  - Alias and key must be in the same account and Region.
  - You cannot change an alias name: delete it and recreate it.
  - `UpdateAlias` only retargets to a key of the same type and key usage.
  - Deleting a key deletes all of its aliases.
  - Aliases are not secret (they appear in CloudTrail).
  - Aliases can grant or deny access via ABAC (`kms:RequestAlias` / `kms:ResourceAliases`).
  - An alias cannot identify a key in the `Resource` element of an IAM policy.
- **Provider note:** the console enforces a 1-to-1 alias-to-key mapping, but the API allows several aliases per key.
- **Import:**
  - Identity (≥ 1.12): `identity = { name = "alias/my-key-alias" }`, with optional `account_id` and `region`.
  - Import block or CLI with `alias/my-key-alias`.

## 6. aws_kms_grant

Source: [8].

- **Required (all force new):** `key_id` (use the ARN for cross-account keys), `grantee_principal`, `operations`.
  - Valid operations include `Decrypt`, `Encrypt`, `GenerateDataKey`, `Sign`, `Verify`, `DescribeKey`, `RetireGrant` (14 values in total; full list not copied, M2).
- **Optional (all force new):**
  - `name`, `retiring_principal`, `grant_creation_tokens`.
  - `constraints { encryption_context_equals | encryption_context_subset }`. The two conflict.
  - `retire_on_delete`: default `false`, which **revokes** the grant on delete. `true` retires it instead and needs extra permissions.
  - `region` does not force new.
- **State warning:** "All arguments including the grant token will be stored in the raw state as plain-text." `grant_token` is **not** documented as a sensitive attribute.
- **Drift:** IAM eventual consistency on `grantee_principal` may cause state drift.
- **Attributes:** `grant_id`, `grant_token`.
- **Import:** `<key_id>:<grant_id>`.

## 7. aws_kms_replica_key, aws_kms_external_key, data aws_kms_key

**aws_kms_replica_key** [9]:
- `primary_key_arn` is required. The primary must be in a different Region of the same partition, and there is one replica per Region.
- Optional:
  - `deletion_window_in_days`: 7–30, default 30.
  - `enabled`: default `true`.
  - `policy`: if omitted, AWS uses the default key policy.
  - `bypass_policy_lockout_safety_check`: default `false`.
  - `description`, `tags`, `region`.
- Attributes: `arn`, `key_id` (shared across related keys), `key_rotation_enabled`, `key_spec`, `key_usage` (shared properties), `tags_all`.
- Import: by key ID. No NOTE blocks.
- AWS rotation rules for multi-Region keys [14]:
  - Rotation is a shared property. It is enabled, disabled or rotated on demand **only on the primary**.
  - New key material is not used until it exists in every replica.
- AWS deletion rules [15]:
  - To delete a primary, schedule deletion of all its replicas first. The primary's waiting period starts when the last replica is deleted.
  - A deleted replica can be recreated by replicating the same primary again.

**aws_kms_external_key** [10] (imported key material, `EXTERNAL` origin):
- Arguments:
  - `key_material_base64`: 256-bit symmetric material, base64.
  - `valid_to`: RFC3339. If omitted, the material does not expire.
  - `key_usage`: default `ENCRYPT_DECRYPT`.
  - `key_spec`: default `SYMMETRIC_DEFAULT`.
  - `multi_region`: default `false`.
  - `deletion_window_in_days`: 7–30, default 30.
  - `enabled`: it can only be `false` while import is pending.
  - `policy`, `bypass_policy_lockout_safety_check` (default `false`).
- **State warning:** "All arguments including the key material will be stored in the raw state as plain-text."
- The page says to use `aws_kms_key` if you want AWS-generated material that can rotate.
- AWS rotation for `EXTERNAL` origin: on-demand rotation only, no automatic rotation [14]. When any of the key's material expires or is deleted, the key becomes unusable [14].
- Attributes: `expiration_model` (`KEY_MATERIAL_EXPIRES` | `KEY_MATERIAL_DOES_NOT_EXPIRE`), `key_state`.
- Import: by **key ARN**.

**data aws_kms_key** [11]:
- `key_id` is required and accepts a key ID, key ARN, alias name (`alias/...`) or alias ARN. `grant_tokens` and `region` are optional.
- Exports:
  - Identity and ownership: `arn`, `aws_account_id`, `id`, `description`, `creation_date`, `key_manager`, `origin`.
  - Key properties: `customer_master_key_spec`, `key_spec`, `key_usage`, `key_state`, `enabled`, `expiration_model`, `valid_to`.
  - Deletion: `deletion_date`, `pending_deletion_window_in_days`.
  - Multi-Region: `multi_region`, `multi_region_configuration { multi_region_key_type, primary_key, replica_keys }`.
  - Key stores: `cloud_hsm_cluster_id`, `custom_key_store_id`, `xks_key_configuration { id }`.

## 8. AWS guidance — key policy, rotation, deletion, Security Hub

**Root account principal** [12]:
- The default statement `"Principal": {"AWS": "arn:aws:iam::<account>:root"}, "Action": "kms:*", "Resource": "*"` is "critical".
- "Unlike other AWS resource policies, an AWS KMS key policy does not automatically give permission to the account or any of its identities."
- "Without this permission, IAM policies that allow access to the key are ineffective, although IAM policies that deny access to the key are still effective."
- The account principal **delegates** to IAM. It does not grant any IAM principal access by itself.
- It "reduces the risk of the key becoming unmanageable": if a policy names only one user and that user is deleted, "the key becomes unmanageable and you must contact AWS Support to regain access."

**Separation of duties** [12], [13], [19]:
- **Key administrators** statement actions: `kms:Create*`, `Describe*`, `Enable*`, `List*`, `Put*`, `Update*`, `Revoke*`, `Disable*`, `Get*`, `Delete*`, `TagResource`, `UntagResource`, `ScheduleKeyDeletion`, `CancelKeyDeletion`, `RotateKeyOnDemand`. Administrators have no cryptographic use.
  - `kms:Delete*` does **not** include `ScheduleKeyDeletion`.
  - Extra permissions for special keys: `kms:ImportKeyMaterial` (keys with no material) and `kms:ReplicateKey` / `kms:UpdatePrimaryRegion` (multi-Region keys).
  - Warning: administrators can change the policy and create grants, "so they can give themselves and others" more permissions. Tag and alias managers can also control access (ABAC).
- **Key users** statements:
  - Symmetric keys: `Encrypt`, `Decrypt`, `ReEncrypt*`, `GenerateDataKey*`, `DescribeKey`. HMAC, asymmetric and key-agreement keys use different action sets.
  - The "Allow attachment of persistent resources" statement allows `CreateGrant`, `ListGrants`, `RevokeGrant` with `Bool kms:GrantIsForAWSResource = true`. Restrict it further with `kms:ViaService`.
- Least privilege:
  - "Only allow all actions (`kms:*`) on a KMS key policy if you plan to further restrict permissions with additional IAM policies."
  - Use `kms:EncryptionContext:*`, `kms:ViaService` and `kms:CallerAccount`.
  - For service principals, "strongly recommend" `aws:SourceArn` / `aws:SourceAccount` (confused deputy).
  - Prefer IAM roles. Use MFA for privileged actions such as scheduling deletion.
- IAM policies:
  - Prefer key policies for sensitive permissions (`kms:PutKeyPolicy`, `kms:ScheduleKeyDeletion`).
  - Limit `kms:CreateKey`, optionally with a `kms:KeySpec` condition.
  - List key ARNs in `Resource`. Avoid `"Resource": "*"` because it covers keys in other accounts.
  - `"*"` is required only for `CreateKey`, `GenerateRandom`, `ListAliases`, `ListKeys` and custom key store actions.

**Policy lockout safety check** [17]:
- The policy "must allow the calling principal to make a subsequent `PutKeyPolicy` request".
- `BypassPolicyLockoutSafetyCheck` defaults to false. "Do not set this value to true indiscriminately". Use it "only when you intend to prevent the principal that is making the request from making a subsequent PutKeyPolicy request".
- Principals must exist and be visible to KMS. Newly created principals may need a delay because of IAM eventual consistency.
- Maximum policy length is 32768.
- A statement that is missing `Action` or `Resource` silently has no effect when set through the API.

**Rotation** [14]:
- Automatic rotation applies only to symmetric encryption keys with `AWS_KMS` origin. The default period is 365 days; `kms:RotationPeriodInDays` can constrain it.
- On-demand rotation applies to `AWS_KMS` and `EXTERNAL` symmetric keys.
- Asymmetric keys, HMAC keys and custom key store keys need **manual** rotation (a new key, then retarget the alias).
- AWS managed keys rotate yearly. Pending-deletion and disabled keys are not rotated.
- Pricing: a monthly fee applies for the first and second rotations, capped after the second.

**Deletion** [15]:
- The waiting period is 7–30 days, default 30. It can run up to 24 hours longer.
- Deletion is irreversible. "If you are not sure, consider disabling the KMS key instead of deleting it."
- Deletion is recorded in CloudTrail. Use a CloudWatch alarm to detect attempted use during the waiting period.

**Security Hub CSPM KMS controls** [4]:

| ID | Title | Severity | Config rule |
|---|---|---|---|
| KMS.1 | IAM customer managed policies should not allow decryption actions on all KMS keys (`kms:Decrypt`, `kms:ReEncryptFrom`; ignores Conditions) | Medium | `iam-customer-policy-blocked-kms-actions` |
| KMS.2 | IAM principals should not have inline policies allowing decryption on all KMS keys | Medium | `iam-inline-policy-blocked-kms-actions` |
| KMS.3 | AWS KMS keys should not be deleted unintentionally (fails if scheduled for deletion) | **Critical** | `kms-cmk-not-scheduled-for-deletion-2` (custom) |
| KMS.4 | AWS KMS key rotation should be enabled (CIS v5.0.0/3.6, PCI DSS v4.0.1/3.7.4) | Medium | `cmk-backing-key-rotation-enabled` (periodic) |
| KMS.5 | KMS keys should not be publicly accessible | **Critical** | `kms-key-policy-no-public-access` |

KMS.5 caveats:
- The control also fails when AWS Config cannot read the key policy (`GetKeyPolicy`). Check SCPs, RCPs and the key policy itself.
- Conditions that use wildcards or policy variables are not evaluated. Use fixed values to pass.

Terraform mapping:
- KMS.1/KMS.2: use specific key ARNs in `aws_iam_policy_document.resources`.
- KMS.3: `prevent_destroy`, plus a 30-day window.
- KMS.4: `enable_key_rotation = true` on symmetric `AWS_KMS` keys.
- KMS.5: no `"*"` principal and no untrusted accounts in `policy`.

## 9. Legacy-file claims found wrong or unsupported

| # | Legacy claim (6.47 file) | Finding | Source |
|---|---|---|---|
| W1 | "No AWS support can recover a KMS key with a locked-out key policy" | **Wrong.** AWS says you "must contact AWS Support to regain access" | [12] |
| W2 | "If you destroy `aws_kms_key_policy` … the key becomes permanently unmanageable" | **Wrong.** Destroying it makes AWS apply the default policy (full account access) | [6] |
| W3 | Inline `policy` "causes perpetual diffs because AWS normalizes key policies"; the split is "recommended in v6.x" | **Unsupported.** The documented hazard is configuring *both* ("inconsistencies and may overwrite configuration"). No recommendation of one form over the other is stated | [5] |
| W4 | `rotation_period_in_days` "default 365" as a provider default | **Partly wrong.** The provider states no default; 365 is the AWS default on enable | [5], [14] |
| W5 | Key-spec list (only `HMAC_256`, no Ed25519) | **Incomplete.** Also `HMAC_224/384/512` and `ECC_NIST_EDWARDS25519` | [5], [17] |
| W6 | Key-admin action list | **Outdated.** Omits `kms:RotateKeyOnDemand` | [12] |
| W7 | "Grant tokens are explicitly documented as sensitive" | **Wrong.** Documented as stored in plain text, not marked sensitive | [8] |
| W8 | Asymmetric rotation fails with `UnsupportedOperationException` | Error name **unverified**. The fact that rotation is not supported is confirmed | [14] |
| W9 | `required_version = ">= 1.7"`, `dynamodb_table` locking | **Superseded** by F1, F6, F7 | F1, F7 |

## 10. Unverified / medium-confidence items and coverage limits

- U1 `key_usage = "KEY_AGREEMENT"` is not listed by the provider although the AWS API supports it. Provider support is unverified.
- U2 Exact `UnsupportedOperationException` error when enabling rotation on asymmetric or HMAC keys (W8).
- U3 FIPS 140-3 Level 3 HSM claim (legacy executive summary) was not fetched.
- M1 Which `aws_kms_key` argument changes force replacement. The AWS API makes spec, usage, origin and multi-Region immutable, but the provider page has no forces-new markers.
- M2 The full 14-value `operations` list for `aws_kms_grant` was paraphrased by WebFetch. Re-read the raw page before copying it into a validation rule.
- M3 Verbatim wording: WebFetch paraphrases. The substance was confirmed on the raw markdown.
- L1 CHANGELOG was read in 100k-character chunks. 6.54.0 was only partly visible at the boundary. No KMS entries appeared in either part.
- L2 The raw `main` docs may run slightly ahead of 6.69.0 (same as the pilot).
- L3 Out of scope and not researched: `aws_kms_custom_key_store`, `aws_kms_ciphertext`, `data.aws_kms_secrets`, `data.aws_kms_alias`, `data.aws_kms_public_key`, and ephemeral KMS resources.
- L4 Terraform `lifecycle.prevent_destroy` semantics were not re-fetched in this unit. They are core language features.

## 11. Security note

- No prompt injection was seen. None of the 19 fetched pages contained instruction-like text aimed at an AI. Imperative text found ("Do not set this value to true indiscriminately") is ordinary documentation addressed to humans.

## Source Bibliography

All fetched 2026-10-14.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown (via F5)
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
4. https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key_policy.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_alias.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_grant.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_replica_key.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_external_key.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/kms_key.html.markdown
12. https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html
13. https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html
14. https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html
15. https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html
16. https://docs.aws.amazon.com/kms/latest/developerguide/kms-alias.html
17. https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateKey.html
18. https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateAlias.html
19. https://docs.aws.amazon.com/kms/latest/developerguide/least-privilege.html
20. `workspace/aws-terraform/_family_facts_v6.md` F1–F13 (orchestrator-verified, 2026-10-14)
