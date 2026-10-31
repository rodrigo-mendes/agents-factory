# solution-architecture

Author and reviewer agents for the **logical solution design** of a SaaS: pieces, contracts, data,
logical security and architecture ADRs. No cloud detail: infrastructure belongs to `aws-architect`.

## Package Contents

```
packages/architecture/solution-architecture/
├── apm.yml                                            <- deps: factory-core, handoff-core
├── README.md
└── .apm/agents/
    ├── solution-architect.agent.md                    <- tools: Read, Grep, Glob, Write; model: opus
    └── solution-architecture-reviewer.agent.md        <- tools: Read, Grep, Glob; model: sonnet
```

| Agent | Does | Writes / returns |
|---|---|---|
| `solution-architect` | E2a: pieces, contracts, data model, logical security, targets, ADRs. E4: one design per flow (11 sections) plus the index `design.md` | `openspec/specs/architecture/**`, `openspec/changes/<id>/design.md`, `design/<flow>.md`, `result-NN-solution-architect.md` (role `solution-architect`) |
| `solution-architecture-reviewer` | Verifies coverage, contracts, errors, tenant isolation, ADR completeness, timing budget | `verify-E2a`, `verify-E4-<flow>`, `verify-E4-index` returned inline (the manager saves them) |

Both are non-interactive: missing decisions come back as numbered questions (`needs-input`), never
assumptions. Only the orchestrator `building-aws-saas-serverless-quarkus-react-nextjs` talks to the
user; ADRs stay `proposed` until the user approves E2. Handoff protocol: `coordinating-agent-handoffs`,
profile `coordinating-quarkus-aws-handoffs`. Folder layout: rule `openspec-project-layout`
(package `openspec-core`).

Depends on: factory-core, handoff-core. Used by: aws-saas-serverless-quarkus-react-nextjs.
