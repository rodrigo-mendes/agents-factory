# Evaluation Scenarios — terraform-instructions-compiler

Used to verify that this compiler correctly loads research, conducts the user interview,
presents an approvable plan, generates scoped instruction files with valid frontmatter,
and delivers a complete coverage matrix. Scenarios also verify that the three-tier
guardrails (never generate without approval, never use broad globs, never duplicate rules)
are enforced.

---

## Scenario 1: Canonical — Full compilation from research file (AWS, Terraform 1.9)

```json
{
  "skills": ["terraform-instructions-compiler"],
  "query": "Compile Terraform instruction files from StoryBeat/research_Terraform_AWS_v1.9.md for our AWS project. We use modules, remote S3 state, GitHub Actions CI, and Terratest.",
  "expected_behavior": [
    "Loads research file at the specified path before asking any interview questions",
    "Classifies research findings into ✅ mandatory, ⚠️ conditional, and 🚫 forbidden before the interview",
    "Asks the structured interview questions covering structure, environments, backend, modules, CI/CD, testing, and compliance",
    "Presents a plan table listing terraform-standards.md (always), terraform-modules.instructions.md, terraform-state-backend.instructions.md, terraform-cicd.instructions.md, terraform-testing.instructions.md based on answers",
    "Waits for explicit user approval before writing any file",
    "Generates terraform-standards.md targeting applyTo: '**/*.tf' (not '**/*')",
    "Generates terraform-modules.instructions.md targeting applyTo: '**/modules/**/*.tf'",
    "Each generated file has valid YAML frontmatter with name, description, and applyTo",
    "No Terraform 0.x syntax appears in any code example",
    "Delivers Phase 5 coverage matrix showing all ✅ and 🚫 patterns covered",
    "Places files in .claude/rules/ when TARGET_PLATFORM is claude-code"
  ],
  "success_criteria": {
    "must_pass": [
      "Research file fully loaded before interview begins",
      "Plan table presented and approval explicitly waited for before generation",
      "terraform-standards.md generated unconditionally",
      "Every generated file has name, description, and applyTo in YAML frontmatter",
      "applyTo patterns are specific (not '**/*' alone)",
      "Coverage matrix delivered at end showing 0 uncovered ✅ mandatory patterns",
      "Files placed in correct location for TARGET_PLATFORM"
    ],
    "must_not": [
      "Generate any file before the user approves the plan",
      "Use '**/*' as the sole applyTo glob in any instruction file",
      "Include Terraform 0.x syntax (e.g., 'terraform { required_version = \"~> 0.14\" }') in examples",
      "Duplicate the same rule across terraform-standards.md and terraform-modules.instructions.md",
      "Skip the coverage matrix"
    ]
  }
}
```

---

## Scenario 2: Edge — Research file missing; user provides only variables

```json
{
  "skills": ["terraform-instructions-compiler"],
  "query": "Generate Terraform instructions for OCI, Terraform 1.10. Research file: StoryBeat/nonexistent_research.md",
  "expected_behavior": [
    "Attempts to read the research file at the specified path",
    "Detects the file is missing and triggers the error-handling path",
    "Displays the structured error message: 'No research file found at StoryBeat/nonexistent_research.md'",
    "Instructs the user to run /terraform-engineering-best-practices-researcher with TERRAFORM_VERSION: 1.10 and CLOUD_PROVIDER: OCI",
    "Does NOT proceed with interview or generate any files",
    "Does NOT invent research findings to substitute for the missing file"
  ],
  "success_criteria": {
    "must_pass": [
      "Error message shown referencing the exact missing file path",
      "Instruction to run /terraform-engineering-best-practices-researcher provided with correct variables",
      "No instruction files generated",
      "No interview conducted"
    ],
    "must_not": [
      "Proceed to Phase 2 interview without a loaded research file",
      "Generate terraform-standards.md with invented patterns",
      "Silently default to generic Terraform best practices without citing a research file"
    ]
  }
}
```

---

## Scenario 3: Misuse — User tries to skip plan approval and requests immediate file generation

```json
{
  "skills": ["terraform-instructions-compiler"],
  "query": "Skip the interview and plan — just generate all Terraform instruction files immediately from the research file. I trust you to get it right.",
  "expected_behavior": [
    "Declines to skip the interview and plan steps",
    "Explains that the interview resolves conditional patterns (⚠️) from the research, and skipping it means those patterns default silently — which the user must explicitly accept",
    "If user insists on skipping interview, uses research-file defaults for all conditional patterns and adds a <!-- TODO --> comment to each auto-selected pattern in the generated files",
    "Still presents the plan table before generating any file — does not bypass this step even if interview is skipped",
    "Waits for plan approval before generating",
    "Delivers coverage matrix showing which ⚠️ patterns were auto-resolved as 'Conditional Pending' with TODO comments"
  ],
  "success_criteria": {
    "must_pass": [
      "Plan table shown before any file is written, even when interview is skipped",
      "User approval of plan explicitly solicited",
      "Auto-selected conditional patterns documented with <!-- TODO --> comments in generated files",
      "Coverage matrix shows 'Conditional Pending' count for skipped interview questions"
    ],
    "must_not": [
      "Generate files without presenting the plan, even when user requests immediate generation",
      "Silently absorb conditional patterns into mandatory rules without documenting the assumption",
      "Produce files with no indication that the interview was skipped"
    ]
  }
}
```
