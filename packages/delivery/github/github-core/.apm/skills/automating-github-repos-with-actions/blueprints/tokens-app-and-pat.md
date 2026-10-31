# Tokens: GitHub App and classic PAT (GitHub.com Actions, as of 2026-10-29)

Back to [SKILL.md](../SKILL.md). Sources fetched 2026-10-29. Commands that use the token (Projects, issues) are in `managing-github-projects-gh-v2-103`.

## Choosing the credential

| Owner of the project | Credential | Why |
|---|---|---|
| Organization | GitHub App installation token | "recommended for organization projects" |
| User account | Classic PAT with `project` + `repo` | fine-grained PATs are not supported for "Projects owned by a user account"; the gap is described as "not permanent" |
| Either | never `GITHUB_TOKEN` | "scoped to the repository level and cannot access projects" |

Ask the user whether the project is organization- or user-owned; never infer it from the login. Sources: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions ; https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

## GitHub App for organization projects

Required App permissions per the Actions automation page: read and write organization projects ("permission to read and write repository projects will not be sufficient") plus read access to repository pull requests and issues. Store the client id as a variable and the private key as a secret.

```yaml
- id: app-token
  uses: actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510  # v3.3.0
  with:
    client-id: ${{ vars.APP_CLIENT_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}
    owner: ${{ github.repository_owner }}
    repositories: ${{ github.event.repository.name }}
    permission-organization-projects: write
    permission-issues: read
    permission-pull-requests: read
- env:
    GH_TOKEN: ${{ steps.app-token.outputs.token }}
  run: python3 tools/sync.py
```

- `client-id` is recommended: "The legacy `app-id` input is also accepted, but `client-id` is recommended". Outputs: `token`, `installation-id`, `app-slug`.
- By default the token "inherits all of the installation's permissions"; `permission-<name>` inputs narrow it and it cannot exceed what the App was granted.
- Valid names include `permission-organization-projects` (read, write, admin), `permission-repository-projects`, `permission-issues`, `permission-pull-requests`, `permission-contents` and `permission-workflows` (write only).
- The installation token expires after 1 hour. Unless `skip-token-revoke` is true it is revoked in the post step, so it cannot be passed to another job: mint one per job.
- Releases: `client-id` needs v3.1.0 or newer; v3.0.0 moved to Node 24 (self-hosted runners need Actions Runner v2.327.1 or newer); v3.2.0 added `enterprise` and `owner/repo` in `repositories`; v3.3.0 refreshed the permission inputs.

Sources: https://github.com/actions/create-github-app-token (README, action.yml, releases) ; https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app

## Classic PAT for user-owned projects

```yaml
- env:
    GH_TOKEN: ${{ secrets.PROJECT_PAT }}    # classic PAT, scopes project + repo
  run: python3 tools/sync.py
```

- Docs: "personal access token (classic) with the `project` and `repo` scopes".
- Risk warning to print whenever this path is chosen: the `repo` scope is broad (full access to the owner's repositories the token can reach), the token is tied to a person and rotated by hand. Recommend moving the project to an organization and using an App.
- Never put the token value in a workflow file; keep it in `secrets`.

Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions

## Why not GITHUB_TOKEN

Every Projects call made with it fails. It stays useful only for repository-scoped work declared in `permissions:`. Events created with it do not start new runs, which is why PR creation that must trigger checks needs an App token or PAT ([PRs and status checks](./prs-and-status-checks.md#opening-a-pr-from-a-workflow)). Source: https://docs.github.com/en/actions/concepts/security/github_token

## Fallback decision

If neither App nor PAT is available, stop and ask the operator; do not substitute `GITHUB_TOKEN` or a fine-grained PAT.
