# Static export to S3 and CloudFront

Back to [SKILL.md](../SKILL.md). Next.js 16.4.x static export (`output: 'export'`, folder `out`); research date 2026-10-30. Commands are representative, adapt to your environment. Login and role trust are owned by `federating-github-actions-aws-oidc`.

Contents: [Reusable deploy](#reusable-workflow-githubworkflows_deploy-s3-cfyml) | [Origin-path switch](#origin-path-switch-script) | [Rollback](#rollback-workflow) | [Plan variants](#plan-variants) | [Routing](#routing-for-static-export)

## Reusable workflow `./.github/workflows/_deploy-s3-cf.yml`

The job names an environment, so its variables (`AWS_DEPLOY_ROLE_ARN`, `AWS_REGION`, `SITE_BUCKET`, `CF_DISTRIBUTION_ID`) are read inside the job. Whether environment-scoped variables resolve inside a reusable workflow job is unverified; the fallback is to inline this job in the caller.

```yaml
# Representative — adapt to your environment
name: _deploy-s3-cf
on:
  workflow_call:
    inputs:
      environment:     { type: string, required: true, description: "staging | prod" }
      artifact-name:   { type: string, required: true }
      artifact-digest: { type: string, default: "", description: "Logged for traceability" }
    outputs:
      release-prefix:
        description: S3 prefix that now holds the release
        value: ${{ jobs.deploy.outputs.release-prefix }}
permissions:
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    environment: ${{ inputs.environment }}
    concurrency: { group: "deploy-s3-${{ inputs.environment }}", cancel-in-progress: false }
    permissions:
      contents: read
      id-token: write                 # this job only
    outputs:
      release-prefix: releases/${{ github.sha }}
    env:
      BUCKET: ${{ vars.SITE_BUCKET }}
      DIST_ID: ${{ vars.CF_DISTRIBUTION_ID }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with:
          name: ${{ inputs.artifact-name }}
          path: out
      - env:
          ARTIFACT_NAME: ${{ inputs.artifact-name }}
          ARTIFACT_DIGEST: ${{ inputs.artifact-digest }}
        run: echo "artifact ${ARTIFACT_NAME} digest ${ARTIFACT_DIGEST}" >> "$GITHUB_STEP_SUMMARY"
      - uses: ./.github/actions/cloud/login-aws     # owned by federating-github-actions-aws-oidc
        with:
          role-arn: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
          region: ${{ vars.AWS_REGION }}
          session-name: gha-deploy-web-${{ github.run_id }}
          role-duration-seconds: "900"
      - run: aws s3 sync out/ "s3://${BUCKET}/releases/${GITHUB_SHA}/" --no-progress
      - run: ./scripts/switch-origin-path.sh "$DIST_ID" "/releases/${GITHUB_SHA}"
      - run: aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"
```

The checkout is only for the script below; the deploy job installs no packages and restores no caches.

## Origin-path switch script

`./scripts/switch-origin-path.sh` rewrites the first origin's path and updates the distribution with the ETag from the read. The `get-distribution-config` and `update-distribution` mechanics were not read on the AWS CLI reference (medium confidence); test it against a sandbox distribution first.

```bash
#!/usr/bin/env bash
# Representative — adapt to your environment
set -euo pipefail
DIST_ID="$1"; NEW_PATH="$2"          # NEW_PATH has a leading slash, no trailing slash
aws cloudfront get-distribution-config --id "$DIST_ID" > cfg.json
ETAG="$(jq -r '.ETag' cfg.json)"
jq --arg p "$NEW_PATH" '.DistributionConfig | .Origins.Items[0].OriginPath = $p' cfg.json > new.json
aws cloudfront update-distribution --id "$DIST_ID" --if-match "$ETAG" --distribution-config file://new.json
```

An origin path makes CloudFront request content from that directory of the origin. Changing the origin path does not empty edge caches, so the `/*` invalidation follows every switch (medium confidence). Wildcard paths count as one path.

## Rollback workflow

Rollback switches the origin path back to an earlier release and invalidates; no rebuild, no upload. The command details are medium confidence (the switch script above).

```yaml
# ops-web-rollback.yml — Representative, adapt to your environment
name: ops-web-rollback
on:
  workflow_dispatch:
    inputs:
      sha: { description: "Full git sha of an existing releases/<sha>/ prefix", required: true }
permissions:
  contents: read
jobs:
  rollback:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    environment: prod
    concurrency: { group: "deploy-s3-prod", cancel-in-progress: false }
    permissions: { contents: read, id-token: write }
    env:
      TARGET_SHA: ${{ inputs.sha }}
      DIST_ID: ${{ vars.CF_DISTRIBUTION_ID }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: ./.github/actions/cloud/login-aws
        with:
          role-arn: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
          region: ${{ vars.AWS_REGION }}
          session-name: gha-rollback-web-${{ github.run_id }}
          role-duration-seconds: "900"
      - run: ./scripts/switch-origin-path.sh "$DIST_ID" "/releases/${TARGET_SHA}"
      - run: aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"
```

## Plan variants

| Item | Pro / Team private (default) | Free private (weaker, accepted risk) |
|---|---|---|
| Gate | Environment `prod` with deployment branch rule `main`; approval is the PR review before merge to protected `main` | No environments and no protected branches; the merge itself is the only gate |
| AWS role trust `sub` | `repo:ORG/REPO:environment:prod` | `repo:ORG/REPO:ref:refs/heads/main` |
| Role ARN and bucket | Environment variables | Repository variables |
| Stored secrets | none | none |
| Upgrade path | Required reviewers on `prod` (public repo or Enterprise) | Move to Pro/Team |

Repositories created after 2026-07-15 use the immutable `sub` format `repo:OWNER@OWNER-ID/REPO@REPO-ID:...` by default; older repositories keep the plain format unless they opt in. On Free, any job on `main` gets the same `sub`, so separate dev and prod by role or account. For Free, inline the deploy job in the caller and drop the `environment` line.

## Routing for static export

Export writes `/blog/post-1.html` (or `/blog/post-1/index.html` with `trailingSlash: true`). CloudFront's default root object applies to the root only. With an S3 REST origin and origin access control, deep links need a viewer-request rewrite that appends `.html` or `index.html`; the CloudFront Functions details were not read (unverified). S3 website endpoints serve subdirectory index documents but cannot use origin access control. Routes whose URLs map directly to files need no rewrite.
