# nextjs-frontend

Front-end executor and reviewer for a **Next.js static export** (S3 + CloudFront), built with pnpm on
Node 26 and the official Vercel skills from `vercel-frontend`.

## Package Contents

```
packages/nextjs-frontend/
├── apm.yml                                            <- deps: factory-core, vercel-frontend, handoff-core
├── README.md
└── .apm/
    ├── agents/
    │   ├── nextjs-frontend-integrator.agent.md        <- tools: Read, Grep, Glob, Edit, Write, Bash; model: sonnet
    │   └── nextjs-code-reviewer.agent.md              <- tools: Read, Grep, Glob; model: sonnet
    └── instructions/
        └── nextjs-static-export.instructions.md       <- applyTo: **/frontend/**, **/next.config.*
```

| Asset | Does |
|---|---|
| `nextjs-frontend-integrator` | One closed front task per work-order: tests first (`R1_empty_showsEmptyState`), minimal code, 4 states + 401/403, refactor, then `pnpm install --frozen-lockfile`, lint, test, build (`out/` and its sha256); report with Spec impact (role `frontend`). Calls only contract endpoints; never deploys |
| `nextjs-code-reviewer` | Read-only review: no server features, contract-only calls, no secrets in `NEXT_PUBLIC_*`, skills' Never-Do, ADRs, scenario-to-test matrix; `review-NN` (role `frontend`) returned inline. Runs before `ui-design-reviewer` |
| rule `nextjs-static-export` | Guardrails: `output: 'export'`, unoptimized images, no server features; unverified items are marked |

Known gap: browser login with Cognito (Hosted UI / OIDC PKCE) has no skill; it is an Ask First,
marked `(unverified)`. Publishing is done by the GitHub pipeline (`github-actions-cicd`), not by
these agents. Orchestrator: `building-aws-saas-serverless-quarkus-react-nextjs`.

Depends on: factory-core, vercel-frontend, handoff-core.
