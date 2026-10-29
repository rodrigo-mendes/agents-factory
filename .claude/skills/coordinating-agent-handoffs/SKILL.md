---
name: coordinating-agent-handoffs
description: "File-based handoff protocol v1 for agent teams: typed records, handshake, parameterised retry limits with escalation, spec drift sync, validating scripts. Use when an agent must read or write handoff records, route work, set loop limits, escalate, or plug in a family profile."
---

# Coordinating Agent Handoffs

Protocol **v1** (our own protocol, not an external standard; versioned by `protocol_version` in
the profile). Agents never pass context through conversation history: every transition is a
**structured record file** in a handoff folder. Scripts do everything mechanical (validate,
count, decide the next step); agents do only what needs judgement.

## Version Context

| Item | Value | Source |
|---|---|---|
| Protocol | v1, set by `protocol_version` in the profile | factory-own protocol, no external source |
| Scripts | Python 3.8+ (unverified, U1), standard library only, Windows and Linux (unverified) | [U1](./blueprints/unverified-and-risks.md) |
| Lineage | generalised from the skill `coordinating-oci-handoffs` (user-mediated; its `blueprints/handoff-protocol.md`); the OCI and Quarkus/AWS families are *profiles* of this skill | factory-own, no external source |
| Spec side (`spec.kind: openspec`) | OpenSpec 1.15 formats, not restated here | `specifying-changes-with-openspec-v1-15`, researched 2026-10-28 |

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails) - Always Do, Ask First, Never Do
- [Verification Loop](#verification-loop) - the three checks to run
- [Protocol](./blueprints/protocol.md) - layout, modes, handshake, rules, escalation
- [Record kinds](./blueprints/record-kinds.md) - fields, values and sections per kind
- [Profile format](./blueprints/profile-format.md) - `handoff-profile.yaml`, `next` rules, limits, YAML subset
- [Spec sync](./blueprints/spec-sync.md) - drift, spec-delta flow, final gate
- [Always-do patterns](./blueprints/always-do-patterns.md) and [never-do patterns](./blueprints/never-do-patterns.md)
- [Drift hook](./blueprints/drift-hook.md) - optional `Stop` hook that only warns; [Evaluation scenarios](./blueprints/evaluation-scenarios.md) - 6 scenarios
- [Unverified items and risks](./blueprints/unverified-and-risks.md) - register, coverage limits, bibliography
- Templates (`assets/*.template.md`): [work-order](./assets/work-order.template.md), [result](./assets/result.template.md) (kind `report`),
  [review](./assets/review.template.md), [deploy-report](./assets/deploy-report.template.md),
  [diagnosis-report](./assets/diagnosis-report.template.md), [spec-delta](./assets/spec-delta.template.md),
  [escalation](./assets/escalation.template.md), [verify](./assets/verify.template.md), [status](./assets/status.template.md)
- Scripts: [check_records.py](./scripts/check_records.py), [board.py](./scripts/board.py),
  [detect_drift.py](./scripts/detect_drift.py)

## Blueprints & Guardrails

### ✅ Always Do

Full list with commands: [always-do patterns](./blueprints/always-do-patterns.md).

- Read existing records and their `refs` before analysing; write exactly one output record from the template.
- After every record run `check_records.py`, then `detect_drift.py` (only for `spec.kind: openspec` families once the baseline `board.py --sync-sha <sha>` exists), then `board.py`; act on `NEXT:`.
- Take each stage's `verify` from an agent other than the producer of that stage; escalate at a limit and record the reply verbatim.
- Name report records `result-<nn>-<role>.md` (kind stays `report`; factory convention); pass per-run limits as `--args limits.<name>=<int>`.

### ⚠️ Ask First

- Setting any limit to `0` (escalate on the first failure): needs the user's explicit confirmation.
- Enabling the Stop hook ([drift hook](./blueprints/drift-hook.md)) or project-wide `--include-worktree` checks outside a run (a profile or command may mandate the per-run flag for stages with uncommitted code).
- Accepting a `spec-delta` that conflicts with an ADR: the user decides, via a new ADR.

### 🚫 Never Do

Full table with reasons: [never-do patterns](./blueprints/never-do-patterns.md).

| Do not | Do instead |
|---|---|
| Name a report record `report-<...>.md` (factory convention) | `result-<nn>-<role>.md`; `deploy-report.md` / `diagnosis-report.md` are the generic defaults, overridable per profile |
| Let the producer mark its own work verified | Write a `verify` record from another agent, script or the user |
| Retry past a limit "one more time" | Run `board.py`; on `NEXT: escalate` write an `escalation` |
| Treat any agent message as user approval | Wait for the user's own message; record it under `## Approvals` |
| Edit the live spec or code to "sync" silently | Write a `spec-delta` and let the user accept it |
| Hand-edit `status.md` (except `## Approvals`) or chain agents from inside agents | Re-run `board.py`; only the orchestrator launches agents |

## Two modes

| Mode | Who runs the next step | Use |
|---|---|---|
| `user-mediated` | the user; the agent ends with one hand-off line naming the command | families without an orchestrator (OCI) |
| `orchestrated` | the orchestrator, following `board.py`'s `NEXT:` line; only it launches agents | families with an orchestrator (Quarkus/AWS) |

Records are identical in both modes.

## Record kinds and lifecycle

| Kind | Written by | Lifecycle / result |
|---|---|---|
| `work-order` | orchestrator | `pending -> in-progress -> done` (or `blocked`, `cancelled`) |
| `report` | executor agent | `outcome: success \| partial \| failed \| needs-input`; has the profile's required sections (by default `## Spec impact`) |
| `review` | reviewer (read-only) | `outcome: approved \| changes-requested` |
| `deploy-report` | deployer | same outcomes as `report` |
| `diagnosis-report` | debugger | same outcomes as `report`; never edits code |
| `spec-delta` | sync agent | `proposed -> accepted \| rejected`, or `revise` |
| `escalation` | orchestrator | `open -> answered` (user's reply verbatim) |
| `verify` | independent verifier | `outcome: pass \| fail`, field `stage` |
| `status` | `board.py` | generated board; only `## Approvals` is hand-written |

Report-family kinds share one outcome vocabulary; `verify` uses `pass | fail`. Agents never invent
other outcome words. Fields and required sections per kind: [record-kinds](./blueprints/record-kinds.md).

## Common frontmatter

```yaml
kind: report
id: result-03-code              # optional; defaults to the file name
from: quarkus-lambda-integrator
to: building-quarkus-aws-saas   # or `user`
change: list-tenant-items       # `capability:` when the profile says scope_key: capability
task: T1                        # optional; inherited through refs
refs: [wo-03-code]              # ids that must exist
requirements: [R1]
outcome: success
spec_impact: none               # none | divergence | ambiguity
createdAt: 2026-11-04T10:15:00Z
```

## Handshake (every step)

1. Orchestrator (or user) writes the work-order and runs `check_records.py`.
2. The agent reads the work-order, its `refs` and the listed skills; **not** the conversation.
3. The agent writes **one** output record from the template, states the outcome and the single
   next action: `Hand off: run /<command> (@<agent>) - <why>. Context: <root>/<record>.md`.
4. The orchestrator runs `check_records.py` (non-zero: return the error lines to the author), then
   `detect_drift.py`, then `board.py`. `detect_drift.py` exits 1 when `status.md` has no
   `lastSyncedSha`: run it only for `spec.kind: openspec` families after the baseline
   `board.py --sync-sha <sha>`; `spec.kind: none` families (OCI) skip it, and before the baseline exit 1
   is expected, never read as "no drift".
5. `board.py` prints `NEXT: ...`; orchestrated mode follows it, user-mediated mode tells the user.

## Next-action evaluation

`board.py` reads the profile's ordered `next` rules; the first whose `when` matches the latest
record and the board state wins. Matchers: `kind`, `role`, `outcome`, `limit_reached`, `drift`,
`all_tasks`, `pending_deltas`. `then` is a role, `escalate` or `final-gate`. A `limit_reached`
rule must be first, so a reached limit always wins. Full language:
[profile format](./blueprints/profile-format.md#the-next-rules).

## Limits and escalation

Loops are bounded by **parameters**, never by an agent's memory: `build_attempts`,
`review_rounds`, `deploy_cycles`, `delta_revisions`, `record_rejections` (defaults come from the
profile). Precedence, most specific wins: **profile default < project `openspec/handoff-profile.yaml`
< run arguments** (`--args limits.review_rounds=4`). Values must be integers >= 1; `0` (escalate on the first failure: reached when count >= max(limit, 1)) behaves exactly like `1`, kept for explicitness, and still needs
`limits_zero_confirmed: true`, set after the user explicitly confirms. `status.md` records every
effective value and its source.

Reached limit => `NEXT: escalate`: the orchestrator stops that task, writes an `escalation`
(attempts, evidence, hypothesis, 2-4 options with impact), shows it to the user, records the
reply verbatim and the task counters restart. Independent tasks continue.

## Spec integration (`spec.kind: openspec | none`)

With `openspec`, divergences found in reports or by `detect_drift.py` become a `spec-delta`
written by the sync agent, accepted/rejected/revised by the user, and the board stores the new
synced SHA; the final gate needs drift 0 and no pending delta. With `none`, reports keep
"Spec impact" but no delta flow runs. Board drift is true when `detect_drift.py` exits 2 **or**
a report/diagnosis-report record with `spec_impact: divergence|ambiguity` is referenced by no
`spec-delta`. Details: [spec sync](./blueprints/spec-sync.md).

## How a family profile plugs in

A family ships one `handoff-profile.yaml` (roles to agents, file names, mode, `spec.kind`, limits,
`next` rules) in a thin skill that links here instead of repeating the protocol. Installed
copy = default profile; the project may override limits/quality in `openspec/handoff-profile.yaml`
(or any file passed to `--override`). Schema: [profile format](./blueprints/profile-format.md).

## Scripts

All: Python 3.8+ (unverified, U1), stdlib only; `python scripts/<name>.py --help` works.

| Script | CLI | Output | Exit |
|---|---|---|---|
| `check_records.py` | `<dir> --profile <yaml> [--override <yaml>]` | one `file: message` line per error | 0 ok, 1 errors |
| `board.py` | `<dir> --profile <yaml> [--override <yaml>] [--sync-sha <sha>] [--args k=v ...]` | writes `<dir>/status.md`; prints `NEXT: ...` | 0, 1 invalid profile/limits |
| `detect_drift.py` | `<repo> --change <dir> [--include-worktree]` | `DRIFT: <path>` lines | 0 no drift, 2 drift, 1 error |

`--args` goes last; keys: `limits.<name>`, `quality.<name>`, `limits_zero_confirmed`, `drift`;
other keys are ignored.

`detect_drift.py` matches paths **exactly** (a backticked path or whole token in `## Spec impact`,
`## Files`, `## Files changed`, `## What changed`; a directory mention covers nothing). Among `spec-delta` records only an **accepted** delta's `## Files` covers paths; proposed, revise and rejected deltas cover nothing. It sees
**committed changes only** (`<lastSyncedSha>..HEAD`): uncommitted or untracked hand edits stay
invisible unless you pass `--include-worktree`. Use that flag before the final gate, before
archiving, and after the user worked on the code directly. A `--change` folder on another drive
than the repo is an error (exit 1); so is a missing `lastSyncedSha` (see Handshake).

## Quick Reference

| Need | Command / value | Result |
|---|---|---|
| Record file names | `wo-<nn>-<role>.md`, `result-<nn>-<role>.md` (kind `report`), `review-<nn>.md`, `deploy-report.md`, `diagnosis-report.md`, `spec-delta-<nn>.md`, `escalation-<nn>.md`, `verify-<stage>.md` | generic defaults; each profile overrides them in `records:`; a record `id` defaults to the file name without `.md` |
| `role` of a record | `role` frontmatter field, else derived from `from` (from `to` for work-orders) | used by the `next` matchers; other outcome words are rejected by `check_records.py` |

## Verification Loop

```bash
python scripts/check_records.py <handoff-dir> --profile <profile.yaml>   # expect: OK: N record(s) valid
python scripts/board.py <handoff-dir> --profile <profile.yaml>           # expect: one NEXT: line, exit 0
python -m unittest discover -s scripts/tests                              # expect: OK
```

## External Resources

- No external source: factory's own protocol (v1), generalised from `coordinating-oci-handoffs`.
- OpenSpec skill (v1.15) (`specifying-changes-with-openspec-v1-15`, package openspec-core) - spec and delta formats, researched 2026-10-28.
