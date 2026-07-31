# Generated SKILL.md — Structure Template (14 sections)

# SKILL: {{SUBJECT_NAME}} — {{SUBJECT_EDITION}}
# For: Architects and Tech Leads
# Context: {{ARCHITECTURE_CONTEXT}}
# Generated: [Date]
# Review By: [Date + 18 months — architecture guidance evolves]

---

## 1. WHAT THIS SKILL DOES

[1 paragraph: what Claude can produce with this skill — specific artifact types,
 not theory. E.g., "Claude can generate C4 Container diagrams in Mermaid with correct
 technology labels, relationship annotations, and abstraction-level discipline for
 cloud-native microservices systems."]

---

## 2. WHEN TO USE THIS SKILL

Trigger this skill when the user asks about:
- [Trigger phrase or artifact request 1]
- [Trigger phrase or artifact request 2]
- [Trigger phrase or artifact request 3]

Do NOT trigger this skill when:
- [Out-of-scope request 1 — e.g., "user asks about team process, not architecture structure"]
- [Out-of-scope request 2]

---

## 3. SUBJECT FACTS

[HIGH-confidence facts only. Everything here must be Tier 1 or Tier 2 sourced.]

Core Purpose: [What problem this subject solves — 1 sentence, from official source]
Governing Body: [Organization or recognized author maintaining this subject]
Official Reference: [URL]
Current Edition: [{{SUBJECT_EDITION}}]
Key Change From Previous: [Most important change architects must know]
Operates At: [Abstraction levels — e.g., System Context, Container, Enterprise]

Mandatory Elements (per official source):
- [Element]: [What it is and why it is mandatory]

Adjacent Subjects (integrates with):
- [Subject]: [How they connect and where they hand off]

---

## 4. ABSTRACTION LEVEL DISCIPLINE

[This section is mandatory for all Diagram Notation and Domain Modeling subjects.
 For API Specification and ADR subjects, adapt to describe scope boundaries instead.]

### Level: [Name]
- Scope: [What belongs here]
- Required: [What Claude MUST include at this level]
- Forbidden: [What Claude MUST NOT include — the most common violations]
- Audience: [Who reads this — calibrate language and detail accordingly]
- Example trigger: "[User request that maps to this level]"

[Repeat for each abstraction level in scope]

### Abstraction Violation Rules
Claude must refuse to mix levels silently. When a violation is detected:
```
Violation: [What the user asked for that mixes levels]
Problem: [Why this produces a misleading or invalid artifact]
Clarification: "[Exact question to ask to resolve the level ambiguity]"
```

---

## 5. ARTIFACT GENERATION RULES

For each artifact type Claude may produce using this skill:

### [Artifact Name]

**Abstraction Level**: [Which level this artifact operates at]

**When to generate**: [Condition — user request pattern that triggers this artifact]

**Mandatory elements** — Claude MUST include all of these:
```
[Element 1]: [Why mandatory — cite official source]
[Element 2]: [Why mandatory]
[Element 3]: [Why mandatory]
```

**Template**:
```
[Complete, copy-ready artifact — architecture-calibrated, includes:
 - correct abstraction level
 - all mandatory labels and annotations
 - relationship directions and nature
 - technology labels where required
 - no implementation detail bleeding from lower levels]
```

**Quality gate** — before presenting to user, verify:
- [ ] Abstraction level is consistent throughout
- [ ] All relationships labeled with direction and nature
- [ ] No lower-level detail bleeding into this artifact
- [ ] [Subject-specific check 1]
- [ ] [Subject-specific check 2]

**ADR Trigger**: [Condition under which a decision made here requires an ADR]

**Source**: [Official source section or Tier 2 reference]

---

## 6. THREE-TIER GUARDRAILS

Pattern counts in each tier should be driven by the subject's domain complexity, not by a fixed template. Simple notation systems may need 3-4 Always Do rules; comprehensive frameworks may need 7-9. Include every pattern the domain requires — never pad to reach a count, never omit to fit under a cap.

### ✅ ALWAYS DO

[Rules Claude must follow every time, for every artifact, with no exceptions]

Rule: [Name]
What: [Exact behavior required]
Why: [Official rationale — source tier and reference]
Applies At: [Abstraction level(s)]
Example:
```
[Correct artifact fragment]
```

---

### ⚠️ ASK FIRST

[Decisions Claude must NOT make autonomously — requires architect input]

Decision: [What to choose]
Why It Matters: [What breaks or misleads if the wrong choice is made]
Options:
| Option | Best For | Architectural Trade-off | Quality Attribute Impact |
|--------|----------|------------------------|--------------------------|
Ask: "[Exact question to ask the architect or tech lead]"
ADR Required: [Yes/No — and why]
Source: [Reference]

---

### 🚫 NEVER DO

[Hard prohibitions — patterns Claude must refuse to produce as-is]

Anti-Pattern: [Name]
What It Looks Like:
```
[Concrete bad example — architecture context]
```
Why It's Wrong: [Abstraction violation | Notation misuse | Decision loss | Misleading]
Instead:
```
[Correct alternative — same intent, properly structured]
```
Architectural Impact: [What breaks — diagram trust | decision traceability | onboarding | incident response]
Source: [Reference]

---

## 7. DECISION TRACEABILITY

[When artifacts produced by this skill require an ADR or equivalent decision record]

### ADR Trigger Conditions
```
Condition: [When an architectural decision must be recorded]
Why: [What is at risk if the decision is not documented]
Minimum ADR Content: [Context, Decision, Consequences — mandatory fields]
Link To: [How this ADR connects back to the diagram or spec artifact]
```

### Decision Status Lifecycle (if applicable)
```
Proposed → [Trigger to move forward]
Accepted → [Who accepts, what evidence is required]
Superseded → [What condition triggers supersession, what replaces it]
Deprecated → [When to use deprecated vs superseded]
```

---

## 8. QUALITY ATTRIBUTES MAPPING

[How this subject surfaces, constrains, or trades off system quality attributes]

| Quality Attribute | How Surfaced in This Subject | Diagram Annotation? | ADR Trigger? |
|------------------|------------------------------|---------------------|--------------|
| [e.g., Scalability] | [How] | [Yes/No] | [Yes/No — condition] |
| [e.g., Security] | [How] | [Yes/No] | [Yes/No — condition] |
| [e.g., Maintainability] | [How] | [Yes/No] | [Yes/No — condition] |

---

## 9. EDITION CHANGES ARCHITECTS MUST KNOW

[Changes in {{SUBJECT_EDITION}} that affect how Claude generates artifacts]

Changed: [What changed]
Before: [Old notation, field, or artifact pattern]
After: [New required approach]
Source: [Official changelog, spec diff, or author announcement]

Deprecated: [Element or practice no longer valid in {{SUBJECT_EDITION}}]
Replaced By: [Current correct approach]
Migration: [How existing artifacts must be updated]

---

## 10. INTEGRATION WITH ADJACENT SUBJECTS

[How this subject connects to others Claude might use simultaneously]

Integrates With: [Subject name]
How: [Connection point — e.g., "C4 Container diagrams reference ADRs for technology choices"]
Artifact Handoff: [What artifact from this subject feeds into the adjacent one]
Conflict Risk: [Where the two subjects produce contradictory guidance]
Resolution: [Which takes precedence and under what conditions]

---

## 11. TOOLING REFERENCE

[Canonical tooling for producing and validating artifacts from this subject]

Tool: [Name and version]
Role: [Renderer | Validator | Generator | Linter | Documentation site]
Output Format: [Mermaid | PlantUML | YAML | Markdown | HTML | etc.]
Usage: [Command or workflow to produce or validate the artifact]
Known Issues: [Rendering edge cases, version-specific bugs, notation gaps]
Source: [Official tool documentation URL]

---

## 12. SCALE BOUNDARIES

[Where this subject breaks down — when to flag limits to the architect]

Works Well For: [System size, team size, organizational complexity]
Breaks Down When: [Specific conditions — e.g., "C4 L3 component diagrams become unmanageable above ~20 components"]
At Scale, Use Instead: [Alternative approach with source]
Warning Signal: "[What Claude should say when the artifact is approaching the limit]"

---

## 13. CONFIDENCE MAP

[Claude's operating confidence for different artifact types in this skill]

HIGH — Generate autonomously:
- [Artifact type]: [Why high confidence — well-specified mandatory structure]

MEDIUM — Generate with architect confirmation:
- [Artifact type]: [What to confirm — e.g., system boundary, technology choice, domain ownership]

LOW — Do not generate without explicit architect design input:
- [Artifact type]: [Why — e.g., security architecture, data sovereignty, compliance scope]

STOP — Escalate before proceeding:
- [Condition]: [Why this requires human judgment — irreversible, compliance-critical, cross-domain]

---

## 14. SOURCE BIBLIOGRAPHY

[All sources used, tagged by tier — every claim in this SKILL.md traces to one of these]

[Tier 1] [Title] — [URL] — [Edition/Date]
[Tier 2] [Author, Title] — [URL or ISBN] — [Publication Date]
[Tier 3] [Study name] — [URL] — [Date]
[Tier 4] [Community standard name] — [URL] — [Date accessed]
```

---
