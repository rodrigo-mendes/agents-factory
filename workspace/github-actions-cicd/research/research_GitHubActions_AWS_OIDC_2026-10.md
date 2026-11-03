# Research: GitHub Actions OIDC to AWS IAM with aws-actions/configure-aws-credentials v6.3.0

> Unit: `federating-github-actions-aws-oidc`. Source item: "need: keyless AWS login". Spec:
> `researching-technical-frameworks` (default depth = exhaustive, MAX_ITERATIONS = 5). Brief:
> `workspace/github-actions-cicd/execution-1/briefs/P4-research-federating-github-actions-aws-oidc.md`.
> Every page was read on 2026-10-30. Family facts (F1-F24) and family rules (1-16) from
> `workspace/github-actions-cicd/_family_facts.md` / `_family_rules.md` are applied as given.
> No agents or investigators were spawned; every page was fetched by this researcher.
>
> Section-order note: the brief requires the file to END with `## Source Bibliography`, so that
> section moves from its template position to the end, after `## Pages read`. All 15 template
> sections are present.
>
> Version note: docs.github.com and docs.aws.amazon.com pages carry no version number or publish
> date. They are the current github.com (Free/Pro/Team/Enterprise Cloud) and current AWS pages,
> and the read date (2026-10-30) is the date recorded for them. The action is pinned to the
> release tag v6.3.0 and the README/action.yml were read at that tag.

## Metadata

```yaml
Full_Name: GitHub Actions OpenID Connect federation into AWS IAM (AssumeRoleWithWebIdentity) via aws-actions/configure-aws-credentials
Target_Version: aws-actions/configure-aws-credentials v6.3.0 = e1253824e5c10ff9df46874f81ed3ec929e19cfd (F3)
Release_Date: v6.3.0 on 2026-09-15 (F3; release header 15 Sep, changelog date 2026-09-11)
Support_Status: Active; v6.3.0 is marked "Latest" on the releases page (2026-10-30)
Primary_Docs:
  - https://docs.github.com/en/actions/reference/security/oidc
  - https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws
  - https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html
Official_Repo: https://github.com/aws-actions/configure-aws-credentials
Integration_Partners: GitHub environments (plan-dependent), reusable workflows (job_workflow_ref), AWS STS, IAM OIDC identity provider
Target_Plan: GitHub Team / Pro / Free with PRIVATE repositories (family rule 16)
Research_Date: 2026-10-30
Domain_Complexity: Complex
Research_Depth: exhaustive (default)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 3 of 5
Triangulated_Count: 7
Unverified_Count: 7
Irresolvable_Count: 0
Research_Quality_Score: 89%   # ~65 claims, 7 unverified
```

## Executive Summary

GitHub Actions can request a short-lived OpenID Connect (OIDC) JSON Web Token from the issuer
`https://token.actions.githubusercontent.com` when the job has `permissions: id-token: write`.
AWS STS accepts that token through `AssumeRoleWithWebIdentity` and returns temporary credentials
for an IAM role whose trust policy names the IAM OIDC identity provider for that issuer. No AWS
access key is stored in GitHub. The official action `aws-actions/configure-aws-credentials`
v6.3.0 (F3) does this when only `role-to-assume` and `aws-region` are given and the job holds the
`id-token: write` permission. Its README marks GitHub OIDC as the "Recommended" authentication path
(README v6.3.0, read 2026-10-30).

What changed for the target version: v6.0.0 (04 Feb 2026) has one breaking change, "Update action
to use node24", which requires GitHub Actions runner v2.327.1 or later. v6.3.0's `action.yml`
declares `runs.using: node24`. The v6 line added (v6.1.0) AWS profiles and a skip-cleanup option,
(v6.2.0) custom session tags, additional default session tags, regex validation of
`role-session-name`, custom STS endpoints, more retry logic, (v6.2.1) enforcement of
`allowed-account-ids` on all auth paths, and (v6.3.0) the `translate-env-variables` option. On the
GitHub side, repositories created on or after 15 July 2026 (or opted in) emit an immutable `sub`
claim that includes numeric owner and repository IDs (`repo:OWNER@OWNER-ID/REPO@REPO-ID:...`). A
trust policy written only for the name form then fails with "Not authorized to perform
sts:AssumeRoleWithWebIdentity" (README v6.3.0; GitHub OIDC reference). On the AWS side, the IAM OIDC
provider thumbprint is no longer needed for GitHub. AWS verifies the JWKS endpoint with its trusted
root CA library and uses thumbprints only as a fallback. IAM also rejects any trust policy for the
GitHub provider that does not evaluate `token.actions.githubusercontent.com:sub` (or
`job_workflow_ref`), or whose value is only a wildcard.

The three critical patterns are: (1) every role trust policy pins
`token.actions.githubusercontent.com:aud = sts.amazonaws.com` and an exact
`token.actions.githubusercontent.com:sub` with `StringEquals`. For deployable roles, the `sub` is
the environment form `repo:ORG/REPO:environment:<env>`, protected by an environment deployment
branch policy. (2) There is one role per stage x environment, and pull-request jobs use a separate
PR-only read role (family rule 13). Its trust pins the `<env>-pr` environment sub or the
`:pull_request` sub, and never trusts a deployable environment. (3) `id-token: write` goes only on
the job that logs in, the action is pinned by SHA (F3), and sessions stay short (900-3600 s; role
chaining is capped at one hour). Tier = Complex: this covers authentication, cross-tenant shared
identity-provider risk, plan-dependent environment features, and fork and pull-request trust
boundaries.

## Architectural Guardrails

> Confidence legend: High = official page read in full, Triangulated where 2+ official sources
> agree | (medium confidence) = one source, partly read, or inferred from two sources | (unverified)
> = no official confirmation found.

### ✅ Mandatory Patterns

**A1. Create the IAM OIDC identity provider for `https://token.actions.githubusercontent.com` with audience `sts.amazonaws.com`; do not maintain a thumbprint**
> Confidence: High | [✓✓ Triangulated | IAM create-OIDC-provider page (2026-10-30) + CLI create-open-id-connect-provider reference v2.39.2 (2026-10-30) + configure-aws-credentials README v6.3.0 (2026-10-30)]
- Why: GitHub states the provider URL is `https://token.actions.githubusercontent.com` and the audience is `sts.amazonaws.com` "if you are using the official action". AWS: "AWS secures communication with OIDC identity providers (IdPs) using our library of trusted root certificate authorities (CAs) to verify the JSON Web Key Set (JWKS) endpoint's TLS certificate. If your OIDC IdP relies on a certificate that is not signed by one of these trusted CAs, only then we secure communication using the thumbprints". The CLI says `--thumbprint-list` "is optional". The action README says the thumbprint is no longer necessary and is ignored if specified. One provider per URL per account ("each IAM OIDC identity provider must use a unique URL"). The provider must be in the same account as the role that trusts it.
- Code:
  ```bash
  # Representative — adapt to your environment (AWS CLI v2.39.2 reference)
  aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com
  # Expected: {"OpenIDConnectProviderArn": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"}
  ```
- Note: the HCL for this provider and its roles belongs to `provisioning-aws-iam-v6` (family rule 12). This research only states the facts that HCL must encode.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html (2026-10-30); https://docs.aws.amazon.com/cli/latest/reference/iam/create-open-id-connect-provider.html (2026-10-30); https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws (2026-10-30)

**A2. Every trust policy pins `aud` and an exact `sub` with `StringEquals`**
> Confidence: High | [✓✓ Triangulated | IAM "Configuring a role for GitHub OIDC identity provider" (2026-10-30) + GitHub oidc-in-aws (2026-10-30) + action README v6.3.0 (2026-10-30)]
- Why: "If you do not limit the condition key `token.actions.githubusercontent.com:sub` to a specific organization or repository, then GitHub Actions from organizations or repositories outside of your control are able to assume roles". The GitHub issuer is shared by every GitHub customer. IAM lists it as a shared provider whose required claim is `sub` or `job_workflow_ref`, and it fails role creation or update with `MalformedPolicyDocument` when the claim is not evaluated. The README recommends `StringEquals` on both `aud` and `sub`.
- Code:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:<ORG>/<REPO>:environment:prod"
        }
      }
    }]
  }
  ```
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html#idp_oidc_Create_GitHub (2026-10-30); https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_secure-by-default.html (2026-10-30)

**A3. Write the `sub` value in the exact format GitHub emits for that job (environment > pull_request > ref)**
> Confidence: High | [✓✓ Triangulated | GitHub OIDC reference (2026-10-30) + GitHub oidc-in-aws (2026-10-30)]
- Why: the default `sub` depends on the job. A job that references an environment gets `repo:ORG/REPO:environment:ENV`. A `pull_request` job gets `repo:ORG/REPO:pull_request` "only if the job doesn't reference an environment". Otherwise the job gets `repo:ORG/REPO:ref:refs/heads/BRANCH` or `repo:ORG/REPO:ref:refs/tags/TAG`. "Colons within metadata values are replaced with `%3A`." So a PR job that references an environment does NOT get the `:pull_request` sub.

  | Job shape | `sub` (name form) |
  |---|---|
  | references `environment: prod` (any event) | `repo:ORG/REPO:environment:prod` |
  | `pull_request`, no environment | `repo:ORG/REPO:pull_request` |
  | push/dispatch on branch, no environment | `repo:ORG/REPO:ref:refs/heads/main` |
  | push on tag, no environment | `repo:ORG/REPO:ref:refs/tags/v1.2.3` |
- Source: https://docs.github.com/en/actions/reference/security/oidc (2026-10-30)

**A4. Use the immutable `sub` form for repositories created on or after 15 July 2026 (or opted in)**
> Confidence: High | [✓✓ Triangulated | GitHub OIDC reference + GitHub oidc-in-aws + action README v6.3.0, all 2026-10-30]
- Why: those repositories emit `repo:OWNER@OWNER-ID/REPO@REPO-ID:ref:refs/heads/BRANCH`. A name-only trust policy then fails with "Not authorized to perform sts:AssumeRoleWithWebIdentity". The org template API exposes `use_immutable_subject` for opting in. The form is not available on GitHub Enterprise Server.
- Code:
  ```json
  "token.actions.githubusercontent.com:sub": "repo:<ORG>@<ORG_ID>/<REPO>@<REPO_ID>:ref:refs/heads/main"
  ```
- Environment variant: `repo:<ORG>@<ORG_ID>/<REPO>@<REPO_ID>:environment:prod` (medium confidence). The README says environment workflows add an `environment:` stanza, but neither page prints the full immutable environment string.
- Source: https://docs.github.com/en/actions/reference/security/oidc (2026-10-30); https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/README.md (2026-10-30); https://docs.github.com/en/rest/actions/oidc (2026-10-30)

**A5. Grant `id-token: write` only on the job that logs in, with `contents: read`**
> Confidence: High | [✓✓ Triangulated | GitHub OIDC reference + workflow-syntax permissions + oidc-in-aws, all 2026-10-30]
- Why: "The job or workflow needs `id-token: write`". The permission "only enables fetching the OIDC token and does not grant write access to other resources". It can be set at workflow or job level. Family rule 7 requires job level, only on the login job.
- Code:
  ```yaml
  # .github/workflows/cd-orders.yml  (family rule 5 naming)
  permissions: {}                    # nothing at workflow level
  jobs:
    deploy:
      runs-on: ubuntu-latest
      environment: prod
      permissions:
        id-token: write              # this job only
        contents: read
      steps:
        - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1 (F10)
        - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0 (F3)
          with:
            role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
            aws-region: ${{ vars.AWS_REGION }}
            role-session-name: gha-${{ github.run_id }}-${{ github.run_attempt }}
            role-duration-seconds: 900
  ```
- Source: https://docs.github.com/en/actions/reference/security/oidc (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30, chars 0-100000 of 235839)

**A6. Pin the action to F3's SHA; never copy the SHA or major from a doc example**
> Confidence: High (F3 + family rules 4 and 11)
- Why: GitHub's oidc-in-aws page shows `aws-actions/configure-aws-credentials@e3dd6a429d7300a6a4c196c26e071d42e0343502` and `actions/checkout@v6`. The README v6.3.0 shows `@v6.2.4` and `@v6`. None of these is the target (v6.3.0 = `e1253824e5c10ff9df46874f81ed3ec929e19cfd`, F3). This is the lesson-1 trap from earlier batches.
- Code: `uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0`. For SHA-pinning rationale, link `automating-github-repos-with-actions` (family rule 4).
- Source: F3 (https://github.com/aws-actions/configure-aws-credentials/releases, 2026-10-30)

**A7. One role per stage x environment; the PR stage uses a PR-only read role**
> Confidence: High for the mechanism [✓✓ Triangulated | IAM GitHub role guidance + GitHub OIDC reference]; the policy itself is family rule 13 (DEC-008)
- Why: AWS recommends limiting `sub` "to a specific set of repositories or branches". A role trusts exactly one `sub`, and the `sub` differs by environment and by event (A3). Family rule 13 forbids PR jobs from using deployable-environment credentials because "branch code runs during plan/build".

  | Role (example name) | Permissions | Trusted `sub` (Team/Pro private) | Trusted `sub` (Free private, no environments) |
  |---|---|---|---|
  | `gha-<app>-<env>-pr-read` | read-only (plan/diff) | `repo:ORG/REPO:environment:<env>-pr` | `repo:ORG/REPO:pull_request` |
  | `gha-<app>-<env>-deploy` | deploy/apply for `<env>` | `repo:ORG/REPO:environment:<env>` | `repo:ORG/REPO:ref:refs/heads/main` (see C1 caveat) |
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html (2026-10-30); https://docs.github.com/en/actions/reference/security/oidc (2026-10-30)

**A8. Keep sessions short: `role-duration-seconds` between 900 and the role's MaxSessionDuration; default 3600**
> Confidence: High | [✓✓ Triangulated | STS AssumeRoleWithWebIdentity API (2026-10-30) + README v6.3.0 (2026-10-30)]
- Why: STS: `DurationSeconds` "can range from 900 seconds (15 minutes) up to the maximum session duration setting for the role. This setting can have a value from 1 hour to 12 hours. If you specify a value higher than this setting, the operation fails." The default is 3600. The README states the same 900-43200 range and the 1-hour default.
- Source: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html (2026-10-30)

**A9. Set a traceable `role-session-name` that matches the STS pattern**
> Confidence: High (STS API reference); action-side regex added in v6.2.0 (release notes), exact regex (unverified)
- Why: `RoleSessionName` must be 2-64 chars matching `[\w+=,.@-]*`. It is part of the assumed-role ARN and "administrators can view this field in AWS CloudTrail logs". The action default is `GitHubActions`, which is the same for every run. `gha-${{ github.run_id }}-${{ github.run_attempt }}` fits the pattern and ties CloudTrail entries to a run.
- Source: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html (2026-10-30); https://github.com/aws-actions/configure-aws-credentials/releases (v6.2.0 "add regex validation to role-session-name", 2026-10-30)

**A10. Fail closed on the wrong account with `allowed-account-ids`**
> Confidence: High (single source: README + action.yml v6.3.0; v6.2.1 release "enforce allowed-account-ids on all auth paths")
- Why: the input takes comma-delimited expected account IDs and the action fails if credentials belong to another account. This catches a role ARN variable pointing at the wrong account.
- Source: https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml (2026-10-30)

### ⚠️ Conditional Patterns

**C1. Approval and isolation mechanism by GitHub plan (target: Team / Pro / Free, private repos)**
> Confidence: High (plan statements) | design default = family rule 16
- Options and availability for PRIVATE repositories:

  | Feature | Free (private) | Pro / Team (private) | Source |
  |---|---|---|---|
  | Configure environments at all | No ("Users with GitHub Free plans can only configure environments for public repositories") | Yes | manage-environments |
  | Environment secrets | No | Yes | deployments-and-environments |
  | Environment variables | No (public only) | Yes | deployments-and-environments |
  | Deployment branches and tags | No (public only) | Yes | deployments-and-environments |
  | Required reviewers | No | No ("only available for public repositories") | deployments-and-environments |
  | Wait timer | No | No | deployments-and-environments |
  | Custom deployment protection rules | No | No | deployments-and-environments |

- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |---|---|---|---|
  | A. Pro/Team: environment `prod` with deployment branch policy `main`; deploy role trusts `environment:prod`; human approval = required PR review before merge to protected `main` (or a `workflow_dispatch` apply run from `main`) | Strong sub isolation per environment; no reviewer feature needed | Approval is upstream (PR review), not at job time | Default for this family (rule 16) |
  | B. Free private: no environments; deploy role trusts `ref:refs/heads/main`; PR role trusts `:pull_request` | Works on Free | Every job running on `main` gets the same `sub`, so dev and prod cannot be separated by `sub` alone | Only when Pro/Team is unavailable; add C3 (custom sub with `job_workflow_ref`/`workflow`) or separate repos/accounts per env |
  | C. Public repo or Enterprise: add environment required reviewers | Approval at job time | Not available on target plan | Upgrade path, tagged as such |

- Why A is safe: the `sub` claim `environment:prod` is only minted for a job that references `prod`. AWS advises "Use deployment branches and tags to restrict which branches and tags can deploy to the environment". The mechanism by which a branch-policy violation blocks the job before the token is minted is (medium confidence). It is inferred from the manage-environments and AWS pages, and the exact runtime message was not read.
- Agent: "Ask user which plan the repository is on and whether it is private; pick A for Pro/Team, B (+C3) for Free."
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30); https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments (2026-10-30); https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html#idp_oidc_Create_GitHub (2026-10-30)

**C2. PR-only read role: `<env>-pr` environment vs plain `pull_request` sub**
> Confidence: High (sub formats) / (medium confidence) (branch-policy evaluation for PR events)
- Options: (a) PR job references environment `<env>-pr` (Pro/Team), so the sub is `environment:<env>-pr`. Its deployment branch policy must allow PR head branches; how GitHub evaluates the policy for `pull_request` events is (unverified). (b) PR job references no environment, so the sub is `:pull_request` (all plans).
- Tradeoffs: (a) allows environment-scoped variables for the PR role ARN and keeps one naming scheme. (b) is simpler and plan-independent, but any PR in the repo (from a same-repo branch) gets the role. Either way the role is read-only (family rule 13).
- Agent: "Ask whether the repo is on Pro/Team; default (b) on Free."
- Source: https://docs.github.com/en/actions/reference/security/oidc (2026-10-30)

**C3. Customize the subject claim template (repo or org)**
> Confidence: High (API) | GitHub OIDC reference + REST OIDC reference (2026-10-30)
- Options: `PUT /repos/{owner}/{repo}/actions/oidc/customization/sub` with `{"use_default": false, "include_claim_keys": [...]}` (scope `repo`); `PUT /orgs/{org}/actions/oidc/customization/sub` with `{"include_claim_keys": [...]}` (scope `write:org`). `{"use_default": true}` resets a repo. Example claim lists from GitHub: `["repo","context","job_workflow_ref"]`, `["repository_owner","repository_visibility"]`, `["environment","repository_owner"]`.
- Tradeoffs: this lets AWS (which only reads `aud`/`sub`/`amr`) enforce `job_workflow_ref` or `workflow`. But every existing trust policy must be updated first: "Create the matching condition in your cloud provider before customizing, or tokens may be rejected". Org templates apply to a repo only when the repo opts in (`use_default: false`). Whether customization is available on Free private repos is (unverified); no plan restriction is stated.
- Agent: "Ask before changing the template; it breaks every trust policy that uses the default format."
- Source: https://docs.github.com/en/rest/actions/oidc (2026-10-30); https://docs.github.com/en/actions/reference/security/oidc (2026-10-30)

**C4. Restrict to a reusable workflow (`job_workflow_ref`)**
> Confidence: (medium confidence). The two official sources disagree on whether AWS evaluates the claim directly.
- Facts: in a reusable workflow, standard claims describe the caller, and `job_workflow_ref` (e.g. `octo-org/octo-automation/.github/workflows/oidc.yml@refs/heads/main`) identifies the called workflow. GitHub: "Support for custom claims is currently available for Google Cloud Platform and HashiCorp Vault". For providers with only `aud`/`sub`, "use the API to customize the `sub` claim to include `job_workflow_ref`". GitHub oidc-in-aws: "Custom OIDC claims are unavailable in AWS". However, the AWS identity-provider-controls table lists `token.actions.githubusercontent.com:job_workflow_ref` as an accepted required claim for GitHub. The AWS condition-key reference lists only `amr`, `aud`, `email`, `oaud`, `sub` for default-implementation IdPs.
- Default: use the C3 route (`sub` template including `job_workflow_ref`) because both vendors document it. Treat a direct `job_workflow_ref` condition key as (unverified) until AWS documents it in the condition-key reference.
- Source: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows (2026-10-30); https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_secure-by-default.html (2026-10-30); https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_iam-condition-keys.html#condition-keys-wif (2026-10-30, OIDC section read)

**C5. `StringLike` with a wildcard on `sub`**
> Confidence: High
- Options: `StringLike` `repo:ORG/REPO:*` (any ref/event/environment of one repo) or `repo:ORG/*` (whole org). IAM rejects a value that is "solely a wildcard character (* and ?) or null".
- Tradeoffs: one role serves many refs, but a feature-branch or PR job can then assume a deploy role. AWS: "We recommend that you limit the condition key ... to a specific value". Use only for read-only roles, never for deploy roles (see F1).
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html#idp_oidc_Create_GitHub (2026-10-30)

**C6. Role chaining (cross-account hop) and session tags**
> Confidence: High | [IAM roles terms page + STS API + README v6.3.0]
- Facts: role chaining "limits your ... role session to a maximum of one hour", and a `DurationSeconds` above one hour fails. The action's second step uses `role-chaining: true`. The second role's trust must allow the first role to assume it and tag the session, unless `role-skip-session-tagging: true`. `transitive-tag-keys` forwards tags along the chain. With OIDC, the action "will use session tagging by default unless you are using OIDC", and "custom tags are not supported when using OIDC or web identity token authentication". With web identity, session tags come only from IdP token claims, and GitHub's documented claim list has no AWS tag claim. So the first OIDC hop carries no session tags (medium confidence, inferred from both lists). Tags appear only on chained `AssumeRole` hops.
- Tradeoffs: chaining centralizes the OIDC provider in one account but caps sessions at 1 h and adds `sts:TagSession` trust. A provider per target account avoids chaining. IAM requires the provider "in the same account as the role that trusts it".
- Agent: "Ask whether there is one AWS account per environment and whether a hub account is mandated."
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html (2026-10-30); https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html (2026-10-30); https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/README.md (2026-10-30)

**C7. Exposing credentials beyond the step (`output-credentials`, `output-env-credentials`, `aws-profile`)**
> Confidence: High (action.yml + README v6.3.0)
- Facts: `output-credentials` defaults to false ("When set, outputs fetched credentials as action step output"). `output-env-credentials` defaults to true, or false when `aws-profile` is set. Account IDs "are not considered secret" and are not masked by default; `mask-aws-account-id` hides them. A post-job step removes credentials unless `AWS_SKIP_CLEANUP_STEP` is "true". Whether the action masks the access key and secret with `setSecret` is (unverified). The README does not state it.
- Default: keep `output-credentials` off. Set `mask-aws-account-id: true` in public logs if account IDs are sensitive to the org.
- Source: https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml (2026-10-30)

### 🚫 Forbidden Patterns

**F1. Trusting a deploy role with a wildcard `sub` (or no `sub`)**
> Severity: Critical
> Confidence: High
- Why: GitHub's issuer is shared. Without a scoped `sub`, "GitHub Actions from organizations or repositories outside of your control are able to assume roles". With `repo:ORG/REPO:*`, any branch or PR job in the repo can deploy.
- Impact: cross-tenant or untrusted-branch takeover of the deploy role. IAM also rejects a missing or pure-wildcard `sub` with `MalformedPolicyDocument`.
- ❌ Wrong:
  ```json
  "StringLike": { "token.actions.githubusercontent.com:sub": "repo:my-org/*" }
  ```
- ✅ Correct:
  ```json
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
    "token.actions.githubusercontent.com:sub": "repo:my-org/orders:environment:prod"
  }
  ```
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html#idp_oidc_Create_GitHub (2026-10-30)

**F2. Storing long-lived AWS access keys in GitHub secrets for CI/CD**
> Severity: High
> Confidence: High [✓✓ GitHub oidc-in-aws + README v6.3.0 "Use temporary credentials when possible"]
- Why: OIDC removes the stored secret. The README recommends temporary credentials and rotation of any long-lived ones.
- Impact: a leaked key is valid until rotated, and it can be used outside GitHub.
- ❌ Wrong:
  ```yaml
  - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
    with:
      aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
      aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      aws-region: eu-west-1
  ```
- ✅ Correct:
  ```yaml
  permissions:
    id-token: write
    contents: read
  steps:
    - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
      with:
        role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
        aws-region: eu-west-1
  ```
- Source: https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/README.md (2026-10-30)

**F3. Giving a pull-request job a deployable environment or deploy role**
> Severity: Critical
> Confidence: High (family rule 13 + sub mechanics A3)
- Why: PR code is untrusted branch code. If the PR job references `environment: prod`, its token gets `sub ...:environment:prod` and can assume the deploy role. Any check that relied on the `:pull_request` sub is then bypassed.
- Impact: unreviewed branch code obtains production credentials during plan or build.
- ❌ Wrong:
  ```yaml
  # ci-orders.yml (on: pull_request)
  jobs:
    plan:
      environment: prod
      permissions: { id-token: write, contents: read }
  ```
- ✅ Correct:
  ```yaml
  # ci-orders.yml (on: pull_request)
  jobs:
    plan:
      environment: prod-pr            # Pro/Team; omit on Free -> sub = :pull_request
      permissions: { id-token: write, contents: read }
      steps:
        - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
          with:
            role-to-assume: ${{ vars.AWS_PR_READ_ROLE_ARN }}   # read-only role
            aws-region: ${{ vars.AWS_REGION }}
  ```
- Source: https://docs.github.com/en/actions/reference/security/oidc (2026-10-30); `_family_rules.md` rule 13

**F4. Using `pull_request_target` (or "Send write tokens to workflows from pull requests") to get OIDC on fork PRs**
> Severity: Critical
> Confidence: High (GitHub events + workflow-syntax + README)
- Why: for fork PRs "the permissions are adjusted to change any write permissions to read only" and secrets are not passed. `id-token: write` is a write scope, so a fork PR job cannot mint a token (medium confidence; inferred, as no page names id-token for forks explicitly). Working around this with `pull_request_target` runs in the base-repo context: "Running untrusted code on the `pull_request_target` trigger may lead to security vulnerabilities", including "granting unintended access to write privileges or secrets". The action README also warns about `pull_request_target`.
- Impact: fork authors execute code with cloud credentials.
- ❌ Wrong:
  ```yaml
  on: pull_request_target
  jobs:
    plan:
      permissions: { id-token: write }
      steps:
        - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
          with: { ref: ${{ github.event.pull_request.head.sha }} }
  ```
- ✅ Correct:
  ```yaml
  on: pull_request          # fork PRs run without cloud login; skip the AWS step for forks
  jobs:
    plan:
      if: github.event.pull_request.head.repo.full_name == github.repository
      permissions: { id-token: write, contents: read }
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30, partial)

**F5. `id-token: write` at workflow level for all jobs**
> Severity: Medium
> Confidence: High (family rule 7 + GitHub OIDC reference)
- Why: every job, including third-party tooling jobs, could mint a token whose `sub` matches your trust policy.
- Impact: wider blast radius for a compromised step.
- ❌ Wrong:
  ```yaml
  permissions:
    id-token: write
    contents: read
  jobs: { lint: ..., test: ..., deploy: ... }
  ```
- ✅ Correct:
  ```yaml
  permissions: {}
  jobs:
    deploy:
      permissions: { id-token: write, contents: read }
  ```
- Source: https://docs.github.com/en/actions/reference/security/oidc (2026-10-30)

**F6. Requesting more than one hour on a chained role, or above the role's MaxSessionDuration**
> Severity: Medium
> Confidence: High [✓✓ IAM roles page + STS API]
- Why: "if you assume a role using role chaining and provide a `DurationSeconds` parameter value greater than one hour, the operation fails". For the first hop, values above the role's maximum also fail.
- Impact: the login step fails at run time.
- ❌ Wrong:
  ```yaml
  with: { role-chaining: true, role-to-assume: arn:aws:iam::222222222222:role/deploy, role-duration-seconds: 7200 }
  ```
- ✅ Correct:
  ```yaml
  with: { role-chaining: true, role-to-assume: arn:aws:iam::222222222222:role/deploy, role-duration-seconds: 3600 }
  ```
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html (2026-10-30)

**F7. `ForAllValues:` in the Allow statement of the trust policy**
> Severity: High
> Confidence: High (single source: README v6.3.0)
- Why: the README warns to avoid `ForAllValues:` in `Allow` statements and to use `StringEquals` or `StringLike`. Not covered by a second source; the IAM multivalued-key semantics page was not read.
- Impact: a condition that can evaluate true when the key is absent.
- ❌ Wrong: `"ForAllValues:StringEquals": { "token.actions.githubusercontent.com:sub": ["repo:o/r:environment:prod"] }`
- ✅ Correct: `"StringEquals": { "token.actions.githubusercontent.com:sub": "repo:o/r:environment:prod" }`
- Source: https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/README.md (2026-10-30)

## Migration Guide

> Confidence: High | Sources: configure-aws-credentials releases pages 1-2 (2026-10-30) + action.yml v6.3.0 (2026-10-30)

**Breaking Changes**:
- v6.0.0 (04 Feb 2026): "Update action to use node24", which needs runner v2.327.1 or later. Self-hosted runners older than that fail. v6.3.0 `action.yml`: `runs.using: node24`.
- v5.0.0 (03 Sep 2025, for v4 users): "Cleanup input handling. Changes invalid boolean input behavior".
- Platform change (not an action release): immutable `sub` for repos created on or after 15 July 2026 (A4).

**v6 changes relevant to OIDC users** (v6.0.0 to v6.3.0):

| Version | Date | Change |
|---|---|---|
| v6.0.0 | 04 Feb 2026 | node24; `transitive-tag-keys` support; fix `aws-account-id`/`authenticated-arn` output with role chaining |
| v6.1.0 | 2026-04-06 | skip cleanup option; AWS profiles (`aws-profile`) |
| v6.1.2 / v6.1.3 | 2026-05-26 / 2026-05-27 | filesystem checks; kubelet token symlink |
| v6.2.0 | 2026-06-01 | additional default session tags; custom session tags; regex validation of `role-session-name`; custom STS endpoints; more retry logic; run id in STS user-agent |
| v6.2.1 | 2026-06-26 | enforce `allowed-account-ids` on all auth paths |
| v6.2.3 | 2026-07-22 | `PackedPolicyTooLarge` detection in STS tags |
| v6.2.4 | 2026-08-31 | account-ids handling; mask proxy as secret in logs; no backoff sleep after final attempt |
| v6.3.0 | 2026-09-15 (changelog 2026-09-11) | `translate-env-variables` option (defaults true) |

**Upgrade Steps**:
1. Confirm self-hosted runners are on v2.327.1 or later (v6.0.0 note). GitHub-hosted runners: (unverified) assumed current.
2. Replace `uses:` with `aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0` (F3).
3. If a custom `role-session-name` is used, check it matches `[\w+=,.@-]*` and is 2-64 chars (STS). v6.2.0 validates it.
4. For repos created on or after 2026-07-15, rewrite `sub` conditions to the immutable form (A4).
5. If other steps set `AWS_*` environment variables on the runner, consider `translate-env-variables: false` (README).
6. Remove any `--thumbprint-list` maintenance for the GitHub provider (A1).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|---|---|---|---|
| GitHub Actions runner | v2.327.1 | — | node24 (v6.0.0 note) |
| Action | v6.3.0 (F3) | — | family rule 11 |
| STS `DurationSeconds` | 900 | 43200 (bounded by role MaxSessionDuration 1-12 h; 3600 when chained) | STS API |
| IAM OIDC provider audiences | 1 | 100 | IAM page |
| IAM OIDC provider thumbprints | 1 (if set) | 5 | IAM page; not needed for GitHub |

## Implementation Blueprint

> Confidence: High | [✓✓ Triangulated | GitHub oidc-in-aws + action README v6.3.0 + IAM GitHub role guidance]

**Lifecycle**:
1. Once per AWS account: create the IAM OIDC provider (A1). HCL lives in `provisioning-aws-iam-v6`.
2. Per app x environment: create `gha-<app>-<env>-deploy` (trust `environment:<env>`) and `gha-<app>-<env>-pr-read` (trust `environment:<env>-pr` or `:pull_request`) (A7).
3. Pro/Team: create environments `<env>` (deployment branch policy: `main` only) and `<env>-pr`. Store role ARNs as environment variables (C1).
4. Workflows: `ci-<app>.yml` (pull_request → PR read role), `cd-<app>.yml` (push to main / dispatch → deploy role) (family rule 5).

**Deploy role trust (Pro/Team, environment form)**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "repo:<ORG>/<REPO>:environment:prod"
      }
    }
  }]
}
```

**PR read role trust (Free, no environments)**:
```json
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
    "token.actions.githubusercontent.com:sub": "repo:<ORG>/<REPO>:pull_request"
  }
}
```

**Reusable login workflow** (`./.github/workflows/_aws-oidc-login-check.yml`, family rules 6 and 15):
```yaml
# configure-aws-credentials v6.3.0 (F3); credentials do not cross job boundaries,
# so the login step must run inside the job that uses AWS.
name: _aws-oidc-login-check
on:
  workflow_call:
    inputs:
      environment:   { type: string, required: true }
      role-arn:      { type: string, required: true }
      aws-region:    { type: string, required: true }
      account-id:    { type: string, required: true }
    outputs:
      caller-arn:
        description: ARN returned by sts get-caller-identity
        value: ${{ jobs.login.outputs.caller-arn }}
permissions: {}
jobs:
  login:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    permissions:
      id-token: write
      contents: read
    outputs:
      caller-arn: ${{ steps.who.outputs.arn }}
    steps:
      - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
        with:
          role-to-assume: ${{ inputs.role-arn }}
          aws-region: ${{ inputs.aws-region }}
          role-session-name: gha-${{ github.run_id }}-${{ github.run_attempt }}
          role-duration-seconds: 900
          allowed-account-ids: ${{ inputs.account-id }}
      - id: who
        run: echo "arn=$(aws sts get-caller-identity --query Arn --output text)" >> "$GITHUB_OUTPUT"
```
- In a reusable workflow, the caller's `repo`/`environment` drive the `sub`. `job_workflow_ref` names this file (C4). For reusable workflows outside the caller's org or enterprise, the caller must set `id-token: write` explicitly (GitHub OIDC reference). Note that `ubuntu-latest` and the AWS CLI being preinstalled on hosted runners are (unverified) in this research.

**Role chaining to a workload account** (C6):
```yaml
- uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
  with:
    role-to-assume: arn:aws:iam::111111111111:role/gha-hub
    aws-region: eu-west-1
- uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
  with:
    role-chaining: true
    role-to-assume: arn:aws:iam::222222222222:role/gha-orders-prod-deploy
    aws-region: eu-west-1
    role-duration-seconds: 3600            # chained: max 1 h
    role-skip-session-tagging: true        # or allow sts:TagSession in the 2nd role's trust
```

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
# 1. Provider exists and lists the audience
aws iam list-open-id-connect-providers
aws iam get-open-id-connect-provider --open-id-connect-provider-arn arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com
# Expected: ClientIDList contains "sts.amazonaws.com"

# 2. Trust policy pins aud + sub with StringEquals (offline check of the JSON)
jq -e '.Statement[].Condition.StringEquals["token.actions.githubusercontent.com:sub"]' trust-prod.json
# Expected: exit 0, a single non-wildcard string

# 3. Workflow hygiene (offline)
grep -n "configure-aws-credentials@" .github/workflows/*.yml
# Expected: every hit is @e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
grep -n "pull_request_target" .github/workflows/*.yml
# Expected: no hit in any workflow that logs in to AWS
grep -n "aws-access-key-id" .github/workflows/*.yml
# Expected: no hit

# 4. Inside the job, after login
aws sts get-caller-identity
# Expected: Arn = arn:aws:sts::<ACCOUNT_ID>:assumed-role/<ROLE>/gha-<run_id>-<attempt>
```

**Troubleshooting** (sources: README v6.3.0, STS API, GitHub OIDC reference, IAM pages; all 2026-10-30):

| Symptom | Likely cause | Check |
|---|---|---|
| `Not authorized to perform sts:AssumeRoleWithWebIdentity` | `sub` mismatch: env vs `pull_request` vs ref form (A3); immutable `sub` repo with name-only policy (A4); custom sub template not reflected in policy (C3); wrong provider ARN/account | Compare the job shape with the A3 table; inspect repo creation date / template via `GET /repos/{owner}/{repo}/actions/oidc/customization/sub` |
| Audience mismatch / `InvalidIdentityToken` | provider `ClientIDList` lacks `sts.amazonaws.com`, or `audience` input changed | `get-open-id-connect-provider`; action `audience` default is `sts.amazonaws.com`. The exact STS message text for an aud mismatch is (unverified) |
| Token cannot be requested at all | job lacks `id-token: write`; fork PR (write scopes downgraded) | job `permissions`; event source |
| `MalformedPolicyDocument` on role create/update | trust lacks `...:sub` (or `job_workflow_ref`) or uses a pure wildcard | IAM identity-provider controls |
| Login fails with DurationSeconds error | above role MaxSessionDuration, or > 3600 when chained | A8, F6 |
| `PackedPolicyTooLarge` | session policies/tags too large (chained hop) | STS; v6.2.3 detection |
| `Credentials loaded by the SDK do not match` | existing credentials in env | README: enable `role-chaining` or `unset-current-credentials` |
| `IDPCommunicationError` | transient reach failure to issuer | action retries (12 attempts default) |

**Mocking**: there is no official offline emulator for `AssumeRoleWithWebIdentity` (unverified). Test the trust JSON statically (step 2), and validate HCL with the mocked tests owned by `provisioning-aws-iam-v6`. Run the first live login in a non-production account.

## Production Readiness

- **Performance**: the action retries with exponential backoff, 12 attempts by default (`retry-max-attempts`, `disable-retry`). `action-timeout-s` sets a global timeout (none by default).
- **Scalability**: up to 100 audiences per provider; one provider URL per account; JWKS limits are on GitHub's side. One role per app x env x stage keeps blast radius small.
- **Monitoring**: CloudTrail `AssumeRoleWithWebIdentity` entries include the token Subject. Use `role-session-name` with the run id to correlate. Review CloudTrail for unexpected `sub` values. Dependabot jobs have `event_name` `dynamic` (GitHub oidc-in-aws).
- **Security**: StringEquals on aud+sub; environment deployment branch policy (Pro/Team); PR-only read role; `id-token: write` per job; SHA-pinned action; `allowed-account-ids`; short sessions; no `pull_request_target` with cloud login; least-privilege permission policies (README: "Grant only those permissions that are necessary").

## Reference Implementations

- GitHub: Configuring OpenID Connect in Amazon Web Services: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws (example uses a stale action SHA; do not copy the version)
- AWS: Configuring a role for GitHub OIDC identity provider: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html#idp_oidc_Create_GitHub
- Action README (OIDC, role chaining, session tagging sections) at tag v6.3.0: https://github.com/aws-actions/configure-aws-credentials/blob/v6.3.0/README.md
- Neighbour skills by name only (family rule 12): `provisioning-aws-iam-v6` (HCL), `composing-github-actions-pipelines`, `federating-github-actions-oci`, `automating-github-repos-with-actions` (SHA pinning, injection).

## Research Gaps

```
Gap: G1 Exact immutable-sub string for environment jobs (repo:ORG@ID/REPO@ID:environment:ENV)
Impact: medium; trust policy may not match for repos created after 2026-07-15 using environments
Workaround: read the sub from a test token (decode in a throwaway job) before writing the policy
Follow-up: docs.github.com OIDC reference "immutable subject" section; README v6.3.0
§7-ref: Iteration 2 — still open (unverified)
```
```
Gap: G2 Whether AWS evaluates token.actions.githubusercontent.com:job_workflow_ref directly (C4)
Impact: medium; reusable-workflow restriction design
Workaround: customize sub to include job_workflow_ref (documented by both vendors)
Follow-up: AWS condition-keys reference (condition-keys-wif) and IAM identity-provider controls page
§7-ref: Iteration 3 — sources conflict, kept (medium confidence)
```
```
Gap: G3 How deployment branch policies evaluate pull_request events for an <env>-pr environment
Impact: low-medium; C2 option (a)
Workaround: use option (b) :pull_request sub
Follow-up: docs.github.com deployments-and-environments "Deployment branches and tags"
§7-ref: Iteration 2 — open (unverified)
```
```
Gap: G4 Whether the action masks access key / secret / session token in logs (setSecret)
Impact: low (credentials are env vars, not printed by default)
Workaround: keep output-credentials false; never echo AWS_* variables
Follow-up: action source src/ at v6.3.0
§7-ref: Iteration 1 — open (unverified)
```
```
Gap: G5 Plan availability of the OIDC subject-template API for Free private repos
Impact: low-medium; Option B + C3 on Free
Workaround: separate repos/accounts per environment
Follow-up: docs.github.com OIDC reference; REST oidc page (no restriction stated)
§7-ref: Iteration 3 — open (unverified)
```
```
Gap: G6 Exact STS error text for an audience mismatch; exact role-session-name regex in the action
Impact: low (troubleshooting wording only)
Workaround: troubleshooting table lists InvalidIdentityToken/Not authorized generically
Follow-up: action source; AWS re:Post article "Resolve errors related to OIDC" (community-adjacent, not read)
§7-ref: Iteration 1 — open (unverified)
```
```
Gap: G7 Fork-PR id-token behaviour stated explicitly (currently inferred from "write permissions to read only")
Impact: low; design already blocks forks
Follow-up: docs.github.com automatic token authentication / OIDC reference
§7-ref: Iteration 2 — inferred (medium confidence)
```

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Migration Guide | v6.0.0 breaking change missing from releases page 1 | Resolved via releases page 2 (node24, runner v2.327.1) | https://github.com/aws-actions/configure-aws-credentials/releases?page=2 (2026-10-30) |
| 1 | C7 / A9 | defaults of inputs | Resolved via action.yml at v6.3.0 (node24, 33 inputs) | https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml (2026-10-30) |
| 2 | A2 | GitHub required claim in IAM | Added identity-provider controls (sub or job_workflow_ref; MalformedPolicyDocument) | https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_secure-by-default.html (2026-10-30) |
| 2 | C1 | plan availability of environments for private repos | Resolved (Free: none; Pro/Team: environments, secrets, branch policies; no reviewers/wait timer) | manage-environments + deployments-and-environments (2026-10-30) |
| 2 | C3 | org-level sub template endpoint path | Resolved (`PUT /orgs/{org}/actions/oidc/customization/sub`) | https://docs.github.com/en/rest/actions/oidc (2026-10-30) |
| 3 | C4 | job_workflow_ref with AWS | Sources conflict; kept (medium confidence), default to sub template | GitHub oidc-with-reusable-workflows + AWS IdP controls + condition-keys (2026-10-30) |
| 3 | G5 | sub template plan availability | Still open (unverified) | — |

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (token, AWS provider/trust, action v6 inputs, migration, PR role, forks, troubleshooting)
- [x] Pattern counts driven by domain needs (10 / 7 / 7)
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete (reusable workflow, chaining)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example (A5, Implementation Blueprint)
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or marked single-source (A6, A9, A10 single-source)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced in the changelog

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1-A8 (triangulated); F1-F6; plan availability table in C1; sub formats.
- **Medium Confidence (validate with user)**: A9 action-side regex; A10 (single source); C4 job_workflow_ref with AWS; immutable environment sub string; fork id-token behaviour (inferred); no session tags on the OIDC hop (inferred).
- **Low Confidence (must ask human)**: G3, G5, G6 (unverified).
- **Edge Cases (pause)**: repo created after 2026-07-15 (immutable sub); self-hosted runner older than v2.327.1; GitHub Enterprise Server (immutable sub not available, not in scope).
- **Facts requested**: none. Only F3 (action) and F10 (checkout) are used in examples.

## Pages read

| URL | read on | official | prompt-injection-like instructions found |
|---|---|---|---|
| https://docs.github.com/en/actions/reference/security/oidc | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (partial: chars 0-100000 of 235839) | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows | 2026-10-30 | yes | no |
| https://docs.github.com/en/rest/actions/oidc | 2026-10-30 | yes | no |
| https://github.com/aws-actions/configure-aws-credentials/releases (page 1: v6.1.0-v6.3.0) | 2026-10-30 | yes | no |
| https://github.com/aws-actions/configure-aws-credentials/releases?page=2 (v4.0.3-v6.0.0) | 2026-10-30 | yes | no |
| https://github.com/aws-actions/configure-aws-credentials/blob/v6.3.0/README.md | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/README.md | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_secure-by-default.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_iam-condition-keys.html (partial: OIDC federation section only of ~86 KB) | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/cli/latest/reference/iam/create-open-id-connect-provider.html (AWS CLI 2.39.2) | 2026-10-30 | yes | no |

Two web searches (2026-10-30) were used only to locate the current reusable-workflows OIDC URL
(a guessed URL returned 404). Their result summaries were not used as evidence.

## Source Bibliography

**Primary (GitHub, read 2026-10-30)**:
- OpenID Connect reference: https://docs.github.com/en/actions/reference/security/oidc
- Configuring OIDC in AWS: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws
- OIDC with reusable workflows: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows
- Deployments and environments reference: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- Managing environments: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- Workflow syntax (permissions): https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- Events that trigger workflows: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- REST API, Actions OIDC: https://docs.github.com/en/rest/actions/oidc

**Primary (action, read 2026-10-30)**:
- Releases page 1 and 2: https://github.com/aws-actions/configure-aws-credentials/releases ; https://github.com/aws-actions/configure-aws-credentials/releases?page=2
- README at v6.3.0: https://github.com/aws-actions/configure-aws-credentials/blob/v6.3.0/README.md
- action.yml at v6.3.0: https://raw.githubusercontent.com/aws-actions/configure-aws-credentials/v6.3.0/action.yml
- Family fact F3 (v6.3.0 = e1253824e5c10ff9df46874f81ed3ec929e19cfd) and F10 (checkout v7.0.1): `workspace/github-actions-cicd/_family_facts.md`

**Primary (AWS, read 2026-10-30)**:
- Create an OIDC identity provider in IAM: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html
- Create a role for OIDC federation / Configuring a role for GitHub: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html
- Identity-provider controls for shared OIDC providers: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_oidc_secure-by-default.html
- IAM and STS condition keys (OIDC federation section): https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_iam-condition-keys.html#condition-keys-wif
- IAM roles terms and concepts (role chaining): https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html
- STS AssumeRoleWithWebIdentity API: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html
- AWS CLI 2.39.2 create-open-id-connect-provider: https://docs.aws.amazon.com/cli/latest/reference/iam/create-open-id-connect-provider.html

**Validation**: no community sources used.
