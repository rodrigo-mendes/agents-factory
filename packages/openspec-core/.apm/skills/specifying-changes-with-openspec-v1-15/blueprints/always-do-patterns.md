# Always-Do Patterns (OpenSpec 1.15.0)

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Delta sections have their own blueprint: [delta format and archive](./delta-format-and-archive.md).

## Contents

- [1. Format and CLI only](#1-format-and-cli-only)
- [2. Live spec skeleton](#2-live-spec-skeleton)
- [3. SHALL or MUST](#3-shall-or-must)
- [4. Scenarios](#4-scenarios)
- [5. Proposal headings](#5-proposal-headings)
- [6. Docs versus validator](#6-docs-versus-validator)
- [7. Tasks format](#7-tasks-format)
- [8. Machine use](#8-machine-use)
- [9. Archive](#9-archive)

## 1. Format and CLI only

Agents in this factory use OpenSpec's **format** and the **`openspec` CLI** only. User decision G1, verbatim: "Format + CLI, our agents (Recommended)". The generated `/opsx:*` commands and `openspec-*` skills are optional for a human and are not used by agents.

Why: `openspec init --tools claude` writes `.claude/skills/openspec-*/SKILL.md` and `.claude/commands/opsx/<id>.md`; `openspec update` regenerates and prunes them per profile ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md), [supported-tools](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/supported-tools.md)). Agent behaviour must not drift with a profile. Overlap with our agents: [table](./ask-first-decisions.md#opsx-overlap-table).

```bash
# Representative: the agent-facing surface is only these commands (OpenSpec 1.15.0)
openspec validate <id> --type change --strict --json --no-interactive
openspec show <id> --type change --deltas-only --json --no-interactive
openspec archive <id> --yes
```

## 2. Live spec skeleton

Every live spec needs `## Purpose` and `## Requirements`. Missing either is an error: "Missing required sections. Expected headers: \"## Purpose\" and \"## Requirements\"" ([constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts)). A Purpose under 50 characters is a warning; a spec with no requirement is an error (same source). The title form `# <Name> Specification` is used by [concepts.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md).

```markdown
# Orders Specification

## Purpose
Accepts, prices and tracks customer orders for a single tenant end to end.

## Requirements

### Requirement: Order creation
The system SHALL create an order when a valid cart is submitted.

#### Scenario: Valid cart
- **WHEN** a tenant user submits a cart with at least one item
- **THEN** the system creates an order in status PENDING
- **AND** returns the order id
```

## 3. SHALL or MUST

Use the literal English `SHALL` or `MUST` in every requirement. A requirement without them gives "Requirement must contain SHALL or MUST keyword" ([constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts)); the warning fails `--strict` ([cli-validate spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-validate/spec.md)). The writing-specs page also names SHOULD and MAY (conflict C5, see [conflicts](./doc-vs-validator-conflicts.md#c5-rfc-2119-words)); put SHOULD/MAY nuance into additional sentences, never as the only keyword.

```markdown
### Requirement: Session timeout
The system SHALL expire a session after 30 minutes of inactivity.
```

## 4. Scenarios

Each requirement needs at least one scenario ("Requirement must have at least one scenario" is an error). Scenarios use exactly `####` (family fact, orchestrator-verified 2026-10-28, quoting [schema.yaml](https://github.com/Fission-AI/OpenSpec/blob/v1.15.0/schemas/spec-driven/schema.yaml): "3 hashtags or bullets will fail silently"). Bullets without a scenario header give the warning "Scenarios must use '#### Scenario:' headers" ([cli-validate spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-validate/spec.md)).

Steps are written `- **WHEN**`, `- **THEN**`, `- **AND**`, as in the schema, the validator guides and the repo's own specs. Whether the parser rejects non-bold steps is (unverified); bold is the safe form (conflict C1).

```markdown
#### Scenario: Idle timeout
- **WHEN** 30 minutes pass with no activity
- **THEN** the session is invalidated
- **AND** the user must re-authenticate
```

## 5. Proposal headings

The validator requires `## Why` (at least 50 characters, error; over 1000 characters gives "should not exceed") and `## What Changes` (cannot be empty) ([constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts)). The template headings are `# Proposal`, `## Why`, `## What Changes`, `## Capabilities` (`### New Capabilities`, `### Modified Capabilities`), `## Impact` ([proposal template](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/templates/proposal.md)).

```markdown
# Proposal

## Why
Administrators need stronger login protection after the Q3 security review findings.

## What Changes
- Add a second factor for administrator logins.

## Capabilities
### New Capabilities
### Modified Capabilities
- auth

## Impact
Auth service and login UI.
```

## 6. Docs versus validator

When a docs page and the schema, template or validator disagree, follow the schema, templates and validator and cite both URLs. The six known conflicts are in [conflicts](./doc-vs-validator-conflicts.md). Source: family fact verified 2026-10-28.

## 7. Tasks format

"Each tracked task MUST be a checkbox: `- [ ] X.Y Task description`" ([schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)). Group under numbered `## N. <Group>` headings. A box with only `x` (either case, any spacing) counts as done; `- [~]` and `- []` count as unfinished. `openspec validate --archived` fails if an archived change has unchecked tasks ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)). Plain bullets go under a section such as `## Workflow follow-up`.

```markdown
# Tasks

## 1. Auth backend
- [x] 1.1 Add TOTP secret column (verify: migration test passes)
- [ ] 1.2 Enforce second factor for admins (verify: scenario "Admin login" test)

## Workflow follow-up
- Archive after merge
```

## 8. Machine use

Validating before every archive is the recommended sequence (Ask First, medium confidence, L1: [SKILL.md](../SKILL.md), row "Validate before every archive; validate command form and version check"). Reading its result is an Ask-First item (row "Reading validate results and exit codes"), because its confidence is medium:

- In `--json` mode stdout holds exactly one pretty-printed JSON document; prose and spinners go to stderr; JSON mode is strictly non-interactive (medium confidence, L2: agent-contract.md was read in condensed form, no verbatim quote recorded; [agent-contract.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/agent-contract.md)).
- Exit `0` is success; exit `1` is any error, including validation failure (medium confidence, L1: cli.md was read through a summarising fetch, no verbatim quote recorded; [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)).
- The JSON field names differ between pages (medium confidence, M1); see [JSON and result reading](./non-interactive-and-windows.md#json-and-result-reading).

```bash
# Representative; adapt to your environment (OpenSpec 1.15.0)
openspec validate --all --strict --json --no-interactive > validate.json
echo "exit=$?"   # 0 = all items valid; 1 = at least one invalid item or error
```

## 9. Archive

`openspec archive <id> --yes` applies the deltas to the live specs and moves the folder to `openspec/changes/archive/YYYY-MM-DD-<id>/` (medium confidence, L2: the cli-archive spec was read as paraphrased scenarios; [cli-archive spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-archive/spec.md)). Without a terminal and without `--yes`, archive "stops before changing anything" and exits 1 (High: the quote is recorded in the research, see the register; [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)). After exit 0, re-validate the live specs with `openspec validate --specs --strict --json --no-interactive`.

```bash
# Representative; OpenSpec 1.15.0
openspec archive add-2fa --yes
```
