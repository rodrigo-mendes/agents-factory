# Isolation matrix and plan availability

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Default design: GitHub Pro or Team private repository (family rule 16).

## Isolation matrix

One column per stage, one row per isolation dimension. A compromised stage must not reach the next column.

| Dimension | PR (`ci-<app>.yml`) | `dev` | `stage` | `prod` |
|---|---|---|---|---|
| Trigger | `pull_request`; never writes to cloud | push to `main` | `needs` dev, smoke passed | `needs` stage, smoke passed |
| Identity | role `<app>-dev-pr-read`, trust `environment:dev-pr` | `<app>-dev-deploy`, trust `environment:dev` | `<app>-stage-deploy`, trust `environment:stage` | `<app>-prod-deploy`, trust `environment:prod` |
| Environment | `dev-pr`, all branches, read-only values | `dev`, branch policy `main` | `stage`, branch policy `main` | `prod`, branch policy `main` |
| State | read-only on dev state | `dev/<component>.tfstate` | `stage/<component>.tfstate` | `prod/<component>.tfstate` |
| Artifact | built for checks, never deployed | built once on `main`, hash recorded | same hash, recomputed | same hash, recomputed |
| Exposure | none | all at once (weight 0) | canary weight 0.10 | canary 0.10, then complete |
| Supply chain | actions pinned by SHA, required check `ci-gate` | pinned SHAs, retention 30 | same | same, plus scanner gate before merge |

Notes:
- The OIDC `sub` for a job with `environment: prod` is `repo:ORG/REPO:environment:prod` in the legacy format and `repo:ORG@ORG-ID/REPO@REPO-ID:environment:prod` for repositories created after 2026-07-15. The role trust is owned by `federating-github-actions-aws-oidc`. Source: https://docs.github.com/en/actions/reference/security/oidc
- The PR row follows family rule 13: branch code runs during plan and build, so it never receives deploy credentials. `deployment: false` keeps PR jobs out of deployment history; its effect on branch policies and on the `sub` claim is (unverified).
- Role-per-environment as the blast-radius boundary is a design inference (medium confidence); the GitHub side (secrets locked until the environment rules pass) is documented. Source: https://docs.github.com/en/actions/concepts/workflows-and-actions/deployment-environments
- Scanner and attestation rules belong to `securing-supply-chain-github-actions`; attestations on private repositories need GitHub Enterprise Cloud (upgrade path).

## Plan availability for private repositories

Read from docs.github.com and the GitHub docs source on 2026-10-30.

| Feature | Free | Pro | Team |
|---|---|---|---|
| Create environments | no | yes | yes |
| Environment secrets and variables | no | yes | yes |
| Deployment branch and tag policy | no | yes | yes |
| Required reviewers, wait timer, custom protection rules | no | no | no |
| Admin bypass setting for environment rules | no | no | no |
| Protected branches and rulesets | no | yes | yes |
| Ruleset `evaluate` enforcement | no | no | no |
| Bypass actors on branch rules | not applicable | no (user-owned) | yes (organization) |
| Required PR reviewers and code owners | no | yes | yes |
| Push rulesets | no | (unverified) | yes |

Sources: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments ; https://docs.github.com/en/get-started/learning-about-github/githubs-plans ; https://raw.githubusercontent.com/github/docs/main/data/reusables/gated-features/repo-rules.md

Consequence: on Pro or Team an environment scopes secrets and restricts the deploying branch, but cannot pause a run for a human. The human gate sits before `main`.
