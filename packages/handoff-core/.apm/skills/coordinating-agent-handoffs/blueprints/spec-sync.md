# Spec Sync: drift, spec-delta, gate

Back to [SKILL.md](../SKILL.md). Applies when the profile has `spec.kind: openspec`. With
`spec.kind: none` there is no spec side: reports still carry "Spec impact", but no spec-delta is
written and the gate checks only records, limits and escalations. OpenSpec file formats (delta
sections, archive order) are defined by the skill
[specifying-changes-with-openspec-v1-15](../../specifying-changes-with-openspec-v1-15/SKILL.md);
this protocol does not restate them.

## Where code diverges from the spec

| Origin | Detected by |
|---|---|
| An agent diverges while implementing | `spec_impact: divergence\|ambiguity` + "Spec impact" section of its report (every handoff step) |
| A fix by the debugger changes behaviour | its diagnosis-report `spec_impact` + `detect_drift.py` |
| The user edits code by hand | `detect_drift.py` (on demand, a Stop hook that only warns, and the final gate) |

## Drift, defined

- **Record drift (board):** a report/diagnosis-report with `spec_impact` `divergence` or `ambiguity` and no
  `spec-delta` whose `refs` lists it. `board.py` computes it. Any spec-delta that `refs` the
  divergent record covers that record, whatever its status: a rejected delta closes it too, because the
  revert work-order handles the code.
- **Code drift:** files changed in `git diff --name-only <lastSyncedSha>..HEAD` that no report
  mentions in its "Spec impact" / "Files" / "Files changed" / "What changed" sections.
  `detect_drift.py` computes it (exit 2). Files under `openspec/` and under the handoff folder are
  never drift. Paths are matched exactly: a report must name each changed file (backticked path or
  whole token); naming a directory or a longer path that merely contains it does not cover it.
  Among `spec-delta` records only the `## Files` of an **accepted** delta covers paths; proposed,
  revise and rejected deltas cover nothing. (Two notions: `detect_drift.py` covers file paths only
  through accepted deltas; the board covers a record through any delta that `refs` it.)
  The board receives the result as `--args drift=true`.
- **Committed changes only, by default.** `detect_drift.py` compares `<lastSyncedSha>..HEAD`, so a
  hand edit that is still uncommitted (or untracked) is invisible. Run it with
  `--include-worktree` when the user may have edited files directly and not committed yet: before
  the final gate, before archiving, and after any session in which the user worked on the code.
  A `--change` folder on another drive than the repo (Windows) is reported as an error (exit 1).

## Flow (always the same)

1. `detect_drift.py <repo> --change <handoff-dir>` lists drifted paths.
2. The sync agent reads that diff, the specs, ADRs and reports and writes a `spec-delta`
   (OpenSpec delta sections + `## Files` listing the drifted paths it covers + `## Questions`). A
   MODIFIED requirement is repeated in full. `## Files` is recommended, not enforced by
   `check_records.py`; a delta without it covers no path. `detect_drift.py` treats the `## Files` of an
   **accepted** spec-delta as coverage (proposed, revise and rejected deltas cover nothing), so an
   uncommitted hand edit stops being drift once its delta is accepted.
3. The orchestrator shows the delta. The user **accepts** (spec updated, `status: accepted`),
   **rejects** (`rejected`; a work-order reverts the code) or **answers the questions**
   (`revise`; a new `spec-delta-<nn>` follows; counted by `delta_revisions`).
4. `board.py <dir> --profile ... --sync-sha <HEAD sha>` stores the new synced SHA; drift returns to 0.

The sync agent writes only deltas; it never edits code and never edits the live spec. Only the
orchestrator applies an accepted delta.

## Final gate (archive / commit)

All must hold: every stage has a `verify` record with `outcome: pass` whose verifier is not the
author; `check_records.py` exits 0; `detect_drift.py` exits 0 and the board shows `drift: false`;
`pending deltas: 0`; no open escalation; no blocking question; approvals recorded in
`status.md`. The board emits `NEXT: final-gate` only when the profile's rule for it matches; the
orchestrator still re-runs the scripts instead of trusting the last output.
