# Package brief — openspec-github

Source plan: C:\Users\r.dos.santos.mendes\.claude\plans\poderia-me-ajudar-aqui-curious-sunbeam.md (approved 2026-10-29).

```yaml
slug: openspec-github
language: en
frameworks:
  - GitHub CLI (gh) <current stable, P1>
  - GitHub Projects (v2) GraphQL API <current, P1>
  - GitHub Actions (issue_comment / pull_request / push, GitHub App token) <current, P1>
needs:
  - mirror OpenSpec changes, tasks, ADRs, escalations and spec-deltas into a GitHub Project (git stays canonical)
  - gate approvals by issue comment, validated by a GitHub Actions workflow (event login + allowlist)
  - spec CI on PR, board sync on push, archive via Actions (PR only)
  - split OpenSpec skill into a reusable package openspec-core
legacy_source: packages/handoff-core, packages/quarkus-aws-saas (read-only references)
deliverables: [skills, agent, rules, readme, scripts, workflow-templates]
agent_kind: executor              # openspec-github-syncer (push/status only, never pull)
out_of_scope: [oci-core profile tracker (follow-up), GitHub MCP server, GitHub Enterprise Server specifics]
research_worker: researching-technical-frameworks
rounds: 3
packages:
  - openspec-core (new; move specifying-changes-with-openspec-v1-15 unchanged)
  - github-core (new; 2 knowledge skills: gh+Projects v2, Actions automation)
  - openspec-github (new; bridge skill + scripts + workflows + agent + command + rule)
  - handoff-core (edit: depends on openspec-core; tracker: block in profile format)
  - quarkus-aws-saas (edit: depends on openspec-github; E1/E8/E9 + preflight)
```

User decisions (verbatim, 2026-10-29):
- Fonte: "Git canônico + Projects espelho (Recomendado)"
- OpenSpec: "Sim, openspec-core (Recomendado)"
- Integração: "gh CLI encapsulado  por scripts python"
- Escopo: "Aprovações dos gates, Escalations e perguntas, Spec-deltas (drift), ADRs, maxima integraçao"
- Actions: "Gate por comentário (Recomendado), CI de spec em PR (Recomendado), Sync do board no push, Archive via Actions"
- Credencial: "GitHub App (Recomendado)"
