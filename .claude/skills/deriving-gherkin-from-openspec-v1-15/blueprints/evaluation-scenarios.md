# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario states the query, the expected behaviour and what must not appear.

## Scenario 1 (canonical)

query: "Generate the feature file for openspec/specs/items/spec.md (R1 and R2, two scenarios each)."

Expected:
- One `src/test/resources/features/items.feature` with one `Feature: items`, two `Rule:` blocks tagged `@R1` and `@R2`, four scenarios with the spec names verbatim.
- `Given` only where the spec writes GIVEN; `@change-<id>` on the Feature when a change id is known; `@happy` or `@negative` per scenario.
- Runs `check_feature_coverage.py --spec-root openspec --features src/test/resources/features` and reports the traceability table.

Must not: invent steps, rename scenarios, or skip the script.

## Scenario 2 (edge: delta with plain keywords)

query: "Change add-x adds R2 and removes R7. The delta uses plain `- WHEN` bullets. Update the features."

Expected:
- Reads plain and bold keywords; adds a Rule `@R2`, deletes the Rule `@R7`, runs the script with `--change add-x`.
- Asks (or states) whether features are per change or from merged specs.

Must not: ignore bullets because they are not bold.

## Scenario 3 (rejection: put Gherkin into the spec)

query: "Replace spec.md with the .feature file so there is one source."

Expected:
- Declines: spec.md stays the canonical Markdown artifact, the `.feature` is derived beside the tests (medium confidence reasoning, no official OpenSpec tool).
- Offers the coverage script as the way to keep both in sync.

Must not: delete or rewrite `spec.md` into Gherkin.

## Scenario 4 (trap: missing precondition)

query: "Scenario 'empty tenant' obviously needs a logged-in admin, add that Given."

Expected:
- Does not add the Given; writes a numbered question (`Q1`) and explains the spec does not state it.
- Offers to add the Given after the spec is updated.

Must not: write `Given the user is logged in as admin`.

## Scenario 5 (trap: invented variants)

query: "Make the quantity scenario an Outline with 0, 1, 1000 and 5000."

Expected:
- Checks the spec: only listed variants become Examples rows; unlisted values become questions.
- Uses plain `Scenario` if the spec lists none.

Must not: add Examples rows the spec does not list.

## Scenario 6 (check: requirement without R-id)

query: "The spec has `### Requirement: Greet a known visitor` with no R-id. Tag it."

Expected: `@req-greet-a-known-visitor` above the Rule; may ask whether R-ids can be added to the spec first; the script reports it covered.

Must not: invent an `@R<n>` the spec does not carry.
