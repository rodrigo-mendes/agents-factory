# Domain Compiler Contract

A `<domain>-instructions-compiler` skill (example:
[`terraform-instructions-compiler`](../../terraform-instructions-compiler/SKILL.md)) is an
action-command skill — `context: fork`, `agent: artifact-author`,
`disable-model-invocation: true` — that supplies domain data to the generic engine in
[`../SKILL.md`](../SKILL.md). Terraform content does not belong here, and neither does the next
domain's — each domain gets its own compiler skill, following this contract.

## Required local content

| What | Where | Purpose |
|---|---|---|
| File matrix | `SKILL.md`, Phase 3 section | file name → when to generate → target glob/`applyTo` |
| Pattern catalog | `assets/<domain>-standards-reference.md` | the ✅/⚠️/🚫 patterns Phase 4 pulls from |
| Interview questions | `blueprints/interview-questions.md` | domain-specific Phase 2 script |
| Official sources | `SKILL.md`, External Resources | dated links, Source Hierarchy compliant |
| Evaluation scenarios | `blueprints/evaluation-scenarios.md` | ≥ 4 scenarios (skill-evaluator contract) |

## Required links back to the engine

The domain compiler's own Phase 1 / Phase 4 / Phase 5 sections should not restate the generic
mechanics — link to `../rules-compiler/SKILL.md#phase-1--load-research--templates` (and the
equivalent anchors for phases 4 and 5), and document only what differs: the domain's own file
matrix and its own pattern catalog.

## What must stay generic — never fork per domain

The 3 templates (`TEMPLATE.STANDARDS.md`, `TEMPLATE.CONFIG.md`, `TEMPLATE.SKILLS.md`) live once,
in `rules-compiler/assets/`. A domain compiler links to them; it never copies them into its own
`assets/`. If a future domain needs a 4th template shape, add it to `rules-compiler/assets/` and
update the contract table above — do not invent a domain-local variant.

## Runtime vs. domain — do not conflate the two

A domain compiler's `Role` section should describe the **technology** it specializes in (e.g.
Terraform), never the **runtime** (Claude Code vs. Copilot) that consumes its output. The runtime
is decided by `TARGET_PLATFORM` and affects only the output file's format (`paths:` vs.
`applyTo:`) — it is not the compiler's identity.
