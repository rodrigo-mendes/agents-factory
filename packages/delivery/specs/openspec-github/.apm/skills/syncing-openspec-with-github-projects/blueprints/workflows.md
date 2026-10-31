# Workflow templates

Four templates in `assets/workflows/`, copied by `bootstrap --install-workflows` into the target
repository's `.github` directory, `workflows` subfolder (never overwritten when a different file exists).
Back to [SKILL.md](../SKILL.md).

## Contents

- [Common rules](#common-rules)
- [The four workflows](#the-four-workflows)
- [Archive jobs](#archive-jobs)
- [Pins](#pins)
- [Repository settings](#repository-settings)
- [Behaviours to know](#behaviours-to-know)

## Common rules

- Every action is pinned by full commit SHA with the tag in a trailing comment (family rule 8).
- Top-level and job `permissions:` are `contents: read`; project writes use the App token or the PAT secret.
- Event text (comment body, issue title and body, SHAs) reaches scripts only through `env:`.
- Step order: checkout, setup-python, then the step "Verify the vendored scripts (before any token or
  script runs)" - right after setup-python, before any token is minted or vendored script runs. It runs
  `_vendor.py verify` on the vendored scripts folder (`.github` + `openspec-github`); a modified file fails the job.
- In `openspec-ci.yml` the step verifies the pull request's own copy (that job has no secrets), so it is an
  integrity check of the vendored copy, not protection against a hostile pull request.
- Concurrency groups are per issue, per ref or per pull request, `cancel-in-progress: false` except CI.
- Runner `ubuntu-24.04` with Python 3.12.

## The four workflows

| File | Trigger | Does | Token |
|---|---|---|---|
| `openspec-gate.yml` | `issue_comment: created`, not on pull requests, body starts with `/`, author not the bot | `gate_command.py evaluate --apply`: label, Gate field, confirmation comment | App (`permission-issues: write`, `permission-organization-projects: write`) or PAT |
| `openspec-ci.yml` | `pull_request` on `openspec/**` and a placeholder code path | `openspec validate <id> --type change --strict --json --no-interactive`, `check_records.py`, `detect_drift.py` only when `lastSyncedSha` is real | none beyond read-only `GITHUB_TOKEN`; no secrets; never `pull_request_target` |
| `openspec-board-sync.yml` | `push` on `openspec/**`, job runs only on the default branch | `gh_projects_sync.py push --apply` for each changed change (all active changes when specs or ADRs changed) | App or PAT |
| `openspec-archive.yml` | `issues: labeled` with label `gate:E9:approved` and `sender.login == vars.OPENSPEC_BOT_LOGIN` | three jobs `authorize` (recheck, read-only token) then `prepare` (no token) then `publish`, see [archive jobs](#archive-jobs) | read-only App token in `authorize`; write token only in the last step of `publish` (or PAT) |

The archive workflow resolves the change id with `gate_command.py resolve-change` (key marker, else the
`change: <id>` title) and requires the folder to exist; the label text is never used as the id. It never
pushes the default branch (it aborts if the branch name equals it; this is a defensive check, since the
branch name `openspec/archive-<id>` can never equal a default branch name in normal use).

The gate job `if:` also requires an `openspec` label on the issue, so other issues are never touched.

## Archive jobs

No step that runs third-party code carries a write token (family rule 15).

| Job | Steps (in order) | Tokens |
|---|---|---|
| `authorize` | checkout, setup-python, vendored verify, credential check, read-only token (`permission-issues: read`, `permission-organization-projects: read`), `gate_command.py recheck . --profile "$PROFILE" --gate E9`, resolve change id | read-only token only |
| `prepare` (needs `authorize`) | fresh runner: checkout, setup-python, vendored verify, `npm install --global --ignore-scripts @fission-ai/openspec@1.15.0`, final gate (`openspec validate`, `check_records.py`, `detect_drift.py`), `openspec archive <id> --yes` and a binary patch | none |
| `publish` | fresh runner: checkout, setup-python, vendored verify, apply the patch (`publish` refuses any patch touching paths outside `openspec/` (both rename sides), mode changes, symlinks or submodules), commit on branch `openspec/archive-<id>`, **then** mint the write token, final step alone holds `GH_TOKEN`: `git push` of that branch and `gh pr create` | write token in the final step only |

- The patch travels as a job output (data, never code), capped at 700,000 bytes; the job output size limit
  is (unverified), register R18.
- `--ignore-scripts` blocks npm lifecycle scripts, but whether that makes the install safe enough is
  (medium confidence), register R17; branch protection or CODEOWNERS on `openspec/github-tracker.yaml`, the `.github`
  directory's `openspec-github` subfolder and the default branch is recommended.
- The archive pull request is a proposal: run `pull` (a gate E9 line in `handoff/status.md`) before merging it.
- A fresh `publish` runner means nothing npm wrote to `$GITHUB_ENV`, `$GITHUB_PATH` or hooks reaches it.
- Residual risk: npm code in `prepare` can still change any content under `openspec/` in the patch;
  `check-patch` only limits *where* it writes. Reviewing the archive pull request diff is the last
  control, so never merge it unread.
- All three jobs check out the same commit (`ref: ${{ github.sha }}`), so a push to the default branch
  between jobs cannot change what is re-checked, archived or published.

## Pins

| Action | Version | Commit (verified 2026-10-29) |
|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-python` | v7.1.0 | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` |
| `actions/create-github-app-token` | v3.3.0 | `64ab729a6294000f5aa4a4bc0b73d1f32bc45510` |

Source: `git ls-remote https://github.com/actions/<repo> refs/tags/<tag>`, family fact F7. Re-pin from a
fresh `ls-remote` when upgrading; `gh actions-lock` (public preview) is only an Ask First alternative.

## Repository settings

| Kind | Name | Used for |
|---|---|---|
| variable | `OPENSPEC_OWNER_TYPE` | `organization` or `user`; the workflows fail when it is unset |
| variable | `OPENSPEC_BOT_LOGIN` | the gate identity; archive sender check; gate loop guard |
| variable | `OPENSPEC_APP_CLIENT_ID` | organization: `client-id` of the App |
| secret | `OPENSPEC_APP_PRIVATE_KEY` | organization: App private key |
| secret | `OPENSPEC_PROJECT_PAT` | user: classic PAT with `project` and `repo` |
| variable (optional) | `OPENSPEC_PROFILE` | profile path; default is the vendored `handoff-profile.yaml` |

## Behaviours to know

- `issue_comment` always runs the default-branch copy of the workflow and scripts, never code from a pull request.
- Events created by the App or PAT trigger the archive workflow, unlike events created with `GITHUB_TOKEN`
  (medium confidence, register R9); the sender login for an App is the bot login form `name[bot]`
  (medium confidence, register R10).
- The archive App permission set (contents and pull-requests write) is (unverified), register R11.
- A required status check behind a `paths:` filter stays Pending when skipped (medium confidence,
  register R13): if `openspec-ci` is made required, delete its `paths:` filter.
- CI and archive install `@fission-ai/openspec@1.15.0` with npm and `--ignore-scripts` (medium confidence, register R12; sufficiency (medium confidence), register R17); this is an Ask First at bootstrap.
- Board-sync on a fresh runner has no `github.yaml`: it adopts objects by marker, so it does not duplicate.
