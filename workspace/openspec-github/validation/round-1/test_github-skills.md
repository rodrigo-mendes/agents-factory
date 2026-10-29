# P6 round 1 TEST - github skills

Method: scenarios answered by reasoning over SKILL.md and linked files (no agents, no gh/network). Approval relay: PIPELINE_STATE.md#approvals (2026-10-29).

| Skill | Pass / Total |
|---|---|
| syncing-openspec-with-github-projects | 8 / 8 |
| automating-github-repos-with-actions | 7 / 7 |
| managing-github-projects-gh-v2-103 | 6 / 6 |

No failed scenarios. Evidence highlights:
- syncing S2/S5: SKILL.md "Who may run what" and Never Do ("Let an agent run `pull`"); "Trust bot records by exact login"; `_model.py:697` "is not in tracker.approvers".
- syncing S3: `_model.py:715` "out of order: the change is at Stage ..."; S4: exit 3 "tracker disabled" (`gh_projects_sync.py:744`); S6: `_gh.py:150` "older than the required"; S8: `gh_projects_sync.py:575` "REFUSED confirmation".
- syncing S7: Always Do classic PAT, Never Do fine-grained PAT, Ask First owner type with "broad `repo` scope".
- actions S1-S7: Always Do/Never Do rows cover env: passing, SHA pins, client-id, GITHUB_TOKEN refusal, user.type unverified, concurrency, path filters, allow-unsafe-pr-checkout, lockfile Ask First, community tools Ask First.
- managing S1-S6: Always Do (item-edit IDs, add-then-update, -L/paginate, 1s serial writes, gh 2.94.0), Never Do (GITHUB_TOKEN, node ID as --id, parse tables, auth refresh), Quick Reference (100 sub-issues, 8 levels, 80/min and 500/hr, winget), Ask First (65,536 body, unverified).

Minor non-failing observations: syncing S2 exact gate-workflow refusal text is only in scripts, not SKILL.md; actions S6 and managing S4/S5 details live in blueprints (prs-and-status-checks.md, issues-sub-issues-and-comments.md, graphql-and-rate-limits.md), not SKILL.md body.
