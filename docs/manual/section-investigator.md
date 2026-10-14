# Agent: section-investigator

> **Model:** `sonnet` | **Tools:** WebSearch, WebFetch
> **Role:** Lightweight parallel sub-investigator for a single research section.

**Internal helper — not routed by any `/command`.** Spawned by
[framework-researcher](framework-researcher.md) via the `Agent` tool during deep research
(`depth=deep`/`exhaustive`), one instance per major documentation section defined in the
invoking skill's `SKILL.md`.

**What it does:** Fetches official documentation for exactly one assigned topic (a
`SECTION_ASSIGNMENT`, a `RESEARCH_TARGET`, a set of `OFFICIAL_URLS`, the `SOURCE_HIERARCHY`, and a
`FRESHNESS_THRESHOLD` — all passed in by the parent call) and returns structured findings in the
`Section / Findings / Sources / Gaps` shape the parent expects.

**What it does NOT do:** Plan the research, write any output file, or spawn further sub-agents.
It has no `Write` or `Agent` tool for exactly that reason — least privilege, enforced by the tool
whitelist, not just by instruction.

## Invocation contract (from the caller's side)

```
Task tool call:
  subagent_type: section-investigator
  SECTION_ASSIGNMENT: <exact section name and scope from SKILL.md>
  RESEARCH_TARGET: <tech> <version>, <context>
  OFFICIAL_URLS: <comma-separated priority URLs from SKILL.md External Resources>
  SOURCE_HIERARCHY: Official docs > official blog > official examples > reject community
  FRESHNESS_THRESHOLD: 12  (months; 6 for researching-technical-frameworks)
```

The parent (`framework-researcher`) merges results from N parallel calls before handing them to
[research-synthesizer](research-synthesizer.md) for P4.

## Related

- [framework-researcher](framework-researcher.md) — the only caller
- [research-synthesizer](research-synthesizer.md) — the sibling helper that merges these findings
