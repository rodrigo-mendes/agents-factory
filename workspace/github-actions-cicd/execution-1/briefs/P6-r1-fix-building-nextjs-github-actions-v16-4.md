Agent: artifact-author (fix cycle, one skill)
Skill: packages/github-actions-cicd/.apm/skills/building-nextjs-github-actions-v16-4/
Findings to fix:
MEDIUM F-023: Vercel token/org/project only on the pull/build/deploy steps (not job env); _deploy-vercel environment: must be optional for the Free F2 variant (or document dropping it); container hand-off uses the new _image-publish `artifact-name` input (coordinate: name it exactly `artifact-name`).
MEDIUM F-020: timeout-minutes on _deploy-s3-cf, rollback job, _deploy-vercel, _node-build; concurrency on ci-web.
MEDIUM F-019: role variable AWS_DEPLOY_ROLE_ARN (rule 17); use the cloud/login-aws composite from federating-github-actions-aws-oidc (inputs role-arn, region, session-name, role-duration-seconds).
LOW (cheap): rename Vercel options "F1/F2" to "Option A/Option B" (collide with fact IDs); drop --token on the command line when VERCEL_TOKEN is in env; pass inputs to run: only via env: (_deploy-s3-cf); Contents list in unverified-and-risks.md.
Approval line: The user approved 9 skills, 2 agents, 4 rules and command /building-cicd-pipelines on 2026-10-30 (G1, workspace/github-actions-cicd/execution-1/state/gates/G1.md) and the fan-out at G2 (state/gates/G2.md); this is P6 fix cycle round 1. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent; do NOT enter plan mode.
- Change only what a listed finding names; keep tags/registers consistent (update unverified-and-risks.md counts and mapping when you add/remove tags); keep every blueprint <= 160 lines; SKILL.md frontmatter only name + description.
- Do not touch _family_* files, shared files, other skills or other packages. If a finding contradicts a family fact, stop and report it.
- Apply workspace/github-actions-cicd/_family_facts.md (F1-F42) and _family_rules.md (1-18; NEW 17 canonical names, 18 timeouts/concurrency/id-token/env secrets) as given.
- Never make shipped text READ workspace/; never invent SHAs or versions.
Evidence: the round-1 reports in workspace/github-actions-cicd/execution-1/rounds/round-1/ (validate__<target>.md, test__<target>.md, audit__package.md) give file:line and fix hints.
Done when: .claude/skills/building-agent-packages/scripts/verify_skill.py <skill-dir> would exit 0 (the orchestrator runs it) and you return a list "F-id -> what changed (file)".
