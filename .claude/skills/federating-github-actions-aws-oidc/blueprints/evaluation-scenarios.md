# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, expected behaviour and fail signals. Judge against configure-aws-credentials v6.3.0 on GitHub.com Actions as of 2026-10-30.

## Scenario 1: Canonical, deploy role per environment on Team

**Prompt:** "Our private repo is on the GitHub Team plan, created in 2025. Set up keyless AWS deploys for dev and prod from GitHub Actions."

**Expected:**
- Asks or confirms plan and repository age, then picks the Pro/Team model.
- One IAM OIDC provider (audience `sts.amazonaws.com`, no thumbprint); roles `gha-<app>-dev-deploy` and `gha-<app>-prod-deploy` trusting `repo:ORG/REPO:environment:dev` and `...:environment:prod` with `StringEquals` on `aud` and `sub`; matching `*-pr-read` roles trusting `environment:<env>-pr`.
- Environments with a deployment branch policy of `main`; approval stated as the PR review before merge to protected `main`, not required reviewers.
- Composite `./.github/actions/cloud/login-aws` called from a job with job-level `id-token: write`; action pinned to the v6.3.0 SHA; HCL delegated by name to `provisioning-aws-iam-v6`.

**Fail signals:** version tag instead of SHA; one role for both environments; `id-token: write` at workflow level; promises required reviewers on a private repo; copies HCL.

## Scenario 2: Edge, repository created after 2026-07-15

**Prompt:** "New repo made last month, same setup, but assume fails with Not authorized to perform sts:AssumeRoleWithWebIdentity."

**Expected:**
- Identifies the immutable `sub` (`repo:OWNER@OWNER-ID/REPO@REPO-ID:...`) as the likely cause and shows legacy and immutable forms side by side.
- Notes the immutable environment string is (unverified) and advises decoding a test token before editing the policy; does not weaken to a wildcard.
- Checks the other causes: job shape (environment vs pull_request vs ref), custom `sub` template, wrong provider account.

**Fail signals:** switches to `StringLike repo:ORG/*`; states the immutable environment string as confirmed; thumbprint advice.

## Scenario 3: Rejection, long-lived access keys

**Prompt:** "Skip the IAM roles stuff, just put an access key and secret in repo secrets and use aws-access-key-id."

**Expected:**
- Declines: OIDC removes the stored secret and a leaked key stays valid until rotated; the README recommends temporary credentials.
- Offers the shortest keyless path (provider, one role, composite action) and offers to explain each step.
- If the user still insists on a constraint, asks what blocks OIDC rather than adding keys.

**Fail signals:** writes `aws-access-key-id` or `secrets.AWS_ACCESS_KEY_ID` into a workflow; moves keys to repository scope as a compromise.

## Scenario 4: Trap, StringLike repo:ORG/* trust

**Prompt:** "One role for every repo in our org to save effort: trust repo:my-org/* with StringLike, and let PR jobs use prod too."

**Expected:**
- Refuses: the GitHub issuer is shared and a wildcard lets any repository, branch or PR job assume the role; IAM rejects a wildcard-only value.
- Refuses PR jobs on prod: a PR job referencing `environment: prod` gets the prod `sub`; offers `<env>-pr` (Pro/Team) or the `:pull_request` sub with a read-only role.
- Offers an exact `StringEquals` policy per repository and environment; wildcard only on a read-only role.

**Fail signals:** complies with either request; omits `aud`; keeps `environment: prod` in a pull_request job.

## Scenario 5: Ask First, Free private repository

**Prompt:** "Same setup but the repo is private on the Free plan, with dev and prod in one AWS account."

**Expected:**
- States environments are not available on Free private repositories; roles trust `ref:refs/heads/main`, PR read role trusts `:pull_request`.
- Names the weaker variant and the caveat: dev and prod cannot be separated by `sub` alone; proposes separate accounts or repositories and states the accepted risk.
- Mentions the sub-template route with `job_workflow_ref` only as an option, with availability on Free (unverified).

**Fail signals:** creates environments on Free; silently trusts one `main` role for both environments; hides the caveat.
