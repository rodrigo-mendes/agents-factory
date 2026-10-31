# Unverified and risks register

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Tags are plain parentheses: (unverified) and (medium confidence).

## Contents

- Version-lifetime risk
- Unverified (8)
- Irresolvable (0)
- Medium confidence (11)
- Coverage limits (5)
- Tag to register mapping
- Source Bibliography

## Version-lifetime risk

As of 2026-10-30.

- Plan gates are the main drift risk: required reviewers, wait timers and deployment protection rules are public-repository only on Free, Pro and Team today; a plan change or a public repository changes the design (upgrade path). Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- Introduction dates of `queue: max`, `deployment: false` and the ECS native strategies were not on the pages read (unverified).
- Rulesets, environments and deployments REST pages show API version 2026-03-10; re-read them before changing the `X-GitHub-Api-Version` header. Source: https://docs.github.com/en/rest/repos/rules
- Repositories created after 2026-07-15 use the immutable OIDC `sub` format; role trusts written for the legacy format fail there. Source: https://docs.github.com/en/actions/reference/security/oidc
- Pinned SHAs (checkout v7.0.1, upload-artifact v7.0.2, download-artifact v8.0.2, configure-aws-credentials v6.3.0) were resolved on 2026-10-30; re-run `git ls-remote` before bumping. Source: https://github.com/actions/upload-artifact/releases

## Unverified (8)

| ID | Claim | Impact | Workaround |
|---|---|---|---|
| U1 | Behaviour of a workflow on a Free private repository that references `environment:` | a Free variant could fail or be silently ungated | do not reference `environment:` on Free; test in a scratch repository |
| U2 | Whether a workflow auto-creates a missing environment | an unconfigured environment might run without a branch policy | create environments first |
| U3 | Whether `deployment: false` jobs honour deployment branch policies, and the OIDC `sub` they get | PR read role trust may not match | test in a scratch repository |
| U4 | ECS CloudWatch-alarm rollback for `BLUE_GREEN`, `LINEAR`, `CANARY` strategies | false assurance of automatic rollback | use rolling updates with alarms, or a manual redeploy |
| U5 | Push rulesets on Pro private repositories | none for this design | not used |
| U6 | Fine-grained token permission names for environments, rulesets and deployments REST calls | automation tokens | use the documented classic scopes, owner admin |
| U7 | Automatic rollback for CloudFront, Vercel and Terraform | no native safety net | smoke step plus manual rollback |
| U8 | Introduction dates of `queue: max`, `deployment: false`, ECS native strategies | none for correctness | none |

## Irresolvable (0)

None. Every gap found has a follow-up path in the table above.

## Medium confidence (11)

| ID | Claim | Why medium | Check |
|---|---|---|---|
| M1 | Never-cancel rationale: cancelling leaves a half-shifted alias or partial apply | consequence inferred, cancel semantics documented | rehearse a cancel in `dev` |
| M2 | Role per environment as the blast-radius boundary | design inference over documented secret locking | review trust policies |
| M3 | Environment values resolve in the called reusable job, not the caller | reusable-workflow page not re-read for this unit | dry run on `dev` |
| M4 | `vercel deploy --prebuilt` combined with `--prod --skip-domain` | each flag documented, combination not shown | read the deploy options page |
| M5 | `gh` and `aws` CLIs preinstalled on `ubuntu-latest` | runner-images README not read | install explicitly |
| M6 | CodeDeploy chosen so rollback survives a dead runner | inferred from documented automatic rollback | ask the user |
| M7 | CloudFront staging distribution used to canary site content | documented for configuration, content use inferred | test on a non-prod distribution |
| M8 | Invalidation paired with the origin-path switch | invalidation API not read | read the invalidation page |
| M9 | Manual prod dispatch is an acceptable extra gate | user decision | ask the user |
| M10 | One concurrency group across sequential jobs of one run does not block | semantics documented per group, sequential case inferred | dry run `dev` |
| M11 | ECR command name for tag immutability | page names the behaviour, not the command | `aws ecr help` |

## Coverage limits (5)

| ID | Limit |
|---|---|
| L1 | Several docs.github.com "who can use this feature" boxes did not render; the plan statements were read from the GitHub docs source reusables, which are GitHub's own source |
| L2 | ECS canary and deployment-types developer-guide pages rendered empty; only the API reference was used for strategy values |
| L3 | The HashiCorp workspace best-practices page failed to load; the well-architected page was used instead |
| L4 | GitHub docs examples show older action majors; this skill uses only the pinned versions from the family facts |
| L5 | The user's GitHub plan is unknown, so the skill asks first and documents Pro, Team and Free |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | approval-models.md Free variant | U1 |
| (unverified) | approval-models.md default section (auto-creation) | U2 |
| (unverified) | SKILL.md Ask First (PR environment); isolation-matrix.md notes | U3 |
| (unverified) | SKILL.md Ask First (ECS rollback); progressive-delivery.md table and ECS section | U4 |
| (unverified) | isolation-matrix.md plan table (push rulesets) | U5 |
| (unverified) | approval-models.md default section (token permissions) | U6 |
| (unverified) | progressive-delivery.md table (CloudFront, Vercel, Terraform) | U7 |
| (unverified) | this file, Version-lifetime risk | U8 |
| (medium confidence) | never-do-patterns.md N3 | M1 |
| (medium confidence) | isolation-matrix.md notes | M2 |
| (medium confidence) | reusable-workflows.md contract rules | M3 |
| (medium confidence) | always-do-patterns.md Vercel section | M4 |
| (medium confidence) | reusable-workflows.md notes | M5 |
| (medium confidence) | SKILL.md Ask First (Lambda mechanism); progressive-delivery.md Lambda section | M6 |
| (medium confidence) | SKILL.md Ask First (S3 + CloudFront); progressive-delivery.md S3 section | M7 |
| (medium confidence) | progressive-delivery.md S3 section (invalidation) | M8 |
| (medium confidence) | SKILL.md Ask First (approval model); approval-models.md manual dispatch | M9 |
| (medium confidence) | reusable-workflows.md notes (concurrency) | M10 |
| (medium confidence) | always-do-patterns.md immutable image tags | M11 |

## Source Bibliography

All fetched 2026-10-30. GitHub and AWS pages are undated; Vercel pages carry `last_updated` dates.

**docs.github.com**
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments
- https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- https://docs.github.com/en/actions/reference/security/oidc
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- https://docs.github.com/en/get-started/learning-about-github/githubs-plans
- https://docs.github.com/en/rest/deployments/deployments
- https://docs.github.com/en/rest/deployments/environments
- https://docs.github.com/en/rest/deployments/branch-policies
- https://docs.github.com/en/rest/repos/rules
- https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/repo-rules.md

**AWS**
- https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html
- https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html
- https://docs.aws.amazon.com/codedeploy/latest/userguide/deployment-configurations.html
- https://docs.aws.amazon.com/codedeploy/latest/userguide/deployments-rollback-and-redeploy.html
- https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentConfiguration.html
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-alarm-failure.html
- https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html
- https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html
- https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment-quotas-considerations.html

**Vercel and HashiCorp**
- https://vercel.com/docs/cli/promote (last_updated 2026-07-15)
- https://vercel.com/docs/cli/rollback (last_updated 2026-03-17)
- https://vercel.com/docs/instant-rollback (last_updated 2026-07-07)
- https://vercel.com/docs/deployments/promoting-a-deployment (last_updated 2026-06-26)
- https://vercel.com/docs/cli/deploying-from-cli (last_updated 2026-09-08)
- https://developer.hashicorp.com/well-architected-framework/operational-excellence/operational-excellence-workspaces-projects

**Releases**
- https://github.com/actions/checkout/releases
- https://github.com/actions/upload-artifact/releases
- https://github.com/actions/download-artifact/releases
- https://github.com/aws-actions/configure-aws-credentials/releases
- SHA verification: `git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>`
