# Claude Code Engine Mechanics Contract — Evaluation Baseline

The baseline the `audit-cc-architecture-engine` lens validates against. It replaces the VS Code Copilot
engine model (applyTo firing, name dedup, passive injection) with the Claude Code engine model
(`paths:` glob firing, auto-listing budget, `context: fork` isolation, progressive-disclosure budget,
permissions coherence).

---

## The two Claude Code loading mechanisms

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Code Engine                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ALWAYS-ON CONTEXT                                                │
│  ─────────────────────────────────────────                        │
│  • CLAUDE.md is injected every turn (project + user memory)      │
│  • Auto-invocable skills (no disable-model-invocation) have their │
│    name + description ALWAYS listed → costs the auto-listing      │
│    budget even when never used                                    │
│                                                                   │
│  PASSIVE PATH (automatic, path-triggered)                         │
│  ─────────────────────────────────────────                        │
│  1. A file is touched whose path matches a rule's `paths:` glob   │
│  2. That rule is auto-loaded into context                         │
│  3. Multiple matching rules all load                              │
│                                                                   │
│  ACTIVE PATH (explicit / deliberate)                              │
│  ─────────────────────────────────────────                        │
│  1. User invokes /command (a SKILL.md with context: fork)        │
│  2. The command forks into its `agent:` subagent — clean, ISOLATED│
│     context (no parent conversation state carried in)             │
│  3. The subagent reads skills/blueprints it needs (file I/O)     │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│  POTENTIAL FAILURES                                               │
│  ─────────────────────────────────────────                        │
│  • `paths:` glob never fires (wrong pattern) or over-fires        │
│  • Too many auto-invocable skills → auto-listing budget bloat     │
│  • Deliberate command missing disable-model-invocation → it       │
│    pollutes the auto-listing budget                               │
│  • Forked command assumes parent-context state it can't see       │
│  • SKILL.md @file-imports a large blueprint → eager-load bloat    │
│  • name collision across skills/agents/rules → silent shadowing   │
│  • tools:/allowed-tools: field swap → artifact breaks             │
│  • Invalid model: value → subagent fails to load                  │
│  • allowed-tools a skill needs is denied in settings.json         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key engine rules

1. **CLAUDE.md is always-on** — every line counts against the budget on every turn.
2. **Auto-listing costs budget** — each skill WITHOUT `disable-model-invocation` has its `name` +
   `description` surfaced so the model can auto-invoke it. Deliberate commands set
   `disable-model-invocation: true` to stay OFF this list (accessible only via `/name`).
3. **`paths:` is the passive trigger** — a rule loads when a touched path matches its `paths:` glob.
   Greedy: all matching rules load. Over-broad `paths: **/*` loads a rule for everything.
4. **`context: fork` isolates** — a forked command runs in a clean subagent context. It must not assume
   the parent conversation's variables/state are present.
5. **Progressive disclosure protects the budget** — a `SKILL.md` should LINK to blueprints
   (`[text](./blueprints/x.md)`), never `@file`-import large content inline (which eager-loads it).
6. **`name` must be unique** across skills/agents/rules — a collision causes one artifact to silently
   shadow another (the Claude Code analogue of Copilot's name-dedup drop).
7. **Field discipline** — subagents use `tools:`; skills/commands use `allowed-tools:`. Swapping breaks
   the artifact.
8. **`model:` validity** — `opus`/`sonnet`/`haiku`/`fable`/`inherit` or an explicit ID. Old versions
   and `*plan` suffixes are invalid.
9. **Permissions coherence** — `.claude/settings.json` allow/ask/deny must not deny a tool a skill
   declares in `allowed-tools:`, and should not carry dead permissions.

---

## Budget simulation format

Replace the Copilot "injection simulation" with a **budget simulation**: estimate what is loaded for a
representative task and compare to a practical limit.

```
BUDGET SIMULATION: user runs {task} touching a {file-type} file
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALWAYS-ON:
  1. CLAUDE.md ................................ [~N lines]
  2. Auto-listed skill descriptions (K skills) [~N lines]
     (skills without disable-model-invocation)
  ────────────────────────────────────────────────────────
  ALWAYS-ON SUBTOTAL: ~N lines

PASSIVE (rules whose paths: match {file-type}):
  3. rule-a.md (paths: {glob}) ............... [~N lines]
  4. rule-b.md (paths: {glob}) ............... [~N lines]
  ────────────────────────────────────────────────────────
  PASSIVE SUBTOTAL: ~N lines

ACTIVE (loaded on the forked command's demand):
  5. {command} SKILL.md ...................... [~N lines]
  6. {skill}/SKILL.md + linked blueprints .... [~N lines]
  ────────────────────────────────────────────────────────
  ACTIVE SUBTOTAL: ~N lines

COMBINED (worst case for this task): ~N lines
BUDGET STATUS: ✅ Within limits / ⚠️ Approaching limit / ❌ Exceeds limit
```

Plus two tables the engine lens always produces:

**Name-collision table** — every `name` value across `.claude/skills/*`, `.claude/agents/*`,
`.claude/rules/*`; flag any value used more than once.

**Field-swap table** — every subagent using `allowed-tools:` (should be `tools:`) and every
skill/command using `tools:` (should be `allowed-tools:`).
