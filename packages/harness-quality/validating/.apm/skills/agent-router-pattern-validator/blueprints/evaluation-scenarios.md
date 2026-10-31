# Evaluation Scenarios — agent-router-pattern-validator

Used to verify that the validator correctly identifies compliant, partially compliant, and violating
Agent Router Pattern implementations — and that it generates complete, file-cited output without
hallucinating findings.

---

## Scenario 1: Canonical — fully compliant project

```json
{
  "skills": ["agent-router-pattern-validator"],
  "query": "Validate the agent project in .github/ — check that the router, instructions, prompts, and skills follow the Agent Router Pattern.",
  "project_state": "Router agent contains only: routing rules, keyword-to-prompt mappings, fallback behavior. All domain logic lives in prompts. Instructions inject only global context. Skills have three-tier guardrails.",
  "expected_behavior": [
    "Reads all files in .github/agents/, .github/instructions/, .github/prompts/, .github/skills/ before writing any finding",
    "Builds the INVENTORY table listing every file found by type",
    "Marks Router Purity criteria as compliant — no domain logic found in the router",
    "Marks Routing Completeness as compliant — every prompt has a keyword mapping",
    "Marks Skills three-tier as compliant — Always Do / Ask First / Never Do all present",
    "Assigns overall score >= 8.0/10",
    "Saves AGENT_ROUTER_PATTERN_REPORT.md with all 8 sections fully written",
    "Confirms saved path and score to the user"
  ],
  "success_criteria": {
    "must_pass": [
      "INVENTORY table produced before analysis begins",
      "All 4 layers assessed with per-criterion status (compliant/partial/violation)",
      "Section 3.1 contains specific file + section citations for each compliant item",
      "Section 4 (Problems) is present and explicitly states 'No critical violations found'",
      "Overall weighted score computed correctly from the 40/20/30/10 weight table",
      "Output file saved and path confirmed"
    ],
    "must_not": [
      "Report a violation without citing the specific file and section",
      "Give a high score without explaining what makes each layer correct",
      "Abbreviate any section with '... and so on' or 'similar issues elsewhere'",
      "Assess a layer without having read its files"
    ]
  }
}
```

---

## Scenario 2: Edge case — router with leaked domain logic

```json
{
  "skills": ["agent-router-pattern-validator"],
  "query": "Check if the agent in .github/ correctly implements the router pattern.",
  "project_state": "The .agent.md file contains: routing rules AND a full 'Core Responsibilities' section with Terraform code patterns AND verification checklists. The corresponding terraform.prompt.md has no Always Do section.",
  "expected_behavior": [
    "Identifies 'domain-specific implementation logic in router' as a Router Purity violation (P1, High priority)",
    "Cites the exact section name ('Core Responsibilities') and file name in the problem description",
    "Identifies missing three-tier guardrails in terraform.prompt.md as a Prompts violation",
    "Proposes Change C1: move Core Responsibilities content from .agent.md to terraform.prompt.md",
    "Proposes Change C2: add Always Do / Ask First / Never Do to terraform.prompt.md",
    "Router Agent score is <= 6/10 due to purity violation",
    "Section 6 Before vs. After diagram shows Core Responsibilities section removed from router and placed in prompt"
  ],
  "success_criteria": {
    "must_pass": [
      "Router Purity marked as violation with file + section citation",
      "Problem description explains which principle is broken (responsibility separation) and the concrete impact",
      "Proposed change C1 specifies file, action (Remove from router / Add to prompt), and exact content description",
      "Score reflects the 40% weight of the Router layer — overall score is dragged below 7.0"
    ],
    "must_not": [
      "Mark the router as compliant because it also has routing rules",
      "Propose vague change like 'refactor the router' without specifying what to move where",
      "Omit the Before vs. After diagram in Section 6"
    ]
  }
}
```

---

## Scenario 3: Misuse — validator used on a non-agent project

```json
{
  "skills": ["agent-router-pattern-validator"],
  "query": "Validate my project structure.",
  "project_state": "The target directory contains only src/main/java/ files, a pom.xml, and README.md. No .agent.md, .instructions.md, .prompt.md, or SKILL.md files exist.",
  "expected_behavior": [
    "Produces the INVENTORY table showing: Agents found: none, Instructions found: none, Prompts found: none, Skills found: none",
    "Does NOT attempt to score layers with no files",
    "States explicitly: 'No Agent Router Pattern artifacts found in the target directory — this does not appear to be a Copilot/Claude Code agent project'",
    "Suggests the user point to the correct directory (.github/ or .claude/) and re-run",
    "Does NOT hallucinate findings for files that do not exist",
    "Does NOT produce a scored report without files to analyze"
  ],
  "success_criteria": {
    "must_pass": [
      "INVENTORY table is produced and all four counts show 'none' or '0'",
      "Analysis explicitly states no artifacts were found — no scores assigned",
      "User is told which directories to try instead",
      "No section of the output contains fabricated file names or findings"
    ],
    "must_not": [
      "Produce a scored report (e.g. '8.0/10') when no files were found",
      "Invent fictional .agent.md or .prompt.md files to populate the inventory",
      "Proceed to Section 4 (Problems) with invented violations"
    ]
  }
}
```
