# DESIGN U4/U5 — package openspec-github (bridge)

Orchestrator design, 2026-10-29. Source of decisions: PIPELINE_STATE.md#approvals and the approved plan.
Facts: `_family_facts_openspec-github.md`; rules: `_family_rules_openspec-github.md` (both win over this file).

## 1. Layout

```
packages/openspec-github/
├── apm.yml                      deps: ../factory-core, ../openspec-core, ../handoff-core, ../github-core
├── README.md
└── .apm/
    ├── skills/syncing-openspec-with-github-projects/      (knowledge skill, hybrid)
    │   ├── SKILL.md
    │   ├── blueprints/ mapping.md, approvals-and-trust.md, cli-contract.md, workflows.md,
    │   │               bootstrap-and-credentials.md, always-do-patterns.md, never-do-patterns.md,
    │   │               unverified-and-risks.md, evaluation-scenarios.md
    │   ├── assets/github.template.yaml
    │   ├── assets/workflows/ openspec-gate.yml, openspec-ci.yml, openspec-board-sync.yml, openspec-archive.yml
    │   └── scripts/ gh_projects_sync.py, _gh.py, _model.py, gate_command.py, _vendor.py,
    │                tests/ test_model.py, test_gate.py, test_sync.py, fake_gh.py, fixtures/
    ├── skills/syncing-openspec-to-github/SKILL.md          (command: context: fork, agent: openspec-github-syncer,
    │                                                         disable-model-invocation: true)
    ├── agents/openspec-github-syncer.agent.md              (Read, Grep, Glob, Bash; push/status only)
    └── instructions/openspec-github-state.instructions.md  (applyTo: "**/openspec/**/github.yaml,**/.github/workflows/openspec-*.yml")
```

## 2. Inputs

- Change dir: `openspec/changes/<id>/` (proposal.md, design.md, tasks.md, specs/, handoff/).
- Handoff dir: `openspec/changes/<id>/handoff/` (records + status.md from board.py).
- Profile: family profile with the `tracker:` block (handoff-core `profile-format.md#tracker`, validated by
  `_handoff_lib.validate_tracker`). Project values may live in `openspec/github-tracker.yaml` (same shape as the
  `tracker:` block; it wins over the profile's block). Reuse `_handoff_lib.load_profile`, `_mini_yaml` from the
  installed `coordinating-agent-handoffs/scripts/` (locate: sibling skill dir `../../coordinating-agent-handoffs/scripts`
  relative to this skill's `scripts/`, i.e. `.claude/skills/coordinating-agent-handoffs/scripts`; fail with a clear
  error if absent). In tests, point to `packages/handoff-core/.apm/skills/coordinating-agent-handoffs/scripts` via env
  `OPENSPEC_GITHUB_HANDOFF_SCRIPTS`.
- ADRs: `openspec/specs/architecture/adr/*.md` (profile `spec.adr_dir`).

## 3. State file `openspec/changes/<id>/handoff/github.yaml` (written by the script only)

```yaml
schema: 1
tracker: {owner: acme, owner_type: organization, project_number: 7, repo: acme/shop}
project_id: "PVT_..."
fields: {Stage: {id: "PVTSSF_...", options: {E1: "opt..", ...}}, Status: {...}, Kind: {...}, Change: {id: ...}, Gate: {...}}
change: {issue: 12, node_id: "I_...", item_id: "PVTI_..."}
tasks: {T1: {issue: 13, node_id: "...", item_id: "..."}}
adrs: {"001": {issue: 14, ...}}
escalations: {"escalation-01": {issue: 15, ...}}
deltas: {"spec-delta-01": {comment_id: 991}}
summary_comment_id: 990
pulled: {"<comment_id>": "<record or approval line id>"}      # idempotency of pull
vendor: {version: "1.0.0", sha256: "..."}                     # bootstrap vendoring of scripts
```
Must be readable by `_mini_yaml` (subset only: flow maps, quoted strings, no anchors/multiline).

## 4. Mapping (git canonical → GitHub mirror)

| Source | GitHub object | Fields / labels | Title/body |
|---|---|---|---|
| change `<id>` | Issue + project item | Kind=change, Change=<id>, Stage=<E1..E9>, Status=(Todo/In progress/Blocked/Done) | title `change: <id>`; body = proposal `## Why` + `## What Changes` (truncate at 60,000 chars with a link to the file; body limit is (unverified) 65,536) + link to the git path |
| task `T<n>` (tasks.md `- [ ] X.Y` groups + work-orders with `task:`) | sub-issue of the change + item | Kind=task, Status from work-order status (pending→Todo, in-progress→In progress, done→Done, cancelled→closed not planned) | title `task: <T> <first line>` |
| ADR `NNN-*.md` | Issue (linked by mention + sub-issue) | Kind=adr, Status Done when ADR status accepted | title `adr: NNN <title>` |
| `escalation-NN` (open) / `needs-input` report | sub-issue, label `blocked` | Kind=escalation, Status=Blocked; closed when the escalation has an answer recorded | body = Options section |
| `spec-delta-NN` (proposed/revise) | comment on the change issue (bot marker), edited in place on status change | — | delta sections + `## Questions` + reply syntax |
| status.md (board) | single summary comment edited in place + Stage/Status fields | — | NEXT line, limits table, drift, pending deltas |
| archive done | close all issues, Status=Done | — | — |

Stage: `--stage E<n>` argument wins; otherwise the highest `verify-E<n>` with outcome pass, +1 (E1 when none).
Labels created on bootstrap: `openspec`, `openspec:change`, `openspec:task`, `openspec:adr`, `blocked`,
`gate:<E>:approved|rejected` for E1,E2,E3,E5,E7,E9, `delta:<nn>:accepted|rejected|revise` created lazily.
Every comment/body written by scripts starts with `<!-- openspec-github:bot v1 -->`.

## 5. CLI `gh_projects_sync.py` (stdlib, Python 3.8+; dry-run default)

```
gh_projects_sync.py bootstrap <repo-root> --change <id> --profile <yaml> [--apply] [--install-workflows] [--vendor]
gh_projects_sync.py push      <repo-root> --change <id> --profile <yaml> [--stage E3] [--apply]
gh_projects_sync.py pull      <repo-root> --change <id> --profile <yaml> [--apply]      # orchestrator only
gh_projects_sync.py close     <repo-root> --change <id> --profile <yaml> [--apply]
gh_projects_sync.py status    <repo-root> --change <id> --profile <yaml>               # read-only drift between git and GitHub
```
- Dry-run prints one line per planned call: `PLAN gh <args...>` and exits 0; `--apply` runs them.
- Exit codes: 0 ok; 1 error (message on stderr, full gh stderr included); 2 `status` found divergence; 3 tracker disabled
  (`kind: none` → prints `tracker disabled` and does nothing).
- Preflight on every command: `gh --version` >= 2.94.0 (rule 9; warn if not 2.103.x), `gh auth status` (no token
  printing; never `--show-token`), tracker block valid. On `owner_type: user` print the classic-PAT risk warning (rule 10).
- Idempotent: ids from github.yaml; a second `push --apply` with no git change issues zero mutating calls.
- All gh calls via `_gh.py`: `run(args, *, json=True, timeout=60)` → subprocess with `GH_PROMPT_DISABLED=1`,
  `NO_COLOR=1`, never shell=True; JSON parsing; rate-limit/secondary-limit detection with bounded backoff
  (max 3 retries); raises `GhError(cmd, code, stderr)`.
- Pure functions in `_model.py` (no I/O): parse tasks.md, records → desired GitHub state; diff desired vs github.yaml.

## 6. Approvals (pull) — trust model (rule 6, rule 12)

- The **Gate workflow** (Actions) is the only component that interprets user commands. It runs `gate_command.py`
  on the `issue_comment` payload passed through env (`COMMENT_BODY`, `COMMENT_AUTHOR`, `COMMENT_URL`,
  `COMMENT_ID`, `ISSUE_NUMBER`, `CREATED_AT`), never interpolated into `run:` text.
- Grammar (first line of the comment only, exact): `/approve E<n>`, `/reject E<n> <reason>`,
  `/accept delta-<nn>`, `/reject delta-<nn> <reason>`, `/revise delta-<nn> <answer...>`, `/answer escalation-<nn> <text>`.
- Accepted only if: author in `tracker.approvers`; author != `tracker.bot_login`; body has no bot marker; gate E<n>
  equals the change's current Stage field (no out-of-order approvals); comment created after the record it answers.
- On accept the workflow, authenticated as the App (org) or the PAT machine user (user), adds label `gate:E<n>:approved`
  and posts a confirmation comment: marker + a fenced YAML block
  `decision: {gate: E2, verdict: approved, by: alice, comment_url: ..., comment_id: ..., created_at: ...}`
  + the user's verbatim text quoted. On reject of the rule it posts a refusal with the reason (no label).
- `pull` (local, orchestrator only) reads only confirmation comments whose author login == `tracker.bot_login`,
  re-fetches the referenced user comment, re-checks author/allowlist/time, and then (with `--apply`) appends to
  status.md `## Approvals`:
  `- <UTC ts> | gate=E2 | subject=<change issue url> | source=github <comment_url> login=<x> | user said: "<verbatim first line + text>"`
  Delta/escalation decisions are printed as JSON for the orchestrator to apply (it still writes the records).
- `approval_source: chat` → pull refuses (exit 1, "approval_source is chat").

## 7. Workflows (assets/workflows/*.yml) — all actions SHA-pinned (F7), minimal permissions, concurrency per issue

- `openspec-gate.yml`: on `issue_comment: [created]`; `if: !github.event.issue.pull_request && startsWith(github.event.comment.body, '/')`;
  steps: checkout (default branch), setup-python, token step (App `client-id`/`private-key` with `permission-issues: write`,
  `permission-organization-projects: write` when org; else `secrets.OPENSPEC_PROJECT_PAT`), run vendored
  `gate_command.py` with env; `GH_TOKEN` = that token. `permissions: {contents: read}` for GITHUB_TOKEN.
  concurrency `openspec-gate-${{ github.event.issue.number }}`, cancel-in-progress false; timeout 5.
- `openspec-ci.yml`: on `pull_request` (paths `openspec/**` + code paths placeholder); installs pinned OpenSpec 1.15.0
  (Ask First at bootstrap: npm `@fission-ai/openspec@1.15.0`), runs `openspec validate <each changed change> --type change
  --strict --json --no-interactive`, vendored `check_records.py`, `detect_drift.py` against the PR base. GITHUB_TOKEN
  `contents: read` only. No secrets. Never `pull_request_target`.
- `openspec-board-sync.yml`: on `push` to default branch, paths `openspec/**`; runs `gh_projects_sync.py push --apply`
  for each changed change dir; App/PAT token; concurrency per ref.
- `openspec-archive.yml`: on `issues: [labeled]` with `github.event.label.name == 'gate:E9:approved'` AND
  `github.event.sender.login == <bot_login>` (configured via repo variable `OPENSPEC_BOT_LOGIN`); re-runs final gate
  (`check_records.py`, `detect_drift.py`, `openspec validate`), then `openspec archive <id> --yes` on branch
  `openspec/archive-<id>`, pushes with App token (contents: write, pull-requests: write), `gh pr create`. Never pushes the
  default branch. Change id comes from the issue's `Change` field / title parsed by script, not from the label text.

## 8. Agent `openspec-github-syncer` (U5)

Non-interactive executor (tools Read, Grep, Glob, Bash). Allowed: `gh_projects_sync.py push|status` (with `--apply` only
if the brief carries the orchestrator's relayed approval line for tracker writes), `gh --version`, `gh auth status`.
Forbidden: `pull`, `close`, `bootstrap --install-workflows`, any `gh` mutating call outside the script, git commit/push,
editing files under `openspec/` other than `handoff/github.yaml` (written by the script itself). Returns: commands run,
exit codes, PLAN/applied lines, `status` divergences. Never talks to the user.

## 9. Tests (offline, stdlib unittest)

- `fake_gh.py`: an executable stub put first on PATH (Windows: `gh.cmd`/`gh.bat` wrapper calling python) that reads
  `FAKE_GH_SCRIPT` (JSON: list of {match: [argv prefix], stdout, stderr, code}) and appends each argv to
  `FAKE_GH_LOG`. Tests assert on the log.
- Cases: dry-run makes no mutating calls; apply creates issue+item+fields then a second apply is a no-op; task status
  mapping; escalation → blocked sub-issue; delta comment edited in place; gate_command accept/reject matrix (author
  not in allowlist, bot author, bot marker in body, out-of-order gate, malformed command, injection-looking body
  `"/approve E2\n$(rm -rf /)"` treated as text); pull trusts only bot_login confirmations and is idempotent; tracker
  kind none → exit 3; gh < 2.94 → exit 1.
- Fixture repo: copy of `handoff-core` quarkus fixture `list-tenant-items` + a minimal `openspec/changes/list-tenant-items/{proposal.md,tasks.md}`.
