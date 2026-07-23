---
name: archtecture-approches-skill-generator
description: Researches a system-architecture methodology/notation and generates an operational SKILL.md for producing correct architecture artifacts. Use when turning architecture research into a skill.
context: fork
agent: skill-author
disable-model-invocation: true
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
### Estrutura do SKILL.md gerado

O SKILL.md produzido segue um template de 14 seções: What/When, Subject Facts, Abstraction Level Discipline, Artifact Generation Rules, Three-Tier Guardrails (✅/⚠️/🚫), Decision Traceability, Quality Attributes, Edition Changes, Integration, Tooling, Scale Boundaries, Confidence Map e Source Bibliography. Template completo em [Generated SKILL Structure](./blueprints/generated-skill-structure.md).
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
