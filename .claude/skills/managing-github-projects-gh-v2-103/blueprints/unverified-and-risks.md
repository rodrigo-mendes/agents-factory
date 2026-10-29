# Unverified and risks register

Back to [SKILL.md](../SKILL.md). Research date 2026-10-29. Tags are plain parentheses: (unverified) and (medium confidence).

## Version-lifetime risk

As of 2026-10-29.

- gh 2.103.3 (2026-10-26) is the latest stable; 2.94.0 (2026-06-10) to 2.103.3 is about four and a half months, so a new minor appears every few weeks. Source: https://github.com/cli/cli/releases
- The gh manual pages carry no version label; they describe the current release and can change under the same URL. Source: https://cli.github.com/manual/
- The fine-grained PAT gap for user-owned projects is described as "not permanent"; the classic PAT rule may relax. Source: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- REST API version 2026-03-10 is the version shown on the sub-issues and comments pages. Source: https://docs.github.com/en/rest/issues/sub-issues
- Re-run the preflight in [auth and tokens](./auth-and-tokens.md#preflight-checklist) after every gh bump.

## Unverified (4)

| ID | Claim | Impact | Workaround |
|---|---|---|---|
| U1 | Creating ITERATION or MULTI_SELECT fields through the API (gh `field-create` cannot) | project bootstrap | create once in the UI, read the IDs |
| U2 | gh behaviour in a non-TTY when a prompt would be needed (error text, exit code) | wrapper classification | pass every required flag; set `GH_PROMPT_DISABLED=1` |
| U3 | stderr wording when gh hits a rate limit | retry detection by text | read headers with `gh api -i` |
| U4 | Official guidance for mocking gh in tests | test design | PATH shim or injected `subprocess.run`; generic practice |

## Irresolvable (1)

| ID | Claim | Note |
|---|---|---|
| I1 | Maximum length of an issue or comment body (65,536 characters appears only in community posts and API error text) | three searches found no official page; oversized bodies fail with 422 "body is too long"; cap bodies far below 65,536 and link to the git file |

## Medium confidence (7)

| ID | Claim | Why medium | Check |
|---|---|---|---|
| M1 | JSON key paths of `gh project item-add`, `item-list`, `field-list` (`.id`, `.items[].content.url`, `.fields[].options`, `.fields[]`, `.totalCount`) | manual does not document the shape; evidence is a trunk test file | one live call, or GraphQL selection set |
| M2 | Key names inside `gh issue view --json comments` and whether every comment is returned | sub-keys not on the manual page | use REST comments with `--paginate` |
| M3 | GHES 3.19 minimum for relationships | summary of the release list, not a tag page | out of scope; read GHES docs if needed |
| M4 | `dataType` selectable on `ProjectV2FieldCommon` | the official guide example requests only `id name` | one live query |
| M5 | 2.98.0 non-TTY `item-add` fix semantics | one-line release-list entry | parse with `--format json` only |
| M6 | `gh api rate_limit` endpoint use | page not read | read `rateLimit` in GraphQL instead |
| M7 | Release rows 2.93.0, 2.98.0 and 2.102.0 (dates and content) | taken from the summarised release list, no tag page read | read the tag pages before relying on them |

## Coverage limits (4)

| ID | Limit |
|---|---|
| L1 | https://github.com/cli/cli/releases and ?page=2 were partly read; dependency sections truncated and summarised by the fetch tool |
| L2 | The fine-grained PAT permissions page was read only in targeted sections; GraphQL Projects permissions are not listed there, so the App permission rests on fact F3 |
| L3 | The GraphQL Projects reference was read only for the targeted types |
| L4 | Release-list dates carry no year; 2026 comes from the tag pages and fact F1 |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First (ITERATION and MULTI_SELECT creation); projects-fields-and-items.md Field types | U1 |
| (unverified) | never-do-patterns.md N7; non-interactive-and-windows.md Environment for scripts | U2 |
| (unverified) | graphql-and-rate-limits.md Backoff algorithm; non-interactive-and-windows.md Python runner; evaluation-scenarios.md Scenario 5 | U3 |
| (unverified) | non-interactive-and-windows.md Testing without GitHub | U4 |
| (unverified) | SKILL.md Ask First (body size); issues-sub-issues-and-comments.md Posting and editing comments; evaluation-scenarios.md Scenario 6 | I1 |
| (medium confidence) | SKILL.md Ask First (`--format json` key paths); projects-fields-and-items.md gh project commands; non-interactive-and-windows.md Verification commands; evaluation-scenarios.md Scenario 2 | M1 |
| (medium confidence) | issues-sub-issues-and-comments.md Reading comments | M2 |
| (medium confidence) | version-changes.md Compatibility matrix | M3 |
| (medium confidence) | projects-fields-and-items.md Resolve IDs once and cache them | M4 |
| (medium confidence) | projects-fields-and-items.md gh project commands; version-changes.md table (2.98.0) | M5 |
| (medium confidence) | graphql-and-rate-limits.md Monitoring headroom | M6 |
| (medium confidence) | version-changes.md table (2.93.0, 2.98.0 and 2.102.0 rows) | M7 |

## Source Bibliography

All fetched 2026-10-29. gh manual pages carry no version label and document the current release.

**GitHub CLI manual**
- https://cli.github.com/manual/ , gh_project , gh_project_item-add , gh_project_item-create , gh_project_item-edit , gh_project_item-list , gh_project_field-create
- https://cli.github.com/manual/gh_issue_create , gh_issue_edit , gh_issue_view , gh_issue_comment , gh_issue_close , gh_label_create
- https://cli.github.com/manual/gh_api , gh_auth_login , gh_auth_refresh , gh_auth_status
- https://cli.github.com/manual/gh_help_environment , gh_help_exit-codes , gh_help_formatting

**Releases and source**
- https://github.com/cli/cli/releases (partly read, L1)
- https://github.com/cli/cli/releases/tag/v2.94.0 , v2.97.0 , v2.99.0 , v2.103.3
- https://github.com/cli/cli/blob/trunk/docs/install_windows.md
- https://raw.githubusercontent.com/cli/cli/trunk/pkg/cmd/project/shared/queries/export_data_test.go (trunk, not tag-pinned; basis of M1)

**docs.github.com**
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects
- https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project
- https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues
- https://docs.github.com/en/rest/issues/sub-issues , https://docs.github.com/en/rest/issues/comments , https://docs.github.com/en/rest/reactions/reactions
- https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens (partly read, L2)
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api
- https://docs.github.com/en/graphql/reference/projects (partly read, L3)

**Rejected (community, not used for claims)**
- Community threads on the 65,536-character body limit; a 2024 changelog post on the 50,000-item beta (superseded by the docs page above).
