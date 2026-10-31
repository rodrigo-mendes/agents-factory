# Auth and tokens (gh 2.103.x)

Back to [SKILL.md](../SKILL.md). Sources fetched 2026-10-29.

## Credential split by owner type

| Owner | Credential | Required access | Source |
|---|---|---|---|
| Organization-owned project | GitHub App installation token | organization Projects read and write; "permission to read and write repository projects will not be sufficient" | https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions |
| User-owned project | classic PAT | `project` and `repo` scopes | same page |
| Any project | never `GITHUB_TOKEN` | "scoped to the repository level and cannot access projects" | same page |

The page recommends a GitHub App for organization projects and a personal access token for user projects. Fine-grained PATs are not supported for "Projects owned by a user account" (listed gap, described as "not permanent"); they do have an organization Projects permission (read, write, admin). Source: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

App creation, token minting in workflows and `actions/create-github-app-token` belong to `automating-github-repos-with-actions`.

## Select the credential from tracker.owner_type

```python
def pick_token(owner_type: str, app_token: str | None, classic_pat: str | None) -> str:
    if owner_type == "organization" and app_token:
        return app_token
    if owner_type == "user" and classic_pat:
        return classic_pat
    raise SystemExit("owner_type must be organization or user, with the matching credential")
```

Read the owner type from configuration; never infer it from the login. Both credentials are supported (family decision "Suportar os dois").

## Scope check before any project call

```bash
gh api graphql -f query='{viewer{login}}'      # works with a valid token
gh auth status --json hosts --jq '.hosts'      # exit 0 even with auth problems when --json is used
```

- GraphQL needs `read:project` for queries or `project` for queries and mutations. Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects
- If the scope is missing, `gh auth refresh -s project` is an operator step (browser or device flow), not an agent action. Source: https://cli.github.com/manual/gh_auth_refresh

## Environment variables

| Variable | Effect | Source |
|---|---|---|
| `GH_TOKEN`, `GITHUB_TOKEN` (in order of precedence) | token used; avoids prompts; wins over stored credentials | https://cli.github.com/manual/gh_help_environment |
| `GH_PROMPT_DISABLED` | any value disables interactive prompting | same page |
| `NO_COLOR` | plain output | same page |
| `GH_NO_UPDATE_NOTIFIER` | silences the update notice (stderr) | same page |
| `GH_CONFIG_DIR` | overrides the config directory | same page |

`gh auth login` docs: "Favour setting `GH_TOKEN` for fine-grained personal access token usage." This applies to organization-owned projects only; user-owned projects need a classic PAT (F6), which is also passed in `GH_TOKEN`. Source: https://cli.github.com/manual/gh_auth_login

## Token handling in 2.103.x

- 2.103.0 to 2.103.3 added refreshable and expiring tokens: `--expiring`, automatic refresh in `gh auth status`, and `--no-refresh`. A status call may therefore refresh a token unless `--no-refresh` is passed. Source: https://github.com/cli/cli/releases/tag/v2.103.3
- 2.97.0 fixed the partial token print of `gh auth status`; do not use older builds. Source: https://github.com/cli/cli/releases/tag/v2.97.0
- Keep tokens in an env var or secret store and never print them in logs (do not use `gh auth status --show-token` there). Source: https://cli.github.com/manual/gh_auth_status
- Primary limits differ per credential; the values are kept in [GraphQL and rate limits](./graphql-and-rate-limits.md#primary-limits-by-credential). Source: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api

## Preflight checklist

1. `gh --version` reports 2.103.x (at least 2.94.0 when sub-issues are used).
2. `GH_TOKEN` is set from the credential matching `owner_type`; `GITHUB_TOKEN` is not used for Projects.
3. `GH_PROMPT_DISABLED=1` is exported.
4. `gh api graphql -f query='{viewer{login}}'` succeeds.
5. The project is reachable: `gh project view 7 --owner my-org --format json`.
