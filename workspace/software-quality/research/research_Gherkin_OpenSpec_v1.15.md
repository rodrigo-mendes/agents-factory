# Research: Gherkin (cucumber/gherkin v42) derived from OpenSpec 1.15.0 specs

Unit: `deriving-gherkin-from-openspec-v1-15` (U3, software-quality family). Produced by
framework-researcher on 2026-11-01 from the brief
`workspace/software-quality/execution-1/briefs/P4-research-deriving-gherkin-from-openspec-v1-15.md`.
Family facts F9, F10, F11 and family rules 1, 2, 5, 6 applied as given.

Note on layout: the brief requires the file to end with the Source Bibliography, so the
template's Source Bibliography section is moved to the end (after Research Gaps, Iteration
Changelog, Completion Checklist and Agent Operation Notes). No other template section was dropped.

---

## Metadata

```yaml
Full_Name: Gherkin language (Cucumber) + cucumber/gherkin parser, mapped from OpenSpec spec-driven schema
Target_Version: gherkin parser 42.0.1 (Gherkin reference page of 2026-10-27); OpenSpec 1.15.0
Release_Date: gherkin 42.0.1 = 2026-08-05 (PyPI); OpenSpec v1.15.0 = 24 Oct (GitHub release page shows no year; 2026 from repo context, medium confidence)
Support_Status: Active (both)
Primary_Docs: https://cucumber.io/docs/gherkin/reference ; https://github.com/Fission-AI/OpenSpec/blob/v1.15.0/schemas/spec-driven/schema.yaml
Official_Repo: https://github.com/cucumber/gherkin ; https://github.com/Fission-AI/OpenSpec
Research_Date: 2026-11-01
Domain_Complexity: Standard
Research_Depth: exhaustive (no section-investigators, no plan mode, per brief)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 3 of 5
Triangulated_Count: 9
Unverified_Count: 3
Irresolvable_Count: 2
Research_Quality_Score: 91%   # (57 claims - 3 unverified - 2 irresolvable) / 57
```

---

## Executive Summary

Gherkin is Cucumber's plain-text language for executable examples: one `Feature` per `.feature`
file, optional `Rule` blocks (since Gherkin 6) that group the examples of one business rule, an
optional `Background` per Feature or per Rule, `Scenario`/`Example` with Given/When/Then/And/But
steps, `Scenario Outline` with one or more `Examples` tables, tags inherited downwards
(Feature -> Rule -> Scenario/Outline -> Examples), data tables, doc strings with an optional content
type, `#` line comments, free-form descriptions and `# language:` for 70+ spoken languages
(https://cucumber.io/docs/gherkin/reference, read 2026-11-01). The parser is `cucumber/gherkin`
v42.0.1; v42.0.0 allows a step to carry both a DocString and a DataTable
(https://github.com/cucumber/gherkin/releases, read 2026-11-01). The Python package
`gherkin-official` 42.0.1 exposes `Parser` and `Compiler` and is the recommended validator for a
coverage script.

OpenSpec 1.15.0 specs are Markdown: `### Requirement: <name>` with SHALL/MUST, one or more
`#### Scenario: <name>` (exactly four `#`) with WHEN/THEN steps; delta specs live in
`openspec/changes/<id>/specs/<capability>/spec.md` under `## ADDED|MODIFIED|REMOVED|RENAMED
Requirements` and are merged at archive in the order RENAMED, REMOVED, MODIFIED, ADDED. The three
official texts disagree on GIVEN: the schema instruction shows only WHEN/THEN, the conventions
spec allows bold `**GIVEN**` (optional), and `docs/concepts.md` shows plain (non-bold)
`- GIVEN`/`- WHEN`/`- THEN`/`- AND`. A deriver must therefore accept GIVEN in both forms and never
require it (family rule 6).

OpenSpec has no official Gherkin converter: issues #508 and #987 were closed "not planned" on
2026-08-06 and moved to Discussions; the maintainers rejected Gherkin syntax inside specs as too
verbose. One unofficial tool (bddfirst, 0 stars, no release) exists and is rejected as a source.
The mapping in this document (capability -> Feature, Requirement -> Rule, Scenario -> Scenario,
WHEN/THEN/AND -> When/Then/And, GIVEN -> Given only when written, `@R<n>` + `@change-<id>` tags)
is therefore a factory design built on official grammar facts, not an OpenSpec feature. Tier
Standard: two well-documented formats, but the mapping itself is a design with no upstream owner.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**A1. One `.feature` file per OpenSpec capability, one `Feature:` per file**
> Confidence: 🟢 High | ✓✓ Triangulated | Gherkin reference (2026-11-01) + OpenSpec concepts.md v1.15.0 (2026-11-01)
- Why: Gherkin allows only one `Feature` per `.feature` file; OpenSpec has one `spec.md` per capability (`openspec/specs/<capability>/spec.md`). One-to-one keeps file names traceable.
- Code:
  ```gherkin
  # source: openspec/specs/items/spec.md
  @capability-items
  Feature: items
  ```
- Source: https://cucumber.io/docs/gherkin/reference (2026-11-01); https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md (2026-11-01)

**A2. Each `### Requirement:` becomes one `Rule:`**
> Confidence: 🟢 High | ✓✓ Triangulated | Gherkin reference (2026-11-01) + cucumber.io/docs/bdd/example-mapping (2026-11-01)
- Why: Gherkin `Rule` "represents one business rule" and groups the examples that illustrate it; OpenSpec requires one behavior per requirement with at least one scenario (schema.yaml v1.15.0). Example Mapping places examples under the rule they illustrate.
- Code:
  ```gherkin
  @R1
  Rule: R1 List items of the tenant
    The system SHALL return only the items of the caller's tenant.
  ```
- Source: Gherkin reference; https://cucumber.io/docs/bdd/example-mapping (2026-11-01); schema.yaml v1.15.0 (2026-11-01)

**A3. Each `#### Scenario:` becomes one `Scenario:` under its Rule, keeping the scenario name verbatim**
> Confidence: 🟢 High | ✓✓ Triangulated | schema.yaml v1.15.0 + openspec-conventions spec v1.15.0 (2026-11-01)
- Why: OpenSpec says each scenario "should be usable as a test case" (schema) and "testable or explicitly verifiable" (conventions). Keeping the name makes `R<n>_<scenario>_<expectation>` test names derivable (F11).
- Source: https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml ; https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md (2026-11-01)

**A4. Step mapping is literal: WHEN -> When, THEN -> Then, AND -> And (continuing the previous kind), GIVEN -> Given only when the spec writes GIVEN**
> Confidence: 🟢 High | ✓✓ Triangulated | Gherkin reference (2026-11-01) + openspec-conventions spec + docs/concepts.md v1.15.0 (2026-11-01)
- Why: Gherkin `And`/`But` continue the preceding step type; OpenSpec AND follows WHEN or THEN the same way. GIVEN is optional in OpenSpec (conventions spec) and absent from the schema example, so a precondition that is not written is not invented (family rule 6: it becomes a numbered question).
- Code: see Implementation Blueprint.
- Source: as above.

**A5. Accept both bold (`**WHEN**`) and plain (`WHEN`) step keywords when parsing a spec**
> Confidence: 🟢 High | ✓✓ Triangulated | openspec-conventions spec (bold) + docs/concepts.md (plain), both v1.15.0 (2026-11-01)
- Why: the two official texts differ; a parser that only matches bold silently drops steps from specs written after concepts.md.
- Code: regex `^\s*[-*+]\s+(?:\*\*)?(GIVEN|WHEN|THEN|AND)(?:\*\*)?\s+(.*)$`
- Source: as above.

**A6. Tag every Rule with `@R<n>` (or `@req-<slug>`) and every Feature produced from a change with `@change-<id>`; rely on tag inheritance**
> Confidence: 🟢 High | ✓✓ Triangulated | cucumber.io/docs/cucumber/api tags (2026-11-01) + cucumber/gherkin README pickles (2026-11-01)
- Why: tags above Feature are inherited by Rule, Scenario, Scenario Outline and Examples; the compiler copies inherited tags into each pickle, so a coverage script reads them per pickle. The tag values themselves are factory convention (F11, family rule 5).
- Code:
  ```gherkin
  @change-list-tenant-items
  Feature: items
    @R1
    Rule: R1 List items of the tenant
      Scenario: empty tenant
  ```
- Source: https://cucumber.io/docs/cucumber/api/ (2026-11-01); https://raw.githubusercontent.com/cucumber/gherkin/main/README.md (2026-11-01)

**A7. Place tags only above Feature, Rule, Scenario, Scenario Outline or Examples**
> Confidence: 🟢 High | ✓✓ Triangulated | cucumber.io/docs/cucumber/api (2026-11-01) + Gherkin reference (2026-11-01)
- Why: "It is not possible to place tags above Background or steps."
- Source: as above.

**A8. Use `Scenario Outline` + `Examples` only when the spec itself lists variants of one scenario (sub-bullets or a table of values)**
> Confidence: 🟢 High | ✓✓ Triangulated | Gherkin reference (2026-11-01) + openspec-conventions spec (sub-bullets add examples) (2026-11-01)
- Why: an Outline runs once per Examples row and must have one or more Examples sections; OpenSpec sub-bullets "add examples or specifics". Variants not listed in the spec are invented behaviour.
- Source: as above.

**A9. Write steps declaratively (behaviour, not UI mechanics); a Then checks an observable outcome**
> Confidence: 🟢 High | ✓✓ Triangulated | cucumber.io/docs/bdd/better-gherkin (2026-11-01) + Gherkin reference (2026-11-01) + OpenSpec conventions (externally observable) (2026-11-01)
- Why: imperative steps are "closely tied to the mechanics of the current UI"; Then outcomes should be observable, not internal state such as database records; OpenSpec behavioural requirements "stay externally observable".
- Source: as above.

**A10. Validate every generated `.feature` with the official parser before committing**
> Confidence: 🟢 High | ✓✓ Triangulated | cucumber/gherkin README (Python API) + PyPI gherkin-official 42.0.1 (2026-11-01)
- Why: an extra colon after a keyword that takes none makes Cucumber ignore the tests (reference); the parser raises `CompositeParserException` (list of `ParserException` with `location`).
- Source: https://raw.githubusercontent.com/cucumber/gherkin/main/README.md ; https://pypi.org/project/gherkin-official/ ; https://raw.githubusercontent.com/cucumber/gherkin/main/python/src/gherkin/errors.py (2026-11-01)

### ⚠️ Conditional Patterns

**C1. Background at Rule level vs repeated Given**
> Confidence: 🟢 High (grammar) / 🟡 Medium (when to use)
- Options: (a) `Background` inside the Rule when every scenario of the requirement states the same GIVEN; (b) repeat `Given` per scenario.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Rule Background | brevity | per-scenario readability | all scenarios share an identical written GIVEN |
  | Repeated Given | 1:1 trace to spec bullets | brevity | GIVENs differ or only some scenarios have one |

- Agent: "Ask user only if the spec repeats an identical GIVEN in every scenario of a requirement; default is repeated Given."
- Source: Gherkin reference — one Background per Feature or Rule, keep it under about four lines (2026-11-01)

**C2. Handling deltas (`openspec/changes/<id>/specs/...`)**
> Confidence: 🟡 Medium (design; archive semantics are 🟢 High)
- Options: ADDED -> new Rule; MODIFIED -> regenerate the whole Rule (the delta repeats the full block); REMOVED -> delete the Rule and its scenarios; RENAMED -> rename Rule title and keep its `@R<n>` tag.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Generate from change delta only | change-scoped review | full-feature view | before archive |
  | Regenerate from merged `openspec/specs/` | single truth | change scoping | after archive |

- Agent: "Ask user whether features are produced per change (tag `@change-<id>`) or from merged specs."
- Source: openspec-conventions spec v1.15.0 (archive order RENAMED, REMOVED, MODIFIED, ADDED); docs/concepts.md v1.15.0 (2026-11-01)

**C3. Spoken language of the feature file**
> Confidence: 🟢 High
- Options: English keywords; or `# language: <code>` matching the language of the spec text.
- Agent: "Ask user if the spec is not in English." Reference advises using the language of the domain experts and not translating.
- Source: Gherkin reference (2026-11-01)

**C4. Markdown Gherkin (`.feature.md`)**
> Confidence: 🟡 Medium
- gherkin-utils can convert `.feature` <-> `.feature.md` and the JS parser offers `GherkinInMarkdownTokenMatcher`; Python support for Markdown Gherkin is (unverified). Default: plain `.feature`.
- Source: https://github.com/cucumber/gherkin-utils ; cucumber/gherkin README (2026-11-01)

### 🚫 Forbidden Patterns

**N1. Inventing a Given that the spec does not state**
> Severity: High
> Confidence: 🟢 High
- Why: OpenSpec GIVEN is optional; the schema example has none (family rule 6).
- Impact: the feature asserts behaviour nobody approved.
- ❌ Wrong:
  ```gherkin
  Scenario: empty tenant
    Given the user is logged in as admin
    When the user lists items
  ```
- ✅ Correct:
  ```gherkin
  Scenario: empty tenant
    When the user lists items
    Then an empty list is returned
  # QUESTION Q1: does R1 require an authenticated caller? (not stated in spec)
  ```
- Source: schema.yaml + openspec-conventions spec v1.15.0 (2026-11-01)

**N2. Tags above Background or steps**
> Severity: Medium
> Confidence: 🟢 High
- ❌ Wrong: `@R1` on the line above `Background:`
- ✅ Correct: `@R1` above `Rule:`
- Source: https://cucumber.io/docs/cucumber/api/ (2026-11-01)

**N3. Imperative UI steps**
> Severity: Medium
> Confidence: 🟢 High
- ❌ Wrong: `When I fill "email" with "bob@x" And I press "Login"`
- ✅ Correct: `When Bob logs in`
- Source: https://cucumber.io/docs/bdd/better-gherkin (2026-11-01)

**N4. Conjunction steps**
> Severity: Medium
> Confidence: 🟢 High
- ❌ Wrong: `Given I have shades and a brand new Mustang`
- ✅ Correct: `Given I have shades` / `And I have a brand new Mustang`
- Source: https://cucumber.io/docs/guides/anti-patterns/ (2026-11-01)

**N5. Same step text under two keywords**
> Severity: Medium
> Confidence: 🟢 High
- Why: keywords are ignored when matching step definitions.
- ❌ Wrong: `Given there is money in my account` and `Then there is money in my account`
- ✅ Correct: `Then my account balance is 10`
- Source: Gherkin reference (2026-11-01)

**N6. Two Backgrounds in one Feature or one Rule; more than one Feature per file**
> Severity: High (parse error)
> Confidence: 🟢 High
- ✅ Correct: split into more Rules or Features.
- Source: Gherkin reference (2026-11-01)

**N7. Colon after a keyword that takes none (e.g. `Given:`)**
> Severity: High
> Confidence: 🟢 High
- Impact: tests are ignored.
- Source: Gherkin reference (2026-11-01)

**N8. Writing Gherkin syntax into OpenSpec `spec.md` or replacing spec.md with `.feature` files**
> Severity: High
> Confidence: 🟡 Medium (maintainer statement + community report, not docs)
- Why: the CLI handles only `.md` spec artifacts and validation expects Markdown delta headers (issue #508 comments; open issue #2115).
- ✅ Correct: keep spec.md canonical, derive `.feature` beside it.
- Source: https://github.com/Fission-AI/OpenSpec/issues/508 ; https://github.com/Fission-AI/OpenSpec/issues?q=gherkin (2026-11-01)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://github.com/cucumber/gherkin/releases (2026-11-01) + https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/CHANGELOG.md (2026-11-01, partial read: first 100000 of 214158 chars)

**Breaking Changes (gherkin)**: v42.0.0 Ruby 3.3, C++ cmate removed, DocString + DataTable allowed on one step, Persian Rule; v41 PHP 8.4, JS namespace imports removed; v40 JS ESM; v39.1 Python 3.9 dropped; v38 Java release 17; v37 messages v31+, `location` on Pickle.

**OpenSpec 1.13–1.15 parser changes relevant to a deriver** ⚠️ Migration Note: REMOVED/RENAMED accept `*` and `+` bullets; repeated delta headers are all applied; closing `#` runs in requirement headings ignored; unpaired FROM/TO is an error; requirements over 500 chars warn under `--strict`; bare scenario header rejected; `/opsx:verify` matches REMOVED by exact name (1.15.0); `show --json` includes requirement and scenario names (1.14).

**Upgrade Steps**: 1. `pip install gherkin-official==42.0.1`; 2. re-parse all features; 3. use `openspec show <capability> --json` (1.14+) as an alternative input source (exact JSON shape unverified).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| gherkin-official (Python) | 42.0.1 | 42.x | PyPI: Python >=3.10; main pyproject says >=3.11 (post-release change, use 3.11+) |
| io.cucumber:gherkin (Java) | 42.0.1 | 42.x | Java 17 since v38 |
| @cucumber/gherkin-utils / io.cucumber:gherkin-utils | 9.0.0 | — | release date unverified |
| OpenSpec | 1.15.0 | 1.15.x | pinned |

---

## Implementation Blueprint

> Confidence: 🟢 High (grammar and parser API) | 🟡 Medium (mapping is a factory design)

**Mapping table**

| OpenSpec 1.15 element | Gherkin element | Rule |
|---|---|---|
| `openspec/specs/<cap>/spec.md` or `openspec/changes/<id>/specs/<cap>/spec.md` | one `.feature`, `Feature: <cap>` | A1 |
| `## Purpose` | Feature description | free text allowed under Feature |
| `### Requirement: R<n> <title>` + SHALL text | `@R<n>` `Rule: R<n> <title>` + description | A2, A6 |
| `#### Scenario: <name>` | `Scenario: <name>` | A3 |
| `GIVEN` / `**GIVEN**` | `Given` (only if written) | A4, N1 |
| `WHEN` / `**WHEN**` | `When` | A4 |
| `THEN` / `**THEN**` | `Then` | A4 |
| `AND` / `**AND**` | `And` | A4 |
| sub-bullets listing value variants | `Scenario Outline` + `Examples` | A8 |
| change id | `@change-<id>` on Feature | A6 |
| ADDED/MODIFIED/REMOVED/RENAMED | add / regenerate / delete / retitle Rule | C2 |

**Integration**: OpenSpec spec.md -> `.feature`
```markdown
### Requirement: R1 List items of the tenant
The system SHALL return only the items of the caller's tenant.

#### Scenario: empty tenant
- **WHEN** the caller lists items
- **THEN** an empty list is returned
- **AND** the status is 200
```
```gherkin
@change-list-tenant-items
Feature: items

  @R1
  Rule: R1 List items of the tenant
    The system SHALL return only the items of the caller's tenant.

    Scenario: empty tenant
      When the caller lists items
      Then an empty list is returned
      And the status is 200
```

**Validation + traceability (Python, gherkin-official 42.0.1)**
```python
# Representative — API from cucumber/gherkin README; exceptions from python/src/gherkin/errors.py
import sys, pathlib
from gherkin import Parser, Compiler
from gherkin.errors import CompositeParserException

tags_seen = set()
for path in pathlib.Path(sys.argv[1]).rglob("*.feature"):
    try:
        doc = Parser().parse(path.read_text(encoding="utf-8"))
    except CompositeParserException as e:
        for err in e.errors:
            print(f"{path}: {err}")
        sys.exit(1)
    doc["uri"] = str(path)
    for pickle in Compiler().compile(doc):   # inherited tags are in each pickle
        names = {t["name"] for t in pickle["tags"]}
        if not any(n.startswith("@R") or n.startswith("@req-") for n in names):
            print(f"untraced scenario: {pickle['name']} ({path})"); sys.exit(1)
        tags_seen |= names
print(sorted(tags_seen))
```
Pickle dict key names (`tags`, `name`) follow the README message description (medium confidence for the Python dict shape).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
python -m pip install gherkin-official==42.0.1
python scripts/check_features.py features/          # exit 0, prints tag set
npx @cucumber/gherkin-utils format features/**/*.feature   # normalizes formatting
grep -c "^#### Scenario:" openspec/specs/items/spec.md     # must equal Scenario count in items.feature
grep -cE "^\s*(Scenario|Scenario Outline):" features/items.feature
```

**Mocking**: not applicable (running features is out of scope: testing-quarkus-cucumber-v8-0).

---

## Production Readiness

- **Performance**: parser v39.1 added speed optimizations; not a concern at spec scale.
- **Scalability**: one file per capability; Rules keep large capabilities navigable.
- **Monitoring**: coverage script fails CI when a requirement has no tagged scenario (family rule 5).
- **Security**: gherkin v39.0.0 fixed hidden-file reading in Python `Parser.parse`; pin >= 42.0.1.

---

## Reference Implementations

- cucumber/gherkin testdata (`testdata/good/*.feature`) — official grammar examples.
- Gherkin reference examples (Rule, Background, Outline) — https://cucumber.io/docs/gherkin/reference
- Community, not used as evidence: bddfirst (`@spec(<capability>#<requirement>)` tags, `generate`/`coverage`), 0 stars, no release, MIT.

---

## Research Gaps

```
Gap: Exact JSON shape of `openspec show --json` requirement/scenario output in 1.15.0
Impact: alternative input path for the deriver cannot be specified
Workaround: parse spec.md Markdown directly (A5 regex)
Follow-up: docs/cli.md at tag v1.15.0
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: Python support for Markdown-with-Gherkin (GherkinInMarkdownTokenMatcher equivalent)
Impact: C4 limited to JS/Java
Workaround: use plain .feature
Follow-up: cucumber/gherkin python/src/gherkin
§7-ref: Iteration 3 — IRRESOLVABLE
```
```
Gap: gherkin-utils 9.0.0 release date (unverified); OpenSpec v1.15.0 release year (page shows "24 Oct" only; medium confidence 2026)
Impact: low
Workaround: pin versions
Follow-up: Maven Central metadata / npm
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Guardrails | GIVEN conflict docs vs schema | Resolved: schema WHEN/THEN only; conventions bold GIVEN optional; concepts.md plain GIVEN | schema.yaml, openspec-conventions spec, docs/concepts.md v1.15.0 (2026-11-01) |
| 1 | Guardrails | Official OpenSpec -> Gherkin tooling | Resolved: none; #508, #987 closed not planned 2026-08-06 | github.com/Fission-AI/OpenSpec/issues (2026-11-01) |
| 2 | Blueprint | Python parser API and exceptions | Resolved | cucumber/gherkin README; python/src/gherkin/errors.py (2026-11-01) |
| 2 | Guardrails | Tag inheritance incl. Rule and Examples | Resolved | cucumber.io/docs/cucumber/api (2026-11-01) |
| 3 | Migration | `openspec show --json` shape | ⚠️ IRRESOLVABLE — not in pages read; human verification required | — |
| 3 | Guardrails | Python Markdown Gherkin | ⚠️ IRRESOLVABLE — README shows JS matcher only | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented
- [x] All scope areas cited (1 grammar, 2 BDD guidance, 3 OpenSpec format, 4 mapping, 5 tooling + parser)
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has alternative
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced

---

## Agent Operation Notes

- **High Confidence**: A1–A10, N1–N7.
- **Medium Confidence (validate with user)**: C2 delta handling, C4, N8, Python pickle dict shape.
- **Low Confidence (ask human)**: IRRESOLVABLE items.
- **Edge Cases**: OpenSpec 1.15.0 released about 8 days before research date (<30 days).

---

## DISCREPANCY notes against _family_facts.md

- F10 says scenarios use bold `**WHEN**`/`**THEN**`/`**AND**` and cites schema.yaml. In v1.15.0 the schema instruction example shows only WHEN/THEN (no AND, no GIVEN); the bold form comes from `openspec/specs/openspec-conventions/spec.md` (which also allows optional bold `**GIVEN**`), and `docs/concepts.md` shows plain non-bold `- GIVEN/- WHEN/- THEN/- AND`. Applied as A5 (accept both).
- F9 is consistent (v42.0.1, 2026-08-05). Not in F9: PyPI lists Python >=3.10 for 42.0.1, while `main` pyproject says >=3.11.

---

## Source Bibliography

**Primary**: Gherkin reference, Cucumber API (tags), BDD overview, Example Mapping, Better Gherkin, Anti-patterns (cucumber.io, all "Last updated Oct 27, 2026"); cucumber/gherkin releases, README, Python errors.py, pyproject; PyPI gherkin-official 42.0.1; OpenSpec v1.15.0 schema.yaml, conventions spec, docs/concepts.md, CHANGELOG, release page.
**Validation**: OpenSpec issues #508, #987, issue search "gherkin" (#2115, #2034, #1081, #1077); gherkin-utils repo.
**Rejected (community)**: github.com/cuikexi/bddfirst.

### Pages read

| URL | read on | official | instructions found in page |
|---|---|---|---|
| https://cucumber.io/docs/gherkin/reference | 2026-11-01 | yes | keywords, Rule, Background per Feature/Rule, Outline/Examples, doc strings, tables, i18n, step guidance |
| https://cucumber.io/docs/cucumber/api/ | 2026-11-01 | yes | tag placement, inheritance, tag expressions (partial read: Tags section) |
| https://cucumber.io/docs/bdd/ | 2026-11-01 | yes | discovery, formulation, automation |
| https://cucumber.io/docs/bdd/example-mapping | 2026-11-01 | yes | story/rule/example/question cards |
| https://cucumber.io/docs/bdd/better-gherkin | 2026-11-01 | yes | declarative vs imperative |
| https://cucumber.io/docs/guides/anti-patterns/ | 2026-11-01 | yes | feature-coupled steps, conjunction steps |
| https://github.com/cucumber/gherkin/releases | 2026-11-01 | yes | v36.1–v42.0.1 changes (page 1 of 10 only) |
| https://raw.githubusercontent.com/cucumber/gherkin/main/README.md | 2026-11-01 | yes | Java/JS/Python API, AST vs pickles, CLI |
| https://raw.githubusercontent.com/cucumber/gherkin/main/python/README.md | 2026-11-01 | yes | none (one-line description) |
| https://github.com/cucumber/gherkin/tree/main/python | 2026-11-01 | yes | file listing only |
| https://raw.githubusercontent.com/cucumber/gherkin/main/python/pyproject.toml | 2026-11-01 | yes | version 42.0.1, requires-python >=3.11 (main) |
| https://raw.githubusercontent.com/cucumber/gherkin/main/python/src/gherkin/errors.py | 2026-11-01 | yes | exception classes |
| https://pypi.org/project/gherkin-official/ | 2026-11-01 | yes | 42.0.1, 2026-08-05, Python >=3.10 |
| https://github.com/cucumber/gherkin-utils | 2026-11-01 | yes | format, .feature.md conversion |
| https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml | 2026-11-01 | yes | specs and tasks artifact instructions, delta ops, scenario format |
| https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/openspec-conventions/spec.md | 2026-11-01 | yes | bold GIVEN/WHEN/THEN/AND, delta rules, archive order |
| https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md | 2026-11-01 | yes | plain GIVEN/WHEN/THEN/AND, archive semantics, paths |
| https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/CHANGELOG.md | 2026-11-01 | yes | 1.10–1.15 parser/archive/verify changes (partial: first 100000 of 214158 chars) |
| https://github.com/Fission-AI/OpenSpec/releases/tag/v1.15.0 | 2026-11-01 | yes | title and "24 Oct" date |
| https://github.com/Fission-AI/OpenSpec/issues?q=gherkin | 2026-11-01 | yes | 6 issues, no official tooling |
| https://github.com/Fission-AI/OpenSpec/issues/508 | 2026-11-01 | yes | maintainers rejected Gherkin in specs; closed not planned |
| https://github.com/Fission-AI/OpenSpec/issues/987 | 2026-11-01 | yes | executable specs idea closed not planned |
| https://github.com/cuikexi/bddfirst | 2026-11-01 | no (community) | @spec tag convention; rejected as evidence |
