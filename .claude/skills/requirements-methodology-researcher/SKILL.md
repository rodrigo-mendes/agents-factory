---
name: requirements-methodology-researcher
description: Researches agile/product requirements methodologies (user stories, requirement artifacts) into a source-backed knowledge base. Use when researching requirements practices for a skill.
argument-hint: "<methodology> (e.g. user-stories, BDD)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# INPUT VARIABLES

- `FRAMEWORK_NAME`: [e.g., "Scrum", "SAFe", "Shape Up", "Kanban", "XP", "Dual-Track Agile"]
- `PRACTICE_OR_ARTIFACT_TYPE`: [e.g., "User Stories", "Job Stories", "Epics", "Acceptance Criteria", "Definition of Done", "Story Mapping", "Event Storming"]
- `FRAMEWORK_EDITION`: [e.g., "Scrum Guide 2020", "SAFe 6.0", "Shape Up 2019", "Kanban Guide 2020"]
- `TEAM_CONTEXT`: [e.g., "5-person product team building B2B SaaS", "scaled org with 3 squads under SAFe", "startup pre-product-market fit", "regulated healthcare product team"]
- `OFFICIAL_SOURCE_IF_KNOWN`: [optional — e.g., "https://scrumguides.org", "https://scaledagileframework.com", "https://basecamp.com/shapeup"]
- `INTEGRATION_TOOLS_LIST`: [e.g., "Jira, Confluence, Cucumber/Gherkin, GitHub Issues, Miro"]

---

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier operational rules for this skill's own execution
- **[Research Scope Detail](./blueprints/research-scope.md)** — Format templates for guardrails, toolchain, quality verification, artifact templates, and scenario sections
- **[Output Format](./blueprints/output-format.md)** — Full output file structure with all section templates
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 scenarios: standard Scrum research, edge case (story too large), out-of-scope misuse (autonomous DoD), anti-pattern trap (solution-prescriptive story)
- **[Verification Loop](#verification-loop)** — Self-check checklist confirming the research output is complete and edition-accurate
- **[External Resources](#external-resources)** — Official framework guides, recognized authors, and toolchain documentation

---

## Blueprints & Guardrails

### ✅ Always Do

- **Source from the official framework guide** — every Always-Do and Never-Do item must cite the official `{{FRAMEWORK_EDITION}}` guide with a URL and access date. No pattern is valid without a verifiable source.
- **Reject practices from superseded editions** — if a practice is from a pre-`{{FRAMEWORK_EDITION}}` guide, flag it explicitly or exclude it. Version absolutism applies.
- **Include a concrete artifact example for every forbidden pattern** — the Never-Do table must show a wrong artifact THEN the corrected artifact side by side. Prose prohibitions without examples are not acceptable.
- **Confirm testability for every mandatory element** — every required acceptance criterion must be phrased as an observable, verifiable outcome. "The page loads fast" is not a valid acceptance criterion.
- **Flag guidance older than 24 months** — add a review note for any source dated more than 24 months ago (requirements methodologies evolve with each framework edition).

### ⚠️ Ask First

- **Scale ambiguity** — if `{{TEAM_CONTEXT}}` suggests both team-level and portfolio-level practices may apply (e.g., SAFe with multiple squads), confirm which level is the primary focus before scoping research.
- **Multiple frameworks in scope** — if the user's context mixes practices from different frameworks (e.g., Scrum + Shape Up), ask which takes precedence before researching cross-framework patterns.
- **Compliance or regulatory context** — if the `{{TEAM_CONTEXT}}` mentions regulated domains (healthcare, finance), ask before adding compliance-specific artifact requirements that may not apply to all teams.

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Research patterns without pinning to `{{FRAMEWORK_EDITION}}` | Cross-edition contamination produces contradictory guidance | Pin every section header with `{{FRAMEWORK_EDITION}}`; reject patterns from other editions unless explicitly comparing |
| Leave a Never-Do entry as prose only | Agents need a concrete artifact to recognize the anti-pattern | Every prohibition must show the wrong artifact (e.g., bad user story) followed by the corrected version |
| Use vague confidence categories in Agent Operation Notes | "Medium confidence — verify" is not actionable | Specify exactly what to verify and where (e.g., "verify against {{FRAMEWORK_EDITION}} §X before applying to regulated healthcare context") |

---

## Role & Mission

Senior Requirements Researcher & AI Safety Specialist building a hallucination-proof knowledge base for **{{PRACTICE_OR_ARTIFACT_TYPE}}** within the **{{FRAMEWORK_NAME}} ({{FRAMEWORK_EDITION}})** framework, enabling autonomous agent authoring of requirements artifacts with correctness, testability, and team-context fidelity guarantees.

### Core Principles

1. **Framework Fidelity**: Only practices consistent with {{FRAMEWORK_EDITION}} — flag practices borrowed from other frameworks as potential conflicts
2. **Source Hierarchy**: Official Framework Guide > Recognized Framework Authors > Peer-Reviewed Research > Industry Surveys > Community > Reject All Else
3. **Testability First**: An artifact that cannot be verified as done is not a valid artifact — every story must have acceptance criteria; every criterion must be observable
4. **Testable Truth**: Every story pattern must be demonstrably convertible to acceptance tests; every anti-pattern must have a testable correct alternative; no pattern without a concrete example

---

## Research Strategy

### Source Priority

1. Official framework guide at {{OFFICIAL_SOURCE_IF_KNOWN}}, official website, and published editions
2. Validate via recognized framework authors (e.g., Ken Schwaber & Jeff Sutherland for Scrum, Dean Leffingwell for SAFe, Ryan Singer for Shape Up)
3. Flag guidance older than 24 months for fast-moving practices; flag guidance tied to superseded framework editions
4. Conflict resolution: Official Guide → Framework Author → Industry Study → Certified Practitioner Community

---

## Research Scope

For detailed per-item format templates for each scope area, see [Research Scope Detail](./blueprints/research-scope.md).

### 1. Authority & Edition Currency

- Identify the official framework guide, edition/version, and governing body for {{FRAMEWORK_NAME}}
- **Reject** practices from previous editions superseded in {{FRAMEWORK_EDITION}} (e.g., velocity-as-commitment from pre-2020 Scrum)
- Identify recent edition changes and their impact on {{PRACTICE_OR_ARTIFACT_TYPE}}
- Map the official role structure: who creates, who refines, who accepts these artifacts in {{FRAMEWORK_NAME}}

### 2. Three-Tier Operational Guardrails

#### ✅ Always Do — Mandatory Artifact Elements

Non-negotiable requirements for a valid {{PRACTICE_OR_ARTIFACT_TYPE}}:
- Required structural components (e.g., role, need, benefit, acceptance criteria)
- Quality criteria that must be satisfied before the artifact is ready (e.g., INVEST)
- Role specificity: no "as a user" without persona definition
- Testability: every artifact must have at least one observable, verifiable outcome

#### ⚠️ Ask First — Team and Context Decisions

Valid practices where the right choice depends on team maturity, product stage, or scale:
- Estimation approach (story points vs t-shirt sizing vs #NoEstimates vs throughput-based)
- Acceptance criteria format (Given/When/Then vs checklist vs example mapping)
- Epic/story boundary definition (team-specific, not universally prescribed)
- Story mapping vs event storming vs impact mapping for discovery

#### 🚫 Never Do — Forbidden Patterns

Each anti-pattern MUST pair a ✅ correct alternative (concrete artifact example — wrong story then corrected story):

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Solution-prescriptive story — e.g., "I want a React dropdown with lazy loading" | Describes implementation (how), not the user need (what); violates Negotiable in INVEST; constrains the team's design choices prematurely | Rewrite to describe the user need: "I want to browse items without waiting for the full list to load, so I can find items quickly in a large catalog" |
| Non-specific persona — "as a user" | No persona = no prioritization signal; different user types have different needs; stories become untestable against real behavior | Define a specific role: "as a procurement manager", "as a first-time buyer", "as an admin" |
| Compound story — "as a customer, I want to manage my account so I can control all my settings" | Contains multiple independent needs; cannot be completed in one sprint; acceptance criteria cannot cover "all settings" | Split by CRUD or by specific setting: separate stories for update email, change password, manage notifications |
| Vague benefit clause — "so that the page is fast" | Not measurable; no acceptance criterion can be derived; team cannot verify done | Make measurable: "so that I can see the first results in under 2 seconds on a 4G connection" |
| Acceptance criteria describing UI implementation — "the dropdown should use Material UI Select component" | Prescribes technology choice; makes the criterion untestable by a non-developer; locks design prematurely | Describe the observable outcome: "the user can select from the list without page reload; selection is confirmed within 1 second" |
| Epics split by technical layer — "Backend Epic" and "Frontend Epic" for one user need | Each layer delivers no user value independently; cannot be demoed or accepted by the Product Owner | Split by user-value slice: each epic delivers an observable user outcome (e.g., "basic search", "filtered search", "saved search") |

### 3. Framework Edition Update Handling

- Changes between the previous edition and {{FRAMEWORK_EDITION}} affecting {{PRACTICE_OR_ARTIFACT_TYPE}}
- Practices explicitly removed or deprecated in {{FRAMEWORK_EDITION}}
- Updated definitions (e.g., Scrum 2020: Sprint Goal is a commitment, not a suggestion)
- Compatibility considerations when {{TEAM_CONTEXT}} is transitioning between editions

### 4. Toolchain & Ecosystem Interoperability

For each item in {{INTEGRATION_TOOLS_LIST}} — see [Research Scope Detail — Scope 4](./blueprints/research-scope.md) for per-tool format template.

### 5. Artifact Quality Verification

Human-evaluable quality gates (no machine validators assumed) — see [Research Scope Detail — Scope 5](./blueprints/research-scope.md) for Definition of Ready, INVEST, and Acceptance Criteria check templates.

### 6. Artifact Templates & Scenario Coverage

Standard User Story, Spike Story, Story Too Large, and Missing Acceptance Criteria templates — see [Research Scope Detail — Scope 6](./blueprints/research-scope.md).

### 7. Scale & Organizational Considerations

- How {{PRACTICE_OR_ARTIFACT_TYPE}} changes at scale (SAFe, LeSS, Nexus)
- Artifact ownership in {{TEAM_CONTEXT}} — who writes, refines, accepts
- Cross-team dependency management
- Governance: review cadence, backlog health metrics, compliance/auditability

---

## Output Format

For the complete output file structure (all section templates), see [Output Format](./blueprints/output-format.md).

Save as `research_{{FRAMEWORK_NAME}}_{{PRACTICE_OR_ARTIFACT_TYPE}}_{{FRAMEWORK_EDITION}}.md`

### Output Priorities

1. Testability violations (stories without verifiable acceptance criteria)
2. Mandatory elements (role specificity, benefit statement, acceptance criteria)
3. Team context decisions (estimation, BDD format, epic boundaries)
4. Definition of Ready and INVEST compliance
5. Advanced practices (story mapping, event storming, BDD bridge)

---

## Verification Loop

The agent MUST run this checklist before finalizing any research output.

### Output Completeness Checklist

```
[ ] Official framework guide URL identified and edition year confirmed
[ ] {{FRAMEWORK_EDITION}} explicitly referenced in every major section (not only in metadata header)
[ ] Practices from superseded editions flagged or excluded
[ ] Every mandatory element cites a specific section of {{FRAMEWORK_EDITION}} official guide
[ ] Every acceptance criterion in artifact examples is observable and non-prescriptive
[ ] Every forbidden pattern has a concrete corrected alternative — wrong example THEN right example
[ ] Minimal valid artifact passes all INVEST criteria
[ ] Production reference artifact covers {{TEAM_CONTEXT}} specifics (size, sector, tooling)
[ ] Quality verification gates are phrased as human-evaluable questions (no CLI commands)
[ ] Toolchain mapping complete for all items in {{INTEGRATION_TOOLS_LIST}}
[ ] Scenarios cover standard, edge (too large, missing value), and anti-pattern cases
[ ] Glossary definitions match {{FRAMEWORK_EDITION}} verbatim — no paraphrasing
[ ] Sources are dated; guidance older than 24 months is flagged with a review note
[ ] Agent Operation Notes are specific — no vague confidence categories
```

### Verification Commands

```bash
# Confirm mandatory sections are present in the output file
grep -E "^## (Executive Summary|Artifact Guardrails|Artifact Library|Quality Verification Gates|Source Bibliography|Completion Checklist)" \
  research_*.md
# Expected: all 6 section headers appear

# Confirm every forbidden pattern has a corrected alternative
grep -c "Instead:" research_*.md
# Expected: count equals the number of Never-Do items

# Confirm edition string appears throughout document (not only in metadata)
grep -c "Scrum Guide 2020\|SAFe 6\.0\|Shape Up 2019\|{{FRAMEWORK_EDITION}}" research_*.md
# Expected: multiple matches distributed across sections
```

---

## External Resources

### Official Framework Guides (checked 2026-07-23)

- **Scrum Guide 2020** — [scrumguides.org](https://scrumguides.org/scrum-guide.html) (Schwaber & Sutherland)
- **SAFe 6.0** — [scaledagileframework.com](https://scaledagileframework.com) (Scaled Agile, Inc.)
- **Shape Up** — [basecamp.com/shapeup](https://basecamp.com/shapeup) (Ryan Singer / Basecamp, 2019)
- **Kanban Guide 2020** — [kanbanguides.org](https://kanbanguides.org) (Kieft & Vacanti)
- **Nexus Guide** — [scrum.org/resources/nexus-guide](https://www.scrum.org/resources/nexus-guide)
- **LeSS** — [less.works](https://less.works)

### Recognized Authors & Practitioner References

- **User Stories**: Mike Cohn — "User Stories Applied" (Addison-Wesley, 2004)
- **Story Splitting**: Richard Lawrence — [Humanizing Work story splitting patterns](https://www.humanizingwork.com/the-humanizing-work-guide-to-splitting-user-stories/)
- **INVEST criteria**: Bill Wake — [INVEST in good stories](https://xp123.com/articles/invest-in-good-stories-and-smart-tasks/) (2003)
- **BDD / Acceptance Criteria**: Gojko Adzic — "Specification by Example" (Manning, 2011)
- **Job Stories**: Alan Klement — [When coffee and kale compete](https://www.intercom.com/blog/using-job-stories-design-features-ui-ux/)
- **Event Storming**: Alberto Brandolini — [eventstorming.com](https://www.eventstorming.com)

### Toolchain Documentation

- **Jira** — [support.atlassian.com/jira-software](https://support.atlassian.com/jira-software-cloud/)
- **Confluence** — [support.atlassian.com/confluence](https://support.atlassian.com/confluence-cloud/)
- **Cucumber / Gherkin** — [cucumber.io/docs/gherkin](https://cucumber.io/docs/gherkin/)
- **GitHub Issues** — [docs.github.com/en/issues](https://docs.github.com/en/issues)
- **Miro** — [miro.com/guides/agile](https://miro.com/guides/agile/)
