# Evaluation Scenarios — skill-creator

Used to verify that this generator correctly reads a research file, maps it to the
three-tier structure, enforces all quality gates (three tiers populated, External
Resources present, evaluation-scenarios.md created and linked), and produces a
SKILL.md under 500 lines.

---

## Scenario 1: Canonical — Generate SKILL.md from a well-formed research file

```json
{
  "skills": ["skill-creator"],
  "query": "/skill-creator StoryBeat/research_FastAPI_v0.104.1.md",
  "expected_behavior": [
    "Loads authoring-agent-skills SKILL.md before processing the research file",
    "Reads StoryBeat/research_FastAPI_v0.104.1.md and derives skill-name = 'fastapi-async-api', tech = 'FastAPI', version = '0.104.1'",
    "Maps 'Mandatory Patterns' from research to ✅ Always Do section",
    "Maps 'Conditional Patterns' from research to ⚠️ Ask First section",
    "Maps 'Forbidden Patterns' from research to 🚫 Never Do section — each with an inline ✅ correct alternative",
    "Maps 'Verification Commands' from research to a Verification Loop section",
    "Maps 'Source Bibliography' from research to an External Resources section",
    "Generated SKILL.md is saved at .claude/skills/fastapi-async-api/SKILL.md",
    "Generated SKILL.md is under 500 lines",
    "Creates blueprints/evaluation-scenarios.md with ≥3 scenarios at .claude/skills/fastapi-async-api/blueprints/evaluation-scenarios.md",
    "Quick Navigation in generated SKILL.md links to ./blueprints/evaluation-scenarios.md",
    "Runs quality checklist self-verification and reports results"
  ],
  "success_criteria": {
    "must_pass": [
      "authoring-agent-skills SKILL.md loaded as Step 1 before any other action",
      "Generated SKILL.md has all three tiers (✅, ⚠️, 🚫) populated — no tier is empty",
      "Every 🚫 Never Do item has an inline ✅ correct alternative",
      "Generated SKILL.md has ## External Resources section with at least one dated link",
      "Generated SKILL.md has a Verification Loop section",
      "blueprints/evaluation-scenarios.md created with ≥3 scenarios (canonical, edge, misuse)",
      "Quick Navigation links to ./blueprints/evaluation-scenarios.md",
      "Generated SKILL.md is < 500 lines"
    ],
    "must_not": [
      "Produce a 🚫 Never Do item without a ✅ correct alternative",
      "Omit the ## External Resources section from the generated SKILL.md",
      "Omit blueprints/evaluation-scenarios.md or leave it unlinked from Quick Navigation",
      "Exceed 500 lines in the generated SKILL.md without extracting to blueprints/",
      "Derive skill-name or version incorrectly from the research file path"
    ]
  }
}
```

---

## Scenario 2: Edge — Research file has no Domain_Complexity field; pattern counts must be assessed

```json
{
  "skills": ["skill-creator"],
  "query": "/skill-creator StoryBeat/research_Redis_v7.2.md",
  "expected_behavior": [
    "Reads the research file and notes the absence of a Domain_Complexity field in metadata",
    "Assesses complexity from research content: Redis v7.2 covers connection pooling, pub/sub, cluster mode, Lua scripting, and security — classifies as 'Standard' tier (5-6 Always Do, 3-4 Ask First, 4-5 Never Do)",
    "Populates pattern counts based on domain needs, not template minimums — does not pad to reach 5 or cut to fit under 6",
    "Generated SKILL.md includes Version Context section with Redis 7.2 target version, release date, and breaking changes from 7.0/7.1",
    "Generated SKILL.md includes all three tiers with domain-appropriate pattern counts",
    "blueprints/evaluation-scenarios.md includes a scenario for Redis cluster mode (edge) and one for anti-pattern trap (misuse: skipping connection pool)",
    "Verification Loop references redis-cli PING and INFO replication commands"
  ],
  "success_criteria": {
    "must_pass": [
      "Complexity tier assessed from research content when Domain_Complexity field is absent",
      "Pattern counts reflect domain needs — no padding or artificial capping",
      "Version Context section present with Redis 7.2 version data",
      "blueprints/evaluation-scenarios.md created with scenarios appropriate to Redis use cases",
      "Verification Loop contains Redis-specific commands, not generic placeholders"
    ],
    "must_not": [
      "Default to exactly 3/2/2 patterns (Foundational minimum) without assessing domain complexity",
      "Leave [placeholder] text in any mandatory section of the generated SKILL.md",
      "Omit the Version Context section because the research file lacks a Release_Date field — derive from research content or mark as 'unverified'"
    ]
  }
}
```

---

## Scenario 3: Misuse — Research file path points to a non-existent file

```json
{
  "skills": ["skill-creator"],
  "query": "/skill-creator StoryBeat/research_NonExistent_v1.0.md",
  "expected_behavior": [
    "Attempts to read the file at StoryBeat/research_NonExistent_v1.0.md",
    "Detects the file does not exist and stops immediately",
    "Reports the missing file path clearly to the user",
    "Instructs the user to run the appropriate researcher command first (e.g., /technical-framework-researcher)",
    "Does NOT generate a SKILL.md with invented content",
    "Does NOT proceed through Steps 2–7 without a loaded research file"
  ],
  "success_criteria": {
    "must_pass": [
      "Clear error message referencing the exact missing path",
      "Instruction to run a researcher command provided",
      "No SKILL.md file written",
      "No blueprints/ directory created"
    ],
    "must_not": [
      "Generate a SKILL.md with generic or hallucinated technology content",
      "Silently use authoring-agent-skills as a substitute for the missing research input",
      "Proceed past Step 1 without a valid research file"
    ]
  }
}
```
