# Always-Do Patterns — provisioning-aws-organizations-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`), S3 backend with `use_lockfile`, management-account provider | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-provider) |
| 2 | Organization (`feature_set = "ALL"`, service principals, policy types) | [always-do-foundation](./always-do-foundation.md#2-organization) |
| 3 | Organizational units nested under `roots[0].id` | [always-do-foundation](./always-do-foundation.md#3-organizational-units) |
| 4 | Accounts (`parent_id`, `role_name` + `ignore_changes`, `prevent_destroy`) | [always-do-foundation](./always-do-foundation.md#4-accounts) |
| 5 | Deny-list SCP and attachment to the root | [always-do-policies](./always-do-policies.md#5-deny-list-scp-and-attachment) |
| 6 | Policy types and non-SCP policies | [always-do-policies](./always-do-policies.md#6-policy-types-and-non-scp-policies) |
| 7 | Delegated administrator and resource policy | [always-do-policies](./always-do-policies.md#7-delegated-administrator-and-resource-policy) |
| 8 | Policies-for-target data source and `terraform test` | [always-do-policies](./always-do-policies.md#8-policies-for-target-and-terraform-test) |
