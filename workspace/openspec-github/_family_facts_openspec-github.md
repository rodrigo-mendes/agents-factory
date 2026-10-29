# Family facts — openspec-github (gh 2.103.x, Projects v2, Actions)

Single source of truth for facts shared by more than one skill. Every row is verified by the
orchestrator against an official page before authors see it. Authors never edit this file.

| ID | Fact | Confidence | Source (URL, page read date) | Used by |
|---|---|---|---|---|
| F1 | GitHub CLI latest stable is v2.103.3 (2026-10-26); the family pins 2.103.x | High | https://github.com/cli/cli/releases (2026-10-29) | U2, U4, U7 |
| F2 | "`GITHUB_TOKEN` is scoped to the repository level and cannot access projects." | High | https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions (2026-10-29) | U2, U3, U4 |
| F3 | GitHub App is "recommended for organization projects"; a personal access token is "recommended for user projects"; the App needs read and write **organization** projects ("permission to read and write repository projects will not be sufficient") | High | same page as F2 (2026-10-29) | U2, U3, U4 |
| F4 | `actions/create-github-app-token` latest is v3.3.0 (2026-10-12); docs use `@v3` | High | https://github.com/actions/create-github-app-token/releases (2026-10-29) | U3, U4 |
| F5 | Sub-issues: up to 100 per parent, up to 8 nesting levels; CLI `gh issue create --parent`, `gh issue edit --add-sub-issue/--remove-sub-issue/--remove-parent`; introduced in gh **2.94.0** (2026-06-10, "Add Issues 2.0 support: issue types, sub-issues, and relationships"; GitHub.com and GHES 3.17+) | High | https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues ; https://github.com/cli/cli/releases/tag/v2.94.0 (both 2026-10-29) | U2, U4 |
| F6 | Fine-grained PATs are NOT supported for "Projects owned by a user account" (listed gap; "not permanent"); user-owned projects therefore need a **classic PAT** (`project` + `repo` scopes per the Actions automation page) | High | https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens (2026-10-29); page of F2 | U2, U3, U4 |
| F7 | Pins (verified with `git ls-remote`, 2026-10-29): `actions/create-github-app-token` v3.3.0 = `64ab729a6294000f5aa4a4bc0b73d1f32bc45510`; `actions/checkout` v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1`; `actions/setup-python` v7.1.0 = `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` | High | git ls-remote https://github.com/actions/<repo> refs/tags/<tag> (2026-10-29) | U3, U4 |
| F8 | create-github-app-token: `client-id` is the recommended input ("The legacy `app-id` input is also accepted, but `client-id` is recommended"); outputs `token`, `installation-id`, `app-slug`; `permission-<name>` inputs narrow the token (default: all installation permissions) | High | https://github.com/actions/create-github-app-token (README, 2026-10-29) | U3, U4 |
| F9 | The documented App setup for project automation also needs read access to repository pull requests and issues (in addition to read/write organization projects, F3) | High | page of F2 (2026-10-29) | U3, U4 |
| F10 | `ubuntu-latest` = ubuntu-24.04, image 20261026.354.1 ships GitHub CLI 2.103.2 and Python 3.12.3; images update weekly | medium confidence (from research, not re-fetched by orchestrator) | https://github.com/actions/runner-images (via U3 research, 2026-10-29) | U3, U4 |
| F11 | GraphQL schema has `updatedAt`, `createdAt`, `creator`, `field` on `ProjectV2ItemFieldSingleSelectValue` (+ `name`, `optionId`) and `ProjectV2ItemFieldTextValue` (+ `text`); `Issue.databaseId`, `Issue.projectItems`, `ProjectV2Item.fieldValues` exist | medium confidence (schema mirror octokit/graphql-schema main, not the docs page; confirm in the live smoke test) | https://raw.githubusercontent.com/octokit/graphql-schema/main/schema.graphql (2026-10-29) | U4 |

## Change log
- 2026-10-29 F5 min version resolved (2.94.0); F6 added — both re-verified by the orchestrator after U2 research.
- 2026-10-29 F7-F10 added after U3 research; F7 SHAs re-verified by orchestrator with git ls-remote; F8 wording taken from README (legacy, not "deprecated").
- 2026-10-29 F11 added: orchestrator parsed the public GraphQL schema mirror; the gate's dependency on field-value updatedAt is schema-backed.
