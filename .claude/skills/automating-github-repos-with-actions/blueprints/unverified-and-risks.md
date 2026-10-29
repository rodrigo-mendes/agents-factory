# Unverified and risks register

Back to [SKILL.md](../SKILL.md). Research date 2026-10-29. Tags are plain parentheses: (unverified) and (medium confidence).

## Version-lifetime risk

As of 2026-10-29.

- `ubuntu-latest` is Ubuntu 24.04 today and migrates "over 1-2 months" at an unannounced date; the preinstalled gh changes weekly with the image. Source: https://github.com/actions/runner-images
- Pinned SHAs (checkout v7.0.1, setup-python v7.1.0, create-github-app-token v3.3.0) were resolved on 2026-10-29; re-run `git ls-remote` before bumping. Source: https://github.com/actions/checkout/releases
- Workflow lockfiles entered public preview on 2026-10-14 and the secure-use page says they supersede SHA pinning for repositories that adopt them. Source: https://github.blog/changelog/2026-10-14-github-actions-workflow-lockfiles-in-public-preview/
- The fine-grained PAT gap for user-owned projects is described as "not permanent"; the classic PAT rule may relax. Source: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- Floating major tags change behaviour: checkout v7 behaviour was backported to v3 to v6 on 2026-07-20. Source: https://github.com/actions/checkout/releases

## Unverified (3)

| ID | Claim | Impact | Workaround |
|---|---|---|---|
| U1 | Value of `user.type` or `sender.type` for App-authored comments (schema says only "string") | a bot guard on type may not match and loop | compare the exact bot login `<slug>[bot]` |
| U2 | Exact App permission set for push and PR creation, and whether `workflows: write` is required for workflow-file pushes | PR creation fails with 403 | test once in a sandbox repository; grant the minimum that works |
| U3 | Differences between act and hosted runners (not listed on its README) | local green, hosted red | treat hosted runs as the truth |

## Irresolvable (2)

| ID | Claim | Note |
|---|---|---|
| I1 | Enumeration of `user.type` values (same gap as U1) | official REST schema gives only "string"; the webhook page does not expand objects |
| I2 | General official statement that comments or labels made with an App token or PAT start workflow runs (same gap as M2) | only the `GITHUB_TOKEN` exemption is documented |

## Medium confidence (5)

| ID | Claim | Why medium | Check |
|---|---|---|---|
| M1 | `github.event.issue.pull_request` separates issue and PR comments | single official page | one captured payload |
| M2 | Comments or labels created with an App token or PAT can retrigger the same workflow | inferred from the `GITHUB_TOKEN` exemption (I2) | add guards regardless |
| M3 | Per-issue concurrency key `github.event.issue.number` | mechanism documented, this key not in an official example | confirm with two quick comments |
| M4 | `ubuntu-latest` image 20261026.354.1 ships gh 2.103.2 and Python 3.12.3 | read from the runner-images list through research, not re-fetched | `gh --version` in the job |
| M5 | `gh actions-lock` lockfile is a public preview feature | preview status can change | read the changelog before adopting |

## Coverage limits (3)

| ID | Limit |
|---|---|
| L1 | docs.github.com pages show no last-updated date; they are the current version and WebFetch returns a condensed view |
| L2 | The workflow-syntax and contexts pages were read in chunks; the contexts page was partly read |
| L3 | Whether `secrets` is usable in step-level `if:` was not confirmed and the skill makes no claim about it |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Never Do (user.type); never-do-patterns.md N7; triggers-and-payloads.md Bot guard for label events; evaluation-scenarios.md Scenario 5 | U1 |
| (unverified) | SKILL.md Ask First (push scope); prs-and-status-checks.md options table, Option A example and note on workflows write | U2 |
| (unverified) | SKILL.md Ask First (offline testing); runners-and-scripts.md Offline linting | U3 |
| (medium confidence) | SKILL.md Always Do (issue and PR split); always-do-patterns.md Who may trigger a comment workflow; triggers-and-payloads.md Issue comment or PR comment | M1 |
| (medium confidence) | SKILL.md Never Do (loop guard); never-do-patterns.md N6; triggers-and-payloads.md Loop prevention | M2 |
| (medium confidence) | SKILL.md Always Do (concurrency group); always-do-patterns.md Concurrency and timeout; triggers-and-payloads.md Concurrency per issue | M3 |
| (medium confidence) | SKILL.md Version Context; runners-and-scripts.md Hosted runner image | M4 |
| (medium confidence) | SKILL.md Ask First (lockfile); security-hardening.md Lockfile alternative; runners-and-scripts.md Offline linting | M5 |

## Source Bibliography

All fetched 2026-10-29. docs.github.com pages are current undated versions.

**docs.github.com**
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.github.com/en/actions/concepts/security/script-injections
- https://docs.github.com/en/actions/concepts/security/github_token
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions
- https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
- https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks
- https://docs.github.com/en/rest/issues/comments
- https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app

**Action repositories and releases**
- https://github.com/actions/create-github-app-token (README, action.yml, releases)
- https://github.com/actions/checkout (README, releases, v7.0.0)
- https://github.com/actions/setup-python/releases
- https://github.com/actions/runner-images
- https://github.com/cli/cli/releases
- SHA verification: `git ls-remote https://github.com/actions/<repo> refs/tags/<tag>`

**GitHub changelog**
- https://github.blog/changelog/2026-06-18-safer-pull_request_target-defaults-for-github-actions-checkout/
- https://github.blog/changelog/2026-10-14-github-actions-workflow-lockfiles-in-public-preview/

**Community tools (classification only, not used for normative claims)**
- https://github.com/rhysd/actionlint
- https://github.com/nektos/act
