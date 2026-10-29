---
name: managing-github-projects-gh-v2-103
description: "Drives GitHub Projects v2, issues, sub-issues and comments with GitHub CLI 2.103.x. Use when scripts or agents call gh project, gh issue, gh label or gh api. Not for Actions workflows, GHES specifics or the gh 2.93-or-older line."
---

# Managing GitHub Projects v2 and issues with gh 2.103.x

> Version lock: every claim applies to **GitHub CLI 2.103.x** (Projects v2, Issues, sub-issues) only. Research date **2026-10-29**.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: generic GitHub knowledge. GitHub content is a mirror and an approval channel, never the spec source. Whether an agent may consume comments is decided by the calling skill. Workflows and App tokens belong to `automating-github-repos-with-actions`; the OpenSpec bridge belongs to `syncing-openspec-with-github-projects`.

## Version Context

| Item | Value | Source (fetched 2026-10-29) |
|---|---|---|
| GitHub CLI (gh) | latest stable v2.103.3 (2026-10-26); family pin 2.103.x; active line | https://github.com/cli/cli/releases |
| Minimum gh for sub-issue flags | 2.94.0 (2026-06-10, Issues 2.0) | https://github.com/cli/cli/releases/tag/v2.94.0 |
| Minimum gh for name-based `item-edit` | 2.97.0 (2026-07-31) | https://github.com/cli/cli/releases/tag/v2.97.0 |
| REST API version | 2026-03-10 (shown on sub-issues and comments pages) | https://docs.github.com/en/rest/issues/sub-issues |
| GraphQL API | unversioned, github.com | https://docs.github.com/en/graphql/reference/projects |
| gh manual | pages carry no version label; they document the current release | https://cli.github.com/manual/ |

**Version-lifetime risk** (as of 2026-10-29; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- gh moved from 2.94.0 to 2.103.3 in about four and a half months; expect a new minor every few weeks, so re-check the manual before bumping the pin.
- The fine-grained PAT gap for user-owned projects is documented as "not permanent"; re-read the PAT page before changing the credential split.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Auth and tokens](./blueprints/auth-and-tokens.md)
- [Projects, fields and items](./blueprints/projects-fields-and-items.md)
- [Issues, sub-issues and comments](./blueprints/issues-sub-issues-and-comments.md)
- [GraphQL and rate limits](./blueprints/graphql-and-rate-limits.md)
- [Non-interactive use and Windows](./blueprints/non-interactive-and-windows.md)
- [Changes 2.93 to 2.103](./blueprints/version-changes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Token with the `project` scope** — "The minimum required scope for the token is: `project`" ([gh project](https://cli.github.com/manual/gh_project)). See [auth](./blueprints/auth-and-tokens.md).
- **GitHub App for organization-owned projects** — the Actions automation page recommends an App with organization Projects read and write ([Actions automation page](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)).
- **Classic PAT with `project` + `repo` for user-owned projects** — fine-grained PATs are not supported there ([PAT page](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)).
- **Inject the token with `GH_TOKEN`** — it takes precedence over stored credentials and avoids prompts ([environment help](https://cli.github.com/manual/gh_help_environment)).
- **Set `GH_PROMPT_DISABLED=1`** for every non-interactive run ([environment help](https://cli.github.com/manual/gh_help_environment)).
- **ID-based `item-edit` flags, one field per call** — `--id`, `--field-id`, `--project-id`, plus `--single-select-option-id` ([item-edit](https://cli.github.com/manual/gh_project_item-edit)).
- **Add the item first, update it second** — "You cannot add and update an item in the same call" ([API guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)).
- **`--format json` for `gh project` commands** — every `gh project` subcommand documents it, with `-q/--jq` ([item-list](https://cli.github.com/manual/gh_project_item-list)).
- **`--json` for `gh issue view/list`, `gh api` for commands without JSON output** — `--jq` and `--template` need `--json` ([formatting help](https://cli.github.com/manual/gh_help_formatting)).
- **Raise `-L` or paginate** — `item-list`, `field-list` and `project list` return 30 by default ([item-list](https://cli.github.com/manual/gh_project_item-list)).
- **Serialize writes with at least one second between them** ([REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)).
- **Require gh 2.94.0 or newer for sub-issue flags** ([v2.94.0 release](https://github.com/cli/cli/releases/tag/v2.94.0)).
- **When the calling skill allows it, read comments via REST** — `since` and `per_page` up to 100 ([comments API](https://docs.github.com/en/rest/issues/comments)).
- **Branch on gh exit codes** — 0 success, 1 failure, 2 cancelled, 4 authentication required ([exit codes](https://cli.github.com/manual/gh_help_exit-codes)).

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Owner type | `organization(login:)` plus App token vs `user(login:)` plus classic PAT | "Is `tracker.owner_type` organization or user?" Never guess from the login. |
| Porcelain vs GraphQL | `gh project item-*` (short, one field per process) vs `gh api graphql` (exact schema, aliases, MULTI_SELECT) | "Readable gh commands or one GraphQL client?" |
| Missing `project` scope | `gh auth refresh -s project` opens a browser or device flow | "Operator: refresh the token with project scope, or supply another." |
| ITERATION or MULTI_SELECT fields | `gh project field-create` only makes TEXT, SINGLE_SELECT, DATE, NUMBER; API creation path (unverified) | "Create the field once in the UI and let the script read its ID?" |
| Draft vs real issue | draft items have no repo, comments or sub-issues | "Does this item need a comment thread?" |
| Status comment | `--edit-last` (own last comment) vs REST PATCH with a stored comment ID | "Keep one status comment per issue and store its ID?" |
| `gh project --format json` key paths | `.id`, `.items[].content.url`, `.fields[].options` (medium confidence) | "Verify with one live call, or use a GraphQL selection set?" |
| Issue and comment body size | official limit not found (unverified) | "Cap bodies far below 65,536 characters and link to the git file?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Use `GITHUB_TOKEN` for Projects: it "cannot access projects" ([source](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)) | Pass an App installation token or classic PAT in `GH_TOKEN` |
| Use a fine-grained PAT for a user-owned project ([PAT page](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)) | Use a classic PAT with `project` + `repo` |
| Pass the issue node ID as `--id` to `item-edit` ([API guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)) | Use the project item ID returned by the add call |
| Set Labels, Assignees, Milestone or Repository through `updateProjectV2ItemFieldValue` (same guide) | `gh issue edit --add-label`, `--add-assignee`, `--milestone` ([issue edit](https://cli.github.com/manual/gh_issue_edit)) |
| Parse table output or combine `--comments` with `--json`, rejected since 2.99.0 ([v2.99.0 release](https://github.com/cli/cli/releases/tag/v2.99.0)) | Use `--json comments` or the REST comments endpoint |
| Fire parallel bursts of creations ([rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)) | Run serially, honour `retry-after` and `x-ratelimit-reset` |
| Run `gh auth login` or `gh auth refresh` from a non-interactive agent (family policy; the refresh flow is browser or device based, [auth refresh](https://cli.github.com/manual/gh_auth_refresh)) | Provide `GH_TOKEN`; ask the operator to refresh scopes |
| Log `gh auth status` from gh older than 2.97.0 ([v2.97.0 release](https://github.com/cli/cli/releases/tag/v2.97.0)) | Pin 2.103.x; never print tokens |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Sub-issue limits | 100 per parent, 8 nesting levels | https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues |
| Project size | 50 fields, 50,000 items including archive | https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects |
| List default | `-L 30` | https://cli.github.com/manual/gh_project_item-list |
| GraphQL page size | `first`/`last` 1 to 100 | https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api |
| `field-create --data-type` | TEXT, SINGLE_SELECT, DATE, NUMBER | https://cli.github.com/manual/gh_project_field-create |
| Content creation cap | about 80 per minute, 500 per hour | https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api |
| Mutation cost | 5 points (900 per minute REST endpoint, 2,000 GraphQL) | same page |
| Close reasons | `completed`, `not planned`, `duplicate` | https://cli.github.com/manual/gh_issue_close |
| Reaction values | `+1 -1 laugh confused heart hooray rocket eyes` | https://docs.github.com/en/rest/reactions/reactions |
| Windows install | `winget upgrade --id GitHub.cli --source winget` | https://github.com/cli/cli/blob/trunk/docs/install_windows.md |

## External Resources

All fetched 2026-10-29.

- [gh manual index](https://cli.github.com/manual/)
- [Using the API to manage Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
