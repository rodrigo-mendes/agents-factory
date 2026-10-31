# Always-do patterns (gh 2.103.x)

Back to [SKILL.md](../SKILL.md). Commands are representative; adapt owner, numbers and IDs. Sources fetched 2026-10-29.

## Token scope and credential

```bash
export GH_TOKEN="$TOKEN"          # wins over GITHUB_TOKEN and stored credentials
export GH_PROMPT_DISABLED=1 NO_COLOR=1 GH_NO_UPDATE_NOTIFIER=1
gh auth status --json hosts       # exit 0 even with auth problems when --json is used
# organization-owned project -> TOKEN = GitHub App installation token (organization Projects read and write)
# user-owned project         -> TOKEN = classic PAT with project + repo
```

- Scope: https://cli.github.com/manual/gh_project and https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects (GraphQL: `read:project` for queries, `project` for queries and mutations).
- Credential split: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions
- Env vars: https://cli.github.com/manual/gh_help_environment ; status: https://cli.github.com/manual/gh_auth_status

More in [auth and tokens](./auth-and-tokens.md).

## ID-based item-edit, one field per call

```bash
gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$STATUS_FIELD_ID" \
   --single-select-option-id "$OPTION_ID"
gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$TEXT_FIELD_ID" --text "feature: add-login"
gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$DATE_FIELD_ID" --date 2026-11-15
gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$NUM_FIELD_ID" --number 3
gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$ITER_FIELD_ID" --iteration-id "$ITER_ID"
gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$TEXT_FIELD_ID" --clear
```

Manual: "For non-draft items, you can update only one field value per invocation." Source: https://cli.github.com/manual/gh_project_item-edit

## Add first, update second

```bash
ITEM_ID=$(gh api graphql -f query='mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}' \
          -f p="$PROJECT_ID" -f c="$ISSUE_NODE_ID" --jq .data.addProjectV2ItemById.item.id)
```

`contentId` is the issue node ID; the returned item ID is what `item-edit` needs. Adding an existing item returns the existing item ID, so the add is idempotent. Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects. The `gh project item-add` variant is in [projects, fields and items](./projects-fields-and-items.md).

## Machine-readable output

```bash
gh project field-list 7 --owner my-org -L 100 --format json
gh issue view 42 -R my-org/repo --json number,title,state,labels,projectItems
gh api repos/my-org/repo/issues/42 --jq '{id, node_id, number}'
```

`gh project *` uses `--format json`, not `--json`. `gh label create`, `gh issue comment` and `gh issue close` have no JSON flag; use `gh api` when an ID is needed. Sources: https://cli.github.com/manual/gh_help_formatting , https://cli.github.com/manual/gh_label_create

## Limits and pagination

```bash
gh api graphql --paginate --slurp -F number=7 -f owner=my-org -f query='
  query($owner:String!, $number:Int!, $endCursor:String) {
    organization(login:$owner) { projectV2(number:$number) {
      items(first:100, after:$endCursor) {
        nodes { id content { ... on Issue { id number url } } }
        pageInfo { hasNextPage endCursor } } } } }'
```

`--paginate` needs a `$endCursor: String` variable and `pageInfo { hasNextPage, endCursor }`; `--slurp` wraps pages in one array. Source: https://cli.github.com/manual/gh_api

## Serial writes with backoff

- At least one second between POST, PATCH, PUT and DELETE; no concurrency.
- On a secondary limit wait `retry-after` seconds; else, if `x-ratelimit-remaining` is 0, wait until `x-ratelimit-reset`; else wait at least one minute; then exponential backoff, then stop.
- Sources: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api , https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api

Runner and header handling: [GraphQL and rate limits](./graphql-and-rate-limits.md).

## Sub-issues (gh 2.94.0 or newer)

```bash
gh --version                                           # expect 2.103.x, at least 2.94.0
gh issue create -R my-org/repo --title "Task 1.2" --body-file task.md --parent 100
gh issue edit 100 -R my-org/repo --add-sub-issue 123,124
SUB_ID=$(gh api repos/my-org/repo/issues/123 --jq .id)
gh api -X POST repos/my-org/repo/issues/100/sub_issues -F sub_issue_id="$SUB_ID"
```

REST `sub_issue_id` is the issue `id`, not its number; `replace_parent` is optional. Sources: https://cli.github.com/manual/gh_issue_create , https://cli.github.com/manual/gh_issue_edit , https://docs.github.com/en/rest/issues/sub-issues

## Reading comments

```bash
gh api --paginate "repos/my-org/repo/issues/42/comments?per_page=100&since=2026-10-01T00:00:00Z" \
   --jq '.[] | {id, login: .user.login, created_at, body}'
```

Fields: `id`, `user.login` (`user` may be null), `created_at`, `updated_at`, `body`, `author_association`; ordered by ascending ID. Source: https://docs.github.com/en/rest/issues/comments

## Exit codes

```python
RC = {0: "ok", 1: "failure", 2: "cancelled", 4: "authentication required"}
```

Source: https://cli.github.com/manual/gh_help_exit-codes

Topic detail: [issues, sub-issues and comments](./issues-sub-issues-and-comments.md), [non-interactive use and Windows](./non-interactive-and-windows.md).
