# Output Format — architecture-methodology-researcher

Save research output as `research_{{METHODOLOGY_OR_NOTATION_NAME}}_{{TARGET_VERSION_OR_EDITION}}.md`

---

## Metadata

```yaml
Full_Name: [Official methodology/notation name]
Target_Version: [Exact version string]
Governing_Body: [Organization or community maintaining the standard]
Official_Spec_URL: [Primary authoritative document URL]
Official_Examples_URL: [Official example repository or reference site]
Output_Format: Markdown
Primary_Audience: Architects and Tech Leads
Abstraction_Level: [{{ABSTRACTION_LEVEL}}]
Research_Date: [Date]
Currency_Threshold: [Date after which this research should be reviewed]
```

---

## Executive Summary

[2–3 paragraphs covering:
1. What `{{METHODOLOGY_OR_NOTATION_NAME}}` is for and its role in the architecture practice
2. What changed in `{{TARGET_VERSION_OR_EDITION}}` vs previous versions
3. The three most critical guardrails for architects producing correct artifacts]

---

## Methodology Glossary

10–20 terms that the architect must understand precisely — defined from the official spec or authoritative source, not informal usage:

```
Term: [Term from the methodology]
Definition: [Exact meaning per {{TARGET_VERSION_OR_EDITION}}]
Spec Section: [Where defined]
Architect Usage: [How to apply this term when generating artifacts]
Common Confusion: [What it is frequently (incorrectly) confused with in practice]
```

---

## Artifact Guardrails

### ✅ Mandatory Elements

**[Element Name]**
- Applies At: [Abstraction level(s)]
- Why: [Methodology reference]
- Example:
  ```markdown
  [Correct Markdown artifact fragment]
  ```
- Validates With: [Self-check or tooling reference]
- Source: [Link]

### ⚠️ Contextual Choices

**[Decision Point]**
- Options: [A, B, C]
- Tradeoffs:

  | Option | Best For | Limitation | Traceability Impact |
  |--------|----------|------------|---------------------|

- Architect Instruction: "Ask [specific question] when [condition is met]"
- Source: [Link]

### 🚫 Forbidden Patterns

**[Anti-Pattern Name]**
```markdown
<!-- DON'T -->
[bad artifact fragment]
```
- Why: [Methodology violation or abstraction error]
- Instead:
```markdown
<!-- DO -->
[correct artifact fragment]
```
- Impact: [Invalid | Misleading | Decision loss | Tooling failure]
- Source: [Link]

---

## Methodology Update Guide

**Breaking Changes from Previous Version**: [List with methodology references]
**Migration Steps**: [Numbered list — artifact-level changes required]
**Compatibility Matrix**:

| Adjacent Methodology | Compatible | Notes |
|---------------------|-----------|-------|

---

## Artifact Library

**Minimal Valid Artifact**:
```markdown
[Minimal conforming example]
```

**Production Reference Artifact** (for `{{ARCHITECTURE_CONTEXT}}`):
```markdown
[Complete, idiomatic, best-practice example]
```

---

## Toolchain Reference

**Diagram Rendering** (Markdown-embedded):
```bash
# Tool + integration method
[Setup or usage command]
# Expected output
[Success state]
```

**ADR Management** (if applicable):
```bash
[ADR CLI or tooling command]
# Expected output
[Success state]
```

---

## Scenario Coverage

**Standard Case**: [Most common artifact for `{{ARCHITECTURE_CONTEXT}}`]
- Approach: [How to structure it]
- Architect Instruction: [What to produce and what decisions to surface]

**Edge Case**: [Boundary scenario — cross-cutting concern, brownfield migration, etc.]
- Approach: [Canonical workaround]

**Anti-Pattern Case**: [What the architect must refuse to produce as-is]
- Clarification: [What to ask before proceeding]

---

## Quality Attributes Mapping

| Quality Attribute | How Surfaced in This Methodology | ADR Trigger? | Diagram Annotation? |
|------------------|----------------------------------|--------------|---------------------|

---

## Production & Governance Readiness

- **Artifact Lifecycle**: [When to update, supersede, or retire artifacts]
- **Living Documentation**: [Strategy for keeping diagrams in sync with implementation]
- **Versioning**: [How to version-control artifacts alongside code]
- **Governance**: [Who owns, reviews, and approves — at team scale]
- **Traceability**: [How to link requirements → ADRs → diagrams → implementation]

---

## Reference Artifacts

- [Official specification examples with URLs]
- [Canonical community templates with URLs]
- [Recognized style guides]

---

## Source Bibliography

**Primary**: [Official spec, governing body publications, authoritative books with URLs and dates]
**Validation**: [Tool documentation, recognized community references with relevance notes]
**All Deep-Links**: [Complete organized list with access dates]

---

## Completion Checklist

- [ ] All scope areas cited with authoritative sources
- [ ] Minimal valid artifact meets all mandatory requirements
- [ ] Production reference artifact covers `{{ARCHITECTURE_CONTEXT}}`
- [ ] Every forbidden pattern has a correct alternative
- [ ] Abstraction levels are correctly defined and respected throughout
- [ ] Quality attribute integration is documented
- [ ] Toolchain compatibility covers Markdown output
- [ ] Scenarios cover standard, edge, and anti-pattern cases
- [ ] Sources dated and methodology-version confirmed
- [ ] Glossary aligns with official methodology definitions

---

## Research Gaps

```
Gap: [Missing or uncertain knowledge area]
Impact: [Risk of incorrect or misleading artifact generation]
Workaround: [Conservative default behavior for architects]
Follow-up: [Where to find the answer — URL, book, specification section]
```

---

## Architect Operation Notes

- **High Confidence**: [Artifacts the architect can produce autonomously — well-documented mandatory structures with unambiguous methodology guidance]
- **Medium Confidence**: [Structures requiring context before generating — e.g., system boundaries, ownership of bounded contexts, build-vs-buy decisions]
- **Low Confidence**: [Structures requiring explicit design input — e.g., security architecture, cross-domain integration patterns, data sovereignty boundaries]
- **Ask First**: [When to pause — artifact scope is ambiguous, multiple valid representations exist, methodology is being stretched beyond its intended use]
- **Emergency Stop**: [Conditions requiring senior architect review — security-critical decisions, regulatory/compliance implications, irreversible architectural choices]
