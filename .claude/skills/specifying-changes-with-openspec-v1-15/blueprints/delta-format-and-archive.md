# Delta Format and Archive Merge Order (OpenSpec 1.15.0)

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Sources: [schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml), [openspec-conventions spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md), [writing-specs.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/writing-specs.md), [cli-archive spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-archive/spec.md).

## Contents

- [Where deltas live](#where-deltas-live)
- [ADDED](#added)
- [MODIFIED](#modified)
- [REMOVED](#removed)
- [RENAMED](#renamed)
- [New capability: delta Purpose](#new-capability-delta-purpose)
- [Archive merge order](#archive-merge-order)
- [Archive guards](#archive-guards)
- [Capability retirement](#capability-retirement)
- [One delta file, all four sections](#one-delta-file-all-four-sections)

## Where deltas live

A delta spec is `openspec/changes/<change-name>/specs/<capability>/spec.md`. The four section headers are exactly `## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements`, `## RENAMED Requirements`. A change with zero deltas fails validation unless `.openspec.yaml` has `skip_specs: true` ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)).

## ADDED

Full requirement blocks, each with SHALL or MUST and at least one scenario. They are appended to the live spec at archive.

```markdown
## ADDED Requirements

### Requirement: Two-factor login
The system MUST require a second factor for administrator accounts.

#### Scenario: Admin login
- **WHEN** an administrator submits valid credentials
- **THEN** the system requests a one-time code
```

## MODIFIED

Include "the complete modified requirement (not a diff)": header, requirement sentence and every scenario. At archive the block replaces the live requirement by normalized header match, so any scenario you leave out is lost. Validation errors when a MODIFIED requirement omits scenarios the live spec still has ([cli-validate spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-validate/spec.md)). If the live requirement has two scenarios, both are repeated. Every MODIFIED header must already exist in the live spec.

```markdown
## MODIFIED Requirements

### Requirement: Session timeout
The system SHALL expire a session after 15 minutes of inactivity.

#### Scenario: Idle timeout
- **WHEN** 15 minutes pass with no activity
- **THEN** the session is invalidated
```

## REMOVED

The requirement header plus `**Reason**:` and `**Migration**:` lines. The conventions spec says to include the reason for removal and to document any migration path if applicable.

```markdown
## REMOVED Requirements

### Requirement: Legacy export
**Reason**: Replaced by new export system
**Migration**: Use new export endpoint at /api/v2/export
```

## RENAMED

`- FROM:` and `- TO:` lines, each holding the full `### Requirement:` header in backticks. Use it for a name change only. If the content also changes, put the requirement under MODIFIED with the **new** header. Since v1.13.1 archive refuses mismatched FROM/TO lines and names that differ only in case (medium confidence, L2: condensed release highlights; [releases](https://github.com/Fission-AI/OpenSpec/releases)).

```markdown
## RENAMED Requirements
- FROM: `### Requirement: Login`
- TO: `### Requirement: Password login`
```

## New capability: delta Purpose

A delta for a new capability may open with `## Purpose` of at least 50 characters. It seeds the live spec's Purpose and is ignored for an existing spec. If it is missing, archive writes a `TBD - created by archiving change ...` placeholder ([writing-specs.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/writing-specs.md), [schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)).

## Archive merge order

Applied per capability, in this order (medium confidence, L2: partly read page, no recorded quote; [conventions spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md)):

| Step | Section | Effect |
|---|---|---|
| 1 | RENAMED | Retitle the live requirement (FROM to TO) |
| 2 | REMOVED | Delete by normalized header match |
| 3 | MODIFIED | Replace by normalized header match, using the new names if renamed |
| 4 | ADDED | Append |

Consequence: a requirement renamed in step 1 is addressed by its new header in MODIFIED, and one removed in step 2 cannot also be MODIFIED.

## Archive guards

From the [cli-archive spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-archive/spec.md):

- A delta that would create duplicate headers aborts.
- A live spec that already has duplicate headers is rejected before anything is applied.
- The target folder is `YYYY-MM-DD-<change-name>` with the current date; a name that already has a date prefix is kept; an existing target fails instead of being overwritten.
- Incomplete `- [ ]` tasks are listed and confirmation is asked, default No (conflict C4, see [conflicts](./doc-vs-validator-conflicts.md#c4-archive-with-incomplete-tasks)).
- `--skip-specs` moves the change without touching specs; `--no-validate` requires confirmation and also disables capability retirement ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)).

## Capability retirement

Removing a capability's last requirement deletes `openspec/specs/<capability>/spec.md` only when the change's `.openspec.yaml` has `retire_capabilities: true`; otherwise archive aborts. Retirement is also refused if the spec has extra content such as `## Notes` ([writing-specs.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/writing-specs.md), [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)).

## One delta file, all four sections

File `openspec/changes/<id>/specs/auth/spec.md`; the section order follows the archive order.

```markdown
## RENAMED Requirements
- FROM: `### Requirement: Login`
- TO: `### Requirement: Password login`

## MODIFIED Requirements

### Requirement: Session timeout
The system SHALL expire a session after 15 minutes of inactivity.

#### Scenario: Idle timeout
- **WHEN** 15 minutes pass with no activity
- **THEN** the session is invalidated

## REMOVED Requirements

### Requirement: Legacy export
**Reason**: Replaced by new export system
**Migration**: Use new export endpoint at /api/v2/export

## ADDED Requirements

### Requirement: Two-factor login
The system MUST require a second factor for administrator accounts.

#### Scenario: Admin login
- **WHEN** an administrator submits valid credentials
- **THEN** the system requests a one-time code
```

Inspect what the parser sees before archiving: `openspec show <id> --type change --deltas-only --json --no-interactive`.
