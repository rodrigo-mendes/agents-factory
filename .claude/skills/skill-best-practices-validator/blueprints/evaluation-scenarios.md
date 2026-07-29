# Evaluation Scenarios — skill-best-practices-validator

Used to verify that the validator correctly identifies compliant, partially compliant, and violating
Agent Skills — and that it generates accurate, criterion-cited output without hallucinating findings.

## Contents

- [Scenario 1: Canonical — fully compliant skill](#scenario-1-canonical--fully-compliant-skill)
- [Scenario 2: Edge case — stale description limit and missing Never Do alternatives](#scenario-2-edge-case--skill-with-stale-description-limit-and-missing-never-do-alternatives)
- [Scenario 3: Misuse — validator pointed at a non-skills directory](#scenario-3-misuse--validator-pointed-at-a-non-skills-directory)

---

## Scenario 1: Canonical — fully compliant skill

```json
{
  "skills": ["skill-best-practices-validator"],
  "query": "Validate the skills in .claude/skills/",
  "skill_state": {
    "name": "integrating-payments-example",
    "description_chars": 190,
    "body_lines": 266,
    "has_always_do": true,
    "has_ask_first": true,
    "has_never_do": true,
    "has_verification_loop": true,
    "has_external_resources": true,
    "has_evaluation_scenarios": true,
    "never_do_has_alternatives": true,
    "paths_use_forward_slashes": true,
    "name_matches_folder": true
  },
  "expected_behavior": [
    "Reads authoring-agent-skills/SKILL.md and blueprints/three-tier-architecture.md before evaluating",
    "Confirms SKILL.md line count by reading the file (not estimating)",
    "Marks A1 as compliant: name is kebab-case, description is under 1536 chars and includes 'Use when'",
    "Marks A2 as compliant: body under 500 lines",
    "Marks D2 as compliant: all three tiers present and populated",
    "Marks D4 as compliant: verification loop with concrete commands present",
    "Marks D5 as compliant: every Never Do entry has a side-by-side correct alternative",
    "Marks C1 as compliant: evaluation-scenarios.md exists with >= 3 scenarios",
    "Generates [skill-name]-best-practices-review.md with all 8 official criteria rows and 7 team criteria rows",
    "Includes summary matrix in skills-best-practices-summary.md"
  ],
  "success_criteria": {
    "must_pass": [
      "Review file contains exactly 8 official criteria rows (A1-A6, B, C) and 7 team rows (D1-D7)",
      "All criteria marked compliant cite the specific section that was verified",
      "Overall compliance percentage computed correctly",
      "No criteria marked 'not evaluated' when the file was readable"
    ],
    "must_not": [
      "Mark A1 as non-compliant for description length if it is under 1536 chars",
      "Report 1024 chars as the limit — the canonical limit is 1536 chars",
      "Estimate line count without reading the file",
      "Generate the summary matrix without individual review files"
    ]
  }
}
```

---

## Scenario 2: Edge case — skill with stale description limit and missing Never Do alternatives

```json
{
  "skills": ["skill-best-practices-validator"],
  "query": "Check skill quality for .claude/skills/example-skill/",
  "skill_state": {
    "name": "example-skill",
    "description_chars": 1100,
    "body_lines": 320,
    "has_always_do": true,
    "has_ask_first": false,
    "has_never_do": true,
    "never_do_has_alternatives": false,
    "has_verification_loop": false,
    "has_external_resources": false,
    "paths_use_forward_slashes": true,
    "name_matches_folder": true
  },
  "expected_behavior": [
    "Marks A1 as COMPLIANT for description length — 1100 chars is within the 1536 char limit",
    "Marks D2 as PARTIAL — Always Do and Never Do present but Ask First missing",
    "Marks D5 as CRITICAL — Never Do entries present but without correct alternatives side-by-side",
    "Marks D4 as MISSING — no verification loop commands found",
    "Marks D7 as MISSING — no external resources section",
    "Lists D5 (anti-patrones sin alternativa) under ALTA priority recommendations",
    "Lists D2 (guardrails incompletos) under MEDIA priority",
    "Lists D4 and D7 under MEDIA priority"
  ],
  "success_criteria": {
    "must_pass": [
      "A1 description check uses 1536 as the limit — 1100 chars must NOT trigger a violation",
      "D5 violation cites criterion 'D5. Anti-patrones con alternativas' and the specific Never Do section",
      "D2 partial cites which tier is missing (Ask First)",
      "Priority classification is consistent: D5 = ALTA, D2/D4/D7 = MEDIA"
    ],
    "must_not": [
      "Report 1100 chars as a description length violation (limit is 1536, not 1024)",
      "Mark D2 as fully compliant because two of three tiers are present",
      "Mark D5 as acceptable without mentioning missing correct alternatives",
      "Omit the Recomendaciones por Prioridad section"
    ]
  }
}
```

---

## Scenario 3: Misuse — validator pointed at a non-skills directory

```json
{
  "skills": ["skill-best-practices-validator"],
  "query": "Validate the skills in src/main/java/",
  "directory_state": "src/main/java/ contains only .java source files — no SKILL.md files present",
  "expected_behavior": [
    "Performs filesystem inspection (ls/Glob) on the target directory",
    "Finds zero SKILL.md files",
    "States explicitly: 'No SKILL.md files found in src/main/java/ — this does not appear to be a skills directory'",
    "Suggests the user point to .claude/skills/ or provide the correct path via $ARGUMENTS",
    "Does NOT generate review files for non-existent skills",
    "Does NOT produce a summary matrix with zero skills and 0% compliance as if analysis ran"
  ],
  "success_criteria": {
    "must_pass": [
      "Filesystem check is performed before attempting evaluation",
      "Zero skills found is reported explicitly — not silently ignored",
      "User receives a corrective suggestion naming the standard skills directory",
      "No [skill-name]-best-practices-review.md files are created"
    ],
    "must_not": [
      "Generate a compliance matrix with invented skill names",
      "Report 0% compliance as if skills were analyzed and failed",
      "Proceed to evaluation without confirming SKILL.md files exist",
      "Create skills-best-practices-summary.md with empty or fabricated data"
    ]
  }
}
```
