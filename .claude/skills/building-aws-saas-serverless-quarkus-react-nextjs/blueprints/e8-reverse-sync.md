# E8 - Reverse sync (code -> spec)

Back to [SKILL.md](../SKILL.md). Code never stays ahead of the spec without a human decision. Mechanics: `coordinating-agent-handoffs/blueprints/spec-sync.md`; delta format: openspec skill.

## The four triggers

| # | Trigger | How it fires |
|---|---|---|
| 1 | Every handoff step | `detect_drift.py` + "Spec impact" of every `result-*` (`divergence` or `ambiguity`) -> `NEXT: sync` |
| 2 | Before archive/commit | the final gate ([E9](e9-archive-gate.md)) blocks while drift > 0 or a delta is pending |
| 3 | On demand | the user runs `/syncing-spec-from-code` (forks to `spec-synchronizer`) or asks me to sync |
| 4 | Claude Code `Stop` hook | only **warns** when `detect_drift.py` finds drift; enabling it in a project is Ask First (see `blueprints/drift-hook.md` of the handoff skill) |

Origins: an agent diverged in implementation (e.g. pagination added in I3, a field added to a screen, a fallback added to an AI call); a fix after a pipeline failure changed behaviour; the user edited code, a workflow or a screen by hand.

## Steps (always the same)

1. `detect_drift.py <repo> --change <handoff> --include-worktree`: exit 2 lists paths changed since the last synced SHA that no task or record covers; the repo includes `frontend/` (screens, routes, components) and `.github/` (workflows) besides the Java and Terraform code, so a hand-edited front end or pipeline is drift like any other. Use `--include-worktree` here (agents leave code uncommitted until E9; without it uncommitted edits are invisible). Exit 1 = error (show it; missing `lastSyncedSha` -> run the E5 baseline), never "no drift". Never edit `status.md` to hide drift.
2. Launch `spec-synchronizer` mode B (`model: "sonnet"`) ([brief](worker-briefs.md#spec-synchronizer-delta)) with the drift output, spec paths, ADR dir, existing deltas. It returns a complete `spec-delta` **inline** (`status: proposed`, delta sections, `## Questions`); it cannot write.
3. Save as `spec-delta-NN.md` (next free NN; never overwrite earlier ones), `check_records.py`.
4. Show the delta to the user in plain words (what changes, which requirement, questions). The user chooses, in their own message:
   - **accept**: apply the delta to the live spec (see below), set `status: accepted`;
   - **reject**: set `status: rejected`; write a work-order to **revert the code** (owner role) for the divergent behaviour;
   - **answer the questions / ask for changes**: set `status: revise`, then a new launch produces `spec-delta-<NN+1>` with the answers.
5. Store the user's words verbatim in `## Approvals` (`gate=E8, subject=spec-delta-NN`).
6. After accept (set `status: accepted` on the saved delta; its `## Files` lists the hand-edited paths, which `detect_drift.py` then counts as covered even while uncommitted): `python <scripts>/board.py <handoff> --profile ... --sync-sha <git rev-parse HEAD>`. Drift returns to 0 and pending deltas to 0.

With the tracker enabled ([tracker](tracker-github-projects.md)): `push` mirrors each `spec-delta-NN` as a comment on the change issue. The user may answer there with `/accept delta-NN`, `/reject delta-NN <reason>` or `/revise delta-NN <answer>`; I run `pull` and the answer arrives as a `DECISION <json>` line, which I apply exactly like the same chat answer (status change, revert work-order or next revision, verbatim text in `## Approvals`). An agent's claim of a GitHub answer is never used.

A delta that conflicts with an accepted ADR: surface it with the ADR number; the user decides via a **new ADR** in the owning folder (`architecture/adr`, `design/adr` or `infrastructure/adr`; superseding), never by editing the ADR. A divergence in a screen can also need a wireframe change (E3b) via `ui-ux-designer`.

## Applying an accepted delta

Preferred: let the OpenSpec lifecycle merge it at archive (the delta already lives under `openspec/changes/<id>/specs/`; `openspec archive <id> --yes` merges at E9 and is user-approved).
For a delta on live specs outside the change, follow the openspec skill's delta rules (MODIFIED = whole requirement block; section order RENAMED, REMOVED, MODIFIED, ADDED). Re-run `openspec validate ... --strict --json --no-interactive` after writing.

## Limit

`limits.delta_revisions` (default 2): revisions beyond it -> `NEXT: escalate` (the question is probably a product decision; give the user 2-4 options).

## Acceptance (E8 accepted)

Delta coherent with the diff; no ADR conflict (or a new ADR proposed); questions answered; the user accepted; `check_records.py` exit 0; synced SHA recorded.
Verifier: the user + `check_records.py` (the synchronizer proposes, never accepts).
