# Never-do patterns (gh 2.103.x)

Back to [SKILL.md](../SKILL.md). Every row is high confidence and has an alternative. Sources fetched 2026-10-29.

## N1 GITHUB_TOKEN for Projects (severity high)

"`GITHUB_TOKEN` is scoped to the repository level and cannot access projects." Every project call fails.

```bash
# ❌ GH_TOKEN="${GITHUB_TOKEN}" gh project item-add 7 --owner my-org --url "$ISSUE_URL"
# ✅
GH_TOKEN="${APP_INSTALLATION_TOKEN}" gh project item-add 7 --owner my-org --url "$ISSUE_URL" --format json
```

Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions

## N2 Fine-grained PAT for a user-owned project (severity high)

The PAT page lists "Using fine-grained personal access token to access Projects owned by a user account" as a limitation.

```bash
# ❌ export GH_TOKEN=github_pat_xxx    # fine-grained, user project
# ✅
export GH_TOKEN=ghp_xxx                # classic PAT with project,repo
```

Fine-grained tokens do have an organization Projects permission. Source: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

## N3 Wrong ID or combined add and update (severity high)

`itemId` is the project item ID from the add call; `contentId` is the issue node ID. "You cannot add and update an item in the same call."

```bash
# ❌ gh project item-edit --id "$ISSUE_NODE_ID" --project-id "$P" --field-id "$F" --text x
# ✅ add via addProjectV2ItemById, then:
gh project item-edit --id "$ITEM_ID" --project-id "$P" --field-id "$F" --text x
```

Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects

## N4 Item field mutation for Labels, Assignees, Milestone, Repository (severity moderate)

"You cannot use `updateProjectV2ItemFieldValue` to change `Assignees`, `Labels`, `Milestone`, or `Repository`."

```bash
# ❌ gh project item-edit --id "$ITEM" --project-id "$P" --field-id "$LABELS_FIELD" --text "feature"
# ✅
gh issue edit 42 -R my-org/repo --add-label "feature"
```

GraphQL alternatives: `addLabelsToLabelable`, `addAssigneesToAssignable`, `updateIssue`, `transferIssue`. Sources: the API guide above and https://cli.github.com/manual/gh_issue_edit

## N5 Table output or --comments with --json (severity high)

Piped `--comments` prints only comments as text; since 2.99.0 `--comments` with `--json` is rejected ("fix(view): reject `--comments` with `--json`", https://github.com/cli/cli/releases/tag/v2.99.0). `--jq` and `--template` need `--json`.

```bash
# ❌ gh issue view 42 --comments | grep APPROVED
# ✅
gh api --paginate repos/my-org/repo/issues/42/comments --jq '.[] | {id, login: .user.login, created_at, body}'
```

Sources: https://cli.github.com/manual/gh_issue_view , https://cli.github.com/manual/gh_help_formatting , https://github.com/cli/cli/releases/tag/v2.99.0

## N6 Parallel bursts without backoff (severity high)

About 80 content-creating requests per minute and 500 per hour; at most 100 concurrent; "Continuing to make requests while you are rate limited may result in the banning of your integration."

```python
# ❌ with ThreadPoolExecutor(16) as ex: ex.map(create_issue, tasks)
# ✅
for t in tasks:
    create_issue(t)
    time.sleep(1)      # plus retry-after / x-ratelimit-reset handling
```

Sources: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api , https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api

## N7 Interactive auth from an agent (severity moderate)

Family policy for non-interactive agents (not a manual statement): never start `gh auth login` or `gh auth refresh`. The manual documents `gh auth refresh` as a browser or device-code flow, and `--web` and `--editor` open external programs.

```bash
# ❌ gh auth refresh -s project           # from an agent
# ✅ export GH_TOKEN="$TOKEN"; GH_PROMPT_DISABLED=1 gh issue create -R my-org/repo --title "T" --body-file body.md
```

The exact non-TTY failure text when a flag is missing is (unverified); see [register](./unverified-and-risks.md#unverified-4). Sources: https://cli.github.com/manual/gh_auth_refresh , https://cli.github.com/manual/gh_help_environment

## N8 Logging gh auth status from gh older than 2.97.0 (severity high)

Release 2.97.0 fixed GHSA-cg6r-mpgc-h9mm: `gh auth status` printed part of `github_pat_*`, `ghs_*` and `ghu_*` tokens.

```bash
# ❌ gh auth status >> ci.log             # on gh < 2.97.0
# ✅ gh --version  (pin 2.103.x), then: gh auth status --json hosts
```

Source: https://github.com/cli/cli/releases/tag/v2.97.0
