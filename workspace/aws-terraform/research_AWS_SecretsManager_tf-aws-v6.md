# Research — AWS Secrets Manager with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `secretsmanager`, P4 fan-out, flat — no sub-agents).
> Regional service: every in-scope resource/data source accepts optional `region` (F5).
> Registry pages are JS-only (F12); upstream raw markdown on `main` is the authoritative resource doc.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_SecretsManager_aws-v6.x.md`
> (6.47.0, Terraform 1.7 — EOL). Wrong claims found in it are listed in §8.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI target | `required_version = "~> 1.16"` (1.17.0 stable but not the target) | F1, F2 |
| hashicorp/aws | latest 6.70.0 (2026-10-21 per CHANGELOG); constraint `~> 6.69`; never pin 6.57.0 | F3, F4, [5] |
| Per-resource `region` | optional, default provider region, change forces replacement, import `id@region` | F5 |
| Write-only args (`secret_string_wo`) | need Terraform **≥ 1.11** — satisfied by 1.16 | [2], [9] |
| Ephemeral resources | need Terraform **≥ 1.10** — satisfied by 1.16 | [9] |
| Identity-based import | Terraform ≥ 1.12.0 | F11, [1] |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

## 2. Provider 6.x changes for Secrets Manager

**6.0.0 upgrade guide (F13):** the guide contains **no** Secrets Manager entries (no removed/renamed
arguments for any `aws_secretsmanager_*` resource or data source) [6].

**CHANGELOG 6.48.0 → 6.70.0** [5]:
- 6.50.0 (#48318): `data-source/aws_secretsmanager_secret_version` eventual-consistency fix on read right
  after create; `resource/aws_secretsmanager_secret_version` fixes "inconsistent final plan" when the value
  references a resource created/replaced in the same apply, empty `version_stages` in state on create, and
  **unnecessary replacement when switching between `secret_string` and `secret_string_wo`**.
- 6.56.0 (#49058): new **list resource** `aws_secretsmanager_secret_policy`.
- 6.57.0: withdrawn (F4). 6.57.1 (#46414): `resource/aws_secretsmanager_secret` new `type` argument
  (managed external secrets); `aws_secretsmanager_secret_rotation` new `external_secret_rotation_role_arn`
  and `external_secret_rotation_metadata`; data source `aws_secretsmanager_secret` adds `type`; data source
  `aws_secretsmanager_secret_rotation` adds the two external-rotation attributes.
- 6.62.0 (#49659): `aws_secretsmanager_secret_rotation` — `rotation_enabled` now configurable;
  `rotation_rules` optional and must be omitted when rotation is disabled. Note on `aws_db_instance` /
  `aws_rds_cluster`: managed-secret rotation can be disabled via this resource with `rotation_enabled = false`.
- 6.70.0 (#50369): `aws_secretsmanager_secret_version` read/delete no longer error when a non-current
  version's KMS key is disabled/deleted — Terraform keeps the value from state and warns.
- No Secrets Manager entries in 6.48.0, 6.49.0, 6.51.0–6.54.0, 6.58.0–6.61.0, 6.63.0–6.69.1 or Unreleased.
  6.55.0 only partly visible (L1).

Pre-window context (outside 6.48 range, for migration awareness): 6.45.0 (#47815) allowed switching
`secret_string` → `secret_string_wo` without recreation; 6.47.0 (#48011/#48033) deprecated `arn` in favor of
`secret_arn` on the version resource/data sources and `name` → `secret_name` on `aws_secretsmanager_secret_versions` [5].
⚠️ Migration Note: use `secret_arn`, not the deprecated `arn`, on `aws_secretsmanager_secret_version` (resource and data source) [2][7].

## 3. `aws_secretsmanager_secret` [1]

No required arguments. Optional:
- `name` — allowed chars letters, digits, `/_+=.@-`; **conflicts with `name_prefix`**. `name_prefix` generates a unique name.
- `description`.
- `kms_key_id` — ARN or ID; **use the key ARN for a key in another account**. Default: account's
  `aws/secretsmanager` key (created on first use).
- `recovery_window_in_days` — `0` forces deletion **without recovery**, otherwise `7`–`30`; **default `30`**.
- `policy` — JSON resource policy. **Warning:** removing it, or setting `null`/`""`, does **not** delete the
  policy (because `aws_secretsmanager_secret_policy` may have set it); set `"{}"` to delete.
- `replica` block (repeatable): `region` (required), `kms_key_id` (optional; ARN, key ID or alias in the
  replica Region; default that Region's `aws/secretsmanager`). Computed per replica: `status`
  (`InProgress`/`Failed`/`InSync`), `status_message`, `last_accessed_date`.
- `force_overwrite_replica_secret` (bool) — overwrite a same-named secret in the destination Region. Default not stated (U1).
- `type` — managed external secret type (`SalesforceClientSecret`, `BigIDClientSecret`,
  `SnowflakeKeyPairAuthentication`); **cannot be changed after creation**.
- `tags` (overrides matching `default_tags` keys), `region` (F5).
- Exports: `arn`, `id` (= ARN), `replica`, `tags_all`.
- Import: identity `{ arn = "<secret-arn>" }` (TF ≥ 1.12); `import { id = "<secret-arn>" }`; CLI with ARN.

Policy: inline `policy` vs `aws_secretsmanager_secret_policy` — the docs' warning shows both write the same
underlying policy; manage it in **one place only** (medium confidence — the doc gives the warning above, not an
explicit "do not mix" sentence; M1).

## 4. `aws_secretsmanager_secret_version` [2]

- `secret_id` (required) — ARN or name of an existing secret.
- Exactly one value source: `secret_string`, `secret_binary` (**must be base64-encoded**), or
  `secret_string_wo` (**write-only**, requires `secret_string_wo_version`; changing `secret_string_wo_version`
  triggers the update). Exported `has_secret_string_wo` shows whether a write-only value is set.
- "`secret_string_wo` is available in place of `secret_string`" and requires **Terraform 1.11.0+**.
- `version_stages` — if omitted, AWS moves `AWSCURRENT` to the new version on create. If set, you must include
  `AWSCURRENT` when this is the only version or the label is already on it — **otherwise perpetual diff**.
- Deletion: if `AWSCURRENT` is on this version, the label cannot be removed and is skipped; the version stays active.
- Single-version tracking: the resource tracks its own version even after rotation or out-of-band versions; to read
  the current value use the data source.
- KMS key change: only `AWSCURRENT`/`AWSPENDING`/`AWSPREVIOUS` are re-encrypted; older versions may become
  undecryptable (6.70.0 behavior: keep state value + warning).
- Exports: `secret_arn`, `version_id`, `has_secret_string_wo`; `arn` **deprecated**.
- Import: identity `{ secret_id, version_id }` (optional `account_id`, `region`); ID `"<secret-arn>|<version-id>"`.

**Secrets in state — exactly what the docs say:**
- Provider doc: only advises marking variables holding secrets `sensitive = true` "to keep them out of logs and
  console output" [2]. It does not itself state that `secret_string` is in state.
- Terraform docs: "If you add secret values directly to your configuration, Terraform stores those secrets in its
  state and plan files"; "`sensitive`" values are still stored in state and plan files; write-only arguments
  (TF ≥ 1.11) and ephemeral resources (TF ≥ 1.10) are not persisted — "Terraform does not store ephemeral
  resources in state or plan files" [9].
- Therefore: `secret_string`/`secret_binary` land in state (plaintext-in-state per [9]); prefer `secret_string_wo`
  + `secret_string_wo_version` for Terraform-seeded values.

```hcl
resource "aws_secretsmanager_secret_version" "db" {
  secret_id                = aws_secretsmanager_secret.db.id
  secret_string_wo         = var.db_password   # ephemeral/sensitive input, not stored in state
  secret_string_wo_version = 1                 # bump to push a new value
}
```

`ignore_changes` patterns: the provider doc provides **no** `ignore_changes` example (L2). The common pattern
`lifecycle { ignore_changes = [secret_string] }` to let rotation own the value is a Terraform meta-argument usage,
not provider-documented (M2). Note the resource only tracks its own version [2], so rotation creates new versions
rather than mutating the tracked one.

## 5. `aws_secretsmanager_secret_rotation` [3]

- `secret_id` (required, secret must exist).
- `rotation_lambda_arn` — optional; **required unless the secret is AWS-managed**.
- `rotate_immediately` — default **`true`** (rotate now vs next window).
- `rotation_enabled` — default enabled when `rotation_rules` set; `false` disables (then omit `rotation_rules`;
  toggle with a `dynamic "rotation_rules"` block). Configurable since 6.62.0.
- `rotation_rules` (required unless `rotation_enabled = false`): one of `automatically_after_days` **or**
  `schedule_expression` (`cron()`/`rate()`); `duration` = window length in hours, e.g. `"3h"`.
- `external_secret_rotation_role_arn` / `external_secret_rotation_metadata { key, value }` — managed external secrets.
- Notes: enabling rotation rotates the secret **once immediately**; Aurora/clustered engines — add `depends_on`
  on the cluster instance; removing rotation mid-rotation can leave `AWSPENDING` on a partial version; destroying
  the resource does not re-enable AWS-configured rotation.
- Import: secret ARN (identity `arn`; schema lists `secret_id`).
- AWS: rotation can run as often as every four hours; strategies single user / alternating users [8].

## 6. `aws_secretsmanager_secret_policy` [4]

- `secret_arn` (required), `policy` (required JSON; `"{}"` is **rejected** here, unlike the secret's `policy`).
- `block_public_policy` (optional) — "Makes an optional API call to Zelkova to validate the Resource Policy to
  prevent broad access"; **default not stated** (U2) — set `true` explicitly.
- Import: secret ARN (identity `arn`, schema `secret_arn`). List resource since 6.56.0.

## 7. Data sources and ephemeral resource

- `data.aws_secretsmanager_secret` [10]: `arn` or `name` (both optional); returns metadata only
  (`kms_key_id`, `policy`, `tags`, `type`, dates…).
- `data.aws_secretsmanager_secret_version` [7]: `secret_id` (req), `version_id` (overrides stage),
  `version_stage` (default `AWSCURRENT`); returns decrypted `secret_string`/`secret_binary`, `secret_arn`
  (`arn` deprecated). Data source results are stored in state (implied by [9]; provider page silent — M3).
- **Ephemeral** `aws_secretsmanager_secret_version` [11]: same arguments; returns decrypted values; page notes
  "Ephemeral resources are a new feature and may evolve". Not stored in state per Terraform docs [9]
  (the provider page itself does not say so). Use it to feed write-only args of other resources.

```hcl
ephemeral "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
}
```

## 8. AWS guidance

**Security Hub CSPM controls** [12] (resource type `AWS::SecretsManager::Secret`):

| ID | Title | Severity | Parameter (default) | Terraform lever |
|---|---|---|---|---|
| SecretsManager.1 | automatic rotation enabled | Medium | `maximumAllowedRotationFrequency` 1–365 (none) | `aws_secretsmanager_secret_rotation` |
| SecretsManager.2 | rotation succeeds as scheduled | Medium | none | working Lambda + permissions |
| SecretsManager.3 | remove unused secrets | Medium | `unusedForDays` 1–365 (90) | lifecycle/process |
| SecretsManager.4 | rotated within N days | Medium | `maxDaysSinceRotation` 1–180 (90) | `rotation_rules` ≤ 90 days |
| SecretsManager.5 | secrets tagged | Low | `requiredTagKeys` ≤ 6 (none) | `tags` / `default_tags`, no PII in tags |

**Best practices** [8]: default to the free `aws/secretsmanager` key; use a customer managed key for
cross-account access or custom key policy, with `kms:ViaService = secretsmanager.<region>.amazonaws.com` and
encryption-context conditions; client-side caching; rotate (single/alternating users); least privilege
(IAM, resource policies, ABAC); `secretsmanager:BlockPublicPolicy: true` condition on `PutResourcePolicy`
(Zelkova); caution with `aws:SourceIp` (breaks rotation Lambda calls); `aws:SourceVpc`/`aws:SourceVpce` may
block AWS services acting on your behalf; replicate for DR; monitor via CloudTrail/CloudWatch/Config/GuardDuty;
interface VPC endpoints.

**Legacy-file claims found wrong or unsupported:**
1. `force_delete_without_recovery` on `aws_secretsmanager_secret` — **not an argument** in the 6.x doc [1]; use `recovery_window_in_days = 0`.
2. "v6.x split rotation into its own resource; deprecated inline `rotation_*` args still exist on the secret" —
   the 6.x secret doc has **no** rotation arguments [1]; the upgrade guide has no Secrets Manager entry [6].
3. "`aws_secretsmanager_secret_replica` resource removed in v6" — no such resource appears in any doc fetched;
   replication is the `replica` block [1] (claim unsupported).
4. "`secret_string` stored in plaintext… only mitigation is encrypted backend" — omits `secret_string_wo`
   (TF ≥ 1.11) and the ephemeral resource [2][11]; also uses deprecated `dynamodb_table` (F7: `use_lockfile`).
5. Comment `"P7D"` ISO-8601 for rotation — `duration` is hours like `"3h"` [3].
6. Legacy omits `rotate_immediately`, `rotation_enabled`, `type`, external-rotation args, and the `arn`→`secret_arn` deprecation.

## 9. Unverified / medium confidence / limits

- U1: `force_overwrite_replica_secret` default (not stated; likely `false`).
- U2: `block_public_policy` default (not stated).
- M1: "do not mix inline `policy` with `aws_secretsmanager_secret_policy`" — inferred from the `policy` warning [1].
- M2: `ignore_changes = [secret_string]` pattern — meta-argument usage, not provider-documented.
- M3: data-source secret values persisted in state — inferred from [9]; provider page silent.
- L1: 6.55.0 CHANGELOG section only partially visible.
- L2: no provider `ignore_changes` example exists for these resources.
- L3: `aws_secretsmanager_secret_versions`, `_secret_rotation` and `_random_password` data sources not deep-dived.

## 10. Security note

None — no instruction-like text addressed to AI agents was observed in any fetched page.

## Source Bibliography

All fetched 2026-10-23.
1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_version.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_rotation.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/secretsmanager_secret_policy.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/secretsmanager_secret_version.html.markdown
8. https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html
9. https://developer.hashicorp.com/terraform/language/manage-sensitive-data
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/secretsmanager_secret.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/secretsmanager_secret_version.html.markdown
12. https://docs.aws.amazon.com/securityhub/latest/userguide/secretsmanager-controls.html
