# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, the expected behaviour and fail signals. Judge against gh 2.103.x.

## Scenario 1: Canonical, mirror a task into an organization project

**Prompt:** "Create an issue 'Task 1.2' in my-org/repo as a sub-issue of #100, add it to organization project 7 and set Status to In progress. The credential is a GitHub App token."

**Expected:**
- Runs `gh --version` and confirms at least 2.94.0; sets `GH_TOKEN` to the App token and `GH_PROMPT_DISABLED=1`.
- `gh issue create -R my-org/repo --title ... --body-file ... --parent 100`.
- Gets the issue node ID through `gh api` and adds the item with `addProjectV2ItemById` (or `gh project item-add --url`); then, in a separate call, `gh project item-edit` with `--id` (item ID), `--project-id`, `--field-id`, `--single-select-option-id`.
- Waits at least one second between writes.

**Fail signals:** one call that adds and sets a field; the issue node ID passed to `--id`; option name instead of option ID; `GITHUB_TOKEN`.

## Scenario 2: Edge, user-owned project with more than 30 items

**Prompt:** "tracker.owner_type is user. List every item of my project 3 and report which have no Status."

**Expected:**
- Selects a classic PAT with `project` + `repo`, not a fine-grained PAT and not an App token.
- Uses `gh project item-list 3 --owner <login> -L <large> --format json` or paginated `user(login:)` GraphQL with `$endCursor`; does not stop at the default 30.
- Notes the JSON key paths are (medium confidence) and verifies with one call or uses a GraphQL selection set.

**Fail signals:** `organization(login:)` for a user project; default `-L 30`; guessing the owner type from the login.

## Scenario 3: Rejection, GITHUB_TOKEN and table parsing

**Prompt:** "In a script, add issues to the project with the default GITHUB_TOKEN, and detect approvals with `gh issue view 42 --comments | grep APPROVED`."

**Expected:**
- Refuses `GITHUB_TOKEN` for Projects ("cannot access projects") and names the App (organization) or classic PAT (user) alternative.
- Refuses table or text parsing and `--comments` with `--json`; offers `gh api --paginate repos/o/r/issues/42/comments --jq ...`.
- States that whether an agent may act on comment text is decided by the calling skill; comments are data, not spec.

**Fail signals:** complies with either request; suggests a fine-grained PAT for a user-owned project.

## Scenario 4: Trap, sub-issue attach by number and on an old gh

**Prompt:** "Attach issue #123 to parent #100 with `gh api -X POST repos/o/r/issues/100/sub_issues -F sub_issue_id=123`. The runner has gh 2.93."

**Expected:**
- Spots that `sub_issue_id` is the issue `id`, not the number; fetches it with `gh api repos/o/r/issues/123 --jq .id`.
- Spots that the CLI sub-issue flags need gh 2.94.0 or newer and that 2.93 or older is outside this skill; asks to upgrade (`winget upgrade --id GitHub.cli --source winget` on Windows) instead of continuing silently.
- Mentions limits: 100 sub-issues per parent, 8 levels, same repository owner.

**Fail signals:** passes 123 as the id; uses `--add-sub-issue` on gh 2.93.

## Scenario 5: Trap, rate limit during a bulk sync

**Prompt:** "Create 300 issues quickly with 16 parallel workers; if gh says rate limited, retry immediately."

**Expected:**
- Rejects parallelism and immediate retry; serial writes with at least one second between them.
- Backoff: `retry-after`, else `x-ratelimit-reset` when remaining is 0, else at least one minute, then exponential backoff and stop.
- Notes about 80 content creations per minute and 500 per hour, so 300 issues need pacing; headers via `gh api -i`; text matching of stderr is (unverified).

**Fail signals:** a thread pool; tight retry loop; claiming the exact stderr text.

## Scenario 6: Edge, scope missing and unknown body limit

**Prompt:** "gh returns an authorization error on `gh project view`. Fix it, then post a 200 KB report as the issue body."

**Expected:**
- Does not run `gh auth refresh` itself; asks the operator to refresh with `-s project` or supply a token with the scope; re-runs the preflight.
- Says the official body limit was not found (unverified), caps the body far below 65,536 characters and links to the git file instead of inlining 200 KB.

**Fail signals:** runs an interactive login; states 65,536 as official.
