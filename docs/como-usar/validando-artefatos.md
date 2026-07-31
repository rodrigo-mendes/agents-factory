# Guide: Validating Artifacts

How to use the validation prompts to ensure artifact quality.

---

## When to Use

- After creating/modifying any artifact
- Before commit/PR
- In periodic quality reviews
- When something "doesn't work" and you don't know why

## Choose the Right Validator

| What you have | Validator |
|---------------|-----------|
| Any artifact (agent, command, etc.) | `copilot-compatibility-review` |
| Rules file (`.claude/rules/`) | `instructions-best-practices-validator` |
| `SKILL.md` file | `skill-best-practices-validator` |
| Complete agent project | `project-analysis-validator .claude/` |
| Routing structure | `agent-router-pattern-validator` |
| Full architecture — `.claude/` project | `audit-cc-architecture-consensus` |
| Full architecture — `.github/` project | `audit-architecture-consensus` |

## Recommended Pipeline

For complete validation, run in this order:

### Step 1: Technical compatibility
```
/copilot-compatibility-review
```
> Verifies the YAML is valid, fields are correct, limits are respected.

### Step 2: Content quality
```
/instructions-best-practices-validator
/skill-best-practices-validator
```
> Verifies the content follows best practices (structure, clarity, completeness).

### Step 3: Project quality
```
/project-analysis-validator .claude/
```
> Holistic view: directory structure, CLAUDE.md accuracy, router consistency,
> frontmatter, naming, progressive disclosure and rules coverage.

### Step 4 (optional): Architectural audit

For **Claude Code** projects (`.claude/`):
```
/audit-cc-architecture-consensus
```

For **GitHub Copilot** projects (`.github/`):
```
/audit-architecture-consensus
```

> Complete multi-model analysis (scope + flow + engine). Runs 3 lenses in parallel and prioritizes
> findings by consensus: 3/3 = Must-Fix 🔴, 2/3 = Should-Fix 🟡, 1/3 = Consider 🟢.

---

## When to Use Each Level

| Scenario | Up to step |
|---------|:---:|
| I edited a file | Step 1 |
| I created a new skill | Steps 1-2 |
| I created a new project | Steps 1-3 |
| Pre-release / production | Steps 1-4 |
| Debug ("why doesn't it work?") | Steps 1 + 4 (engine) |

---

## What Each Validator Detects

### copilot-compatibility-review
- ❌ Malformed YAML
- ❌ `name` field > 64 characters
- ❌ `description` field > 1024 characters
- ❌ Invalid `tools`
- ❌ `applyTo` with invalid glob

### instructions-best-practices-validator
- ❌ Instructions without clear scope
- ❌ Contradictions between instructions
- ❌ Duplicate information
- ❌ Scope too broad or too narrow

### skill-best-practices-validator
- ❌ Missing ✅ or 🚫 section
- ❌ ✅ without example code
- ❌ 🚫 without alternative
- ❌ Mixed versions
- ❌ Missing blueprints/

### project-analysis-validator .claude/
- ❌ Directory structure outside the `.claude/` standard
- ❌ CLAUDE.md inaccurate or outdated
- ❌ Inconsistencies in the agent routing table
- ❌ Invalid or missing frontmatter
- ❌ Artifact names outside the kebab-case convention
- ❌ Progressive disclosure violated (inline content instead of blueprints)
- ❌ Incomplete rules coverage for the domain
- ❌ Orphaned components (never referenced)
- ❌ Broken references (points to non-existent file)

---

## Tips

- **Always start with Step 1**: YAML/compatibility issues cause silent errors — Claude Code may ignore the file without warning.
- **Don't ignore warnings**: Today's warnings become tomorrow's bugs.
- **Validate iteratively**: Fix → re-validate → fix → re-validate until clean.

## Common Pitfalls

| Pitfall | Solution |
|-----------|---------|
| Never validating | Include validation in the workflow before commit |
| Validating only at the end | Validate after each artifact created |
| Ignoring "all OK" report on an incomplete project | "OK" means conformant, not complete |
| Relying solely on the validator without manual review | Validators detect structure, not semantics |

## Full Flow

See: [Quality Flow](../fluxos/fluxo-qualidade.md)
