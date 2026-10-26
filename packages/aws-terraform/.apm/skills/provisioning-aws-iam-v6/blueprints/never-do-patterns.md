# Never-Do Patterns — provisioning-aws-iam-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-14), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| Setting `region =` on `aws_iam_*` resources (IAM is global) | [never-do-identity](./never-do-identity.md#1-setting-region-on-iam-resources) |
| Using `id@region` import IDs for IAM resources | [never-do-identity](./never-do-identity.md#2-using-idregion-import-ids-for-iam-resources) |
| Using deprecated `data.aws_region.current.name` in ARNs | [never-do-identity](./never-do-identity.md#3-using-deprecated-dataaws_regioncurrentname) |
| Using `inline_policy` or `managed_policy_arns` on `aws_iam_role` (deprecated) | [never-do-roles-policies](./never-do-roles-policies.md#1-using-deprecated-inline_policy-or-managed_policy_arns) |
| Mixing `aws_iam_policy_attachment` with `aws_iam_role_policy_attachment` on the same role | [never-do-roles-policies](./never-do-roles-policies.md#2-mixing-aws_iam_policy_attachment-with-role-scoped-attachments) |
| Using `aws_iam_policy_attachment` for policies shared across multiple Terraform-managed resources | [never-do-roles-policies](./never-do-roles-policies.md#3-aws_iam_policy_attachment-exclusive-blast-radius) |
| Admin wildcard `Action *` / `Resource *` in customer managed policies (IAM.1) | [never-do-roles-policies](./never-do-roles-policies.md#4-admin-wildcard-in-customer-managed-policy) |
| Omitting or wildcarding the `sub` condition in a GitHub OIDC trust policy | [never-do-identity](./never-do-identity.md#4-missing-or-wildcard-sub-in-github-oidc-trust-policy) |
| Using `aws_iam_access_key` for human users or workloads that can use roles | [never-do-identity](./never-do-identity.md#5-long-term-access-keys-for-users-or-workloads) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-provider-migration](./never-do-provider-migration.md#5-s3-backend-with-dynamodb_table) |
| Pinning withdrawn provider 6.57.0 | [never-do-provider-migration](./never-do-provider-migration.md#6-pinning-version-6570) |
