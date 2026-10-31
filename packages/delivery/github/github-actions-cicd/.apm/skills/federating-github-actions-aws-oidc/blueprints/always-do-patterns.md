# Always-do patterns with code

Back to [SKILL.md](../SKILL.md). configure-aws-credentials v6.3.0; research date 2026-10-30. Trust policies: [trust policies by plan](./trust-policies-by-plan.md). Full workflows: [login composite action](./login-composite-action.md).

## Contents

- Provider without thumbprint
- Trust policy pins aud and sub
- Job-level id-token
- Pinned action, session name, duration, account guard
- Keep credentials inside the step
- Runner minimum

## Provider without thumbprint

The HCL for the provider belongs to `provisioning-aws-iam-v6`; the CLI form shows the facts it must encode.

```bash
# Representative: adapt to your environment
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com
# Expected: {"OpenIDConnectProviderArn": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"}
```

One provider per URL per account, in the same account as the role that trusts it.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html

## Trust policy pins aud and sub

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "repo:<ORG>/<REPO>:environment:prod"
      }
    }
  }]
}
```

IAM fails role creation with `MalformedPolicyDocument` when the trust does not evaluate `sub` (or `job_workflow_ref`) for the GitHub provider.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_secure-by-default.html

## Job-level id-token

```yaml
# ./.github/workflows/cd-orders.yml
permissions: {}                       # nothing at workflow level
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: prod
    permissions:
      id-token: write                 # this job only
      contents: read
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: ./.github/actions/cloud/login-aws
        with:
          role-arn: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
          region: ${{ vars.AWS_REGION }}
```

The permission only fetches the OIDC token; it grants no write access to other resources.
Source: https://docs.github.com/en/actions/reference/security/oidc

## Pinned action, session name, duration, account guard

Direct call of the official action (the composite wraps the same call):

```yaml
- uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
  with:
    role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
    aws-region: ${{ vars.AWS_REGION }}
    role-session-name: gha-${{ github.run_id }}-${{ github.run_attempt }}
    role-duration-seconds: 3600
    allowed-account-ids: ${{ vars.AWS_ACCOUNT_ID }}
```

- The action default session name `GitHubActions` is identical for every run; the run id ties a CloudTrail entry to one run. The action validates the name since v6.2.0 and its exact regex is (unverified); keep to `[\w+=,.@-]*`, 2 to 64 characters.
- `DurationSeconds` ranges from 900 up to the role's maximum (1 to 12 hours); a higher value fails. The default is 3600; a chained role is capped at 3600. A short 900 s session can expire mid-job, so the composite defaults to 3600 and exposes `role-duration-seconds`.
- `allowed-account-ids` fails the step when credentials belong to another account, which catches a role ARN variable pointing at the wrong account.

Source: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html; https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml

## Keep credentials inside the step

`output-credentials` defaults to `false`; leave it. A post-job step removes credentials unless `AWS_SKIP_CLEANUP_STEP` is `true`. Account IDs are not secret and are not masked unless `mask-aws-account-id` is set. Whether the action masks the key, secret and session token with `setSecret` is (unverified), so never echo `AWS_*` variables.
Source: https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml

## Runner minimum

v6.0.0 moved the action to node24 and needs runner v2.327.1 or later; self-hosted runners older than that fail. That GitHub-hosted runners already meet it is (unverified). v6.3.0 declares `runs.using: node24`. Role chaining and session tags: with OIDC the first hop carries no session tags (medium confidence); tags appear on chained `AssumeRole` hops, and a chained session is capped at one hour. See the chaining example in [login composite action](./login-composite-action.md#role-chaining-to-a-workload-account).
Source: https://github.com/aws-actions/configure-aws-credentials/releases?page=2
