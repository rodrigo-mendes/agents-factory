# Plan variants: Pro/Team default and Free

Back to [SKILL.md](../SKILL.md). GitHub.com docs as of 2026-10-30. The executor asks the GitHub plan before generating any deploy job.

## Feature availability on private repositories

| Feature | Free | Pro / Team |
|---|---|---|
| Create environments | no ("Users with GitHub Free plans can only configure environments for public repositories") | yes (Team for organizations, Pro for user accounts) |
| Environment secrets and variables | no | yes |
| Deployment branch and tag policy | no (no environments) | yes |
| Protected branches, required PR reviewers, code owners | not listed | yes |
| Required reviewers on environments, wait timers, custom protection rules | no | no (public repositories or Enterprise) |

Sources: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments ; https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments ; https://docs.github.com/en/get-started/learning-about-github/githubs-plans

## Default: Pro/Team private repository

- Environments `<env>` with secrets and variables, deployment branch policy `main`; PR jobs use `<env>-pr` with read-only credentials.
- Protected `main` with required pull request reviewers: the approval is the PR review before merge.
- Cloud roles trust the `environment:<env>` claim of the OIDC `sub`; the exact string for an environment in the immutable format is (unverified). Repositories created after 2026-07-15 use the immutable format `repo:OWNER@OWNER-ID/REPO@REPO-ID:...`, shown in the docs with `ref:refs/heads/main`; older repositories keep `repo:OWNER/REPO:...` unless they opt in (https://docs.github.com/en/actions/reference/security/oidc).
- PR jobs use `<env>-pr` with the `AWS_PR_ROLE_ARN` variable; deploy jobs use `<env>` with `AWS_DEPLOY_ROLE_ARN`; both are read inside the called job that declares the environment.
- Required reviewers, wait timers and artifact attestations are the upgrade path (public repository or Enterprise).

```yaml
# caller: the environment name travels as an input
deploy:
  needs: build
  uses: ./.github/workflows/_deploy-s3-cf.yml
  permissions:
    contents: read
    id-token: write
  with:
    environment: prod
    artifact-name: ${{ needs.build.outputs.artifact-name }}
    artifact-digest: ${{ needs.build.outputs.artifact-digest }}
```

## Free private repository (weaker, stated explicitly)

This variant is weaker and is never chosen silently. Tell the user the accepted risks.

- No environments and no protected branches: a human gate before deploy does not exist in GitHub; the only controls are the branch the workflow runs on and the cloud trust policy.
- Cloud roles trust `ref:refs/heads/main` (subject format by repository creation date as above); keyless OIDC where the cloud supports it, so no static deploy secret exists.
- Separate dev and prod by cloud account or role, or by repository.
- Where a static secret is unavoidable (container registry or Vercel token), store it as a least-privilege repository secret and warn that every workflow on any branch with access can read it.
- Do not set an `environment` input in the deploy block for this variant; whether an empty `environment:` expression is accepted was not confirmed (unverified), so inline the deploy job in the caller without the key.
- Run PR jobs without any deploy credential; only the `main` push workflow logs in.

```yaml
# cd-web.yml (Free): inline job, no environment key; the cloud role trusts refs/heads/main
concurrency:
  group: deploy-web
  cancel-in-progress: false
jobs:
  deploy:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    timeout-minutes: 20
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: ./.github/actions/cloud/login-aws
        with:
          role-arn: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          region: eu-west-1
```

Steps after the login are the deploy steps of the owner skill (`building-nextjs-github-actions-v16-4`, deploy to S3 and CloudFront). Free has no environment variables, so the role ARN comes from a repository secret or an inline value.

## Ask

"Which GitHub plan owns this private repository: Pro/Team or Free?" On Free, also ask whether the accepted risks are acceptable or whether moving to Pro/Team is possible.
