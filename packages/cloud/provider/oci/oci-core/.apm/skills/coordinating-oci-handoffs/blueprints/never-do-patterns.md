# Never-Do Patterns

Back to [SKILL.md](../SKILL.md).

## Contents

- [F1 A record name outside the convention](#f1-a-record-name-outside-the-convention)
- [F2 Two roles writing one file](#f2-two-roles-writing-one-file)
- [F3 Limit counters read as cycle counts](#f3-limit-counters-read-as-cycle-counts)
- [F4 Auto-chaining](#f4-auto-chaining)

## F1 A record name outside the convention

Severity: moderate. Name records `result-<role>.md`; the kind stays `report`. A subagent write guard on
names starting with `report` was observed `(unverified)`, register U1: if it applies, the record is
silently missing and the next agent finds nothing.

```text
# ❌ Wrong
docs/handoff/func-orders/report-java.md
# ✅ Correct (the kind inside the frontmatter stays `report`)
docs/handoff/func-orders/result-java.md
```

`deploy-report.md` and `diagnosis-report.md` do not start with `report` and keep their names.

## F2 Two roles writing one file

Severity: high. A second role that writes `result-terraform-infra.md` replaces the terraform record
(OCIDs, validation, outcome) within the same capability.

```text
# ❌ Wrong: oci-observability writes docs/handoff/<cap>/result-terraform-infra.md
# ✅ Correct: oci-observability writes docs/handoff/<cap>/result-observability.md
```

## F3 Limit counters read as cycle counts

Severity: moderate (High confidence: the generic protocol, skill `coordinating-agent-handoffs`, blueprint
`protocol.md`, says that for a family that overwrites records per cycle, counters that depend on history
(limits) are not meaningful). Records are overwritten on every new cycle, so the files cannot show how many
build attempts or deploy cycles happened. The profile limits (`build_attempts: 3`, `deploy_cycles: 2`) are
not meaningful counters in this family.

```text
# ❌ Wrong: "board.py reports no limit reached, so I retry again"
# ✅ Correct: keep "attempt 2 of 3" in the record body, and ask the user at the limit
```

## F4 Auto-chaining

Severity: moderate. No agent invokes another (not even `@oci-serverless-stack`, which hands off streams A and
B and resumes with `--integrate`). Every agent ends with the Hand off line; invoking the next agent itself skips the
user's chance to review the record.
