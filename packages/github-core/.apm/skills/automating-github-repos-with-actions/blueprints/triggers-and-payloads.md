# Triggers and payloads (GitHub.com Actions, as of 2026-10-29)

Back to [SKILL.md](../SKILL.md). Sources fetched 2026-10-29. Payload field lists are the ones used by this skill, not the full schema.

## Trigger table

| Trigger | Fires when | Runs which file | Fields used |
|---|---|---|---|
| `issue_comment` (`created`, `edited`) | a comment on an issue or a PR | default branch copy; `GITHUB_SHA` = default-branch tip | `comment.body`, `comment.id`, `comment.html_url`, `comment.created_at`, `comment.author_association`, `comment.user.login`, `issue.number`, `issue.pull_request` |
| `issues` (`labeled`) | a label is added | default branch copy | `label.name`, `issue.number`, `sender.login` |
| `pull_request` | default types opened, synchronize, reopened | merge ref, `GITHUB_REF` = `refs/pull/N/merge` | `pull_request.number`, `pull_request.head.ref` |
| `push` | commits pushed; filter with `branches` and `paths` | pushed ref | `ref`, `repository.default_branch` |

- `issue_comment` and `issues` only trigger when the workflow file exists on the default branch, so a change takes effect after it merges. Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- `push` events are not created when more than 5,000 branches are pushed at once. Source: same page.
- `comment.id` (int64), `comment.html_url` and `comment.created_at` are required fields in the REST comment schema. Source: https://docs.github.com/en/rest/issues/comments

## Issue comment or PR comment

"The `issue_comment` event occurs for comments on both issues and pull requests." Single official page (medium confidence).

```yaml
on:
  issue_comment:
    types: [created, edited]
jobs:
  on-issue:
    if: ${{ !github.event.issue.pull_request }}     # PR comments: ${{ github.event.issue.pull_request }}
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

## Untrusted fields

Field names that typically end with `body`, `default_branch`, `email`, `head_ref`, `label`, `message`, `name`, `page_name`, `ref` and `title` are attacker-controlled; this covers `github.event.comment.body`, `github.event.issue.title` and `github.event.label.name`. Always route them through `env:` ([always-do](./always-do-patterns.md#event-text-through-env)). Source: https://docs.github.com/en/actions/reference/security/secure-use

## Who triggered it

Anyone who can comment on a public issue triggers `issue_comment`, so the workflow must check the author.

```yaml
if: >-
  ${{ contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.comment.author_association) }}
```

Enum values: COLLABORATOR, CONTRIBUTOR, FIRST_TIMER, FIRST_TIME_CONTRIBUTOR, MANNEQUIN, MEMBER, NONE, OWNER. Source: https://docs.github.com/en/rest/issues/comments

## Bot guard for label events

```yaml
on:
  issues:
    types: [labeled]
jobs:
  gate:
    if: ${{ github.event.label.name == 'approved' && github.event.sender.login != 'my-app[bot]' }}
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    permissions: { contents: read }
    steps:
      - env:
          LABEL: ${{ github.event.label.name }}
          SENDER: ${{ github.event.sender.login }}
        run: echo "label=$LABEL by $SENDER"
```

Comparing `sender.type` with `Bot` is (unverified); use the exact login. Source: https://docs.github.com/en/rest/issues/comments (schema lists `type` only as a string)

## Loop prevention

- Events created with `GITHUB_TOKEN` "will not create a new workflow run". Source: https://docs.github.com/en/actions/concepts/security/github_token
- Docs recommend an App token or PAT precisely so workflow-created PRs start runs; no official sentence states the general rule for comments and labels, so assume they can retrigger (medium confidence).
- Guard with the author check above plus a per-issue concurrency group.

## Concurrency per issue

```yaml
concurrency:
  group: sync-${{ github.event.issue.number }}   # the per-issue key is not in an official example (medium confidence)
  cancel-in-progress: false
```

- "There can be at most one running job or workflow in a concurrency group at any time"; group names are case insensitive.
- Default `queue: single` keeps only the newest pending run; `queue: max` allows up to 100 pending and cannot combine with `cancel-in-progress: true`.
- `cancel-in-progress: true` suits CI; `false` suits writers.
- Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency ; https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## Timeouts

Job `timeout-minutes` defaults to 360; set a value sized to the job (for example 5 to 15). An App token lasts 1 hour, so a longer job must mint again. Sources: workflow syntax page above ; https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app
