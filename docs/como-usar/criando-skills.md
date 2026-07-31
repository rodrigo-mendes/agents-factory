# Guide: Creating Skills

How to create a SKILL.md that follows all framework patterns.

---

## When to Use

- After researching a technology (researcher output)
- To encapsulate specific domain knowledge
- To provide guardrails to agents

## Step by Step

### 1. Have the research ready

A skill needs validated content. If you don't have it yet:
```
/researching-technical-frameworks
```
See: [Researching Technologies](pesquisando-tecnologias.md)

### 2. Run the skill-creator

```
/skill-creator
```

Provide the path to the research document when prompted.

### 3. What the skill-creator does internally

1. Applies built-in authoring patterns (three-tier, YAML, blueprints)
2. Reads your research document
3. Structures in three-tier:
   - **✅ Always Do**: Mandatory patterns with complete code
   - **⚠️ Ask First**: Architectural decisions (presents trade-offs)
   - **🚫 Never Do**: Anti-patterns with alternative and impact
4. Generates correct YAML frontmatter
5. Creates auxiliary blueprints

### 4. Expected result

```
skill-name/
├── SKILL.md              ← Main skill
└── blueprints/
    ├── always-do-patterns.md   ← Patterns with code
    └── never-do-patterns.md    ← Anti-patterns with alternatives
```

### 5. Validate the skill

```
/skill-best-practices-validator
```

### 6. Quality checklist

Before considering it done, check:

- [ ] YAML frontmatter with `name` (≤64 chars, kebab-case)
- [ ] YAML `description` with "Use when..." (≤1536 chars)
- [ ] ✅ Always Do section with example code in ALL patterns
- [ ] ⚠️ Ask First section with trade-off matrix
- [ ] 🚫 Never Do section with alternative AND impact
- [ ] `blueprints/` with always-do and never-do
- [ ] Specific version declared (version absolutism)
- [ ] No information from different versions mixed in

---

## Alternative Compilers

If your research is from a specific domain, use the specialized compiler:

| Research domain | Use |
|---------------------|------|
| Generic | `skill-creator` |
| Cloud service + Terraform (`technical-framework-researcher-terraform`) | `skill-creator` |
| Architecture (C4, DDD, TOGAF) | `architecture-approaches-skill-generator` |
| Methodologies (Scrum, SAFe) | `methodologies-skill-generator` |
| Terraform practices (`terraform-engineering-best-practices-researcher`) | `terraform-instructions-compiler` (generates .instructions.md, not SKILL.md) |

---

## Tips

- **Code is mandatory in ✅**: Each "Always Do" MUST have a working code block. No code = incomplete skill.
- **Alternatives in 🚫**: Each "Never Do" must say WHAT to do instead. "Don't do X" without an alternative is unhelpful.
- **Progressive disclosure**: Basic information first, advanced details later. Don't frontload everything.

## Common Pitfalls

| Pitfall | Solution |
|-----------|---------|
| Creating a skill without prior research | Always research first — avoids hallucinations |
| Mixing versions in the same skill | One skill = one version. Keep separate. |
| ✅ without code | Add a working code block |
| 🚫 without alternative | Always include "Instead, do Y" |
| Generic name ("utils", "helpers") | Use descriptive gerund form (e.g., `provisioning-oci-functions`) |

## Full Flow

See: [Knowledge Base Flow](../fluxos/fluxo-base-conhecimento.md)
