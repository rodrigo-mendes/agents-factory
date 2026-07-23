# Output Format — requirements-methodology-researcher

Save research output as `research_{{FRAMEWORK_NAME}}_{{PRACTICE_OR_ARTIFACT_TYPE}}_{{FRAMEWORK_EDITION}}.md`

---

## Metadata

```yaml
Framework: [Official framework name]
Practice_Artifact: [Artifact type being researched]
Edition: [Exact edition/version string]
Governing_Body: [Organization that maintains the framework]
Official_Guide_URL: [Primary authoritative document URL]
Recognized_Authors: [Key authors/practitioners for this framework]
Team_Context: [Description of target team — size, sector, product stage]
Research_Date: [Date]
Currency_Threshold: [Date after which this research should be reviewed]
```

---

## Executive Summary

[2–3 paragraphs: what {{PRACTICE_OR_ARTIFACT_TYPE}} is in the context of {{FRAMEWORK_NAME}}, what changed in {{FRAMEWORK_EDITION}} that affects how these artifacts are written, and the three most critical quality guardrails the agent must enforce]

---

## Framework Terminology Glossary

[10–20 terms the agent must understand precisely — defined per {{FRAMEWORK_EDITION}}, not informally]

```
Term: [Framework term]
Definition: [Exact meaning per {{FRAMEWORK_EDITION}} official guide]
Guide Section: [Where defined]
Commonly Confused With: [Related term it is NOT synonymous with]
Agent Usage: [How the agent should apply this term when authoring artifacts]
```

---

## Artifact Guardrails

### ✅ Mandatory Elements

[Element Name]
- Why: [Framework rationale + author reference]
- Template:
  ```
  [Minimal valid artifact using this element]
  ```
- Quality Check: [Human-evaluable verification question]
- Source: [Link]

### ⚠️ Team Context Decisions

[Decision Point]
- Options: [A, B, C]
- Tradeoffs:

  | Option | Best For | Trade-off | Context Signal |
  |--------|----------|-----------|----------------|

- Agent Instruction: "Ask the team [specific question] when [condition]"
- Source: [Link]

### 🚫 Forbidden Patterns

[Anti-Pattern Name]

  Bad:
  ```
  [Concrete anti-pattern example]
  ```
- Why: [Quality damage caused]
- Instead:
  ```
  [Corrected version with same intent]
  ```
- Downstream Impact: [Sprint planning | Acceptance testing | Prioritization | Stakeholder trust]
- Source: [Link]

---

## Framework Update Guide

**Changes in {{FRAMEWORK_EDITION}}**: [List of changes relevant to {{PRACTICE_OR_ARTIFACT_TYPE}}]
**Deprecated Practices**: [What to stop doing — with correct replacement]
**Migration**: [How existing artifacts need to be updated to conform]

---

## Artifact Library

**Minimal Valid Artifact**:
```
[Smallest conforming example — no optional elements]
```

**Production Reference Artifact** (for {{TEAM_CONTEXT}}):
```
[Complete, best-practice example — happy path + edge case criteria + spike variant if applicable]
```

**Story Splitting Reference**:
```
Pattern: [Split strategy name]
When: [Symptom that triggers this split]
Before: [Oversized story]
After: [Correctly split stories]
```

---

## Quality Verification Gates

**Definition of Ready**:
```
[ ] [Check 1 — question form]
[ ] [Check 2]
[ ] [Check 3]
[ ] [Check 4]
[ ] [Check 5]
```

**INVEST Check** (if applicable):
```
[ ] Independent
[ ] Negotiable
[ ] Valuable
[ ] Estimable
[ ] Small
[ ] Testable
```

**Acceptance Criteria Check**:
```
[ ] Observable outcome (not implementation)
[ ] Clear pass/fail state
[ ] Covers happy path
[ ] Covers key error/edge states
[ ] Verifiable without source code access
```

---

## Toolchain Integration

**[Tool from {{INTEGRATION_TOOLS_LIST}}]**:
```
Artifact Mapping: [How story fields map to tool fields]
Required Fields: [Tool fields that must be populated]
Gap Warning: [What the tool cannot capture — manual documentation needed]
```

**BDD Bridge** (if applicable):
```
Acceptance criterion:
  [Example criterion]
Resulting scenario:
  Given [context]
  When [action]
  Then [outcome]
Tool: [BDD framework]
```

---

## Scenario Coverage

**Standard Case**: [Most common artifact for {{TEAM_CONTEXT}}]
- Approach: [How to author it]
- Agent Instruction: [Default template to apply]

**Edge Case — Too Large**: [Oversized artifact]
- Detection: [How to identify this]
- Resolution: [Split pattern to apply]

**Edge Case — Missing Value**: [Artifact without clear benefit]
- Detection: [Signal]
- Resolution: [Questions to ask to surface the value]

**Anti-Pattern Case**: [Common bad artifact the agent must not produce]
- Refusal: [What the agent must say/do instead]

---

## Scale & Governance

- **Multi-Team**: [How artifact changes across teams in {{TEAM_CONTEXT}}]
- **Ownership**: [Who writes, refines, accepts in {{FRAMEWORK_NAME}}]
- **Backlog Health**: [Metrics that signal artifact quality at portfolio level]
- **Compliance**: [Traceability or audit requirements in {{TEAM_CONTEXT}}]

---

## Reference Artifacts

- [Official framework guide examples with URLs]
- [Recognized practitioner templates with authors and URLs]
- [Backlog refinement and story splitting guides]

---

## Source Bibliography

**Primary**: [Official framework guide, governing body publications with URLs and edition dates]
**Validation**: [Recognized author books/articles, industry surveys, certified practitioner references with relevance notes]
**All Deep-Links**: [Complete organized list with access dates]

---

## Completion Checklist

- [ ] All scope areas cited with guide-level sources
- [ ] Minimal valid artifact passes INVEST checklist
- [ ] Production reference artifact covers {{TEAM_CONTEXT}} specifics
- [ ] Every forbidden pattern has a corrected alternative example
- [ ] All quality verification gates are human-evaluable (no machine validators assumed)
- [ ] Toolchain mapping complete for all items in {{INTEGRATION_TOOLS_LIST}}
- [ ] Scenario coverage includes standard, edge, and anti-pattern cases
- [ ] Sources dated and edition-confirmed
- [ ] Glossary aligns with {{FRAMEWORK_EDITION}} official definitions

---

## Research Gaps

```
Gap: [Missing or uncertain knowledge area]
Impact: [Risk of producing incorrect or low-quality artifacts]
Workaround: [Conservative default — most restrictive valid interpretation]
Follow-up: [Where to find the answer — guide section, recognized author, community]
```

---

## Agent Operation Notes

- **High Confidence**: [Artifacts the agent can produce autonomously — e.g., standard user story from a clear feature description with known persona]
- **Medium Confidence**: [Artifacts requiring context from the Product Owner or team before authoring — e.g., epic decomposition, acceptance criteria for complex business rules]
- **Low Confidence**: [Artifacts the agent must not produce without explicit human input — e.g., Definition of Done (team-specific commitment), story priority or sequencing]
- **Edge Cases**: [When to pause and ask — e.g., story appears too large, benefit is not specified, conflicting acceptance criteria, regulated domain requirements]
- **Emergency Stop**: [Conditions requiring human review before proceeding — e.g., story touches compliance or security domain, acceptance criteria reference personal data handling, story implies architectural decision not yet made]
