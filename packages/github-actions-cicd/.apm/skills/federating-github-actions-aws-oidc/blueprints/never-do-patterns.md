# Never-do patterns with examples

Back to [SKILL.md](../SKILL.md). Each pattern states the alternative. configure-aws-credentials v6.3.0; research date 2026-10-30.

## Contents

- N1 Wildcard sub on a deploy role
- N2 PR job with a deployable environment
- N3 Stored access keys
- N4 pull_request_target for cloud login
- N5 Workflow-level id-token
- N6 Chained role beyond one hour
- N7 ForAllValues in an Allow statement
- N8 Action SHA copied from a doc example

## N1 Wildcard sub on a deploy role

GitHub's issuer is shared; without a scoped `sub`, "GitHub Actions from organizations or repositories outside of your control are able to assume roles". With `repo:ORG/REPO:*` any branch or PR job in the repo can deploy. IAM rejects a value that is only a wildcard.

```json
// ❌ Wrong
"StringLike": { "token.actions.githubusercontent.com:sub": "repo:my-org/*" }
// ✅ Correct
"StringEquals": {
  "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
  "token.actions.githubusercontent.com:sub": "repo:my-org/orders:environment:prod"
}
```

A wildcard is acceptable only on a read-only role, and then only per repository.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html

## N2 PR job with a deployable environment

A job that references `environment: prod` gets `sub` `...:environment:prod` and can assume the deploy role; the `:pull_request` sub exists only when the job does not reference an environment. Branch code runs during plan and build (family decision).

```yaml
# ❌ Wrong: ci-orders.yml, on: pull_request
jobs:
  plan:
    environment: prod
    permissions: { id-token: write, contents: read }
```

```yaml
# ✅ Correct: ci-orders.yml, on: pull_request
jobs:
  plan:
    environment: <env>-pr             # e.g. prod-pr; Pro/Team; omit on Free, sub becomes :pull_request
    permissions: { id-token: write, contents: read }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: ./.github/actions/cloud/login-aws
        with:
          role-arn: ${{ vars.AWS_PR_ROLE_ARN }}   # variable of <env>-pr, read in this job
          region: ${{ vars.AWS_REGION }}
```

Source: https://docs.github.com/en/actions/reference/security/oidc

## N3 Stored access keys

OIDC removes the stored secret; the README recommends temporary credentials. A leaked key stays valid until rotated and works outside GitHub.

```yaml
# ❌ Wrong
with:
  aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
  aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
# ✅ Correct (job has permissions: id-token: write)
with:
  role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
  aws-region: ${{ vars.AWS_REGION }}
```

Source: https://github.com/aws-actions/configure-aws-credentials/blob/v6.3.0/README.md

## N4 pull_request_target for cloud login

Fork PRs get write permissions reduced to read and no secrets, so `id-token: write` cannot mint a token there (medium confidence). `pull_request_target` runs in the base-repo context; running untrusted code there can grant "unintended access to write privileges or secrets".

```yaml
# ❌ Wrong
on: pull_request_target
jobs:
  plan:
    permissions: { id-token: write }
```

```yaml
# ✅ Correct
on: pull_request
jobs:
  plan:
    if: github.event.pull_request.head.repo.full_name == github.repository
    permissions: { id-token: write, contents: read }
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

## N5 Workflow-level id-token

Every job, including third-party tooling jobs, could mint a token that matches the trust policy.

```yaml
# ❌ Wrong
permissions: { id-token: write, contents: read }
# ✅ Correct
permissions: {}
jobs:
  deploy:
    permissions: { id-token: write, contents: read }
```

Source: https://docs.github.com/en/actions/reference/security/oidc

## N6 Chained role beyond one hour

With role chaining, a `DurationSeconds` above one hour makes the operation fail.

```yaml
# ❌ Wrong
with: { role-chaining: true, role-to-assume: arn:aws:iam::222222222222:role/deploy, role-duration-seconds: 7200 }
# ✅ Correct
with: { role-chaining: true, role-to-assume: arn:aws:iam::222222222222:role/deploy, role-duration-seconds: 3600 }
```

Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html

## N7 ForAllValues in an Allow statement

The README warns against `ForAllValues:` in `Allow` statements; a second source was not read.

```json
// ❌ Wrong
"ForAllValues:StringEquals": { "token.actions.githubusercontent.com:sub": ["repo:o/r:environment:prod"] }
// ✅ Correct
"StringEquals": { "token.actions.githubusercontent.com:sub": "repo:o/r:environment:prod" }
```

Source: https://github.com/aws-actions/configure-aws-credentials/blob/v6.3.0/README.md

## N8 Action SHA copied from a doc example

GitHub's AWS guide shows an older action SHA and `actions/checkout@v6`; the README shows `@v6.2.4`. None is the pinned target.

```yaml
# ❌ Wrong
- uses: aws-actions/configure-aws-credentials@v6
# ✅ Correct
- uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
```

For SHA-pinning rationale see `automating-github-repos-with-actions`.
Source: https://github.com/aws-actions/configure-aws-credentials/releases
