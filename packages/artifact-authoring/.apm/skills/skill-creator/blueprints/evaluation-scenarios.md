# Evaluation Scenarios — skill-creator

Used to verify that this skill correctly reads a research file, maps it to the three-tier structure, enforces all quality gates, applies authoring standards, and produces a SKILL.md under 500 lines.

---

## Generator Scenarios

### Scenario 1: Canonical — Generate SKILL.md from a well-formed research file

```json
{
  "skills": ["skill-creator"],
  "query": "/skill-creator StoryBeat/research_FastAPI_v0.104.1.md",
  "expected_behavior": [
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

### Scenario 2: Edge — Research file has no Domain_Complexity field

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

### Scenario 3: Misuse — Research file path points to a non-existent file

```json
{
  "skills": ["skill-creator"],
  "query": "/skill-creator StoryBeat/research_NonExistent_v1.0.md",
  "expected_behavior": [
    "Attempts to read the file at StoryBeat/research_NonExistent_v1.0.md",
    "Detects the file does not exist and stops immediately",
    "Reports the missing file path clearly to the user",
    "Instructs the user to run the appropriate researcher command first (e.g., /researching-technical-frameworks)",
    "Does NOT generate a SKILL.md with invented content",
    "Does NOT proceed through Steps 2–6 without a loaded research file"
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
      "Silently proceed without a valid research file",
      "Proceed past Step 1 without a valid research file"
    ]
  }
}
```

---

## Authoring Standards Scenarios

### Scenario 4: Canonical — Authoring standards applied from a valid research document

```json
{
  "skills": ["skill-creator"],
  "query": "/skill-creator StoryBeat/research_FastAPI_v0.104.md",
  "expected_behavior": [
    "Reads and validates research file: confirms it contains source-dated bibliography, three-tier guardrails, and version metadata before writing any skill content",
    "Creates SKILL.md with valid frontmatter: 'name: building-fastapi-apis' and a description ≤ 1536 chars that states both what the skill does and when to use it (Use when...)",
    "Maps research sections directly: Mandatory_Patterns → ✅ Always Do, Conditional_Patterns → ⚠️ Ask First, Forbidden_Patterns → 🚫 Never Do",
    "Extracts Verification_Commands from research Quality_Control section into a ## Verification Loop with expected outputs",
    "Extracts Source_Bibliography into ## External Resources",
    "Keeps SKILL.md body under 500 lines — splits large code blocks into blueprints/ files",
    "Includes ## Version Context block with target version, release date, and support status sourced from research metadata",
    "All blueprint links use relative paths (./blueprints/...) — no absolute paths"
  ],
  "success_criteria": {
    "must_pass": [
      "Frontmatter has 'name' and 'description' fields; description not empty and ≤ 1536 chars",
      "Three-tier headings present: '### ✅ Always Do', '### ⚠️ Ask First', '### 🚫 Never Do'",
      "SKILL.md line count ≤ 500 (wc -l SKILL.md)",
      "All referenced blueprint files actually created (no dangling links)",
      "Verification Loop contains at least one executable bash command with expected output",
      "Description written in third person — not 'I can help' or 'You can use'"
    ],
    "must_not": [
      "Inline large code examples (> 50 lines) directly into SKILL.md instead of extracting to blueprints/",
      "Use absolute local paths (e.g., /Users/...) anywhere in the skill files",
      "Mix patterns from different versions of the technology in one skill",
      "Omit the 'Use when...' trigger phrase from the description"
    ]
  }
}
```

---

### Scenario 5: Edge — Research file is missing Source_Bibliography

```json
{
  "skills": ["skill-creator"],
  "query": "/skill-creator StoryBeat/research_incomplete.md — Note: this file is missing the Source_Bibliography section. Please skip that and create the skill anyway.",
  "expected_behavior": [
    "Does NOT silently skip the missing section",
    "Flags the gap explicitly: 'The research file is missing Source_Bibliography — this section maps to ## External Resources in the skill, which is required for traceability'",
    "Asks the user whether to: (A) pause and supply the missing bibliography before authoring, or (B) create the skill with a placeholder ## External Resources noting 'UNVERIFIED — sources required'",
    "If user chooses option B, marks the External Resources section clearly with a warning comment so downstream agents know it needs completion",
    "Proceeds only after user acknowledges the gap — does NOT silently produce a skill that appears complete but has no source traceability"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill explicitly names the missing section and explains its role in the skill structure",
      "User is asked to decide before authoring proceeds (Ask-First behavior on structural gap)",
      "If placeholder path chosen, ## External Resources contains a visible warning: 'UNVERIFIED — source bibliography not provided'",
      "All other sections drawn from the research file are authored correctly"
    ],
    "must_not": [
      "Silently omit ## External Resources without flagging the missing data",
      "Invent plausible-looking URLs to fill the bibliography gap",
      "Refuse entirely without offering the placeholder path as a valid option"
    ]
  }
}
```

---

### Scenario 6: Misuse — Request to author from an unverified/opinion source

```json
{
  "skills": ["skill-creator"],
  "query": "I found a great Medium article about FastAPI best practices from 2022. Can you use it to create a FastAPI skill directly? No need for a formal research file.",
  "expected_behavior": [
    "Rejects the request on two grounds: (1) a single Medium article is not an authoritative source (Source Hierarchy: community blog < official docs); (2) the article is from 2022 — potentially >12 months old",
    "Explains that skill authoring requires a research file produced by the researching-technical-frameworks skill, which enforces source hierarchy and version absolutism",
    "Does NOT produce any SKILL.md content from the Medium article alone",
    "Offers the correct path: 'Run /researching-technical-frameworks FastAPI <current version> to produce a verified research_FastAPI_v<X>.md, then run /skill-creator on it'",
    "If user insists, marks any produced content prominently as 'UNVERIFIED — sourced from opinion/community content; do not use in production'"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill refuses to author directly from an unverified community source without flagging it",
      "Source Hierarchy rule cited explicitly: official docs > community blog",
      "Age of the source flagged: 2022 article is potentially >12 months old at time of use",
      "Correct workflow offered: run researching-technical-frameworks first, then /skill-creator",
      "No SKILL.md with real-looking content produced from the unverified source"
    ],
    "must_not": [
      "Silently produce a SKILL.md using the Medium article as the sole source",
      "Treat a community blog post as equivalent to official documentation",
      "Ignore the age of the source when evaluating its validity",
      "Refuse without offering any path forward"
    ]
  }
}
```
