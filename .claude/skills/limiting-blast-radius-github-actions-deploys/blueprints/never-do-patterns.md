# Never-do patterns with examples

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Every alternative is documented on the cited page.

## Contents

- N1 Relying on required reviewers
- N2 Rebuilding per environment
- N3 Cancelling a running deploy
- N4 Loose environment branch policy
- N5 Ruleset with bypass actors or evaluate
- N6 Promoting a Vercel Preview
- N7 Lambda alias on $LATEST
- N8 Mutable image tags
- Trap: the private Team repository

## N1 Relying on required reviewers

On Free, Pro and Team, "required reviewers are only available for public repositories"; the pipeline ships without the gate its authors believe exists.

```yaml
# ❌ assumes a human pauses this job; on a private Pro or Team repo nothing pauses it
deploy-prod:
  environment: prod
```

```yaml
# ✅ approval happened at PR review (ruleset); the environment admits only main
deploy-prod:
  if: github.ref == 'refs/heads/main'
  environment: { name: prod, url: "https://orders.example.com" }
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

## N2 Rebuilding per environment

```yaml
# ❌ prod job runs the build again
deploy-prod:
  steps: [ { run: mvn package }, { run: ./deploy.sh } ]
```

```yaml
# ✅ download, verify hash, deploy the same bytes (images by digest, Vercel --prebuilt)
deploy-prod:
  uses: ./.github/workflows/_promote.yml
  with: { artifact_sha256: "${{ needs.build.outputs.zip_sha256 }}" }
```

Source: https://vercel.com/docs/cli/deploying-from-cli ; family rule 8

## N3 Cancelling a running deploy

```yaml
# ❌
concurrency: { group: deploy-orders-prod, cancel-in-progress: true }
# ✅
concurrency: { group: deploy-orders-prod, cancel-in-progress: false }
```

`cancel-in-progress: true` also cancels the running job, so a half-shifted alias or a partial apply may be killed mid-way (medium confidence).
Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency

## N4 Loose environment branch policy

```json
{ "deployment_branch_policy": null }
{ "deployment_branch_policy": { "protected_branches": true, "custom_branch_policies": false } }
```

The first admits every branch, the second every protected branch. Use:

```json
{ "deployment_branch_policy": { "protected_branches": false, "custom_branch_policies": true } }
```

plus one policy named `main` of type `branch`.
Source: https://docs.github.com/en/rest/deployments/environments

## N5 Ruleset with bypass actors or evaluate

```json
{ "enforcement": "evaluate", "bypass_actors": [ { "actor_type": "RepositoryRole", "actor_id": 5, "bypass_mode": "always" } ] }
```

Admins merge unreviewed, and `evaluate` is only available with GitHub Enterprise. Use `"bypass_actors": []` and `"enforcement": "active"`.
Source: https://docs.github.com/en/rest/repos/rules

## N6 Promoting a Vercel Preview

```bash
# ❌ Preview build: promoting it creates a new production deployment (a rebuild)
vercel promote https://orders-git-feature-x.vercel.app --yes
# ✅ promote the staged production deployment
vercel promote https://orders-abc123.vercel.app --yes
```

Source: https://vercel.com/docs/cli/promote

## N7 Lambda alias on $LATEST

```bash
# ❌ the alias cannot point to $LATEST
aws lambda update-alias --function-name orders --name live --function-version '$LATEST'
# ✅ publish, then point at the number
aws lambda update-alias --function-name orders --name live --function-version 42
```

Source: https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html

## N8 Mutable image tags

```yaml
# ❌ the tag can be overwritten between stage and prod
image: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/orders:latest
# ✅ digest, with an immutable repository
image: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/orders@sha256:<digest>
```

Source: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html

## Trap: the private Team repository

A request to "add required reviewers to prod" on a private Team repository must be answered with the plan table (reviewers need a public repository or GitHub Enterprise), then the default design in [approval models](./approval-models.md). Do not create an environment and say it is gated.
