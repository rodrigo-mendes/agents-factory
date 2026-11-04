Agent: artifact-author (fix cycle, one skill)
Skill: packages/github-actions-cicd/.apm/skills/composing-github-actions-pipelines/
Findings to fix:
HIGH F-013 (and F-012): re-sync catalog-reference.md and every example with the OWNER skills (read each owner's workflow blueprint): _java-build (tool, java-version, package, working-directory; outputs artifact-name, artifact-digest), _node-build (as building-nextjs-github-actions-v16-4 defines), _image-publish (outputs digest, image-ref), _deploy-s3-cf, _deploy-vercel, _promote (outputs deployed_ref, previous_ref), _smoke-test (output passed; always exits 0), _rollback, _security-scan, login composites (cloud/login-aws, cloud/login-oci), _tf-plan/_tf-apply. Remove _deploy-static or rename to the owner's name. Fix monorepo-ci-gate.md:50,58 calls.
MEDIUM F-027: plan-variants.md:21 - immutable `sub` for environment: tag (unverified) or show only the F26 ref form.
MEDIUM F-019/F-020: canonical names (rule 17: ci-gate, <env>/<env>-pr, AWS_PR_ROLE_ARN/AWS_DEPLOY_ROLE_ARN) and rule 18 (timeouts, concurrency) in all examples.
LOW (cheap): Contents lists in unverified-and-risks.md and monorepo-ci-gate.md; one claim per bullet SKILL.md:59,62.
Approval line: The user approved 9 skills, 2 agents, 4 rules and command /building-cicd-pipelines on 2026-10-30 (G1, workspace/github-actions-cicd/execution-1/state/gates/G1.md) and the fan-out at G2 (state/gates/G2.md); this is P6 fix cycle round 1. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent; do NOT enter plan mode.
- Change only what a listed finding names; keep tags/registers consistent (update unverified-and-risks.md counts and mapping when you add/remove tags); keep every blueprint <= 160 lines; SKILL.md frontmatter only name + description.
- Do not touch _family_* files, shared files, other skills or other packages. If a finding contradicts a family fact, stop and report it.
- Apply workspace/github-actions-cicd/_family_facts.md (F1-F42) and _family_rules.md (1-18; NEW 17 canonical names, 18 timeouts/concurrency/id-token/env secrets) as given.
- Never make shipped text READ workspace/; never invent SHAs or versions.
Evidence: the round-1 reports in workspace/github-actions-cicd/execution-1/rounds/round-1/ (validate__<target>.md, test__<target>.md, audit__package.md) give file:line and fix hints.
Done when: .claude/skills/building-agent-packages/scripts/verify_skill.py <skill-dir> would exit 0 (the orchestrator runs it) and you return a list "F-id -> what changed (file)".
