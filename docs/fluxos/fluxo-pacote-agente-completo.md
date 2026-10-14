# Flow: Complete Agent Package

End-to-end orchestration from a brief to a committed APM package (skills + agent + rules), driven by
the inline skill [`building-agent-packages`](../../packages/agent-package-builder/README.md).

---

## Diagram

```mermaid
flowchart TD
    IN([brief / research_dir / resume]) --> P0[P0 intake + preflight]
    P0 --> P1[P1 version gate]
    P1 --> P2[P2 inventory + design + family facts]
    P2 --> G1{{G1 user: scope, version, units}}
    G1 --> P3[P3 pilot: 1 unit end to end]
    P3 --> G2{{G2 user: review pilot + cost}}
    G2 --> P4[P4 fan-out, batches of 4]
    P4 --> P5[P5 agent, rules, structure skill, apm.yml]
    P5 --> P6

    subgraph P6[P6 quality loop, rounds=N default 3]
        V[validate] --> T[test] --> A[audit] --> F[triage + fix]
    end

    P6 --> P7[P7 fact sweep]
    P7 --> P8[P8 mechanical close: scripts, apm install, counts]
    P8 --> G3{{G3 user: commit plan + leftovers}}
    G3 --> P9[P9 commits by explicit paths]
    P9 --> G4{{G4 user: push manually}}
```

## Entry modes

| Mode | Input | Enters at |
|---|---|---|
| `new` | list of frameworks and/or needs | P0 |
| `from-research` | folder with finished research | inspect -> P2 -> G1 |
| `resume` | working directory (state file optional) | first unfinished step |

## Workers it drives (unchanged)

`framework-researcher` (research), `artifact-author` (skills, agent, rules), `quality-validator`,
`skill-evaluator`, `architecture-auditor`. Launched as subagents with each worker's SKILL.md as spec,
flat (no nesting), with genuine user approvals relayed and recorded.

## See also

[Knowledge Base Flow](fluxo-base-conhecimento.md) · [Quality Flow](fluxo-qualidade.md) · [Project Creation Flow](fluxo-criacao-projeto.md)
