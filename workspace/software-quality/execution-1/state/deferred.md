# Deferred items

Written only by `scripts/state_event.py <slug> defer ...`. Anything left for later (a unit waiting
for a final release, a G3 leftover, a step moved to another run) gets an owner and a resume trigger.
Carried to the next execution while OPEN or RESUMED.

| Timestamp | ID | Status | Owner | Trigger | Actor | Text |
|---|---|---|---|---|---|---|
| 2026-10-31T23:13:21 | D-001 | OPEN | user | after this run | orchestrator | Wire an acceptance role into coordinating-quarkus-aws-handoffs and the SaaS orchestrator E5-E7 |
| 2026-11-01T01:48:26 | D-002 | OPEN | user | next successful apm install | orchestrator | apm.lock.yaml lacks _local/acceptance-testing and _local/quarkus-acceptance-testing entries (install failed on vercel externals); rerun apm install after fixing agent-browser checkout/LongPathsEnabled |
| 2026-11-01T01:48:26 | D-003 | OPEN | user | docs pass | orchestrator | README.md, docs/visao-geral.md, docs/capacidades/*, docs/manual/README.md counts were already stale before this run (246 skills/41 agents); only CLAUDE.md and packages/README.md updated |
