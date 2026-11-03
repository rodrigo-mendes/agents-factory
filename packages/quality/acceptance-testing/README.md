# acceptance-testing

Generic, stack-agnostic authoring of **acceptance tests from OpenSpec specs**: Gherkin `.feature` files
derived from a spec or a change delta, tagged for traceability, and checked by script. Nothing here runs
tests and nothing assumes a language or framework.

Depends on `factory-core` (factory rules and frontmatter conventions that the skill, rule and agent follow) and `openspec-core` (the OpenSpec 1.15 skill that defines the spec format).

## Contents

| Artifact | Path under `.apm/` | Role |
|---|---|---|
| Skill `deriving-gherkin-from-openspec-v1-15` (knowledge, auto-invocable) | `skills/deriving-gherkin-from-openspec-v1-15/` | mapping spec to Gherkin, style rules, questions, traceability, worked example |
| Script `check_feature_coverage.py` | `skills/deriving-gherkin-from-openspec-v1-15/scripts/` | stdlib coverage check spec vs features; tests in `scripts/tests/` |
| Rule `gherkin-feature-authoring` | `instructions/gherkin-feature-authoring.instructions.md` | scoped to `**/*.feature`: declarative steps, mandatory tags, Always / Ask First / Never / Verify |
| Agent `acceptance-test-reviewer` | `agents/acceptance-test-reviewer.agent.md` | read-only, `model: sonnet`; returns one review record with the traceability matrix |

## Scope

- Derive `.feature` files from OpenSpec 1.15 specs and deltas.
- Tag every scenario with its requirement (`@R<n>` or `@req-<slug>`) and, when generating from a change delta, the change (`@change-<id>`; none for a spec root).
- Review features against the spec and, optionally, against step definitions.

## Out of scope

- Running the tests (Cucumber runners, Quarkus wiring): belongs to the package `quarkus-acceptance-testing`.
- Wiring into the SaaS orchestrator flow: deferred.
- Writing the spec itself: OpenSpec skill in `openspec-core`.

## How to use

Coverage check (paths as installed under `.claude/skills/`):

```bash
python .claude/skills/deriving-gherkin-from-openspec-v1-15/scripts/check_feature_coverage.py --spec-root openspec --features src/test/resources/features
python .claude/skills/deriving-gherkin-from-openspec-v1-15/scripts/check_feature_coverage.py --spec-root openspec --features src/test/resources/features --change <id> --strict
```

Exit codes: 0 complete, 1 gaps, 2 nothing found, 3 usage error. Add `--json` for machine output.
Self-test: `python -m unittest discover -s .claude/skills/deriving-gherkin-from-openspec-v1-15/scripts/tests`.

Review: launch `acceptance-test-reviewer` with a change id or spec root plus the features directory
(and optionally the step-definition directory).

## Versions

OpenSpec 1.15, Gherkin parser cucumber/gherkin 42 (research date 2026-11-01). Tags `(unverified)` and
`(medium confidence)` in the skill apply.

## Provenance

Research and decisions: `workspace/software-quality/` (family facts, family rules, research files). The
shipped artifacts do not read that folder.
