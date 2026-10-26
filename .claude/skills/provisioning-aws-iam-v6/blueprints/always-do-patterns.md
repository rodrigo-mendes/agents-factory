# Always-Do Patterns — provisioning-aws-iam-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-14).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-roles-policies](./always-do-roles-policies.md#1-terraform-block-and-s3-backend) |
| 2 | Policy document with `jsonencode()` and `data.aws_iam_policy_document` | [always-do-roles-policies](./always-do-roles-policies.md#2-policy-document-patterns) |
| 3 | Inline policies with `aws_iam_role_policy` and `aws_iam_role_policies_exclusive` | [always-do-roles-policies](./always-do-roles-policies.md#3-inline-policies-with-exclusive-management) |
| 4 | Managed policy attachments with `aws_iam_role_policy_attachment` and `aws_iam_role_policy_attachments_exclusive` | [always-do-roles-policies](./always-do-roles-policies.md#4-managed-policy-attachments-with-exclusive-management) |
| 5 | `terraform test` with `mock_provider` and CI commands | [always-do-testing](./always-do-testing.md#5-terraform-test-and-ci) |
| 6 | GitHub Actions OIDC provider and trust role with scoped `sub` condition | [always-do-oidc-users](./always-do-oidc-users.md#6-github-actions-oidc-provider-and-trust-role) |
| 7 | IAM users and groups (least-privilege, IAM.2 compliant) | [always-do-oidc-users](./always-do-oidc-users.md#7-iam-users-and-groups) |
| 8 | Password policy with CIS-safe settings (IAM.15/16/17 compliant) | [always-do-oidc-users](./always-do-oidc-users.md#8-password-policy) |
