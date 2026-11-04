# Deferred items

Written only by `scripts/state_event.py <slug> defer ...`. Anything left for later (a unit waiting
for a final release, a G3 leftover, a step moved to another run) gets an owner and a resume trigger.
Carried to the next execution while OPEN or RESUMED.

| Timestamp | ID | Status | Owner | Trigger | Actor | Text |
|---|---|---|---|---|---|---|
| 2026-10-30T10:35:04 | D-001 | OPEN | orchestrator | G2 answer | orchestrator | verify_skill.py bans literal .github/; Actions skills need it in uses: paths (placeholder ./<repo-workflows-dir>/ used). Ask user to allow exception for packages/github-actions-cicd |
| 2026-10-30T10:53:23 | D-001 | RESUMED | orchestrator | G2 answer | orchestrator | G2: exception approved |
| 2026-10-30T10:54:34 | D-001 | CLOSED | orchestrator | G2 answer | orchestrator | verifier exception in place, regression test passed |
| 2026-10-30T11:05:15 | D-002 | OPEN | user | G3 decision list (or earlier if a skill needs it) | orchestrator | GitHub Free private repos lack environment secrets and deployment branch policies (Pro/Team only, per Java research). Family rules 10/16 assume environments. Decide: support Free (repo secrets + OIDC- |
| 2026-10-30T11:21:31 | D-002 | CLOSED | user | G3 decision list (or earlier if a skill needs it) | orchestrator | DEC-012; family rule 16 rewritten |
| 2026-10-30T11:21:32 | D-003 | OPEN | user | G3 decision list | orchestrator | OCI researcher: oci-terraform rules terraform-state-backend and terraform-cicd say OCI has no state locking; native oci backend (TF >= 1.12) locks via If-None-Match. Other package - not edited by this |
| 2026-10-30T12:06:19 | D-004 | OPEN | orchestrator | apm install background task completes | orchestrator | P5 install rehearsal: run after_install.py --package github-actions-cicd, check .claude artifacts, shared-unlock |
| 2026-10-30T12:09:46 | D-005 | OPEN | user | G3 decision list | orchestrator | building-agent-packages already fails its own verify_skill at HEAD: p8-mechanical-close.md:10 and hybrid-format-checklist.md:9 mention the literal '.github/' rule text. Pre-existing, not from this run |
| 2026-10-30T12:15:03 | D-004 | CLOSED | orchestrator | apm install background task completes | orchestrator | full install done 1666s; recovered; .claude agent-package-builder playbooks stale until P8 |
| 2026-10-30T12:27:19 | D-006 | OPEN | orchestrator | P8 docs | orchestrator | AUD-2: CLAUDE.md lacks github-actions-cicd paragraph, How-to-run line and refreshed counts (P8 step 4 with check_counts.py) |
