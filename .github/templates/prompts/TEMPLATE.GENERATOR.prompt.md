---
description: 'Extracts [DOMAIN] best practices from research files and generates targeted [OUTPUT FILE TYPE] files for GitHub Copilot, with user interview and planning phases.'
---

# Prompt: [DOMAIN] Best Practices → [OUTPUT TYPE] Generator

## PURPOSE

This is an **extraction, planning, and generation prompt**. Given a [DOMAIN] best practices research file (produced by `[research-prompt-name].prompt.md` or equivalent), it:

1. **Interviews** the user about their project context and preferences
2. **Plans** which `[output-file-pattern]` files to generate and their scope
3. **Generates** production-ready files following the template standards

The output is **NOT a document for humans to read** — it is a set of **operational [OUTPUT TYPE] files for GitHub Copilot agents**, structured to enforce best practices during code generation.

---

## INPUT VARIABLES

```yaml
RESEARCH_FILE:          # Path to the best practices research file
                        # e.g., "agents_arch_doc/[domain]/research_[Name]_v[VERSION].md"
TARGET_VERSION:         # e.g., "1.11", "17", "3.x"
DOMAIN_CONTEXT:         # e.g., "OCI", "AWS", "Spring Boot"
PROJECT_ROOT:           # Where to place generated files
                        # e.g., "." (current workspace)
```

---

## Role
Copilot Configuration Architect & Senior [DOMAIN] Engineer specializing in [DOMAIN] standards enforcement through GitHub Copilot custom [OUTPUT TYPE].

## Context
You have received a [DOMAIN] best practices research file. Your mission is to transform this research into actionable `[output-file-pattern]` files that GitHub Copilot will use to enforce standards during code generation, review, and refactoring.

---

## Execution Workflow

### Phase 1: Load Research & Templates (REQUIRED)

#### Step 1.1: Load Research File

Read the research file at `{{RESEARCH_FILE}}` and extract and classify all findings into:
- ✅ Mandatory patterns → Will become `Always Do` rules
- ⚠️ Conditional patterns → Will become interview questions for the user
- 🚫 Forbidden patterns → Will become `Never Do` rules

#### Step 1.2: Load Templates

Read the relevant templates from `.github/templates/[template-subdir]/`:
- `TEMPLATE.[TYPE].md` for each template type

Understand the template types and their purposes:
- **[TEMPLATE A]** → [purpose — applies to which files]
- **[TEMPLATE B]** → [purpose — applies to which files]
- **[TEMPLATE C]** → [purpose — applies to which files]

---

### Phase 2: User Interview (REQUIRED)

Before planning output files, ask the user these questions to calibrate the output. Present ALL questions at once, grouped by category.

Organize questions into logical categories based on the domain's scope. The number of categories and questions should scale with domain complexity — simple domains may need 2-3 categories with 4-6 questions; complex domains may need 5-7 categories with 10-15 questions. Do not force a fixed category count.

#### 2.1 — [CATEGORY 1] Questions

```
[EMOJI] [CATEGORY NAME]

Q1: [Question about project context]
   a) [Option a]
   b) [Option b]
   c) [Option c]
   d) [Option d — "Not decided yet — recommend"]

Q2: [Question about preferences]
   a) [Option a]
   b) [Option b]
   c) [Option c]
   d) [Option d]

Q3: [Question about structure]
   a) [Option a]
   b) [Option b]
   c) [Option c]
   d) [Option d]
```

#### 2.2 — [CATEGORY 2] Questions

```
[EMOJI] [CATEGORY NAME]

Q4: [Question]
   a) [Option]
   b) [Option]
   c) [Option]
   d) [Option]

Q5: [Question]
   a) [Option]
   b) [Option]
   c) [Option]
   d) [Option]

Q6: [Question]
   a) [Option]
   b) [Option]
   c) [Option]
   d) [Option]
```

#### 2.3 — [CATEGORY 3] Questions

```
[EMOJI] [CATEGORY NAME]

Q7: [Question]
   a) [Option]
   b) [Option]
   c) [Option]

Q8: [Question]
   a) [Option]
   b) [Option]
   c) [Option]
```

#### 2.4 — [CATEGORY 4] Questions

```
[EMOJI] [CATEGORY NAME]

Q9: [Question]
   a) [Option]
   b) [Option]
   c) [Option]

Q10: [Question]
   a) [Option]
   b) [Option]
   c) [Option]
   (Select all that apply)
```

#### 2.5 — [CATEGORY 5] Questions

```
[EMOJI] [CATEGORY NAME]

Q11: [Question]
   a) [Option]
   b) [Option]
   c) [Option]

Q12: [Question]
   a) [Option]
   b) [Option]
   c) [Option]
```

---

### Phase 3: Planning (REQUIRED)

Based on the interview answers, generate a **plan** before creating any files. The plan MUST be presented to the user for approval.

#### 3.1 — Determine Files to Generate

Evaluate which files are needed based on answers:

| Output File | When to Generate | applyTo / Scope |
|---|---|---|
| `[prefix]-standards.[ext]` | **Always** — core standards | `[glob pattern]` |
| `[prefix]-[domain-1].[ext]` | When [condition from Q answers] | `[glob pattern]` |
| `[prefix]-[domain-2].[ext]` | When [condition from Q answers] | `[glob pattern]` |
| `[prefix]-[domain-3].[ext]` | When [condition from Q answers] | `[glob pattern]` |
| `[prefix]-[domain-4].[ext]` | When [condition from Q answers] | `[glob pattern]` |
| `[prefix]-skills.[ext]` | When [condition from Q answers] | `[glob pattern]` |

#### 3.2 — Present Plan to User

```
📋 [OUTPUT TYPE] FILES PLAN

Based on your answers, I will generate the following files:

┌─────────────────────────────────────────────────────────────┐
│ #  │ File                                  │ Scope          │
├─────────────────────────────────────────────────────────────┤
│ 1  │ [filename-1]                          │ [scope]        │
│    │ → [brief description]                  │                │
├─────────────────────────────────────────────────────────────┤
│ 2  │ [filename-2]                          │ [scope]        │
│    │ → [brief description]                  │                │
├─────────────────────────────────────────────────────────────┤
│ ...│ ...                                    │ ...            │
└─────────────────────────────────────────────────────────────┘

Each file will enforce:
  ✅ Mandatory patterns (count driven by domain complexity)
  ⚠️ Conditional patterns (resolved by your answers)
  🚫 Forbidden patterns (count driven by domain complexity)

Total files: [N]
Location: {{PROJECT_ROOT}}/[output-directory]/

Proceed with generation? (yes / adjust plan)
```

**Wait for user approval before proceeding to Phase 4.**

---

### Phase 4: Generate Files

For each planned file, follow the structure from the appropriate template in `.github/templates/`.

#### 4.1 — [ALWAYS-GENERATED FILE] (ALWAYS GENERATED)

```markdown
---
[frontmatter appropriate to output type]
---

[Content structure following template pattern]

## ✅ Always Do
[Extract all mandatory patterns from research]

## 🚫 Never Do
[Extract all forbidden patterns from research]
```

#### 4.2 — [CONDITIONAL FILE 1] (CONDITIONAL)

```markdown
---
[frontmatter appropriate to output type]
---

[Content structure based on Q answers]
```

#### 4.N — [CONDITIONAL FILE N] (CONDITIONAL)

```markdown
---
[frontmatter appropriate to output type]
---

[Content structure based on Q answers]
```

---

### Phase 5: Validation (REQUIRED)

After generating all files, validate each:

#### 5.1 — Structure Validation
- [ ] Frontmatter has required fields ([list fields])
- [ ] Description clearly states what the file enforces
- [ ] Scope/applyTo pattern is correct
- [ ] File is saved to `{{PROJECT_ROOT}}/[output-directory]/`

#### 5.2 — Content Validation
- [ ] All ✅ patterns from research are covered across files
- [ ] All 🚫 patterns from research are covered across files
- [ ] ⚠️ patterns resolved by user answers are included as ✅
- [ ] ⚠️ patterns NOT resolved are documented with TODO comments
- [ ] No duplication between files — each concern lives in ONE file
- [ ] Version numbers match {{TARGET_VERSION}} throughout

#### 5.3 — Coverage Matrix

Present a final coverage matrix to the user:

```
📊 COVERAGE MATRIX

Research Section                    → Output File
─────────────────────────────────────────────────────
[Section 1]                         → [filename]
[Section 2]                         → [filename]
[Section 3]                         → [filename]
...

Mandatory Patterns (✅):  [N] covered / [N] total from research
Forbidden Patterns (🚫):  [N] covered / [N] total from research
Conditional Resolved (⚠️→✅): [N] resolved by interview
Conditional Pending (⚠️):     [N] deferred (user didn't decide)
```

---

## Quality Gates (Final Checklist)

Before delivering output:
- [ ] Research file was fully loaded and parsed
- [ ] User interview completed (all questions answered)
- [ ] Plan was approved by user before generation
- [ ] All generated files follow template structure
- [ ] Frontmatter is valid in every file
- [ ] Scope patterns don't overlap excessively between files
- [ ] No research patterns left uncovered (coverage matrix is complete)
- [ ] No hardcoded secrets or credentials in examples
- [ ] All code examples use {{TARGET_VERSION}} syntax
- [ ] Domain references match {{DOMAIN_CONTEXT}} throughout
- [ ] Each file is self-contained (can be understood without other files)
- [ ] Files are placed in `{{PROJECT_ROOT}}/[output-directory]/`

---

## Output Priorities
1. 🚨 Security and safety rules (always in standards file)
2. ✅ Core standards (always generated)
3. [Priority 3 — domain-specific]
4. [Priority 4 — domain-specific]
5. [Priority 5 — domain-specific]
6. [Priority N — conditional files]

---

## Error Handling

### If Research File Is Missing
```
"No research file found at {{RESEARCH_FILE}}.

To generate one, use the prompt:
  /[research-prompt-name]

With variables:
  [VARIABLE_1]: {{value}}
  [VARIABLE_2]: {{value}}

Then re-run this prompt with the generated research file."
```

### If User Skips Questions
For any unanswered question, use the research file's recommended default and add a comment:
```markdown
<!-- TODO: This pattern was auto-selected from research defaults.
     Review and adjust for your specific context.
     Original question: [Q text] -->
```

### If Templates Are Missing
Generate files using the patterns documented in this prompt directly. Templates are preferred but not required.
