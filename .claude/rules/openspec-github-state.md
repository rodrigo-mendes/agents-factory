---
name: openspec-github-state
description: "Guardrails for the OpenSpec GitHub bridge files: the script-written github.yaml cache, the project tracker file and the openspec workflow files. Use when editing these files or reviewing a change that touches them."
paths:
  - "**/openspec/**/github.yaml"
  - "**/openspec/github-tracker.yaml"
  - "**/workflows/openspec-*.yml"
---

# OpenSpec GitHub bridge state and workflows

Technical facts live in `syncing-openspec-with-github-projects`. This rule states what to check when one
of these files is edited; it does not duplicate the skill. Tags `(unverified)` and `(medium confidence)`
from the skill apply here too.

## Always

- `github.yaml` is written by `gh_projects_sync.py` only; to change it, re-run `push` (git is canonical).
- Approvals reach `handoff/status.md` only through `pull`, run by the orchestrator, never by an agent.
- `openspec/github-tracker.yaml` keeps `approval_source: chat` until the user chooses `github` or `both`.
- `bot_login` is quoted in YAML and is never listed in `approvers`.
- Workflow edits keep every action pinned by full commit SHA with the tag in a trailing comment.
- Workflow edits keep minimal `permissions:` (`contents: read`) and the vendored-scripts `verify` step right after setup-python, before any token is minted or vendored script runs.
- Workflow edits pass event text (comment, title, body, SHAs) through `env:`, never inside `run:`.
- Workflow edits keep third-party code (npm, `openspec`) in steps without a write token: tokens are minted only for the final step that needs them.
- Workflow edits never hand-edit the vendored scripts folder (the target repo's `openspec-github` folder under its `.github` directory); it changes only by re-vendoring (`bootstrap --vendor`), and `_vendor.py verify` rejects edits.
- Local bridge commands run with a machine-user token (App tokens only inside Actions), never an approver's login, when approvals are on GitHub.

## Ask First

- Switching `owner_type` to `user` (classic PAT with broad `repo` scope) or changing `approval_source`.
- Changing a workflow trigger, the credential path, or the archive sender check.
- Replacing SHA pins with workflow lockfiles.

## Never

- Hand-edit `github.yaml`; delete it only to force adoption by marker, then `push`.
- Use `GITHUB_TOKEN` for Projects, `pull_request_target`, or an unpinned action.
- Let the archive workflow push the default branch; it opens a pull request from `openspec/archive-<id>`.
- Treat a GitHub issue or comment as the spec source.
