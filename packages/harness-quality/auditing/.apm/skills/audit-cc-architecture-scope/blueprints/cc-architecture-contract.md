# Claude Code Architecture Contract — Evaluation Baseline & Responsibility Matrix

This is the single source of truth every `audit-cc-architecture-*` lens cites. It defines the
Claude Code scope hierarchy (G0→G4 + governance) and the Responsibility Matrix — what belongs at each
layer of a `.claude/` agent project, and what constitutes **responsibility leakage**.

> This is the Claude Code counterpart of the Copilot `architecture-contract.md`. Layer semantics
> differ from Copilot's L0→L4 — read the mechanics below, do not assume a 1:1 mapping.

---

## Architecture Contract (Evaluation Baseline)

The correct layered architecture follows the **Skill (`/command`) → Subagent → Rules → Skills**
pattern with strict responsibility boundaries:

```
┌─────────────────────────────────────────────────────────────┐
│  G0 — CLAUDE.md (Global, always-on)                          │
│  Injected every turn. Project principles, conventions,       │
│  subagent catalog, command routing table.                    │
│  NO code examples, NO path-scoped guardrails inline.         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  G1 — Subagent (.claude/agents/<name>.md)                    │
│  Router / specialist. Intent classification, delegation,     │
│  orchestration workflow, `tools:` least-privilege.           │
│  NO implementation code, NO domain code examples.            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  G2 — Rules (.claude/rules/<name>.md, `paths:`)              │
│  Auto-loaded guardrails when a touched path matches `paths:`.│
│  Cross-cutting standards, conventions, skill routing hints.  │
│  NO full code examples (delegate to skills). NO routing      │
│  tables that duplicate the subagent/CLAUDE.md.               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  G3 — Commands (skills/<name>/SKILL.md, deliberate)          │
│  `context: fork` + `agent:` + `disable-model-invocation:true`│
│  Deliberate `/command` entry point that forks to a subagent. │
│  Structured task workflow, argument-hint, output spec.        │
│  NO implementation code (delegates to skills/blueprints).    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  G4 — Skills / knowledge (skills/<name>/SKILL.md + blueprints)│
│  Auto-invocable knowledge (NO disable-model-invocation).     │
│  Code examples, scripts, verification commands live HERE.    │
│  Three-tier (✅⚠️🚫), version context, progressive disclosure.│
└─────────────────────────────────────────────────────────────┘

        ┌───────────────────────────────────────────────┐
        │  G-perm — .claude/settings.json (governance)  │
        │  Permissions allow/ask/deny. Cross-cutting.   │
        │  Not a scope layer — a governance concern.    │
        └───────────────────────────────────────────────┘
```

### Two Claude Code subtleties with no clean Copilot analogue

1. **G3 and G4 are the same file type** (`SKILL.md`). They are distinguished ONLY by frontmatter:
   `disable-model-invocation: true` present → deliberate command (G3); absent → auto-invocable
   knowledge skill (G4). Leakage and classification checks must key off the **frontmatter**, never the
   filename or folder.
2. **`.claude/settings.json`** (permissions allow/ask/deny) is a Claude-Code-only governance layer with
   no Copilot equivalent. Treat it as a cross-cutting concern (`G-perm`), not a scope layer.

---

## Responsibility Matrix (Single Source of Truth)

Any ✅ found in the wrong column is a **responsibility leakage violation**.

| Responsibility | G0 CLAUDE.md | G1 Subagent | G2 Rules (`paths:`) | G3 Command | G4 Skill | G-perm settings.json |
|---|---|---|---|---|---|---|
| Project-wide conventions / principles | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Subagent catalog / command routing table | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Intent classification / delegation | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `tools:` least-privilege declaration | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Orchestration workflow (P0–P5 / fan-out) | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Path-scoped guardrails (`paths:` glob) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Cross-cutting standards / conventions | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Deliberate `/command` entry + `argument-hint` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `context: fork` + `agent:` linkage | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Structured task workflow / output spec | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Implementation code / scripts / examples | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Three-tier safety (✅⚠️🚫) | ❌ | ❌ | ❌ | (⚠️ allowed) | ✅ | ❌ |
| Version context & constraints | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Verification loop (bash) | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Progressive disclosure (`blueprints/`) | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Permissions (allow/ask/deny) | ❌ (references only) | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Field-and-frontmatter contract (Claude Code specifics)

These are the mechanical rules the repo enforces (`.claude/rules/skill-frontmatter.md`,
`CLAUDE.md` Gotchas). They are evaluation anchors across all lenses:

| Rule | Correct | Wrong (leakage / defect) |
|---|---|---|
| Tools field on **skills/commands** | `allowed-tools:` | `tools:` (that is the subagent field) |
| Tools field on **subagents** | `tools:` | `allowed-tools:` (that is the skill field) |
| Deliberate command frontmatter | `context: fork` + `agent:` + `disable-model-invocation: true` | any missing → mis-classified as knowledge skill |
| Knowledge skill frontmatter | no `disable-model-invocation` (auto-invocable) | `disable-model-invocation: true` on a knowledge skill it shouldn't be |
| `name` (skills) | == folder name, kebab-case, ≤64 chars | mismatch → silent shadow / broken invocation |
| `name` (subagents) | == filename, kebab-case | mismatch |
| `description` (skills) | ≤1536 chars, contains a "Use when…" trigger | missing trigger, over length |
| `model:` (subagents) | `opus`/`sonnet`/`haiku`/`fable`/`inherit` or explicit ID | old versions, `*plan` suffix |
| Rules scope | `paths:` glob, specific | `paths: **/*` unless genuinely global |
| YAML values with `:` | quoted (e.g. `argument-hint: "Scope: new / review"`) | unquoted → YAML parse error |
| Large blueprint content | linked via `[text](./blueprints/x.md)` | `@file` eager-import inline (defeats progressive disclosure) |

---

## Claude-Code-specific leakage examples

- A rule (`.md` with `paths:`) containing a routing table → belongs in the subagent or CLAUDE.md.
- A subagent embedding code examples / HCL / Java → belongs in a G4 skill.
- `tools:` on a skill, or `allowed-tools:` on a subagent → field swap (a repo Gotcha).
- A knowledge skill that should be a deliberate command but lacks `disable-model-invocation` → wrong
  G3/G4 classification (it will auto-list and cost budget).
- `@file` eager import of a large blueprint inside a `SKILL.md` → defeats progressive disclosure and
  inflates the always-loaded budget.

---

*Baseline: Skill (`/command`) → Subagent → Rules → Skills pattern. Layers: G0 CLAUDE.md, G1 Subagent,
G2 Rules, G3 Commands, G4 Skills, G-perm settings.json.*
