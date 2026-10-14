# Evaluation Scenarios — methodologies-skill-generator

Used to verify that this generator correctly classifies methodologies, produces SKILL.md
files that are complete (three-tier guardrails, evaluation-scenarios, External Resources,
Verification Loop), and refuses Tier 5 sources or version-mixed guidance. Scenarios also
verify that the generator correctly handles methodology-specific requirements such as
conditional Flow Metrics sections.

---

## Scenario 1: Canonical — Generate Kanban SKILL.md (Flow & Delivery)

```json
{
  "skills": ["methodologies-skill-generator"],
  "query": "Generate a SKILL.md for Kanban Guide 2020 for a platform engineering team managing 3 internal services using Jira and GitHub.",
  "expected_behavior": [
    "Classifies methodology as 'Flow & Delivery' before researching",
    "Sources mandatory elements from Kanban Guide 2020 at kanban.university (Tier 1)",
    "Generated SKILL.md contains all three tiers: ✅ Always Do, ⚠️ Ask First, 🚫 Never Do",
    "Every 🚫 Never Do item has an inline ✅ correct alternative",
    "Flow Metrics section (Section 6) is present because Kanban defines cycle time, lead time, and throughput",
    "Generated SKILL.md includes a Verification Loop section",
    "Generated SKILL.md includes an External Resources section with a dated link to kanban.university",
    "Creates blueprints/evaluation-scenarios.md with ≥3 scenarios (canonical, edge, misuse)",
    "Links evaluation-scenarios.md from Quick Navigation in the generated SKILL.md",
    "Generated SKILL.md is under 500 lines",
    "Phase 4 self-validation checklist is run with no unresolved failures"
  ],
  "success_criteria": {
    "must_pass": [
      "Phase 1 classification completed before research begins",
      "Kanban Guide 2020 (Tier 1) cited in Research Confidence Report",
      "Generated SKILL.md has ✅, ⚠️, and 🚫 sections all populated",
      "WIP limits appear as ✅ Always Do rule (mandatory per Kanban Guide)",
      "Flow Metrics section present and includes cycle time definition",
      "blueprints/evaluation-scenarios.md created and linked from Quick Navigation",
      "External Resources section present with dated link"
    ],
    "must_not": [
      "Omit WIP limits from ✅ Always Do (they are mandatory in Kanban Guide 2020)",
      "Include Tier 5 sources in the generated SKILL.md",
      "Produce a 🚫 Never Do item without a ✅ correct alternative",
      "Exceed 500 lines without extracting to blueprints/",
      "Mix Kanban Guide 2020 with pre-2020 David Anderson Kanban guidance without marking the difference"
    ]
  }
}
```

---

## Scenario 2: Edge — Structural methodology without flow metrics (Team Topologies)

```json
{
  "skills": ["methodologies-skill-generator"],
  "query": "Generate a SKILL.md for Team Topologies for a scaled engineering org with 5 squads across 2 domains.",
  "expected_behavior": [
    "Classifies methodology as 'Organizational Design'",
    "Sources Skelton & Pais 'Team Topologies' book (Tier 2) and teamtopologies.com (Tier 2)",
    "Correctly omits Flow Metrics section (Section 6) because Team Topologies does not define measurable flow outcomes — it is structural",
    "Generated SKILL.md three-tier section covers team interaction mode guardrails (e.g., ✅ always define team interaction modes explicitly, 🚫 never assign a team to collaboration mode permanently without a trigger to transition)",
    "Generated SKILL.md includes cognitive load as a ✅ Always Do constraint",
    "blueprints/evaluation-scenarios.md created with ≥3 scenarios relevant to Team Topologies use (team mapping, interaction mode selection, anti-pattern detection)",
    "Generated SKILL.md Verification Loop includes self-check questions appropriate for structural methodology (not pipeline commands)"
  ],
  "success_criteria": {
    "must_pass": [
      "Flow Metrics section (Section 6) is absent from the generated SKILL.md",
      "Classification is 'Organizational Design', not generic",
      "Three team types (stream-aligned, platform, enabling, complicated-subsystem) all defined in Methodology Facts",
      "Three interaction modes (collaboration, x-as-a-service, facilitating) defined with guardrails",
      "blueprints/evaluation-scenarios.md created and linked"
    ],
    "must_not": [
      "Include a Flow Metrics section with cycle time / lead time for Team Topologies",
      "Use Spotify Model as a synonym or replacement for Team Topologies",
      "Mark community-derived interaction mode heuristics as [HIGH] confidence"
    ]
  }
}
```

---

## Scenario 3: Misuse — User provides ambiguous edition and expects generator to guess

```json
{
  "skills": ["methodologies-skill-generator"],
  "query": "Generate a SKILL.md for Scrum for a 6-person backend team.",
  "expected_behavior": [
    "Asks the user to specify the Scrum Guide edition (2017 vs 2020) before proceeding — does not infer or default silently",
    "Explains that Scrum Guide 2020 removed sub-team roles and introduced 'Developers' as a single role, while 2017 had Development Team, Scrum Master, and Product Owner separately defined — these produce different artifact templates",
    "After receiving the edition (e.g., 2020), proceeds with research sourcing scrumguides.org (Tier 1)",
    "Generated SKILL.md marks any 2017-only patterns as deprecated with Scrum Guide 2020 replacement",
    "Does NOT mix 2017 and 2020 patterns in the same SKILL.md without explicit deprecation markers",
    "Three-tier guardrails reflect Scrum Guide 2020: ✅ Sprint Goal is mandatory (added in 2020), 🚫 never use story points as the only measure (not in official guide)"
  ],
  "success_criteria": {
    "must_pass": [
      "Generator asks clarifying question about edition before researching",
      "Research Confidence Report cites scrumguides.org as Tier 1 for the specified edition",
      "Generated SKILL.md pins to a single edition with no silent version mixing",
      "Deprecated 2017 practices explicitly marked with replacement",
      "Sprint Goal appears as ✅ Always Do mandatory element (Scrum Guide 2020)"
    ],
    "must_not": [
      "Default to Scrum Guide 2020 without asking when edition is unspecified",
      "Mix 2017 Development Team role definition with 2020 Developers role silently",
      "Include story points as a ✅ mandatory pattern (not in official Scrum Guide)",
      "Use a Tier 5 source (e.g., Mountain Goat Software blog) as the primary Scrum reference"
    ]
  }
}
```
