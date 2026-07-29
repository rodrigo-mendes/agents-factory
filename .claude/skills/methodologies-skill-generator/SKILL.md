---
name: methodologies-skill-generator
description: Researches an engineering/process methodology and generates an operational SKILL.md for producing correct artifacts. Use when turning a methodology into a skill.
argument-hint: "<methodology> (e.g. TDD, scrum, kanban)"
context: fork
agent: skill-author
disable-model-invocation: true
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

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier rules for this generator's own operation
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 scenarios: canonical, edge, misuse
- **[Verification Loop](#verification-loop)** — Post-generation self-check
- **[External Resources](#external-resources)** — Reference links

---

## Blueprints & Guardrails

These rules govern this generator's own operation (not the skills it generates).

### ✅ Always Do

- **Classify before researching** — Complete Phase 1 classification before any research. The category determines which SKILL.md sections to emphasize, preventing generic outputs that don't fit the methodology.
- **Source every claim at Tier 1 or 2** — Every mandatory element, role definition, or artifact template in the generated SKILL.md must cite an official guide, governing body, or recognized methodology author. Tag with `[HIGH]`/`[MEDIUM]`/`[LOW]`.
- **Include full three-tier guardrails in the generated SKILL.md** — The output SKILL.md must contain ✅ Always Do, ⚠️ Ask First, and 🚫 Never Do sections with correct-alternative counterparts for every Never Do item. Never omit any tier.
- **Create `blueprints/evaluation-scenarios.md` for the generated skill** — Every generated SKILL.md must be accompanied by at least 3 evaluation scenarios (canonical, edge, misuse) in the house JSON format. Link from Quick Navigation in the generated SKILL.md.
- **Add `## External Resources` to the generated SKILL.md** — Include links to the official guide, governing body, and canonical tooling. All links must be dated.
- **Include a Verification Loop in the generated SKILL.md** — Provide concrete self-check steps the consuming agent can execute after generating a methodology artifact.
- **Run Phase 4 self-validation before finalizing** — Complete the full checklist; flag every failure explicitly. Do not silently skip items.
- **Keep the generated SKILL.md under 500 lines** — Use `blueprints/` to extract content that exceeds the limit.
- **Include the source bibliography** — Section 11 of the generated SKILL.md must list all sources used, tagged by tier.

### ⚠️ Ask First

- **Ambiguous edition** — When `METHODOLOGY_EDITION` is absent or multiple editions exist (e.g., Scrum Guide 2017 vs 2020), ask for the specific edition before researching. Mixing editions is disinformation.
- **Category boundary** — When a methodology spans categories (e.g., SAFe spans Scaling Framework and Engineering Practices), ask the user which primary use case to emphasize before classifying.
- **Engineering context scope** — When `ENGINEERING_CONTEXT` is vague, ask for team size, tooling, and maturity level. These determine which artifact templates and flow metrics to include.
- **Tier 1 source unavailable** — When no official guide exists for a mandatory element, ask whether to use a Tier 2 source with `[MEDIUM]` confidence or omit and document as a Research Gap.

### 🚫 Never Do

- **Never include Tier 5 sources** — Blog posts, informal adaptations, or undated community posts must not appear in the generated SKILL.md. ✅ Find a Tier 1 or 2 source, or document the gap in Research Gaps.
- **Never omit the correct alternative for a Never Do item** — Every prohibited pattern in the generated SKILL.md must include a concrete correct alternative. ✅ Write the correct alternative inline, side-by-side with the anti-pattern.
- **Never mix methodology versions** — Do not blend Scrum Guide 2017 and 2020 guidance in the same SKILL.md. ✅ Pin to a single edition; mark older patterns as deprecated with their replacement.
- **Never produce a generic SKILL.md** — The generated output must be specific to the methodology's category (Flow & Delivery, Scaling Framework, etc.). ✅ Complete Phase 1 classification and adapt sections accordingly.
- **Never skip Research Gaps** — If a finding cannot be confirmed at Tier 1–3, do not silently omit it. ✅ Document it in Research Gaps with a conservative default behavior.
- **Never allow the generated SKILL.md to exceed 500 lines** — ✅ Extract large content (artifact templates, metrics tables) to `blueprints/` files and link from Quick Navigation.
- **Never include the Flow Metrics section for structural methodologies** — Only include Section 6 (Flow Metrics) when the methodology defines measurable flow outcomes. ✅ Skip the section for Team Topologies, TOGAF-style frameworks, and similar structural approaches.

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
- **Three-tier guardrails are complete** — ✅ Always Do, ⚠️ Ask First, and 🚫 Never Do sections
  must all be present with correct alternatives for every Never Do item
- **`blueprints/evaluation-scenarios.md` is created** alongside the SKILL.md with
  ≥3 scenarios (canonical, edge, misuse) and linked from Quick Navigation
- **`## External Resources` section is present** with dated official links
- **A Verification Loop section is present** with concrete self-check steps

### SKILL.md STRUCTURE

The generated SKILL.md follows 11 sections: What This Skill Does, When To Use, Methodology Facts,
Artifact Generation Rules, Three-Tier Guardrails (✅/⚠️/🚫), Flow Metrics (conditional),
Edition Changes, Integration with Adjacent Methodologies, Scale Boundaries, Confidence Map,
and Source Bibliography. It also requires Quick Navigation, Verification Loop, and External
Resources sections. Full structure and field-by-field guidance is in the prompt body below.

#### Generated SKILL.md Section Outline

```markdown
# SKILL: {{METHODOLOGY_NAME}} — {{METHODOLOGY_EDITION}}
# For: Engineering teams (Tech Leads and Engineers)
# Context: {{ENGINEERING_CONTEXT}}
# Generated: [Date]
# Review By: [Date + 18 months]

## Quick Navigation
- [Always Do / Ask First / Never Do](#three-tier-guardrails)
- [Evaluation Scenarios](./blueprints/evaluation-scenarios.md)
- [Artifact Templates](#artifact-generation-rules)
- [Verification Loop](#verification-loop)
- [External Resources](#external-resources)

## 1. WHAT THIS SKILL DOES
## 2. WHEN TO USE THIS SKILL
## 3. METHODOLOGY FACTS
## 4. ARTIFACT GENERATION RULES
## 5. THREE-TIER GUARDRAILS  ← ✅ Always Do / ⚠️ Ask First / 🚫 Never Do
## 6. FLOW METRICS (conditional — only if methodology defines measurable outcomes)
## 7. EDITION CHANGES ENGINEERS MUST KNOW
## 8. INTEGRATION WITH ADJACENT METHODOLOGIES
## 9. SCALE BOUNDARIES
## 10. CONFIDENCE MAP
## 11. SOURCE BIBLIOGRAPHY
## Verification Loop
## External Resources
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
[ ] Three-tier guardrails complete (✅ Always Do, ⚠️ Ask First, 🚫 Never Do all present)
[ ] blueprints/evaluation-scenarios.md created with ≥3 scenarios
[ ] blueprints/evaluation-scenarios.md linked from Quick Navigation
[ ] External Resources section present with dated links
[ ] Verification Loop section present

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
[ ] Generated SKILL.md is under 500 lines
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
   > Save as: `.claude/skills/<skill-name>/SKILL.md`

4. **`blueprints/evaluation-scenarios.md`** (≥3 scenarios in house JSON format)
   > Save as: `.claude/skills/<skill-name>/blueprints/evaluation-scenarios.md`

5. **Validation Report** (Phase 4 output — checklist with pass/fail per item)
   > Flag any item that does not pass — do not silently skip failures.

6. **Research Gaps** (any Tier 5 rejections or LOW confidence items that
   could not be resolved — with follow-up instructions)
   > ```
   > Gap: [What could not be confirmed at Tier 1–3]
   > Risk: [What Claude might get wrong without this]
   > Default: [Conservative behavior until gap is resolved]
   > Follow-up: [Where to find the authoritative answer]
   > ```

---

## Verification Loop

After generating a SKILL.md, the agent MUST verify:

```
[ ] Generated SKILL.md is < 500 lines (wc -l .claude/skills/<skill-name>/SKILL.md)
[ ] blueprints/evaluation-scenarios.md exists at .claude/skills/<skill-name>/blueprints/
[ ] Quick Navigation in SKILL.md links to ./blueprints/evaluation-scenarios.md
[ ] Three-tier section is present and all three tiers (✅/⚠️/🚫) are populated
[ ] External Resources section is present with at least one dated official link
[ ] Verification Loop section is present in the generated SKILL.md
[ ] Every 🚫 Never Do item has an inline ✅ correct alternative
[ ] Phase 4 validation checklist has no unresolved failures
[ ] Flow Metrics section is present ONLY if methodology defines measurable outcomes
```

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
- `blueprints/evaluation-scenarios.md` created with ≥3 scenarios and linked

---

## External Resources

### Methodology Governing Bodies & Official Guides
- [Scrum Guide 2020](https://scrumguides.org/scrum-guide.html) — Schwaber & Sutherland
- [Kanban Guide 2020](https://kanban.university/kanban-guide/) — Kanban University
- [SAFe 6.0](https://scaledagileframework.com) — Scaled Agile, Inc.
- [BPMN 2.0.2 Specification](https://www.omg.org/spec/BPMN/2.0.2/) — OMG
- [DORA State of DevOps](https://dora.dev/research/) — DORA Research Program
- [Team Topologies](https://teamtopologies.com) — Skelton & Pais (official site)
- [Shape Up](https://basecamp.com/shapeup) — Basecamp / Ryan Singer

### Skill Authoring Standards
- [authoring-agent-skills SKILL.md](../authoring-agent-skills/SKILL.md) — House conventions for generated SKILL.md files
- [TEMPLATE.SKILL.md](../../templates/skills/TEMPLATE.SKILL.md) — Canonical scaffold for generated output
- [skill-frontmatter rules](../../rules/skill-frontmatter.md) — YAML frontmatter requirements
