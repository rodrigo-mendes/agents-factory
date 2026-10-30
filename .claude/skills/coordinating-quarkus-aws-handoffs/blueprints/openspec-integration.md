# OpenSpec integration

Back to [SKILL.md](../SKILL.md). OpenSpec formats (requirements, scenarios, delta sections, archive
order) are defined by `specifying-changes-with-openspec-v1-15`; this page only says where this
profile puts its own files. Items marked (unverified) are not confirmed by the OpenSpec docs.

## Where each file lives (target project)

| File | Path | Written by |
|---|---|---|
| Functional spec (live) | `openspec/specs/<capability>/spec.md` | applied from accepted deltas only (archive, or orchestrator) |
| Architecture spec (live) and contracts | `openspec/specs/architecture/spec.md`, `architecture/contracts/*.md` | `solution-architect` (E2a); reviewed by `solution-architecture-reviewer` |
| Design system, wireframes, navigation | `openspec/specs/design/design-system.md`, `design/wireframes/*.md`, `design/navigation.md` | `ui-ux-designer` (E2b, E3b); reviewed by `ui-design-reviewer` |
| Infrastructure spec | `openspec/specs/infrastructure/spec.md` | `aws-infrastructure-architect` (E2c); reviewed by `aws-architect-reviewer` |
| ADRs, three folders, numbering per folder | `openspec/specs/architecture/adr/`, `design/adr/`, `infrastructure/adr/` as `<NNN>-<title>.md` ([template](../assets/adr.template.md), field `area:`) | the author of each area (E2); never edited once accepted; cite as `design/adr/002` |
| Change proposal, tasks | `openspec/changes/<id>/proposal.md`, `tasks.md` | orchestrator |
| Change designs | `openspec/changes/<id>/design.md` (index + traceability) and `design/<flow>.md` (one per flow) | `solution-architect` (E4) |
| Change infra design | `openspec/changes/<id>/infra-design.md` | `aws-infrastructure-architect` (E4) |
| Change deltas | `openspec/changes/<id>/specs/<capability>/spec.md` | orchestrator, from accepted `spec-delta` records |
| Handoff records | `openspec/changes/<id>/handoff/*.md` | agents and orchestrator |
| Generated board | `openspec/changes/<id>/handoff/status.md` | `board.py` |
| Project overrides | `openspec/handoff-profile.yaml` (`limits:` / `quality:` only) | the user, via the orchestrator |

The profile's `spec.functional`, `spec.architecture` and `spec.adr_dir` mirror this table; `adr_dir` points only to `architecture/adr` and is informational (the scripts do not read it),
so every work-order lists the three ADR folders explicitly. The folder layout beyond the official OpenSpec files (`architecture/`, `design/`, `infrastructure/`, `design/<flow>.md`, `infra-design.md`, `handoff/`) is a factory convention; see U2, U3.

## Records and the spec: one direction per record

- `spec-delta-NN.md` is a **proposal** (frontmatter `status: proposed`); its body uses the OpenSpec
  delta sections plus `## Questions`. Accepting it means the orchestrator copies the sections into
  `openspec/changes/<id>/specs/<capability>/spec.md` and sets the record `accepted`.
- A delta that touches the architecture, design or infrastructure spec also carries a new ADR in the matching folder (the user decides through the ADR).
- The sync agent never writes under `openspec/`; the orchestrator is the only writer of the spec.

## Archive

`openspec archive <id> --yes` moves the change folder to the archive folder named `YYYY-MM-DD-<id>`
(see the OpenSpec skill) and merges the deltas into the live specs. The `handoff/` folder is inside the change folder, so it
travels with it. Whether the CLI moves or validates a non-standard subfolder such as `handoff/` is
(unverified); run `openspec validate <id> --type change --strict --json --no-interactive` before the
archive and inspect the archived folder after the first real archive. The orchestrator archives
only after the final gate and with the user's approval (Ask-First C3 of the OpenSpec skill: archive
only is the agent default).

## GitHub Projects mirror (optional)

Off by default (`tracker.kind: none` in the profile; project values in `openspec/github-tracker.yaml`).
When enabled, the bridge skill `syncing-openspec-with-github-projects` mirrors the change, tasks, ADRs,
escalations and deltas to GitHub issues and a project; git stays canonical and GitHub content is never a spec
source. `openspec/changes/<id>/handoff/github.yaml` (issue ids) is written only by the bridge script; never edit it.
Approvals trust model: only the Actions gate workflow interprets `/approve`-style comments, accepting authors in
`tracker.approvers` and never `tracker.bot_login`; the orchestrator's `pull` trusts only confirmations authored
by `bot_login`, re-checks the user comment, and appends `source=github <url> login=<x>` to `## Approvals`.
Agents never run `pull` and a relayed "approved on GitHub" is not an approval.

## The final gate (E9)

All must hold, re-run by the orchestrator (not trusted from earlier output):

1. `check_records.py` exit 0.
2. `detect_drift.py` exit 0 and `board.py` shows `drift: false`, `pending spec-deltas: 0`.
3. A `verify` record with `outcome: pass` for each stage `E1`, `E2a`, `E2b`, `E2c`, `E3`, `E3b` (when the change has UI), `E4-<flow>` (every design), `E4-index`, `E4-infra`, `E5`, `E7` (`verify-E7.md` by `aws-lambda-debugger` mode B, role `debug`) and `E7-site` (`static-site-verifier`, when the change has a front end), each by a verifier that differs from the authors.
4. No open `escalation`; no blocking question; every `## Approvals` entry in `status.md` is the user's own words.
5. `board.py` prints `NEXT: final-gate`.
6. The last `result-NN-pipeline.md` of role `pipeline-cd` for prod is `success`.

Then: ask the user to approve the archive; the archive and the commit go in a PR of the user (the agents never push).

## Drift sync after a manual edit

`detect_drift.py` lists changed code paths that no report covers -> `spec-synchronizer` (mode B)
writes `spec-delta-NN` -> user accepts, rejects or answers -> `board.py --sync-sha <HEAD>` stores
the new SHA. The optional `Stop` hook only warns and needs the user's confirmation (see
[unverified and risks](./unverified-and-risks.md), U1).
