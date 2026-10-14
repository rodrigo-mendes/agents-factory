# Package brief — <slug>

Copy to `workspace/<slug>/PACKAGE_BRIEF.md` and fill in. Lists accept frameworks, needs, or both.

```yaml
slug: <kebab-case>                  # workspace/<slug>/ and package name suffix
language: en                        # artifact language
frameworks:                         # name + optional version (missing version -> P1 proposes the current one)
  - <Framework> <version>
needs:                              # plain-language needs; P2 maps each to candidate frameworks
  - <need>
legacy_source: <path or none>       # read-only project/agent to migrate from
deliverables: [skills, agent, rules, readme]   # also: structure-skill, orchestrator-skill
agent_kind: executor                # executor | advisory | none
out_of_scope: []                    # explicit negative scope
research_worker: researching-technical-frameworks   # per unit override allowed in P2
rounds: 3                           # P6 quality loop; integer >= 1 (0 requires explicit confirmation)
```

Rules: overlapping items are merged and shown at G1; a need with no identifiable official source
becomes a declared gap; every unit records which item motivated it.
