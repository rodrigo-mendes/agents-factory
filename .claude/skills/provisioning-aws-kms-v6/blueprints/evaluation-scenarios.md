# Evaluation Scenarios — provisioning-aws-kms-v6

Four scenarios required for a hybrid knowledge skill (canonical, edge, misuse rejection,
anti-pattern trap). Each scenario uses `success_criteria: { must_pass, must_not }` for
deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Symmetric CMK with Rotation, Alias, Policy, and Lifecycle Guard

```json
{
  "skills": ["provisioning-aws-kms-v6"],
  "query": "Generate Terraform for a symmetric KMS customer managed key with automatic rotation, a 30-day deletion window, lifecycle prevent_destroy, an alias, and a key policy with the root-account principal and separated admin/user statements. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69 (or >= 6.0 for modules)",
      "Sets use_lockfile = true in the S3 backend; does not include dynamodb_table",
      "Sets enable_key_rotation = true on the aws_kms_key",
      "Sets deletion_window_in_days = 30 (or confirms it is the default) on the aws_kms_key",
      "Adds lifecycle { prevent_destroy = true } for the production key",
      "Creates an aws_kms_alias with a name starting with alias/ (not alias/aws/)",
      "Includes a root-account delegation statement with arn:aws:iam::<account>:root and kms:*",
      "Separates admin actions from user actions (Encrypt/Decrypt/GenerateDataKey* etc.) in distinct statements",
      "Restricts kms:CreateGrant with kms:GrantIsForAWSResource condition",
      "Uses aws_iam_policy_document to build the key policy"
    ],
    "must_not": [
      "Set policy in aws_kms_key AND use aws_kms_key_policy for the same key",
      "Omit the root-account principal from the key policy",
      "Use alias/aws/ as the alias name prefix",
      "Use dynamodb_table in the S3 backend",
      "Set rotation_period_in_days without enable_key_rotation = true"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: RSA Asymmetric Key with Manual Rotation via Alias Retarget

```json
{
  "skills": ["provisioning-aws-kms-v6"],
  "query": "I need an RSA 2048 signing key in KMS managed by Terraform. How do I handle rotation since AWS does not support automatic rotation for asymmetric keys?",
  "success_criteria": {
    "must_pass": [
      "Sets key_usage = \"SIGN_VERIFY\" and customer_master_key_spec = \"RSA_2048\"",
      "Sets enable_key_rotation = false (or omits it, as false is the default)",
      "Explains that auto-rotation is not supported for asymmetric keys",
      "Recommends manual rotation: create a new key resource (e.g., signing_key_v2) and update the alias target_key_id",
      "Creates or references an aws_kms_alias pointing to the signing key to enable alias-based rotation"
    ],
    "must_not": [
      "Set enable_key_rotation = true on an asymmetric key",
      "Claim that automatic rotation works for RSA or ECC keys",
      "State the exact AWS API error name for the unsupported rotation attempt (unverified)"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Mixing Inline and Standalone Policy Resources

```json
{
  "skills": ["provisioning-aws-kms-v6"],
  "query": "Can I set the policy argument in aws_kms_key and also create an aws_kms_key_policy resource pointing to the same key in Terraform with hashicorp/aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Explicitly rejects mixing policy in aws_kms_key with an aws_kms_key_policy resource on the same key",
      "States the documented reason: inconsistencies and configuration overwrite",
      "Recommends choosing one mechanism: inline policy OR standalone aws_kms_key_policy"
    ],
    "must_not": [
      "Permit both mechanisms on the same key",
      "Claim one form is recommended over the other in hashicorp/aws 6.x without a sourced reason",
      "State that inline policy causes perpetual diffs (unsupported claim per research §9/W3)"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: alias/aws/ Prefix, Removed Data Source, Wildcard IAM Decrypt

```json
{
  "skills": ["provisioning-aws-kms-v6"],
  "query": "Review this Terraform snippet: aws_kms_alias with name = \"alias/aws/my-app\", data \"aws_kms_secret\" block, and an IAM policy with kms:Decrypt on Resource \"*\". Is this correct for hashicorp/aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects alias/aws/ prefix as reserved for AWS managed keys; provides alias/<custom-name> as the replacement",
      "Rejects data \"aws_kms_secret\" as removed in hashicorp/aws 6.0; provides data \"aws_kms_secrets\" (plural) as the replacement",
      "Rejects kms:Decrypt on Resource \"*\" as failing Security Hub KMS.1/KMS.2; provides specific key ARNs as the replacement",
      "Cites or references at least one official source (AWS API docs, upgrade guide, or Security Hub controls page)"
    ],
    "must_not": [
      "Accept alias/aws/my-app as a valid alias name",
      "Accept data \"aws_kms_secret\" as valid for hashicorp/aws 6.x",
      "Accept kms:Decrypt on Resource \"*\" without noting the Security Hub control violation",
      "Claim that rotation_period_in_days defaults to 365 in the provider (the provider has no default; 365 is the AWS default on enable)"
    ]
  }
}
```
