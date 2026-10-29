# Docs Versus Validator Conflicts (OpenSpec 1.15.0)

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Rule: where the docs and the validator or schema conflict, follow `schema.yaml`, the templates and the validator, and cite both (family fact verified 2026-10-28). Items the research could not settle stay in the [register](./unverified-and-risks.md).

## Contents

- [C1 Scenario step markup](#c1-scenario-step-markup)
- [C2 Proposal sections](#c2-proposal-sections)
- [C3 validate --json shape](#c3-validate---json-shape)
- [C4 Archive with incomplete tasks](#c4-archive-with-incomplete-tasks)
- [C5 RFC 2119 words](#c5-rfc-2119-words)
- [C6 archive --json](#c6-archive---json)

## C1 Scenario step markup

| Side | Source | Says |
|---|---|---|
| Docs | [concepts.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md), [writing-specs.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/writing-specs.md) | plain `- GIVEN` / `- WHEN` / `- THEN` bullets |
| Schema and validator | [schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml), [constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts), [conventions spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md), [cli-archive spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-archive/spec.md) | bold `- **WHEN**` / `- **THEN**` / `- **AND**` |

Decision: always emit bold. Whether the 1.15.0 parser rejects non-bold steps is (unverified); bold is the safe superset.

## C2 Proposal sections

| Side | Source | Says |
|---|---|---|
| Docs | [concepts.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md) | `## Intent`, `## Scope`, `## Approach` |
| Template and validator | [proposal template](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/templates/proposal.md), [constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts), [cli-validate spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-validate/spec.md) | `## Why` and `## What Changes` required |

Decision: the validator wins; use `## Why` and `## What Changes`.

## C3 validate --json shape

| Side | Source | Says |
|---|---|---|
| CLI reference | [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md) | `results` (`name`, `valid`, `warnings`) and `summary{total, valid, invalid}` |
| Agent contract and validator spec | [agent-contract.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/agent-contract.md), [cli-validate spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-validate/spec.md) | `items`, `summary`, `version: "1.0"` |

Decision: gate on the exit code (medium confidence, L1), read `items`, fall back to `results` (medium confidence, M1). See [JSON and result reading](./non-interactive-and-windows.md#json-and-result-reading).

## C4 Archive with incomplete tasks

| Side | Source | Says |
|---|---|---|
| Troubleshooting | [troubleshooting](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/troubleshooting.md) | archive "won't block" but warns |
| Spec | [cli-archive spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-archive/spec.md) | prompts with default No; declining aborts non-zero |

Both hold if read as warn plus confirm. With `--yes` the behaviour is presumably to proceed (unverified). Decision: check every task before `archive`.

## C5 RFC 2119 words

| Side | Source | Says |
|---|---|---|
| Docs | [writing-specs.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/writing-specs.md), [concepts.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md) | SHOULD and MAY are accepted RFC 2119 words |
| Validator | [constants.ts](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/src/core/validation/constants.ts) | every requirement must contain SHALL or MUST |

Decision: SHALL or MUST in every requirement; SHOULD or MAY only in additional sentences.

## C6 archive --json

| Side | Source | Says |
|---|---|---|
| CLI reference | [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md) | no `--json` flag listed for `archive` |
| Agent contract and releases | [agent-contract.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/agent-contract.md), [releases](https://github.com/Fission-AI/OpenSpec/releases) | an `archive` JSON object is documented; v1.14.1 mentions `archive_retirement_cleanup_failed` "in `--json`" |

Unverified (register I2). Decision: gate on the exit code and check that the archive folder exists.

## Minor

The releases page dates v1.14.1 as 06 Oct while the [tags page](https://github.com/Fission-AI/OpenSpec/tags) says Oct 5, 2026, likely a timezone difference. No conflict with the family facts; their open tag on MODIFIED and REMOVED sections is resolved by the research (schema.yaml, conventions spec, writing-specs.md, cli-validate spec).
