---
kind: work-order
id: wo-<nn>-cicd
from: building-aws-saas-serverless-quarkus-react-nextjs
to: cicd-pipeline-engineer
change: <change-id>
task: <task-id>
refs: []                         # fix round: [<previous wo id>, review-<nn>]
requirements: [R1]
status: pending
createdAt: <ISO 8601 UTC>
---

## Scope

Write the GitHub Actions workflows and composite actions of the change (`.github/workflows/**`, `.github/actions/**`) from
`infrastructure/spec.md` section 10. Offline checks only (`actionlint`, `yamllint` when installed, the grep checks of the skills).
The engineer never pushes, opens a PR, triggers a workflow, applies Terraform or creates secrets.
Output: files + `result-<nn>-cicd.md` (kind `report`, shape of `assets/result-code.template.md`, `role: cicd` is derived from the agent) with a `user-must-add`
list: branch protection of `main`, required check `ci-gate`, environments, variables with the role ARNs.

## Closed requirement (the engineer cannot ask; every line must be filled or the answer is `needs-input`)

- GitHub plan and repo visibility: <Free | Pro | Team | Enterprise | public>
- Clouds and targets: <AWS Lambda, S3 + CloudFront>
- Environments and who releases prod: <dev, prod; approver>
- Repo layout: <backend path, frontend path, Terraform path>
- Workflows wanted: <ci-app, cd-app, ops-drift, reusable _java-build, _node-build, _tf-plan, _tf-apply, _deploy-s3-cf, _smoke-test, _rollback, _security-scan>

## Skills

- composing-github-actions-pipelines - building-java-github-actions - building-nextjs-github-actions-v16-4 - automating-terraform-github-actions-v1-17
- federating-github-actions-aws-oidc - limiting-blast-radius-github-actions-deploys - securing-supply-chain-github-actions

## Requirements

- R1: <requirement text> - pipeline consequence: <job or gate that proves it>.

## Applicable ADRs

- `infrastructure/adr/<NNN>-github-oidc-roles.md`, `infrastructure/adr/<NNN>-...` - <what each forces>.

## Constraints

- Actions pinned by full SHA taken from a loaded skill; minimal `permissions`; OIDC without keys; one `ci-gate` required check; no deploy in `pull_request` workflows.

## Limits

- build_attempts: <effective value> - review_rounds: <effective value>   (source: profile | override | args)

## Acceptance criteria

- [ ] `actionlint` and `yamllint` clean (or marked not installed, with the grep checks run).
- [ ] The `user-must-add` list is complete.
- [ ] Reviewed by `cicd-pipeline-reviewer` (review record with `role: cicd`, REQUIRED: it sends `changes-requested` back to `cicd-pipeline-engineer`).
- [ ] Result record valid, with `spec_impact` and `## Spec impact`.
