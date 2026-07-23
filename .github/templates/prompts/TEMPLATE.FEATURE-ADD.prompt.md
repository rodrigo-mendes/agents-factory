---
description: '[Brief description of what this prompt implements]'
agent: [agent-name]
argument-hint: '[Suggested argument: e.g., "Choose the [FEATURE] strategy"]'
---

> ⚙️ **Template tecnologia-agnóstico.** Substitua TODOS os `[PLACEHOLDERS]`. Nomes em `e.g.`/`[e.g., ...]` são apenas exemplos ilustrativos — não são padrões nem defaults desta fábrica.

# Add [FEATURE NAME]

**Skill**: `[primary-skill-name]`

## What this does

[1-2 sentences describing what this prompt creates or modifies. Focus on deliverables, not process.]

## Required information

1. **[Context dimension 1]**: [What the user needs to provide] (e.g., name, type, scope)
2. **[Context dimension 2]**: [Options or choices]
   - [Option A] — [brief description]
   - [Option B] — [brief description]
   - [Option C] — [brief description]
3. **[Context dimension 3]**: [Yes/No or specific value]
4. **[Context dimension 4]**: [Additional context if needed]

## What will be generated

- [Deliverable 1] — [description]
- [Deliverable 2] — [description]
- [Deliverable 3] — [description]
- [Deliverable 4] — [description (e.g., test skeleton)]

---

## Skills Required

**Always load**:
- `.github/skills/[primary-skill-name]/SKILL.md` — [Brief description]

**Load conditionally**:
- [Condition 1]? → `.github/skills/[conditional-skill-1]/SKILL.md`
- [Condition 2]? → `.github/skills/[conditional-skill-2]/SKILL.md`

---

## Trigger Keywords

Use this prompt when the user mentions:
- "[keyword1]", "[keyword2]", "[keyword3]", "[keyword4]", "[keyword5]"

---

## Workflow

### Step 1: Load Primary Skill

Read `.github/skills/[primary-skill-name]/SKILL.md` before proceeding.

### Step 2: Verify Critical Requirements

From the skill, enforce:
- ✅ [Mandatory requirement 1]
- ✅ [Mandatory requirement 2]
- ✅ [Mandatory requirement 3]
- 🚫 NEVER [prohibition 1]
- 🚫 NEVER [prohibition 2]

### Step 3: Ask Architectural Questions

From `.github/skills/[primary-skill-name]/SKILL.md` (⚠️ Ask First section):

Present decisions that require user input:
- **[Decision 1]**: [Options with trade-offs — reference skill section]
- **[Decision 2]**: [Options with trade-offs — reference skill section]

See skill file for complete trade-off matrices.

### Step 4: Generate Implementation

Follow the ✅ Always Do patterns from the loaded skill exactly.

---

## ⚠️ Single Source of Truth

**IMPORTANT**: This prompt describes WHAT to implement and WHERE to find patterns. It does NOT duplicate code examples.

**For implementation details, code examples, and verification steps:**
- Load `.github/skills/[primary-skill-name]/SKILL.md`
- Look for sections marked with ✅ (Always), 🚫 (Never Do), ⚠️ (Ask First)
- Reference specific sections using anchors (e.g., `#[section-anchor]`)

**When generating code:**
1. Ask clarifying questions from ⚠️ Ask First sections
2. Implement patterns from ✅ Always sections
3. Add comments referencing relevant skill sections
4. Do NOT repeat examples from this prompt — they are in the skill file

---

## Mandatory Patterns

### ✅ Always Do (From Skill)

Implementation patterns are documented in `.github/skills/[primary-skill-name]/SKILL.md`. Follow all mandatory requirements — the number of patterns depends on the skill's domain complexity:

#### [Mandatory Pattern 1]
**Reference**: `.github/skills/[primary-skill-name]/SKILL.md#[section-anchor]`

[Natural language description of WHAT to do, not code]

**Requirement**: [Why it matters]

#### [Mandatory Pattern N]
**Reference**: `.github/skills/[primary-skill-name]/SKILL.md#[section-anchor]`

[Add as many mandatory patterns as the skill requires — do not cap artificially]

### 🚫 Never Do (From Skill)

Refer to `.github/skills/[primary-skill-name]/SKILL.md#never-do` for anti-patterns:

- **Never [anti-pattern 1]**: [Brief explanation]
- **Never [anti-pattern N]**: [Include all anti-patterns from the skill — do not cap artificially]

### ⚠️ Ask First (From Skill)

**[Architectural Decision 1]**:

Reference: `.github/skills/[primary-skill-name]/SKILL.md#[section-anchor]`

| Option | Pro | Con | When |
|--------|-----|-----|------|
| [Option 1] | [Pro] | [Con] | [When] |
| [Option 2] | [Pro] | [Con] | [When] |

---

## Common Scenarios

Include scenarios that cover the critical paths for this feature. Add as many as needed to represent the main use cases:

### Scenario 1: [Common Use Case 1]

**User request**: "[Example request]"

**Implementation**: Follow pattern in `.github/skills/[primary-skill-name]/SKILL.md` (✅ Always section) with:
- [Characteristic 1]
- [Characteristic 2]

**Key decisions**: [Decision 1], [Decision 2]

### Scenario 2: [Common Use Case 2]

**User request**: "[Example request]"

**Implementation**: Combine patterns from:
- `.github/skills/[skill-1]/SKILL.md#[section]` — [Description]
- `.github/skills/[skill-2]/SKILL.md#[section]` — [Description]

**Key decisions**: [Decision 1], [Decision 2]

---

## Integration Patterns

### With [Other Technology/Case]

When [specific context], combine patterns from [skill1] and [skill2].

**Skills needed**:
- `.github/skills/[skill-1]/SKILL.md` — [Description]
- `.github/skills/[skill-2]/SKILL.md` — [Description]

**Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## Verification Checklist

Reference: `.github/skills/[primary-skill-name]/SKILL.md`

- [ ] [Requirement 1] — [Description]
- [ ] [Requirement 2] — [Description]
- [ ] [Requirement 3] — [Description]
- [ ] [Requirement 4] — [Description]
- [ ] [Requirement 5] — [Description]
