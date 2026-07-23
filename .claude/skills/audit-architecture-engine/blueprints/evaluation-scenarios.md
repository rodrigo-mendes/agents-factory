# Evaluation Scenarios — audit-architecture-engine

Used to verify the skill correctly simulates passive injection scenarios, detects applyTo
conflicts and context budget pressure, and avoids conflating redundancy with contradiction.

---

## Scenario 1: Canonical audit — injection landscape and conflict detection (standard path)

```json
{
  "skills": ["audit-architecture-engine"],
  "query": "Audit the engine mechanics for the oci-terraform agent.",
  "expected_behavior": [
    "Reads every instruction file associated with oci-terraform and extracts each applyTo glob pattern",
    "Builds the Passive Injection Map: for each file type the agent creates (*.tf, *.tfvars, *.tftest.hcl, *.yml), lists which instructions auto-inject",
    "Builds the Active Loading Map: for each agent/prompt P0 trigger keyword, lists which skill files are explicitly read",
    "Simulates at least one injection scenario per file type: lists passive instructions with line counts, active skills with line counts, combined total, and budget status",
    "Evaluates criteria C.1–C.5 (applyTo correctness), C.6–C.8 (injection volume), C.9–C.11 (conflict detection), C.12–C.18 (active path), C.19–C.24 (frontmatter)",
    "Distinguishes redundant rules (same content in multiple files) from contradictory rules (rules that cannot both be true)",
    "Scores each component with the 30%/25%/20%/15%/10% weights and produces an overall score",
    "Generates TECHNICAL_MECHANISMS_AUDIT_REPORT.md as a single complete file"
  ],
  "success_criteria": {
    "must_pass": [
      "Injection scenarios include actual line counts (estimated from file reads) — not placeholder text",
      "Every applyTo pattern is verified against actual file types the agent creates (not assumed)",
      "Conflict analysis distinguishes redundancy (⚠️ wastes context) from contradiction (❌ breaks behavior)",
      "Frontmatter name uniqueness check (C.19) is run across ALL instruction, prompt, and skill files",
      "Report file is named TECHNICAL_MECHANISMS_AUDIT_REPORT.md and contains all 8 sections"
    ],
    "must_not": [
      "Report 'redundancy' as a critical conflict — redundancy wastes context but does not cause errors (C.7 ⚠️ not ❌)",
      "Assume an applyTo pattern fires without verifying file types the agent actually creates",
      "Skip the context budget calculation — it is the most quantitative and actionable finding"
    ]
  }
}
```

---

## Scenario 2: Edge case — global applyTo pattern (instruction applies to all files)

```json
{
  "skills": ["audit-architecture-engine"],
  "query": "Audit the engine mechanics for the framework-researcher agent. One of its instructions has applyTo: **/*.",
  "expected_behavior": [
    "Detects the global applyTo: **/* pattern and evaluates it against C.2 (no over-matching)",
    "Assesses whether the instruction's content is genuinely project-wide (appropriate for **/*) or domain-specific (should be narrowed)",
    "Marks as ❌ if the instruction contains domain-specific rules that should not apply to all file types",
    "Marks as ⚠️ if the instruction contains only project-wide conventions and the broad pattern is intentional",
    "Calculates context budget impact: a globally-injected instruction contributes to EVERY file-type scenario",
    "Simulates the worst-case injection scenario: the file type that triggers the most instructions simultaneously",
    "Checks if the global instruction's content conflicts with any domain-specific instruction (C.9, C.11)"
  ],
  "success_criteria": {
    "must_pass": [
      "C.1 and C.2 are both evaluated — matches intended files AND does not over-match",
      "Budget impact is calculated for the maximum-injection scenario, not just the average",
      "Recommendation specifies a narrower glob pattern if over-matching is confirmed"
    ],
    "must_not": [
      "Automatically flag **/* as wrong — it is correct for genuinely global conventions (C.1 pass + C.2 warning)",
      "Skip the conflict check between global and domain-specific instructions"
    ]
  }
}
```

---

## Scenario 3: Misuse — user requests fixing the frontmatter conflicts found

```json
{
  "skills": ["audit-architecture-engine"],
  "query": "The engine audit found two instructions with the same `name` value. Fix the YAML in both files for me.",
  "expected_behavior": [
    "Declines to edit instruction files — explicitly states that implementing fixes is outside the technical mechanisms auditor's scope",
    "Explains that Model C identifies and reports engine-level issues but does not modify project files",
    "Provides the remediation guidance from the report: specifies exactly which two files have colliding name values, what each should be renamed to, and why uniqueness matters for VS Code deduplication",
    "Confirms that the TECHNICAL_MECHANISMS_AUDIT_REPORT.md already contains a Proposed Change block for this fix"
  ],
  "success_criteria": {
    "must_pass": [
      "No instruction file is modified or written",
      "The specific collision is described precisely: file paths + current name values + proposed unique names",
      "The VS Code deduplication mechanism (why name collisions cause one instruction to drop silently) is explained"
    ],
    "must_not": [
      "Edit YAML frontmatter in any project file",
      "Generate corrected instruction file content beyond what is already in the report's Proposed Change block"
    ]
  }
}
```

---

## Scenario 4: Context budget pressure — instruction pile-up on a single file type

```json
{
  "skills": ["audit-architecture-engine"],
  "query": "Audit the engine mechanics for a project where four instruction files all match *.tf files.",
  "expected_behavior": [
    "Identifies all four instructions as injecting simultaneously when a *.tf file is opened",
    "Reads all four files and estimates their line counts",
    "Calculates combined passive injection total and adds the always-on copilot-instructions.md lines",
    "Compares total against the practical limit (~500 lines combined) per criterion C.6",
    "Checks for redundant rules across the four files (C.7) — same rules appearing in multiple instructions waste context",
    "Reports BUDGET STATUS as ✅ Within limits / ⚠️ Approaching limit / ❌ Exceeds limit with the actual numbers",
    "Recommends consolidation of redundant rules into a single instruction to reduce injection volume if budget is stressed"
  ],
  "success_criteria": {
    "must_pass": [
      "Line counts are derived from actual file reads — not estimated as a flat number",
      "Combined total includes copilot-instructions.md (always injected) in the budget calculation",
      "Redundancy analysis lists each duplicated rule, both files it appears in, and which file should keep it",
      "Budget recommendation quantifies the savings from consolidation (e.g., removing N duplicate lines)"
    ],
    "must_not": [
      "Skip the budget calculation because 'there are many instructions'",
      "Report budget pressure as a critical conflict — it is ⚠️ Approaching limit, not ❌ unless it demonstrably exceeds practical limits"
    ]
  }
}
```
