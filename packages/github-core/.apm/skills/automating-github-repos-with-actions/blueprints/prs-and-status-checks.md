# Pull requests and required status checks (GitHub.com Actions, as of 2026-10-29)

Back to [SKILL.md](../SKILL.md). Sources fetched 2026-10-29.

## Opening a PR from a workflow

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. App token + `gh auth setup-git` + `git push` + `gh pr create` | commits and PR authored by `<slug>[bot]`; PR checks run normally | App needs contents and pull requests write (unverified) | default for repository automation |
| B. `actions/checkout` with `token:` set to the App token | simple single-job push | `persist-credentials` defaults to `true`, so the token stays in the local git config for later steps | single-job push |
| C. `GITHUB_TOKEN` | no extra credential | needs the repository setting "Allow GitHub Actions to create and approve pull requests" (off by default for personal repositories); PR runs wait in an approval-required state; no Projects access | when checks need not run |

Ask: "Must the generated PR trigger required CI checks automatically?" If yes use A or B. Sources: https://github.com/actions/create-github-app-token ; https://github.com/actions/checkout ; https://docs.github.com/en/actions/concepts/security/github_token ; https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository

## Option A example

```yaml
- id: app-token
  uses: actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510  # v3.3.0
  with:
    client-id: ${{ vars.APP_CLIENT_ID }}
    private-key: ${{ secrets.APP_PRIVATE_KEY }}
    repositories: ${{ github.event.repository.name }}
    permission-contents: write          # push the branch (unverified exact set)
    permission-pull-requests: write     # create the PR (unverified exact set)
- name: Push branch and open PR
  env:
    GH_TOKEN: ${{ steps.app-token.outputs.token }}
    APP_SLUG: ${{ steps.app-token.outputs.app-slug }}
    BRANCH: feature/sync-${{ github.run_id }}
  run: |
    BOT_ID=$(gh api "/users/${APP_SLUG}[bot]" --jq .id)
    git config user.name  "${APP_SLUG}[bot]"
    git config user.email "${BOT_ID}+${APP_SLUG}[bot]@users.noreply.github.com"
    gh auth setup-git
    git switch -c "$BRANCH"
    git commit -am "chore: sync generated files"
    git push origin "$BRANCH"
    gh pr create --head "$BRANCH" --title "Sync generated files" --body "Automated by ${APP_SLUG}[bot]"
```

- Pushing files under the workflows directory also needs `permission-workflows: write` (input exists, write only); whether it is required for the push is (unverified).
- Use a run-unique branch name so reruns never collide.
- The built-in token alternative from the checkout README commits as `github-actions[bot]` with email `41898282+github-actions[bot]@users.noreply.github.com`.

Sources: https://github.com/actions/create-github-app-token (README "Configure Git CLI") ; https://github.com/actions/checkout (README)

## Required status checks

- A workflow skipped by a path filter, branch filter or commit message leaves its checks "Pending", which blocks merging; a job skipped by a conditional "reports "Success"". "Avoid requiring workflows that can be skipped."
- Therefore: no `paths` or `branches` filter on the workflow that provides a required check; skip heavy jobs with job-level `if:`.
- For CI, `cancel-in-progress: true` gives fast feedback; for writers use `false` ([triggers](./triggers-and-payloads.md#concurrency-per-issue)).

Sources: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks ; https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets

## CI gate example

```yaml
on:
  pull_request:          # default types: opened, synchronize, reopened
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: ci-${{ github.head_ref || github.run_id }}
  cancel-in-progress: true
jobs:
  validate:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1   # v7.0.1
        with:
          persist-credentials: false
      - run: python3 tools/check.py
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax ; https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
