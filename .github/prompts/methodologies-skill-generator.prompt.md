---
name: methodologies-skill-generator
description: Methodology SKILL.md Generator — converts a validated methodology research file into an operational SKILL.md with ✅⚠️🚫 patterns. Use when generating a skill from a requirements or architecture methodology research base.
argument-hint: "Path to methodology research file (e.g. StoryBeat/research_SAFe_v6.md)"
---

# Meta-Prompt: Methodology Research → SKILL.md Generator

---

## PURPOSE

This is a **research and skill generation prompt**. Given any engineering or process
methodology, it researches the methodology authoritatively and produces a `SKILL.md`
file that Claude can use as a reference to generate correct, high-quality artifacts.

The output is not a document for humans to read — it is a **operational knowledge file
for Claude**, structured to enable autonomous artifact generation with correctness
guarantees.

---

## INPUT VARIABLES

```yaml
METHODOLOGY_NAME:       # e.g., "Scrum", "Kanban", "SAFe", "Lean Software Development",
                        #        "BPM/BPMN 2.0", "XP", "Shape Up", "DORA", "Team Topologies"
METHODOLOGY_EDITION:    # e.g., "Scrum Guide 2020", "SAFe 6.0", "BPMN 2.0.2", "Kanban Guide 2020"
ENGINEERING_CONTEXT:    # e.g., "platform engineering team doing cloud-native migration",
                        #        "5-person SaaS backend team", "scaled org with 3 squads"
OFFICIAL_SOURCE:        # optional — e.g., "https://scrumguides.org"
```

---

## PHASE 1 — METHODOLOGY CLASSIFICATION

Before researching, classify the methodology to determine what kind of SKILL.md to produce.

Analyze `{{METHODOLOGY_NAME}}` and identify:

### 1.1 — Primary Category
Determine which category best describes this methodology:

| Category | Examples | Primary Artifact Types |
|---|---|---|
| **Flow & Delivery** | Kanban, Scrum, XP, Shape Up | Work items, boards, cadences, metrics |
| **Scaling Framework** | SAFe, LeSS, Nexus, Spotify Model | PI Plans, ARTs, dependency maps, team structures |
| **Process Modeling** | BPM, BPMN, SIPOC, Value Stream Mapping | Process flows, swim lanes, VSMs, RACI |
| **Engineering Practices** | XP, DORA, DevOps, GitOps | DoD, pipelines, fitness functions, deployment metrics |
| **Organizational Design** | Team Topologies, DDD, Sociocracy | Team maps, interaction modes, domain boundaries |
| **Lean / Improvement** | Lean SW, Six Sigma, Kaizen, PDCA | VSMs, waste taxonomy, A3 reports, improvement katas |

### 1.2 — Artifact Taxonomy
List the artifact types this methodology produces. For each:
```
Artifact: [Name]
Purpose: [What engineering problem it solves]
Producer: [Who creates it — role in the methodology]
Consumer: [Who acts on it — role in the methodology]
Lifecycle: [How it is created, refined, used, and retired]
```

### 1.3 — Skill Structure Decision
Based on classification, decide the SKILL.md structure:

- **Flow & Delivery** → Emphasize: work item templates, DoD/DoR gates, flow metrics, anti-patterns
- **Scaling Framework** → Emphasize: role boundaries, artifact ownership at scale, dependency management
- **Process Modeling** → Emphasize: notation rules, swimlane conventions, exception path requirements, tooling
- **Engineering Practices** → Emphasize: pipeline integration, measurable outcomes, fitness functions, CI/CD gates
- **Organizational Design** → Emphasize: team interaction modes, boundary definitions, cognitive load considerations
- **Lean / Improvement** → Emphasize: waste taxonomy, current vs future state, metrics collection, improvement cycle

Document the decision:
```
Classification: [Category]
Rationale: [Why this methodology fits this category]
SKILL.md Emphasis: [Which sections will be most critical]
Sections To Minimize: [Which standard sections are less relevant for this methodology]
```

---

## PHASE 2 — AUTHORITATIVE RESEARCH

Research `{{METHODOLOGY_NAME}} {{METHODOLOGY_EDITION}}` using the source hierarchy below.
Every claim in the SKILL.md must be traceable to a source at the appropriate tier.

### Source Hierarchy
```
Tier 1 — Official: Official guide, specification, or governing body publication
Tier 2 — Author:   Recognized methodology authors (named creators, original books)
Tier 3 — Study:    Peer-reviewed research or industry survey (e.g., State of Agile)
Tier 4 — Canon:    Widely adopted community standards (e.g., DORA metrics, ADR formats)
Tier 5 — Reject:   Blog posts, informal adaptations, version-mixed guidance
```

### Research Checklist
For each item below, find the authoritative answer and note the source tier:

```
[ ] What problem does this methodology solve? (Tier 1 or 2)
[ ] What are the mandatory elements — non-negotiable per the official guide? (Tier 1)
[ ] What are the common anti-patterns that degrade outcomes? (Tier 1, 2, or 3)
[ ] What changed in {{METHODOLOGY_EDITION}} vs. the previous version? (Tier 1)
[ ] What are the context-dependent decisions engineers must make? (Tier 1 or 2)
[ ] What metrics does the methodology use to measure success? (Tier 1 or 2)
[ ] What adjacent methodologies does this integrate with? (Tier 2 or canon)
[ ] What tooling is canonical for this methodology? (Tier 1 or official tool docs)
[ ] What are the scale limits — where does this methodology break down? (Tier 2 or 3)
[ ] What are the most common misapplications in engineering teams? (Tier 2 or 3)
```

### Confidence Tagging
Tag every research finding with its confidence level:
```
[HIGH]   — Tier 1 source, directly quoted or closely paraphrased from official guide
[MEDIUM] — Tier 2 or 3 source, widely accepted but not officially mandated
[LOW]    — Tier 4 or inferred — flag in SKILL.md as "community convention, not official"
[REJECT] — Tier 5 — do not include in SKILL.md
```

---

## PHASE 3 — SKILL.md GENERATION

Using the classification from Phase 1 and research from Phase 2, generate the SKILL.md.

The SKILL.md must satisfy these non-negotiable requirements:
- Every rule Claude must follow is **unambiguous** — no "it depends" without explicit decision logic
- Every artifact example is **copy-ready** — no placeholders left unfilled in the mandatory sections
- Every forbidden pattern has a **correct alternative** — never just say "don't do X"
- Structure adapts to the methodology category — do not use a one-size-fits-all template

---

### SKILL.md STRUCTURE

```markdown
# SKILL: {{METHODOLOGY_NAME}} — {{METHODOLOGY_EDITION}}
# For: Engineering teams (Tech Leads and Engineers)
# Context: {{ENGINEERING_CONTEXT}}
# Generated: [Date]
# Review By: [Date + 18 months — methodology guidance expires]

---

## 1. WHAT THIS SKILL DOES

[1 paragraph: what Claude can do with this skill — be specific about artifact types,
 not methodology theory. E.g., "Claude can generate Kanban board designs, WIP limit
 recommendations, and cycle time analysis templates for engineering teams."]

---

## 2. WHEN TO USE THIS SKILL

Trigger this skill when the user asks about:
- [Trigger phrase or request type 1]
- [Trigger phrase or request type 2]
- [Trigger phrase or request type 3]

Do NOT trigger this skill when:
- [Out-of-scope request 1 — e.g., "user asks about business strategy, not delivery process"]
- [Out-of-scope request 2]

---

## 3. METHODOLOGY FACTS

[HIGH-confidence facts only. Everything here must be Tier 1 or Tier 2 sourced.]

Core Purpose: [What problem this methodology solves — 1 sentence, official definition]
Governing Body: [Organization that maintains the methodology]
Official Guide: [URL]
Current Edition: [{{METHODOLOGY_EDITION}}]
Key Change From Previous: [Most important change engineers must know]

Mandatory Roles (if defined by the methodology):
- [Role]: [Responsibility relevant to artifact generation]

Mandatory Artifacts:
- [Artifact]: [Purpose and mandatory elements]

Mandatory Events/Cadences (if applicable):
- [Event]: [Purpose, timebox, required outputs]

---

## 4. ARTIFACT GENERATION RULES

For each artifact type Claude may produce using this skill:

### [Artifact Name]

**When to generate**: [Condition that triggers this artifact]

**Mandatory elements** — Claude MUST include all of these:
```
[Element 1]: [Why mandatory — cite guide section]
[Element 2]: [Why mandatory]
[Element 3]: [Why mandatory]
```

**Template**:
```
[Complete, copy-ready artifact template — engineering-calibrated,
 no business fluff, includes technical constraints and CI/CD hooks where relevant]
```

**Quality gate** — before presenting to user, verify:
- [ ] [Check 1 — engineer-evaluable question]
- [ ] [Check 2]
- [ ] [Check 3 — verifiable without source code access]

**Source**: [Official guide section or Tier 2 reference]

---

## 5. THREE-TIER GUARDRAILS

Pattern counts in each tier should be driven by the methodology's domain complexity, not by a fixed template. Simple flow methodologies may need 3-4 Always Do rules; comprehensive scaling frameworks may need 7-9. Include every pattern the domain requires — never pad to reach a count, never omit to fit under a cap.

### ✅ ALWAYS DO

[Rules Claude must follow every time, for every artifact, with no exceptions]

Rule: [Name]
What: [Exact behavior required]
Why: [Official rationale — source tier and reference]
Example:
```
[Correct artifact fragment]
```

---

### ⚠️ ASK FIRST

[Decisions Claude must NOT make autonomously — must ask the engineering team]

Decision: [What to choose]
Why It Matters: [What breaks if the wrong choice is made]
Options:
| Option | Best For | Engineering Trade-off |
|--------|----------|----------------------|
Ask: "[Exact question to ask the tech lead or engineer]"
Source: [Reference]

---

### 🚫 NEVER DO

[Hard prohibitions — patterns Claude must refuse to produce as-is]

Anti-Pattern: [Name]
What It Looks Like:
```
[Concrete bad example — engineering context]
```
Why It's Wrong: [Flow degradation | Methodology violation | Misleading | Untestable]
Instead:
```
[Correct alternative — same intent, properly done]
```
Engineering Impact: [What breaks downstream]
Source: [Reference]

---

## 6. FLOW METRICS (if applicable)

[Include this section only if the methodology defines measurable flow outcomes.
 Skip for methodologies that are purely structural, e.g., Team Topologies.]

| Metric | Definition | What It Signals | Anti-Pattern |
|--------|-----------|----------------|--------------|
| [Name] | [Exact definition per {{METHODOLOGY_EDITION}}] | [Engineering signal] | [How it's gamed] |

---

## 7. EDITION CHANGES ENGINEERS MUST KNOW

[Changes in {{METHODOLOGY_EDITION}} that affect how Claude generates artifacts]

Changed: [What changed]
Before: [Old behavior or artifact pattern]
After: [New required behavior or artifact pattern]
Source: [Official changelog or guide diff]

Deprecated: [Practice no longer valid in {{METHODOLOGY_EDITION}}]
Replaced By: [Current correct approach]

---

## 8. INTEGRATION WITH ADJACENT METHODOLOGIES

[How this methodology connects to others Claude might be used with simultaneously]

Integrates With: [Methodology name]
How: [Connection point — e.g., "Scrum stories feed Kanban flow board after sprint planning"]
Conflict Risk: [Where the two methodologies contradict each other]
Resolution: [Which takes precedence and why — cite both official sources]

---

## 9. SCALE BOUNDARIES

[Where this methodology breaks down — critical for Claude to know when to flag limits]

Works Well For: [Team size, system complexity, organizational scale]
Breaks Down When: [Specific conditions — e.g., "Scrum degrades above 9 team members per official guide"]
At Scale, Use Instead: [Alternative or scaling extension with source]

---

## 10. CONFIDENCE MAP

[Claude's operating confidence for different artifact types in this skill]

HIGH — Generate autonomously:
- [Artifact type]: [Why high confidence]

MEDIUM — Generate with user confirmation:
- [Artifact type]: [What to confirm before generating]

LOW — Do not generate without explicit human design input:
- [Artifact type]: [Why — and what to ask instead]

STOP — Escalate to human before proceeding:
- [Condition]: [Why this requires human judgment]

---

## 11. SOURCE BIBLIOGRAPHY

[All sources used, tagged by tier]

[Tier 1] [Title] — [URL] — [Edition/Date]
[Tier 2] [Author, Title] — [URL or ISBN] — [Publication Date]
[Tier 3] [Study name] — [URL] — [Date]
```

---

## PHASE 4 — SKILL.md SELF-VALIDATION

Before finalizing the SKILL.md, run this checklist:

```
STRUCTURE
[ ] Section 1 describes what Claude can DO — not what the methodology IS
[ ] Section 2 has clear trigger conditions and explicit out-of-scope exclusions
[ ] Section 4 has at least one complete, copy-ready artifact template
[ ] Every template uses engineering-calibrated language — no pure business language

CORRECTNESS
[ ] Every mandatory element in Section 4 cites a Tier 1 or Tier 2 source
[ ] Every "NEVER DO" has a correct alternative — no prohibition without replacement
[ ] Every "ASK FIRST" includes the exact question Claude should ask
[ ] Pattern counts driven by domain needs (not fixed template minimums)
[ ] Edition changes in Section 7 are confirmed against {{METHODOLOGY_EDITION}} official guide
[ ] Deprecated practices are explicitly marked — not silently omitted

CALIBRATION
[ ] Flow metrics section present ONLY if the methodology defines measurable outcomes
[ ] Scale boundaries reflect the official guide — not informal community opinion
[ ] Confidence map distinguishes what Claude can do autonomously vs. needs human input
[ ] No [LOW] confidence items are left in the ALWAYS DO section

USABILITY
[ ] A tech lead could use Section 4 templates without reading the methodology guide
[ ] Quality gates are evaluable by an engineer — no abstract or business-only language
[ ] SKILL.md is self-contained — no external references required to use it
[ ] Review date is set to 18 months from generation — methodology guidance expires
```

---

## PHASE 5 — OUTPUT INSTRUCTION

Produce the following output, in this order:

1. **Classification Summary** (Phase 1 output — 1 short paragraph)
   > "This is a [Category] methodology. The SKILL.md will emphasize [X, Y, Z]
   > and minimize [A, B] because [rationale]."

2. **Research Confidence Report** (Phase 2 output — table format)
   > | Finding | Source | Tier | Confidence |
   > |---------|--------|------|------------|

3. **SKILL.md** (Phase 3 output — complete file, ready to save)
   > Save as: `SKILL_{{METHODOLOGY_NAME}}_{{METHODOLOGY_EDITION}}.md`

4. **Validation Report** (Phase 4 output — checklist with pass/fail per item)
   > Flag any item that does not pass — do not silently skip failures.

5. **Research Gaps** (any Tier 5 rejections or LOW confidence items that
   could not be resolved — with follow-up instructions)
   > ```
   > Gap: [What could not be confirmed at Tier 1–3]
   > Risk: [What Claude might get wrong without this]
   > Default: [Conservative behavior until gap is resolved]
   > Follow-up: [Where to find the authoritative answer]
   > ```

---

## USAGE EXAMPLE

```yaml
METHODOLOGY_NAME:    "Kanban"
METHODOLOGY_EDITION: "Kanban Guide 2020"
ENGINEERING_CONTEXT: "Platform engineering team managing 3 internal services,
                      intermediate maturity, using Jira and GitHub"
OFFICIAL_SOURCE:     "https://kanban.university/kanban-guide/"
```

Expected output:
- Classification: Flow & Delivery
- SKILL.md sections emphasized: work item states, WIP limits, flow metrics, commitment point
- SKILL.md sections minimized: scaling framework, org design
- Artifact templates: Kanban board design, WIP limit calculation, cycle time SLA template
- Key guardrails: WIP limits are mandatory (not optional), columns represent work states
  (not team states), cycle time must be measured (not estimated)
```