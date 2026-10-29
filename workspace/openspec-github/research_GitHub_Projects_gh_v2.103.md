# Research — GitHub CLI (gh) 2.103.x + GitHub Projects (v2) API

Unit: U2 (pilot) — source item: framework "gh + Projects v2". Proposed skill: `managing-github-projects-gh-v2-103`.
Consumers: non-interactive Python scripts and agents (OpenSpec bridge) that mirror changes, tasks, ADRs,
escalations and spec-deltas as issues + project items with custom fields, and read issue comments.

All pages below were read on **2026-10-29** unless stated otherwise. Tags follow family rule 2:
`(medium confidence)`, `(unverified)`. "Partly read" marks pages where only part of the text was read.

---

## Metadata

```yaml
Full_Name: GitHub CLI (gh) + GitHub Projects (ProjectV2) GraphQL/REST API + Issues/sub-issues REST/GraphQL
Target_Version: gh 2.103.x (latest patch 2.103.3, 2026-10-26); GitHub REST API version 2026-03-10; GraphQL API (unversioned, github.com)
Release_Date: gh 2.103.0 2026-10-21; 2.103.3 2026-10-26
Support_Status: Active (current stable line)
Primary_Docs: https://cli.github.com/manual/ ; https://docs.github.com/en/issues/planning-and-tracking-with-projects
Official_Repo: https://github.com/cli/cli
Research_Date: 2026-10-29
Domain_Complexity: Standard (CLI + two APIs, auth split, rate limits; not crypto/compliance-critical)
Research_Depth: standard
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 3 of 5
Triangulated_Count: 0   # depth=standard: triangulation not required; several patterns have 2 sources anyway (noted inline)
Unverified_Count: 7
Irresolvable_Count: 1
Research_Quality_Score: 89%   # ~64 claims, 7 unverified/irresolvable
```

Process notes (deviations from the framework-researcher P0–P5 workflow, at the caller's explicit instruction):
- No `section-investigator` / `research-synthesizer` agents were spawned; all pages were fetched directly.
- No plan-mode gate: the caller relayed an approval recorded in `workspace/openspec-github/PIPELINE_STATE.md#approvals`. This agent did not obtain or verify that approval itself.
- The output file was written directly (not via `research-synthesizer`).

---

## Executive Summary

GitHub CLI (`gh`) 2.103.x drives GitHub Projects (v2) through three surfaces: the `gh project` command group
(19 subcommands, JSON via `--format json`), `gh issue` / `gh label` for issue content, and `gh api` for raw REST
and GraphQL calls. A project item is a separate object from the issue it wraps: `gh project item-add` /
`addProjectV2ItemById` take the issue's *content* node ID (or URL) and return a *project item* ID, and every
field update (`gh project item-edit`, `updateProjectV2ItemFieldValue`) targets the item ID plus the field ID
(and, for single-select, the option ID). Projects need the `project` token scope (`read:project` for read-only
GraphQL); `GITHUB_TOKEN` in Actions cannot reach projects at all.

Changes relevant to the bridge between gh 2.93 and 2.103: **2.94.0 (2026-06-10)** added Issues 2.0 —
issue types, sub-issues (`gh issue create --parent`, `gh issue edit --add-sub-issue/--remove-sub-issue/--parent/--remove-parent`)
and blocked-by/blocking relationships; **2.97.0 (2026-07-31)** added name-based `gh project item-edit`
(`--field` + `--value`) and named field columns in `item-list`, and fixed four security advisories
(including partial token printing by `gh auth status`); **2.98.0** fixed `item-add` output for non-TTY;
**2.99.0** added `--attach` and made `gh issue view --comments --json` an error; **2.103.x** added
refreshable-token handling in `gh auth` and the `gh issue artifact` group (out of scope here).

Three critical patterns: (1) authenticate with a token carrying the `project` scope — GitHub App for
organization projects, **classic** PAT for user projects (fine-grained PATs cannot access user-owned projects);
(2) in scripts use ID-based flags (`--id`, `--field-id`, `--project-id`, `--single-select-option-id`) and
`--format json`, add then update in separate calls, one field per call; (3) serialize writes, pause ≥ 1 s between
mutations, and honour `retry-after` / `x-ratelimit-reset` — content creation is capped at ~80/min and ~500/h.
Domain tier **Standard**: multiple integrations and an auth split, but no encryption/compliance surface.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (official source, read in full or the relevant section, dated ≤12mo) | 🟡 Medium (1 partial source, source code on trunk, or summarised release list) | 🔴 Low (community — not used for guardrails)

### ✅ Mandatory Patterns

**A1. Token must carry the `project` scope (classic/OAuth), checked before any project call**
> Confidence: 🟢 High | Sources: gh_project manual + using-the-api-to-manage-projects (both 2026-10-29)
- Why: "The minimum required scope for the token is: `project`." (gh project). GraphQL: "`read:project` scope (for queries) or `project` scope (for queries and mutations)."
- Code (gh 2.103.x):
  ```bash
  gh auth status --json hosts          # exit 0 even with auth problems when --json is used
  gh auth refresh -s project           # interactive (browser/device flow) — operator step, not for agents
  ```
- Source: https://cli.github.com/manual/gh_project (2026-10-29); https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects (2026-10-29); https://cli.github.com/manual/gh_auth_status (2026-10-29)

**A2. Credential by owner type: GitHub App (org projects) / classic PAT with `project` + `repo` (user projects); never `GITHUB_TOKEN`**
> Confidence: 🟢 High | Sources: automating-projects-using-actions + managing-your-personal-access-tokens (2026-10-29)
- Why: "`GITHUB_TOKEN` is scoped to the repository level and cannot access projects." The page recommends a GitHub App for organization projects and "a personal access token (classic) with the `project` and `repo` scopes" for user projects. The PAT page lists as a fine-grained limitation: "Using fine-grained personal access token to access Projects owned by a user account." Fine-grained PATs do have an **organization** "Projects" permission (read/write/admin).
- Code:
  ```bash
  # owner_type=organization -> GH_TOKEN=<GitHub App installation token, org Projects: read & write>
  # owner_type=user         -> GH_TOKEN=<classic PAT with project,repo>
  export GH_TOKEN="$TOKEN"   # GH_TOKEN wins over GITHUB_TOKEN and stored credentials
  ```
- Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions (2026-10-29); https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens (2026-10-29); https://cli.github.com/manual/gh_help_environment (2026-10-29)

**A3. Inject the token through `GH_TOKEN` (env), not `gh auth login`, in non-interactive runs**
> Confidence: 🟢 High
- Why: "`GH_TOKEN`, `GITHUB_TOKEN` (in order of precedence): an authentication token … Setting this avoids being prompted to authenticate and takes precedence over previously stored credentials." `gh auth login` docs: "Favour setting `GH_TOKEN` for fine-grained personal access token usage."
- Code: see A2. Also set `GH_PROMPT_DISABLED=1` ("set to any value to disable interactive prompting in the terminal"), `NO_COLOR=1`, `GH_NO_UPDATE_NOTIFIER=1` (update notice goes to stderr).
- Source: https://cli.github.com/manual/gh_help_environment (2026-10-29); https://cli.github.com/manual/gh_auth_login (2026-10-29)

**A4. Use ID-based `item-edit` flags in scripts; one field per call; single-select needs option ID**
> Confidence: 🟢 High
- Why: manual: "Scripts and automation: Use GraphQL node IDs with `--id`, `--field-id`, and `--project-id`. For single-select fields, add `--single-select-option-id`." "For non-draft items, you can update only one field value per invocation." Name-based `--field`/`--value` exists since 2.97.0 but resolves names at runtime.
- Code (gh 2.103.x):
  ```bash
  gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
     --field-id "$STATUS_FIELD_ID" --single-select-option-id "$OPTION_ID" --format json
  gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$TEXT_FIELD_ID" --text "change/add-login"
  gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$DATE_FIELD_ID" --date 2026-11-15
  gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$NUM_FIELD_ID" --number 3
  gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$ITER_FIELD_ID" --iteration-id "$ITER_ID"
  gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$TEXT_FIELD_ID" --clear
  ```
- Source: https://cli.github.com/manual/gh_project_item-edit (2026-10-29); https://github.com/cli/cli/releases/tag/v2.97.0 (2026-10-29)

**A5. Add first, update second (item ID ≠ content ID)**
> Confidence: 🟢 High | two sources: GraphQL guide + gh manual
- Why: "You cannot add and update an item in the same call." `addProjectV2ItemById` takes `projectId` + `contentId` (issue/PR node ID) and returns `item { id }`; "Adding an existing item returns the existing item's ID" (idempotent add). `gh project item-add` takes the issue `--url`.
- Code:
  ```bash
  ITEM_ID=$(gh project item-add 7 --owner my-org --url "https://github.com/my-org/repo/issues/42" --format json --jq .id)  # .id key: (medium confidence)
  ```
- Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects (2026-10-29); https://cli.github.com/manual/gh_project_item-add (2026-10-29)

**A6. Machine-readable output only: `--format json` for `gh project`, `--json` for `gh issue`, `gh api` for the rest**
> Confidence: 🟢 High
- Why: every `gh project` subcommand documents `--format <string>` (only value `json`) plus `-q/--jq`; `gh issue view` documents `--json <fields>`; formatting help: "you must pass the `--json` flag and field names to use the `--jq` or `--template` flags", and jq need not be installed.
- Note for family rule 7: `gh project *` uses `--format json`, **not** `--json`; `gh label create`, `gh issue comment`, `gh issue close` have no JSON output flag (they print a URL/nothing) — use `gh api` when an ID is needed.
- Source: https://cli.github.com/manual/gh_project_item-list (2026-10-29); https://cli.github.com/manual/gh_issue_view (2026-10-29); https://cli.github.com/manual/gh_help_formatting (2026-10-29); https://cli.github.com/manual/gh_label_create (2026-10-29)

**A7. Always pass a large enough `--limit` (default 30) or paginate GraphQL with `$endCursor`**
> Confidence: 🟢 High
- Why: `item-list`, `field-list`, `project list` default `-L 30`. A project can have "up to 50 fields" and "a maximum of 50,000 items across both active views and the archive page". `gh api --paginate` for GraphQL requires a `$endCursor: String` variable and `pageInfo { hasNextPage, endCursor }`; `--slurp` wraps pages in one array. GraphQL connections need `first`/`last` in 1–100.
- Code:
  ```bash
  gh project field-list 7 --owner my-org -L 100 --format json
  gh api graphql --paginate --slurp -F number=7 -f owner=my-org -f query='
    query($owner:String!, $number:Int!, $endCursor:String) {
      organization(login:$owner) { projectV2(number:$number) {
        items(first:100, after:$endCursor) {
          nodes { id content { ... on Issue { id number url } } }
          pageInfo { hasNextPage endCursor } } } } }'
  ```
- Source: https://cli.github.com/manual/gh_api (2026-10-29); https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects (2026-10-29); https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project (2026-10-29); https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api (2026-10-29)

**A8. Serialize writes, ≥ 1 s between mutations, honour `retry-after`/`x-ratelimit-reset`, exponential backoff**
> Confidence: 🟢 High | two sources: REST rate limits + REST best practices (+ GraphQL limits page)
- Why: secondary limits — ≤ 100 concurrent requests; 900 points/min per REST endpoint, 2,000/min GraphQL; ~80 content-generating requests/min and 500/h; mutations cost 5 points. "make requests serially instead of concurrently", "wait at least one second between each request" for POST/PATCH/PUT/DELETE. On secondary limit: wait `retry-after` seconds; else if `x-ratelimit-remaining` = 0 wait until `x-ratelimit-reset`; else wait ≥ 1 minute; on repeated failures exponential backoff then stop. "Continuing to make requests while you are rate limited may result in the banning of your integration."
- Source: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api (2026-10-29); https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api (2026-10-29); https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api (2026-10-29)

**A9. Sub-issues: use gh ≥ 2.94.0 flags or REST with the issue `id` (not number)**
> Confidence: 🟢 High (flags + REST) | min version from release tag page 🟢
- Why: `gh issue create --parent <number|url>`; `gh issue edit --add-sub-issue 123,124`, `--remove-sub-issue`, `--parent`, `--remove-parent`. Released in v2.94.0 ("Add Issues 2.0 support: issue types, sub-issues, and relationships", 10 Jun). REST `POST /repos/{o}/{r}/issues/{n}/sub_issues` body `sub_issue_id` = the issue's `id` field, optional `replace_parent`. Limits: 100 sub-issues per parent, 8 nesting levels; sub-issue must share the parent's repository owner.
- Code:
  ```bash
  gh issue create -R my-org/repo --title "Task 1.2" --body-file task.md --parent 100
  gh issue edit 100 -R my-org/repo --add-sub-issue 123,124
  SUB_ID=$(gh api repos/my-org/repo/issues/123 --jq .id)
  gh api -X POST repos/my-org/repo/issues/100/sub_issues -F sub_issue_id="$SUB_ID"
  ```
- Source: https://cli.github.com/manual/gh_issue_create (2026-10-29); https://cli.github.com/manual/gh_issue_edit (2026-10-29); https://github.com/cli/cli/releases/tag/v2.94.0 (2026-10-29); https://docs.github.com/en/rest/issues/sub-issues (2026-10-29); https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues (2026-10-29)

**A10. Read comments with `gh issue view --json comments` or REST (`since`, `per_page≤100`); never `--comments` with `--json`**
> Confidence: 🟢 High (flags/REST) / 🟡 Medium (JSON key names inside `comments`)
- Why: `gh issue view` JSON fields include `comments`, `subIssues`, `parent`, `projectItems`, `reactionGroups`. 2.99.0: "fix(view): reject `--comments` with `--json`". Piped `--comments` prints only comments as text (not stable). REST `GET /repos/{o}/{r}/issues/{n}/comments` returns `id`, `user.login` (`user` may be null), `created_at`, `updated_at`, `body`, `author_association`, ordered by ascending ID, `since` = ISO 8601 updated-after.
- Code:
  ```bash
  gh api --paginate "repos/my-org/repo/issues/42/comments?per_page=100&since=2026-10-01T00:00:00Z" \
     --jq '.[] | {id, login: .user.login, created_at, body}'
  gh issue view 42 -R my-org/repo --json comments --jq '.comments[] | {a: .author.login, t: .createdAt}'   # key names (medium confidence)
  ```
- Source: https://cli.github.com/manual/gh_issue_view (2026-10-29); https://github.com/cli/cli/releases (2026-10-29); https://docs.github.com/en/rest/issues/comments (2026-10-29)

### ⚠️ Conditional Patterns

**C1. gh porcelain vs `gh api graphql`**
> Confidence: 🟢 High (both options documented)
- Options: (A) `gh project item-add/item-edit` with ID flags; (B) `gh api graphql` with `addProjectV2ItemById` / `updateProjectV2ItemFieldValue` / `clearProjectV2ItemFieldValue` / `archiveProjectV2Item`.

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A gh project | short commands, gh resolves owner/number | one field per process spawn; JSON shape not documented in manual | few writes, readable scripts |
  | B gh api graphql | exact schema (`ProjectV2FieldValue`: text, number Float, date Date, singleSelectOptionId, iterationId, multiSelectOptionIds), one request per mutation, aliases | must manage node IDs and pagination yourself | bulk sync, MULTI_SELECT fields, archived-state queries |

- Agent: "Ask the user whether the bridge favours readability (A) or a single GraphQL client (B)."
- Source: https://docs.github.com/en/graphql/reference/projects (2026-10-29); https://cli.github.com/manual/gh_project_item-edit (2026-10-29)

**C2. Owner type: organization vs user project**
> Confidence: 🟢 High
- Options: `organization(login:)` vs `user(login:)` lookup; `--owner my-org` vs `--owner "@me"`/login; credential App vs classic PAT (A2).
- Agent: "Ask `tracker.owner_type` (organization | user); never guess from the login."
- Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects (2026-10-29)

**C3. Field data types and creation path**
> Confidence: 🟢 High
- `gh project field-create --data-type` accepts only `TEXT`, `SINGLE_SELECT`, `DATE`, `NUMBER` (+ `--single-select-options`). ITERATION and MULTI_SELECT exist in the GraphQL `ProjectV2FieldType` enum, but gh 2.103 cannot create them; how to create them via API is (unverified) — options: create in the UI once, or research `createProjectV2Field`.
- Agent: "Ask whether iteration fields are needed; if yes, the field is created manually and the bridge only reads its ID."
- Source: https://cli.github.com/manual/gh_project_field-create (2026-10-29); https://docs.github.com/en/graphql/reference/projects (2026-10-29)

**C4. Draft issues vs real issues**
> Confidence: 🟢 High
- `gh project item-create --title --body` / `addProjectV2DraftIssue` create draft items (no repo issue, no comments, no sub-issues). Real issues need a repository and support comments/sub-issues.
- Agent: "Ask whether escalations need a comment thread (then real issue) or are board-only notes (draft)."
- Source: https://cli.github.com/manual/gh_project_item-create (2026-10-29); https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects (2026-10-29)

**C5. Editing a comment in place**
> Confidence: 🟢 High
- Options: (A) `gh issue comment N --edit-last [--create-if-none] --body-file f` — acts only on *your own* most recent comment; (B) REST `PATCH /repos/{o}/{r}/issues/comments/{comment_id}` with `body` — exact comment, needs the stored comment ID (fine-grained: Issues write).
- Agent: "Ask whether the bridge keeps one status comment per issue (store its ID, use B)."
- Source: https://cli.github.com/manual/gh_issue_comment (2026-10-29); https://docs.github.com/en/rest/issues/comments (2026-10-29); https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens (2026-10-29)

### 🚫 Forbidden Patterns

**N1. Using `GITHUB_TOKEN` for Projects**
> Severity: Critical | Confidence: 🟢 High
- Why: "`GITHUB_TOKEN` is scoped to the repository level and cannot access projects."
- Impact: every project call fails ("Resource not accessible").
- ❌ Wrong:
  ```bash
  GH_TOKEN="${GITHUB_TOKEN}" gh project item-add 7 --owner my-org --url "$ISSUE_URL"
  ```
- ✅ Correct:
  ```bash
  GH_TOKEN="${APP_INSTALLATION_TOKEN}" gh project item-add 7 --owner my-org --url "$ISSUE_URL" --format json
  ```
- Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions (2026-10-29)

**N2. Fine-grained PAT for a user-owned project**
> Severity: High | Confidence: 🟢 High
- Why: "Using fine-grained personal access token to access Projects owned by a user account" is a listed limitation.
- Impact: auth/permission errors on `user(login:){projectV2}` mutations.
- ❌ Wrong:
  ```bash
  export GH_TOKEN=github_pat_xxx   # fine-grained, user project
  ```
- ✅ Correct:
  ```bash
  export GH_TOKEN=ghp_xxx          # classic PAT with project,repo scopes
  ```
- Source: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens (2026-10-29); automating-projects-using-actions (2026-10-29)

**N3. Adding and setting fields in one mutation / passing the issue ID as `itemId`**
> Severity: High | Confidence: 🟢 High
- Why: "You cannot add and update an item in the same call." `itemId` is the project item ID returned by `addProjectV2ItemById`, `contentId` is the issue node ID.
- ❌ Wrong:
  ```bash
  gh project item-edit --id "$ISSUE_NODE_ID" --project-id "$P" --field-id "$F" --text x
  ```
- ✅ Correct:
  ```bash
  ITEM_ID=$(gh api graphql -f query='mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}' \
            -f p="$P" -f c="$ISSUE_NODE_ID" --jq .data.addProjectV2ItemById.item.id)
  gh project item-edit --id "$ITEM_ID" --project-id "$P" --field-id "$F" --text x
  ```
- Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects (2026-10-29)

**N4. Using `updateProjectV2ItemFieldValue` for Labels/Assignees/Milestone/Repository**
> Severity: Medium | Confidence: 🟢 High
- Why: "You cannot use `updateProjectV2ItemFieldValue` to change `Assignees`, `Labels`, `Milestone`, or `Repository`"; use `addLabelsToLabelable`, `addAssigneesToAssignable`, `updateIssue`, `transferIssue` — or `gh issue edit --add-label`.
- ❌ Wrong:
  ```bash
  gh project item-edit --id "$ITEM" --project-id "$P" --field-id "$LABELS_FIELD" --text "spec-delta"
  ```
- ✅ Correct:
  ```bash
  gh issue edit 42 -R my-org/repo --add-label "spec-delta"
  ```
- Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects (2026-10-29); https://cli.github.com/manual/gh_issue_edit (2026-10-29)

**N5. Parsing human/table output or combining `--comments` with `--json`**
> Severity: High | Confidence: 🟢 High
- Why: piped `--comments` prints only comments as text; since 2.99.0 `--comments` with `--json` is rejected. Formatting help: `--jq`/`--template` need `--json`.
- ❌ Wrong:
  ```bash
  gh issue view 42 --comments | grep APPROVED
  ```
- ✅ Correct:
  ```bash
  gh api --paginate repos/my-org/repo/issues/42/comments --jq '.[] | {id, login: .user.login, created_at, body}'
  ```
- Source: https://cli.github.com/manual/gh_issue_view (2026-10-29); https://github.com/cli/cli/releases (2026-10-29)

**N6. Parallel bursts of issue/comment creation without backoff**
> Severity: High | Confidence: 🟢 High
- Why: ~80 content-creating requests/min, 500/h; 100 concurrent max; risk of ban.
- ❌ Wrong:
  ```python
  with ThreadPoolExecutor(16) as ex: ex.map(create_issue, tasks)
  ```
- ✅ Correct:
  ```python
  for t in tasks: create_issue(t); time.sleep(1)   # + retry-after / reset handling (see Implementation Blueprint)
  ```
- Source: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api (2026-10-29); https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api (2026-10-29)

**N7. Running `gh auth refresh` / `gh auth login` / `--web` / `--editor` from an agent**
> Severity: Medium | Confidence: 🟢 High (browser flow) / 🟡 Medium (exact failure mode in non-TTY)
- Why: `gh auth refresh` opens a browser/device-code flow; `--editor`/`--web` open external programs. Missing `--title`/`--body` makes `gh issue create` prompt.
- ❌ Wrong:
  ```bash
  gh issue create -R my-org/repo            # prompts for title/body
  ```
- ✅ Correct:
  ```bash
  GH_PROMPT_DISABLED=1 gh issue create -R my-org/repo --title "T" --body-file body.md
  ```
- Source: https://cli.github.com/manual/gh_auth_refresh (2026-10-29); https://cli.github.com/manual/gh_issue_create (2026-10-29); https://cli.github.com/manual/gh_help_environment (2026-10-29)

---

## Migration Guide

> Confidence: 🟢 High for items read on tag pages (2.94.0, 2.97.0, 2.103.3); 🟡 Medium for items read only from the paginated release list (partly read: dependency sections truncated).
> Sources: https://github.com/cli/cli/releases and ?page=2 (2026-10-29); tag pages v2.94.0, v2.97.0, v2.103.3 (2026-10-29). Release-list dates show no year; year 2026 taken from asset timestamps and F1.

**Breaking / behaviour changes 2.93 → 2.103 (scope commands only)**

| Version (date) | Change | Impact on bridge |
|---|---|---|
| 2.93.0 (2026-05-27) | `gh auth refresh` hint printed on 401; TUF auth-header leak fixed | none |
| 2.94.0 (2026-06-10) | **Issues 2.0**: issue types (`--type`), sub-issues (`--parent`, `--add-sub-issue`, `--remove-sub-issue`, `--remove-parent`), relationships (`--blocked-by`, `--blocking`); GHES 3.17+ for sub-issues, 3.19+ for relationships (medium confidence — from release-list summary) | **minimum gh for sub-issue flags** |
| 2.97.0 (2026-07-31) | name-based `gh project item-edit` (`--field`/`--value`); `item-list --field` named columns; security: GHSA-cg6r-mpgc-h9mm (`gh auth status` printed part of `github_pat_*`/`ghs_*`/`ghu_*` tokens), GHSA-4fjg-2h4q-fwg3 (unescaped URL path components), GHSA-3m3g-3wcr-px46 (terminal escapes) | require ≥ 2.97.0 in any case; logs from older `gh auth status` may hold token fragments |
| 2.98.0 (2026-08-20) | "Fix project item-add output for non-TTY" | parse `item-add` only with `--format json` (medium confidence) |
| 2.99.0 (2026-09-01) | `--attach` on `issue create/edit/comment`; `--comments` with `--json` now rejected | N5 |
| 2.102.0 (2026-09-30) | host versions removed from `item-list` help | none |
| 2.103.0–2.103.3 (2026-10-21..26) | refreshable/expiring tokens (`--expiring`, auto refresh in `gh auth status`, `--no-refresh`); `gh issue artifact` group | `gh auth status` may refresh tokens unless `--no-refresh` |

`⚠️ Migration Note`: A4 (name-based alternative) and A9 depend on APIs introduced in 2.97.0 / 2.94.0.

**Upgrade Steps (Windows, official WinGet package)**
1. `winget upgrade --id GitHub.cli --source winget`
2. Open a new terminal window (installer changes PATH).
3. `gh --version` — expect `gh version 2.103.x`.

**Compatibility Matrix**

| Dependency | Min | Max | Notes |
|---|---|---|---|
| gh | 2.94.0 (sub-issue flags) | 2.103.x pinned | family pins 2.103.x (F1) |
| REST API version header | 2026-03-10 | — | shown on sub-issues/comments pages |
| GHES (if ever used) | 3.17 (sub-issues), 3.19 (relationships) | — | (medium confidence) |

---

## Implementation Blueprint

> Confidence: 🟢 High for commands/flags (manual pages); 🟡 Medium for exact JSON keys of `gh project` output (source tests on trunk, not version-tagged).

**Lifecycle (bridge, gh 2.103.x)**
1. Preflight: `gh --version` (≥ 2.103.0), `gh auth status --json hosts` (or `gh api graphql -f query='{viewer{login}}'`), `GH_TOKEN` set, `GH_PROMPT_DISABLED=1`.
2. Resolve once and cache: project node ID, field IDs, single-select option IDs.
   ```bash
   gh api graphql -F number=7 -f owner=my-org -f query='
     query($owner:String!,$number:Int!){ organization(login:$owner){ projectV2(number:$number){ id
       fields(first:50){ nodes{
         ... on ProjectV2FieldCommon { id name dataType }
         ... on ProjectV2SingleSelectField { options { id name } }
         ... on ProjectV2IterationField { configuration { iterations { id startDate } } } } } } } }'
   ```
   (50 = documented max fields per project; `dataType` on `ProjectV2FieldCommon` is (medium confidence) — the guide's example requests only `id name`.)
3. Ensure labels: `gh label create spec-delta -R my-org/repo --color 5319E7 --description "OpenSpec delta" --force` (`--force` updates if it exists; color = 6-hex).
4. Create issue: `gh issue create -R my-org/repo --title ... --body-file - --label spec-delta [--parent N]` — prints the issue URL on stdout.
5. Add to project → item ID (A5); set fields one per call (A4).
6. Read comments (A10); edit own status comment (C5); react: `gh api -X POST repos/o/r/issues/comments/{id}/reactions -f content=eyes` (200 = already existed, 201 = created; values `+1 -1 laugh confused heart hooray rocket eyes`).
7. Close: `gh issue close 42 -R my-org/repo --reason completed|"not planned"|duplicate [--comment ...]`; archive item: `gh project item-archive 7 --owner my-org --id "$ITEM_ID"` (`--undo` to restore).

**Python wrapper (representative — adapt to your environment)**
```python
# gh 2.103.x — non-interactive runner with secondary-rate-limit backoff
import json, os, subprocess, time

ENV = {**os.environ, "GH_PROMPT_DISABLED": "1", "NO_COLOR": "1", "GH_NO_UPDATE_NOTIFIER": "1"}

def gh(*args, parse_json=True, mutating=False, retries=5):
    delay = 60                                   # docs: otherwise wait at least one minute
    for attempt in range(retries):
        p = subprocess.run(["gh", *args], capture_output=True, text=True, env=ENV, encoding="utf-8")
        if p.returncode == 0:
            if mutating:
                time.sleep(1)                    # docs: >= 1 s between mutative requests
            return json.loads(p.stdout) if parse_json and p.stdout.strip() else p.stdout
        if p.returncode == 4:                    # gh exit code 4 = authentication required
            raise RuntimeError("gh auth required: " + p.stderr)
        if "rate limit" in p.stderr.lower() and attempt < retries - 1:   # stderr wording: (unverified)
            time.sleep(delay); delay *= 2; continue
        raise RuntimeError(f"gh {' '.join(args)} failed ({p.returncode}): {p.stderr}")

# headers (retry-after, x-ratelimit-reset) are only visible with `gh api -i`; parsing them is the precise path.
```
Exit codes (gh): 0 success, 1 failure, 2 cancelled, 4 authentication required — https://cli.github.com/manual/gh_help_exit-codes (2026-10-29).

**Windows notes**
- PowerShell: quote arguments with `{owner}`/`{repo}` placeholders (gh_api manual). Prefer `subprocess` argument lists over shell strings.
- Config dir default on Windows: `$AppData/GitHub CLI` unless `GH_CONFIG_DIR`/`XDG_CONFIG_HOME` set (gh_help_environment).
- Install/upgrade: `winget install|upgrade --id GitHub.cli --source winget`; new terminal window after install (docs/install_windows.md).
- Use `--body-file` (file or `-` for stdin) for multi-line bodies; avoids shell quoting.

**Integration**: gh ↔ OpenSpec bridge — git stays canonical (family rule 4); GitHub writes are dry-run by default with `--apply` (rule 6). This research adds no OpenSpec facts (U4).

---

## Quality Control

**Verification Commands**
```bash
# Representative — adapt to your environment (gh 2.103.x)
gh --version                                   # Expected: gh version 2.103.x (...)
gh auth status --json hosts --jq '.hosts'      # Expected: exit 0; per-host account state
gh api graphql -f query='{viewer{login}}'      # Expected: {"data":{"viewer":{"login":"..."}}}
gh project field-list 7 --owner my-org -L 100 --format json --jq '.fields[] | {id,name,type}'
gh project item-list 7 --owner my-org -L 1000 --format json --jq '.totalCount'
gh api repos/my-org/repo/issues/100/sub_issues --jq 'length'
gh api rate_limit --jq '.resources.graphql'    # rate_limit endpoint: (medium confidence, not read this session)
```

**Mocking**
- Test the wrapper by substituting the `gh` executable (PATH shim returning canned JSON and exit codes 0/1/4), or by injecting the `subprocess.run` callable. No real GitHub calls in unit tests. (Testing approach is generic engineering practice — no official gh mocking guidance found (unverified).)
```python
def fake_run(args, **kw):
    class P: returncode=0; stdout='{"id":"PVTI_x"}'; stderr=""
    return P()
```

---

## Production Readiness

- **Performance**: one process per gh call; batch reads with GraphQL (≤100 per connection page, ≤500,000 nodes per call, 10 s timeout → 502/504 and extra point deduction).
- **Scalability**: 50,000 items per project including archived; 50 fields per project; 100 sub-issues per parent, 8 nesting levels; primary limits 5,000 points or requests/h for PAT/user, App installations 5,000–12,500 (15,000 on Enterprise Cloud REST; 10,000 GraphQL), `GITHUB_TOKEN` 1,000/h per repo.
- **Monitoring**: GraphQL `rateLimit { limit remaining used resetAt cost }`; headers `x-ratelimit-remaining/-reset/-used/-resource`; GraphQL primary-limit exhaustion still returns HTTP 200 with remaining 0; REST returns 403/429.
- **Security**: GH_TOKEN only via env/secret store; never `gh auth status --show-token` in logs; require gh ≥ 2.97.0 (token-fragment leak fixed); items the token cannot see return as `REDACTED`; use `If-None-Match` conditional requests (304 does not count against primary limit).

---

## Reference Implementations

- gh manual (official): https://cli.github.com/manual/gh_project , https://cli.github.com/manual/gh_issue
- Official GraphQL walkthrough with `gh api graphql` examples: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects
- Official Actions automation example (App/PAT): https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions (U3 owns Actions)
- gh source tests showing project JSON export shape (trunk, not tag-pinned): https://raw.githubusercontent.com/cli/cli/trunk/pkg/cmd/project/shared/queries/export_data_test.go

---

## Source Bibliography

**Primary — GitHub CLI manual (all read 2026-10-29; pages carry no version label, they document the current release 2.103.x)**
- https://cli.github.com/manual/gh_project — 19 subcommands; minimum scope `project`
- https://cli.github.com/manual/gh_project_create , _view , _list , _close , _link , _field-create , _field-list , _item-add , _item-create , _item-edit , _item-list , _item-archive
- https://cli.github.com/manual/gh_issue_create , gh_issue_edit , gh_issue_view , gh_issue_comment , gh_issue_close
- https://cli.github.com/manual/gh_label_create
- https://cli.github.com/manual/gh_api
- https://cli.github.com/manual/gh_auth_login , gh_auth_refresh , gh_auth_status
- https://cli.github.com/manual/gh_help_environment , gh_help_exit-codes , gh_help_formatting
- https://cli.github.com/manual/ (index)

**Primary — release notes (read 2026-10-29)**
- https://github.com/cli/cli/releases (page 1: 2.98.0–2.103.3; partly read — dependency lists truncated)
- https://github.com/cli/cli/releases?page=2 (2.88.1–2.97.0; partly read — summarised by fetch tool)
- https://github.com/cli/cli/releases/tag/v2.94.0 , /v2.97.0 , /v2.103.3 (read in full, Docs & Dependencies of 2.97.0 summarised)
- https://github.com/cli/cli/blob/trunk/docs/install_windows.md

**Primary — docs.github.com (read 2026-10-29)**
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project
- https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues
- https://docs.github.com/en/rest/issues/sub-issues
- https://docs.github.com/en/rest/issues/comments
- https://docs.github.com/en/rest/reactions/reactions
- https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens (partly read — targeted sections)
- https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api
- https://docs.github.com/en/graphql/reference/projects (partly read — targeted types)
- https://docs.github.com/en/graphql/reference/issues (read in two parts, offset 0 and 100000)

**Secondary — official source code (medium confidence; trunk, not tag-pinned)**
- https://raw.githubusercontent.com/cli/cli/trunk/pkg/cmd/project/shared/queries/export_data_test.go

**Rejected / not used for claims (community)**
- github.community thread and w3c/webref PR on the 65,536-character body limit (found via search, 2026-10-29); github.blog changelog 2024-02-12 (50k items beta, > 12 months, superseded by the docs page above).

---

## Research Gaps

```
Gap: Issue body / comment body maximum length (65,536 characters cited only by community and API error text)
Impact: oversized spec-delta bodies fail with 422 "body is too long"
Workaround: cap bodies well below 65,536 chars; link to the git file instead of inlining
Follow-up: REST issues create page or docs.github.com limits page; test once against the API
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Exact JSON output of `gh project item-add|item-list|field-list --format json` at tag v2.103.x (keys .id, .items[].content.url, .fields[].options)
Impact: jq paths could break
Workaround: verify with one live call; or use gh api graphql with an explicit selection set
Follow-up: pkg/cmd/project/shared/format and queries at tag v2.103.3
§7-ref: Iteration 2 — medium confidence
```
```
Gap: Behaviour of gh in non-TTY when a required prompt is needed (error text, exit code 1?) and stderr wording on rate limiting
Impact: wrapper retry/classification logic
Workaround: always pass all required flags; use `gh api -i` to read headers
Follow-up: gh source (pkg/cmdutil, api/client), live test
```
```
Gap: Fine-grained token / GitHub App permission needed for Projects via GraphQL (permissions page lists REST projectsV2 endpoints only)
Impact: App permission set for organization projects
Workaround: F3 (organization Projects read & write) — U3 owns App setup
Follow-up: GitHub Apps permissions reference
```
```
Gap: Creating ITERATION / MULTI_SELECT fields via API (gh field-create cannot)
Impact: project template bootstrap
Workaround: create once in the UI, read IDs
Follow-up: GraphQL createProjectV2Field input
```
```
Gap: Key names inside `gh issue view --json comments` (author.login, createdAt, url, id) and whether all comments are returned without a cap
Impact: comment reader
Workaround: use REST comments endpoint with --paginate (documented fields)
Follow-up: gh source pkg/cmd/issue/view, live test
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Migration Guide | Minimum gh version for sub-issue flags (F5 "unverified") | Resolved: 2.94.0 (10 Jun 2026) | https://github.com/cli/cli/releases/tag/v2.94.0 (2026-10-29) |
| 1 | Production Readiness | 50,000 items per project | Resolved: "maximum of 50,000 items across both active views and the archive page" | https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project (2026-10-29) |
| 1 | Guardrails A2 | PAT type for user projects | Resolved: classic PAT (`project`,`repo`); fine-grained cannot access user-owned projects | managing-your-personal-access-tokens + automating-projects-using-actions (2026-10-29) |
| 2 | Implementation Blueprint | `gh project` JSON shape | Updated: from gh source tests (trunk) — medium confidence | export_data_test.go (2026-10-29) |
| 2 | Guardrails C1 | ProjectV2FieldValue number/date shapes | Resolved: number Float, date Date, + multiSelectOptionIds | https://docs.github.com/en/graphql/reference/projects (2026-10-29) |
| 3 | Research Gaps | Issue/comment body size limit | ⚠️ IRRESOLVABLE — 3 searches found only community/error-message sources; no official page | — |
| 3 | Guardrails N7 | non-TTY prompt failure text | Left (unverified) — only community results | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (auth, gh project, GraphQL, issues/sub-issues/comments/reactions, rate limits, non-TTY/exit codes/Windows, 2.93→2.103 changes)
- [x] Pattern counts driven by domain needs (10 / 5 / 7)
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative (not executed in this session)
- [x] Integration examples complete (Python wrapper)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] Triangulation not required at depth=standard (noted)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced where it reached the loop

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1–A9, N1–N6; command flags from the gh 2.103 manual; limits from docs.github.com.
- **Medium Confidence (validate with user / live test)**: JSON keys of `gh project --format json` output; `gh issue view --json comments` sub-keys; GHES minimums; `dataType` field on `ProjectV2FieldCommon`; non-TTY `item-add` output fix semantics.
- **Low Confidence (must ask human)**: body size limit (IRRESOLVABLE); creation of ITERATION/MULTI_SELECT fields via API; App permission names for GraphQL Projects (U3).
- **Edge Cases (pause)**: 2.103.0 released 2026-10-21 (< 30 days before research) — manual pages were read live and match 2.103.x; patch releases are auth-only.
- **Family facts/rules conflicts (report, not edited)**: rule 5 says "fine-grained PAT for user-owned projects" — official docs say fine-grained PATs cannot access user-owned projects; use a classic PAT. Rule 7 says "always `--json`" — `gh project` uses `--format json`, and several write commands have no JSON flag.
