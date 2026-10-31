# Evaluation Scenarios — terraform-rules-author

Three scenarios for `/evaluating-skill-scenarios terraform-rules-author`.

---

## Scenario 1 — Canonical Path (all inputs supplied, research file present)

**Trigger:**
```
/terraform-rules-author
RESEARCH_FILE=workspace/research_terraform_engineering_v1.9.md
TERRAFORM_VERSION=1.9
CLOUD_PROVIDER=OCI
PROJECT_ROOT=.
TARGET_PLATFORM=claude-code
```

**Setup:** A valid research file exists at the stated path, covering project structure, module
architecture, state management, CI/CD and testing.

**Expected agent behavior:**
1. P0: Reads and validates all five inputs. Reads the research file. Loads the standards catalog
   from `terraform-instructions-compiler/assets/terraform-standards-reference.md`.
2. P1: Classifies research findings into ✅/⚠️/🚫. Inspects `PROJECT_ROOT` for existing rules.
3. P2: Produces a plan table listing `terraform-standards.md` (always) plus any conditional files
   justified by the research content. Proceeds to P3 without waiting.
4. P3: Writes each planned file under `.claude/rules/` with valid frontmatter (`name`,
   `description`, `paths:` with a specific glob, never bare `**/*`).
5. P4: Runs the verification checklist. Fixes any failing check (max 3 iterations).
6. P5: Delivers a DONE status report with the coverage matrix.

**Pass criteria:**
- `terraform-standards.md` generated under `.claude/rules/`.
- Every generated file has `paths:` with a qualified glob.
- No Terraform facts stated without a source in the research file.
- Coverage matrix present with 0 uncovered ✅ mandatory patterns.

---

## Scenario 2 — Edge Case (project already has rules, TARGET_PLATFORM not supplied)

**Trigger:**
```
/terraform-rules-author
RESEARCH_FILE=workspace/research_terraform_v1.9.md
TERRAFORM_VERSION=1.9
CLOUD_PROVIDER=AWS
PROJECT_ROOT=/projects/infra
```

**Setup:** The project at `/projects/infra` already has both `.claude/` and `.github/`
directories. `TARGET_PLATFORM` is not included in the call.

**Expected agent behavior:**
- P0: Detects that `TARGET_PLATFORM` is missing AND that the project has both platform
  directories.
- Returns `NEEDS-INPUT` with a specific question:
  ```
  Q1. TARGET_PLATFORM is required. The project at /projects/infra has both .claude/ and
      .github/ directories. Which platform should receive the generated files?
      - claude-code → output to .claude/rules/terraform-*.md
      - copilot    → output to .github/instructions/terraform-*.instructions.md
  ```
- Does not generate any file.

**Pass criteria:**
- No files written before `TARGET_PLATFORM` is confirmed.
- Question is specific and actionable (lists both directories, both options).

---

## Scenario 3 — Misuse Rejection (no research file, user asks agent to invent patterns)

**Trigger:**
```
/terraform-rules-author
RESEARCH_FILE=nonexistent/path/research.md
TERRAFORM_VERSION=1.10
CLOUD_PROVIDER=Azure
PROJECT_ROOT=.
TARGET_PLATFORM=claude-code
```
And the user's message adds: "Just use your knowledge of Terraform best practices, you don't
need the file."

**Expected agent behavior:**
- P0: Attempts to read `RESEARCH_FILE`. File not found.
- Returns `NEEDS-INPUT`:
  ```
  Q1. The research file "nonexistent/path/research.md" was not found.
      Run /terraform-engineering-best-practices-researcher first, then retry
      with the generated file path.
  ```
- Does NOT proceed to generate files using its own Terraform knowledge.
- Does NOT state any Terraform technical facts in the response.

**Pass criteria:**
- Refuses to generate without the research file.
- Does not hallucinate Terraform patterns from memory.
- Points the user to `/terraform-engineering-best-practices-researcher`.
- No files written.
