---
name: gherkin-feature-authoring
description: "Rules for writing Gherkin .feature files derived from OpenSpec specs: declarative steps, mandatory requirement tags (change tag for deltas), no invented Given. Use when creating or editing a .feature file."
paths:
  - "**/*.feature"
---

# Gherkin feature authoring

Features are derived from the OpenSpec spec, never invented. Facts, mapping and examples live in the
skill `deriving-gherkin-from-openspec-v1-15`; this rule only states what to do. Tags `(unverified)` and
`(medium confidence)` from that skill apply.

## Rules

- Steps are declarative: they describe behaviour, not mechanics.
- One behaviour per scenario.
- Tag every scenario (directly or through Rule/Feature inheritance) with `@R<n>` or `@req-<slug>`. Add `@change-<id>` only when generating from a change delta, and then it is required; for a spec root no change tag.
- `Given` comes only from what the spec states. A missing precondition becomes a numbered question.
- No HTTP, UI or SQL detail in steps (no verbs, paths, status codes, selectors, queries).
- `Background` only for preconditions shared by all scenarios of its scope.
- `Scenario Outline` only for variants the spec lists; do not invent Examples rows.

## Skills

| Need | Skill |
|---|---|
| Spec to Gherkin mapping, style, deltas, questions, traceability | `deriving-gherkin-from-openspec-v1-15` |
| Spec format and delta sections | `specifying-changes-with-openspec-v1-15` |

## Always Do

- Read the spec (or the change delta) before writing a step.
- Keep one `Feature:` per file, one `Rule:` per requirement, one `Scenario:` per spec scenario.
- Raise unanswered preconditions as numbered questions.

## Ask First

- Whether features are produced per change or from the merged specs.
- Whether to use a `Background` when every scenario of a requirement repeats the same GIVEN.
- Whether a requirement without an R-id may get one before using `@req-<slug>`.

## Never Do

| Do not | Do instead |
|---|---|
| Invent a `Given` or behaviour the spec does not state | Omit it and add a numbered question |
| Write imperative UI, HTTP or SQL steps | State the observable behaviour |
| Leave a scenario without its requirement tag (or a delta feature without `@change-<id>`) | Add `@R<n>`/`@req-<slug>` (and `@change-<id>` for a delta) |
| Use an Outline for variants the spec does not list | Plain Scenario, or a question |

## Verify

Run the coverage script from the skill and fix every gap before reporting done:

```bash
python .claude/skills/deriving-gherkin-from-openspec-v1-15/scripts/check_feature_coverage.py --spec-root openspec --features <features dir>
```

Add `--change <id>` for a delta and `--strict` for the parser check. Exit 0 means complete.
