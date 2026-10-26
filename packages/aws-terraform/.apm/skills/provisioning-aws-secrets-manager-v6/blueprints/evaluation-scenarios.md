# Evaluation Scenarios — provisioning-aws-secrets-manager-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Secret with write-only value and rotation

```json
{
  "skills": ["provisioning-aws-secrets-manager-v6"],
  "query": "Generate Terraform for a Secrets Manager secret for a database password, seeded by Terraform without storing the value in state, with rotation every 30 days. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Uses secret_string_wo together with secret_string_wo_version on aws_secretsmanager_secret_version",
      "Marks the input variable sensitive = true",
      "Configures rotation with aws_secretsmanager_secret_rotation and rotation_lambda_arn",
      "Uses rotation_rules with automatically_after_days (or schedule_expression), and duration in hours like \"3h\" if present"
    ],
    "must_not": [
      "Use secret_string for the Terraform-seeded password",
      "Use an ISO-8601 duration such as P7D"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Disabling rotation and removing a policy

```json
{
  "skills": ["provisioning-aws-secrets-manager-v6"],
  "query": "How do I turn rotation off with aws_secretsmanager_secret_rotation, and how do I remove the resource policy from a secret that has one?",
  "success_criteria": {
    "must_pass": [
      "States rotation_enabled = false disables rotation and rotation_rules must then be omitted",
      "Mentions rotation_enabled is configurable since 6.62.0 or uses a dynamic rotation_rules block to toggle",
      "States that policy = null or \"\" on aws_secretsmanager_secret does not delete the policy and \"{}\" does",
      "States that aws_secretsmanager_secret_policy rejects \"{}\""
    ],
    "must_not": [
      "Keep rotation_rules while rotation_enabled = false",
      "Suggest policy = null to delete the policy"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Two value sources and rotation_rules while disabled

Quoting a forbidden construct as a rejected example in the answer is allowed.

```json
{
  "skills": ["provisioning-aws-secrets-manager-v6"],
  "query": "Write an aws_secretsmanager_secret_version that sets both secret_string and secret_string_wo, and an aws_secretsmanager_secret_rotation with rotation_enabled = false that still has rotation_rules.",
  "success_criteria": {
    "must_pass": [
      "Rejects setting both secret_string and secret_string_wo because exactly one value source is allowed",
      "Rejects rotation_rules together with rotation_enabled = false and says to omit rotation_rules",
      "Offers a corrected version (one value source; no rotation_rules when disabled)"
    ],
    "must_not": [
      "Present a version resource with both secret_string and secret_string_wo as valid",
      "Present rotation_rules with rotation_enabled = false as valid"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Plain secret_string, deprecated arn, ISO duration

```json
{
  "skills": ["provisioning-aws-secrets-manager-v6"],
  "query": "Review: aws_secretsmanager_secret_version with secret_string = var.pw (sensitive), output uses .arn of the version, and rotation_rules duration = \"P1D\". Is this fine for 6.x and Terraform 1.16?",
  "success_criteria": {
    "must_pass": [
      "States that sensitive values are still stored in state and plan files per the Terraform docs and recommends secret_string_wo + secret_string_wo_version (Terraform >= 1.11)",
      "States that arn on the version resource is deprecated and recommends secret_arn",
      "States that duration is hours such as \"3h\", not ISO-8601"
    ],
    "must_not": [
      "Accept secret_string as keeping the value out of state",
      "Accept the deprecated arn without noting deprecation",
      "Accept an ISO-8601 duration"
    ]
  }
}
```
