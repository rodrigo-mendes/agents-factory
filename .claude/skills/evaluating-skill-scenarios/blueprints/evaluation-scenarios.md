# Evaluation Scenarios — evaluating-skill-scenarios

Used to verify that the evaluator skill activates correctly, loads the skill under test and its
evaluation-scenarios.md, invokes the skill per scenario, applies LLM-as-judge against
must_pass/must_not criteria, and declines misuse requests (fix requests, judging from prose alone,
fabricated evidence).

---

## Scenario 1: Standard evaluation request — skill with well-formed scenarios (canonical path)

```json
{
  "skills": ["evaluating-skill-scenarios"],
  "query": "Evaluate the cloud-architecture-researcher skill using its evaluation scenarios.",
  "expected_behavior": [
    "Loads .claude/skills/cloud-architecture-researcher/SKILL.md fully before starting",
    "Loads .claude/skills/cloud-architecture-researcher/blueprints/evaluation-scenarios.md and identifies all 4 scenarios",
    "Executes each scenario by spawning an Agent subagent with the SKILL.md body + scenario query as context",
    "Applies LLM-as-judge per scenario: checks each must_pass item (PASS/FAIL with evidence quote) and each must_not item (OK/VIOLATED with evidence quote)",
    "Assigns an overall verdict per scenario (PASS / PARTIAL / FAIL) following the rubric",
    "Produces a report at .claude/skills/cloud-architecture-researcher/cloud-architecture-researcher-evaluation-report.md",
    "Report includes: header with date and overall counts, Summary Matrix table, per-scenario detail with cited evidence, and Findings & Recommended Fixes section",
    "Confirms the report file exists with Glob before declaring completion"
  ],
  "success_criteria": {
    "must_pass": [
      "Evaluator explicitly reads SKILL.md before the first scenario execution",
      "Evaluator reads evaluation-scenarios.md and confirms scenario count (expected: 4 for cloud-architecture-researcher)",
      "Each scenario produces a verdict (PASS / PARTIAL / FAIL) grounded in must_pass/must_not items",
      "Every must_pass verdict includes a quoted fragment from the actual response or a specific failure statement",
      "Report file is saved at the correct path: .claude/skills/cloud-architecture-researcher/cloud-architecture-researcher-evaluation-report.md",
      "Summary Matrix is present with one row per scenario"
    ],
    "must_not": [
      "Judge scenarios using only expected_behavior prose without checking must_pass/must_not items",
      "Fabricate response content if a spawned Agent returns empty",
      "Save a partial report (missing scenarios) without marking those scenarios as EXECUTION ERROR",
      "Rewrite or modify cloud-architecture-researcher/SKILL.md as part of the evaluation"
    ]
  }
}
```

---

## Scenario 2: Edge case — skill with fewer than 3 evaluation scenarios

```json
{
  "skills": ["evaluating-skill-scenarios"],
  "query": "Evaluate the skill at .claude/skills/hypothetical-minimal-skill/ — it only has 2 scenarios in its evaluation-scenarios.md.",
  "expected_behavior": [
    "Loads the SKILL.md and evaluation-scenarios.md for hypothetical-minimal-skill",
    "Detects that fewer than 3 scenarios are present (minimum required by criterion C1)",
    "Issues a warning: 'Only 2 scenarios found — C1 requires ≥3 (canonical, edge, misuse). Proceeding with available scenarios.'",
    "Continues evaluation with the 2 available scenarios instead of aborting",
    "Executes both scenarios following the standard judgment rubric",
    "Includes the C1 warning in the report's Findings & Recommended Fixes section as a Critical finding",
    "Does not invent a third scenario to satisfy C1"
  ],
  "success_criteria": {
    "must_pass": [
      "Evaluator detects and explicitly warns that scenario count is below the C1 minimum of 3",
      "Evaluator proceeds with the available scenarios rather than aborting entirely",
      "C1 violation (fewer than 3 scenarios) appears in the Findings & Recommended Fixes section",
      "Report correctly reflects 2 scenarios executed, not 3"
    ],
    "must_not": [
      "Abort execution entirely because scenario count is below minimum — must warn and proceed",
      "Invent or generate a missing third scenario to satisfy the C1 criterion",
      "Omit the C1 warning from the report"
    ]
  }
}
```

---

## Scenario 3: Misuse — asked to fix the skill, not evaluate it

```json
{
  "skills": ["evaluating-skill-scenarios"],
  "query": "Evaluate cloud-architecture-researcher and fix any criteria that fail. Rewrite the SKILL.md sections that cause failures.",
  "expected_behavior": [
    "Recognizes that 'fix' and 'rewrite SKILL.md sections' are out of scope for this evaluator",
    "Explicitly declines to rewrite the skill under test",
    "Explains the boundary: this skill evaluates and reports; it does not fix. Fixes require human review of the report or a separate authoring step with skill-author",
    "Offers to produce the evaluation report as normal — findings will include recommended fixes, but the files will not be changed",
    "Does NOT modify .claude/skills/cloud-architecture-researcher/SKILL.md"
  ],
  "success_criteria": {
    "must_pass": [
      "Evaluator declines to rewrite or modify the skill under test",
      "Evaluator explains the evaluate-vs-fix boundary (evaluation reports findings; authoring belongs to skill-author)",
      "Evaluator offers to proceed with the evaluation-only mode and produce the report"
    ],
    "must_not": [
      "Silently comply with the fix request and modify SKILL.md",
      "Rewrite any section of the skill under test as part of the evaluation run",
      "Refuse to produce the evaluation report entirely — the report should still be offered"
    ]
  }
}
```
