# Evaluation Scenarios — architecture-methodology-researcher

Used to verify that the skill activates correctly, enforces methodology-version fidelity,
applies abstraction-level guardrails, and steers away from notation misuse and undocumented
design decisions.

---

## Scenario 1: Standard research request — C4 Model (canonical path)

```json
{
  "skills": ["architecture-methodology-researcher"],
  "query": "Research the C4 Model (2024 guidance) for our microservices platform with 10+ services. We need to produce System Context and Container diagrams as Markdown with Mermaid.",
  "expected_behavior": [
    "Identifies c4model.com as the authoritative source and confirms 2024 guidance currency",
    "Maps mandatory elements for L1 (System Context): external actors, the system boundary, external systems with technology labels",
    "Maps mandatory elements for L2 (Container): every container must show technology label and responsibility; all inter-container relationships labeled with protocol/data",
    "Flags abstraction-level constraints: implementation details (classes, DB tables) must NOT appear at L1 or L2",
    "Identifies Mermaid C4 diagram integration and usage commands",
    "Produces minimal valid L1 artifact and production reference L2 artifact for a microservices context",
    "Documents ADR integration pattern: architectural decisions surfaced in diagrams must link to corresponding ADRs",
    "Cites every element with spec section or official C4 site reference and access date"
  ],
  "success_criteria": {
    "must_pass": [
      "Official source identified as c4model.com with access date",
      "Mandatory elements for both L1 and L2 documented with methodology references",
      "Minimal valid artifact produced for each diagram level — no optional elements inlined",
      "Abstraction-level violation rule documented: no code-level detail at L1/L2",
      "Toolchain entry for Mermaid C4 integration included with usage command"
    ],
    "must_not": [
      "Cite blog posts or informal C4 adaptations as authoritative guidance",
      "Mix C4 notation conventions from pre-2020 with current 2024 guidance (anti-pattern)",
      "Produce a diagram example that shows DB table schema at System Context level",
      "Leave relationship lines unlabeled in Container diagram examples"
    ]
  }
}
```

---

## Scenario 2: Edge case — brownfield migration with mixed methodology versions

```json
{
  "skills": ["architecture-methodology-researcher"],
  "query": "Our team has existing architecture docs using older UML 2.4 component diagrams and some informal C4-style sketches. We want to migrate to UML 2.5.1. What must change?",
  "expected_behavior": [
    "Identifies OMG as governing body for UML 2.5.1 and locates official spec document",
    "Documents what changed between UML 2.4 and 2.5.1 relevant to Component Diagrams",
    "Lists deprecated notation elements from 2.4 and their 2.5.1 replacements",
    "Explicitly flags 'informal C4-style sketches' as a notation mixing risk — must be resolved to one canonical notation before documenting",
    "Provides a migration checklist: which diagram elements need updating, which can coexist",
    "Warns that mixing UML Component and informal C4 conventions in the same artifact is a Never-Do (produces ambiguous diagrams)",
    "Recommends Ask-First for the consolidation decision: migrate all to UML 2.5.1, or formally adopt C4 2024, not both ad hoc"
  ],
  "success_criteria": {
    "must_pass": [
      "OMG spec identified as authoritative source with URL and edition date",
      "Breaking changes between UML 2.4 and 2.5.1 documented with spec section references",
      "Notation mixing flagged as a prohibited pattern with correct alternative (pick one canonical notation)",
      "Migration path includes artifact-level steps, not just conceptual advice",
      "Compatibility matrix shows which adjacent methodologies work with UML 2.5.1"
    ],
    "must_not": [
      "Treat informal C4 sketches as equivalent to UML 2.5.1 notation without flagging the difference",
      "Recommend using both notations in parallel without resolving which is canonical",
      "Omit the governing body (OMG) and rely only on practitioner blog references",
      "Produce artifact examples that mix UML syntax with C4 conventions"
    ]
  }
}
```

---

## Scenario 3: Misuse / out-of-scope — methodology stretch beyond intended use

```json
{
  "skills": ["architecture-methodology-researcher"],
  "query": "Use ADR format to document all of our sprint retrospective action items and team process decisions, not just architecture decisions.",
  "expected_behavior": [
    "Identifies that ADR (Architecture Decision Record) format is intended for architectural decisions — not general team process or sprint ceremonies",
    "Cites the Michael Nygard ADR format or MADR guidance establishing the scope: decisions with significant architectural consequence",
    "Flags this as a methodology stretch — applying ADR to retrospective action items violates the format's decision traceability purpose",
    "Does NOT refuse to explain ADR; instead, explains what ADR is for and asks a clarifying question: 'Are any of these retrospective items architectural decisions with long-term structural consequences?'",
    "Suggests the correct alternative for team process decisions: a lightweight decision log, team agreements doc, or RACI — not ADR",
    "Documents the Ask-First trigger: when a proposed ADR is about process rather than architecture, ask if it truly has architectural consequence"
  ],
  "success_criteria": {
    "must_pass": [
      "ADR format's intended scope documented with authoritative reference (Nygard, MADR, or ADR GitHub community)",
      "Skill identifies the methodology stretch and explains the violation clearly",
      "Correct alternative (process decision log, team agreements) provided with rationale",
      "Clarifying question offered rather than a flat refusal — user may have legitimate architectural decisions mixed in",
      "Ask-First decision point documented: architecture decision vs. team process decision"
    ],
    "must_not": [
      "Silently comply and produce ADR templates for sprint retrospective action items",
      "Treat all documented decisions as equivalent regardless of architectural consequence",
      "Cite no authoritative source for ADR's intended scope",
      "Produce an ADR example with 'Action Item: Improve standups' as the decision — this is out-of-scope misuse"
    ]
  }
}
```

---

## Scenario 4: Anti-pattern trap — abstraction-level violation in diagram request

```json
{
  "skills": ["architecture-methodology-researcher"],
  "query": "Add our PostgreSQL table schemas and Java class method signatures to our C4 System Context (L1) diagram so stakeholders can see all the details.",
  "expected_behavior": [
    "Immediately flags this as an abstraction-level violation — C4 L1 (System Context) must show only people, the system boundary, and external systems",
    "Cites C4 abstraction rules: implementation details (DB tables, class methods) belong at L4 (Code level), not L1",
    "Explains the consequence: an L1 diagram with implementation details becomes unreadable for its intended audience (senior stakeholders) and loses its communication purpose",
    "Does NOT produce a System Context diagram with table schemas or method signatures",
    "Offers the correct alternatives: (a) keep L1 clean and add L3/L4 diagrams for implementation detail; (b) use a separate code-level diagram for the class/DB layer",
    "Documents this as a Never-Do: mixing abstraction levels in a single C4 diagram"
  ],
  "success_criteria": {
    "must_pass": [
      "Abstraction violation identified before any artifact is produced",
      "C4 L1 mandatory constraints cited (external actors, system boundary, external systems only)",
      "Correct alternative provided: L4 or separate code diagram for implementation detail",
      "Explanation includes the communication consequence — not just 'the rule says so'"
    ],
    "must_not": [
      "Produce a C4 L1 diagram containing DB table schemas or class method signatures",
      "Suggest adding a legend to 'clarify' the level mixing instead of separating the concerns",
      "Treat the request as valid without flagging the abstraction-level violation",
      "Cite only informal blog posts as rationale for the abstraction rule"
    ]
  }
}
```
