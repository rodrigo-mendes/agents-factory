# OpenSpec integration

Back to [SKILL.md](../SKILL.md). OpenSpec formats (requirements, scenarios, delta sections, archive
order) are defined by `specifying-changes-with-openspec-v1-15`; this page only says where this
profile puts its own files. Items marked (unverified) are not confirmed by the OpenSpec docs.

## Where each file lives (target project)

| File | Path | Written by |
|---|---|---|
| Functional spec (live) | `openspec/specs/<capability>/spec.md` | applied from accepted deltas only (archive, or orchestrator) |
| Architecture spec (live) | `openspec/specs/architecture/spec.md` | orchestrator via change deltas; reviewed by `aws-architect` |
| ADRs | `openspec/specs/architecture/adr/<NNN>-<title>.md` ([template](../assets/adr.template.md)) | orchestrator (E2); never edited once accepted |
| Change proposal, design, tasks | `openspec/changes/<id>/proposal.md`, `design.md`, `tasks.md` | orchestrator |
| Change deltas | `openspec/changes/<id>/specs/<capability>/spec.md` | orchestrator, from accepted `spec-delta` records |
| Handoff records | `openspec/changes/<id>/handoff/*.md` | agents and orchestrator |
| Generated board | `openspec/changes/<id>/handoff/status.md` | `board.py` |
| Project overrides | `openspec/handoff-profile.yaml` (`limits:` / `quality:` only) | the user, via the orchestrator |

The profile's `spec.functional`, `spec.architecture` and `spec.adr_dir` mirror this table.

## Records and the spec: one direction per record

- `spec-delta-NN.md` is a **proposal** (frontmatter `status: proposed`); its body uses the OpenSpec
  delta sections plus `## Questions`. Accepting it means the orchestrator copies the sections into
  `openspec/changes/<id>/specs/<capability>/spec.md` and sets the record `accepted`.
- A delta that touches the architecture spec also carries a new ADR (the user decides through the ADR).
- The sync agent never writes under `openspec/`; the orchestrator is the only writer of the spec.

## Archive

`openspec archive <id> --yes` moves the change folder to the archive folder named `YYYY-MM-DD-<id>`
(see the OpenSpec skill) and merges the deltas into the live specs. The `handoff/` folder is inside the change folder, so it
travels with it. Whether the CLI moves or validates a non-standard subfolder such as `handoff/` is
(unverified); run `openspec validate <id> --type change --strict --json --no-interactive` before the
archive and inspect the archived folder after the first real archive. The orchestrator archives
only after the final gate and with the user's approval (Ask-First C3 of the OpenSpec skill: archive
only is the agent default).

## The final gate (E9)

All must hold, re-run by the orchestrator (not trusted from earlier output):

1. `check_records.py` exit 0.
2. `detect_drift.py` exit 0 and `board.py` shows `drift: false`, `pending spec-deltas: 0`.
3. A `verify` record with `outcome: pass` for each stage E1-E4 and E7 (`verify-E7.md` by `aws-lambda-debugger` mode B, role `debug`) whose verifier differs from the authors.
4. No open `escalation`; no blocking question; every `## Approvals` entry in `status.md` is the user's own words.
5. `board.py` prints `NEXT: final-gate`.

Then: ask the user to approve commit and archive; commit (never push) only with that approval.

## Drift sync after a manual edit

`detect_drift.py` lists changed code paths that no report covers -> `spec-synchronizer` (mode B)
writes `spec-delta-NN` -> user accepts, rejects or answers -> `board.py --sync-sha <HEAD>` stores
the new SHA. The optional `Stop` hook only warns and needs the user's confirmation (see
[unverified and risks](./unverified-and-risks.md), U1).
