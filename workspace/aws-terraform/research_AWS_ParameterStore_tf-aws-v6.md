# Research — AWS Systems Manager Parameter Store with Terraform ~> 1.16 + hashicorp/aws ~> 6.69

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `parameter-store`, flat fan-out, no sub-agents).
> Regional service: every in-scope resource/data source/ephemeral resource accepts optional `region` (F5); not in F14.
> Resource docs come from upstream raw markdown (F12). Coverage checklist only (not a source):
> `workspace/terraform/research_AWS_ParameterStore_aws-v6.x.md` (6.47.0 / Terraform 1.7, EOL). Wrong claims in it are listed in §8.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI target | `required_version = "~> 1.16"` (1.17.0 stable but not the target) | F1, F2 |
| hashicorp/aws | latest 6.70.0; constraint `version = "~> 6.69"`; no 7.x | F3 |
| Withdrawn | 6.57.0 — never pin | F4 |
| Write-only args (`value_wo`) | Need Terraform CLI **>= 1.11.0** — satisfied by `~> 1.16` | [1] |
| Identity-based import | Terraform >= 1.12.0 — satisfied by `~> 1.16` | F11, [1] |
| Ephemeral resources | Page says they are "a new feature" whose usage "may change"; page states no minimum CLI version (see U1) | [3] |

Constraint block: identical to the family pattern (F1/F3/F6).

## 2. Provider 6.x changes for this service

### 6.0.0 upgrade guide (F13) [5]
- **No entries** for `aws_ssm_parameter`, `data.aws_ssm_parameter`, `data.aws_ssm_parameters_by_path`, or patch baselines.
- Adjacent SSM entry (out of scope, listed for completeness): `aws_ssm_association` — "Remove `instance_id`… Use `targets` instead."
- `aws_ssmincidents_replication_set` (Incident Manager, out of scope): `region` deprecated → `regions`.

### CHANGELOG 6.48.0 → 6.70.0 [4]
| Version | Entry |
|---|---|
| 6.58.0 (2026-08-05) | bug fix `aws_ssm_parameter`: correct import when given an ARN (#49134) |
| 6.58.0 | bug fix `aws_ssm_parameter`: prevent errors when importing a specific version (#49134) |
| 6.59.0 (2026-08-12) | bug fix `aws_ssm_parameter`: names with a leading slash and no other slashes were losing the slash (#49339) |
| 6.59.0 | **New list resource** `aws_ssm_patch_baseline` (#49332) |
| 6.60.0–6.70.0 | No entries for in-scope SSM resources found |
| 6.48.0–6.55.0 | No entries found (see L1 for read coverage) |

Practical consequence: pin at least `~> 6.69` (already the family constraint) so the 6.58/6.59 import and name fixes are in effect.

## 3. Resource `aws_ssm_parameter` [1]

### Arguments
| Argument | Req | Notes / default |
|---|---|---|
| `name` | Yes | Names with a path must start with `/` |
| `type` | Yes | `String`, `StringList`, `SecureString` |
| `value` | One of three | **Always marked sensitive** in plan output |
| `insecure_value` | One of three | **Never** marked sensitive; **cannot be used with `SecureString`** |
| `value_wo` | One of three | Write-only: **never stored in state**; requires `value_wo_version`; Terraform >= 1.11 |
| `value_wo_version` | With `value_wo` | Changing it triggers an update of `value_wo` (the only way to push a new write-only value) |
| `tier` | No | `Standard`, `Advanced`, `Intelligent-Tiering`. Default = the account/Region default tier. **Downgrading `Advanced` → `Standard` recreates the resource** |
| `key_id` | No | KMS key ID/ARN for `SecureString`; when omitted AWS uses `aws/ssm` [8] |
| `data_type` | No | `text`, `aws:ssm:integration`, `aws:ec2:image` (AMI IDs) |
| `allowed_pattern` | No | Regex validating the value |
| `description` | No | — |
| `overwrite` | No | Default `false` on create, `true` afterward. Lets Terraform overwrite an existing parameter (including one created outside Terraform). **Not marked deprecated on the current page** — see §8 |
| `tags` | No | Overrides matching provider `default_tags` keys |
| `region` | No | F5 |

### Documented notes
- Exactly one of `value`, `value_wo`, `insecure_value` is required.
- State exposure, quoted in substance from the page: the unencrypted value of a `SecureString` "is stored in state as plain text" when using `value` (page links Terraform's sensitive-data-in-state guidance). Only `value_wo` avoids this. [1]
- `aws:ssm:integration` parameters must be `SecureString` and named with the prefix `/d9d01087-4a3f-49e0-b0b4-d568d7826553/ssm/integrations/webhook/`.
- Use lifecycle rules (e.g. `ignore_changes`) for other update behavior (the page points to lifecycle rather than `overwrite`).

### Attributes
`arn`, `version`, `has_value_wo`, `tags_all`.

### Import
- TF >= 1.12: `import { identity = { name = "/app/prod/x" } }` (`account_id`, `region` optional) (F11).
- TF >= 1.5: `import { id = "<parameter name>" }`.
- CLI: `terraform import aws_ssm_parameter.x /app/prod/x`. ARN import was fixed in 6.58.0 [4].

### Recommended write pattern (derived from [1])
```hcl
resource "aws_ssm_parameter" "db_password" {
  name             = "/myapp/prod/db/password"
  type             = "SecureString"
  key_id           = aws_kms_key.params.arn
  value_wo         = ephemeral.random_password.db.result # or var marked ephemeral
  value_wo_version = 1                                    # bump to rotate
}

resource "aws_ssm_parameter" "db_host" {
  name           = "/myapp/prod/db/host"
  type           = "String"
  insecure_value = aws_db_instance.main.address # non-secret, readable diff
}
```
(`ephemeral.random_password` lives in the hashicorp/random provider — not verified in this unit, U2.)

## 4. Reading parameters

### Data source `aws_ssm_parameter` [2]
- Args: `name` (required; `name:version` selects a version, e.g. `foo:3`), `with_decryption` (default **`true`**), `region`.
- Attrs: `arn`, `name`, `type`, `value` (always sensitive), `insecure_value` (never sensitive), `version`.
- Note: decrypted `SecureString` value "is stored in the raw state as plain text". Every type returns a string; use `split()` for `StringList`.

### Ephemeral resource `aws_ssm_parameter` [3]
- Args: **`arn`** (required — not `name`), `with_decryption` (default `true`), `region`.
- Attrs: `name`, `type`, `value`, `version`, `with_decryption`.
- Ephemeral values are not persisted in state/plan (general Terraform semantics, M1). Usable only in ephemeral contexts (write-only args such as `value_wo`/`password_wo`, provider config, other ephemeral resources) — M1.
- To get metadata without the value, the page directs you to the data source.

### Data source `aws_ssm_parameters_by_path` [6]
- Args: `path` (required, starts with `/`, max 15 levels), `recursive` (default `false`), `with_decryption` (default `true`), `region`.
- Attrs: `arns`, `names`, `types`, `values` (always sensitive; `nonsensitive()` only if certain no secrets are returned).
- With `with_decryption = true`, decrypted values are stored in state as plain text.
- Passing a full parameter name as `path` returns nothing unless other parameters use it as a hierarchy prefix.

## 5. Service facts from AWS docs

### Tiers and limits [7][9][10]
| | Standard | Advanced |
|---|---|---|
| Max parameters / account / Region | 10,000 | 100,000 |
| Max value size | 4 KB (KMS page: 4096 bytes) | 8 KB |
| Parameter policies | No | Yes (max 10 per parameter) |
| Cross-account sharing | No | Yes |
| Downgrade | — | **Not possible** (would truncate, drop policies, different encryption); delete and recreate |
| Cost | No charge | Charged |
- Versions retained: 100 per parameter. [9]
- Throughput: default 40 TPS shared by GetParameter/GetParameters/GetParametersByPath; with higher throughput: 10,000 / 1,000 / 100. PutParameter default 3 TPS (10 high). Higher throughput is charged; SecureString may also be limited by KMS quotas. [9] — relevant to Terraform `for_each` over many parameters (PutParameter 3 TPS → throttling/retries, M2).
- `Intelligent-Tiering` is primarily a **default-tier setting** (`UpdateServiceSetting`); it creates Standard unless the request needs Advanced (>4 KB, policies, >10,000 count) and then upgrades automatically. [10] Upgrades are one-way, so values can silently become billable Advanced parameters.
- Default tier is set per account/Region via service setting `/ssm/parameter-store/default-parameter-tier`; changing it does not affect existing parameters. [7]

### Hierarchy and naming [11]
- Hierarchies use `/`; maximum **15 levels**. Suggested shapes: `/Environment/Type/Application/Data` (e.g. `/Dev/WebServer/Linux/approved-ami`).
- `/parameter-name` and `parameter-name` are both treated as root parameters.
- `GetParametersByPath` returns everything under a level; add `--with-decryption` for SecureString.
- Other name constraints (length, allowed characters, reserved `aws`/`ssm` prefixes): **unverified** — the naming-constraints page returned no content (U3).

### SecureString and KMS [8]
- Only **symmetric** KMS keys are supported.
- No `key_id` → AWS managed key alias `aws/ssm`. "You cannot establish access control policies for the default `aws/ssm` KMS key" → use a CMK when you need key-policy control (cross-account readers, separation of duties).
- Standard: KMS `Encrypt` directly (needs `kms:Encrypt`). Advanced: envelope encryption via AWS Encryption SDK (needs `kms:GenerateDataKey`). Decrypt both: `kms:Decrypt`.
- Encryption context: `PARAMETER_ARN = arn:aws:ssm:<region>:<account>:parameter/<name>` — usable in IAM conditions `kms:EncryptionContext:PARAMETER_ARN` to scope decrypt to specific parameters.

### IAM for parameter paths [8][12]
- Resource ARN pattern in AWS examples: `arn:aws:ssm:<region>:<account>:parameter/FinancialParameters/*` (note: no leading `/` after `parameter` in ARN for hierarchical names; e.g. `parameter/ReadableParameters/MyParameter`).
- Readers: `ssm:GetParameter*` on the path + `kms:Decrypt` on the CMK; writers: `ssm:PutParameter` + `kms:Encrypt` (standard) or `kms:GenerateDataKey` (advanced).
- Parameter Store overview: IAM can let a role read `/myapp/prod/*` but not `/myapp/dev/*`. [12]
- Whether `GetParametersByPath` needs the bare path ARN as well as `path/*`: **unverified** (U4 — the access page returned no content).

### Parameter Store vs Secrets Manager (only as stated by AWS) [12]
- AWS: "For secrets such as database credentials, API keys, or tokens, we recommend AWS Secrets Manager, which provides purpose built security controls including automatic rotation and cross-region replication."
- Comparison table: Parameter Store — static config, approved AMI IDs, endpoints; rotation **None**; standard tier free. Secrets Manager — credentials, automatic rotation, cross-account access, fine-grained audit logging; billed per secret/month.
- Updates take effect on next read, no validation/rollback (AppConfig offers that). ECS env vars from Parameter Store resolve at task start.

## 6. Patch baselines (brief)
- `aws_ssm_patch_baseline` gained a **list resource** in 6.59.0 [4]. `aws_ssm_default_patch_baseline` exists in provider docs — arguments not researched (L2). Quota: 50 patch baselines, 25 patch groups per baseline [9]. Security Hub SSM.2 (patch compliance, High) relates to Patch Manager, not parameters [13].
- `aws_ssm_maintenance_window`: out of scope.

## 7. AWS guidance

### Security Hub CSPM SSM controls [13]
| ID | Title | Severity | Relevance to parameters |
|---|---|---|---|
| SSM.1 | EC2 instances should be managed by Systems Manager | Medium | None |
| SSM.2 | Managed instances patch compliance COMPLIANT | High | None (Patch Manager) |
| SSM.3 | Association compliance COMPLIANT | Low | None |
| SSM.4 | SSM documents should not be public | Critical | None (documents) |
| SSM.5 | SSM documents should be tagged | Low | None |
| SSM.6 | SSM Automation CloudWatch logging enabled | Medium | None |
| SSM.7 | SSM documents block public sharing enabled | Critical | None |
**No Security Hub control evaluates Parameter Store parameters** (as of 2026-10-23).

### Best practices (each tied to an official statement)
1. Store real secrets in Secrets Manager; use SecureString for encrypted config [12].
2. Prefer `value_wo` + `value_wo_version` for SecureString writes so plaintext never lands in state [1]; prefer the ephemeral resource over the data source to read secrets [2][3].
3. Use `insecure_value` for non-secret `String`/`StringList` to keep diffs readable; never with SecureString [1].
4. Use a CMK (`key_id`) when key-policy control or encryption-context scoping is needed; `aws/ssm` cannot be policy-controlled [8].
5. Design hierarchies (<= 15 levels) aligned with env/app and scope IAM by path [11][12].
6. Choose tier explicitly; avoid relying on Advanced unless needed (one-way, charged) [7][10]; downgrade in Terraform = replacement [1].
7. Watch throughput quotas when creating/reading many parameters [9].

## 8. Legacy-file claims found wrong or unsupported
| # | Legacy claim | Finding |
|---|---|---|
| W1 | "`overwrite` deprecated since provider v5.0", "causes perpetual plan diffs" | Current page documents `overwrite` without a deprecation marker, default `false` on create / `true` after [1]. Deprecation not confirmed — wrong as stated. |
| W2 | Advanced→Standard in Terraform "will cause a persistent error and may require `terraform state rm`" | Page: downgrading "recreates the resource" [1]. Wrong. |
| W3 | Intelligent-Tiering row "100,000/region, 8 KB" treated as a third tier | AWS describes it as a default-tier setting choosing Standard or Advanced [10]. Misleading. |
| W4 | Omits `value_wo`/`value_wo_version` and claims ephemeral resource is the way to avoid state for *writes* | The ephemeral resource only reads; `aws_ssm_parameter.value` still stores plaintext — writes need `value_wo` [1][3]. Gap. |
| W5 | "ephemeral `aws_ssm_parameter` (introduced in provider v6.x)" | Not confirmed in sources read (U1). |
| W6 | Citations to registry.terraform.io pages | JS-only pages (F12); not verifiable sources. |

## 9. Unverified / medium-confidence / limits
- **U1** Minimum Terraform CLI version for ephemeral resources and the provider version that introduced `ephemeral.aws_ssm_parameter` (not stated on [3]).
- **U2** `ephemeral "random_password"` in hashicorp/random (out of unit scope).
- **U3** Parameter name constraints (length, characters, reserved prefixes) — page fetch empty.
- **U4** IAM need for bare-path ARN with `GetParametersByPath`; recursive-deny behavior — access page fetch empty.
- **M1** Ephemeral-value semantics (not persisted; ephemeral contexts only) are general Terraform behavior, not restated on [3] (medium confidence).
- **M2** Terraform throttling with many parameters inferred from PutParameter 3 TPS quota [9] (medium confidence).
- **L1** CHANGELOG read from top through ~6.40 in two chunks; the 6.55.0 section boundary was split across chunks, so a 6.55.0 SSM entry could be missed.
- **L2** `aws_ssm_default_patch_baseline` / `aws_ssm_patch_baseline` arguments not researched (brief: "only briefly").
- **L3** Parameter policies (Expiration, ExpirationNotification, NoChangeNotification) — no Terraform argument documented on [1]; not researched further.
- **L4** Pricing figures not researched (legacy "$0.05/param/month" not verified).

## 10. Security note
No prompt-injection text observed. Two fetches (naming-constraints, access-control pages) returned empty bodies and the fetch tool substituted general-knowledge text; that text was **discarded** and the items marked U3/U4.

## Source Bibliography
All accessed 2026-10-23.
1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameter.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/ephemeral-resources/ssm_parameter.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/ssm_parameters_by_path.html.markdown
7. https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html
8. https://docs.aws.amazon.com/systems-manager/latest/userguide/secure-string-parameter-kms-encryption.html
9. https://docs.aws.amazon.com/general/latest/gr/ssm.html
10. https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-default-tier.html
11. https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html
12. https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html
13. https://docs.aws.amazon.com/securityhub/latest/userguide/ssm-controls.html
14. c:\agents\agents-factory\workspace\aws-terraform\_family_facts_v6.md (F1–F6, F11–F13)
