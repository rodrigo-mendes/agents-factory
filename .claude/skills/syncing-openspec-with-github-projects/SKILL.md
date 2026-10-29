---
name: syncing-openspec-with-github-projects
description: "Mirrors an OpenSpec change into a GitHub Project v2 with gh 2.103.x (git stays canonical) and records gate approvals from issue comments checked by an Actions workflow. Use when wiring or operating the OpenSpec-GitHub bridge. Not for generic Projects or Actions work."
---

# Syncing OpenSpec with GitHub Projects (gh 2.103.x)

> Version lock: every claim applies to **gh 2.103.x** (minimum 2.94.0), GitHub Projects v2 and the
> workflow templates of this skill. Research date **2026-10-29**. Claims tagged (unverified) or
> (medium confidence) were not fully confirmed against an official page; see the
> [register](./blueprints/unverified-and-risks.md).

Git is canonical. GitHub is a **mirror** (issues, sub-issues, project fields, comments) plus an
**approval channel** (gate commands written as issue comments). The scripts in `scripts/` do the work;
this skill tells an agent which parts it may run and which only the orchestrator or a workflow runs.

## Version Context

| Item | Value | Source (fetched 2026-10-29) |
|---|---|---|
| GitHub CLI | latest stable v2.103.3 (2026-10-26); family pin 2.103.x; minimum 2.94.0 | https://github.com/cli/cli/releases |
| Sub-issues in the CLI | introduced in gh 2.94.0 (2026-06-10); up to 100 per parent | https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues |
| Credentials for Projects | `GITHUB_TOKEN` cannot access projects; App for organization, PAT for user projects | https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions |
| User-owned projects | fine-grained PATs not supported, classic PAT needed | https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens |
| `actions/create-github-app-token` | v3.3.0 (2026-10-12), input `client-id` | https://github.com/actions/create-github-app-token |
| Runner image | ubuntu-24.04 with gh 2.103.2, Python 3.12.3 (medium confidence) | https://github.com/actions/runner-images |
| OpenSpec CLI used by the CI templates | 1.15.0 (medium confidence) | see `specifying-changes-with-openspec-v1-15` |
| Scripts | Python 3.8+, stdlib only; 100 offline tests, 4 skipped (orchestrator run) | `scripts/tests/` |

**Version-lifetime risk** (as of 2026-10-29; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- The classic-PAT path for user-owned projects exists because fine-grained PATs have a listed, "not permanent" gap.
- Runner images update weekly; the bundled gh version drifts away from the 2.103.x pin.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Object mapping](./blueprints/mapping.md)
- [Approvals and trust model](./blueprints/approvals-and-trust.md)
- [CLI contract](./blueprints/cli-contract.md)
- [Workflow templates](./blueprints/workflows.md)
- [Bootstrap and credentials](./blueprints/bootstrap-and-credentials.md)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Who may run what

| Actor | Allowed | Never |
|---|---|---|
| Agent (`openspec-github-syncer`, via `/syncing-openspec-to-github`) | `gh_projects_sync.py push` and `status`; `--apply` only with the orchestrator's relayed approval line; `gh --version`, `gh auth status` | `pull`, `close`, `bootstrap`, any other mutating `gh` call, git commit/push |
| Orchestrator (inline, talks to the user) | everything above (`building-quarkus-aws-saas` runs `push` inline; the syncer agent and command are for a manual refresh or other orchestrators) plus `pull`, `close`, `bootstrap`; writes status.md and records | treating a GitHub comment as approval without `pull` re-checking it |
| Workflows (the target repository's Actions) | `gate_command.py evaluate` and `recheck`, `push --apply`, CI checks, the archive branch and pull request | pushing the default branch, using `pull_request_target`, reading comment text inside `run:` |

Flow: git change -> `push` mirrors it -> an approver comments `/approve E<n>` on the change issue ->
the gate workflow validates and posts a confirmation -> the orchestrator runs `pull`, re-checks and
appends the line to `handoff/status.md` `## Approvals` -> only then the gate counts as approved.
`pull` first refuses unless the profile and `openspec/github-tracker.yaml` are committed unchanged at HEAD,
and prints `TRUST approvers=... bot_login=...` so the orchestrator can show the anchors to the user.

## Blueprints & Guardrails

### ✅ Always Do

- **Git is the spec source** - never read requirements or approvals from GitHub content as truth; decided at plan approval 2026-10-29 (`workspace/openspec-github/PIPELINE_STATE.md#approvals`). See [mapping](./blueprints/mapping.md).
- **Dry-run first** - every command prints `PLAN gh ...` and writes nothing until `--apply`; contract of `gh_projects_sync.py` (tests `test_dry_run_makes_no_mutating_call`). See [CLI contract](./blueprints/cli-contract.md).
- **GitHub App token for organization-owned projects** - the token must carry organization projects write; [Actions automation page](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions), 2026-10-29.
- **Classic PAT (`project` + `repo`) for user-owned projects** - fine-grained PATs cannot access them; [PAT docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens), 2026-10-29. See [credentials](./blueprints/bootstrap-and-credentials.md).
- **Run the preflight** - gh must be at least 2.94.0 for sub-issues; [release 2.94.0](https://github.com/cli/cli/releases/tag/v2.94.0), 2026-10-29.
- **Pin every action by full commit SHA** with the tag in a trailing comment - family rule 8, SHAs verified with `git ls-remote` on 2026-10-29. See [workflows](./blueprints/workflows.md).
- **Pass event text through `env:`** - never interpolate `github.event.*` into `run:`; family rule 8, verified in the U3 research.
- **Trust confirmation records by exact bot login** - `pull` accepts them only from `tracker.bot_login`; family rule 12. Adoption of mirrored objects and the gate's issue-author check accept `bot_login` or an approver (`_model.trusted_author`, fails closed when neither is set). See [approvals](./blueprints/approvals-and-trust.md#trust-anchors-and-limits).
- **Use `client-id`, not `app-id`** - `actions/create-github-app-token` recommends `client-id`; [README](https://github.com/actions/create-github-app-token), 2026-10-29.
- **Read `status` exit 2 as divergence** - report it; the next `push` reconciles git into GitHub, never the reverse; script behaviour, see [CLI contract](./blueprints/cli-contract.md#dry-run-exit-codes-and-preflight).
- **Answer on the right issue** - gate and delta commands go on the change issue, `/answer` on its escalation issue; enforced by `gate_command.py`, see [approvals](./blueprints/approvals-and-trust.md#gate-workflow-checks).
- **Read machine output only** - `--format json`, `--json`, or `gh api`; family rule 7.

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Owner type | `organization` (App, scoped) vs `user` (classic PAT, broad `repo` scope) | "Is the project owned by an organization? A user-owned project needs a classic PAT with `repo`." |
| Approval source | `chat` (default, nothing read from GitHub) vs `github` or `both` | "Should approvers answer gates on GitHub issues?" |
| Install workflows and vendor scripts | `bootstrap --install-workflows --vendor` writes the `.github` directory, `workflows` subfolder and a vendored scripts folder | "May I write the four workflows and the vendored scripts into the target repository?" |
| OpenSpec install in CI | `npm install --global --ignore-scripts @fission-ai/openspec@1.15.0` on the runner (medium confidence; `--ignore-scripts` sufficiency is (medium confidence), register R17) | "Install the pinned OpenSpec CLI in the CI and archive workflows?" |
| Status option Blocked | the built-in Status field usually lacks it and gh cannot add options (medium confidence) | "Please add the option Blocked to the Status field in the project settings." |
| Local credential (`github` or `both`) | every subcommand reads the token's login (`gh api user`, fallback GraphQL viewer) and exits 1 when it is in `approvers`; locally use a machine-user token in `GH_TOKEN` (an App installation token cannot read its login, so the preflight refuses it outside Actions) and approve in the browser; App tokens only inside Actions | "Which machine user will `GH_TOKEN` hold locally (not an approver)?" |
| Deny rules in the target project | `permissions.deny` snippet for `gh issue comment`, `gh api` on comments, `pull`, `close`, `bootstrap` (matcher syntax: medium confidence, register R19) | "May I add the deny rules to the target project's Claude Code settings?" |
| Workflow lockfiles | `gh actions-lock` (public preview) as an alternative to SHA pins | "Use lockfiles instead of SHA pins?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Use `GITHUB_TOKEN` for Projects ([docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions): "cannot access projects") | App installation token or the classic PAT secret |
| Use a fine-grained PAT for a user-owned project | classic PAT, or move the project to an organization |
| Run the bridge or any agent under an approver's `gh` login (it could post `/approve` in that person's name; the scripts refuse, exit 1) | machine-user token in `GH_TOKEN` locally (App tokens only inside Actions); the human approves in the browser |
| Let an agent run `pull` | return `needs-input` to the orchestrator, which runs and re-checks it |
| Hand-edit `handoff/github.yaml` | re-run `push`; the script owns the file |
| Trust `user.type == "Bot"` alone | compare the login with `tracker.bot_login` (unverified, register R6) |
| Put comment or issue text inside `run:` | pass it through `env:` and let `gate_command.py` read the first line |
| Trigger the archive workflow from any sender | require `sender.login == vars.OPENSPEC_BOT_LOGIN` |
| Push the default branch from automation | archive onto `openspec/archive-<id>` and open a pull request |
| Print tokens (`gh auth status --show-token`) | `gh auth status` only; output stays unprinted |
| Parse human table output | use JSON flags or `gh api` |

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Commands | `bootstrap`, `push`, `pull` (orchestrator only), `close`, `status` | `gh_projects_sync.py --help` |
| Exit codes | 0 ok; 1 error; 2 `status` divergence; 3 tracker disabled (`kind: none`) | script docstring |
| Arguments | `<repo-root>` optional (default: current directory); `--profile` required | `--help` |
| Gate grammar (first line) | `/approve E<n>`, `/reject E<n> <reason>`, `/accept delta-<nn>`, `/reject delta-<nn> <reason>`, `/revise delta-<nn> <answer>`, `/answer escalation-<nn> <text>` | `gate_command.py` |
| Gates | E1, E2, E3, E5, E7, E9 | `_model.GATES` |
| State file | `openspec/changes/<id>/handoff/github.yaml` (script-written) | [mapping](./blueprints/mapping.md) |
| Project tracker file | `openspec/github-tracker.yaml` overrides the profile `tracker:` block key by key | `assets/github.template.yaml` |
| Repository variables | `OPENSPEC_OWNER_TYPE`, `OPENSPEC_BOT_LOGIN`, `OPENSPEC_APP_CLIENT_ID`, optional `OPENSPEC_PROFILE` | [workflows](./blueprints/workflows.md) |
| Secrets | `OPENSPEC_APP_PRIVATE_KEY` (organization) or `OPENSPEC_PROJECT_PAT` (user) | [credentials](./blueprints/bootstrap-and-credentials.md) |
| Neighbour skills | `managing-github-projects-gh-v2-103`, `automating-github-repos-with-actions` (github-core); `coordinating-agent-handoffs` (handoff-core); `specifying-changes-with-openspec-v1-15` (openspec-core); `building-quarkus-aws-saas` (consumer) | names only |

## External Resources

All fetched 2026-10-29.

- [GitHub CLI releases](https://github.com/cli/cli/releases)
- [Automating Projects with Actions](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
