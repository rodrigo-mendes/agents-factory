Agent: artifact-author (fix cycle, one skill)
Skill: packages/github-actions-cicd/.apm/skills/securing-supply-chain-github-actions/
Findings to fix:
MEDIUM F-025: ci-api grants security-events: write / pull-requests: write only to the jobs that need them and only when CODE_SECURITY_ENABLED (split licensed jobs or use separate callers); deploy gate must grant what the called licensed jobs need or not call them.
MEDIUM F-019: required check `ci-gate` (not `gate`); cd-api must call `_image-publish.yml` from publishing-container-images-github-actions and use its `image-ref` output (already contains @sha256), not a placeholder.
LOW (cheap): licensed-jobs text says Checkov+Trivy results but uploads only trivy SARIF - align; timeouts on jobs; concurrency on ci-api; Contents list in unverified-and-risks.md; registry pull token for the deploy gate as an environment secret on Pro/Team (rule 10) with the Free variant warning.
Approval line: The user approved 9 skills, 2 agents, 4 rules and command /building-cicd-pipelines on 2026-10-30 (G1, workspace/github-actions-cicd/execution-1/state/gates/G1.md) and the fan-out at G2 (state/gates/G2.md); this is P6 fix cycle round 1. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent; do NOT enter plan mode.
- Change only what a listed finding names; keep tags/registers consistent (update unverified-and-risks.md counts and mapping when you add/remove tags); keep every blueprint <= 160 lines; SKILL.md frontmatter only name + description.
- Do not touch _family_* files, shared files, other skills or other packages. If a finding contradicts a family fact, stop and report it.
- Apply workspace/github-actions-cicd/_family_facts.md (F1-F42) and _family_rules.md (1-18; NEW 17 canonical names, 18 timeouts/concurrency/id-token/env secrets) as given.
- Never make shipped text READ workspace/; never invent SHAs or versions.
Evidence: the round-1 reports in workspace/github-actions-cicd/execution-1/rounds/round-1/ (validate__<target>.md, test__<target>.md, audit__package.md) give file:line and fix hints.
Done when: .claude/skills/building-agent-packages/scripts/verify_skill.py <skill-dir> would exit 0 (the orchestrator runs it) and you return a list "F-id -> what changed (file)".
