---
name: limiting-blast-radius-github-actions-deploys
description: "Limits blast radius of GitHub Actions deploys (Team, Pro, Free private repos): PR-review approval by ruleset, main-only environments, role per environment, one artifact promoted by digest, canary and rollback per target. Use when designing or reviewing CD."
---

# Limiting the blast radius of GitHub Actions deployments

> Version lock: GitHub.com plans Free, Pro and Team with **private repositories**, REST API version 2026-03-10, as read on **2026-10-30**. Targets: Lambda, ECS, S3 + CloudFront, Vercel, Terraform.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: the control layer around a deploy (who may run it, with which identity, how much traffic, how to undo it). Release steps belong to `deploying-aws-lambda`; Terraform plan and apply to `automating-terraform-github-actions-v1-17`; AWS login to `federating-github-actions-aws-oidc`; OCI login to `federating-github-actions-oci`; image build and push to `publishing-container-images-github-actions`; Vercel tokens to `vercel-cli-with-tokens`.
> Provenance: the dated research file for this unit under the factory workspace; this skill never reads it at run time.

## Version Context

| Item | Value | Source (fetched 2026-10-30) |
|---|---|---|
| Required reviewers, wait timers | Free, Pro and Team: public repositories only | https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments |
| Environments, secrets, branch policy | private repos need Pro (user) or Team (organization) | https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments |
| Rulesets and protected branches | private repos on Pro, Team, Enterprise Cloud | https://docs.github.com/en/get-started/learning-about-github/githubs-plans |
| Ruleset `evaluate` mode | GitHub Enterprise only | https://docs.github.com/en/rest/repos/rules |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` | https://github.com/actions/checkout/releases |
| `actions/upload-artifact` | v7.0.2 = `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | https://github.com/actions/upload-artifact/releases |
| `actions/download-artifact` | v8.0.2 = `9000827ccba6bdab643e8b6fd33ac0654aef8333` | https://github.com/actions/download-artifact/releases |
| `aws-actions/configure-aws-credentials` | v6.3.0 = `e1253824e5c10ff9df46874f81ed3ec929e19cfd` | https://github.com/aws-actions/configure-aws-credentials/releases |
| OIDC `sub` format | repos created after 2026-07-15 use `repo:OWNER@OWNER-ID/REPO@REPO-ID:...`; older repos keep `repo:OWNER/REPO:...` | https://docs.github.com/en/actions/reference/security/oidc |

**Version-lifetime risk** (as of 2026-10-30; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Plan gates move: if the repository becomes public or joins GitHub Enterprise, required reviewers become available.
- ECS native strategies and their alarm coverage are recent and not fully documented in the pages read.
- Pinned action SHAs go stale; re-resolve them with `git ls-remote` before every bump.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Verification Loop](#verification-loop)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Isolation matrix and plan availability](./blueprints/isolation-matrix.md)
- [Approval models: default, solo maintainer, Free, upgrade path](./blueprints/approval-models.md)
- [Reusable workflows and contracts: _promote.yml](./blueprints/reusable-workflows.md)
- [_smoke-test.yml, _rollback.yml and the cd caller](./blueprints/workflow-smoke-rollback.md)
- [Progressive delivery per target](./blueprints/progressive-delivery.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

Shape: a caller `cd-<app>.yml` (push to `main`) builds once, then chains the fixed reusable workflows `_promote.yml`, `_smoke-test.yml` and `_rollback.yml` for `dev`, `stage` and `prod`. Default human approval on Pro and Team is the pull-request review before merge (family decision); required reviewers are an upgrade path only. Cross-references by name only: `securing-supply-chain-github-actions`, `automating-github-repos-with-actions` (SHA pinning, injection-safe scripts).

### ✅ Always Do

- **Require a pull request with one approval on the default branch through a ruleset** ([available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)).
- **Enable approval of the most recent reviewable push**, so the last pusher cannot approve ([available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)).
- **Create the ruleset with enforcement `active`**; `evaluate` needs GitHub Enterprise ([REST rules](https://docs.github.com/en/rest/repos/rules)).
- **Restrict every deployable environment to selected branch `main`** ([deployments reference](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
- **Keep deploy secrets as environment secrets**; the job reads them only after the environment rules pass ([deployments reference](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
- **Use one cloud role, one state key and one target per environment** (family decision; [workspace guidance](https://developer.hashicorp.com/well-architected-framework/operational-excellence/operational-excellence-workspaces-projects)).
- **Promote Lambda by published version**; its code and configuration are immutable ([Lambda versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html)).
- **Set ECR tag immutability** so a promoted tag cannot be overwritten ([ECR tag mutability](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html)).
- **Deploy Vercel from `vercel deploy --prebuilt` output** so no remote rebuild happens ([deploying from CLI](https://vercel.com/docs/cli/deploying-from-cli)).
- **Set `cancel-in-progress: false` on every deploy concurrency group** ([control concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)).
- **Set `timeout-minutes` on every deploy job**; the default is 360 ([workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)).
- **Declare `environment` with `name` and `url` on the deploying job** to create a deployment record ([control deployments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments)).
- **Point a Lambda alias only at published versions, at most two**, never `$LATEST` ([alias routing](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)).
- **Split Terraform state by volatility and by stateful versus stateless resources** ([workspace guidance](https://developer.hashicorp.com/well-architected-framework/operational-excellence/operational-excellence-workspaces-projects)).

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| GitHub plan | Pro or Team (default design) vs Free private (weaker, no environments or protected branches) | "Which plan owns this private repository?" |
| Approval model | Merge-only gate vs merge gate plus manual prod dispatch (medium confidence) vs required reviewers (public or Enterprise only) | "Is a second human click before prod wanted?" |
| Solo maintainer | Add a second collaborator (preferred) vs 0 approvals with required checks vs manual dispatch | "Is there a second person who can review?" |
| Lambda mechanism | Workflow alias shift vs CodeDeploy canary or linear (medium confidence on the runner-death rationale) | "Must rollback happen if the runner dies mid-shift?" |
| ECS rollback | Native strategy plus alarms; alarm coverage outside rolling updates is (unverified) | "Which strategy and which alarms?" |
| S3 + CloudFront | Versioned origin prefix vs staging distribution (canarying site content is medium confidence) | "Is traffic splitting needed, or is a prefix switch enough?" |
| PR environment | Separate `<env>-pr` read environment, `deployment: false` effects are (unverified) | "Should PR jobs create deployment records?" |
| Manual rollback target | Previous version or an older recorded one | "Which release must be restorable?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Rely on required reviewers or wait timers in a private Free, Pro or Team repo ([deployments reference](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)) | PR review before merge by ruleset, plus `main`-only environments |
| Rebuild for each environment (family decision) | Build once, verify hash or digest, promote |
| `cancel-in-progress: true` on a deploy group ([control concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)) | `cancel-in-progress: false` |
| "Protected branches only" or no restriction on a prod environment ([REST environments](https://docs.github.com/en/rest/deployments/environments)) | `custom_branch_policies: true` with policy `main` |
| Ruleset bypass actors or `evaluate` enforcement on Pro or Team ([REST rules](https://docs.github.com/en/rest/repos/rules)) | `bypass_actors: []`, `enforcement: active` |
| Promote a Vercel Preview deployment to production ([vercel promote](https://vercel.com/docs/cli/promote)) | Promote the staged production deployment |
| Point a Lambda alias at `$LATEST` ([alias routing](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)) | Publish a version, point the alias at its number |
| Deploy by mutable image tag such as `:latest` ([ECR tag mutability](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html)) | `repo@sha256:<digest>` with immutable tags |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Concurrency | at most one running job per group; `queue: max` allows 100 pending, not with `cancel-in-progress: true` | https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency |
| Job timeout | default 360 minutes | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax |
| Required reviewers (upgrade path) | up to six; one approval suffices | https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments |
| Lambda alias | max two versions; same role and DLQ config | https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html |
| ECS strategies | `ROLLING`, `BLUE_GREEN`, `LINEAR`, `CANARY` | https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentConfiguration.html |
| CloudFront staging weight | `SingleWeight` up to 15 percent | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment-quotas-considerations.html |
| Vercel staged production | `vercel --prod --skip-domain`, then `vercel promote` | https://vercel.com/docs/deployments/promoting-a-deployment |
| Artifact retention default | 90 days; set `retention-days` | https://docs.github.com/en/actions/tutorials/store-and-share-data |

## Verification Loop

Run these offline checks in a repository that follows the skill, then compare with the expected output.

```bash
# 1. every deploying reusable workflow has a timeout and a concurrency group
grep -nE "timeout-minutes:|concurrency:" .github/workflows/_promote.yml .github/workflows/_rollback.yml
# Expected: at least one of each per file
# 2. no cancelling deploy groups
grep -nE "cancel-in-progress:\s*true" .github/workflows/cd-*.yml .github/workflows/_*.yml
# Expected: no output (exit 1)
# 3. no rebuild in the promotion workflows
grep -nE "docker build|mvn (package|verify)|vercel build" .github/workflows/_promote.yml .github/workflows/_rollback.yml
# Expected: no output (exit 1)
# 4. environment policy (live, read-only)
gh api repos/ORG/REPO/environments/prod --jq '.deployment_branch_policy'
# Expected: {"protected_branches":false,"custom_branch_policies":true}
gh api repos/ORG/REPO/environments/prod/deployment-branch-policies --jq '.branch_policies[].name'
# Expected: main
```

## External Resources

All fetched 2026-10-30.

- [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [Lambda weighted alias](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)
- [Vercel promoting deployments](https://vercel.com/docs/deployments/promoting-a-deployment)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
