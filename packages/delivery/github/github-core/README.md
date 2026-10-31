# github-core

Generic **GitHub** knowledge for non-interactive agents and scripts. Nothing here is
OpenSpec-specific; the bridge `openspec-github` builds on it.

| Kind | Name | Purpose |
|---|---|---|
| skill | `managing-github-projects-gh-v2-103` | GitHub CLI 2.103.x: auth and scopes, `gh project` fields and items, Issues, sub-issues (gh >= 2.94.0), labels, comments, `gh api` GraphQL/REST, rate limits, non-interactive use and Windows |
| skill | `automating-github-repos-with-actions` | GitHub Actions repository automation: `issue_comment` / `pull_request` / `push` triggers, minimal `permissions:`, GitHub App token (organization projects) or classic PAT (user projects), SHA pinning, injection-safe `github.event.*` handling |

Credentials: `GITHUB_TOKEN` cannot access Projects. Organization-owned projects use a GitHub App;
user-owned projects need a classic PAT (fine-grained PATs cannot access user-owned projects).

Depends on: factory-core. Used by: openspec-github.
