---
name: [language]-[framework]-skills
description: "Integrates [STANDARD_NAME] skills from .github/skills/ for [LANGUAGE] development — routes requests to specialized skills and prompts"
applyTo: "**/*.[extension]"
---

> ⚙️ **Template tecnologia-agnóstico.** Substitua TODOS os `[PLACEHOLDERS]`. Nomes em `e.g.`/`[e.g., ...]` são apenas exemplos ilustrativos — não são padrões nem defaults desta fábrica.

## ⚠️ Check Prompts First!

Before loading skills directly, check if a specialized prompt exists for the user's request:

| User Intent | Recommended Prompt |
|---|---|
| [Intent 1] | `/[prompt-name-1]` |
| [Intent 2] | `/[prompt-name-2]` |
| [Intent 3] | `/[prompt-name-3]` |
| [Intent 4] | `/[prompt-name-4]` |

**If a prompt matches** → Recommend it to the user. Prompts provide guided workflows with context collection.

**If no prompt matches** → Proceed with skill loading below.

---

## Skill Directory Mapping

Use this table to identify which skill(s) to load based on trigger keywords in the user's request:

### [Domain 1] Skills

| Keyword Triggers | Skill File | Focus Area |
|---|---|---|
| [trigger keywords 1] | `.github/skills/[skill-name-1]/SKILL.md` | [focus area 1] |
| [trigger keywords 2] | `.github/skills/[skill-name-2]/SKILL.md` | [focus area 2] |
| [trigger keywords 3] | `.github/skills/[skill-name-3]/SKILL.md` | [focus area 3] |

### Architecture & Design Skills

| Keyword Triggers | Skill File | Focus Area |
|---|---|---|
| [trigger keywords] | `.github/skills/[design-skill-name]/SKILL.md` | [design focus] |

---

## Mandatory Cross-Cutting Rules

These rules apply **regardless** of which specific skill is loaded:

### ✅ Always Do
1. [Cross-cutting rule 1] — [description]
2. [Cross-cutting rule 2] — [description]
3. [Cross-cutting rule 3] — [description]
4. [Cross-cutting rule 4] — [description]
5. [Cross-cutting rule 5] — [description]

### 🚫 Never Do
1. [Cross-cutting prohibition 1] — [description]
2. [Cross-cutting prohibition 2] — [description]
3. [Cross-cutting prohibition 3] — [description]
4. [Cross-cutting prohibition 4] — [description]

---

## Multi-Skill Composition

When a request requires multiple skills, load them in this order:

1. **Base**: `[base-skill-name]/SKILL.md` (always loaded first)
2. **Specialization**: `[specialization-skill-name]/SKILL.md` (if needed)
3. **Integration**: One or more integration skills
4. **Design context**: Architecture skills (if designing new responsibilities)
5. **Testing**: `[testing-skill-name]/SKILL.md` (if writing tests)

---

## Version Compliance

| Component | Required Version | Notes |
|---|---|---|
| [Component 1] | [version] | [notes] |
| [Component 2] | [version] | [notes] |
| [Component 3] | [version] | [notes] |

---

## Agent Delegation

For requests outside [LANGUAGE] scope:
- **[Other domain 1]** → Delegate to `@[agent-name-1]`
- **[Other domain 2]** → Delegate to `@[agent-name-2]`
- **[Other domain 3]** → Delegate to `@[agent-name-3]`
