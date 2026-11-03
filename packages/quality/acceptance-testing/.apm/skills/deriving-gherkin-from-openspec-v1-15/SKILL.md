---
name: deriving-gherkin-from-openspec-v1-15
description: "Derive Gherkin .feature files from OpenSpec 1.15 specs and change deltas, with R-id and change tags and a coverage script. Use when turning a spec.md or a delta into Cucumber features. Not for step definitions, Cucumber runners or writing the spec itself."
---

# Deriving Gherkin from OpenSpec 1.15

> Version lock: OpenSpec **1.15.0** specs and the Gherkin language as parsed by **cucumber/gherkin 42.0.1**. Research date **2026-11-01**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; see the [register](./blueprints/unverified-and-risks.md).
> OpenSpec has no official Gherkin tooling; the mapping below is a factory design built on official grammar facts.

## Version Context

| Item | Value | Source (fetched 2026-11-01) |
|---|---|---|
| Gherkin parser | cucumber/gherkin 42.0.1 (2026-08-05); Python package `gherkin-official` 42.0.1 | https://pypi.org/project/gherkin-official/ |
| Gherkin keywords | Feature, Rule, Background (one per Feature or Rule), Scenario/Example, Scenario Outline + Examples, Given/When/Then/And/But, tags | https://cucumber.io/docs/gherkin/reference |
| OpenSpec | 1.15.0 (release page shows "24 Oct" only: year 2026 is (medium confidence)) | https://github.com/Fission-AI/OpenSpec/releases/tag/v1.15.0 |
| Requirement and scenario format | `### Requirement:` with SHALL/MUST, `#### Scenario:` (four `#`), delta sections | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml |
| Step bullets, bold form | `**GIVEN**` (optional), `**WHEN**`, `**THEN**`, `**AND**` | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md |
| Step bullets, plain form | `- GIVEN`, `- WHEN`, `- THEN`, `- AND` | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md |
| Official OpenSpec to Gherkin tool | none: issues #508 and #987 closed as not planned | https://github.com/Fission-AI/OpenSpec/issues/508 |
| `R<n>` ids and `R<n>_<scenario>_<expectation>` test names | factory convention F11, not OpenSpec | factory SaaS functional-spec convention (factory convention F11) |

**Version-lifetime risk** (as of 2026-11-01; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- OpenSpec 1.15.0 is recent and the three official texts already disagree on GIVEN; re-read the conventions spec before trusting a newer release.
- `gherkin-official` Python floor differs between PyPI (3.10) and the main branch (3.11).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Mapping table, deltas, file layout](./blueprints/mapping-and-deltas.md)
- [Gherkin style rules and anti-patterns](./blueprints/gherkin-style.md)
- [Questions and traceability table](./blueprints/questions-and-traceability.md)
- [Worked example: spec.md to .feature](./blueprints/worked-example.md)
- [Always-do patterns](./blueprints/always-do-patterns.md)
- [Never-do patterns](./blueprints/never-do-patterns.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

Scope split: running the features is `testing-quarkus-cucumber-v8-0`; test types and mocks are in `developing-quarkus-junit-v3-40`;
writing the spec is the OpenSpec skill `specifying-changes-with-openspec-v1-15`. This skill only turns a spec into `.feature` text and proves coverage.

## Blueprints & Guardrails

Flow: read the spec (or the delta of one change), apply the [mapping](./blueprints/mapping-and-deltas.md), write
`src/test/resources/features/<capability>.feature`, list unanswered preconditions as numbered questions, run the coverage script.

### ✅ Always Do

- **Write one `.feature` per capability with one `Feature:`** — Gherkin allows one Feature per file ([Gherkin reference](https://cucumber.io/docs/gherkin/reference)).
- **Turn each `### Requirement:` into one `Rule:`** — a Rule represents one business rule and groups its examples ([Gherkin reference](https://cucumber.io/docs/gherkin/reference)).
- **Turn each `#### Scenario:` into one `Scenario:` under its Rule** — OpenSpec says each scenario should be usable as a test case ([schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)).
- **Write `Given` only when the spec writes GIVEN** — GIVEN is optional in OpenSpec ([conventions spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md)). See [patterns](./blueprints/always-do-patterns.md#givens-and-questions).
- **Accept bold and plain step keywords when reading a spec** — the conventions spec uses bold, `docs/concepts.md` uses plain ([concepts.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md)).
- **Tag each Rule `@R<n>` (or `@req-<slug>`) and, for a change delta, each Feature `@change-<id>` (none for a spec root), relying on tag inheritance** — tags above Feature are inherited by Rule, Scenario and Examples ([Cucumber API tags](https://cucumber.io/docs/cucumber/api/)). See [tags](./blueprints/mapping-and-deltas.md#tags).
- **Place tags only above Feature, Rule, Scenario, Scenario Outline or Examples** — tags above Background or steps are not possible ([Cucumber API tags](https://cucumber.io/docs/cucumber/api/)).
- **Use `Scenario Outline` only for variants the spec lists** — an Outline runs once per Examples row ([Gherkin reference](https://cucumber.io/docs/gherkin/reference)).
- **Write declarative steps that describe behaviour** — imperative steps are tied to UI mechanics ([Better Gherkin](https://cucumber.io/docs/bdd/better-gherkin)). See [style](./blueprints/gherkin-style.md).
- **Parse every generated feature with the official parser** — an extra colon after a keyword makes Cucumber ignore the tests ([Gherkin reference](https://cucumber.io/docs/gherkin/reference)). See [patterns](./blueprints/always-do-patterns.md#verification-loop).
- **Run the coverage script before reporting done** — traceability is checked by script, never estimated (factory convention F11).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Delta handling (medium confidence) | Generate from the change delta only (change-scoped review) vs regenerate from merged `openspec/specs/` (single truth). `--change` checks the merged base plus the delta, so untouched base requirements without features are reported MISSING: generate them or exclude them | "Are features produced per change or from the merged specs?" |
| Missing precondition | A numbered question vs no `Given` at all | "Q1: does R1 require an authenticated caller? The spec does not say." |
| Rule-level Background | Repeated `Given` (1:1 trace to spec bullets, default) vs one Background when every scenario of a requirement states the same GIVEN | "The spec repeats the same GIVEN in every scenario of R2: use a Background?" |
| Spoken language | English keywords vs `# language:` matching the spec text | "Is the spec written in English?" |
| Markdown Gherkin (`.feature.md`) | Plain `.feature` (default) vs `.feature.md` (JS and Java tooling only, Python support (unverified)) | "Does the team need `.feature.md`?" |
| Requirement without R-id | `@req-<slug>` tag vs adding R-ids to the spec | "May the requirement ids be added to the spec first?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Invent a `Given` the spec does not state ([conventions spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md)) | Omit it and add a numbered question |
| Put a tag above `Background:` or a step ([Cucumber API tags](https://cucumber.io/docs/cucumber/api/)) | Tag the `Rule:` or `Scenario:` |
| Write imperative UI steps such as filling fields and pressing buttons ([Better Gherkin](https://cucumber.io/docs/bdd/better-gherkin)) | `When Bob logs in` |
| Join two facts in one step ([anti-patterns](https://cucumber.io/docs/guides/anti-patterns/)) | One step per fact, continued with `And` |
| Use the same step text under two keywords ([Gherkin reference](https://cucumber.io/docs/gherkin/reference)) | Rephrase the `Then` as an observable outcome |
| Declare two Backgrounds in one Feature or Rule, or two Features in a file ([Gherkin reference](https://cucumber.io/docs/gherkin/reference)) | Split into more Rules or more files |
| Put a colon after `Given`, `When`, `Then`, `And` or `But` ([Gherkin reference](https://cucumber.io/docs/gherkin/reference)) | `Given a visitor without a name` |
| Invent Examples rows the spec does not list ([conventions spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md)) | Plain `Scenario`, or a question |
| Replace or rewrite `spec.md` with Gherkin, or invent a scenario for a requirement that has none ([mapping](./blueprints/mapping-and-deltas.md#file-layout); OpenSpec [#508](https://github.com/Fission-AI/OpenSpec/issues/508) closed not planned, F10) | Keep `spec.md` canonical, write the `.feature` beside the tests, ask a numbered question |

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Feature file path | `src/test/resources/features/<capability>.feature` | factory convention F11 |
| Rule header | `Rule: R<n> <title>` above it `@R<n>` | https://cucumber.io/docs/gherkin/reference |
| Change tag | `@change-<id>` on the Feature when generating from a change delta; none for a spec root | https://cucumber.io/docs/cucumber/api/ |
| Step regex for specs | `^\s*[-*+]\s+(?:\*\*)?(GIVEN\|WHEN\|THEN\|AND)(?:\*\*)?\s+(.*)$` (the escaped pipes are the regex alternation) | https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md |
| Requirement without scenarios | reported as EMPTY (`empty_requirements`, reason `no-scenarios`), exit 1; becomes a numbered question to the spec owner, never an invented scenario | skill script |
| Coverage | `python <skill>/scripts/check_feature_coverage.py --spec-root openspec --features src/test/resources/features` | skill script |
| Coverage with delta | add `--change <id>`; add `--strict` for the parser check; `--json` for machine output | skill script |
| Exit codes | 0 complete, 1 gaps, 2 nothing found, 3 usage error | skill script |
| Self-test | `python -m unittest discover -s <skill>/scripts/tests` | skill script |

## External Resources

All fetched 2026-11-01.

- [Gherkin reference](https://cucumber.io/docs/gherkin/reference)
- [OpenSpec 1.15.0 schema](https://github.com/Fission-AI/OpenSpec/blob/v1.15.0/schemas/spec-driven/schema.yaml)
- [cucumber/gherkin releases](https://github.com/cucumber/gherkin/releases)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
