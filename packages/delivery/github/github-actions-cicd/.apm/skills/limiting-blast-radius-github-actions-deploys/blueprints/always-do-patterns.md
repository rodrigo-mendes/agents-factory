# Always-do patterns with code

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Ruleset and environment API calls: [approval models](./approval-models.md). Workflows: [reusable workflows](./reusable-workflows.md), [smoke and rollback](./workflow-smoke-rollback.md).

## Contents

- Verify the artifact hash before every deploy
- One concurrency group per app and environment
- Timeout on every deploy job
- Deployment record per environment
- Lambda alias, published versions only
- Immutable image tags
- Vercel prebuilt output

## Verify the artifact hash before every deploy

The build job records the SHA-256 of the zip as a job output; each deploy job recomputes it (family decision, family rule 8). Lambda versions are immutable once published.

```yaml
- uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
  with: { name: orders-zip, path: dist }
- name: Verify artifact hash before deploy
  run: echo "${EXPECTED_SHA256}  dist/function.zip" | sha256sum -c -
  env:
    EXPECTED_SHA256: ${{ inputs.artifact_sha256 }}
# Expected: "dist/function.zip: OK"; any other output fails the job
```

Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html

## One concurrency group per app and environment

```yaml
concurrency:
  group: deploy-orders-${{ inputs.environment }}
  cancel-in-progress: false
```

At most one job runs per group; a new run only replaces a pending one. `queue: max` keeps up to 100 pending runs and cannot be combined with `cancel-in-progress: true`.
Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency

## Timeout on every deploy job

```yaml
jobs:
  release:
    timeout-minutes: 30   # longest expected bake or shift time plus margin
```

A hung deploy holds the concurrency group and blocks the next release; the default of 360 minutes is too long for that.
Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## Deployment record per environment

```yaml
environment:
  name: ${{ inputs.environment }}
  url: ${{ vars.APP_URL }}
```

```bash
# Representative; REST API version 2026-03-10
gh api "repos/ORG/REPO/deployments?environment=prod&per_page=5" \
  -H "X-GitHub-Api-Version: 2026-03-10" --jq '.[] | {id, sha, ref, created_at}'
# Expected: JSON objects, newest first, one per prod deployment
```

The deployments API gives the audit trail of which commit is live per environment.
Source: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments ; https://docs.github.com/en/rest/deployments/deployments

## Lambda alias, published versions only

```bash
# Representative; AWS CLI v2. Weighted shift, then complete or revert
aws lambda update-alias --function-name orders --name live \
  --routing-config 'AdditionalVersionWeights={"42"=0.10}'
aws lambda update-alias --function-name orders --name live --function-version 42 \
  --routing-config 'AdditionalVersionWeights={}'   # complete
aws lambda update-alias --function-name orders --name live \
  --routing-config 'AdditionalVersionWeights={}'   # revert, alias stays on the old version
```

Both versions must share the execution role and DLQ configuration. Release steps are owned by `deploying-aws-lambda`.
Source: https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html

## Immutable image tags

```bash
aws ecr put-image-tag-mutability --repository-name orders --image-tag-mutability IMMUTABLE
# deploy by digest
image: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/orders@sha256:<digest>
```

With immutability, pushing an existing tag returns `ImageTagAlreadyExistsException`. The put-image-tag-mutability command name is not on the page read; confirm it with `aws ecr help` (medium confidence).
Source: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html

## Vercel prebuilt output

Vercel is the one target whose build output is environment-bound (the production build embeds production settings), so dev and stage cannot receive the same bytes. The rule "build once" holds for production: build in the build stage, never in `_promote.yml`, and promote that staged build.

```bash
# Representative; token handling is owned by vercel-cli-with-tokens
# Build stage (not _promote.yml): vercel build --prod, upload .vercel/output as the artifact, record its digest
# Deploy stage: download the artifact, verify the digest, then:
vercel deploy --prebuilt --prod --skip-domain   # staged production deployment
# smoke-test the printed URL, then:
vercel promote <deployment-url> --yes
```

The promoted identity is the staged deployment built from the verified output archive; dev and stage use Preview deployments, not the promoted bytes. `vercel promote` of a staged production build does not rebuild. Combining `--prebuilt` with `--skip-domain` in one command is (medium confidence).
Source: https://vercel.com/docs/cli/deploying-from-cli ; https://vercel.com/docs/deployments/promoting-a-deployment
