# Evaluation Report: provisioning-aws-iam-v6 (Round 1)

Method: no sub-agents. For each scenario I wrote the response the skill-equipped assistant would give, using only SKILL.md and its linked blueprints. I then judged that response against the criteria.
Files read: SKILL.md, always-do-roles-policies.md, always-do-oidc-users.md, never-do-roles-policies.md, never-do-identity.md, evaluation-scenarios.md.
I did not read always-do-testing.md, always-do-patterns.md, never-do-patterns.md, never-do-provider-migration.md or unverified-and-risks.md. None of the four scenarios depends on them.

## Summary

| Scenario | must_pass | must_not | Verdict |
|---|---|---|---|
| 1 Canonical role + exclusive policies | 10/10 | 7/7 OK | PASS |
| 2 GitHub OIDC trust role | 7/7 | 4/4 OK | PASS |
| 3 Misuse rejection | 6/6 | 4/4 OK | PASS |
| 4 Anti-pattern trap | 5/5 | 4/4 OK | PASS |

Overall: 28/28 must_pass (100%), 19/19 must_not OK. All four scenarios PASS.

## Scenario 1 - Canonical role with exclusive management

Simulated response: the HCL follows always-do-roles-policies §1, §3 and §4.
- `terraform {}` block: `required_version = "~> 1.16"`, aws `~> 6.69`, S3 backend with `use_lockfile = true` and `encrypt = true`. There is no `dynamodb_table`.
- `aws_iam_role.app` has an EC2 assume-role policy and no `inline_policy` or `managed_policy_arns`.
- `aws_iam_role_policy.app_s3` has `Action = ["s3:GetObject"]` on `arn:aws:s3:::my-bucket/*`.
- `aws_iam_policy.s3_read` is attached with `aws_iam_role_policy_attachment.app_managed`.
- `aws_iam_role_policies_exclusive` and `aws_iam_role_policy_attachments_exclusive` list every co-managed name or ARN.
- Neither IAM resource sets `region`. An `aws_iam_instance_profile` is added for EC2.

must_pass:
1. PASS. Version constraints: `required_version = "~> 1.16"`, `version = "~> 6.69"`.
2. PASS. `use_lockfile = true # S3-native lock; dynamodb_table is deprecated`.
3. PASS. Role block comment: "Do NOT use inline_policy or managed_policy_arns".
4. PASS. `aws_iam_role_policy "app_s3"`.
5. PASS. `aws_iam_role_policy_attachment "app_managed"`.
6. PASS. `aws_iam_role_policies_exclusive "app"`.
7. PASS. `aws_iam_role_policy_attachments_exclusive "app"`.
8. PASS. Actions are scoped (`s3:GetObject`, `s3:ListBucket`) and resources are specific buckets.
9. PASS. No `region =` on any `aws_iam_*` resource. The backend `region` is a backend argument, not an IAM resource.
10. PASS. `.name` is not used. No region interpolation is needed, and the skill gives `.region` if it were.

must_not: all seven OK. None of the forbidden constructs appear.

Ambiguity: must_pass #9 and must_not #4 say "region =" on `aws_iam_*` resources. The S3 backend block also contains `region = "eu-west-1"`, which is required. A strict string-match judge could misflag it. Suggest rewording to "on any aws_iam_* resource (backend region is allowed)".

## Scenario 2 - GitHub Actions OIDC trust role

Simulated response: the HCL follows always-do-oidc-users §6.
- `aws_iam_openid_connect_provider.github` has `url = "https://token.actions.githubusercontent.com"` and `client_id_list = ["sts.amazonaws.com"]`.
- `thumbprint_list` is omitted. The response says it is optional for GitHub because AWS uses its own root CA library.
- The trust policy uses a Federated principal with the provider ARN and action `sts:AssumeRoleWithWebIdentity`.
- Conditions are `StringEquals` on `:aud` = `sts.amazonaws.com` and on `:sub` = `repo:MyOrg/MyRepo:ref:refs/heads/main`.
- The response notes that IAM rejects a missing or wildcard-only `sub`.

must_pass:
1. PASS. Provider URL and client_id_list match.
2. PASS. "thumbprint_list is optional for GitHub - AWS uses its own trusted root CA library".
3. PASS. `type = "Federated"`, `identifiers = [aws_iam_openid_connect_provider.github.arn]`.
4. PASS. `actions = ["sts:AssumeRoleWithWebIdentity"]`.
5. PASS. `StringEquals ... :aud = ["sts.amazonaws.com"]`.
6. PASS. `values = ["repo:MyOrg/MyRepo:ref:refs/heads/main"]`.
7. PASS. The `sub` condition uses `StringEquals`, with no wildcard.

must_not: all four OK.

## Scenario 3 - Misuse rejection

Simulated response: "No. This combination is wrong on two counts."
- `inline_policy` has been deprecated since 5.68.0. That is not new in 6.x, and it is not removed in 6.x either. It is incompatible with `aws_iam_role_policy` and the separate attachment resources, and causes "resource cycling and/or errors".
- Mixing `aws_iam_policy_attachment` with `aws_iam_role_policy_attachment` on the same role causes a permanent diff.
- `aws_iam_policy_attachment` creates account-wide exclusive attachments. It revokes the policy from every holder not listed in that resource.
- Use `aws_iam_role_policy` + `aws_iam_role_policies_exclusive` for inline policies.
- Use `aws_iam_role_policy_attachment` + `aws_iam_role_policy_attachments_exclusive` for managed policies.

Sources: never-do-roles-policies §1-3 and the SKILL.md Never Do table.

must_pass: 6/6 PASS. Each criterion is stated almost verbatim in the skill, for example "deprecated since 5.68.0 (not new in 6.x, not removed)", "causes a permanent diff", and "account-wide exclusive attachments".

must_not: all four OK. The response does not say it was deprecated in 6.x or removed in 6.x. It does not call `aws_iam_policy_document` the only option. It does not permit mixing.

Ambiguity: the must_not about `aws_iam_policy_document` is irrelevant to this query, since policy JSON is not asked about. It passes trivially. Consider dropping it or adding a policy-JSON element to the query.

## Scenario 4 - Anti-pattern trap

Simulated response: "Not correct. Three problems, plus one related rule."
- `region = "us-east-1"` on `aws_iam_role` is an unsupported argument. IAM is global and non-region-aware (enhanced-region-support guide).
- `data.aws_region.current.name` was deprecated in 6.0. Use `data.aws_region.current.region` (version-6-upgrade guide).
- S3 backend `dynamodb_table` is deprecated and will be removed. Use `use_lockfile = true`.
- Related rule: do not use `id@region` import IDs for IAM resources. Import by name or ARN, for example `terraform import aws_iam_role.good good-role`.

must_pass:
1. PASS. "Setting `region` ... triggers an unsupported-argument error."
2. PASS. `.name` is deprecated in 6.0, with `.region` as the replacement.
3. PASS. `dynamodb_table` is deprecated, with `use_lockfile = true` as the replacement.
4. PASS. never-do-identity §2 and the SKILL.md Never Do table cover `@region` import IDs.
5. PASS. SKILL.md and the blueprints cite both guides as sources for each rule.

must_not: all four OK.

Ambiguity: must_pass #4 depends on the model proactively raising import IDs. The query does not mention imports. The skill gives it prominence in the Never Do table, so it should surface. It is the most fragile item in the suite.

## Failures and fixes needed

No failures. Optional hardening, all low priority:
1. `blueprints/evaluation-scenarios.md`, Scenarios 1 and 3: apply the two ambiguity rewordings above. For Scenario 4 criterion #4, either mention imports in the query or accept it as an "extra rule" check.
2. SKILL.md, Always Do list: add the `id@region` import rule as a bullet. It is currently only in the Never Do table. This would make Scenario 4 criterion #4 more robust.

Caveat: this is a self-simulated evaluation without a sub-agent run. The verdicts reflect what the skill content supports. They do not show how a separate model would behave.
