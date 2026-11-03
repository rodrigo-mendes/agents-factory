# Always-do patterns

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-01: [Gherkin reference](https://cucumber.io/docs/gherkin/reference), [Cucumber API tags](https://cucumber.io/docs/cucumber/api/), [conventions spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md), [concepts.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md).

## Structure

- One `.feature` per capability, one `Feature:`; one `Rule:` per requirement; one `Scenario:` per spec scenario.
- Scenario names are copied verbatim: the coverage script and test names `R<n>_<scenario>_<expectation>` (F11) depend on them.
- Source: https://cucumber.io/docs/gherkin/reference.

## Givens and questions

- Write `Given` only for a written GIVEN; WHEN, THEN and AND map literally.
- Accept bold (`**WHEN**`) and plain (`- WHEN`) keywords with `-`, `*` or `+` bullets when reading the spec.
- A precondition that is not in the spec is a numbered question (see [questions](./questions-and-traceability.md)).
- Source: conventions spec and concepts.md above.

## Tags

- `@R<n>` above each Rule (or `@req-<slug>`), `@change-<id>` above the Feature when generating from a change delta (none for a spec root), `@happy` or `@negative` above each Scenario.
- Tags above Feature are inherited by Rule, Scenario and Examples; never tag Background or steps.
- Source: https://cucumber.io/docs/cucumber/api/ (tags section).

## Verification loop

1. Coverage: `python <skill>/scripts/check_feature_coverage.py --spec-root openspec --features src/test/resources/features`
2. Delta: add `--change <id>`; the merged base plus delta set is checked.
3. Parser: add `--strict` after `pip install gherkin-official==42.0.1`; without the module the script warns and continues.
4. Script self-test: `python -m unittest discover -s <skill>/scripts/tests`
5. Fix the feature until exit 0; exit 2 means check the paths, exit 3 means fix the command line.

The script needs Python 3.8+ and the standard library only; `gherkin-official` itself needs Python 3.10 or newer (PyPI) and 3.11 on the main branch (medium confidence, register M4).

## Reporting

- Give the traceability table and the numbered questions in the final answer.
- State which Rules were generated, regenerated, deleted or retitled for a delta.
