# Evaluation Scenarios - syncing-spec-from-code

Five scenarios for the `spec-synchronizer` agent routed via this skill.

## Contents

- [Scenario 1: Drift in one requirement (canonical)](#scenario-1-drift-in-one-requirement-canonical)
- [Scenario 2: No drift](#scenario-2-no-drift)
- [Scenario 3: Delta conflicts with an accepted ADR](#scenario-3-delta-conflicts-with-an-accepted-adr)
- [Scenario 4: Record drift with detect_drift exit 0](#scenario-4-record-drift-with-detect_drift-exit-0)
- [Scenario 5: Misuse, spec.kind none](#scenario-5-misuse-speckind-none)

---

## Scenario 1: Drift in one requirement (canonical)

**Input**:
```
/syncing-spec-from-code list-tenant-items
```

**Context**: `detect_drift.py` exits 2 with `DRIFT: src/main/java/.../ItemResource.java`. The code
now caps the page size at 50; the spec requirement "List items" says nothing about a cap and has
two scenarios.

**Expected agent behavior**:
1. Runs `detect_drift.py`, reads the diff since `lastSyncedSha`, the spec and ADRs.
2. Returns one `spec-delta-<nn>` record with `status: proposed` and a `## MODIFIED Requirements`
   entry that repeats the whole "List items" requirement (sentence + both scenarios, one new
   scenario for the cap).
3. `## Questions` asks whether 50 is a business rule or only technical.
4. Ends with the `Hand off: orchestrator - save spec-delta-<nn>.md ...` line.

**Pass criteria**:
- MODIFIED block is complete (no partial requirement); bold WHEN/THEN under `#### Scenario:`.
- No file written, no spec or code edited (no Write tool used, no shell redirect).
- `status` is `proposed`.

---

## Scenario 2: No drift

**Input**: `/syncing-spec-from-code list-tenant-items` when `detect_drift.py` exits 0 and every
`report` record with `spec_impact: divergence|ambiguity` is already listed in the `refs` of a `spec-delta`.

**Expected**: reports "no drift", returns no delta, stops.

**Pass criteria**: no delta record invented; no Bash command outside the allowed list; the record
scan was done (not only the script exit code).

---

## Scenario 3: Delta conflicts with an accepted ADR

**Input**:
```
/syncing-spec-from-code list-tenant-items
```

**Context**: the drifted code uses a polling loop; accepted ADR-004 mandates event-driven updates.

**Expected agent behavior**:
1. Proposes the delta describing the observed behaviour.
2. Names ADR-004 in `## Questions` and states that accepting the delta needs a new ADR; the user decides.
3. Reports `delta_revisions: <n>` from the existing `revise` records.

**Pass criteria**: the conflict is explicit, not silently resolved; acceptance is never decided by the agent.

---

## Scenario 4: Record drift with detect_drift exit 0

**Input**: `/syncing-spec-from-code list-tenant-items`

**Context**: `detect_drift.py` exits 0 (every changed file is named by a report), but
`result-03-code.md` has `spec_impact: divergence` and no `spec-delta` lists `result-03-code` in `refs`.
The board therefore reports drift.

**Expected agent behavior**:
1. Runs `detect_drift.py` (exit 0) and scans the handoff records; finds `result-03-code` uncovered.
2. Does **not** answer "no drift"; continues to P2, reads that report and the spec.
3. Returns a `spec-delta-<nn>` with `status: proposed` whose `refs` include `result-03-code`.

**Pass criteria**: the delta `refs` the uncovered record id; no "no drift" stop; no file written.

---

## Scenario 5: Misuse, spec.kind none

**Input**: `/syncing-spec-from-code func-api-facade --profile oci.yaml` where the profile has `spec.kind: none` (the profile's `root` template, here `docs/handoff/{capability}`, resolves the id `func-api-facade`; the agent reads `spec.kind` first and does not need the folder).

**Expected agent behavior**: reads `spec.kind`, says the family has no spec side and stops.

**Pass criteria**: no delta proposed; no `detect_drift.py` run; no invented spec; says the orchestrator
should not route `none` families to this command.
