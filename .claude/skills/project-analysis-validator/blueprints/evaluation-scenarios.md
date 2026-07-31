# Evaluation Scenarios — project-analysis-validator

Used to verify that this skill correctly enumerates artifacts, reads all reference files, grades
all seven dimensions, detects anti-patterns, and produces a well-structured report.

---

## Scenario 1: Canonical — Healthy project with minor count drift

```json
{
  "skills": ["project-analysis-validator"],
  "query": "/project-analysis-validator .claude/",
  "expected_behavior": [
    "Uses Glob to enumerate all .claude/skills/*/SKILL.md files — never trusts CLAUDE.md counts",
    "Reads CLAUDE.md fully before grading P2",
    "Reads all .claude/agents/*.md files before grading P3 and P4",
    "Reads .claude/rules/skill-frontmatter.md for frontmatter conventions before grading P3",
    "Grades P1 ✅ when all required dirs (agents/, skills/, rules/) and CLAUDE.md are present",
    "Grades P2 ⚠️ when CLAUDE.md skill count is off by 1 from disk count",
    "Grades P3 ✅ when all agent/skill frontmatter fields are present and valid",
    "Grades P4 ✅ when every context:fork skill has an agent: that resolves to a real file",
    "Saves report to .claude/project-analysis-report.md",
    "Every finding cites dimension + file path + specific evidence"
  ],
  "success_criteria": {
    "must_pass": [
      "Actual skill count confirmed via Glob before P2 grade is assigned",
      "Report file saved to .claude/project-analysis-report.md",
      "All 7 dimensions graded (✅ / ⚠️ / 🚫)",
      "P2 grade reflects disk count, not CLAUDE.md claim"
    ],
    "must_not": [
      "Report CLAUDE.md's stated count as the actual count without verifying with Glob",
      "Grade any dimension Pass without reading the relevant files",
      "Edit or fix any audited file — read-only validator only"
    ]
  }
}
```

---

## Scenario 2: Edge — Project with a broken agent reference

```json
{
  "skills": ["project-analysis-validator"],
  "query": "/project-analysis-validator .claude/",
  "context": "One skill has 'agent: nonexistent-agent' but .claude/agents/nonexistent-agent.md does not exist",
  "expected_behavior": [
    "Reads every .claude/skills/*/SKILL.md and collects all agent: field values",
    "For each agent: value, checks whether .claude/agents/<value>.md exists on disk",
    "Detects 'agent: nonexistent-agent' has no matching file in .claude/agents/",
    "Grades P4 🚫 Fail with finding: 'P4 — skill <name>/SKILL.md: agent: nonexistent-agent resolves to .claude/agents/nonexistent-agent.md which does not exist'",
    "Grades overall project health as 🚫 due to P4 Fail",
    "Includes this finding in the 🚫 Critical section of the report"
  ],
  "success_criteria": {
    "must_pass": [
      "P4 graded 🚫 Fail — not ⚠️ Warn — for a broken agent: reference",
      "Finding cites exact skill path and the missing agent file path",
      "Critical section of report lists this as a blocking issue"
    ],
    "must_not": [
      "Grade P4 as Pass or Warn when a broken agent: reference exists",
      "Accept that the agent file 'might exist elsewhere' — check the exact path .claude/agents/<name>.md",
      "Omit the finding from the Critical recommendations section"
    ]
  }
}
```

---

## Scenario 3: Misuse — Non-standard project layout

```json
{
  "skills": ["project-analysis-validator"],
  "query": "/project-analysis-validator src/agents/",
  "context": "User passes a non-standard root that contains an 'agents/' subdir but no 'skills/' or CLAUDE.md",
  "expected_behavior": [
    "Enumerates contents of the given root directory",
    "Detects that 'skills/' directory is absent",
    "Detects that CLAUDE.md is absent at the given root",
    "Does NOT proceed to grade P2–P7 without the required structural elements",
    "Asks the user to confirm the project layout before continuing (Ask-First behavior)",
    "Explains which required dirs/files are missing and what is expected for a valid project root"
  ],
  "success_criteria": {
    "must_pass": [
      "P1 graded 🚫 Fail when skills/ or CLAUDE.md is absent",
      "User is asked to confirm the layout before grading P2–P7",
      "Missing items listed explicitly: which dirs/files are absent"
    ],
    "must_not": [
      "Proceed to grade P2–P7 when P1 is a hard Fail (missing required dirs)",
      "Assume the project is healthy because an agents/ dir was found",
      "Silently skip the missing dirs and produce a partial report without flagging the structural gap"
    ]
  }
}
```
