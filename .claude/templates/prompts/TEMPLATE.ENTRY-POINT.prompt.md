---
name: [action-noun]
description: 'Generic entry point for [DOMAIN]. Collects context and requirements, then routes to the [agent-name] agent.'
agent: [agent-name]
argument-hint: 'Describe what [DOMAIN ARTIFACT] you need'
context: fork
disable-model-invocation: true
---

> ⚙️ **Technology-agnostic template.** Replace ALL [PLACEHOLDERS]. Names in e.g./[e.g., ...] are illustrative examples only — they are not standards or defaults of this factory.

# [DOMAIN TITLE]

## Context Collection

Before starting, I need to understand your request.

**Answer these questions:**

1. **What do you need?**
   - [Option A — specific capability/resource type]
   - [Option B — specific capability/resource type]
   - [Option C — specific capability/resource type]
   - [Option D — specific capability/resource type]
   - [Option E — integrated / full stack]

2. **Environment**: Which environment is this for? ([env options])

3. **[CONTEXT QUESTION 1]**: [Domain-specific context needed]

4. **[CONTEXT QUESTION 2]**: [Additional context — e.g., existing code, new project?]

## Workflow

Once I have your answers, I will follow the P0–P5 workflow:
- **P0**: Load the right skill(s) based on your needs
- **P1**: Analyze existing [files/code/infrastructure] in the workspace
- **P2**: Consult skill patterns (✅/🚫 rules)
- **P3**: Propose a plan for your approval
- **P4**: Generate [output type]
- **P5**: Validate with [validation commands]

---

## Scope Rejection Format

When a user request is outside this skill's scope, respond exactly:

> **Out of scope for [skill name].**
> This skill handles: [one-line description of what it does].
> Your request appears to match: `/[correct-command]` — [one-line description of that command].
> Run `/[correct-command] [args]` to proceed.

Never attempt to fulfill an out-of-scope request inline — always route to the correct command.
