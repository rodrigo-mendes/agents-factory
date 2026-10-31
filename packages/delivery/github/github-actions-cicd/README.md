# github-actions-cicd

GitHub Actions CI/CD for AWS, OCI and Vercel, with Terraform, Java and Next.js stacks. Facts are dated 2026-10-30.

## What it does

You give the `/building-cicd-pipelines` command a closed requirement. A non-interactive agent loads only the matching knowledge skills, writes or fixes `.github/workflows/**` and `.github/actions/**` (plus the few files the skills require, see Scope limits), and runs offline checks (`actionlint`, `yamllint`, `terraform fmt -check`, the grep checks of each skill). It never pushes, triggers workflows, applies infrastructure or reads secrets. The command is write/fix only; reviews go to `cicd-pipeline-reviewer`.

## Building-block model

Callers hold triggers and decisions. Reusable workflows hold one job-level capability. Composite actions hold repeated step sequences.

```
callers (triggers, inputs, environment names)
  .github/workflows/ci-<app>.yml      PR: read-only, PR-only cloud role, single ci-gate
  .github/workflows/cd-<app>.yml      merge/release: environments, promotion by digest
  .github/workflows/ops-<name>.yml    drift, scheduled, manual operations
        |  uses: ./.github/workflows/_<domain>-<name>.yml
        v
reusable workflows (typed inputs, secrets as inputs, environment as input)
  _tf-plan  _tf-apply  _java-build  _image-publish  _node-build
  _deploy-s3-cf  _deploy-vercel  _promote  _smoke-test  _rollback  _security-scan
        |  uses: ./.github/actions/<domain>/<name>
        v
composite actions
  .github/actions/aws/login-aws   .github/actions/oci/login-oci   build setup steps
```

GitHub does not allow workflows in subfolders of `.github/workflows/`. The domain therefore goes in the file-name prefix: `_<domain>-<name>.yml`. Blocks live in the same repository by default. A central blocks repository is an option that requires SHA-pinned cross-repository references.

## Contents

| Type | Name | One line |
|---|---|---|
| Skill | `composing-github-actions-pipelines` | Building-block model, monorepo ci-gate, plan variants, central blocks repo |
| Skill | `automating-terraform-github-actions-v1-17` | Terraform 1.17 PR plan, saved-plan apply, S3 or oci backends, drift |
| Skill | `federating-github-actions-aws-oidc` | Keyless AWS login, trust policies by plan, login-aws composite |
| Skill | `federating-github-actions-oci` | OCI API key default, optional token exchange, OCIR, login-oci composite |
| Skill | `building-java-github-actions` | Maven 3.10 wrapper or Gradle 9.8, JDK matrix, Lambda zip, image hand-off |
| Skill | `publishing-container-images-github-actions` | buildx, GHCR/ECR/OCIR, digest outputs, BuildKit attestations |
| Skill | `building-nextjs-github-actions-v16-4` | Next.js 16.4 CI, static export to S3+CloudFront, standalone image, Vercel |
| Skill | `limiting-blast-radius-github-actions-deploys` | Approvals by plan, promotion by digest, progressive delivery, rollback |
| Skill | `securing-supply-chain-github-actions` | Checkov/Trivy gates, CodeQL and dependency review when licensed, Dependabot |
| Agent | `cicd-pipeline-engineer` | Non-interactive executor: writes and fixes workflows, offline checks only |
| Agent | `cicd-pipeline-reviewer` | Read-only reviewer of workflows (all review-only requests), spawned via the Agent tool |
| Rule | `github-workflows-security` | SHA pins, minimal permissions, keyless login, trigger and injection hygiene |
| Rule | `github-workflows-pr-ci` | `ci-*.yml`: read-only, PR-only role, plan and comment, single ci-gate |
| Rule | `github-workflows-merge-cd` | `cd-*.yml`: plan variants, environments, saved-plan apply, digest promotion, prod smoke test and rollback |
| Rule | `github-workflows-building-blocks` | `_*.yml` and composites: typed contract, environment as input, no hardcoded values |
| Command | `/building-cicd-pipelines` | Forks to `cicd-pipeline-engineer` with a closed requirement |

Related skills in other packages are referenced by name only: `automating-github-repos-with-actions` (`github-core`, a dependency). The others are optional and named, when missing, as an open question with the package to install: `managing-terraform-cicd` (`oci-terraform`, Azure DevOps), `provisioning-aws-iam-v6` (`aws-terraform`), `deploying-aws-lambda` (`aws-lambda`), `vercel-cli-with-tokens` (`vercel-frontend`).

## GitHub plan support

The agent asks the plan before generating any deploy job. Source: docs.github.com plans and deployments pages, 2026-10-30 (F25, F33, F39).

| Plan (private repo) | Approval model | Notes |
|---|---|---|
| Pro / Team (default) | Protected `main` with required pull request reviewers; the approval is the PR review before merge. Environments with secrets, variables and a `main` deployment branch policy (Team for organizations, Pro for user accounts). | Protected branches, required PR reviewers and code owners in private repos are Pro and Team features (F39). |
| Free (weaker variant) | No environments in private repos ("Users with GitHub Free plans can only configure environments for public repositories"). No environment secrets; the cloud role trusts `ref:refs/heads/main`; static secrets are repository secrets (the only case where that is allowed), with a warning. Protected branches and required reviewers are not listed for Free private. | The weaker variant is stated explicitly in the output. The agent asks whether the accepted risks are acceptable or the repo can move to Pro/Team. |
| Enterprise / public repo (upgrade path) | Required reviewers, wait timers and custom deployment protection rules on environments are public-repo or Enterprise only (F25). Artifact attestations on private repos need GitHub Enterprise Cloud (F33). | CodeQL and dependency review jobs are generated only when licensed. |

## How to use

```
/building-cicd-pipelines Java 21 Lambda CI+CD to AWS via OIDC, GitHub Team private repo, environments dev and prod (prod after PR review), monorepo with app at ./services/orders, blocks in the same repo, Maven wrapper, Checkov + Trivy scans, role ARN in AWS_DEPLOY_ROLE_ARN, CI and CD, repo-root .
```

Include the plan, clouds and targets, environments, layout, block location, stack details, Ask First decisions (for example OCI API key vs token exchange) and scope. Missing items come back as NEEDS-INPUT questions. The generated callers expose one required check, `ci-gate`. For an independent or review-only pass, spawn `cicd-pipeline-reviewer` through the Agent tool on the `.github/` paths.

### Recommended permission deny entries (not configured by this package)

The package does not edit `settings.json`. Consider adding deny entries in your own Claude Code settings for the commands the agents must never run, for example `Bash(terraform apply:*)`, `Bash(terraform destroy:*)`, `Bash(gh workflow run:*)` and `Bash(git push:*)`.

## Scope limits

Out of scope: GitHub Enterprise Server, self-hosted runner fleets, Azure, Jenkins and Azure DevOps pipelines (see `managing-terraform-cicd` for the latter), and database migrations. The package never runs pipelines, triggers workflows, or runs `terraform apply`, `destroy` or `import`. It writes only under `.github/workflows/` and `.github/actions/`, plus exactly the files the skills require: `.github/dependabot.yml`, the blueprint-named helper scripts (`scripts/smoke.sh`, `scripts/switch-origin-path.sh`) and `vercel.json`. Anything else (Terraform code, Dockerfiles, branch protection, environments, secrets, IAM) is returned as a user-must-add item.

## Versions (as of 2026-10-30)

| Component | Version | Fact |
|---|---|---|
| Terraform CLI | 1.17.1 (2026-10-28) | F1 |
| Java LTS | 25 (latest), 21, 17 | F11 |
| Maven | 3.10.0 (Maven 4 not GA) | F12 |
| Gradle | 9.8.2 | F13 |
| Node.js LTS | 26 (26.13.0), 24, 22 | F14 |
| Next.js | 16.4.3 | F15 |

Medium-confidence items (for example OCI token exchange, F21) are surfaced as unverified, not used as rules.

## Provenance

The research files under `workspace/github-actions-cicd/` in the factory repository (`_family_facts.md` F1-F42, `_family_rules.md` 1-18) are cited here as provenance. No shipped skill, agent or rule reads them at runtime.
