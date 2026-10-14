---
name: agent-creator
description: "Creates a Claude Code subagent (.claude/agents/<name>.md) from a validated template — persona, P0–P5 workflow, tools whitelist, and model pin. Use when adding a new subagent to an agent project, or converting a manual agent definition into the house standard."
argument-hint: "<domain-role> [advisory|orchestrator] (e.g. terraform-reviewer advisory)"
context: fork
agent: artifact-author
disable-model-invocation: true
---

# Agent Creator

## Function

Generates a new subagent definition (`.claude/agents/<domain-role>.md`) from one of the 3
validated templates in [`./assets/`](./assets/), and wires it to `../../rules/agent-frontmatter.md`
so it passes validation on the first try. Fills the gap the factory has had: a skill exists for
creating skills ([skill-creator](../skill-creator/SKILL.md)) and for compiling rules
([rules-compiler](../rules-compiler/SKILL.md)) — none existed for creating the third artifact type.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Agent Decision Tree](./blueprints/agent-decision-tree.md)** — which of the 3 templates to start from
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 scenarios (skill-evaluator contract)
- **[Verification Loop](#verification-loop)**
- **[Quick Reference](#quick-reference)** — the 7 live agents as worked examples
- **[External Resources](#external-resources)**

## Blueprints & Guardrails

### ✅ Always Do

- **Choose the template via the decision tree first** — read [agent-decision-tree.md](./blueprints/agent-decision-tree.md) before writing anything; do not guess between the 3 shapes.
- **Whitelist `tools:` minimally** — list only what the agent's own workflow actually calls. Never inherit by omission, never use `*`.
- **Pin `model:` explicitly** — `opus` for an agent that reasons over consensus or does multi-source fan-out (today: `architecture-auditor`, `framework-researcher`); `sonnet` for execution/generation agents (today: the other 5). Never a `*plan` suffix, never an old version string.
- **Write `description` as "Use when…"** — it is the only field the runtime uses for automatic delegation routing (`../../rules/agent-frontmatter.md`).
- **Confirm at least one skill will route to it** — an agent with no `agent: <name>` skill pointing at it is unreachable. Check with `grep -rl "^agent: <name>$" .claude/skills/*/SKILL.md` before finishing.
- **Validate against `agent-frontmatter.md`** — `name` matches the filename, `tools:` (not `allowed-tools:`), `model:` from the allowed set.

### ⚠️ Ask First

- **`tools: [..., Agent, ...]`** — only if the new agent genuinely fans out to sub-agents (today: `architecture-auditor`'s 3-lens consensus, `framework-researcher`'s parallel section-investigators, `skill-evaluator`'s scenario runs). Ask if unsure; declaring `Agent` without calling it is exactly the drift `agent-router-pattern-validator` and `audit-cc-architecture-engine` are meant to catch.
- **`tools: [..., EnterPlanMode, ExitPlanMode, ...]`** — only if the agent's own workflow has a P3-style approval gate it actually calls. A declared-but-unused plan-mode pair is worse than not declaring it — see the Quick Reference note below.
- **Body length approaching 300 lines** — ask whether a procedure belongs in the *invoking skill's* blueprints instead of the agent body.

### 🚫 Never Do

| ❌ Incorrect | ✅ Correct |
|---|---|
| Declare `tools:` the agent's body never calls | Audit the body first; whitelist only what's actually used |
| Duplicate a rule that already lives in a `paths:`-triggered rule | Reference the rule; keep the agent body about persona + workflow |
| Skip the decision tree and pattern-match off an existing agent | Read `agent-decision-tree.md` — existing agents may themselves need the same fix this skill exists to prevent |
| Ship the agent with zero skills routing to it | Create or update at least one skill with `agent: <name>` in the same change |

## Verification Loop

```
[ ] .claude/agents/<name>.md matches agent-frontmatter.md (name, tools:, optional model:)
[ ] `grep -rl "^agent: <name>$" .claude/skills/*/SKILL.md` returns at least 1 file
[ ] Every tool in `tools:` is called at least once in the agent body (or is a declared
    fan-out/plan-mode pair actually exercised by the workflow — not just listed)
[ ] /agent-router-pattern-validator passes for the new agent
```

## Quick Reference

The 7 live agents, as of this refactor — use these as worked examples, not as a source of new
placeholder content (the `examples/` directories were removed from `.claude/templates/` for being
hardcoded; do not recreate that problem here):

| Agent | `tools:` | `model:` | Template shape |
|---|---|---|---|
| `architecture-auditor` | `Read, Grep, Glob, Agent, Write, Bash, EnterPlanMode, ExitPlanMode` | `opus` | Orchestrator (3-lens consensus via `Agent`, plan-mode gate at P3) |
| `framework-researcher` | `Read, Grep, Glob, WebSearch, WebFetch, Write, Agent, EnterPlanMode, ExitPlanMode` | `opus` | Orchestrator (parallel `section-investigator` fan-out, plan-mode gate at P3) |
| `skill-evaluator` | `Read, Grep, Glob, Agent, Write, Edit` | `sonnet` | Orchestrator (spawns scenario runs via `Agent`) |
| `artifact-author` | `Read, Grep, Glob, Write, Edit` | `sonnet` | Standard (executes and writes skills/agents/rules) |
| `quality-validator` | `Read, Grep, Glob, Write` | `sonnet` | Standard (read + report; no `Bash` — nothing in its workflow shells out) |
| `research-synthesizer` | `Read, Write, Grep` | `sonnet` | Standard (internal helper — never routed by a `/command`, only invoked by `framework-researcher` via `Agent`) |
| `section-investigator` | `WebSearch, WebFetch` | `sonnet` | Advisory-shaped helper (read-only fetch; internal, same caller as above) |

`quality-validator` previously declared `Bash` with zero calls in its body, and
`architecture-auditor` declared `EnterPlanMode`/`ExitPlanMode` without ever calling them — both
fixed as part of this refactor (menor privilégio; a declared-and-unused plan-mode gate does not
enforce anything, prose alone does not stop execution).

## External Resources

- [agent-frontmatter rules](../../rules/agent-frontmatter.md) — required/optional fields, description style
- [TEMPLATE.AGENT.md](./assets/TEMPLATE.AGENT.md) — standard P0–P5 workflow agent
- [TEMPLATE.ADVISORY-AGENT.md](./assets/TEMPLATE.ADVISORY-AGENT.md) — read-only, advisory-only agent
- [TEMPLATE.ORCHESTRATOR-AGENT.md](./assets/TEMPLATE.ORCHESTRATOR-AGENT.md) — multi-domain / fan-out agent
- [naming-conventions](../../rules/naming-conventions.md) — `domain-role` pattern for agent filenames
