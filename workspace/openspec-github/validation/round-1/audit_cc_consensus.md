# CC Architecture Multi-Model Report - openspec-github / github-core / openspec-core (round 1)

Date: 2026-10-29. Auditor: architecture-auditor (lenses A/B/C applied sequentially in one context, per the
pipeline's flat fan-out rule; no sub-agents spawned). Spec: `.claude/skills/audit-cc-architecture-consensus/SKILL.md`.
Approval relay: scope U1-U7, P4-P6, rounds=3, user words "Aprovo, seguir com P4–P6 completo (Recomendado)"
recorded in `workspace/openspec-github/PIPELINE_STATE.md#approvals` (relay, not a new approval).

Target (generated `.claude/`): `skills/syncing-openspec-with-github-projects/` (scripts, assets/workflows),
`skills/syncing-openspec-to-github/`, `agents/openspec-github-syncer.md`, `rules/openspec-github-state.md`,
`skills/managing-github-projects-gh-v2-103/`, `skills/automating-github-repos-with-actions/`,
`skills/specifying-changes-with-openspec-v1-15/`, consumers `building-quarkus-aws-saas`,
`coordinating-quarkus-aws-handoffs`, `coordinating-agent-handoffs`. Package graph: `packages/{openspec-core,github-core,openspec-github,handoff-core,quarkus-aws-saas}/apm.yml`.

Objective checks run (P5): YAML frontmatter parsed with PyYAML for all 10 artifacts (all parse; `name` == folder/filename;
descriptions 214-340 chars, all contain "Use when"); 0 broken relative links across all target `.md` files;
hybrid blueprints present (`Version-lifetime risk` + `Source Bibliography` + >= 6 scenarios) in all 4 knowledge skills;
`diff -rq` packages/openspec-core vs .claude copy = identical; counts on disk: 226 skills, 41 agents, 50 rules,
67 `disable-model-invocation: true` commands, 32 packages.

## 1. Executive Summary

Consensus Verdict: **CONDITIONAL** (2 consensus findings at 3/3; two HIGH findings; Models B and C < 7.0).

| Model | Score | Unique findings |
|---|---|---|
| Model A - Scope | 8.0 / 10 | 2 |
| Model B - Flow | 6.8 / 10 | 0 |
| Model C - Engine (incl. Actions trust) | 6.5 / 10 | 3 |

Answers to the four questions:
1. **Scope**: each artifact is at the right level (knowledge skill / fork command / non-interactive agent / scoped rule).
   The openspec-core split is clean: DAG openspec-core -> factory-core; handoff-core -> openspec-core; github-core ->
   factory-core; openspec-github -> {openspec-core, handoff-core, github-core}; quarkus-aws-saas -> {handoff-core, openspec-github}.
   No reverse dependency, no cross-package relative link (the only `../<skill>/` links are coordinating-quarkus-aws-handoffs ->
   building-quarkus-aws-saas, same package). github-core stays generic in content; only name-level mentions of the bridge (LOW).
2. **Flow**: routing is correct (`context: fork` + `agent: openspec-github-syncer` + `disable-model-invocation: true`); the
   agent has no Agent tool (cannot nest); only the inline orchestrator runs `pull`. Gaps: an agent CAN originate an approval
   through the operator's shared `gh` credential (HIGH, F1); the archive workflow acts before `pull` re-checks (F5); the
   command's documented canonical call always ends in needs-input (F4).
3. **Engine**: frontmatter valid everywhere; rule globs valid but slightly broad and miss the vendored dir; agent tools are
   minimal but Bash is prompt-limited only; naming of `syncing-openspec-to-github` matches 30 of 67 existing commands but
   contradicts `naming-conventions.md` (recommend amending the rule, not renaming).
4. **Actions trust model**: one HIGH - `openspec-archive.yml` runs unlocked third-party npm code with a write token in its
   environment (F2). gate/board-sync/ci are otherwise sound (env-only event text, SHA pins, default-branch code for
   privileged triggers, `pull_request` not `pull_request_target`, fail-closed `trusted_author`, exact-login bot anchor).

## 2. Consensus Findings (3/3) - MUST FIX

### F1 [HIGH] An agent can author a genuine approver comment through the shared local `gh` login
- **Model A (G1.2 least privilege)**: `.claude/agents/openspec-github-syncer.md:8` `tools: Read, Grep, Glob, Bash`; line 34 admits
  "the Bash tool itself is not restricted". The non-mutation guarantee is prompt-only.
- **Model B (approval origin)**: the docs make the local operator an approver: `syncing-openspec-with-github-projects/SKILL.md:87`
  (Ask First "operator must be `bot_login` or an approver"), `blueprints/bootstrap-and-credentials.md:56`,
  `blueprints/never-do-patterns.md:54`. When the local `gh auth` identity is in `tracker.approvers`, any Bash-capable agent
  (this syncer, or executors such as quarkus-lambda-integrator) can run `gh issue comment <n> --body "/approve E3"`. The gate
  workflow (`_model.py:692-700`) and `pull`'s re-check (`_model.py:795-820`) both accept it, because the author really is an
  approver. "Approvals never originate from an agent" therefore holds only by instruction.
- **Model C (ECC.16 permissions)**: `.claude/settings.json` has no deny for `gh issue comment`, `gh api */comments` or
  `gh_projects_sync.py pull|close|bootstrap`; `gh_projects_sync.py` never checks the local login (no `gh api user` call; grep).
- **Remediation**: (a) Never-Do and preflight: the identity used for local `push --apply` must be `bot_login` or a
  non-approver machine user. In `preflight()`, read `gh api user --jq .login` and refuse `--apply` (exit 1) when that login is in
  `approvers`; change the Ask First row at SKILL.md:87 and bootstrap step 6 to match. (b) Add to `.claude/settings.json`
  `permissions.deny` (or a PreToolUse hook) for `Bash(gh issue comment *)`, `Bash(gh api *comments*)`, `Bash(gh pr comment *)`
  and `Bash(python *gh_projects_sync.py pull*)`, `...close*`, `...bootstrap*`. Keep the agent prompt limits as well.

### F3 [MEDIUM] CLAUDE.md (G0) does not know the new packages and is stale
- **Model A (G0.4/G0.5, XCC.1)**: CLAUDE.md lists neither `/syncing-openspec-to-github` nor `openspec-github-syncer`, nor the
  packages openspec-core, github-core, openspec-github.
- **Model B (FCC.9 fallback)**: the CLAUDE.md fallback ("If a request does not match any `/command` listed above ... route or
  decline") will steer away from the unlisted command.
- **Model C (ECC.14 CLAUDE.md contradiction)**: CLAUDE.md:83-84 places `specifying-changes-with-openspec-v1-15` in handoff-core
  (now openspec-core). Counts are off: CLAUDE.md:137 says 40 agents (disk 41), :146 222 skills / 66 commands (disk 226 / 67),
  :128 "The 66 commands", :150 49 rules (disk 50), :155 29 packages (disk 32).
- **Remediation**: add an openspec-github / github-core / openspec-core paragraph to the package list (command, agent, rule,
  "off by default"), move the OpenSpec skill to openspec-core in the handoff-core bullet, add a How-to-run line, and update all
  five counts. Edit through the source of CLAUDE.md (hand-authored), not `.claude/`.

## 3. Two-Model Findings (2/3) - SHOULD FIX

### F4 [MEDIUM] The command's canonical invocation can never succeed as documented (B, C)
- B (FCC.20): `syncing-openspec-to-github/SKILL.md:53` and agent line 30 require the repository root and profile path, otherwise
  needs-input; but `argument-hint` (line 4) is `<change-id> [--stage E<n>] [--apply]` and the canonical example (line 57) plus
  scenario 1 (`blueprints/evaluation-scenarios.md:7-12`) expect a plan from just `<change-id>`. When a user calls the command
  directly there is no orchestrator, so the "relayed approval line" for `--apply` (line 51, example line 58) cannot exist.
  The user's own typed `--apply` is real user consent, but it is always refused.
- C (ECC.6 fork isolation, ECC.18): the forked brief assumes orchestrator-supplied state (root, profile, relay) that a fork does not have.
- Model A dissent: structure is complete (G3.1-G3.4 pass).
- Fix: default repo root to the cwd, add `--profile <yaml>` to `argument-hint`, state that a user's direct `/syncing-openspec-to-github ... --apply`
  counts as the user's own approval for that one call (or drop `--apply` from direct use and say so), and align example 2 and scenario 2.

### F5 [MEDIUM] The archive workflow acts on a GitHub-only approval before the orchestrator `pull` re-check (B, C)
- B: SKILL.md:57-59 says a gate "counts as approved" only after `pull` re-checks and appends to `status.md`. `openspec-archive.yml:4,26`
  starts on the label `gate:E9:approved` set by the gate workflow, then runs `openspec archive`, pushes `openspec/archive-<id>`
  and opens a PR, without the git-side approval line.
- C: the "Re-run the final gate" step (lines 79-88) does not assert an E9 line in `handoff/status.md` `## Approvals`.
- Mitigation already present: only a reviewable PR, never the default branch.
- Fix: in the archive job, fail unless `status.md` holds an `gate=E9` approval line (a `check_records.py` flag or a grep), or document the
  workflow as a pre-approval proposal that the orchestrator's `pull` must precede before merging.

### F7 [MEDIUM] `pull` reads its trust anchors from the mutable working tree (B, C)
- `_model.py:92-101` (`resolve_tracker`, "the project file wins") merges `openspec/github-tracker.yaml` from the local checkout;
  `gh_projects_sync.py:564` (bot login) and `_model.py:803` (approvers) use it. Any agent with Edit/Write in the target repo can
  add an approver or change `bot_login` before the orchestrator runs `pull`. The rule `openspec-github-state` fires on edits, but
  it is advice only.
- Fix: in `pull`, refuse when `openspec/github-tracker.yaml` or the profile has uncommitted changes (`git status --porcelain -- <file>`)
  or differs from the default branch, and always print the effective `approvers`/`bot_login` in the output so the orchestrator shows them to the user.

### F8 [LOW] Syncer agent and command are not wired into the orchestrator (A, B)
- A (XCC.3) / B (FCC.7): `building-quarkus-aws-saas/SKILL.md:138,168` and `blueprints/tracker-github-projects.md:22` run `push`
  inline; neither names `openspec-github-syncer` nor `/syncing-openspec-to-github` (repo grep: references only inside the
  openspec-github package). The agent description says "Use when the orchestrator needs...", but it is reachable only by user
  command or auto-delegation.
- Fix: either add one line to the tracker blueprint ("for a drift check without the main context, spawn `openspec-github-syncer`
  with root, profile and, for writes, the approval line") or reword the agent/command descriptions to "user-run board refresh".

### F9 [LOW] Naming: gerund-style action command vs naming-conventions.md (A, C)
- `syncing-openspec-to-github` (fork command) breaks `naming-conventions.md` (action commands = `action-noun`/`domain-role`), but
  30 of 67 commands on disk are gerund-named (e.g. `syncing-spec-from-code`, `researching-platform-software`, `evaluating-skill-scenarios`).
  The precedent beats the written rule. It also differs by only the last words from the knowledge skill `syncing-openspec-with-github-projects`.
- Recommendation (no rename): amend `naming-conventions.md` to allow `gerund-noun` for action commands that front a knowledge skill,
  and add a disambiguation line to both descriptions ("command: ..."; "knowledge: ...").

### F11 [LOW] Rule globs: slightly over-broad, and the vendored dir is missing (B FCC.15, C ECC.2)
- `rules/openspec-github-state.md:7` `**/openspec-*.yml` matches any `openspec-*.yml` anywhere, not only workflows. The vendored
  scripts dir `.github/openspec-github/**` is not covered, so editing it by hand (which `_vendor.py verify` then rejects) gets no guardrail.
- Fix: `**/.github/workflows/openspec-*.yml`, `**/assets/workflows/openspec-*.yml`, plus `**/.github/openspec-github/**` with a
  "re-vendor, never hand-edit" bullet.

## 4. Single-Model Findings - CONSIDER

### F2 [HIGH] Archive workflow exposes a write token to unlocked npm code (C only)
- `openspec-archive.yml:56-65` mints the App token (contents + pull-requests write) before `npm install --global @fission-ai/openspec@1.15.0`
  (lines 74-77: no lockfile, no `--ignore-scripts`, transitive deps float). Lines 90-101 then run `openspec archive` (npm code) in the same
  step as `GH_TOKEN`. In `owner_type: user` that token is the classic PAT with `repo` scope over all the owner's repositories. A compromised
  transitive dependency can push to an unprotected default branch, rewrite `.github/openspec-github/` or `openspec/github-tracker.yaml`
  (approvers), or leak the PAT.
- Likely real: yes. A and B miss it because it is inside a workflow template, not an agent artifact.
- Fix: split the step. (1) Run `openspec archive` and `git commit` with no token in env. (2) Mint the App token after that step.
  (3) Use a final step with `GH_TOKEN` only for `gh auth setup-git`, `git push` and `gh pr create`. Install with `--ignore-scripts`
  (or `npm ci` from a committed lockfile). Recommend branch protection / CODEOWNERS on the default branch, `.github/openspec-github/**`
  and `openspec/github-tracker.yaml`. Apply the same install hardening to `openspec-ci.yml:48-51` (no secrets there, so LOW).

### F6 [MEDIUM] Gate workflow answers every slash-comment from anyone, on any issue (C only)
- `openspec-gate.yml:32` filters only on `startsWith(body,'/')`, non-PR, non-bot, and lines 61-70 mint a write token for each one.
  `gate_command.py:154-155` refuses malformed commands before any issue check, and `_model.py:696-700` checks approvers before the
  key-marker check. So a non-approver typing `/approve ...` on any issue in the repo gets a bot refusal comment. That means noise,
  Actions minutes, rate-limit pressure and collisions with other `/approve` bots.
- Likely real: yes (operational, not privilege escalation).
- Fix: add `contains(github.event.issue.labels.*.name, 'openspec')` to the job `if:`. In `evaluate`, check the issue marker first and
  ignore non-approvers silently, refusing only approvers' malformed or out-of-order commands.

### F10 [LOW] Generic packages carry bridge-specific framing (A only)
- handoff-core `_handoff_lib.py:224-266` and `coordinating-agent-handoffs/blueprints/profile-format.md:70-90` encode `kind: github-projects`,
  `owner_type`, `bot_login` requirements. github-core `managing-github-projects-gh-v2-103/SKILL.md:10` and
  `automating-github-repos-with-actions/SKILL.md:9` name the OpenSpec bridge and state its "mirror + approval channel" stance.
  openspec-core `SKILL.md:10` names downstream consumers. All are name-level only; the dependency direction is intact.
- Fix (optional): in handoff-core, validate only `kind` and delegate kind-specific keys to the bridge. In github-core, replace the
  bridge-specific sentence with "consumers decide whether GitHub content is authoritative".

### F12 [LOW] `pull` re-check does not bind the user comment to the change issue (C only)
- `recheck_user_comment` (`_model.py:795-820`) verifies author, time and text, but not that the fetched comment's `issue_url` is the
  change issue, and not the Stage at comment time. This matters only with a stolen bot key/PAT (forged confirmation pointing at an
  approver's `/approve E9` posted elsewhere or earlier). `approvals-and-trust.md` "Trust anchors and limits" covers stolen keys only in part.
- Fix: compare `user_comment.issue_url` with the change/escalation issue URL from `github.yaml`.

### F13 [LOW] Command lacks an explicit verification step (A only, G3.7)
- `syncing-openspec-to-github/SKILL.md` has Output (lines 70-73) but no check. Add: "the reply contains the exit code of each command
  and, after `--apply`, a `status` exit 0 or the DIVERGE list".

## 5. Per-Model Detailed Results

### 5.1 Model A - Scope (G0-G4 + XCC)
| Layer | Score | Notes |
|---|---|---|
| G0 CLAUDE.md (5%) | 4 | F3 stale catalog/counts/package |
| G1 agent (20%) | 8 | role, P0, non-responsibilities, model sonnet valid; Bash prompt-limited (F1) |
| G2 rule (20%) | 9 | single concern, no routing table, no code, links to skill; globs F11 |
| G3 command (20%) | 8 | fork+agent+dmi, argument-hint quoted, evaluation-scenarios present; F4/F13 |
| G4 knowledge skills (30%) | 9 | three-tier, version context, Quick Navigation, blueprints linked not `@`-imported, hybrid register complete; F10 |
| G-perm (5%) | 5 | no deny for gh comment / pull (F1) |
**Model A Overall: 8.0 / 10**

### 5.2 Model B - Flow (FCC.1-FCC.20)
| Component | Score | Notes |
|---|---|---|
| Commands (25%) | 6.5 | FCC.1-3 pass; FCC.20 fails for the canonical call (F4) |
| Subagent (30%) | 7 | FCC.6/9/10 pass, no Agent tool, no cycle; F1 approval origin; F8 not wired |
| Rules (20%) | 8 | FCC.11-14 pass; FCC.15 broad glob (F11) |
| Skills (25%) | 6 | FCC.16-19 pass (0 broken links); F5 archive before pull, F7 anchors |
**Model B Overall: 6.8 / 10**

### 5.3 Model C - Engine (ECC.1-ECC.18) + Actions trust
| Component | Score | Notes |
|---|---|---|
| paths (25%) | 8 | valid globs (ECC.3); over/under-match (F11) |
| Budget (25%) | 8.5 | 3 new auto-listed descriptions, each <= 290 chars with "Not for"; command off-budget (ECC.5) |
| Fork/Disclosure (20%) | 6.5 | ECC.7 pass; ECC.6 fork assumes orchestrator state (F4) |
| Conflicts (15%) | 5 | ECC.14 CLAUDE.md (F3); ECC.16 permissions (F1) |
| Frontmatter/Governance (15%) | 4 | ECC.8-12/17/18 all pass; governance weighted by trust findings F2 (HIGH), F6, F7 |
**Model C Overall: 6.5 / 10**

## 6. Unified Remediation Roadmap
| Priority | Issue | Consensus | Action | File | Effort |
|---|---|---|---|---|---|
| 1 | F1 agent can approve via shared gh login | 3/3 HIGH | preflight refuses `--apply` when local login is an approver; settings deny for gh comment/pull/close/bootstrap | `scripts/gh_projects_sync.py` preflight; SKILL.md:87; bootstrap-and-credentials.md:56; never-do-patterns.md:54; `.claude/settings.json` | M |
| 2 | F2 npm code with write token | 1/3 HIGH | split archive step; mint token late; `--ignore-scripts`; branch protection note | `assets/workflows/openspec-archive.yml`; `blueprints/workflows.md` | S |
| 3 | F3 CLAUDE.md stale | 3/3 MED | add packages/command/agent; fix OpenSpec package; counts 41/226/67/50/32 | `CLAUDE.md` | S |
| 4 | F5 archive before pull | 2/3 MED | require E9 approval line in status.md | `openspec-archive.yml` | S |
| 5 | F7 anchors from working tree | 2/3 MED | refuse `pull` on dirty/divergent tracker file; print anchors | `gh_projects_sync.py` cmd_pull | S |
| 6 | F4 command canonical call | 2/3 MED | default root, `--profile` in hint, define direct-use apply | `syncing-openspec-to-github/SKILL.md`, agent, scenarios | S |
| 7 | F6 gate noise | 1/3 MED | label filter in `if:`; silent ignore for non-approvers | `openspec-gate.yml:32`; `_model.py` evaluate order; `gate_command.py` | S |
| 8 | F8, F9, F11, F10, F12, F13 | 2/3-1/3 LOW | wire or reword agent; amend naming rule; narrow globs; issue_url check; verification line | various | S |

## 7. Model Effectiveness Analysis
| Model | Unique | False positives | Most actionable |
|---|---|---|---|
| A | F10, F13 | none | F3 |
| B | none (all corroborated) | none | F5 |
| C | F2, F6, F12 | none expected; F2 assumes an unlocked npm tree (true: no lockfile in the template) | F2 |
Re-audit recommended: yes, Model C, plus a targeted B check of F1/F4 after fixes.

## 8. Conclusion
The packaging and layering are healthy: clean DAG, generic github-core and openspec-core, valid frontmatter, correct fork routing,
a non-nesting agent, a fail-closed `trusted_author`, an exact-login bot anchor and env-only event text. The consensus findings show
one systemic gap: technical controls stop at the GitHub side, while the local side relies on prompts (F1, F7) and the hand-authored
CLAUDE.md lags the generated tree (F3). Also, the archive template (F2) breaks least privilege with a write token near unlocked npm code.
Expected scores after fixing F1-F7: A 8.8, B 8.5, C 8.5, i.e. PASS.
