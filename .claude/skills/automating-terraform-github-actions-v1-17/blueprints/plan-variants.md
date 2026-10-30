# Plan variants: Pro/Team default, Free, upgrade path

Back to [SKILL.md](../SKILL.md). GitHub.com docs as of 2026-10-30. Ask the GitHub plan before generating the apply path; the shared feature table lives in `composing-github-actions-pipelines` (plan variants).

## Default: Pro/Team private repository

- Protected `main` with required pull request reviewers: the approval is the PR review of the rendered preview plan before the merge (Pro and Team feature; https://docs.github.com/en/get-started/learning-about-github/githubs-plans).
- Environments `<env>` (deploy role, merge-time plan and apply in the same run, plan takes the state lock) and `<env>-pr` (PR plan, read-only role, `-lock=false`). `<env>` carries the deployment branch policy `main`; `<env>-pr` must not be restricted to `main`, because PR jobs run on a pull request ref (whether a PR job passes an `<env>-pr` branch policy is (unverified), see register U11).
- Cloud roles trust `environment:<env>` and `environment:<env>-pr`; AWS role ARNs are `AWS_DEPLOY_ROLE_ARN` (in `<env>`) and `AWS_PR_ROLE_ARN` (in `<env>-pr`), read inside the called job.
- No required reviewers on the environment: they do not work on private Free, Pro or Team repositories (https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

## Free private repository (weaker, stated explicitly)

This variant is weaker and is never chosen silently. Tell the user the accepted risks.

- No environments and no protected branches: nothing in GitHub stops a deploy after a bad merge or a push; the controls are the branch the workflow runs on and the cloud trust policy.
- Deploy role trusts `ref:refs/heads/main`; PR plan role is read-only and trusts the `pull_request` subject; keyless OIDC, so no static deploy secret exists (subject formats: `federating-github-actions-aws-oidc`).
- Separate dev and prod by cloud account or role, or by repository.
- Use `_tf-plan.yml` and `_tf-apply.yml` copies without the `environment:` key; whether an empty `environment:` expression is accepted was not confirmed (unverified, see register U11).
- Run the apply job only on `github.ref == 'refs/heads/main'`; PR jobs never hold the deploy role.
- Mitigate the missing review gate by reading the preview plan before every merge by team convention.

```yaml
# _tf-apply-free.yml job (no environment key; the role trusts refs/heads/main)
apply:
  if: github.ref == 'refs/heads/main'
  runs-on: ubuntu-latest
  timeout-minutes: 60
  permissions:
    contents: read
    id-token: write
```

## Upgrade path

Required reviewers, wait timers and artifact attestations on the `<env>` environment need a public repository or GitHub Enterprise. With them, the apply job waits for approval on the environment and its secrets stay locked until then; keep the PR review as well.

## Ask

"Which GitHub plan owns this private repository: Pro/Team or Free?" On Free, also ask whether the accepted risks are acceptable or whether moving to Pro/Team is possible.
