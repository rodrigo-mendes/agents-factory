# Record Kinds (protocol v1)

Back to [SKILL.md](../SKILL.md). Templates: [work-order](../assets/work-order.template.md),
[result](../assets/result.template.md), [review](../assets/review.template.md),
[verify](../assets/verify.template.md), [spec-delta](../assets/spec-delta.template.md),
[escalation](../assets/escalation.template.md) (and the others in the same folder). The file
name of a `report` record follows the factory convention `result-<nn>-<role>.md`. Section names are
matched case-insensitively against `## ` headings (code fences ignored). A profile may replace the
required sections or the allowed values of a kind
([profile format](./profile-format.md#overriding-defaults)).

## Common frontmatter

| Field | Type | Required | Notes |
|---|---|---|---|
| `kind` | enum | yes | one of the kinds below |
| `id` | string | no | defaults to the file name without `.md`; must be unique in the folder |
| `from` | string | yes (not `status`) | author agent (a leading `@` is ignored) |
| `to` | string | yes (not `status`) | consumer agent, or `user` |
| `change` / `capability` | string | yes (not `status`) | the profile's `scope_key` names which |
| `task` | string | no | task id; inherited through `refs` when omitted; a work-order without it is its own task |
| `refs` | list or string | no | ids of records this one answers; each must exist (a `.md` suffix is ignored) |
| `requirements` | list | no | requirement ids (`R1`) |
| `role` | string | no | overrides the role derived from `from` (`to` for work-orders) via the profile |
| `createdAt` | ISO 8601 | yes (not `status`) | `2026-11-04T10:15:00Z`; placeholders are rejected |

Extra fields are allowed and ignored. Frontmatter is flat (`key: value`, inline `[a, b]` lists).

## Kinds

| Kind | Writer -> reader | Extra fields | Allowed values | Default required sections |
|---|---|---|---|---|
| `work-order` | orchestrator -> agent | `status` (req.) | `pending`, `in-progress`, `done`, `blocked`, `cancelled` (`completed` is accepted only when the profile lists it under `values:`; it then counts as done) | Scope, Skills, Requirements, Constraints, Acceptance criteria |
| `report` | agent -> orchestrator | `outcome` (req.), `spec_impact` | `success`, `partial`, `failed`, `needs-input`; impact `none`, `divergence`, `ambiguity` | Done, Evidence, Spec impact, Suggested next step |
| `review` | reviewer -> orchestrator | `outcome` (req.) | `approved`, `changes-requested` | Findings, ADR check |
| `deploy-report` | deployer -> debugger/orchestrator | `outcome` (req.) | `success`, `partial`, `failed`, `needs-input` | Deployed, Validation, Next step |
| `diagnosis-report` | debugger -> owner | `outcome` (req.), `spec_impact` | `success`, `partial`, `failed`, `needs-input` | Symptom, Root cause, Evidence, Exact fix, Classification, Next step |
| `spec-delta` | sync agent -> orchestrator/user | `status` (req.) | `proposed`, `accepted`, `rejected`, `revise` | Questions (+ at least one `ADDED/MODIFIED/REMOVED/RENAMED Requirements` section when `spec.kind: openspec`) |
| `escalation` | orchestrator -> user | `status` (req.), `limit`, `answeredAt` | `open`, `answered` | Attempts, Evidence, Hypothesis, Options (2-4 top-level items) |
| `verify` | verifier -> orchestrator | `stage` (req.), `outcome` (req.) | `pass`, `fail` | Criteria, Evidence |
| `status` | `board.py` (generated) | `profile`, `lastSyncedSha`, `updatedAt` | - | none (do not hand-edit, except `## Approvals`) |

## Outcome vocabulary

The **report family** (`report`, `deploy-report`, `diagnosis-report`) shares one vocabulary:
`success | partial | failed | needs-input`. `verify` alone uses `pass | fail`, `review` uses
`approved | changes-requested`. Agents never invent other outcome words; a profile may replace the
list per kind via `values:`. Only `failed` (and `partial` for `report`) advance the built-in
counters; a `needs-input` record waits for the orchestrator to ask the user.

## Lifecycles

- **work-order:** `pending -> in-progress -> done`, or `blocked` / `cancelled`. Only the
  orchestrator changes it. A task is `done` when all its non-cancelled work-orders are done.
- **report / review / deploy-report / diagnosis-report / verify:** immutable once written; the
  `outcome` is the result. A new attempt is a new record.
- **spec-delta:** `proposed -> accepted | rejected`, or `revise` (the user asked for a rework: keep
  the file, write the next `spec-delta-<nn>`). `proposed` and `revise` count as *pending deltas*.
- **escalation:** `open -> answered` (see [protocol](./protocol.md#escalation)).

## Field meaning used by the board

- A record's **role** is the profile role of its `from` agent (of `to` for a work-order).
- The **latest record** (greatest `createdAt` compared as a UTC instant, so `+02:00` offsets order
  correctly; unparseable values fall back to string order with a warning; ties by file name;
  `status` excluded) is the event
  the `next` rules match on `kind` / `role` / `outcome`.
- `spec_impact: divergence|ambiguity` with no `spec-delta` that `refs` the record = drift.
- `rejections: <int>` (optional, on any record) is written by the orchestrator each time it
  returns the record to its author after `check_records.py` failed; feeds `record_rejections`.

## Section content guide

- **Spec impact** (report): `Implemented:` ids, `Divergences:`, `Ambiguities:`, `Files:` with
  repo-relative paths in backticks. `detect_drift.py` looks for changed paths in the sections
  `Spec impact`, `Files`, `Files changed`, `What changed` of report-like records; the match is
  exact per path (a directory mention does not cover its files). Among `spec-delta` records only
  an **accepted** delta's `## Files` covers paths; proposed, revise and rejected cover nothing.
- **Findings** (review): `SEVERITY file:line - problem - fix`; a HIGH forces `changes-requested`.
- **Options** (escalation): top-level list items (`-` or `1.`), each with its impact.
- **Questions** (spec-delta): list items, or the single word `none`.
- **Files** (spec-delta): repo-relative paths in backticks that the delta covers. Recommended, not
  among the required sections checked by `check_records.py`; a delta without it covers no path.
