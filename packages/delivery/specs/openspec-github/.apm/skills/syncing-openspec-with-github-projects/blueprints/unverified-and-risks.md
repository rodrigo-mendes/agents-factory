# Unverified and risks register

Research date 2026-10-29. Tags are plain: (medium confidence), (unverified). Items marked "to confirm"
are checked in the live smoke test ([bootstrap step 7](./bootstrap-and-credentials.md#bootstrap-steps)).
Back to [SKILL.md](../SKILL.md).

## Register

| ID | Item | Tag | Effect if wrong | Check |
|---|---|---|---|---|
| R1 | GraphQL field values expose `updatedAt` on `ProjectV2ItemFieldSingleSelectValue` and text values (family fact F11; schema mirror, not the docs page) | (medium confidence) | gate cannot tell when Stage was set; every gate is refused | live smoke test |
| R2 | `gh api ... --input -` reads the JSON body from stdin | (unverified) | writes fail at the first call | live smoke test; fall back to `-f` fields |
| R3 | `gh api --paginate --slurp` returns a list of pages | (unverified) | adoption and `pull` read one page; code also accepts a flat list | live smoke test |
| R4 | REST issue update accepts `state_reason` `completed` and `not_planned` | (unverified) | cancelled tasks close without the right reason | live smoke test |
| R5 | rate limits are recognised from gh's stderr text | (unverified) | no retry, the run exits 1 | rerun later |
| R6 | `user.type == "Bot"` is not used as a trust anchor | (unverified) | the exact-login check stays the only anchor | none needed |
| R7 | the built-in Status field usually lacks "Blocked" and gh cannot add options | (medium confidence) | Blocked values are skipped with a warning | user adds the option in the UI |
| R8 | with `approval_source` `github` or `both` the local token must not be an approver (rule 13), so adoption of mirrored objects works only for objects created by `bot_login` (or an approver, who cannot run locally); a local apply under another machine user is not adopted by runner pushes | known limit (script behaviour) | duplicates on the next runner push | run locally with the `bot_login` identity |
| R9 | events created by an App or PAT trigger the archive workflow, unlike `GITHUB_TOKEN` events (U3 G2) | (medium confidence) | archive never starts | live smoke test with a test change |
| R10 | `github.event.sender.login` for an App equals `name[bot]`, so it can match `vars.OPENSPEC_BOT_LOGIN` | (medium confidence) | archive never starts | compare with the issue event payload |
| R11 | archive App permission set is contents write and pull-requests write | (unverified) | push or `gh pr create` fails | live smoke test |
| R12 | npm and Node are available on `ubuntu-24.04`; `@fission-ai/openspec@1.15.0` installs from npm | (medium confidence) | CI and archive fail at install | Ask First at bootstrap |
| R13 | a required check behind a `paths:` filter stays Pending when skipped | (medium confidence) | merges blocked | drop the filter if the check is required |
| R14 | local gh 2.93.0 fails the preflight by design (minimum 2.94.0) | known limit (tested) | none: upgrade | `gh --version` |
| R15 | issue body limit of 65,536 characters (the script truncates at 60,000) | (unverified) | truncation earlier or later than needed | none |
| R16 | runner image ships gh 2.103.2 and Python 3.12.3 (family fact F10) | (medium confidence) | gh drift from the 2.103.x pin warns, older than 2.94.0 fails | read the warning |
| R17 | `npm install --ignore-scripts` of `@fission-ai/openspec@1.15.0` works and keeps the archive `prepare` job safe: the registry manifest (https://registry.npmjs.org/@fission-ai%2Fopenspec/1.15.0, read 2026-10-29) has no preinstall/install/postinstall script, `bin` is `bin/openspec.js`, 12 pure-JS direct dependencies; transitive dependencies and a real CLI run not checked (no lockfile) | (medium confidence) | npm code still runs in `openspec`; it holds no token and its output is a size-capped patch | branch protection / CODEOWNERS; consider a lockfile |
| R18 | job output size limit is above the 700,000-byte patch cap used by the archive workflow | (unverified) | `prepare` or `publish` fails on a large archive | live test with a large change |
| R19 | exact Claude Code deny-rule matcher syntax for the target-project snippet (`:*` prefix versus space-star, `*comments*` wildcard) | (medium confidence) | a deny rule does not match and the command is not blocked | check the Claude Code settings docs; try a denied command |

Counts: 19 entries = 8 (unverified) (R2, R3, R4, R5, R6, R11, R15, R18) + 9 (medium confidence) (R17, R1, R7,
R9, R10, R12, R13, R16, R19) + 2 known limits (R8, R14).

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md Version Context (Runner image row); Source Bibliography (runner-images) | R16 |
| (medium confidence) | SKILL.md Version Context (OpenSpec CLI row) and Ask First (OpenSpec install in CI); workflows.md Behaviours to know (npm install) | R12 |
| (medium confidence) | SKILL.md Ask First (Status option Blocked); mapping.md Project fields and labels | R7 |
| (medium confidence) | approvals-and-trust.md Gate workflow checks (Stage `updatedAt`); Source Bibliography (GraphQL schema mirror) | R1 |
| (medium confidence) | workflows.md Behaviours to know (App/PAT events trigger archive) | R9 |
| (medium confidence) | workflows.md Behaviours to know (bot login form); bootstrap-and-credentials.md Organization project step 4 | R10 |
| (medium confidence) | workflows.md Behaviours to know (required check Pending) | R13 |
| (unverified) | SKILL.md Never Do (`user.type`); approvals-and-trust.md Trust anchors and limits; never-do-patterns.md Approvals | R6 |
| (unverified) | cli-contract.md How gh is called (`--input -` row) | R2 |
| (unverified) | cli-contract.md How gh is called (`--paginate --slurp` row) | R3 |
| (unverified) | mapping.md Stage and Status (Done tasks) | R4 |
| (unverified) | cli-contract.md How gh is called (rate limits) | R5 |
| (unverified) | workflows.md Behaviours to know (archive permission set); bootstrap-and-credentials.md Organization project step 2 | R11 |
| (unverified) | mapping.md Objects (body truncation) | R15 |
| known limit (no tag) | mapping.md Markers and adoption; bootstrap-and-credentials.md Bootstrap steps (step 6); never-do-patterns.md State and mirror | R8 |
| (medium confidence) | SKILL.md Ask First (OpenSpec install in CI); workflows.md Archive jobs and Behaviours to know | R17 |
| (unverified) | workflows.md Archive jobs (job output size) | R18 |
| (medium confidence) | SKILL.md Ask First (Deny rules); bootstrap-and-credentials.md Deny rules for the target project | R19 |
| known limit (no tag) | cli-contract.md Dry-run, exit codes and preflight; bootstrap-and-credentials.md Local use | R14 |

## Version-lifetime risk

As of 2026-10-29:

- gh 2.103.3 (2026-10-26) is the latest stable; flags and JSON fields were verified only on 2.103.x.
- Sub-issue commands need 2.94.0 or later (GitHub.com and GHES 3.17+).
- Fine-grained PAT support for user-owned projects is a listed gap described as "not permanent"; when it
  closes, the classic-PAT path should be revisited.
- Runner images update weekly; the bundled gh version moves away from the pin.
- `actions/create-github-app-token` is at v3.3.0; the SHA pins need refreshing on upgrade.
- Workflow lockfiles (`gh actions-lock`) are public preview and not the default.

## Source Bibliography

All read 2026-10-29 unless marked.

| Source | URL | Used for |
|---|---|---|
| gh releases (v2.103.3, v2.94.0) | https://github.com/cli/cli/releases | F1, F5 |
| Adding sub-issues | https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues | F5 |
| Automating Projects using Actions | https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions | F2, F3, F9 |
| Managing personal access tokens | https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens | F6 |
| create-github-app-token | https://github.com/actions/create-github-app-token | F4, F8 |
| runner-images (via U3 research) | https://github.com/actions/runner-images | F10 (medium confidence) |
| GraphQL schema mirror | https://raw.githubusercontent.com/octokit/graphql-schema/main/schema.graphql | F11 (medium confidence) |
| Action pins | `git ls-remote https://github.com/actions/<repo> refs/tags/<tag>` | F7 |
| Pipeline decisions | `workspace/openspec-github/PIPELINE_STATE.md#approvals` | rules 4, 5, 10 |
