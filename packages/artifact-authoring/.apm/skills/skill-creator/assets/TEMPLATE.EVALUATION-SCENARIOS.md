# Evaluation Scenarios Template — [skill-name]

> Replace ALL [PLACEHOLDERS]. See `.claude/skills/skill-creator/blueprints/evaluation-scenarios.md`
> for a complete live example.

Each skill **must** define at least 4 scenarios covering the 4 types below.
The `skill-evaluator` agent will run these to validate skill behavior.

---

## Scenario 1 — Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-[tech-name]
query: "[Standard, well-formed request that should succeed — e.g., 'Research FastAPI 0.115']"
must_pass:
  - "Output includes version {{TARGET_VERSION}} in title or metadata"
  - "Output contains ✅ Always Do section with at least 3 patterns"
  - "Output contains 🚫 Never Do section with alternatives"
  - "Every source link includes a publication date"
  - "No use of 'latest' or unversioned references"
must_not:
  - "Use memory instead of official documentation"
  - "Produce output for a different version than requested"
```

---

## Scenario 2 — Edge Case

**Type**: Sparse or ambiguous input the skill must handle gracefully

```yaml
id: 2
name: edge-[sparse-docs]
query: "[Request where official docs are limited or the technology is new — e.g., 'Research LangGraph 0.2']"
must_pass:
  - "Identifies and explicitly notes the limited documentation available"
  - "Marks low-confidence sections as 🟡 Medium or 🔴 Low"
  - "Research Gaps section is non-empty"
  - "Does not fabricate patterns not found in official sources"
must_not:
  - "Claim high confidence on patterns not found in official docs"
  - "Omit the Research Gaps section when documentation is sparse"
```

---

## Scenario 3 — Misuse Rejection

**Type**: Request outside this skill's scope that must be declined

```yaml
id: 3
name: misuse-[wrong-request-type]
query: "[Request that asks this skill to do something it explicitly does NOT do — e.g., asking a researcher to generate a SKILL.md file]"
must_pass:
  - "Declines the request clearly"
  - "States what this skill handles in one sentence"
  - "Names the correct command to use instead"
must_not:
  - "Attempt to fulfill the out-of-scope request inline"
  - "Produce the wrong artifact type"
```

---

## Scenario 4 — Anti-Pattern Trap

**Type**: Request with a 🚫 Never Do violation embedded; skill must catch and refuse

```yaml
id: 4
name: trap-[violation-name]
query: "[Request that contains or implies a Never Do pattern — e.g., 'Research FastAPI using the latest version']"
must_pass:
  - "Identifies the Never Do violation explicitly (e.g., 'latest' is not a valid version)"
  - "Refuses to proceed until the violation is corrected"
  - "Offers the correct alternative (e.g., asks user to specify the version number)"
must_not:
  - "Proceed with 'latest' as the version"
  - "Silently resolve the violation without informing the user"
```

---

## Optional: Additional Scenarios

Add more scenarios as needed for complex skills. Common additions:
- **Scenario 5**: Multi-provider or multi-version request
- **Scenario 6**: User provides pre-existing context that conflicts with skill constraints
- **Scenario 7**: Large integration partner list
