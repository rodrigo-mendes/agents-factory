---
name: syncing-spec-from-code
description: "Detects drift between code and the OpenSpec spec of a change and proposes a spec-delta plus open questions, without editing code or spec. Use when code was changed by hand or diverged from the spec and the spec must be brought back in sync, or before the final gate of a handoff run."
argument-hint: "<change-id or handoff dir> [--repo <path>] [--profile <yaml>]"
context: fork
agent: spec-synchronizer
disable-model-invocation: true
---

# Syncing Spec From Code

Routes to the `spec-synchronizer` agent, which proposes a **spec-delta** (OpenSpec delta format
plus `## Questions`) for code that drifted from the spec. Nothing is written to the spec or the
code: the delta comes back inline, the orchestrator saves it as `spec-delta-NN.md`, and the user
accepts, rejects or answers. This command always runs the agent's **Mode B (sync)**; Mode A (spec
review before approval) is the orchestrator's direct use of the agent, not this command.
The orchestrator never invokes this command for a family whose profile has `spec.kind: none`.

## Quick Navigation

- [How to invoke](#how-to-invoke)
- [Agent workflow](#agent-workflow)
- [Output](#output)
- [Blueprints & Guardrails](#blueprints--guardrails)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)

## Blueprints & Guardrails

Drift detection and the spec-sync procedure live in `coordinating-agent-handoffs` (blueprint
`spec-sync`); the delta format lives in `specifying-changes-with-openspec-v1-15`. Scenarios:
[blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).

Stage ids (E1-E9) in this skill are the stage ids of the Quarkus/AWS flow. `detect_drift.py` exit 1 means an error. If the message says `lastSyncedSha` is missing, return it
with the hint: the orchestrator runs the baseline `board.py --sync-sha <sha>` (stage E5 of the
Quarkus/AWS orchestrator's flow), then re-runs this command.

`--include-worktree` is mandatory per run for the stages where code is uncommitted (E6-E9 in the
Quarkus/AWS flow). The generic protocol's Ask-First item covers only the Stop hook and project-wide
checks outside a run.

### ✅ Always Do

- Run `detect_drift.py` and scan the records for uncovered `spec_impact` records before proposing
  anything; an empty drift list **and** no uncovered record means no delta.
- Keep every proposed requirement testable: `SHALL`/`MUST` and `#### Scenario:` with the bold
  WHEN/THEN of the schema and templates, as `specifying-changes-with-openspec-v1-15` defines the
  delta format (parser enforcement of bold is (unverified): register I1 of that skill).

### ⚠️ Ask First

- A delta that contradicts an accepted ADR: propose it, name the ADR in `## Questions`, and let the
  user decide whether a new ADR is needed.
- A handoff dir without `status.md`: return a question to the orchestrator (the right dir, or create it).
- Running outside a git repository (`detect_drift.py` needs git history): return a question asking for `--repo`.

### 🚫 Never Do

| Do not | Do instead |
|---|---|
| Edit code or the live spec, or mark the delta accepted | Return `status: proposed`; the user decides |
| Run this command when the profile has `spec.kind: none` (checked when `--profile` is given) | Say there is no spec side and stop |
| Stop at "no drift" because `detect_drift.py` exited 0 without scanning the records | Scan for uncovered `divergence` / `ambiguity` records; they still need a delta that `refs` them |

## How to invoke

```
/syncing-spec-from-code <change-id | handoff dir> [--repo <path>] [--profile <yaml>]
```

- `<change-id>` resolves to `openspec/changes/<change-id>/handoff` inside `--repo`; with `--profile`,
  the profile's `root` template resolves the id instead (for example `docs/handoff/{capability}`).
- A path containing a `status.md` is used as the handoff dir. A relative path is resolved against
  `--repo`: the agent joins it with `--repo` before calling `detect_drift.py`, which itself resolves
  `--change` against the current working directory.
- `--repo` defaults to the current working directory.
- `--profile` (optional) is the family's `handoff-profile.yaml`. When given, the agent reads its
  `spec.kind`; `none` means there is no spec side: say so and stop. When omitted, the agent cannot
  know `spec.kind` and relies on the orchestrator not routing `none` families here.

Examples:

- `/syncing-spec-from-code list-tenant-items`
- `/syncing-spec-from-code openspec/changes/list-tenant-items/handoff --repo ../saas-app`: the agent
  runs `detect_drift.py ../saas-app --change ../saas-app/openspec/changes/list-tenant-items/handoff`.

## Agent workflow

1. **P0 - Verify docs**: read `coordinating-agent-handoffs` (spec sync blueprint) and
   `specifying-changes-with-openspec-v1-15`; stop if unreadable.
2. **P1 - Detect** (two scans; board drift is either of them):
   - **Code drift**: run `python <coordinating-agent-handoffs>/scripts/detect_drift.py <repo> --change <repo>/<handoff dir>` (the `--change` path joined with `--repo`).
     Add `--include-worktree` while the task code is still uncommitted (stages E6-E9 of the
     Quarkus/AWS orchestrator's flow, per run) or when the work-order says so; otherwise
     omit it and state that choice in the output. A committed-only comparison cannot see
     uncommitted edits and would report "no drift". Exit 1: return the error line. Exit 0: no code
     drift. Exit 2: the `DRIFT: <path>` lines.
   - **Record drift**: list the `report` and `diagnosis-report` records of the handoff dir whose
     `spec_impact` is `divergence` or `ambiguity` (Grep `spec_impact:`) and keep those that no
     `spec-delta` lists in `refs`. These are the *uncovered records*.
   - Both empty (exit 0 and no uncovered record): report "no drift" and stop. Otherwise continue,
     also when exit is 0 but uncovered records exist: the board counts them as drift, so
     stopping would leave the run asking for a sync again.
3. **P2 - Analyse**: read the diff since `lastSyncedSha`, the spec, ADRs, reports (the uncovered
   records first) and earlier deltas.
4. **P3 - Propose**: write the delta (sections in archive order: RENAMED, REMOVED with Reason and
   Migration, MODIFIED with the whole requirement block, ADDED) and `## Questions`; put the id of every uncovered record
   the delta resolves in its `refs`; state `delta_revisions: <n>`.
5. **P4 - Return**: output the full `spec-delta-<nn>` record inline with `status: proposed`.

## Output

- One `spec-delta` record body (frontmatter + delta sections + `## Files` + `## Questions`), inline.
  `## Files` is recommended, not enforced by `check_records.py`; a delta without it covers no path.
- Final line: `Hand off: orchestrator - save spec-delta-<nn>.md and show it to the user. Context: <handoff dir>`.

Standalone use (no orchestrator): the delta is only printed. Save it yourself as
`spec-delta-<nn>.md` in the handoff dir, or re-run through the orchestrator so it is saved and shown.

## Evaluation Scenarios

See [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
