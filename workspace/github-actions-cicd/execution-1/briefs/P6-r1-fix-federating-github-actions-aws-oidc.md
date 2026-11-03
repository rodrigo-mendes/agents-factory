Agent: artifact-author (fix cycle, one skill)
Skill: packages/github-actions-cicd/.apm/skills/federating-github-actions-aws-oidc/
Findings to fix:
HIGH F-015: add a `role-duration-seconds` input to cloud/login-aws (default 3600, documented: must not exceed the role maximum; chained roles capped at 1h) and explain why; update callers.
MEDIUM F-027: "created on or after 2026-07-15" -> "after 2026-07-15" (F26 wording) in SKILL.md:21,53.
MEDIUM F-019: role variables AWS_PR_ROLE_ARN (environment <env>-pr) and AWS_DEPLOY_ROLE_ARN (<env>) per rule 17; read them inside the job that declares the environment.
MEDIUM F-021: id-token: write only on the login job (rule 18).
LOW (cheap): persist-credentials: false on checkout examples; remove the unsourced "AWS CLI v2.39.2" or tag it (unverified); avoid raw F-numbers/"family rule N" in shipped text (say the fact itself).
Approval line: The user approved 9 skills, 2 agents, 4 rules and command /building-cicd-pipelines on 2026-10-30 (G1, workspace/github-actions-cicd/execution-1/state/gates/G1.md) and the fan-out at G2 (state/gates/G2.md); this is P6 fix cycle round 1. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent; do NOT enter plan mode.
- Change only what a listed finding names; keep tags/registers consistent (update unverified-and-risks.md counts and mapping when you add/remove tags); keep every blueprint <= 160 lines; SKILL.md frontmatter only name + description.
- Do not touch _family_* files, shared files, other skills or other packages. If a finding contradicts a family fact, stop and report it.
- Apply workspace/github-actions-cicd/_family_facts.md (F1-F42) and _family_rules.md (1-18; NEW 17 canonical names, 18 timeouts/concurrency/id-token/env secrets) as given.
- Never make shipped text READ workspace/; never invent SHAs or versions.
Evidence: the round-1 reports in workspace/github-actions-cicd/execution-1/rounds/round-1/ (validate__<target>.md, test__<target>.md, audit__package.md) give file:line and fix hints.
Done when: .claude/skills/building-agent-packages/scripts/verify_skill.py <skill-dir> would exit 0 (the orchestrator runs it) and you return a list "F-id -> what changed (file)".
