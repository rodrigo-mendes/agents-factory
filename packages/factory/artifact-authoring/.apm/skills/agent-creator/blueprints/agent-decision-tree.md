# Agent Decision Tree

Pick exactly one starting template. Do not blend two shapes into one agent.

| Situation | Template | Precedent in this repo |
|---|---|---|
| Executes and writes artifacts, follows a P0–P5 workflow | [`TEMPLATE.AGENT.md`](../assets/TEMPLATE.AGENT.md) | `artifact-author`, `quality-validator` |
| Only analyzes and recommends — never writes | [`TEMPLATE.ADVISORY-AGENT.md`](../assets/TEMPLATE.ADVISORY-AGENT.md) | none yet live (`tools: Read, Grep, Glob` only — `section-investigator` is close but is an internal fetch helper, not user-facing) |
| Coordinates 2+ domains, or fans out to sub-agents via `Agent` | [`TEMPLATE.ORCHESTRATOR-AGENT.md`](../assets/TEMPLATE.ORCHESTRATOR-AGENT.md) | `architecture-auditor` (3-lens consensus), `framework-researcher` (parallel `section-investigator`), `skill-evaluator` (scenario runs) |

## Follow-up checks after picking a template

1. **Does a skill already exist that should route to this agent?** If not, you're creating an
   orphan — pair this with a new or updated `SKILL.md` carrying `agent: <name>`.
2. **Is this agent invoked only by another agent (never by a `/command`)?** Then it's an internal
   helper (like `section-investigator`, `research-synthesizer`) — its `tools:` should be the
   narrowest possible, and it needs no routing skill of its own.
3. **Does the workflow have an approval gate before writing output?** If yes, the orchestrator
   template's `tools:` must include `EnterPlanMode, ExitPlanMode` **and** the body must actually
   call them at the gate — not just declare them. See the Quick Reference note in `SKILL.md` for
   why a declared-but-unused pair is worse than omitting it.
