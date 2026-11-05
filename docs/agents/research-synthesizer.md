# Agent: research-synthesizer

> **Model:** `sonnet` | **Tools:** Read, Write, Grep
> **Role:** Research Merge & Format Enforcement Agent.

**Internal helper — not routed by any `/command`.** Invoked by
[framework-researcher](framework-researcher.md) at P4, once per research run, after all
[section-investigator](section-investigator.md) sub-calls (if any — only spawned at
`depth=deep`/`exhaustive`) have returned.

**What it does:** Reads the invoking skill's `blueprints/output-format.md` skeleton first, then
fills each section from the merged `P2_FINDINGS` block, resolving any `MERGE_REQUIRED: <topic>`
flags left by overlapping sub-investigators, runs the skill's verification checklist, and writes
the final `research_[TECH]_v[VERSION].md` file.

**What it does NOT do:** Fetch web pages itself (no `WebSearch`/`WebFetch` in its tool whitelist —
by the time it runs, all fetching is done) and does not plan the research scope; both are
`framework-researcher`'s job, at P1/P2.

## Invocation contract (from the caller's side)

```
Task tool call:
  subagent_type: research-synthesizer
  → receives: P2_FINDINGS (merged, MERGE_REQUIRED flags included),
              the skill's blueprints/output-format.md path,
              the target output path (research_[TECH]_v[VERSION].md)
```

## Related

- [framework-researcher](framework-researcher.md) — the only caller; see its P4 for the exact
  handoff
- [section-investigator](section-investigator.md) — produces the findings this agent merges
