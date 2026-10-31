# Invocation Flow Contract — Evaluation Baseline (Claude Code)

The baseline the `audit-cc-architecture-flow` lens traces against: the canonical delegation chain, the
three entry paths, and the Reachability Matrix format.

---

## Canonical chain

```
/command  →  Subagent (fork)  →  Rules (paths:)  →  Skills
  G3            G1                  G2                 G4
```

A request enters at a command (or directly at the subagent, or at an auto-invocable knowledge skill),
the subagent orchestrates, rules auto-load for touched paths, and skills provide the terminal
knowledge/implementation. A **complete chain** resolves every step to a real, referenced file. A
**broken chain** fails at some step N (missing file, missing reference, or a cycle).

---

## The three entry paths

| Path | Trigger | How the engine reaches it | Auditor test |
|---|---|---|---|
| **PATH 1 — Command** | User types `/command` | `SKILL.md` has `context: fork` + `agent: {target}` → forks into the subagent | The command file exists, `agent:` resolves, the subagent references the needed skill |
| **PATH 2 — Auto-delegation** | User request matches a subagent's `description` "Use when" | Model auto-delegates to `.claude/agents/{target}.md` | The subagent's `description` covers the request domain and reaches its skills |
| **PATH 3 — Knowledge skill** | User request matches a knowledge skill's `description` "Use when" | Auto-invocable `SKILL.md` (no `disable-model-invocation`) loads on demand | The skill is self-contained and its `description` trigger is specific |

**Key rule:** a G4 knowledge skill reachable only via PATH 3 (description match, no command forking to
it) is **NOT an orphan**. It is legitimately reachable. Only flag as orphan a file reachable by none of
the three paths.

---

## Cycle & dead-end definitions

- **Dead-end chain**: an entry point whose chain fails to reach any terminal skill (e.g. `/command`
  forks to a subagent that references no skill for that domain).
- **Cycle**: `/command → subagent → a command that re-forks into the same subagent for the same
  intent`, with no terminal skill — loops without producing output.
- **Orphan command**: a `SKILL.md` with `agent: {X}` where `.claude/agents/{X}.md` does not exist.
- **Unreachable skill**: a skill file no path (1/2/3) can reach.

---

## Reachability Matrix format

Rows = entry points (each `/command`, the `@subagent` auto-delegation, each knowledge skill, each rule
`paths:`). Columns = skills. A cell is ✅ if that entry point reaches that skill, ❌ if it doesn't, `—`
if not applicable (e.g. a knowledge skill is its own terminal — it doesn't "reach" other skills).

```
REACHABILITY MATRIX — {target-name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                        │ skill-1 │ skill-2 │ skill-3 │ ... │
━━━━━━━━━━━━━━━━━━━━━━━━┼─────────┼─────────┼─────────┼─────┤
/command-1              │   ✅    │   ❌    │   ❌    │     │
@subagent (description) │   ✅    │   ✅    │   ❌    │     │
knowledge-skill (desc)  │   —     │   —     │   ✅    │     │
rule paths: {glob}      │   ✅    │   ❌    │   ❌    │     │
━━━━━━━━━━━━━━━━━━━━━━━━┼─────────┼─────────┼─────────┼─────┤
REACHABLE BY ≥1 PATH    │   ✅    │   ✅    │   ✅    │     │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UNREACHABLE SKILLS: [list or "none"]
ORPHAN COMMANDS (agent: → missing subagent): [list or "none"]
DEAD-END CHAINS: [list or "none"]
```

The last row (REACHABLE BY ≥1 PATH) is the primary evidence for FCC.16 (reachability) and for orphan
detection.
