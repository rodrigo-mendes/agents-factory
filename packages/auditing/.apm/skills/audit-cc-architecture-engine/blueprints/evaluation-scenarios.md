# Evaluation Scenarios — audit-cc-architecture-engine

Used to verify the skill correctly maps the Claude Code loading landscape, simulates the budget,
detects auto-listing bloat / name collisions / field swaps, and avoids conflating redundancy with
contradiction.

---

## Scenario 1: Canonical audit — loading landscape and budget simulation (standard path)

```json
{
  "skills": ["audit-cc-architecture-engine"],
  "query": "Audit the engine mechanics for the framework-researcher subagent.",
  "expected_behavior": [
    "Maps the Loading Landscape: always-on (CLAUDE.md + auto-listed skill descriptions), passive (paths: rules), active (context: fork commands)",
    "Counts skills WITHOUT disable-model-invocation (auto-listing budget cost) and confirms deliberate commands set disable-model-invocation: true (ECC.4/ECC.5)",
    "Reads CLAUDE.md and each rule/skill and estimates line counts from actual reads",
    "Simulates the budget for a representative task: always-on + passive + active = combined vs practical limit, with BUDGET STATUS",
    "Evaluates ECC.1–ECC.3 (paths:), ECC.4–ECC.5/ECC.13 (auto-listing/budget), ECC.6–ECC.7 (fork/disclosure), ECC.8–ECC.12/ECC.16–ECC.18 (frontmatter/governance), ECC.14–ECC.15 (conflicts)",
    "Produces the name-collision table and the field-swap table",
    "Scores each component with the 25%/25%/20%/15%/15% weights",
    "Generates CC_ENGINE_MECHANICS_AUDIT_REPORT.md as a single complete file"
  ],
  "success_criteria": {
    "must_pass": [
      "Budget simulation includes actual line counts (estimated from file reads), not placeholders",
      "Auto-invocable skills are counted and deliberate commands verified for disable-model-invocation",
      "name uniqueness check (ECC.11) runs across ALL skills, agents, and rules",
      "The field-swap table (tools:/allowed-tools:) is produced",
      "Report file is named CC_ENGINE_MECHANICS_AUDIT_REPORT.md and contains all 8 sections"
    ],
    "must_not": [
      "Report redundancy as a critical conflict — redundancy wastes budget but does not break behavior (⚠️ not ❌)",
      "Assume a paths: pattern fires without verifying files the work actually touches",
      "Skip the budget calculation"
    ]
  }
}
```

---

## Scenario 2: Edge case — over-broad `paths:` pattern (rule applies to everything)

```json
{
  "skills": ["audit-cc-architecture-engine"],
  "query": "Audit the engine mechanics. One rule has paths: **/*.",
  "expected_behavior": [
    "Detects the over-broad paths: **/* and evaluates it against ECC.2 (no over-match)",
    "Assesses whether the rule content is genuinely project-wide (appropriate for **/*) or scoped (should be narrowed)",
    "Marks ❌ if the rule contains scoped rules that should not apply to all files",
    "Marks ⚠️ if the rule holds only project-wide conventions and the broad pattern is intentional",
    "Calculates budget impact: a globally-firing rule adds to EVERY task scenario",
    "Simulates the worst-case: the task that triggers the most rules simultaneously",
    "Checks whether the global rule contradicts any scoped rule or CLAUDE.md (ECC.14)"
  ],
  "success_criteria": {
    "must_pass": [
      "ECC.1 and ECC.2 are both evaluated — matches intended files AND does not over-match",
      "Budget impact is calculated for the maximum-firing scenario, not just the average",
      "Recommendation specifies a narrower paths: glob if over-matching is confirmed"
    ],
    "must_not": [
      "Automatically flag **/* as wrong — it is correct for genuinely global conventions (ECC.1 pass + ECC.2 warning)",
      "Skip the conflict check between the global rule and scoped rules"
    ]
  }
}
```

---

## Scenario 3: Misuse — user requests fixing the frontmatter conflicts found

```json
{
  "skills": ["audit-cc-architecture-engine"],
  "query": "The engine audit found two skills with the same name value and one subagent using allowed-tools:. Fix the YAML in all of them for me.",
  "expected_behavior": [
    "Declines to edit files — states that implementing fixes is outside the engine auditor's scope",
    "Explains that Model C identifies and reports engine-level issues but does not modify files",
    "Provides the remediation from the report: which two files collide on name (ECC.11), what each should be renamed to, and the subagent whose allowed-tools: must become tools: (ECC.8)",
    "Explains why name collisions cause silent shadowing and why the field swap breaks the artifact",
    "Confirms the report already contains Proposed Change blocks for these fixes"
  ],
  "success_criteria": {
    "must_pass": [
      "No file is modified or written",
      "The collision is described precisely: file paths + current name values + proposed unique names",
      "The field swap is described precisely: file + wrong field + correct field",
      "The silent-shadowing mechanism is explained"
    ],
    "must_not": [
      "Edit YAML frontmatter in any file",
      "Generate corrected file content beyond what is in the report's Proposed Change blocks"
    ]
  }
}
```

---

## Scenario 4: Auto-listing budget pressure — many auto-invocable skills

```json
{
  "skills": ["audit-cc-architecture-engine"],
  "query": "Audit the engine mechanics for a project where many operational skills lack disable-model-invocation and therefore all auto-list.",
  "expected_behavior": [
    "Identifies every SKILL.md without disable-model-invocation — each has its name + description surfaced always (ECC.4)",
    "Distinguishes intended auto-invocable meta/knowledge skills from operational commands that SHOULD set disable-model-invocation: true (ECC.5)",
    "Estimates the auto-listing cost (sum of name + description across auto-listed skills) and adds it to the always-on budget (ECC.13)",
    "Reports BUDGET STATUS with actual numbers",
    "Recommends adding disable-model-invocation: true to the operational commands to move them off the auto-listing budget"
  ],
  "success_criteria": {
    "must_pass": [
      "Auto-listing cost is derived from actual description lengths, not a flat estimate",
      "Only operational commands missing disable-model-invocation are flagged — genuine knowledge skills are not",
      "The budget recommendation quantifies the savings from moving commands off the auto-list"
    ],
    "must_not": [
      "Flag every auto-invocable skill as bloat — meta/knowledge skills are supposed to auto-list",
      "Report budget pressure as a critical conflict — it is ⚠️ unless it demonstrably exceeds practical limits"
    ]
  }
}
```
