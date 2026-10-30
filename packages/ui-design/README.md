# ui-design

UI/UX agents for a SaaS front end: design system, design ADRs, wireframes and the review of both
and of the built front end. They rely on the official Vercel design skills in `vercel-frontend`
(`building-components`, `web-design-guidelines`, `composition-patterns`).

## Package Contents

```
packages/ui-design/
├── apm.yml                                  <- deps: factory-core, vercel-frontend
├── README.md
└── .apm/agents/
    ├── ui-ux-designer.agent.md              <- tools: Read, Grep, Glob; model: sonnet
    └── ui-design-reviewer.agent.md          <- tools: Read, Grep, Glob; model: sonnet
```

| Agent | Does | Returns (inline) |
|---|---|---|
| `ui-ux-designer` | E2b design system (light/dark tokens, contrast, component states) and design ADRs; E3b wireframes in ASCII with R* tags and 4 states, plus navigation | file contents (`design/design-system.md`, `design/adr/NNN-*.md`, `design/wireframes/<screen>.md`, `design/navigation.md`) and a report record (role `designer`) |
| `ui-design-reviewer` | Reviews E2b, E3b and, at E6, the fidelity of the built front to wireframe and tokens | `verify-E2b`, `verify-E3b`, `review-NN` (role `frontend`) |

Neither agent has a Write tool: the manager `building-aws-saas-serverless-quarkus-react-nextjs` saves
the content. The designer never reviews; the reviewer never creates or corrects a design. Missing
brand, languages or accessibility level come back as numbered questions (`needs-input`).

Depends on: factory-core, vercel-frontend. Used by: aws-saas-serverless-quarkus-react-nextjs.
