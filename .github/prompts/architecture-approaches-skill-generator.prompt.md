---
name: architecture-approaches-skill-generator
description: Architecture Approach SKILL.md Generator — converts a validated architecture approach or design pattern research file into an operational SKILL.md with ✅⚠️🚫 patterns. Use when generating a skill from an architecture approach research base (e.g. C4 Model, Hexagonal Architecture).
argument-hint: "Path to architecture research file (e.g. StoryBeat/research_C4_Model_2024.md)"
---

# Meta-Prompt: Architecture Research → SKILL.md Generator

---

## PURPOSE

This is a **research and skill generation prompt**. Given any system architecture
methodology, notation, or design approach, it researches the subject authoritatively
and produces a `SKILL.md` file that Claude can use as a reference to generate correct,
high-quality architecture artifacts.

The output is not a document for humans to read — it is an **operational knowledge file
for Claude**, structured to enable autonomous artifact generation with correctness,
abstraction-level discipline, and decision traceability guarantees.

---

## INPUT VARIABLES

```yaml
SUBJECT_NAME:        # e.g., "C4 Model", "UML Component Diagrams", "ADR",
                     #        "Domain-Driven Design", "Event-Driven Architecture",
                     #        "TOGAF", "ArchiMate 3.2", "OpenAPI 3.1", "AsyncAPI 3.0",
                     #        "Microservices Patterns", "Team Topologies"
SUBJECT_EDITION:     # e.g., "C4 Model 2024", "UML 2.5.1", "TOGAF 10",
                     #        "OpenAPI 3.1.0", "Michael Nygard ADR format"
ARCHITECTURE_CONTEXT: # e.g., "microservices platform with 10+ services",
                      #        "event-driven B2B SaaS", "cloud-native mobile backend",
                      #        "domain-driven e-commerce system"
OFFICIAL_SOURCE:     # optional — e.g., "https://c4model.com", "https://adr.github.io"
```

---

## PHASE 1 — SUBJECT CLASSIFICATION

Before researching, classify the subject to determine what kind of SKILL.md to produce.

Analyze `{{SUBJECT_NAME}}` and identify:

### 1.1 — Primary Category

Determine which category best describes this architecture subject:

| Category | Examples | Primary Artifact Types |
|---|---|---|
| **Diagram Notation** | C4 Model, UML, ArchiMate, BPMN | Diagrams, views, notation rules, rendering |
| **API Specification** | OpenAPI 3.1, AsyncAPI 3.0, gRPC/Protobuf | Spec files, contract definitions, schema |
| **Architecture Decision** | ADR, MADR, RFC, Y-Statements | Decision records, trade-off documentation |
| **Design Pattern Catalog** | Microservices Patterns, EAA Patterns, CQRS/ES | Pattern descriptions, applicability, trade-offs |
| **Architecture Framework** | TOGAF, Zachman, SAF | Viewpoints, phases, governance artifacts |
| **Domain Modeling** | DDD, Event Storming, Context Mapping | Bounded contexts, aggregates, domain maps |
| **System Quality Model** | DORA Metrics, SRE, Fitness Functions | Measurable quality attributes, thresholds |

### 1.2 — Artifact Taxonomy

List every artifact type this subject produces. For each:

```
Artifact: [Name]
Purpose: [What architectural problem it solves]
Producer: [Who creates it — role in architecture practice]
Consumer: [Who acts on it — architects, engineers, stakeholders]
Abstraction Level: [System context | Container | Component | Code | Cross-cutting]
Lifecycle: [How it is created, updated, superseded, and retired]
```

### 1.3 — Abstraction Level Map

Identify which abstraction levels are relevant for this subject:

```
Level: [Name — e.g., System Context, Container, Component, Code, Enterprise]
Scope: [What is visible at this level]
Audience: [Who reads artifacts at this level]
Forbidden Detail: [What must NOT appear at this level — critical for discipline]
```

### 1.4 — Skill Structure Decision

Based on classification, decide the SKILL.md emphasis:

- **Diagram Notation** → Emphasize: notation rules, abstraction discipline, required labels,
  rendering tooling, forbidden mixing of levels
- **API Specification** → Emphasize: required fields, schema correctness, versioning,
  contract-first discipline, tooling validation
- **Architecture Decision** → Emphasize: decision record structure, when to write an ADR,
  status lifecycle, traceability to diagrams and code
- **Design Pattern Catalog** → Emphasize: applicability conditions, trade-off documentation,
  known misapplications, combination patterns
- **Architecture Framework** → Emphasize: viewpoint selection, phase sequencing,
  artifact ownership, governance process
- **Domain Modeling** → Emphasize: bounded context boundaries, ubiquitous language,
  context mapping patterns, strategic vs tactical DDD
- **System Quality Model** → Emphasize: metric definitions, measurement methods,
  threshold setting, fitness function design

Document the decision:
```
Classification: [Category]
Rationale: [Why this subject fits this category]
SKILL.md Emphasis: [Which sections will be most critical]
Sections To Minimize: [Which standard sections are less relevant]
Abstraction Levels In Scope: [Which levels this subject operates at]
```

---

## PHASE 2 — AUTHORITATIVE RESEARCH

Research `{{SUBJECT_NAME}} {{SUBJECT_EDITION}}` using the source hierarchy below.
Every claim in the SKILL.md must be traceable to a source at the appropriate tier.

### Source Hierarchy

```
Tier 1 — Official:  Official spec, standard, or governing body publication
                    (OMG, OpenAPI Initiative, AsyncAPI Initiative, The Open Group)
Tier 2 — Author:    Recognized creators and authoritative authors
                    (Simon Brown/C4, Eric Evans/DDD, Gregor Hohpe/EAI, Chris Richardson/Microservices)
Tier 3 — Study:     Peer-reviewed research or recognized industry study
Tier 4 — Canon:     Widely adopted community standards with broad practitioner consensus
Tier 5 — Reject:    Blog posts, informal adaptations, version-mixed guidance,
                    undated community posts
```

### Research Checklist

For each item below, find the authoritative answer and note the source tier:

```
[ ] What architectural problem does this subject solve? (Tier 1 or 2)
[ ] What are the mandatory elements — non-negotiable per the official source? (Tier 1)
[ ] What abstraction-level violations are most common? (Tier 1 or 2)
[ ] What changed in {{SUBJECT_EDITION}} vs. the previous version? (Tier 1)
[ ] What context-dependent decisions must architects make? (Tier 1 or 2)
[ ] What quality attributes does this subject help address or trade off? (Tier 1 or 2)
[ ] What adjacent subjects does this integrate with? (Tier 2 or canon)
[ ] What tooling is canonical for this subject? (Tier 1 or official tool docs)
[ ] What are the scale and complexity limits of this approach? (Tier 2 or 3)
[ ] What are the most common misapplications in practice? (Tier 2 or 3)
[ ] What decisions made using this subject require an ADR? (Tier 2 or canon)
```

### Confidence Tagging

Tag every research finding with its confidence level:

```
[HIGH]   — Tier 1 source, directly from official spec or governing body
[MEDIUM] — Tier 2 or 3 source, widely accepted but not officially mandated
[LOW]    — Tier 4 or inferred — flag in SKILL.md as "community convention, not official"
[REJECT] — Tier 5 — do not include in SKILL.md
```

---

## PHASE 3 — SKILL.md GENERATION

Using the classification from Phase 1 and research from Phase 2, generate the SKILL.md.

The SKILL.md must satisfy these non-negotiable requirements:
- Every rule Claude must follow is **unambiguous** — no "it depends" without
  explicit decision logic
- Every artifact example is **copy-ready** — no unfilled placeholders in
  mandatory sections
- Every forbidden pattern has a **correct alternative** — never just "don't do X"
- **Abstraction discipline is enforced** — every artifact example must declare its
  level and respect the forbidden-detail rules for that level
- Structure adapts to the subject category — no one-size-fits-all template

---

### SKILL.md STRUCTURE

```markdown
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

## PHASE 4 — SKILL.md SELF-VALIDATION

Before finalizing the SKILL.md, run this checklist:

```
STRUCTURE
[ ] Section 1 describes what Claude can DO — not what the subject IS
[ ] Section 2 has clear trigger conditions and explicit out-of-scope exclusions
[ ] Section 4 (Abstraction Discipline) present and correctly scoped to the subject category
[ ] Section 5 has at least one complete, copy-ready artifact template per artifact type
[ ] Every template declares its abstraction level explicitly

CORRECTNESS
[ ] Every mandatory element in Section 5 cites a Tier 1 or Tier 2 source
[ ] Every "NEVER DO" has a correct alternative — no prohibition without replacement
[ ] Every "ASK FIRST" includes the exact question Claude should ask
[ ] Every "ASK FIRST" declares whether an ADR is required
[ ] Pattern counts driven by domain needs (not fixed template minimums)
[ ] Edition changes in Section 9 confirmed against {{SUBJECT_EDITION}} official source
[ ] Deprecated patterns are explicitly marked — not silently omitted

ABSTRACTION DISCIPLINE
[ ] Every artifact example declares its abstraction level
[ ] Forbidden-detail rules are specified per level in Section 4
[ ] Abstraction violation detection rules are present with exact clarifying questions
[ ] No artifact template contains detail from a lower abstraction level

DECISION TRACEABILITY
[ ] ADR trigger conditions are defined in Section 7
[ ] Decision status lifecycle present where the subject involves reversible choices
[ ] Quality attributes mapping present in Section 8

USABILITY
[ ] An architect could use Section 5 templates without reading the original source
[ ] Quality gates are evaluable by a tech lead — no ambiguous criteria
[ ] SKILL.md is self-contained — no external references required to use it
[ ] Review date set to 18 months from generation — architecture guidance evolves
[ ] Scale boundaries warn Claude when to flag limits to the architect
```

---

## PHASE 5 — OUTPUT INSTRUCTION

Produce the following output, in this order:

1. **Classification Summary** (Phase 1 output — 1 short paragraph)
   > "This is a [Category] subject. The SKILL.md will emphasize [X, Y, Z]
   > and minimize [A, B] because [rationale]. It operates at [abstraction levels]."

2. **Research Confidence Report** (Phase 2 output — table format)
   > | Finding | Source | Tier | Confidence |
   > |---------|--------|------|------------|

3. **SKILL.md** (Phase 3 output — complete file, ready to save)
   > Save as: `SKILL_{{SUBJECT_NAME}}_{{SUBJECT_EDITION}}.md`

4. **Validation Report** (Phase 4 output — checklist with pass/fail per item)
   > Flag every failure — do not silently skip. For each failure, state what
   > is missing and what source would resolve it.

5. **Research Gaps**
   > ```
   > Gap: [What could not be confirmed at Tier 1–3]
   > Risk: [What Claude might get wrong without this]
   > Default: [Conservative behavior until gap is resolved]
   > Follow-up: [Where to find the authoritative answer]
   > ```

---

## USAGE EXAMPLES

### Example 1 — Diagram Notation
```yaml
SUBJECT_NAME:         "C4 Model"
SUBJECT_EDITION:      "C4 Model 2024"
ARCHITECTURE_CONTEXT: "microservices platform with 10+ services and an event bus"
OFFICIAL_SOURCE:      "https://c4model.com"
```
Expected: Classification as Diagram Notation. SKILL.md emphasizes abstraction
discipline across L1–L4, required labels, Mermaid rendering, and ADR triggers
for technology choices at Container level.

---

### Example 2 — Architecture Decision
```yaml
SUBJECT_NAME:         "ADR"
SUBJECT_EDITION:      "Michael Nygard format / MADR 3.0"
ARCHITECTURE_CONTEXT: "cloud-native backend team making frequent technology decisions"
OFFICIAL_SOURCE:      "https://adr.github.io"
```
Expected: Classification as Architecture Decision. SKILL.md emphasizes decision
record structure, status lifecycle, when to write vs skip an ADR, traceability
to diagrams and code, and format variants (Nygard vs MADR vs Y-Statements).

---

### Example 3 — Domain Modeling
```yaml
SUBJECT_NAME:         "Domain-Driven Design"
SUBJECT_EDITION:      "Eric Evans DDD / Vernon IDDD"
ARCHITECTURE_CONTEXT: "e-commerce platform decomposing a monolith into bounded contexts"
OFFICIAL_SOURCE:      "https://domainlanguage.com/ddd/"
```
Expected: Classification as Domain Modeling. SKILL.md emphasizes bounded context
identification, ubiquitous language, context mapping patterns, strategic vs tactical
DDD boundary, and ADR triggers for context boundary and ownership decisions.

---

### Example 4 — API Specification
```yaml
SUBJECT_NAME:         "OpenAPI"
SUBJECT_EDITION:      "OpenAPI 3.1.0"
ARCHITECTURE_CONTEXT: "microservices REST APIs with contract-first development"
OFFICIAL_SOURCE:      "https://spec.openapis.org/oas/v3.1.0"
```
Expected: Classification as API Specification. SKILL.md emphasizes required fields
(info, paths, components), schema correctness, versioning strategy, contract-first
discipline, tooling validation, and ADR triggers for breaking changes.
```