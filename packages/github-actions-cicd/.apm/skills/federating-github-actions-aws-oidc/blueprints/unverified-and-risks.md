# Unverified and risks register

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Tags are plain parentheses: (unverified) and (medium confidence).

## Version-lifetime risk

As of 2026-10-30.

- `configure-aws-credentials` v6.3.0 was released on 2026-09-15; v6.0.0 (2026-02-04) to v6.3.0 added profiles, session tags, `allowed-account-ids` enforcement and `translate-env-variables`. Re-resolve the SHA with `git ls-remote` before bumping. Source: https://github.com/aws-actions/configure-aws-credentials/releases
- Repositories created after 2026-07-15 emit the immutable `sub`; trust policies written for the name form stop matching. Source: https://docs.github.com/en/actions/reference/security/oidc
- v6 needs runner v2.327.1 or later (node24); older self-hosted runners fail. Source: https://github.com/aws-actions/configure-aws-credentials/releases?page=2
- GitHub and AWS pages conflict on `job_workflow_ref` as a direct condition key; re-read the AWS condition-key reference before relying on it. Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_secure-by-default.html
- Environment features on private repositories depend on the plan and have changed over time; re-read the environments pages before promising a gate. Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

## Unverified (9)

| ID | Claim | Impact | Workaround |
|---|---|---|---|
| U1 | Exact immutable `sub` string for environment jobs | trust may not match on repos created after 2026-07-15 | decode a test token in a throwaway job first |
| U2 | How deployment branch policies evaluate `pull_request` events for a `<env>-pr` environment | PR read role may not start | use the `:pull_request` sub |
| U3 | Plan availability of the OIDC subject-template API on Free private repositories | custom `sub` may be unavailable | separate repositories or accounts per environment |
| U4 | Whether the action masks the access key, secret and session token with `setSecret` | possible log exposure | keep `output-credentials` false; never echo `AWS_*` |
| U5 | Exact action regex for `role-session-name`; exact STS text for an audience mismatch | troubleshooting wording only | stay within `[\w+=,.@-]*`, 2 to 64 characters |
| U6 | A local composite action needs a prior checkout of the repository | login step cannot find the action | check out first; confirm on the first run |
| U7 | GitHub-hosted runners already meet runner v2.327.1 | v6 fails on a stale runner | none known; self-hosted runners must be checked |
| U8 | `ubuntu-latest` ships the AWS CLI | `get-caller-identity` step fails | confirm on the first run or install the CLI |
| U9 | An official offline emulator for `AssumeRoleWithWebIdentity` | trust is not testable offline | test the trust JSON statically; first live login in a non-production account |

## Irresolvable (0)

None. The `job_workflow_ref` conflict is kept as medium confidence M1 because both vendors document the `sub` template route.

## Medium confidence (4)

| ID | Claim | Why medium | Check |
|---|---|---|---|
| M1 | AWS evaluates `token.actions.githubusercontent.com:job_workflow_ref` directly | the identity-provider controls page lists it; the condition-key reference does not | use the `sub` template route; re-read both pages |
| M2 | The first OIDC hop carries no session tags | inferred from the README and GitHub claim list | read session tags in CloudTrail |
| M3 | A fork PR job cannot mint an OIDC token | inferred from "write permissions to read only" | run a fork PR in a test repository |
| M4 | A deployment branch policy blocks the job before the token is minted | inferred from the environments and AWS pages | trigger from a non-allowed branch |

## Coverage limits (5)

| ID | Limit |
|---|---|
| L1 | The workflow-syntax page was read only for characters 0-100000 of 235839 |
| L2 | The AWS condition-keys page was read only in its OIDC federation section |
| L3 | docs.github.com and docs.aws.amazon.com pages carry no version or date; the read date 2026-10-30 is recorded |
| L4 | The user's GitHub plan and repository creation date are unknown to this skill; it asks |
| L5 | GitHub Enterprise Server is out of scope (no immutable `sub`) |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | trust-policies-by-plan.md immutable table, environment row; evaluation-scenarios.md scenario 2 | U1 |
| (unverified) | SKILL.md Ask First (PR read role form); trust-policies-by-plan.md Pro and Team section | U2 |
| (unverified) | SKILL.md Ask First (sub template); trust-policies-by-plan.md customizing section; evaluation-scenarios.md scenario 5 | U3 |
| (unverified) | always-do-patterns.md keep credentials inside the step | U4 |
| (unverified) | always-do-patterns.md session name; login-composite-action.md troubleshooting | U5 |
| (unverified) | login-composite-action.md composite notes | U6 |
| (unverified) | always-do-patterns.md runner minimum | U7 |
| (unverified) | login-composite-action.md reusable login check | U8 |
| (unverified) | SKILL.md Verification Loop | U9 |
| (medium confidence) | SKILL.md Ask First (reusable-workflow restriction); trust-policies-by-plan.md reusable section | M1 |
| (medium confidence) | always-do-patterns.md runner minimum (session tags) | M2 |
| (medium confidence) | never-do-patterns.md N4 | M3 |
| (medium confidence) | trust-policies-by-plan.md Pro and Team section | M4 |

## Source Bibliography

All fetched 2026-10-30.

**docs.github.com**
- https://docs.github.com/en/actions/reference/security/oidc
- https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws
- https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (partly read)
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/rest/actions/oidc

**Action repository**
- https://github.com/aws-actions/configure-aws-credentials/releases (pages 1 and 2)
- https://github.com/aws-actions/configure-aws-credentials/blob/v6.3.0/README.md
- https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml
- https://github.com/actions/checkout/releases
- SHA verification: `git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>`

**AWS**
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_secure-by-default.html
- https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_iam-condition-keys.html (OIDC section)
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html
- https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html
- https://docs.aws.amazon.com/cli/latest/reference/iam/create-open-id-connect-provider.html

**Community**: none used.
