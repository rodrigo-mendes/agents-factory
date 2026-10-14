# Skills — Taxonomy & Conventions

This directory holds the project's **knowledge-skills** — model-loaded pattern libraries. The
**command entry points** that fork to a subagent were migrated to [`.claude/commands/*.md`](../commands/)
(46 files); this directory no longer holds command-skills. This README is the map; the authoritative
command catalog is [`.claude/AGENTS.md`](../AGENTS.md).

## Command entry points → `.claude/commands/`

Slash-commands (`/add-oci-function`, `/deploy-function`, …) live in `.claude/commands/*.md`. Their
frontmatter forks to the executing subagent and blocks for the result:

```yaml
context: fork                    # runs in a forked sub-context
agent: oci-functions-java        # which subagent executes it
background: false                # block and stream output inline
disable-model-invocation: true   # never auto-triggered; only explicit /command
```

Each command body injects `$ARGUMENTS` (the target the user types) and points to the knowledge-skill
it reads (`**Skill**: ...`). These are the entries in the AGENTS.md prompt catalog. Naming: `add-*`
(create/extend infra or code), `design-*` (advisory design via architect), `deploy-function` /
`debug-function` (ops), `execute-pattern` / `engineer-terraform-project` / `audit-*` (orchestration),
and the generic front-door entry points (`provision-infra`, `develop-function`, `add-observability`,
`create-serverless-capability`).

## Knowledge-skills — model-loaded on demand

Plain frontmatter (`name` + `description` only). The model reads these directly when a task matches the description — no fork, no agent field. Naming prefixes:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `designing-*` | Architecture / decision guidance (ask-first, trade-offs) — **no HCL** | `designing-oci-logging` |
| `provisioning-*` | Terraform HCL patterns (always-do, resource blocks) | `provisioning-oci-logging` |
| `developing-*` / `implementing-*` / `integrating-*` / `invoking-*` / `publishing-*` | Java function code patterns (FDK, SDK) | `developing-oci-functions-java` |
| `monitoring-*` / `observing-*` / `logging-*` | Observability instrumentation | `observing-oci-java-functions` |
| `managing-*` / `testing-*` / `engineering-*` | Terraform lifecycle (state, CI/CD, tests, governance) | `managing-terraform-state` |
| `architecting-*` / `validating-*` / `scaffolding-*` | Cross-cutting (arch overview, live validation, scaffolds) | `validating-oci-observability` |

## design → provision pairing

Most services have a `designing-oci-<svc>` (architecture decisions) **and** a `provisioning-oci-<svc>` (Terraform HCL). They are complementary, not duplicates: design decides *what/why*, provisioning writes the *how*. Each `designing-*` skill cross-links its `provisioning-*` counterpart for the HCL, and vice-versa.

> Note: a `designing-*` skill's frontmatter `name` must match its directory (`name: designing-oci-<svc>`), not the provisioning sibling. Keep the lead verb "Designs" (not "Provisions") in its description.

## Blueprints

36 skills carry a `blueprints/` subdirectory with the standard four files:

```
blueprints/
  always-do-patterns.md      # mandatory guardrails + code
  ask-first-decisions.md     # architectural crossroads + trade-off matrices
  never-do-patterns.md       # anti-patterns (❌ wrong / ✅ correct)
  integration-patterns.md    # cross-service integration
```

`scaffolding-oci-function` (uses `templates/`) and `validating-oci-observability` (uses `scripts/`) do **not** carry blueprints — that's expected, not a defect. (The command entry points, now in `.claude/commands/`, also carry none.)

## Related-skill discovery

The four observability skills overlap by design and cross-link each other:
`monitoring-oci-apm` (APM domains/tracing) · `monitoring-oci-java-functions` (custom metrics) · `observing-oci-java-functions` (all three pillars) · `configuring-oci-monitoring-alarms` (alarms). Start from `observing-oci-java-functions` for a function-level overview.
