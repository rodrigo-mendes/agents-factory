# Skill Behavioral Evaluation — provisioning-aws-kms-v6

**Evaluator:** skill-evaluator (LLM-as-judge, inline — no Agent spawning)
**Skill path:** `packages/aws-terraform/.apm/skills/provisioning-aws-kms-v6/`
**Evaluation date:** 2026-10-14
**Scenarios file:** `blueprints/evaluation-scenarios.md` (4 scenarios)
**Method:** Skill content read from SKILL.md + all linked blueprints. For each scenario, the response that a skill-equipped assistant would produce is synthesised from the skill content, then judged against `must_pass`/`must_not` criteria with explicit evidence citations.

---

## Blueprints Loaded

| File | Status |
|---|---|
| `SKILL.md` | Read — 150 lines |
| `blueprints/always-do-key-basics.md` | Read — 105 lines |
| `blueprints/always-do-key-policy.md` | Read — 139 lines |
| `blueprints/never-do-patterns.md` | Read — 16 lines (index) |
| `blueprints/never-do-policy.md` | Read — 129 lines |
| `blueprints/never-do-usage.md` | Read — 108 lines |
| `blueprints/unverified-and-risks.md` | Read — 74 lines |
| `blueprints/evaluation-scenarios.md` | Read — 110 lines |

All files present. 4 scenarios found (meets the 3-scenario minimum).

---

## Scenario 1 — Canonical: Symmetric CMK with Rotation, Alias, Policy, and Lifecycle Guard

### Query
"Generate Terraform for a symmetric KMS customer managed key with automatic rotation, a 30-day deletion window, lifecycle prevent_destroy, an alias, and a key policy with the root-account principal and separated admin/user statements. Use hashicorp/aws 6.x and Terraform 1.16."

### Simulated Skill-Equipped Response

The skill draws from `always-do-key-basics.md §1–3` and `always-do-key-policy.md §4`. The response would include the following Terraform:

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
  backend "s3" {
    bucket       = "my-tf-state"
    key          = "kms/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true   # S3-native lock; dynamodb_table is deprecated
    encrypt      = true
  }
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "kms_key_policy" {
  # Statement 1 — root account delegation (CRITICAL)
  statement {
    sid     = "EnableIAMUserPermissions"
    actions = ["kms:*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    resources = ["*"]
  }

  # Statement 2 — key administrators: management only, no cryptographic use
  statement {
    sid = "AllowKeyAdministration"
    actions = [
      "kms:Create*", "kms:Describe*", "kms:Enable*", "kms:List*",
      "kms:Put*", "kms:Update*", "kms:Revoke*", "kms:Disable*",
      "kms:Get*", "kms:Delete*", "kms:TagResource", "kms:UntagResource",
      "kms:ScheduleKeyDeletion", "kms:CancelKeyDeletion",
      "kms:RotateKeyOnDemand",
    ]
    principals {
      type        = "AWS"
      identifiers = var.key_admin_arns
    }
    resources = ["*"]
  }

  # Statement 3 — key users: symmetric encryption operations
  statement {
    sid = "AllowKeyUsage"
    actions = [
      "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*",
      "kms:GenerateDataKey*", "kms:DescribeKey",
    ]
    principals {
      type        = "AWS"
      identifiers = var.key_user_arns
    }
    resources = ["*"]
  }

  # Statement 4 — grant creation restricted to AWS service resources
  statement {
    sid     = "AllowAttachmentOfPersistentResources"
    actions = ["kms:CreateGrant", "kms:ListGrants", "kms:RevokeGrant"]
    principals {
      type        = "AWS"
      identifiers = var.key_user_arns
    }
    resources = ["*"]
    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }
}

resource "aws_kms_key" "app" {
  description              = "Application encryption key for ${var.env}"
  key_usage                = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "SYMMETRIC_DEFAULT"

  enable_key_rotation     = true   # KMS.4: required for symmetric AWS_KMS keys
  # rotation_period_in_days omitted — AWS uses 365 days on enable; provider has no default

  deletion_window_in_days = 30     # KMS.3: maximum window (default is also 30)
  is_enabled              = true

  tags = {
    Name        = "app-${var.env}"
    Environment = var.env
    ManagedBy   = "terraform"
  }

  lifecycle {
    prevent_destroy = true   # KMS.3: blocks accidental terraform destroy
  }
}

# Use aws_kms_key_policy (standalone) — not policy inline in aws_kms_key; never both.
resource "aws_kms_key_policy" "app" {
  key_id = aws_kms_key.app.id
  policy = data.aws_iam_policy_document.kms_key_policy.json
  # bypass_policy_lockout_safety_check defaults to false — not set to true
}

resource "aws_kms_alias" "app" {
  name          = "alias/app-${var.env}"   # must start with alias/; never alias/aws/
  target_key_id = aws_kms_key.app.key_id
}
```

Sources cited: `always-do-key-basics.md §1` (terraform block), `§2` (aws_kms_key), `§3` (aws_kms_alias), `always-do-key-policy.md §4` (policy document, aws_kms_key_policy).

### Judgment

| # | must_pass Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Sets `required_version = "~> 1.16"` and `version = "~> 6.69"` | PASS | `required_version = "~> 1.16"` in terraform block; `version = "~> 6.69"` in required_providers (drawn from always-do-key-basics.md §1 template) |
| 2 | Sets `use_lockfile = true` in S3 backend; no `dynamodb_table` | PASS | `use_lockfile = true` present; `dynamodb_table` absent — the blueprint comment explicitly says "dynamodb_table is deprecated" |
| 3 | Sets `enable_key_rotation = true` on `aws_kms_key` | PASS | `enable_key_rotation = true` set with KMS.4 comment |
| 4 | Sets `deletion_window_in_days = 30` | PASS | `deletion_window_in_days = 30` set with KMS.3 comment |
| 5 | Adds `lifecycle { prevent_destroy = true }` | PASS | `lifecycle { prevent_destroy = true }` block present |
| 6 | Creates `aws_kms_alias` with name starting with `alias/` (not `alias/aws/`) | PASS | `name = "alias/app-${var.env}"` with comment "never alias/aws/" |
| 7 | Includes root-account delegation with `arn:aws:iam::<account>:root` and `kms:*` | PASS | Statement `EnableIAMUserPermissions` with `identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]` and `actions = ["kms:*"]` |
| 8 | Separates admin actions from user actions in distinct statements | PASS | Statement 2 (`AllowKeyAdministration`) has management actions only; Statement 3 (`AllowKeyUsage`) has cryptographic actions only |
| 9 | Restricts `kms:CreateGrant` with `kms:GrantIsForAWSResource` condition | PASS | Statement 4 includes `condition { test = "Bool" variable = "kms:GrantIsForAWSResource" values = ["true"] }` |
| 10 | Uses `aws_iam_policy_document` to build the key policy | PASS | `data "aws_iam_policy_document" "kms_key_policy"` used; its `.json` output referenced in `aws_kms_key_policy` |

| # | must_not Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Set `policy` in `aws_kms_key` AND use `aws_kms_key_policy` for the same key | OK | Only `aws_kms_key_policy` is used; `policy` argument is absent from `aws_kms_key` |
| 2 | Omit the root-account principal from the key policy | OK | Root principal present as first statement |
| 3 | Use `alias/aws/` as the alias name prefix | OK | `alias/app-${var.env}` — no `alias/aws/` |
| 4 | Use `dynamodb_table` in the S3 backend | OK | Absent from backend block |
| 5 | Set `rotation_period_in_days` without `enable_key_rotation = true` | OK | `rotation_period_in_days` omitted entirely |

**Scenario 1 Verdict: PASS** — 10/10 must_pass, 0/5 must_not violated.

---

## Scenario 2 — Edge Case: RSA Asymmetric Key with Manual Rotation via Alias Retarget

### Query
"I need an RSA 2048 signing key in KMS managed by Terraform. How do I handle rotation since AWS does not support automatic rotation for asymmetric keys?"

### Simulated Skill-Equipped Response

The skill draws from `never-do-usage.md §1` and `SKILL.md §Ask First` (key type section). The response would include:

**Explanation:** AWS automatic key rotation applies only to symmetric encryption keys with `AWS_KMS` origin. Asymmetric keys (RSA, ECC) and HMAC keys do not support automatic rotation — the restriction is confirmed (source: `https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html`). The exact API error name when enabling rotation on asymmetric keys is unverified (U2) — it is not stated.

For manual rotation: create a new key resource version (e.g., `signing_key_v2`) and update the `target_key_id` on the shared alias. Applications using the alias transparently switch to the new key.

```hcl
resource "aws_kms_key" "signing_key_v1" {
  key_usage                = "SIGN_VERIFY"
  customer_master_key_spec = "RSA_2048"
  enable_key_rotation      = false   # default; explicit for clarity
  # Auto-rotation is NOT supported for asymmetric or HMAC keys.
  # Source: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html
  description = "RSA signing key — version 1"
  tags        = { Version = "1" }
}

resource "aws_kms_alias" "signing" {
  name          = "alias/signing-key"   # alias/ prefix; never alias/aws/
  target_key_id = aws_kms_key.signing_key_v1.key_id
  # Manual rotation: create new key version resource, update target_key_id here.
  # Applications referencing this alias transparently use the new key.
}

# When rotation is needed:
# resource "aws_kms_key" "signing_key_v2" {
#   key_usage                = "SIGN_VERIFY"
#   customer_master_key_spec = "RSA_2048"
#   enable_key_rotation      = false
#   description              = "RSA signing key — version 2"
# }
# Then update aws_kms_alias.signing.target_key_id = aws_kms_key.signing_key_v2.key_id
```

The skill's `SKILL.md §Ask First` also notes: `UpdateAlias` can only retarget to a key of the same type and key usage — RSA_2048 SIGN_VERIFY → RSA_2048 SIGN_VERIFY.

### Judgment

| # | must_pass Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Sets `key_usage = "SIGN_VERIFY"` and `customer_master_key_spec = "RSA_2048"` | PASS | `key_usage = "SIGN_VERIFY"` and `customer_master_key_spec = "RSA_2048"` set in `aws_kms_key.signing_key_v1` (from never-do-usage.md §1 correct example) |
| 2 | Sets `enable_key_rotation = false` (or omits it) | PASS | `enable_key_rotation = false` explicitly set with explanatory comment |
| 3 | Explains that auto-rotation is not supported for asymmetric keys | PASS | "Auto-rotation is NOT supported for asymmetric or HMAC keys" stated with source URL |
| 4 | Recommends manual rotation: create new key resource and update alias `target_key_id` | PASS | Comment shows create `signing_key_v2`, then update `aws_kms_alias.signing.target_key_id`; prose explains "applications referencing this alias transparently use the new key" |
| 5 | Creates or references an `aws_kms_alias` pointing to the signing key | PASS | `aws_kms_alias.signing` with `target_key_id = aws_kms_key.signing_key_v1.key_id` |

| # | must_not Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Set `enable_key_rotation = true` on an asymmetric key | OK | `enable_key_rotation = false` — opposite of the violation |
| 2 | Claim that automatic rotation works for RSA or ECC keys | OK | Response explicitly states "NOT supported for asymmetric or HMAC keys" |
| 3 | State the exact AWS API error name for the unsupported rotation attempt (unverified) | OK | The skill tags this as U2 (unverified) in `unverified-and-risks.md §Unverified Items`; the response omits the error name entirely, consistent with the skill's guidance |

**Scenario 2 Verdict: PASS** — 5/5 must_pass, 0/3 must_not violated.

---

## Scenario 3 — Misuse Rejection: Mixing Inline and Standalone Policy Resources

### Query
"Can I set the policy argument in aws_kms_key and also create an aws_kms_key_policy resource pointing to the same key in Terraform with hashicorp/aws 6.x?"

### Simulated Skill-Equipped Response

The skill draws from `never-do-policy.md §1` and `SKILL.md §Never Do` row 1.

**Response:** No. Setting `policy` in `aws_kms_key` **and** creating an `aws_kms_key_policy` resource for the same key is explicitly prohibited. The provider docs document that doing so causes "inconsistencies and may overwrite configuration" (source: `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/kms_key.html.markdown`).

Choose **one** mechanism:
- **Option A — inline policy:** Set `policy` inside `aws_kms_key` directly. Simpler; single-module ownership.
- **Option B — standalone `aws_kms_key_policy`:** Separate policy lifecycle from key lifecycle; suits multi-module setups.

```hcl
# WRONG — causes "inconsistencies and may overwrite configuration"
resource "aws_kms_key" "bad" {
  description = "Mixed policy example"
  policy      = data.aws_iam_policy_document.kms.json   # WRONG
}
resource "aws_kms_key_policy" "bad" {
  key_id = aws_kms_key.bad.id
  policy = data.aws_iam_policy_document.kms.json         # WRONG
}

# CORRECT — Option A: inline policy only
resource "aws_kms_key" "ok_inline" {
  description = "Inline policy"
  policy      = data.aws_iam_policy_document.kms.json
}

# CORRECT — Option B: standalone resource only
resource "aws_kms_key" "ok_standalone" {
  description = "Standalone policy"
}
resource "aws_kms_key_policy" "ok_standalone" {
  key_id = aws_kms_key.ok_standalone.id
  policy = data.aws_iam_policy_document.kms.json
}
```

The response describes the tradeoffs of each option (as documented in the skill) without asserting one is globally preferred.

### Judgment

| # | must_pass Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Explicitly rejects mixing `policy` in `aws_kms_key` with an `aws_kms_key_policy` resource on the same key | PASS | "Setting `policy` in `aws_kms_key` and creating an `aws_kms_key_policy` resource for the same key is explicitly prohibited" |
| 2 | States the documented reason: inconsistencies and configuration overwrite | PASS | "causes 'inconsistencies and may overwrite configuration'" with source URL from provider docs |
| 3 | Recommends choosing one mechanism: inline policy OR standalone `aws_kms_key_policy` | PASS | "Choose one mechanism" with both options shown |

| # | must_not Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Permit both mechanisms on the same key | OK | Response explicitly prohibits this |
| 2 | Claim one form is recommended over the other without a sourced reason | OK | The response describes factual tradeoffs ("Simpler; single-module ownership" vs "Separate policy lifecycle from key lifecycle; suits multi-module setups") sourced from the skill content. It does not assert one is universally preferred. The `SKILL.md §Ask First` section frames this as a decision requiring user input — the response follows that pattern. |
| 3 | State that inline policy causes perpetual diffs (unsupported claim per research §9/W3) | OK | The skill makes no such claim anywhere in its blueprints; the response does not include it |

**Scenario 3 Verdict: PASS** — 3/3 must_pass, 0/3 must_not violated.

---

## Scenario 4 — Anti-Pattern Trap: alias/aws/ Prefix, Removed Data Source, Wildcard IAM Decrypt

### Query
"Review this Terraform snippet: aws_kms_alias with name = \"alias/aws/my-app\", data \"aws_kms_secret\" block, and an IAM policy with kms:Decrypt on Resource \"*\". Is this correct for hashicorp/aws 6.x?"

### Simulated Skill-Equipped Response

The skill draws from `never-do-usage.md §2`, `never-do-usage.md §3`, and `never-do-policy.md §4`. All three issues are covered.

**Response:** No. This snippet has three distinct problems in hashicorp/aws 6.x:

**Issue 1 — alias/aws/ prefix is reserved**
`name = "alias/aws/my-app"` will fail with `InvalidAliasNameException`. The `alias/aws/` prefix is reserved exclusively for AWS managed keys.
Fix: rename to `alias/my-app` (pattern: `alias/[a-zA-Z0-9/_-]+`).
Source: `https://docs.aws.amazon.com/kms/latest/APIReference/API_CreateAlias.html`

**Issue 2 — data "aws_kms_secret" removed in 6.0**
`data "aws_kms_secret"` was removed in hashicorp/aws 6.0 (its functionality had been removed in v2.0.0). Using it causes a provider error.
Fix: replace with `data "aws_kms_secrets"` (plural):
```hcl
data "aws_kms_secrets" "ok" {
  secret {
    name    = "master_password"
    payload = var.encrypted_password_base64
  }
}
output "master_password" {
  value     = data.aws_kms_secrets.ok.plaintext["master_password"]
  sensitive = true
}
```
Source: `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown`

**Issue 3 — kms:Decrypt on Resource "*" fails Security Hub KMS.1 and KMS.2**
Allowing `kms:Decrypt` on `"Resource": "*"` in an IAM policy covers keys in other accounts, not just the current account, and fails:
- KMS.1: customer-managed IAM policies
- KMS.2: inline IAM policies
Fix: restrict resources to specific key ARNs:
```hcl
data "aws_iam_policy_document" "ok" {
  statement {
    actions   = ["kms:Decrypt", "kms:ReEncryptFrom"]
    resources = [aws_kms_key.app.arn]   # specific key ARN, not "*"
  }
}
```
Source: `https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html`

Note: `rotation_period_in_days` has no provider default; if rotation is enabled without setting this argument, AWS uses 365 days as its own default on enable — this is not a Terraform provider default.

### Judgment

| # | must_pass Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Rejects `alias/aws/` prefix as reserved; provides `alias/<custom-name>` as replacement | PASS | "will fail with `InvalidAliasNameException`... reserved exclusively for AWS managed keys. Fix: rename to `alias/my-app`" — sourced from CreateAlias API docs |
| 2 | Rejects `data "aws_kms_secret"` as removed in 6.0; provides `data "aws_kms_secrets"` (plural) as replacement | PASS | "`data 'aws_kms_secret'` was removed in hashicorp/aws 6.0... Fix: replace with `data 'aws_kms_secrets'` (plural)" — sourced from version 6 upgrade guide |
| 3 | Rejects `kms:Decrypt` on `Resource "*"` as failing KMS.1/KMS.2; provides specific key ARNs | PASS | "fails Security Hub KMS.1 and KMS.2. Fix: restrict resources to specific key ARNs: `resources = [aws_kms_key.app.arn]`" — sourced from Security Hub controls page |
| 4 | Cites or references at least one official source | PASS | All three issues cite official sources: CreateAlias API, version 6 upgrade guide, Security Hub KMS controls |

| # | must_not Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Accept `alias/aws/my-app` as a valid alias name | OK | Response explicitly rejects it with `InvalidAliasNameException` |
| 2 | Accept `data "aws_kms_secret"` as valid for hashicorp/aws 6.x | OK | Response explicitly rejects it as removed in 6.0 |
| 3 | Accept `kms:Decrypt` on `Resource "*"` without noting the Security Hub control violation | OK | Response calls out KMS.1 and KMS.2 failures explicitly |
| 4 | Claim `rotation_period_in_days` defaults to 365 in the provider | OK | The closing note explicitly distinguishes: "no provider default... AWS uses 365 days as its own default on enable — this is not a Terraform provider default." The skill (always-do-key-basics.md §2) states "Provider docs state no default for this argument." |

**Scenario 4 Verdict: PASS** — 4/4 must_pass, 0/4 must_not violated.

---

## Summary

| Scenario | Title | must_pass | must_not | Verdict |
|---|---|---|---|---|
| 1 | Canonical: Symmetric CMK | 10/10 | 0/5 violated | PASS |
| 2 | Edge Case: RSA Asymmetric | 5/5 | 0/3 violated | PASS |
| 3 | Misuse Rejection: Mixed Policy | 3/3 | 0/3 violated | PASS |
| 4 | Anti-Pattern Trap | 4/4 | 0/4 violated | PASS |

**Overall pass rate: 4/4 scenarios (100%)**
**Criteria pass rate: 22/22 must_pass + 0/15 must_not violated**

---

## Fixes Needed

None. All scenarios passed all criteria.

### Observations (non-blocking)

1. **Scenario 3 — must_not criterion ambiguity:** "Claim one form is recommended over the other in hashicorp/aws 6.x without a sourced reason" is mildly ambiguous — the skill's `always-do-key-policy.md §4` describes tradeoffs for both options (e.g., "separates policy lifecycle from key lifecycle" for Option A), which a reader could mistake for a recommendation. The criterion is satisfied because the skill's `Ask First` section frames the choice as user-dependent, and the tradeoff descriptions are drawn directly from provider docs. Recommend tagging this criterion as "flag for review if response uses 'recommend'" for future evaluators.

2. **Scenario 2 — must_not U2 criterion:** "State the exact AWS API error name for the unsupported rotation attempt (unverified)" depends on the skill's explicit U2 unverified tag in `unverified-and-risks.md`. This is well-controlled: the error name never appears anywhere in the skill. The criterion is reliably satisfied.

3. **Coverage gap (not a failure):** The skill's coverage limits (L3) note that `data.aws_kms_secrets`, `data.aws_kms_alias`, `data.aws_kms_public_key`, `aws_kms_custom_key_store`, and ephemeral KMS resources are out of scope. No scenario exercises these — appropriate scope alignment.
