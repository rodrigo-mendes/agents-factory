# Always-do patterns (GitHub.com Actions, as of 2026-10-29)

Back to [SKILL.md](../SKILL.md). Snippets are representative; adapt names and ids. Sources fetched 2026-10-29. Script paths are placeholders.

## Event text through env

```yaml
- name: Parse command
  env:
    COMMENT_BODY: ${{ github.event.comment.body }}
    ISSUE_NUMBER: ${{ github.event.issue.number }}
  run: python3 tools/parse_command.py   # reads COMMENT_BODY and ISSUE_NUMBER from the environment
```

"The expressions inside `${{ }}` are evaluated and then substituted with the resulting values" before the shell runs. Source: https://docs.github.com/en/actions/reference/security/secure-use ; https://docs.github.com/en/actions/concepts/security/script-injections

## Read-only default, per-job raise

```yaml
permissions:
  contents: read            # workflow default
jobs:
  reply:
    permissions:
      contents: read
      issues: write         # only when this job comments with GITHUB_TOKEN
```

"If you specify the access for any of these permissions, all of those that are not specified are set to `none`." `permissions: {}` disables all. Sources: https://docs.github.com/en/actions/reference/security/secure-use ; https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## SHA pins with the tag as comment

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1                 # v7.0.1
- uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0             # v7.1.0
- uses: actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510  # v3.3.0
```

The repository setting "Require actions to be pinned to a full-length commit SHA" covers GitHub-authored actions too. Resolve a tag: `git ls-remote https://github.com/actions/checkout refs/tags/v7.0.1` and confirm the commit belongs to the action's repository, not a fork. "Dependabot only creates alerts for vulnerable actions that use semantic versioning", so enable Dependabot version updates for the `github-actions` ecosystem. Sources: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository ; https://docs.github.com/en/actions/reference/security/secure-use ; releases pages of each action

## App token, narrowed and per job

```yaml
- id: app-token
  uses: actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510  # v3.3.0
  with:
    client-id: ${{ vars.APP_CLIENT_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}
    repositories: ${{ github.event.repository.name }}
    permission-organization-projects: write
    permission-issues: write
```

Details and the PAT variant: [tokens](./tokens-app-and-pat.md). Source: https://github.com/actions/create-github-app-token (README, action.yml)

## GH_TOKEN on every gh step

```yaml
- env:
    GH_TOKEN: ${{ steps.app-token.outputs.token }}
  run: gh --version && python3 tools/sync.py
```

"GitHub CLI is preinstalled on all GitHub-hosted runners" and needs `GH_TOKEN`. Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli

## Who may trigger a comment workflow

```yaml
if: >-
  ${{ !github.event.issue.pull_request &&
      contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.comment.author_association) &&
      github.event.comment.user.login != 'my-app[bot]' }}
```

`!` at the start of an expression needs the `${{ }}` wrapper because it is reserved in YAML. The `github.event.issue.pull_request` split rests on one page (medium confidence). Sources: https://docs.github.com/en/rest/issues/comments ; https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

## Concurrency and timeout

```yaml
concurrency:
  group: sync-${{ github.event.issue.number }}   # per-issue key is not shown in an official example (medium confidence)
  cancel-in-progress: false
jobs:
  sync:
    timeout-minutes: 10
```

With the default `queue: single`, a pending run in the group "is canceled and replaced". Sources: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax ; https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency

## Checkout without persisted credentials

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1   # v7.0.1
  with:
    persist-credentials: false
```

`persist-credentials` defaults to `true`, leaving the token in the local git config for later steps. Source: https://github.com/actions/checkout (README)

## Preflight and required checks

- Print `gh --version` at the start of a job that calls gh; images update weekly. Source: https://github.com/actions/runner-images
- Required check workflows have no `paths` or `branches` filters; see [PRs and status checks](./prs-and-status-checks.md). Source: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks
