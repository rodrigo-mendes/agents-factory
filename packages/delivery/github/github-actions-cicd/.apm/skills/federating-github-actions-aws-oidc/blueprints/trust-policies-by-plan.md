# Trust policies by plan

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Ask the plan first (Free, Pro or Team, private or public) before writing any trust policy.

## Contents

- Plan model
- Trust table
- Legacy and immutable sub formats
- Job shape decides the sub
- Pro and Team trust policies
- Free private trust policies
- Customizing the sub template
- Reusable workflows and job_workflow_ref

## Plan model

Default = Pro/Team private repositories (family decision): environments with variables and a deployment branch policy limited to `main`, protected `main` with required PR reviewers, so the approval is the PR review before merge; the deploy role trusts `environment:<env>`. Free private is weaker and stated as such: no environments, no protected branches, roles trust the `main` ref. Required reviewers, wait timers and custom protection rules are public-repository or Enterprise features (upgrade path only).
Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

## Trust table

| Role | Pro/Team private, `sub` | Free private, `sub` |
|---|---|---|
| `gha-<app>-<env>-deploy` | `repo:ORG/REPO:environment:<env>` | `repo:ORG/REPO:ref:refs/heads/main` |
| `gha-<app>-<env>-pr-read` | `repo:ORG/REPO:environment:<env>-pr` | `repo:ORG/REPO:pull_request` |
| `gha-<app>-<env>-publish` (push-only registry role, read as `vars.ECR_PUSH_ROLE_ARN` by `publishing-container-images-github-actions`) | `repo:ORG/REPO:environment:<env>-publish` | `repo:ORG/REPO:ref:refs/heads/main` (same as deploy: Free cannot separate them) |

Free caveat (accepted risk, never silent): every job running on `main` carries the same `sub`, so dev and prod deploy roles cannot be separated by `sub` alone. Separate them by AWS account or by repository, and keep the PR role read-only. Where a static secret is unavoidable elsewhere in the pipeline, use a least-privilege repository secret with a warning.
Source: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments

## Legacy and immutable sub formats

| Job shape | Legacy `sub` (older repositories) | Immutable `sub` (created after 2026-07-15) |
|---|---|---|
| push or dispatch on branch | `repo:ORG/REPO:ref:refs/heads/main` | `repo:ORG@ORG_ID/REPO@REPO_ID:ref:refs/heads/main` |
| `pull_request`, no environment | `repo:ORG/REPO:pull_request` | `repo:ORG@ORG_ID/REPO@REPO_ID:pull_request` |
| environment job | `repo:ORG/REPO:environment:prod` | `repo:ORG@ORG_ID/REPO@REPO_ID:environment:prod` (unverified) |

The published immutable example is `repo:octo-org@123456/octo-repo@456789:ref:refs/heads/main`; older repositories keep the legacy form unless they opt in. A name-only policy on an immutable repository fails with "Not authorized to perform sts:AssumeRoleWithWebIdentity". Read the real `sub` from a decoded test token in a throwaway job before writing the policy. The immutable form is not available on GitHub Enterprise Server. Colons inside metadata values are replaced with `%3A`.
Source: https://docs.github.com/en/actions/reference/security/oidc

## Job shape decides the sub

| Job shape | Resulting `sub` (legacy) |
|---|---|
| references `environment: prod`, any event | `repo:ORG/REPO:environment:prod` |
| `pull_request`, no environment | `repo:ORG/REPO:pull_request` |
| branch, no environment | `repo:ORG/REPO:ref:refs/heads/main` |
| tag, no environment | `repo:ORG/REPO:ref:refs/tags/v1.2.3` |

A PR job that references `environment: prod` gets the prod `sub`, never `:pull_request`; that is why it is a Never Do.
Source: https://docs.github.com/en/actions/reference/security/oidc

## Pro and Team trust policies

Deploy role, legacy form (immutable: replace the value with the immutable string from the table):

```json
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
    "token.actions.githubusercontent.com:sub": "repo:<ORG>/<REPO>:environment:prod"
  }
}
```

PR read role: same shape with `"repo:<ORG>/<REPO>:environment:prod-pr"`. The `prod` environment gets a deployment branch policy of `main` only; that this blocks the job before a token is minted is (medium confidence), inferred from the environment and AWS pages. How a branch policy is evaluated for `pull_request` events on `prod-pr` is (unverified); use the `:pull_request` form when in doubt.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html

## Free private trust policies

```json
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
    "token.actions.githubusercontent.com:sub": "repo:<ORG>/<REPO>:ref:refs/heads/main"
  }
}
```

PR read role: replace the value with `"repo:<ORG>/<REPO>:pull_request"`. Any same-repository PR can then assume the read role, so keep it read-only. Use `StringLike` with `repo:ORG/REPO:*` only on read-only roles, never on a deploy role.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html

## Customizing the sub template

AWS reads only `aud`, `sub` and `amr` for this provider, so extra claims must go into `sub`.

```bash
# Representative: adapt to your environment (scope: repo)
gh api --method PUT repos/<ORG>/<REPO>/actions/oidc/customization/sub --input - <<'EOF'
{"use_default": false, "include_claim_keys": ["repo", "context", "job_workflow_ref"]}
EOF
# Org level: PUT orgs/<ORG>/actions/oidc/customization/sub (scope write:org); {"use_default": true} resets a repo
```

Update every trust policy first: "Create the matching condition in your cloud provider before customizing, or tokens may be rejected". An org template applies to a repo only when it opts in with `use_default: false`. Plan availability on Free private repositories is (unverified).
Source: https://docs.github.com/en/rest/actions/oidc

## Reusable workflows and job_workflow_ref

In a reusable workflow the standard claims describe the caller; `job_workflow_ref` names the called file. GitHub says custom claims are available only for some providers and that AWS has none, so the documented route is a `sub` template that includes `job_workflow_ref`. The AWS identity-provider controls page lists `job_workflow_ref` as an accepted claim, while its condition-key reference lists only `amr`, `aud`, `email`, `oaud` and `sub`; whether AWS evaluates the key directly is (medium confidence). Callers outside the org or enterprise must set `id-token: write` explicitly.
Source: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows
