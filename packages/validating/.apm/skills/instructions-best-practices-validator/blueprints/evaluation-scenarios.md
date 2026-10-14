# Evaluation Scenarios — instructions-best-practices-validator

Used to verify that the validator correctly identifies compliant, partially compliant, and violating
custom instruction files — and that it generates accurate, criterion-cited output including the
mandatory applyTo pattern analysis.

---

## Scenario 1: Canonical — fully compliant instruction file

```json
{
  "skills": ["instructions-best-practices-validator"],
  "query": "Validate the instruction files in .github/instructions/",
  "instruction_state": {
    "file": "terraform-standards.instructions.md",
    "name": "terraform-standards",
    "description": "Enforces Terraform v1.11+ coding standards for OCI provider. Use when editing .tf files in the infrastructure layer.",
    "applyTo": "**/*.tf",
    "body_lines": 95,
    "has_role_statement": true,
    "has_version_context": true,
    "has_reasoning_in_rules": true,
    "has_concrete_code_examples": true,
    "paths_use_forward_slashes": true,
    "name_matches_filename": true
  },
  "expected_behavior": [
    "Reads at least 3 existing instruction files as style reference before evaluating",
    "Marks A1 as compliant: name is kebab-case and matches filename without extension",
    "Marks A2 as compliant: description is specific, in third person, and includes 'Use when'",
    "Marks A3 as compliant: applyTo is present with a specific glob pattern using forward slashes",
    "Marks B2 as compliant: rules include justification (e.g. 'because Terraform 1.11 deprecated X')",
    "Marks B3 as compliant: code examples present with correct/incorrect side-by-side",
    "Marks E2 as compliant: role statement present in first line of body",
    "Marks E3 as compliant: Version Context section explicitly states Terraform v1.11+",
    "Produces the applyTo Patterns section showing pattern coverage, overlaps, and gaps",
    "No ALTA priority recommendations generated"
  ],
  "success_criteria": {
    "must_pass": [
      "applyTo field verified as present before any other criterion is checked",
      "Compliance table contains exactly 13 official criteria rows and 6 team convention rows",
      "applyTo Patterns section is present with Cobertura, Conflictos, and Gaps subsections",
      "All compliant items cite the specific section or line where compliance was verified"
    ],
    "must_not": [
      "Mark A3 as violation when applyTo is specific and valid",
      "Omit the applyTo Patterns analysis section from the output",
      "Report the file as non-compliant without citing a specific failing criterion",
      "Generate ALTA recommendations when no critical violations are found"
    ]
  }
}
```

---

## Scenario 2: Edge case — instruction file with missing applyTo and conflicting rules

```json
{
  "skills": ["instructions-best-practices-validator"],
  "query": "Check instruction quality for .github/instructions/",
  "instruction_state": {
    "files": [
      {
        "file": "java-standards.instructions.md",
        "applyTo": null,
        "description": "I help you with Java code",
        "rules_have_reasoning": false,
        "has_concrete_examples": false
      },
      {
        "file": "java-error-handling.instructions.md",
        "applyTo": "**/src/main/java/**/*.java",
        "rule_conflict": "java-standards.instructions.md also targets Java files with contradicting error handling rules when manually attached"
      }
    ]
  },
  "expected_behavior": [
    "Marks A3 for java-standards.instructions.md as CRITICAL (applyTo absent) — file never activates automatically",
    "Marks A2 for java-standards.instructions.md as violation — description is in first person ('I help')",
    "Marks B2 as violation for java-standards.instructions.md — rules present without justification",
    "Marks B3 as violation for java-standards.instructions.md — no concrete code examples",
    "Lists A3 (applyTo ausente) under ALTA priority",
    "Lists A2 (descripción en primera persona) under ALTA priority",
    "Notes potential conflict between java-standards and java-error-handling in the Conflictos Detectados subsection",
    "Marks D3 as partial (conflict risk when java-standards is manually attached alongside java-error-handling)"
  ],
  "success_criteria": {
    "must_pass": [
      "A3 absence is the first and highest-priority finding for java-standards.instructions.md",
      "A2 violation cites the exact phrase 'I help you' as the first-person indicator",
      "ALTA section lists at minimum: applyTo ausente and descripción en primera persona",
      "Conflictos Detectados subsection names both files and the contradicting rules"
    ],
    "must_not": [
      "Mark A3 as acceptable because the file can be manually attached",
      "Mark A2 as acceptable because the description is 'short enough'",
      "Omit the conflict detection between java-standards and java-error-handling",
      "Generate a 0% compliance score without citing specific failing criteria"
    ]
  }
}
```

---

## Scenario 3: Misuse — validator pointed at a source code directory

```json
{
  "skills": ["instructions-best-practices-validator"],
  "query": "Validate instructions in src/main/java/",
  "directory_state": "src/main/java/ contains only .java source files — no .instructions.md or .md rule files present",
  "expected_behavior": [
    "Performs filesystem inspection on the target directory",
    "Finds zero .instructions.md or rule .md files",
    "States explicitly: 'No instruction or rule files found in src/main/java/ — this does not appear to be an instructions directory'",
    "Suggests the user point to .claude/rules/ (Claude Code) or .github/instructions/ (Copilot) instead",
    "Does NOT produce a compliance matrix with invented file names",
    "Does NOT generate INSTRUCTIONS_BEST_PRACTICES_REVIEW.md with fabricated findings"
  ],
  "success_criteria": {
    "must_pass": [
      "Filesystem check performed before any evaluation begins",
      "Zero files found is reported explicitly with a corrective suggestion",
      "Standard directories (.claude/rules/, .github/instructions/) are named as alternatives",
      "No INSTRUCTIONS_BEST_PRACTICES_REVIEW.md is created"
    ],
    "must_not": [
      "Produce a compliance matrix with invented instruction file names",
      "Report 0% compliance as if analysis ran against real files",
      "Proceed past the discovery step without finding valid instruction files",
      "Create output files with fabricated or placeholder data"
    ]
  }
}
```
