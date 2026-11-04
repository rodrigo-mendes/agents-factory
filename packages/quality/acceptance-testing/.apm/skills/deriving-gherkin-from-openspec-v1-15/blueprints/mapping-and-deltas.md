# Mapping, tags, deltas and file layout

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-01: [Gherkin reference](https://cucumber.io/docs/gherkin/reference), [schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml), [conventions spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md), [concepts.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md).

## Mapping table

| OpenSpec 1.15 element | Gherkin element |
|---|---|
| `openspec/specs/<cap>/spec.md` or `openspec/changes/<id>/specs/<cap>/spec.md` | one `.feature`, `Feature: <cap>` |
| `## Purpose` | free-text description under `Feature:` |
| `### Requirement: R<n> <title>` and its SHALL text | `@R<n>` then `Rule: R<n> <title>`, SHALL text as description |
| `#### Scenario: <name>` (exactly four `#`) | `Scenario: <name>`, name kept verbatim |
| `GIVEN` or `**GIVEN**` | `Given`, only if written |
| `WHEN` or `**WHEN**` | `When` |
| `THEN` or `**THEN**` | `Then` |
| `AND` or `**AND**` | `And` (continues the previous kind) |
| sub-bullets listing value variants | `Scenario Outline` plus `Examples` |
| change id (change delta only) | `@change-<id>` on the Feature; none for a spec root |

Spec bullets may use `-`, `*` or `+`; accept all three.

## Tags

- `@R<n>` above each `Rule:` (factory convention F11); when the requirement has no R-id use `@req-<slug>`, slug = kebab-case of the title.
- For a change delta, `@change-<id>` above `Feature:` (none for a spec root); Rule, Scenario and Examples inherit it.
- Outcome tags `@happy` or `@negative` above a `Scenario:`: `@negative` when the THEN is a rejection, error or empty result, else `@happy`.
- Tags never go above `Background:` or steps.

## File layout

```
src/test/resources/features/<capability>.feature      one Feature per capability
openspec/specs/<capability>/spec.md                    source of truth, stays Markdown
```

Keep `spec.md` canonical and write the `.feature` beside the tests (medium confidence: the OpenSpec CLI handles Markdown spec artifacts only, see register M3).

## Deltas

Delta specs live in `openspec/changes/<id>/specs/<capability>/spec.md`; archive applies them in the order RENAMED, REMOVED, MODIFIED, ADDED.

| Delta section | Feature file action |
|---|---|
| `## ADDED Requirements` | add a new Rule with its scenarios |
| `## MODIFIED Requirements` | regenerate the whole Rule; the delta repeats the full requirement block |
| `## REMOVED Requirements` | delete the Rule and its scenarios |
| `## RENAMED Requirements` (FROM and TO lines) | retitle the Rule, keep its `@R<n>` tag |

Per-change versus merged generation is an Ask First decision (medium confidence, register M1). The coverage script merges base specs with the delta when `--change <id>` is given: ADDED and MODIFIED replace or add, REMOVED leaves the merged set, RENAMED moves the base requirement to its new name.

With `--change`, the script checks the merged base plus the delta: base requirements the change does not touch and that have no features are reported MISSING (generate them or exclude them).

## Requirement without scenarios

A `### Requirement:` with no `#### Scenario:` is reported as EMPTY (`empty_requirements`, reason `no-scenarios`) and the script exits 1. It becomes a numbered question to the spec owner ("Q2: R2 has no scenario, which behaviour proves it?"), never an invented scenario.

## Scenario Outline

Use it only when a scenario in the spec lists variants (sub-bullets or a table). Each variant becomes one Examples row; a variant that the spec does not list is not generated.

```gherkin
@R3
Rule: R3 Reject out-of-range quantity
  @negative
  Scenario Outline: quantity out of range
    When the caller orders <quantity> units
    Then the order is rejected with status <status>

    Examples:
      | quantity | status |
      | 0        | 400    |
      | 1001     | 400    |
```
