---
name: building-cicd-pipelines
description: "Routes a closed GitHub Actions CI/CD requirement to the cicd-pipeline-engineer agent. Use when a fully specified pipeline (build, scan, deploy to AWS/OCI/Vercel, Terraform) must be written or fixed as workflows and verified offline. Write/fix only; review-only requests go to cicd-pipeline-reviewer."
argument-hint: "<requirement summary> <repo-root> (e.g. 'Java Lambda CI+CD to AWS via OIDC, Pro private repo, dev+prod, monorepo ./')"
context: fork
agent: cicd-pipeline-engineer
disable-model-invocation: true
---

# Building CI/CD Pipelines

## Function

Routes a closed GitHub Actions CI/CD requirement to the `cicd-pipeline-engineer` agent. The agent
loads only the matching knowledge skills of this package, writes or fixes `.github/workflows/**`
and `.github/actions/**`, and runs offline checks. It states no GitHub, cloud or tool facts of its
own. This command is write/fix only: for a review-only request, spawn `cicd-pipeline-reviewer`
through the Agent tool instead.

## How to phrase a closed requirement

The agent is non-interactive. Supply all of the following or it returns NEEDS-INPUT questions:

1. **GitHub plan and repository visibility** (Free, Pro, Team, Enterprise; public or private).
   Mandatory before any CD: it decides the approval and environment-protection variant.
2. **Clouds and targets** (AWS, OCI, Vercel; Lambda, container image, static site, Terraform).
3. **Environments** (names, which need approval, which is production).
4. **Repository layout** (monorepo or single app; app paths).
5. **Block location** (default: the same repository; or a central blocks repository).
6. **Stack details**: build tool and JDK or Node version, image registry, Terraform root and state
   backend (or "no backend").
7. **Decisions** the skills treat as Ask First for those domains (e.g. OCI token exchange vs API
   key, progressive delivery or not).
8. **Scope**: CI only, CD, or both; scanners wanted.

## What the agent will and will not do

**Will:** load the four rules and only the matching skills (always `composing-github-actions-pipelines`), write or fix
callers (`ci-`, `cd-`, `ops-`), reusable workflows (`_<domain>-<name>.yml`) and composite actions;
run `actionlint` and `yamllint` if installed, `terraform fmt -check` where HCL is touched, and the
grep checks of each skill's Verification Loop; report exact outputs; surface every
`(unverified)` / `(medium confidence)` item instead of using it as a rule.

**Will not:** push, commit, open pull requests, trigger workflows (`gh workflow run`), run
`terraform apply`/`destroy`/`import`, call cloud APIs or CLIs, create or read secrets, use actions
or SHAs that no loaded skill shows, assume missing requirements (it returns questions), or cover
other CI systems, other clouds or stacks without a skill. Commands that skills show are
descriptions: the agent reports "skill suggests X; not run".

**Write scope:** `.github/workflows/**`, `.github/actions/**`, plus exactly the files the skills
require: `.github/dependabot.yml`, the blueprint-named helper scripts (`scripts/smoke.sh`,
`scripts/switch-origin-path.sh`) and `vercel.json`. Anything else (Terraform code, Dockerfiles,
branch protection, environments, secrets, IAM) comes back as a user-must-add item.

Optional related skills in other packages, referenced by name only: `managing-terraform-cicd`
(`oci-terraform`, Azure DevOps), `provisioning-aws-iam-v6` (`aws-terraform`), `deploying-aws-lambda`
(`aws-lambda`), `vercel-cli-with-tokens` (`vercel-frontend`). If one is not installed, the agent
returns an open question naming the package to install.

## Usage examples

```
/building-cicd-pipelines "Java 21 Maven Lambda, CI on PR and CD on merge to main to AWS via OIDC, GitHub Pro private repo, environments dev and prod (prod needs approval), monorepo with apps/orders, blocks in the same repo, Checkov and Trivy scans" .
/building-cicd-pipelines "Terraform 1.17 PR plan and saved-plan apply for ./infra, S3 backend bucket acme-tfstate key app/terraform.tfstate eu-west-1, AWS OIDC, Team plan, single repo, environments staging and prod" .
/building-cicd-pipelines "fix the existing .github/workflows to the blast-radius and supply-chain guardrails (pin actions by SHA, add permissions, digest promotion), Pro plan private repo, environments dev and prod, monorepo ./" .
```

For review-only, use the reviewer instead (no edits): spawn `cicd-pipeline-reviewer` through the Agent tool on the `.github/` paths.

## Evaluation Scenarios

See [./blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
