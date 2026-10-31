---
name: federating-github-actions-aws-oidc
description: "Keyless AWS login from GitHub Actions with OIDC and configure-aws-credentials v6.3.0: IAM provider, trust policies by GitHub plan, PR read role, immutable sub, login composite action. Use when a workflow must assume an AWS role without stored access keys."
---

# GitHub Actions to AWS with OIDC (configure-aws-credentials v6.3.0)

> Version lock: every claim applies to `aws-actions/configure-aws-credentials` **v6.3.0** on GitHub.com Actions (Free, Pro, Team with private repositories). Research date **2026-10-30**.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: only the AWS login and the IAM trust. HCL for the provider and roles belongs to `provisioning-aws-iam-v6`; reusable-workflow mechanics to `composing-github-actions-pipelines`; SHA pinning and injection-safe scripting to `automating-github-repos-with-actions`; OCI login to `federating-github-actions-oci`.
> Provenance: the dated research file for this unit under the factory workspace; this skill never reads it at run time.

## Version Context

| Item | Value | Source (fetched 2026-10-30) |
|---|---|---|
| `aws-actions/configure-aws-credentials` | v6.3.0 (2026-09-15) = `e1253824e5c10ff9df46874f81ed3ec929e19cfd` | https://github.com/aws-actions/configure-aws-credentials/releases |
| v6.0.0 breaking change | node24; runner v2.327.1 or later | https://github.com/aws-actions/configure-aws-credentials/releases?page=2 |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` | https://github.com/actions/checkout/releases |
| OIDC issuer and audience | `https://token.actions.githubusercontent.com`, `sts.amazonaws.com` | https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws |
| Immutable `sub` | repositories created after 2026-07-15 | https://docs.github.com/en/actions/reference/security/oidc |
| STS session length | 900 s up to the role maximum; 3600 s when chained | https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html |

**Version-lifetime risk** (as of 2026-10-30; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- The action line moves quickly (v6.0.0 to v6.3.0 in about seven months); re-resolve the SHA with `git ls-remote` before every bump.
- The immutable `sub` default changes which trust policies work for new repositories.
- GitHub and AWS disagree on whether AWS evaluates `job_workflow_ref` directly.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Verification Loop](#verification-loop)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Trust policies by plan](./blueprints/trust-policies-by-plan.md)
- [Login composite action and workflows](./blueprints/login-composite-action.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

Shape: one IAM OIDC provider per AWS account; per app and environment one `gha-<app>-<env>-deploy` role and one `gha-<app>-<env>-pr-read` role; the composite action `./.github/actions/cloud/login-aws` wraps the official action. Default plan model is Pro/Team private repositories (family decision); Free is a documented weaker variant.

### ✅ Always Do

- **Create the IAM OIDC provider for `https://token.actions.githubusercontent.com` with audience `sts.amazonaws.com`** ([IAM provider page](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)).
- **Leave the thumbprint out for GitHub**; AWS verifies the JWKS endpoint with its trusted root CAs ([IAM provider page](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)).
- **Pin `aud` with `StringEquals` in every trust policy** ([GitHub guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)).
- **Pin an exact `sub` with `StringEquals`**, because the issuer is shared by all GitHub customers ([IAM GitHub role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html)).
- **Write the `sub` in the format GitHub emits for that job shape**: environment, then pull_request, then ref ([OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)).
- **Use the immutable `sub` form for repositories created after 2026-07-15** ([OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)).
- **Give `id-token: write` only to the job that logs in** (the job that runs the login composite, never a build, test or plan-only job), with `contents: read` ([OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)).
- **Pin the action to the v6.3.0 SHA from the facts table** (family decision; [releases](https://github.com/aws-actions/configure-aws-credentials/releases)).
- **Create one deploy role per environment and a separate PR-only read role** (family decision; [IAM GitHub role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html)). Store the ARNs as variables `AWS_DEPLOY_ROLE_ARN` (environment `<env>`) and `AWS_PR_ROLE_ARN` (environment `<env>-pr`), read inside the job that declares the environment.
- **Keep `role-duration-seconds` between 900 and the role's maximum session duration** ([STS API](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html)).
- **Set `role-session-name` to a value that carries the run id** ([STS API](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html)).
- **Set `allowed-account-ids` when calling the action directly** ([action.yml](https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml)).
- **Keep `output-credentials` at its default `false`** ([action.yml](https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml)).
- **Run v6 only on runners v2.327.1 or later** ([releases](https://github.com/aws-actions/configure-aws-credentials/releases?page=2)).

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| GitHub plan | Pro/Team private: environments, secrets, branch policy (default); Free private: no environments, so roles trust `ref:refs/heads/main` and dev and prod cannot be told apart by `sub` | "Which GitHub plan owns this private repository, and is it private?" |
| PR read role form | `environment:<env>-pr` (Pro/Team) vs `:pull_request` sub (all plans); branch-policy evaluation for PR events (unverified) | "Is the repository on Pro or Team?" |
| Customizing the `sub` template | Needed to enforce `job_workflow_ref`; breaks every trust policy that uses the default; availability on Free private (unverified) | "May the repository or org `sub` template change?" |
| Reusable-workflow restriction | `sub` template with `job_workflow_ref` is documented by both vendors; a direct condition key is (medium confidence) | "Must the role be limited to one called workflow?" |
| Hub account and role chaining | Chaining caps sessions at 1 h and needs `sts:TagSession` trust; a provider per account avoids chaining | "One AWS account per environment, or a mandated hub account?" |
| Account IDs in public logs | `mask-aws-account-id: true` hides them; default shows them | "Are account IDs sensitive for this org?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Trust a deploy role with `StringLike` `repo:ORG/*` or `repo:ORG/REPO:*` ([IAM GitHub role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html)) | `StringEquals` with the exact environment or ref `sub` |
| Give a PR job `environment: prod` ([OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)) | PR job on `<env>-pr` or no environment, with the PR read role |
| Store `aws-access-key-id` secrets for CI ([README](https://github.com/aws-actions/configure-aws-credentials/blob/v6.3.0/README.md)) | `role-to-assume` with `id-token: write` |
| Use `pull_request_target` to get a cloud login on fork PRs ([events reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)) | `pull_request` with the login skipped for forks |
| Set `id-token: write` at workflow level ([OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)) | `permissions: {}` and job-level grant |
| Request more than 3600 s on a chained role ([IAM terms](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html)) | `role-duration-seconds: 3600` or less |
| Use `ForAllValues:` in an Allow statement ([README](https://github.com/aws-actions/configure-aws-credentials/blob/v6.3.0/README.md)) | `StringEquals` or `StringLike` |
| Copy the action SHA or major from a GitHub doc example ([releases](https://github.com/aws-actions/configure-aws-credentials/releases)) | The SHA shown in Version Context |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Job shape to `sub` | environment job: `environment:<env>`; PR job without environment: `pull_request`; otherwise `ref:refs/heads/<branch>` | https://docs.github.com/en/actions/reference/security/oidc |
| IAM rule for shared providers | trust must evaluate `sub` or `job_workflow_ref`; wildcard-only value fails with `MalformedPolicyDocument` | https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_secure-by-default.html |
| Session name | 2 to 64 characters, pattern `[\w+=,.@-]*` | https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html |
| Retries | 12 attempts by default (`retry-max-attempts`) | https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml |
| Providers per account | one per issuer URL, same account as the trusting role | https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html |

## Verification Loop

Run offline from the repository root; adapt file names to your layout.

```bash
# 1. every login step is pinned to the v6.3.0 SHA
grep -rn "configure-aws-credentials@" ./.github
# Expected: every hit ends in e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0

# 2. no stored keys and no pull_request_target next to a login
grep -rn "aws-access-key-id" ./.github
# Expected: no output
grep -rln "pull_request_target" ./.github/workflows
# Expected: no file that also calls login-aws

# 3. trust policy pins an exact, non-wildcard sub
jq -e '.Statement[].Condition.StringEquals["token.actions.githubusercontent.com:sub"]' trust-prod.json
# Expected: exit 0 and one string with no * or ?
```

Live check inside a job after login (no offline emulator for the web-identity call, (unverified)): `aws sts get-caller-identity` shows `assumed-role/<ROLE>/gha-<run_id>-<attempt>`. Run the first live login in a non-production account.

## External Resources

All fetched 2026-10-30.

- [GitHub: OIDC in AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
- [AWS: role for GitHub OIDC](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html)
- [Action README v6.3.0](https://github.com/aws-actions/configure-aws-credentials/blob/v6.3.0/README.md)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
