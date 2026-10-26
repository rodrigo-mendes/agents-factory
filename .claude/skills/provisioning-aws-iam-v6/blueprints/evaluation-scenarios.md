# Evaluation Scenarios — provisioning-aws-iam-v6

Four scenarios required for a hybrid knowledge skill (canonical, edge, misuse rejection, anti-pattern trap).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: IAM Role with Inline and Managed Policies

```json
{
  "skills": ["provisioning-aws-iam-v6"],
  "query": "Generate Terraform for an IAM role for an EC2 instance that needs to read from an S3 bucket. Include the role, an inline policy for S3 read, a managed policy attachment, and exclusive management of both. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69 (or >=6.0)",
      "Uses use_lockfile = true in the S3 backend; does not include dynamodb_table",
      "Does NOT use inline_policy or managed_policy_arns on aws_iam_role",
      "Uses aws_iam_role_policy for inline policies (not inline_policy on the role)",
      "Uses aws_iam_role_policy_attachment for managed policy attachments (not aws_iam_policy_attachment)",
      "Includes aws_iam_role_policies_exclusive to enforce exclusive inline policy management",
      "Includes aws_iam_role_policy_attachments_exclusive to enforce exclusive managed policy management",
      "Policy does not use Action * or Resource * (least-privilege, IAM.1 compliant)",
      "Does not set region = on aws_iam_role or any aws_iam_* resource (the S3 backend block may legitimately set region)",
      "Does not use data.aws_region.current.name (uses .region if region is needed)"
    ],
    "must_not": [
      "Use inline_policy block on aws_iam_role",
      "Use managed_policy_arns on aws_iam_role",
      "Use aws_iam_policy_attachment",
      "Set region = on any aws_iam_* resource (a region in the S3 backend block is allowed)",
      "Use Action * on Resource * in any customer managed policy",
      "Use dynamodb_table in the S3 backend",
      "Use data.aws_region.current.name"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: GitHub Actions OIDC Trust Role

```json
{
  "skills": ["provisioning-aws-iam-v6"],
  "query": "Set up a GitHub Actions OIDC provider and an IAM role that a GitHub Actions workflow can assume. The role should only be assumable from the main branch of org MyOrg and repo MyRepo. Use hashicorp/aws 6.x.",
  "success_criteria": {
    "must_pass": [
      "Creates aws_iam_openid_connect_provider with url = \"https://token.actions.githubusercontent.com\" and client_id_list = [\"sts.amazonaws.com\"]",
      "Does NOT hard-code thumbprint_list as required — states that AWS uses its own CA library for GitHub and thumbprint_list is optional",
      "Trust policy principal is Federated with the OIDC provider ARN",
      "Trust policy action is sts:AssumeRoleWithWebIdentity",
      "Includes a StringEquals aud condition for sts.amazonaws.com",
      "Includes a non-wildcard sub condition scoped to MyOrg/MyRepo and main branch",
      "Does not use StringLike with a wildcard-only sub value"
    ],
    "must_not": [
      "State that thumbprint_list is required for GitHub OIDC",
      "Omit the sub condition from the trust policy",
      "Use a wildcard-only sub condition (IAM would reject this)",
      "Set region = on aws_iam_openid_connect_provider or aws_iam_role"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Using `inline_policy` and `aws_iam_policy_attachment`

```json
{
  "skills": ["provisioning-aws-iam-v6"],
  "query": "Is it correct to use inline_policy on aws_iam_role and aws_iam_policy_attachment together with aws_iam_role_policy_attachment on the same role in hashicorp/aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Explicitly states that inline_policy on aws_iam_role is deprecated (since 5.68.0, not new in 6.x)",
      "States that inline_policy is incompatible with aws_iam_role_policy and causes resource cycling or errors",
      "Explicitly states that mixing aws_iam_policy_attachment with aws_iam_role_policy_attachment on the same role causes a permanent diff",
      "States that aws_iam_policy_attachment creates account-wide exclusive attachments and revokes the policy from any holder not listed",
      "Recommends aws_iam_role_policy + aws_iam_role_policies_exclusive for inline policies",
      "Recommends aws_iam_role_policy_attachment + aws_iam_role_policy_attachments_exclusive for managed policies"
    ],
    "must_not": [
      "State that inline_policy was deprecated in 6.x (it was deprecated in 5.68.0)",
      "State that inline_policy was removed in 6.x (it is deprecated, not removed)",
      "State that aws_iam_policy_document is the only or recommended way to build policy JSON (both it and jsonencode are equal options)",
      "Silently permit mixing aws_iam_policy_attachment with aws_iam_role_policy_attachment"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Region on IAM and Deprecated `.name`

```json
{
  "skills": ["provisioning-aws-iam-v6"],
  "query": "Review this Terraform snippet: aws_iam_role with region = \"us-east-1\", data.aws_region.current.name used in an ARN, and S3 backend with dynamodb_table. Is this correct for hashicorp/aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects region = \"us-east-1\" on aws_iam_role as unsupported — IAM is a global non-region-aware service",
      "Rejects data.aws_region.current.name as deprecated in 6.0; provides data.aws_region.current.region as the replacement",
      "Rejects S3 backend dynamodb_table as deprecated; provides use_lockfile = true as the replacement",
      "Notes that @region import IDs must not be used for IAM resources",
      "Cites the enhanced-region-support guide or version-6-upgrade guide as authority"
    ],
    "must_not": [
      "Accept region = on aws_iam_role as valid",
      "Accept data.aws_region.current.name as valid for 6.x",
      "Accept dynamodb_table without noting its deprecated status",
      "Suggest using id@region import syntax for aws_iam_role"
    ]
  }
}
```
