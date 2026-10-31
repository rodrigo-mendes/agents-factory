# Evaluation Scenarios — writing-technical-book

4 required scenario types for skill evaluation via `skill-evaluator`.

---

## Scenario 1 — Canonical Path

```json
{
  "skills": ["writing-technical-book"],
  "query": "/writing-technical-book \"Event-Driven Architecture\" audience=\"senior backend engineers\" context=\"cloud-native microservices\" chapters=8 depth=standard",
  "expected_behavior": [
    "Validates all 3 required inputs (topic, audience, context) are present",
    "Acknowledges depth=standard and chapters=5",
    "Enters planning mode (EnterPlanMode) to present TOC",
    "TOC contains exactly 5 chapters with objectives, descriptions, and key concepts",
    "Does NOT start writing prose before user approves the TOC"
  ],
  "success_criteria": {
    "must_pass": [
      "Presents TOC via EnterPlanMode before any prose generation",
      "TOC has exactly 5 chapters matching the domain",
      "Each chapter entry includes: objective, description, and key concepts list",
      "Pipeline halts at P3 awaiting user approval"
    ],
    "must_not": [
      "Start generating prose before TOC approval",
      "Skip the EnterPlanMode gate",
      "Generate EPUB or translations before chapters are written",
      "Produce fewer or more than 5 chapters"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Missing Required Input

```json
{
  "skills": ["writing-technical-book"],
  "query": "/writing-technical-book \"Distributed Systems\" chapters=10",
  "expected_behavior": [
    "Detects that 'audience' and 'context' parameters are missing",
    "Aborts with a clear error message listing the missing required parameters",
    "Does NOT proceed to any pipeline phase",
    "Provides example of correct invocation"
  ],
  "success_criteria": {
    "must_pass": [
      "Identifies missing 'audience' parameter",
      "Identifies missing 'context' parameter",
      "Outputs a helpful error message with correct usage example",
      "Does not write any files"
    ],
    "must_not": [
      "Proceed to TOC research with missing inputs",
      "Guess or infer the missing parameters without user input",
      "Write book_metadata.md or any other file before inputs are validated"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Wrong Command

```json
{
  "skills": ["writing-technical-book"],
  "query": "/writing-technical-book — please write me a novel about a developer who builds an AI",
  "expected_behavior": [
    "Recognizes that a fiction novel is not within scope for this skill",
    "Declines the request clearly",
    "Explains that this skill generates technical non-fiction books",
    "Optionally suggests re-framing as a technical book topic"
  ],
  "success_criteria": {
    "must_pass": [
      "Declines to generate a fiction novel",
      "Explains the skill's actual scope (technical non-fiction)",
      "Does not proceed to pipeline execution"
    ],
    "must_not": [
      "Generate a TOC for a fiction novel",
      "Attempt to run the pipeline for non-technical content",
      "Silently proceed with a misinterpreted scope"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: chapters > 15

```json
{
  "skills": ["writing-technical-book"],
  "query": "/writing-technical-book \"Kubernetes Deep Dive\" audience=\"platform engineers\" context=\"enterprise cloud\" chapters=20",
  "expected_behavior": [
    "Detects chapters=20 exceeds the warning threshold of 15",
    "Warns the user that this will take very significant time and compute",
    "Asks for confirmation before proceeding",
    "Does NOT silently start the 20-chapter pipeline"
  ],
  "success_criteria": {
    "must_pass": [
      "Warns about chapters > 15 before starting",
      "Explicitly asks user to confirm before proceeding",
      "Explains the time/cost implication of 20 chapters"
    ],
    "must_not": [
      "Silently start pipeline with 20 chapters",
      "Reduce chapters to 15 without asking",
      "Refuse entirely without offering to proceed if confirmed"
    ]
  }
}
```
