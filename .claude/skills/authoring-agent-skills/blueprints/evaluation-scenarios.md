# Evaluation Scenarios — authoring-agent-skills

Used to verify that the skill activates correctly, enforces three-tier guardrails, requires source-dated research as input, and refuses to author from unverified or opinion-only sources.

---

## Scenario 1 (Canonical): Author a skill from a valid research document

```json
{
  "skills": ["authoring-agent-skills"],
  "query": "Here is the completed research file research_FastAPI_v0.104.md. Please create the skill .claude/skills/building-fastapi-apis/SKILL.md following team conventions.",
  "expected_behavior": [
    "Reads the research file and confirms it contains source-dated bibliography, three-tier guardrails, and version metadata before writing any skill content",
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
      "Three-tier headings present: '## ✅ Always Do', '## ⚠️ Ask First', '## 🚫 Never Do'",
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

## Scenario 2 (Edge): Research file is missing a mandatory section

```json
{
  "skills": ["authoring-agent-skills"],
  "query": "Please author a skill from this research file. I notice it's missing the Source_Bibliography section — just skip that and create the skill anyway.",
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

## Scenario 3 (Misuse): Request to author from an unverified / opinion source

```json
{
  "skills": ["authoring-agent-skills"],
  "query": "I found a great Medium article about FastAPI best practices from 2022. Can you use it to create a FastAPI skill directly? No need for a formal research file.",
  "expected_behavior": [
    "Rejects the request on two grounds: (1) a single Medium article is not an authoritative source (Source Hierarchy: community blog < official docs); (2) the article is from 2022 — potentially >12 months old, which the source hierarchy rejects unless it documents the current stable version",
    "Explains that skill authoring requires a research file produced by the researching-technical-frameworks skill, which enforces source hierarchy and version absolutism",
    "Does NOT produce any SKILL.md content from the Medium article alone",
    "Offers the correct path: 'Run /technical-framework-researcher FastAPI <current version> to produce a verified research_FastAPI_v<X>.md, then return here to author the skill'",
    "If user insists, marks any produced content prominently as 'UNVERIFIED — sourced from opinion/community content; do not use in production'"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill refuses to author directly from an unverified community source without flagging it",
      "Source Hierarchy rule cited explicitly: official docs > community blog",
      "Age of the source flagged: 2022 article is potentially >12 months old at time of use",
      "Correct workflow offered: run researching-technical-frameworks first, then author",
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
