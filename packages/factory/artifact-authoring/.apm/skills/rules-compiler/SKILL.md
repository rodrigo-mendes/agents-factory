---
name: rules-compiler
description: "Reference for the generic 5-phase workflow (load research → interview → plan → generate → validate) that a domain-specific `<domain>-instructions-compiler` skill follows, plus the 3 canonical instruction templates (STANDARDS, CONFIG, SKILLS). Use when authoring a new domain compiler (e.g. a Kubernetes or AWS equivalent of `terraform-instructions-compiler`), or when executing an existing one that links here for its generic mechanics."
---

# Rules Compiler — generic engine

This is a **knowledge skill**, not a `/command`. It is never invoked directly — a domain compiler
(example: [`terraform-instructions-compiler`](../terraform-instructions-compiler/SKILL.md)) links
into it for the parts of the workflow that never change between domains, and keeps its own
file matrix, pattern catalog, interview questions, and official sources local.

Zero domain-specific content lives here. If a mention of a specific technology ever creeps into
this file, it belongs in a domain compiler instead — see
[domain-compiler-contract.md](./blueprints/domain-compiler-contract.md).

## The 5 Phases

### Phase 1 — Load Research & Templates

- Read the domain's research file completely before starting the interview. Classify every
  finding into ✅ Mandatory / ⚠️ Conditional / 🚫 Forbidden. A missing or unreadable research file
  triggers the domain compiler's error-handling path — never generate from memory.
- Load the 3 instruction templates from [`./assets/`](./assets/):
  - **[TEMPLATE.STANDARDS.md](./assets/TEMPLATE.STANDARDS.md)** — code quality, naming, structure rules
  - **[TEMPLATE.CONFIG.md](./assets/TEMPLATE.CONFIG.md)** — project configuration, backend/provider setup
  - **[TEMPLATE.SKILLS.md](./assets/TEMPLATE.SKILLS.md)** — skill integration and routing

### Phase 2 — User Interview

The domain compiler owns its own question script. This phase's only generic rule: ask before
assuming a ⚠️ conditional pattern's default — never silently pick one.

### Phase 3 — Planning

- After the interview, present the full file plan (name, when-to-generate condition, target
  glob/`applyTo` pattern) and wait for explicit user approval before writing anything.
- Never generate speculatively.
- Two planned files sharing an overlapping glob → ask whether to merge them or document
  precedence explicitly; do not silently choose.

### Phase 4 — Generate

- For each approved file, pick the matching template (STANDARDS / CONFIG / SKILLS), fill it with
  the domain's own matrix/catalog data, and write it to the location the target deploy format
  expects (`paths:` for a Claude Code rule, `applyTo:` for a Copilot instruction — the target
  decides the dialect, this skill does not choose a platform).
- One concern per file — never duplicate a rule across two generated files.
- Never use `**/*` as the sole glob; scope to the concern.
- Always deliver the Phase 5 coverage matrix, even when every pattern is already covered.

### Phase 5 — Validation

- [ ] Every generated file has valid frontmatter (`name`, `description`, and `paths:`/`applyTo:`)
- [ ] Every ✅ and 🚫 pattern from research appears in exactly one generated file
- [ ] Every ⚠️ pattern is either resolved (→ ✅, with a note of how) or explicitly deferred with a
      `<!-- TODO -->` comment — never silently dropped
- [ ] No secrets or credential literals in any example
- [ ] Coverage matrix delivered, showing 0 uncovered mandatory/forbidden patterns

## Authoring a new domain compiler

See [domain-compiler-contract.md](./blueprints/domain-compiler-contract.md) for what a
`<domain>-instructions-compiler` skill must supply locally, and how it should link back here
instead of restating these 5 phases.

## Assets

- [TEMPLATE.STANDARDS.md](./assets/TEMPLATE.STANDARDS.md) — canonical scaffold for a standards/rules file
- [TEMPLATE.CONFIG.md](./assets/TEMPLATE.CONFIG.md) — canonical scaffold for a project-config file
- [TEMPLATE.SKILLS.md](./assets/TEMPLATE.SKILLS.md) — canonical scaffold for a skill-routing file

## External Resources

- [skill-frontmatter rules](../../rules/skill-frontmatter.md) — this skill is a knowledge skill: `name` + `description` only, no `context:`/`agent:`
- [terraform-instructions-compiler](../terraform-instructions-compiler/SKILL.md) — the one domain compiler that exists today; read it alongside this file to see the contract applied
