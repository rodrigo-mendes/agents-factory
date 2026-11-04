# Unverified Register, Risks and Bibliography

Research date 2026-11-01. Back to [SKILL.md](../SKILL.md). Research quality score reported by the research file: 91%. This register lists **3 unverified items (U1-U3), 0 irresolvable items, 4 medium-confidence items (M1-M4), 3 coverage limits (L1-L3)**.

## Contents

- [Tag to register mapping](#tag-to-register-mapping)
- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Source Bibliography](#source-bibliography)

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) Python support for `.feature.md` | SKILL.md Ask First | U1 |
| (medium confidence) delta handling per change vs merged | SKILL.md Ask First; mapping-and-deltas.md | M1 |
| (medium confidence) OpenSpec 1.15.0 release year 2026 | SKILL.md Version Context | M2 |
| (medium confidence) OpenSpec CLI handles Markdown spec artifacts only | mapping-and-deltas.md | M3 |
| (medium confidence) gherkin-official Python floor 3.10 vs 3.11 | always-do-patterns.md | M4 |
| High (shared version facts) | Version Context | family-facts sources in the [bibliography](#source-bibliography) |

## Version-lifetime risk

- OpenSpec 1.15.0 was released about a week before the research date (page shows "24 Oct"); the three official texts disagree on GIVEN (schema shows only WHEN/THEN, conventions spec bold optional GIVEN, concepts.md plain GIVEN). Re-read them before trusting a newer release.
- OpenSpec 1.13 to 1.15 changed parser details relevant to a deriver: REMOVED and RENAMED accept `*` and `+` bullets, repeated delta headers are all applied, an unpaired FROM/TO is an error (High, OpenSpec CHANGELOG, partial read, L2).
- cucumber/gherkin 42.0.0 allows a step with both a DocString and a DataTable; v42 dropped Ruby below 3.3 (High, releases page, L1).
- No official OpenSpec to Gherkin tooling and none planned (issues #508 and #987): the mapping is a factory design and may be overtaken by an upstream feature.

## Unverified items

- U1. Python support for Markdown-with-Gherkin (`.feature.md`): the README shows only a JavaScript token matcher; the Python parser was not checked. Treat as irresolvable until the Python source is read.
- U2. The JSON shape of `openspec show <capability> --json` in 1.15.0 (the CLI doc page for the tag was not read); the skill parses `spec.md` directly instead.
- U3. The coverage script and its unit tests were written without being executed in the authoring session (no shell); run `python -m unittest discover -s <skill>/scripts/tests` first.

## Medium-confidence items

- M1. Delta handling (ADDED new Rule, MODIFIED regenerate, REMOVED delete, RENAMED retitle) is a design on top of the archive semantics (High: archive order RENAMED, REMOVED, MODIFIED, ADDED, conventions spec).
- M2. OpenSpec v1.15.0 release page shows "24 Oct" without a year; 2026 is inferred from repository context.
- M3. The statement that the OpenSpec CLI handles only Markdown spec artifacts comes from a maintainer comment in issue #508 and an open issue, not from documentation.
- M4. `gherkin-official` 42.0.1 on PyPI requires Python 3.10 or newer; the main-branch pyproject says 3.11 or newer (a later change); use 3.11+ when in doubt.

## Coverage limits

- L1. https://github.com/cucumber/gherkin/releases: page 1 of 10 read.
- L2. OpenSpec v1.15.0 CHANGELOG: first 100000 of 214158 characters read.
- L3. https://cucumber.io/docs/cucumber/api/: tags section only.

## Source Bibliography

All fetched 2026-11-01. Provenance: research file for this unit (workspace research, 2026-11-01).

- https://cucumber.io/docs/gherkin/reference
- https://cucumber.io/docs/cucumber/api/
- https://cucumber.io/docs/bdd/better-gherkin
- https://cucumber.io/docs/bdd/example-mapping
- https://cucumber.io/docs/guides/anti-patterns/
- https://github.com/cucumber/gherkin/releases
- https://raw.githubusercontent.com/cucumber/gherkin/main/README.md
- https://pypi.org/project/gherkin-official/
- https://github.com/cucumber/gherkin-utils
- https://github.com/Fission-AI/OpenSpec/blob/v1.15.0/schemas/spec-driven/schema.yaml
- https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml
- https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md
- https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md
- https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/CHANGELOG.md
- https://github.com/Fission-AI/OpenSpec/releases/tag/v1.15.0
- https://github.com/Fission-AI/OpenSpec/issues/508
- https://github.com/Fission-AI/OpenSpec/issues/987
