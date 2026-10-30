# openspec-github

Bridge between OpenSpec changes in git and a GitHub Project (v2). Git stays canonical; GitHub is a
mirror (issues, sub-issues, project fields, comments) plus an approval channel (gate commands as issue
comments, validated by a GitHub Actions workflow and re-checked locally by the orchestrator).
Targets gh 2.103.x (minimum 2.94.0). Research date 2026-10-29.

Depends on `factory-core`, `openspec-core`, `handoff-core` and `github-core` (see `apm.yml`).

## Contents

| Artifact | Path under `.apm/` | Role |
|---|---|---|
| Knowledge skill `syncing-openspec-with-github-projects` | `skills/syncing-openspec-with-github-projects/` | SKILL.md, 9 blueprints, `scripts/` (stdlib Python), `assets/` (tracker template, 4 workflow templates) |
| Command `/syncing-openspec-to-github` | `skills/syncing-openspec-to-github/` | forks to the syncer agent; `push` and `status` |
| Agent `openspec-github-syncer` | `agents/openspec-github-syncer.agent.md` | non-interactive; never `pull`, `close`, `bootstrap` |
| Rule `openspec-github-state` | `instructions/openspec-github-state.instructions.md` | guards `github.yaml`, the tracker file and the openspec workflow files |

## Credentials summary

| Project owner | Token | Notes |
|---|---|---|
| organization | GitHub App installation token (`client-id` variable `OPENSPEC_APP_CLIENT_ID`, secret `OPENSPEC_APP_PRIVATE_KEY`) | organization projects read and write |
| user | classic PAT with `project` and `repo` (secret `OPENSPEC_PROJECT_PAT`) | broad scope: risk warning on every run; prefer an organization |

`GITHUB_TOKEN` cannot access projects. Repository variables: `OPENSPEC_OWNER_TYPE`, `OPENSPEC_BOT_LOGIN`,
optional `OPENSPEC_PROFILE`. Details in the skill's `blueprints/bootstrap-and-credentials.md`.

## Who runs what

- Agents: `push` and `status` (dry-run; `--apply` only with the orchestrator's relayed approval line, or when
  the user typed `--apply` in the command, which is itself the relayed line). The syncer agent and command are
  for a manual refresh or other orchestrators; `building-aws-saas-serverless-quarkus-react-nextjs` runs `push` inline.
- With `approval_source` `github` or `both` no bridge command runs under an approver's `gh` login (exit 1):
  use a machine-user token in `GH_TOKEN` locally (App tokens only inside Actions) and approve in the browser.
- Orchestrator: `bootstrap`, `pull`, `close`, plus everything above.
- Workflows: gate commands, CI checks, board sync, archive on a branch with a pull request.

## Tests

Offline, Python 3.8+ standard library, no network and no real gh (`scripts/tests/fake_gh.py` is the stub).
Run from the repository root:

```bash
OPENSPEC_GITHUB_HANDOFF_SCRIPTS=packages/handoff-core/.apm/skills/coordinating-agent-handoffs/scripts \
  python -m unittest discover -s packages/openspec-github/.apm/skills/syncing-openspec-with-github-projects/scripts/tests
```

The variable points to the handoff-core scripts (`_handoff_lib.py`, `_mini_yaml.py`); the test helper
defaults to that repository path when it is unset. Optional: `actionlint` on PATH enables a workflow lint test. Last run: 100 tests, 4 skipped.
At runtime the scripts need gh 2.103.x on PATH (or `OPENSPEC_GITHUB_GH`) and `GH_TOKEN` for the owner type.

## Open items

See the skill's `blueprints/unverified-and-risks.md` (19 entries: 8 unverified, 9 medium confidence, 2 known limits).

## Follow-ups (open after the 2026-10-29 build)

- Live smoke test on a sandbox repository and Project (Ask First): bootstrap and push dry-run, then `--apply`,
  App install, `/approve E2` through the gate workflow, `pull`, a forged bot-marker comment ignored, CI on a PR,
  board sync on push, `/approve E9` archive PR, `close`. It confirms the (unverified) and (medium confidence)
  register items (GraphQL field-value `updatedAt`, `--ignore-scripts`, job-output size, `--paginate --slurp`).
- Local gh must be upgraded to 2.103.x before use (minimum 2.94.0; preflight refuses older versions).
- naming-conventions.md (factory-core) asks for action-noun command names while 30 of 67 commands, including
  `/syncing-openspec-to-github`, are gerund-style: align the rule with practice in a separate change.
- OCI family (`oci-core`): tracker support is not wired in (user-mediated, `spec.kind: none`).
