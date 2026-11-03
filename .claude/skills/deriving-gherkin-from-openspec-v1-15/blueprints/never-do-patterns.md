# Never-do patterns

Back to [SKILL.md](../SKILL.md). Sources read 2026-11-01: [Gherkin reference](https://cucumber.io/docs/gherkin/reference), [Better Gherkin](https://cucumber.io/docs/bdd/better-gherkin), [anti-patterns](https://cucumber.io/docs/guides/anti-patterns/), [Cucumber API tags](https://cucumber.io/docs/cucumber/api/), [conventions spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md).

## Invented Given

Impact: the feature asserts behaviour nobody approved.

```gherkin
# ❌ Wrong: the spec never mentions an admin
Scenario: empty tenant
  Given the user is logged in as admin
  When the user lists items
```

✅ Instead: no Given and a numbered question.

```gherkin
Scenario: empty tenant
  When the user lists items
  Then an empty list is returned
  # QUESTION Q1: does R1 require an authenticated caller? (not stated in the spec)
```

## Tag above Background or a step

```gherkin
# ❌ Wrong
@R1
Background:
```

✅ Instead: `@R1` above `Rule:`.

## Imperative UI steps

```gherkin
# ❌ Wrong
When I fill "email" with "bob@x"
And I press "Login"
```

✅ Instead: `When Bob logs in`.

## Conjunction step

```gherkin
# ❌ Wrong
Given I have shades and a brand new Mustang
```

✅ Instead: `Given I have shades` then `And I have a brand new Mustang`.

## Same text under two keywords

```gherkin
# ❌ Wrong
Given there is money in my account
Then there is money in my account
```

✅ Instead: `Then my account balance is 10`.

## Two Backgrounds or two Features

A Feature or Rule with two Backgrounds, or a file with two Features, fails to parse.
✅ Instead: split into more Rules or one file per capability.

## Colon after a keyword

`Given:` makes Cucumber ignore the tests. ✅ Instead: `Given a visitor without a name`.

## Invented Examples rows

An Outline row the spec does not list is behaviour nobody approved.
✅ Instead: a plain `Scenario` for the written case and a question for the others.
