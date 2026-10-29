# Never-Do Patterns (OpenSpec 1.15.0)

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Every row rests on High claims; items that are mainly medium or unverified live in [ask-first decisions](./ask-first-decisions.md).

## Contents

- [F1 Partial MODIFIED delta](#f1-partial-modified-delta)
- [F2 Rename through REMOVED plus ADDED](#f2-rename-through-removed-plus-added)
- [F3 Archive in a script without a name or --yes](#f3-archive-in-a-script-without-a-name-or---yes)
- [F4 Agents depending on generated opsx commands or skills](#f4-agents-depending-on-generated-opsx-commands-or-skills)
- [F5 Requirement without SHALL or MUST, scenario without header](#f5-requirement-without-shall-or-must-scenario-without-header)
- [F6 Proposal headings from the concepts page](#f6-proposal-headings-from-the-concepts-page)

## F1 Partial MODIFIED delta

Severity: high. MODIFIED replaces the whole requirement at archive; "Using MODIFIED with partial content loses detail at archive time" ([schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)). Validation errors when MODIFIED omits scenarios the live spec has, and archive refuses the change ([cli-validate spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-validate/spec.md), [troubleshooting](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/troubleshooting.md)).

```markdown
<!-- 🚫 WRONG -->
## MODIFIED Requirements
### Requirement: Session timeout
Change 30 minutes to 15 minutes.
```

```markdown
<!-- ✅ CORRECT -->
## MODIFIED Requirements
### Requirement: Session timeout
The system SHALL expire a session after 15 minutes of inactivity.

#### Scenario: Idle timeout
- **WHEN** 15 minutes pass with no activity
- **THEN** the session is invalidated
```

## F2 Rename through REMOVED plus ADDED

Severity: high. Renames have a dedicated `## RENAMED Requirements` section, applied first at archive (medium confidence, L2: cli-archive read as paraphrased scenarios); a content change after a rename goes under MODIFIED with the new header. Since v1.13.1 archive refuses mismatched FROM/TO lines (medium confidence, L2: condensed release highlights; [releases](https://github.com/Fission-AI/OpenSpec/releases)); the section format itself is in the [conventions spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md). Impact: lost requirement history or an archive refusal.

```markdown
<!-- 🚫 WRONG -->
## REMOVED Requirements
### Requirement: Login
## ADDED Requirements
### Requirement: Password login
```

```markdown
<!-- ✅ CORRECT -->
## RENAMED Requirements
- FROM: `### Requirement: Login`
- TO: `### Requirement: Password login`
```

## F3 Archive in a script without a name or --yes

Severity: high. Without a terminal and without `--yes`, archive "stops before changing anything" and exits 1 (High; quote recorded in the register); a missing change name in non-interactive mode exits non-zero ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md), [cli-archive spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-archive/spec.md)). The troubleshooting page shows the older symptom `User force closed the prompt with 0 null` ([troubleshooting](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/troubleshooting.md)).

```bash
# 🚫 WRONG
openspec archive
```

```bash
# ✅ CORRECT (representative; OpenSpec 1.15.0)
openspec archive add-2fa --yes
```

## F4 Agents depending on generated opsx commands or skills

Severity: high for this factory (decision G1). The generated commands and skills are profile-dependent, regenerated and pruned by `openspec update`; skills are "detected at startup", so changes need an IDE restart; since v1.13.1 they name only the workflows the profile installs (medium confidence, L2: condensed release highlights; [releases](https://github.com/Fission-AI/OpenSpec/releases)) ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md), [migration-guide](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/migration-guide.md)). Impact: agent behaviour drifts with the profile, and it duplicates the `spec-synchronizer` agent.

```text
🚫 WRONG (agent prompt): Run /opsx:archive to finish the change.
✅ CORRECT (agent prompt): Run "openspec archive <id> --yes". The validate step before it is the Ask First row "Validate before every archive; validate command form and version check".
```

## F5 Requirement without SHALL or MUST, scenario without header

Severity: moderate. "Requirement must contain SHALL or MUST keyword" ([constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts)); bullets without `#### Scenario:` give a warning that fails `--strict` ([cli-validate spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-validate/spec.md)).

```markdown
<!-- 🚫 WRONG -->
### Requirement: Export
Users can export data.
- WHEN user clicks Export
- THEN a CSV downloads
```

```markdown
<!-- ✅ CORRECT -->
### Requirement: Export
The system SHALL let users export their data as CSV.

#### Scenario: Successful export
- **WHEN** user clicks "Export" button
- **THEN** system downloads a CSV file with all user data
```

## F6 Proposal headings from the concepts page

Severity: moderate. The validator requires `## Why` and `## What Changes`; the `## Intent` / `## Scope` / `## Approach` example in [concepts.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md) would fail validation (conflict C2, [conflicts](./doc-vs-validator-conflicts.md#c2-proposal-sections)). Sources: [constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts), [proposal template](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/templates/proposal.md).

```markdown
<!-- 🚫 WRONG -->
# Proposal: Add 2FA
## Intent
## Scope
## Approach
```

```markdown
<!-- ✅ CORRECT -->
# Proposal
## Why
## What Changes
## Capabilities
## Impact
```
