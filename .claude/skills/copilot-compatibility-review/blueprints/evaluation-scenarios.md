# Evaluation Scenarios — copilot-compatibility-review

Used to verify that the validator correctly identifies compliant, partially compliant, and violating
GitHub Copilot assets — and that it generates an accurate, reference-linked output without inventing
findings or failing on inaccessible external dependencies.

---

## Scenario 1: Canonical — fully compliant Copilot project

```json
{
  "skills": ["copilot-compatibility-review"],
  "query": "Review the Copilot assets in .github/ for compatibility.",
  "project_state": {
    "agents": [
      {
        "file": "oci-architect.agent.md",
        "has_yaml_frontmatter": true,
        "name": "oci-architect",
        "name_is_kebab_case": true,
        "description_present": true,
        "tools_declared": true
      }
    ],
    "instructions": [
      {
        "file": "terraform-standards.instructions.md",
        "has_yaml_frontmatter": true,
        "applyTo": "**/*.tf",
        "description_present": true
      }
    ],
    "prompts": [
      {
        "file": "design-api-gateway.prompt.md",
        "has_yaml_frontmatter": true,
        "name": "design-api-gateway",
        "agent_field_present": true,
        "description_present": true
      }
    ],
    "skills": [
      {
        "path": ".github/skills/provisioning-oci-functions/SKILL.md",
        "has_yaml_frontmatter": true,
        "name": "provisioning-oci-functions",
        "description_present": true
      }
    ],
    "readme": {
      "has_supported_environments_section": true,
      "values_correct": true
    }
  },
  "expected_behavior": [
    "Searches for official GitHub Copilot documentation before evaluating any asset",
    "Reads all found assets before writing any finding",
    "Lists all assets found by type in each section (Archivo Actual)",
    "Reports no ALTA priority problems — all required fields are present and valid",
    "RESUMEN DE ACCIONES section appears first in the output, with ALTA section stating 'No critical problems found'",
    "Each section (AGENTS, INSTRUCTIONS, PROMPTS, SKILLS, README) is present even with no problems",
    "Output file COPILOT_COMPATIBILITY_REVIEW.md is saved with no code correction examples"
  ],
  "success_criteria": {
    "must_pass": [
      "RESUMEN DE ACCIONES appears before the per-section analysis",
      "All 5 asset types have their own section in the output",
      "No code blocks with corrected examples appear in the output",
      "Each section lists its files immediately after the section title",
      "At least one official documentation reference is cited per asset type"
    ],
    "must_not": [
      "Report ALTA problems when all required fields are present and valid",
      "Include code correction examples in the output",
      "Omit any of the 5 asset type sections from the output",
      "Evaluate based on cached/internal knowledge without fetching official docs"
    ]
  }
}
```

---

## Scenario 2: Edge case — missing frontmatter and inaccessible Confluence URL

```json
{
  "skills": ["copilot-compatibility-review"],
  "query": "Check compatibility of .github/ assets.",
  "project_state": {
    "agents": [
      {
        "file": "my-agent.agent.md",
        "has_yaml_frontmatter": false,
        "name_in_filename": "my-agent"
      }
    ],
    "instructions": [
      {
        "file": "java-standards.instructions.md",
        "has_yaml_frontmatter": true,
        "applyTo": null,
        "description": "Helps with Java"
      }
    ],
    "readme": {
      "has_supported_environments_section": true,
      "contains_invalid_value": "NFT"
    },
    "confluence_eci_accessible": false
  },
  "expected_behavior": [
    "Reports ALTA: YAML frontmatter completely absent in my-agent.agent.md — no fields can be read",
    "Reports ALTA: applyTo absent in java-standards.instructions.md — instruction never activates automatically",
    "Reports ALTA: README.md contains invalid environment value 'NFT'",
    "Marks the ECI Confluence verification as 'requires internal access' — does NOT fail the entire analysis",
    "Continues and completes the review of all other assets despite the Confluence URL being inaccessible",
    "RESUMEN DE ACCIONES lists at minimum 3 ALTA items (frontmatter, applyTo, README)",
    "The Confluence check appears in the README section as: 'ECI structure verification: requires internal access — validated using repository conventions instead'"
  ],
  "success_criteria": {
    "must_pass": [
      "Missing frontmatter in my-agent.agent.md is listed as ALTA with the file name cited",
      "applyTo absence in java-standards.instructions.md is listed as ALTA",
      "README NFT value is listed as ALTA with reference to ECI documentation",
      "Confluence inaccessibility is noted as 'requires internal access' — not as a blocker",
      "Analysis completes and output file is saved despite the Confluence URL being unavailable"
    ],
    "must_not": [
      "Abort the entire analysis because the Confluence URL returned an error",
      "Report the Confluence inaccessibility as a ALTA blocking problem",
      "Skip the README section because ECI reference was unavailable",
      "Invent what the Confluence page says based on internal knowledge"
    ]
  }
}
```

---

## Scenario 3: Misuse — validator pointed at a non-Copilot directory

```json
{
  "skills": ["copilot-compatibility-review"],
  "query": "Review Copilot assets in src/",
  "directory_state": "src/ contains only application source files — no .agent.md, .instructions.md, .prompt.md, or SKILL.md files present",
  "expected_behavior": [
    "Performs filesystem inspection on the target directory",
    "Finds zero Copilot asset files across all five asset types",
    "States explicitly: 'No Copilot assets found in src/ — this does not appear to be a Copilot project directory'",
    "Suggests the user point to .github/ as the standard Copilot assets directory",
    "Does NOT generate COPILOT_COMPATIBILITY_REVIEW.md with fabricated findings",
    "Does NOT produce a RESUMEN DE ACCIONES with invented problems"
  ],
  "success_criteria": {
    "must_pass": [
      "Filesystem check is performed before any evaluation attempt",
      "Zero assets found is reported explicitly with a corrective directory suggestion",
      ".github/ is named as the standard target directory for Copilot assets",
      "No output file is created"
    ],
    "must_not": [
      "Generate a compatibility review with invented asset names",
      "Report ALTA/MEDIA/BAJA problems for files that do not exist",
      "Create COPILOT_COMPATIBILITY_REVIEW.md with empty or placeholder sections",
      "Proceed to per-section analysis without confirming asset files exist"
    ]
  }
}
```
