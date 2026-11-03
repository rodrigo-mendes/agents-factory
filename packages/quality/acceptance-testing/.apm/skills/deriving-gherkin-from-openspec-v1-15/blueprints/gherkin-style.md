# Gherkin style rules and anti-patterns

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-01: [Gherkin reference](https://cucumber.io/docs/gherkin/reference), [Better Gherkin](https://cucumber.io/docs/bdd/better-gherkin), [anti-patterns](https://cucumber.io/docs/guides/anti-patterns/), [Cucumber API tags](https://cucumber.io/docs/cucumber/api/) (tags section only, see register L3).

## Style rules

- Declarative: describe what the user achieves, not clicks. Spec steps are already behavioural; keep their wording.
- One behaviour per scenario; the spec scenario is the unit, do not merge two.
- A `Then` states an observable outcome (response, status, visible result), not internal state such as a database row; OpenSpec requirements stay externally observable.
- `And` continues the previous kind; do not start a scenario with `And`.
- A Background (one per Feature or per Rule) holds only a GIVEN that every scenario of that Rule states in the spec; keep it short (the reference suggests about four lines). Default is a repeated `Given`.
- Keep the Rule description (the SHALL sentence) as free text under `Rule:`; it is not a step.
- Keywords are ignored when step definitions match text, so the same sentence under `Given` and `Then` is ambiguous.
- Comments with `#` are allowed; use them for numbered questions: `# QUESTION Q1: ...`.

## Anti-patterns and fixes

| Anti-pattern | Fix |
|---|---|
| Imperative UI steps (fill, click, press) | `When Bob logs in` |
| Conjunction step: `Given I have shades and a brand new Mustang` | `Given I have shades` then `And I have a brand new Mustang` |
| Same text under two keywords | `Then my account balance is 10` |
| Two Backgrounds in one Feature or Rule | split into more Rules |
| Colon after a keyword that takes none | remove the colon |
| Tag above a Background or step | move it to the Rule or Scenario |
| Invented Given | numbered question, no Given |

## Example of a question instead of a Given

```gherkin
@R1
Rule: R1 List items of the tenant
  @happy
  Scenario: empty tenant
    When the caller lists items
    Then an empty list is returned
    # QUESTION Q1: does R1 require an authenticated caller? (not stated in the spec)
```
