# Research Scope Detail — requirements-methodology-researcher

Detailed format templates for each research scope area. The agent fills these during the research
phase and includes the completed versions in the output file.

---

## Scope 2 — Three-Tier Operational Guardrails

### ✅ Always Do: Mandatory Artifact Elements

Non-negotiable requirements for a valid {{PRACTICE_OR_ARTIFACT_TYPE}} per {{FRAMEWORK_EDITION}} and universal software product quality standards:
- Required structural components of the artifact (e.g., role, need, benefit, acceptance criteria)
- Quality criteria that must be satisfied before the artifact is considered ready (e.g., INVEST for user stories)
- Role specificity requirements — no placeholders like "as a user" without persona definition
- Testability requirement — every artifact must contain at least one observable, verifiable outcome

**Format per item**:
```
Element: [Required component or quality criterion name]
Why: [Framework rationale — cite specific guide section or recognized author]
Template:
  [Minimal valid artifact example using the element]
Quality Check: [Human-evaluable question to verify this element is present and correct]
Source: [URL to framework guide section or recognized author reference]
```

---

### ⚠️ Ask First: Team and Context Decisions

Valid practices where the right choice depends on team maturity, product stage, scale, or organizational context:
- Estimation approach (story points vs t-shirt sizing vs #NoEstimates vs throughput-based)
- Acceptance criteria format (Given/When/Then BDD style vs checklist vs example mapping)
- Epic/story boundary definition (team-specific, not universally prescribed)
- Story mapping vs event storming vs impact mapping for discovery
- Feature flag strategy for stories spanning multiple sprints

**Format per item**:
```
Decision: [What to choose]
Options: [A, B, C]
Tradeoffs: [Each approach optimizes/sacrifices what for which team context]
Recommended When: [Context factors — team maturity, product stage, scale, regulatory environment]
Team Context Signal: [How to identify which option fits {{TEAM_CONTEXT}}]
Source: [Framework guide or recognized practitioner reference]
```

---

### 🚫 Never Do: Forbidden Patterns

Anti-patterns that produce invalid, unmaintainable, or low-quality requirements artifacts:
- Solution-prescriptive stories that describe implementation instead of user need
- Compound stories masked as single items (detectable by "and" in the need)
- Acceptance criteria that describe UI implementation instead of observable user behavior
- Epics split by technical layer instead of user value
- Missing benefit clause — story describes what but not why
- Acceptance criteria that require access to source code to verify

**Format per item**:
```
Anti-Pattern: [What NOT to do — be specific]
Why: [Quality degradation this causes — untestable | unestimable | no value signal | not independent]
Bad Example:
  [Concrete example of the anti-pattern]
Instead:
  [Corrected artifact with the same intent, properly written]
Quality Damage: [What breaks downstream — sprint planning | acceptance testing | prioritization | stakeholder trust]
Source: [Framework guide, recognized author, or industry study that documents this anti-pattern]
```

---

## Scope 3 — Framework Edition Update Handling

- Changes between the previous edition and {{FRAMEWORK_EDITION}} that affect {{PRACTICE_OR_ARTIFACT_TYPE}}
- Practices explicitly removed or deprecated in {{FRAMEWORK_EDITION}}
- Updated definitions (e.g., Scrum 2020 removed "sprint goal is suggested" — it is now a commitment)
- Compatibility considerations when {{TEAM_CONTEXT}} is transitioning between editions or frameworks

---

## Scope 4 — Toolchain & Ecosystem Interoperability

For each item in {{INTEGRATION_TOOLS_LIST}}:

```
Tool: [Tool name]
Role: [Backlog management | Documentation | BDD bridge | Test management | Collaboration]
Artifact Mapping: [How {{PRACTICE_OR_ARTIFACT_TYPE}} maps to this tool's data model]
Required Fields: [Fields in the tool that must be populated for a complete artifact]
Integration Flow: [How this tool connects to adjacent tools in the workflow]
Risks: [What gets lost in translation — field mapping gaps, manual steps, sync delays]
Source: [Official tool documentation URL]
```

For the bridge between {{PRACTICE_OR_ARTIFACT_TYPE}} and executable test artifacts:

```
Bridge: {{PRACTICE_OR_ARTIFACT_TYPE}} → [Test artifact type]
Trigger: [When to make this bridge — not all stories need it]
Transformation Rule: [How acceptance criteria map to test scenarios]
Example:
  Story acceptance criterion:
    [criterion]
  Resulting test scenario:
    [Given/When/Then or equivalent]
Tool: [BDD framework or test management tool]
Source: [BDD guide or tool documentation]
```

---

## Scope 5 — Artifact Quality Verification

Human-evaluable quality gates — every check must be a question a person can answer.

**Definition of Ready Gate** (before sprint/iteration commitment):
```
Check: [Quality question]
Pass Condition: [What "yes" looks like]
Fail Condition: [What "no" looks like — and what action to take]
```

**INVEST Checklist** (for {{PRACTICE_OR_ARTIFACT_TYPE}} if applicable):
```
Independent: [Can this be developed and delivered without depending on another incomplete story?]
Negotiable: [Is the how open to discussion, with only the what and why fixed?]
Valuable: [Does the benefit statement name a real stakeholder outcome?]
Estimable: [Does the team have enough information to size this?]
Small: [Can this be completed within one iteration?]
Testable: [Can every acceptance criterion be verified by a non-developer?]
```

**Acceptance Criteria Quality Check**:
```
Observable: [Does each criterion describe a user-visible or system-measurable outcome?]
Bounded: [Does each criterion have a clear pass/fail state — no "it should be fast"?]
Non-prescriptive: [Does each criterion avoid specifying implementation?]
Complete: [Do the criteria together cover happy path, edge cases, and error states?]
```

---

## Scope 6 — Artifact Templates & Scenario Coverage

**Standard User Story**:
```
As a [specific role/persona — not "user"],
I want [need or capability — what, not how],
so that [measurable business or user outcome].

Acceptance Criteria:
- Given [context], when [action], then [observable outcome]
- Given [context], when [action], then [observable outcome]
[...]

Definition of Ready: [ ] Independent [ ] Estimable [ ] Testable [ ] Sized <= sprint
```

**Spike Story** (time-boxed research):
```
Goal: [Specific question to answer or risk to reduce]
Timebox: [Maximum effort — hours or story points]
Output: [What will be produced — decision, prototype, ADR, benchmark]
Done When: [Observable outcome that closes the spike]
```

**Edge Case — Story Too Large**:
```
Symptom: [Story requires more than one sprint to complete]
Split Pattern: [Workflow steps | Happy/unhappy paths | Data variations | CRUD operations | User roles]
Example split: [Before → After]
Source: [Story splitting guide reference]
```

**Edge Case — Missing Acceptance Criteria**:
```
Symptom: [Story has no verifiable done state]
Resolution: [Three questions to extract criteria: "What does success look like?", "What could go wrong?", "How will you test this?"]
```

---

## Scope 7 — Scale & Organizational Considerations

- How {{PRACTICE_OR_ARTIFACT_TYPE}} changes at scale (multiple teams, SAFe, LeSS, Nexus)
- Artifact ownership and authorship in {{TEAM_CONTEXT}} — who writes, who refines, who accepts
- Cross-team dependency management in the artifact (linking, blocking, sequencing)
- Governance: review cadence, refinement process, backlog health metrics
- Regulatory or compliance constraints on requirements artifacts in {{TEAM_CONTEXT}} (auditability, traceability, change control)
