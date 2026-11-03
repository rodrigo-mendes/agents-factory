# Worked example: spec.md to .feature

Back to [SKILL.md](../SKILL.md). The same fixtures drive the script tests; mapping rules in [mapping and deltas](./mapping-and-deltas.md).

## Input: `openspec/specs/greeting/spec.md`

```markdown
# greeting Specification

## Purpose
Greet a visitor by name.

## Requirements

### Requirement: R1 Greet a known visitor
The system SHALL greet a visitor by the given name.

#### Scenario: named visitor
- **WHEN** the visitor opens the greeting with the name "Ana"
- **THEN** the greeting is "Hello, Ana"

#### Scenario: blank name
- **GIVEN** a visitor without a name
- **WHEN** the visitor opens the greeting
- **THEN** the greeting is "Hello, guest"
- **AND** the status is 200
```

## Output: `src/test/resources/features/greeting.feature`

```gherkin
@change-greet
Feature: greeting
  Greet a visitor by name.

  @R1
  Rule: R1 Greet a known visitor
    The system SHALL greet a visitor by the given name.

    @happy
    Scenario: named visitor
      When the visitor opens the greeting with the name "Ana"
      Then the greeting is "Hello, Ana"

    @happy
    Scenario: blank name
      Given a visitor without a name
      When the visitor opens the greeting
      Then the greeting is "Hello, guest"
      And the status is 200
```

Notes: only the second scenario has a `Given` because only it writes GIVEN; scenario names are verbatim; `@change-greet` is on the Feature and inherited.

## Delta input (plain keywords): `openspec/changes/add-x/specs/greeting/spec.md`

```markdown
## ADDED Requirements

### Requirement: R2 Greet in uppercase on request
The system SHALL return the greeting in uppercase when the visitor asks for it.

#### Scenario: uppercase requested
- WHEN the visitor opens the greeting with the name "Ana" and asks for uppercase
- THEN the greeting is "HELLO, ANA"
```

ADDED becomes a new Rule `@R2` in the same file, with `@change-add-x` on the Feature.

## Verify

```bash
python <skill>/scripts/check_feature_coverage.py --spec-root openspec --change add-x --features src/test/resources/features
```

Expected: exit 0, every spec scenario listed as covered. Delete the feature scenario `blank name` and the exit becomes 1 with a `MISSING R1 'blank name'` line.

## Requirement without R-id

`### Requirement: Greet a known visitor` is tagged `@req-greet-a-known-visitor` (kebab-case of the title); matching is the same.
