Agent: artifact-author (fix cycle, one skill)
Skill: packages/github-actions-cicd/.apm/skills/limiting-blast-radius-github-actions-deploys/
Findings to fix:
MEDIUM F-024: the caller must end red after an automatic prod rollback (final job failing when smoke passed != true); check_script via env: not ${{ }} in run:; explain the Vercel exception (vercel build --prod at deploy vs build-once) or move build to the build stage with prebuilt output; complete-prod failure after smoke must have a rollback path.
MEDIUM F-019: required check `ci-gate` everywhere (approval-models.md ruleset JSON, scenarios); role variable AWS_DEPLOY_ROLE_ARN; use cloud/login-aws composite.
MEDIUM F-021: id-token: write only on the login job (_promote) per rule 18 - restructure or justify.
LOW (cheap): remove unused `environment` input of _smoke-test or use it; Contents list in unverified-and-risks.md; _build-orders.yml placeholder -> _java-build.yml from building-java-github-actions.
Approval line: The user approved 9 skills, 2 agents, 4 rules and command /building-cicd-pipelines on 2026-10-30 (G1, workspace/github-actions-cicd/execution-1/state/gates/G1.md) and the fan-out at G2 (state/gates/G2.md); this is P6 fix cycle round 1. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent; do NOT enter plan mode.
- Change only what a listed finding names; keep tags/registers consistent (update unverified-and-risks.md counts and mapping when you add/remove tags); keep every blueprint <= 160 lines; SKILL.md frontmatter only name + description.
- Do not touch _family_* files, shared files, other skills or other packages. If a finding contradicts a family fact, stop and report it.
- Apply workspace/github-actions-cicd/_family_facts.md (F1-F42) and _family_rules.md (1-18; NEW 17 canonical names, 18 timeouts/concurrency/id-token/env secrets) as given.
- Never make shipped text READ workspace/; never invent SHAs or versions.
Evidence: the round-1 reports in workspace/github-actions-cicd/execution-1/rounds/round-1/ (validate__<target>.md, test__<target>.md, audit__package.md) give file:line and fix hints.
Done when: .claude/skills/building-agent-packages/scripts/verify_skill.py <skill-dir> would exit 0 (the orchestrator runs it) and you return a list "F-id -> what changed (file)".
