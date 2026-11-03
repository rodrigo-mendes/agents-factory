# Inventory and design — github-actions-cicd (P2, 2026-10-30)

## Go/no-go table

| # | Unit (skill name) | Motivating item | Official docs root | Version lock | Worker | Scope boundary | Overlap |
|---|---|---|---|---|---|---|---|
| 1 | `composing-github-actions-pipelines` | need: replaceable building blocks; monorepo | docs.github.com/en/actions | dated (platform, no version) | researching-technical-frameworks | reusable workflows, composite actions, contracts, matrix, cache, concurrency, environments, path filters, artifacts, required checks | links github-core for pinning/injection/tokens |
| 2 | `automating-terraform-github-actions-v1-17` (PILOT) | need: Terraform CI/CD AWS+OCI | developer.hashicorp.com/terraform + docs.github.com | Terraform 1.17 (F1) | researching-technical-frameworks | PR plan + comment, saved-plan apply, state per env (S3 / OCI Object Storage), drift, `terraform test` in CI | GitHub Actions counterpart of `managing-terraform-cicd` (Azure DevOps) |
| 3 | `federating-github-actions-aws-oidc` | need: keyless AWS login | docs.aws.amazon.com IAM OIDC + docs.github.com OIDC | dated; action v6.3.0 (F3) | researching-technical-frameworks | OIDC provider, trust policy `sub`/`aud`, role per stage x env, troubleshooting | HCL by name: `provisioning-aws-iam-v6` |
| 4 | `federating-github-actions-oci` | need: OCI login + OCIR | docs.oracle.com IAM / CLI / Terraform provider | dated | researching-technical-frameworks | API-key path (default), token-exchange path (medium, F20/F21), OCIR login, Object Storage backend | `oci-terraform` rules (no state lock) by name |
| 5 | `building-java-github-actions` | Java: Maven image, Maven Lambda zip, Gradle, CI only | docs.github.com Java guides, maven.apache.org, docs.gradle.org | dated; Java 25/21/17 (F11), Maven 3.10 (F12), Gradle 9.8 (F13) | researching-technical-frameworks | setup-java, Maven, Gradle (setup-gradle), caching, tests/coverage, Lambda zip artifact, JDK matrix | Lambda release defers to `deploying-aws-lambda` |
| 6 | `publishing-container-images-github-actions` | Java image + Next.js container | docs.docker.com build/ci, docs.github.com packages | dated; build-push v7.4.0 (F7) | researching-technical-frameworks | buildx, metadata/tags, GHCR/ECR/OCIR, SBOM/provenance, digest hand-off | OCIR login uses `oracle-actions/login-ocir` (F22) |
| 7 | `building-nextjs-github-actions-v16-4` | Next.js: Vercel, S3+CloudFront, container, CI only | nextjs.org/docs, vercel.com/docs, docs.github.com Node guide | Next.js 16.4 (F15), Node LTS (F14) | researching-technical-frameworks | setup-node, cache, lint/typecheck/test, `.next/cache`, static export to S3+CF, standalone image, Vercel prebuilt deploy | Vercel CLI details by name: `vercel-cli-with-tokens` |
| 8 | `limiting-blast-radius-github-actions-deploys` | user: blast radius | docs.github.com environments/deployments + per-target docs | dated | researching-technical-frameworks | env promotion of one artifact, approvals, branch policies, progressive delivery per target, smoke test, rollback, isolation matrix | Lambda alias rollback by name: `deploying-aws-lambda` |
| 9 | `securing-supply-chain-github-actions` | scope C8 | docs.github.com code-security, dependency review, Dependabot, attestations | dated; codeql v4 (F8), dependency-review v5 (F9) | researching-technical-frameworks | dependency review, CodeQL Java/TS, IaC + image scan, SBOM/attestations, Dependabot for actions/Maven/Gradle/npm, blocking policy | github-core covers workflow hardening, not scanning |

## Package design

- Slug / package: `github-actions-cicd` -> `packages/github-actions-cicd/` (`agents-factory-github-actions-cicd`).
- Dependencies (apm.yml): `../factory-core`, `../github-core`. Root `apm.yml`: add only `packages/github-actions-cicd` (github-core and factory-core stay transitive).
- Agents: `cicd-pipeline-engineer` (executor: Read, Grep, Glob, Edit, Write, Bash — offline checks only), `cicd-pipeline-reviewer` (advisory: Read, Grep, Glob).
- Command: `building-cicd-pipelines` (`context: fork`, `agent: cicd-pipeline-engineer`, `disable-model-invocation: true`).
- Rules (authored as `.apm/instructions/<name>.instructions.md` with `applyTo:`):
  - `github-workflows-security` -> `**/.github/workflows/**` (overlaps `openspec-github-state` on purpose, DEC-001)
  - `github-workflows-pr-ci` -> `**/.github/workflows/ci-*.yml`
  - `github-workflows-merge-cd` -> `**/.github/workflows/cd-*.yml`
  - `github-workflows-building-blocks` -> `**/.github/workflows/_*.yml,**/.github/actions/**/action.yml`
- Note: this repo's own `.github/workflows/apm.yml` will get the security rule when edited — acceptable.

## Open decisions for G1

1. Names and version suffixes above (only units 2 and 7 are version-locked).
2. Unit 4 (OCI): keep with API key default + token exchange as medium-confidence option, or ship API key only.
3. Where building blocks live by default: in-repo (A) vs central repo (B) — both taught; which is the executor's default.
4. Unit 9 IaC/image scanner choice: research decides among official/first-party options; user may pin one.
