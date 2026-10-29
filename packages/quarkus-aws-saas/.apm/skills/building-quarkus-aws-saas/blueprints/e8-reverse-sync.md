# E8 - Reverse sync (code -> spec)

Back to [SKILL.md](../SKILL.md). Code never stays ahead of the spec without a human decision. Mechanics: `coordinating-agent-handoffs/blueprints/spec-sync.md`; delta format: openspec skill.

## The four triggers

| # | Trigger | How it fires |
|---|---|---|
| 1 | Every handoff step | `detect_drift.py` + "Spec impact" of every `result-*` (`divergence` or `ambiguity`) -> `NEXT: sync` |
| 2 | Before archive/commit | the final gate ([E9](e9-archive-gate.md)) blocks while drift > 0 or a delta is pending |
| 3 | On demand | the user runs `/syncing-spec-from-code` (forks to `spec-synchronizer`) or asks me to sync |
| 4 | Claude Code `Stop` hook | only **warns** when `detect_drift.py` finds drift; enabling it in a project is Ask First (see `blueprints/drift-hook.md` of the handoff skill) |

Origins: an agent diverged in implementation (e.g. pagination added in I3); the debugger's fix changed behaviour; the user edited code by hand.

## Steps (always the same)

1. `detect_drift.py <repo> --change <handoff> --include-worktree`: exit 2 lists paths changed since the last synced SHA that no task or record covers. Use `--include-worktree` here (agents leave code uncommitted until E9; without it uncommitted edits are invisible). Exit 1 = error (show it; missing `lastSyncedSha` -> run the E5 baseline), never "no drift". Never edit `status.md` to hide drift.
2. Launch `spec-synchronizer` mode B ([brief](worker-briefs.md#spec-synchronizer-delta)) with the drift output, spec paths, ADR dir, existing deltas. It returns a complete `spec-delta` **inline** (`status: proposed`, delta sections, `## Questions`); it cannot write.
3. Save as `spec-delta-NN.md` (next free NN; never overwrite earlier ones), `check_records.py`.
4. Show the delta to the user in plain words (what changes, which requirement, questions). The user chooses, in their own message:
   - **accept**: apply the delta to the live spec (see below), set `status: accepted`;
   - **reject**: set `status: rejected`; write a work-order to **revert the code** (owner role) for the divergent behaviour;
   - **answer the questions / ask for changes**: set `status: revise`, then a new launch produces `spec-delta-<NN+1>` with the answers.
5. Store the user's words verbatim in `## Approvals` (`gate=E8, subject=spec-delta-NN`).
6. After accept (set `status: accepted` on the saved delta; its `## Files` lists the hand-edited paths, which `detect_drift.py` then counts as covered even while uncommitted): `python <scripts>/board.py <handoff> --profile ... --sync-sha <git rev-parse HEAD>`. Drift returns to 0 and pending deltas to 0.

A delta that conflicts with an accepted ADR: surface it with the ADR number; the user decides via a **new ADR** in E2 (superseding), never by editing the ADR.

## Applying an accepted delta

Preferred: let the OpenSpec lifecycle merge it at archive (the delta already lives under `openspec/changes/<id>/specs/`; `openspec archive <id> --yes` merges at E9 and is user-approved).
For a delta on live specs outside the change, follow the openspec skill's delta rules (MODIFIED = whole requirement block; section order RENAMED, REMOVED, MODIFIED, ADDED). Re-run `openspec validate ... --strict --json --no-interactive` after writing.

## Limit

`limits.delta_revisions` (default 2): revisions beyond it -> `NEXT: escalate` (the question is probably a product decision; give the user 2-4 options).

## Acceptance (E8 accepted)

Delta coherent with the diff; no ADR conflict (or a new ADR proposed); questions answered; the user accepted; `check_records.py` exit 0; synced SHA recorded.
Verifier: the user + `check_records.py` (the synchronizer proposes, never accepts).
