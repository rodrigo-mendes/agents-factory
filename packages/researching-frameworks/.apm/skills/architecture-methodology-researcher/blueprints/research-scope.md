# Research Scope Detail — architecture-methodology-researcher

Detailed format templates for each research scope area. The agent fills these during the research
phase and includes the completed versions in the output file.

---

## Scope 2 — Three-Tier Operational Guardrails

### ✅ Always Do: Mandatory Elements

Non-negotiable requirements of the methodology or notation standard:

- Required structural elements (e.g., every C4 Container diagram must show technology labels and inter-container relationships)
- Naming and labeling conventions enforced by the methodology
- Abstraction-level constraints — what must and must not appear at `{{ABSTRACTION_LEVEL}}`
- Traceability requirements (e.g., ADRs must link to the architectural concern they address)
- Audience-appropriate detail level for architects and tech leads

**Format per item**:
```
Element: [Required element or rule name]
Why: [Methodology section or authoritative rationale — cite exactly]
Applies At: [Which abstraction level(s) this applies to]
Example:
  [Minimal valid artifact fragment in Markdown]
Anti-Example:
  [What omitting or violating this looks like]
Source: [URL to spec section or authoritative reference]
```

---

### ⚠️ Ask First: Architectural and Notation Choices

Valid design variations that depend on context, system scale, or design philosophy:

- Diagram scope decisions (e.g., which C4 level to use, when to add a C4-L3 component diagram)
- Notation style choices where multiple valid representations exist (e.g., sync vs async in sequence diagrams, bounded context mapping styles in DDD)
- ADR format variants (Nygard, MADR, Y-Statements) and when to choose each
- Methodology combinations (e.g., C4 + ADRs, DDD + Event Storming, TOGAF + ArchiMate)
- Trade-off representation: when to capture quality attribute trade-offs explicitly in diagrams vs ADRs

**Format per item**:
```
Decision: [What to choose]
Options: [A, B, C — all valid per the methodology]
Tradeoffs:
  | Option | Best For | Limitation | Impact on Traceability |
  |--------|----------|------------|------------------------|
Recommended When: [Context — system scale, team maturity, stakeholder needs]
Ask The User: [Exact question to ask before proceeding]
Source: [Official docs or recognized community guidance]
```

---

### 🚫 Never Do: Forbidden Patterns

Anti-patterns, methodology violations, and notation misuse:

- Abstraction-level violations (e.g., showing database table schema in a C4 System Context diagram)
- Notation misuse (e.g., using UML Class Diagrams to represent runtime behavior instead of structure)
- Undocumented design decisions — architectural choices made without a corresponding ADR when the methodology requires traceability
- Mixing methodology versions (e.g., combining C4 notation conventions from pre-2020 with current 2024 guidance)
- Ambiguous relationship labeling — diagrams where the nature of inter-component relationships is undefined
- ADRs that record *what* was decided without *why* — violates the core purpose of the format

**Format per item**:
```
Anti-Pattern: [What NOT to do]
Why: [Methodology violation | Abstraction error | Traceability failure | Misleading diagram]
Applies At: [Which abstraction level(s) this matters for]
Instead: [Correct alternative with Markdown example]
Impact: [Invalid artifact | Wrong interpretation | Decision loss | Misleading documentation]
Source: [Spec section, authoritative book, or recognized community guidance]
```

---

## Scope 4 — Toolchain & Ecosystem for Markdown Output

For each relevant tool in the `{{METHODOLOGY_OR_NOTATION_NAME}}` ecosystem with Markdown output:

```
Tool: [Tool name and version]
Role: [Diagram renderer | ADR generator | Documentation site | Linter]
Integration: [How it integrates with Markdown — e.g., embedded Mermaid, Hugo site, ADR CLI]
Usage: [Command or workflow to produce or validate the artifact]
Expected Output: [What success looks like — rendered diagram, validated ADR, etc.]
Compatibility: [{{TARGET_VERSION_OR_EDITION}} confirmed support]
Known Issues: [Notation gotchas, rendering edge cases, version-specific bugs]
Source: [Official docs URL]
```

For integrations with adjacent architecture artifacts:

```
Integration: {{METHODOLOGY_OR_NOTATION_NAME}} → [Adjacent artifact/methodology]
How: [Linking strategy — e.g., ADRs linked from C4 diagrams, Event Storming outputs feeding DDD bounded contexts]
Tooling: [Generator, adapter, or documentation system]
Example: [Minimal working integration in Markdown]
Source: [Official guide or canonical community reference]
```

---

## Scope 5 — Artifact Verification

Valid, complete artifact examples — copy-paste ready for architects and tech leads.

**Minimal Valid Artifact** (smallest conforming example):
```markdown
[Minimal valid artifact — no optional elements, meets all mandatory requirements]
# Validates Against: [Methodology checklist or ADR template]
```

**Production Reference Artifact** (for `{{ARCHITECTURE_CONTEXT}}`):
```markdown
[Full artifact for the architecture context — includes all best practices,
 correct abstraction level, proper labeling, decision traceability]
```

**Self-Validation Checklist**:
```
✅ Abstraction level is consistent throughout
✅ All relationships are labeled with direction and nature
✅ Technology labels present where required by methodology
✅ ADR includes context, decision, consequences (minimum viable)
✅ No lower-level implementation detail bleeds into higher-level diagram
✅ Artifact is audience-appropriate for architects and tech leads
```

---

## Scope 6 — Scenario Coverage & Architectural Edge Cases

Common artifact types and cross-cutting concerns:

**Format per item**:
```
Scenario: [Artifact category + architectural difficulty]
Trigger: [When this artifact type is needed in {{ARCHITECTURE_CONTEXT}}]
Architect Approach: [How to structure the artifact under guardrails]
Edge Case: [What breaks at the boundary of this scenario]
Workaround: [Canonical solution recognized by the methodology community]
Reference: [Official example or authoritative source]
```

---

## Scope 7 — Architecture Quality Attributes (QAs) Integration

- Which quality attributes (performance, security, scalability, maintainability, etc.) are surfaced by this methodology
- How to annotate or link QA trade-offs in diagrams and ADRs
- When a QA concern mandates a new ADR vs. a diagram annotation
- How to represent QA decisions across abstraction levels

---

## Scope 8 — Production & Governance Considerations

- **Artifact Lifecycle**: How diagrams and ADRs age — when to update, when to supersede, when to retire
- **Living Documentation**: Strategies for keeping architecture artifacts synchronized with implementation (e.g., diagram-as-code, architecture fitness functions)
- **Team Governance**: Review and approval patterns — who owns ADRs, who approves diagram changes, how to manage architectural drift
- **Versioning Strategy**: How to version-control architecture artifacts alongside code (mono-repo, docs-as-code, wiki)
- **Traceability Matrix**: Linking business requirements → ADRs → diagrams → implementation artifacts
