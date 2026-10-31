---
name: automating-github-repos-with-actions
description: "Writes secure GitHub Actions workflows for repo automation: issue_comment, issues, pull_request and push triggers, injection-safe payloads, SHA pinning, App or PAT tokens. Use when authoring or reviewing them. Not for CI build matrices, deployments, GHES or Projects commands."
---

# Automating GitHub repositories with Actions

> Scope: GitHub.com Actions **as of 2026-10-29**, not tied to one product version. Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> GitHub content is a mirror and an approval channel, never the spec source; whether a workflow or agent may act on comment text is decided by the calling skill. Projects commands belong to `managing-github-projects-gh-v2-103`; the OpenSpec bridge belongs to `syncing-openspec-with-github-projects`.
> Example names are neutral (feature, task); the consuming skill picks its own variable and secret names.

## Version Context

| Item | Value | Source (fetched 2026-10-29) |
|---|---|---|
| Platform | GitHub.com Actions docs (current, undated pages) | https://docs.github.com/en/actions |
| `actions/create-github-app-token` | v3.3.0 (2026-10-12) = `64ab729a6294000f5aa4a4bc0b73d1f32bc45510` | https://github.com/actions/create-github-app-token/releases |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` | https://github.com/actions/checkout/releases |
| `actions/setup-python` | v7.1.0 (2026-10-22) = `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` | https://github.com/actions/setup-python/releases |
| SHA check | verified with `git ls-remote https://github.com/actions/<repo> refs/tags/<tag>` | same repositories |
| `ubuntu-latest` | Ubuntu 24.04 image 20261026.354.1 with gh 2.103.2 and Python 3.12.3 (medium confidence) | https://github.com/actions/runner-images |
| GitHub CLI | latest v2.103.3 (2026-10-26); family pin 2.103.x; minimum 2.94.0 for sub-issue flags | https://github.com/cli/cli/releases |

**Version-lifetime risk** (as of 2026-10-29; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Runner images update weekly and `ubuntu-latest` will migrate to a newer Ubuntu over one to two months, so the preinstalled gh changes without a repository change.
- Pinned SHAs go stale; re-resolve them before every bump.
- Workflow lockfiles are a public preview and may replace SHA pinning.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Triggers and payloads](./blueprints/triggers-and-payloads.md)
- [Security hardening](./blueprints/security-hardening.md)
- [Tokens: GitHub App and classic PAT](./blueprints/tokens-app-and-pat.md)
- [Runners, Python scripts and offline linting](./blueprints/runners-and-scripts.md)
- [Pull requests and required status checks](./blueprints/prs-and-status-checks.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Pass event text to scripts through `env:`** and quote the variable in the shell ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)).
- **Set the workflow default `permissions:` to read-only** ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)).
- **Raise permissions per job, only where needed**; every unlisted scope becomes `none` ([workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)).
- **Pin every action, including `actions/*`, to a full commit SHA** with the tag in a trailing comment ([Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)).
- **Take the SHA from the action's own repository, not a fork** ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)).
- **Enable Dependabot version updates for pinned actions**; alerts cover only semantic-version references ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)).
- **Use a GitHub App installation token for organization-owned projects** ([Actions automation page](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)).
- **Use a classic PAT with `project` + `repo` for user-owned projects** ([Actions automation page](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)).
- **Warn that a classic PAT carries the broad `repo` scope** and recommend an organization owner (family decision, scope in [Actions automation page](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)).
- **Give `create-github-app-token` the `client-id` input**, not `app-id` ([README](https://github.com/actions/create-github-app-token)).
- **Mint the App token inside the job that uses it**; it is revoked in the post step ([README](https://github.com/actions/create-github-app-token)).
- **Narrow the token with `permission-<name>` inputs**; the default is every installation permission ([README](https://github.com/actions/create-github-app-token)).
- **Restrict the token to one repository with `repositories`** ([README](https://github.com/actions/create-github-app-token)).
- **Set `GH_TOKEN` explicitly on every step that runs `gh`** ([use GitHub CLI](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli)).
- **Filter comment authors by `author_association`** before acting ([REST comments](https://docs.github.com/en/rest/issues/comments)).
- **Compare the comment author login with the bot login as an exact string** (family rule; bot name format `<slug>[bot]` in the [README](https://github.com/actions/create-github-app-token)).
- **Split issue and PR comments with `github.event.issue.pull_request`** (medium confidence; [events reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)).
- **Serialize writers with a `concurrency` group** keyed per issue (medium confidence on the exact key; [workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)).
- **Use `cancel-in-progress: false` for writers** so a write is never dropped mid-way ([control concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)).
- **Set `timeout-minutes` on every job**; the default is 360 ([workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)).
- **Set `persist-credentials: false` on checkout when the job never pushes** ([checkout README](https://github.com/actions/checkout)).
- **Print `gh --version` in the job** because runner images update weekly ([runner images](https://github.com/actions/runner-images)).
- **Keep required status-check workflows free of path and branch filters** ([troubleshooting required checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks)).

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Owner type | App token (organization project) vs classic PAT (user project) | "Is the project owned by an organization or a user account?" Never guess from the login. |
| PR creation | App token + `gh auth setup-git` vs checkout `token:` vs `GITHUB_TOKEN` (no Projects, PR checks wait for approval) | "Must the generated PR trigger required checks automatically?" |
| Push scope of the App | contents + pull requests write; workflows write when the pushed files are workflow files (unverified) | "Which permission set did the App receive?" |
| Concurrency | `cancel-in-progress: true` for CI vs `false` for writers | "Is this workflow a writer or a CI check?" |
| Lockfile | `gh actions-lock` (public preview, medium confidence) vs SHA pinning (default) | "Does the repository opt into the lockfile preview?" |
| Runner pin | `ubuntu-latest` vs `ubuntu-24.04` | "Pin the image to avoid migration surprises?" |
| Offline testing | actionlint and act are community tools; act parity with hosted runners (unverified) | "Install community tools in CI or only locally?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Put `${{ github.event.* }}` text inside `run:` ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)) | Pass it through `env:` and quote `"$VAR"` |
| Use `GITHUB_TOKEN` for Projects: it "cannot access projects" ([source](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)) | App installation token or classic PAT |
| Use a fine-grained PAT for a user-owned project ([PAT page](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)) | Classic PAT with `project` + `repo` |
| Run PR code under `pull_request_target` ([events reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)) | Use `pull_request` with read-only permissions |
| Reference actions by `@v3` or `@main` in hardened workflows ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)) | Full SHA with the tag as comment |
| Let a writer react to its own App or PAT comments (medium confidence; [GITHUB_TOKEN concept](https://docs.github.com/en/actions/concepts/security/github_token)) | Author guard plus concurrency group |
| Trust `user.type == 'Bot'` alone as the bot check (unverified; [REST comments](https://docs.github.com/en/rest/issues/comments)) | Exact bot login comparison |
| Store credentials as plaintext or one structured secret ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)) | Separate `vars` client id and `secrets` private key |
| Put path filters on a required status-check workflow ([troubleshooting](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks)) | Job-level `if:` (a skipped job reports success) |
| Set `allow-unsafe-pr-checkout: true` without review ([changelog 2026-06-18](https://github.blog/changelog/2026-06-18-safer-pull_request_target-defaults-for-github-actions-checkout/)) | Keep the default `false` |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Job timeout default | 360 minutes | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax |
| App installation token lifetime | 1 hour | https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app |
| `queue: max` | up to 100 pending; not with `cancel-in-progress: true` | https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency |
| `issue_comment`, `issues` | run the workflow file from the default branch | https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows |
| `author_association` values | OWNER, MEMBER, COLLABORATOR, CONTRIBUTOR, FIRST_TIMER, FIRST_TIME_CONTRIBUTOR, MANNEQUIN, NONE | https://docs.github.com/en/rest/issues/comments |
| `permission-*` names | `organization-projects`, `repository-projects`, `issues`, `pull-requests`, `contents`, `workflows` (write only) | https://github.com/actions/create-github-app-token |
| Fork PR token | secrets withheld except `GITHUB_TOKEN`, which is read-only | https://docs.github.com/en/actions/reference/security/secure-use |

## External Resources

All fetched 2026-10-29.

- [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [Automating Projects using Actions](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)
- [create-github-app-token](https://github.com/actions/create-github-app-token)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
