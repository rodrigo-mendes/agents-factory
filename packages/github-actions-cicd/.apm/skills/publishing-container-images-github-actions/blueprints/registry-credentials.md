# Registry credentials per GitHub plan

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Applies family rule 16: the default is GitHub Pro or Team private repositories; the Free private variant is documented as weaker. Ask the plan before generating the publish job.

Contents: [Plan facts](#plan-facts), [Default: Pro or Team private](#default-pro-or-team-private), [Free private variant](#free-private-variant), [Upgrade path](#upgrade-path).

## Plan facts

- Environment secrets and variables, and deployment branch policies, exist for private repositories on Pro, Team or Enterprise; on Free only public repositories (F25).
- Required reviewers, wait timers and custom protection rules on Free, Pro and Team are public-repository only (F25).
- Protected branches and required pull request reviewers in private repositories are Pro and Team features (F39).
- A job cannot read environment secrets until the environment rules pass.

Sources: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments; https://docs.github.com/en/get-started/learning-about-github/githubs-plans (read 2026-10-30)

## Default: Pro or Team private

| Registry | Credential | Where it lives | Notes |
|---|---|---|---|
| GHCR | `GITHUB_TOKEN` with `packages: write` on the publishing job | no stored secret | storage and bandwidth are currently free; quotas apply to private packages |
| ECR | OIDC role through `aws-actions/configure-aws-credentials` (F3) then `amazon-ecr-login` (F32) | role ARN as environment variable of `<env>-publish` | role trust is scoped to `environment:<env>-publish`; format per F26 in `federating-github-actions-aws-oidc` |
| OCIR | username `<tenancy-namespace>/<user>` and auth token | environment secrets of `<env>-publish` with deployment branch policy `main` | one push-only OCI user limited to the registry compartment |

Approval is the pull request review before merge to protected `main`; no required-reviewers gate is promised on a private repository (family rule 16).

PR builds use `push: false` and no login. A PR job that must pull a private base image uses a separate PR-only read role or environment `<env>-pr`, never the `<env>-publish` credentials (family rule 13).

Sources: https://github.com/docker/login-action/blob/v4.7.0/README.md; https://github.com/aws-actions/amazon-ecr-login/blob/v2.1.7/README.md; https://docs.github.com/en/billing/concepts/product-billing/github-packages (read 2026-10-30)

## Free private variant

Weaker by design; state it to the user, never apply it silently.

| Registry | Layout | Risk accepted |
|---|---|---|
| GHCR | same as the default; no stored secret | none beyond the default |
| ECR | OIDC role whose trust names `ref:refs/heads/main`; role ARN as repository variable or literal (medium confidence) | without protected branches (F39) any user with write access can push to `main` or open a workflow on a branch that the trust does not match; scope the role to push-only on one repository |
| OCIR | auth token as a least-privilege repository secret | repository secrets are readable by any non-fork workflow run on any branch; no environment branch policy exists (family rule 10 cannot be met) |

- Recommend GHCR or ECR on Free private repositories (no stored static secret), or an upgrade to Pro or Team for OCIR.
- OIDC `sub` formats and environment scoping on Free private repositories are (unverified) here; the format is owned by `federating-github-actions-aws-oidc` and, for repositories created after 2026-07-15, follows F26.
- The OCIR mitigation (push-only user in a dedicated compartment plus a branch-protected workflow) is an inference, (medium confidence).

Sources: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments; https://docs.github.com/en/actions/reference/security/oidc (read 2026-10-30)

## OCIR credentials are static

No page read documents an OIDC or token-exchange login for the registry itself; F20 and F21 cover OCI API calls, and their use for OCIR is (unverified). Keep the auth token rotation outside the workflow and never echo it. Federation for OCI deploys: `federating-github-actions-oci`.

## Upgrade path

Required reviewers, wait timers and artifact attestations (F33) are available for public repositories or GitHub Enterprise Cloud. Add them when the repository moves there; the workflow does not change except for the attestation step in [attestations](./attestations-and-verification.md#upgrade-path-artifact-attestations).
