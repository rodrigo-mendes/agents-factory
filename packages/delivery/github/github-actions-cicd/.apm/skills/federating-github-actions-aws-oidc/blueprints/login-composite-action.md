# Login composite action and workflows

Back to [SKILL.md](../SKILL.md). configure-aws-credentials v6.3.0 (pinned SHA in SKILL.md Version Context); research date 2026-10-30. Trust policies: [trust policies by plan](./trust-policies-by-plan.md).

## Contents

- Composite action login-aws
- Calling it from a CD job
- Reusable login check workflow
- Role chaining to a workload account
- Troubleshooting

## Composite action login-aws

```yaml
# ./.github/actions/cloud/login-aws/action.yml
name: login-aws
description: Keyless AWS login through GitHub OIDC (wraps configure-aws-credentials v6.3.0)
inputs:
  role-arn:
    description: ARN of the role to assume (deploy or PR read role)
    required: true
  region:
    description: AWS region
    required: true
  session-name:
    description: Session name, 2 to 64 characters of [\w+=,.@-]; empty uses gha-<run_id>-<run_attempt>
    required: false
    default: ""
  role-duration-seconds:
    description: Session length in seconds. Must not exceed the role maximum session duration; a chained role is capped at 3600
    required: false
    default: "3600"
runs:
  using: composite
  steps:
    - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
      with:
        role-to-assume: ${{ inputs.role-arn }}
        aws-region: ${{ inputs.region }}
        role-session-name: ${{ inputs.session-name != '' && inputs.session-name || format('gha-{0}-{1}', github.run_id, github.run_attempt) }}
        role-duration-seconds: ${{ inputs.role-duration-seconds }}
```

Notes:
- The composite cannot grant `id-token: write`; only the job that calls it holds it (job level only).
- `role-duration-seconds` defaults to 3600 because a fixed 900 s session expires during a long Terraform apply or image push. Never set it above the role's maximum session duration (default 1 h; raise the role setting first), and keep it at 3600 or less for chained roles.
- The composite exposes four inputs on purpose; for `allowed-account-ids`, `role-chaining` or `mask-aws-account-id` call the official action directly (see the chaining example).
- A local composite action must be present in the workspace, so the calling job checks out the repository first; that ordering is (unverified) in the research and is standard GitHub behavior to confirm on the first run.
- Credentials do not cross job boundaries: log in inside the job that uses AWS.
Source: https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml

## Calling it from a CD job

```yaml
# ./.github/workflows/cd-orders.yml  (Pro/Team: environment trust)
on:
  push:
    branches: [main]
permissions: {}
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: prod
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: ./.github/actions/cloud/login-aws
        with:
          role-arn: ${{ vars.AWS_DEPLOY_ROLE_ARN }}   # variable of environment prod, read in this job
          region: ${{ vars.AWS_REGION }}
```

On Free private there is no environment: remove `environment: prod`, store the role ARN as a repository variable, and trust `ref:refs/heads/main`.
Source: https://docs.github.com/en/actions/reference/security/oidc

The PR variant (PR read role, `<env>-pr` environment, fork guard) is shown in [never-do patterns](./never-do-patterns.md#n2-pr-job-with-a-deployable-environment).

## Reusable login check workflow

Use it to prove a trust policy before real pipelines depend on it.

```yaml
# ./.github/workflows/_aws-oidc-login-check.yml
name: _aws-oidc-login-check
on:
  workflow_call:
    inputs:
      environment: { type: string, required: true }
      role-arn:    { type: string, required: true }
      aws-region:  { type: string, required: true }
      account-id:  { type: string, required: true }
    outputs:
      caller-arn:
        description: ARN returned by sts get-caller-identity
        value: ${{ jobs.login.outputs.caller-arn }}
permissions: {}
jobs:
  login:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    permissions:
      id-token: write
      contents: read
    outputs:
      caller-arn: ${{ steps.who.outputs.arn }}
    steps:
      - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
        with:
          role-to-assume: ${{ inputs.role-arn }}
          aws-region: ${{ inputs.aws-region }}
          role-session-name: gha-${{ github.run_id }}-${{ github.run_attempt }}
          role-duration-seconds: 3600
          allowed-account-ids: ${{ inputs.account-id }}
      - id: who
        run: echo "arn=$(aws sts get-caller-identity --query Arn --output text)" >> "$GITHUB_OUTPUT"
```

In a reusable workflow the caller's repo and environment drive the `sub`. The `role-arn` input is for a check run; in real pipelines the called job that declares the environment reads `vars.AWS_DEPLOY_ROLE_ARN` (or `vars.AWS_PR_ROLE_ARN` on `<env>-pr`) itself, never the caller. That `ubuntu-latest` ships the AWS CLI is (unverified) in the research; confirm on the first run.
Source: https://docs.github.com/en/actions/reference/security/oidc

## Role chaining to a workload account

A hub account holds the provider; the second step assumes a role in the workload account. Chained sessions last at most one hour.

```yaml
- uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
  with:
    role-to-assume: arn:aws:iam::111111111111:role/gha-hub
    aws-region: eu-west-1
- uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
  with:
    role-chaining: true
    role-to-assume: arn:aws:iam::222222222222:role/gha-orders-prod-deploy
    aws-region: eu-west-1
    role-duration-seconds: 3600
    role-skip-session-tagging: true   # or allow sts:TagSession in the second role's trust
```

Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html

## Troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| `Not authorized to perform sts:AssumeRoleWithWebIdentity` | `sub` mismatch (environment vs pull_request vs ref); immutable repo with name-only policy; custom template not in policy; wrong provider account | compare job shape with the table; `GET /repos/{owner}/{repo}/actions/oidc/customization/sub` |
| Audience error or `InvalidIdentityToken` | provider lacks `sts.amazonaws.com`, or `audience` changed | `aws iam get-open-id-connect-provider`; exact STS text for an aud mismatch is (unverified) |
| No token at all | job lacks `id-token: write`, or fork PR | job `permissions`; event source |
| `MalformedPolicyDocument` on role create | trust lacks `sub` or uses only a wildcard | identity-provider controls page |
| Duration error | above role maximum, or above 3600 when chained | `role-duration-seconds` |
| `Credentials loaded by the SDK do not match` | credentials already in env | enable `role-chaining` or `unset-current-credentials` |

Source: https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/README.md
