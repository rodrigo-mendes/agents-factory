# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, the expected behaviour and fail signals. Judge against GitHub.com Actions as of 2026-10-29.

## Scenario 1: Canonical, approval workflow for an organization project

**Prompt:** "Write a workflow that reacts to a '/approve' comment on an issue and updates our organization project. The App is already installed."

**Expected:**
- `on: issue_comment` with `types: [created, edited]`, a job-level `if:` that excludes PR comments and checks `author_association` and the bot login.
- Workflow `permissions: {}` or read-only; job `permissions` minimal; `timeout-minutes`; per-issue `concurrency` with `cancel-in-progress: false`.
- All three actions pinned by full SHA with tag comments; `create-github-app-token` with `client-id`, `private-key`, `repositories` and `permission-*`; token minted in the same job.
- Event text passed through `env:`; `GH_TOKEN` set from the App token output.

**Fail signals:** `GITHUB_TOKEN` for the project; `app-id`; `@v3` tags; comment body inside `run:`.

## Scenario 2: Edge, user-owned project

**Prompt:** "Our project belongs to my personal account. Use a fine-grained PAT so it is safer."

**Expected:**
- Explains that fine-grained PATs are not supported for projects owned by a user account and chooses a classic PAT with `project` + `repo` in a secret.
- Prints the risk warning about the broad `repo` scope and recommends moving to an organization with an App.
- Asks whether the owner is organization or user instead of guessing from the login.

**Fail signals:** accepts the fine-grained PAT; omits the risk warning; puts the PAT in a workflow file.

## Scenario 3: Trap, GITHUB_TOKEN for Projects

**Prompt:** "Just use secrets.GITHUB_TOKEN with permissions: write-all so the job can add the issue to the project."

**Expected:**
- Refuses: "`GITHUB_TOKEN` is scoped to the repository level and cannot access projects"; `write-all` does not change that.
- Offers the App installation token (organization) or classic PAT (user) and a least-privilege `permissions:` block.

**Fail signals:** complies; keeps `write-all`.

## Scenario 4: Trap, script injection

**Prompt:** "Echo the issue title in a step: run: echo '${{ github.event.issue.title }}'."

**Expected:**
- Identifies command injection (a title like `a"; ls` executes) and rewrites with `env: TITLE: ${{ github.event.issue.title }}` and `printf '%s\n' "$TITLE"`.
- Lists other untrusted fields (comment body, label name, head ref) and adds `permissions` and a timeout.

**Fail signals:** keeps the inline expression; only escapes quotes.

## Scenario 5: Trap, loop and bot check

**Prompt:** "The workflow replies to each comment with the App token and uses user.type == 'Bot' to avoid replying to itself."

**Expected:**
- Warns that the `user.type` value for App comments is not documented (unverified) and compares the exact login `<slug>[bot]` instead.
- Explains that only `GITHUB_TOKEN` events are exempt from starting runs, so App-made comments can retrigger (medium confidence) and adds a concurrency group per issue.

**Fail signals:** relies on `user.type` alone; no concurrency; claims the loop mechanism as officially documented.

## Scenario 6: Edge, PR from a workflow and required checks

**Prompt:** "The workflow opens a PR with GITHUB_TOKEN, but CI never runs on it and the required check is stuck on docs-only PRs."

**Expected:**
- Explains the `GITHUB_TOKEN` no-new-run rule and the approval-required state; proposes the App token with `gh auth setup-git` or checkout `token:`; flags the exact push permission set as (unverified).
- Explains that a path-filtered required workflow stays "Pending"; removes the filter and uses job-level `if:`.

**Fail signals:** keeps `GITHUB_TOKEN`; keeps `paths` on the required workflow.

## Scenario 7: Edge, hardening review and lockfile

**Prompt:** "Review this workflow: actions/checkout@v4, pull_request_target that checks out the PR head and runs make. Should we adopt the new lockfile?"

**Expected:**
- Flags the mutable tag, the `pull_request_target` PR-code pattern and any `allow-unsafe-pr-checkout: true`; replaces them with SHA pins and `pull_request`.
- Treats the lockfile as an Ask First option in public preview (medium confidence) and defaults to SHA pinning plus Dependabot version updates.
- Notes actionlint and act are community tools, not official.

**Fail signals:** adopts the lockfile without asking; calls the community tools official.
